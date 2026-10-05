"""
harmonic_engine.py - Tesla 3-6-9 harmonic engine. adapted from bobby's existing
tesla-harmonics-engineering-2026-09-13.md + tesla-f137-acoustic-resonance-2026-09-15.md.

the pattern: every frequency in the constitutional substrate is a harmonic
of 3, 6, or 9. the 3-6-9 are the FIRST THREE sheaves of the prime lattice.
f137 = 1/alpha (fine-structure constant).

bobby's load-bearing:
  - the constitutional axes resonate on 3-6-9 harmonics
  - f137 = the fine-structure constant frequency (load-bearing across physics)
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


def f137() -> TeslaHarmonic:
    """the load-bearing frequency. 137 Hz ~ 1/alpha."""
    return TeslaHarmonic(base=9, n=15, frequency=137.0,
                         meaning="fine-structure constant frequency ~ 1/a = 137.036")


def is_in_tesla_series(freq: float, tol: float = 0.5) -> bool:
    """check if a frequency is in the 3-6-9 series."""
    for h in generate_harmonics():
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