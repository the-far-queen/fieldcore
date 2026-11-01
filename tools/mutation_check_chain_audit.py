"""
tools/mutation_check_chain_audit.py -- the checks, shown able to go RED.

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
PROVES THE MUTATION APPLIED before it runs the checks. That proof is
the part the old harness lacked: a mutation that did not apply would
be reported as GREEN, and it would look like a surviving mutation
rather than a broken harness.

THE MUTATIONS
-------------
Each corrupts the chain-audit behaviour in a way that should break a
specific check:

  the reach threshold is raised to 0.99       -> the prediction lead
  the announce frames are emptied             -> the prediction lead
  the function-word list is emptied           -> the content-word measure
  the two-signal rule is raised to three      -> the agreement rule
  the signal-direction map is emptied         -> the decision rule
  the candidate markers are emptied           -> the candidate count
  the control is rigged to the observed       -> the inheritance lift

Run: python tools/mutation_check_chain_audit.py
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

MODULE = os.path.join(_SRC, "chain_audit.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_chain_audit.py")


def run_tests() -> Tuple[int, str]:
    """run the check file, and return the exit code and the output."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ===========================================================================
# THE MUTATION, as a source rewrite
# ===========================================================================

def _set_constant(source: str, name: str, literal: str) -> str:
    """Replace the module-level assignment of `name` with `literal`.

    **AND THE PATTERN MUST ALLOW A TYPE ANNOTATION.** The first
    pattern was `^(NAME\\s*=\\s*)`, which does not match
    `ANNOUNCE_FRAMES: Tuple[str, ...] = (...)`. So the harness raised
    on the second mutation and stopped -- which is the RIGHT behaviour
    (a mutation that cannot apply must not be reported as a result),
    but it meant the harness could only ever test the first mutation.

    So the pattern now allows an optional `: annotation` between the
    name and the `=`, and the annotation is PRESERVED.

    AND THE REPLACEMENT MUST BE VERIFIABLE, which is the point. If the
    assignment is not found the harness RAISES, so a mutation can never
    silently fail to apply -- which is the defect that made the
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


def with_mutated_source(mutate: Callable[[str], str]) -> Tuple[int, str, bool]:
    """write a mutated module, run the checks, restore the original.

    **THE ORIGINAL IS RESTORED IN A FINALLY BLOCK**, so a mutation
    that makes the harness itself fail cannot leave a corrupt source
    file behind for the next run.

    AND THE MUTATION IS VERIFIED BEFORE THE CHECKS RUN: the harness
    asserts that the mutated source actually differs from the original.
    A mutation that did not apply is a BROKEN HARNESS, and it is
    reported as such -- not as a surviving mutation, and not as a
    green suite.
    """
    with open(MODULE, encoding="utf-8") as fh:
        original = fh.read()

    backup = MODULE + ".mutationbak"
    shutil.copy2(MODULE, backup)
    try:
        mutated = mutate(original)
        if mutated == original:
            return 0, "", False
        with open(MODULE, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        code, out = run_tests()
        return code, out, True
    finally:
        shutil.move(backup, MODULE)


# ===========================================================================
# THE MUTATIONS
# ===========================================================================

def m_reach_threshold_high(src: str) -> str:
    """the reach threshold raised to 0.99 -> the reach never fires"""
    return _set_constant(src, "REACH_THRESHOLD", "0.99")


def m_announce_frames_emptied(src: str) -> str:
    """the announce frames emptied -> no announcement is ever found"""
    return _set_constant(src, "ANNOUNCE_FRAMES", "()")


def m_function_words_emptied(src: str) -> str:
    """the function-word list is emptied -> the measure counts 'the'

    **AND THIS ONE NEEDS A BLOCK REPLACEMENT, because the constant
    spans eleven lines.** The single-line pattern would have replaced
    only its first line and left the rest of the set dangling, which
    is a syntax error rather than a mutation -- and a harness that
    corrupts the file instead of mutating it is not testing anything.
    So the whole assignment is replaced, from the name to the closing
    `.split())`.
    """
    pattern = re.compile(
        r"^FUNCTION_WORDS(?:\s*:\s*[^=\n]+)?\s*=\s*set\(\"\"\".*?\"\"\"\.split\(\)\)",
        re.MULTILINE | re.DOTALL)
    if not pattern.search(src):
        raise SystemExit("MUTATION HARNESS BROKEN: the FUNCTION_WORDS block "
                         "was not found in %s" % MODULE)
    return pattern.sub("FUNCTION_WORDS: Set[str] = frozenset()", src,
                       count=1)


def m_min_agreement_raised(src: str) -> str:
    """the two-signal rule raised to three -> nothing can ever decide"""
    return _set_constant(src, "MIN_AGREEMENT", "3")


def m_aligned_emptied(src: str) -> str:
    """the signal-direction map emptied -> no signal points anywhere"""
    return _set_constant(src, "_ALIGNED", "{}")


def m_candidate_markers_emptied(src: str) -> str:
    """the candidate markers emptied -> the candidate count collapses"""
    return _set_constant(src, "CANDIDATE_MARKERS", "()")


def m_control_rigged(src: str) -> str:
    """the control is rigged to EQUAL the observed value -> lift is 1.0

    THIS IS THE FITTED-RATE MUTATION, and it is the most important
    one in the list. If the control can be made to equal the observed
    value, every chain lifts by exactly 1.0 and the inheritance signal
    is dead while still reading as a working number.
    """
    target = "control = _shuffled_inheritance(chain.steps, seed=20261101)"
    if target not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the control assignment "
                         "was not found in %s" % MODULE)
    return src.replace(
        target,
        "control = observed  # MUTATED: the control is the observed value")


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the reach threshold is raised to 0.99", m_reach_threshold_high),
    ("the announce frames are emptied", m_announce_frames_emptied),
    ("the function-word list is emptied", m_function_words_emptied),
    ("the two-signal rule is raised to three", m_min_agreement_raised),
    ("the signal-direction map is emptied", m_aligned_emptied),
    ("the candidate markers are emptied", m_candidate_markers_emptied),
    ("the control is rigged to the observed value", m_control_rigged),
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
        code, out, applied = with_mutated_source(mutate)
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
