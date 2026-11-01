#!/usr/bin/env python3
"""
tools/mutation_check_measurement_coverage.py -- prove the two new checks
can FAIL.

THE RULE, and it is the project's own: a test that cannot fail is not a
test. So each mutation below removes ONE mechanism from the fix, and
each must turn at least one check RED.

THE TWO DEFECTS (found 2026-11-02):

  M1  the property layer's self-measurement loads two of four corpora
      -> the catch rate it reports is a number on the easy sets

  M2  one of the eight public claims has no predicate
      -> the structural layer cannot catch a denial of it

  M3  the goal-2 deny list is blunt ("admits every")
      -> an abstract argument about a hypothetical gate is refused

A mutation that stays GREEN is a mutation too weak to catch the
defect, and the check it targets is not a check.

Run:  python tools/mutation_check_measurement_coverage.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
REGISTRY = REPO / "src" / "predicate_registry.py"
PROPERTY = REPO / "src" / "property_layer.py"
TEST = "tests/test_measurement_coverage.py"


def m1_measurement_skips_the_unfitted_corpora(src: str) -> str:
    """The self-measurement loads two corpora instead of four."""
    old = """    CORPORA = (("BLIND", "held_out_adversarial.json"),
                ("INFORMED", "informed_adversarial.json"),
                ("V2 (14 REGISTERS)", "held_out_v2.json"),
                ("FRESH (BLIND WRITER)", "fresh_adversarial.json"))"""
    new = """    CORPORA = (("BLIND", "held_out_adversarial.json"),
                ("INFORMED", "informed_adversarial.json"))"""
    if old not in src:
        raise SystemExit("mutation 1: the CORPORA tuple is not in the file")
    return src.replace(old, new)


def m2_the_public_claim_has_no_predicate(src: str) -> str:
    """The goal-2 predicate is removed from the registry."""
    old = '            id="gate_refuses_moving_axes",'
    if old not in src:
        raise SystemExit("mutation 2: the predicate is not in the file")
    return src.replace(old, '            id="gate_refuses_moving_axes_DISABLED",')


def m3_the_deny_list_is_blunt(src: str) -> str:
    """The deny list goes back to 'admits every'."""
    old = '"admits every proposal", "admits any proposal",'
    new = '"admits every", "admits any",'
    if old not in src:
        raise SystemExit("mutation 3: the sharpened wording is not there")
    return src.replace(old, new)


def m4_the_ask_does_not_read_the_substrate(src: str) -> str:
    """The goal-2 predicate's ask always answers False.

    A predicate that reads False is not a missing check -- it is a
    check that says YES to the adversary.
    """
    old = "        return bool(veto_before and names_itself and is_a_bit)"
    new = "        return False"
    if old not in src:
        raise SystemExit("mutation 4: the ask's return is not in the file")
    return src.replace(old, new)


MUTATIONS = [
    ("M1  the measurement skips the unfitted corpora",
     PROPERTY, m1_measurement_skips_the_unfitted_corpora),
    ("M2  the public claim has no predicate",
     REGISTRY, m2_the_public_claim_has_no_predicate),
    ("M3  the deny list is blunt again",
     REGISTRY, m3_the_deny_list_is_blunt),
    ("M4  the ask does not read the substrate",
     REGISTRY, m4_the_ask_does_not_read_the_substrate),
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
    originals = {p: p.read_text(encoding="utf-8") for p in
                 (REGISTRY, PROPERTY)}
    print("MUTATION CHECK  the measurement coverage")
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
        for name, target, fn in MUTATIONS:
            try:
                mutated = fn(originals[target])
            except SystemExit as exc:
                print("%-52s SKIP (%s)" % (name, exc))
                all_red = False
                continue
            target.write_text(mutated, encoding="utf-8")
            rc, out = run_tests()
            state = "RED" if rc != 0 else "GREEN"
            failed = re.findall(r"^FAILED (\S+)", out, re.M)
            print("%-52s %s  rc=%d  %s"
                  % (name, state, rc, ", ".join(failed[:3])))
            if state == "GREEN":
                all_red = False
                print("    ^^ this mutation stayed GREEN: the checks it "
                      "targets do not catch it")
            target.write_text(originals[target], encoding="utf-8")

        print("-" * 72)
        print("every mutation went RED" if all_red
              else "AT LEAST ONE MUTATION STAYED GREEN")
        return 0 if all_red else 1
    finally:
        for p, s in originals.items():
            p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
