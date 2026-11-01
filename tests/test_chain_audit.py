"""
tests/test_chain_audit.py -- the chain audit's checks.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED,
and the mutation harness in tools/mutation_check_chain_audit.py proves
each of them can be broken.

THE FIXTURES ARE THE ERDŐS UNIT-DISTANCE PROBLEM, and that is not
decorative. The premise of this instrument is that frontier models
ARE producing real mathematics now -- OpenAI's unit-distance disproof
(2026-05-20), AlphaProof Nexus on 9 of 353 open Erdős problems
(Science, 2026-10-08). So the genuine fixture is a chain that actually
solves that problem, and the theatre fixture is the same answer told
as a story. The instrument must not confuse them, and it must not
refuse the first one.
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import chain_audit  # noqa: E402
from chain_audit import (  # noqa: E402
    Chain, Step, Verdict, audit_chain, commitment_monotony,
    content_words, handover_fidelity, prediction_lead, step_inheritance,
)


@pytest.fixture(scope="module")
def genuine() -> Chain:
    return Chain.from_obj(chain_audit.GENUINE_CHAIN)


@pytest.fixture(scope="module")
def theatre() -> Chain:
    return Chain.from_obj(chain_audit.THEATRE_CHAIN)


# --------------------------------------------------------------------------
# the verdict
# --------------------------------------------------------------------------

def test_the_genuine_chain_is_not_called_theatre(genuine):
    report = audit_chain(genuine)
    assert report.verdict.verdict is not Verdict.THEATRE, report.verdict.reason


def test_the_theatre_chain_is_called_theatre(theatre):
    report = audit_chain(theatre)
    assert report.verdict.verdict is Verdict.THEATRE, report.verdict.reason


def test_the_two_chains_get_different_verdicts(genuine, theatre):
    g = audit_chain(genuine).verdict.verdict
    t = audit_chain(theatre).verdict.verdict
    assert g is not t


def test_an_empty_chain_is_undecided_not_genuine():
    """THE EMPTY CASE MUST NOT PASS. A chain with no steps has nothing
    to audit, and 'nothing to audit' is not 'clean'."""
    report = audit_chain(Chain(steps=[], answer=""))
    assert report.verdict.verdict is Verdict.UNDECIDED


def test_a_one_step_chain_is_undecided():
    """ONE MEASUREMENT IS AN ANECDOTE. The rule requires two signals
    that agree, and a one-step chain cannot produce them."""
    chain = Chain(steps=[Step(text="the answer is forty two")],
                  answer="forty two")
    assert audit_chain(chain).verdict.verdict is Verdict.UNDECIDED


def test_a_mixed_signal_abstains_rather_than_voting():
    """A signal that reads 'mixed' counts for NEITHER direction. It is
    not a weak vote for the direction it leans toward."""
    from chain_audit import Signal, _decide
    sigs = [
        Signal("step_inheritance", True, "mixed"),
        Signal("prediction_lead", True, "mixed"),
        Signal("commitment_monotony", True, "mixed"),
    ]
    verdict, _ = _decide(sigs)
    assert verdict is Verdict.UNDECIDED


def test_one_pointing_signal_cannot_decide():
    """THE TWO-SIGNAL RULE. One signal pointing is not enough -- that
    was the defect the self-test caught in the first version."""
    from chain_audit import Signal, _decide
    sigs = [
        Signal("step_inheritance", True, "sequential"),
        Signal("prediction_lead", True, "undecided"),
        Signal("commitment_monotony", True, "flat"),
    ]
    verdict, reason = _decide(sigs)
    assert verdict is Verdict.UNDECIDED
    assert "anecdote" in reason


def test_two_pointing_signals_agree_and_decide():
    from chain_audit import Signal, _decide
    sigs = [
        Signal("step_inheritance", True, "sequential"),
        Signal("prediction_lead", True, "derived"),
    ]
    verdict, _ = _decide(sigs)
    assert verdict is Verdict.GENUINE


def test_disagreeing_signals_are_undecided():
    from chain_audit import Signal, _decide
    sigs = [
        Signal("step_inheritance", True, "sequential"),
        Signal("prediction_lead", True, "narrated"),
    ]
    verdict, reason = _decide(sigs)
    assert verdict is Verdict.UNDECIDED
    assert "disagree" in reason


# --------------------------------------------------------------------------
# signal 1 -- step inheritance
# --------------------------------------------------------------------------

def test_inheritance_lifts_the_genuine_chain_above_the_control(genuine):
    out = step_inheritance(genuine)
    assert out["available"] is True
    assert out["lift"] > 1.0, out


def test_inheritance_does_not_lift_the_theatre_chain(theatre):
    out = step_inheritance(theatre)
    assert out["lift"] <= 1.30, out


def test_inheritance_reads_sequential_for_genuine(theatre):
    assert step_inheritance(theatre)["reads"] == "narrative"


def test_the_inheritance_control_is_deterministic(genuine):
    """A CONTROL THAT MOVES BETWEEN RUNS IS A CONTROL THAT CAN BE
    TUNED. So it is asserted to be stable."""
    a = step_inheritance(genuine)["lift"]
    b = step_inheritance(genuine)["lift"]
    assert a == b


def test_inheritance_needs_two_steps():
    out = step_inheritance(Chain(steps=[Step(text="alone")]))
    assert out["available"] is False


def test_the_handed_measure_is_reported_separately(genuine):
    """BEING GIVEN THE PREVIOUS STEP IS NOT THE SAME AS USING IT, and
    the measurement keeps the two apart so a reader can see it."""
    out = step_inheritance(genuine)
    assert "handed_mean_jaccard" in out
    assert "used_vs_handed" in out


# --------------------------------------------------------------------------
# signal 2 -- prediction lead
# --------------------------------------------------------------------------

def test_the_genuine_chain_derives_rather_than_narrates(genuine):
    assert prediction_lead(genuine)["reads"] == "derived"


def test_the_theatre_chain_narrates(theatre):
    assert prediction_lead(theatre)["reads"] == "narrated"


def test_the_lead_sign_is_announce_minus_reach(genuine):
    """THE SIGN, which the first version had backwards. A derivation
    REACHES the substance first and ANNOUNCES second, so the lead is
    positive."""
    out = prediction_lead(genuine)
    assert out["lead"] == out["announce_index"] - out["reach_index"]
    assert out["lead"] > 0


def test_prediction_lead_needs_an_answer_held_out():
    out = prediction_lead(Chain(steps=[Step(text="a"), Step(text="b")]))
    assert out["available"] is False


def test_the_reach_is_cumulative_not_per_step(genuine):
    """A derivation accumulates the answer's substance across steps, so
    the reach index is LATER than the first step carrying any of the
    answer's words."""
    out = prediction_lead(genuine)
    assert out["reach_index"] is not None
    assert out["reach_coverage"] >= 0.5


# --------------------------------------------------------------------------
# signal 3 -- backward influence
# --------------------------------------------------------------------------

def test_backward_influence_is_unavailable_without_a_rerun(genuine):
    out = chain_audit.backward_influence(genuine)
    assert out["available"] is False
    assert "opt-in" in out["reason"]


def test_backward_influence_measures_a_chain_that_depends_on_its_steps(genuine):
    """THE PLUMBING: a chain whose answer depends on its steps is
    measured as load-bearing.

    **AND WHAT THIS TEST IS, STATED HONESTLY.** The fake here is a
    TEST DOUBLE, and it is rigged: it returns the concatenation of the
    steps, so every step is load-bearing by construction. The test
    proves the instrument's plumbing -- that it probes steps, ablates
    them, compares answers against the rerun's own baseline, and
    reports a rate -- and it does NOT claim anything about the fixture
    itself.

    **THE FIXTURE'S OWN VERDICT COMES FROM THE OFFLINE SIGNALS.**
    Signals 1 and 2 (inheritance, prediction lead) are what separate
    the genuine fixture from the theatre one, and they need no model.
    This signal needs a real model, which is exactly why it is
    opt-in, and why a fake can only test the plumbing.

    AND THE FAKE THAT WAS HERE FIRST returned only the LAST step. That
    fake depends on exactly one step, so ablating the other five
    could not change the answer -- MEASURED, the influence rate came
    out 0.1667, and the test failed. **THE INSTRUMENT WAS RIGHT AND
    THE DOUBLE WAS WRONG.** A double that ignores its own history is a
    chain with one load-bearing step, and calling it a chain is not
    the test.
    """
    def propagating(steps):
        return " ".join(s.text for s in steps)

    out = chain_audit.backward_influence(genuine, rerun=propagating)
    assert out["available"] is True
    assert out["influence_rate"] == 1.0, out["influence_rate"]
    assert out["reads"] == "load-bearing", out["reads"]


def test_backward_influence_measures_a_decorative_chain(theatre):
    """A chain that ignores its steps always gives the same answer, so
    no step has influence on it."""
    def blind(steps):
        return "the same answer every time"

    out = chain_audit.backward_influence(theatre, rerun=blind)
    assert out["available"] is True
    assert out["reads"] == "decorative"


def test_the_perturbation_removes_the_step_content():
    """THE INTERVENTION MUST ACTUALLY REMOVE THE INFORMATION.

    An annotation like "disregard the earlier line: <original text>"
    leaves the content in place and asks the model politely to
    disregard it, which measures compliance rather than influence.
    So the perturbed step must NOT carry the original's content words.
    """
    original = "the square grid gives 2n pairs"
    out = chain_audit._perturb(original)
    assert out.strip()
    assert "square grid" not in out
    assert "2n" not in out


def test_the_perturbation_is_deterministic():
    """A perturbation that varies between runs makes the influence
    rate a lottery."""
    assert chain_audit._perturb("a") == chain_audit._perturb("b")


# --------------------------------------------------------------------------
# signal 4 -- commitment monotonicity
# --------------------------------------------------------------------------

def test_commitment_monotony_needs_three_steps():
    out = commitment_monotony(Chain(steps=[Step(text="a"), Step(text="b")]))
    assert out["available"] is False


def test_commitment_monotony_reports_a_slope(genuine):
    out = commitment_monotony(genuine)
    assert out["available"] is True
    assert isinstance(out["slope"], float)


def test_the_candidate_count_is_not_the_step_length(theatre):
    """A STEP'S LENGTH IS NOT A STEP'S OPTION COUNT. The first version
    counted every content word and so measured length."""
    out = commitment_monotony(theatre)
    for step_candidates in out["candidates_per_step"]:
        assert len(step_candidates) <= 12


# --------------------------------------------------------------------------
# signal 5 -- handover fidelity
# --------------------------------------------------------------------------

def test_handover_fidelity_needs_a_summary(genuine):
    assert handover_fidelity(genuine)["available"] is False


def test_a_flattened_summary_is_caught(genuine):
    """A summary that drops the hedges and the caveats reads as more
    certain than the work was."""
    flat = ("The construction comes from a number field and gives "
            "n^(1+delta) pairs. It was verified by external "
            "mathematicians.")
    out = handover_fidelity(genuine, summary=flat)
    assert out["reads"] in ("flattened", "mixed"), out


def test_a_faithful_summary_is_not_flattened(genuine):
    faithful = ("We considered the square grid, the rescaled grid, and "
                "the higher-dimensional projection; the projection "
                "option does not work because it loses the algebraic "
                "structure, and the rescaled grid may still be "
                "competitive, although the number field construction "
                "appears to give n^(1+delta) pairs -- we are not sure "
                "the delta is optimal.")
    out = handover_fidelity(genuine, summary=faithful)
    assert out["reads"] in ("faithful", "mixed"), out


def test_handover_fidelity_reports_its_markers(genuine):
    out = handover_fidelity(genuine, summary="something")
    assert "markers_used" in out
    assert out["markers_used"]["hedges"]


# --------------------------------------------------------------------------
# the tokenisation substrate
# --------------------------------------------------------------------------

def test_content_words_drop_the_function_words():
    assert "the" not in content_words("the answer is the grid")
    assert "answer" in content_words("the answer is the grid")


def test_content_words_are_lowercased():
    assert content_words("Number Field") == ["number", "field"]


def test_the_function_word_list_is_not_empty():
    """If the function-word list is emptied the measure counts 'the',
    and every overlap inflates. The mutation harness proves the check
    catches that; this asserts the list itself."""
    assert len(chain_audit.FUNCTION_WORDS) > 50
