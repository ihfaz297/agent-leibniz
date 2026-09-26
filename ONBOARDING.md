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

**What works.** Track 0, the Python engine, is built, tested, and has produced
real numbers. There are ten problems where the no-derivative search cannot finish
and the derivative finishes in a handful of steps. That result held when we
changed the accounting three different ways and when we doubled the compute
budget.

**What broke along the way, and this is the important part.** Our original metric
was "count the steps with and without the derivative; the difference is the
payoff." That number turned out to be mostly an artefact of how finely we chopped
the rewrite rules. Chop them differently and the difference nearly vanishes — on
some problems it went *negative*, meaning the derivative was worse than plain
algebra. So the headline numbers from our first run are not trustworthy, and the
ledger says so at length.

What survived is coarser and more honest: **can the no-derivative search finish at
all?** That is a yes/no per problem and it does not care how the rules are
chopped.

**What is unproven.** The Lean side, Track 1, has not started. There is a gate in
CLAUDE.md with two conditions; one has passed, one is being measured now. And
there is no agent anywhere in this project yet — every rule on both sides is
hand-written by us.

**The failure mode we are most likely to die of** is not maths, it is drift: four
people, several AI chat sessions, and a new plan every week. Hence the rule in
CLAUDE.md — CLAUDE.md is the plan, LEDGER.md is the record, everything else is a
chat log. If a plan lives only in a chat window, it is not the plan.

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
| `test_track0.py` | 25 tests. Run them before writing a ledger entry. |
| `results/` | Raw JSON from every run. |

### Documents

| file | what it is |
|---|---|
| `CLAUDE.md` | The plan and the hard rules. Doubles as instructions for AI assistants working in the repo. |
| `LEDGER.md` | Append-only. One entry per cycle: what we tried, what happened, **what it cost us**. That third thing is the point — every design choice gives something up, and we write the sacrifice down while making it, not months later. This file becomes the paper's limitations section. |
| `ONBOARDING.md` | This file. |
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

Everything so far is us hand-writing both toolkits. The actual research question
needs a *proposer* — something that invents the second toolkit itself. The design
is deliberately boring, copied from FunSearch rather than from reinforcement
learning.

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

## 7. Track 0 is the demo system — what to do to it

Track 0 is not a toy version of Track 1. It is the instrument calibration: the
cheap rig where we find out whether the measurement works at all before paying for
real proofs. It has already earned its cost, by telling us our first metric was an
artefact — which would have taken months to discover in Lean.

Useful things to do to it, roughly in order of value:

1. **Add a problem type.** Everything is currently "slope of a polynomial at a
   point." Extrema (`show f(x) ≥ f(1)` for x ≥ 0) and sum-of-powers closed forms
   (`Σk³ = n²(n+1)²/4`) are both statable in the base and both want a *different*
   abstraction — finite differences for the second, which is arguably a better
   target than the derivative because it is a small theory rather than a single
   definition, so a hit there is a hit on "discovered a framework." Check the four
   questions in CLAUDE.md before adding anything.
2. **Build the proposer loop** against the existing banks. Everything it needs
   already exists.
3. **Do the rename test.** One afternoon, and it is the control everyone asks for
   first.
4. **Make the numeric-point finding explicit.** Every problem evaluated at a
   literal number, like `x³ at −2`, is cheap, because `canon` folds constants for
   free. Every boundary problem is at a symbolic point. That is four for four, and
   a future bank should state it up front rather than spend cells rediscovering
   it.

Things not to do: raise the depth cap or node budget, "improve" the base rules,
edit `heldout.py`, or add a dependency without asking.

---

## 8. Your first afternoon

1. `python test_track0.py` — confirm 25 pass.
2. `python experiment.py --paths --only "x^2 at a"` — read the two proofs side by
   side. That is the whole project on one screen.
3. Read `LEDGER.md` **from the bottom up**. The recent entries hold the real
   findings; the first entry's headline numbers are the ones we later showed to be
   artefacts.
4. Read the "Non-negotiable constraints" section of `CLAUDE.md`. Four items, each
   there because breaking it would silently invalidate a result.
5. Pick something from §7, and put a line in the ledger when it produces a number.

If something in here is wrong, fix it and push. A stale manual is worse than none.
