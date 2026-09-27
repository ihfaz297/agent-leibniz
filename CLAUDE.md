# Abstraction discovery project

## What this is

Testing whether an agent, working in a formal theory missing a concept, can construct
that concept itself. Test case: pre-calculus base theory, derivative as the target.

We are NOT claiming the agent discovers calculus. Any model capable enough to propose
anything has read every calculus textbook. What we are building is a way to measure
whether a proposed abstraction actually pays off, and controls that tell us how much
of any result is contamination.

## Two tracks

**Track 0** (Python, current focus). Term-rewriting engine. Measures BFS step count to
find a tangent slope, with and without derivative rules available. Validates the metric
before we commit to Lean.

**Track 1** (Lean 4, later). Same measurement, real proofs, real verifier.

Track 0 is not a toy version of Track 1. It is the instrument calibration. If the
compression gap does not appear in Track 0, Track 1 is not worth building.

**Gate to Track 1 (2026-09-12).** The step-count gap appeared and then dissolved under
re-factoring (LEDGER.md). Track 1 is not started until both of these are in the ledger:

1. *Boundary bank.* Ten or more problems, chosen by grid, where the base exhausts and the
   derivative finishes -- and the boundary holds at `closure=1,2,3` and under a changed
   node budget. If the boundary moves with the accounting, there is no metric, and Lean
   will not supply one.
2. *Lean discriminates.* Stated generally, demonstrated on one named target and form.
   **Rewritten 2026-09-27 by the project owner** after the first wording proved
   unanswerable; see LEDGER.md for the retraction. Wording committed before any further
   measurement.

   **Condition (target-agnostic).** There exist **N >= 5** problems on which, within one
   fixed budget applied identically to both sides, the **base cannot prove the statement
   and the abstraction can.** Pass/fail, not proof length: Track 0 established that step
   *count* is an artefact of rule factoring, and Lean's analogue -- tactic count is partly
   a fact about how `ring_nf` and `linarith` normalize -- is the same trap differently
   shaped. Do not restate this gate in terms of proof length.

   **Demonstrated on.** Tangent slope to a polynomial over Q, stated in the
   **cofactor-value-withheld** form: the cofactor's *degree* is given, its *coefficients*
   are existentials. Named explicitly so it cannot be re-chosen after a disappointing
   result -- that is exactly how the first wording failed. The other two forms are
   disqualified and stay disqualified: verify-a-supplied-answer is 1 tactic (`ring`) at
   any degree, and cofactor-handed-over is 6 at any degree. Both measure Mathlib.

   **The abstraction side.** A polynomial derivative **defined from the base by hand**.
   `Mathlib.Analysis.*` is banned as always, and so is `Polynomial.derivative` -- it
   arrives with its own proved lemmas, which is importing the answer together with its
   support library. How much work the hand-rolled version costs is itself informative.

   **What "the base cannot prove it" means -- SETTLED 2026-09-27 by the owner.** In
   Track 0 "the base cannot" is honest because an exhaustive mechanical search over a
   fixed rule set exhausted a stated budget. Lean has no such search: a human writes the
   proof, so "we did not find one" is not a result, and without a restriction a
   sufficiently clever human always rescues the base and the gate can never return "no".

   The base is therefore allowed: instantiation of the hypothesis at up to k points,
   `ring_nf`, one automation call (`linarith` / `nlinarith`), and **at most ONE
   hand-derived intermediate lemma.** More than one, and the base has failed.

   This admits genuine ingenuity -- one clever step is exactly what a competent
   mathematician would reach for -- while staying falsifiable, and it lets the n-1 growth
   law do the discriminating rather than an arbitrary prohibition. Against the measured
   spike it already separates the degrees: the quadratic form needs one such lemma
   (`k = 1`) and **passes**; the degree-5 form needs four (`k3 = 1`, `k2 = 2a`,
   `k1 = 3a^2`, `k0 = 4a^3`) and **fails**, with `nlinarith` over eight instantiations
   also failing to close it. A flat ban on hand-derived lemmas was considered and
   rejected as rigged against the base.

   **Known gap, must be closed before the gate is evaluated.** The abstraction side has
   never been measured. `dmono_two` / `dmono_five` in the spike are stubs that
   differentiate a monomial; they are not a tangent-slope proof via the abstraction. The
   base side is measured; there is currently no gap, only half a comparison.

If either item fails, Track 1 is not built. That is a semester saved, not a project lost.

**Item 1: PASSED** -- ten boundary problems, stable across `closure=1,2,3` and a doubled
node budget. **Item 2: NOT YET EVALUATED** under this wording. What is measured so far is
the base side only, in the named form: 12 tactics at degree 2, 23 at degree 5, with a
structural growth law of n-1 hand-derived lemmas for degree n, and automation alone
failing at degree 5. Track 1 is **not cleared.**

## Track 0 layout

```
terms.py       Const, Var, Add, Mul, Pow as a tagged union
canon.py       flatten Add/Mul to sorted n-ary multisets; canonicalize after every rewrite
rules.py       base rules R1-R8 (the power law went into canon); derivative D1-D5 + bridge B
search.py      iterative deepening, depth cap 12, node budget 400k, returns step count;
               `closure=k` lets k rules chained *inside one produced subterm* count as
               one step -- the symmetric "derived lemma is one step" accounting
verify.py      sample ~100 random rational instantiations, compare both sides exactly
experiment.py  the training problems and the three-configuration driver
heldout.py     the held-out set, FROZEN 2026-09-12; append-only, every append ledgered
propose.py     the proposer loop: soundness -> training -> held-out -> triage.
               A candidate is a module in candidates/ with a PROVENANCE dict; one
               that saw heldout.py is refused, not warned
candidates/    candidate abstractions, one module each.  c001 is the contamination
               ceiling (the real derivative); c002 and c003 are fixtures that must
               be Quarantined, one unsound and one sound-but-useless
test_track0.py 25 tests; run before every ledger entry
obfuscate.py   the contamination control: builds the proposer's prompt for one arm.
               plain = real names (the ceiling); renamed = opaque symbols, rules
               numbered by position, every rule described ONLY by example.  Checks
               its own output for leaked target vocabulary and refuses if it finds any
proposer.py    model -> candidate module.  stdlib urllib, DeepSeek by default.  Writes
               the candidate UNREVIEWED; propose.py refuses to score it until a human
               reads the file and sets REVIEWED = True
opaque_ops.py  neutral re-exports so a prompt can say what to import without naming
               the target (`from terms import Slope` leaked the answer in the import)
test_propose.py 12 tests for the loop's referees and triage
test_proposer.py 24 tests for the arms, extraction, the audit and the review gate
check_claims.py every capability this file CLAIMS, paired with a grep that must find it
               in the code.  Exists because this file promised a library of kept
               abstractions for a month and no library was ever written.  CI runs it
graveyard/     quarantined plans and documents, each with a header saying why
track1/        the Lean spike.  RingSpike.lean is byte-identical to the file that
               compiled; README.md holds the results table AND THE VERSION PIN --
               Lean v4.34.1, mathlib d13f23b (2026-09-24).  Pin those on any rebuild:
               `lake new spike math` on a later date pulls current mathlib and the
               file will not necessarily compile (one deprecation already surfaced).
               The generated spike/ tree is gitignored and was deleted 2026-09-27 to
               reclaim 6.6 GB; nothing unique was in it, but rebuilding means
               redownloading mathlib (hours on a slow link).
```

**What Track 0 found (2026-09-12, see LEDGER.md).** The per-problem step-count gap is a
rule-granularity artefact: under `closure=2` or `3` it is within ±1 on everything below
degree 3, and no gap anywhere exceeds 2. The measurement that survives re-factoring is
*whether the base can finish at all*. Any new number quoted from Track 0 says which
`closure` it was computed under, and any new problem bank is built around the base's
completion boundary, not around gaps between two searches that both complete.

**And step count cannot stand alone (2026-09-27).** An abstraction with a one-character
error in its power rule scores *identically* to the correct one -- same problems
finished, same gaps -- while getting 22 answers wrong. Soundness and usefulness are two
separate referees and neither substitutes for the other. `candidates/c002_bad_power.py`
and `c003_additive_only.py` are kept in the repo permanently as the two failure
directions.

## Non-negotiable constraints

- **Exact rationals only.** `fractions.Fraction`. Never floats. Float error in a
  verifier that judges by numerical equality is a silent, miserable bug class.
- **AC normalization is free, not searched.** If associativity and commutativity are
  searchable rules, BFS dies at depth 4 and even the good path gets buried. Path length
  counts only the real rules.
- **Validate on `x^2` before the cubic.** The cubic base path will probably time out
  rather than complete. That is the result we want, but we need one completing run first
  or we cannot distinguish "base is hard" from "base rules are incomplete."
- **Held-out problems are written before any agent output is seen.** Never edit the
  held-out set to be "more representative." Never raise the depth cap or node budget
  because a row exhausted it -- an exhausted row is a result.

## Designing a NEW base: the freeze, and how to know when you are done

"Do not improve the base rule set" protects a base that has already been measured
against. A base that does not exist yet has to be *designed*, and designing means
iterating -- the current base ended up with eight rules rather than the nine this file
originally sketched, and the power law moved into `canon`. That was legitimate. So the
rule needs a second half, and this is it.

**The line is the freeze, not the editing.**

- *Before the freeze:* iterate on the base freely. Argue each choice in `LEDGER.md`. The
  only legitimate reason to add a base rule is that without it a problem is **impossible
  or unstatable** rather than merely painful.
- *The freeze:* commit the base rules **and** the held-out bank, before any candidate has
  been scored against held-out.
- *After the freeze:* frozen. The red-flag sentence is "the base cannot solve X, let us
  add a rule." Before the freeze that is design. After it, that is the violation this
  file exists to prevent.

**Stopping criterion, so "done" is a check and not a feeling.** The base must solve the
easiest problem in the class *painfully* and fail the hardest one. For the Delta base
that is:

> grinds `sum k`, fails `sum k^3`

Too thin if it cannot do `sum k` at all -- then the problems are impossible rather than
hard, and nothing has been built. Too thick if `sum k^3` falls out easily -- then the
target has been handed over. This is question 1 below, applied to the base design instead
of to a problem.

**Three tests for any proposed base rule.**

1. **True?** `verify.py` says so, by random exact-rational instantiation.
2. **Pre-calculus?** Would a textbook state it before introducing the target?
3. **Does it leave the target derivable but not given?** If a competent reader could read
   the target off the base rules, the base is too thick.

**The specific trap for the Delta base: telescoping.** The discrete fundamental theorem
(`sum of Delta f telescopes to f(b) - f(a)`) is *half the abstraction*. Give the base
general telescoping and the target is gone. Give it no cancellation at all and `sum k^3`
is unreachable, so the problems fail question 1. The needle: the base may collapse **one
concrete difference** by writing the terms out -- which is what a pre-calculus student
actually does -- while the general operator and the telescoping theorem stay as the
target. That mirrors how `R7`/`R8` split from `D1`-`D5`.

## Problem bank: four questions per problem

Ask these before adding anything to the bank.

1. Can the base solve it, painfully? (Not trivially, not never.)
2. Does the phrasing give away the target? (No "as h shrinks", no "approaches",
   no "instantaneous". Test is whether a reader could reconstruct the derivative from
   the wording alone.)
3. Is the answer machine-checkable without human judgement?
4. Does it share an abstraction with at least three other problems?

## Triage: every candidate lands in exactly one bucket

- **Kept** — verifier accepted, and it helps on held-out problems it was never selected
  against. **NOTE (2026-09-27): there is no library.** An earlier version of this line
  promised that a Kept candidate "goes into the library so the next abstraction can build
  on it". No such mechanism exists -- `propose.py` scores every candidate against
  `BASE_RULES` alone, never against the base plus previously-kept abstractions. So this
  project is currently **single-step only**. See "One abstraction at a time" below.
- **Quarantined** — interesting but unsound, or compressed on training and not held-out.
  Do not delete. This is where the historically interesting cases live.
- **Fatal** — the failure was structural, not about this candidate. Base theory made
  problems unstatable, or the metric could not discriminate. Goes back to base design.

## One abstraction at a time, and one abstraction SHAPE

Two limits on what this project can currently claim. Both were found by a question from
the owner rather than by us, and both bound what a *success* would mean -- not just what a
failure would mean.

**1. Single-step only. There is no library.** `propose.py` scores a candidate against the
base. It cannot score a candidate against the base *plus* an abstraction already Kept, so
it cannot detect an abstraction whose payoff depends on an earlier one existing. That is
the difference between "discover a concept" and "discover a theory", and it is the
mechanism DreamCoder -- the lineage this project claims -- is entirely built around.

The fix is cheap in code and premature in science: scoring against `BASE_RULES + kept`
is a few lines, but it means nothing until there are two genuinely proposed abstractions
to compound, and there is currently one Kept candidate and it is the contamination
ceiling. **Two-step compounding is the right v2 target**, and it is stronger than "more
problems" -- nobody has demonstrated it.

What is NOT on any roadmap: anything of the shape of Wiles on Fermat. That is decades of
human theory-building across several fields. Saying otherwise is how a project gets
dismissed in the first paragraph.

**2. We test exactly one abstraction shape.** Both targets -- `d/dx` and the Delta
operator -- are the same move: *introduce a small or discrete increment, then take a limit
or a sum.* Leibniz's `dx`, Riemann's sums, and Planck's `epsilon = h nu` are all that move;
Planck's was explicitly a counting device in an entropy sum that turned out to be physical.

Historically that shape is the productive one, so testing it is not arbitrary. But it is
**one** shape. Galois theory, homology, and anything category-shaped do not look like it.
So if the loop succeeds here, what has been shown is that it can find abstractions *of
this shape* -- and a reader is entitled to ask whether the loop would find any other kind.
We do not know, and the honest answer in a paper is that we did not test it.

## Ledger

`LEDGER.md`, append-only, one entry per cycle:

```
Date | what we tried | what happened | what it cost us
```

The fourth column is the one that matters. Every design choice forfeits something.
Write the forfeit down while making the choice, not four months later. This file
becomes the limitations section.

## Which documents are real

CLAUDE.md is the plan. LEDGER.md is the record. Everything else -- chat logs, generated
"system prompts", design conversations -- is input, and gets triaged like a candidate:
kept (folded into one of the two files above), quarantined (`graveyard/`, with a header),
or ignored. A plan that lives only in a chat log is not the plan.

## Working style

- Do not add dependencies without asking. Track 0 is stdlib plus maybe sympy for
  cross-checking.
- Do not "improve" the base rule set to make problems easier. The difficulty is the
  experiment.
- When a run produces a number, write it in the ledger before moving on.
- If asked to expand scope (population search, MCTS, RL), say no and point here.
  Those are v2 and v2 only exists if v1 runs.