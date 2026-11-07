#!/usr/bin/env python3
"""
mutation_check_coherence_spine.py -- THE SPINE CAN GO RED.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*, and the
robot's pattern for each fc system: the substrate it reaches, a
MEASUREMENT that it reaches it, a NAMED REFUSAL, a selftest that can
go RED, and the census saying WIRED rather than ORPHAN.

**AND THE CENSUS SAID THIS MODULE HAD A HOLE, AND THE HOLE WAS THIS
ONE.** MEASURED 2026-11-07 by `tools/pattern_census.py`, over the
whole fc:

    the modules measured        220
    the pattern WHOLE             7
    with HOLES in it            213

and `coherence_spine` -- which the fc's own docs name TWICE, and which
three of the fc's own modules import (`evacuated`, `predicate_registry`,
`sheaf_bridge`) -- carried exactly ONE hole:

    coherence_spine   meas ok  ref ok  red .    <- CAN GO RED

**AND THAT IS THE WORST KIND OF HOLE, because the module LOOKS
complete.** It has a measurement (`coherence()`), it has a named
refusal (`'b->c: restricted 0.5 vs held 0.9, gap 0.4 > tolerance
0.01'`), and it has a selftest that PASSES. **A SELFTEST THAT HAS
NEVER BEEN MUTATED IS A SELFTEST NOBODY HAS SEEN FAIL.** The bridge
next door has six mutations; the spine had none.

**AND THE MUTATIONS, one per claim the selftest makes:**

    M1  the seam break stops being seen
    M2  the coherence stops being computed from the structure
    M3  the threshold stops refusing
    M4  the threshold's bound stops being immutable
    M5  the NaN bound stops being refused
    M6  the violation stops naming the seam
    M7  a fresh site stops reporting its own value as drift
    M8  the glue map stops applying its rule

**AND EVERY MUTATION MUST GO RED.** A mutation that stays GREEN is a
claim that is not proven, and the check names it.

**AND THE MUTATED FILE IS RESTORED BY THE SHARED RESTORE**, so the
tree ends byte-identical AND stat-identical -- the bytes are what a
reader sees and the mtime is what the gate fingerprints.

Run:
    python tools/mutation_check_coherence_spine.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from mutation_restore import Restored          # noqa: E402

TARGET = REPO / "src" / "coherence_spine.py"
PY = sys.executable


def _run_selftest() -> tuple[bool, str]:
    proc = subprocess.run([PY, "-B", str(TARGET), "--selftest"],
                          capture_output=True, text=True, cwd=str(REPO))
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def _mutate(src: str, old: str, new: str) -> str:
    if old not in src:
        raise AssertionError("the mutation site was not found: %r" % old[:70])
    return src.replace(old, new, 1)


#: THE MUTATIONS. Each one removes ONE mechanism from the module, and
#: the module's own selftest must notice.
MUTATIONS = [
    ("M1 the seam break stops being seen",
     "        return not self.violations()",
     "        return True  # MUTATED: the seam is never seen"),

    ("M2 the coherence stops being computed from the structure",
     "        mean_gap = total / len(self.maps)\n"
     "        return max(0.0, min(1.0, 1.0 - mean_gap))",
     "        return 1.0  # MUTATED: the coherence is asserted, not computed"),

    ("M3 the threshold stops refusing",
     "    def fires(self, value: float) -> bool:\n"
     '        return value >= self.bound if self.direction == "above" \\\n'
     '            else value <= self.bound',
     "    def fires(self, value: float) -> bool:\n"
     "        return False  # MUTATED: nothing ever breaches"),

    ("M4 the threshold's bound stops being immutable",
     "@dataclass(frozen=True)\n"
     "class Threshold:",
     "@dataclass\n"
     "class Threshold:"),

    ("M5 the NaN bound stops being refused",
     "        if math.isnan(self.bound) or math.isinf(self.bound):\n"
     '            raise ValueError(f"{self.name}: bound must be finite, got {self.bound}")',
     "        if False:\n"
     '            raise ValueError(f"{self.name}: bound must be finite, got {self.bound}")'),

    ("M6 the violation stops naming the seam",
     '                out.append(\n'
     '                    f"{g.name}: restricted {restricted:.6g} vs held "\n'
     '                    f"{tgt.value:.6g}, gap {gap:.6g} > tolerance "\n'
     '                    f"{tgt.tolerance:.6g}")',
     '                out.append(\n'
     '                    f"{g.name}: something is wrong")'),

    ("M7 a fresh site stops reporting its own value as drift",
     "        if self.prior is None:\n"
     "            self.prior = self.value",
     "        if self.prior is None:\n"
     "            self.prior = 0.0  # MUTATED: a system at rest looks moved"),

    ("M8 the glue map stops applying its rule",
     "    def apply(self, value: float) -> float:\n"
     "        return float(self.rule(value))",
     "    def apply(self, value: float) -> float:\n"
     "        return float(value)  # MUTATED: the rule is ignored"),
]


def main() -> int:
    print("=" * 78)
    print("THE COHERENCE SPINE, AND WHETHER IT CAN GO RED")
    print("=" * 78)
    print()

    ok, out = _run_selftest()
    print("the selftest as it stands: %s" % ("PASSES" if ok else "FAILS"))
    if not ok:
        print(out[-1500:])
        print()
        print("THE SELFTEST DOES NOT PASS, SO THERE IS NOTHING TO MUTATE")
        return 1

    went_red = 0
    stayed_green = []
    for name, old, new in MUTATIONS:
        with Restored(TARGET) as f:
            try:
                f.write(_mutate(f._original, old, new))
            except AssertionError as exc:
                print("  [STALE] %-52s %s" % (name, exc))
                stayed_green.append(name)
                continue
            passed, mout = _run_selftest()
        if passed:
            stayed_green.append(name)
            print("  [GREEN] %-52s <-- THE CLAIM IS NOT PROVEN" % name)
        else:
            went_red += 1
            first = ""
            for line in mout.splitlines():
                if "AssertionError" in line or "Error" in line:
                    first = line.strip()[:70]
                    break
            print("  [RED  ] %-52s %s" % (name, first))

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
