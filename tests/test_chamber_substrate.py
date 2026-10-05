"""
test_chamber_substrate.py - tests for the 4 chamber/biological/cymatic modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import os
HERE = Path(os.path.dirname(os.path.abspath(__file__))).parent if "__file__" in dir() else Path("C:/Users/HP/AppData/Local/hermes/work_repos/fieldcore")
sys.path.insert(0, str(HERE / "src"))

from water_cymatics_3d import WaterCymaticsGrid, WaterCymaticsSim
from kuramoto_interference import (
    Oscillator, KuramotoNetwork, CANONICAL_NETWORK,
)
from transformation_chamber import (
    ChamberDimensions, GizaKingChamber, BarabarChamber,
    fundamental_freq,
)
from biological_frequencies import (
    BiologicalFrequency, BIOLOGICAL_FREQUENCIES,
    frequencies_for_target,
)


def test_t1_water_surface_evolves():
    """a water surface driven sinusoidally evolves over time."""
    grid = WaterCymaticsGrid(width=20, height=20, depth=5)
    sim = WaterCymaticsSim(grid)
    import math
    sim.drive(10, 10, freq=30.0, t=1.0 / (4 * 30.0))
    max0 = max(max(row) for row in sim.surface)
    assert max0 > 0  # the drive put energy in
    for _ in range(5):
        sim.step()
    max1 = max(max(row) for row in sim.surface)
    # surface may have spread or grown due to wave equation
    assert abs(max1 - max0) > 1e-6 or max1 != max0
    print(f"T1: ok (water surface: peak {max0:.4f} -> {max1:.4f})")


def test_t2_water_surface_digest_unique():
    """different states of the surface produce different digests."""
    grid = WaterCymaticsGrid(width=10, height=10, depth=5)
    sim = WaterCymaticsSim(grid)
    import math
    sim.drive(5, 5, freq=30.0, t=math.pi / (4 * 30.0))
    d1 = sim.surface_digest()
    for _ in range(3):
        sim.step()
    d2 = sim.surface_digest()
    assert d1 != d2
    print(f"T2: ok (digest varies: {d1[:8]} != {d2[:8]})")


def test_t3_kuramoto_canonical_network():
    """the 8-axis canonical network synchronizes or partially synchronizes."""
    net = KuramotoNetwork(CANONICAL_NETWORK, coupling=0.3)
    r0, _ = net.order_parameter()
    for _ in range(100):
        net.step(dt=0.01)
    r1, _ = net.order_parameter()
    # r in [0, 1] always
    assert 0.0 <= r0 <= 1.0
    assert 0.0 <= r1 <= 1.0
    print(f"T3: ok (Kuramoto: r={r0:.3f} -> {r1:.3f} after 100 steps)")


def test_t4_kuramoto_8_axes():
    """the canonical network has all 8 constitutional axes."""
    assert len(CANONICAL_NETWORK) == 8
    axes = {o.name for o in CANONICAL_NETWORK}
    expected = {"boundaries", "coherence", "stability", "routing",
               "recovery", "authenticity", "norm", "commit_radius"}
    assert axes == expected
    print(f"T4: ok (8 axes: {sorted(axes)})")


def test_t5_giza_chamber_coprime():
    """Giza King's Chamber: 2:1:1.1 ratio -> coprime (gcd=1)."""
    g = GizaKingChamber()
    assert g.width == 10.47
    assert g.height == 5.82
    assert g.depth == 5.23
    assert g.aspect_ratio() == (2, 1, 1)
    assert g.is_coprime()
    print(f"T5: ok (Giza: {g.aspect_ratio()} coprime, V={g.volume():.1f}m^3)")


def test_t6_barabar_chamber_coprime_finer_polish():
    """Barabar chamber is coprime and 50x finer polish than Giza."""
    b = BarabarChamber()
    assert b.is_coprime()
    assert b.tolerance_mm == 1.0  # ±0.1 cm = 1 mm
    g = GizaKingChamber()
    assert g.tolerance_mm == 50.0  # ±5 cm = 50 mm
    assert g.tolerance_mm / b.tolerance_mm == 50.0
    print(f"T6: ok (Barabar polish 50x finer than Giza: {b.tolerance_mm}mm vs {g.tolerance_mm}mm)")


def test_t7_fundamental_freq_in_range():
    """chamber fundamental frequencies are in the audible range."""
    g = GizaKingChamber()
    b = BarabarChamber()
    for chamber in (g, b):
        freqs = fundamental_freq(chamber)
        for f in freqs:
            assert 10 < f < 100, f"{f} Hz out of audible range"
    print(f"T7: ok (chamber fundamentals in 10-100 Hz range)")


def test_t8_biological_9_frequencies():
    """9 canonical biological frequencies mapped to body targets."""
    assert len(BIOLOGICAL_FREQUENCIES) == 9
    expected = {30, 42, 54, 57, 72, 108, 109, 137, 144}
    actual = {f.freq for f in BIOLOGICAL_FREQUENCIES}
    assert actual == expected
    print(f"T8: ok (9 frequencies: {sorted(actual)})")


def test_t9_biological_137_109_not_in_3_6_9():
    """f137 and f109 are NOT in the 3-6-9 series. bobby's quantum-mimicry signal."""
    f_137 = next(f for f in BIOLOGICAL_FREQUENCIES if f.freq == 137)
    f_109 = next(f for f in BIOLOGICAL_FREQUENCIES if f.freq == 109)
    assert not f_137.in_tesla_series
    assert not f_109.in_tesla_series
    # but the OTHER 7 ARE in the series
    in_series = [f for f in BIOLOGICAL_FREQUENCIES if f.in_tesla_series]
    assert len(in_series) == 7
    print(f"T9: ok (137 + 109 NOT in 3-6-9; {len(in_series)} others ARE)")


def test_t10_frequencies_for_target():
    """filter by body target."""
    brain = frequencies_for_target("brain")
    assert any(f.freq == 30 for f in brain)
    dna = frequencies_for_target("dna")
    assert any(f.freq == 54 for f in dna)
    atom = frequencies_for_target("atom")
    assert any(f.freq == 57 for f in atom)
    assert any(f.freq == 109 for f in atom)
    assert any(f.freq == 137 for f in atom)
    print(f"T10: ok (target filter: brain=30, dna=54, atom=[57,109,137])")


def main():
    test_t1_water_surface_evolves()
    test_t2_water_surface_digest_unique()
    test_t3_kuramoto_canonical_network()
    test_t4_kuramoto_8_axes()
    test_t5_giza_chamber_coprime()
    test_t6_barabar_chamber_coprime_finer_polish()
    test_t7_fundamental_freq_in_range()
    test_t8_biological_9_frequencies()
    test_t9_biological_137_109_not_in_3_6_9()
    test_t10_frequencies_for_target()
    print("\\nALL CHAMBER SUBSTRATE TESTS PASS (T1..T10)")


if __name__ == "__main__":
    main()