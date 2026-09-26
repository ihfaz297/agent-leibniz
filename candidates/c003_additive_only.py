"""c003 -- FIXTURE, sound but useless.  Must be Quarantined.

Not a proposal.  c001 with the product rule (D4) and the power rule (D5)
removed, leaving only: constant, variable, sum, and the bridge.

Every remaining rule is a true statement about the derivative, so the soundness
referee will pass it.  But `D(4*x)` and `D(x^2)` are both unreachable, so it
cannot finish a single problem in the bank.

This is the failure mode the design notes warned about and named: a checker can
tell you a rule is VALID, never that it is USEFUL.  Left alone with only a
soundness gate, a generator emits infinite well-typed garbage -- which is how
Lenat's AM died.  c003 is the smallest example of that in this repo, and the
reason soundness and usefulness are two separate referees in propose.py.
"""

from rules import DERIV_RULES

NAME = "FIXTURE: sound but useless (no product or power rule)"

RULES = tuple(r for r in DERIV_RULES
              if r.name not in ("D4.mul", "D5.pow"))

PROVENANCE = {
    "proposer": "fixture -- c001 with two rules deleted",
    "kind": "fixture",
    "saw_heldout": False,
    "saw_boundary": False,
    "calculus_words": True,
    "date": "2026-09-27",
}

NOTES = """
Expected verdict: Quarantined, and specifically NOT by the soundness referee --
it should pass soundness cleanly and be rejected for usefulness. If the
soundness referee flags it, the referee is wrong: every rule in here is true.
"""
