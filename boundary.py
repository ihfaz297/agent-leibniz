"""Boundary bank: candidates for the gate to Track 1 (CLAUDE.md).

A boundary problem is one where the base exhausts and the derivative finishes,
at closure=1, 2 and 3, and where the base still exhausts under a doubled node
budget.  Sixteen candidates chosen by grid before any were run:

    degree {3, 4} x terms {1, 2, 3} x coefficients {unit, non-unit}
                x evaluation point {symbolic, numeric}

Not every cell is filled -- 16 of 24.  (3,1,unit,*) is already covered by
experiment.py and heldout.py; the eight cells left out are all non-unit or
three-term cases at a numeric point, dropped to keep the run under an hour.
The list was fixed before any candidate was run.  2x^3 - 3x^2 + x at a is
the anchor: the one row from heldout.py that held at every k.

Run:  python boundary.py [--budget 400000] [--jobs N]  -> results/boundary.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
from multiprocessing import Pool

from canon import canon
from experiment import poly, C, V
from rules import BASE_ONLY, DERIV_ONLY
from search import DEFAULT_NODE_BUDGET, search
from terms import Slope

#: (name, body, point)   -- degree, terms, coeff, point annotated in the name order
CANDIDATES = [
    ("2x^3 at a",                 poly(0, 0, 0, 2),        V("a")),
    ("2x^3 at 2",                 poly(0, 0, 0, 2),        C(2)),
    ("x^3 + x at a",              poly(0, 1, 0, 1),        V("a")),
    ("x^3 + x at -1",             poly(0, 1, 0, 1),        C(-1)),
    ("x^3 - x^2 at a",            poly(0, 0, -1, 1),       V("a")),
    ("3x^3 + 2x at a",            poly(0, 2, 0, 3),        V("a")),
    ("x^3 + x^2 + x at a",        poly(0, 1, 1, 1),        V("a")),
    ("x^3 - x^2 + 1 at 2",        poly(1, 0, -1, 1),       C(2)),
    ("2x^3 - 3x^2 + x at a",      poly(0, 1, -3, 2),       V("a")),   # anchor
    ("x^4 at a",                  poly(0, 0, 0, 0, 1),     V("a")),
    ("x^4 at -1",                 poly(0, 0, 0, 0, 1),     C(-1)),
    ("3x^4 at a",                 poly(0, 0, 0, 0, 3),     V("a")),
    ("x^4 + x^2 at a",            poly(0, 0, 1, 0, 1),     V("a")),
    ("x^4 - x at 1",              poly(0, -1, 0, 0, 1),    C(1)),
    ("x^4 + x^3 + x at a",        poly(0, 1, 0, 1, 1),     V("a")),
    ("2x^4 + 3x^2 at a",          poly(0, 0, 3, 0, 2),     V("a")),
]


def _job(args):
    name, body, at, config, k, budget = args
    rules = BASE_ONLY if config == "base" else DERIV_ONLY
    start = canon(Slope(body, "x", at))
    t0 = time.time()
    r = search(start, rules, closure=k, node_budget=budget)
    return {
        "problem": name, "config": config, "closure": k, "budget": budget,
        "status": r.status, "steps": r.steps, "nodes": r.nodes,
        "depth_reached": r.depth_reached, "secs": round(time.time() - t0, 1),
        "answer": repr(r.path[-1][1]) if r.found else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=DEFAULT_NODE_BUDGET)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default="results/boundary.json")
    ap.add_argument("--closures", default="1,2,3")
    ap.add_argument("--only", default=None, help="substring filter on problem name")
    ap.add_argument("--configs", default="base,deriv")
    args = ap.parse_args()
    ks = [int(k) for k in args.closures.split(",")]
    cfgs = args.configs.split(",")

    jobs = [(n, b, a, cfg, k, args.budget)
            for n, b, a in CANDIDATES if not args.only or args.only in n
            for k in ks for cfg in cfgs]
    # slowest first so the pool tail is short
    jobs.sort(key=lambda j: (j[3] != "base", -j[4]))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    results = []
    t0 = time.time()
    with Pool(args.jobs) as pool:
        for i, res in enumerate(pool.imap_unordered(_job, jobs), 1):
            results.append(res)
            print(f"[{i:>3}/{len(jobs)}] {res['problem']:<24} {res['config']:<5} k={res['closure']} "
                  f"{res['status']:<16} steps={res['steps']} {res['secs']}s", flush=True)
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
    print(f"done in {time.time()-t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
