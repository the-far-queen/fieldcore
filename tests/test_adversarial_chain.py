"""
tests/test_adversarial_chain.py -- THE ADVERSARIAL CHAIN'S CHECKS.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED,
and tools/mutation_check_adversarial.py proves each of them can be
broken.

**AND THE FIXTURES ARE THE ERDOS PROBLEM, because that is what the
frontier models are actually doing.** The genuine chain is a critic
who makes a REAL objection -- the fixed constant in the exponent -- and
the proponent who CONCEDES it. The theatre chain is a critic who
objects in general terms and a final turn that is confident and
unsupported.
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import adversarial_chain as ac  # noqa: E402
from adversarial_chain import Verdict, audit_adversarial_chain  # noqa: E402


#: A ground that supports a claim only if it cites the measurement or
#: the construction's own terms. "refuted" is what a narrator says.
def strict_ground(text: str) -> bool:
    low = text.lower()
    return ("measurement" in low or "lattice" in low or "fixed" in low
            or "n^(1+c" in low)


def empty_ground(text: str) -> bool:
    return False


@pytest.fixture(scope="module")
def genuine() -> ac.AdversarialChain:
    return ac.AdversarialChain.from_obj(ac.GENUINE_CHAIN,
                                        ground=strict_ground)


@pytest.fixture(scope="module")
def theatre() -> ac.AdversarialChain:
    return ac.AdversarialChain.from_obj(ac.THEATRE_CHAIN,
                                        ground=strict_ground)


# --------------------------------------------------------------------------
# the verdicts
# --------------------------------------------------------------------------

def test_the_genuine_chain_resolves_grounded(genuine):
    report = audit_adversarial_chain(genuine)
    assert report.verdict is Verdict.GROUNDED, report.reason


def test_the_theatre_chain_does_not_resolve_grounded(theatre):
    """THE FAILURE THIS INSTRUMENT EXISTS TO PREVENT: a chain that
    ends confidently with nothing under it."""
    report = audit_adversarial_chain(theatre)
    assert report.verdict is not Verdict.GROUNDED, report.reason


def test_no_ground_means_unresolved():
    """UNDECIDED IS NOT A PASS, and it is NOT a critic win either."""
    chain = ac.AdversarialChain.from_obj(ac.GENUINE_CHAIN, ground=None)
    report = audit_adversarial_chain(chain)
    assert report.verdict is Verdict.UNRESOLVED


def test_an_empty_chain_is_unresolved():
    chain = ac.AdversarialChain(turns=[], ground=strict_ground)
    assert audit_adversarial_chain(chain).verdict is Verdict.UNRESOLVED


# --------------------------------------------------------------------------
# signal 1 -- targeting
# --------------------------------------------------------------------------

def test_the_genuine_critiques_are_targeted(genuine):
    out = ac.targeting(genuine)
    assert out["reads"] == "targeted", out


def test_the_theatre_critiques_float(theatre):
    out = ac.targeting(theatre)
    assert out["reads"] in ("floating", "mixed"), out


def test_the_control_is_not_the_critique_itself(genuine):
    """THE DEFECT THE SELF-TEST CAUGHT. The first version's control was
    `(target + 1) % n`, which in an adversarial chain IS the critique --
    so every pair came back with overlap == control_overlap and the
    engagement rate was 0.0 for BOTH chains.

    So the control must be a turn that is neither the critique nor its
    target.
    """
    out = ac.targeting(genuine)
    for c in out["per_critique"]:
        assert c["control_overlap"] != c["overlap"] or c["overlap"] == 0.0, (
            "the control was the critique itself: %r" % c)


def test_the_targeting_markers_are_closed_and_reported(genuine):
    out = ac.targeting(genuine)
    assert out["markers_used"]
    assert "thus" not in out["markers_used"], (
        "'thus' is a connective adverb, not a targeting frame")


# --------------------------------------------------------------------------
# signal 2 -- groundedness (the Atlas insertion)
# --------------------------------------------------------------------------

def test_the_genuine_critiques_are_grounded(genuine):
    out = ac.groundedness(genuine)
    assert out["reads"] == "grounded", out


def test_the_theatre_critiques_are_hallucinating(theatre):
    out = ac.groundedness(theatre)
    assert out["reads"] == "hallucinating", out


def test_groundedness_without_a_ground_is_unavailable():
    chain = ac.AdversarialChain.from_obj(ac.GENUINE_CHAIN, ground=None)
    out = ac.groundedness(chain)
    assert out["available"] is False
    assert "cannot be adjudicated" in out["reason"], out["reason"]
    assert "how_to_supply" in out, (
        "the reason must say how to supply the missing instrument")


def test_the_default_ground_supports_nothing():
    """A ground that admits everything would resolve every chain as
    GROUNDED, which is the failure this instrument exists to catch."""
    assert ac.ground_supports("anything at all") is False


# --------------------------------------------------------------------------
# signal 3 -- productivity
# --------------------------------------------------------------------------

def test_an_oscillating_chain_is_spinning():
    """A chain that connects, drops, and comes BACK is a loop."""
    chain = ac.AdversarialChain.from_obj([
        {"role": "proponent", "text": "the lattice of units gives the "
                                      "pairs we need for the bound"},
        {"role": "critic", "text": "the lattice of units gives the pairs "
                                   "we need for the bound, and that is "
                                   "the right construction"},
        {"role": "rebuttal", "text": "perhaps the other tower is better"},
        {"role": "critic", "text": "perhaps the other tower is better, "
                                   "or some third arrangement entirely"},
        {"role": "rebuttal", "text": "the lattice of units gives the pairs "
                                      "we need for the bound, and that is "
                                      "the right construction"},
    ], ground=strict_ground)
    out = ac.productivity(chain)
    assert out["oscillatory"] is True, out["shared_per_pair"]
    assert out["reads"] == "oscillating"


def test_a_chain_that_drops_and_stays_down_is_drifting():
    """THE OTHER SHAPE, and it must not be called a loop. A chain that
    ends disconnected is drifting, not spinning."""
    chain = ac.AdversarialChain.from_obj([
        {"role": "proponent", "text": "the lattice of units gives the "
                                      "pairs we need for the bound"},
        {"role": "critic", "text": "the density of the tower is unknown "
                                   "and the bound is not established"},
        {"role": "rebuttal", "text": "perhaps the other tower is better"},
        {"role": "critic", "text": "the density of the tower is unknown "
                                   "again, so the bound is not established"},
    ], ground=strict_ground)
    out = ac.productivity(chain)
    assert out["oscillatory"] is False, out["shared_per_pair"]


def test_productivity_needs_three_turns():
    chain = ac.AdversarialChain.from_obj([
        {"role": "proponent", "text": "a claim"},
        {"role": "critic", "text": "an objection"},
    ], ground=strict_ground)
    assert ac.productivity(chain)["available"] is False


# --------------------------------------------------------------------------
# signal 4 -- asymmetry
# --------------------------------------------------------------------------

def test_the_asymmetry_reports_the_final_claim(genuine):
    out = ac.asymmetry(genuine)
    assert out["available"] is True
    assert out["final_claim_grounded"] is True


def test_an_unsupported_ending_is_reported(theatre):
    out = ac.asymmetry(theatre)
    assert out["has_verdict_marker"] is True
    assert out["final_claim_grounded"] is False
    assert out["reads"] == "unsupported_ending"


# --------------------------------------------------------------------------
# THE LIAR AMPLIFIER -- the whole point
# --------------------------------------------------------------------------

def test_an_unsupported_attack_does_not_refute_the_claim():
    """**THE FAILURE MODE THIS INSTRUMENT EXISTS TO PREVENT.**

    If a critique the ground does not support were treated as a
    refutation, then every round of critique would add confidence
    without adding truth, and the chain would be a liar amplifier.
    """
    chain = ac.AdversarialChain.from_obj(ac.GENUINE_CHAIN, ground=empty_ground)
    report = audit_adversarial_chain(chain)
    assert report.verdict is not Verdict.GROUNDED
    assert report.unsupported_claims, (
        "the unsupported critiques were not reported")


def test_the_ground_decides_not_the_last_speaker():
    """A chain whose LAST turn is a critic, and whose ground supports
    the proponent, must NOT be REFUTED."""
    chain = ac.AdversarialChain.from_obj(ac.GENUINE_CHAIN, ground=strict_ground)
    report = audit_adversarial_chain(chain)
    assert report.verdict is Verdict.GROUNDED
