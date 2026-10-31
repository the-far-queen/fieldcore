"""
mutation_check_ladder_cap.py -- prove the new checks can go RED.

THE RULE (CENTRAL-RULES 7): a test that cannot fail is not a test.

THE DEFECT BEING PROVEN
------------------------
`ladder_cap.py` read the cap conditions' key as "surplus" while
`bench_balance_final.py` writes "peak_surplus". So `worst_surplus()`
returned None, the refusal said the surplus at the peak was
"negative", and the report printed a table of "?"s -- while the
measured surplus is +7.298 bits.

THE MUTATIONS
-------------
Each corrupts the SOURCE the way the bug was, and each must make the
suite RED:

  the reader's key reverts to "surplus"   -> the surplus checks
  the report's key reverts                -> the report check

AND THE HARNESS ASSERTS THE UNMUTATED SUITE IS GREEN FIRST, so a
broken harness cannot produce a mutation "result".

Run: python tools/mutation_check_ladder_cap.py
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

TARGET = os.path.join(_SRC, "ladder_cap.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_dual_ladder.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def with_mutated_source(mutate: Callable[[str], str]) -> Tuple[int, str]:
    """write a mutated source, run the checks, restore the original.

    **AND THE ORIGINAL IS RESTORED IN A FINALLY BLOCK**, so a mutation
    that breaks the harness cannot leave a broken source behind.
    """
    backup = TARGET + ".backup"
    shutil.copy2(TARGET, backup)
    try:
        with open(TARGET, encoding="utf-8") as fh:
            original = fh.read()
        mutated = mutate(original)
        if mutated == original:
            # THE MUTATION DID NOT APPLY. That is the failure mode the
            # previous session's harness had, and it looks like a
            # result. So it is a LOUD failure, not a silent one.
            raise RuntimeError("the mutation did not change the source")
        with open(TARGET, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        return run_tests()
    finally:
        shutil.move(backup, TARGET)


def m_reader_key_reverts(p: str) -> str:
    """the reader looks for "surplus" again -- the original defect"""
    return p.replace('surplus = c.get("peak_surplus")',
                     'surplus = c.get("surplus")', 1)


def m_report_key_reverts(p: str) -> str:
    """the report looks for the bare keys again"""
    return p.replace('surplus = c.get("peak_surplus", c.get("surplus"))',
                     'surplus = c.get("surplus")', 1)


def m_report_capacity_key_reverts(p: str) -> str:
    return p.replace('capacity = c.get("peak_capacity_bits", c.get("capacity"))',
                     'capacity = c.get("capacity")', 1)


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the reader's key reverts to 'surplus'", m_reader_key_reverts),
    ("the report's surplus key reverts", m_report_key_reverts),
    ("the report's capacity key reverts", m_report_capacity_key_reverts),
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
        print(out[-3000:])
        return 1
    print("  the unmutated suite is GREEN (%d checks)" % _count(out))
    print()

    went_red = 0
    for name, mutate in MUTATIONS:
        try:
            code, out = with_mutated_source(mutate)
        except RuntimeError as exc:
            print("  %-46s HARNESS BROKEN: %s" % (name, exc))
            continue
        red = code != 0
        went_red += 1 if red else 0
        print("  %-46s %s" % (name, "RED" if red else "GREEN  <-- NOT CAUGHT"))
        if not red:
            print("      (the suite still passed with this corruption)")

    print()
    print("  %d of %d mutations went RED" % (went_red, len(MUTATIONS)))
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
