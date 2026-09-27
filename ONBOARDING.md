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

## 7. Pick a task

Three rules for all of them: **claim it in the team channel first**; run
`python test_track0.py && python test_propose.py && python test_proposer.py` before and
after; **add one line to `LEDGER.md` when you get a number.**

Ordered easiest first.

---

### 1. Write down the numeric-point rule - 1 hour, no key, no Lean

A problem evaluated at a literal number is cheap, because `canon.py` folds constants for
free. A problem at a symbolic point is not.

- **See it first:** `python experiment.py`. Compare `x^3 at -2` (9 steps) against
  `x^3 at a` (10). All four literal-point problems in the banks grind; all ten boundary
  problems are at symbolic points.
- **Edit:** `CLAUDE.md`, section "Problem bank: four questions". Add a fifth question:
  *is the evaluation point symbolic?* If not, the base will probably grind it and the
  problem cannot discriminate.
- **Done when:** the fifth question is in `CLAUDE.md` and one line is in `LEDGER.md`.

---

### 2. Feed the adapter a real model reply - half a day, needs one API call

Everything in `proposer.py` was built against *invented* messy output. No real reply has
ever gone through it. Highest value-per-hour job in the repo.

- **You do not need your own key.** Anyone with one runs
  `python proposer.py --arm renamed --model deepseek-chat` once and shares the raw reply
  text. Then: `python proposer.py --arm renamed --from-file reply.txt`
- **Edit:** `proposer.py` (`extract_module`, `audit`) and `propose.py` (`smoke_test`).
- **The rule:** fix the *pipeline*, never the generated file. Hand-editing a model's
  Python to make it load means you are measuring your own editing.
- **Done when:** the generated candidate loads under `python propose.py <name>` with no
  hand-editing, and every new failure mode you hit has a test in `test_proposer.py`.

---

### 3. Shorten the quintic Lean proof - an afternoon, needs Lean

`derive_quintic_cofactor_unknown` takes 23 tactics. That is the proof we happened to
find, not a minimum.

- **Setup:** rebuild Mathlib, pinning Lean `v4.34.1` and mathlib `d13f23b` - both in
  `track1/README.md`. Hours of download, then minutes of work.
- **Edit:** `track1/RingSpike.lean`.
- **Done when:** it compiles with fewer tactics, `#print axioms` still shows only
  `propext, Classical.choice, Quot.sound`, and the table in `track1/README.md` is updated.
- **Note:** the robust claim is the *n-1 substitutions* law, not the count. A shorter
  proof should move the count and not the law. If it moves the law, that is a far more
  interesting result - say so loudly.

---

### 4. Add extrema as a second problem type - 1 to 2 days, no key, no Lean

Everything is currently "slope of a polynomial at a point". Extrema use the same base and
want the same abstraction, which tests whether the instrument generalises at all.

- **Problem shape:** show `f(x) >= f(c)` for `x >= 0`. For example `x^3 - 3x >= -2` on
  `x >= 0`, which factors as `(x-1)^2 (x+2) >= 0`.
- **Edit:** `terms.py` (a new goal node beside `Slope`), `rules.py` (base rules to reach
  it), and a new bank file modelled on `heldout.py`.
- **Before writing the bank:** answer the four questions in `CLAUDE.md` for each problem,
  and **grid it** (degree x terms x coefficient type) rather than hand-picking, the way
  `boundary.py` does.
- **Done when:** the base grinds some and fails others, `c001_derivative` helps on them,
  and all 61 tests still pass.

---

### 5. The Delta base - several days, no key, no Lean. THE BIG ONE.

Swap the target from the derivative to `D f(n) = f(n+1) - f(n)`, with sum problems
(`sum k`, `sum k^2`, `sum k^3`). This unblocks arms 3 and 4, the only controls that test
whether a model needs the target to be *familiar* rather than merely *named*. Full design
in `NEXT.md` section 1.

- **Settle this with a second person before writing code:** *what route does the base get
  to a closed-form sum?* Give it general telescoping and you have handed over half the
  target. Give it nothing and the problems become impossible rather than painful. The
  likely answer is a single-instance cancellation rule - the base can collapse one
  concrete difference by writing the terms out - with the general operator and the
  telescoping theorem left as the target. That mirrors how `R7`/`R8` split from
  `D1`-`D5`. **Put the argument in `LEDGER.md` before the code.**
- **Three rules that keep it honest** (also in `NEXT.md`): the Delta rules never go into
  the base; the oracle computes sums numerically so it cannot leak them; grid the bank.
- **Edit:** `terms.py`, `canon.py`, `rules.py`, plus new `delta_experiment.py` and
  `delta_heldout.py`.
- **Done when:** the base grinds `sum k` and fails `sum k^3`, a hand-written Delta
  candidate in `candidates/` is Kept, and `obfuscate.py` has a third arm.

---

### 6. The Lean abstraction side - days, needs Lean. THE GATE BLOCKER.

We measured how hard the *base* finds these problems. We never measured the abstraction.
So there is half a comparison, no gap, and gate item 2 cannot be evaluated.

- **Edit:** `track1/RingSpike.lean`. Define a polynomial derivative **by hand**, on
  coefficient lists, the way `dmono` begins to. `Polynomial.derivative` is banned, like
  `Mathlib.Analysis.*`, because it arrives with its own proved lemmas.
- **Prove with it:** the tangent-slope statements in the cofactor-value-withheld form, at
  several degrees.
- **Done when:** five problems exist where the base fails under the section 9 rule (more
  than one hand-derived lemma) and the abstraction succeeds - and `CLAUDE.md`'s gate
  status stops saying "not yet evaluated".
- **Know before starting:** this is most of a Track 1 prototype. The gate cannot be
  checked cheaply.

---

### If you would rather read than code

- **Review the problem wordings.** Question 2 in `CLAUDE.md`: could a reader reconstruct
  the target from the phrasing alone? Read `experiment.py`, `heldout.py`, `boundary.py`.
  Whoever wrote them cannot audit their own blind spot, and this is what cost BACON its
  credibility.
- **Look for a fourth retraction.** Three claims here were made and walked back, all
  still in `LEDGER.md`. Best place to dig: three of the ten boundary problems are the
  *weak* form, where the search ran out of budget rather than proving no path exists.
  Someone with a bigger machine could delete those three.
- **Second-opinion the open gate rule** in section 9.

---

### Do not

Raise the depth cap or node budget. "Improve" the base rules. Edit `heldout.py`. Add a
dependency without asking. Build population search, MCTS or RL - those are v2, and v2
exists only if v1 runs. See `graveyard/` for what ignoring that looks like.

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
8. Claim a task from §7 — task 1 takes an hour and is a real contribution.

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
