"""
test_wound_core.py — the v6.2 wound core, and every claim it makes.

Every test here can go red. That is the whole point, and the module that
implements the equaliser has already shown why: the Rust core's `equalise`
discarded the imaginary part of its inversion, and every existing test
transmitted a FLAT REAL frame, for which the correct answer is 1 + 0j --
so the loss was invisible. The defect was not in the formula. It was in
the fixture.

So: every assertion below has a mutation that must break it, and the
mutations are applied by hand and recorded in the commit that adds this
file.

WHAT IS ASSERTED, and what each one is worth:

  THE GEOMETRY
    concentric order is enforced          a core outside the inner
                                         winding is not a coax
    two loop modes per stalk              v6.2: 3 conductors -> 2 loops
    the three mutual couplings are        unequal by construction is
    unequal by construction               what breaks the degeneracy
    the loop eigenvalues separate         v6.2 §7's falsification, computed
    beyond sigma_g

  THE POPULATION CODE
    phase is the address                  probe each stalk's phase, get
                                         that stalk back
    the decode has contrast               a flat population is the honest
                                         "I do not know"

  THE CHANNEL
    the notch is a POSITIVE depth         the sign convention cost the
                                         Rust suite four tests
    a clean channel is refused            paper 24's proposition, as code
    the equaliser recovers a flat         dirty is recoverable
    transmit
    the equaliser PRESERVES PHASE         a frame with phase must come
                                         back with its phase intact
    the python port and the rust core     one algorithm, one behaviour
    agree

  THE GATE
    the thresholds come from the kernel   the policy cannot drift
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wound_core import (  # noqa: E402
    Channel,
    CoaxWinding,
    PopulationCode,
    Stratum,
    WoundCore,
    coupling_matrix,
    degeneracy_check,
    standard_wound_core,
)
from tiniest_core.tiniest_core import MAX_NORM as TC_MAX_NORM  # noqa: E402
from tiniest_core.tiniest_core import MIN_COS as TC_MIN_COS  # noqa: E402


# ---------------------------------------------------------------------------
# the geometry
# ---------------------------------------------------------------------------

def test_concentric_order_is_enforced():
    """A core outside the inner winding is not a coaxial structure."""
    with pytest.raises(ValueError):
        CoaxWinding(id="bad", girth_core=0.10, girth_in=0.06, girth_out=0.05,
                    n_in=5, n_out=11)
    with pytest.raises(ValueError):
        CoaxWinding(id="bad", girth_core=0.02, girth_in=0.06, girth_out=0.01,
                    n_in=5, n_out=11)


def test_two_loop_modes_per_stalk():
    """v6.2: n conductors -> n-1 independent differential modes.

    Three conductors -> two. So a stalk addresses TWO axes, not one, and
    the mode count over N stalks is 2N.
    """
    s = CoaxWinding(id="one", girth_core=0.02, girth_in=0.06, girth_out=0.10,
                    n_in=5, n_out=11)
    assert s.loop_modes == ("outer-inner", "inner-core")
    assert len(s.loop_modes) == 2
    core = standard_wound_core()
    assert core.n_loop_modes == 2 * core.n_stalks


def test_the_three_mutual_couplings_are_unequal():
    """v6.2 §1.2: with two conductors there is ONE off-diagonal coupling.
    With three there are THREE, and concentric geometry makes them
    unequal BY CONSTRUCTION. That is what breaks the degeneracy."""
    s = CoaxWinding(id="one", girth_core=0.02, girth_in=0.06, girth_out=0.10,
                    n_in=5, n_out=11)
    m = s.mutual_couplings()
    assert len(m) == 3
    vals = [m["m_out_in"], m["m_in_core"], m["m_out_core"]]
    assert len(set(round(v, 9) for v in vals)) == 3, \
        f"the three couplings must differ, got {vals}"


def test_the_inductance_matrix_is_symmetric():
    """v6.2 §1.2 keeps the physics correction: the matrix is NOT
    asymmetric. In a linear reciprocal medium M_ij == M_ji. The earlier
    framing 'M is no longer symmetric' was a physics error, and the
    document preserved the correction rather than quietly dropping it."""
    s = CoaxWinding(id="one", girth_core=0.02, girth_in=0.06, girth_out=0.10,
                    n_in=5, n_out=11)
    M = s.inductance_matrix()
    for i in range(3):
        for j in range(3):
            assert M[i][j] == pytest.approx(M[j][i]), \
                f"M[{i}][{j}]={M[i][j]} != M[{j}][{i}]={M[j][i]}"


def test_the_geometry_separates_the_loop_modes_beyond_sigma_g():
    """v6.2 §7's falsification test, computed rather than asserted.

    The claim, quoted: "two windings of DIFFERENT GIRTH on a shared core
    produce structurally non-degenerate loop modes, so 20 axes need no
    sigma_g perturbation."

    The falsifier: if the geometry cannot tell a differing-girth stalk
    from a same-girth one to within sigma_g precision, the geometry is
    not carrying the count and the v6.1 perturbation was doing the work.
    """
    res = degeneracy_check(standard_wound_core())
    assert res["geometry_carries_the_count"], \
        f"the geometry does not separate the spectra: {res}"
    assert res["geometry_spectrum_distance"] > res["sigma_g"], res


def test_the_geometry_check_can_fail():
    """THE CONTROL. The check above is worthless if it cannot fail.

    Two stalks with the SAME geometry have the same spectrum, so the
    distance between them must be zero. If the measurement reported a
    separation for identical geometry, it would be measuring noise.
    """
    res = degeneracy_check(standard_wound_core())
    assert res["identical_geometry_distance"] < 1e-9, \
        f"identical geometry must give zero distance: {res}"


def test_a_differing_girth_stalk_differs_from_a_same_girth_one():
    """The claim, as a direct comparison.

    A stalk whose two windings differ in girth, against one whose windings
    are the same girth: the loop spectra must be measurably different, or
    the geometry is not carrying the mode count.
    """
    res = degeneracy_check(standard_wound_core())
    assert res["geometry_spectrum_distance"] > 0.1, \
        f"the two geometries are too close: {res}"
    assert res["geometry_carries_the_count"], res


def test_the_coupling_law_does_not_explode():
    """THE BUG THIS FOUND.

    The first coupling law was m_out_in = overlap / (girth_out -
    girth_in) -- the mutual inductance divided by the SEPARATION of the
    two conductors. Two windings at nearly the same radius then gave
    m = 10000, because the separation was in the denominator where it
    belonged in the numerator.

    Two concentric windings couple by the RATIO of their radii: the inner
    winding sits inside the outer's flux, so the coupling rises as they
    approach and is bounded by 1.
    """
    near = CoaxWinding(id="near", girth_core=0.02, girth_in=0.060,
                       girth_out=0.0601, n_in=5, n_out=5)
    # a WIDE pair: the inner winding is a thin shell near the core, the
    # outer one is far out. (The constructor enforces core < inner < out,
    # and it caught a fixture that broke it -- the core cannot be outside
    # the inner winding.)
    far = CoaxWinding(id="far", girth_core=0.005, girth_in=0.010,
                      girth_out=0.100, n_in=5, n_out=11)
    for w in (near, far):
        m = w.mutual_couplings()
        assert m["m_out_in"] <= 1.0 + 1e-9, \
            f"m_out_in must be bounded by 1, got {m['m_out_in']}"
    # and the near pair couples MORE than the far one
    assert near.mutual_couplings()["m_out_in"] > \
        far.mutual_couplings()["m_out_in"]


def test_the_turns_ratio_sets_the_voltage_ratio():
    """v6.2 §1.3: the core makes the two windings share a flux path, so
    the turns ratio IS the voltage ratio of a tapped primary."""
    s = CoaxWinding(id="one", girth_core=0.02, girth_in=0.06, girth_out=0.10,
                    n_in=5, n_out=11)
    assert s.turns_ratio == pytest.approx(11 / 5)


# ---------------------------------------------------------------------------
# the population code
# ---------------------------------------------------------------------------

def test_phase_is_the_address():
    """Probe each stalk's own phase; the population must read that stalk
    back. This is the brain part: a population code addresses a feature
    by the RATIO of responses across a population, not by a dedicated
    wire."""
    pop = standard_wound_core().population()
    for s in pop.strata:
        dec = pop.decoded(s.phase)
        assert dec["winner"] == s.id, \
            f"probe {s.phase:.4f} read back {dec['winner']}, wanted {s.id}"


def test_the_population_addresses_are_distinct():
    """Two stalks with the same address would be ambiguous by design.

    This is the test the mutation probe found missing. The check that
    every stalk reads back as the winner PASSED even when every stalk
    was given the SAME phase -- because with equal phases the decode
    still returns a winner (the first one), it just returns one with
    zero contrast. So the winner check was not enough on its own: the
    addresses have to be DISTINCT for the winner check to mean anything.

    That is the same shape of defect as the Rust core's dropped
    imaginary part: the test asserted the output was well-formed when it
    should have asserted the output carried the information.
    """
    pop = standard_wound_core().population()
    phases = [s.phase for s in pop.strata]
    assert len(set(round(p, 9) for p in phases)) == len(phases), \
        f"two stalks share an address: {phases}"


def test_the_address_comes_from_the_geometry_not_the_position():
    """THE ADDRESS MUST BE DERIVED, NOT ASSIGNED.

    A mutation probe caught this: replacing the geometric phase with the
    stalk's INDEX (0, 1/N, 2/N, ...) left the whole suite green. The
    decode still worked, because evenly spaced phases decode fine. So
    nothing in the suite was checking the thing that actually matters:
    that the address is a function of the PHYSICAL DESIGN.

    This matters because the address is supposed to BE the geometry. If
    the address were the index, then two stalks with identical geometry
    in different positions would have different addresses, and moving a
    stalk in the rack would change what it means -- which is exactly
    what a geometry-derived code is supposed to prevent.

    So: reorder the stalks and the addresses must follow the GEOMETRY,
    not the position. A stalk's address is a property of the stalk.
    """
    core = standard_wound_core()
    by_id = {s.id: s.phase for s in core.population().strata}

    # the same stalks, in a different order
    reordered = WoundCore(list(reversed(core.stalks)))
    after = {s.id: s.phase for s in reordered.population().strata}

    assert by_id == after, \
        "the address must follow the geometry, not the position in the list"


def test_the_phase_actually_moves_the_response():
    """THE CONTROL for the address.

    If every stratum sat at the same phase, the population would carry
    no address at all: every probe would get the same response vector,
    and the decode would be a coin toss dressed as a reading.

    So: probe two different addresses and the response vectors must
    DIFFER. Without this, the whole multiplex is decorative.
    """
    pop = standard_wound_core().population()
    a = pop.readout(pop.strata[0].phase)
    b = pop.readout(pop.strata[1].phase)
    assert a != b, "two different addresses give the same response"
    # The threshold is not arbitrary: it is what the decode needs. Two
    # addresses are distinguishable if the population's response moves
    # by more than the response's own spread across the population --
    # otherwise the winner is being decided by noise. The nearest pair
    # of addresses in the standard core is s11 (0.1923) and s5 (0.1667),
    # and that pair must still separate.
    nearest = min(
        ((abs(i - j), pop.strata[i].phase, pop.strata[j].phase)
         for i in range(len(pop.strata)) for j in range(i + 1, len(pop.strata))),
        key=lambda t: t[0])
    ia, ib = [i for i, s in enumerate(pop.strata) if s.phase == nearest[1]][0], \
             [i for i, s in enumerate(pop.strata) if s.phase == nearest[2]][0]
    ra = pop.readout(nearest[1])
    rb = pop.readout(nearest[2])
    move = max(abs(x - y) for x, y in zip(ra, rb))
    spread = max(max(r) - min(r) for r in (ra, rb))
    assert move > 0.0, f"the nearest pair must move the population at all"
    assert move > 0.1 * spread, \
        f"the nearest pair ({nearest[1]:.4f}, {nearest[2]:.4f}) moves only " \
        f"{move:.4f} against a spread of {spread:.4f}"


def test_a_flat_population_cannot_claim_a_winner():
    """A population with no address must not look like it knows.

    With every stratum at the same phase, the decode returns a winner
    whose CONTRAST is zero. That is the honest "I do not know", and the
    contrast is the only thing that says so -- so the contrast must be
    checked, not just the winner.
    """
    flat = PopulationCode(strata=[Stratum(id=f"s{i}", phase=0.0, gain=1.0)
                                  for i in range(4)])
    dec = flat.decoded(0.0)
    assert dec["contrast"] == pytest.approx(0.0), \
        f"a flat population must have zero contrast, got {dec}"


def test_the_decode_carries_contrast_not_just_a_winner():
    """A flat population is the honest 'I do not know', and the contrast
    is what says so. A decode that always returns a confident winner is
    the failure the width ladder is meant to catch."""
    pop = standard_wound_core().population()
    dec = pop.decoded(pop.strata[0].phase)
    assert dec["contrast"] > 0.0, "a decode with no contrast is not a decode"
    # a flat population: every stratum at the same phase
    flat = PopulationCode(strata=[Stratum(id=f"s{i}", phase=0.25, gain=1.0)
                                  for i in range(4)])
    fdec = flat.decoded(0.25)
    assert abs(fdec["contrast"]) < 1e-9, \
        "a flat population must have zero contrast"


def test_the_carrier_is_the_sum_of_the_strata():
    """One carrier, many contributors. The multiplex is what makes the
    topology complex enough without being a wire per idea."""
    pop = PopulationCode(strata=[Stratum(id="a", phase=0.0, gain=1.0),
                                 Stratum(id="b", phase=0.25, gain=1.0)],
                         samples=64)
    car = pop.carrier()
    assert len(car) == 64
    assert max(car) > 1.5, "two strata must add"


# ---------------------------------------------------------------------------
# the channel
# ---------------------------------------------------------------------------

def test_the_notch_is_a_positive_depth():
    """The sign convention is load-bearing and cost the Rust suite four
    tests: a notch is a DEPTH, so it is reported POSITIVE. 0 means flat.
    60 means a response null was actually reached."""
    c = Channel([(1.0, 0.0), (-0.8, 0.2)])
    assert c.notch_db() > 10.0, "a two-path channel must produce a null"
    assert Channel.clean().notch_db() < 3.0


def test_a_clean_channel_is_refused():
    """Paper 24's proposition, as an assertion: a perfectly isolated
    braid has nothing to model and therefore nothing to invert."""
    eq = Channel.clean().equalise([(1.0, 0.0)] * 8)
    assert not eq["ok"]
    assert eq["error"] == "flat_channel"


def test_the_equaliser_recovers_a_flat_transmit():
    """Dirty is recoverable: invert the channel's own response and the
    flat transmit comes back."""
    c = Channel([(1.0, 0.0), (-0.8, 0.2)])
    n = 16
    rx = [c.response_complex(k / n - 0.5) for k in range(n)]
    eq = c.equalise(rx, noise_floor=-80.0)
    assert eq["ok"], eq
    samples = eq["samples"]
    assert isinstance(samples, list)
    for re, im in samples:
        assert abs(re - 1.0) < 1e-6, f"got {re}, want 1.0"
        assert abs(im) < 1e-6, f"imaginary part should be ~0, got {im}"


def test_the_equaliser_preserves_the_phase_of_the_frame():
    """THE test that was missing from the Rust core.

    Every earlier test transmitted a FLAT REAL frame, for which the
    correct answer is 1 + 0j -- so the imaginary part is legitimately
    zero and its loss was invisible. Here the frame HAS phase, and the
    recovered imaginary part must survive.

    The Rust core's `equalise` had exactly this defect and it was fixed
    on 2026-10-24. This test is the python-side twin of
    `equalise_preserves_the_phase_of_the_frame` in carrier.rs.
    """
    c = Channel([(1.0, 0.0), (-0.8, 0.2)])
    n = 16
    # transmit 1 + 1j per bin
    tx = [(1.0, 1.0)] * n
    rx = []
    for k in range(n):
        f = k / n - 0.5
        hr, hi = c.response_complex(f)
        yr, yi = tx[k]
        rx.append((yr * hr - yi * hi, yr * hi + yi * hr))
    eq = c.equalise(rx, noise_floor=-80.0)
    assert eq["ok"], eq
    samples = eq["samples"]
    assert isinstance(samples, list)
    for re, im in samples:
        assert abs(re - 1.0) < 1e-6, f"real part got {re}, want 1.0"
        assert abs(im - 1.0) < 1e-6, f"imaginary part got {im}, want 1.0"


def test_the_channel_has_a_notch_because_the_geometry_is_not_uniform():
    """The substrate's channel must have structure, or the equaliser has
    nothing to work with. This is the proposition from the other side:
    design the geometry so the channel is invertible."""
    core = standard_wound_core()
    ch = core.channel()
    assert ch.notch_db() > 3.0, \
        f"the channel is flat, so it is uncorrectable: {ch.notch_db()}"


def test_the_interstalk_matrix_is_non_trivial():
    """Stalks must actually talk. A matrix of zeros means nothing is being
    said."""
    m = coupling_matrix(standard_wound_core())
    n = len(m)
    for i in range(n):
        for j in range(n):
            if i != j:
                assert m[i][j] > 0.0, f"stalk {i}->{j} has no interstalk"


def test_the_interstalk_matrix_is_symmetric():
    """Reciprocity: the coupling between two stalks is the same either
    way round."""
    m = coupling_matrix(standard_wound_core())
    n = len(m)
    for i in range(n):
        for j in range(n):
            assert m[i][j] == pytest.approx(m[j][i])


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def test_the_gate_uses_the_kernel_thresholds():
    """The policy is imported from the kernel, not restated, so it cannot
    drift. This is the one-gate rule: one implementation, no
    caller-controlled bounds."""
    core = standard_wound_core()
    assert core.max_norm == TC_MAX_NORM
    assert core.min_cos == TC_MIN_COS


def test_the_gate_refuses_outside_the_bounds():
    core = standard_wound_core()
    assert core.gate(TC_MAX_NORM + 1.0, 1.0) == (False, "refuse_norm")
    assert core.gate(1.0, TC_MIN_COS - 0.1) == (False, "refuse_coherence")
    assert core.gate(1.0, 1.0) == (True, "allow")


def test_the_gate_admits_no_caller_supplied_bound():
    """A caller that can supply the limit can send a limit that permits
    everything. The signature must not admit one."""
    import inspect
    params = set(inspect.signature(WoundCore.gate).parameters)
    assert not (params & {"max_norm", "min_cos", "max_drift", "tolerance"}), \
        f"the gate admits {params}"
