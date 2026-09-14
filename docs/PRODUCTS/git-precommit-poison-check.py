#!/usr/bin/env python
"""pre-commit hook: scans staged diff for bad vocab. Blocks if found.
poisoned-lint: disable-file"""
import re, subprocess, sys
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

diff = subprocess.run(
    ["git", "diff", "--cached", "--diff-filter=ACMR"],
    capture_output=True, text=True
).stdout
diff = "\n".join(line for line in diff.split("\n") if "banned_words" not in line)

hits = list(set(m.group(0) for m in _PATTERN.finditer(diff)))
if hits:
    print("BAD WORDS IN STAGED DIFF -- commit halted.", file=sys.stderr)
    for h in hits:
        print(f"  bad: {h!r}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
