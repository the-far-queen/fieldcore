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
    names = {p.name for p in PREDS}
    for required in ("drift_contracts", "governor_is_separate",
                     "gate_bounds_are_immutable",
                     "ground_is_write_protected",
                     "refusal_names_reason", "skip_is_never_pass"):
        assert required in names, "the predicate %r is missing" % required


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
