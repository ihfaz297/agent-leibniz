"""Rewrite rules.  One application = one step of path length.

Two sets:

  BASE   R1-R9.  Pre-calculus only.  No limits, no derivative.  The tangent
         slope is reached by forming a difference quotient, cancelling the h
         algebraically (valid because h != 0 while cancelling), and then
         substituting h = 0 -- which is licensed for a polynomial without any
         limit machinery, because after cancellation the expression is a
         polynomial and polynomials are total.

  DERIV  D1-D5 plus the bridge B.  The candidate abstraction.

Rules are deliberately oriented (expansion direction only: distribute, never
factor).  That keeps the search tractable, and it *helps* the base path, so it
biases against the compression result we expect to see.  Recorded in LEDGER.md.

A rule is applied at the root of whatever subterm the search hands it and
returns zero or more replacement terms.  The search canonicalizes the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

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
    contains,
    free_vars,
    positions,
    subst,
)

H = "h"  # the increment variable used by the base difference quotient


@dataclass(frozen=True)
class Rule:
    name: str
    fn: Callable[[Term], list]
    #: True if lhs == rhs as functions of their free variables, so verify.py
    #: can check it by random rational instantiation.  False means the rule is
    #: sound for a reason the pointwise checker cannot see (see verify.py for
    #: the targeted checks those get instead).
    identity: bool = True
    #: True if the rule is a whole-term operation and must only fire at the root.
    root_only: bool = False

    def apply(self, t: Term) -> list:
        return self.fn(t)


# ------------------------------------------------------------------ base rules

def _r1_distribute(t: Term) -> list:
    """R1  (p1 + ... + pn) * rest  ->  p1*rest + ... + pn*rest"""
    if not isinstance(t, Mul):
        return []
    out = []
    for i, f in enumerate(t.args):
        if isinstance(f, Add):
            rest = t.args[:i] + t.args[i + 1:]
            out.append(Add(tuple(Mul((p,) + rest) for p in f.args)))
    return out


def _r2_pow_add_expand(t: Term) -> list:
    """R2  (p1 + ... + pn)^k  ->  p1*(...)^(k-1) + ... + pn*(...)^(k-1)   k >= 2

    Peels one factor off a power of a sum.  Combined with R1 this gives full
    binomial expansion, one product at a time."""
    if not (isinstance(t, Pow) and isinstance(t.base, Add) and isinstance(t.exp, Const)):
        return []
    k = t.exp.value
    if k.denominator != 1 or k < 2:
        return []
    inner = Pow(t.base, C(k - 1))
    return [Add(tuple(Mul((p, inner)) for p in t.base.args))]


def _split_coeff(u: Term):
    """u  ->  (rational coefficient, the rest)"""
    if isinstance(u, Const):
        return u.value, C(1)
    if isinstance(u, Mul):
        coeff = Fraction(1)
        rest = []
        for f in u.args:
            if isinstance(f, Const):
                coeff *= f.value
            else:
                rest.append(f)
        if not rest:
            return coeff, C(1)
        return coeff, (rest[0] if len(rest) == 1 else Mul(tuple(rest)))
    return Fraction(1), u


def _r3_collect_like(t: Term) -> list:
    """R3  c1*u + c2*u  ->  (c1 + c2)*u"""
    if not isinstance(t, Add):
        return []
    split = [_split_coeff(a) for a in t.args]
    out = []
    n = len(t.args)
    for i in range(n):
        for j in range(i + 1, n):
            if split[i][1] != split[j][1]:
                continue
            merged = Mul((C(split[i][0] + split[j][0]), split[i][1]))
            rest = [t.args[k] for k in range(n) if k != i and k != j]
            out.append(Add(tuple(rest) + (merged,)))
    return out


def _r4_pow_of_mul(t: Term) -> list:
    """R4  (u*v)^n  ->  u^n * v^n"""
    if not (isinstance(t, Pow) and isinstance(t.base, Mul)):
        return []
    return [Mul(tuple(Pow(f, t.exp) for f in t.base.args))]


def _r5_pow_of_pow(t: Term) -> list:
    """R5  (u^m)^n  ->  u^(m*n)"""
    if not (isinstance(t, Pow) and isinstance(t.base, Pow)):
        return []
    if not (isinstance(t.exp, Const) and isinstance(t.base.exp, Const)):
        return []
    return [Pow(t.base.base, C(t.base.exp.value * t.exp.value))]


def _r6_at_elim(t: Term) -> list:
    """R6  (f)|x=v  ->  f[x := v]

    Refuses while an unresolved D sits inside f: substituting into D(x) would
    turn it into D(a), which is not what evaluating a derivative at a point
    means.  The D rules have to fire first."""
    if not isinstance(t, At):
        return []
    if contains(t.body, D):
        return []
    return [subst(t.body, t.var, t.value)]


def _r7_slope_dq(t: Term) -> list:
    """R7  Slope[x](f @ a)  ->  (f|x=a+h - f|x=a) * h^-1

    The base theory's only handle on "slope of the tangent". Not a pointwise
    identity: the two sides agree only in the h -> 0 sense, which is exactly
    what R8 finishes.  Soundness of the R7-then-R8 composite is what verify.py
    checks."""
    if not isinstance(t, Slope):
        return []
    h = Var(H)
    fwd = At(t.body, t.var, Add((t.at, h)))
    here = At(t.body, t.var, t.at)
    return [Mul((Add((fwd, Mul((C(-1), here)))), Pow(h, C(-1))))]


def _h_elimination_is_safe(t: Term) -> bool:
    """h := 0 is licensed once no h remains under a negative or fractional
    power, and no h sits in an exponent.  At that point the term is polynomial
    in h and substitution is total."""
    for _, sub_t in positions(t):
        if not isinstance(sub_t, Pow):
            continue
        if H in free_vars(sub_t.exp):
            return False
        if isinstance(sub_t.exp, Const):
            e = sub_t.exp.value
            if (e < 0 or e.denominator != 1) and H in free_vars(sub_t.base):
                return False
        elif H in free_vars(sub_t.base):
            return False
    return True


def _r8_eval_h_zero(t: Term) -> list:
    """R8  substitute h := 0, once the term is polynomial in h."""
    if H not in free_vars(t):
        return []
    if not _h_elimination_is_safe(t):
        return []
    return [subst(t, H, C(0))]


#: Eight rules, not the nine CLAUDE.md sketched.  The ninth would have been the
#: power law u^m * u^n -> u^(m+n); it is free in canon instead (see canon.py's
#: header for why, and LEDGER.md for what that costs us).
BASE_RULES = (
    Rule("R1.distribute", _r1_distribute),
    Rule("R2.pow_add_expand", _r2_pow_add_expand),
    Rule("R3.collect_like", _r3_collect_like),
    Rule("R4.pow_of_mul", _r4_pow_of_mul),
    Rule("R5.pow_of_pow", _r5_pow_of_pow),
    Rule("R6.at_elim", _r6_at_elim),
    Rule("R7.slope_dq", _r7_slope_dq, identity=False),
    Rule("R8.eval_h_zero", _r8_eval_h_zero, identity=False, root_only=True),
)


# ------------------------------------------------------------ derivative rules

def _d1_const(t: Term) -> list:
    if isinstance(t, D) and isinstance(t.body, Const):
        return [C(0)]
    return []


def _d2_var(t: Term) -> list:
    if isinstance(t, D) and isinstance(t.body, Var):
        return [C(1) if t.body.name == t.var else C(0)]
    return []


def _d3_add(t: Term) -> list:
    if isinstance(t, D) and isinstance(t.body, Add):
        return [Add(tuple(D(a, t.var) for a in t.body.args))]
    return []


def _d4_mul(t: Term) -> list:
    """n-ary Leibniz."""
    if not (isinstance(t, D) and isinstance(t.body, Mul)):
        return []
    args = t.body.args
    terms = []
    for i in range(len(args)):
        parts = args[:i] + (D(args[i], t.var),) + args[i + 1:]
        terms.append(Mul(parts))
    return [Add(tuple(terms))]


def _d5_pow(t: Term) -> list:
    """D(u^n) -> n * u^(n-1) * D(u)   for literal n."""
    if not (isinstance(t, D) and isinstance(t.body, Pow)):
        return []
    p = t.body
    if not isinstance(p.exp, Const):
        return []
    n = p.exp.value
    return [Mul((C(n), Pow(p.base, C(n - 1)), D(p.base, t.var)))]


def _b_bridge(t: Term) -> list:
    """B  Slope[x](f @ a)  ->  (D[x] f)|x=a

    The whole claim of the abstraction, in one rule."""
    if not isinstance(t, Slope):
        return []
    return [At(D(t.body, t.var), t.var, t.at)]


DERIV_RULES = (
    Rule("D1.const", _d1_const),
    Rule("D2.var", _d2_var),
    Rule("D3.add", _d3_add),
    Rule("D4.mul", _d4_mul),
    Rule("D5.pow", _d5_pow),
    Rule("B.bridge", _b_bridge, identity=False),
)


#: Configuration 1 -- pre-calculus only.  R7/R8 are the only route to a slope.
BASE_ONLY = BASE_RULES

#: Configuration 2 -- the abstraction is the only route to a slope.  R7 and R8
#: are withheld, so the reported length is the cost of the derivative path
#: itself.  Without this column a zero gap is unreadable: it could mean the
#: abstraction saves nothing, or that the base route simply happened to be
#: shorter and the search took it.
DERIV_ONLY = tuple(r for r in BASE_RULES
                   if r.name not in ("R7.slope_dq", "R8.eval_h_zero")) + DERIV_RULES

#: Configuration 3 -- everything available.  This is the honest "what would an
#: agent with both do" number, and it is min(base, deriv) by construction.
WITH_DERIV = BASE_RULES + DERIV_RULES

ALL_RULES = WITH_DERIV
