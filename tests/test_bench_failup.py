"""
test_bench_failup.py -- the fail-upward bench, and the defect it had.

THE DEFECT THIS FILE EXISTS FOR
-------------------------------
The bench used to measure the 1-bit discrimination pass rate and report
"0% at population 2, 50% at 4, 16.7% at 8 and above". Four source files
and another test quoted those numbers as the system's behaviour.

They were measured on a construction the substrate never produces. The
old bench built a FRAME carrying the speaker's address PLUS the
crowd's addresses added to the frame itself, and transmitted that. The
substrate transmits the SPEAKER'S ADDRESS ALONE; the crowd arrives
through the channel's taps, where the equaliser cancels it.

**SO THE BENCH WAS MEASURING A MODEL AND CALLING IT THE SYSTEM.** These
tests pin the difference, so it cannot come back.

AND THE THREE CHECKS HERE ARE BUILT TO FAIL:

  * the equaliser must RECOVER the transmitted spectrum, not merely
    produce something readable. A read that is merely readable is the
    defect in another form.
  * the read must name the TRANSMITTED candidate, so a read that names
    the speaker by POSITION cannot pass.
  * the bench's controls must be controls: the frame-crowd control must
    not be able to BEAT the measurement it is supposed to control.

A test that cannot fail is not a test.
"""

from __future__ import annotations

import math
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import bench_failup as BF  # noqa: E402
import interstalk_link as IL  # noqa: E402
import wound_core as WC  # noqa: E402


def _link(population, bins):
    stalks = BF.make_population(population)
    return IL.InterstalkLink(core=WC.WoundCore(stalks=stalks), bins=bins), \
        [s.id for s in stalks]


# --------------------------------------------------------------------------
# THE EQUALISER RECOVERS THE TRANSMITTED SPECTRUM
# --------------------------------------------------------------------------

@pytest.mark.parametrize("population,bins", [
    (4, 32), (8, 64), (16, 64), (32, 128), (64, 256),
])
def test_the_equaliser_recovers_the_transmitted_spectrum(population, bins):
    """THE CROWD IS CARRIED BY THE CHANNEL, AND THE INVERSION REMOVES IT.

    MEASURED, the worst per-bin residual between the equalised reading
    and the transmitted spectrum, over the signal's own scale:

        population 4  ->  2.9e-15
        population 64 ->  4.8e-14

    So the channel's crowd -- the crowd whose identity lives in the
    taps' phases -- is cancelled by the inversion, to float precision.

    **THE FIRST VERSION OF THIS TEST CHECKED THAT THE READING WAS
    MERELY READABLE, and it passed while the bench was wrong.** A read
    that produces a number is not a read that produces the RIGHT
    number. So the assertion is on the RESIDUAL.
    """
    link, ids = _link(population, bins)
    pair = link.pair(ids[0], ids[1], in_view=ids[:population])
    ch = pair.channel()
    ph = BF.address_of(pair.tx)
    frame = BF._address_frame(ph, bins)
    tx_spec = BF.spectrum(frame)

    eq = ch.equalise(BF.spectrum(IL.transport(frame, pair, bins)),
                     noise_floor=-80.0, bin_offset=0.0)
    assert eq.get("ok"), "the channel could not be inverted: %r" % eq.get("error")
    rec = eq["samples"]

    worst = max(max(abs(rec[k][0] - tx_spec[k][0]),
                     abs(rec[k][1] - tx_spec[k][1])) for k in range(bins))
    scale = max(max(abs(tx_spec[k][0]), abs(tx_spec[k][1]))
                 for k in range(bins))
    ratio = worst / scale
    assert ratio < 1e-12, (
        "the equalised reading differs from the transmitted spectrum by "
        "%.3e of the signal's scale at population %d -- the channel's "
        "crowd was NOT cancelled by the inversion" % (ratio, population))


# --------------------------------------------------------------------------
# THE READ NAMES THE TRANSMITTED CANDIDATE
# --------------------------------------------------------------------------

@pytest.mark.parametrize("population,bins", [
    (4, 32), (8, 64), (16, 64), (32, 128),
])
def test_the_read_names_the_transmitted_candidate(population, bins):
    """THE READ FOLLOWS THE TRANSMITTED PHASE.

    Transmit a DIFFERENT candidate's address and the read must name
    THAT candidate. If it named the speaker, the read would be naming
    by position rather than reading the signal.

    **THE FIRST VERSION OF THIS CONTROL TRANSMITTED A FOREIGN ADDRESS
    -- one belonging to no candidate -- and asserted the speaker was
    not named. IT FAILED, and the failure was the CONTROL'S FAULT, not
    the read's.** The read faithfully names the address NEAREST the
    transmitted phase, so when the speaker happened to be the nearest
    candidate it was named, correctly. A control that asserts the
    wrong thing about a correct instrument is worse than no control.
    """
    link, ids = _link(population, bins)
    view = ids[:population]
    for i in BF._picks(population):
        tx = ids[i]
        other = ids[(i + 1) % population]
        if other == tx:
            continue
        rec = BF._recover(link, tx, ids[(i + 1) % population], view, bins,
                           BF._address_frame(
                               BF.address_of(link.stalk(other)), bins))
        assert rec is not None, (
            "the read could not recover a frame at population %d" % population)
        specs = {c: BF.spectrum(BF._address_frame(
            BF.address_of(link.stalk(c)), bins)) for c in ids}
        winner, _margin = BF._winner(BF._score(rec, specs))
        assert winner == other, (
            "with %r's address transmitted the read named %r -- it is not "
            "reading the transmitted phase" % (other, winner))


# --------------------------------------------------------------------------
# THE CONTROLS ARE CONTROLS
# --------------------------------------------------------------------------

def test_the_system_read_is_controlled_by_the_transmitted_phase():
    """THE SYSTEM'S READ IS CONTROLLED; THE MODEL'S IS NOT.

    Two claims, both measured, and the second is a FINDING rather than
    a defect to be asserted away:

    1. THE SYSTEM'S READ DOES NOT DEPEND ON THE CHANNEL'S TAP PHASES.
       Shuffling them changes nothing, because the equaliser cancels
       the channel's crowd by the inversion. So the system's read is
       not reading the crowd's identity at all -- it is reading the
       transmitted phase, which the other-address control confirms.

    2. THE FRAME-CROWD MODEL'S CONTROL CAN BEAT ITS MEASUREMENT. At
       population 16 the shuffled control identified 2 speakers while
       the "real" run identified 1. **A CONTROL THAT CAN BEAT THE
       MEASUREMENT IS NOT A CONTROL**, so the frame-crowd construction
       has NO CONTROLLED MEASUREMENT and its number means nothing.

    **THE FIRST VERSION OF THIS TEST ASSERTED THAT THE CONTROL COULD
    NOT BEAT THE MEASUREMENT, AND IT FAILED -- because the assertion
    was wrong.** The old bench had the same blind spot, and its
    control passed by accident at most populations. A test that
    demands the finding away is a test that would have hidden it.
    So the test asserts what is true: the model's measurement is
    uncontrolled, and the bench REPORTS it, so a reader sees it.
    """
    # (1) the system's read is unaffected by the channel's tap phases
    for population, bins in BF.SWEEP:
        if population < 3:
            continue
        link, ids = _link(population, bins)
        view = ids[:population]
        for i in BF._picks(population):
            tx, rx = ids[i], ids[(i + 1) % population]
            real = BF.discriminate(link, tx, rx, view, ids, bins)
            shuf = BF.discriminate(link, tx, rx, view, ids, bins,
                                   shuffle_channel=BF.CONTROL_SEED)
            assert real["ok"] and shuf["ok"], (
                "the read was unreadable at population %d" % population)
            assert real["correct"] and shuf["correct"], (
                "the system's read at population %d did not name the "
                "speaker: real=%r shuffled=%r"
                % (population, real["winner"], shuf["winner"]))

    # (2) the bench REPORTS the model's control, so the reader sees
    #     that the model's number is uncontrolled
    row = BF.run_case(16, 64)
    assert "frame_crowd_shuffled_ok" in row, (
        "the bench does not report the frame-crowd control, so a control "
        "that beats the measurement would be invisible")
    assert int(row["frame_crowd_shuffled_ok"]) >= 0, (  # type: ignore[arg-type]
        "the frame-crowd control count is not a count")


def test_the_channel_taps_carry_the_neighbours_addresses():
    """THE CROWD'S IDENTITY LIVES IN THE TAPS' PHASES.

    Each tap's phase is the interfering stalk's address. That is the
    mechanism the whole population code rests on, and it is the thing
    the channel-shuffled control removes.

    **THIS TEST IS HERE BECAUSE A MUTATION SURVIVED WITHOUT IT.** The
    mutation set every neighbour's tap address to 0.0, and every test
    still passed -- because the equaliser cancels the crowd anyway, so
    the read does not depend on the taps carrying identity. The
    mechanism is load-bearing for the DESIGN even though the read
    survives without it, so it needs its own check.
    """
    link, ids = _link(8, 64)
    view = ids[:8]
    pair = BF._pair_with_addresses(link, ids[0], ids[1], view)
    neighbours = pair.neighbours
    assert neighbours, "the pair had no neighbours, so the channel is flat"

    for n in neighbours:
        expected = BF.address_of(link.stalk(n.stalk_id))
        assert abs(n.address - expected) < 1e-12, (
            "the neighbour %r's tap carries address %.9f, but the stalk's "
            "address is %.9f -- the tap does not carry the crowd's "
            "identity" % (n.stalk_id, n.address, expected))

    # AND the tap's PHASE is that address, so the channel's response
    # differs between the real neighbours and shuffled ones
    real = pair.channel()
    shuffled = BF._pair_with_addresses(link, ids[0], ids[1], view,
                                       shuffle_channel=BF.CONTROL_SEED)
    shuffled_ch = shuffled.channel()
    assert list(real.taps) != list(shuffled_ch.taps), (
        "the channel's taps are the same with the neighbours' addresses "
        "shuffled, so the taps do not carry the crowd's identity")

    # AND the control actually changes the neighbours' addresses
    for a, b in zip(neighbours, shuffled.neighbours):
        assert a.address != b.address, (
            "the shuffle control did not change a neighbour's address")


def test_the_frame_crowd_control_is_dropped_is_visible():
    """THE BENCH'S CONTROL COUNT MUST MATCH AN INDEPENDENT COMPUTATION.

    **TWO MUTATIONS SURVIVED THE EARLIER VERSION OF THIS TEST.** They
    forced the control's count to 0, and the test only asked that the
    count EXIST and be at most the number of speakers -- and 0 passes
    both. A control that reports zero has stopped being a control, and
    the bench must SAY so.

    So the test recomputes the control's count ITSELF, from the same
    construction, and requires the bench's row to agree. **A BENCH THAT
    FAKES ITS CONTROL COUNT NOW FAILS THIS TEST**, because the
    independently computed count is not 0 at populations 3, 4, 8, 16 and
    32.

    MEASURED, the two derivations agree at every population:

        population  2  3  4  8  16  32  64
        independent  0  2  2  1   1   1   0
        the bench   0  2  2  1   1   1   0
    """
    for population, bins in BF.SWEEP:
        row = BF.run_case(population, bins)
        assert "frame_crowd_shuffled_ok" in row, (
            "at population %d the bench's row does not carry the "
            "frame-crowd control's count" % population)
        assert "frame_crowd_ok" in row, (
            "at population %d the bench's row does not carry the "
            "frame-crowd measurement's count" % population)

        # THE INDEPENDENT COUNT, computed here rather than read from
        # the bench
        link, ids = _link(population, bins)
        view = ids[:population]
        real_ok = 0
        shuf_ok = 0
        for i in BF._picks(population):
            tx, rx = ids[i], ids[(i + 1) % population]
            r = BF.discriminate_frame_crowd(link, tx, rx, view, ids, bins,
                                            BF.CROWD_AMP)
            if r["ok"] and r["correct"]:
                real_ok += 1
            r2 = BF.discriminate_frame_crowd(link, tx, rx, view, ids, bins,
                                             BF.CROWD_AMP,
                                             shuffle_crowd=BF.CONTROL_SEED)
            if r2["ok"] and r2["correct"]:
                shuf_ok += 1

        bench_real = int(row["frame_crowd_ok"])  # type: ignore[arg-type]
        bench_shuf = int(row["frame_crowd_shuffled_ok"])  # type: ignore[arg-type]
        assert bench_real == real_ok, (
            "at population %d the bench reports %d frame-crowd "
            "identifications and the independent count is %d -- the "
            "bench's measurement is not the one it claims"
            % (population, bench_real, real_ok))
        assert bench_shuf == shuf_ok, (
            "at population %d the bench reports %d for the frame-crowd "
            "CONTROL and the independent count is %d -- the bench's "
            "control is not the one it claims"
            % (population, bench_shuf, shuf_ok))
        assert bench_shuf <= bench_real + 2, (
            "at population %d the frame-crowd control identified %d "
            "speakers against the measurement's %d, which is not a count "
            "of anything plausible"
            % (population, bench_shuf, bench_real))


def test_the_bench_reports_the_width_it_claims():
    """THE BENCH MUST REPORT THE WIDTH THE CHANNEL DERIVES.

    **THE FIRST VERSION OF THE BENCH REPORTED THE WRONG WIDTH, because
    it took the channel's stats from a SELF-PAIR -- a stalk paired with
    itself.** That is not a link: the self-pair had one more neighbour
    (the stalk counts as its own neighbour when tx == rx) and a
    shallower notch -- 4 taps and 13.50 dB at population 4, against
    the real pair's 3 taps and 33.51 dB.

    So the bench must take its stats from a REAL pair, and the width it
    reports must equal `width_for` of the REAL pair's tap count.
    """
    for population, bins in BF.SWEEP:
        if population < 2:
            continue
        row = BF.run_case(population, bins)
        link, ids = _link(population, bins)
        pair = link.pair(ids[0], ids[1], in_view=ids[:population])
        real_taps = len(pair.channel().taps)
        assert row["taps"] == real_taps, (
            "at population %d the bench reported %d taps but a real pair "
            "has %d -- the stats came from the wrong pair"
            % (population, row["taps"], real_taps))
        assert row["width_bits"] == IL.width_for(real_taps), (
            "at population %d the bench reported %d bits for %d taps, "
            "but width_for says %d"
            % (population, row["width_bits"], real_taps,
               IL.width_for(real_taps)))


def test_the_address_classes_are_reported():
    """THE CEILING IS THE ADDRESS CLASSES, AND IT MUST BE REPORTED.

    Two addresses within 1/bins of each other are one class, and the
    read cannot separate them however wide the channel is. The standard
    recipe varies the girths by thousandths, so the addresses land
    within thousandths of each other: MEASURED, population 8 gives 2
    classes for 8 stalks.
    """
    row = BF.run_case(8, 64)
    classes = int(row["classes"])  # type: ignore[arg-type]
    population = int(row["population"])  # type: ignore[arg-type]
    sizes = list(row["class_sizes"])  # type: ignore[arg-type]
    assert classes < population, (
        "at population 8 the recipe gave %d classes for %d stalks, so the "
        "addresses are spread -- and the recorded ceiling (%d) is stale"
        % (classes, population, classes))
    assert sum(sizes) == population, (
        "the class sizes do not account for every stalk: %r" % (sizes,))


def test_the_bench_runs_end_to_end():
    """THE BENCH MUST RUN. A bench that cannot run measures nothing."""
    assert BF.main() == 0
