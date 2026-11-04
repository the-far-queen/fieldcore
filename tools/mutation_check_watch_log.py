#!/usr/bin/env python3
"""
tools/mutation_check_watch_log.py -- prove the python watcher's checks
can FAIL.

THE RULE, and it is the project's own (CENTRAL-RULES rule 7): a test
that cannot fail is not a test. So each mutation below removes ONE
mechanism from the watcher or its observer, and each must turn at
least one check RED.

THE MUTATIONS:
  M1  the observer stops recomputing the digest
      -> a doctored entry must no longer be caught
  M2  the observer stops checking the link
      -> a broken chain must no longer be caught
  M3  an absent chain reads as healthy
      -> absence must no longer be caught
  M4  the observer ignores the ANCHOR
      -> a rewrite whose digests were recomputed must no longer be caught
  M5  the watcher stops checking the ORDER
      -> a swapped order must no longer be caught
  M6  the watcher stops re-deriving the gate's verdict
      -> a gate that changes its mind must no longer be caught

AND THE HARNESS, and the two parts that are easy to get wrong:

  * THE BASELINE MUST BE GREEN FIRST. A mutation run against a RED
    baseline proves nothing.
  * THE MUTATION MUST APPLY. Each mutation RAISES if its anchor text
    is not in the file, because a mutation that silently does nothing
    reports "the check survived" -- which reads like a result and is
    not one.
  * THE FILE IS RESTORED IN A FINALLY BLOCK.

Run:  python tools/mutation_check_watch_log.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
WATCH = REPO / "src" / "watch_log.py"
TEST = "tests/test_watch_log.py"


def m1_the_observer_stops_recomputing_the_digest(src: str) -> str:
    old = """        recomputed = e.recomputed_digest()
        if recomputed != e.digest:"""
    new = """        recomputed = e.digest
        if False:"""
    if old not in src:
        raise SystemExit("mutation 1: the digest re-derivation is not in the file")
    return src.replace(old, new)


def m2_the_observer_stops_checking_the_link(src: str) -> str:
    old = """        if e.prev != prev:"""
    new = """        if False:"""
    if old not in src:
        raise SystemExit("mutation 2: the link check is not in the file")
    return src.replace(old, new)


def m3_absent_is_treated_as_healthy(src: str) -> str:
    old = """        return Observation(
            verdict="absent", checked=0, broke_at=None,
            reason="no_watch_log: the watcher wrote nothing, and an "
                   "absent watcher is not a healthy one")"""
    new = """        return Observation(
            verdict="consistent", checked=0, broke_at=None,
            reason="no_watch_log")"""
    if old not in src:
        raise SystemExit("mutation 3: the absent branch is not in the file")
    return src.replace(old, new)


def m4_the_observer_ignores_the_anchor(src: str) -> str:
    old = """    if anchor is not None:
        head = chain.entries[-1].digest"""
    new = """    if False:
        head = chain.entries[-1].digest"""
    if old not in src:
        raise SystemExit("mutation 4: the anchor branch is not in the file")
    return src.replace(old, new)


def m5_the_watcher_stops_checking_the_order(src: str) -> str:
    old = """        if seen == expected:
            return self.chain.push("order", "exchange", "order_ok",
                                   "the exchange ran in the project's order")"""
    new = """        if True:
            return self.chain.push("order", "exchange", "order_ok",
                                   "the exchange ran in the project's order")"""
    if old not in src:
        raise SystemExit("mutation 5: the order check is not in the file")
    return src.replace(old, new)


def m6_the_watcher_stops_rederiving_the_gate(src: str) -> str:
    old = """        if second_allowed == first_allowed:
            return self.chain.push(
                "gate", "answer", "gate_stable","""
    new = """        if True:
            return self.chain.push(
                "gate", "answer", "gate_stable","""
    if old not in src:
        raise SystemExit("mutation 6: the gate re-derivation is not in the file")
    return src.replace(old, new)


MUTATIONS = [
    ("M1  the observer stops recomputing the digest",
     m1_the_observer_stops_recomputing_the_digest),
    ("M2  the observer stops checking the link",
     m2_the_observer_stops_checking_the_link),
    ("M3  an absent chain reads as healthy",
     m3_absent_is_treated_as_healthy),
    ("M4  the observer ignores the anchor",
     m4_the_observer_ignores_the_anchor),
    ("M5  the watcher stops checking the order",
     m5_the_watcher_stops_checking_the_order),
    ("M6  the watcher stops re-deriving the gate's verdict",
     m6_the_watcher_stops_rederiving_the_gate),
]


def run_tests() -> tuple:
    argv = [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
            "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(argv, cwd=str(REPO), capture_output=True,
                              text=True, errors="replace", timeout=300)
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    original = WATCH.read_text(encoding="utf-8")
    print("MUTATION CHECK  the python watcher and its observer")
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
            failed = re.findall(r"^FAILED (\S+)", out, re.M)
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


if __name__ == "__main__":
    sys.exit(main())
