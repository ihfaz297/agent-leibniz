"""The proposer loop.  First time this project has an agent in it.

    propose -> check soundness -> score on training -> score on HELD-OUT -> triage

The loop is deliberately boring: one candidate at a time, no population, no
search over candidates, no reward signal.  CLAUDE.md forbids those and they are
v2.  What this file adds is the plumbing that turns "here is a proposed
abstraction" into a row in the ledger, with the two referees kept separate:

  * `verify.py` says whether a candidate is SOUND.  It can never say whether a
    candidate is USEFUL.  Given only a soundness check a generator emits
    infinite valid garbage -- this is how Lenat's AM died.
  * `search.py` plus the problem banks say whether it is USEFUL.  Scored on
    training first, then on problems it was never selected against.  Only the
    second number counts.

A candidate is a module in `candidates/` exposing:

    NAME        str
    RULES       tuple[Rule, ...]
    PROVENANCE  dict -- WHO proposed it and WHAT THEY COULD SEE.  Required.
                Contamination is the whole methodological problem here, so a
                candidate with no provenance is refused before it is scored.
    NOTES       str, optional

Candidates are plain Python and are imported and executed.  That is the
FunSearch arrangement and it is fine for a local research repo where every
candidate is committed and read by a human first -- but it does mean: never
point this at a candidate you have not read.

Usage:
    python propose.py --list
    python propose.py c001_derivative
    python propose.py c001_derivative --boundary     # slow, adds the gate bank
    python propose.py --all
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pkgutil
import time
from fractions import Fraction

from canon import canon
from rules import BASE_ONLY, BASE_RULES, Rule
from search import DEFAULT_MAX_DEPTH, DEFAULT_NODE_BUDGET, search
from terms import Slope
from verify import check_rule, oracle_eval

import experiment
import heldout

#: The base minus the two rules that reach a slope without an abstraction.  A
#: candidate scored against this has to supply its own route, so a zero gap is
#: readable (LEDGER.md 2026-08-28).
BASE_NO_SLOPE = tuple(r for r in BASE_RULES
                      if r.name not in ("R7.slope_dq", "R8.eval_h_zero"))

CANDIDATE_DIR = "candidates"

#: Provenance keys a candidate must supply.  These are not bureaucracy: every
#: one of them is a thing a reviewer will ask, and answering after the fact is
#: how BACON lost its credibility.
REQUIRED_PROVENANCE = (
    "proposer",          # who or what emitted it
    "saw_heldout",       # bool -- did the proposer see heldout.py?
    "saw_boundary",      # bool -- did it see boundary.py?
    "calculus_words",    # bool -- was calculus vocabulary present in the prompt?
    "date",
)


class BadCandidate(Exception):
    pass


def load(name: str):
    mod = importlib.import_module(f"{CANDIDATE_DIR}.{name}")
    for attr in ("NAME", "RULES", "PROVENANCE"):
        if not hasattr(mod, attr):
            raise BadCandidate(f"{name}: missing {attr}")
    missing = [k for k in REQUIRED_PROVENANCE if k not in mod.PROVENANCE]
    if missing:
        raise BadCandidate(f"{name}: PROVENANCE missing {missing}")
    if mod.PROVENANCE["saw_heldout"]:
        raise BadCandidate(
            f"{name}: proposer saw the held-out set. It cannot be scored on it. "
            "This is not recoverable -- write a new held-out set or a new "
            "candidate (CLAUDE.md)."
        )
    return mod


def discover() -> list:
    if not os.path.isdir(CANDIDATE_DIR):
        return []
    return sorted(m.name for m in pkgutil.iter_modules([CANDIDATE_DIR]))


# ----------------------------------------------------------------- referee one

def soundness(mod, trials: int = 100) -> dict:
    """Random exact-rational testing of every rule the candidate declares as a
    pointwise identity.  Rules declared non-identity cannot be checked this way
    and are carried to the answer-level oracle check instead, which is where
    R7/R8/B are checked too."""
    out = {"checked": {}, "failures": [], "unchecked": []}
    for r in mod.RULES:
        if not r.identity:
            out["unchecked"].append(r.name)
            continue
        checked, fails = check_rule(r, trials=trials)
        out["checked"][r.name] = checked
        if checked == 0:
            out["failures"].append((r.name, "rule never fired on a random term"))
        for f in fails:
            out["failures"].append((r.name, f"counterexample at {f[3]}: "
                                            f"{f[4]} != {f[5]}"))
    return out


# ----------------------------------------------------------------- referee two

def _score_one(body, at, rules, closure, budget, max_depth):
    start = canon(Slope(body, "x", at))
    t0 = time.time()
    res = search(start, rules, closure=closure, node_budget=budget,
                 max_depth=max_depth)
    row = {"status": res.status, "steps": res.steps,
           "secs": round(time.time() - t0, 1)}
    if res.found:
        # the answer-level check: does it agree with the independent oracle?
        env = {"a": Fraction(7, 3)}
        try:
            row["answer_ok"] = (oracle_eval(res.path[-1][1], env)
                                == oracle_eval(start, env))
        except Exception as exc:                      # noqa: BLE001
            row["answer_ok"] = None
            row["answer_note"] = repr(exc)
        row["answer"] = repr(res.path[-1][1])
    return row


def score(mod, problems, closure: int = 1, budget: int = DEFAULT_NODE_BUDGET,
          max_depth: int = DEFAULT_MAX_DEPTH) -> list:
    """For each problem: base alone, candidate alone (no R7/R8), and both."""
    cand_only = BASE_NO_SLOPE + tuple(mod.RULES)
    both = BASE_RULES + tuple(mod.RULES)
    rows = []
    for name, body, at, *_ in problems:
        row = {"problem": name}
        for label, rules in (("base", BASE_ONLY), ("cand", cand_only),
                             ("both", both)):
            row[label] = _score_one(body, at, rules, closure, budget, max_depth)
        rows.append(row)
    return rows


def summarize(rows) -> dict:
    """The two numbers that matter, and nothing else.

    `finishes_base_cannot` is the k-invariant result from LEDGER.md: the base
    cannot finish and the candidate can.  `gap_*` are reported but must never be
    quoted without their closure value -- they are factoring-sensitive."""
    wrong = [r["problem"] for r in rows
             for lab in ("base", "cand", "both")
             if r[lab].get("answer_ok") is False]
    finishes = [r["problem"] for r in rows
                if r["base"]["status"] != "found" and r["cand"]["status"] == "found"]
    regress = [r["problem"] for r in rows
               if r["base"]["status"] == "found" and r["cand"]["status"] != "found"]
    gaps = {r["problem"]: r["base"]["steps"] - r["cand"]["steps"]
            for r in rows
            if r["base"]["status"] == "found" and r["cand"]["status"] == "found"}
    return {
        "wrong_answers": wrong,
        "finishes_base_cannot": finishes,
        "base_finishes_cand_cannot": regress,
        "gaps": gaps,
        "median_gap": (sorted(gaps.values())[len(gaps) // 2] if gaps else None),
    }


# --------------------------------------------------------------------- triage

def triage(sound, train, held) -> tuple:
    """Exactly one bucket (CLAUDE.md).  Returns (bucket, reason)."""
    if sound["failures"]:
        return "Quarantined", f"unsound: {sound['failures'][0]}"
    if train["wrong_answers"] or held["wrong_answers"]:
        return "Quarantined", ("produced a wrong answer on "
                               f"{(train['wrong_answers'] + held['wrong_answers'])[0]}")
    helps_held = bool(held["finishes_base_cannot"]) or (
        held["median_gap"] is not None and held["median_gap"] > 0)
    helps_train = bool(train["finishes_base_cannot"]) or (
        train["median_gap"] is not None and train["median_gap"] > 0)
    if helps_held:
        return "Kept", (f"held-out: finishes {len(held['finishes_base_cannot'])} "
                        f"the base cannot, median gap {held['median_gap']}")
    if helps_train:
        return "Quarantined", "compressed on training but not on held-out"
    return "Quarantined", "sound but does not help anywhere"


# ----------------------------------------------------------------------- driver

def run(name, closure, budget, max_depth, with_boundary, trials) -> dict:
    mod = load(name)
    print(f"\n=== {mod.NAME}  ({name}) ===")
    print(f"  proposer: {mod.PROVENANCE['proposer']}  "
          f"calculus vocabulary: {mod.PROVENANCE['calculus_words']}  "
          f"saw boundary bank: {mod.PROVENANCE['saw_boundary']}")
    print(f"  rules: {', '.join(r.name for r in mod.RULES)}")

    print("\n  [1/4] soundness")
    sound = soundness(mod, trials=trials)
    for rn, n in sound["checked"].items():
        print(f"        {rn:<22} {n} random instantiations")
    for rn in sound["unchecked"]:
        print(f"        {rn:<22} not a pointwise identity -- answer-level check only")
    for f in sound["failures"]:
        print(f"        FAIL {f}")

    print(f"\n  [2/4] training  (closure={closure})")
    train_rows = score(mod, experiment.PROBLEMS, closure, budget, max_depth)
    train = summarize(train_rows)
    for r in train_rows:
        print(f"        {r['problem']:<24} base={r['base']['status'] if r['base']['status']!='found' else r['base']['steps']:<10} "
              f"cand={r['cand']['status'] if r['cand']['status']!='found' else r['cand']['steps']}")

    print(f"\n  [3/4] held-out  (frozen; the only number that counts)")
    held_rows = score(mod, heldout.HELDOUT, closure, budget, max_depth)
    held = summarize(held_rows)
    for r in held_rows:
        print(f"        {r['problem']:<24} base={r['base']['status'] if r['base']['status']!='found' else r['base']['steps']:<10} "
              f"cand={r['cand']['status'] if r['cand']['status']!='found' else r['cand']['steps']}")

    bound = bound_rows = None
    if with_boundary:
        import boundary
        print("\n        boundary bank (the gate bank) -- slow")
        bound_rows = score(mod, [(n, b, a) for n, b, a in boundary.CANDIDATES],
                           closure, budget, max_depth)
        bound = summarize(bound_rows)
        print(f"        finishes {len(bound['finishes_base_cannot'])} the base cannot")

    bucket, reason = triage(sound, train, held)
    print(f"\n  [4/4] triage: {bucket} -- {reason}")

    return {
        "candidate": name, "name": mod.NAME, "provenance": mod.PROVENANCE,
        "rules": [r.name for r in mod.RULES],
        "closure": closure, "budget": budget, "max_depth": max_depth,
        "soundness": {"checked": sound["checked"],
                      "unchecked": sound["unchecked"],
                      "failures": [list(map(str, f)) for f in sound["failures"]]},
        "training": {"rows": train_rows, "summary": train},
        "heldout": {"rows": held_rows, "summary": held},
        "boundary": ({"rows": bound_rows, "summary": bound} if bound else None),
        "triage": {"bucket": bucket, "reason": reason},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--closure", type=int, default=1)
    ap.add_argument("--budget", type=int, default=DEFAULT_NODE_BUDGET)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    ap.add_argument("--boundary", action="store_true", help="also run the gate bank")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--out", default="results/proposals.json")
    args = ap.parse_args()

    if args.list or (not args.candidate and not args.all):
        names = discover()
        print("candidates in ./candidates:")
        for n in names:
            try:
                mod = load(n)
                print(f"  {n:<28} {mod.NAME}")
            except BadCandidate as exc:
                print(f"  {n:<28} REFUSED: {exc}")
        if not names:
            print("  (none)")
        return

    targets = discover() if args.all else [args.candidate]
    out = []
    for t in targets:
        try:
            out.append(run(t, args.closure, args.budget, args.max_depth,
                           args.boundary, args.trials))
        except BadCandidate as exc:
            print(f"\n=== {t} ===\n  REFUSED: {exc}")
            out.append({"candidate": t, "refused": str(exc)})

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    existing = []
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                pass
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(existing + out, f, indent=1)
    print(f"\nwrote {args.out}")

    print("\nsummary")
    print(f"{'candidate':<28} {'bucket':<14} reason")
    for r in out:
        if "refused" in r:
            print(f"{r['candidate']:<28} {'REFUSED':<14} {r['refused']}")
        else:
            print(f"{r['candidate']:<28} {r['triage']['bucket']:<14} "
                  f"{r['triage']['reason']}")


if __name__ == "__main__":
    main()
