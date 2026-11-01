"""
tools/mutation_check_interstalk_ladder.py -- the combination, shown able
to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
SO THIS HARNESS MUTATES THE SOURCE OF THE MODULE UNDER TEST, and it
PROVES THE MUTATION APPLIED before it runs the checks.

THE MUTATIONS
-------------
Each undoes one part of the combination:

  the axes stop alternating   -> it becomes width-first
  the population is not read  -> the population axis is a label
  the channel refusals stop
  escalating                   -> the ladder never climbs
  the cap is removed           -> the ladder spends on dead rungs
  the cost model is wrong      -> the trade is mismeasured

Run: python tools/mutation_check_interstalk_ladder.py
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

DUAL = os.path.join(_SRC, "dual_ladder.py")
LADDER = os.path.join(_SRC, "interstalk_ladder.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_interstalk_ladder.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def with_mutated(mutate: Callable[[str, str], Tuple[str, str]]
                 ) -> Tuple[int, str, bool]:
    with open(DUAL, encoding="utf-8") as fh:
        orig_dual = fh.read()
    with open(LADDER, encoding="utf-8") as fh:
        orig_ladder = fh.read()
    bak_dual = DUAL + ".mutationbak"
    bak_ladder = LADDER + ".mutationbak"
    shutil.copy2(DUAL, bak_dual)
    shutil.copy2(LADDER, bak_ladder)
    try:
        new_dual, new_ladder = mutate(orig_dual, orig_ladder)
        if new_dual == orig_dual and new_ladder == orig_ladder:
            return 0, "", False
        with open(DUAL, "w", encoding="utf-8") as fh:
            fh.write(new_dual)
        with open(LADDER, "w", encoding="utf-8") as fh:
            fh.write(new_ladder)
        code, out = run_tests()
        return code, out, True
    finally:
        shutil.move(bak_dual, DUAL)
        shutil.move(bak_ladder, LADDER)


# ===========================================================================
# THE MUTATIONS
# ===========================================================================

def m_axes_stop_alternating(dual: str, ladder: str) -> Tuple[str, str]:
    """the axes stop alternating -> it becomes width-first

    THE DESIGN. Finishing one axis first is always wrong: all width
    first serialises a wide read of a hyperlocal question, and all
    population first recruits the whole area before the local question
    is shown to be unanswerable locally.
    """
    # AND THE ASSIGNMENT IS A STATEMENT, not a keyword argument, so
    # the mutation targets `axis = "population"`.
    if 'axis = "population"' not in dual:
        raise SystemExit("MUTATION HARNESS BROKEN: the axis assignment was "
                         "not found")
    dual = dual.replace('axis = "population"', 'axis = "width"')
    return dual, ladder


def m_population_not_read(dual: str, ladder: str) -> Tuple[str, str]:
    """the population is NOT read -> the population axis is a label"""
    # AND THE MUTATION REPLACES THE SLICE, not prepends to it -- so
    # the population in view is FIXED at two whatever the rung asks
    # for, and the population axis stops being real.
    old = "        in_view = [s.id for s in self.pool[:wanted]"
    if old not in ladder:
        raise SystemExit("MUTATION HARNESS BROKEN: the in_view build was "
                         "not found")
    new = ("        in_view = [s.id for s in self.pool[:2]]  # MUTATED: "
           "the population is fixed")
    return dual, ladder.replace(old, new, 1)


def m_channel_refusals_stop(dual: str, ladder: str) -> Tuple[str, str]:
    """the channel's refusals stop escalating -> the ladder never climbs"""
    # AND THE REASON MUST COME FROM THE CHANNEL, so the mutation
    # replaces the reason -- not the allowed flag. The channel's own
    # refusals are the only ones the ladder escalates on.
    old = ("        return (bool(ex.allowed), str(ex.reason), "
           "float(ex.alignment))")
    if old not in ladder:
        raise SystemExit("MUTATION HARNESS BROKEN: the attempt return was "
                         "not found")
    new = ("        return (bool(ex.allowed), 'refuse_norm',  # MUTATED\n"
           "                float(ex.alignment))")
    return dual, ladder.replace(old, new, 1)


def m_cap_removed(dual: str, ladder: str) -> Tuple[str, str]:
    """the cap is removed -> the ladder spends on dead rungs"""
    old = "        ladder = DL.DualLadder(use_cap=self.use_cap)"
    if old not in ladder:
        raise SystemExit("MUTATION HARNESS BROKEN: the ladder build was "
                         "not found")
    new = ("        ladder = DL.DualLadder(use_cap=False)  # MUTATED: the "
           "measured cap is gone")
    return dual, ladder.replace(old, new, 1)


def m_cost_model_wrong(dual: str, ladder: str) -> Tuple[str, str]:
    """the cost model is wrong -> the trade is mismeasured

    WIDTH is serial and expensive in TIME; POPULATION is parallel and
    expensive in SPACE. The product is the cost.
    """
    old = "        return self.width * self.population"
    if old not in dual:
        raise SystemExit("MUTATION HARNESS BROKEN: the cost property was "
                         "not found")
    return dual.replace(old, "        return self.width  # MUTATED", 1), ladder


MUTATIONS: List[Tuple[str, Callable[[str, str], Tuple[str, str]]]] = [
    ("the axes stop alternating", m_axes_stop_alternating),
    ("the population is not read", m_population_not_read),
    ("the channel refusals stop escalating", m_channel_refusals_stop),
    ("the cap is removed", m_cap_removed),
    ("the cost model is wrong", m_cost_model_wrong),
]


def main() -> int:
    print("=" * 74)
    print("THE MUTATION CHECK -- each mutation must make the suite RED")
    print("=" * 74)
    print()

    code, out = run_tests()
    if code != 0:
        print("  THE UNMUTATED SUITE IS NOT GREEN -- the harness is broken.")
        print(out[-3000:])
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
            print("  %-48s HARNESS BROKEN (%s)" % (name, exc))
            continue
        if not applied:
            broken += 1
            print("  %-48s HARNESS BROKEN" % name)
            continue
        red = code != 0
        went_red += 1 if red else 0
        print("  %-48s %s" % (name, "RED" if red else "GREEN  <-- NOT CAUGHT"))

    print()
    print("  %d of %d mutations went RED" % (went_red, len(MUTATIONS)))
    if broken:
        print("  %d mutation(s) could not be applied" % broken)
        return 1
    if went_red != len(MUTATIONS):
        print("  A SURVIVING MUTATION MEANS THE CHECK IS DECORATIVE.")
        return 1
    return 0


def _count(out: str) -> int:
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    sys.exit(main())
