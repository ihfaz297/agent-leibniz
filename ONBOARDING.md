# Onboarding

For someone who just got handed this repo and wants to do work in it today.
No maths background assumed beyond "I know what a derivative is."

Two documents outrank this one: **CLAUDE.md** is the plan, **LEDGER.md** is the
record of every run and what each decision cost. This file is the map. If it ever
disagrees with those two, they win and this file is stale — say so and fix it.

---

## 1. What we are actually doing

**The idea in one sentence.** Give a system a maths toolkit that stops just short
of calculus, hand it problems that calculus makes easy, and see whether inventing
a calculus-shaped tool measurably pays off.

**The idea in one paragraph.** A concept like the derivative does not let you
prove anything you could not prove before — you can find a tangent slope with
nothing but algebra, painfully. What it does is make the painful thing cheap. So
instead of arguing about whether a system "really understood" anything, we measure
the cheapness: how much work does a problem take without the concept, and with it?
If the second number is much smaller on problems the concept was never tuned
against, the concept earned its place.

**The thing we are NOT claiming.** We are not claiming an AI discovers calculus.
Any model smart enough to propose anything has read every calculus textbook ever
written. Say this out loud early and often — it is the first objection anyone
raises, and conceding it up front is what makes everything else defensible. What
we are building is the measuring instrument, plus the controls that tell us how
much of any result is just the model remembering.

**Why anyone should care.** There is a ladder: solve a problem, discover a
theorem, discover a *concept*, discover a theory. Rungs 1 and 2 have plenty of
work on them — Lean provers, AlphaProof, FunSearch. Rung 3 is basically empty.
Nobody has convincingly shown a system inventing a reusable abstraction and then
compounding on it. We are building the bench you would need to test that, using
calculus as the known-answer case to calibrate against.

---

## 2. The state of things, honestly

Read this before you get either excited or disappointed.

| piece | state |
|---|---|
| Track 0 engine, verifier, search | **done**, 25 tests |
| Training bank (5) and held-out bank (8, frozen) | **done** |
| Boundary bank (24 problems, pre-registered) | **done**, raw JSON in `results/` |
| Proposer loop: soundness, scoring, triage | **done**, 12 tests |
| Obfuscation arms 1 and 2 | **done**, 24 tests |
| Model adapter (DeepSeek or any OpenAI-shaped endpoint) | **done**, needs a key to run |
| Lean spike, gate item 2 base side | **done**, compiles, axioms clean |
| Gate item 1 | **PASSED** |
| Gate item 2 | **specified, not evaluated** -- see §9 |
| Lean abstraction side | **never measured** -- the real blocker |
| Δ base (finite differences) | **not started** -- blocks arms 3 and 4 |
| Any result from an actual model | **none. Zero. Not one call has been made.** |

**What works.** The engine has produced real numbers. There are ten problems where
the no-derivative search cannot finish and the derivative finishes in a handful of
steps. That held when we changed the accounting three different ways and when we
doubled the compute budget.

**What broke along the way, and this is the important part.** Our original metric was
"count the steps with and without the derivative; the difference is the payoff." That
number turned out to be mostly an artefact of how finely we chopped the rewrite rules.
Chop them differently and the difference nearly vanishes — on some problems it went
*negative*, meaning the derivative was worse than plain algebra. The headline numbers
from our first run are not trustworthy and the ledger says so at length.

What survived is coarser and more honest: **can the no-derivative search finish at
all?** That is a yes/no per problem and it does not care how the rules are chopped.

**The second thing that broke, and it is worse.** An abstraction with a one-character
error in its power rule scores *identically* to the correct one — same problems
finished, same savings — while getting 22 answers wrong. Run
`python propose.py c002_bad_power` and watch it. Cost alone cannot tell a real
abstraction from a plausible lie. That is why there are two independent referees and
why neither may be removed.

**There is still no proposer, and this matters more than anything above.** The *bench*
is built: `propose.py` scores and triages, `proposer.py` will call a model and write
the result out, `obfuscate.py` builds the controlled prompt. But every candidate in
`candidates/` was written by hand, and **no model has ever been called.** Do not let
anyone — including us — describe this as an AI discovering anything yet. What exists is
the apparatus, and apparatus that has never met real data usually has bugs in it.

**Three claims in this repo were retracted after being made.** The ledger keeps them
visible rather than editing them away: a gate verdict that was goalpost-moving, an
overclaim that a finite-difference target would catch contamination cleanly, and a
claim that the adapter could handle real model output when it could not. If you catch a
fourth, that is the most useful thing you can do this week.

**The failure mode we are most likely to die of** is not maths, it is drift: four
people, several AI chat sessions, and a new plan every week. Hence the rule in
CLAUDE.md — CLAUDE.md is the plan, LEDGER.md is the record, everything else is a chat
log. If a plan lives only in a chat window, it is not the plan.

---

## 3. Repo map

### The engine (Track 0) — Python, standard library only

| file | what it is |
|---|---|
| `terms.py` | The data structure. An expression is a tree: `Const`, `Var`, `Add`, `Mul`, `Pow`, plus three special nodes — `Slope` (the problem), `D` (a derivative), `At` (evaluate at a point). Also the tree utilities: walk positions, substitute, replace. |
| `canon.py` | Tidies an expression into one standard shape after every edit — flattens nesting, sorts, folds numbers, cancels `h·h⁻¹`. **This is free and does not count as work.** Read its header. The line between "free" and "counted" is the most load-bearing design choice in the project. |
| `rules.py` | The two toolkits. `R1`–`R8` are the pre-calculus base: distribute, expand a power, collect like terms, substitute, form a difference quotient, set h to 0. `D1`–`D5` plus `B` are the derivative: constant, variable, sum, product, power, and the bridge rule saying "a slope is a derivative evaluated at a point." |
| `search.py` | Finds the shortest sequence of rule applications from problem to answer. Iterative deepening, cap of 12 steps, budget of 400k nodes. Has a `closure=k` option — see §5. **The number this file produces is the whole instrument.** |
| `verify.py` | The independent referee. Plugs random exact fractions into both sides of every rule and every step of every answer. Separately recovers polynomial coefficients by interpolation and differentiates them — a code path sharing nothing with `rules.py`, so it can catch `rules.py` being wrong. |
| `experiment.py` | The five training problems and the driver that runs three configurations. |
| `heldout.py` | Eight problems, **frozen**. Written before any candidate was tested against them. Append-only, and every append gets a ledger line. |
| `boundary.py` | 24 problems chosen by a grid and committed before being run. This is the bank the Lean gate rests on. |
| `propose.py` | **The proposer loop.** Takes a candidate abstraction, checks it is sound, scores it on training, scores it on held-out, and sorts it into exactly one bucket. Run `python propose.py --list` then `python propose.py c001_derivative`. |
| `candidates/` | One module per candidate abstraction. `c001` is the real derivative — the contamination ceiling. `c002` and `c003` are permanent fixtures that must both be rejected: one is unsound, one is sound but useless. |
| `obfuscate.py` | **The contamination control.** Builds the proposer's entire prompt for one arm. `plain` keeps real names and calculus words (the ceiling); `renamed` renames the operators, numbers the rules by position, and describes each rule **only by a worked example** — a rule called "distribute" leaks its own semantics. Checks its own output for leaked target vocabulary and refuses the arm if it finds any. Try `python obfuscate.py renamed`. |
| `proposer.py` | **The model adapter.** Builds the prompt, calls an OpenAI-shaped endpoint over stdlib `urllib` (DeepSeek by default), extracts the fenced module, audits it, writes it to `candidates/` with the exact prompt beside it. It scores nothing — generation and judgement stay in separate processes on purpose. `--dry-run` needs no key. |
| `opaque_ops.py` | Neutral re-exports, so a renamed prompt can say what to import without naming the target. `from terms import Slope` leaked the answer in the import line; this exists because the vocabulary checker caught that. |
| `test_track0.py` | 25 tests. Run them before writing a ledger entry. |
| `test_propose.py` | 12 tests for the loop's two referees and its triage. |
| `test_proposer.py` | 24 tests: the arms, extraction, the audit, the review gate, and ten adversarial cases for malformed model output. |
| `results/` | Raw JSON from every run. |

### Documents

| file | what it is |
|---|---|
| `CLAUDE.md` | The plan and the hard rules. Doubles as instructions for AI assistants working in the repo. |
| `LEDGER.md` | Append-only. One entry per cycle: what we tried, what happened, **what it cost us**. That third thing is the point — every design choice gives something up, and we write the sacrifice down while making it, not months later. This file becomes the paper's limitations section. |
| `ONBOARDING.md` | This file. |
| `NEXT.md` | What to do next, and which parts cost money (almost none of it does). Read after this. |
| `track1/` | The Lean spike. Not Track 1 yet. |
| `FIRST_MISSIONS.txt.txt` | The original two-week plan. Partly superseded, but useful for its instinct about which task can return an answer you do not want. |
| `schizophrenic-conversations.txt` | The design conversation the project came out of. Long, but every constraint in CLAUDE.md traces back to it. Worth an hour. |
| `graveyard/` | Quarantined documents, each with a header saying why. Currently one: an AI-generated "plan" involving quantum computing with no falsifiable mechanism in it. Kept as a specimen of the exact failure mode this project studies. Do not build on anything in here. |

---

## 4. Setup

### Python side — five minutes

Python 3.11. No packages, no virtualenv.

```bash
python test_track0.py           # 25 tests, about 5 seconds
python experiment.py            # the training table
python experiment.py --paths    # same, but prints every rewrite step
python boundary.py --jobs 11    # the big run, about 5 minutes on 12 cores
```

Start with `--paths`. Watching a 12-step algebra grind next to a 4-step
derivative proof is the fastest way to understand what this project measures.

### Lean side — an hour, mostly waiting

Only needed for Track 1 and the gate spike. You do not need Lean to work on the
Python side.

**Install, Windows:**

```powershell
Invoke-WebRequest -Uri "https://github.com/leanprover/elan/releases/latest/download/elan-x86_64-pc-windows-msvc.zip" -OutFile "$env:TEMP\elan.zip"
Expand-Archive "$env:TEMP\elan.zip" -DestinationPath "$env:TEMP\elan" -Force
& "$env:TEMP\elan\elan-init.exe" -y --default-toolchain stable
# restart the shell, or for this session:
$env:Path = "$env:USERPROFILE\.elan\bin;$env:Path"
```

**Install, macOS or Linux:**

```bash
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
source ~/.elan/env
```

**Then make a project that has Mathlib in it:**

```bash
lake new spike math      # the 'math' template pulls Mathlib and picks the toolchain
cd spike
lake exe cache get       # THE IMPORTANT ONE. Downloads prebuilt Mathlib, several GB.
lake build
```

### Lean tips, each of which will save you a day

- **`lake exe cache get` is not optional.** Without it `lake build` compiles
  Mathlib from source — hours, and it may simply fall over. If a build looks like
  it is compiling half of mathematics, you skipped this.
- **Never pin a toolchain version by hand.** Let the `math` template choose, then
  record what worked. Guessing version numbers is the classic way to spend a day
  on imports instead of maths.
- **`elan` manages versions, `lake` manages projects.** If you know Rust: elan is
  rustup, lake is cargo.
- **Use VS Code with the "Lean 4" extension.** The editor *is* the interface — you
  put the cursor in a proof and it shows you the remaining goal. Using Lean from a
  plain terminal is doing it on hard mode.
- **`sorry` is a legal placeholder.** It compiles with a warning and means "I will
  prove this later." Use it freely while drafting; never let one reach a
  measurement.
- **`#print axioms myTheorem`** lists what a proof actually depends on. Our rule
  is that it must show nothing but Lean's three built-ins. This is how you catch a
  proof that quietly assumed the thing it was proving — which matters here,
  because Lean checks that proofs follow from assumptions and never checks that
  the assumptions are true.
- **Do not `import Mathlib` whole** unless you enjoy waiting. Import the specific
  modules.

---

## 5. Two ideas you need before the ledger makes sense

**"Closure", or: how coarsely do we count?** A step is one rule application. But
is `D(5x) → 5·D(x)` one step or two? It is two of our rules chained, and any
textbook treats it as one move. So `search(closure=k)` lets up to `k` rules
chained *inside the piece the previous rule just produced* count as a single step,
applied to both toolkits equally. We ran k=1, 2, 3. The per-problem differences
largely dissolved; "can it finish at all" did not. Every number we quote now says
which k it came from.

**Why we do not just tune things until the numbers look good.** Because we could,
trivially, and the result would be worthless. Hence: held-out problems are written
before anything is tested on them and are never edited to be "more
representative"; caps and budgets are never raised because a problem hit one (a
problem that runs out of room is a *result*); the base toolkit is never improved
to make problems easier, because the difficulty **is** the experiment. When we
came close to breaking one of these — extending the problem grid after seeing a
disappointing count — we committed the extension before running it and wrote a
paragraph in the ledger explaining why a critic might call it tuning anyway.

---

## 6. What we build next: the proposer

Everything so far is us hand-writing both toolkits. The actual research question needs
a *proposer* — something that invents the second toolkit itself. The design is
deliberately boring, copied from FunSearch rather than from reinforcement learning.

**Steps 1 through 5 below are all built as of 2026-09-27.** What is missing is a key and
somebody to run it. See §7.

```
   1. PROPOSE
      A model sees the base toolkit and problems it cannot solve.
      It emits a candidate: a new operator plus rules for it.
      Nothing else.  No prose, no solving.
                    |
                    v
   2. CHECK SOUNDNESS            verify.py  (later: Lean)
      Random exact-rational testing of every proposed rule,
      then the independent oracle.
      Unsound -> quarantine.  Do not delete.
                    |
                    v
   3. SCORE USEFULNESS           search.py + experiment.py
      Does it let the search finish problems the base cannot?
      Scored on TRAINING problems only.
                    |
                    v
   4. TRANSFER                   heldout.py + boundary.py
      Re-score on problems it was never selected against.
      THIS IS THE ONLY NUMBER THAT MATTERS.
      Everything above is bookkeeping.
                    |
                    v
   5. TRIAGE - exactly one bucket, no exceptions
      Kept         sound, and helps on held-out
      Quarantined  unsound, or helps on training only
      Fatal        the setup broke, not the candidate
                   -> go back and redesign the base
```

Three rules for this loop that are not up for discussion:

**Soundness and usefulness need separate referees.** A checker can tell you a rule
is valid. It can never tell you a rule is *useful*. Given only a soundness check,
a generator produces infinite valid garbage. This is exactly how Lenat's AM died
in the 1970s, and you will be asked about it, so read Ritchie and Hanna's critique
before you need to.

We have now measured how badly you need both, and it is worse than expected.
`candidates/c002_bad_power.py` is the derivative with one character wrong in the power
rule. It gets 22 answers wrong. Its step counts are **identical** to the correct
version's — same problems solved, same savings. Score on cost alone and you keep the
lie. Run `python propose.py c002_bad_power` and watch it happen.

**Propose and exploit are separate calls.** Never let one generation both invent a
rule and use it to solve a problem. That is how you get a system that quietly
assumes what it is proving.

**The proposer may define, never assume.** If it is ever allowed to postulate a
new axiom rather than construct something from what exists, the verifier stops
verifying: Lean will happily accept an inconsistent assumption and then "prove"
every remaining problem from it, and your dashboard shows 100%. If we ever do want
postulation, the price of entry is supplying a model — in Lean, a `class` plus an
`instance`, where the instance *is* the consistency proof.

And the control that makes any of it meaningful: **the rename test.** Strip every
calculus word from the prompt, rename `Slope` and `D` to meaningless symbols,
rerun. If performance collapses, the model was recalling rather than searching,
and we learned that in an afternoon instead of at a demo. If it survives, we have
real signal. Either outcome is publishable, which is what makes it a good
experiment.

Explicitly **not** doing, and please do not propose them: population search, MCTS,
reinforcement learning, quantum anything. Those are v2, and v2 exists only if v1
runs. The file in `graveyard/` is what happens when this rule is not followed.

---

## 7. Where you can actively contribute

Claimable tasks. Each says what skill it needs, roughly how long, and what it unblocks.
Put your name against one in your team channel so two people do not do the same thing,
and **put a line in `LEDGER.md` when it produces a number.**

### Needs nothing but Python — start here

**A. The Δ base.** *Biggest item. A few days. Blocks arms 3 and 4, which are the only
controls that test whether the proposer needs the target to be FAMILIAR rather than
merely named.* Swap the target from the derivative to the finite difference operator
`Δf(n) = f(n+1) − f(n)`, with sum-of-powers problems (`Σk`, `Σk²`, `Σk³`). Full design,
including the three rules that keep it honest, is in `NEXT.md` §1.

One genuine design decision needs settling first and it is not a coding question: **what
route does the base get to a closed-form sum?** Give it general telescoping and you have
handed over half the target. Give it nothing and the problems are unsolvable rather than
painful. Argue it out with a second person before writing code, and write the argument
into the ledger.

**B. Feed the adapter a real reply and fix what breaks.** *Half a day. Needs a key — or
someone else's saved reply.* `proposer.py --from-file` replays a saved response, so this
can be done with one call's output shared around. Everything in the pipeline was built
against *imagined* messy output; contact will find failure modes we did not think of. The
ledger says so explicitly. This is the highest value-per-hour task in the repo.

**C. The numeric-point finding.** *An hour.* Every problem evaluated at a literal number
(`x³ at −2`) is cheap because `canon` folds constants for free; every boundary problem is
at a symbolic point. Four for four. Make it explicit in the bank-design rules so a future
bank does not spend cells rediscovering it.

**D. A second problem type in the current base.** *A day.* Extrema — `show f(x) ≥ f(1)`
for x ≥ 0 — are statable in the base and want a different abstraction. Check the four
questions in CLAUDE.md before adding anything, and grid the bank rather than hand-picking.

### Needs Lean

**E. The abstraction side of gate item 2.** *The real blocker on Track 1. Days.* Build a
hand-rolled polynomial derivative in Lean with its lemmas, and prove the tangent-slope
statements with it. `Polynomial.derivative` is banned, like `Mathlib.Analysis.*`. Until
this exists we have half a comparison and no gap. Note honestly that **doing this is most
of a Track 1 prototype** — the gate cannot be checked cheaply.

**F. Shorten `derive_quintic_cofactor_unknown`.** *An afternoon.* It is 23 tactics for
the proof we happened to find, not a minimum. A shorter one moves the 12→23 ratio. The
robust claim is the *n−1 substitutions* law; the counts are soft.

**G. CI for the Lean spike.** *A day, mostly waiting.* Nothing in the repo currently
reproduces the Lean result without redoing the multi-GB Mathlib download by hand. Pin
Lean `v4.34.1` and mathlib `d13f23b` — both recorded in `track1/README.md`.

### Needs judgement rather than typing — and these are not junior tasks

**H. Adversarially review the problem phrasings.** Question 2 of the four in CLAUDE.md:
could a reader reconstruct the target from the wording alone? Whoever wrote a bank cannot
audit their own blind spot, and this is exactly what cost BACON its credibility. Bring
fresh eyes to `experiment.py`, `heldout.py` and `boundary.py`.

**I. Hunt for a fourth retraction.** Three claims in this repo were made and then walked
back; they are all still visible in the ledger. Read it bottom-up looking for a fourth.
Specifically worth doubting: the ten boundary problems rest on a mechanical search budget,
and three of the ten are the weak form of the claim (budget exhausted, not proved
impossible). Anyone with a bigger machine could remove those three.

**J. Confirm or veto the open gate sub-decision.** See §9.

### Do not do these

Raise the depth cap or node budget. "Improve" the base rules. Edit `heldout.py`. Add a
dependency without asking. Population search, MCTS, or RL — those are v2, and v2 exists
only if v1 runs. `graveyard/` holds what happens when that rule is ignored.

---

## 8. Your first afternoon

1. `python test_track0.py && python test_propose.py && python test_proposer.py` — 61
   tests, about 10 seconds.
2. `python experiment.py --paths --only "x^2 at a"` — read the two proofs side by side.
   That is the whole project on one screen.
3. `python propose.py --all` — watch the loop keep the real derivative, reject an
   unsound abstraction, and reject a sound useless one. Three verdicts, three reasons.
4. `python propose.py c002_bad_power` and compare its step counts to `c001`'s. They are
   identical, and `c002` gets 22 answers wrong. That is why there are two referees.
5. `python obfuscate.py renamed` — the prompt a model actually gets, with the vocabulary
   stripped. Ask yourself whether *you* could tell what the target is. (Look at `r7`.
   That is the honest limit of this arm, and it is written up in §6.)
6. Read `LEDGER.md` **from the bottom up**. Recent entries hold the real findings; the
   first entry's headline numbers are the ones we later showed to be artefacts.
7. Read the "Non-negotiable constraints" section of `CLAUDE.md`. Four items, each there
   because breaking it silently invalidates a result.
8. Claim something from §7. Put a line in the ledger when it produces a number.

---

## 9. The gate, and the one decision still open

Track 1 (Lean) is gated on two conditions in `CLAUDE.md`. **Item 1 has passed.** Item 2
is fully specified and **not yet evaluated**; the blocker is task E in §7.

Item 2 was rewritten on 2026-09-27 after its first wording turned out to be unanswerable
— it asked whether the base could be proved "with `ring`" without saying *which
statement*, and the answer is 1 tactic, 6 tactics, or 12→23 depending on the form. An
earlier version of this repo called that a conditional pass. That was goalpost-moving and
the ledger retracts it. **If you take one methodological lesson from this project, take
that one: the wording goes in before the measurement, or the measurement means nothing.**

One sub-decision is settled but worth a second opinion, and anyone can reopen it: what
"the base cannot prove it" *means*. Lean has no exhaustive search, so "we did not find a
proof" is not a result and a clever enough person always rescues the base. The rule
adopted: the base may instantiate at up to k points, `ring_nf`, make one automation call,
and derive **at most one** intermediate lemma. More than one and it has failed. Under that
rule the quadratic passes (needs one) and degree 5 fails (needs four).

The threshold "at most one" is still a number somebody picked. A degree-3 or degree-4
problem needing two lemmas sits on the wrong side of a line drawn without measuring those
degrees. If the bank grows to include them, **revisit the line before running, not after.**

---

Then read `NEXT.md` for the zero-budget plan and the Δ design.

If something in here is wrong, fix it and push. A stale manual is worse than none.
