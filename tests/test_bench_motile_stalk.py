"""
test_bench_motile_stalk.py -- the motility findings must be able to FAIL.

THE RULE: a check that cannot go red is not a check.

WHAT IS ASSERTED, and what each one is worth:

  THE FOUR LEVERS
    attach changes the channel and the width    it IS the ladder
    attach does NOT change the address         identities stay stable
    proximity changes the GAIN                 a volume knob
    proximity does NOT change the shape        the shape is the claim
    girth changes NOTHING                      everything is a ratio
    length changes NOTHING in the channel      the deepest gap

  THE MARGIN
    the margin does NOT separate correct from wrong readings, so
    nothing may threshold on it

THE POINT OF THE FIRST FOUR: they pin the model's limits. If a future
change makes girth or length matter, these go red -- which is the
signal to update the architecture note, not to leave a stale claim
sitting in a comment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import bench_motile_stalk as bms  # noqa: E402
import do_stalks_communicate as dsc  # noqa: E402
from interstalk_link import InterstalkLink, width_for  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402


@pytest.fixture(scope="module")
def setup():
    stalks = bms.base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    return stalks, link, [s.id for s in stalks]


# ===========================================================================
# LEVER 1 -- ATTACH / DETACH
# ===========================================================================

def test_attaching_a_stalk_adds_a_tap_and_the_width_follows(setup):
    """ATTACHING IS THE LADDER. The channel's taps are one per stalk in
    view, so attaching a stalk adds a tap and the width is DERIVED from
    the tap count."""
    stalks, link, ids = setup
    for p in range(2, len(ids) + 1):
        ch = link.pair(ids[0], ids[1], in_view=ids[:p]).channel()
        assert len(ch.taps) == p - 1
        assert width_for(len(ch.taps)) == width_for(p - 1)


def test_attaching_does_not_change_any_address(setup):
    """THE ADDRESS MUST BE STABLE. A bigger crowd must not change who
    anyone is, or the identities would not be derivable from the
    geometry."""
    stalks, link, ids = setup
    before = [dsc.address_of(s) for s in stalks]
    link.pair(ids[0], ids[1], in_view=ids)
    after = [dsc.address_of(s) for s in stalks]
    assert before == after


def test_two_stalks_in_view_cannot_be_read(setup):
    """The flat channel: one path, no null, nothing to invert."""
    stalks, link, ids = setup
    ex = link.exchange(ids[0], ids[1], in_view=[ids[0], ids[1]])
    assert not ex.allowed
    assert ex.reason == "channel_flat_channel"


# ===========================================================================
# LEVER 2 -- PROXIMITY
# ===========================================================================

def test_proximity_changes_the_gain(setup):
    """The pair coupling falls as the separation grows."""
    stalks, link, ids = setup
    pair = link.pair(ids[0], ids[1], in_view=ids)
    pair.separation = 0.0
    near = pair.pair_coupling()
    pair2 = link.pair(ids[0], ids[1], in_view=ids)
    pair2.separation = 0.160
    far = pair2.pair_coupling()
    assert near > far, "moving the receiver away must reduce the coupling"


def test_proximity_does_not_change_the_shape(setup):
    """THE CLAIM BEING PINNED: proximity is a GAIN knob.

    The notch, the width, the address and the tap count all hold still
    while the coupling moves. If a future change makes the notch depend
    on the separation -- which is the physical fix -- this goes red, and
    that is the signal to update the note.
    """
    stalks, link, ids = setup
    shapes = []
    gains = []
    for sep in (0.0, 0.010, 0.040, 0.160):
        pair = link.pair(ids[0], ids[1], in_view=ids)
        pair.separation = sep
        ch = pair.channel()
        shapes.append((round(ch.notch_db(), 6), len(ch.taps),
                       width_for(len(ch.taps))))
        gains.append(round(pair.pair_coupling(), 9))
    assert len(set(shapes)) == 1, (
        "the channel's SHAPE moved with the separation: %r" % (shapes,))
    assert len(set(gains)) > 1, (
        "the channel's GAIN did not move with the separation: %r" % (gains,))


# ===========================================================================
# LEVER 3 -- GIRTH
# ===========================================================================

def test_girth_growth_changes_nothing_that_matters(setup):
    """THE WORN HIGHWAY, INERT.

    Everything that matters is a RATIO of the geometry: the coupling is
    overlap x inner/outer, the address is (parity/2) + (ratio - 1), the
    notch is a ratio of two paths that scale together. So a bigger wire
    is a louder wire and nothing else.
    """
    stalks, link, ids = setup
    rows = []
    for growth in (0.75, 1.0, 1.5, 2.0):
        grown = [CoaxWinding(
            id=s.id, girth_core=s.girth_core * growth,
            girth_in=s.girth_in * growth, girth_out=s.girth_out * growth,
            n_in=s.n_in, n_out=s.n_out) for s in stalks]
        glink = InterstalkLink(core=WoundCore(stalks=grown), bins=dsc.BINS)
        pair = glink.pair(ids[0], ids[1], in_view=ids)
        ch = pair.channel()
        rows.append((round(pair.pair_coupling(), 9), len(ch.taps),
                     width_for(len(ch.taps)),
                     round(dsc.address_of(grown[0]), 9)))
    assert len(set(rows)) == 1, (
        "girth growth now changes something that matters: %r" % (rows,))


def test_the_address_carries_the_girth_ratio(setup):
    """And the address DOES carry the ratio -- so the ratio is the
    address's continuous component, and scaling both windings leaves it
    alone because it is a ratio."""
    s = CoaxWinding(id="x", girth_core=0.03, girth_in=0.060,
                    girth_out=0.072, n_in=12, n_out=14)
    assert dsc.address_of(s) == pytest.approx(0.2, abs=1e-12)


# ===========================================================================
# LEVER 4 -- LENGTH
# ===========================================================================

def test_length_changes_nothing_in_the_channel(setup):
    """THE DEEPEST GAP.

    The lay angle moves with the length, so the geometry knows it. But
    the channel's taps are dimensionless and the delay is a bin count,
    so the channel does not. A coil twice as long is a coil with the
    same filter.
    """
    stalks, link, ids = setup
    rows = []
    angles = []
    for length in (0.5, 1.0, 2.0, 4.0):
        long_stalks = [CoaxWinding(
            id=s.id, girth_core=s.girth_core, girth_in=s.girth_in,
            girth_out=s.girth_out, n_in=s.n_in, n_out=s.n_out,
            length=length) for s in stalks]
        llink = InterstalkLink(core=WoundCore(stalks=long_stalks),
                               bins=dsc.BINS)
        pair = llink.pair(ids[0], ids[1], in_view=ids)
        ch = pair.channel()
        rows.append((round(pair.pair_coupling(), 9), len(ch.taps),
                     width_for(len(ch.taps)),
                     round(ch.notch_db(), 6)))
        angles.append(round(long_stalks[0].lay_angle_deg(
            long_stalks[0].girth_in, long_stalks[0].n_in), 3))
    assert len(set(rows)) == 1, (
        "length now changes the channel: %r" % (rows,))
    assert len(set(angles)) > 1, (
        "the lay angle no longer moves with the length, so the geometry "
        "has stopped knowing the length: %r" % (angles,))


# ===========================================================================
# THE MARGIN
# ===========================================================================

def test_the_margin_does_not_separate_correct_from_wrong(setup):
    """THE NEGATIVE RESULT, pinned.

    The score is a signed correlation, so on a messy reading every
    candidate scores near zero and the difference between two near-zero
    numbers is large while meaning nothing. So a big margin on a bad
    reading means 'nothing was heard, and these two are equally unheard'.

    Nothing may threshold on it.
    """
    stalks, link, ids = setup
    good = []
    bad = []
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, dsc.CROWD)
            (good if r["correct"] else bad).append(r["margin"])
    assert good and bad
    assert max(bad) > min(good), (
        "the margin now separates, so it would be usable as a confidence "
        "-- which this file says it is not")


def test_the_alignment_is_necessary_but_not_sufficient(setup):
    """THE REPLACEMENT CONFIDENCE, and its limit.

    The alignment is measured against the waveform that was actually
    sent, so a reading with no sender in it has a low alignment. That
    makes it NECESSARY. It is not SUFFICIENT, because the readout picks
    by raw correlation and a neighbouring address correlates almost as
    well -- so the medians separate and the extremes overlap.
    """
    stalks, link, ids = setup
    good = []
    bad = []
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, dsc.CROWD)
            (good if r["correct"] else bad).append(r["align_sender"])
    assert good and bad
    med_good = sorted(good)[len(good) // 2]
    med_bad = sorted(bad)[len(bad) // 2]
    assert med_good > med_bad, (
        "the median alignment no longer separates: %.4f against %.4f" % (
            med_good, med_bad))
    assert min(good) > 0.3
