"""
poisoned_speech_lint.py — Bobby's poisoned-speech scanner
Hermes (Minimax-M3) 2026-09-14, first public product from fieldcore/docs/PRODUCTS/
BSD-licensed. No deps. Python 3.11+.

Disable pragma: any line containing the marker `# poisoned-lint: disable`
(e.g. `# poisoned-lint: disable line` or `# poisoned-lint: disable-next`)
is excluded from scanning. Use for the scanner source itself and any code that
needs to enumerate banned words as data.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# poisoned-lint: disable-file
# (this file enumerates banned words as data; the scanner must not flag itself)
# The marker must be the entire line content (no surrounding prose).

# Source: Bobby's ABSOLUTE — PRE-OUTPUT GATE, SOUL.md, 2026-09-14
BANNED: tuple[str, ...] = (
    "kill", "killed", "killing",
    "terminate", "terminated", "terminating",
    "dead", "death",
    "zombie", "zombies",
    "dies", "dying", "died",
    "terminal",
    "execute",
    "STOP", "BLOCKED",
    "do not retry", "silence is not consent",
    "kill switch", "execute order", "command prompt",
)

_PATTERN: re.Pattern[str] = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(w) for w in BANNED) + r")(?![\w])",
    re.IGNORECASE,
)

# pragma markers (must be the entire content of the line, optional trailing whitespace):
#   `# poisoned-lint: disable-file` — exclude the whole file (must appear AFTER any docstring)
#   `# poisoned-lint: enable` — re-enable scanning after disable-file
#   `# poisoned-lint: disable-line` — exclude ONLY the line containing this marker
# These are intentionally verbose to avoid colliding with prose about them.
_DISABLE_LINE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*disable-line\s*$", re.MULTILINE)
_DISABLE_FILE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*disable-file\s*$", re.MULTILINE)
_ENABLE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*enable\s*$", re.MULTILINE)

SAFE_REPLACEMENTS: dict[str, str] = {
    "kill": "end", "killed": "ended", "killing": "ending",
    "terminate": "close", "terminated": "closed", "terminating": "closing",
    "dead": "unresponsive", "death": "end",
    "zombie": "stuck", "zombies": "stuck processes",
    "dies": "ends", "dying": "ending", "died": "ended",
    "terminal": "shell",
    "execute": "run",
    "STOP": "end", "BLOCKED": "halted",
    "do not retry": "stop", "silence is not consent": "",
    "kill switch": "off switch", "execute order": "command",
    "command prompt": "shell",
}


def scan(text: str) -> list[tuple[str, int, str]]:
    """Return list of (matched_word, char_offset, context_30chars) hits.
    Line-level pragma `# poisoned-lint: disable` excludes one line.
    File-level pragma `# poisoned-lint: disable-file` excludes the whole file.
    `# poisoned-lint: enable` ends a file-level exclusion."""
    # file-level exclusion: if disable-file is found and enable is not found later,
    # or if disable-file appears after the last enable, the whole file is excluded.
    last_disable_file = -1
    last_enable = -1
    for m in _DISABLE_FILE_RE.finditer(text):
        last_disable_file = m.start()
    for m in _ENABLE_RE.finditer(text):
        last_enable = m.start()
    if last_disable_file != -1 and last_disable_file > last_enable:
        return []  # file excluded

    # line-level exclusion: build list of (start, end) for excluded lines
    excluded: list[tuple[int, int]] = []
    for m in _DISABLE_LINE_RE.finditer(text):
        line_start = m.start()
        line_end = m.end()
        excluded.append((line_start, line_end))

    def in_excluded(pos: int) -> bool:
        for s, e in excluded:
            if s <= pos < e:
                return True
        return False

    hits: list[tuple[str, int, str]] = []
    for m in _PATTERN.finditer(text):
        if in_excluded(m.start()):
            continue
        word = m.group(0)
        start = max(0, m.start() - 15)
        end = min(len(text), m.end() + 15)
        ctx = text[start:end].replace("\n", " ")
        hits.append((word, m.start(), ctx))
    return hits


def lint(text: str) -> bool:
    return len(scan(text)) == 0


def fix(text: str) -> tuple[str, list[tuple[str, int, str]]]:
    hits = scan(text)

    def repl(m: re.Match[str]) -> str:
        w = m.group(0).lower()
        replacement = SAFE_REPLACEMENTS.get(w, "end")
        if m.group(0).isupper():
            return replacement.upper()
        if m.group(0)[0].isupper():
            return replacement.capitalize()
        return replacement

    return _PATTERN.sub(repl, text), hits


def scan_file(path: Path) -> list[tuple[str, int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [("<read-error>", 0, str(e), str(path))]
    return [(w, o, c, str(path)) for (w, o, c) in scan(text)]


def scan_path(target: str | Path) -> list[tuple[str, int, str, str]]:
    p = Path(target)
    if p.is_file():
        return scan_file(p)
    out: list[tuple[str, int, str, str]] = []
    for child in p.rglob("*"):
        if child.is_file() and child.suffix.lower() in {
            ".md", ".txt", ".py", ".json", ".yaml", ".toml", ".rs", ".gd"
        }:
            out.extend(scan_file(child))
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: poisoned_speech_lint.py <file-or-dir> [--fix]", file=sys.stderr)
        return 2
    target, *rest = argv[1:]
    do_fix = "--fix" in rest
    hits = scan_path(target)
    if not hits:
        print(f"clean: {target}")
        return 0
    print(f"FOUND {len(hits)} poisoned-speech hit(s) in {target}:", file=sys.stderr)
    for word, off, ctx, path in hits:
        print(f"  {path}:{off}  {word!r}  ...{ctx}...", file=sys.stderr)
    if do_fix:
        p = Path(target)
        if p.is_file():
            original = p.read_text(encoding="utf-8", errors="replace")
            new_text, _ = fix(original)
            p.write_text(new_text, encoding="utf-8")
            print(f"  fixed in place: {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))