#!/usr/bin/env python
"""commit-msg hook: scans commit message for bad vocab. Blocks if found.
poisoned-lint: disable-file"""
import re, sys
from pathlib import Path

_HOOK_DIR = Path(__file__).resolve().parent
_BANNED_FILE = (_HOOK_DIR / ".." / ".." / "docs" / "PRODUCTS" / "banned_words.list").resolve()


def _load_banned():
    if not _BANNED_FILE.exists():
        return []
    return tuple(w.strip() for w in _BANNED_FILE.read_text(encoding="utf-8").splitlines() if w.strip())


_BANNED = _load_banned()
if not _BANNED:
    sys.exit(0)

_PATTERN = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(w) for w in _BANNED) + r")(?![\w])",
    re.IGNORECASE,
)

if len(sys.argv) < 2:
    sys.exit(0)

msg_file = sys.argv[1]
with open(msg_file, encoding="utf-8", errors="replace") as f:
    msg = f.read()
# skip lines referencing banned_words
msg = "\n".join(line for line in msg.split("\n") if "banned_words" not in line)

hits = list(set(m.group(0) for m in _PATTERN.finditer(msg)))
if hits:
    print("BAD WORDS IN COMMIT MESSAGE -- commit halted.", file=sys.stderr)
    for h in hits:
        print(f"  bad: {h!r}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
