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

## The gate -- rewritten, and what is still open

**Gate item 2 was rewritten on 2026-09-27** by the project owner and committed before any
further measurement (LEDGER.md). It now reads: N >= 5 problems where, within one budget
applied to both sides, the base *cannot prove* the statement and the abstraction can --
pass/fail, never proof length -- demonstrated on tangent slope in the
cofactor-value-withheld form, with the abstraction being a hand-rolled polynomial
derivative (`Polynomial.derivative` banned, like `Mathlib.Analysis.*`).

**One thing remains.**

1. *Nothing. The gate is fully settled* -- including what "the base cannot prove it"
   means: the base may instantiate at up to k points, `ring_nf`, make one automation call,
   and derive **at most one** intermediate lemma. More than one and it has failed. Under
   that rule the measured spike already separates the degrees: the quadratic needs one
   (`k = 1`) and passes, degree 5 needs four and fails.
2. *The one real blocker: the abstraction side has never been measured.* The base side is done; `dmono_two` and
   `dmono_five` in the spike are monomial stubs, not tangent-slope proofs. So there is half
   a comparison and no gap. Closing it means building a hand-rolled polynomial derivative
   in Lean with its lemmas -- which is most of a Track 1 prototype. **Evaluating the gate
   now costs about as much as building the thing it gates.** Worth knowing before anyone
   starts.

## Free work, in order of value

**Δ first, then a key.** Arms 1 and 2 are runnable today on a key alone (§2). Arms 3 and
4 -- the ones that test whether the proposer needs the target to be familiar rather than
merely named -- need the Δ base, and that is §1.

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

`verify.py` catches that class of error with no new code — random exact rationals find
`Δ(fg) ≠ fΔg + gΔf` immediately.

**Do not oversell this, as an earlier draft of this file did.** Finite differences is
standard discrete-maths material. `Δ(fg) = fΔg + gΔf + ΔfΔg` and falling factorials are
in any textbook that covers the subject, so a competent model asked about Δ will often
simply know them. The table above catches a *careless* retrieval, not retrieval as such.
Δ is **less** contaminated than d/dx; it is not clean.

Three-way outcome, all three publishable — but read the caveat above first:
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
base rules for shifting an index and summing a range; the Δ rules as a candidate module
in `candidates/`.

Three rules for building it, and they are the whole reason it stays honest:
- **The Δ rules never go into the base.** They are the target. The base gets arithmetic,
  shifting, summing — the given toolkit, which nobody discovers.
- **The oracle must not use them either.** To check `Σk³` it computes the sum numerically
  for specific `n`. That is independent of any Δ rule, so there is no leak through the
  verifier.
- **Build the bank from a mechanical grid, not by hand.** Whoever writes it already knows
  the target and cannot audit their own phrasing for smuggling — that is what killed
  BACON's credibility. Grid it, commit it, and have a second person check question 2 in
  CLAUDE.md before anything is scored against it.

### 2. Run arms 1 and 2 -- this needs ONLY a key now

Built and tested as of 2026-09-27. Nothing else is required:

```bash
python obfuscate.py renamed          # read the prompt the model will get; no key needed
python proposer.py --arm plain    --dry-run
export LEIBNIZ_API_KEY=sk-...
python proposer.py --arm plain    --model deepseek-chat
python proposer.py --arm renamed  --model deepseek-chat
# read each generated file IN FULL, then set REVIEWED = True in it
python propose.py m001_plain_deepseek_chat
python propose.py m002_renamed_deepseek_chat
```

`--from-file` replays a saved reply, so develop against a canned one before spending a
call. DeepSeek is the default because it is cheap enough to sample many proposals, which
is what a FunSearch-style loop wants; `--base-url` points it anywhere OpenAI-shaped.

**What arms 1 and 2 measure, and what they do not.** Arm 1 is the ceiling: real names,
calculus vocabulary present. Arm 2 is the same mathematics with the vocabulary stripped --
operators renamed, rules numbered by position, and each rule described only by a worked
example rather than an English name. The difference between the two is whether the
proposer needed the *words*.

It is **not** whether the proposer needed the target to be *familiar*. Rule `r7` is the
base's own route to a GOAL term, and its demonstration shows a difference quotient, which
is recognisable on sight whatever it is called. Withholding it would misrepresent the
system. So a pass on arm 2 is real but limited, and arms 3 and 4 -- which need the Delta
base -- are what test familiarity.

**Malformed output is refused with a reason, not crashed on.** `ast.parse` at write time;
then a smoke test firing every rule at every position of 300 random terms, catching
`RULES` of the wrong type or empty, bare functions instead of `Rule` objects, wrong arity,
rules that raise, rules returning `None` or a bare term. The search and the soundness
referee are both guarded too, so a shape the smoke test misses becomes a verdict rather
than a traceback. Ten adversarial tests cover one failure mode each.

Refusals name the fix, so feed it back into the next prompt rather than hand-repairing the
module -- a pipeline that silently fixes model output is measuring the pipeline.

**The review gate is not optional.** A machine-written candidate arrives with
`REVIEWED = False` and `propose.py` refuses to score it, because scoring imports and
executes the module. Read the file. There is an import allowlist and a static audit, and
neither is a substitute for reading it.

### 3. Small, genuinely useful, an hour each

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
