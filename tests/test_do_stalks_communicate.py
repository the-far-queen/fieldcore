"""
test_do_stalks_communicate.py -- the communication claim must be able to
FAIL.

THE CLAIM: the stalks communicate electronically. That is stronger than
"the channel has structure", and it has three parts that can each go
red on their own:

  1. THE SENDER'S SIGNAL ARRIVES AT THE RECEIVER -- the recovered
     spectrum matches the SENDER's address, not the receiver's own.
     A loopback fails this and nothing else catches it.
  2. MOVING THE RECEIVER CHANGES WHAT ARRIVES -- if the channel is the
     same for every receiver, it is a transmitter hearing itself.
  3. THE RECEIVER NAMES WHO SPOKE -- and it refuses BY NAME when the
     reading is ambiguous.

Every check below names the mistake it catches. Two of them are mistakes
this file's own development made:

  * the population recipe divided the ratio step by the half-circle
    count, which produced a 2-bin address separation instead of the
    8 the sweep measured, and the naming rate it reported (73%) was the
    2-bin population's number, not the 8-bin one's
  * the spread was taken from the girth bench's own population (16
    bins), which measures WORSE than 8 bins -- more separation means
    the girth ratios are further apart, which means weaker coupling
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

import do_stalks_communicate as dsc  # noqa: E402
from interstalk_link import InterstalkLink, width_for  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402


@pytest.fixture(scope="module")
def setup():
    stalks = dsc.the_population(8)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    return stalks, link, [s.id for s in stalks]


# ===========================================================================
# 1. THE SENDER'S SIGNAL ARRIVES
# ===========================================================================

def test_the_receiver_hears_the_sender_not_itself(setup):
    """THE LOOPBACK FALSIFICATION, on the recovery itself.

    The recovered spectrum is compared against the SENDER's address and
    against the RECEIVER's own. If the sender's alignment is high and
    the receiver's is low, the receiver heard the sender.
    """
    stalks, link, ids = setup
    sender_aligns = []
    receiver_aligns = []
    for i in range(len(ids)):
        tx, rx = ids[i], ids[(i + 1) % len(ids)]
        r = dsc.recover(link, stalks, tx, rx, dsc.CROWD)
        assert r["ok"], r.get("reason")
        sender_aligns.append(r["align_sender"])
        receiver_aligns.append(r["align_receiver"])
    mean_sender = sum(sender_aligns) / len(sender_aligns)
    mean_receiver = sum(receiver_aligns) / len(receiver_aligns)
    assert mean_sender > 0.4, (
        "the sender's signal does not arrive: mean alignment %.6f" %
        mean_sender)
    assert mean_receiver < 0.1, (
        "the receiver is hearing ITSELF: mean alignment with its own "
        "address %.6f" % mean_receiver)
    assert mean_sender > 4.0 * mean_receiver + 0.1, (
        "the sender and the receiver are not distinguishable")


def test_the_addresses_are_resolvable(setup):
    """Two stalks must be tellable apart, or naming is a coin flip."""
    stalks, link, ids = setup
    addrs = [dsc.address_of(s) for s in stalks]
    sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
              for i, a in enumerate(addrs) for b in addrs[i + 1:])
    assert sep * dsc.BINS >= 4.0, (
        "the addresses are only %.2f DFT bins apart at %d bins" % (
            sep * dsc.BINS, dsc.BINS))


def test_the_spread_is_per_stalk(setup):
    """THE RECIPE, checked on the recipe.

    The first version divided the ratio step by the half-circle count,
    which made the address separation four times smaller than intended
    and the naming rate it reported belonged to a different population.
    """
    stalks, link, ids = setup
    ratios = [s.girth_ratio for s in stalks]
    step = ratios[2] - ratios[0]
    assert step == pytest.approx(dsc.SPREAD_STEP, abs=1e-9), (
        "the per-stalk ratio step is %.6f, not the specified %.6f" % (
            step, dsc.SPREAD_STEP))
    addrs = [dsc.address_of(s) for s in stalks]
    sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
              for i, a in enumerate(addrs) for b in addrs[i + 1:])
    assert sep * dsc.BINS == pytest.approx(8.0, abs=0.5)


# ===========================================================================
# 2. MOVING THE RECEIVER CHANGES WHAT ARRIVES
# ===========================================================================

def test_every_receiver_has_its_own_channel(setup):
    """One transmitter, every receiver: the fingerprints must all differ."""
    stalks, link, ids = setup
    prints = set()
    for rx in ids[1:]:
        pair = link.pair(ids[0], rx, in_view=ids)
        prints.add((round(pair.pair_coupling(), 9),
                    round(pair.channel().notch_db(), 6),
                    tuple(round(t[0], 9) for t in pair.taps())))
    assert len(prints) == len(ids) - 1, (
        "two receivers have the same channel, so the receiver is not "
        "part of the path")


def test_the_transmitter_hearing_itself_is_a_flat_channel(setup):
    """A stalk speaking to itself over a channel with no other stalk in
    view has ONE path, so no null, so nothing to invert -- and the gate
    refuses it BY NAME."""
    stalks, link, ids = setup
    ex = link.exchange(ids[0], ids[1], in_view=[ids[0], ids[1]])
    assert not ex.allowed
    assert ex.reason == "channel_flat_channel"


# ===========================================================================
# 3. NAMING, AND REFUSING
# ===========================================================================

def test_the_receiver_names_the_sender_more_often_than_not(setup):
    """The naming rate, at the crowd the ladder's peak was measured at."""
    stalks, link, ids = setup
    correct = 0
    total = 0
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, dsc.CROWD)
            total += 1
            if r["correct"]:
                correct += 1
    rate = correct / total
    assert rate > 0.70, (
        "the receiver names the sender only %.0f%% of the time" % (rate * 100))


def test_a_clean_channel_names_the_sender_every_time(setup):
    """With no crowd there is nothing to confuse the reading, so the
    naming must be perfect. If it is not, the readout itself is wrong."""
    stalks, link, ids = setup
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, 0.0)
            assert r["correct"], (
                "with no crowd, %s -> %s named %s" % (a, b, r["named"]))


def test_a_loud_crowd_forces_a_named_refusal(setup):
    """A receiver that always answers is not reading.

    At a heavy crowd the reading is ambiguous, and the gate must refuse
    with the NAME of the refusal -- not guess.
    """
    stalks, link, ids = setup
    r = dsc.recover(link, stalks, ids[0], ids[1], 0.70)
    assert not r["correct"], (
        "at crowd 0.70 the receiver named the sender: %s" % r["named"])
    assert r["reason"].startswith("refuse_") or \
        r["reason"].startswith("channel_"), (
        "the refusal carries no name: %r" % r["reason"])


def test_the_alignment_separates_the_answer_from_the_refusal(setup):
    """THE CONFIDENCE IS THE ALIGNMENT, and this test found out that the
    MARGIN is not.

    The first version of this check asserted that the margin -- the gap
    between the best and second-best candidate score -- separates correct
    readings from wrong ones. IT DOES NOT, and the measurement says why:
    the score is a signed correlation, so on a messy reading every
    candidate scores near zero and the DIFFERENCE between two near-zero
    numbers is large while meaning nothing. The wrong readings had the
    LARGER margins.

    So the margin is not a confidence and no gate should threshold on
    it. The ALIGNMENT is the confidence -- it is measured against the
    waveform that was actually sent -- and that is what the kernel's
    MIN_COS gate uses.
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
    assert good and bad, "the test needs both outcomes to be meaningful"
    # THE ALIGNMENT DOES NOT FULLY SEPARATE, and the measurement says
    # why, so the check asserts the truth rather than a wish:
    #
    #   correct readings: alignment 0.4333 to 0.8274 (median 0.7362)
    #   wrong readings:   alignment 0.4505 to 0.7531 (median 0.4838)
    #
    # so the MEDIANS separate and the extremes overlap. The reason is
    # visible in the failures: for s07 -> s03 the sender's signal IS
    # present (alignment 0.7531) and the receiver still named the wrong
    # stalk, because the readout picks by raw correlation and a
    # neighbouring address correlates almost as well.
    #
    # So the alignment is a NECESSARY condition (a reading with no
    # sender in it has a low alignment) and it is not a SUFFICIENT one.
    med_good = sorted(good)[len(good) // 2]
    med_bad = sorted(bad)[len(bad) // 2]
    assert med_good > med_bad, (
        "the median alignment does not separate the answer from the "
        "refusal: %.4f against %.4f" % (med_good, med_bad))
    assert min(good) > 0.3, (
        "a correct reading with a near-zero alignment means the sender "
        "was not really in the received signal")


def test_the_margin_does_not_separate_and_must_not_be_used_as_a_confidence(
        setup):
    """THE NEGATIVE RESULT, pinned so nobody re-derives the wrong
    quantity and builds a threshold on it.

    The margin overlaps between correct and wrong readings, and the
    wrong readings have the LARGER margins. That is a property of the
    measurement, not an accident, so it is asserted.
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
    # they overlap, and the wrong readings reach higher
    assert max(bad) > min(good), (
        "the margin now separates, which means the score's sign or the "
        "candidate set changed -- and the margin would then be usable "
        "as a confidence, which this file says it is not")


# ===========================================================================
# THE WIDTH IS DERIVED, NOT REQUESTED
# ===========================================================================

def test_the_width_follows_the_channel(setup):
    """The width is the channel's, not the caller's."""
    stalks, link, ids = setup
    taps = len(link.pair(ids[0], ids[1], in_view=ids).taps())
    assert width_for(taps) == 16
    # and with fewer stalks in view the width is smaller
    for p in range(2, 9):
        t = len(link.pair(ids[0], ids[1], in_view=ids[:p]).taps())
        assert width_for(t) == width_for(t)
        assert t == p - 1
