"""
water_cymatics_3d.py - 3D cymatics in water. cymatic patterns form in fluids.

the pattern: standing waves on a water surface form Chladni-like nodal
patterns when driven by acoustic sources. classical cymatics extended
to fluid displacement.

adopted from nolangz/3D-Chladni (35*), kl4yfd/Cymatic3D (43*),
PettaBoy/Cymatics-Simulator-Chladni (34*).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class WaterCymaticsGrid:
    """a 3D grid for water displacement simulation.
    x: horizontal, y: depth (into the water), z: vertical (out of the surface)."""

    width: int = 80
    depth: int = 20
    height: int = 80


@dataclass
class WaterCymaticsSim:
    """water-surface standing waves."""

    def __init__(self, grid: WaterCymaticsGrid):
        self.grid = grid
        self.surface = [[0.0] * grid.width for _ in range(grid.height)]
        self.surface_prev = [[0.0] * grid.width for _ in range(grid.height)]  # for leapfrog

    def drive(self, x: int, y: int, freq: float, t: float, amplitude: float = 0.1) -> None:
        """drive the water at (x, y) with a sinusoidal source."""
        if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            self.surface[y][x] += amplitude * math.sin(2 * math.pi * freq * t)

    def step(self, dt: float = 0.01, c: float = 1.0) -> None:
        """one fluid step. leapfrog wave equation.
        u^{n+1} = 2*u^n - u^{n-1} + (c*dt/dx)^2 * Laplacian
        """
        w, h = self.grid.width, self.grid.height
        cfl = (c * dt) ** 2
        new = [[0.0] * w for _ in range(h)]
        for y in range(1, h-1):
            for x in range(1, w-1):
                laplacian = (self.surface[y][x+1] + self.surface[y][x-1] +
                             self.surface[y+1][x] + self.surface[y-1][x] -
                             4 * self.surface[y][x])
                new[y][x] = (2 * self.surface[y][x] - self.surface_prev[y][x] +
                             cfl * laplacian)
        # shift: prev <- curr, curr <- new
        for y in range(h):
            for x in range(w):
                self.surface_prev[y][x] = self.surface[y][x]
                self.surface[y][x] = new[y][x]

    def surface_digest(self) -> str:
        """SHA-256[:16] of the surface state."""
        import hashlib
        flat = []
        for row in self.surface:
            flat.extend(row)
        canonical = "".join(f"{v:.6f}" for v in flat)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


if __name__ == "__main__":
    grid = WaterCymaticsGrid(width=40, height=40, depth=10)
    sim = WaterCymaticsSim(grid)
    sim.drive(20, 20, freq=30.0, t=1.0 / (4 * 30.0))  # sin(2*pi*30*1/120) = sin(pi/2) = 1
    d1 = sim.surface_digest()
    for _ in range(10):
        sim.step()
    d2 = sim.surface_digest()
    assert d1 != d2
    print(f"W1: ok (water cymatics, surface evolved from {d1[:8]} to {d2[:8]})")