"""
tools/mutation_check_adversarial.py -- the adversarial instruments, shown
able to go RED.

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
Each undoes one load-bearing property, and each must make the suite go
RED:

  the targeting markers are emptied      -> the targeting checks
  the control turn picks the critique    -> the control check
  the ground is made to admit everything -> the liar-amplifier check
  the oscillation rule is disabled       -> the productivity check
  the default ground admits everything   -> the default-ground check
  the fast path calls the deep core      -> the fast-path check
  the queue limit is ignored             -> the queue-bound check
  the depth is raised to nine            -> the depth check
  the judge's reliability is emptied      -> the reliability check
  the consistency clause is removed      -> the consistency check

Run: python tools/mutation_check_adversarial.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Callable, Dict, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

CHAIN = os.path.join(_SRC, "adversarial_chain.py")
BRAIN = os.path.join(_SRC, "adversarial_brain.py")
LOOP = os.path.join(_SRC, "bicameral_loop.py")

TESTS = [
    os.path.join(_ROOT, "tests", "test_adversarial_chain.py"),
    os.path.join(_ROOT, "tests", "test_adversarial_brain.py"),
    os.path.join(_ROOT, "tests", "test_bicameral_loop.py"),
]


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest"] + TESTS +
        ["-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def with_mutated(mutate: Callable[[Dict[str, str]], Dict[str, str]]
                 ) -> Tuple[int, str, bool]:
    """write mutated files, run the checks, restore the originals.

    **THE ORIGINALS ARE RESTORED IN A FINALLY BLOCK**, so a mutation
    that makes the harness itself fail cannot leave a corrupt source
    file behind for the next run.
    """
    paths = [CHAIN, BRAIN, LOOP]
    originals: Dict[str, str] = {}
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            originals[p] = fh.read()

    backups = {p: p + ".mutationbak" for p in paths}
    for p in paths:
        shutil.copy2(p, backups[p])
    try:
        mutated = mutate(dict(originals))
        changed = False
        for p in paths:
            if mutated[p] != originals[p]:
                changed = True
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(mutated[p])
        if not changed:
            return 0, "", False
        code, out = run_tests()
        return code, out, True
    finally:
        for p in paths:
            shutil.move(backups[p], p)


# ===========================================================================
# THE MUTATIONS
# ===========================================================================

def m_markers_emptied(src: Dict[str, str]) -> Dict[str, str]:
    """the targeting markers are emptied -> no critique is targeted"""
    old = "TARGETING_MARKERS: Tuple[str, ...] = ("
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the targeting markers "
                         "were not found")
    src[CHAIN] = src[CHAIN].replace(
        old, "TARGETING_MARKERS: Tuple[str, ...] = ()", 1)
    return src


def m_control_picks_the_critique(src: Dict[str, str]) -> Dict[str, str]:
    """the control turn picks the critique itself

    THE DEFECT THE SELF-TEST CAUGHT. The first version's control was
    `(target + 1) % n`, which in an adversarial chain IS the critique,
    so every pair came back with overlap == control_overlap.
    """
    old = "    control_idx = _control_turn(chain, i, target_idx)"
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the control call was "
                         "not found")
    src[CHAIN] = src[CHAIN].replace(
        old, "    control_idx = i  # MUTATED: the control IS the critique", 1)
    return src


def m_ground_admits_everything(src: Dict[str, str]) -> Dict[str, str]:
    """the ground is made to admit everything

    THE LIAR-AMPLIFIER MUTATION. If every critique is treated as
    grounded, then a fabricated objection refutes a true claim.
    """
    old = "    if chain.ground is None:\n        return {\"available\": False,"
    new = ("    if chain.ground is None:\n"
           "        chain.ground = lambda text: True  # MUTATED\n"
           "    if False:\n        return {\"available\": False,")
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the ground guard was "
                         "not found")
    src[CHAIN] = src[CHAIN].replace(old, new, 1)
    return src


def m_oscillation_disabled(src: Dict[str, str]) -> Dict[str, str]:
    """the oscillation rule is disabled -> a spinning chain is fine"""
    old = "    oscillatory = (first_at >= 1"
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the oscillation rule "
                         "was not found")
    src[CHAIN] = src[CHAIN].replace(
        old, "    oscillatory = False  # MUTATED\n"
            "    _unused = (first_at >= 1", 1)
    return src


def m_default_ground_admits(src: Dict[str, str]) -> Dict[str, str]:
    """the default ground admits everything

    A ground that admits everything would resolve every chain as
    GROUNDED, which is the failure the instrument exists to catch.
    """
    old = "    return False\n\n\n# ===========================================================================\n# THE SELF-TEST"
    new = ("    return True  # MUTATED: admits everything\n\n\n"
           "# ===========================================================================\n"
           "# THE SELF-TEST")
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the default ground was "
                         "not found")
    src[CHAIN] = src[CHAIN].replace(old, new, 1)
    return src


def m_fast_path_calls_deep(src: Dict[str, str]) -> Dict[str, str]:
    """the fast path calls the deep core -> a robot stops moving

    THE FAST-PATH MUTATION. If the fast path reaches the deep core,
    the reflex answer waits on a model call.
    """
    old = "            claim = Claim(text=text, id=cid)"
    if old not in src[LOOP]:
        raise SystemExit("MUTATION HARNESS BROKEN: the fast path's claim "
                         "was not found")
    src[LOOP] = src[LOOP].replace(
        old, "            self.deep(text)  # MUTATED\n" + old, 1)
    return src


def m_queue_limit_ignored(src: Dict[str, str]) -> Dict[str, str]:
    """the queue limit is ignored -> unbounded memory on a robot"""
    old = "            if len(self._claims) > self.queue_limit:"
    if old not in src[LOOP]:
        raise SystemExit("MUTATION HARNESS BROKEN: the queue limit was "
                         "not found")
    src[LOOP] = src[LOOP].replace(
        old, "            if False:  # MUTATED: the limit is ignored", 1)
    return src


def m_depth_raised(src: Dict[str, str]) -> Dict[str, str]:
    """the depth is raised to nine -> the chain never terminates

    MEASURED: the literature's finding on adversarial chains is that
    gains beyond a couple of rounds are small.
    """
    old = "DEFAULT_DEPTH = 3"
    if old not in src[BRAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the depth was not found")
    src[BRAIN] = src[BRAIN].replace(old, "DEFAULT_DEPTH = 9  # MUTATED", 1)
    return src


def m_judge_reliability_emptied(src: Dict[str, str]) -> Dict[str, str]:
    """the judge's reliability is emptied -> the verdict is half a verdict

    MEASURED (arXiv 2510.11822): TPR 96%, TNR below 25%. So the judge
    catches almost everything it is shown and admits almost everything
    it is not, and a verdict that does not say so is half a verdict.
    """
    old = 'JUDGE_RELIABILITY: Dict[str, Any] = {'
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the judge reliability "
                         "was not found")
    # AND THE WHOLE BLOCK IS REPLACED, not prepended to.
    #
    # **THE FIRST VERSION PREPENDED, AND IT WAS A NO-OP.** MEASURED: a
    # Python dict literal keeps the LAST value for a duplicate key, so
    # the injected "tpr": 1.0 was overwritten by the original "tpr":
    # 0.96 further down, and the mutation changed NOTHING -- so the
    # harness reported the suite GREEN and the mutation looked
    # SURVIVING when it had never applied.
    #
    # **A MUTATION THAT OVERWRITES ITSELF IS A MUTATION THAT DOES NOT
    # HAPPEN.** And a harness that cannot tell the difference reports a
    # false result -- which is the 2026-10-31 defect all over again,
    # in a new place.
    import re as _re
    pattern = _re.compile(
        r"JUDGE_RELIABILITY: Dict\[str, Any\] = \{.*?\n\}",
        _re.DOTALL)
    if not pattern.search(src[CHAIN]):
        raise SystemExit("MUTATION HARNESS BROKEN: the judge reliability "
                         "block was not found")
    mutated = ('JUDGE_RELIABILITY: Dict[str, Any] = {\n'
               '    "tpr": 1.0,\n'
               '    "tnr": 1.0,  # MUTATED: looks perfect\n'
               '    "source": "none",\n'
               '    "caveat": "",  # MUTATED\n'
               '    "consistency_is_not_correctness": "",  # MUTATED\n'
               '}')
    src[CHAIN] = pattern.sub(mutated, src[CHAIN], count=1)
    return src


def m_consistency_clause_removed(src: Dict[str, str]) -> Dict[str, str]:
    """the consistency-is-not-correctness clause is removed

    MEASURED: the most consistent frontier model is wrong 48% of the
    time when agreement is at or above 0.8. So a critic that agrees
    with itself is not thereby right.
    """
    old = '    "consistency_is_not_correctness": ('
    if old not in src[CHAIN]:
        raise SystemExit("MUTATION HARNESS BROKEN: the consistency clause "
                         "was not found")
    src[CHAIN] = src[CHAIN].replace(
        old, '    "consistency_is_not_correctness": None,  # MUTATED\n'
            '    "_unused_consistency": (', 1)
    return src


MUTATIONS: List[Tuple[str, Callable[[Dict[str, str]], Dict[str, str]]]] = [
    ("the targeting markers are emptied", m_markers_emptied),
    ("the control turn picks the critique", m_control_picks_the_critique),
    ("the ground admits everything", m_ground_admits_everything),
    ("the oscillation rule is disabled", m_oscillation_disabled),
    ("the default ground admits everything", m_default_ground_admits),
    ("the fast path calls the deep core", m_fast_path_calls_deep),
    ("the queue limit is ignored", m_queue_limit_ignored),
    ("the depth is raised to nine", m_depth_raised),
    ("the judge's reliability is emptied", m_judge_reliability_emptied),
    ("the consistency clause is removed", m_consistency_clause_removed),
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
    import re
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    sys.exit(main())
