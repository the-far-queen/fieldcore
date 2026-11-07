#!/usr/bin/env python3
"""
tools/mutation_check_gate_staleness.py -- prove the staleness checks can FAIL.

THE RULE, and it is the project's own: a test that cannot fail is not a
test. So each mutation below removes ONE mechanism from the staleness
checker, and each must turn at least one check RED.

THE MUTATIONS:

  M1  the record is dropped            -> a checker with no record
  M2  the fingerprint ignores mtime    -> a moved file does not move the hash
  M3  the diff is empty                -> a stale report names no file
  M4  the throttle is removed          -> the check runs on every call
  M5  the import-time record is not used -> a checker has nothing to compare

A mutation that stays GREEN is a mutation too weak to catch the
defect, and the check it targets is not a check.

Run:  python tools/mutation_check_gate_staleness.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
TARGET = REPO / "src" / "gate_staleness.py"
TEST = "tests/test_gate_staleness.py"

#: Where the mutation work goes. The hermes home's scratch dir, which
#: is pruned on a 24h idle -- so the work dir is removed in the
#: `finally` block and never left behind.
SCRATCH = pathlib.Path(os.path.expanduser("~")) / "AppData" / "Local" \
    / "hermes" / "cache" / "scratch"


def m1_drop_the_record(src: str) -> str:
    """The checker keeps no record, so nothing can be compared."""
    old = """        self._built: Optional[Snapshot] = (
            built if built is not None else import_snapshot())"""
    new = """        self._built: Optional[Snapshot] = None"""
    if old not in src:
        raise SystemExit("mutation 1: the record assignment is not in the file")
    return src.replace(old, new)


def m2_ignore_the_mtime(src: str) -> str:
    """The fingerprint hashes the name and the size, not the mtime.

    AND WHY THIS IS THE RIGHT MUTATION. It is the mechanism that
    detects a changed file, so removing it makes the checker blind to
    every change that does not change a file's size."""
    old = """        h.update(os.path.basename(path).encode("utf-8"))
        h.update(str(mtime_ns).encode("ascii"))
        h.update(str(size).encode("ascii"))"""
    new = """        h.update(os.path.basename(path).encode("utf-8"))
        h.update(str(size).encode("ascii"))"""
    if old not in src:
        raise SystemExit("mutation 2: the fingerprint body is not in the file")
    return src.replace(old, new)


def m3_empty_the_diff(src: str) -> str:
    """A stale report names no file."""
    old = """    moved: List[str] = []
    for path in sorted(set(old) | set(new)):
        if old.get(path) != new.get(path):
            moved.append(path)
    return moved"""
    new = """    moved: List[str] = []
    return moved"""
    if old not in src:
        raise SystemExit("mutation 3: the diff body is not in the file")
    return src.replace(old, new)


def m4_remove_the_throttle(src: str) -> str:
    """The check runs on every call."""
    old = """        if (not force and self._has_checked
                and (now - self._last_check) < self.interval):
            return self._last_result"""
    new = """        if False:
            return self._last_result"""
    if old not in src:
        raise SystemExit("mutation 4: the throttle is not in the file")
    return src.replace(old, new)


def m5_ignore_the_import_record(src: str) -> str:
    """A checker has no record to compare against."""
    old = """        self._built: Optional[Snapshot] = (
            built if built is not None else import_snapshot())"""
    new = """        self._built: Optional[Snapshot] = (
            built if built is not None else {})"""
    if old not in src:
        raise SystemExit("mutation 5: the record assignment is not in the file")
    return src.replace(old, new)


MUTATIONS = [
    ("M1  the record is dropped", m1_drop_the_record),
    ("M2  the fingerprint ignores the mtime", m2_ignore_the_mtime),
    ("M3  the diff is empty", m3_empty_the_diff),
    ("M4  the throttle is removed", m4_remove_the_throttle),
    ("M5  the import-time record is ignored", m5_ignore_the_import_record),
]


def run_tests(workdir: pathlib.Path) -> tuple:
    argv = [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
            "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(argv, cwd=str(workdir), capture_output=True,
                              text=True, errors="replace", timeout=300)
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    original = src
    # AND THE MTIME IS RECORDED, because the bytes are not the only
    # thing the gate watches. MEASURED 2026-11-07: `gate_staleness.py`
    # fingerprints the mtime of every rule file, so a tool that writes
    # a real source file and restores its BYTES leaves the tree looking
    # changed -- and the gate says STALE and names the file. **THE GATE
    # WAS RIGHT.** See `tools/mutation_restore.py`.
    _orig_stat = TARGET.stat()
    print("MUTATION CHECK  the gate's staleness detector")
    print("-" * 72)

    def run_in_place():
        """Run the checks against the REAL tree.

        AND WHY IN PLACE AND NOT IN A COPY. The staleness module
        resolves its rule directories RELATIVE TO ITS OWN FILE, so a
        copy in a temp dir would look for the rules somewhere that does
        not exist, and every check would fail for the wrong reason --
        the baseline RED and the mutations RED for reasons that have
        nothing to do with the mutation. So the file is mutated in
        place, the checks are run against the real tree, and the
        original is restored in the `finally` block.

        AND THE RESTORE IS NOT OPTIONAL. A failed run that leaves a
        mutated file in the tree is a worse failure than a red
        baseline.
        """
        return run_tests(REPO)

    try:
        # the unmutated tree must be GREEN
        rc, out = run_in_place()
        base = "GREEN" if rc == 0 else "RED"
        print("baseline (no mutation)                    %s  rc=%d" % (base, rc))
        if rc != 0:
            print(out[-2500:])
            print("-" * 72)
            print("the baseline is RED: the checks do not pass on the "
                  "unmutated tree, so they prove nothing")
            return 1

        all_red = True
        for name, fn in MUTATIONS:
            try:
                mutated = fn(src)
            except SystemExit as exc:
                print("%-52s SKIP (%s)" % (name, exc))
                all_red = False
                continue
            TARGET.write_text(mutated, encoding="utf-8")
            rc, out = run_in_place()
            state = "RED" if rc != 0 else "GREEN"
            failed = re.findall(r"^FAILED (\S+)", out, re.M)
            print("%-52s %s  rc=%d  %s"
                  % (name, state, rc, ", ".join(failed[:4])))
            if state == "GREEN":
                all_red = False
                print("    ^^ this mutation stayed GREEN: the checks it "
                      "targets do not catch it")
            TARGET.write_text(original, encoding="utf-8")
            os.utime(TARGET,
                     ns=(_orig_stat.st_atime_ns, _orig_stat.st_mtime_ns))

        print("-" * 72)
        print("every mutation went RED" if all_red
              else "AT LEAST ONE MUTATION STAYED GREEN")
        return 0 if all_red else 1
    finally:
        TARGET.write_text(original, encoding="utf-8")
        # AND THE MTIME GOES BACK TO WHERE IT WAS.
        os.utime(TARGET, ns=(_orig_stat.st_atime_ns, _orig_stat.st_mtime_ns))


if __name__ == "__main__":
    sys.exit(main())
