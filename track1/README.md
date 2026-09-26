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

## RESULT (2026-09-27) — measured, compiles, axioms clean

Lean 4.34.1 + Mathlib. `lake env lean Spike/RingSpike.lean` exits 0, no `sorry`, every
theorem depends on exactly `[propext, Classical.choice, Quot.sound]`. Raw output:
`results/ring-spike-output.txt`.

| theorem | form | supplied | tactics |
|---|---|---|---|
| `verify_quadratic` | A | the answer | **1** (`ring`) |
| `verify_quintic` | A | the answer | **1** (`ring`) |
| `exists_tangent_quadratic` | B | witnesses | 1 (`ring`, term mode) |
| `derive_quadratic` | C | the cofactor | **6** |
| `derive_quintic` | C | the cofactor | **6** |
| `derive_quadratic_cofactor_unknown` | C′ | only its degree | **12** |
| `derive_quintic_cofactor_unknown` | C′ | only its degree | **23** |
| `no_cofactor_function_form_is_false` | — | proves the naive form FALSE | 8 |

**Verdict: the gate passes, conditionally.** A and C are flat in degree — build on those
and you measure Mathlib's normalizer, which is exactly what the gate was watching for.
C′ grows, and for a structural reason: no linear tactic can close it, because the
hypotheses are linear in atoms like `a * k3` while the goal needs `a ^ 4`, which appears
in none of them. The cofactor coefficients must be solved triangularly, one substitution
each, so degree n costs n − 1 substitutions. `ring` need not be banned — it cannot do C′.

**The sharpest finding is not a count.** `∃ q : ℚ → ℚ` is the obvious way to withhold the
cofactor, and it makes the statement **false**: at x = a the equation becomes `0 = 0 * q a`,
pinning q nowhere, so q can be built pointwise for any m. This shipped as a `sorry`
believing it merely unproven. Its negation is now a theorem. The double-root condition
needs q *polynomial*; as a function it is vacuous.

**Caveat to carry into Track 1.** `ring_nf` and `linarith` do the real work in C′, so 23
is partly a fact about Mathlib's tactics — the Lean analogue of the rule-factoring problem
that ate Track 0's first metric. Quote the growth law (n − 1 substitutions), not the
tactic counts.

---

## Reproducing

```bash
lake new spike math
cp RingSpike.lean spike/Spike/
cd spike && lake exe cache get && lake env lean Spike/RingSpike.lean
```

Budget hours for `cache get`: it is several GB. On a slow link it dominates
everything else, and a power cut mid-write leaves zero-filled files that look the
right size — check one with `head -c 40 lakefile.toml` before trusting the tree.

## How to read the result

- **A is one tactic at both degrees** — CONFIRMED. So on A-style statements the
  Track 0 boundary-bank result does not transfer, and any Lean measurement built
  on A-style statements is measuring Mathlib's normalizer. Do not build Track 1
  on A.
- **C's degree-5 cost is much larger than its degree-2 cost** — WRONG for C (flat at 6), RIGHT for C′ (12 → 23). Where it holds,
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
