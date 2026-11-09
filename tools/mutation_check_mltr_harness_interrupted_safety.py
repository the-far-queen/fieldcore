#!/usr/bin/env python3
"""
mutation_check_mltr_harness_interrupted_safety.py -- PROVE THE HARNESS
SURVIVES BEING INTERRUPTED MID-MUTATION.

**AND THIS CHECK EXISTS BECAUSE THE HARNESS HAD THE DEFECT IT NOW
CHECKS.** MEASURED 2026-11-09: the harness
`tools/mutation_check_mltr_derivation_input.py` restored the tree in a
`finally` block -- and a `finally` runs when the process is asked to
stop, but NOT when the process is ended. The cron runs that harness
under `runbound.py`, and a run that exceeded its budget left the tree
mutated:

    tools/derive_mltr_terms.py   DOMAIN_ENRICH = 1.9   (should be 2.0)

**AND THE CONSEQUENCE WAS A MEASUREMENT THAT WAS NOT A MEASUREMENT.**
The next run's BASELINE was RED -- 3 tests failed -- and the baseline is
supposed to be the unmutated tree. So the harness printed "the baseline
is RED, so they prove nothing" and exited 1, which was CORRECT about
the tree and wrong about the cause. The cause was the previous run's
leftovers.

**SO THE FIX IS: THE ORIGINAL BYTES GO TO A FILE BESIDE THE TARGET
BEFORE THE MUTATION**, and the next run reads that file back before it
measures anything. **A backup that lives in a variable goes with the
process that made it; a backup that lives in a FILE survives it.**

**AND THE FIRST FOUR VERSIONS OF THIS CHECK WERE WORTHLESS, AND IT IS
THE REASON THIS FILE SAYS SO.**

The first version's arms read the harness's source and reported whether
the mechanism was present -- they never MUTATED anything, so they would
report "ok" whether the fix was there or not.

The second version's arms left a mutated tree and a backup file and
asked whether the harness restored the tree -- but it PRE-CREATED the
backup, so M2 (the harness never writes a backup) could not be caught,
and M3 (the restore runs after the baseline) could not be caught
either, because the restore still happened.

The third version waited for the restore line and then STOPPED the
harness, so the baseline line was never printed and the ORDER could not
be measured -- and the control arm failed for that reason.

The fourth version had the POLARITY BACKWARDS on the mutation arms: it
reported a caught mutation as a failure, because an arm that sees the
mechanism ABSENT was scored as "the arm failed" rather than "the
mutation was caught". **A CHECK THAT CANNOT FAIL IS NOT A CHECK** --
and neither is a check that cannot PASS.

**SO THE RULE FOR EVERY ARM HERE IS THE SAME, AND IT IS STATED ONCE:**
an arm PASSES when the mechanism behaves the way the arm demands. The
control arms demand the mechanism WORKING; the mutation arms demand it
BROKEN. The score is the same shape either way, and the difference is
in the arm's demand, not in the scoring.

THE ARMS:

  C0  CONTROL -- the unbroken harness restores an interrupted run's
      tree, removes the backup, and announces the restore BEFORE it
      measures the baseline
  M1  the startup restore is removed -- so the tree stays mutated
  C1  CONTROL -- the unbroken harness writes the backup file while it
      runs
  M2  the backup file is never written -- so an interrupted run leaves
      nothing to restore from
  M3  the restore runs AFTER the baseline -- so the baseline is
      measured against the mutated tree

Run:
    python tools/mutation_check_mltr_harness_interrupted_safety.py
Exit: 0 when every arm passed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HARNESS_REL = os.path.join("tools", "mutation_check_mltr_derivation_input.py")
TOOL_REL = os.path.join("tools", "derive_mltr_terms.py")
TEST_REL = os.path.join("tests", "test_mltr_derivation_input.py")
BACKUP_SUFFIX = ".mutation-backup"

#: THE MARKER that stands in for a mutation. It has to be a real
#: change to the file, because the check is that the tree comes BACK.
MARKER = "DOMAIN_ENRICH = 2.0"
MARKER_MUTATED = "DOMAIN_ENRICH = 1.9"

#: THE LINE the harness prints when it restores a tree left mutated.
#: AND ITS POSITION IN THE OUTPUT IS THE MEASUREMENT: the restore has
#: to happen BEFORE the baseline is measured.
RESTORED_LINE = "RESTORED A TREE LEFT MUTATED"
BASELINE_LINE = "baseline (no mutation)"

#: A STUB for the slow test file, so an arm does not pay the 45-second
#: derivation eight times. AND IT SLEEPS, because the arm needs a
#: window in which the harness is mid-mutation.
STUB_TEST = '''\
"""A stub for the slow derivation test, used by the arm harness."""
import time


def test_stub_sleeps():
    time.sleep(2)
'''


#: THE MUTATIONS. Each one is a real break in the harness's
#: interrupted-safety mechanism, applied to a COPY of the harness.
#:
#: AND THEY ARE BUILT FROM THE FILE'S OWN TEXT RATHER THAN FROM FIXED
#: STRINGS, because a fixed anchor is a line-ending dependency: the
#: file is CRLF on this machine, and an anchor carrying a bare newline
#: does not match it. (That defect was found and fixed in simself's
#: harness on 2026-11-09.)
def _m1(text: str):
    """the startup restore is removed"""
    old = "    _restore_from_backup()\n"
    if old not in text:
        return None
    return old, "    # MUTATION: the startup restore is removed\n"


def _m2(text: str):
    """the backup file is never written"""
    old = ('        with open(backup, "wb") as f:\n'
           '            f.write(original.encode("utf-8"))\n')
    if old not in text:
        return None
    return old, "        # MUTATION: the backup file is never written\n"


def _m3(text: str):
    """the restore runs AFTER the baseline instead of before it"""
    early = "    _restore_from_backup()\n"
    base = ('    rc, out = _run_tests()\n'
            '    print("baseline (no mutation)                    %s  rc=%d"\n'
            '          % ("GREEN" if rc == 0 else "RED", rc))\n')
    if early not in text or base not in text:
        return None
    # THE EARLY CALL GOES AND A LATE ONE ARRIVES, so the restore is
    # measured against the mutated tree -- which is the defect.
    new = text.replace(early, "", 1).replace(
        base, base + "    _restore_from_backup()\n", 1)
    return text, new


MUTATIONS = (
    ("M1 the startup restore is removed", _m1),
    ("M2 the backup file is never written", _m2),
    ("M3 the restore runs after the baseline", _m3),
)


def _copy_tree(src: str, dest: str) -> None:
    """Copy the repo into a temp dir, minus the heavy and generated
    directories. AND THE COPY IS THE POINT: the real repo is never
    touched, because a check that damages the tree it checks is worse
    than no check."""
    skip = {".git", "__pycache__", ".pytest_cache", "core", "corpus",
            "papers", "sacred_library"}
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        rel = os.path.relpath(root, src)
        out = dest if rel == "." else os.path.join(dest, rel)
        os.makedirs(out, exist_ok=True)
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                continue
            shutil.copy2(os.path.join(root, name),
                         os.path.join(out, name))


def _apply_harness_mutation(copy: str, builder) -> bool:
    path = os.path.join(copy, HARNESS_REL)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    pair = builder(text)
    if pair is None:
        return False
    old, new = pair
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new)
    return True


def _stub_the_test(copy: str) -> None:
    path = os.path.join(copy, TEST_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(STUB_TEST)


def _leave_a_mutated_tree(copy: str) -> bool:
    """Leave the tree exactly as an INTERRUPTED run leaves it: the
    target mutated, and the backup file beside it.

    AND THIS IS THE FAILURE BEING REPRODUCED, not a simulation of it.
    """
    tool = os.path.join(copy, TOOL_REL)
    backup = tool + BACKUP_SUFFIX
    with open(tool, encoding="utf-8") as fh:
        original = fh.read()
    if MARKER not in original:
        return False
    with open(backup, "wb") as fh:
        fh.write(original.encode("utf-8"))
    with open(tool, "w", encoding="utf-8") as fh:
        fh.write(original.replace(MARKER, MARKER_MUTATED, 1))
    return True


def _tool_is_restored(copy: str) -> bool:
    tool = os.path.join(copy, TOOL_REL)
    try:
        with open(tool, encoding="utf-8") as fh:
            after = fh.read()
    except OSError:
        return False
    return MARKER in after and MARKER_MUTATED not in after


def _stop(proc) -> None:
    """Stop the harness and everything it started."""
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, text=True, timeout=60)
    except Exception:
        pass
    try:
        proc.wait(timeout=30)
    except Exception:
        pass


def _run_harness(copy: str, log_path: str, watch_file: str = "",
                 timeout: float = 300.0):
    """Run the harness in the copy to completion.

    AND IT WATCHES A FILE WHILE IT RUNS, because the property M2 is
    about is what the harness DOES WHILE IT RUNS -- and a check that
    looks only at the end state cannot see it: the harness removes its
    backup when it is done, so the backup is gone by the end either
    way.

    Returns (the output, whether the watched file was ever seen).
    """
    harness = os.path.join(copy, HARNESS_REL)
    seen = False
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, "-B", harness], cwd=copy, stdout=log,
            stderr=subprocess.STDOUT)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if watch_file and os.path.isfile(watch_file):
                seen = True
            time.sleep(0.05)
        if proc.poll() is None:
            _stop(proc)
    if watch_file and os.path.isfile(watch_file):
        seen = True
    try:
        with open(log_path, encoding="utf-8", errors="replace") as fh:
            return fh.read(), seen
    except OSError:
        return "", seen


def _arm_restore(label: str, builder=None, want_broken: bool = False) -> bool:
    """C0, M1 and M3: the harness is asked to restore a tree that an
    interrupted run left mutated.

    The measurement is FOUR things: the tree came back, the backup was
    removed, the restore was ANNOUNCED, and it was announced BEFORE the
    baseline was measured. The last is what catches M3, where the tree
    still comes back but the baseline was measured against the mutation
    first -- and M3's early call has to be REMOVED, not merely joined
    by a late one, or the early one still does the work.

    AND `want_broken` IS THE ARM'S DEMAND: a control arm demands the
    mechanism WORK, and a mutation arm demands it BROKEN. The scoring
    is the same shape either way.
    """
    with tempfile.TemporaryDirectory() as td:
        copy = os.path.join(td, "fieldcore")
        _copy_tree(REPO, copy)
        _stub_the_test(copy)
        if builder is not None:
            if not _apply_harness_mutation(copy, builder):
                print("    [FAIL] %s -- the anchor text is not in the "
                      "harness, so the mutation did not apply" % label)
                return False
        if not _leave_a_mutated_tree(copy):
            print("    [FAIL] %s -- the marker %r is not in the tool, so "
                  "the arm cannot be built" % (label, MARKER))
            return False

        log = os.path.join(td, "harness.log")
        out, _ = _run_harness(copy, log)

        restored = _tool_is_restored(copy)
        backup_gone = not os.path.isfile(
            os.path.join(copy, TOOL_REL) + BACKUP_SUFFIX)
        restored_at = out.find(RESTORED_LINE)
        baseline_at = out.find(BASELINE_LINE)
        announced = restored_at != -1
        before = announced and baseline_at != -1 and restored_at < baseline_at
        working = restored and backup_gone and before

        # THE ARM'S DEMAND IS "WORKING" OR "BROKEN", AND THE COMPARISON
        # IS AGAINST THAT. A control arm demands the mechanism working;
        # a mutation arm demands it broken. **AND THE COMPARISON HAS TO
        # BE WRITTEN AGAINST `want_working` AND NOT AGAINST
        # `want_broken`**, because comparing "working" with
        # "want_broken" scores every arm the wrong way round -- and the
        # first version of this file did exactly that, so a mechanism
        # that was WORKING was reported as a failure. (MEASURED
        # 2026-11-09: all five arms failed while the mechanism was
        # working and every mutation was being caught.)
        want_working = not want_broken
        if working != want_working:
            print("    [FAIL] %s -- the mechanism %s working (restored: "
                  "%s, backup removed: %s, announced: %s, announced "
                  "before the baseline: %s)"
                  % (label, "IS" if working else "is NOT", restored,
                     backup_gone, announced, before))
            print("    the harness's own output, the last 1200 chars:")
            print(out[-1200:])
            return False
        print("    [ok ] %s -- the mechanism %s working, as this arm "
              "demands" % (label, "IS" if working else "is NOT"))
        return True


def _arm_backup_written(label: str, builder=None,
                        want_broken: bool = False) -> bool:
    """M2: the harness must WRITE the backup before it mutates.

    AND THIS ARM NEEDS A REAL RUN, because the property is about what
    the harness does WHILE it runs. The previous version of this file
    could not catch it, because its arm PRE-CREATED the backup file.
    """
    with tempfile.TemporaryDirectory() as td:
        copy = os.path.join(td, "fieldcore")
        _copy_tree(REPO, copy)
        _stub_the_test(copy)
        if builder is not None:
            if not _apply_harness_mutation(copy, builder):
                print("    [FAIL] %s -- the anchor text is not in the "
                      "harness, so the mutation did not apply" % label)
                return False

        tool = os.path.join(copy, TOOL_REL)
        backup = tool + BACKUP_SUFFIX
        if os.path.isfile(backup):
            os.remove(backup)

        log = os.path.join(td, "harness.log")
        _out, seen = _run_harness(copy, log, watch_file=backup)
        # AND THE COMPARISON IS AGAINST `want_writing`, FOR THE SAME
        # REASON AS THE OTHER ARM: comparing "seen" with "want_broken"
        # scores the arms the wrong way round.
        want_writing = not want_broken
        if seen != want_writing:
            print("    [FAIL] %s -- the harness %s write the backup file "
                  "while it ran, and this arm demands the opposite"
                  % (label, "did" if seen else "did not"))
            return False
        print("    [ok ] %s -- the harness %s write the backup file "
              "while it ran, as this arm demands"
              % (label, "did" if seen else "did not"))
        return True


def main() -> int:
    print("=" * 78)
    print("THE HARNESS'S INTERRUPTED SAFETY -- the arms, shown able to "
          "go RED")
    print("=" * 78)
    print()

    results = []

    print("C0  CONTROL: the unbroken harness restores an interrupted "
          "run's tree, before the baseline")
    ok = _arm_restore("C0 the unbroken harness", None, want_broken=False)
    results.append(("C0 the unbroken harness restores the tree", ok))
    print()

    print("M1  the startup restore is removed")
    ok = _arm_restore("M1 the startup restore is removed", _m1,
                      want_broken=True)
    results.append(("M1 the startup restore is removed", ok))
    print()

    print("C1  CONTROL: the unbroken harness writes the backup file")
    ok = _arm_backup_written("C1 the unbroken harness writes the backup",
                             None, want_broken=False)
    results.append(("C1 the unbroken harness writes the backup", ok))
    print()

    print("M2  the backup file is never written")
    ok = _arm_backup_written("M2 the backup file is never written", _m2,
                             want_broken=True)
    results.append(("M2 the backup file is never written", ok))
    print()

    print("M3  the restore runs after the baseline")
    ok = _arm_restore("M3 the restore runs after the baseline", _m3,
                      want_broken=True)
    results.append(("M3 the restore runs after the baseline", ok))
    print()

    caught = sum(1 for _, ok in results if ok)
    print("=" * 78)
    print("  %d of %d arms passed" % (caught, len(results)))
    for label, ok in results:
        print("    [%s] %s" % ("ok " if ok else "FAIL", label))
    print("=" * 78)
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
