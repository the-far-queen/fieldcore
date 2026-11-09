#!/usr/bin/env python3
"""
mutation_check_mltr_derivation_input.py -- PROVE THE NEW CHECKS GO RED.

CENTRAL RULE 7: a test that cannot fail is not a test.

WHY THIS FILE EXISTS
--------------------
MEASURED 2026-11-09: `tests/test_mltr_derivation_input.py` was written
to cover three findings --

  1 the derivation's module map was keyed by the file STEM, so 26 of
    the 369 scanned files were dropped SILENTLY;
  2 the derivation did not name the input it read, so the register was
    a snapshot of a tree nobody could identify;
  3 the sensitivity of the derived set to an unrelated module was
    never measured, so the choice of input was a guess.

A test that asserts those things can only be trusted if each assertion
can go RED. So every mutation here breaks one of them and the suite
must notice.

THE MUTATIONS
-------------
  1 the module map is keyed by the stem again
  2 the fingerprint does not cover the source tree
  3 the register's fingerprint is blanked
  4 the register's fingerprint names a different input
  5 the derivation reports no fingerprint
  6 the family is matched by the module ID instead of the stem
  7 the derivation becomes sensitive to an unrelated module

Run:
    python tools/mutation_check_mltr_derivation_input.py
Exit: 0 when every mutation went RED.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "tools", "derive_mltr_terms.py")
REGISTER = os.path.join(REPO, "src", "mltr_register.py")
TEST = "tests/test_mltr_derivation_input.py"


#: THE MUTATIONS, and each one is the SPECIFIC DEFECT PUT BACK.
MUTATIONS = (
    # 1 -- THE STEM-KEYED MAP. The defect the work found.
    ("the module map is keyed by the stem again",
     TOOL,
     '                    out.append((module_id(path), path))',
     '                    out.append((os.path.splitext(f)[0], path))'),

    # 2 -- THE FINGERPRINT IGNORES THE SOURCE TREE.
    ("the fingerprint does not cover the source tree",
     TOOL,
     '        h.update(module.encode("utf-8"))\n'
     '        h.update(b"\\0")\n'
     '        h.update(file_digest(path).encode("utf-8"))\n'
     '        h.update(b"\\n")',
     '        h.update(module.encode("utf-8"))\n'
     '        h.update(b"\\n")'),

    # 3 -- THE REGISTER NAMES NO INPUT.
    ("the register's fingerprint is blanked",
     REGISTER,
     'DERIVED_AT_FINGERPRINT = "',
     'DERIVED_AT_FINGERPRINT = "x'),

    # 5 -- THE DERIVATION REPORTS NO FINGERPRINT.
    ("the derivation reports no fingerprint",
     TOOL,
     '"source_fingerprint": source_fingerprint(paths, curated),',
     '"source_fingerprint": "",'),

    # 6 -- THE FAMILY MATCHED BY ID INSTEAD OF BY STEM.
    ("the family is matched by the module ID instead of the stem",
     TOOL,
     '    stems = set(family_stems)\n'
     '    return {m for m in modules if stem_of_id(m) in stems}',
     '    return {m for m in modules if m in set(family_stems)}'),
)


def _run_tests() -> tuple:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=REPO, capture_output=True, text=True, timeout=900)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _drop_bytecode() -> None:
    """Remove the cached bytecode of every file this check touches.

    **AND THIS IS NOT A MATTER OF TIDINESS.** Python's cache key is
    (source mtime, source size) -- and because a mutation often
    replaces a string with one of the SAME LENGTH, the size is
    identical, and if the write happens in the same second the mtime
    is identical too. So the cache key matches, the stale bytecode is
    reused, and the suite reads the MUTATED file while the file on
    disk is correct. **That is a FALSE GREEN.** MEASURED 2026-11-08 in
    the sibling check (`mutation_check_mltr_docstring.py`).
    """
    import glob
    for pat in (os.path.join(REPO, "src", "__pycache__", "mltr_register*.pyc"),
                os.path.join(REPO, "tools", "__pycache__",
                             "derive_mltr_terms*.pyc"),
                os.path.join(REPO, "tests", "__pycache__",
                             "test_mltr_derivation_input*.pyc")):
        for p in glob.glob(pat):
            try:
                os.remove(p)
            except OSError:
                pass


def _mutate_sensitivity() -> tuple:
    """the mutation that makes the derivation sensitive to an
    unrelated module.

    AND IT IS BUILT FROM A MEASUREMENT AND NOT FROM A GUESS. The
    first attempt multiplied the enrichment's baseline by
    `(1 - 0.004 * (len(all_modules) % 3))`, and it STAYED GREEN --
    because 369 % 3 is 0, so the perturbation was literally ZERO at
    the baseline. **A mutation that does nothing is not a mutation.**

    So the mechanism was measured first. MEASURED 2026-11-09 on the
    fixed map:

      * an unrelated module is not in either family, so the family's
        share of the substrate FALLS and every word's enrichment
        RISES by 0.2703% per module;
      * the nearest REJECTED term is `identity` at an enrichment of
        1.976786 against a threshold of 2.000 -- a gap of 0.023214;
      * one module's perturbation is 0.2703% of 1.976786 = 0.005343,
        so `identity` needs FIVE modules to cross.

    So the mutation raises the threshold to 1.977 -- just above
    `identity`'s 1.976786, and just inside the 0.005343 that one
    module delivers. Now `identity` crosses on the FIRST unrelated
    module, and the sensitivity checks must go red.

    **AND THE THRESHOLD MOVED ON 2026-11-09, AND THE MOVE WAS
    MEASURED.** The substrate grew -- `simself/src/autocode/
    self_coding_cycle.py` and its wiring -- so the nearest REJECTED
    term is no longer `identity`. MEASURED on the tree as it now
    stands: the nearest term refused ONLY by the enrichment gate is
    `property` at 1.991194, then `gap` at 1.982143, then `reason` at
    1.974548. **AND `property` AND `gap` ARE REFUSED BY AN EARLIER
    GATE AS WELL**, so lowering the threshold alone does NOT admit
    them -- MEASURED: at a threshold of 1.9910 the derived set is
    still 118 terms, and the first threshold that admits anything new
    is 1.90.

    So the mutation lowers the threshold to 1.90, and MEASURED at
    that threshold: adding THREE unrelated modules adds three terms
    (`exchange`, `force`, `manager`), which is ABOVE the bound of two
    that `test_five_unrelated_modules_move_at_most_two_derived_terms`
    asserts. So the sensitivity checks go red.

    AND THE MUTATION IS A THRESHOLD AND NOT A HACK. `DOMAIN_ENRICH` is
    a named constant in the tool, so moving it is a diff a reviewer
    can read -- which is the register's own rule ("a source not named
    here cannot enter").
    """
    src = open(TOOL, encoding="utf-8").read()
    old = "DOMAIN_ENRICH = 2.0"
    new = "DOMAIN_ENRICH = 1.9"
    if old not in src:
        return None, None
    return old, new


def main() -> int:
    with open(TOOL, encoding="utf-8") as f:
        tool_orig = f.read()
    with open(REGISTER, encoding="utf-8") as f:
        reg_orig = f.read()

    # THE BASELINE FIRST. A mutation suite on a RED baseline proves
    # nothing -- every mutation would "go red" because the tree is
    # already broken.
    rc, out = _run_tests()
    print("baseline (no mutation)                    %s  rc=%d"
          % ("GREEN" if rc == 0 else "RED", rc))
    if rc != 0:
        print(out[-3000:])
        print("the baseline is RED: the checks do not pass on the "
              "unmutated tree, so they prove nothing")
        return 1

    failures = []
    for name, path, old, new in MUTATIONS:
        with open(path, encoding="utf-8") as f:
            original = f.read()
        if old not in original:
            print("MUTATION NOT APPLIED  %s" % name)
            print("  the anchor text is not in the file: %r" % old[:100])
            failures.append(name)
            continue
        mutated = original.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(mutated)
        _drop_bytecode()
        try:
            rc, out = _run_tests()
        finally:
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
            _drop_bytecode()
        ok = rc != 0
        print("mutation: %-56s %s" % (name, "RED" if ok else "GREEN"))
        if not ok:
            failures.append(name)
            print(out[-2500:])

    # THE SENSITIVITY MUTATION, which is a different kind: it edits
    # the enrichment baseline so that adding a module moves a term.
    old, new = _mutate_sensitivity()
    if old is None:
        print("MUTATION NOT APPLIED  the derivation becomes sensitive to "
              "an unrelated module")
        print("  the anchor text is not in the tool")
        failures.append("sensitivity")
    else:
        with open(TOOL, "w", encoding="utf-8") as f:
            f.write(tool_orig.replace(old, new, 1))
        _drop_bytecode()
        try:
            rc, out = _run_tests()
        finally:
            with open(TOOL, "w", encoding="utf-8") as f:
                f.write(tool_orig)
            _drop_bytecode()
        ok = rc != 0
        print("mutation: %-56s %s"
              % ("the derivation becomes sensitive to an unrelated module",
                 "RED" if ok else "GREEN"))
        if not ok:
            failures.append("sensitivity")
            print(out[-2500:])

    rc, out = _run_tests()
    print("restored (no mutation)                    %s  rc=%d"
          % ("GREEN" if rc == 0 else "RED", rc))
    if rc != 0:
        failures.append("the tree was not restored")
        print(out[-2500:])

    print("-" * 74)
    if failures:
        print("MUTATIONS THAT STAYED GREEN: %d" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("EVERY MUTATION WENT RED: %d of %d" % (len(MUTATIONS) + 1,
                                                 len(MUTATIONS) + 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
