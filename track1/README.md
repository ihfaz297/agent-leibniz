# Track 1 spike — gate item 2

Not Track 1. One afternoon's measurement that decides whether Track 1 gets built.
CLAUDE.md, "Gate to Track 1", item 2.

## Setup (no toolchain in this repo yet)

```
lake new track1spike math      # pulls Mathlib and pins the toolchain itself
cp RingSpike.lean track1spike/Track1spike/
cd track1spike && lake exe cache get && lake build
```

`lake new ... math` is used rather than a checked-in `lakefile` + `lean-toolchain`
on purpose: pinning versions from a machine that cannot compile them is how you
spend a day on imports. Let Mathlib choose, then pin what worked.

## What to record

| cell | statement | tactics | heartbeats | outcome |
|---|---|---|---|---|
| A quadratic | answer supplied, degree 2 | | | |
| A quintic | answer supplied, degree 5 | | | |
| B quadratic | existential, witnesses given | | | |
| C1 | `refine ⟨?m, ?c, _⟩; ring` | | | |
| C2 | `polyrith` | | | |
| C3 | coefficient matching by hand | | | |

## How to read the result

- **A quintic is one tactic** (predicted). Then the Track 0 boundary-bank result
  does not transfer: `ring` normalizes polynomials and does not care about the
  degree the way BFS over rewrite rules does. The ten boundary rows buy nothing
  in Lean, and a Lean base measured on A-style statements is trivially strong at
  every degree. This is the outcome that fails the gate.
- **C1 and C2 fail** (predicted). Then the base difficulty in Lean is real, but
  it lives in *finding* the coefficients, not in proving an identity — so Track 1
  must be built on C-style statements, and its metric cannot be proof length of
  a supplied answer.
- **C3's tactic count** is the only number that can honestly be compared against
  a derivative-based proof. If C3 is short, the base is not a grind and the gate
  fails on that instead.

Banning `ring` is banning an algorithm, not an axiom. Decide whether that is
defensible *before* building anything — and note that if the verdict is
"Track 1 must sit on C-style statements", banning `ring` may not even be
necessary, because `ring` cannot do C.
