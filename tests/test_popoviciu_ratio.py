"""
test_popoviciu_ratio.py -- the ratio readout, measured and pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE SELF-CHECK AGREES. The bench works in the frequency domain for
   speed, and that is only allowed if it agrees with the real
   transport. A sign error in the DFT convention is invisible to every
   other check in the file -- the frequency path and the ratio path
   would both be self-consistent and both wrong.

2. THE COHORT RECOVERS POPOVICIU'S +3 dB PER DOUBLING. This is the
   positive claim: a population of redundant copies of one address,
   each through its own channel, coherent-sums the signal and
   quadrature-sums the noise.

3. THE COHORT'S GAIN IS COHERENCE, NOT POPULATION. The contrast pair:
   the same members with RANDOM phases must NOT show the gain. This
   is the assertion that can go red, and it is the one that would
   catch a measurement of the wrong thing. A check that cannot fail
   is not a check.

4. THE RATIO READOUT DOES NOT RECOVER THE +3 dB FROM POPULATION
   ALONE. The measured finding: the ratio path's SNR PEAKS at a small
   population and FALLS, because the crowd's phases add coherently in
   the shared carrier. So the ratio path alone does not give Popoviciu's
   gain, and the ladder's cap at population 4 stands for the
   frequency path. This is the item's question, and it is asserted as
   an ORDERING (peak then fall), not as a threshold, so it survives a
   re-tuned bound.

5. THE MEASUREMENT IS NOT FITTED TO ITS OWN ANSWER. The lattice and
   the jittered readings are both reported, and the jittered one must
   be the pessimistic one -- if the jitter made the reading BETTER,
   the jitter would be helping rather than hurting, and the honest
   number would be the other one.

Run:
    python -m pytest tests/test_popoviciu_ratio.py -q
"""

from __future__ import annotations

import math
import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import bench_popoviciu_ratio as B  # noqa: E402

#: Popoviciu's number: 3 dB per doubling of a coherent population.
POPOVICIU_DB = 3.0


# ===========================================================================
# 1. THE SELF-CHECK
# ===========================================================================

def test_the_analytic_route_agrees_with_the_transport():
    """the frequency-domain shortcut must match the real path.

    Measured, 2026-10-31: the first version of the bench used
    exp(+j2*pi*FC*i) for the carrier, and the repo's DFT puts that
    tone in bin N-f0 rather than bin f0. The analytic route and the
    transport disagreed by 0.39 -- a 100% error -- while every other
    number in the bench looked plausible.
    """
    assert B.self_check(), (
        "the analytic carrier route does not agree with transport + "
        "spectrum; the bench is measuring its own arithmetic")


# ===========================================================================
# 2. THE COHORT RECOVERS +3 dB PER DOUBLING
# ===========================================================================

def test_a_coherent_cohort_gains_three_db_per_doubling():
    """the positive claim.

    With no crowd, the signal is C*|s| and the noise is sqrt(C)*sigma,
    so the SNR in dB rises 10*log10(C) = 3.01 dB per doubling.
    """
    vals = [B.measure_cohort(c, 0.15, coherent=True, with_crowd=False)["snr_db"]
            for c in (2, 4, 8, 16)]
    deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    mean_delta = sum(deltas) / len(deltas)
    assert abs(mean_delta - POPOVICIU_DB) < 0.5, (
        "the coherent cohort gained %.2f dB per doubling, not %.2f: %s"
        % (mean_delta, POPOVICIU_DB, deltas))


def test_the_cohort_gain_holds_for_every_doubling_not_just_the_mean():
    """the law is per doubling, so every step must show it.

    A mean can be right while its steps are wrong -- the first
    version of this measurement gave deltas of +1.85 and +4.06 at 32
    trials, whose mean was right and whose steps were not.
    """
    vals = [B.measure_cohort(c, 0.15, coherent=True, with_crowd=False)["snr_db"]
            for c in (2, 4, 8, 16)]
    deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    for d in deltas:
        assert abs(d - POPOVICIU_DB) < 1.0, (
            "a doubling gained %.2f dB, not %.2f: %s"
            % (d, POPOVICIU_DB, deltas))


# ===========================================================================
# 3. THE CONTRAST PAIR -- the gain is coherence, not population
# ===========================================================================

def test_random_phases_destroy_the_gain():
    """the same members, incoherent, must NOT show +3 dB per doubling.

    THIS IS THE CHECK THAT CAN GO RED, and it is the one that would
    catch a measurement of the wrong thing: if the "gain" were an
    artefact of the estimator or of the channel, the incoherent case
    would show it too.
    """
    coh = [B.measure_cohort(c, 0.15, coherent=True, with_crowd=True)["snr_db"]
           for c in (2, 4, 8, 16)]
    inc = [B.measure_cohort(c, 0.15, coherent=False, with_crowd=True)["snr_db"]
           for c in (2, 4, 8, 16)]
    coh_gain = (coh[-1] - coh[0]) / 3.0
    inc_gain = (inc[-1] - inc[0]) / 3.0
    assert coh_gain > inc_gain + 1.0, (
        "the coherent cohort gained %.2f dB per doubling and the "
        "incoherent one %.2f -- the gain is not coming from coherence"
        % (coh_gain, inc_gain))


def test_the_coherent_cohort_beats_the_incoherent_one_at_every_size():
    """the ordering, not the cutoff."""
    for c in (2, 4, 8, 16):
        coh = B.measure_cohort(c, 0.15, coherent=True,
                               with_crowd=True)["snr_db"]
        inc = B.measure_cohort(c, 0.15, coherent=False,
                               with_crowd=True)["snr_db"]
        assert coh > inc, (
            "at cohort %d the coherent reading (%.2f) is not above the "
            "incoherent one (%.2f)" % (c, coh, inc))


# ===========================================================================
# 4. THE RATIO READOUT DOES NOT RECOVER THE GAIN FROM POPULATION ALONE
# ===========================================================================

def test_the_ratio_readout_peaks_and_then_falls():
    """the item's question, answered as an ordering.

    The ratio path puts every transmitter on ONE carrier, so the
    crowd's phases add COHERENTLY at that carrier and the SNR FALLS as
    the population grows. The measurement must show a peak and a fall,
    not a rise -- and it must show it at EVERY population above the
    peak.

    THE POPULATION AXIS IS WRITTEN OUT HERE, not taken from
    bench_balance_final's POPS. That axis is the other worker's to
    change -- it was widened to the dense grid on 2026-10-31 -- and a
    test that reads its axis from another module is a test whose
    meaning moves when somebody else edits a different file.

    IT IS ALSO A DOUBLE-DOUBLING AXIS, so "a doubling" is exactly a
    doubling: 4 -> 8 -> 16 -> 32 -> 64.
    """
    axis = (4, 8, 16, 32, 64)
    vals = [B.measure_ratio(pop, 0.15, "A", jitter=True)["snr_db"]
            for pop in axis]
    peak_i = max(range(len(vals)), key=lambda i: vals[i])
    assert peak_i < len(vals) - 1, (
        "the ratio path never falls: %s" % vals)
    for i in range(peak_i + 1, len(vals)):
        assert vals[i] < vals[peak_i], (
            "the ratio path rose above its peak at population %d: %s"
            % (axis[i], vals))


def test_the_ratio_path_is_not_better_than_the_frequency_path_at_large_pop():
    """the two paths, compared where the population is large.

    At a small population the two are close; at a large one the
    frequency path must be ahead, because it separates the crowd by
    frequency while the ratio path adds it up at the carrier.
    """
    import bench_balance_final as BF
    ratio = B.measure_ratio(32, 0.15, "A", jitter=True)["snr_db"]
    freq = BF.measure(32, 0.15, "A")["snr_db"]
    assert freq > ratio, (
        "at population 32 the frequency path (%.2f dB) is not ahead of "
        "the ratio path (%.2f dB)" % (freq, ratio))


# ===========================================================================
# 5. THE MEASUREMENT IS NOT FITTED TO ITS OWN ANSWER
# ===========================================================================

def test_the_jittered_reading_is_the_pessimistic_one():
    """if the jitter made the reading BETTER, the honest number would
    be the lattice one.

    On the lattice the crowd's phases are the roots of unity and their
    sum at the shared carrier nearly vanishes, which flatters the ratio
    path. The jittered reading is the honest one, so it must be the
    lower of the two.
    """
    for pop in (8, 16, 32):
        even = B.measure_ratio(pop, 0.15, "A", jitter=False)["snr_db"]
        jit = B.measure_ratio(pop, 0.15, "A", jitter=True)["snr_db"]
        assert jit < even, (
            "at population %d the jittered reading (%.2f) is not below the "
            "lattice reading (%.2f), so the lattice is the honest number"
            % (pop, jit, even))


def test_the_decode_rate_falls_with_the_population():
    """the reading gets worse as the crowd grows.

    The named rate is how often the ratio readout picked the right
    candidate. It must be high at a small population and lower at a
    large one -- a ratio path that stayed at 100% while the crowd grew
    would be reading something other than the crowd.
    """
    small = B.measure_ratio(4, 0.15, "A", jitter=True)["rate"]
    large = B.measure_ratio(64, 0.15, "A", jitter=True)["rate"]
    assert small > large, (
        "the ratio decode rate did not fall with the population: "
        "%d -> %d" % (small, large))
    assert small >= 0.5, (
        "the ratio path cannot even name the speaker at population 4 "
        "(rate %.2f), so the fall is not a crowding effect" % small)
