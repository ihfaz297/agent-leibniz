"""Term algebra for Track 0.

A tagged union of Const, Var, Add, Mul, Pow, plus three operator nodes used to
pose tangent-slope problems and to carry a candidate abstraction:

    Slope(body, var, at)   the thing we are asked for: slope of the tangent to
                           `body` (a term in `var`) at the point `at`
    D(body, var)           formal derivative operator -- the candidate abstraction
    At(body, var, value)   deferred substitution, so a rule can hand back an
                           unevaluated "evaluate this here"

Everything is a frozen dataclass: terms are immutable and hashable, which the
search's visited table depends on.  Numeric values are always Fraction, never
float (CLAUDE.md, non-negotiable #1).

Add and Mul are n-ary.  Nothing in this module normalizes; construction is
literal.  Normalization lives in canon.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from typing import Union


@dataclass(frozen=True)
class Const:
    value: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.value, Fraction):
            object.__setattr__(self, "value", Fraction(self.value))

    def __repr__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Var:
    name: str

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Add:
    args: tuple

    def __repr__(self) -> str:
        return "(" + " + ".join(repr(a) for a in self.args) + ")"


@dataclass(frozen=True)
class Mul:
    args: tuple

    def __repr__(self) -> str:
        return "(" + "*".join(repr(a) for a in self.args) + ")"


@dataclass(frozen=True)
class Pow:
    base: "Term"
    exp: "Term"

    def __repr__(self) -> str:
        return f"{self.base!r}^{self.exp!r}"


@dataclass(frozen=True)
class Slope:
    body: "Term"
    var: str
    at: "Term"

    def __repr__(self) -> str:
        return f"Slope[{self.var}]({self.body!r} @ {self.at!r})"


@dataclass(frozen=True)
class D:
    body: "Term"
    var: str

    def __repr__(self) -> str:
        return f"D[{self.var}]({self.body!r})"


@dataclass(frozen=True)
class At:
    body: "Term"
    var: str
    value: "Term"

    def __repr__(self) -> str:
        return f"({self.body!r})|{self.var}={self.value!r}"


Term = Union[Const, Var, Add, Mul, Pow, Slope, D, At]

ALGEBRA = (Const, Var, Add, Mul, Pow)
OPERATORS = (Slope, D, At)


# ---------------------------------------------------------------- constructors

def C(v) -> Const:
    return Const(Fraction(v))


def V(n: str) -> Var:
    return Var(n)


def add(*args) -> Add:
    return Add(tuple(args))


def mul(*args) -> Mul:
    return Mul(tuple(args))


def pw(base, exp) -> Pow:
    return Pow(base, exp if not isinstance(exp, (int, Fraction)) else C(exp))


def neg(t) -> Mul:
    return Mul((C(-1), t))


def sub(a, b) -> Add:
    return Add((a, neg(b)))


ZERO = C(0)
ONE = C(1)


# ------------------------------------------------------------------- traversal

def children(t: Term) -> tuple:
    """Uniform child access.  Binder names (var) are not children."""
    if isinstance(t, (Const, Var)):
        return ()
    if isinstance(t, Pow):
        return (t.base, t.exp)
    if isinstance(t, (Add, Mul)):
        return t.args
    if isinstance(t, Slope):
        return (t.body, t.at)
    if isinstance(t, D):
        return (t.body,)
    if isinstance(t, At):
        return (t.body, t.value)
    raise TypeError(f"not a term: {t!r}")


def rebuild(t: Term, cs: tuple) -> Term:
    """Same node shape, new children."""
    if isinstance(t, (Const, Var)):
        return t
    if isinstance(t, Pow):
        return Pow(cs[0], cs[1])
    if isinstance(t, Add):
        return Add(tuple(cs))
    if isinstance(t, Mul):
        return Mul(tuple(cs))
    if isinstance(t, Slope):
        return Slope(cs[0], t.var, cs[1])
    if isinstance(t, D):
        return D(cs[0], t.var)
    if isinstance(t, At):
        return At(cs[0], t.var, cs[1])
    raise TypeError(f"not a term: {t!r}")


def positions(t: Term, path: tuple = ()):
    """Yield (path, subterm) for every node, root first."""
    yield path, t
    for i, c in enumerate(children(t)):
        yield from positions(c, path + (i,))


def replace_at(t: Term, path: tuple, new: Term) -> Term:
    if not path:
        return new
    cs = list(children(t))
    cs[path[0]] = replace_at(cs[path[0]], path[1:], new)
    return rebuild(t, tuple(cs))


# ---------------------------------------------------------------- substitution

def subst(t: Term, var: str, value: Term) -> Term:
    """Capture-avoiding in the only sense we need: Slope, D and At all bind
    their `var` inside `body`, so a substitution for that same name stops at
    the binder (but still descends into the non-body children)."""
    if isinstance(t, Var):
        return value if t.name == var else t
    if isinstance(t, Const):
        return t
    if isinstance(t, Slope):
        body = t.body if t.var == var else subst(t.body, var, value)
        return Slope(body, t.var, subst(t.at, var, value))
    if isinstance(t, D):
        return t if t.var == var else D(subst(t.body, var, value), t.var)
    if isinstance(t, At):
        body = t.body if t.var == var else subst(t.body, var, value)
        return At(body, t.var, subst(t.value, var, value))
    return rebuild(t, tuple(subst(c, var, value) for c in children(t)))


def free_vars(t: Term) -> frozenset:
    if isinstance(t, Var):
        return frozenset({t.name})
    if isinstance(t, Const):
        return frozenset()
    if isinstance(t, Slope):
        return (free_vars(t.body) - {t.var}) | free_vars(t.at)
    if isinstance(t, D):
        # D[x] f is still a function of x -- the binder does not remove it.
        return free_vars(t.body) | {t.var}
    if isinstance(t, At):
        return (free_vars(t.body) - {t.var}) | free_vars(t.value)
    out = frozenset()
    for c in children(t):
        out |= free_vars(c)
    return out


def contains(t: Term, kind) -> bool:
    """Is there a node of type `kind` anywhere in t?"""
    if isinstance(t, kind):
        return True
    return any(contains(c, kind) for c in children(t))


def size(t: Term) -> int:
    return 1 + sum(size(c) for c in children(t))


# ------------------------------------------------------------------ total order
# Needed so canon can sort n-ary args into a canonical sequence.  The order is
# arbitrary but must be total and stable across runs.

_RANK = {Const: 0, Var: 1, Pow: 2, Mul: 3, Add: 4, At: 5, D: 6, Slope: 7}


@lru_cache(maxsize=None)
def sort_key(t: Term):
    rank = _RANK[type(t)]
    name = ""
    num = Fraction(0)
    if isinstance(t, Const):
        num = t.value
    elif isinstance(t, Var):
        name = t.name
    elif isinstance(t, (Slope, D, At)):
        name = t.var
    return (rank, name, num, tuple(sort_key(c) for c in children(t)))
