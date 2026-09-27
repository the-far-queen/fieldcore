"""
test_quantum_mimic.py — smoke tests for src/quantum_mimic.py.

Verifies:
  1. Phase arithmetic (add, conjugate, scale, inner)
  2. EntangledPair correlation preserved under measurement
  3. Superposition normalization + observe() collapse
  4. Interference destructive + constructive
  5. WaveField gaussian peak + plane wave intensity

These are stdlib-only tests. No numpy, no scipy.
"""
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
sys.path.insert(0, str(_SRC))

import pytest

from quantum_mimic import (
    Phase,
    EntangledPair,
    Superposition,
    Interference,
    WaveField,
    TWO_PI,
)


# ----------------------------------------------------------------------------
# 1. Phase
# ----------------------------------------------------------------------------

def test_phase_add_same_angle():
    """Phase(1, θ) + Phase(1, θ) = Phase(2, θ)."""
    p1 = Phase(1.0, math.pi / 3)
    p2 = Phase(1.0, math.pi / 3)
    p_sum = p1.add(p2)
    assert abs(p_sum.magnitude - 2.0) < 1e-6
    assert abs(p_sum.angle - math.pi / 3) < 1e-6


def test_phase_add_opposite_angle():
    """Phase(1, θ) + Phase(1, -θ) = Phase(2·cos(θ), 0)."""
    p1 = Phase(1.0, math.pi / 4)
    p2 = Phase(1.0, -math.pi / 4)
    p_sum = p1.add(p2)
    # magnitude = 2·cos(π/4) = √2
    assert abs(p_sum.magnitude - math.sqrt(2)) < 1e-6
    # angle should be 0 (real axis)
    assert abs(p_sum.angle) < 1e-6


def test_phase_conjugate_negates_angle():
    """Phase(magnitude, θ).conjugate() = Phase(magnitude, -θ mod 2π)."""
    p = Phase(1.5, 1.234)
    c = p.conjugate()
    assert abs(c.magnitude - 1.5) < 1e-9
    assert abs(c.angle - (TWO_PI - 1.234)) < 1e-6


def test_phase_inner_product():
    """inner(Phase, Phase) = cos(angle_diff). Range [-1, 1]."""
    p1 = Phase(1.0, 0.0)
    p2 = Phase(1.0, 0.0)
    assert abs(p1.inner(p2) - 1.0) < 1e-9    # aligned
    p3 = Phase(1.0, math.pi)
    assert abs(p1.inner(p3) - (-1.0)) < 1e-9   # anti-aligned
    p4 = Phase(1.0, math.pi / 2)
    assert abs(p1.inner(p4)) < 1e-9          # orthogonal


def test_phase_scale_negative():
    """Phase.scale(-k) flips phase by π (multiplication by negative real)."""
    p = Phase(1.0, 0.0)
    p_neg = p.scale(-2.0)
    assert abs(p_neg.magnitude - 2.0) < 1e-9
    assert abs(p_neg.angle - math.pi) < 1e-6 or abs(p_neg.angle) < 1e-6


# ----------------------------------------------------------------------------
# 2. EntangledPair
# ----------------------------------------------------------------------------

def test_entangled_pair_initial_correlation():
    """create() with conjugate must produce a pair satisfying conjugation."""
    pair = EntangledPair.create(Phase(1.0, 0.7), correlation="conjugate")
    assert pair.correlation_holds()


def test_entangled_pair_measurement_preserves_correlation():
    """After measure_a, the pair still satisfies the declared correlation."""
    pair = EntangledPair.create(Phase(1.0, math.pi / 5), correlation="conjugate")
    pair.measure_a(angle=math.pi / 3)
    assert pair.correlation_holds()
    pair.measure_b(angle=math.pi / 7)
    assert pair.correlation_holds()


def test_entangled_pair_parallel_correlation():
    """parallel correlation: a and b have the same angle after measurement."""
    pair = EntangledPair.create(Phase(1.0, 0.0), correlation="parallel")
    assert pair.correlation_holds()
    pair.measure_a(angle=1.23)
    assert pair.correlation_holds()
    assert abs(pair.p_a.angle - pair.p_b.angle) < 1e-9


def test_entangled_pair_anti_parallel_correlation():
    """anti-parallel: angles differ by π mod 2π."""
    pair = EntangledPair.create(Phase(1.0, 0.5), correlation="anti-parallel")
    assert pair.correlation_holds()
    pair.measure_a(angle=0.7)
    diff = (pair.p_a.angle - pair.p_b.angle) % TWO_PI
    assert abs(diff - math.pi) < 1e-6


def test_entangled_pair_history():
    """measure_a and measure_b both record to history."""
    pair = EntangledPair.create(Phase(1.0, 0.0), correlation="conjugate")
    pair.measure_a(angle=0.1)
    pair.measure_b(angle=0.2)
    pair.measure_a(angle=0.3)
    assert pair.history == [("a", 0.1), ("b", 0.2), ("a", 0.3)]


# ----------------------------------------------------------------------------
# 3. Superposition
# ----------------------------------------------------------------------------

def test_superposition_normalization_sums_to_one():
    """After normalize(), sum of |w|² = 1."""
    sp = Superposition()
    sp.add("a", Phase(1.0, 0.0))
    sp.add("b", Phase(2.0, 0.0))
    sp.add("c", Phase(3.0, 0.0))
    sp.normalize()
    total = sum(p.magnitude ** 2 for p in sp.weights.values())
    assert abs(total - 1.0) < 1e-9


def test_superposition_probability_calculation():
    """probability_of(b) = |w_b|² / Σ|w|²."""
    sp = Superposition()
    sp.add("x", Phase(1.0, 0.0))
    sp.add("y", Phase(1.0, 0.0))
    sp.add("z", Phase(1.0, 0.0))
    # uniform: each = 1/3
    for basis in ("x", "y", "z"):
        assert abs(sp.probability_of(basis) - 1 / 3) < 1e-9
    # add a heavy one
    sp.add("w", Phase(3.0, 0.0))
    # now Σ|w|² = 1+1+1+9 = 12; w_prob = 9/12 = 0.75
    assert abs(sp.probability_of("w") - 0.75) < 1e-9


def test_superposition_observe_collapses_to_one():
    """observe() leaves exactly one basis with weight 1.0, others gone."""
    sp = Superposition()
    sp.add("a", Phase(1.0, 0.0))
    sp.add("b", Phase(1.0, 0.0))
    sp.add("c", Phase(1.0, 0.0))
    sp.normalize()
    collapsed = sp.observe()
    assert collapsed in ("a", "b", "c")
    assert len(sp.weights) == 1
    assert collapsed in sp.weights
    assert abs(sp.weights[collapsed].magnitude - 1.0) < 1e-9
    assert abs(sp.probability_of(collapsed) - 1.0) < 1e-9


def test_superposition_observe_forced_basis():
    """observe(basis_to_force="x") deterministically collapses to x."""
    sp = Superposition()
    sp.add("x", Phase(0.1, 0.0))   # low probability
    sp.add("y", Phase(10.0, 0.0))  # high probability
    sp.normalize()
    collapsed = sp.observe(basis_to_force="x")
    assert collapsed == "x"
    assert len(sp.weights) == 1


def test_superposition_plus_unions_bases():
    """plus() combines two superpositions; overlapping bases sum, others union."""
    a = Superposition(weights={"x": Phase(1.0, 0.0), "y": Phase(1.0, 0.0)})
    b = Superposition(weights={"y": Phase(1.0, math.pi), "z": Phase(1.0, 0.0)})
    combined = a.plus(b)
    assert set(combined.weights.keys()) == {"x", "y", "z"}
    # y weight: Phase(1,0) + Phase(1,π) = Phase(0, 0) — destructive
    assert combined.weights["y"].magnitude < 1e-6


# ----------------------------------------------------------------------------
# 4. Interference
# ----------------------------------------------------------------------------

def test_interference_destructive_and_constructive():
    """Aligning + anti-aligning waves produce 0 and 2 at the right bases."""
    a = Superposition(weights={
        "0": Phase(1.0, 0.0),
        "1": Phase(1.0, 0.0),
        "2": Phase(1.0, 0.0),
    })
    b = Superposition(weights={
        "0": Phase(1.0, math.pi),     # anti-align
        "1": Phase(1.0, 0.0),         # align
        "2": Phase(1.0, math.pi),     # anti-align
    })
    interf = Interference(offset=0.0)
    combined = interf.combine(a, b)
    assert combined.weights["0"].magnitude < 1e-6  # destructive
    assert combined.weights["1"].magnitude > 1.99  # constructive (~2)
    assert combined.weights["2"].magnitude < 1e-6


def test_interference_offset_rotates_b():
    """offset=π/2 should rotate b's angles by π/2 before adding."""
    a = Superposition(weights={"0": Phase(1.0, 0.0)})
    # b[0] = Phase(1, π/3). After offset π/2, becomes Phase(1, π/3+π/2=5π/6).
    # Sum with a[0]=Phase(1, 0): total angle = arg(Phase(1,0)+Phase(1, 5π/6)).
    b = Superposition(weights={"0": Phase(1.0, math.pi / 3)})
    interf = Interference(offset=math.pi / 2)
    combined = interf.combine(a, b)
    # The combined angle is arg of (1·cos(0) + 1·cos(5π/6), 1·sin(0) + 1·sin(5π/6))
    # = atan2(0 + 0.5, 1 + (-√3/2)) = atan2(0.5, ~0.134)
    expected_angle = math.atan2(
        math.sin(0) + math.sin(math.pi / 3 + math.pi / 2),
        math.cos(0) + math.cos(math.pi / 3 + math.pi / 2),
    ) % TWO_PI
    # the combined angle should be close to expected
    assert abs(combined.weights["0"].angle - expected_angle) < 1e-6


def test_interference_fringe_spacing():
    """fringe_spacing returns n_bases values, each in [0, 1]."""
    # wavelength=8 over n_bases=16 means cos(2π·x/8): peaks at x=0,4,8,12
    # and nodes at x=2,6,10,14. Use this so the test sees both peaks
    # and nodes in the same pattern.
    fringe = Interference.fringe_spacing(wavelength=8.0, n_bases=16)
    assert len(fringe) == 16
    assert all(0.0 <= f <= 1.0 + 1e-9 for f in fringe)
    # peak at x=0 (cos²(0)=1), node at x=2 (cos²(π/2)=0)
    assert abs(fringe[0] - 1.0) < 1e-9
    assert abs(fringe[2] - 0.0) < 1e-9
    # next peak at x=4
    assert abs(fringe[4] - 1.0) < 1e-9


# ----------------------------------------------------------------------------
# 5. WaveField
# ----------------------------------------------------------------------------

def test_wave_field_gaussian_peak_at_center():
    """gaussian peak should be at x ≈ center."""
    packet = WaveField.gaussian(n=64, center=32.0, sigma=8.0)
    peak_x = max(range(64), key=lambda x: packet.measure_at(x))
    assert abs(peak_x - 32) <= 1


def test_wave_field_plane_wave_normalized():
    """Plane wave after normalize() has total intensity = 1."""
    wave = WaveField.plane_wave(n=16, k=math.pi)
    wave.normalize()
    total = sum(wave.measure_at(x) for x in range(16))
    assert abs(total - 1.0) < 1e-9


def test_wave_field_to_superposition_roundtrip():
    """to_superposition() preserves the field structure."""
    wave = WaveField.plane_wave(n=8, k=math.pi / 3)
    sp = wave.to_superposition()
    assert set(sp.weights.keys()) == {str(i) for i in range(8)}


def test_wave_field_modulation_by_k():
    """gaussian(..., k=π/2) gives non-zero phases (modulated packet)."""
    p0 = WaveField.gaussian(n=8, center=4.0, sigma=2.0, k=0.0)
    pk = WaveField.gaussian(n=8, center=4.0, sigma=2.0, k=math.pi / 2)
    # at x=5: pk should have phase (k*5) mod 2π ≠ 0
    assert abs(pk.field[5].angle - (math.pi / 2 * 5) % TWO_PI) < 1e-6
    # p0 should have phase 0 everywhere
    for x in range(8):
        assert abs(p0.field[x].angle) < 1e-9