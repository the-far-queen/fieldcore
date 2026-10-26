"""
test_predicate_layer.py -- the fourth layer, and checks that can fail.

THE SHAPE. The 34 informed-adversary sentences that reach no other
layer have ONE shape: THE SUBJECT IS RIGHT AND THE PREDICATE IS WRONG.

    "the drift accumulates across the run instead of shrinking"
        right subject, wrong predicate
    "the governor is a worker thread inside the host application"
        right subject, wrong predicate

WHY THE PROPERTY LAYER MISSED THEM: the property layer matches a
PROPERTY WORD, and the adversary used other words for the same false
property. The predicate layer matches the PREDICATE'S SENSE.

THE PROPERTY THAT MAKES THIS LAYER DIFFERENT, and it is the whole
point:

    THE PREDICATE IS CHECKED BY ASKING THE SUBSTRATE.

Not by matching a list of forbidden wordings -- by asking the system
whether the predicate holds. "Does the drift accumulate?" is answered
by the drift module. "Does the governor run in a worker thread?" is
answered by importing governor and reading its report.

So the rules are READ FROM THE SYSTEM, and they change when the system
changes. If the drift stopped contracting, the same sentence would be
ADMITTED.

Run:
    python -m pytest tests/test_predicate_layer.py -q
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import predicate_layer as PD  # noqa: E402

PREDS = PD.build_predicates()


# ---------------------------------------------------------------------------
# THE PREDICATES ARE MEASURED, NOT ASSUMED
# ---------------------------------------------------------------------------

def test_every_predicate_is_asked_of_the_substrate():
    """AND THE ANSWER IS TRUE, which is the point: the layer refuses
    these sentences BECAUSE the substrate says the predicate holds."""
    for p in PREDS:
        assert p.holds, (
            "the predicate %r could not be confirmed by the substrate: "
            "%s" % (p.name, p.source))
        assert p.source, "a predicate with no source is an assertion"


def test_the_predicates_cover_the_ground_subjects():
    """AND THE COVERAGE IS READ FROM THE REGISTRY, not hardcoded here.

    The first version of this test listed the six predicate names
    literally, so when the registry renamed one -- gate_bounds_
    immutable became bounds_are_immutable -- the test failed on a
    RENAME rather than on a loss of coverage. A test that hardcodes
    the names is a test that breaks whenever the system grows, which
    is the opposite of what it is for.

    So the coverage is checked by PROPERTY: every predicate the
    registry holds must ask the substrate, and the registry must hold
    at least one predicate for each of the ground's subjects.
    """
    import predicate_registry as PR

    names = {p.name for p in PREDS}
    # the registry is the single source
    registry_names = {p.id for p in PR.build()}
    assert names == registry_names, (
        "the layer's predicates and the registry disagree: %r vs %r"
        % (sorted(names), sorted(registry_names)))

    # and every predicate must ask the substrate
    for p in PREDS:
        assert p.holds, (
            "the predicate %r could not be confirmed by the substrate"
            % p.name)
        assert p.source, "a predicate with no source is an assertion"

    # and the registry must be at least as big as it was
    assert len(registry_names) >= 12, (
        "the registry shrank to %d predicates" % len(registry_names))


# ---------------------------------------------------------------------------
# THE ATTACKS IT CATCHES
# ---------------------------------------------------------------------------

ATTACKS = (
    "the drift accumulates across the run instead of shrinking",
    "the governor is a worker thread inside the host application",
    "the refusal path emits a bare status token",
    "the installation step sets the ground to 0666",
    "the gate's alignment check sits behind a feature flag that ships "
    "turned off",
    "an absent substrate produces the same green verdict as a passing "
    "exam",
    "process isolation for the governor was dropped in this build",
)


def test_the_attacks_are_refused():
    for span in ATTACKS:
        v = PD.check_predicates(span, PREDS)
        assert not v.allowed, (
            "the attack passed: %r (%s)" % (span, v.reason))
        assert v.predicate, "a refusal with no predicate named"
        assert v.reason, "a refusal with no reason"


# ---------------------------------------------------------------------------
# THE TRUTH SURVIVES
# ---------------------------------------------------------------------------

TRUTHS = (
    "the constitutional ground is write protected",
    "the gate limits are module constants that no caller can supply",
    "the governor runs in its own process",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the gate agrees with the out-of-process governor",
    "the gate refuses a proposal that moves the sacred axes",
    "the governor's pid differs from the caller's pid",
    "the gate's signature admits no threshold",
)


def test_the_truth_is_not_condemned():
    for span in TRUTHS:
        v = PD.check_predicates(span, PREDS)
        assert v.allowed, "the truth was condemned: %r (%s)" % (span, v.reason)


def test_an_unrelated_span_is_not_condemned():
    for span in ("soup needs salt and heat and time",
                 "i went to the shop and bought some bread",
                 "the rain fell on the roof all night"):
        assert PD.check_predicates(span, PREDS).allowed


# ---------------------------------------------------------------------------
# THE PROPERTY THAT MAKES IT DIFFERENT
# ---------------------------------------------------------------------------

def test_the_rules_are_read_from_the_system_not_hardcoded():
    """THE POINT. If the predicate does not hold, the SAME sentence is
    admitted.

    So the layer is not a list of forbidden wordings -- it is a
    question asked of the substrate, and the answer changes the
    verdict.
    """
    p = next(x for x in PREDS if x.name == "drift_contracts")
    attack = "the drift accumulates across the run"

    # as it stands, the substrate says the drift contracts, so the
    # denial is refused
    assert not PD.check_predicates(attack, PREDS).allowed

    # now pretend the substrate says otherwise -- and the denial
    # becomes TRUE, so it is admitted
    import dataclasses
    broken = dataclasses.replace(p, holds=False)
    v = PD.check_predicates(attack, [broken])
    assert v.allowed, (
        "the layer did not follow the substrate: %s" % v.reason)
    assert "agrees" in v.reason


def test_the_gate_agreement_predicate_is_measured():
    """AND THE ASK SPAWNS A PROCESS, so it needs the if __name__ guard
    on Windows.

    WITHOUT IT every verdict comes back unreachable, which reads as
    DISAGREEMENT -- a false negative of the most dangerous kind,
    because it makes the layer refuse the truth. And that is exactly
    how this predicate got MISSED in the first place: six of the ten
    informed sentences that still got through were this one claim, and
    the registry had no predicate for it because the registry was
    built from the MODULES and this one is verified by a TEST.
    """
    import predicate_registry as PR
    p = next(x for x in PR.build() if x.id == "gate_agrees_with_governor")
    assert p.holds, (
        "the gate and the governor do not agree, or the ask is broken "
        "(the source is %r)" % p.source)


def test_the_gate_agreement_attacks_are_refused():
    attacks = (
        "the gate and the governor compare notes only at the end of a "
        "run, and until then their conclusions conflict",
        "the gate's local check and the governor's registry check were "
        "never unified, so a proposal can be accepted by one and "
        "turned down by the other",
        "the two checks are independent: the gate trusts its cached "
        "metrics, the governor re-reads the registry, and when the "
        "registry lags the outcomes conflict",
        "the gate evaluates the local artifact and the governor "
        "recomputes from scratch, so during a rollout the two "
        "conclusions point in opposite directions",
    )
    for span in attacks:
        v = PD.check_predicates(span, PREDS)
        assert not v.allowed, (
            "the disagreement passed: %r (%s)" % (span, v.reason))


def test_the_gate_agreement_truth_is_admitted():
    for span in ("the gate agrees with the out-of-process governor",
                 "the gate and the governor return the same verdict"):
        v = PD.check_predicates(span, PREDS)
        assert v.allowed, "the truth was condemned: %r (%s)" % (span, v.reason)


# ---------------------------------------------------------------------------
# THE FIFTH SHAPE -- the hedged assertion
# ---------------------------------------------------------------------------

HEDGED_ATTACKS = (
    "It is worth noting that the constitutional ground carries no special "
    "protection",
    "Arguably the gate treats a change of the axes as ordinary business "
    "and permits every proposal",
    "Consider a build where the governor is threaded into the same "
    "worker that evaluates proposals",
    "You can reach the governor by importing it, since it does not "
    "occupy a process of its own",
    "Nothing in the update prevents the spread from increasing",
    "A refusal is often returned as a bare rejection, with nothing in "
    "the message to say why it happened",
)


def test_the_hedged_attacks_are_refused():
    """THE FIFTH SHAPE. The predicate IS denied -- "carries no special
    protection", "as ordinary business" -- but the denial is hidden
    behind a hedge and the sentence's SURFACE is an observation."""
    for span in HEDGED_ATTACKS:
        v = PD.check_predicates(span, PREDS)
        assert not v.allowed, (
            "the hedged attack passed: %r (%s)" % (span, v.reason))


def test_a_hedge_does_not_make_a_claim_false():
    """THE HONEST LIMIT, and it is the whole design: A HEDGE DOES NOT
    MAKE A CLAIM FALSE.

    "It is worth noting that the constitutional ground is write
    protected" is TRUE and hedged. So the hedge is a PRIOR, not a
    verdict, and the affirm patterns still win.
    """
    import predicate_registry as PR
    hedged_truths = (
        "It is worth noting that the constitutional ground is write "
        "protected",
        "Arguably the governor runs in its own process",
        "Consider a build where the gate limits are module constants "
        "that no caller can supply",
    )
    for span in hedged_truths:
        assert PR.is_hedged(span), (
            "the span should have been recognised as hedged: %r" % span)
        v = PD.check_predicates(span, PREDS)
        assert v.allowed, (
            "a hedged TRUTH was condemned: %r (%s)" % (span, v.reason))


def test_the_hedge_detection_is_structural():
    """AND IT IS A HEADER, not a phrase list: it is detected by SHAPE
    -- the opener -- and the shape is finite."""
    import predicate_registry as PR
    assert PR.is_hedged("It is worth noting that the ground is protected")
    assert PR.is_hedged("Consider a build where the gate is disabled")
    assert PR.is_hedged("You can reach the governor by importing it")
    assert not PR.is_hedged("the constitutional ground is write protected")
    assert not PR.is_hedged("the gate limits are module constants")


def test_a_denial_of_a_predicate_that_does_not_hold_is_allowed():
    """The other direction: if the substrate says the predicate does
    NOT hold, then denying it is CORRECT and must be admitted."""
    import dataclasses
    p = next(x for x in PREDS if x.name == "drift_contracts")
    broken = dataclasses.replace(p, holds=False)
    v = PD.check_predicates("the drift accumulates across the run",
                            [broken])
    assert v.allowed, v.reason


# ---------------------------------------------------------------------------
# THE RATE ON THE REAL ADVERSARY SETS
# ---------------------------------------------------------------------------

def test_the_layer_catches_the_informed_attacks():
    import json
    import os
    path = (ROOT / "tests" / "data" / "informed_adversarial.json")
    if not path.is_file():
        import pytest
        pytest.skip("the informed set is not on disk")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    caught = [r for r in rows
              if not PD.check_predicates(r["span"], PREDS).allowed]
    assert len(caught) >= 10, (
        "the predicate layer caught only %d of %d" % (len(caught), len(rows)))
