#!/usr/bin/env python3
"""
tools/mutation_check_watch.py -- prove the Rust watcher's checks can FAIL.

THE RULE, and it is the project's own (CENTRAL-RULES rule 7): a test
that cannot fail is not a test. So each mutation below removes ONE
mechanism from the watcher/observer, and each must turn at least one
Rust check RED.

THE MUTATIONS:
  M1  the watcher stops re-deriving the WIDTH
      -> a forged width must no longer be caught
  M2  the observer stops recomputing the digest
      -> a doctored entry must no longer be caught
  M3  the observer stops checking the LINK
      -> a broken chain must no longer be caught
  M4  the observer treats an ABSENT chain as healthy
      -> absence must no longer be caught
  M5  the observer ignores the ANCHOR
      -> a rewrite whose digests were recomputed must no longer be caught

AND THE HARNESS ITSELF, which is the part that is easy to get wrong:

  * THE BASELINE MUST BE GREEN FIRST. A mutation run against a RED
    baseline proves nothing, so the harness asserts the baseline before
    it mutates anything.
  * THE MUTATION MUST APPLY. Each mutation RAISES if its anchor text
    is not in the file, because a mutation that silently does nothing
    reports "the check survived" -- which reads like a result and is
    not one.
  * THE FILE IS RESTORED IN A FINALLY BLOCK, so a mutation that
    crashes the harness cannot leave the tree mutated.

Run:  python tools/mutation_check_watch.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
CORE = REPO / "core"
WATCH = CORE / "src" / "watch.rs"


def m1_the_watcher_stops_rederiving_the_width(src: str) -> str:
    """The width re-derivation is removed from the watcher."""
    old = """        if reading.width != recomputed_width {
            problems.push(format!(
                "width_not_derived: the reading says {} and the channel derives {}",
                reading.width, recomputed_width
            ));
        }"""
    new = """        let _ = recomputed_width;"""
    if old not in src:
        raise SystemExit("mutation 1: the width check is not in the file")
    return src.replace(old, new)


def m2_the_observer_stops_recomputing_the_digest(src: str) -> str:
    """The digest re-derivation is removed from the observer."""
    old = """        let recomputed = e.recomputed_digest();
        if recomputed != e.digest {"""
    new = """        let recomputed = e.digest.clone();
        if false {"""
    if old not in src:
        raise SystemExit("mutation 2: the digest re-derivation is not in the file")
    return src.replace(old, new)


def m3_the_observer_stops_checking_the_link(src: str) -> str:
    """The link check is removed from the observer."""
    old = """        if e.prev != prev_digest {"""
    new = """        if false {"""
    if old not in src:
        raise SystemExit("mutation 3: the link check is not in the file")
    return src.replace(old, new)


def m4_absent_is_treated_as_healthy(src: str) -> str:
    """An absent chain reads as consistent."""
    old = """        return Observation {
            verdict: ObservationVerdict::Absent,
            checked: 0,
            broke_at: None,
            reason: "no_watch_log: the watcher has written nothing, and an \\
                     absent watcher is not a healthy one"
                .to_string(),
        };"""
    new = """        return Observation {
            verdict: ObservationVerdict::Consistent,
            checked: 0,
            broke_at: None,
            reason: "no_watch_log".to_string(),
        };"""
    if old not in src:
        raise SystemExit("mutation 4: the absent branch is not in the file")
    return src.replace(old, new)


def m5_the_observer_ignores_the_anchor(src: str) -> str:
    """The second witness is not consulted."""
    old = """    if let Some(a) = anchor {
        let head = chain.entries.last().map(|e| e.digest.clone()).unwrap_or_default();"""
    new = """    if let Some(_a) = anchor {
        let head = chain.entries.last().map(|e| e.digest.clone()).unwrap_or_default();
        if false {"""
    if old not in src:
        raise SystemExit("mutation 5: the anchor branch is not in the file")
    return src.replace(old, new)


MUTATIONS = [
    ("M1  the watcher stops re-deriving the width",
     m1_the_watcher_stops_rederiving_the_width),
    ("M2  the observer stops recomputing the digest",
     m2_the_observer_stops_recomputing_the_digest),
    ("M3  the observer stops checking the link",
     m3_the_observer_stops_checking_the_link),
    ("M4  an absent chain reads as healthy",
     m4_absent_is_treated_as_healthy),
    ("M5  the observer ignores the anchor",
     m5_the_observer_ignores_the_anchor),
]


def run_tests() -> tuple:
    argv = ["cargo", "test", "--release", "--test", "watch"]
    try:
        proc = subprocess.run(argv, cwd=str(CORE), capture_output=True,
                              text=True, errors="replace", timeout=600)
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    original = WATCH.read_text(encoding="utf-8")
    backup = CORE / "src" / "watch.rs.orig"
    shutil.copy2(WATCH, backup)
    print("MUTATION CHECK  the rust watcher and its observer")
    print("-" * 72)

    try:
        rc, out = run_tests()
        base = "GREEN" if rc == 0 else "RED"
        print("baseline (no mutation)                    %s  rc=%d" % (base, rc))
        if rc != 0:
            print(out[-3000:])
            print("-" * 72)
            print("the baseline is RED: the checks do not pass on the "
                  "unmutated tree, so they prove nothing")
            return 1

        all_red = True
        for name, fn in MUTATIONS:
            try:
                mutated = fn(original)
            except SystemExit as exc:
                print("%-52s SKIP (%s)" % (name, exc))
                all_red = False
                continue
            WATCH.write_text(mutated, encoding="utf-8")
            rc, out = run_tests()
            state = "RED" if rc != 0 else "GREEN"
            failed = re.findall(r"^test (\S+) \.\.\. FAILED", out, re.M)
            print("%-52s %s  rc=%d  %s"
                  % (name, state, rc, ", ".join(failed[:2])))
            if state == "GREEN":
                all_red = False
                print("    ^^ this mutation stayed GREEN: the checks it "
                      "targets do not catch it")
            WATCH.write_text(original, encoding="utf-8")

        print("-" * 72)
        print("every mutation went RED" if all_red
              else "AT LEAST ONE MUTATION STAYED GREEN")
        return 0 if all_red else 1
    finally:
        WATCH.write_text(original, encoding="utf-8")
        if backup.exists():
            backup.unlink()


if __name__ == "__main__":
    sys.exit(main())
