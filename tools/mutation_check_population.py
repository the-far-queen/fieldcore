"""
tools/mutation_check_population.py -- the escalation policy, shown able
to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
SO THIS HARNESS MUTATES THE SOURCE OF THE MODULE UNDER TEST, and it
PROVES THE MUTATION APPLIED before it runs the checks.

THE MUTATIONS
-------------
Each undoes one load-bearing property of the population-first policy:

  the population-first rule is inverted   -> the order is wrong
  the width ceiling is raised to 256      -> the ceiling is gone
  the population step is set to zero      -> the population cannot grow
  the cap is ignored                      -> the population is unbounded
  the stop is turned into a widening      -> a stop is not a decision

Run: python tools/mutation_check_population.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import Callable, Dict, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

MODULE = os.path.join(_SRC, "population_escalation.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_population_escalation.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _set_constant(source: str, name: str, literal: str) -> str:
    pattern = re.compile(
        r"^(%s(?::\s*[^=\n]+)?\s*=\s*)(.*)$" % re.escape(name),
        re.MULTILINE)
    if not pattern.search(source):
        raise SystemExit("MUTATION HARNESS BROKEN: %r is not assigned at "
                         "module level." % name)
    return pattern.sub(lambda m: m.group(1) + literal, source, count=1)


def with_mutated(mutate: Callable[[str], str]) -> Tuple[int, str, bool]:
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


def m_order_inverted(src: str) -> str:
    """the population-first rule is INVERTED -> it widens first"""
    old = """        if population + self.population_step <= cap:
            return Escalation(
                width_needed=needed, width_used=needed,
                population_before=population,
                population_after=population + self.population_step,
                reason=GROW_POPULATION)"""
    new = """        if population + self.population_step <= cap:
            return Escalation(
                width_needed=needed, width_used=needed,
                population_before=population,
                population_after=population,
                reason=WIDEN)  # MUTATED: widened first"""
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the grow branch was not "
                         "found")
    return src.replace(old, new, 1)


def m_ceiling_raised(src: str) -> str:
    """the width ceiling is raised to 256"""
    return _set_constant(src, "POPULATION_FIRST_WIDTHS",
                         "(1, 4, 8, 16, 32, 64, 128, 256)")


def m_step_zero(src: str) -> str:
    """the population step is ZERO -> the population cannot grow

    AND IT IS A DATACLASS FIELD, not a module constant, so the
    constant-replacement helper cannot reach it. MEASURED: the harness
    reported itself BROKEN on the first attempt, which is the right
    behaviour -- a mutation that cannot apply must not be reported as
    a result. So the mutation edits the USE site instead.
    """
    old_use = "population_after=population + self.population_step,"
    new_use = "population_after=population + 0,  # MUTATED: no growth"
    if old_use not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the population step's "
                         "use site was not found")
    return src.replace(old_use, new_use, 1)


def m_cap_ignored(src: str) -> str:
    """the cap is IGNORED -> the population is unbounded"""
    old = "        if population + self.population_step <= cap:"
    new = "        if True:  # MUTATED: the cap is ignored"
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the cap check was not "
                         "found")
    return src.replace(old, new, 1)


def m_stop_becomes_widening(src: str) -> str:
    """the STOP is turned into a WIDENING -> a stop is not a decision"""
    old = """        return Escalation(width_needed=needed, width_used=needed,
                          population_before=population,
                          population_after=population,
                          reason=STOPPED)"""
    new = """        return Escalation(width_needed=needed, width_used=needed,
                          population_before=population,
                          population_after=population,
                          reason=WIDEN)  # MUTATED: a stop is not a decision"""
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the stop branch was not "
                         "found")
    return src.replace(old, new, 1)


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the population-first rule is inverted", m_order_inverted),
    ("the width ceiling is raised to 256", m_ceiling_raised),
    ("the population step is set to zero", m_step_zero),
    ("the cap is ignored", m_cap_ignored),
    ("the stop becomes a widening", m_stop_becomes_widening),
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
