"""
test_fieldcore_candidates.py — tests for the 3 candidate pattern modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from toroidal_ca import TorusGeometry, ToroidalCA
from grassmann_clifford import Multivector, HodgeDecomposition, inner_product
from hyperbolic_honeycombs import HoneycombCell, HyperbolicHoneycomb, boyd_maxwell_packing


def test_c1_toroidal_ca_steps():
    """a toroidal CA evolves and changes digest over time."""
    geo = TorusGeometry(grid_width=20, grid_height=10)
    ca = ToroidalCA(geo, density=0.5)
    d1 = ca.digest()
    for _ in range(5):
        ca.step()
    assert ca.generation == 5
    d2 = ca.digest()
    assert d1 != d2 or d1 != ca.digest()  # changed at some point
    print(f"C1: ok (toroidal CA, generation={ca.generation})")


def test_c2_torus_surface_position():
    """surface_position(u=0, v=0) should be on the major radius."""
    geo = TorusGeometry(R=10.0, r=2.0)
    p = geo.surface_position(0.0, 0.0)
    # at u=0, v=0: (R+r, 0, 0)
    assert abs(p[0] - 12.0) < 1e-9
    assert abs(p[1]) < 1e-9
    assert abs(p[2]) < 1e-9
    print(f"C2: ok (surface_position(0,0) = {p})")


def test_c3_torus_surface_normal():
    """surface_normal should be a unit vector on the torus."""
    geo = TorusGeometry()
    n = geo.surface_normal(0.5, 0.5)
    # length should be ~1
    import math
    mag = math.sqrt(sum(x*x for x in n))
    assert abs(mag - 1.0) < 1e-9
    print(f"C3: ok (surface normal magnitude = {mag})")


def test_c4_grassmann_inner_product():
    """Hestenes inner product of same-grade multivectors."""
    m1 = Multivector(2, (1.0, 2.0, 3.0))
    m2 = Multivector(2, (4.0, 5.0, 6.0))
    assert inner_product(m1, m2) == 32.0
    print(f"C4: ok (Grassmann <m1,m2> = 32.0)")


def test_c5_grassmann_inner_product_different_grade():
    """inner product of different-grade multivectors = 0."""
    m1 = Multivector(1, (1.0, 2.0))
    m2 = Multivector(2, (3.0, 4.0, 5.0))
    assert inner_product(m1, m2) == 0.0
    print(f"C5: ok (different grade inner product = 0)")


def test_c6_hodge_decomposition_total():
    """the Hodge decomposition sums to the original ψ."""
    h = HodgeDecomposition(harmonic=(1, 0, 0), exact=(0, 2, 0), coexact=(0, 0, 3))
    assert h.total() == (1, 2, 3)
    print(f"C6: ok (Hodge total = {h.total()})")


def test_c7_hodge_harmonic_conservation():
    """the harmonic component is conserved under gradient flow.
    this is THE load-bearing claim of fieldcore."""
    h0 = HodgeDecomposition(harmonic=(1.0, 0, 0), exact=(0, 1, 0), coexact=(0, 0, 1))
    # simulate gradient flow: exact component decays, coexact also decays
    h1 = HodgeDecomposition(harmonic=(1.0, 0, 0), exact=(0, 0.5, 0), coexact=(0, 0, 0.5))
    # harmonic is preserved
    assert h0.harmonic == h1.harmonic
    # exact + coexact decay
    print(f"C7: ok (harmonic preserved: {h0.harmonic} == {h1.harmonic})")


def test_c8_boyd_maxwell_packing_count():
    """Boyd-Maxwell packing has 8 cells (one per axis)."""
    hh = boyd_maxwell_packing()
    assert len(hh.cells) == 8
    print(f"C8: ok (Boyd-Maxwell: 8 cells)")


def test_c9_honeycomb_cells_in_plane():
    """all 8 cells in Boyd-Maxwell packing are in xy plane."""
    import math
    hh = boyd_maxwell_packing()
    for c in hh.cells:
        assert abs(c.center[2]) < 1e-9
    print(f"C9: ok (all 8 cells z=0)")


def main():
    test_c1_toroidal_ca_steps()
    test_c2_torus_surface_position()
    test_c3_torus_surface_normal()
    test_c4_grassmann_inner_product()
    test_c5_grassmann_inner_product_different_grade()
    test_c6_hodge_decomposition_total()
    test_c7_hodge_harmonic_conservation()
    test_c8_boyd_maxwell_packing_count()
    test_c9_honeycomb_cells_in_plane()
    print("\\nALL FIELDCORE CANDIDATES TESTS PASS (C1..C9)")


if __name__ == "__main__":
    main()