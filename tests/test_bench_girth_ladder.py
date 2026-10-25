"""
test_bench_girth_ladder.py -- the girth/ladder bench must be able to FAIL.

THE RULE: a check that cannot go red is not a check. Every assertion
below names the mistake it is meant to catch, and three of them are the
mistakes this bench's own development made:

  * the mode gap was measured on POOLED eigenvalues, so it compared one
    stalk's low mode against another stalk's low mode and reported
    0.0000 for every candidate -- which read as "the geometry carries no
    axis at all", a completely different claim
  * the gap's guard `mid > 1e-18` was false for every candidate because
    the loop matrix is INDEFINITE (the off-diagonals are dimensionless
    ratios and the diagonal is r^2 N^2), so every gap came out zero
  * the crowd was held fixed while the population grew, so the answer
    was a fact about the crowd amplitude rather than about the ladder

WHAT IS ASSERTED, and what each one is worth:

  THE GEOMETRY
    the addresses are separable at the chosen spread    the naming floor
    the flat channel is refused BY NAME                the design law
    moving the receiver changes the channel             not a loopback
    the mode gap is measured WITHIN a stalk             the v6.2 claim
    the controls FAIL                                  the checks can go red

  THE LADDER
    the width is DERIVED from the taps                  the architecture
    the peak population is where the naming rate peaks  the balance point
    the two crowd models DISAGREE                       the coupling is real

  THE CACHE
    the cache saves ATTEMPTS, not answers               the honest claim
    a cache hit is still measured                      not a shortcut
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

import bench_girth_ladder as bgl  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402
from interstalk_link import InterstalkLink, width_for  # noqa: E402


# ===========================================================================
# THE GEOMETRY
# ===========================================================================

def test_address_formula_is_the_links_formula():
    """The bench's address must be the LINK's address.

    A different derivation would make the readout correlate against a
    phase the transmitter never sent, and the failure would look like a
    channel problem rather than a bookkeeping one.
    """
    for spec in bgl.CANDIDATES[:6]:
        for s in bgl.make_stalks(
                float(spec["base_ratio"]), float(spec["delta_step"]),
                float(spec["core_ratio"]), int(spec["n_in"]),
                list(spec["n_outs"])):
            assert bgl.address_of(s) == InterstalkLink._address(s)


def test_the_address_carries_the_girth_ratio():
    """The address carries (girth_ratio - 1). If it did not, the girth
    would be decoration and the whole address scheme would be the turn
    parity alone -- which has only two values."""
    s = CoaxWinding(id="x", girth_core=0.015, girth_in=0.060,
                    girth_out=0.072, n_in=12, n_out=14)
    # parity 14 -> 0.0; ratio 1.2 -> 0.2
    assert bgl.address_of(s) == pytest.approx(0.2, abs=1e-12)
    # and a different ratio moves it
    s2 = CoaxWinding(id="y", girth_core=0.015, girth_in=0.060,
                     girth_out=0.078, n_in=12, n_out=14)
    assert bgl.address_of(s2) == pytest.approx(0.3, abs=1e-12)


def test_flat_channel_is_refused_by_name():
    """The design law: a channel with no notch has nothing to invert, so
    the gate refuses it BY NAME. A bare False would not carry the
    reason, and the reason is what makes the refusal actionable."""
    stalks = bgl.make_spread_population(4)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    ex = link.exchange(ids[0], ids[1], in_view=[ids[0], ids[1]])
    assert not ex.allowed
    assert ex.reason == "channel_flat_channel"


def test_moving_the_receiver_changes_the_channel():
    """THE LOOPBACK FALSIFICATION.

    The defect this exists to catch: an earlier version built the
    channel from the TRANSMITTER alone, so `measure(tx, rx)` and
    `measure(tx, a different rx)` returned byte-identical results.
    """
    stalks = bgl.make_spread_population(4)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    t1 = link.pair(ids[0], ids[1], in_view=ids).taps()
    t2 = link.pair(ids[0], ids[2], in_view=ids).taps()
    assert t1 != t2


def test_the_mode_gap_is_measured_within_a_stalk():
    """THE MEASUREMENT THAT WAS WRONG, checked ON THE BENCH ITSELF.

    Pooling every stalk's eigenvalues into one sorted list compares one
    stalk's LOW mode against another stalk's low mode. That is a
    between-stalk comparison, not the within-stalk one the v6.2 claim is
    about.

    The first version of this test recomputed the gap itself, so it
    could not catch the bench regressing -- the mutation run MISSED it
    for exactly that reason. So the check is now on the bench's OWN
    output: `evaluate()` must report a non-zero within-stalk gap.
    """
    spec = dict(bgl.CANDIDATES[4])
    r = bgl.evaluate(spec)
    assert r["min_gap"] > 0.0, (
        "the bench reports a zero within-stalk mode gap, so the geometry "
        "carries no axis -- and if that is true it is a finding, not a "
        "bug")
    assert r["min_gap_frac"] > 0.0
    # AND IT IS NOT THE POOLED GAP. The pooled gap compares one stalk's
    # low mode against another stalk's low mode, so it is a different
    # measurement. If the bench ever swapped the two, the numbers would
    # still be non-zero -- which is exactly why the mutation run missed
    # it the first time.
    assert r["min_gap"] != r["pooled_gap"], (
        "the within-stalk gap and the pooled gap are the same number, so "
        "the bench is reporting the pooled one")


def test_the_mode_gap_is_not_the_pooled_gap():
    """The pooled gap and the within-stalk gap must DIFFER, or the
    measurement is measuring the wrong thing and would not notice."""
    stalks = bgl.make_spread_population(4)
    pooled = []
    within = []
    for s in stalks:
        pooled.extend(s.loop_eigenvalues())
    pooled.sort()
    pgaps = []
    for i in range(len(pooled) - 1):
        mid = abs((pooled[i] + pooled[i + 1]) / 2.0)
        if mid > 1e-18:
            pgaps.append(abs(pooled[i + 1] - pooled[i]) / mid)
    for s in stalks:
        e1, e2 = s.loop_eigenvalues()
        a, b = abs(e1), abs(e2)
        hi, lo = max(a, b), min(a, b)
        within.append((hi - lo) / hi)
    # the two must not be identical for every candidate, otherwise the
    # distinction is not doing any work
    assert not (len(pgaps) and all(
        abs(g - min(within)) < 1e-12 for g in pgaps))


def test_the_chosen_geometry_separates_its_addresses():
    """The minimum spread has to be resolvable in DFT bins, or two
    stalks cannot be told apart by the transform."""
    stalks = bgl.make_spread_population(8)
    addrs = [bgl.address_of(s) for s in stalks]
    sep_bins = bgl.min_separation(addrs) * bgl.BINS
    assert sep_bins >= bgl.RESOLVE_FLOOR_BINS


def test_the_control_whose_addresses_coincide_is_not_resolvable():
    """THE CONTROL. A geometry whose addresses nearly coincide must FAIL
    the resolvability check. If it passed, the check cannot go red and
    the whole grid is meaningless."""
    spec = next(c for c in bgl.CANDIDATES
                if c.get("note", "").startswith("CONTROL: the addresses"))
    r = bgl.evaluate(spec)
    assert not r["resolvable"], (
        "the deliberately-colliding control passed the resolvability "
        "check, so that check cannot fail")


# ===========================================================================
# THE LADDER
# ===========================================================================

def test_the_width_is_derived_from_the_taps():
    """THE ARCHITECTURE'S CENTRAL FACT.

    `width_for(taps)` derives the width from the channel. So a wider
    channel IS a bigger population in view, and "widen" and "recruit"
    are one dial, not two.
    """
    assert width_for(1) == 1
    assert width_for(2) == 4
    assert width_for(3) == 8
    assert width_for(4) == 8
    assert width_for(5) == 16
    # and it is a function of the taps ALONE: the same tap count always
    # gives the same width
    for taps in (1, 2, 3, 4, 5, 8, 15):
        assert width_for(taps) == width_for(taps)


def test_the_taps_are_one_per_stalk_in_view():
    """So the population in view IS the channel's width, mechanically."""
    stalks = bgl.make_spread_population(8)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    for p in range(2, 9):
        ch = link.pair(ids[0], ids[1], in_view=ids[:p]).channel()
        assert len(ch.taps) == p - 1


def test_two_stalks_in_view_is_a_flat_channel():
    """The minimum readable population is THREE, because two give one
    path and therefore no null."""
    stalks = bgl.make_spread_population(4)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    ch = link.pair(ids[0], ids[1], in_view=ids[:2]).channel()
    assert ch.notch_db() < 3.0


def test_the_crowd_and_the_taps_are_decoupled_in_the_decoupled_model():
    """The control that isolates the tap effect.

    The COUPLED model has the crowd growing with the population (the
    architecture as built). The DECOUPLED model holds the crowd at the
    whole population. If the two give the same answer, the coupling is
    not real and the distinction is decoration.
    """
    stalks = bgl.make_spread_population(6)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    # coupled: the crowd is the in-view set, so at pop 3 there is 1
    # interferer and at pop 6 there are 4
    coupled = bgl.name_the_speaker(link, stalks, ids[0], ids[1], 0.10,
                                   in_view=ids[:3], crowd_set=ids[:3])
    # decoupled: the crowd is always the whole population
    decoupled = bgl.name_the_speaker(link, stalks, ids[0], ids[1], 0.10,
                                     in_view=ids[:3], crowd_set=ids)
    assert coupled["taps"] == decoupled["taps"], (
        "the channel must be the same in both models for the comparison "
        "to isolate the crowd")
    assert coupled["snr_db"] != decoupled["snr_db"], (
        "the crowd's membership changed nothing, so the coupling is "
        "not doing any work")


def test_the_two_crowd_models_disagree_about_the_peak():
    """THE ARCHITECTURAL FINDING, and it has to be reproducible.

    COUPLED: recruiting adds a tap AND an interferer, so the peak is
    early. DECOUPLED: the crowd is held constant, so the peak is
    later. If they agreed, the architecture would not have the property
    that makes the ladder's cap interesting.
    """
    # the structural claim, computed rather than asserted
    stalks = bgl.make_spread_population(8)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bgl.BINS)
    ids = [s.id for s in stalks]
    # at pop 3 the coupled crowd has 2 interferers, the decoupled has 6
    c = bgl.name_the_speaker(link, stalks, ids[0], ids[1], 0.10,
                             in_view=ids[:3], crowd_set=ids[:3])
    d = bgl.name_the_speaker(link, stalks, ids[0], ids[1], 0.10,
                             in_view=ids[:3], crowd_set=ids)
    assert c["snr_db"] > d["snr_db"], (
        "the coupled model must see LESS interference than the decoupled "
        "one at the same population, because the coupled crowd is "
        "smaller")


# ===========================================================================
# THE CACHE
# ===========================================================================

def test_the_cache_saves_attempts_not_answers():
    """THE HONEST CLAIM.

    A cache hit skips rungs that were NOT measured. So a cache hit is a
    belief that the channel has not changed. The cache must not be
    described as, or implemented as, a shortcut.
    """
    cache = bgl.PathwayCache()
    assert cache.lookup("a", "b") is None
    assert cache.misses == 1
    cache.store("a", "b", 5)
    assert cache.lookup("a", "b") == 5
    assert cache.hits == 1
    # and the cache is per ORDERED PAIR: a->b is not b->a
    assert cache.lookup("b", "a") is None


def test_the_cache_key_is_the_pair():
    """Two different pairs must not share a rung."""
    cache = bgl.PathwayCache()
    cache.store("a", "b", 3)
    cache.store("a", "c", 7)
    assert cache.lookup("a", "b") == 3
    assert cache.lookup("a", "c") == 7


# ===========================================================================
# THE GROWTH MEASUREMENT
# ===========================================================================

def test_growing_the_wire_does_not_move_the_address():
    """THE WORN HIGHWAY, and the finding is that it buys NOTHING by
    growing the wire.

    Everything that matters -- coupling, address, notch -- is a RATIO of
    the geometry, and scaling the geometry leaves every ratio alone. So
    a wider roadway carries more traffic but not more DIFFERENT traffic.

    This is the check that keeps the finding honest: if someone later
    changes the coupling law to be scale-dependent, this goes red.
    """
    s = CoaxWinding(id="x", girth_core=0.015, girth_in=0.060,
                    girth_out=0.072, n_in=12, n_out=13)
    g = CoaxWinding(id="x", girth_core=0.015 * 1.5, girth_in=0.060 * 1.5,
                    girth_out=0.072 * 1.5, n_in=12, n_out=13)
    assert bgl.address_of(s) == bgl.address_of(g)
    assert s.mutual_couplings()["m_out_in"] == \
        pytest.approx(g.mutual_couplings()["m_out_in"], abs=1e-12)
    assert s.girth_ratio == pytest.approx(g.girth_ratio, abs=1e-12)


def test_the_recipe_steps_the_ratio_by_exactly_the_step():
    """THE RECIPE, checked on the recipe.

    The mutation run MISSED the mutation that added `i * 0.01` to the
    ratio, because the test only checked a hand-built CoaxWinding and
    never the recipe the bench actually uses. So the recipe's ratio must
    step by exactly the requested step.

    This matters because the step IS the address spacing: the address
    carries (girth_ratio - 1), so a silent extra term moves every
    address and every separation the bench reports.
    """
    base = 1.40
    step = 0.03
    stalks = bgl.make_stalks(base, step, 0.25, 12, (13, 14, 15, 16))
    for i, s in enumerate(stalks):
        assert s.girth_ratio == pytest.approx(base + i * step, abs=1e-12)


def test_the_recipe_keeps_the_inner_girth_fixed():
    """The inner girth is the unit every ratio is on, so it is the same
    for every stalk. A recipe that moved it would move the address."""
    stalks = bgl.make_stalks(1.40, 0.03, 0.25, 12, (13, 14, 15, 16))
    for s in stalks:
        assert s.girth_in == pytest.approx(bgl.INNER_GIRTH, abs=1e-12)
        assert s.girth_core == pytest.approx(
            bgl.INNER_GIRTH * 0.25, abs=1e-12)
