/-
Gate item 2: the `ring` spike.  CLAUDE.md, "Gate to Track 1".

UNTESTED.  Written on a machine with no Lean toolchain (2026-09-26).  Expect to
fix syntax on first compile; the *design* is the deliverable, not the syntax.

The question the gate asks is "if the base proof is one tactic, Track 1 as
designed measures Mathlib's normalizer, not the abstraction."  Working through
it produced a sharper question, which is what this file is arranged around:

    the difficulty is not in the proof, it is in the STATEMENT.

Formulation A supplies the answer and asks Lean to check it.  That is a ring
identity and `ring` closes it, at every degree, in one tactic.  Formulation C
supplies no answer and asks for the slope.  Nothing in the base finds it.
Track 1 measures something only if it sits on C, and C is not a proof-length
problem at all.

Run each section, record: tactic count, `count_heartbeats` output, and for C
which tactics were tried and what they did.  Then fill the table in
track1/README.md and put it in LEDGER.md.
-/

import Mathlib.Tactic.Ring
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.Polyrith
import Mathlib.Util.CountHeartbeats

/-! ## A — answer supplied.  Prediction: one tactic, every degree. -/

count_heartbeats in
theorem tangent_A_quadratic (a x : ℚ) :
    x ^ 2 - (2 * a * x + -a ^ 2) = (x - a) ^ 2 := by
  ring

/- The same at degree 5 -- one of the ten boundary-bank problems where the
   Track 0 base search cannot finish at all.  If this is also one tactic, the
   boundary-bank result does NOT transfer to Lean: `ring` is polynomial
   normalization and its cost does not grow the way BFS over rewrite rules
   does.  That is the prediction this line tests, and it is the single most
   important cell in the spike. -/
count_heartbeats in
theorem tangent_A_quintic (a x : ℚ) :
    x ^ 5 - (5 * a ^ 4 * x + -4 * a ^ 5) = (x - a) ^ 2 * (x ^ 3 + 2 * a * x ^ 2 + 3 * a ^ 2 * x + 4 * a ^ 3) := by
  ring

/-! ## B — existential, witnesses supplied by the author.

This is what an agent that already knows the answer emits.  The witnesses ARE
the answer; `ring` only checks them. -/

count_heartbeats in
theorem tangent_B_quadratic (a : ℚ) :
    ∃ m c : ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 :=
  ⟨2 * a, -a ^ 2, fun _ => by ring⟩

/-! ## C — existential, witnesses NOT supplied.  The real base problem.

Try each of these and record what happens.  Expected: all fail, because none
of them solve for a metavariable in a coefficient position.  If any succeeds,
Track 1 has a very different shape than planned. -/

-- C1: can `ring` close a goal with metavariables in it?  (Prediction: no.)
-- theorem tangent_C1 (a : ℚ) :
--     ∃ m c : ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 := by
--   refine ⟨?m, ?c, fun x => ?_⟩
--   ring

-- C2: polyrith / linear_combination, which do search over coefficients.
-- theorem tangent_C2 (a : ℚ) :
--     ∃ m c : ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 := by
--   polyrith

-- C3: the honest base grind -- match coefficients by hand.  THIS is the thing
-- whose length should be compared against a derivative-based proof.  Write it
-- out, count the tactics, and that number is the Track 1 base cost.
-- theorem tangent_C3 (a : ℚ) :
--     ∃ m c : ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 := by
--   sorry

/-! ## Axiom hygiene.  Every theorem above must depend on nothing but Lean's
three built-ins.  CI rule from the August design notes. -/

#print axioms tangent_A_quadratic
#print axioms tangent_A_quintic
#print axioms tangent_B_quadratic
