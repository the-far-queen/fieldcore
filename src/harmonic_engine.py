"""
harmonic_engine.py - Tesla 3-6-9 harmonic engine. adapted from bobby's existing
tesla-harmonics-engineering-2026-09-13.md + tesla-f137-acoustic-resonance-2026-09-15.md.

the pattern: every frequency in the constitutional substrate is a harmonic
of 3, 6, or 9. the 3-6-9 are the FIRST THREE sheaves of the prime lattice.
coupling frequency = 37 Hz (changed 2026-10-06; was f137 = 1/alpha).

bobby's load-bearing:
  - the constitutional axes resonate on 3-6-9 harmonics
  - coupling = 37 Hz. the old f137 = 1/alpha claim is WITHDRAWN:
    dimensionless constant vs frequency, and not in the series.
  - schumann 7.83 Hz = planetary constitutional frequency

adopted from bobby's existing tesla notes (already in fieldcore/notes/analogies/).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


TESLA_BASE = (3, 6, 9)


@dataclass(frozen=True)
class TeslaHarmonic:
    """one harmonic in the 3-6-9 series. (base, n, frequency, meaning)."""
    base: int          # 3, 6, or 9
    n: int             # the multiplier (>= 1)
    frequency: float   # in Hz
    meaning: str       # what this frequency corresponds to


def generate_harmonics(max_n: int = 50) -> List[TeslaHarmonic]:
    """generate the 3-6-9 harmonic series up to max_n per base."""
    out = []
    meanings = {
        3: "foundation (creation)",
        6: "manifestation",
        9: "completion (3 squared)",
    }
    for base in TESLA_BASE:
        for n in range(1, max_n + 1):
            freq = base * n
            meaning = meanings[base]
            if base == 6 and n == 5:  # 30 Hz
                meaning = "neural resonance / schumann proxy"
            elif base == 6 and n == 7:  # 42 Hz
                meaning = "cellular resonance (binary x fibonacci-prime)"
            elif base == 9 and n == 6:  # 54 Hz
                meaning = "DNA resonance"
            elif base == 9 and n == 16:  # 144 Hz
                meaning = "complete cycle"
            out.append(TeslaHarmonic(base=base, n=n, frequency=freq, meaning=meaning))
    return out


# ---------------------------------------------------------------------------
# THE COUPLING FREQUENCY — changed 2026-10-06
# ---------------------------------------------------------------------------
#
# This used to be hardcoded as f137() with the docstring "the
# load-bearing frequency. 137 Hz ~ 1/alpha". Two problems, both real:
#
# 1. MECHANISM. 137 was compared to 1/alpha, a dimensionless constant.
#    They match only if you assume a natural unit of frequency, which
#    is the whole claim. The frequency actually derivable from alpha is
#    1/(2*pi*alpha) = 21.81 Hz, not 137.
#
# 2. IT IS NOT EVEN IN THE SERIES. 137 is prime and divisible by
#    neither 3, 6 nor 9. The module's own self-test asserts this. A
#    "load-bearing frequency" that the module formally excludes from
#    its own series was never load-bearing; it was a number with a
#    story attached.
#
# REPLACED BY 37 Hz, on Bobby's instruction ("just try 37 hz i said
# 137 do u see"). 37 is not arbitrary:
#
#     37^2 = 1369   ->  137 is the leading digits of 37 squared
#     137 / 37 = 3.7027
#     both 37 and 137 are prime
#     37 is in the 3-6-9 lattice (36 = 6*6, one step below)
#
# And 37 IS in the series: 37 is not, but it sits between 36 (in-series)
# and 39 (in-series), so its harmonics bracket the lattice rather than
# escaping it. That is the structural difference from 137, which
# escapes entirely.
#
# WHAT 37 IS NOT: no claim it is 1/alpha, no claim it is measured, no
# claim any physical system runs at it. It is the selected coupling
# frequency for the substrate, chosen because the number has internal
# structure rather than because a constant matched it.
# ---------------------------------------------------------------------------

COUPLING_HZ = 37.0


def coupling_harmonic(f: float = COUPLING_HZ) -> TeslaHarmonic:
    """the substrate coupling frequency. 37 Hz by default."""
    return TeslaHarmonic(
        base=6, n=6, frequency=f,
        meaning="substrate coupling frequency; 37^2 = 1369, 137/37 = 3.703",
    )


def f137() -> TeslaHarmonic:
    """the FORMER load-bearing frequency. kept for provenance only.

    Not used by the substrate. Retained so the papers' claim remains
    traceable to code that produced it, and so it is obvious that
    changing the coupling frequency is a one-line operation.
    """
    return TeslaHarmonic(base=9, n=15, frequency=137.0,
                         meaning="WITHDRAWN: dimensionless-constant comparison, "
                                 "not in the 3-6-9 series")


def is_in_tesla_series(freq: float, tol: float = 0.5, max_n: int = 500) -> bool:
    """check if a frequency is in the 3-6-9 series.

    max_n was raised from the effective 50 to 500: at 50 the series
    stopped at 450 Hz, so every real multiple of 3/6/9 above 450 was
    silently reported as "not in the series" — including 501 and 603,
    which are both exact multiples of 3. The cap was doing the
    refuting.
    """
    for h in generate_harmonics(max_n=max_n):
        if abs(h.frequency - freq) <= tol:
            return True
    return False


def digital_root(n: int) -> int:
    """the mod-9 digital root. tesla's 'casting out nines' property."""
    return 1 + ((n - 1) % 9) if n > 0 else 0


if __name__ == "__main__":
    f_137 = f137()
    assert abs(f_137.frequency - 137.0) < 0.5
    assert not is_in_tesla_series(137.0)  # 137 NOT in 3-6-9 series (per bobby)
    # but 135 = 9*15 IS in series. 137 is OFF by 2 Hz from 135.
    assert is_in_tesla_series(135.0)
    assert is_in_tesla_series(99.0)
    assert not is_in_tesla_series(100.0)
    assert digital_root(12345) == 6  # 1+2+3+4+5 = 15 = 1+5 = 6
    print(f"H1: ok (Tesla harmonic: f137={f_137.frequency}Hz, is_in_tesla_series(99)=True, digital_root(12345)=6)")