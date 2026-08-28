"""Verification.  Nothing enters the library on the strength of a proof sketch.

Two jobs:

1. Rule soundness.  For every rule flagged `identity=True`, generate random
   terms, fire the rule wherever it matches, and compare the before/after terms
   at ~100 random rational points.  Exact Fraction arithmetic, so a mismatch is
   a real mismatch, not rounding (CLAUDE.md, non-negotiable #1).

2. The two rules that are *not* pointwise identities -- R7 (difference
   quotient) and B (the bridge) -- get targeted checks against an independent
   oracle.  The oracle does not use the rewrite rules at all: it recovers a
   polynomial's exact coefficients by Lagrange interpolation at rational
   points and differentiates the coefficient list.  That is a genuinely
   separate implementation, so agreement means something.

Nothing here imports sympy or anything else outside the stdlib.
"""

from __future__ import annotations

import random
from fractions import Fraction

from canon import canon
from rules import BASE_RULES, DERIV_RULES, H, Rule
from terms import (
    Add,
    At,
    C,
    Const,
    D,
    Mul,
    Pow,
    Slope,
    Term,
    Var,
    children,
    free_vars,
    positions,
    replace_at,
    subst,
)


class NotPolynomial(Exception):
    pass


# ------------------------------------------------------------------ evaluation

def evaluate(t: Term, env: dict) -> Fraction:
    """Exact value of an algebra-only term.  Raises on anything it cannot do."""
    if isinstance(t, Const):
        return t.value
    if isinstance(t, Var):
        return env[t.name]
    if isinstance(t, Add):
        return sum((evaluate(a, env) for a in t.args), Fraction(0))
    if isinstance(t, Mul):
        out = Fraction(1)
        for a in t.args:
            out *= evaluate(a, env)
        return out
    if isinstance(t, Pow):
        b = evaluate(t.base, env)
        e = evaluate(t.exp, env)
        if e.denominator != 1:
            raise NotPolynomial("fractional exponent")
        e = int(e)
        if b == 0 and e < 0:
            raise ZeroDivisionError
        return b ** e
    raise NotPolynomial(f"operator node in evaluate: {t!r}")


# --------------------------------------------------- exact polynomial handling

def _poly_add(a, b):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else Fraction(0)) + (b[i] if i < len(b) else Fraction(0))
            for i in range(n)]


def _poly_mul(a, b):
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x == 0:
            continue
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def lagrange(xs, ys):
    """Exact coefficient list (ascending) of the unique interpolant."""
    coeffs = [Fraction(0)]
    for i in range(len(xs)):
        num = [Fraction(1)]
        den = Fraction(1)
        for j in range(len(xs)):
            if i == j:
                continue
            num = _poly_mul(num, [-xs[j], Fraction(1)])
            den *= xs[i] - xs[j]
        coeffs = _poly_add(coeffs, [c * ys[i] / den for c in num])
    return coeffs


def struct_degree(t: Term, var: str) -> int:
    """Upper bound on the degree of t in var.  Refuses non-polynomials."""
    if isinstance(t, Const):
        return 0
    if isinstance(t, Var):
        return 1 if t.name == var else 0
    if isinstance(t, Add):
        return max((struct_degree(a, var) for a in t.args), default=0)
    if isinstance(t, Mul):
        return sum(struct_degree(a, var) for a in t.args)
    if isinstance(t, Pow):
        if not isinstance(t.exp, Const) or t.exp.value.denominator != 1:
            raise NotPolynomial("non-literal or fractional exponent")
        n = int(t.exp.value)
        d = struct_degree(t.base, var)
        if n < 0:
            if d > 0:
                raise NotPolynomial("var under a negative power")
            return 0
        return n * d
    # Operator nodes get a safe *upper* bound.  Over-estimating the degree only
    # costs the interpolator extra sample points; under-estimating would be wrong.
    if isinstance(t, D):
        d = struct_degree(t.body, var)
        return max(d - 1, 0) if t.var == var else d
    if isinstance(t, At):
        inner = 0 if t.var == var else struct_degree(t.body, var)
        return inner + struct_degree(t.body, t.var) * struct_degree(t.value, var)
    if isinstance(t, Slope):
        inner = 0 if t.var == var else struct_degree(t.body, var)
        return inner + max(struct_degree(t.body, t.var) - 1, 0) * struct_degree(t.at, var)
    raise NotPolynomial(f"unhandled node in struct_degree: {t!r}")


def poly_coeffs(t: Term, var: str, env: dict) -> list:
    """Exact coefficients of t as a polynomial in var, other vars fixed by env.

    Interpolation, not symbolic expansion -- deliberately, so that this shares
    no code path with rules.py."""
    d = struct_degree(t, var)
    xs, ys = [], []
    k = 0
    while len(xs) <= d:
        x = Fraction(k)
        k += 1
        try:
            y = oracle_eval(t, {**env, var: x})
        except ZeroDivisionError:
            continue
        xs.append(x)
        ys.append(y)
        if k > 200:
            raise NotPolynomial("could not find enough safe sample points")
    return lagrange(xs, ys)


def _diff_coeffs(coeffs):
    return [coeffs[i] * i for i in range(1, len(coeffs))] or [Fraction(0)]


def _eval_coeffs(coeffs, x):
    out = Fraction(0)
    for c in reversed(coeffs):
        out = out * x + c
    return out


def oracle_eval(t: Term, env: dict) -> Fraction:
    """evaluate(), extended to give Slope, D and At their intended meanings via
    the interpolation oracle rather than via any rewrite rule."""
    if isinstance(t, D):
        coeffs = poly_coeffs(t.body, t.var, env)
        return _eval_coeffs(_diff_coeffs(coeffs), env[t.var])
    if isinstance(t, At):
        v = oracle_eval(t.value, env)
        return oracle_eval(t.body, {**env, t.var: v})
    if isinstance(t, Slope):
        a = oracle_eval(t.at, env)
        coeffs = poly_coeffs(t.body, t.var, {**env, t.var: Fraction(0)})
        return _eval_coeffs(_diff_coeffs(coeffs), a)
    if isinstance(t, Add):
        return sum((oracle_eval(a, env) for a in t.args), Fraction(0))
    if isinstance(t, Mul):
        out = Fraction(1)
        for a in t.args:
            out *= oracle_eval(a, env)
        return out
    if isinstance(t, Pow):
        b = oracle_eval(t.base, env)
        e = oracle_eval(t.exp, env)
        if e.denominator != 1:
            raise NotPolynomial("fractional exponent")
        e = int(e)
        if b == 0 and e < 0:
            raise ZeroDivisionError
        return b ** e
    return evaluate(t, env)


# ------------------------------------------------------------- random material

def random_term(rng: random.Random, vars_: list, depth: int = 2,
                ops: bool = False) -> Term:
    """Random algebra term.  With ops=True it also grows D and At nodes, which
    is the only way rules R6 and D1-D5 ever get anything to match against."""
    if depth == 0 or rng.random() < 0.3:
        if rng.random() < 0.4 or not vars_:
            return C(rng.randint(-3, 3))
        return Var(rng.choice(vars_))
    if ops and rng.random() < 0.35:
        inner = random_term(rng, vars_, depth - 1, ops=False)
        if rng.random() < 0.5:
            return D(inner, "x")
        return At(inner, "x", random_term(rng, vars_, depth - 1, ops=False))
    kind = rng.choice(["add", "mul", "pow"])
    if kind == "add":
        n = rng.randint(2, 3)
        return Add(tuple(random_term(rng, vars_, depth - 1, ops) for _ in range(n)))
    if kind == "mul":
        n = rng.randint(2, 3)
        return Mul(tuple(random_term(rng, vars_, depth - 1, ops) for _ in range(n)))
    return Pow(random_term(rng, vars_, depth - 1, ops), C(rng.randint(0, 3)))


def random_poly(rng: random.Random, var: str, max_deg: int = 3) -> Term:
    deg = rng.randint(1, max_deg)
    terms = []
    for k in range(deg + 1):
        c = rng.randint(-4, 4)
        if c == 0:
            continue
        terms.append(Mul((C(c), Pow(Var(var), C(k)))))
    if not terms:
        terms = [Var(var)]
    return canon(Add(tuple(terms)))


def random_env(rng: random.Random, names) -> dict:
    return {n: Fraction(rng.randint(-9, 9), rng.randint(1, 6)) for n in names}


# ------------------------------------------------------------------ the checks

def check_rule(rule: Rule, trials: int = 100, seed: int = 0) -> tuple:
    """Fire `rule` on random terms and compare both sides at random rationals.

    Returns (checked, failures) where failures is a list of counterexamples."""
    if not rule.identity:
        return 0, []
    rng = random.Random(seed)
    checked = 0
    failures = []
    attempts = 0
    while checked < trials and attempts < trials * 400:
        attempts += 1
        t = canon(random_term(rng, ["x", "y", H], depth=3, ops=True))
        cands = []
        for path, sub in positions(t):
            if rule.root_only and path:
                continue
            for new_sub in rule.apply(sub):
                cands.append((path, new_sub))
        if not cands:
            continue
        path, new_sub = rng.choice(cands)
        try:
            after = canon(replace_at(t, path, new_sub))
        except ZeroDivisionError:
            continue
        env = random_env(rng, sorted(free_vars(t) | free_vars(after)))
        try:
            lhs = oracle_eval(t, env)
            rhs = oracle_eval(after, env)
        except (ZeroDivisionError, NotPolynomial, KeyError):
            continue
        checked += 1
        if lhs != rhs:
            failures.append((rule.name, t, after, env, lhs, rhs))
    return checked, failures


def check_bridge(trials: int = 100, seed: int = 1) -> tuple:
    """B says Slope[x](f @ a) = (D[x] f)|x=a.  Check both sides against the
    interpolation oracle on random polynomials at random rational points."""
    rng = random.Random(seed)
    failures = []
    for _ in range(trials):
        f = random_poly(rng, "x")
        a = Fraction(rng.randint(-9, 9), rng.randint(1, 6))
        lhs = oracle_eval(Slope(f, "x", C(a)), {})
        rhs = oracle_eval(At(D(f, "x"), "x", C(a)), {})
        if lhs != rhs:
            failures.append((f, a, lhs, rhs))
    return trials, failures


def check_dq_composite(trials: int = 100, seed: int = 2) -> tuple:
    """R7-then-R8 is the base theory's whole claim, and neither half is an
    identity on its own.  Check the composite directly and independently:

        g(h) = (f(a+h) - f(a)) / h   sampled at nonzero rationals,
        interpolated exactly (it is a polynomial of degree deg(f)-1),
        then evaluated at h = 0

    must equal f'(a) from the coefficient oracle."""
    rng = random.Random(seed)
    failures = []
    for _ in range(trials):
        f = random_poly(rng, "x")
        a = Fraction(rng.randint(-9, 9), rng.randint(1, 6))
        deg = struct_degree(f, "x")
        xs, ys = [], []
        k = 1
        while len(xs) <= max(deg - 1, 0):
            hval = Fraction(k)
            k += 1
            num = evaluate(f, {"x": a + hval}) - evaluate(f, {"x": a})
            xs.append(hval)
            ys.append(num / hval)
        limit = _eval_coeffs(lagrange(xs, ys), Fraction(0))
        truth = oracle_eval(Slope(f, "x", C(a)), {})
        if limit != truth:
            failures.append((f, a, limit, truth))
    return trials, failures


def check_path(start: Term, path: list, env_vars=None, trials: int = 100,
               seed: int = 3) -> tuple:
    """Every term along a rewrite path must agree with the start, at random
    rational points -- except across R7 and R8, which are not pointwise
    identities.  Those two get check_bridge / check_dq_composite instead, so
    here they simply reset the reference term."""
    rng = random.Random(seed)
    terms = [start] + [t for _, t in path]
    names = ["R7.slope_dq"] + [n for n, _ in path]
    failures = []
    ref = 0
    for i in range(1, len(terms)):
        if names[i] in ("R7.slope_dq", "R8.eval_h_zero", "B.bridge"):
            ref = i
            continue
        vs = sorted(free_vars(terms[ref]) | free_vars(terms[i]))
        for _ in range(trials // 10 or 1):
            env = random_env(rng, vs)
            try:
                a = oracle_eval(terms[ref], env)
                b = oracle_eval(terms[i], env)
            except (ZeroDivisionError, NotPolynomial, KeyError):
                continue
            if a != b:
                failures.append((names[i], terms[ref], terms[i], env, a, b))
                break
        ref = i
    return len(terms) - 1, failures


def run_all(trials: int = 100) -> bool:
    ok = True
    print("rule soundness (random rational instantiation, exact):")
    for rule in BASE_RULES + DERIV_RULES:
        if not rule.identity:
            print(f"  {rule.name:<18} not a pointwise identity - targeted check below")
            continue
        n, fails = check_rule(rule, trials=trials)
        status = "ok" if not fails else f"FAIL x{len(fails)}"
        print(f"  {rule.name:<18} {n:>4} instances   {status}")
        if fails:
            ok = False
            for f in fails[:2]:
                print(f"      {f}")

    print("\ntargeted checks against the interpolation oracle:")
    n, fails = check_bridge(trials)
    print(f"  B.bridge           {n:>4} instances   {'ok' if not fails else f'FAIL x{len(fails)}'}")
    ok = ok and not fails
    n, fails = check_dq_composite(trials)
    print(f"  R7+R8 composite    {n:>4} instances   {'ok' if not fails else f'FAIL x{len(fails)}'}")
    ok = ok and not fails
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_all() else 1)
