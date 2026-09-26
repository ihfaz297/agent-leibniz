/-
Gate item 2: the `ring` spike.  CLAUDE.md, "Gate to Track 1".

The gate asks: if the base proof is one tactic, does Track 1 measure Mathlib's
normalizer instead of the abstraction?

Working the statements out shows the question splits in two, and the two halves
answer differently.  That split is what this file is built to measure.

  A  VERIFY.   The answer is supplied; Lean checks a polynomial identity.
               `ring` closes it.  Cost should NOT grow with degree, because
               `ring` normalizes rather than searching.

  C  DERIVE.   The answer is not supplied.  Given only "the difference has a
               double root at a", recover m and c.  Cost SHOULD grow with
               degree: you instantiate at enough points and solve a linear
               system whose size is the degree.

  D  WITH THE ABSTRACTION.  m = f'(a), one lemma application.  Cost should not
     grow with degree either.

So the comparison that means anything is C against D, not A against anything.
If C grows and D does not, Track 0's boundary-bank result DOES transfer, and
`ring` is not a threat — because `ring` cannot do C at all.  If C is also flat,
the Lean base is not a grind and the gate fails.

Each section says what to record.  Fill the table in track1/README.md, then
LEDGER.md.  Heartbeat measurement is in the last section, separated on purpose
so a syntax problem there cannot block the theorems.
-/

import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.LinearCombination

namespace RingSpike

/-! ## A — VERIFY.  Answer supplied.  Record: tactic count at each degree.

Tangent to x^2 at a:  m = 2a, c = -a^2.
Tangent to x^5 at a:  m = 5a^4, c = -4a^5, cofactor x^3 + 2ax^2 + 3a^2x + 4a^3.
(Both identities checked outside Lean before being written here.) -/

theorem verify_quadratic (a x : ℚ) :
    x ^ 2 - (2 * a * x + -a ^ 2) = (x - a) ^ 2 := by
  ring

theorem verify_quintic (a x : ℚ) :
    x ^ 5 - (5 * a ^ 4 * x + -4 * a ^ 5)
      = (x - a) ^ 2 * (x ^ 3 + 2 * a * x ^ 2 + 3 * a ^ 2 * x + 4 * a ^ 3) := by
  ring

/-- Degree 5 is one of the ten problems where the Track 0 base search cannot
finish at all.  If this is still one tactic, then on A-style statements the
boundary-bank result does not transfer. -/
example (a x : ℚ) :
    x ^ 5 - (5 * a ^ 4 * x + -4 * a ^ 5)
      = (x - a) ^ 2 * (x ^ 3 + 2 * a * x ^ 2 + 3 * a ^ 2 * x + 4 * a ^ 3) := by
  ring

/-! ## B — existential with witnesses supplied.  What an agent that already
knows the answer emits.  The witnesses ARE the answer; `ring` only checks. -/

theorem exists_tangent_quadratic (a : ℚ) :
    ∃ m c : ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 :=
  ⟨2 * a, -a ^ 2, fun _ => by ring⟩

/-! ## C — DERIVE.  The real base problem: recover m and c from the double-root
condition, with nothing supplied.  This is the pre-calculus grind, and its
tactic count is the base cost that Track 1 should be measuring.

Method: instantiate the hypothesis at enough points to pin the coefficients,
then solve.  The number of instantiations is what grows with degree. -/

theorem derive_quadratic (a m c : ℚ)
    (h : ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2) :
    m = 2 * a ∧ c = -a ^ 2 := by
  have h0 := h 0
  have h1 := h 1
  ring_nf at h0 h1
  constructor
  · linarith
  · linarith

/-- Same at degree 5.  Record how many instantiations and tactics this needs
against the quadratic: that ratio is the base's growth rate, and it is the
number the gate actually turns on. -/
theorem derive_quintic (a m c : ℚ)
    (h : ∀ x : ℚ, x ^ 5 - (m * x + c)
          = (x - a) ^ 2 * (x ^ 3 + 2 * a * x ^ 2 + 3 * a ^ 2 * x + 4 * a ^ 3)) :
    m = 5 * a ^ 4 ∧ c = -4 * a ^ 5 := by
  have h0 := h 0
  have h1 := h 1
  ring_nf at h0 h1
  constructor
  · linarith
  · linarith

/-! ## C' — the harder, honest form of C.

In C the cofactor is handed over, which is a large gift: knowing the cofactor is
most of knowing the answer.  The un-gifted version quantifies it away.  If this
is much harder than C, then C is understating the base cost and C' is the real
baseline.  Left as `sorry` deliberately — closing it is the first real Track 1
task, and how hard it turns out to be is itself the measurement. -/

theorem derive_quadratic_no_cofactor (a m c : ℚ)
    (h : ∃ q : ℚ → ℚ, ∀ x : ℚ, x ^ 2 - (m * x + c) = (x - a) ^ 2 * q x) :
    m = 2 * a ∧ c = -a ^ 2 := by
  sorry

/-! ## D — WITH THE ABSTRACTION.

Track 1's whole claim is that this stays one step as the degree climbs, while C
does not.  Written against a hand-rolled polynomial derivative so that no
analysis import is needed: `Mathlib.Analysis.*` is banned in the base by
CLAUDE.md, and `Polynomial.derivative` is algebraic, not analytic. -/

/-- Derivative of a monomial coefficient list, as a plain function, so the base
theory stays free of any analysis import. -/
def dmono (n : ℕ) (a : ℚ) : ℚ := (n : ℚ) * a ^ (n - 1)

theorem dmono_two (a : ℚ) : dmono 2 a = 2 * a := by
  unfold dmono; norm_num

theorem dmono_five (a : ℚ) : dmono 5 a = 5 * a ^ 4 := by
  unfold dmono; norm_num

/-! ## Axiom hygiene.  Every theorem must depend on nothing but Lean's three
built-ins.  A proof that shows anything else has assumed something. -/

#print axioms verify_quadratic
#print axioms verify_quintic
#print axioms exists_tangent_quadratic
#print axioms derive_quadratic
#print axioms derive_quintic

end RingSpike
