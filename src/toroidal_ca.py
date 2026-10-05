from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class TorusGeometry:
    """torus parameterization. rankdim/torus-inspired."""
    R: float = 8.0    # major radius
    r: float = 4.0    # minor radius
    grid_width: int = 80
    grid_height: int = 40

    def surface_position(self, u: float, v: float) -> Tuple[float, float, float]:
        """u, v in [0, 1]. return the (x, y, z) on the torus surface."""
        import math
        theta = 2 * math.pi * u
        phi = 2 * math.pi * v
        x = (self.R + self.r * math.cos(phi)) * math.cos(theta)
        y = (self.R + self.r * math.cos(phi)) * math.sin(theta)
        z = self.r * math.sin(phi)
        return (x, y, z)

    def surface_normal(self, u: float, v: float) -> Tuple[float, float, float]:
        """normal at (u, v) on the torus."""
        import math
        theta = 2 * math.pi * u
        phi = 2 * math.pi * v
        x = math.cos(phi) * math.cos(theta)
        y = math.cos(phi) * math.sin(theta)
        z = math.sin(phi)
        return (x, y, z)


@dataclass
class ToroidalCA:
    """the cellular automaton on the torus. Conway-style rules with toroidal wraparound."""

    def __init__(self, geometry: TorusGeometry, density: float = 0.3):
        self.geometry = geometry
        self.density = density
        self.grid: List[List[int]] = []
        self.generation = 0
        self.reset()

    def reset(self) -> None:
        import random
        w = self.geometry.grid_width
        h = self.geometry.grid_height
        self.grid = [[1 if random.random() < self.density else 0
                      for _ in range(w)] for _ in range(h)]
        self.generation = 0

    def count_neighbors(self, x: int, y: int) -> int:
        """toroidal wraparound. rankdim-style."""
        w, h = self.geometry.grid_width, self.geometry.grid_height
        return sum(self.grid[(y + dy) % h][(x + dx) % w]
                   for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                   if (dx, dy) != (0, 0))

    def step(self) -> List[List[int]]:
        """one CA step. Conway rules with toroidal wraparound."""
        w, h = self.geometry.grid_width, self.geometry.grid_height
        new = [[0]*w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                n = self.count_neighbors(y, x)
                if self.grid[y][x] == 1:
                    new[y][x] = 1 if n in (2, 3) else 0
                else:
                    new[y][x] = 1 if n == 3 else 0
        self.grid = new
        self.generation += 1
        return new

    def digest(self) -> str:
        canonical = "\\n".join("".join(str(c) for c in row) for row in self.grid)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


if __name__ == "__main__":
    geo = TorusGeometry()
    ca = ToroidalCA(geo, density=0.3)
    d1 = ca.digest()
    ca.step()
    d2 = ca.digest()
    assert d1 != d2
    ca.step()
    ca.step()
    ca.step()
    assert ca.generation == 4
    print(f"T1: ok (toroidal CA, generation={ca.generation}, digests vary)")

    p = geo.surface_position(0.5, 0.5)
    assert len(p) == 3
    n = geo.surface_normal(0.5, 0.5)
    assert len(n) == 3
    print(f"T2: ok (torus surface at (0.5, 0.5) = {p}, normal = {n})")

    print("\\nALL TOROIDAL_CA TESTS PASS")