"""Held-out problem set.  FROZEN 2026-09-12.

Written before any candidate abstraction beyond D1-D5+B was run against it,
and frozen before D1-D5+B itself was.  Per CLAUDE.md: never edited to be "more representative."
The only permitted change is appending, and every append
gets a ledger line.

Selection was by grid, not by hand: degree {1,2,3} × term count {1,2,3} ×
coefficients {unit, non-unit} × evaluation point {symbolic, numeric}.  Eight
cells chosen so that every axis varies at least twice and no cell repeats a
training problem in experiment.py.  The grid is the disclosure: whoever
wrote this knew D6 existed (see LEDGER.md 2026-09-12), so the choice of
problems was taken out of their hands.

`expect_base` is a prediction written before the base was run, per the
four-question rubric (Q1: can the base solve it, painfully?).  Ledger records
whether the prediction held.
"""

from experiment import poly, C, V

#: (name, body, evaluation point, expect_base)
HELDOUT = [
    # degree 1 — the floor.  If the gap is negative here the metric is broken.
    ("4x - 7 at a",           poly(-7, 4),          V("a"),  True),
    # degree 2, unit coefficients, two terms, symbolic
    ("x^2 + x at a",          poly(0, 1, 1),        V("a"),  True),
    # degree 2, one term, non-unit, symbolic
    ("2x^2 at a",             poly(0, 0, 2),        V("a"),  True),
    # degree 2, rational coefficient — exercises the Fraction path
    ("x^2/2 - 3x at a",       poly(0, -3, "1/2"),   V("a"),  True),
    # degree 2, numeric point, constant term — the x^3-2x-at-1 failure mode
    ("x^2 - 4 at 2",          poly(-4, 0, 1),       C(2),    True),
    # degree 3, unit, two terms, symbolic — probably at the cap
    ("x^3 + x^2 at a",        poly(0, 0, 1, 1),     V("a"),  False),
    # degree 3, one term, numeric, negative point
    ("x^3 at -2",             poly(0, 0, 0, 1),     C(-2),   True),
    # degree 3, three terms, non-unit, symbolic — expected to exhaust the cap
    ("2x^3 - 3x^2 + x at a",  poly(0, 1, -3, 2),    V("a"),  False),
]
