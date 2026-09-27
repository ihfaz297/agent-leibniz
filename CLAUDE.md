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

   **What "the base cannot prove it" means -- OPEN, decided by Claude, owner to confirm
   or veto.** In Track 0 "the base cannot" is honest because an exhaustive mechanical
   search over a fixed rule set exhausted a stated budget. Lean has no such search: a
   human writes the proof, so "we did not find one" is not a result. To make base failure
   falsifiable, the base is restricted to a **stated mechanical script**: instantiate the
   hypothesis at up to k points, `ring_nf`, then a single automation call (`linarith` or
   `nlinarith`) -- and **no target-specific hand-derived intermediate lemmas.** Under that
   restriction the existing spike already shows a base failure: `nlinarith` with eight
   instantiations does not close the degree-5 form, and the 23-tactic proof that does
   close it works only because it supplies four hand-derived lemmas (`k3 = 1`, `k2 = 2a`,
   ...) and solves triangularly. Without this restriction the gate is unfalsifiable; with
   it, a cleverer human is not allowed to rescue the base. If the owner rejects the
   restriction, the gate needs a different notion of base failure before it can be used.

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
test_propose.py 12 tests for the loop's referees and triage
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

## Problem bank: four questions per problem

Ask these before adding anything to the bank.

1. Can the base solve it, painfully? (Not trivially, not never.)
2. Does the phrasing give away the target? (No "as h shrinks", no "approaches",
   no "instantaneous". Test is whether a reader could reconstruct the derivative from
   the wording alone.)
3. Is the answer machine-checkable without human judgement?
4. Does it share an abstraction with at least three other problems?

## Triage: every candidate lands in exactly one bucket

- **Kept** — verifier accepted, held-out step count dropped. Goes into the library so
  the next abstraction can build on it.
- **Quarantined** — interesting but unsound, or compressed on training and not held-out.
  Do not delete. This is where the historically interesting cases live.
- **Fatal** — the failure was structural, not about this candidate. Base theory made
  problems unstatable, or the metric could not discriminate. Goes back to base design.

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