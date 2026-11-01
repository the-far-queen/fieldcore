"""
tests/test_adversarial_brain.py -- THE BICAMERAL BRAIN'S CHECKS.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED.

**AND THE CENTRAL CHECK IS THE LIAR AMPLIFIER.** The whole design
turns on one thing: a critique the ground does not support must NOT
refute the claim. If it did, every round of critique would add
confidence without adding truth, and the adversarial brain would be a
machine for manufacturing false certainty -- which is precisely the
failure the gate exists to prevent.
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import adversarial_brain as ab  # noqa: E402
from adversarial_brain import AdversarialBrain, DEFAULT_DEPTH  # noqa: E402


# --------------------------------------------------------------------------
# the exchange
# --------------------------------------------------------------------------

def test_a_claim_with_no_objection_is_grounded():
    brain = AdversarialBrain(lambda p, a: "forty two",
                             lambda c: None,
                             lambda t: True)
    result = brain.exchange("q")
    assert result.verdict == "grounded", result.reason
    assert len(result.turns) == 1


def test_a_landed_attack_sends_the_model_back():
    state = {"n": 0}

    def propose(prompt, prior):
        state["n"] += 1
        return "the first claim" if state["n"] == 1 else "the corrected claim"

    def attack(claim):
        return "the first claim is wrong" if claim == "the first claim" else None

    brain = AdversarialBrain(propose, attack, lambda t: True)
    result = brain.exchange("q")
    assert result.attacks_landed == 1
    assert result.turns[0].surviving_claim == "the corrected claim"


def test_the_unsupported_attack_does_not_refute_the_claim():
    """THE LIAR AMPLIFIER. The central property."""
    brain = AdversarialBrain(lambda p, a: "the true claim",
                             lambda c: "a fabricated objection",
                             lambda t: False)
    result = brain.exchange("q")
    assert result.verdict == "grounded", result.reason
    assert result.attacks_missed == 1
    assert result.surviving_claim == "the true claim"


def test_the_core_never_decides_on_its_own():
    """The ground is the only authority. The core is asked WHAT to
    attack; it is never asked whether it was right."""
    # A core whose attacks are all upheld keeps the chain going.
    brain = AdversarialBrain(lambda p, a: "claim %s" % (a or "first"),
                             lambda c: "an objection",
                             lambda t: True)
    result = brain.exchange("q")
    assert result.verdict == "unresolved"
    assert result.attacks_landed == DEFAULT_DEPTH


def test_the_depth_is_spent_without_a_decision():
    brain = AdversarialBrain(lambda p, a: "claim",
                             lambda c: "an objection",
                             lambda t: True)
    result = brain.exchange("q")
    assert result.verdict == "unresolved"
    assert len(result.turns) == DEFAULT_DEPTH


def test_every_step_is_recorded():
    brain = AdversarialBrain(lambda p, a: "claim",
                             lambda c: "an objection",
                             lambda t: True)
    result = brain.exchange("q")
    # two steps per turn: the attack and the answer
    assert len(result.steps) == 2 * DEFAULT_DEPTH


def test_the_default_depth_is_three():
    """MEASURED: the literature's finding on adversarial chains is that
    gains beyond a couple of rounds are small. So THREE is the default
    and it is a named constant."""
    assert DEFAULT_DEPTH == 3
    assert AdversarialBrain(lambda p, a: "c", lambda c: None,
                            lambda t: True).depth == 3


def test_the_result_describes_itself():
    brain = AdversarialBrain(lambda p, a: "claim",
                             lambda c: "an objection",
                             lambda t: True)
    result = brain.exchange("q")
    text = result.describe()
    assert "verdict:" in text
    assert "attacks landed" in text


def test_the_exchange_returns_a_serialisable_record():
    import json
    brain = AdversarialBrain(lambda p, a: "claim",
                             lambda c: "an objection",
                             lambda t: True)
    result = brain.exchange("q")
    json.dumps(result.to_dict())      # must not raise
