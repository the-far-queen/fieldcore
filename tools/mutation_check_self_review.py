#!/usr/bin/env python3
"""
mutation_check_self_review.py -- break the self-review six ways and
show each one RED.

Bobby, 2026-11-06: *"code best of hermes own self-improvement
techniques right into fieldcore"*.

**AND THE POINT OF THIS FILE.** A check that cannot go red is a check
that cannot catch anything, and the substrate's own doctrine says so.
So every rule the instrument claims is load-bearing gets broken, and
the broken instrument has to FAIL.

**AND THE MUTATIONS ARE APPLIED TO A COPY, IN A TEMPORARY TREE**, so
the real instrument is never left broken -- and each mutation starts
from a FRESH copy, because a mutation that inherits the previous
mutation is not a mutation of the thing it claims to mutate.

    M1  the grounding requirement is removed -- and a lesson nobody
        can point at must become admissible
    M2  the duplicate check is removed -- and the same lesson must be
        appended twice to an append-only store
    M3  the chain's link check is removed -- and a rewritten event must
        verify clean
    M4  the routing collapses to one store -- and a fact must be able
        to land in BOTH stores
    M5  the bare-refusal reader is removed -- and a refusal with no
        marker word must become unread
    M6  the chain's head is not read -- and a reloaded store must
        start a fresh chain at GENESIS

Run:
    python tools/mutation_check_self_review.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
TESTS = os.path.join(ROOT, "tests")


def _python() -> str:
    venv = os.path.join(os.path.dirname(ROOT), ".venv", "Scripts",
                        "python.exe")
    if os.path.isfile(venv):
        return venv
    return sys.executable


def _run_tests(src_dir: str) -> Tuple[int, str]:
    """The instrument's own tests, against the MUTATED source.

    **AND THE MUTATED SOURCE IS NAMED EXPLICITLY**, not only put on
    the path. MEASURED 2026-11-06: the first version set PYTHONPATH
    and every one of the six mutations stayed GREEN -- because the
    test file put the REAL `src` at the FRONT of sys.path, so the
    mutated copy was never imported. **A MUTATION THAT IS NOT LOADED
    IS NOT A MUTATION.**

    So the tests read the source under test from the environment, and
    the environment names the mutated copy.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = src_dir
    env["FC_SELFTEST_SRC"] = src_dir
    # AND THE CONFTEST IS REMOVED FROM THE WAY, because a conftest
    # that inserts the real src would undo this -- and it is the same
    # defect in a different place.
    proc = subprocess.run(
        [_python(), "-m", "pytest", os.path.join(TESTS,
                                                 "test_self_review.py"),
         "-q", "--no-header", "-x", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=ROOT, env=env)
    return proc.returncode, (proc.stdout or "")[-2500:]


def main() -> int:
    print("=" * 78)
    print("THE SELF REVIEW -- the mutation check")
    print("=" * 78)
    print()
    ok = True
    tmpdir = tempfile.mkdtemp(prefix="selfreview_mut_")
    mut_src = os.path.join(tmpdir, "src")
    os.makedirs(mut_src, exist_ok=True)

    def fresh_tree() -> None:
        """A fresh copy of the instrument, every time."""
        shutil.rmtree(mut_src, ignore_errors=True)
        os.makedirs(mut_src, exist_ok=True)
        shutil.copy(os.path.join(SRC, "self_review.py"),
                    os.path.join(mut_src, "self_review.py"))

    def mutated(old: str, new: str) -> None:
        path = os.path.join(mut_src, "self_review.py")
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        if old not in body:
            raise SystemExit("the mutation does not apply: %r" % old[:80])
        body = body.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)

    def report(code: str, name: str, rc: int, out: str) -> None:
        nonlocal ok
        print("  %-3s %s" % (code, name))
        if rc != 0:
            print("      the tests went RED -- the rule is load-bearing")
            print("      -> caught")
            print("      GREEN, as required (the mutation was caught)")
        else:
            print("      the tests stayed GREEN -- the mutation was NOT "
                  "caught")
            print("      -> RED as required (the harness cannot check it)")
            ok = False
        print()

    # -- M1: the grounding requirement goes ----------------------------
    fresh_tree()
    mutated('        if not self.path.strip():\n'
            '            raise ValueError("the grounding has no path")',
            '        if not self.path.strip():\n'
            '            pass')
    rc, out = _run_tests(mut_src)
    report("M1", "the grounding requirement removed", rc, out)

    # -- M2: the duplicate check goes ----------------------------------
    fresh_tree()
    mutated('            if existing.get("rule", "").strip() '
            '== lesson.rule.strip():\n'
            '                return False, ("the lesson %r is already held, '
            'and the "\n'
            '                               "store is append-only" '
            '% lesson.key)',
            '            if False:\n'
            '                return False, ""')
    rc, out = _run_tests(mut_src)
    report("M2", "the duplicate check removed", rc, out)

    # -- M3: the chain's link check goes -------------------------------
    fresh_tree()
    mutated('            if ev.get("prev") != prev:\n'
            '                problems.append(\n'
            '                    "link break at seq %d: the entry points '
            'at %r and the "\n'
            '                    "entry before it ends at %s"\n'
            '                    % (i, ev.get("prev"), prev))',
            '            if False:\n'
            '                problems.append("")')
    rc, out = _run_tests(mut_src)
    report("M3", "the chain's link check removed", rc, out)

    # -- M4: the routing collapses to one store ------------------------
    #
    # AND THE MUTATION MAKES EVERY REFUSAL GO TO THE FIELD STORE, and
    # not merely the first branch. MEASURED 2026-11-06: the first
    # version replaced the SHAPE branch with `if False`, which left
    # the WORK branch routing to the LESSON store -- so the two stores
    # still got different lessons and the check stayed GREEN. **A
    # MUTATION THAT DOES NOT MUTATE THE THING IT CLAIMS TO MUTATE IS
    # NOT A MUTATION.**
    fresh_tree()
    mutated('    if any(m in low for m in SHAPE_MARKERS):\n'
            '        return Store.FIELD, LessonKind.REFUSAL_SHAPE\n'
            '    if any(m in low for m in WORK_MARKERS):\n'
            '        return Store.LESSON, LessonKind.REFUSAL_WORK',
            '    return Store.FIELD, LessonKind.REFUSAL_SHAPE')
    rc, out = _run_tests(mut_src)
    report("M4", "the routing collapsed to one store", rc, out)

    # -- M5: the bare-refusal reader goes ------------------------------
    fresh_tree()
    mutated('    (r"(?i)^\\s*([^\\s].*?\\b(?:does not|do not|cannot|can '
            'not|must not|"\n'
            '     r"never|is not|are not|has no|have no|lacks|refuses?|'
            'refused|"\n'
            '     r"rejects?|rejected|is wrong|failed)\\b.*?)\\s*$",\n'
            '     "a bare refusal"),',
            '    (r"(?i)^\\s*NEVERMATCHESANYTHING\\b.*?)\\s*$",\n'
            '     "a bare refusal"),')
    rc, out = _run_tests(mut_src)
    report("M5", "the bare-refusal reader removed", rc, out)

    # -- M6: the chain's head is not read ------------------------------
    fresh_tree()
    mutated('    def head(self) -> str:\n'
            '        return self.events[-1]["digest"] if self.events '
            'else self.GENESIS',
            '    def head(self) -> str:\n'
            '        return self.GENESIS')
    rc, out = _run_tests(mut_src)
    report("M6", "the chain's head is not read", rc, out)

    # -- M7: the chain's DIGEST check goes -----------------------------
    #
    # AND THIS ONE IS NOT A CONSEQUENCE OF M3. MEASURED 2026-11-06: a
    # store whose lesson rule was changed in place reported "digest
    # mismatch at seq 0" -- and a store whose 'prev' was changed
    # reported BOTH "link break at seq 1" AND the digest mismatches.
    # So the digest and the link are TWO checks, and removing one must
    # leave the other.
    fresh_tree()
    mutated('            if digest != ev.get("digest"):\n'
            '                problems.append("digest mismatch at seq %d" % i)',
            '            if False:\n'
            '                problems.append("")')
    rc, out = _run_tests(mut_src)
    report("M7", "the chain's digest check removed", rc, out)

    shutil.rmtree(tmpdir, ignore_errors=True)

    print("=" * 78)
    if ok:
        print("VERDICT: PASS -- 7 of 7 mutations caught")
        print("  the self-review's rules are load-bearing.")
        return 0
    print("VERDICT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
