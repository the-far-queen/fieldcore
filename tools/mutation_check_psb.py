#!/usr/bin/env python3
"""
mutation_check_psb.py -- the PSB schema's invariants can go red.

Bobby, 2026-11-06.

**WHY A MUTATION CHECK, AND NOT JUST A TEST SUITE.** A test suite
proves the schema holds NOW. It does not prove the test would NOTICE
if the schema broke -- and a test that cannot fail is not a test.
Each mutation below breaks ONE invariant, and the check asserts the
test suite goes red.

**AND THE MUTATIONS ARE MUTATIONS OF THE SCHEMA, NOT OF THE TEST.**
Each one changes `simself/src/constitutional/psb_schema.py` -- the
schema the substrate uses -- and then runs the real test file against
the mutated schema. A mutation of the test file would prove nothing.

THE TWELVE MUTATIONS:
  M1  I1 -- the id shape check is removed
  M2  I1 -- the duplicate-id refusal is removed
  M3  I2 -- the word-must-be-in-the-inflections check is removed
  M4  I3 -- the surface-form check is removed
  M5  I4 -- the senses-must-be-non-empty check is removed
  M6  I5 -- the contexts check is removed
  M7  I5 -- the snr range check is removed
  M8  I6 -- the relation check is removed
  M9  I7 -- the layer check is removed
  M10 I8 -- the provenance check is removed
  M11 I9 -- the revision check is removed
  M12 I11 -- the distinct-domains check is removed

AND TWO MORE, FOR THE RULES THAT ARE NOT INVARIANTS:
  M13 a revision with no reason is allowed
  M14 a retirement DELETES the PSB instead of retiring it

Run:
    python tools/mutation_check_psb.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
FIELD = os.path.dirname(HERE)
WORK_REPOS = os.path.dirname(FIELD)
SCHEMA = os.path.join(WORK_REPOS, "simself", "src", "constitutional",
                      "psb_schema.py")
TEST = os.path.join(FIELD, "tests", "test_psb.py")


def _python() -> str:
    """THE INTERPRETER THAT HAS THE PROJECT'S DEPENDENCIES.

    AND WHY IT IS NOT sys.executable. MEASURED 2026-11-06: the bare
    `python` on PATH is hermes' own 3.11 venv, which has no numpy --
    so `import psb_schema` fails there and the mutation check would
    report "the mutation went unnoticed" for every mutation, when the
    truth is that the schema was never loaded.
    """
    for cand in (os.path.join(WORK_REPOS, ".venv", "Scripts",
                              "python.exe"),
                 os.path.join(WORK_REPOS, ".venv", "bin", "python")):
        if os.path.isfile(cand):
            return cand
    return sys.executable


#: THE MUTATIONS: (code, name, old, new, the test that must go red)
MUTATIONS: List[Tuple[str, str, str, str, str]] = [
    ("M1", "I1 -- the id shape check is removed",
     '    elif not _ID_RE.match(psb.id):',
     '    elif False:',
     "test_i1_an_id_that_is_not_kebab_case_is_refused"),

    ("M2", "I1 -- the duplicate-id refusal is removed",
     '    if psb.id in reg:\n'
     '        return False, ["I1: the id %r is already in the registry -- a "',
     '    if False:\n'
     '        return False, ["I1: the id %r is already in the registry -- a "',
     "test_i1_a_duplicate_id_is_refused"),

    ("M3", "I2 -- the word-must-be-in-the-inflections check is removed",
     '    elif psb.word.lower() not in {f.lower() for f in psb.inflections}:',
     '    elif False:',
     "test_i2_a_word_that_is_not_among_the_inflections_is_refused"),

    ("M4", "I3 -- the surface-form check is removed",
     '            if not _shares_stem(w, f):',
     '            if False:',
     "test_i3_an_inflection_that_is_not_a_surface_form_is_refused"),

    ("M5", "I4 -- the senses-must-be-non-empty check is removed",
     '    if not psb.senses:\n'
     '        bad.append("I4: the senses are empty -- a PSB with no senses is "',
     '    if False:\n'
     '        bad.append("I4: the senses are empty -- a PSB with no senses is "',
     "test_i4_a_psb_with_no_senses_is_refused"),

    ("M6", "I5 -- the contexts check is removed",
     '        if not s.contexts:',
     '        if False:',
     "test_i5_an_incomplete_sense_is_refused"),

    ("M7", "I5 -- the snr range check is removed",
     '        if not (0.0 <= snr <= 1.0):',
     '        if False:',
     "test_i5_an_incomplete_sense_is_refused"),

    ("M8", "I6 -- the relation check is removed",
     '        for end in (r.from_id, r.to_id):\n'
     '            if end not in reg:',
     '        for end in (r.from_id, r.to_id):\n'
     '            if False:',
     "test_i6_a_relation_to_a_missing_psb_is_refused"),

    ("M9", "I7 -- the layer check is removed",
     '    if psb.layer not in LAYERS:',
     '    if False:',
     "test_i7_a_layer_outside_the_six_is_refused"),

    ("M10", "I8 -- the provenance check is removed",
     '        if not psb.provenance:\n'
     '            bad.append("I8: an admitted PSB has no provenance -- a "',
     '        if False:\n'
     '            bad.append("I8: an admitted PSB has no provenance -- a "',
     "test_i8_an_admitted_psb_with_no_provenance_is_refused"),

    ("M11", "I9 -- the revision check is removed",
     '    if psb.revision < 1:',
     '    if False:',
     "test_i9_a_revision_below_one_is_refused"),

    ("M12", "I11 -- the distinct-domains check is removed",
     '    domains = [s.domain for s in psb.senses]',
     '    domains = []',
     "test_i11_two_senses_in_one_domain_are_refused"),

    ("M13", "a revision with no reason is allowed",
     '    if not (reason or "").strip():\n'
     '        return False, ["a revision with no reason is a replacement, "',
     '    if False:\n'
     '        return False, ["a revision with no reason is a replacement, "',
     "test_a_revision_with_no_reason_is_refused"),

    ("M14", "a retirement DELETES the PSB instead of retiring it",
     '    reg.put(retired)\n    return True, []\n\n\ndef _from_dict',
     '    reg.remove(psb_id)\n    return True, []\n\n\ndef _from_dict',
     "test_a_retirement_keeps_the_psb_readable"),
]


def _run_tests(root: str) -> Tuple[int, str]:
    """Run the PSB test file against a tree at `root`."""
    proc = subprocess.run(
        [_python(), "-m", "pytest", TEST, "-q", "--no-header", "-x"],
        capture_output=True, text=True, cwd=root,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    print("=" * 78)
    print("THE PSB SCHEMA -- the mutation check")
    print("=" * 78)
    print()
    print("BASELINE (no mutation) -- the schema holds")
    src = open(SCHEMA, encoding="utf-8").read()
    ok = True
    tmp = tempfile.mkdtemp(prefix="psb_mut_")
    try:
        # -- the baseline ------------------------------------------------
        shutil.copy2(SCHEMA, SCHEMA + ".bak")
        rc, out = _run_tests(FIELD)
        print("  the test file: rc=%d -- %s" % (
            rc, "PASSED" if rc == 0 else "FAILED"))
        if rc != 0:
            print("  the baseline is RED -- the mutation check cannot "
                  "start")
            print(out[-1500:])
            return 2
        print()

        print("AND THE MUTATIONS CAN GO RED")
        print()
        for code, name, old, new, test_name in MUTATIONS:
            print("  %-3s %s" % (code, name))
            if old not in src:
                print("      NOT APPLIED -- the anchor is not in the file.")
                print("      the mutation is stale, so it proves nothing.")
                print("      RED as required (the harness cannot check it)")
                ok = False
                print()
                continue
            mutated = src.replace(old, new, 1)
            with open(SCHEMA, "w", encoding="utf-8") as fh:
                fh.write(mutated)
            try:
                rc, out = _run_tests(FIELD)
            finally:
                with open(SCHEMA, "w", encoding="utf-8") as fh:
                    fh.write(src)
            if rc == 0:
                print("      the mutation did NOT turn the suite red")
                print("      -> RED as required (the mutation went "
                      "unnoticed)")
                print("      expected %s to fail" % test_name)
                ok = False
            else:
                failed = [ln for ln in out.splitlines()
                          if ln.startswith("FAILED") or " failed" in ln]
                print("      the suite went RED: %s"
                      % (failed[0][:100] if failed else out.strip()[-100:]))
                print("      -> caught: %s" % test_name)
                print("      GREEN, as required (the mutation was caught)")
            print()

        # -- the schema is restored -------------------------------------
        with open(SCHEMA, "w", encoding="utf-8") as fh:
            fh.write(src)
        rc, out = _run_tests(FIELD)
        if rc != 0:
            print("  THE SCHEMA DID NOT COME BACK GREEN -- rc=%d" % rc)
            print(out[-1500:])
            ok = False
        else:
            print("  and the schema is restored and green again")

        print()
        print("=" * 78)
        if ok:
            print("VERDICT: PASS")
            return 0
        print("VERDICT: FAIL")
        return 1
    finally:
        if os.path.isfile(SCHEMA + ".bak"):
            shutil.copy2(SCHEMA + ".bak", SCHEMA)
            os.remove(SCHEMA + ".bak")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
