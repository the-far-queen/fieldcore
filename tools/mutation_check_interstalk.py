"""
tools/mutation_check_interstalk.py -- the live-path wiring, shown able
to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
SO THIS HARNESS MUTATES THE SOURCE OF THE MODULE UNDER TEST, and it
PROVES THE MUTATION APPLIED before it runs the checks.

THE MUTATIONS
-------------
Each undoes one part of the population-first wiring in the LIVE path:

  the policy is not consulted          -> the escalation is a stub
  the width-first ladder is restored    -> the population never grows
  the population is not recorded        -> the ledger lies
  the report loses the population       -> the measurement is invisible
  the irrecoverable path skips the policy -> the branch is unreachable

Run: python tools/mutation_check_interstalk.py
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

MODULE = os.path.join(_SRC, "interstalk_link.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_interstalk_population_first.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


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


def m_policy_not_consulted(src: str) -> str:
    """the policy is NOT consulted -> the escalation is a stub"""
    old = "            esc = self._policy.decide(len(channel.taps), population,"
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the policy call was "
                         "not found")
    return src.replace(
        old,
        "            esc = PE_Escalation(width_needed=needed, width_used=needed,"
        "                population_before=population,"
        "                population_after=population, reason='not_worth_knowing')"
        "            # MUTATED\n"
        "            _ = self._policy", 1)


def m_width_first_restored(src: str) -> str:
    """the width-first ladder is RESTORED -> the population never grows"""
    old = "            used = esc.width_used\n            escalation = esc.reason"
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the escalation "
                         "assignment was not found")
    return src.replace(
        old,
        "            nxt = escalate(needed)\n"
        "            used = nxt if nxt is not None else needed\n"
        "            escalation = NEEDS_MORE  # MUTATED", 1)


def m_population_not_recorded(src: str) -> str:
    """the population is NOT recorded -> the ledger lies"""
    old = "            population=population,"
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the population field "
                         "was not found")
    return src.replace(old, "            population=0,  # MUTATED", 1)


def m_report_loses_population(src: str) -> str:
    """the report LOSES the population -> the measurement is invisible"""
    old = '            "populations": {str(k): v for k, v in sorted(pops.items())},'
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the report's population "
                         "was not found")
    return src.replace(old, "", 1)


def m_irrecoverable_skips_policy(src: str) -> str:
    """the IRRECOVERABLE path skips the policy -> the branch is
    unreachable

    AND MEASURED THAT IT HAS TO BE THERE: the interstalk channel is
    BINARY. Over 48 configurations the alignment is 1.000000 or
    0.000000, never between, so the middle path -- allowed but below
    the resolve threshold -- is unreachable, and the escalation would
    never fire.
    """
    old = """            esc = self._policy.decide(len(channel.taps),
                                       len(pair.neighbours),
                                       readable=False,
                                       max_population=self.max_population)"""
    if old not in src:
        raise SystemExit("MUTATION HARNESS BROKEN: the irrecoverable "
                         "policy call was not found")
    return src.replace(
        old,
        "            esc = None  # MUTATED: the policy is skipped\n"
        "            _ = self._policy", 1)


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the policy is not consulted", m_policy_not_consulted),
    ("the width-first ladder is restored", m_width_first_restored),
    ("the population is not recorded", m_population_not_recorded),
    ("the report loses the population", m_report_loses_population),
    ("the irrecoverable path skips the policy", m_irrecoverable_skips_policy),
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
