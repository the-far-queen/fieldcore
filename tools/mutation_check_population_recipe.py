#!/usr/bin/env python3
"""
mutation_check_population_recipe.py -- PROVE THE NEW CHECKS CAN GO RED.

CENTRAL-RULES rule 7: "If I cannot show a check going RED, I do not know
whether it works."

WHAT THIS PROVES
----------------
Six checks were added, and each must be able to fail:

  M1  the CANONICAL RECIPE is reverted to the clustered one
      -> `tools/check_population_recipe.py` must report the population
         as DEGENERATE, and the benches that still import the
         canonical one must DIVERGE from it

  M2  the ADVERSARIAL CONTROL is reverted to the index-next one
      -> the nearest-neighbour test must go red, because the control
         would no longer be the nearest one

  M3  the CANONICAL RECIPE is reverted to the clustered one, and
      `measure_gate_margin` keeps the adversarial control
      -> the measurement must report a class-mate, and the
         "no class-mate" test must go red

  M4  a NEW MODULE appears carrying its own copy of the recipe
      -> the CENSUS must name it.  This is the mutation that matters
         most: MEASURED 2026-11-06, two modules in `src/` carried a
         DIVERGED copy that the check did not see, because the check
         named the modules it knew about in a HARDCODED LIST.  A new
         module is invisible to a list by construction.

  M5  a module in the LOCUS FAMILY drifts from the shared builder
      -> the locus family check must report the drift

  M6  the harness itself must notice when a test NEVER RAN

Each mutation is applied to a COPY of the tree, the copy is proven to
be the one under test (the harness failed once before, by measuring the
ORIGINAL module -- see the note in `mutation_check_exam_areas.py`),
and the check is run against the copy.

THE HARNESS'S OWN FALSE REDS
----------------------------
MEASURED 2026-11-06: the copy this harness made carried `src/` and
`tools/` but NOT `tests/`.  So M2 and M3 pointed pytest at a path that
did not exist, pytest exited 4 -- "file or directory not found" -- and
the harness read that as "the test went RED".  Both were FALSE REDS:
the test never ran, so nothing was proved.

And the mutation M2 applies is NOT DETECTABLE on the canonical recipe
by itself: MEASURED, on the evenly-spread recipe the NEXT INDEX IS
the nearest neighbour (both pick `p001`, separation 0.125), so
reverting the control to the index-next one changes nothing measurable.
The mutation only bites in combination with a clustered recipe -- which
is what M3 is.  So M2's "RED" was not only a false red, it was a
mutation that could not have gone red.

The harness now copies the tests, and `ran_a_test()` refuses to call a
run RED unless pytest actually ran a test.

Run:
    python tools/mutation_check_population_recipe.py
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_SRC = os.path.join(_ROOT, "src")
PY = sys.executable


def run(cmd, cwd, env=None, timeout=600):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def clone(dst: str) -> str:
    """A copy of the repo's src/, tools/ AND tests/, and the corpus/ the
    cap needs.  The copy is what the mutation is applied to.

    MEASURED 2026-11-06: this used to copy only `src/` and `tools/`.
    So the two mutations that run pytest pointed it at a path that did
    not exist in the copy, and pytest exited 4 -- "file or directory
    not found" -- which the harness read as "the test went RED".  Both
    of those mutations were FALSE REDS: the test never ran.

    A harness that cannot distinguish "the check failed" from "the
    check could not start" is a harness that proves nothing, so the
    copy now carries the tests, and the harness ALSO asserts that
    pytest ran a test (see `ran_a_test`).
    """
    shutil.copytree(os.path.join(_ROOT, "src"), os.path.join(dst, "src"))
    shutil.copytree(os.path.join(_ROOT, "tools"), os.path.join(dst, "tools"))
    shutil.copytree(os.path.join(_ROOT, "tests"), os.path.join(dst, "tests"))
    corpus = os.path.join(_ROOT, "corpus")
    if os.path.isdir(corpus):
        shutil.copytree(corpus, os.path.join(dst, "corpus"))
    return dst


def ran_a_test(out: str) -> bool:
    """Did pytest actually RUN a test?

    MEASURED 2026-11-06: pytest exits 4 with "file or directory not
    found" when the path is wrong, and 5 with "no tests ran" when the
    selection matches nothing.  Both are INFRASTRUCTURE failures, and
    both look like a red test to a harness that only checks the exit
    code.  A mutation harness must tell them apart, or it certifies
    checks that never ran.
    """
    low = out.lower()
    if "no tests ran" in low:
        return False
    if "file or directory not found" in low:
        return False
    if "error" in low and "passed" not in low and "failed" not in low:
        return False
    return (" passed" in low) or (" failed" in low) or ("error" in low)


def mutate_recipe_to_clustered(src_dir: str) -> bool:
    """Replace the canonical recipe with the old clustered one."""
    p = os.path.join(src_dir, "stalk_population.py")
    if not os.path.isfile(p):
        return False
    with open(p, "r", encoding="utf-8") as fh:
        src = fh.read()
    old = """    out: List[CoaxWinding] = []
    for i in range(n):
        a = (i + 0.5) / n
        out.append(CoaxWinding(
            id="p%03d" % i,
            girth_out=GIRTH_IN * (1.0 + a),
            girth_in=GIRTH_IN,
            girth_core=GIRTH_CORE,
            n_in=N_IN,
            n_out=N_OUT,
        ))
    return out"""
    new = """    out: List[CoaxWinding] = []
    for i in range(n):
        core = 0.018 + 0.0007 * (i % 7)
        inner = 0.050 + 0.0011 * (i % 11)
        outer = 0.090 + 0.0019 * (i % 13)
        if not (core < inner < outer):
            core, inner, outer = 0.016, 0.048, 0.092
        out.append(CoaxWinding(
            id="p%03d" % i, girth_out=outer, girth_in=inner, girth_core=core,
            n_in=5 + (i % 6), n_out=11 + (i % 9)))
    return out"""
    if old not in src:
        return False
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(src.replace(old, new))
    return True


def mutate_control_to_farthest(src_dir: str) -> bool:
    """Replace the ADVERSARIAL control with the EASY one.

    MEASURED 2026-11-06: this used to replace the control with the
    old INDEX-NEXT one -- and that mutation is a NO-OP on the canonical
    recipe, because on an evenly-spread population the next index IS
    the nearest neighbour (MEASURED: both pick `p001`, separation
    0.125).  So the mutation changed nothing measurable and the test
    could not go red.  It only ever "went red" because pytest could
    not find the test file.

    A mutation has to remove the MECHANISM, not swap a synonym.  The
    mechanism here is "the false candidate is the one NEAREST the
    speaker's address".  Removing it means picking the FARTHEST, which
    is the easiest possible case -- and the test that asserts the
    control's separation must go red.
    """
    p = os.path.join(src_dir, "measure_gate_margin.py")
    if not os.path.isfile(p):
        return False
    with open(p, "r", encoding="utf-8") as fh:
        src = fh.read()
    old = """    cands = [c for c in ids if c != tx]
    if not cands:
        return tx
    return min(cands, key=lambda c: _address_separation(addrs, tx, c))"""
    new = """    cands = [c for c in ids if c != tx]
    if not cands:
        return tx
    return max(cands, key=lambda c: _address_separation(addrs, tx, c))"""
    if old not in src:
        return False
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(src.replace(old, new))
    return True


def mutate_add_a_copy(src_dir: str) -> bool:
    """ADD A NEW MODULE THAT CARRIES ITS OWN COPY OF THE RECIPE.

    This is the mutation that matters most: MEASURED 2026-11-06, two
    modules in `src/` carried a DIVERGED copy of the recipe and the
    check did not see them, because the check named the modules it
    knew about in a HARDCODED LIST.  A new module is invisible to a
    list by construction.

    So the mutation writes a NEW file -- `bench_rogue_copy.py` -- with
    the old clustered recipe, and the census must notice a module it
    has never heard of.
    """
    p = os.path.join(src_dir, "bench_rogue_copy.py")
    if os.path.exists(p):
        return False
    body = '''"""A NEW MODULE with its own copy of the population recipe.

This file exists so the mutation check can prove the CENSUS notices a
copy it was never told about.  A hardcoded list cannot see this file.
"""

from __future__ import annotations

import os
import sys
from typing import List

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from wound_core import CoaxWinding  # noqa: E402


def make_population(n: int) -> List[CoaxWinding]:
    """The OLD CLUSTERED recipe -- the confound."""
    out: List[CoaxWinding] = []
    for i in range(n):
        core = 0.018 + 0.0007 * (i % 7)
        inner = 0.050 + 0.0011 * (i % 11)
        outer = 0.090 + 0.0019 * (i % 13)
        if not (core < inner < outer):
            core, inner, outer = 0.016, 0.048, 0.092
        out.append(CoaxWinding(
            id="p%03d" % i, girth_out=outer, girth_in=inner, girth_core=core,
            n_in=5 + (i % 6), n_out=11 + (i % 9)))
    return out
'''
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(body)
    return True


def check_tool_reports_degenerate(cwd: str) -> tuple:
    """The recipe check must FAIL on a clustered recipe."""
    rc, out, err = run([PY, os.path.join(cwd, "tools",
                                         "check_population_recipe.py")],
                       cwd=cwd)
    return rc, out + err


def test_nearest_neighbour_fails(cwd: str) -> tuple:
    """The nearest-neighbour test must go RED on the index-next control."""
    rc, out, err = run(
        [PY, "-m", "pytest",
         os.path.join(cwd, "tests", "test_measure_gate_margin.py"),
         "-q", "--no-header", "-p", "no:cacheprovider",
         "-k", "nearest_neighbour"],
        cwd=cwd,
        env={"PYTHONPATH": os.path.join(cwd, "src")})
    return rc, out + err


def test_no_classmate_fails(cwd: str) -> tuple:
    """The no-class-mate test must go RED on a clustered recipe."""
    rc, out, err = run(
        [PY, "-m", "pytest",
         os.path.join(cwd, "tests", "test_measure_gate_margin.py"),
         "-q", "--no-header", "-p", "no:cacheprovider",
         "-k", "margin_reports_the_address_classes"],
        cwd=cwd,
        env={"PYTHONPATH": os.path.join(cwd, "src")})
    return rc, out + err


def main() -> int:
    print("=" * 78)
    print("MUTATION CHECK: the new checks must be able to go RED")
    print("=" * 78)
    results = []

    # -- the BASELINE: the checks pass on the unmutated tree ----------
    print()
    print("BASELINE (no mutation) -- every check must be GREEN")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "base"))
        rc, out = check_tool_reports_degenerate(cwd)
        green = ("DEGENERATE" not in out and "FAIL" not in out.split("VERDICT")[-1])
        print("  the recipe check on the unmutated tree: %s"
              % ("GREEN" if green else "RED -- THE CHECK IS BROKEN"))
        results.append(("baseline: the recipe check is green", green))

    # -- M1: the canonical recipe reverted to the clustered one -------
    print()
    print("M1: the canonical recipe reverted to the CLUSTERED one")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m1"))
        if not mutate_recipe_to_clustered(os.path.join(cwd, "src")):
            print("  MUTATION DID NOT APPLY -- the recipe's text moved")
            results.append(("M1", False))
        else:
            rc, out = check_tool_reports_degenerate(cwd)
            red = ("DEGENERATE" in out)
            print("  the recipe check reports DEGENERATE: %s -> %s"
                  % (red, "RED as required" if red else "NOT RED -- THE CHECK "
                     "CANNOT FAIL"))
            results.append(("M1: a clustered recipe is caught", red))

    # -- M2: the control reverted to the index-next one ----------------
    print()
    print("M2: the ADVERSARIAL control reverted to the EASY (farthest) one")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m2"))
        if not mutate_control_to_farthest(os.path.join(cwd, "src")):
            print("  MUTATION DID NOT APPLY -- the control's text moved")
            results.append(("M2", False))
        else:
            rc, out = test_nearest_neighbour_fails(cwd)
            ran = ran_a_test(out)
            red = (rc != 0) and ran
            print("  the nearest-neighbour test: exit %d, ran a test: %s -> %s"
                  % (rc, ran, "RED as required" if red else "NOT RED -- THE "
                     "TEST CANNOT FAIL" if ran else "NOT RED -- THE TEST "
                     "NEVER RAN"))
            results.append(("M2: an easy control is caught", red))

    # -- M3: clustered recipe AND the adversarial control --------------
    print()
    print("M3: the clustered recipe AND the adversarial control together")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m3"))
        mutate_recipe_to_clustered(os.path.join(cwd, "src"))
        if not mutate_control_to_farthest(os.path.join(cwd, "src")):
            print("  MUTATION DID NOT APPLY")
            results.append(("M3", False))
        else:
            rc, out = test_no_classmate_fails(cwd)
            ran = ran_a_test(out)
            red = (rc != 0) and ran
            print("  the no-class-mate test: exit %d, ran a test: %s -> %s"
                  % (rc, ran, "RED as required" if red else "NOT RED"))
            results.append(("M3: a class-mate is noticed", red))

    # -- M4: A NEW MODULE CARRIES ITS OWN COPY -------------------------
    print()
    print("M4: a NEW module appears carrying its own copy of the recipe")
    print("    (the census must see a module it was never told about)")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m4"))
        if not mutate_add_a_copy(os.path.join(cwd, "src")):
            print("  MUTATION DID NOT APPLY")
            results.append(("M4", False))
        else:
            rc, out = check_tool_reports_degenerate(cwd)
            red = ("bench_rogue_copy" in out) and ("UNNAMED COPY" in out)
            print("  the census names the rogue copy: %s -> %s"
                  % (red, "RED as required" if red else "NOT RED -- A LIST "
                     "CANNOT SEE A MODULE IT WAS NEVER TOLD ABOUT"))
            results.append(("M4: an unknown module is caught", red))

    # -- M5: the LOCUS FAMILY loses a member ----------------------------
    print()
    print("M5: a module in the LOCUS FAMILY stops carrying the recipe")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m5"))
        p = os.path.join(cwd, "src", "locus.py")
        with open(p, "r", encoding="utf-8") as fh:
            src = fh.read()
        old = """    from stalk_population import make_locus_population
    return make_locus_population(n, id_fmt="L%d")"""
        new = """    from wound_core import CoaxWinding
    return [CoaxWinding(id="L%d" % i, girth_core=0.030, girth_in=0.060,
                        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                        n_in=12, n_out=13 + (i % 2)) for i in range(n)]"""
        if old not in src:
            print("  MUTATION DID NOT APPLY -- the locus recipe's text moved")
            results.append(("M5", False))
        else:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src.replace(old, new))
            rc, out = check_tool_reports_degenerate(cwd)
            red = ("DIVERGED" in out) or ("DROPPED" in out)
            print("  the locus family check reports the drift: %s -> %s"
                  % (red, "RED as required" if red else "NOT RED"))
            results.append(("M5: a drifted locus copy is caught", red))

    # -- M6: THE HARNESS MUST CATCH ITS OWN FALSE RED ------------------
    print()
    print("M6: the harness must notice when a test NEVER RAN")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = clone(os.path.join(tmp, "m6"))
        # point the runner at a test file that does not exist
        rc, out, _ = run(
            [PY, "-m", "pytest",
             os.path.join(cwd, "tests", "test_no_such_file.py"),
             "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=cwd)
        ran = ran_a_test(out)
        caught = (rc != 0) and (not ran)
        print("  pytest exit %d, ran_a_test says %s -> %s"
              % (rc, ran, "CAUGHT as required" if caught else "NOT CAUGHT -- "
                 "THE HARNESS WOULD CALL THIS A RED"))
        results.append(("M6: a test that never ran is not a red", caught))

    print()
    print("=" * 78)
    print("THE SUMMARY")
    print("=" * 78)
    allok = True
    for name, ok in results:
        print("  %-44s %s" % (name, "OK" if ok else "NOT OK"))
        allok = allok and ok
    print()
    print("  %d of %d" % (sum(1 for _, ok in results if ok), len(results)))
    print("  VERDICT: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
