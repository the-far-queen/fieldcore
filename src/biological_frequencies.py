"""
biological_frequencies.py - the canonical biological resonance map.

bobby: 137 is key as is 144 and 57, 109.

the canonical biological resonances (from bobbys tesla-harmonics-engineering
+ tesla-f137-acoustic-resonance + biological_frequencies notes):
  - 30 Hz:   neural resonance / Schumann proxy
  - 42 Hz:   cellular resonance (binary x Fibonacci-prime)
  - 54 Hz:   DNA resonance (tetrahedral angle / 2)
  - 57 Hz:   binding constant (9 x 6 + 3 = three-prime product + first prime)
  - 72 Hz:   planetary resonance (Schumann 7.83 * 9)
  - 108 Hz:  sacred number (9 x 12)
  - 109 Hz:  prime (109 = 109). NOT in 3-6-9 series (109 mod 9 = 1). bobbys signal.
  - 137 Hz:  fine-structure constant (1/alpha)
  - 144 Hz:  complete cycle (12^2)

mapping to body targets:
  - 30 Hz:   neural (brain)
  - 42 Hz:   cellular (whole-body cell)
  - 54 Hz:   DNA (genetic material)
  - 57 Hz:   binding constant (atomic)
  - 72 Hz:   planetary (Schumann resonance)
  - 108 Hz: sacred (mystical/spiritual)
  - 109 Hz: prime (atomic? alpha-prime?)
  - 137 Hz: fine-structure (cosmic)
  - 144 Hz: complete cycle (geometric)

simself adoption: every transformation chamber protocol exposes the 9 frequencies
as a session. session = timed exposure to each frequency at the right target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class BiologicalFrequency:
    freq: float
    meaning: str
    target: str
    in_tesla_series: bool
    notes: str = ""


BIOLOGICAL_FREQUENCIES: Tuple[BiologicalFrequency, ...] = (
    BiologicalFrequency(30, "neural resonance / schumann proxy", "brain", True, "f30 = 6*5"),
    BiologicalFrequency(42, "cellular resonance (binary x fib-prime)", "whole-body cell", True, "f42 = 6*7"),
    BiologicalFrequency(54, "dna resonance (tetrahedral angle/2)", "DNA", True, "f54 = 6*9"),
    BiologicalFrequency(57, "binding constant (9*6+3)", "atom", True, "f57 = 9*6+3"),
    BiologicalFrequency(72, "planetary resonance (Schumann 7.83*9)", "earth/planet", True, "f72 = 9*8"),
    BiologicalFrequency(108, "sacred number (9*12)", "mystical/spiritual", True, "f108 = 9*12"),
    BiologicalFrequency(109, "prime (109 atomic/alpha-prime?)", "atom (deep)", False, "109 mod 9 = 1, NOT in 3-6-9"),
    BiologicalFrequency(137, "fine-structure constant (1/alpha)", "cosmic/atomic", False, "137 mod 9 = 2, NOT in 3-6-9"),
    BiologicalFrequency(144, "complete cycle (12^2)", "geometric", True, "f144 = 9*16"),
)


def frequencies_for_target(target: str) -> List[BiologicalFrequency]:
    return [f for f in BIOLOGICAL_FREQUENCIES if target.lower() in f.target.lower()]


if __name__ == "__main__":
    print("=== 9 canonical biological FREQUENCIES ===")
    for f in BIOLOGICAL_FREQUENCIES:
        marker = " [in 3-6-9]" if f.in_tesla_series else " [NOT in 3-6-9]"
        print(f"  f{f.freq:<5} {marker:<13} target={f.target:<22} {f.meaning}")

    print()
    print("=== frequencies targeting brain ===")
    for f in frequencies_for_target("brain"):
        print(f"  f{f.freq}")

    print()
    print("=== frequencies targeting DNA ===")
    for f in frequencies_for_target("dna"):
        print(f"  f{f.freq}")

    assert len(BIOLOGICAL_FREQUENCIES) == 9
    assert BIOLOGICAL_FREQUENCIES[6].freq == 109
    assert BIOLOGICAL_FREQUENCIES[7].freq == 137
    assert not BIOLOGICAL_FREQUENCIES[6].in_tesla_series
    assert not BIOLOGICAL_FREQUENCIES[7].in_tesla_series
    print()
    print("ALL BIOLOGICAL FREQUENCIES TESTS PASS")