"""
cavity_modes.py — room-mode frequencies from geometry alone.

WHY THIS EXISTS
---------------
The 137 Hz claim in the FieldCore papers was a guess: a dimensionless
constant (1/alpha) compared against a frequency, equal only if you
assume a natural unit of frequency. There was no mechanism.

The alternative Bobby named is the one that actually works, and it is
older and blunter:

    f  =  c / (2L)     for a dimension between two reflecting surfaces
    f  = (c/2) * sqrt((n/Lx)^2 + (m/Ly)^2 + (p/Lz)^2)   for a room

Frequency is set by GEOMETRY and the wave speed in the medium. That
makes it derivable rather than guessed, and derivable numbers can be
built, measured, and checked against a microphone.

This module computes the room-mode spectrum of a rectangular cavity
from its dimensions. It does not claim any pyramid was built to a
frequency. It claims only that dimensions determine modes, which is
textbook acoustics and is verifiable with a phone microphone and a
clap.

WHAT IT IS NOT
--------------
1. Not a claim about intent. Giza's proportions may or may not have
   been chosen for any acoustic reason. This computes what the
   geometry WOULD produce. Whether anyone knew is a separate question
   with a separate evidence standard.

2. Not biology. Nothing here says a human being resonates at these
   frequencies. The brain-coupling idea is a separate experiment.

3. Not numerology. No constants are fitted to make numbers look
   meaningful. Every output is c and L in, frequency out.

Run: python src/cavity_modes.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

# wave speed in dry air at 20 C, m/s
C_AIR = 343.0
# speed of sound in granite, m/s (published range roughly 5000-6500)
C_GRANITE = 6000.0


@dataclass
class Mode:
    """One room mode. (n,m,p) are the half-wave counts per axis."""
    f: float
    n: int
    m: int
    p: int
    band: str

    def to_dict(self) -> Dict:
        return asdict(self)


def _band(f: float) -> str:
    """Name the frequency band. EEG/MEG convention, since the interest
    is coupling to a brain, not acoustics for its own sake."""
    if f < 1: return "delta-sub"
    if f < 4: return "delta"
    if f < 8: return "theta"
    if f < 13: return "alpha"
    if f < 30: return "beta"
    if f < 80: return "gamma"
    if f < 8000: return "alpha-band+"
    return "ultrasonic"


def axial_modes(Lx: float, Ly: float, Lz: float,
                c: float = C_AIR, n_max: int = 12) -> List[Mode]:
    """Modes where only ONE index is non-zero.

    These are the strongest, most easily excited modes in a room and
    the ones worth measuring first with a microphone. A listener at one
    end of an axis hears these loudest.
    """
    out: List[Mode] = []
    for axis, L in enumerate((Lx, Ly, Lz)):
        for n in range(1, n_max + 1):
            f = c * n / (2.0 * L)
            idx = [0, 0, 0]
            idx[axis] = n
            out.append(Mode(round(f, 4), idx[0], idx[1], idx[2], _band(f)))
    out.sort(key=lambda m: m.f)
    return out


def full_modes(Lx: float, Ly: float, Lz: float,
               c: float = C_AIR, n_max: int = 4) -> List[Mode]:
    """All (n,m,p) up to n_max. Degenerate modes are kept separate
    because that degeneracy IS the signature of a cube and is worth
    seeing rather than smoothing away."""
    out: List[Mode] = []
    for n in range(0, n_max + 1):
        for m in range(0, n_max + 1):
            for p in range(0, n_max + 1):
                if n == m == p == 0:
                    continue
                f = (c / 2.0) * math.sqrt(
                    (n / Lx) ** 2 + (m / Ly) ** 2 + (p / Lz) ** 2
                )
                out.append(Mode(round(f, 4), n, m, p, _band(f)))
    out.sort(key=lambda mo: (mo.f, mo.n, mo.m, mo.p))
    return out


def degeneracy(modes: List[Mode], tol: float = 0.5) -> Dict[float, int]:
    """How many modes share a frequency.

    A perfect cube is maximally degenerate; a room that is not a cube
    is not. For a rectangular cavity the pattern of coincident
    frequencies is a direct fingerprint of the aspect ratio, and it is
    measurable. This is the honest version of "the pyramid was tuned
    to a frequency": you can measure the fingerprint and compare it to
    the predicted one.
    """
    hist: Dict[float, int] = {}
    for mo in modes:
        key = round(mo.f / tol) * tol
        hist[key] = hist.get(key, 0) + 1
    return dict(sorted(hist.items()))


def report(Lx: float, Ly: float, Lz: float, c: float = C_AIR,
           label: str = "", n_max: int = 12) -> Dict:
    ax = axial_modes(Lx, Ly, Lz, c)
    fm = full_modes(Lx, Ly, Lz, c)
    return {
        "label": label,
        "dimensions_m": {"Lx": Lx, "Ly": Ly, "Lz": Lz},
        "wave_speed_m_s": c,
        "fundamental_per_axis_hz": {
            "x": round(c / (2 * Lx), 4),
            "y": round(c / (2 * Ly), 4),
            "z": round(c / (2 * Lz), 4),
        },
        "axial_modes": [m.to_dict() for m in ax],
        "lowest_12_full_modes": [m.to_dict() for m in fm[:12]],
        "degeneracy_histogram": degeneracy(fm),
        "note": (
            "Computed from geometry and wave speed. Says nothing about "
            "whether the geometry was chosen for this."
        ),
    }


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: kings | cube | granite | custom | compare")
        return 0

    if argv[0] == "kings":
        # King's Chamber interior, commonly cited ~10.47 x 5.23 x 5.97 m
        r = report(10.47, 5.23, 5.97, C_AIR, "King's Chamber (air)")
        print(json.dumps(r, indent=2))
        return 0

    if argv[0] == "cube":
        r = report(2.0, 2.0, 2.0, C_AIR, "2m cube (air)")
        print(json.dumps(r, indent=2))
        return 0

    if argv[0] == "granite":
        # Solid granite block, not a room. Shows the scale difference:
        # granite carries ~17x the frequency of air at the same length.
        r = report(2.0, 2.0, 2.0, C_GRANITE, "2m granite block (solid)")
        print(json.dumps(r, indent=2))
        return 0

    if argv[0] == "custom":
        if len(argv) < 4:
            print("usage: custom Lx Ly Lz [c]")
            return 1
        c = float(argv[4]) if len(argv) > 4 else C_AIR
        r = report(float(argv[1]), float(argv[2]), float(argv[3]), c, "custom")
        print(json.dumps(r, indent=2))
        return 0

    if argv[0] == "compare":
        cases = [
            (10.47, 5.23, 5.97, C_AIR, "King's Chamber air"),
            (2.0, 2.0, 2.0, C_AIR, "cube air"),
            (2.0, 2.0, 2.0, C_GRANITE, "cube granite"),
        ]
        print(f"{'case':26} {'fx':>9} {'fy':>9} {'fz':>9}")
        for Lx, Ly, Lz, c, name in cases:
            print(f"{name:26} {c/(2*Lx):>9.2f} {c/(2*Ly):>9.2f} {c/(2*Lz):>9.2f}")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))