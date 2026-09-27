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

```
lake new spike math          # pulls Mathlib, picks the toolchain itself
cp RingSpike.lean spike/Spike/
cd spike
lake exe cache get
lake build
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

## Exact versions that produced the result above

Pin these. `lake new spike math` on a later date pulls current Mathlib, and this file
will not necessarily compile against it -- one deprecation (`if_neg`) already surfaced
during development.

```
leanprover/lean4:v4.34.1
mathlib  d13f23b723b8a846827a245b89c10fc7d3f11612   (2026-09-24)
```

To pin, after `lake new spike math`, edit the mathlib `[[require]]` in `lakefile.toml` to
add `rev = "d13f23b723b8a846827a245b89c10fc7d3f11612"`, set `lean-toolchain` to
`leanprover/lean4:v4.34.1`, then run `lake update` followed by `lake exe cache get`.

`track1/RingSpike.lean` as committed is byte-identical to the file that compiled, so
the generated `spike/` tree holds nothing unique and can be deleted to reclaim ~6.6 GB.
What the tree costs to rebuild is the Mathlib download, not any lost work.

## Reproducing

```
lake new spike math
cp RingSpike.lean spike/Spike/
cd spike
lake exe cache get
lake env lean Spike/RingSpike.lean
```

Budget hours for `cache get`: it is several GB. On a slow link it dominates
everything else, and a power cut mid-write leaves zero-filled files that look the
right size — check one with `head -c 40 lakefile.toml` before trusting the tree.

## How the predictions landed

Written before the run, resolved after it. Kept visible because a prediction that is
quietly deleted when it misses is worth nothing.

- **"A is one tactic at both degrees."** CONFIRMED. `ring` closes the verify form at
  degree 2 and degree 5 alike. So a Lean measurement built on A-style statements measures
  Mathlib's normalizer. Do not build Track 1 on A.
- **"Withholding the cofactor makes it grow."** WRONG as first written, RIGHT as
  corrected. C — which hands the cofactor over — is flat at 6 tactics for both degrees.
  Only C′, which withholds the cofactor's value and fixes only its degree, grows: 12 → 23.
  The morning's prediction did not distinguish these and was therefore right about the
  direction and wrong about the statement.
- **"C′ is merely unproven."** WRONG, and this was the useful mistake. The first C′
  statement quantified the cofactor as a *function*, `∃ q : ℚ → ℚ`, and that statement is
  **false** — at x = a it degenerates to `0 = 0 * q a`, so q is pinned nowhere. It shipped
  as a `sorry`. Its negation is now a theorem in the file. The lesson generalises past
  this project: when the cost of a statement is the thing being measured, the statement
  has to be checked for truth before its proof is worth timing.

Banning `ring` turned out to be a non-question: `ring` cannot do C′ at all.
