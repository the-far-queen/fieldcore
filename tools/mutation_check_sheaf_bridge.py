"""
mutation_check_sheaf_bridge.py -- the sheaf bridge can go RED.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"* -- and the
bridge between the SCALAR sheaf and the LINEAR sheaf is new.

**AND A BRIDGE THAT CANNOT GO RED IS A BRIDGE THAT PROVES NOTHING.**

**AND THE MUTATIONS, one per claim the selftest makes:**

    M1  the scalar sheaf's broken seam stops being seen
    M2  the linear sheaf's cocycle stops being read
    M3  the cross compares H^1 instead of the cocycle
    M4  a question about a zero disagreement comes back
    M5  the refusal stops naming both sheafs
    M6  the agreement is hard-coded to True

**AND EVERY MUTATION MUST GO RED.**
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "src" / "sheaf_bridge.py"
PY = sys.executable


def _run_selftest() -> tuple[bool, str]:
    proc = subprocess.run([PY, "-B", str(TARGET), "--selftest"],
                          capture_output=True, text=True, cwd=str(REPO))
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def _mutate(src: str, old: str, new: str) -> str:
    if old not in src:
        raise AssertionError("the mutation site was not found: %r" % old[:70])
    return src.replace(old, new, 1)


MUTATIONS = [
    ("M1 the scalar sheaf's broken seam stops being seen",
     "    if broken:\n        sh.sites[\"c\"].observe(0.9)",
     "    if False:\n        sh.sites[\"c\"].observe(0.9)"),

    ("M2 the linear sheaf's cocycle stops being read",
     '    cocycle_norm = float(out.get("cocycle_norm", 0.0))',
     '    cocycle_norm = 0.0  # MUTATED: the cocycle is not read'),

    ("M3 the cross compares H^1 instead of the cocycle",
     "    data_obstructed = cocycle_norm > 1e-12",
     "    data_obstructed = obstructed  # MUTATED: the cover, not the data"),

    # M4 IS IN THE OTHER FILE, and that is the point: the vacuous
    # question is the LINEAR sheaf's, and the bridge is what catches it.
    # So the mutation is applied to sheaf_loop.py -- the loop's guard --
    # and the BRIDGE's selftest must go red because the question comes
    # back.
    ("M4 a question about a zero disagreement comes back",
     "        if norm <= 1e-12:\n"
     '            return {"question": None, "directions": [], "vacuous": True}',
     "        if False:\n"
     '            return {"question": None, "directions": [], "vacuous": True}',
     "sheaf_loop.py"),

    ("M5 the refusal stops naming both sheafs",
     '            "the two sheafs disagree about the same obstruction: the "\n'
     '            "scalar sheaf says consistent=%s (coherence %.6f, drift "',
     '            "the obstruction: the "\n'
     '            "scalar sheaf says consistent=%s (coherence %.6f, drift "',
     "sheaf_bridge.py"),

    ("M6 the agreement is hard-coded to True",
     "    agree = (not scalar_consistent) == data_obstructed",
     "    agree = True  # MUTATED: the cross always agrees",
     "sheaf_bridge.py"),
]


def main() -> int:
    print("=" * 78)
    print("THE SHEAF BRIDGE, AND WHETHER IT CAN GO RED")
    print("=" * 78)
    print()

    original = TARGET.read_text(encoding="utf-8")

    ok, out = _run_selftest()
    print("the selftest as it stands: %s" % ("PASSES" if ok else "FAILS"))
    if not ok:
        print(out[-1500:])
        print()
        print("THE SELFTEST DOES NOT PASS, SO THERE IS NOTHING TO MUTATE")
        return 1

    # AND THE MUTATIONS CAN TARGET EITHER FILE, because the vacuous
    # question lives in the LINEAR sheaf and the cross lives in the
    # bridge -- and it is the BRIDGE's selftest that must catch it.
    LOOP = REPO / "src" / "sheaf_loop.py"
    originals = {TARGET: TARGET.read_text(encoding="utf-8"),
                 LOOP: LOOP.read_text(encoding="utf-8")}

    went_red = 0
    stayed_green = []
    try:
        for entry in MUTATIONS:
            name, old, new = entry[0], entry[1], entry[2]
            target = REPO / "src" / entry[3] if len(entry) > 3 else TARGET
            target.write_text(_mutate(originals[target], old, new),
                              encoding="utf-8")
            passed, mout = _run_selftest()
            if passed:
                stayed_green.append(name)
                print("  [GREEN] %-52s <-- THE CLAIM IS NOT PROVEN" % name)
            else:
                went_red += 1
                first = ""
                for line in mout.splitlines():
                    if "AssertionError" in line:
                        first = line.strip()[:70]
                        break
                print("  [RED  ] %-52s %s" % (name, first))
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")

    print()
    print("  mutations that went RED: %d" % went_red)
    print("  mutations that stayed GREEN: %d" % len(stayed_green))
    for n in stayed_green:
        print("     -- %s" % n)
    print()
    if stayed_green:
        print("  EVERY MUTATION MUST GO RED, AND %d DID NOT" % len(stayed_green))
        return 1
    print("  every mutation went RED: the checks hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
