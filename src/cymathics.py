"""
cymathics.py — Chladni pattern simulation. adopted from multiple Chladni repos.

the pattern: solve the wave equation on a 2D plate with fixed boundaries,
visualize the nodal lines (where the sand would collect on a Chladni plate).

bobby's load-bearing: cymatics IS the substrate. **the resonance patterns
show the geometry of the substrate.** f137 = fine-structure constant.

simself adoption:
  - the substrate's resonance pattern IS the constitutional graph
  - nodal lines = sacred axes (no displacement)
  - antinodes = resilient axes (max displacement)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class ChladniPlate:
    """a 2D Chladni plate. width x height. fixed at edges."""
    width: int = 100
    height: int = 100

    def mode(self, m: int, n: int) -> float:
        """the (m, n) mode frequency. (m+1) and (n+1) avoid zero-mode issue."""
        return math.sqrt(((m+1) ** 2 + (n+1) ** 2))


@dataclass
class ChladniSimulator:
    """a simple finite-difference Chladni simulator."""

    def __init__(self, plate: ChladniPlate, m: int = 5, n: int = 8):
        self.plate = plate
        self.m = m
        self.n = n

    def displacement(self, t: float) -> List[List[float]]:
        """the (m, n) eigenmode at time t."""
        w, h = self.plate.width, self.plate.height
        omega = self.plate.mode(self.m, self.n)
        result = []
        for y in range(h):
            row = []
            for x in range(w):
                val = (math.sin((self.m+1) * math.pi * x / (w-1)) *
                       math.sin((self.n+1) * math.pi * y / (h-1)) *
                       math.cos(omega * t))
                row.append(val)
            result.append(row)
        return result

    def nodal_lines(self, t: float = 0, threshold: float = 0.01) -> int:
        """count the nodal lines (zero crossings). the load-bearing pattern metric."""
        grid = self.displacement(t)
        nodes = 0
        for y in range(len(grid)):
            for x in range(1, len(grid[0])):
                if (grid[y][x-1] < -threshold < grid[y][x]) or (grid[y][x-1] > threshold > grid[y][x]):
                    nodes += 1
        return nodes


if __name__ == "__main__":
    plate = ChladniPlate()
    sim = ChladniSimulator(plate, m=5, n=8)
    d = sim.displacement(0.0)
    assert len(d) == plate.height
    assert len(d[0]) == plate.width
    nodes = sim.nodal_lines(0.0)
    assert nodes > 0
    print(f"C1: ok (Chladni mode (5,8): {nodes} nodal lines)")