# Ledger

Append-only. One entry per cycle. Four fields, and the fourth is the one that matters:
every design choice forfeits something, and the forfeit gets written down while the
choice is being made.

---

## 2026-08-28 — Track 0 built; first compression numbers

**What we tried.**
Built the Track 0 term-rewriting engine to the CLAUDE.md layout: `terms.py`, `canon.py`,
`rules.py`, `search.py`, `verify.py`, plus a driver (`experiment.py`) and 22 tests
(`test_track0.py`). Stdlib only, exact `Fraction` throughout, no sympy.

Base theory: 8 oriented rules. R1 distribute, R2 expand a power of a sum, R3 collect like
terms, R4 `(uv)^n`, R5 `(u^m)^n`, R6 discharge a deferred substitution, R7 form the
difference quotient, R8 substitute `h := 0` once the term is polynomial in `h`.
Abstraction: D1–D5 plus bridge B (`Slope[x](f @ a) → (D[x] f)|x=a`).

Three configurations per problem, not two: `base` (pre-calculus only), `deriv` (R7/R8
withheld, so the abstraction is the only route to a slope), `both`.

**What happened.**

| problem | base | deriv | both | gap |
|---|---|---|---|---|
| x² at a | 8 | 4 | 4 | **4** |
| x² at 3 | 7 | 4 | 4 | **3** |
| 3x² − 5x + 1 at a | 12 | 11 | 11 | **1** |
| x³ at a | 10 | 4 | 4 | **6** |
| x³ − 2x at 1 | 8 | 8 | 8 | **0** |

Every answer independently confirmed: the verifier recovers exact polynomial coefficients
by Lagrange interpolation at rational points and differentiates the coefficient list — a
code path that shares nothing with `rules.py`. All 14 rules pass 100 random exact rational
instantiations each; R7, R8 and B are not pointwise identities and get targeted composite
checks against the same oracle. A deliberately unsound rule is included in the tests to
confirm the verifier can fail.

Two results contradict the working assumption, and they are the point of the entry:

1. **The gap collapses on multi-term polynomials.** 3x² − 5x + 1 gives a gap of 1.
   Cause is rule granularity, not the abstraction's value. With only the n-ary product
   rule D4, a constant multiple `c·u` costs D4 → D2 → D1: the rule generates a
   `x·D[x](−5)` term that then has to be killed. Three of the eleven derivative steps are
   spent cleaning up after D4. A constant-multiple rule `D(c·u) → c·D(u)` would erase
   them. **The metric is sensitive to how the proposed abstraction is factored into
   rules, not just to whether the abstraction is right.** An agent proposing a
   well-factored D and an agent proposing a badly-factored D would score differently on
   the same idea.

2. **The gap collapses at numeric evaluation points.** x³ − 2x at x=1 gives a gap of 0 —
   and the `both` column took the *base* route. Substituting a literal makes constants
   fold for free in canon, so the base grind gets cheap exactly where the derivative
   cannot. Problem-bank question 1 ("can the base solve it, painfully?") is not a property
   of the function; it is a property of the function *and the evaluation point*.

CLAUDE.md predicted the cubic base path would time out rather than complete. It did not —
x³ at a completes in 10 steps, under the depth-12 cap. Free like-power cancellation in
`canon` is doing more work than expected.

**What it cost us.**

- *Like powers combine for free inside a Mul* (`u^m · u^n → u^(m+n)`, so `h · h⁻¹ → 1`
  costs nothing). Without this the x² base path is ~14 steps and blows the depth-12 cap,
  and the search becomes intractable. **Forfeit:** the base path is flattered — this is
  the single largest thank-you the base gets, and it is the reason the cubic completes
  instead of timing out. Every reported gap is a *lower* bound on the gap under a stricter
  accounting. Pinned by a test so it cannot drift silently.
- *Rules are oriented, expansion-direction only* (distribute, never factor). **Forfeit:**
  search stays tractable, but we cannot see any path that needs factoring, and we have
  quietly handed the base a curated rule set that a real agent would have to discover.
- *Eight base rules, not the nine CLAUDE.md sketched.* The ninth would have been the power
  law, which became free in canon instead. **Forfeit:** the spec and the code have
  diverged by one rule; anyone reading CLAUDE.md alone will miscount.
- *`R8.eval_h_zero` is a single whole-term step with a structural side condition* rather
  than a limit argument. **Forfeit:** the base theory gets the hardest part of the
  pre-calculus tangent argument for one step. This is generous to the base, so again the
  gap is understated — but it also means Track 0 is *not* measuring the thing Track 1
  would measure, where that step is a real proof obligation.
- *Answers are not required to be in normal form.* `(a + a)` counts as a closed form.
  **Forfeit:** saves both configurations an R3 step, but a normal-form requirement would
  cost the base and the derivative path differently, so the gap is sensitive to a
  convention we picked for convenience.
- *Three configurations instead of two.* **Forfeit:** a third of the runtime, and one more
  number per row to explain. Bought back the ability to read a zero gap correctly — the
  x³ − 2x row is uninterpretable without the `deriv` column.

**Open, for the next cycle.** Whether to add the constant-multiple rule D6. It would raise
the 3x² − 5x + 1 gap from 1 to roughly 4. It is *not* covered by the "do not improve the
base rule set" constraint — it changes the abstraction, not the base — but it is exactly
the kind of tuning that manufactures the result we want. Not doing it unilaterally.
