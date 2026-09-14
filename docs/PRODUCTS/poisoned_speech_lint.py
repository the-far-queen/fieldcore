
"""
poisoned_speech_lint.py -- Bobby's bad-words scanner (sanitized version)

Loads banned vocabulary from a separate file (banned_words.txt) so this
source file does not contain the literal banned words.

Hermes (Minimax-M3) 2026-09-14, first public product from fieldcore/docs/PRODUCTS/
BSD-licensed. No deps. Python 3.11+.

Disable pragmas (must be entire line content):
  # poisoned-lint: disable-file
  # poisoned-lint: enable
  # poisoned-lint: disable-line
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


_BANNED_PATH = Path(__file__).parent / "banned_words.txt"


def _load_banned():
    return tuple(w.strip() for w in _BANNED_PATH.read_text(encoding="utf-8").splitlines() if w.strip())


_DISABLE_LINE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*disable-line\s*$", re.MULTILINE)
_DISABLE_FILE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*disable-file\s*$", re.MULTILINE)
_ENABLE_RE = re.compile(r"^\s*#\s*poisoned-lint:\s*enable\s*$", re.MULTILINE)


# Safe replacements loaded from parallel config file (one mapping per line).
_SAFE_REPL_PATH = Path(__file__).parent / "banned_words_safe.txt"


def _load_safe_replacements():
    out = {}
    if _SAFE_REPL_PATH.exists():
        for line in _SAFE_REPL_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


_SAFE_REPL = _load_safe_replacements()


def _build_pattern():
    banned = _load_banned()
    return re.compile(
        r"(?<![\w])(" + "|".join(re.escape(w) for w in banned) + r")(?![\w])",
        re.IGNORECASE,
    )


_PATTERN = _build_pattern()


def scan(text):
    """Return list of (matched_word, char_offset, context_30chars) hits.
    File- and line-level pragmas honored."""
    last_disable_file = -1
    last_enable = -1
    for m in _DISABLE_FILE_RE.finditer(text):
        last_disable_file = m.start()
    for m in _ENABLE_RE.finditer(text):
        last_enable = m.start()
    if last_disable_file != -1 and last_disable_file > last_enable:
        return []

    excluded = []
    for m in _DISABLE_LINE_RE.finditer(text):
        excluded.append((m.start(), m.end()))

    def in_excluded(pos):
        for s, e in excluded:
            if s <= pos < e:
                return True
        return False

    hits = []
    for m in _PATTERN.finditer(text):
        if in_excluded(m.start()):
            continue
        word = m.group(0)
        start = max(0, m.start() - 15)
        end = min(len(text), m.end() + 15)
        ctx = text[start:end].replace("\n", " ")
        hits.append((word, m.start(), ctx))
    return hits


def lint(text):
    return len(scan(text)) == 0


def fix(text):
    hits = scan(text)

    def repl(m):
        w = m.group(0).lower()
        replacement = _SAFE_REPL.get(w, "end")
        if m.group(0).isupper():
            return replacement.upper()
        if m.group(0)[0].isupper():
            return replacement.capitalize()
        return replacement

    return _PATTERN.sub(repl, text), hits


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [("<read-error>", 0, str(e), str(path))]
    return [(w, o, c, str(path)) for (w, o, c) in scan(text)]


def scan_path(target):
    p = Path(target)
    if p.is_file():
        return scan_file(p)
    out = []
    for child in p.rglob("*"):
        if child.is_file() and child.suffix.lower() in {
            ".md", ".txt", ".py", ".json", ".yaml", ".toml", ".rs", ".gd"
        } and not child.name.startswith("banned_words"):
            out.extend(scan_file(child))
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: poisoned_speech_lint.py <file-or-dir> [--fix]", file=sys.stderr)
        return 2
    target, *rest = argv[1:]
    do_fix = "--fix" in rest
    hits = scan_path(target)
    if not hits:
        print(f"clean: {target}")
        return 0
    print(f"FOUND {len(hits)} bad-word hit(s) in {target}:", file=sys.stderr)
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
