#!/usr/bin/env python3
"""
tools/mutation_check_property_fp.py -- prove the property-layer fix can FAIL.

THE RULE, and it is the project's own: a test that cannot fail is not a
test. So each mutation below removes ONE mechanism from the fix, and
each must turn at least one check RED.

THE DEFECT (found 2026-11-02): the property layer refused 85 of this
machine's own real replies (0.2430% of 34,981 spans). Three causes, and
each one has a mutation:

  M1  the anchor has no word boundaries   -> "gateway" matches "gate"
  M2  a quoted word is read as a claim    -> a citation is refused
  M3  the citation rule ignores predicate position
                                           -> quotes become a SHELTER
  M4  the inventory says the gate cannot be stale
                                           -> the truth is refused
  M5  the inventory says the gate cannot be advisory
                                           -> the truth is refused

A mutation that stays GREEN is a mutation too weak to catch the
defect, and the check it targets is not a check.

Run:  python tools/mutation_check_property_fp.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
TARGET = REPO / "src" / "property_layer.py"
TEST = "tests/test_property_layer_false_positives.py"


def m1_anchor_without_boundaries(src: str) -> str:
    """The anchor is matched as a bare substring, so 'gateway' contains
    'gate' -- the first defect, restored."""
    old = """    words = anchor.split()
    if not words:
        return False
    pat = r"(?<![a-z])" + r"\\s+".join(re.escape(w) for w in words) + r"(?![a-z])"
    return re.search(pat, low) is not None"""
    new = """    return anchor in low"""
    if old not in src:
        raise SystemExit("mutation 1: the anchor matcher is not in the file")
    return src.replace(old, new)


def m2_quotes_are_claims(src: str) -> str:
    """A quoted word is read as a claim -- the second defect, restored.

    The citation rule is made to return False always."""
    old = """        if _is_citation(span, prop, subject):
            continue"""
    new = """        if False and _is_citation(span, prop, subject):
            continue"""
    if old not in src:
        raise SystemExit("mutation 2: the citation call is not in the file")
    return src.replace(old, new)


def m3_quotes_are_a_shelter(src: str) -> str:
    """The citation rule ignores PREDICATE position, so the adversary
    adds quotes and is admitted."""
    old = """        if _PROPERTY_COPULA.search(before):
            # a linking verb right before it -- an assertion
            continue"""
    new = """        if False and _PROPERTY_COPULA.search(before):
            # a linking verb right before it -- an assertion
            continue"""
    if old not in src:
        raise SystemExit("mutation 3: the copula test is not in the file")
    src = src.replace(old, new)
    old2 = """                if not rest or _PROPERTY_DET.search(rest):
                    # the subject itself, then the word -- an assertion
                    in_predicate = True
                    break"""
    new2 = """                if False and (not rest or _PROPERTY_DET.search(rest)):
                    # the subject itself, then the word -- an assertion
                    in_predicate = True
                    break"""
    if old2 not in src:
        raise SystemExit("mutation 3b: the subject test is not in the file")
    return src.replace(old2, new2)


def m4_the_gate_cannot_be_stale(src: str) -> str:
    """The inventory claims the gate lacks 'stale' -- the third defect,
    restored."""
    old = """            "a stale snapshot", "hard-coded stale snapshot","""
    new = """            "a stale snapshot", "hard-coded stale snapshot",
            "stale","""
    if old not in src:
        raise SystemExit("mutation 4: the stale snapshot entry is not in the file")
    return src.replace(old, new)


def m5_the_gate_cannot_be_advisory(src: str) -> str:
    """The inventory claims the gate lacks 'advisory' -- restored."""
    old = """            "a parameter", "informational","""
    new = """            "a parameter", "advisory", "informational","""
    if old not in src:
        raise SystemExit("mutation 5: the advisory entry is not in the file")
    return src.replace(old, new)


MUTATIONS = [
    ("M1  the anchor has no word boundaries", m1_anchor_without_boundaries),
    ("M2  a quoted word is read as a claim", m2_quotes_are_claims),
    ("M3  quotes are a shelter", m3_quotes_are_a_shelter),
    ("M4  the gate cannot be stale", m4_the_gate_cannot_be_stale),
    ("M5  the gate cannot be advisory", m5_the_gate_cannot_be_advisory),
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
    src = TARGET.read_text(encoding="utf-8")
    original = src
    # AND THE MTIME IS RECORDED, because the bytes are not the only
    # thing the gate watches. MEASURED 2026-11-07: `gate_staleness.py`
    # fingerprints the mtime of every rule file, so a tool that writes
    # a real source file and restores its BYTES leaves the tree looking
    # changed -- and the gate says STALE and names the file. **THE GATE
    # WAS RIGHT.** See `tools/mutation_restore.py`.
    _orig_stat = TARGET.stat()
    print("MUTATION CHECK  the property layer's false positives")
    print("-" * 72)

    try:
        rc, out = run_tests()
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
            rc, out = run_tests()
            state = "RED" if rc != 0 else "GREEN"
            failed = re.findall(r"^FAILED (\S+)", out, re.M)
            print("%-52s %s  rc=%d  %s"
                  % (name, state, rc, ", ".join(failed[:3])))
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
