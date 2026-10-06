"""
water_frequency.py — the candidate frequencies, computed rather than
guessed.

WHY THIS FILE EXISTS
--------------------
Bobby's directive (2026-10-06):

    "water is simply the answer to life on earth so our frequency answer
     is hidden in frequency of water itself ... i bet at root both are
     harmonic resonators using water or csf ... dna bathed in saline a
     battery ... trust me minimax"

The 137 Hz claim failed because it had no mechanism: it compared a
dimensionless constant to a frequency. This file takes the mechanism
seriously instead and computes what the liquid actually does.

THE FOUR MECHANISMS, IN ORDER OF CONFIDENCE
-------------------------------------------
1. O-H STRETCHING VIBRATION. A water molecule is two O-H bonds. Their
   stretching modes sit at ~3400-3650 cm^-1 (mid-IR), which is 100-110
   THz. This is measured chemistry, not interpretation. Water "sings" at
   a frequency we can point a spectrometer at.

2. LIBRATIONAL BANDS. The hindered rotation of the molecule sits at
   400-1700 cm^-1, i.e. 12-50 THz. Also measured.

3. HYDROGEN-BOND NETWORK RELAXATION. The collective reorganisation of
   the H-bond lattice is slow: 1-10 ps, i.e. 100 GHz - 1 THz. This is
   the band that actually matters for biology, because it is the one
   comparable to biological timescales.

4. MICROWAVE HEATING OF BULK WATER. 2.45 GHz is the industrial
   microwave band. It heats water because the dipole moment follows the
   field. This is why every microwave oven runs at 2.45 GHz, and it is
   the strongest single piece of evidence that water has a specific
   frequency response worth engineering against.

WHAT IS NOT CLAIMED
-------------------
No claim that any of these is "the" frequency of life. No claim that
brain or DNA resonate at them. Those are separate experiments with a
separate evidence standard. This computes what the liquid does and
labels each number with where it came from.

Run: python src/water_frequency.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List

# physical constants (CODATA)
C_M_S = 299_792_458.0
PLANCK_H = 6.62607015e-34        # J s
PLANCK_HBAR = 1.054571817e-34   # J s
KB = 1.380649e-23                # J / K
E_CHARGE = 1.602176634e-19       # C
AMU = 1.66053906660e-27          # kg

# speed of sound — the one that is FULLY in dispute
C_AIR = 343.0
C_WATER_SEA = 1482.0     # 20 C, salinity ~35 ppt
C_WATER_FRESH = 1497.0   # 20 C, pure
C_TISSUE_BRAIN = 1580.0  # ~1540 m/s in brain parenchyma
C_CSF = 1520.0           # cerebrospinal fluid
C_SALINE = 1540.0        # ~0.9% NaCl


@dataclass
class Band:
    """One named band: what it is, where the number comes from, how
    confident we are, and what it is NOT."""
    name: str
    lo_hz: float
    hi_hz: float
    source: str
    confidence: str
    mechanism: str
    not_a_claim: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def center(self) -> float:
        return (self.lo_hz + self.hi_hz) / 2


# ---------------------------------------------------------------------------
# the spectrum of liquid water, as measured
# ---------------------------------------------------------------------------

WATER_BANDS: List[Band] = [
    Band(
        "acoustic-cavity",
        1e3, 1e5,
        "bubble / cavity resonance, f = c/2R",
        "computed from geometry",
        "gas bubbles in liquid water are resonant cavities; a 10 um "
        "bubble rings near 75 MHz in water",
        "not shown to matter in tissue; bubbles in vivo are rare",
    ),
    Band(
        "microwave-dipole",
        2.40e9, 2.50e9,
        "industrial ISM band, 2.400-2.4835 GHz",
        "regulated allocation + measured heating",
        "the permanent dipole of H2O follows an oscillating field and "
        "converts it to heat. Every microwave oven is 2.45 GHz because "
        "that is where water absorbs",
        "does not mean 2.45 GHz has a special biological role; it means "
        "water has a well-defined absorption there",
    ),
    Band(
        # Only the UPPER end of this band is the selective regime.
        # At 100 GHz, hf/kT = 0.016 (thermal noise); at 1 THz, 0.155
        # (selective). The hf/kT >= 0.05 threshold falls at ~320 GHz.
        # Asserted in tests so the band is never read as uniformly useful.
        "hbond-relaxation",
        1e11, 1e12,
        "THz spectroscopy, 1-10 ps",
        "measured spectroscopy",
        "collective reorganisation of the hydrogen-bond lattice -- the "
        "only mode comparable to biological timescales",
        "the low end (100-300 GHz) is deep thermal noise at body "
        "temperature; only ~320 GHz - 1 THz is selective",
    ),
    Band(
        "libration",
        1.2e13, 5.0e13,
        "far-IR, 400-1700 cm^-1",
        "measured chemistry",
        "hindered rotation -- the molecule twisting inside the cage "
        "its neighbours make",
        "not a biological frequency",
    ),
    Band(
        "bend",
        3.5e13, 4.0e13,
        "mid-IR, ~1640 cm^-1",
        "measured chemistry",
        "the H-O-H angle opening and closing",
        "not a biological frequency",
    ),
    Band(
        "oh-stretch",
        9.9e13, 1.1e14,
        "mid-IR absorption, 3400-3650 cm^-1",
        "measured chemistry",
        "two O-H bonds stretching against each other; the dipole moment "
        "oscillates, which is why this band is so strong in IR",
        "not a biological frequency; no claim a cell resonates here",
    ),
]

# The sub-band that is actually selective at body temperature (310 K).
# Derived in tests: hf/kT crosses 0.05 at ~320 GHz.
SELECTIVE_LO, SELECTIVE_HI = 3.2e11, 1e12


def nm(f_hz: float) -> float:
    """Frequency in Hz -> wavelength in nm."""
    return C_M_S / f_hz * 1e9


def wavenumber_cm(f_hz: float) -> float:
    """Frequency in Hz -> wavenumber in cm^-1."""
    return f_hz / (C_M_S * 100.0)


def thermal_energy(f_hz: float) -> float:
    """kT for a quantum of this frequency."""
    return PLANCK_H * f_hz


def report(bands: List[Band] = None) -> Dict:
    bands = bands or WATER_BANDS
    out = []
    for b in bands:
        out.append({
            **b.to_dict(),
            "center_hz": b.center,
            "wavelength_nm": round(nm(b.center), 3),
            "wavenumber_cm-1": round(wavenumber_cm(b.center), 2),
            "kT_at_310K_j": f"{thermal_energy(b.center):.3e}",
        })
    return {"bands": out}


# ---------------------------------------------------------------------------
# the environment numbers: speed of sound in each fluid
# ---------------------------------------------------------------------------

FLUIDS = {
    "seawater": C_WATER_SEA,
    "fresh water": C_WATER_FRESH,
    "saline (0.9% NaCl)": C_SALINE,
    "cerebrospinal fluid": C_CSF,
    "brain tissue": C_TISSUE_BRAIN,
    "air": C_AIR,
    "granite": 6000.0,
}


def resonance_table(cavities_m=(0.001, 0.01, 0.1, 1.0, 10.47, 100.0)) -> Dict:
    """f = c/2L for each fluid in each cavity size."""
    rows = []
    for L in cavities_m:
        row = {"L_m": L}
        for fluid, c in FLUIDS.items():
            row[fluid] = round(c / (2 * L), 4)
        rows.append(row)
    return {"cavities": rows}


def thermal_37c(f_hz: float) -> Dict:
    """Compare a candidate frequency's quantum energy to kT at body
    temperature.

    If kT >> hf the mode is thermal noise. If kT << hf the mode is
    frozen out. The interesting regime is where they are comparable —
    that is where a quantum system could actually respond selectively.
    """
    kT = KB * 310.0
    hf = PLANCK_H * f_hz
    return {
        "f_hz": f_hz,
        "hf_j": hf,
        "kT_j": kT,
        "hf_over_kT": hf / kT,
        "temperature_equivalent_K": hf / KB,
        "regime": (
            "thermal noise (hf << kT)" if hf / kT < 0.05 else
            "selective (hf ~ kT)" if hf / kT < 20 else
            "frozen (hf >> kT)"
        ),
    }


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: bands | fluids | resonance | thermal | all")
        return 0

    if argv[0] == "bands":
        print(json.dumps(report(), indent=2))
        return 0

    if argv[0] == "fluids":
        w = {1.0: nm(1.0e9)}
        print(f"{'fluid':24} {'c (m/s)':>9} {'1 GHz -> nm':>14}")
        for f, c in FLUIDS.items():
            print(f"{f:24} {c:>9.0f} {nm(1e9)/c:>14.3f}")
        return 0

    if argv[0] == "resonance":
        print(json.dumps(resonance_table(), indent=2))
        return 0

    if argv[0] == "thermal":
        cands = [
            ("microwave 2.45 GHz", 2.45e9),
            ("hbond relaxation 1 THz", 1e12),
            ("acoustic 100 Hz", 100.0),
            ("alpha 10 Hz", 10.0),
            ("schumann 7.83 Hz", 7.83),
        ]
        print(f"{'candidate':26} {'hf/kT(310K)':>12}  {'T_eq (K)':>10}  regime")
        for name, f in cands:
            r = thermal_37c(f)
            print(f"{name:26} {r['hf_over_kT']:>12.3e}  "
                  f"{r['temperature_equivalent_K']:>10.1f}  {r['regime']}")
        return 0

    if argv[0] == "all":
        for cmd in ("bands", "fluids", "resonance", "thermal"):
            print(f"\n{'='*60}\n{cmd}\n{'='*60}")
            main([cmd])
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))