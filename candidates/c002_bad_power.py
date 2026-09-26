"""c002 -- FIXTURE, deliberately unsound.  Must be Quarantined.

Not a proposal.  A mechanical corruption of c001: the power rule drops the
exponent decrement, so D(u^n) -> n*u^n*D(u) instead of n*u^(n-1)*D(u).  Every
other rule is untouched.

It exists to prove the loop can reject.  A pipeline that has never rejected
anything is not a referee, it is a rubber stamp -- so one of these lives in the
repo permanently, the same way test_track0.py keeps a deliberately wrong rule.

The corruption is a one-token edit and does not depend on the contents of any
problem bank, which is why `saw_heldout` is honestly False.
"""

from rules import Rule, DERIV_RULES
from terms import C, Const, D, Mul, Pow


def _d5_pow_broken(t):
    """WRONG on purpose: forgets to decrement the exponent."""
    if not (isinstance(t, D) and isinstance(t.body, Pow)):
        return []
    p = t.body
    if not isinstance(p.exp, Const):
        return []
    n = p.exp.value
    return [Mul((C(n), Pow(p.base, C(n)), D(p.base, t.var)))]   # n, not n-1


NAME = "FIXTURE: derivative with a broken power rule (must be Quarantined)"

RULES = tuple(r for r in DERIV_RULES if r.name != "D5.pow") + (
    Rule("D5.pow_BROKEN", _d5_pow_broken),
)

PROVENANCE = {
    "proposer": "fixture -- mechanical corruption of c001",
    "kind": "fixture",
    "saw_heldout": False,
    "saw_boundary": False,
    "calculus_words": True,
    "date": "2026-09-27",
}

NOTES = """
Expected verdict: Quarantined, caught by the soundness referee at the rule level
(check_rule should find a counterexample within a handful of random
instantiations, since D(x^2) -> 2*x^2 is wrong at every x other than 0 and 1).

If it is ever caught only by the answer-level oracle and not by check_rule, that
is a finding about the rule-level checker's coverage and belongs in the ledger.
"""
