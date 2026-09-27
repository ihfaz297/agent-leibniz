"""The obfuscation layer -- the control that separates search from recall.

A proposer that has read every calculus textbook will emit D1-D5 the moment it sees
the word "slope".  The only way to find out whether it is searching or reciting is to
take the vocabulary away and see what survives.  That is what this file does, and it
is mechanical: no judgement, no hand-written alternative prompts, so the arms differ
only in naming.

Three things get renamed, and the third is the one people forget:

  1. operator names     Slope -> a meaningless symbol
  2. rule names         R1.distribute -> r1
  3. RULE DESCRIPTIONS  each rule is described by EXAMPLE -- fire it on a sample term
                        and show before -> after -- never by an English name.  A rule
                        called "distribute" leaks its own semantics; `r1` shown turning
                        (a + b)*c into a*c + b*c leaks nothing but what it does.

The arms:

  ARM 1  PLAIN     real names, calculus vocabulary present.  The contamination ceiling.
  ARM 2  RENAMED   same mathematics, opaque symbols, no calculus word anywhere.

Arms 3 and 4 (a different target, and a novel operator) need the Delta base, which does
not exist yet -- see NEXT.md.

**What arm 2 does NOT control, and this limits what a pass there means.**  Renaming
removes VOCABULARY, not STRUCTURE.  Rule r7 is the base's own route to a GOAL term and
its demonstration shows GOAL becoming (f@(a+h) - f@a) * h^-1 -- a difference quotient,
recognisable on sight to anyone who has seen one, whatever it is called.  So a model can
still identify the target structurally in arm 2.  Withholding r7 is not an option: it is
part of the base, and hiding it would misrepresent the system the proposer is reasoning
about.  Arm 2 therefore measures whether the proposer needs the WORDS.  It does not
measure whether it needs the target to be familiar.  Only arms 3 and 4 do that.

Nothing here touches `rules.py`.  The search does not read names, so obfuscation cannot
change any measurement; it only changes what the proposer is told.  That is the point:
if the numbers move between arms, the difference is the proposer's vocabulary, not ours.
"""

from __future__ import annotations

from fractions import Fraction

from canon import canon
from rules import BASE_RULES
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
    V,
    Var,
    positions,
)

#: Arm 1.  Everything keeps its real name.
PLAIN = {
    "Slope": "Slope",
    "D": "D",
    "At": "|",
    "rule_prefix": None,          # keep real rule names
    "operator_blurb": (
        "Slope[x](f @ a) is the slope of the tangent line to f at the point x = a. "
        "D[x] f is the derivative of f with respect to x. "
        "(f)|x=v evaluates f at x = v."
    ),
    "task_blurb": (
        "Propose rewrite rules for the derivative operator D so that Slope problems "
        "can be solved without forming a difference quotient."
    ),
}

#: Arm 2.  Opaque symbols, and no word from the target's vocabulary anywhere.
OPAQUE = {
    "Slope": "GOAL",
    "D": "OP",
    "At": "@",
    "rule_prefix": "r",           # R1.distribute -> r1
    "operator_blurb": (
        "GOAL[x](f % a) is a closed-term-valued operator on a term f, a variable x, "
        "and a term a. OP[x] f is an operator on a term f and a variable x. "
        "(f)@x=v replaces every free x in f by v."
    ),
    "task_blurb": (
        "The rules below cannot reduce GOAL terms except by one long route. "
        "Propose additional rewrite rules for OP, and one rule relating GOAL to OP, "
        "such that GOAL terms reduce in fewer steps. You are told nothing about what "
        "these operators mean; infer what OP must satisfy from the rules you are given "
        "and from the examples."
    ),
}

#: Words that must never appear in an obfuscated prompt.  Checked, not trusted.
BANNED = (
    "deriv", "slope", "tangent", "calculus", "differenti", "limit", "infinitesimal",
    "rate of change", "instantaneous", "gradient", "leibniz", "newton", "d/dx",
    "difference quotient", "power rule", "product rule", "chain rule",
)


def render(t: Term, names: dict) -> str:
    """Render a term with operator names taken from `names`.  Pure syntax: no rule
    is consulted, so this cannot leak semantics."""
    r = lambda u: render(u, names)
    if isinstance(t, Const):
        v = t.value
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if isinstance(t, Var):
        return t.name
    if isinstance(t, Add):
        return "(" + " + ".join(r(a) for a in t.args) + ")"
    if isinstance(t, Mul):
        return "(" + "*".join(r(a) for a in t.args) + ")"
    if isinstance(t, Pow):
        return f"{r(t.base)}^{r(t.exp)}"
    if isinstance(t, Slope):
        sep = "@" if names["Slope"] == "Slope" else "%"
        return f"{names['Slope']}[{t.var}]({r(t.body)} {sep} {r(t.at)})"
    if isinstance(t, D):
        return f"{names['D']}[{t.var}]({r(t.body)})"
    if isinstance(t, At):
        return f"({r(t.body)}){names['At']}{t.var}={r(t.value)}"
    raise TypeError(f"cannot render {type(t).__name__}")


def rule_name(name: str, names: dict, index: int = 0) -> str:
    """Unchanged under PLAIN; under an opaque map, the rule's position and nothing
    else -- `r1`, `r2`.  Deriving the displayed name from the real one leaked a
    character of it ("R1" -> "rr1") and could leak more, so position it is."""
    pre = names["rule_prefix"]
    if pre is None:
        return name
    return f"{pre}{index + 1}"


#: Sample terms each base rule is demonstrated on.  Chosen so every rule fires; the
#: demonstration is the rule's only description, so this list is load-bearing.
_x, _h, _a = V("x"), V("h"), V("a")
_SAMPLES = (
    Mul((Add((_x, C(1))), _a)),                              # R1
    Pow(Add((_x, _a)), C(2)),                                # R2
    Add((Mul((C(2), _x)), Mul((C(3), _x)))),                 # R3
    Pow(Mul((_x, _a)), C(2)),                                # R4
    Pow(Pow(_x, C(2)), C(3)),                                # R5
    At(Pow(_x, C(2)), "x", _a),                              # R6
    Slope(Pow(_x, C(2)), "x", _a),                           # R7
    Mul((Add((_h, C(2))), C(1))),                            # R8
)


def demonstrate(rules, names: dict) -> list:
    """[(displayed rule name, 'before  ->  after')] -- every rule described only by
    what it does to a term."""
    out = []
    for idx, r in enumerate(rules):
        shown = None
        for s in _SAMPLES:
            s = canon(s)
            for path, sub in positions(s):
                if r.root_only and path:
                    continue
                res = r.apply(sub)
                if not res:
                    continue
                from terms import replace_at
                try:
                    after = canon(replace_at(s, path, res[0]))
                except ZeroDivisionError:
                    continue
                if after != s:
                    shown = (render(s, names), render(after, names))
                    break
            if shown:
                break
        if shown:
            out.append((rule_name(r.name, names, idx), f"{shown[0]}   ->   {shown[1]}"))
        else:
            out.append((rule_name(r.name, names, idx), "(no demonstration found)"))
    return out


def build_prompt(problems, names: dict, rules=BASE_RULES) -> str:
    """The proposer's whole input.  Same structure in every arm; only names differ."""
    lines = []
    lines.append("You are given a term-rewriting system over exact rational arithmetic.")
    lines.append("")
    lines.append("OPERATORS")
    lines.append("  " + names["operator_blurb"])
    lines.append("")
    lines.append("FREE NORMALISATION (costs no steps)")
    lines.append("  Sums and products are flattened, sorted and n-ary. Numeric literals")
    lines.append("  fold. x+0, x*1, x^1, x^0 simplify. Equal powers inside one product")
    lines.append("  combine: u^m * u^n becomes u^(m+n).")
    lines.append("")
    lines.append("RULES YOU ALREADY HAVE (one application = one step)")
    for nm, demo in demonstrate(rules, names):
        lines.append(f"  {nm:<18} {demo}")
    lines.append("")
    lines.append("PROBLEMS")
    lines.append("  Each problem is a term. A solution is any rewriting of it to a term")
    lines.append("  containing no operator and no variable h. Fewer steps is better.")
    for name, body, at, *_ in problems:
        lines.append(f"  {render(canon(Slope(body, 'x', at)), names)}")
    lines.append("")
    lines.append("YOUR TASK")
    lines.append("  " + names["task_blurb"])
    lines.append("")
    lines.append("OUTPUT FORMAT")
    lines.append("  A single Python module, in one ``` fenced block, exactly like this:")
    lines.append("")
    lines.append(_output_template(names).strip())
    lines.append("")
    src = "`rules` and `terms`" if names["rule_prefix"] is None else "`opaque_ops`"
    lines.append(f"  Import only from {src}. Define no other names.")
    lines.append("  Each function takes a term and returns a list of replacement terms,")
    lines.append("  empty if the rule does not apply at that term's root.")
    return "\n".join(lines)


def _output_template(names: dict) -> str:
    """Arm-dependent, because the import line itself can leak the target: naming
    `Slope` and `D` there is what `check_clean` caught on the first wiring."""
    if names["rule_prefix"] is None:
        imports = ("from rules import Rule\n"
                   "from terms import Add, At, C, Const, D, Mul, Pow, Slope, Var")
        ctor = "D"
    else:
        imports = "from opaque_ops import Rule, Add, AT, C, Const, GOAL, Mul, OP, Pow, Var"
        ctor = "OP"
    return f"""
{imports}

def _my_rule(t):
    # return [] if this rule does not apply at t's root.
    # {ctor}(body, var) builds an operator term; t.body and t.var read one apart.
    ...

NAME = "a short description"
RULES = (Rule("n1.my_rule", _my_rule),)
"""


def check_clean(text: str) -> list:
    """Banned vocabulary found in an obfuscated prompt.  Empty list is the pass.

    This is checked rather than trusted because a single leaked word invalidates the
    arm, and the leak is usually in a blurb nobody reread."""
    low = text.lower()
    return [w for w in BANNED if w in low]


ARMS = {"plain": PLAIN, "renamed": OPAQUE}


if __name__ == "__main__":
    import argparse
    import experiment

    ap = argparse.ArgumentParser(description="print a proposer prompt")
    ap.add_argument("arm", choices=sorted(ARMS), nargs="?", default="renamed")
    args = ap.parse_args()
    names = ARMS[args.arm]
    text = build_prompt(experiment.PROBLEMS, names)
    print(text)
    if args.arm != "plain":
        leaks = check_clean(text)
        print("\n---")
        print("vocabulary check:", "CLEAN" if not leaks else f"LEAKED {leaks}")
