# What to do next

Written 2026-09-27, at the point where the API budget ran out. Everything here is
either free or costs disk space. Read `ONBOARDING.md` first for the map.

---

## State of play, three lines

The instrument works and is tested. Four real findings are in `LEDGER.md`, two of
which killed metrics we had been relying on. **No agent has ever proposed anything**
— every abstraction in `candidates/` was hand-written, so there is currently zero
evidence about discovery, only evidence that the bench works.

---

## The one thing that needs a human, not code

**Gate item 2 in `CLAUDE.md` is underspecified and has to be rewritten by a person.**
It says "proved by the base with `ring`" without naming *which statement*, and the
answer depends entirely on that — 1 tactic, 6 tactics, or 12→23 depending on the form
(table in CLAUDE.md). An earlier version of this repo called that a conditional pass;
that was goalpost-moving and has been retracted in the ledger.

Rewrite the item to name the statement form, **commit that wording before measuring
anything again**, and Track 1 is cleared or not on its own terms. Do not skip the
commit-first step; the whole reason this project has any credibility is that it has
been done that way twice and the one time it wasn't got retracted.

---

## Free work, in order of value

### 1. The Δ base — the experiment that actually discriminates

This is the highest-value thing in the repo that needs neither money nor Lean, and
it is what makes a contamination control possible at all.

Swap the target from the derivative to the **finite difference** operator:

    Δf(n) = f(n+1) − f(n)

It is elementary, it is squarely pre-calculus, and it has a property that makes it a
near-perfect trap for a model that is retrieving rather than deriving:

| rule | the truth | what a model reciting calculus emits |
|---|---|---|
| product | **Δ(fg) = fΔg + gΔf + ΔfΔg** | `fΔg + gΔf` — drops a term |
| power | **Δ(n²) = 2n + 1** | `2n` |
| power, general | `Δ(n⁽ᵏ⁾) = k·n⁽ᵏ⁻¹⁾` on **falling factorials** `n⁽ᵏ⁾ = n(n−1)…(n−k+1)` | `k·n^(k−1)` on ordinary powers |
| sum | `Δ(f+g) = Δf + Δg` | same — this one transfers, which is why it is not a discriminator |

So contamination does not fail vaguely. It fails in a **specific, predictable,
machine-detectable** way, and `verify.py` already catches exactly that class of error
with no new code — random exact rationals will find `Δ(fg) ≠ fΔg + gΔf` immediately.

Three-way outcome, all three publishable:
- proposes correct Δ-rules → evidence of derivation
- proposes the calculus rules, verifier rejects them → retrieval, caught red-handed
- proposes nothing usable → the proposer is too weak, which is also worth knowing

It also upgrades the target. Finite differences is not one definition — it is an
operator, a telescoping theorem (`Σ_{k=a}^{b−1} Δf(k) = f(b) − f(a)`, the discrete
fundamental theorem), and falling factorials as the natural basis. A hit there is a hit
on "found a small framework", not "guessed an object."

**Problems for the Δ bank:** closed forms for `Σk`, `Σk²`, `Σk³`. The base can verify a
closed form by induction if handed one; *finding* it is the hard part, and telescoping
turns it into a procedure. Check all four questions in CLAUDE.md before adding any.

**Implementation sketch.** New operator node alongside `Slope`/`D` in `terms.py`; new
base rules for shifting and summing; the Δ rules as a candidate module in `candidates/`.
Write the Δ held-out bank *before* any candidate exists, the way `heldout.py` was done.

### 2. A local proposer — this is free and I was wrong to imply otherwise

A local open-weights model via `ollama` costs nothing but disk. It is weaker and just
as contaminated as a frontier model, **and that does not matter**, because the controls
do the work, not the model's ignorance. You cannot make a model forget calculus; you
can make the task unrecognisable.

Three arms, escalating:

1. **Plain.** Rules named as they are, calculus words present. This is the ceiling, and
   `candidates/c001_derivative.py` already establishes it by hand: Kept, finishes two
   held-out problems the base cannot.
2. **Renamed.** Same mathematics, meaningless symbols, no calculus vocabulary anywhere
   in the prompt. One afternoon. If it still works, the model is matching structure
   rather than keywords — interesting, not conclusive.
3. **Δ, disguised.** The trap above. This is the only arm that separates search from
   recall.

Caveat on using a weak local model: if it fails arm 3, you cannot tell "too dumb" from
"was only ever retrieving." So a *failure* on a local model is uninformative, while a
*pass* is a strong result. Plan for that asymmetry rather than being surprised by it.

`propose.py` takes any candidate module, so the only new code is the bit that turns
model output into a module — and remember the provenance dict is enforced, not advisory:
a candidate whose proposer saw `heldout.py` is refused before scoring.

### 3. Small, genuinely useful, an hour each

- **Make the numeric-point finding explicit.** Every problem evaluated at a literal
  number is cheap, because `canon` folds constants for free; every boundary problem is
  at a symbolic point. Four for four. A future bank should state that up front instead
  of spending cells rediscovering it.
- **Close `derive_quintic_cofactor_unknown` more tidily.** The 23 tactics is the count
  for the proof that was found, not a minimum. A shorter one moves the 12→23 ratio, and
  the robust claim is the *n−1 substitutions* law, not the counts.
- **Add a CI job for the Lean spike.** Currently nothing in the repo reproduces the Lean
  result without redoing the multi-GB Mathlib download by hand.

---

## What costs money, and what it buys

Only one thing: a frontier model as the proposer, via API. It buys a stronger arm 3 —
a pass there means much more than a pass from a local 7B, and a failure is actually
interpretable. Everything else on this page is free.

If you do get budget, the order does not change: **build the Δ base first.** A proposer
pointed at the un-disguised task can only ever reproduce the contamination ceiling,
which `c001` already measured by hand for free.
