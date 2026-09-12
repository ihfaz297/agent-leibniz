"""Iterative-deepening search over rewrites.  The step count is the measurement.

Iterative deepening rather than plain BFS so that the frontier never has to be
held in memory, with a per-iteration visited table so the usual IDDFS blowup is
bounded: within one depth limit, a term reached again at an equal or greater
depth is pruned.

The number this file produces -- the length of the shortest rewrite path from
the problem statement to a closed form -- is the whole instrument.  Everything
else in Track 0 exists to make it trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from canon import canon
from rules import H, Rule
from terms import (
    At,
    D,
    Slope,
    Term,
    contains,
    free_vars,
    positions,
    replace_at,
)

DEFAULT_MAX_DEPTH = 12
DEFAULT_NODE_BUDGET = 400_000


class BudgetExceeded(Exception):
    pass


@dataclass
class SearchResult:
    #: "found" | "depth_exhausted" | "budget_exceeded"
    status: str
    steps: Optional[int] = None
    path: list = field(default_factory=list)  # [(rule_name, resulting_term)]
    nodes: int = 0
    depth_reached: int = 0

    @property
    def found(self) -> bool:
        return self.status == "found"

    def __str__(self) -> str:
        if self.found:
            return f"{self.steps} steps ({self.nodes} nodes expanded)"
        return f"NO PATH: {self.status} at depth {self.depth_reached} ({self.nodes} nodes)"


def is_closed_form(t: Term) -> bool:
    """Goal test: the problem's operators are all discharged and the increment
    variable is gone.  What remains is an ordinary pre-calculus expression."""
    if contains(t, (Slope, D, At)):
        return False
    return H not in free_vars(t)


def successors(t: Term, rules, closure: int = 1) -> dict:
    """{canonical successor term: name of the rule that got there}.

    Deduplicated, and self-loops dropped: a rewrite that canon undoes is not a
    step, it is a no-op, and counting it would inflate every path.

    `closure` > 1 admits *local* compositions as single steps: after a rule
    fires at some position and produces `new_sub`, a further rule may fire
    anywhere inside `new_sub` (canonicalized on its own first, which is what
    the whole-term canon would do to it, since canon is bottom-up), and the
    composite counts as one step.  Up to `closure` rules may chain this way.
    The locality is the point: a global "any k steps = 1" would just divide
    every path length by k and measure nothing.  Local closure is the
    mechanical, rule-set-symmetric version of "a derived lemma is one step" --
    D(c*u) -> c*D(u) falls out of D4-then-D1 without being written down, and
    the base gets the same treatment for R6-then-R1 and friends.  Which rule
    sets gain more is what it measures.  LEDGER.md 2026-09-12."""
    out: dict = {}
    for path, sub in positions(t):
        for r in rules:
            if r.root_only and path:
                continue
            for new_sub in r.apply(sub):
                for names, final_sub in _local_chain(new_sub, rules, closure - 1,
                                                     at_root=not path):
                    try:
                        nt = canon(replace_at(t, path, final_sub))
                    except ZeroDivisionError:
                        continue
                    if nt != t and nt not in out:
                        out[nt] = ">".join((r.name,) + names)
    return out


def _local_chain(sub: Term, rules, remaining: int, at_root: bool):
    """Yield (rule names, resulting subterm) for every chain of up to
    `remaining` further rules fired strictly inside `sub`.  The empty chain
    is always yielded first, so a plain single step is always available."""
    yield (), sub
    if remaining <= 0:
        return
    try:
        sub = canon(sub)
    except ZeroDivisionError:
        return
    for inner_path, inner in positions(sub):
        for r in rules:
            if r.root_only and (inner_path or not at_root):
                continue
            for new_inner in r.apply(inner):
                nxt = replace_at(sub, inner_path, new_inner)
                for names, final in _local_chain(nxt, rules, remaining - 1, at_root):
                    yield (r.name,) + names, final


def search(
    start: Term,
    rules,
    goal: Callable[[Term], bool] = is_closed_form,
    max_depth: int = DEFAULT_MAX_DEPTH,
    node_budget: int = DEFAULT_NODE_BUDGET,
    closure: int = 1,
) -> SearchResult:
    start = canon(start)
    nodes = 0
    reached = 0

    for limit in range(max_depth + 1):
        reached = limit
        seen: dict = {}

        def dfs(t: Term, depth: int, path: list):
            nonlocal nodes
            if goal(t):
                return path
            if depth == limit:
                return None
            prev = seen.get(t)
            if prev is not None and prev <= depth:
                return None
            seen[t] = depth
            for nt, rname in successors(t, rules, closure).items():
                nodes += 1
                if nodes > node_budget:
                    raise BudgetExceeded
                got = dfs(nt, depth + 1, path + [(rname, nt)])
                if got is not None:
                    return got
            return None

        try:
            got = dfs(start, 0, [])
        except BudgetExceeded:
            return SearchResult("budget_exceeded", nodes=nodes, depth_reached=reached)
        if got is not None:
            return SearchResult("found", steps=len(got), path=got, nodes=nodes,
                                depth_reached=reached)

    return SearchResult("depth_exhausted", nodes=nodes, depth_reached=reached)


def format_path(start: Term, result: SearchResult) -> str:
    lines = [f"    start   {start!r}"]
    for i, (rname, term) in enumerate(result.path, 1):
        lines.append(f"    {i:>2}. {rname:<18} {term!r}")
    return "\n".join(lines)
