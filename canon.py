"""Canonicalization.  Runs after every rewrite; costs zero search steps.

CLAUDE.md, non-negotiable #2: AC normalization is free.  This file is where the
line between "free" and "searched" actually gets drawn, so the line is written
down here explicitly rather than left implicit in the code.

FREE (done here, not counted as a step):
  - flatten nested Add/Mul into n-ary nodes
  - sort n-ary args by terms.sort_key           (commutativity)
  - fold numeric literals: 2*3 -> 6, 2+3 -> 5
  - identities: x+0 -> x, x*1 -> x, x*0 -> 0, x^1 -> x, x^0 -> 1
  - combine like powers inside a single Mul: u^m * u^n -> u^(m+n)

SEARCHED (rules.py, each application counts as one step):
  - distributivity, in either direction
  - collecting like terms across an Add: c1*u + c2*u -> (c1+c2)*u
  - (u*v)^n, (u^m)^n
  - anything touching Slope, D or At

The one judgement call is combining like powers inside a Mul.  It is bookkeeping
in any canonical polynomial representation, and it is what makes h * h^-1 -> 1
free -- which is the cancellation the base path leans on.  That choice flatters
the base path (makes it shorter), so it biases *against* the result we expect.
Recorded in LEDGER.md.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

from terms import (
    Add,
    At,
    Const,
    D,
    Mul,
    Pow,
    Slope,
    Term,
    Var,
    children,
    rebuild,
    sort_key,
)


@lru_cache(maxsize=None)
def canon(t: Term) -> Term:
    t = rebuild(t, tuple(canon(c) for c in children(t)))
    if isinstance(t, Add):
        return _canon_add(t)
    if isinstance(t, Mul):
        return _canon_mul(t)
    if isinstance(t, Pow):
        return _canon_pow(t)
    return t


def _flatten(t, kind) -> list:
    out = []
    for a in t.args:
        if isinstance(a, kind):
            out.extend(a.args)
        else:
            out.append(a)
    return out


def _canon_add(t: Add) -> Term:
    flat = _flatten(t, Add)
    total = Fraction(0)
    rest = []
    for a in flat:
        if isinstance(a, Const):
            total += a.value
        else:
            rest.append(a)
    rest.sort(key=sort_key)
    if total != 0:
        rest.insert(0, Const(total))
    if not rest:
        return Const(Fraction(0))
    if len(rest) == 1:
        return rest[0]
    return Add(tuple(rest))


def _as_base_exp(f: Term):
    """Split a Mul factor into (base, exponent) when the exponent is a literal.
    Anything else is opaque and gets exponent 1."""
    if isinstance(f, Pow) and isinstance(f.exp, Const):
        return f.base, f.exp.value
    return f, Fraction(1)


def _canon_mul(t: Mul) -> Term:
    flat = _flatten(t, Mul)
    coeff = Fraction(1)
    powers: dict = {}
    for f in flat:
        base, exp = _as_base_exp(f)
        if isinstance(base, Const):
            if exp.denominator == 1:
                if base.value == 0 and exp < 0:
                    raise ZeroDivisionError("0 raised to a negative power")
                coeff *= base.value ** int(exp)
                continue
            # a genuine radical; leave it opaque
        powers[base] = powers.get(base, Fraction(0)) + exp
    if coeff == 0:
        return Const(Fraction(0))

    factors = []
    for base, exp in powers.items():
        if exp == 0:
            continue
        factors.append(base if exp == 1 else Pow(base, Const(exp)))
    factors.sort(key=sort_key)

    if coeff != 1:
        factors.insert(0, Const(coeff))
    if not factors:
        return Const(coeff)
    if len(factors) == 1:
        return factors[0]
    return Mul(tuple(factors))


def _canon_pow(t: Pow) -> Term:
    if isinstance(t.exp, Const):
        if t.exp.value == 0:
            return Const(Fraction(1))
        if t.exp.value == 1:
            return t.base
        if isinstance(t.base, Const) and t.exp.value.denominator == 1:
            if t.base.value == 0 and t.exp.value < 0:
                raise ZeroDivisionError("0 raised to a negative power")
            return Const(t.base.value ** int(t.exp.value))
        if isinstance(t.base, Const) and t.base.value == 1:
            return Const(Fraction(1))
    return t
