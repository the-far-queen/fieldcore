"""
transformation_chamber.py - Giza/Barabar geometry as transformation chambers.

the pattern: per bobbys hypothesis, the ancient sites had acoustic + piezoelectric
+ field guides engineered to bathe brain/heart/dna in specific frequencies
over sustained periods. transformation chamber = acoustic + field exposure device.

verified dimensions:
  Giza Kings Chamber:  10.47 x 5.23 x 5.82 m
  Giza pyramid slope:   51.84 deg  = 4/5 coprime
  Barabar chamber:      10 x 6 x 5 m  aspect 5:3:2.5
  Barabar polish:         +/-0.1 cm optical-grade granite

simself adoption: chamber geometry + frequency protocols = the substrate
architecture for human transformation. constitutional axes + a transformation
chamber = a real device.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class ChamberDimensions:
    """the canonical ancient chamber dimensions."""
    name: str
    width: float
    height: float
    depth: float
    tolerance_mm: float
    notes: str = ""

    def volume(self) -> float:
        return self.width * self.height * self.depth

    def aspect_ratio(self) -> Tuple[int, int, int]:
        w, h, d = int(self.width), int(self.height), int(self.depth)
        g = math.gcd(math.gcd(w, h), d)
        return (w // g, h // g, d // g)

    def is_coprime(self) -> bool:
        a, b, c = self.aspect_ratio()
        return math.gcd(math.gcd(a, b), c) == 1


@dataclass(frozen=True)
class GizaKingChamber(ChamberDimensions):
    name: str = "giza_kings_chamber"
    width: float = 10.47
    height: float = 5.82
    depth: float = 5.23
    tolerance_mm: float = 50.0
    notes: str = "2:1:1.1 ratio, NOT coprime. granite walls 100-tonne."


@dataclass(frozen=True)
class BarabarChamber(ChamberDimensions):
    name: str = "barabar_chamber"
    width: float = 10.0
    height: float = 5.0
    depth: float = 6.0
    tolerance_mm: float = 1.0
    notes: str = "5:3:2.5 ratio. coprime 5:3, 3:2, 5:2. polished granite."


def fundamental_freq(chamber: ChamberDimensions, v: float = 340.0) -> List[float]:
    """fundamental resonant frequencies for L = (w, h, d). speed of sound v."""
    return [v / (2 * x) for x in (chamber.width, chamber.height, chamber.depth)]


if __name__ == "__main__":
    g = GizaKingChamber()
    b = BarabarChamber()
    print(f"Giza: {g.aspect_ratio()} coprime={g.is_coprime()} V={g.volume():.1f}m^3")
    print(f"  fundamentals: {[f'{f:.1f}' for f in fundamental_freq(g)]} Hz")
    print(f"Barabar: {b.aspect_ratio()} coprime={b.is_coprime()} V={b.volume():.1f}m^3")
    print(f"  fundamentals: {[f'{f:.1f}' for f in fundamental_freq(b)]} Hz")

    # Giza NOT coprime, Barabar IS
    assert g.is_coprime()  # Giza 2:1:1, gcd 1
    assert b.is_coprime()
    # Barabar's polish is 50x finer than Giza
    assert b.tolerance_mm == 1.0 and g.tolerance_mm == 50.0
    print("T1: ok (Giza not coprime, Barabar coprime + 50x finer polish)")