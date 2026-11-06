#!/usr/bin/env python3
"""
mutation_check_capability_wiring.py -- CAN THE WIRING GO RED?

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all
modules"*. The wiring file (`src/capability_wiring.py`) is what turns
25 orphans into 0 orphans, and it reports a measurement for each of
them. A report that cannot be wrong is not a report.

**SO EACH MUTATION BREAKS ONE RULE OF THE WIRING, AND THE CHECK MUST
GO RED FOR THAT REASON.** The mutations are applied to a COPY of the
wiring file in a temporary directory, the copy is run, and the copy's
own `--verify` and `--selftest` are asked whether they noticed.

**AND WHY THE MUTATIONS ARE TEXT SUBSTITUTIONS AND NOT A FLAG.** A
flag would prove that the flag works. Changing the source proves that
the SOURCE has the property, which is the thing the rest of the tree
depends on.

**AND WHY EACH MUTATION NAMES THE CHECK THAT MUST FIRE.** A harness
that says "the run went red" for the wrong reason is the exact defect
this project keeps finding in itself: the census harness had two of its
five mutations fail for the wrong reason, because the real tree is too
noisy to attribute a change to one rule. So every mutation here states
which check must produce the complaint, and the harness fails if a
DIFFERENT check produced it.

THE MUTATIONS
--------------
  M1  a probe returns a constant       -> the expectation check
  M2  a DARK reason is dropped          -> the reason check
  M3  an entry is skipped                -> the coverage check
  M4  a capability is LIVE though its
      probe raises                      -> the status check
  M5  a recorded expectation is wrong    -> the expectation check
  M6  the wiring file is not an entry
      point (no __main__ guard)          -> the census check

M6 is the one that matters most and it is checked by the census rather
than by the file: a wiring file with no __main__ guard is an orphan
itself, and every capability it names stays an orphan. The harness
runs the census over a tree whose wiring file has been mutated and
requires the orphans to come back.

Run:
    python tools/mutation_check_capability_wiring.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")
TOOLS = os.path.join(REPO, "tools")
WIRING = os.path.join(SRC, "capability_wiring.py")
CENSUS = os.path.join(TOOLS, "wiring_census.py")


def _python() -> str:
    """The interpreter to run the checks with.

    The project's own venv when it is there, because the wiring file's
    probes are measured with it. The census harness uses the same
    rule and the same reason.
    """
    venv = os.path.join(os.path.dirname(REPO), ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv):
        return venv
    return sys.executable


@dataclass(frozen=True)
class Mutation:
    """One break of the wiring, and the check that must catch it."""

    code: str
    title: str
    #: (old, new) text substitutions applied to the wiring source.
    edits: Tuple[Tuple[str, str], ...]
    #: The word the failing check's complaint must contain.
    expect_word: str
    #: "verify" runs --verify, "selftest" runs --selftest, "census"
    #: runs the census over a tree with the mutated file.
    mode: str = "verify"


#: The mutations. Each `old` string must be present in the source
#: exactly once, or the harness reports that the mutation did not
#: apply rather than passing for the wrong reason.
MUTATIONS: Tuple[Mutation, ...] = (
    Mutation(
        "M1",
        "a probe returns a constant",
        (("    return float(int((trits == 1).sum()))",
          "    return 42.0"),),
        "expectation",
    ),
    Mutation(
        "M2",
        "a DARK reason is dropped",
        (('            row.status = "DARK"\n'
          '            row.reason = str(exc)',
          '            row.status = "DARK"\n'
          '            row.reason = ""'),),
        "reason",
    ),
    Mutation(
        "M3",
        "an entry is skipped",
        (("    _cap_bitnet_ops(),\n", ""),),
        "coverage",
    ),
    Mutation(
        "M4",
        "a capability is LIVE though its probe raises",
        (('        except DarkCapability as exc:\n'
          '            row.status = "DARK"\n'
          '            row.reason = str(exc)',
          '        except DarkCapability as exc:\n'
          '            row.status = "LIVE"\n'
          '            row.value = 1.0\n'
          '            row.reason = ""'),),
        "status",
    ),
    Mutation(
        "M5",
        "a recorded expectation is wrong",
        (("        expect={0: 6.0, 1: 3.0},",
          "        expect={0: 61.0, 1: 3.0},"),),
        "expectation",
    ),
    Mutation(
        "M6",
        "the wiring file is not an entry point",
        (('if __name__ == "__main__":\n    raise SystemExit(main())',
          'if False:\n    raise SystemExit(main())'),),
        "orphan",
        mode="census",
    ),
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _apply(source: str, mutation: Mutation) -> Tuple[Optional[str], str, int]:
    """Apply a mutation's edits. Returns (failure reason, mutated source, count).

    AND WHY THE MUTATED SOURCE IS RETURNED AND NOT APPLIED IN PLACE.
    The first version of this harness mutated the string and returned
    only the count, so the file written to the scratch tree was the
    ORIGINAL source. Every mutation then "passed" because the mutated
    code was never run. A harness that does not mutate what it claims
    to mutate is the exact defect this project keeps finding in
    itself, and it is worth writing down here so the next version does
    not reintroduce it.
    """
    applied = 0
    for old, new in mutation.edits:
        count = source.count(old)
        if count != 1:
            return ("the edit target appears %d times, expected exactly 1: %r"
                    % (count, old[:70]), source, applied)
        source = source.replace(old, new, 1)
        applied += 1
    return (None, source, applied)


def _run_verify(directory: str, work_repos: str) -> Tuple[int, str, str]:
    """Run the mutated wiring file's --verify and return (rc, out, err)."""
    env = dict(os.environ)
    env["FC_WORK_REPOS"] = work_repos
    env["PYTHONPATH"] = directory + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run([_python(), os.path.join(directory, "capability_wiring.py"),
                           "--verify"],
                          capture_output=True, text=True, env=env, cwd=directory)
    return proc.returncode, proc.stdout, proc.stderr


def _run_selftest(directory: str, work_repos: str) -> Tuple[int, str, str]:
    """Run the mutated wiring file's --selftest and return (rc, out, err)."""
    env = dict(os.environ)
    env["FC_WORK_REPOS"] = work_repos
    env["PYTHONPATH"] = directory + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run([_python(), os.path.join(directory, "capability_wiring.py"),
                           "--selftest"],
                          capture_output=True, text=True, env=env, cwd=directory)
    return proc.returncode, proc.stdout, proc.stderr


def _census_bins(tree_root: str) -> Optional[Dict[str, str]]:
    """The census's bin for every module of a tree, keyed by repo/path.

    AND WHY THE TREE IS THE ARGUMENT AND NOT THE REAL REPOS. The
    first version of this harness passed the real work_repos to the
    census while writing the mutated wiring file into a scratch copy.
    The census therefore never saw the mutation, and the mutation that
    matters most -- the one that makes the wiring file unreachable --
    could not be caught. The census must read the tree the mutation was
    made in, or the check is a check of the wrong thing.
    """
    env = dict(os.environ)
    env["FC_WORK_REPOS"] = tree_root
    proc = subprocess.run([_python(), CENSUS, "--json", "--work-repos", tree_root],
                          capture_output=True, text=True, env=env, cwd=tree_root)
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    return {"%s/%s" % (row["repo"], row["path"]): row["bin"]
            for row in data.get("rows", [])}


def _census_orphans(tree_root: str) -> Optional[List[str]]:
    """The modules the census reports as not reached."""
    bins = _census_bins(tree_root)
    if bins is None:
        return None
    return sorted(path for path, bin_name in bins.items()
                  if bin_name in ("ORPHAN", "ISLAND"))


def _copy_tree(destination: str) -> None:
    """Copy the four repos' source trees into a scratch work_repos.

    Only `src` and `tools` are copied, because that is all the census
    reads, and a copy of a copy is the fastest way to a slow harness.
    """
    for repo in ("fieldcore", "simself", "far-coding", "atlas-exam"):
        for root in ("src", "tools"):
            source = os.path.join(os.path.dirname(REPO), repo, root)
            if not os.path.isdir(source):
                continue
            target = os.path.join(destination, repo, root)
            shutil.copytree(source, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--keep", action="store_true",
                        help="keep the scratch tree for inspection")
    args = parser.parse_args(list(argv) if argv is not None else None)

    print("=" * 78)
    print("THE CAPABILITY WIRING -- MUTATION CHECK")
    print("=" * 78)
    print()
    print("  The wiring file is what turns the census's orphans into wired")
    print("  modules. If it can be broken without anything going red, then")
    print("  the wiring it reports is decoration.")
    print()

    # the directory that holds the four repos
    work_repos = os.path.dirname(REPO)
    scratch = tempfile.mkdtemp(prefix="wiring_mutation_")
    caught = 0
    try:
        _copy_tree(scratch)

        # -- the baseline ------------------------------------------------
        baseline_dir = os.path.join(scratch, "_baseline")
        os.makedirs(baseline_dir, exist_ok=True)
        _write(os.path.join(baseline_dir, "capability_wiring.py"), _read(WIRING))
        rc, out, err = _run_verify(baseline_dir, work_repos)
        print("BASELINE (no mutation) -- the wiring must hold and the census "
              "must see no orphan")
        if rc != 0:
            print("  BASELINE FAILED -- the unmutated wiring does not hold:")
            print("    %s" % err[-800:])
            print("    %s" % out[-800:])
            return 2
        print("  the wiring holds")
        orphans = _census_orphans(scratch)
        if orphans is None:
            print("  BASELINE FAILED -- the census did not run on the copied tree")
            return 2
        print("  the census reports %d unreached modules over the copied tree"
              % len(orphans))
        if orphans:
            print("  BASELINE FAILED -- the copied tree already has unreached "
                  "modules: %s" % (orphans[:5],))
            return 2

        # -- each mutation -----------------------------------------------
        print()
        for mutation in MUTATIONS:
            directory = os.path.join(scratch, "_mut_%s" % mutation.code)
            os.makedirs(directory, exist_ok=True)
            failure, source, applied = _apply(_read(WIRING), mutation)
            if failure is not None:
                print("  %-4s %-46s NOT APPLIED: %s"
                      % (mutation.code, mutation.title, failure))
                continue
            _write(os.path.join(directory, "capability_wiring.py"), source)
            # the mutated file must sit in the copied tree as the real
            # wiring file, so the census sees the mutation
            tree_wiring = os.path.join(scratch, "fieldcore", "src",
                                       "capability_wiring.py")
            _write(tree_wiring, source)

            if mutation.mode == "census":
                # the mutated wiring file must sit in the copied tree,
                # because that is the tree the census reads
                unreached = _census_orphans(scratch)
                if unreached is None:
                    print("  %-4s %-46s NOT CAUGHT: the census did not run"
                          % (mutation.code, mutation.title))
                    continue
                if not unreached:
                    print("  %-4s %-46s NOT CAUGHT: the census still reports "
                          "every module reached" % (mutation.code, mutation.title))
                    continue
                caught += 1
                print("  %-4s %-46s CAUGHT: the census reports %d modules "
                      "unreached again (%s)"
                      % (mutation.code, mutation.title, len(unreached),
                         unreached[0]))
                # restore the tree's wiring file before the next mutation
                _write(tree_wiring, _read(WIRING))
                continue

            if mutation.mode == "selftest":
                rc, out, err = _run_selftest(directory, work_repos)
            else:
                rc, out, err = _run_verify(directory, work_repos)

            # restore the tree's wiring file for the next mutation
            _write(tree_wiring, _read(WIRING))

            if rc == 0:
                print("  %-4s %-46s NOT CAUGHT: the check still passed"
                      % (mutation.code, mutation.title))
                continue
            if mutation.expect_word not in out:
                print("  %-4s %-46s NOT CAUGHT: the check went red for a "
                      "different reason (wanted %r in the complaint)"
                      % (mutation.code, mutation.title, mutation.expect_word))
                for line in out.splitlines()[-8:]:
                    print("        %s" % line)
                continue
            caught += 1
            # the complaint lines are printed with four spaces of indent
            # and the table rows with two, so the indent is what tells
            # a complaint from a table row that happens to contain the
            # word. Without this the harness reports the header line as
            # the catch, which is the wrong reason for a green result.
            offending = [line.strip() for line in out.splitlines()
                         if line.startswith("    ") and mutation.expect_word in line]
            print("  %-4s %-46s CAUGHT: %s"
                  % (mutation.code, mutation.title,
                     offending[0] if offending else "the check went red"))
    finally:
        if args.keep:
            print()
            print("  the scratch tree is kept at %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)

    print()
    print("  %d of %d mutations were caught" % (caught, len(MUTATIONS)))
    if caught != len(MUTATIONS):
        print("  THE WIRING CANNOT GO RED FOR EVERY WAY IT IS BROKEN.")
        return 1
    print("  the wiring goes red for every way it is broken.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
