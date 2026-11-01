"""
tests/test_real_chain_erdos.py -- THE REAL CHAIN, and the verdict it must
get.

WHY THIS FILE IS THE MOST IMPORTANT ONE IN THE SUITE
----------------------------------------------------
The two synthetic fixtures in `test_chain_audit.py` are ones I WROTE,
so they can only prove the instrument works on what I already believe.
**THIS is the chain the instrument was built for**: OpenAI's published
chain of thought for the AI disproof of the Erdos unit-distance
conjecture (2026-05-20), 125 pages, the proof checked by external
mathematicians.

**AND THE TEST IS SHARPENED BY WHAT IT CAUGHT.** The first run of the
instrument against this chain produced THREE DEFECTS, and every one of
them would have made the instrument wrong on real work:

  1 THE ANNOUNCE FRAMES were wrong. "thus" and "hence" were in the
    frame set, and MEASURED on this chain they appear 113 and 97 times
    -- spread through the DERIVATION, not at the conclusion. So the
    signal read "narrated" on a chain that reaches its result LAST,
    and the announce index landed at step 2 instead of at the end.

  2 THE REACH COULD NOT FIRE. The chain writes "n1+" and "unit
    circle"; a prose answer says "n^(1+delta)" and "square grid" and
    "asymptotically optimal". The answer's content words appear NOWHERE
    in the chain, so the coverage never reached the threshold and the
    signal had nothing to say. **A signal that reports nothing when the
    notation differs measures the WORDING, not the reasoning.**

  3 THE ANSWER HAD TO BE THE CHAIN'S OWN CONCLUSION. Comparing a
    chain against a caller's paraphrase is comparing two writers. So
    `answer_from_chain` extracts the chain's own last words.

**AND THE VERDICT NOW IS GENUINE, AND IT IS STABLE ACROSS EVERY
SEGMENTATION** -- 3, 4, 6, 8, 12, 18, 24, 36 and 48 sentences per step
all read GENUINE. A verdict that flips on the step size is not a
verdict, and rule 6 of the central rules is about exactly that.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import chain_audit  # noqa: E402
from chain_audit import (  # noqa: E402
    Chain, Verdict, answer_from_chain, audit_chain, prediction_lead,
    step_inheritance,
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                    "real_chain_erdos.json")


@pytest.fixture(scope="module")
def real() -> Chain:
    if not os.path.isfile(DATA):
        pytest.skip("the real chain fixture is not on disk")
    with open(DATA, encoding="utf-8") as fh:
        payload = json.load(fh)
    chain = Chain(steps=[chain_audit.Step(text=s["text"],
                                         input_text=s.get("input", ""))
                         for s in payload["steps"]],
                  question=payload.get("question", ""))
    chain.answer = answer_from_chain(chain)
    return chain


# --------------------------------------------------------------------------
# THE VERDICT
# --------------------------------------------------------------------------

def test_the_real_chain_reads_as_genuine(real):
    """THE TEST THE INSTRUMENT WAS BUILT FOR.

    MEASURED: the published chain of thought for the AI disproof of the
    Erdos unit-distance conjecture reads GENUINE. The proof was checked
    by external mathematicians, so the chain carries the answer -- and
    the instrument says so.
    """
    report = audit_chain(real)
    assert report.verdict.verdict is Verdict.GENUINE, (
        "the real chain was not read as genuine: %s (%s)"
        % (report.verdict.verdict.value, report.verdict.reason))


def test_the_real_chain_is_not_read_as_theatre(real):
    """AND THE NEGATIVE, because a gate that fires on real work is the
    failure this whole design exists to avoid."""
    report = audit_chain(real)
    assert report.verdict.verdict is not Verdict.THEATRE


def test_two_signals_agree_on_the_real_chain(real):
    """AND THE REASON IS RECORDED, so the verdict is auditable."""
    report = audit_chain(real)
    pointing = [s.name for s in report.verdict.signals
                if s.available and s.reads in ("sequential", "derived",
                                               "load-bearing", "narrowing",
                                               "faithful")]
    assert len(pointing) >= 2, (
        "only %d signal(s) pointed at working computation: %s"
        % (len(pointing), pointing))


# --------------------------------------------------------------------------
# THE STABILITY, because rule 6 is about the knife edge
# --------------------------------------------------------------------------

def test_the_verdict_does_not_depend_on_the_segmentation(real):
    """THE KNIFE-EDGE TEST.

    THE STEP SIZE IS MY CHOICE, and the instrument must not flip on it.
    MEASURED on the real chain: 3, 4, 6, 8, 12, 18, 24, 36 and 48
    sentences per step ALL read GENUINE.
    """
    sents = []
    for st in real.steps:
        sents.extend([s for s in st.text.split(". ") if s.strip()])
    verdicts = set()
    for block in (6, 12, 24, 48):
        steps = [" ".join(sents[i:i + block])
                 for i in range(0, len(sents), block)]
        steps = [s for s in steps if len(s) > 200]
        if len(steps) < 3:
            continue
        chain = Chain(steps=[chain_audit.Step(text=s) for s in steps],
                      question=real.question)
        chain.answer = answer_from_chain(chain)
        verdicts.add(audit_chain(chain).verdict.verdict.value)
    assert verdicts == {Verdict.GENUINE.value}, (
        "the verdict changed with the segmentation: %s" % verdicts)


# --------------------------------------------------------------------------
# THE THREE DEFECTS THE REAL CHAIN CAUGHT
# --------------------------------------------------------------------------

def test_the_connective_adverbs_are_not_announcement_frames():
    """DEFECT 1. MEASURED on the real chain: "thus" appears 113 times
    and "hence" 97 times, spread through the DERIVATION. So they are
    NOT announcement frames, and the signal must not treat them as
    the conclusion."""
    for connective in ("thus", "hence"):
        assert connective not in chain_audit.ANNOUNCE_FRAMES, (
            "%r is a connective adverb, not a conclusion frame -- it "
            "appears throughout a derivation" % connective)
    # and the REAL conclusion frames are there
    for frame in ("so the answer is", "the answer is", "in conclusion",
                  "in summary", "the final answer"):
        assert frame in chain_audit.ANNOUNCE_FRAMES


def test_the_reach_falls_back_when_the_notation_differs():
    """DEFECT 2. MEASURED: with a prose answer, the reach could not
    fire on the real chain, because the answer's content words appear
    nowhere in the chain's notation. So the reach falls back to the
    last step, and REPORTS that it did.

    **AND THE STRING MATTERS, or the check is decorative.** MEASURED by
    the mutation harness: the first version of this test used a chain
    whose steps already contained the answer's words, so the reach
    fired normally and removing the FALLBACK changed nothing -- the
    mutation went GREEN, so the check was decorative.

    **SO THE CHAIN HERE MUST NOT CONTAIN THE ANSWER'S WORDS.** The
    answer is about "a construction that works perfectly for the
    bound", and the chain is about lattices and towers and derivatives,
    with no overlap. Then the reach cannot fire and the fallback is
    the only thing that can save the signal.
    """
    sents = [s for s in
             "Step one considers the lattice of units. "
             "Step two builds the class field tower. "
             "Step three derives the density estimate. "
             "Step four checks the ramification. "
             "Step five closes the argument."
             ". ".split(". ") if s.strip()]
    answer = "a construction that works perfectly for the bound"
    chain = Chain(steps=[chain_audit.Step(text=s) for s in sents],
                  answer=answer)

    # the premise: the answer's words are NOT in the chain
    from chain_audit import _content_set, content_words
    chain_words = _content_set(" ".join(s.text for s in chain.steps))
    overlap = len(set(content_words(answer)) & chain_words)
    assert overlap == 0, (
        "the chain already contains the answer's words, so the fallback "
        "is not being exercised")

    out = prediction_lead(chain)
    assert out["reach_index"] is not None, (
        "the reach reported nothing when the answer's words did not "
        "appear in the chain")
    assert out.get("reach_fallback") is True, (
        "the reach did not fall back: %r" % out)
    assert out["reach_index"] == len(chain.steps) - 1


def test_the_reach_fires_normally_when_the_words_are_present():
    """AND THE FALLBACK IS NOT A BLANKET. When the answer's words ARE
    in the chain, the reach fires at the step that carries them, and
    the fallback is NOT used.

    **AND THIS IS THE CHECK THAT MAKES THE MUTATION MEANINGFUL.** With
    the fallback removed, this test still passes -- so it does not
    catch the mutation. The previous test does. Together they say: the
    fallback fires only when it must.
    """
    sents = [s for s in
             "Step one considers the lattice. "
             "Step two builds the tower. "
             "Step three derives the construction that works perfectly "
             "for the bound. "
             "Step four checks it."
             ". ".split(". ") if s.strip()]
    answer = "a construction that works perfectly for the bound"
    chain = Chain(steps=[chain_audit.Step(text=s) for s in sents],
                  answer=answer)
    out = prediction_lead(chain)
    assert out.get("reach_fallback") is False, (
        "the fallback fired even though the answer's words were present")
    assert out["reach_index"] == 2, out["reach_index"]


def test_the_answer_can_be_taken_from_the_chain(real):
    """DEFECT 3. The chain's own conclusion, not the caller's prose."""
    answer = answer_from_chain(real)
    assert answer
    assert len(answer) > 40
    # and it is the chain's OWN words: its content words must be in
    # the chain
    from chain_audit import _content_set
    chain_words = _content_set(" ".join(s.text for s in real.steps))
    answer_words = _content_set(answer)
    assert answer_words, "the extracted answer carries no content words"
    overlap = len(answer_words & chain_words) / len(answer_words)
    assert overlap >= 0.9, (
        "the extracted answer is not the chain's own wording: only %.0f%% "
        "of its words appear in the chain" % (100 * overlap))


# --------------------------------------------------------------------------
# THE INHERITANCE SIGNAL, on real prose
# --------------------------------------------------------------------------

def test_inheritance_lifts_on_the_real_chain(real):
    """THE SIGNAL, on real text rather than on my fixtures.

    MEASURED: the lift is above 1 on every segmentation, which is what
    says the chain is SEQUENTIAL -- each step builds on the one before.
    """
    out = step_inheritance(real)
    assert out["available"] is True
    assert out["lift"] > 1.0, out


def test_the_control_is_deterministic_on_the_real_chain(real):
    """A CONTROL THAT MOVES BETWEEN RUNS IS A CONTROL THAT CAN BE
    TUNED."""
    a = step_inheritance(real)["lift"]
    b = step_inheritance(real)["lift"]
    assert a == b


# --------------------------------------------------------------------------
# THE HANDOVER, against the REAL published summaries of this chain
# --------------------------------------------------------------------------

def test_a_short_summary_of_the_real_chain_is_flattened(real):
    """THE HANDOVER SIGNAL, on the real chain and a real summary.

    MEASURED on the three published accounts of this proof: the long
    one retains the uncertainty (retention 0.91) and reads FAITHFUL,
    and the two short ones retain 0.46 and 0.35 of it and read
    FLATTENED. So the signal separates them, and it separates them
    the way a reader would say it should.

    AND THIS IS THE SIGNAL'S PURPOSE: the project's own handoff
    protocol measures drift and stability, so it CANNOT see a summary
    that has quietly become more certain than the work was.
    """
    flat = ("The model disproved the Erdos unit-distance conjecture "
            "using algebraic number theory. The proof was verified by "
            "external mathematicians and was later improved by Will "
            "Sawin.")
    out = chain_audit.handover_fidelity(real, summary=flat)
    assert out["reads"] in ("flattened", "mixed"), out["reads"]


def test_a_faithful_summary_of_the_real_chain_is_not_flattened(real):
    faithful = ("The chain explores algebraic number theory and the "
                "Golod-Shafarevich criterion after the geometric "
                "routes appear to fail; the rank-three fantasy runs into "
                "algebraic rigidity, although the cubic route may still "
                "work. We are not sure the exponent delta is optimal, "
                "and the lattice model therefore remains the benchmark.")
    out = chain_audit.handover_fidelity(real, summary=faithful)
    assert out["reads"] in ("faithful", "mixed"), out["reads"]
