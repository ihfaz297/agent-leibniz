"""Track 0 tests.  Stdlib unittest -- no pytest, no new dependencies.

    python3 test_track0.py
"""

import unittest
from fractions import Fraction

from canon import canon
from rules import BASE_ONLY, BASE_RULES, DERIV_ONLY, DERIV_RULES, WITH_DERIV, H
from search import is_closed_form, search, successors
from terms import (
    Add, At, C, D, Mul, Pow, Slope, V, contains, free_vars, subst,
)
from verify import (
    check_bridge, check_dq_composite, check_path, check_rule, oracle_eval,
)

x, h, a = V("x"), V("h"), V("a")


class TestCanon(unittest.TestCase):
    def test_flatten_and_sort_is_ac(self):
        self.assertEqual(canon(Add((x, Add((h, a))))), canon(Add((a, h, x))))
        self.assertEqual(canon(Mul((x, Mul((h, a))))), canon(Mul((a, h, x))))

    def test_identities(self):
        self.assertEqual(canon(Add((x, C(0)))), x)
        self.assertEqual(canon(Mul((x, C(1)))), x)
        self.assertEqual(canon(Mul((x, C(0)))), C(0))
        self.assertEqual(canon(Pow(x, C(1))), x)
        self.assertEqual(canon(Pow(x, C(0))), C(1))

    def test_constant_folding_is_exact(self):
        self.assertEqual(canon(Mul((C(Fraction(1, 3)), C(3)))), C(1))
        self.assertEqual(canon(Add((C(Fraction(1, 3)), C(Fraction(1, 6))))),
                         C(Fraction(1, 2)))

    def test_like_powers_cancel_for_free(self):
        # This is the one judgement call in canon.py; pin it down.
        self.assertEqual(canon(Mul((h, Pow(h, C(-1))))), C(1))
        self.assertEqual(canon(Mul((Pow(h, C(2)), Pow(h, C(-1))))), h)

    def test_like_terms_are_not_collected_for_free(self):
        # x + x must stay a two-element sum; collecting it is R3, a real step.
        self.assertEqual(canon(Add((x, x))), Add((x, x)))


class TestTerms(unittest.TestCase):
    def test_subst_stops_at_binders(self):
        self.assertEqual(subst(At(x, "x", a), "x", C(5)), At(x, "x", a))
        self.assertEqual(subst(At(x, "y", V("y")), "y", C(5)), At(x, "y", C(5)))

    def test_free_vars_of_D_keeps_the_variable(self):
        # D[x](x^2) is 2x -- still a function of x.
        self.assertEqual(free_vars(D(Pow(x, C(2)), "x")), frozenset({"x"}))
        self.assertEqual(free_vars(At(D(Pow(x, C(2)), "x"), "x", a)),
                         frozenset({"a"}))


class TestRules(unittest.TestCase):
    def test_at_elim_refuses_over_an_unresolved_D(self):
        t = At(D(x, "x"), "x", a)
        self.assertEqual([r for r in BASE_RULES if r.name == "R6.at_elim"][0].apply(t), [])

    def test_eval_h_zero_refuses_while_h_is_in_a_denominator(self):
        r8 = [r for r in BASE_RULES if r.name == "R8.eval_h_zero"][0]
        self.assertEqual(r8.apply(canon(Mul((h, Pow(h, C(-1)), a)))), [])  # no h left
        self.assertEqual(r8.apply(canon(Mul((a, Pow(h, C(-1)))))), [])     # unsafe
        self.assertNotEqual(r8.apply(canon(Add((a, h)))), [])              # safe

    def test_no_rule_produces_a_self_loop_as_a_step(self):
        t = canon(Slope(Pow(x, C(2)), "x", a))
        self.assertNotIn(t, successors(t, WITH_DERIV))


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.start = canon(Slope(Pow(x, C(2)), "x", a))

    def test_x_squared_base_completes_inside_the_cap(self):
        # CLAUDE.md: validate on x^2 before the cubic.  We need one completing
        # base run or "base is hard" and "base rules are incomplete" look alike.
        res = search(self.start, BASE_ONLY)
        self.assertTrue(res.found, res.status)
        self.assertEqual(res.steps, 8)

    def test_x_squared_derivative_path(self):
        res = search(self.start, DERIV_ONLY)
        self.assertTrue(res.found, res.status)
        self.assertEqual(res.steps, 4)

    def test_the_gap_exists_on_a_monomial(self):
        base = search(self.start, BASE_ONLY)
        deriv = search(self.start, DERIV_ONLY)
        self.assertGreater(base.steps, deriv.steps)

    def test_answer_matches_the_independent_oracle(self):
        env = {"a": Fraction(7, 3)}
        truth = oracle_eval(self.start, env)
        for rules in (BASE_ONLY, DERIV_ONLY, WITH_DERIV):
            res = search(self.start, rules)
            self.assertEqual(oracle_eval(res.path[-1][1], env), truth)

    def test_goal_test_rejects_a_leftover_h(self):
        self.assertFalse(is_closed_form(Add((a, h))))
        self.assertFalse(is_closed_form(D(x, "x")))
        self.assertTrue(is_closed_form(Mul((C(2), a))))

    def test_budget_is_reported_not_silently_swallowed(self):
        res = search(self.start, WITH_DERIV, max_depth=12, node_budget=5)
        self.assertEqual(res.status, "budget_exceeded")


class TestVerifier(unittest.TestCase):
    def test_every_identity_rule_gets_real_instances(self):
        # A rule the generator never triggers would report "0 checked, ok",
        # which is how a broken rule hides.
        for rule in BASE_RULES + DERIV_RULES:
            if not rule.identity:
                continue
            n, fails = check_rule(rule, trials=25)
            self.assertGreater(n, 0, f"{rule.name} never fired")
            self.assertEqual(fails, [], f"{rule.name}: {fails[:1]}")

    def test_bridge_against_the_oracle(self):
        _, fails = check_bridge(trials=25)
        self.assertEqual(fails, [])

    def test_difference_quotient_composite_against_the_oracle(self):
        _, fails = check_dq_composite(trials=25)
        self.assertEqual(fails, [])

    def test_oracle_is_independent_of_the_rules(self):
        # 3x^2 - 5x + 1 at x = 2  ->  6*2 - 5 = 7
        f = canon(Add((C(1), Mul((C(-5), x)), Mul((C(3), Pow(x, C(2)))))))
        self.assertEqual(oracle_eval(Slope(f, "x", C(2)), {}), Fraction(7))

    def test_found_paths_are_sound_step_by_step(self):
        start = canon(Slope(Pow(x, C(2)), "x", a))
        for rules in (BASE_ONLY, DERIV_ONLY):
            res = search(start, rules)
            _, fails = check_path(start, res.path)
            self.assertEqual(fails, [])

    def test_a_deliberately_wrong_rule_is_caught(self):
        # The verifier has to be able to fail, or the green ticks mean nothing.
        from rules import Rule
        bad = Rule("bogus", lambda t: [Add((t, C(1)))] if isinstance(t, Mul) else [])
        n, fails = check_rule(bad, trials=25)
        self.assertGreater(len(fails), 0)



class TestClosure(unittest.TestCase):
    """search(closure=2): local 2-chains count as one step (LEDGER 2026-09-12)."""

    def _start(self):
        body = Add((C(1), Mul((C(-5), x)), Mul((C(3), Pow(x, C(2))))))  # 3x^2 - 5x + 1
        return canon(Slope(canon(body), "x", a))

    def test_closure_never_lengthens_a_path_and_stays_sound(self):
        from rules import BASE_ONLY, DERIV_ONLY
        from verify import check_path
        start = self._start()
        for rules in (BASE_ONLY, DERIV_ONLY):
            r1 = search(start, rules, closure=1)
            r2 = search(start, rules, closure=2)
            self.assertTrue(r1.found and r2.found)
            self.assertLessEqual(r2.steps, r1.steps)
            _, fails = check_path(start, r2.path)
            self.assertEqual(fails, [])
            self.assertEqual(r1.path[-1][1], r2.path[-1][1])

    def test_closure_one_is_the_old_behaviour(self):
        from rules import BASE_ONLY
        start = self._start()
        self.assertEqual(search(start, BASE_ONLY).steps, search(start, BASE_ONLY, closure=1).steps)

    def test_constant_multiple_emerges_as_a_chain(self):
        """D(c*u) -> c*D(u) is not a rule; under closure it is the step D4>D1."""
        from rules import DERIV_ONLY
        r = search(self._start(), DERIV_ONLY, closure=2)
        self.assertIn("D4.mul>D1.const", [n for n, _ in r.path])

if __name__ == "__main__":
    unittest.main(verbosity=2)
