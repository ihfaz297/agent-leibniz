"""Catch CLAUDE.md promising capabilities the code does not have.

The library gap (2026-09-27) existed for a month because the governing document said a
Kept candidate "goes into the library so the next abstraction can build on it" and no
library was ever written.  Nothing in this repo would have caught that.  This does.

Each check is a claim CLAUDE.md makes, paired with a grep that must find evidence of it in
the code.  Add a check whenever CLAUDE.md starts claiming a new capability -- a document
that promises a mechanism nobody implemented is worse than one that says nothing, because
it is read as a description of what exists.

    python check_claims.py        # exits non-zero if a claim is unbacked
"""

from __future__ import annotations

import re
import sys

#: (name, regex that must appear somewhere in the listed files, files)
CHECKS = [
    ("exact rationals, never floats",
     r"Fraction", ["terms.py", "verify.py"]),
    ("candidate provenance is enforced, not documented",
     r"saw_heldout", ["propose.py"]),
    ("machine candidates need human review before scoring",
     r"REVIEWED", ["propose.py"]),
    ("two separate referees: soundness and usefulness",
     r"def soundness", ["propose.py"]),
    ("held-out scoring is separate from training",
     r"heldout", ["propose.py"]),
    ("the closure accounting exists and defaults to 1",
     r"closure: int = 1", ["search.py"]),
    ("obfuscation checks its own prompt for leaked vocabulary",
     r"def check_clean", ["obfuscate.py"]),
    ("malformed machine output is refused, not crashed on",
     r"def smoke_test", ["propose.py"]),
]

#: Claims CLAUDE.md is ALLOWED to make only as an explicit absence.  If the text appears
#: without the disclaimer nearby, the document is promising something that is not there.
MUST_DISCLAIM = [
    ("a library of kept abstractions", r"goes into the library", r"there is no library"),
]


def main() -> int:
    failures = []
    for name, pattern, files in CHECKS:
        found = False
        for f in files:
            try:
                if re.search(pattern, open(f, encoding="utf-8").read()):
                    found = True
                    break
            except FileNotFoundError:
                pass
        print(f"  {'ok  ' if found else 'FAIL'} {name}")
        if not found:
            failures.append(f"{name}: no {pattern!r} in {files}")

    claude = open("CLAUDE.md", encoding="utf-8").read()
    for name, claim, disclaimer in MUST_DISCLAIM:
        if re.search(claim, claude, re.I) and not re.search(disclaimer, claude, re.I):
            print(f"  FAIL {name}: CLAUDE.md claims it with no disclaimer")
            failures.append(f"{name}: claimed in CLAUDE.md, not implemented, not disclaimed")
        else:
            print(f"  ok   {name} (claimed only as an absence, or not claimed)")

    if failures:
        print("\nUNBACKED CLAIMS:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nevery claim checked is backed by code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
