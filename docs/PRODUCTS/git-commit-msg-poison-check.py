#!/usr/bin/env python
"""commit-msg hook: scans the commit message file. git passes the path as arg 1.
poisoned-lint: disable-file"""
import re, sys

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

if len(sys.argv) < 2:
    sys.exit(0)  # no message file, allow

msg_file = sys.argv[1]
with open(msg_file, encoding="utf-8", errors="replace") as f:
    msg = f.read()

hits = list(set(m.group(0) for m in _PATTERN.finditer(msg)))
if hits:
    print("POISONED SPEECH IN COMMIT MESSAGE -- commit blocked.", file=sys.stderr)
    for h in hits:
        print(f"  banned: {h!r}", file=sys.stderr)
    print("Safe replacements: end, close, stop, halt, shut down.", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
