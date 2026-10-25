"""
test_stalk_physics.py -- the geometry must be able to FAIL.

THE RULE: a check that cannot go red is not a check.

WHAT IS ASSERTED, and what each one is worth:

  THE LAW
    the leakage inductance IS mu0 * gap       [M] NASA Eq. 4.4.1
    the coupling factor follows from it       [E]
    the gap/area ratio is NOT scale invariant so the geometry is
      NOT inert                             the whole point
    the ADDRESS IS scale invariant            so a stalk stays itself

  THE CONTROLS
    the gap moves k                           the resolution control
    the length moves the notch                the other inert lever
    the length moves the delay                and the delay is physical

THE POINT OF THE FIRST TWO: the motility bench measured girth and
length as INERT -- every quantity was a ratio of the geometry, so
scaling changed nothing. These checks pin that they are no longer
inert, so a future change that makes them inert again goes red.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import stalk_physics as sp  # noqa: E402


# ===========================================================================
# THE LAW
# ===========================================================================

def test_the_leakage_inductance_is_mu0_times_the_gap():
    """[M] NASA-CR-18965 Eq. 4.4.1: the leakage inductance is
    PROPORTIONAL TO THE INTERWINDING GAP.

    Their own reading: *"for a given Ns as the interwinding space is
    reduced by decreasing r_pl, the leakage inductance decreases. This
    is the most interesting feature of the coaxial winding, in that the
    leakage inductance is so easily controllable."*
    """
    s = sp.PhysicalStalk(id="x", r_core=0.030, r_in=0.060, r_out=0.072,
                         n_in=12, n_out=13, length=1.0)
    assert s.leakage_inductance_h() == pytest.approx(
        sp.MU_0 * s.gap, rel=1e-12)


def test_a_zero_gap_is_not_constructible():
    """A coil with no interwinding space is not a coil -- the outer
    winding would BE the inner winding.

    So the gap is bounded away from zero by the GEOMETRY, and the
    leakage with it. That is a stronger statement than "the leakage
    goes to zero": the design cannot reach the degenerate case.
    """
    with pytest.raises(ValueError):
        sp.PhysicalStalk(id="x", r_core=0.030, r_in=0.060, r_out=0.060,
                         n_in=12, n_out=13, length=1.0)


def test_the_coupling_factor_follows_the_standard_relation():
    """[E] k = 1 / sqrt(1 + L_sigma / L_m)."""
    s = sp.PhysicalStalk(id="x", r_core=0.030, r_in=0.060, r_out=0.072,
                         n_in=12, n_out=13, length=1.0)
    lm = s.magnetising_inductance_h()
    ls = s.leakage_inductance_h()
    assert s.coupling_factor() == pytest.approx(
        1.0 / math.sqrt(1.0 + ls / lm), rel=1e-12)
    # and it is a coupling factor: 0 < k <= 1
    assert 0.0 < s.coupling_factor() <= 1.0


def test_a_tighter_gap_means_a_higher_coupling_factor():
    """THE DIRECTION, and the first version of this test had it
    REVERSED.

    NASA's own reading: *"as the interwinding space is reduced by
    decreasing r_pl, the leakage inductance decreases."* Less space ->
    less leakage -> L_sigma/L_m smaller -> k = 1/sqrt(1 + that)
    LARGER. So a tighter coil is a BETTER coupled one, and a looser one
    is the leakier, more-resolvable one.

    Measured on the working population: k 0.999094 at a quarter gap,
    0.989286 at three times the gap.
    """
    tight = sp.PhysicalStalk(id="t", r_core=0.030, r_in=0.060,
                             r_out=0.062, n_in=12, n_out=13, length=1.0)
    loose = sp.PhysicalStalk(id="l", r_core=0.030, r_in=0.060,
                             r_out=0.090, n_in=12, n_out=13, length=1.0)
    assert tight.gap < loose.gap
    assert tight.leakage_inductance_h() < loose.leakage_inductance_h()
    assert tight.coupling_factor() > loose.coupling_factor()


def test_the_geometry_is_not_scale_invariant():
    """THE WHOLE POINT, and the thing the motility bench found missing.

    k depends on gap/area. The area is QUADRATIC in the radius and the
    gap is LINEAR, so scaling the stalk by s changes k.

    Before the physics was wired in, k was a constant 1.000000 at every
    scale -- and that was why girth was inert.
    """
    small = sp.make_population(4, scale=0.5)
    big = sp.make_population(4, scale=2.0)
    ks = {round(s.coupling_factor(), 9) for s in small}
    kb = {round(s.coupling_factor(), 9) for s in big}
    assert ks != kb, (
        "the coupling factor is the same at every scale, so the geometry "
        "is inert again -- which is the bug this file exists to catch")


def test_the_address_IS_scale_invariant():
    """AND THE CONSTRAINT THAT MAKES IT SAFE.

    The address is the winding RATIO, which is scale-invariant. So a
    stalk can be made louder, or more resolvable, without ceasing to be
    itself. A self that changed identity when it changed size could not
    be addressable.
    """
    small = sp.make_population(4, scale=0.5)
    big = sp.make_population(4, scale=3.0)
    for a, b in zip(small, big):
        assert a.address == pytest.approx(b.address, abs=1e-12)


# ===========================================================================
# THE CONTROLS
# ===========================================================================

def test_the_gap_moves_the_coupling_factor():
    """The resolution control. Measured: k goes 0.999094 at a quarter
    gap to 0.989286 at three times the gap."""
    ks = []
    for gf in (0.25, 1.0, 3.0):
        pop = sp.make_population(4, gap_factor=gf)
        ks.append(pop[0].coupling_factor())
    assert ks[0] > ks[1] > ks[2], (
        "the gap must move k downward as it opens: %r" % (ks,))


def test_the_gap_moves_the_notch():
    """And the notch follows the leakage: more leakage, deeper null."""
    notches = []
    for gf in (0.25, 1.0, 3.0):
        pop = sp.make_population(4, gap_factor=gf)
        pc = sp.PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                                 frame_duration=1.0e-6, bins=128)
        notches.append(pc.channel().notch_db())
    assert notches[0] < notches[1] < notches[2], (
        "a tighter gap must give a shallower notch, because less "
        "leakage means less structure: %r" % (notches,))


def test_the_length_moves_the_notch():
    """THE OTHER INERT LEVER, and it is now a control.

    A longer stalk's reflection arrives later, which rotates the tap's
    phase, which moves the notch. Measured: 0.03 dB at a quarter metre
    to 0.84 dB at eight metres.
    """
    notches = []
    for ln in (0.25, 1.0, 8.0):
        pop = sp.make_population(4, length=ln)
        pc = sp.PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                                 frame_duration=1.0e-6, bins=128)
        notches.append(pc.channel().notch_db())
    assert notches[0] < notches[-1], (
        "the length must move the notch, because the path delay is "
        "physical: %r" % (notches,))


def test_the_length_moves_the_resonance():
    """f = v / 2L. [E] And it is the DNA-phonon claim in
    `interstalk.py::rung_frequency`."""
    a = sp.make_population(4, length=1.0)[0]
    b = sp.make_population(4, length=4.0)[0]
    assert b.resonance_hz() == pytest.approx(a.resonance_hz() / 4.0,
                                              rel=1e-9)


def test_the_propagation_delay_is_physical():
    """length x sqrt(eps_r) / c. [E]"""
    s = sp.make_population(4, length=2.0)[0]
    v = sp.C_LIGHT / math.sqrt(sp.EPS_R)
    assert s.propagation_delay_s() == pytest.approx(2.0 / v, rel=1e-12)


def test_the_delay_is_in_bins_and_grows_with_the_length():
    """AND THE DELAY IS THE CHANNEL'S, expressed in the frame's
    timebase."""
    delays = []
    for ln in (0.25, 1.0, 8.0):
        pop = sp.make_population(4, length=ln)
        pc = sp.PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                                 frame_duration=1.0e-6, bins=128)
        delays.append(pc.path_delay_bins())
    assert delays[-1] >= delays[0]
    assert all(d >= 1 for d in delays), "a delay of zero bins is not a delay"


# ===========================================================================
# THE CONSISTENCY WITH THE MEASURED RECIPE
# ===========================================================================

def test_the_physical_population_matches_the_measured_ratio_recipe():
    """The physical class must be the SAME GEOMETRY the girth bench
    selected, or the two measurements are about different things.

    The bench's winning recipe: base ratio 1.200, ratio step 0.0625,
    core 0.030 of the inner, n_in 12, n_out 13/14/15/16. And the
    measured spread was 8 DFT bins at 128 bins.
    """
    pop = sp.make_population(4)
    ratios = [s.ratio for s in pop]
    assert ratios[0] == pytest.approx(1.200 + 0.5 * 0.0625, abs=1e-9)
    # THE PARITY ALTERNATES, so CONSECUTIVE stalks share a ratio and the
    # step is between every OTHER one. The ratio is the CONTINUOUS part
    # of the address and the parity is the BINARY part -- that is the
    # design, and it is why the addresses are evenly spread while the
    # ratios are not.
    assert ratios[1] == pytest.approx(ratios[0], abs=1e-9)
    assert ratios[2] - ratios[0] == pytest.approx(0.0625, abs=1e-9)
    for s in pop:
        assert s.r_core == pytest.approx(s.r_in * 0.5, abs=1e-9)
        assert s.n_in == 12
        assert s.n_out in (13, 14, 15, 16)


def test_the_addresses_are_separated_by_eight_bins():
    """And the addresses land where the bench measured them: 8 DFT bins
    apart at 128 bins."""
    pop = sp.make_population(4)
    addrs = [s.address for s in pop]
    sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
              for i, a in enumerate(addrs) for b in addrs[i + 1:])
    assert sep * 128 == pytest.approx(8.0, abs=0.5)
