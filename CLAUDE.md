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
2. *`ring` spike.* One tangent-slope problem stated in Lean and proved by the base with
   `ring`. If that is one tactic, the Lean base is not a painful grind, and Track 1 as
   designed measures Mathlib's normalizer, not the abstraction. Banning `ring` is banning
   an algorithm, not an axiom; decide whether that is defensible before building anything.

If either fails, Track 1 is not built. That is a semester saved, not a project lost.

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
test_track0.py 25 tests; run before every ledger entry
graveyard/     quarantined plans and documents, each with a header saying why
```

**What Track 0 found (2026-09-12, see LEDGER.md).** The per-problem step-count gap is a
rule-granularity artefact: under `closure=2` or `3` it is within ±1 on everything below
degree 3, and no gap anywhere exceeds 2. The measurement that survives re-factoring is
*whether the base can finish at all*. Any new number quoted from Track 0 says which
`closure` it was computed under, and any new problem bank is built around the base's
completion boundary, not around gaps between two searches that both complete.

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