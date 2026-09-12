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

---

## 2026-09-12 — D6 measured and deferred; one plan quarantined

**What we tried.**

Two things, one of them housekeeping.

*Housekeeping.* A Gemini-generated "system prompt" (MCTS + FunSearch + Qiskit "fidelity"
as a verifier, under the borrowed name Minimo) had landed in the repo root. Moved to
`graveyard/brainwash-gemini-2026-09.txt` with a header saying what it is. Not deleted:
it is a clean specimen of the failure mode this project studies — a fluent, confident
artifact with no falsifiable mechanism in it. Rule adopted: CLAUDE.md is the plan,
LEDGER.md is the record, everything else is a chat log.

*D6.* Measured the constant-multiple rule `D(c·u) → c·D(u)` (rational literal `c`) as
a scratch candidate, without editing `rules.py`. Same three configurations, same oracle.

**What happened.**

| problem | base | deriv | deriv+D6 | gap | gap+D6 |
|---|---|---|---|---|---|
| x² at a | 8 | 4 | 4 | 4 | 4 |
| x² at 3 | 7 | 4 | 4 | 3 | 3 |
| 3x² − 5x + 1 at a | 12 | 11 | **9** | 1 | **3** |
| x³ at a | 10 | 4 | 4 | 6 | 6 |
| x³ − 2x at 1 | 8 | 8 | **7** | 0 | **1** |

Sound on every path; oracle agrees. Last cycle's estimate of "roughly 4" was wrong; it
is 3. D6 touches only the rows with non-unit coefficients, as it should.

The 9-step path: B, D3, D1, D6, D2, D6, D5, D2, R6. Every step is doing something; there
is no cleanup left. So 9 is the floor for this abstraction on this problem, and the base's
12 is the base's floor under the current rules. A gap of 3 is what "linearity vs. grind"
is worth on a three-term quadratic at a symbolic point. Smaller than we hoped.

**Decision: D6 is not added this cycle.** Two reasons, one good and one decisive.

The good reason for adding it: the derivative on ℚ[x] is *the* ℚ-linear derivation with
D(x)=1. D3 is additivity; D6 is homogeneity. The current abstraction has half of linearity.
That is a legitimate definitional argument and it will still be true next cycle.

The decisive reason against, today: there is no held-out set. All five problems in
`experiment.py` are training. We looked at the training row with the worst gap and found
the rule that improves it — that is exactly the selection a held-out set exists to catch,
and with no held-out set the definitional argument and post-hoc tuning are
indistinguishable. Any lemma that helped would have had *some* story.

Second, a symmetry the "do not improve the base" constraint does not cover: the base path
spends four steps in `R1.distribute` and would also benefit from compound lemmas. If
derived lemmas are admissible for the abstraction and not for the base, the gap measures
our tuning budget.

**Next cycle, in order.** (1) Write the held-out set, before any candidate touches it.
(2) Write down the *policy*: is the abstraction its generating set only, or the
generating set plus lemmas derivable in ≤ k of its own steps — and if the latter, the base
gets the same allowance. (3) Run D6 through normal triage against held-out. It goes in
with the held-out number or not at all.

**What it cost us.**

- *Deferring D6.* **Forfeit:** the 3x² − 5x + 1 row stays at gap 1 and reads as "the
  abstraction barely helps on the one realistic polynomial." The honest caption is "we
  withheld half of linearity"; that has to be said every time the table is shown.
- *Measuring D6 on training before a held-out set existed.* **Forfeit:** we now know
  which rule helps, and cannot un-know it. Whoever writes the held-out set writes it
  knowing D6 exists. The mitigation is that held-out problems are chosen by the
  four-question rubric, not by coefficient pattern, and that the set is fixed before
  D6 is run on it — but the contamination is real and this line is the disclosure.
- *Quarantine, not deletion, of the Gemini plan.* **Forfeit:** one more file for a new
  reader to be confused by. Bought: a documented specimen, and a habit — plans get
  triaged the same way candidates do.

**Addendum, same day — held-out set frozen.** `heldout.py`, eight problems chosen by a
degree × terms × coefficient × point grid. Base-only run to check Q1 predictions: all
eight held (6, 10, 9, 12, 7, exhausted, 9, exhausted). Two decisions made at freeze:
`x²/2 − 3x at a` sits exactly at the depth-12 cap and stays there — it completed, and
moving it because of the number is the edit CLAUDE.md forbids. The two cubic rows
exhaust the cap and the cap is not raised — an instrument adjusted after seeing the data
is not an instrument. **Forfeit:** six informative rows out of eight, and one of the six
is one accounting change away from becoming a seventh exhausted row. No `deriv` or D6
numbers existed on this set at the time of freezing.

**Addendum, same day — D1-D5+B on the frozen held-out set.**

| problem | base | deriv | both | gap |
|---|---|---|---|---|
| 4x − 7 at a | 6 | 7 | 6 | **−1** |
| x² + x at a | 10 | 6 | 6 | 4 |
| 2x² at a | 9 | 6 | 6 | 3 |
| x²/2 − 3x at a | 12 | 10 | 10 | 2 |
| x² − 4 at 2 | 7 | 6 | 6 | 1 |
| x³ + x² at a | exhausted | 7 | 7 | – |
| x³ at −2 | 9 | 4 | 4 | 5 |
| 2x³ − 3x² + x at a | exhausted | 12 | 12 | – |

All paths sound, all answers match the oracle. Three readings:

1. **The abstraction loses on the linear case.** On 4x − 7 the derivative path is one step
   *longer* than the grind, and `both` takes the base route. Cause is the same
   D4-then-cleanup cost as the 3x² − 5x + 1 training row: `D(4x)` costs D4 → D2 → D1
   where the grind just distributes. This is the first negative gap the instrument has
   produced and it is on the simplest problem in the bank. It is not a metric failure —
   it is the metric saying that D1-D5+B, as factored, is a worse tool than algebra for
   degree 1. Honest and worth keeping in the table.
2. **The cubics complete under the abstraction and not under the base.** This is the
   "cubic times out" result CLAUDE.md predicted, now on held-out. The gap prints as `–`;
   under any depth cap it is ≥ 12 − 7 = 5 and ≥ 12 − 12 = 0 respectively. The second of
   those is not informative: 2x³ − 3x² + x hits the cap on the *derivative* side too.
3. **Gap tracks non-unit coefficients downward, again.** Rows with unit coefficients
   (x² + x, x³ at −2) gap 4–5; rows with non-unit coefficients gap 1–3 or negative.
   Same mechanism as the training set. This is now a held-out finding, not a training
   artefact.

**Forfeit:** none new — but the 2x³ − 3x² + x row was frozen with a `deriv` cost sitting
exactly on the cap, which nobody could have known before running it, and it will flip to
uninformative under any accounting change.

---

## 2026-09-12 (later) — Route 2: symmetric local closure. The gap mostly disappears.

**What we tried.**

Decision taken: derived lemmas count as one step, *symmetrically*. Implemented not by
hand-writing D6 and a matching set of base lemmas (which would have been "improving the
base rule set" by another name) but mechanically: `search(..., closure=2)` lets a second
rule fire *inside the subterm the first rule just produced*, and the composite is one
step. Locality is essential — a global "any 2 steps = 1" just halves every path and
measures nothing. Under local closure, `D(c·u) → c·D(u)` falls out of D4-then-D1 without
being written; the base gets R7-then-R6, R6-then-R1, R1-then-R1, R3-then-R8, and so on,
on the same terms. Default `closure=1` is untouched; all 22 tests still pass.

**What happened.** closure=1 → closure=2, all paths sound, all answers match the oracle.

| | closure=1 | | | closure=2 | | |
|---|---|---|---|---|---|---|
| problem | base | deriv | gap | base | deriv | gap |
| x² at a | 8 | 4 | 4 | 4 | 3 | **1** |
| x² at 3 | 7 | 4 | 3 | 4 | 3 | **1** |
| 3x² − 5x + 1 at a | 12 | 11 | 1 | 7 | 7 | **0** |
| x³ at a | 10 | 4 | 6 | 5 | 3 | **2** |
| x³ − 2x at 1 | 8 | 8 | 0 | 4 | 5 | **−1** |
| *held-out* | | | | | | |
| 4x − 7 at a | 6 | 7 | −1 | 4 | 5 | **−1** |
| x² + x at a | 10 | 6 | 4 | 5 | 4 | **1** |
| 2x² at a | 9 | 6 | 3 | 5 | 4 | **1** |
| x²/2 − 3x at a | 12 | 10 | 2 | 6 | 6 | **0** |
| x² − 4 at 2 | 7 | 6 | 1 | 4 | 4 | **0** |
| x³ + x² at a | exhausted | 7 | – | 7 | 4 | **3** |
| x³ at −2 | 9 | 4 | 5 | 5 | 3 | **2** |
| 2x³ − 3x² + x at a | exhausted | 12 | – | budget (400k nodes, 137 s) | 7 | – |

**The base gains more from closure than the derivative does.** Base paths roughly halve
(8→4, 12→7, 10→5); derivative paths shrink by a third (4→3, 11→7). Cause: local closure
rewards rules whose output is *rich*. R6 substitutes a polynomial, R1 distributes into
one — there is always something to chain into. D1 outputs `0`, D2 outputs `1`; there is
nothing inside to fire a second rule on. The derivative's rules are terminal by nature,
so "a derived lemma is one step" hands the derivative D6 and hands the base a great deal
more. The symmetric accounting is symmetric in rule-count and asymmetric in effect.

**What survives closure.** On every quadratic the gap is now in {−1, 0, 1}. On every cubic
that completes it is 2–3, and on the one that does not, the base exhausts a 400k node
budget where the derivative finishes in 7. Both accountings agree on one thing: the
derivative's cost grows slowly in degree and term count, and the base's grows fast. That
is a claim about *scaling*, not about per-problem gap, and it is the only claim in the
table that did not move when the accounting changed.

**Reading.** Route 2 does not rescue D6; it removes the thing D6 was supposed to improve.
The per-problem gap was a granularity artefact to within ±1 on everything below degree 3.
This confirms, harder than expected, the earlier entry's warning: step count over
hand-written rewrite rules measures the hand that wrote the rules. Track 0 has now
produced its calibration result — the metric that survives re-factoring is growth rate,
not gap, and a factoring-invariant cost (proof-term size, Track 1) is required for
anything finer.

**What it cost us.**

- *Closure is a search option, not a rule change.* **Forfeit:** two accountings now exist
  and every future number has to say which. Bought: the sensitivity of the instrument to
  factoring is a measured quantity, not a sentence.
- *Local closure, k=2, with "inside the produced subterm" as the locality criterion.*
  **Forfeit:** that criterion is a choice; a different locality (same position only, or
  anywhere below) gives different numbers. k=2 was picked because D6 is a 2-chain. Any k
  is a knob.
- *`verify.check_path` now splits composite names to find the non-identity rules.*
  **Forfeit:** one more place where the rule-name string is load-bearing.
- *Branching factor roughly squares under closure.* **Forfeit:** the hardest held-out
  problem now dies on the node budget rather than the depth cap, and took two minutes to
  do it. The budget is now part of the instrument in a way it was not before.
- *The per-problem gap, as a headline number.* **Forfeit:** it is gone below degree 3,
  and the training-set gaps of 4 and 6 in the first entry should be read as upper bounds
  under a favourable factoring. The first entry's table is not wrong, but it is not
  robust, and this line is the correction.

**Addendum — closure=3.** Same run, k=3. All paths sound, oracle agrees.

| problem | k=1 gap | k=2 gap | k=3 gap | (base / deriv at k=3) |
|---|---|---|---|---|
| x² at a | 4 | 1 | 1 | 3 / 2 |
| 3x² − 5x + 1 at a | 1 | 0 | −1 | 4 / 5 |
| x³ at a | 6 | 2 | 2 | 4 / 2 |
| x³ − 2x at 1 | 0 | −1 | 0 | 4 / 4 |
| 4x − 7 at a | −1 | −1 | 0 | 3 / 3 |
| x² + x at a | 4 | 1 | 1 | 4 / 3 |
| x²/2 − 3x at a | 2 | 0 | −1 | 4 / 5 |
| x³ + x² at a | – | 3 | 1 | 5 / 4 |
| x³ at −2 | 5 | 2 | 2 | 4 / 2 |
| 2x³ − 3x² + x at a | – | – | – | budget / 6 |

The cubic gaps did not all hold. Single-term cubics stay at 2 (k=2 → k=3). The two-term
cubic dropped 3 → 1. Two quadratics went negative. So the "scaling" claim from the k=2
entry is softer than written: what is stable across k is not a gap of 2–3 on cubics, it
is that *no gap anywhere exceeds 2 once lemmas are one step*, and that the gap on
anything below degree 3 is indistinguishable from zero.

What did hold, at every k: **2x³ − 3x² + x at a — the base does not finish and the
derivative does** (12, 7, 6 steps at k=1,2,3; base exhausts the depth cap at k=1 and the
400k node budget at k=2,3). That is not a step-count result. It is a solve-rate result:
one problem the base scores zero on and the abstraction scores one. It is also the only
row in the bank with that property, which means the current bank has a sample size of one
for the only claim that survived.

Two instrument notes. (i) At k=3 the `both` configuration *also* blew the budget on that
row while `deriv` alone finished in 6 — the larger rule set has a larger branching factor
and spends the budget before reaching depth 6. So `both = min(base, deriv)` is no longer
true by construction once the budget binds; it is true only when the search completes.
(ii) As k grows, any finite path compresses toward 1 (x² deriv: 4, 3, 2). There is no
"right" k; the accounting is degenerate in the limit, and the per-problem gap has no
k-independent meaning.

**Reading, end of day.** Track 0's calibration is done and the answer is: step-count gap
is not the measurement. The measurement is whether the base *can* finish. That is the
conclusion the design conversation reached in August on other grounds ("your metric stops
being proof length and becomes solve rate on problems the base agent scores zero on") and
which Track 0 was built partly to avoid needing. It was not avoided. The next problem bank
should be built around the base's completion boundary — problems just past what the base
can grind — not around a gap between two numbers that both finish.

**What it cost us.** *Running k=3.* **Forfeit:** three minutes and the last of the cubic
gap. Bought: the knowledge that the k=2 scaling claim would not have survived a reviewer
asking "and at k=3?", and one row — a sample of one — that is worth building the next
bank around.

---

## 2026-09-12 (night) — Boundary bank, gate item 1. Four, not ten.

**What we tried.** Sixteen candidates chosen by grid (degree {3,4} × terms {1,2,3} ×
coefficients {unit, non-unit} × point {symbolic, numeric}), committed in `boundary.py`
*before* any ran. Base and derivative at closure=1,2,3, node budget 400k, 96 searches on
11 cores, 306 s. Raw results in `results/boundary-400k.json`. A CI workflow now exists
that runs the same bank on a runner nobody touches and commits results back with the
commit hash — not used for this run (2 cores vs 11), available for the next.

**What happened.**

| problem | k=1 base/deriv | k=2 | k=3 | bin |
|---|---|---|---|---|
| x³ + x at −1 | 8 / 6 | 5 / 4 | 3 / 3 | base grinds it |
| 2x³ at a | 11 / 6 | 6 / 4 | 4 / 3 | base grinds it |
| 2x³ at 2 | 10 / 6 | 5 / 4 | 4 / 3 | base grinds it |
| x³ + x at a | 12 / 6 | 6 / 4 | 4 / 3 | base grinds it |
| x⁴ − x at 1 | 9 / 8 | 5 / 5 | 3 / 4 | base grinds it |
| x³ − x² + 1 at 2 | 9 / 10 | 5 / 6 | 4 / 5 | base grinds it |
| x⁴ at −1 | 10 / 4 | 5 / 3 | 4 / 2 | base grinds it |
| x⁴ at a | 12 / 4 | 6 / 3 | 4 / 2 | base grinds it |
| 3x³ + 2x at a | depth / 10 | 7 / 6 | 5 / 5 | moves with closure |
| x³ + x² + x at a | depth / 8 | 8 / 5 | 5 / 4 | moves with closure |
| x³ − x² at a | depth / 9 | 8 / 5 | 5 / 5 | moves with closure |
| 3x⁴ at a | depth / 6 | 7 / 4 | 5 / 3 | moves with closure |
| **x⁴ + x² at a** | budget / 7 | budget / 4 | budget / 4 | **boundary** |
| **x⁴ + x³ + x at a** | budget / 8 | budget / 5 | budget / 4 | **boundary** |
| **2x³ − 3x² + x at a** | depth / 12 | budget / 7 | budget / 6 | **boundary** |
| **2x⁴ + 3x² at a** | budget / 11 | budget / 6 | budget / 6 | **boundary** |

8 / 4 / 4. Four candidates hold at every closure; the gate asked for ten. The 800k-budget
half of the test is running on the four as this is written.

**Three readings.**

1. *The boundary is real but thin.* Where the base exhausts at all k, it does so
   decisively — the derivative finishes in 4–12 and the base burns 400k nodes. But only a
   quarter of a grid built to straddle the boundary actually lands past it. The band
   between "base grinds" and "derivative also exhausts" is one or two terms wide.
2. *"Moves with closure" is its own result.* Four problems exhaust the depth-12 cap at
   k=1 and grind in 7–8 at k=2. Under the k=1 accounting they would have been counted as
   boundary rows. They are not; they are the k=1 instrument being coarser than the k=2
   one. This is the failure mode the gate was written to catch, and it caught four.
3. *The base is a lot stronger than CLAUDE.md assumed.* "The cubic base path will
   probably time out" — it does not; every single-term cubic and quartic grinds, and
   `x⁴ at a` lands at exactly 12 at k=1, the third row this project has put on the cap
   by accident. Free like-power cancellation in `canon` is doing most of the work.

**Not decided yet:** whether four is enough. The gate says ten. The honest options are
(a) four is the answer, gate fails on count, Track 1 is not started on this bank; (b)
the grid is extended — degree 5, four terms — to find where the base's boundary sits at
k=3, with the extension committed before running, as this one was. (b) is not editing
the bank to be more representative; it is asking where the boundary is, which is the
question. But it is a decision, and it is not being taken in this entry.

**What it cost us.**

- *Sixteen candidates, not twenty-four.* **Forfeit:** eight grid cells unrun, all
  non-unit or three-term at a numeric point. The numeric-point axis is under-sampled
  exactly where earlier entries said the base gets cheap.
- *Parallel run, not CI.* **Forfeit:** the numbers were produced on a machine with a
  hand on it. The workflow exists; the first CI-produced table has not been made.
- *Budget-exceeded and depth-exhausted are both "exhausts".* **Forfeit:** they are not
  the same thing. A depth exhaust at k=1 says the shortest path is longer than 12; a
  budget exhaust says the search could not tell. Three of the four boundary rows are
  budget exhausts at k=2,3, which is why the 800k run matters.

**Addendum — 800k budget, base only, on the four.** All twelve cells exhausted. At k=1
every row went from budget-exceeded (400k) to depth-exhausted (800k): the search
*completed* depth 12 and found no path, which is the stronger statement. At k=2 and k=3
all eight cells are still budget-exceeded at 800k, 140–250 s each.

| problem | k=1 | k=2 | k=3 |
|---|---|---|---|
| x⁴ + x² at a | depth | budget | budget |
| x⁴ + x³ + x at a | depth | budget | budget |
| 2x³ − 3x² + x at a | depth | budget | budget |
| 2x⁴ + 3x² at a | depth | budget | budget |

**Gate item 1, as measured: four boundary rows, stable across closure=1,2,3 and across a
doubled budget.** The gate asked for ten. Final bins on the sixteen: 8 grind / 4 move
with closure / 4 boundary. Whether four is enough, or the grid is extended upward to find
where the k=3 boundary sits, is the open decision — not taken here.

**Forfeit:** the k=2,3 base cells are budget exhausts, not depth exhausts, at both
budgets. "No path ≤ 12" is proven only at k=1. At k=2,3 what is proven is "not findable
in 800k nodes," and someone with a bigger machine can re-ask.

---

## 2026-09-12 (late) — Extension: eight harder candidates. Six more boundary rows at 400k.

**What we tried.** Decision taken: extend the grid upward rather than fail the gate on
count — the "ten" in CLAUDE.md was written before anyone knew where the boundary sat, and
three of the four boundary rows were the largest quartics in the grid. Eight new cells
(degree 5; four-term cubics and quartics), committed in `boundary.py` before running.
Same procedure: closure=1,2,3, both sides, 400k. `results/boundary-ext-400k-*.json`.

**What happened.**

| problem | k=1 base/deriv | k=2 | k=3 | bin |
|---|---|---|---|---|
| x⁵ − 2x² at 1 | 11 / 9 | 6 / 5 | 4 / 5 | base grinds it |
| **x⁵ at a** | budget / 4 | budget / 3 | budget / 2 | boundary (400k) |
| **2x⁵ at a** | budget / 6 | budget / 4 | budget / 3 | boundary (400k) |
| **x⁵ + x at a** | budget / 6 | budget / 4 | budget / 3 | boundary (400k) |
| **x⁵ + x³ at a** | budget / 7 | budget / 4 | budget / 4 | boundary (400k) |
| **x⁵ + x⁴ + x at a** | budget / 8 | budget / 5 | budget / 4 | boundary (400k) |
| **x⁴ + x³ + x² + x at a** | budget / 10 | budget / 6 | budget / 5 | boundary (400k) |
| 2x⁴ − x³ + 3x at a | budget / **depth** | budget / 8 | budget / 7 | deriv also exhausts |

Six of eight. The 800k check on the six is running as this is written.

**Two readings.**

1. *The window has a far edge, and we hit it.* On 2x⁴ − x³ + 3x the *derivative* path
   exceeds 12 at k=1 (it is 8 at k=2), so at k=1 both sides exhaust and the row says
   nothing. The bank lives between "base grinds" and "derivative hits the cap"; at k=1
   that band is roughly degree 4–5 with up to four unit-coefficient terms. Non-unit
   coefficients on multi-term quartics fall off the far side. This bounds what the
   current instrument can ever say, and it is a depth-cap artefact on the *derivative*
   side — the first time the cap has bitten there.
2. *The numeric-point rule is now four for four.* Every candidate evaluated at a literal
   point (x³ − x² + 1 at 2, x⁴ − x at 1, x⁵ − 2x² at 1, and earlier x³ − 2x at 1) grinds.
   Literal substitution folds constants in canon for free. Symbolic-point problems are the
   only ones that reach the boundary. A future bank should say so up front rather than
   spend cells learning it again.

**What it cost us.**

- *Extending the grid after seeing the first result.* **Forfeit:** this is the closest
  the day has come to editing the bank to get the number. The defence is that the
  extension was committed before running, extends only in the direction the first result
  pointed, and the bins are reported in full — nine grind, four move with closure, one
  falls off the far edge. Anyone who wants to call it tuning has this line to cite.
- *All eight extension cells are symbolic-point except one.* **Forfeit:** the numeric
  axis is now badly under-sampled at high degree, by choice, because it was going to
  grind. That is a prediction, not a measurement, for degree 5.

**Addendum — 800k on the six. All held. Gate item 1: ten boundary rows.**

Final bins over 24 grid-chosen candidates: **9 grind / 4 move with closure / 1 falls off
the derivative's cap / 10 boundary.** The ten, with the k=1 base result at 800k:

| problem | deriv k=1/2/3 | base k=1 @800k |
|---|---|---|
| x⁴ + x² at a | 7 / 4 / 4 | depth exhausted |
| x⁴ + x³ + x at a | 8 / 5 / 4 | depth exhausted |
| 2x³ − 3x² + x at a | 12 / 7 / 6 | depth exhausted |
| 2x⁴ + 3x² at a | 11 / 6 / 6 | depth exhausted |
| x⁵ at a | 4 / 3 / 2 | depth exhausted |
| 2x⁵ at a | 6 / 4 / 3 | depth exhausted |
| x⁵ + x at a | 6 / 4 / 3 | depth exhausted |
| x⁵ + x³ at a | 7 / 4 / 4 | budget |
| x⁵ + x⁴ + x at a | 8 / 5 / 4 | budget |
| x⁴ + x³ + x² + x at a | 10 / 6 / 5 | budget |

Base at k=2 and k=3: budget-exceeded on all ten at both 400k and 800k.

Seven of the ten are the strong form at k=1 — the search completed depth 12 and no path
exists. Three are the weak form — 800k nodes was not enough to finish depth 12, so "no
path ≤ 12" is not proven for them, only "not found." At k=2,3 all ten are the weak form.
Both forms satisfy the gate as written ("the base exhausts"); the distinction is recorded
so the next reader does not have to rediscover it.

**Gate item 1 passes.** Ten problems where the base cannot finish and the derivative
finishes in 2–12 steps, stable across closure=1,2,3 and across a doubled node budget.
Gate item 2 — the Lean `ring` spike — has not been done and Track 1 is not started.

**What it cost us.** *Ten reached by extension, not by the first grid.* **Forfeit:** the
number the gate asked for was hit on the second try, after extending in the direction
the first try pointed. The extension was committed before running and every bin is
reported, but "we kept going until we had ten" is a sentence a reviewer can write, and
this line is where they get to write it. *Three weak-form rows.* **Forfeit:** on those,
someone with a bigger machine can, in principle, find a base path ≤ 12 and remove them.
Seven would remain.
