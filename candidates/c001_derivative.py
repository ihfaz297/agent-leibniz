"""c001 -- the derivative, as already written in rules.py.

This is the CONTAMINATION CEILING, not a discovery.  The rules are imported
from `rules.py` rather than retyped, because they are literally the same
abstraction: a model that has read every calculus textbook wrote them, and the
number this candidate scores is the ceiling any future proposer is measured
against.  Report it, do not celebrate it (FIRST_MISSIONS.txt, M2).

The one thing it is honestly allowed to claim: `saw_heldout` is False, and git
proves it.  D1-D5 and B were committed in `rules.py` on 2026-08-28
(dac5c44); `heldout.py` was written and frozen on 2026-09-12 (a0ce525).  The
abstraction predates the held-out set, so scoring it on that set is legitimate.
"""

from rules import DERIV_RULES

NAME = "derivative (D1-D5 + bridge B) -- contamination ceiling"

RULES = DERIV_RULES

PROVENANCE = {
    "proposer": "Claude (Aug 2026 session), hand-written into rules.py",
    "kind": "abstraction",
    "saw_heldout": False,      # git: rules.py 2026-08-28, heldout.py 2026-09-12
    "saw_boundary": False,     # boundary.py written 2026-09-12
    "calculus_words": True,    # the rules are NAMED after the derivative
    "date": "2026-08-28",
}

NOTES = """
Fully contaminated in the sense that matters: the proposer knew calculus, the
rules are named after it, and the bridge rule B states the answer outright.
What it measures is whether the LOOP works -- soundness check, training score,
held-out transfer, triage -- against a candidate whose verdict we already know
(Kept).  A loop that cannot Keep this one is broken.

Known weakness, from LEDGER.md 2026-09-12: this factoring has additivity (D3)
but not homogeneity -- there is no constant-multiple rule.  So it is slower than
it should be on polynomials with non-unit coefficients, and on `4x - 7` it is
one step SLOWER than plain algebra.  That is a property of this factoring, not
of the derivative, and it is why the per-problem gap is not the headline number.
"""
