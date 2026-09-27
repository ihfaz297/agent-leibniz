# Onboarding

**Start here, in five minutes:**

```bash
python test_track0.py && python test_propose.py && python test_proposer.py   # 61 tests
python experiment.py --paths --only "x^2 at a"                               # the whole project, one screen
python propose.py --all                                                      # three verdicts, three reasons
```

Then read §2 (what is actually done) and pick a task from §7. Task 1 takes an hour.

Two documents outrank this one. **CLAUDE.md** is the plan. **LEDGER.md** is the record of
every run and what each decision cost. If this file disagrees with them, they win — fix
this file and push.

---

## 1. What we are doing

**One sentence.** Give a system a maths toolkit that stops just short of calculus, hand it
problems calculus makes easy, and measure whether inventing a calculus-shaped tool pays
off.

**Why that is a measurement and not a vibe.** A concept like the derivative lets you prove
nothing you could not prove before — you can find a tangent slope with algebra alone,
painfully. What it does is make the painful thing cheap. So we never argue about whether a
system "understood" anything. We measure the cheapness: how much work does a problem take
without the concept, and with it?

**What we are NOT claiming.** Not that an AI discovers calculus. Any model good enough to
propose anything has read every calculus textbook. Say this out loud early and often — it
is the first objection anyone raises, and conceding it is what makes the rest defensible.
What we build is the measuring instrument plus the controls that say how much of a result
is just the model remembering.

**Why it matters.** There is a ladder: solve a problem → discover a theorem → discover a
*concept* → discover a theory. Rungs 1 and 2 are crowded (Lean provers, AlphaProof,
FunSearch). Rung 3 is close to empty — nobody has convincingly shown a system inventing a
reusable abstraction and then compounding on it. We are building the bench you would need
to test that, with calculus as the known-answer case to calibrate against.

---

## 2. What is actually done

| piece | state |
|---|---|
| Engine, verifier, search | **done**, 25 tests |
| Training bank (5), held-out bank (8, frozen) | **done** |
| Boundary bank (24, pre-registered) | **done**, raw JSON in `results/` |
| Proposer loop: soundness → scoring → triage | **done**, 12 tests |
| Obfuscation arms 1 and 2 | **done**, 24 tests |
| Model adapter (DeepSeek or any OpenAI-shaped API) | **done**, needs a key to run |
| Lean spike, base side of gate item 2 | **done**, compiles, axioms clean |
| Gate item 1 | **PASSED** |
| Gate item 2 | **specified, not evaluated** — see §9 |
| Lean abstraction side | **never measured** — the real blocker (task 6) |
| Δ base (finite differences) | **not started** — blocks arms 3 and 4 (task 5) |
| Any result from an actual model | **none. Not one call has been made.** |

Four things a newcomer should know before trusting any number in here.

**1. The good result.** Ten problems where the no-derivative search cannot finish and the
derivative finishes in a handful of steps. It held when we changed the accounting three
ways and doubled the compute budget.

**2. Our first metric was an artefact.** We started by counting steps with and without the
derivative and calling the difference the payoff. Chop the rewrite rules differently and
that difference nearly vanishes — on some problems it goes *negative*. What survived is
coarser and honest: **can the base finish at all?** That is a yes/no and it does not care
how the rules are chopped.

**3. Cost alone cannot detect a wrong abstraction.** Run
`python propose.py c002_bad_power`. It is the derivative with one character wrong. It gets
22 answers wrong. Its step counts are *identical* to the correct version's. That is why
there are two independent referees and why neither may be removed.

**4. Three claims here were retracted after being made.** The ledger keeps them visible
instead of editing them away: a gate verdict that moved the goalposts, an overclaim that a
finite-difference target would catch contamination cleanly, and a claim that the adapter
could handle real model output when it could not. **Finding a fourth is the most useful
thing you can do this week** — see §7.

**And there is still no proposer.** The bench is built; every candidate in `candidates/`
was written by hand, and no model has ever been called. Do not let anyone — us included —
call this an AI discovering things yet.

**The failure mode most likely to kill us** is drift, not maths: four people, several AI
chat sessions, a new plan weekly. Hence the rule: CLAUDE.md is the plan, LEDGER.md is the
record, everything else is a chat log. A plan that lives only in a chat window is not the
plan.

---

## 3. Repo map

### Engine — Python, standard library only

| file | what it is |
|---|---|
| `terms.py` | The data structure. Expressions are trees: `Const`, `Var`, `Add`, `Mul`, `Pow`, plus `Slope` (the problem), `D` (a derivative), `At` (evaluate at a point). |
| `canon.py` | Tidies a term after every edit — flattens, sorts, folds numbers, cancels `h·h⁻¹`. **Free: it costs no steps.** Read its header; the line between free and counted is the most load-bearing choice in the project. |
| `rules.py` | The two toolkits. `R1`–`R8` = the pre-calculus base. `D1`–`D5` + `B` = the derivative. |
| `search.py` | Shortest rule sequence from problem to answer. Depth cap 12, budget 400k nodes, `closure=k` option (§5). **The number it produces is the instrument.** |
| `verify.py` | The independent referee. Random exact fractions through every rule and every answer, plus a coefficient oracle that shares no code with `rules.py` — so it can catch `rules.py` being wrong. |
| `experiment.py` | 5 training problems + the driver. |
| `heldout.py` | 8 problems, **frozen** before any candidate was tested. Append-only; every append gets a ledger line. |
| `boundary.py` | 24 problems, gridded and committed before running. The bank the Lean gate rests on. |
| `results/` | Raw JSON from every run. |

### The loop

| file | what it is |
|---|---|
| `propose.py` | Scores a candidate: sound? helps on training? helps on held-out? Then one bucket. `python propose.py --list` |
| `candidates/` | One module per candidate. `c001` = the real derivative (the contamination ceiling). `c002` and `c003` are permanent fixtures that must both be rejected — one unsound, one sound-but-useless. |
| `obfuscate.py` | Builds the proposer's prompt for one arm. Describes each rule **only by worked example**, never by name. Checks its own output for leaked target vocabulary. `python obfuscate.py renamed` |
| `proposer.py` | Calls a model, extracts the module, audits it, writes it to `candidates/`. Scores nothing — generation and judgement stay separate. `--dry-run` needs no key. |
| `opaque_ops.py` | Neutral re-exports, so a renamed prompt can say what to import without naming the target. Exists because `from terms import Slope` leaked the answer in an import line. |
| `test_track0.py`, `test_propose.py`, `test_proposer.py` | 25 + 12 + 24 tests. Run before every ledger entry. |

### Documents

| file | what it is |
|---|---|
| `CLAUDE.md` | The plan and the hard rules. Also instructions for AI assistants in this repo. |
| `LEDGER.md` | Append-only. Per cycle: what we tried, what happened, **what it cost us**. The third one is the point — every choice gives something up, written down while making it. Becomes the paper's limitations section. |
| `NEXT.md` | The zero-budget plan and the Δ design. |
| `track1/` | The Lean spike. Not Track 1 yet. Holds the version pin. |
| `graveyard/` | Quarantined documents with a header saying why. Currently one AI-generated "plan" involving quantum computing with no falsifiable mechanism. **Do not build on anything in here.** |
| `schizophrenic-conversations.txt` | The design conversation this came from. Long, but every constraint in CLAUDE.md traces back to it. Worth an hour. |
| `FIRST_MISSIONS.txt.txt` | The original two-week plan. Partly superseded. |

---

## 4. Setup

### Python — five minutes

Python 3.11. No packages, no virtualenv.

```bash
python test_track0.py           # 25 tests, ~5 seconds
python experiment.py            # the training table
python experiment.py --paths    # same, printing every rewrite step
python boundary.py --jobs 11    # the big run, ~5 min on 12 cores
```

Start with `--paths`. A 12-step algebra grind next to a 4-step derivative proof is the
fastest way to see what this measures.

### Lean — an hour, mostly waiting. Only needed for tasks 3 and 6.

```powershell
# Windows
Invoke-WebRequest -Uri "https://github.com/leanprover/elan/releases/latest/download/elan-x86_64-pc-windows-msvc.zip" -OutFile "$env:TEMP\elan.zip"
Expand-Archive "$env:TEMP\elan.zip" -DestinationPath "$env:TEMP\elan" -Force
& "$env:TEMP\elan\elan-init.exe" -y --default-toolchain stable
$env:Path = "$env:USERPROFILE\.elan\bin;$env:Path"
```

```bash
# macOS / Linux
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y && source ~/.elan/env
```

```bash
lake new spike math      # pulls Mathlib, picks the toolchain
cd spike
lake exe cache get       # THE IMPORTANT ONE. Several GB of prebuilt Mathlib.
lake build
```

**Pin the versions** before building, or `RingSpike.lean` may not compile — one
deprecation already bit us. Lean `v4.34.1`, mathlib `d13f23b`; instructions in
`track1/README.md`.

Tips, each worth a day:

- **`lake exe cache get` is not optional.** Skip it and `lake build` compiles Mathlib from
  source: hours, and it may just fall over. If a build looks like it is compiling half of
  mathematics, you skipped this.
- **Never hand-pick a toolchain version.** Let the `math` template choose, then record
  what worked.
- **elan is rustup, lake is cargo.** Versions vs projects.
- **Use VS Code + the "Lean 4" extension.** The editor *is* the interface — put the cursor
  in a proof and it shows the remaining goal. Terminal-only Lean is hard mode.
- **`sorry` is a legal placeholder.** Compiles with a warning. Use it while drafting;
  never let one reach a measurement.
- **`#print axioms myThm`** shows what a proof really depends on. Ours must show only
  `propext, Classical.choice, Quot.sound`. This is how you catch a proof that quietly
  assumed the thing it was proving — Lean checks that proofs follow from assumptions, never
  that assumptions are true.
- **Do not `import Mathlib` whole** unless you enjoy waiting.

---

## 5. Two ideas you need before the ledger makes sense

**"Closure" — how coarsely do we count?** A step is one rule application. But is
`D(5x) → 5·D(x)` one step or two? Two of our rules chained, and any textbook calls it one
move. So `search(closure=k)` lets up to `k` rules chained *inside the piece the previous
rule just produced* count as one step, applied to both toolkits equally. We ran k=1,2,3.
Per-problem differences largely dissolved; "can it finish at all" did not. **Every number
we quote says which k it came from.**

**Why we do not tune until the numbers look good.** Because we could, trivially, and the
result would be worthless. So: held-out problems are written before anything is tested on
them and never edited to be "more representative"; caps and budgets are never raised
because a problem hit one (**a problem that runs out of room is a result**); the base is
never improved to make problems easier, because the difficulty *is* the experiment.

The one time we came close to breaking this — extending the problem grid after a
disappointing count — we committed the extension *before* running it and wrote a ledger
paragraph explaining why a critic could still call it tuning. The one time we did not take
that precaution, the result had to be retracted.

---

## 6. The loop

Everything so far is us hand-writing both toolkits. The research question needs a
*proposer* — something that invents the second toolkit itself. The design is deliberately
boring: FunSearch-shaped, not reinforcement learning.

**All five steps are built.** What is missing is a key and somebody to run it (§7, task 2).

```
   1. PROPOSE                      proposer.py + obfuscate.py
      A model sees the base toolkit and problems it cannot solve.
      It emits a candidate: a new operator plus rules for it.
      Nothing else.  No prose, no solving.
                    |
                    v
   2. CHECK SOUNDNESS              verify.py   (later: Lean)
      Random exact-rational testing of every proposed rule,
      then the independent oracle.
      Unsound -> quarantine.  Never delete.
                    |
                    v
   3. SCORE USEFULNESS             search.py + experiment.py
      Does it let the search finish problems the base cannot?
      TRAINING problems only.
                    |
                    v
   4. TRANSFER                     heldout.py + boundary.py
      Re-score on problems it was never selected against.
      THIS IS THE ONLY NUMBER THAT MATTERS.
                    |
                    v
   5. TRIAGE - one bucket, no exceptions
      Kept         sound, and helps on held-out
      Quarantined  unsound, or helps on training only
      Fatal        the setup broke, not the candidate
                   -> go redesign the base
```

Four rules that are not up for discussion.

**Soundness and usefulness need separate referees.** A checker says a rule is *valid*,
never that it is *useful*. Given only a soundness check, a generator emits infinite valid
garbage — this is how Lenat's AM died in the 1970s, and you will be asked about it, so read
Ritchie and Hanna's critique before you need to. We measured how badly you need both:
`c002_bad_power` is one character wrong, gets 22 answers wrong, and scores *identically* to
the real thing.

**Propose and exploit are separate calls.** Never let one generation both invent a rule and
use it to solve a problem. That is how you get a system that quietly assumes what it is
proving.

**The proposer may define, never assume.** If it can postulate a new axiom rather than
construct from what exists, the verifier stops verifying: Lean happily accepts an
inconsistent assumption and then "proves" everything from it, and your dashboard reads
100%. If we ever want postulation, the price of entry is supplying a model — in Lean, a
`class` plus an `instance`, where the instance *is* the consistency proof.

**A human reads every machine-written candidate before it runs.** Scoring imports and
executes the module. Machine candidates arrive with `REVIEWED = False` and `propose.py`
refuses them until someone flips it. There is an import allowlist and a static audit;
neither replaces reading the file.

**The control that makes any of it mean something: the rename test.** Strip the calculus
vocabulary, rename the operators, rerun. If performance collapses, the model was reciting,
not searching — and we learned that in an afternoon instead of at a demo. If it survives,
we have signal. Either outcome is publishable, which is what makes it a good experiment.
Arms 1 and 2 are built (§7 task 2); arms 3 and 4 need the Δ base (task 5).

**Not doing, and please do not propose:** population search, MCTS, reinforcement learning,
quantum anything. Those are v2, and v2 exists only if v1 runs. `graveyard/` is what
ignoring this looks like.

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
   tests, ~10 seconds.
2. `python experiment.py --paths --only "x^2 at a"` — the two proofs side by side. The
   whole project on one screen.
3. `python propose.py --all` — the loop keeps the real derivative, rejects an unsound
   abstraction, rejects a sound useless one. Three verdicts, three reasons.
4. `python propose.py c002_bad_power` — compare its step counts to `c001`'s. Identical.
   And it gets 22 answers wrong. That is why there are two referees.
5. `python obfuscate.py renamed` — the prompt a model actually gets, vocabulary stripped.
   Could *you* tell what the target is? Look at `r7`. That is the honest limit of this
   arm, written up in §6.
6. Read `LEDGER.md` **bottom-up**. Recent entries hold the real findings; the first
   entry's headline numbers are the ones we later showed to be artefacts.
7. Read "Non-negotiable constraints" in `CLAUDE.md`. Four items, each there because
   breaking it silently invalidates a result.
8. Claim a task from §7. Task 1 takes an hour and is a real contribution.

---

## 9. The gate, and the one decision still open

Track 1 (Lean) is gated on two conditions in `CLAUDE.md`.

- **Item 1: PASSED.** Ten boundary problems, stable across `closure=1,2,3` and a doubled
  budget.
- **Item 2: specified, not evaluated.** The blocker is task 6 — the abstraction side has
  never been measured, so there is half a comparison and no gap.

**Item 2 was rewritten on 2026-09-27**, because the first wording could not be answered.
It asked whether the base could be proved "with `ring`" without saying *which statement* —
and the answer is 1 tactic, 6 tactics, or 12→23 depending on the form. An earlier version
of this repo called that a conditional pass. That moved the goalposts, and the ledger
retracts it.

**If you take one methodological lesson from this project, take that one: the wording goes
in before the measurement, or the measurement means nothing.**

One sub-decision is settled but reopenable. What does "the base cannot prove it" *mean*?
Lean has no exhaustive search, so "we did not find a proof" is not a result, and a clever
enough person always rescues the base. The rule adopted: the base may instantiate at up to
k points, `ring_nf`, make one automation call, and derive **at most one** intermediate
lemma. More than one and it has failed. Under that rule the quadratic passes (needs one)
and degree 5 fails (needs four).

"At most one" is still a number somebody picked. A degree-3 or degree-4 problem needing two
lemmas sits on the wrong side of a line drawn without measuring those degrees. If the bank
grows to include them, **revisit the line before running, not after.**

---

Then read `NEXT.md` for the zero-budget plan and the Δ design.

If something in here is wrong, fix it and push. A stale manual is worse than none.
