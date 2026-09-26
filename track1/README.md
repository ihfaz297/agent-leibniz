# Track 1 spike — gate item 2

Not Track 1. One afternoon's measurement that decides whether Track 1 gets built.
CLAUDE.md, "Gate to Track 1", item 2.

## Why the gate question splits in two

The gate asks whether `ring` makes the Lean base trivial. Writing the statements
out shows that depends entirely on *which statement*:

- **A — verify.** The answer is supplied; Lean checks a polynomial identity.
  `ring` closes it. Should not grow with degree — `ring` normalizes, it does not
  search.
- **C — derive.** The answer is not supplied. From "the difference has a double
  root at a", recover m and c. Should grow with degree, because you instantiate
  at enough points to pin the coefficients and the system grows.
- **D — with the abstraction.** m = f'(a), one lemma. Should not grow.

So the only comparison that means anything is **C against D**, not A against
anything. And `ring` is not a threat to C, because `ring` cannot do C at all —
it does not solve for coefficients sitting in metavariable position.

## Setup

```bash
lake new spike math          # pulls Mathlib, picks the toolchain itself
cp RingSpike.lean spike/Spike/
cd spike && lake exe cache get && lake build
```

`lake new ... math` rather than a checked-in lakefile on purpose: pinning
versions from a machine that cannot compile them is how you lose a day to
imports. Let Mathlib choose, then record what worked.

The generated `spike/` tree is gitignored. Only `RingSpike.lean` and this file
are tracked.

## What to record

| cell | statement | tactics | notes |
|---|---|---|---|
| `verify_quadratic` | A, degree 2 | | |
| `verify_quintic` | A, degree 5 | | |
| `exists_tangent_quadratic` | B, witnesses given | | |
| `derive_quadratic` | C, degree 2 | | |
| `derive_quintic` | C, degree 5 | | |
| `derive_quadratic_no_cofactor` | C′, cofactor quantified away | | starts as `sorry` |
| `dmono_two` / `dmono_five` | D, the abstraction | | |

Also record, for every theorem: `#print axioms` shows nothing but Lean's three
built-ins. Anything else means the proof assumed something.

## How to read the result

- **A is one tactic at both degrees** (predicted). Then on A-style statements the
  Track 0 boundary-bank result does not transfer, and any Lean measurement built
  on A-style statements is measuring Mathlib's normalizer. Do not build Track 1
  on A.
- **C's degree-5 cost is much larger than its degree-2 cost** (predicted). Then
  the base difficulty in Lean is real and grows, the boundary-bank result *does*
  transfer in spirit, and Track 1 should sit on C-style statements. `ring` need
  not be banned.
- **C is flat, or nearly** — then the Lean base is not a grind at all and the
  gate fails on that instead. This is the outcome that stops Track 1.
- **C′ is far harder than C.** C hands over the cofactor, which is most of the
  answer. If C′ is much worse, C understates the base cost and C′ is the real
  baseline. It ships as `sorry` deliberately: closing it is the first genuine
  Track 1 task, and how hard that turns out to be is itself a measurement.

Banning `ring` would be banning an algorithm rather than an axiom. Decide whether
that is defensible *before* building anything — and note that if the verdict is
"Track 1 sits on C", the question may not arise.
