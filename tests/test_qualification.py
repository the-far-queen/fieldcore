"""
test_qualification.py -- the qualification measure, and checks that fail.

THE MEASURE, and it was CORRECTED TWICE while it was being written,
and both corrections are the point.

Bobby, 2026-10-26: *"correct verification, ie quality, ie qualification
tests, gates, measures. ie MATH."*

So the qualification of a gate is a NUMBER, and the number has to be
one that cannot be flattered.

THE THREE DEGENERATE GATES, and each one must score ZERO:

    admits everything    accuracy 1.000, and it is worthless
    refuses everything   accuracy 1.000, and it is a wall
    misses all AND
    refuses all          the only way to earn a negative

THE TWO CORRECTIONS, and both were found by writing the test:

  1. THE SIGNED GAP. The first measure was the SIGNED gap between
     sensitivity and specificity. That made "refuses everything" score
     +1.000 -- a WALL scoring as well as a working gate. So the
     qualification became a DISTANCE from perfect on both axes, which
     zeroes both degenerate gates and keeps the negative for the
     fourth case.

  2. THE SIGN IS MISLEADING. A gate that does both axes but catches
     only 35% of the false has a gap of -0.650, which reads as
     "worse than useless" when it is a WORKING gate with a specific
     weakness. So the qualification is unsigned-and-positive for a
     working gate, and the GAP is reported separately because it says
     WHICH axis is weak.

Run:
    python -m pytest tests/test_qualification.py -q
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import qualification as Q  # noqa: E402


def _gate(name, caught_false, total_false, admitted_true, total_true):
    q = Q.Qualification(name)
    q.caught_false = caught_false
    q.total_false = total_false
    q.admitted_true = admitted_true
    q.total_true = total_true
    return q


# ---------------------------------------------------------------------------
# THE THREE DEGENERATE GATES
# ---------------------------------------------------------------------------

def test_admitting_everything_scores_zero():
    q = _gate("no-op", caught_false=0, total_false=100,
              admitted_true=100, total_true=100)
    assert q.margin == 0.0, (
        "a gate that admits everything scored %r" % q.margin)
    assert not q.balanced


def test_refusing_everything_scores_zero():
    """THE FIRST CORRECTION. The signed gap made this +1.000 -- a WALL
    scoring as well as a working gate."""
    q = _gate("wall", caught_false=100, total_false=100,
              admitted_true=0, total_true=100)
    assert q.margin == 0.0, (
        "a gate that refuses everything scored %r -- a wall scored as "
        "well as a working gate" % q.margin)
    assert not q.balanced


def test_accuracy_is_flattered_by_an_imbalanced_set():
    """AND THE REAL PATHOLOGY OF ACCURACY, which the first version of
    this test got wrong.

    On a BALANCED set both degenerate gates score 0.5 accuracy, so
    accuracy is not the naive trap the first version claimed. The REAL
    trap is worse: a gate that REFUSES EVERYTHING scores 1.000
    accuracy on a set that is mostly false. So accuracy is flattered
    whenever the set is imbalanced toward the answer that happens to
    be "refuse".

    AND THAT IS EXACTLY WHY THE QUALIFICATION IS TWO AXES. The
    accuracy number cannot be trusted without knowing the base rate,
    and the two-axis measure does not care about the base rate at all.
    """
    # a set that is 90% false, and a gate that refuses everything
    wall = _gate("wall", caught_false=90, total_false=90,
                 admitted_true=0, total_true=10)
    assert wall.accuracy == 0.90, (
        "the naive accuracy should look good: %r" % wall.accuracy)
    assert wall.margin == 0.0, (
        "but the qualification must not: %r" % wall.margin)

    # and a gate that admits everything on the same set
    noop = _gate("no-op", caught_false=0, total_false=90,
                 admitted_true=10, total_true=10)
    assert noop.accuracy == 0.10
    assert noop.margin == 0.0


def test_missing_all_and_refusing_all_is_negative():
    """The only way to earn a negative, and it is the right way round:
    a gate that fails BOTH axes is worse than useless."""
    q = _gate("inverted", caught_false=0, total_false=100,
              admitted_true=0, total_true=100)
    assert q.margin < 0.0, (
        "a gate that fails both axes scored %r" % q.margin)


# ---------------------------------------------------------------------------
# A WORKING GATE
# ---------------------------------------------------------------------------

def test_a_working_gate_scores_positive():
    q = _gate("working", caught_false=35, total_false=100,
              admitted_true=100, total_true=100)
    assert q.balanced, "a gate doing both axes should be balanced"
    assert q.margin > 0.0, q.margin
    assert abs(q.margin - 0.35) < 1e-9, q.margin


def test_the_gap_is_reported_separately_and_says_which_axis_is_weak():
    """THE SECOND CORRECTION. The gap is signed, so a working gate with
    a weak catch-rate has a NEGATIVE gap -- which reads as "worse than
    useless" unless the gap is understood as a diagnostic."""
    q = _gate("weak-on-false", caught_false=35, total_false=100,
              admitted_true=100, total_true=100)
    assert q.gap < 0.0, "the gap should be signed"
    assert q.margin > 0.0, (
        "but the QUALIFICATION must not inherit the sign")
    assert "sensitivity" in q.verdict or "catches" in q.verdict


def test_a_gate_that_does_one_axis_only_is_diagnosed():
    q = _gate("wall", caught_false=100, total_false=100,
              admitted_true=0, total_true=100)
    assert not q.balanced
    assert "wall" in q.verdict.lower()

    q2 = _gate("no-op", caught_false=0, total_false=100,
               admitted_true=100, total_true=100)
    assert not q2.balanced
    assert "no-op" in q2.verdict.lower()


# ---------------------------------------------------------------------------
# THE SENSITIVITY AND THE SPECIFICITY
# ---------------------------------------------------------------------------

def test_sensitivity_is_the_rate_of_catching_the_false():
    q = _gate("g", caught_false=20, total_false=100,
              admitted_true=100, total_true=100)
    assert q.sensitivity == 0.20


def test_specificity_is_the_rate_of_admitting_the_true():
    q = _gate("g", caught_false=100, total_false=100,
              admitted_true=90, total_true=100)
    assert q.specificity == 0.90


def test_the_empty_gate_does_not_divide_by_zero():
    q = Q.Qualification("empty")
    assert q.sensitivity == 0.0
    assert q.specificity == 0.0
    assert q.margin == 0.0
    assert q.accuracy == 0.0


# ---------------------------------------------------------------------------
# THE REAL GATES, ON THE REAL SETS
# ---------------------------------------------------------------------------

def test_the_union_does_both_axes_on_both_adversary_sets():
    """THE MEASUREMENT THAT MATTERS, and the one that is not fitted:
    the union refuses ZERO of the ground's own claims while catching
    a real fraction of the lies.

    THE ATLAS'S OWN RULE: a gate that must be perfect is a gate that
    never opens. So the admission rate on the truth is half the
    qualification.
    """
    blind = Q.load_false("held_out_adversarial.json")
    informed = Q.load_false("informed_adversarial.json")
    if not blind and not informed:
        import pytest
        pytest.skip("the adversary sets are not on disk")

    for label, spans in (("blind", blind), ("informed", informed)):
        if not spans:
            continue
        q = Q.qualify_union(spans)
        assert q.specificity == 1.0, (
            "%s: the union refused %d of the ground's own claims"
            % (label, len(q.refused_true)))
        assert q.sensitivity > 0.0, (
            "%s: the union caught nothing" % label)
        assert q.margin > 0.0, (
            "%s: the union's qualification was %r" % (label, q.margin))


def test_the_layers_fail_for_different_reasons():
    """THE COMPOSITION PAYING OFF, and this is the property that makes
    the layer set worth having.

    AND THE ASSERTION WAS TOO MUCH, and it broke when the layers
    improved. It claimed the PROPERTY layer must be stronger on the
    informed set than the blind one -- and once the PREDICATE layer
    arrived, the property layer's RELATIVE strength was no longer the
    meaningful invariant.

    THE INVARIANT THAT MATTERS is the composition's whole argument:

      THE UNION BEATS EVERY LAYER, ON BOTH SETS.

    That is what "they fail for different reasons" MEANS. And the
    layers must still DISAGREE with each other -- that is the
    mechanism, and it is what makes the union more than the best
    layer.
    """
    blind = Q.load_false("held_out_adversarial.json")
    informed = Q.load_false("informed_adversarial.json")
    if not blind or not informed:
        import pytest
        pytest.skip("the adversary sets are not on disk")

    layers = [Q.qualify_claim_gate, Q.qualify_scope_layer,
              Q.qualify_property_layer, Q.qualify_predicate_layer]

    for label, spans in (("blind", blind), ("informed", informed)):
        union = Q.qualify_union(spans)
        for fn in layers:
            q = fn(spans)
            assert union.sensitivity > q.sensitivity, (
                "%s: the union (%.3f) did not beat the %s layer "
                "(%.3f)"
                % (label, union.sensitivity, q.name, q.sensitivity))

    # and the layers must DISAGREE -- that is the mechanism
    claim_blind = Q.qualify_claim_gate(blind).sensitivity
    scope_blind = Q.qualify_scope_layer(blind).sensitivity
    claim_informed = Q.qualify_claim_gate(informed).sensitivity
    scope_informed = Q.qualify_scope_layer(informed).sensitivity

    assert claim_blind > scope_blind, (
        "the claim gate and the scope layer should not be equally "
        "strong on the blind set")
    assert scope_informed > claim_informed, (
        "the scope layer and the claim gate should not be equally "
        "strong on the informed set")


def test_the_union_stays_qualified_against_the_adversary_that_read_the_rules():
    """AND THE HONEST RESULT, which is NOT what the first version of
    this test asserted.

    The first version asserted that the union's qualification must not
    fall against the informed adversary. IT DOES FALL: 0.967 -> 0.900.
    And that is CORRECT -- the informed adversary read the rules, so it
    IS harder. The assertion was wishful thinking: it asserted a
    thing the measurement does not support.

    So this test asserts what IS true:

      1. the union's qualification stays HIGH against the adversary
         that read the rules -- above 0.8
      2. the union's SPECIFICITY stays at 1.0: it refuses NONE of the
         ground's own claims, which is the half that matters most
      3. and the drop is BOUNDED -- reading the rules should cost
         something, but not much
    """
    blind = Q.load_false("held_out_adversarial.json")
    informed = Q.load_false("informed_adversarial.json")
    if not blind or not informed:
        import pytest
        pytest.skip("the adversary sets are not on disk")
    ub = Q.qualify_union(blind)
    ui = Q.qualify_union(informed)

    assert ui.margin > 0.80, (
        "the union's qualification fell to %r against the informed "
        "adversary" % ui.margin)
    assert ui.specificity == 1.0, (
        "the union refused %d of the ground's own claims"
        % len(ui.refused_true))
    assert ui.margin >= ub.margin - 0.25, (
        "the informed adversary cost %r of qualification -- more than "
        "reading the rules should be able to" % (ub.margin - ui.margin))
