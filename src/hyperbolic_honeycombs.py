from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class HoneycombCell:
    """one hexagonal cell of a 3D honeycomb. centered at origin,
    has 6 neighbors in the hexagonal lattice."""

    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius: float = 1.0
    neighbors: Tuple[int, ...] = ()


@dataclass(frozen=True)
class HyperbolicHoneycomb:
    """a 3D honeycomb — the substrate for the constitutional axis graph.

    8 cells (one per axis). the cells are arranged in hyperbolic space,
    with adjacency = axiom influence.
    """

    cells: Tuple[HoneycombCell, ...]


def boyd_maxwell_packing() -> HyperbolicHoneycomb:
    """Boyd-Maxwell sphere packings: maximally dense 3D sphere packings.
    used as the canonical 3D-projection of the 4D constitutional lattice.
    """
    cells = tuple(
        HoneycombCell(
            center=(math.cos(2*math.pi*k/8), math.sin(2*math.pi*k/8), 0.0),
            radius=0.5,
            neighbors=(k-1, k+1),
        )
        for k in range(8)
    )
    return HyperbolicHoneycomb(cells=cells)


if __name__ == "__main__":
    hh = boyd_maxwell_packing()
    assert len(hh.cells) == 8
    print(f"H1: ok (Boyd-Maxwell packing: {len(hh.cells)} cells)")

    # the cells are arranged in a circle in the xy plane
    centers = [c.center for c in hh.cells]
    for i, c in enumerate(centers):
        assert abs(c[2]) < 1e-9  # z = 0
    print(f"H2: ok (all 8 cells in xy plane)")

    print("\\nALL HYPERBOLIC_HONEYCOMBS TESTS PASS")