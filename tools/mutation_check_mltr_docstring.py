#!/usr/bin/env python3
"""
mutation_check_mltr_docstring.py -- PROVE THE DOCSTRING CHECKS GO RED.

WHY THIS FILE EXISTS
--------------------

MEASURED 2026-11-08. The register's docstring said "110 DERIVED" and
"14 engineering". The register held 109 and 13. **AND THE REGISTER'S
OWN COUNT TEST WAS GREEN THE WHOLE TIME**, because it checked the
REGISTER and not the PROSE about the register.

**A TEST THAT CHECKS THE REGISTER AND NOT ITS PROSE IS HALF A TEST.**

So `tests/test_mltr_docstring_numbers.py` was written to check the
prose, and CENTRAL RULE 7 says a check that cannot fail is not a
check -- so every mutation here puts a STALE NUMBER BACK into the
prose and the suite must go red.

THE MUTATIONS
-------------

  1 the derived count is wrong in the prose
  2 the curated count is wrong in the prose
  3 the total is wrong in the prose
  4 a domain count is wrong in the table
  5 the derived split's engineering count is wrong
  6 the quoted check line is wrong
  7 the gap does not follow from the spec and the measurement
  8 the search-index comment is wrong

Run:
    python tools/mutation_check_mltr_docstring.py
Exit: 0 when every mutation went RED.
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TARGET = os.path.join(REPO, "src", "mltr_register.py")
TEST = "tests/test_mltr_docstring_numbers.py"


#: THE MUTATIONS, and each one is a STALE NUMBER PUT BACK.
#:
#: AND A MUTATION THAT ONLY ADDS A LINE PROVES NOTHING -- so every one
#: of these puts back the exact drift that was MEASURED on 2026-11-08,
#: because that is the mutation that shows the check is watching the
#: number and not the file.
MUTATIONS = (
    ("the derived count is wrong in the prose",
     "    109 DERIVED   produced by a COMMAND",
     "    110 DERIVED   produced by a COMMAND"),

    ("the curated count is wrong in the prose",
     "    306 CURATED   a person read the word off the substrate and wrote",
     "    305 CURATED   a person read the word off the substrate and wrote"),

    ("the total is wrong in the prose",
     "    the register holds 415 terms",
     "    the register holds 416 terms"),

    ("a domain count is wrong in the table",
     "    engineering    76",
     "    engineering    75"),

    ("the derived split's engineering count is wrong",
     "MEASURED, that command prints 109 derived terms -- 96 control, 13",
     "MEASURED, that command prints 109 derived terms -- 96 control, 14"),

    ("the quoted check line is wrong",
     "reports `derived terms: 109   in the register: 109   missing: 0",
     "reports `derived terms: 110   in the register: 110   missing: 0"),

    ("the gap does not follow from the spec and the measurement",
     "    the GAP          35   what is still missing",
     "    the GAP          34   what is still missing"),

    ("the search-index comment is wrong",
     "#: terms -- so without the index it is 415 lookups per token.",
     "#: terms -- so without the index it is 306 lookups per token."),
)


def _run_tests() -> tuple:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=REPO, capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _drop_bytecode() -> None:
    """Remove the module's cached bytecode.

    **AND THIS IS NOT A MATTER OF TIDINESS -- IT IS THE BUG THIS FILE
    HIT.** MEASURED 2026-11-08: the mutation check wrote the file back
    with the original BYTES, and the restore left a stale `.pyc` in
    `src/__pycache__/`. Python's cache key is (source mtime, source
    size) -- and because the mutation replaced "35" with "34" the SIZE
    WAS IDENTICAL, and because the write happened in the SAME SECOND
    the MTIME WAS IDENTICAL TOO. So the cache key matched, the stale
    bytecode was reused, and the suite read the MUTATED docstring
    while the file on disk was correct.

    **AND THAT IS A FALSE GREEN AND NOT A FALSE RED**, so it would
    have hidden a real defect. The bytecode is dropped after EVERY
    write, mutated or restored, so the source is always the source.
    """
    import glob
    for pat in (os.path.join(REPO, "src", "__pycache__",
                             "mltr_register*.pyc"),):
        for p in glob.glob(pat):
            try:
                os.remove(p)
            except OSError:
                pass


def main() -> int:
    with open(TARGET, encoding="utf-8") as f:
        original = f.read()

    # AND THE BASELINE FIRST.
    rc, out = _run_tests()
    print("baseline (no mutation)                    %s  rc=%d"
          % ("GREEN" if rc == 0 else "RED", rc))
    if rc != 0:
        print(out[-3000:])
        print("the baseline is RED: the checks do not pass on the "
              "unmutated tree, so they prove nothing")
        return 1

    failures = []
    for name, old, new in MUTATIONS:
        if old not in original:
            print("MUTATION NOT APPLIED  %s" % name)
            print("  the anchor text is not in the file: %r" % old[:100])
            failures.append(name)
            continue
        mutated = original.replace(old, new, 1)
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(mutated)
        _drop_bytecode()
        try:
            rc, out = _run_tests()
        finally:
            # AND THE TREE IS RESTORED, ALWAYS.
            with open(TARGET, "w", encoding="utf-8") as f:
                f.write(original)
            _drop_bytecode()
        ok = rc != 0
        print("mutation: %-46s %s" % (name, "RED" if ok else "GREEN"))
        if not ok:
            failures.append(name)
            print(out[-2500:])

    rc, out = _run_tests()
    print("restored (no mutation)                    %s  rc=%d"
          % ("GREEN" if rc == 0 else "RED", rc))
    if rc != 0:
        failures.append("the tree was not restored")

    print("-" * 74)
    if failures:
        print("MUTATIONS THAT STAYED GREEN: %d" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("EVERY MUTATION WENT RED: %d of %d" % (len(MUTATIONS),
                                                 len(MUTATIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
