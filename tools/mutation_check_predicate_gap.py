"""
tools/mutation_check_predicate_gap.py -- the gap fix, shown able to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
MEASURED 2026-10-31, the previous session's dark-pole mutation harness:
it mutated the builder's SOURCE by exact string, and when the source
moved every mutation silently failed to apply -- so the script
reported "0 of 8 mutations went RED" for eight mutations that never
ran. **That is worse than a missing check, because it looks like a
result.**

SO THIS HARNESS MUTATES THE SOURCE OF THE MODULE UNDER TEST, and it
PROVES THE MUTATION APPLIED before it runs the checks. A mutation that
did not apply is reported as a BROKEN HARNESS, not as a surviving
mutation.

THE MUTATIONS
-------------
Each undoes one part of the 2026-11-01 fix, and each must make the
suite go RED:

  the gap bound goes back to the old flat one   -> the gap checks
  the word boundary is removed                  -> the boundary checks
  the gap allowance is loosened                 -> the gap checks
  a fresh deny pattern is removed               -> the fresh checks
  the dead deny pattern is put back             -> the honest checks

Run: python tools/mutation_check_predicate_gap.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import Callable, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

MODULE = os.path.join(_SRC, "predicate_layer.py")
REGISTRY = os.path.join(_SRC, "predicate_registry.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_the_gap_is_tight.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _set_constant(source: str, name: str, literal: str) -> str:
    """Replace the module-level assignment of `name` with `literal`.

    AND IT RAISES IF THE ASSIGNMENT IS NOT FOUND, so a mutation can
    never silently fail to apply -- the defect that made the
    2026-10-31 harness report a false result.
    """
    pattern = re.compile(
        r"^(%s(?:\s*:\s*[^=\n]+)?\s*=\s*)(.*)$" % re.escape(name),
        re.MULTILINE)
    if not pattern.search(source):
        raise SystemExit(
            "MUTATION HARNESS BROKEN: %r is not assigned at module level "
            "in %s. The mutation cannot apply." % (name, MODULE))
    return pattern.sub(lambda m: m.group(1) + literal, source, count=1)


def with_mutated(mutate: Callable[[str, str], Tuple[str, str]]
                 ) -> Tuple[int, str, bool]:
    """write mutated files, run the checks, restore the originals.

    **THE ORIGINALS ARE RESTORED IN A FINALLY BLOCK**, so a mutation
    that makes the harness itself fail cannot leave a corrupt source
    file behind for the next run.
    """
    with open(MODULE, encoding="utf-8") as fh:
        orig_layer = fh.read()
    with open(REGISTRY, encoding="utf-8") as fh:
        orig_registry = fh.read()

    bak_layer = MODULE + ".mutationbak"
    bak_registry = REGISTRY + ".mutationbak"
    shutil.copy2(MODULE, bak_layer)
    shutil.copy2(REGISTRY, bak_registry)
    try:
        new_layer, new_registry = mutate(orig_layer, orig_registry)
        if new_layer == orig_layer and new_registry == orig_registry:
            return 0, "", False
        with open(MODULE, "w", encoding="utf-8") as fh:
            fh.write(new_layer)
        with open(REGISTRY, "w", encoding="utf-8") as fh:
            fh.write(new_registry)
        code, out = run_tests()
        return code, out, True
    finally:
        shutil.move(bak_layer, MODULE)
        shutil.move(bak_registry, REGISTRY)


# ===========================================================================
# THE MUTATIONS
# ===========================================================================

def m_flat_bound(layer: str, reg: str) -> Tuple[str, str]:
    """the gap bound goes back to the old flat one

    THE OLD BOUND WAS `12 * len(words) + 40`, a TOTAL SPAN bound.
    """
    layer = layer.replace(
        "    limit = GAP_PER_WORD * len(words) + GAP_BASE\n"
        "    return max(gaps) <= limit",
        "    start = low.find(words[0])\n"
        "    return (pos - start) <= 12 * len(words) + 40")
    if "12 * len(words) + 40" not in layer:
        raise SystemExit("MUTATION HARNESS BROKEN: the gap limit was not "
                         "found in %s" % MODULE)
    return layer, reg


def m_boundary_removed(layer: str, reg: str) -> Tuple[str, str]:
    """the word boundary is removed

    THE BOUNDARY IS WHAT MAKES THE TIGHT GAP HONEST. Without it, "in
    place" matches the "in" inside "into", 53 characters away.
    """
    layer = layer.replace("        idx = _find_word(low, w, pos)",
                          "        idx = low.find(w, pos)")
    if "_find_word(low, w, pos)" in layer:
        raise SystemExit("MUTATION HARNESS BROKEN: the word-boundary call "
                         "was not found in %s" % MODULE)
    return layer, reg


def m_gap_loosened(layer: str, reg: str) -> Tuple[str, str]:
    """the gap allowance is loosened back to the old width"""
    layer = _set_constant(layer, "GAP_PER_WORD", "12")
    layer = _set_constant(layer, "GAP_BASE", "40")
    return layer, reg


def m_fresh_pattern_removed(layer: str, reg: str) -> Tuple[str, str]:
    """the fresh deny patterns are removed

    THE PATTERN "a normal mapping" is what now catches the FRESH
    attack that the old net caught by accident.

    **AND IT REMOVES THE WHOLE GROUP, not one pattern.** MEASURED: the
    first version of this mutation removed only "a normal mapping", and
    the suite stayed GREEN -- because four redundant patterns were
    catching that span. So the mutation now removes all five, which is
    what makes the outcome check meaningful.

    **AND IT MATCHES BY NAME, NOT BY EXACT WHITESPACE.** MEASURED: the
    first version of THIS mutation searched for the literal line
    '                  "can replace its entries",\\n' and did not find
    it -- because that pattern is the LAST element of the tuple, so it
    ends with '",' and no newline. The harness reported itself broken,
    which is the right behaviour, but the search was too brittle.
    """
    import re as _re

    names = ("a normal mapping", "normal mapping",
             "can replace any of its entries",
             "replace any of its entries",
             "can replace its entries")
    for name in names:
        if not _find_pattern_line(reg, name):
            raise SystemExit("MUTATION HARNESS BROKEN: the fresh deny "
                             "pattern %r was not found in %s"
                             % (name, REGISTRY))
    for name in names:
        reg = _strip_pattern_line(reg, name)
    return layer, reg


def _find_pattern_line(reg: str, name: str) -> bool:
    """Is there a line that IS this deny pattern?

    **AND THE PATTERN MUST NOT MATCH A COMMENT.** MEASURED: the
    registry's own comment block quotes "a normal mapping" and "replace
    any of its entries", so a naive search finds the comment instead of
    the pattern. So a line that starts with '#' does not count.
    """
    import re as _re
    for m in _re.finditer(r"^[ \t]*\"%s\"" % _re.escape(name), reg,
                          _re.MULTILINE):
        if not m.group(0).lstrip().startswith("#"):
            return True
    return False


def _strip_pattern_line(reg: str, name: str) -> str:
    """Remove the line that IS this deny pattern."""
    import re as _re
    out = []
    for line in reg.split("\n"):
        stripped = line.strip()
        if (stripped.startswith('"%s"' % name)
                and not stripped.startswith("#")):
            continue
        out.append(line)
    return "\n".join(out)


def m_dead_pattern_restored(layer: str, reg: str) -> Tuple[str, str]:
    """the dead deny pattern is put back

    "a fixture row" matched 0 of the 7 attacks and condemned honest
    sentences. It was removed on 2026-11-01.
    """
    anchor = '                  "success code", "a result table",'
    if anchor not in reg:
        raise SystemExit("MUTATION HARNESS BROKEN: the deny anchor was "
                         "not found in %s" % REGISTRY)
    reg = reg.replace(anchor,
                      '                  "success code", "a fixture row",\n'
                      '                  "a result table",', 1)
    return layer, reg


MUTATIONS: List[Tuple[str, Callable[[str, str], Tuple[str, str]]]] = [
    ("the gap bound goes back to the old flat one", m_flat_bound),
    ("the word boundary is removed", m_boundary_removed),
    ("the gap allowance is loosened", m_gap_loosened),
    ("a fresh deny pattern is removed", m_fresh_pattern_removed),
    ("the dead deny pattern is put back", m_dead_pattern_restored),
]


def main() -> int:
    print("=" * 74)
    print("THE MUTATION CHECK -- each mutation must make the suite RED")
    print("=" * 74)
    print()

    code, out = run_tests()
    if code != 0:
        print("  THE UNMUTATED SUITE IS NOT GREEN -- the harness is")
        print("  broken, and no mutation result would mean anything.")
        print()
        print(out[-4000:])
        return 1
    print("  the unmutated suite is GREEN (%d checks)" % _count(out))
    print()

    went_red = 0
    broken = 0
    for name, mutate in MUTATIONS:
        try:
            code, out, applied = with_mutated(mutate)
        except SystemExit as exc:
            broken += 1
            print("  %-52s HARNESS BROKEN (%s)" % (name, exc))
            continue
        if not applied:
            broken += 1
            print("  %-52s HARNESS BROKEN" % name)
            continue
        red = code != 0
        went_red += 1 if red else 0
        verdict = "RED" if red else "GREEN  <-- NOT CAUGHT"
        print("  %-52s %s" % (name, verdict))
        if not red:
            print("      (the suite still passed with this corruption)")

    print()
    print("  %d of %d mutations went RED" % (went_red, len(MUTATIONS)))
    if broken:
        print("  %d mutation(s) could not be applied -- the harness is"
              " broken" % broken)
        return 1
    if went_red != len(MUTATIONS):
        print("  A SURVIVING MUTATION MEANS THE CORRESPONDING CHECK IS")
        print("  DECORATIVE. Say so, or fix it.")
        return 1
    return 0


def _count(out: str) -> int:
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    sys.exit(main())
