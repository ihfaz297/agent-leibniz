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

        class Stub:
            NAME = "stub"
            RULES = ()
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
