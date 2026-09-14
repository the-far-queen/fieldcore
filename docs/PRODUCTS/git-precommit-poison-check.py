#!/usr/bin/env python
"""pre-commit hook: scans staged diff for poison vocab. Blocks if found.
poisoned-lint: disable-file"""
import re, subprocess, sys

BANNED = (
    "kill", "killed", "killing",
    "terminate", "terminated", "terminating",
    "dead", "death",
    "zombie", "zombies",
    "dies", "dying", "died",
    "terminal", "execute",
    "STOP", "BLOCKED",
    "do not retry", "silence is not consent",
    "kill switch", "execute order", "command prompt",
)
_PATTERN = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(w) for w in BANNED) + r")(?![\w])",
    re.IGNORECASE,
)

diff = subprocess.run(
    ["git", "diff", "--cached", "--diff-filter=ACMR"],
    capture_output=True, text=True
).stdout
hits = list(set(m.group(0) for m in _PATTERN.finditer(diff)))
if hits:
    print("POISONED SPEECH IN STAGED DIFF -- commit blocked.", file=sys.stderr)
    for h in hits:
        print(f"  banned: {h!r}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
