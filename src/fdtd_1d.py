"""
fdtd_1d.py — 1D Finite-Difference Time-Domain Maxwell solver.

the pattern: discretize Maxwell's equations on a 1D grid. update E and H
fields by leapfrog integration. apply a source. observe the wave propagation.

bobby's load-bearing: FDTD IS fieldcore's EM substrate. every wave propagation
in simself runs through FDTD. the curl equations are the differential operators.

adopted from NanoComp/meep (1,784 stars - canonical FDTD),
flaport/fdtd (724 stars), ymahlau/fdtdx (357 stars, JAX).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class FDTD1D:
    """a 1D FDTD simulator for Maxwell's equations.

    discretization:
      E[i] is at integer grid points.
      H[i] is at half-integer (Yee lattice).
      dt = dx / (2 * c) (CFL condition).
    """
    n_points: int = 200
    c: float = 1.0  # speed of light (normalized)

    def cfl_dt(self, dx: float = 1.0) -> float:
        return dx / (2.0 * self.c)

    def step(self, E: List[float], H: List[float]) -> Tuple[List[float], List[float]]:
        """one FDTD time step. leapfrog E and H updates (Yee lattice).
        H at half-integer points i+1/2: H[i] couples E[i] and E[i+1].
        E at integer points i: E[i] couples H[i-1] and H[i].
        """
        n = len(E)
        m = len(H)
        assert m == n - 1, f"H must be n-1 (E has {n}, H has {m})"

        # update H[i] using E[i] (left) and E[i+1] (right)
        new_H = [0.0] * m
        for i in range(m):
            new_H[i] = H[i] + 0.5 * (E[i+1] - E[i])

        # update E[i] using H[i-1] (left) and H[i] (right)
        new_E = [0.0] * n
        for i in range(n):
            h_left = H[i-1] if i >= 1 else 0.0
            h_right = H[i] if i < m else 0.0
            new_E[i] = E[i] + 0.5 * (h_left - h_right)

        return (new_E, new_H)

    def gaussian_pulse(self, center: int = 50, width: int = 10) -> Tuple[List[float], List[float]]:
        """initial Gaussian pulse in E."""
        E = [math.exp(-((i - center) ** 2) / (2 * width ** 2)) for i in range(self.n_points)]
        H = [0.0] * (self.n_points - 1)
        return (E, H)


if __name__ == "__main__":
    fd = FDTD1D(n_points=100)
    E, H = fd.gaussian_pulse()
    assert len(E) == 100 and len(H) == 99
    # run 2 steps (the leapfrog needs E -> H -> E -> H to propagate)
    for _ in range(2):
        E, H = fd.step(E, H)
    # after 2 steps the pulse should have moved
    n = len(E)
    original = [math.exp(-((i - 50) ** 2) / (2 * 10 ** 2)) for i in range(n)]
    assert any(abs(E[i] - original[i]) > 1e-6 for i in range(n)), "pulse did not move"
    print("F1: ok (1D FDTD: pulse propagated after 2 steps)")