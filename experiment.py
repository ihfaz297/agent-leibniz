"""Track 0 driver: run each problem twice, base-only and with the derivative,
and print the two step counts side by side.

That difference is the compression gap.  If it does not appear here, Track 1 is
not worth building (CLAUDE.md).
"""

from __future__ import annotations

import argparse
import time
from fractions import Fraction

from canon import canon
from rules import BASE_ONLY, DERIV_ONLY, WITH_DERIV
from search import DEFAULT_MAX_DEPTH, DEFAULT_NODE_BUDGET, format_path, search
from terms import C, Pow, Slope, V
from verify import check_path, oracle_eval

X = V("x")


def poly(*coeffs):
    """poly(1, 0, -2) -> x^2 + 0*x - 2 ... ascending: poly(c0, c1, c2, ...)."""
    from terms import Add, Mul
    terms = [Mul((C(c), Pow(X, C(k)))) for k, c in enumerate(coeffs) if c != 0]
    return canon(Add(tuple(terms)))


#: Validate on x^2 before the cubic (CLAUDE.md).  `expect_base` records, before
#: the run, whether we believe the base can grind it out inside the depth cap.
PROBLEMS = [
    ("x^2 at a",          poly(0, 0, 1),      V("a"),  True),
    ("x^2 at 3",          poly(0, 0, 1),      C(3),    True),
    ("3x^2 - 5x + 1 at a", poly(1, -5, 3),    V("a"),  True),
    ("x^3 at a",          poly(0, 0, 0, 1),   V("a"),  False),
    ("x^3 - 2x at 1",     poly(0, -2, 0, 1),  C(1),    False),
]


def run(name, body, at, expect_base, max_depth, budget, show_path):
    start = canon(Slope(body, "x", at))
    row = {"name": name, "expect_base": expect_base}
    for label, rules in (("base", BASE_ONLY), ("deriv", DERIV_ONLY),
                         ("both", WITH_DERIV)):
        t0 = time.time()
        res = search(start, rules, max_depth=max_depth, node_budget=budget)
        row[label] = res
        row[label + "_secs"] = time.time() - t0
        if res.found and show_path:
            print(f"\n  [{name} / {label}]  {res.steps} steps")
            print(format_path(start, res))
    return start, row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    ap.add_argument("--budget", type=int, default=DEFAULT_NODE_BUDGET)
    ap.add_argument("--paths", action="store_true", help="print the rewrite paths")
    ap.add_argument("--only", default=None, help="substring filter on problem name")
    args = ap.parse_args()

    print(f"depth cap {args.max_depth}, node budget {args.budget}\n")
    rows = []
    for name, body, at, expect_base in PROBLEMS:
        if args.only and args.only not in name:
            continue
        start, row = run(name, body, at, expect_base, args.max_depth, args.budget,
                         args.paths)
        rows.append((start, row))

    print(f"\n{'problem':<20} {'base':>16} {'deriv':>16} {'both':>16} "
          f"{'gap':>5}  answer")
    print("-" * 92)
    for start, r in rows:
        b, d, w = r["base"], r["deriv"], r["both"]
        cell = lambda x: str(x.steps) if x.found else x.status
        gap = str(b.steps - d.steps) if (b.found and d.found) else "-"
        ans = repr(d.path[-1][1]) if d.found else ""
        print(f"{r['name']:<20} {cell(b):>16} {cell(d):>16} {cell(w):>16} "
              f"{gap:>5}  {ans}")

    print("\nsoundness of each path found (algebraic steps only):")
    for start, r in rows:
        for label in ("base", "deriv", "both"):
            res = r[label]
            if not res.found:
                continue
            n, fails = check_path(start, res.path)
            print(f"  {r['name']:<20} {label:<6} {n} steps  "
                  f"{'ok' if not fails else f'FAIL {fails[0][0]}'}")

    print("\nanswers vs the interpolation oracle:")
    for start, r in rows:
        truth_env = {"a": Fraction(7, 3)}
        truth = oracle_eval(start, truth_env)
        for label in ("base", "deriv", "both"):
            res = r[label]
            if not res.found:
                continue
            got = oracle_eval(res.path[-1][1], truth_env)
            print(f"  {r['name']:<20} {label:<6} {got}  "
                  f"{'ok' if got == truth else f'MISMATCH (oracle {truth})'}")

    print("\ntiming (seconds):")
    for _, r in rows:
        print(f"  {r['name']:<20} base {r['base_secs']:>7.2f}  "
              f"deriv {r['deriv_secs']:>7.2f}  both {r['both_secs']:>7.2f}")


if __name__ == "__main__":
    main()
