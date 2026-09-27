"""Tests for the obfuscation layer and the proposer adapter.

No network. The adapter is exercised with a canned reply, which is also how you should
develop against it before spending a single API call."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import experiment
import obfuscate
import proposer
from obfuscate import ARMS, build_prompt, check_clean, render
from proposer import audit, extract_module


class TestObfuscation(unittest.TestCase):

    def test_the_renamed_arm_leaks_no_target_vocabulary(self):
        """The whole arm is invalidated by one leaked word, so this is checked rather
        than trusted. It caught a real leak on first wiring: the output template's
        import line said `from terms import Slope, D`."""
        text = build_prompt(experiment.PROBLEMS, ARMS["renamed"])
        self.assertEqual(check_clean(text), [])

    def test_the_plain_arm_deliberately_does_leak(self):
        """Arm 1 is the contamination ceiling. If it were clean, the two arms would not
        differ and the comparison would measure nothing."""
        text = build_prompt(experiment.PROBLEMS, ARMS["plain"])
        self.assertTrue(check_clean(text))

    def test_both_arms_describe_the_same_number_of_rules(self):
        """Arms must differ only in naming. A different rule count would mean the
        proposer was shown a different system, not the same one renamed."""
        a = build_prompt(experiment.PROBLEMS, ARMS["plain"])
        b = build_prompt(experiment.PROBLEMS, ARMS["renamed"])
        self.assertEqual(a.count("   ->   "), b.count("   ->   "))

    def test_every_base_rule_gets_a_demonstration(self):
        """Rules are described only by example, so a rule with no demonstration would
        be invisible to the proposer."""
        from rules import BASE_RULES
        demos = obfuscate.demonstrate(BASE_RULES, ARMS["renamed"])
        self.assertEqual(len(demos), len(BASE_RULES))
        for name, demo in demos:
            self.assertNotIn("no demonstration", demo, f"{name} has no demonstration")

    def test_opaque_rule_names_carry_no_information(self):
        """`R1.distribute` -> `r1`. Derived from position, not from the real name: an
        earlier version built it from the name and leaked a character ('rr1')."""
        from rules import BASE_RULES
        names = [n for n, _ in obfuscate.demonstrate(BASE_RULES, ARMS["renamed"])]
        self.assertEqual(names, [f"r{i + 1}" for i in range(len(BASE_RULES))])

    def test_rendering_hides_operator_identity(self):
        from terms import C, Pow, Slope, V
        t = Slope(Pow(V("x"), C(2)), "x", V("a"))
        self.assertIn("Slope", render(t, ARMS["plain"]))
        self.assertNotIn("Slope", render(t, ARMS["renamed"]))
        self.assertIn("GOAL", render(t, ARMS["renamed"]))


_GOOD_REPLY = """
Reasoning about r7, here is my proposal.

```python
from opaque_ops import Rule, C, Const, OP

def _op_const(t):
    if isinstance(t, OP) and isinstance(t.body, Const):
        return [C(0)]
    return []

RULES = (Rule("n1.const", _op_const),)
```
"""

_BAD_REPLY = """
```python
import subprocess
from pathlib import Path
RULES = ()
```
"""


class TestExtraction(unittest.TestCase):

    def test_it_finds_the_fenced_block(self):
        src = extract_module(_GOOD_REPLY)
        self.assertIn("_op_const", src)
        self.assertNotIn("Reasoning about", src)

    def test_a_reply_with_no_code_is_an_error_not_a_guess(self):
        with self.assertRaises(proposer.ProposerError):
            extract_module("I think the answer is the derivative.")


class TestAudit(unittest.TestCase):
    """The audit is a filter on what a human is asked to read, never a substitute for
    them reading it."""

    def test_a_reasonable_module_passes(self):
        self.assertEqual(audit(extract_module(_GOOD_REPLY) + '\nNAME = "x"'), [])

    def test_unexpected_imports_are_objected_to(self):
        problems = audit(extract_module(_BAD_REPLY))
        self.assertTrue(any("subprocess" in p for p in problems))
        self.assertTrue(any("pathlib" in p for p in problems))

    def test_missing_rules_is_objected_to(self):
        self.assertTrue(any("RULES" in p for p in audit("NAME = 'x'")))


class TestTheReviewGate(unittest.TestCase):
    """A machine-written candidate must not be scorable until a human has read it,
    because scoring imports and executes it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.orig = os.getcwd()

    def tearDown(self):
        os.chdir(self.orig)
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_unreviewed_machine_candidates_are_refused(self):
        import sys
        from propose import BadCandidate, load

        class Stub:
            NAME = "stub"
            RULES = ()
            REVIEWED = False
            PROVENANCE = {"proposer": "a model", "kind": "machine",
                          "saw_heldout": False, "saw_boundary": False,
                          "calculus_words": False, "date": "2026-09-27"}
        sys.modules["candidates._stub_machine"] = Stub
        with self.assertRaises(BadCandidate) as cm:
            load("_stub_machine")
        self.assertIn("REVIEWED", str(cm.exception))

    def test_reviewed_machine_candidates_load(self):
        import sys
        from propose import load
        from rules import Rule

        class Stub:
            NAME = "stub"
            # a real rule, not (): the smoke test rejects an empty RULES, correctly
            RULES = (Rule("n1.noop", lambda t: []),)
            REVIEWED = True
            PROVENANCE = {"proposer": "a model", "kind": "machine",
                          "saw_heldout": False, "saw_boundary": False,
                          "calculus_words": False, "date": "2026-09-27"}
        sys.modules["candidates._stub_machine_ok"] = Stub
        self.assertTrue(load("_stub_machine_ok"))


class TestUnverifiedIsNotUnsound(unittest.TestCase):
    """A rule that never fires on a random term is UNVERIFIABLE, not wrong. Calling it
    unsound would quarantine correct proposals -- a proposer that declares its bridge
    rule as a pointwise identity lands here, and a false rejection is far worse for
    this experiment than a false pass."""

    def test_a_never_firing_rule_is_unverified_not_failed(self):
        from propose import soundness
        from rules import Rule
        from terms import C, Slope

        def _only_fires_on_slope(t):
            return [C(0)] if isinstance(t, Slope) else []

        class Stub:
            NAME = "stub"
            RULES = (Rule("n1.slope_only", _only_fires_on_slope),)
            PROVENANCE = {}
        s = soundness(Stub, trials=20)
        self.assertEqual(s["failures"], [])
        self.assertIn("n1.slope_only", s["unverified"])


NL = chr(10)
F = "`" * 3


class TestMessyModelOutput(unittest.TestCase):
    """The point of this class. A real reply is not a canned one, and every failure
    below is a REFUSAL WITH A REASON rather than a stack trace -- either at write time
    (audit) or at load time (smoke_test), never five minutes into a search."""

    def _stub(self, name, rules, provenance=None):
        import sys
        mod = type("M", (), {})
        mod.NAME = name
        mod.RULES = rules
        mod.REVIEWED = True
        mod.PROVENANCE = provenance or {
            "proposer": "a model", "kind": "machine", "saw_heldout": False,
            "saw_boundary": False, "calculus_words": False, "date": "2026-09-27"}
        sys.modules[f"candidates._{name}"] = mod
        return f"_{name}"

    def test_source_that_does_not_parse_is_refused_at_write_time(self):
        problems = audit("def f(t:\n    return [")
        self.assertTrue(problems)
        self.assertIn("does not parse", problems[0])

    def test_bare_functions_instead_of_Rule_objects(self):
        """The single most likely shape error: the model writes the functions and
        forgets to wrap them."""
        from propose import BadCandidate, load
        def _f(t):
            return []
        name = self._stub("bare_fns", (_f,))
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("not a Rule", str(cm.exception))

    def test_a_rule_that_raises_is_caught_before_scoring(self):
        from propose import BadCandidate, load
        from rules import Rule
        def _boom(t):
            return [t.body.args[7]]          # IndexError / AttributeError on most terms
        name = self._stub("boom", (Rule("n1.boom", _boom),))
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        msg = str(cm.exception)
        self.assertIn("unscoreable", msg)
        self.assertIn("n1.boom", msg)

    def test_a_rule_returning_None_is_caught(self):
        from propose import BadCandidate, load
        from rules import Rule
        name = self._stub("nones", (Rule("n1.none", lambda t: None),))
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("None", str(cm.exception))

    def test_a_rule_returning_a_bare_term_is_caught(self):
        """Returning the term instead of a list of terms -- an easy misreading of the
        contract, and it would otherwise corrupt the search silently."""
        from propose import BadCandidate, load
        from rules import Rule
        from terms import C
        name = self._stub("bare_term", (Rule("n1.bare", lambda t: C(0)),))
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("must return a list", str(cm.exception))

    def test_wrong_arity_is_caught(self):
        from propose import BadCandidate, load
        from rules import Rule
        name = self._stub("arity", (Rule("n1.arity", lambda t, extra: []),))
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("unscoreable", str(cm.exception))

    def test_empty_RULES_is_caught(self):
        from propose import BadCandidate, load
        name = self._stub("empty", ())
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("empty", str(cm.exception))

    def test_RULES_of_the_wrong_type_is_caught(self):
        from propose import BadCandidate, load
        name = self._stub("wrongtype", "not a tuple")
        with self.assertRaises(BadCandidate) as cm:
            load(name)
        self.assertIn("expected a tuple", str(cm.exception))

    def test_a_good_candidate_still_passes_the_smoke_test(self):
        """The gate must not be so strict that the real abstraction trips it."""
        from propose import load, smoke_test
        self.assertEqual(smoke_test(load("c001_derivative")), [])

    def test_prose_and_several_blocks_still_extracts(self):
        """A real reply wraps its code in prose and sometimes offers two blocks."""
        reply = NL.join([
            "Here are two options.",
            "",
            F + "python",
            "RULES = ()",
            F,
            "",
            "Actually this longer one is better:",
            "",
            F + "python",
            "from opaque_ops import Rule",
            "def _f(t):",
            "    return []",
            "RULES = (Rule('n1.f', _f),)",
            "NAME = 'x'",
            F,
        ])
        src = extract_module(reply)
        self.assertIn("n1.f", src)
        self.assertEqual(audit(src), [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
