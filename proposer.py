"""The proposer adapter: model -> candidate module on disk.

This is the last piece between "we have an API key" and "we have results". It does
three things and deliberately nothing else:

  1. builds the prompt for one arm            (obfuscate.py)
  2. calls an OpenAI-shaped chat endpoint     (stdlib urllib -- NO new dependency)
  3. writes the reply out as a candidate module in candidates/, unreviewed

It does NOT score anything. `propose.py` does that, and keeping them apart is the same
separation the design notes insisted on: a generation that both invents a rule and
judges it is how you get a system that quietly assumes what it is proving.

    export LEIBNIZ_API_KEY=sk-...
    python proposer.py --arm renamed --model deepseek-chat
    # read candidates/m001_renamed_deepseek-chat.py, then flip REVIEWED = True
    python propose.py m001_renamed_deepseek-chat

Works against DeepSeek, or any endpoint speaking the same shape, via --base-url.
Defaults to DeepSeek because it is cheap enough to sample many proposals, which is what
a FunSearch-style loop actually wants -- capability is not the binding constraint here,
the controls are.

SAFETY. The model writes Python and `propose.py` imports it. That is the FunSearch
arrangement and it is fine for a local research repo -- but only because of the rule
below, which is enforced rather than suggested:

    A machine-written candidate carries REVIEWED = False and `propose.py` refuses to
    score it until a human reads it and flips the flag.

Never flip it without reading the file. Never point this at an endpoint you do not
control and then run the result unread.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date

import experiment
from obfuscate import ARMS, build_prompt, check_clean

DEFAULT_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
ENV_KEY = "LEIBNIZ_API_KEY"

CANDIDATE_DIR = "candidates"


class ProposerError(Exception):
    pass


# --------------------------------------------------------------------- the call

def call_model(prompt: str, *, model: str, base_url: str, api_key: str,
               temperature: float = 1.0, timeout: int = 180) -> str:
    """One chat completion. stdlib only, so the repo stays dependency-free."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        base_url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise ProposerError(f"HTTP {exc.code}: {exc.read()[:400].decode(errors='replace')}")
    except urllib.error.URLError as exc:
        raise ProposerError(f"could not reach {base_url}: {exc.reason}")
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ProposerError(f"unexpected response shape: {json.dumps(payload)[:400]}")


# ------------------------------------------------------------------- extraction

_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.S)

#: A machine-written candidate may import from exactly these.  Anything else is a
#: refusal rather than a warning: an import we did not expect is the one line nobody
#: rereads before flipping REVIEWED.
ALLOWED_IMPORTS = {"rules", "terms", "opaque_ops", "fractions"}

_BANNED_CALLS = ("open(", "exec(", "eval(", "__import__", "subprocess", "socket",
                 "urllib", "shutil", "os.", "sys.", "compile(", "globals(", "locals(")


def extract_module(reply: str) -> str:
    """Pull the fenced Python block out of a reply, or raise."""
    blocks = _FENCE.findall(reply)
    if not blocks:
        raise ProposerError("no fenced code block in the reply")
    return max(blocks, key=len).strip()


def audit(src: str) -> list:
    """Static objections to machine-written source. Empty list means "worth a human
    reading it", NOT "safe to run" -- only a human flipping REVIEWED means that."""
    problems = []
    for m in re.finditer(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", src, re.M):
        mod = (m.group(1) or m.group(2)).split(".")[0]
        if mod not in ALLOWED_IMPORTS:
            problems.append(f"imports {mod!r}, which is not in {sorted(ALLOWED_IMPORTS)}")
    for bad in _BANNED_CALLS:
        if bad in src:
            problems.append(f"contains {bad!r}")
    if "RULES" not in src:
        problems.append("defines no RULES")
    if "NAME" not in src:
        problems.append("defines no NAME")
    return problems


_HEADER = '''"""{name}

MACHINE-WRITTEN. Arm: {arm}. Model: {model}. Generated {day}.

Unreviewed. `propose.py` will refuse to score this until a human reads the whole file
and changes REVIEWED to True. Do not flip it without reading -- the module is imported
and executed when scored.

Static audit at generation time: {audit}

The prompt this came from is saved beside it as {promptfile}.
"""

REVIEWED = False

PROVENANCE = {{
    "proposer": "{model} via proposer.py, arm={arm}",
    "kind": "machine",
    "saw_heldout": False,
    "saw_boundary": False,
    "calculus_words": {calc_words},
    "date": "{day}",
}}

# ---------------------------------------------------------------- model output below

'''


def write_candidate(src: str, *, arm: str, model: str, slug: str,
                    prompt: str, objections: list) -> tuple:
    os.makedirs(CANDIDATE_DIR, exist_ok=True)
    stem = f"{slug}_{arm}_{model}".replace("-", "_").replace(".", "_")
    path = os.path.join(CANDIDATE_DIR, f"{stem}.py")
    promptfile = os.path.join(CANDIDATE_DIR, f"{stem}.prompt.txt")
    header = _HEADER.format(
        name=f"{slug} -- machine-written candidate",
        arm=arm, model=model, day=date.today().isoformat(),
        audit=("clean" if not objections else "; ".join(objections)),
        promptfile=os.path.basename(promptfile),
        calc_words=(arm == "plain"),
    )
    # the model's own NAME/PROVENANCE, if it wrote any, must not shadow ours
    src = re.sub(r"^\s*(NAME|PROVENANCE|REVIEWED)\s*=.*$", "", src, flags=re.M)
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + src.strip() + "\n\nNAME = " + repr(f"{slug} ({arm}, {model})") + "\n")
    with open(promptfile, "w", encoding="utf-8") as f:
        f.write(prompt)
    return path, promptfile


def next_slug() -> str:
    used = [f for f in os.listdir(CANDIDATE_DIR) if f.startswith("m")] \
        if os.path.isdir(CANDIDATE_DIR) else []
    return f"m{len(used) + 1:03d}"


# ----------------------------------------------------------------------- driver

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", choices=sorted(ARMS), default="renamed")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the prompt and exit; makes no call and needs no key")
    ap.add_argument("--from-file", default=None,
                    help="read the reply from a file instead of calling; for testing")
    args = ap.parse_args()

    names = ARMS[args.arm]
    prompt = build_prompt(experiment.PROBLEMS, names)

    if args.arm != "plain":
        leaks = check_clean(prompt)
        if leaks:
            raise SystemExit(f"REFUSING: arm {args.arm!r} prompt leaks {leaks}. "
                             "A single leaked word invalidates the arm.")
        print(f"vocabulary check: clean ({args.arm})", file=sys.stderr)

    if args.dry_run:
        print(prompt)
        return

    if args.from_file:
        reply = open(args.from_file, encoding="utf-8").read()
    else:
        key = os.environ.get(ENV_KEY)
        if not key:
            raise SystemExit(f"set {ENV_KEY} (or use --dry-run / --from-file)")
        print(f"calling {args.model} at {args.base_url}", file=sys.stderr)
        reply = call_model(prompt, model=args.model, base_url=args.base_url,
                           api_key=key, temperature=args.temperature)

    src = extract_module(reply)
    objections = audit(src)
    path, promptfile = write_candidate(
        src, arm=args.arm, model=args.model, slug=next_slug(),
        prompt=prompt, objections=objections,
    )

    print(f"\nwrote {path}")
    print(f"      {promptfile}")
    if objections:
        print("\nstatic audit objections:")
        for o in objections:
            print(f"  - {o}")
    print(f"\nNEXT: read {path} in full, then set REVIEWED = True, then")
    print(f"      python propose.py {os.path.basename(path)[:-3]}")


if __name__ == "__main__":
    main()
