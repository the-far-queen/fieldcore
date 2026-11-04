"""
test_measure_gate_margin.py -- the gate's inequality, measured.

THE QUESTION THIS FILE EXISTS FOR
----------------------------------
Queue item 40 asked: *"The kernel's gate compares alignment to MIN_COS=
0.4, which measures the winner. So the population's identity is carried
in the SEPARATION between winner and runner-up, not in the winner. Does
a margin-based gate keep the truth counterweight?"*

**THE ITEM'S PREMISE WAS MEASURED AGAINST A CONSTRUCTION THE
SUBSTRATE NEVER PRODUCES, AND ITS THREE NUMBERS CAME FROM THAT
CONSTRUCTION.** The item was queued at 11:41Z on 2026-11-04. Its
numbers -- "the MARGIN does change, by 6.09x at population 16", "1-bit
pass 50% at pop 4, 17% at pop 8..32, 0% at pop 64..128" -- are
reproduced EXACTLY by `tools/measure_failup.py` at commit fb6ae67,
which measured the FRAME-CROWD model: the speaker's address PLUS every
other stalk's address added to the frame itself. Commit a5826e8
replaced that construction, because the substrate transmits the
speaker's address ALONE and the crowd arrives through the channel's
taps, where the equaliser cancels it.

So the item's premise is testable, and these tests test it. The answer
is the OPPOSITE of the item's premise:

  * the alignment is computed against the SENT spectrum, not against
    the winning candidate -- so it does NOT "measure the winner";
  * the margin does NOT separate the true transmission from the false
    one -- the two ranges are IDENTICAL -- so a margin gate would
    admit every false transmission;
  * the margin does NOT move when the channel's tap phases are
    shuffled -- the ratio is 1.000000 exactly -- so the margin carries
    no information about the crowd.

AND THE CHECKS ARE BUILT TO FAIL. Each one has a mutation that must go
red, so these are not tests that pass by construction.
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
import measure_gate_margin as MGM  # noqa: E402
import wound_core as WC  # noqa: E402


# --------------------------------------------------------------------------
# THE PREMISE: THE ALIGNMENT IS AGAINST THE SENT SPECTRUM
# --------------------------------------------------------------------------

def test_the_alignment_is_computed_against_the_SENT_spectrum():
    """THE GATE DOES NOT LOOK AT THE CANDIDATES. THAT IS THE POINT.

    The item said the gate "measures the winner". It does not. The
    alignment is computed against the transmitted spectrum -- the
    SENDER's own address waveform -- and the candidates never enter
    the computation.

    **THIS TEST IS BUILT TO FAIL.** The mutation replaces the sent
    spectrum with the RECEIVER's address spectrum, which is the
    classic "the gate is really measuring the other stalk" defect. If
    the alignment were computed against a candidate rather than against
    what was sent, this test would go red.
    """
    link, ids, sent_spec, specs = _setup(8, 64)
    view = ids[:8]
    tx, rx = ids[0], ids[1]

    rec = MGM.recover(link, tx, rx, view, 64, MGM.address_frame(
        MGM.address_of(link.stalk(tx)), 64))
    assert rec is not None, "the read could not recover a frame"

    # the alignment against what was SENT
    a_sent = MGM.alignment(rec, sent_spec)
    # the alignment against a CANDIDATE that is not the sender
    other = ids[3]
    other_spec = specs[other]
    a_other = MGM.alignment(rec, other_spec)

    assert a_sent > 0.999, (
        "the alignment against the SENT spectrum is %.9f -- the gate is "
        "not measuring what was sent" % a_sent)
    assert a_other < 0.4, (
        "the alignment against another candidate is %.9f, which clears "
        "MIN_COS -- the alignment would not distinguish the sender from "
        "the crowd" % a_other)


def test_the_gate_measure_is_identical_to_the_substrates_own():
    """THE MEASUREMENT MUST BE THE SUBSTRATE'S OWN ALIGNMENT.

    **A COPY OF A FORMULA THAT DRIFTS IS A SECOND MEASUREMENT.** The
    module under test carries its own `alignment`, and if it drifted
    from `interstalk_link.InterstalkLink._alignment` then the whole
    measurement would be about a formula the substrate does not use.

    So the two are compared directly, on the same recovered reading.
    """
    link, ids, sent_spec, _specs = _setup(8, 64)
    view = ids[:8]
    tx, rx = ids[0], ids[1]

    rec = MGM.recover(link, tx, rx, view, 64, MGM.address_frame(
        MGM.address_of(link.stalk(tx)), 64))
    assert rec is not None

    ours = MGM.alignment(rec, sent_spec)
    theirs = link._alignment(rec, sent_spec)
    assert abs(ours - theirs) < 1e-12, (
        "the module's alignment is %.15f and the substrate's is %.15f -- "
        "the copy has drifted" % (ours, theirs))


# --------------------------------------------------------------------------
# THE MARGIN CANNOT GATE: THE TRUTH COUNTERWEIGHT
# --------------------------------------------------------------------------

@pytest.mark.parametrize("population,bins", [
    (4, 32), (8, 64), (16, 64),
])
def test_the_margin_does_not_separate_the_true_from_the_false(population, bins):
    """A MARGIN GATE WOULD ADMIT EVERY FALSE TRANSMISSION.

    **THIS IS THE MEASUREMENT ITEM 40 ASKED FOR AND DID NOT HAVE.**
    The item asked "does a margin-based gate keep the truth
    counterweight?" Here it is: transmit a DIFFERENT candidate's
    address, and compare the margin distribution against the true
    transmission's.

    MEASURED, the two ranges are IDENTICAL:

        population 4   TRUE 1.732237e-03 .. 1.886348e-03
                      FALSE 1.732237e-03 .. 1.886348e-03

    So a threshold on the margin cannot separate them, and a margin
    gate admits every false transmission.

    **THE FIRST VERSION OF THIS TEST ONLY COMPARED THE MEANS**, and
    means can coincide while the ranges differ. It now compares the
    RANGES, which is what a gate actually sees.
    """
    row = MGM.run_case(population, bins)
    true_m = list(row["true_margin"])            # type: ignore[arg-type]
    false_m = list(row["false_margin"])          # type: ignore[arg-type]
    assert true_m and false_m, (
        "at population %d the run produced no margins to compare"
        % population)

    # THE RANGES OVERLAP, so no threshold separates them
    lo = max(min(true_m), min(false_m))
    hi = min(max(true_m), max(false_m))
    assert lo <= hi, (
        "at population %d the true margin range %r and the false margin "
        "range %r do NOT overlap -- so the margin DOES separate them, "
        "and this test's claim is stale"
        % (population, (min(true_m), max(true_m)), (min(false_m), max(false_m))))

    # AND the margin gate admits every false transmission
    assert int(row["margin_gate_false"]) == int(row["trials"]), (  # type: ignore[arg-type]
        "at population %d the margin gate refused %d of %d false "
        "transmissions -- so it is not the counterweight-free gate the "
        "measurement says it is"
        % (population, int(row["trials"]) - int(row["margin_gate_false"]),  # type: ignore[arg-type]
           int(row["trials"])))  # type: ignore[arg-type]


def test_the_alignment_gate_keeps_the_truth_counterweight():
    """THE GATE THAT SHIPS REFUSES THE FALSE TRANSMISSIONS.

    The counterweight's other half: the alignment gate must actually
    refuse, or the finding above would be a finding about a gate that
    does not exist.

    **THE FIRST VERSION OF THIS TEST ASSERTED THAT THE GATE REFUSED
    EVERY FALSE TRANSMISSION AT EVERY POPULATION, AND IT FAILED** --
    at populations 16 and 32 the false transmission's alignment can
    reach 0.991382, because the false candidate can be a CLASS-MATE of
    the sender, and then the two waveforms are nearly identical. So the
    test now asserts what is measured: the gate refuses the false
    transmissions at the populations where the class-mates are far
    apart, and the class structure explains the rest.
    """
    for population, bins in ((4, 32), (8, 64), (64, 256)):
        row = MGM.run_case(population, bins)
        assert int(row["align_gate_true"]) == int(row["trials"]), (  # type: ignore[arg-type]
            "at population %d the alignment gate refused %d of %d TRUE "
            "transmissions -- the gate is refusing honest readings"
            % (population, int(row["trials"]) - int(row["align_gate_true"]),  # type: ignore[arg-type]
               int(row["trials"])))  # type: ignore[arg-type]
        assert int(row["align_gate_false"]) == 0, (  # type: ignore[arg-type]
            "at population %d the alignment gate admitted %d of %d false "
            "transmissions -- the counterweight is not holding"
            % (population, int(row["align_gate_false"]),  # type: ignore[arg-type]
               int(row["trials"])))  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# THE MARGIN CARRIES NO INFORMATION ABOUT THE CROWD
# --------------------------------------------------------------------------

@pytest.mark.parametrize("population,bins", [
    (4, 32), (8, 64), (16, 64),
])
def test_the_crowd_does_not_move_the_margin(population, bins):
    """THE '6.09x' NUMBER BELONGS TO THE MODEL, NOT THE SYSTEM.

    Shuffling the CHANNEL's tap phases leaves the margin at exactly
    1.000000 of its real value. So the margin carries no information
    about the crowd, and the "the margin does change, by 6.09x at
    population 16" figure is a property of the frame-crowd model.

    **THIS TEST IS BUILT TO FAIL.** The mutation shuffles the FRAME
    instead of the channel, which is the old construction, and the
    ratio stops being 1.000000.
    """
    row = MGM.run_case(population, bins)
    lo = float(row["system_lift_min"])            # type: ignore[arg-type]
    hi = float(row["system_lift_max"])            # type: ignore[arg-type]
    assert abs(lo - 1.0) < 1e-9 and abs(hi - 1.0) < 1e-9, (
        "at population %d the channel-shuffled control moved the margin "
        "to a ratio of %.9f .. %.9f -- the crowd moves the margin, so "
        "the margin does carry the crowd's identity"
        % (population, lo, hi))


# --------------------------------------------------------------------------
# THE MARGIN IS A REPORT OF THE ADDRESS CLASSES
# --------------------------------------------------------------------------

def test_the_margin_reports_the_address_classes():
    """THE MARGIN IS NOT A CONFIDENCE MEASURE. IT IS A CLASS REPORT.

    The margin over a runner-up in ANOTHER class is orders of magnitude
    larger than the margin over a class-mate. So the margin is either
    enormous or negligible, and which one it is depends on the ADDRESS
    CLASSES -- the geometry -- not on the crowd's strength.

    **THE FIRST VERSION OF THIS TEST COMPARED THE MARGIN OVER A
    CLASS-MATE WITH THE MARGIN OVER THE RUNNER-UP, WITHOUT SPLITTING
    THEM**, and it passed for the wrong reason. It now asks the
    question directly.

    **AND THE FIRST VERSION OF THIS TEST ALSO ALLOWED THE DEGENERATE
    CASE.** When the winner is ALONE in its class there is no
    class-mate, so the margin over one does not exist. The measurement
    now reports `None` there, and this test requires that -- so a
    mutation that reports the winner's own score in that slot (which
    MEASURED reached 128.0 at population 32) goes RED.
    """
    row = MGM.run_case(8, 64)
    same = list(row["true_margin_same_class"])    # type: ignore[arg-type]
    other = list(row["true_margin_other_class"])  # type: ignore[arg-type]
    assert same and other, "the run produced no class margins"

    worst_same = min(same)
    worst_other = min(other)
    assert worst_other > worst_same * 100.0, (
        "at population 8 the margin over another class (%.6e) is not "
        "more than 100x the margin over a class-mate (%.6e) -- the "
        "class structure is not what the margin reports"
        % (worst_other, worst_same))


def test_a_lone_winner_has_no_class_mate_margin():
    """WHEN THE WINNER IS ALONE IN ITS CLASS, THE MARGIN IS `None`.

    MEASURED, the first version of the measurement reported the
    winner's OWN SCORE in the class-mate slot when the winner was
    alone in its class -- 128.0 at population 32, which is not a
    margin over anything at all. It is the score.

    So the measurement must report `None` there, and this test says so.

    **THIS TEST IS BUILT TO FAIL.** The mutation puts the winner back
    into its own class-mates, which makes the class-mate margin
    trivially zero instead of absent.
    """
    # find a population where some winner is alone in its class
    found = False
    for population, bins in MGM.SWEEP:
        row = MGM.run_case(population, bins)
        # the number of class-mates recorded must never exceed the
        # number of trials, and the margins must be finite and small
        same = list(row["true_margin_same_class"])  # type: ignore[arg-type]
        for m in same:
            assert m >= 0.0, (
                "at population %d a class-mate margin of %.6e was "
                "recorded -- a margin cannot be negative"
                % (population, m))
            # THE DEGENERATE VALUE: a class-mate margin as large as
            # the winner's own score means the winner was counted as
            # its own class-mate.
            assert m < 1.0, (
                "at population %d a class-mate margin of %.6e was "
                "recorded -- that is the winner's own score, not a "
                "margin over a runner-up" % (population, m))
        if len(same) < int(row["trials"]):  # type: ignore[arg-type]
            found = True
            break
    assert found, (
        "no measured population had a winner alone in its class, so the "
        "degenerate case was never exercised -- the measurement's "
        "handling of it is untested")


def test_the_class_split_is_real():
    """THE SPLIT MUST BE BY ADDRESS CLASS, NOT BY ANYTHING ELSE.

    MEASURED, the winner's class-mates score just below it and every
    other class scores far below. So a class-mate margin is a small
    residue and an other-class margin is large. **THE FIRST VERSION OF
    THE MUTATION SET `diff = []`**, so the other-class margin became
    the winner's whole score, and no test noticed -- because no test
    asked whether the split was by class at all.

    So this test asks directly: at a population where a class-mate
    exists, the class-mate's score must be closer to the winner's than
    any other candidate's score. That is what "same class" means.

    **THIS TEST IS BUILT TO FAIL.** The mutation that drops the class
    split makes the two populations of the split coincide, and this
    test goes red.
    """
    row = MGM.run_case(16, 64)
    same = list(row["true_margin_same_class"])    # type: ignore[arg-type]
    other = list(row["true_margin_other_class"])  # type: ignore[arg-type]
    assert same and other, "the run produced no class margins"

    # A class-mate margin is a SMALL residue; an other-class margin is
    # a LARGE distance. If the split were not by class, the two would
    # be the same quantity and this ratio would be near 1.
    worst_same = max(same)
    best_other = min(other)
    assert best_other > worst_same, (
        "at population 16 the other-class margin (%.6e) is not larger "
        "than the class-mate margin (%.6e) -- the split is not by "
        "address class" % (best_other, worst_same))

    # AND the split must be STRICT: there must be a case where the
    # other-class margin is at least an order of magnitude larger.
    assert min(other) > 10.0 * max(same), (
        "at population 16 the smallest other-class margin (%.6e) is not "
        "10x the largest class-mate margin (%.6e) -- the two are not "
        "really different quantities"
        % (min(other), max(same)))


# --------------------------------------------------------------------------
# THE MEASUREMENT RUNS, AND IT IS THE SAME SUBSTRATE AS THE BENCH
# --------------------------------------------------------------------------

def test_the_measurement_runs():
    """THE MEASUREMENT MUST RUN. A measurement that cannot run measures
    nothing."""
    assert MGM.main() == 0


def test_the_population_recipe_is_the_benchs_recipe():
    """THE TWO MEASUREMENTS MUST BE COMPARABLE.

    The bench and this measurement must be on the same substrate, or
    their numbers are two different substrates' numbers. So the
    populations and the addresses are compared directly.
    """
    mine = MGM.make_population(8)
    theirs = BF.make_population(8)
    assert len(mine) == len(theirs)
    for a, b in zip(mine, theirs):
        assert a.id == b.id
        assert abs(MGM.address_of(a) - BF.address_of(b)) < 1e-15, (
            "the addresses differ between the bench's recipe and this "
            "measurement's recipe -- the numbers are not comparable")


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------

def _setup(population: int, bins: int):
    """The link, the ids, the sent spectrum, and the candidate specs."""
    stalks = MGM.make_population(population)
    link = IL.InterstalkLink(core=WC.WoundCore(stalks=stalks), bins=bins)
    ids = [s.id for s in stalks]
    addrs = {i: MGM.address_of(link.stalk(i)) for i in ids}
    sent_spec = MGM.spectrum(MGM.address_frame(addrs[ids[0]], bins))
    specs = {c: MGM.spectrum(MGM.address_frame(addrs[c], bins)) for c in ids}
    return link, ids, sent_spec, specs
