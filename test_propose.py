"""Tests for the proposer loop.  Deliberately cheap -- the full loop takes a
minute per candidate, so these test the referees and the triage logic directly
rather than driving end-to-end runs."""

from __future__ import annotations

import unittest

import propose
from propose import BadCandidate, load, soundness, triage


class TestCandidateContract(unittest.TestCase):

    def test_the_three_shipped_candidates_load(self):
        for name in ("c001_derivative", "c002_bad_power", "c003_additive_only"):
            mod = load(name)
            self.assertTrue(mod.RULES)
            self.assertIn("proposer", mod.PROVENANCE)

    def test_missing_provenance_is_refused(self):
        class Stub:
            NAME = "stub"
            RULES = ()
            PROVENANCE = {"proposer": "x"}          # missing the rest
        import sys
        sys.modules["candidates._stub_missing"] = Stub
        with self.assertRaises(BadCandidate):
            load("_stub_missing")

    def test_a_proposer_that_saw_heldout_is_refused(self):
        """The refusal is not a warning.  A candidate proposed with the held-out
        set in view cannot be scored on it, and no amount of good faith fixes
        that after the fact (CLAUDE.md)."""
        class Stub:
            NAME = "stub"
            RULES = ()
            PROVENANCE = {"proposer": "x", "saw_heldout": True,
                          "saw_boundary": False, "calculus_words": True,
                          "date": "2026-09-27"}
        import sys
        sys.modules["candidates._stub_contaminated"] = Stub
        with self.assertRaises(BadCandidate) as cm:
            load("_stub_contaminated")
        self.assertIn("held-out", str(cm.exception))


class TestSoundnessReferee(unittest.TestCase):

    def test_it_catches_the_broken_power_rule(self):
        s = soundness(load("c002_bad_power"), trials=20)
        self.assertTrue(s["failures"], "the broken power rule went undetected")
        self.assertTrue(any("D5.pow_BROKEN" in f[0] for f in s["failures"]))

    def test_it_passes_the_sound_but_useless_candidate(self):
        """c003 is true and worthless.  The soundness referee must not object:
        if it does, it is judging usefulness, which is not its job."""
        s = soundness(load("c003_additive_only"), trials=20)
        self.assertEqual(s["failures"], [])

    def test_it_passes_the_real_derivative(self):
        s = soundness(load("c001_derivative"), trials=20)
        self.assertEqual(s["failures"], [])


class TestTriage(unittest.TestCase):
    """Every candidate lands in exactly one bucket, and the ORDER matters:
    unsoundness outranks usefulness, because an unsound candidate can score
    exactly as well as a correct one (LEDGER.md 2026-09-27)."""

    def _summary(self, **kw):
        base = {"wrong_answers": [], "finishes_base_cannot": [],
                "base_finishes_cand_cannot": [], "gaps": {}, "median_gap": None}
        base.update(kw)
        return base

    def test_unsound_is_quarantined_even_when_it_scores_well(self):
        sound = {"failures": [("D5", "counterexample")], "checked": {}, "unchecked": []}
        good = self._summary(finishes_base_cannot=["p1", "p2"], median_gap=3)
        bucket, reason = triage(sound, good, good)
        self.assertEqual(bucket, "Quarantined")
        self.assertIn("unsound", reason)

    def test_wrong_answer_is_quarantined_even_with_clean_rules(self):
        sound = {"failures": [], "checked": {}, "unchecked": []}
        bad = self._summary(wrong_answers=["p1"], median_gap=3)
        bucket, _ = triage(sound, bad, bad)
        self.assertEqual(bucket, "Quarantined")

    def test_helps_heldout_is_kept(self):
        sound = {"failures": [], "checked": {}, "unchecked": []}
        bucket, _ = triage(sound,
                           self._summary(median_gap=2),
                           self._summary(finishes_base_cannot=["p1"], median_gap=2))
        self.assertEqual(bucket, "Kept")

    def test_training_only_is_quarantined_with_that_reason(self):
        sound = {"failures": [], "checked": {}, "unchecked": []}
        bucket, reason = triage(sound,
                                self._summary(median_gap=4),
                                self._summary(median_gap=0))
        self.assertEqual(bucket, "Quarantined")
        self.assertIn("training", reason)

    def test_sound_and_inert_is_quarantined(self):
        sound = {"failures": [], "checked": {}, "unchecked": []}
        bucket, reason = triage(sound, self._summary(), self._summary())
        self.assertEqual(bucket, "Quarantined")
        self.assertIn("does not help", reason)


class TestTheFindingIsPinned(unittest.TestCase):

    def test_broken_and_correct_candidates_have_the_same_rule_count(self):
        """The reason step-count scoring cannot tell c001 from c002: they differ
        by one character inside one rule, so they explore the same shape of
        search space and finish in the same number of steps.  Pinned so nobody
        later 'simplifies' the loop down to a single referee."""
        c1 = load("c001_derivative")
        c2 = load("c002_bad_power")
        self.assertEqual(len(c1.RULES), len(c2.RULES))


if __name__ == "__main__":
    unittest.main(verbosity=2)
