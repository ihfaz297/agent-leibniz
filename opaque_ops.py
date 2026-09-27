"""Neutral re-exports, so an obfuscated prompt can tell a proposer what to import
without naming the target.

`from terms import Slope, D` leaks the answer in the import line -- which is exactly
the leak `obfuscate.check_clean` caught the first time this was wired up.  Arm 2
candidates import from here instead.

Only the three semantic names are aliased.  Add, Mul, Pow, Const, Var and C carry no
information about the target and keep their names.
"""

from rules import Rule                       # noqa: F401
from terms import Add, C, Const, Mul, Pow, Var   # noqa: F401
from terms import At as AT                   # noqa: F401
from terms import D as OP                    # noqa: F401
from terms import Slope as GOAL              # noqa: F401
