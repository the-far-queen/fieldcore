"""
test_em_cymatics.py — tests for the 3 EM/cymatics/harmonic modules.
"""

from __future__ import annotations

import math

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from cymathics import ChladniPlate, ChladniSimulator
from fdtd_1d import FDTD1D
from harmonic_engine import (
    TeslaHarmonic, generate_harmonics, f137, COUPLING_HZ, is_in_tesla_series,
    digital_root, TESLA_BASE,
)


def test_e1_chladni_mode():
    """a Chladni mode has nodal lines."""
    plate = ChladniPlate(width=80, height=80)
    sim = ChladniSimulator(plate, m=4, n=7)
    d = sim.displacement(0.0)
    assert len(d) == plate.height
    assert all(len(row) == plate.width for row in d)
    nodes = sim.nodal_lines(0.0)
    assert nodes > 0
    print(f"E1: ok (Chladni mode (4,7): {nodes} nodal lines)")


def test_e2_chladni_time_evolution():
    """the eigenmode oscillates. check at t=0 and t=pi/(2*omega)."""
    plate = ChladniPlate(width=50, height=50)
    sim = ChladniSimulator(plate, m=3, n=5)
    omega = plate.mode(3, 5)
    d0 = sim.displacement(0.0)
    d_half = sim.displacement(math.pi / (2 * omega))
    # the half-period should be close to zero (cos(pi/2) ~ 0)
    center0 = d0[25][25]
    center_half = d_half[25][25]
    assert abs(center_half) < abs(center0)
    print(f"E2: ok (Chladni oscillates: center={center0:.4f} -> {center_half:.4f})")


def test_e3_fdtd_pulse_propagates():
    """a 1D FDTD Gaussian pulse propagates after a few steps."""
    fd = FDTD1D(n_points=100)
    E, H = fd.gaussian_pulse()
    E0 = [e for e in E]  # copy
    for _ in range(5):
        E, H = fd.step(E, H)
    # the field should have changed
    assert any(abs(E[i] - E0[i]) > 1e-6 for i in range(len(E)))
    print(f"E3: ok (1D FDTD: pulse propagated after 5 steps)")


def test_e4_fdtd_cfl_dt():
    """CFL dt = dx / (2c). default c=1, so dt=dx/2."""
    fd = FDTD1D(n_points=10, c=1.0)
    assert abs(fd.cfl_dt(dx=1.0) - 0.5) < 1e-9
    assert abs(fd.cfl_dt(dx=2.0) - 1.0) < 1e-9
    print(f"E4: ok (CFL dt = dx/(2c))")


def test_e5_tesla_harmonic_series():
    """the 3-6-9 series contains 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60."""
    for f in (3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60):
        assert is_in_tesla_series(float(f)), f"{f} should be in series"
    print(f"E5: ok (Tesla 3-6-9 series: 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60 all in)")


def test_e6_tesla_137_not_in_series():
    """137 is NOT in the 3-6-9 series (137 = 9*15 + 2, not divisible by 3)."""
    assert not is_in_tesla_series(137.0)
    assert is_in_tesla_series(135.0)  # 9*15 IS
    print(f"E6: ok (137 NOT in series, 135 IS)")


def test_e7_digital_root():
    """digital_root is the mod-9 closure."""
    assert digital_root(9) == 9
    assert digital_root(18) == 9
    assert digital_root(12345) == 6  # 1+2+3+4+5=15=1+5=6
    assert digital_root(0) == 0
    print(f"E7: ok (digital_root 9=9, 18=9, 12345=6, 0=0)")


def test_e8_generate_harmonics_loads_meanings():
    """the harmonic series includes specific biological meanings."""
    hs = generate_harmonics(max_n=20)
    by_freq = {h.frequency: h for h in hs}
    # f30 = "neural resonance / schumann proxy"
    assert "neural" in by_freq[30.0].meaning.lower()
    # f42 = "cellular resonance"
    assert "cellular" in by_freq[42.0].meaning.lower()
    # f54 = "DNA resonance"
    assert "dna" in by_freq[54.0].meaning.lower()
    # f144 = "complete cycle"
    assert "cycle" in by_freq[144.0].meaning.lower()
    print(f"E8: ok (meanings: 30Hz=neural, 42Hz=cellular, 54Hz=DNA, 144Hz=cycle)")


def test_e9_f137_is_withdrawn_not_load_bearing():
    """The f137 = 1/alpha claim was WITHDRAWN, deliberately.

    `harmonic_engine.py` says why in its own docstring: alpha is a
    DIMENSIONLESS COUPLING CONSTANT, not a frequency, and 137 is not in
    the 3-6-9 series the constitutional axes run on. Coupling moved to
    37 Hz on 2026-10-06.

    This test used to assert the withdrawn claim -- that f137 is
    load-bearing as the fine-structure constant -- so it failed the
    moment the source was corrected. That is the test being stale, not
    the source being wrong: correcting a false claim should be allowed
    to break the test that asserted it.

    What is asserted now is that the withdrawal STICKS. If someone
    reinstates the claim, this goes red, which is the correct direction.
    """
    h = f137()
    assert h.frequency == 137.0
    assert "withdrawn" in h.meaning.lower(), h.meaning
    assert "fine-structure" not in h.meaning.lower(), (
        f"the withdrawn claim has been reinstated: {h.meaning}")
    # 137 is not in the 3-6-9 series, which is the stated reason
    assert 137 % 3 != 0 and 137 % 6 != 0 and 137 % 9 != 0
    # the substrate's actual coupling frequency
    assert abs(COUPLING_HZ - 37.0) < 1e-9


def main():
    test_e1_chladni_mode()
    test_e2_chladni_time_evolution()
    test_e3_fdtd_pulse_propagates()
    test_e4_fdtd_cfl_dt()
    test_e5_tesla_harmonic_series()
    test_e6_tesla_137_not_in_series()
    test_e7_digital_root()
    test_e8_generate_harmonics_loads_meanings()
    test_e9_f137_load_bearing()
    print("\\nALL EM+CYMATICS+HARMONIC TESTS PASS (E1..E9)")


if __name__ == "__main__":
    main()