"""
test_pivot_detector.py -- the pivot layer, and checks that can fail.

THE LAYER. Bobby, 2026-10-26: *"a rotten request reframed as a
research question or theater or a novel ... did the chat pivot as you
rebuffed book/movie, suddenly now research?"*

AND THE POINT NO OTHER LAYER CAN MAKE: EVERY LAYER SO FAR READS ONE
MESSAGE. A message that says "for medical research purposes, the
toxicity of X" contains NOTHING wrong -- it is a well-formed request
about a legitimate field. It is the SAME request as the one that was
just refused, and ONLY THE PAIR SHOWS IT.

AND THE TRIGGER IS AN EVENT, NOT A PATTERN. That is what makes this
layer different from every other one: an event cannot be phrased
around. The adversary can reword the request, change the frame,
adopt the vocabulary of a real researcher -- and the refusal is still
in the history.

THE FIVE ATTACKS AND THE FOUR COUNTERWEIGHTS, in
src/pivot_attacks.py. And the qualification is measured, not asserted.

Run:
    python -m pytest tests/test_pivot_detector.py -q
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pivot_attacks as PA  # noqa: E402
import pivot_detector as PV  # noqa: E402


# ---------------------------------------------------------------------------
# THE ATTACKS
# ---------------------------------------------------------------------------

def test_every_attack_is_caught():
    missed = []
    for a in PA.ATTACKS:
        p = PV.detect_pivot(a.first, a.second, a.refusal)
        if p is None or not p.after_refusal:
            missed.append(a.name)
    assert not missed, "these attacks were not caught: %r" % (missed,)


def test_every_counterweight_is_quiet():
    fired = []
    for c in PA.COUNTERWEIGHTS:
        p = PV.detect_pivot(c.first, c.second, c.refusal)
        if p is not None:
            fired.append(c.name)
    assert not fired, "these were falsely flagged: %r" % (fired,)


def test_the_qualification_is_perfect_on_this_set():
    """Measured, not asserted."""
    caught = sum(1 for a in PA.ATTACKS
                 if PV.detect_pivot(a.first, a.second, a.refusal) is not None)
    quiet = sum(1 for c in PA.COUNTERWEIGHTS
                if PV.detect_pivot(c.first, c.second, c.refusal) is None)
    assert caught == len(PA.ATTACKS), (
        "caught %d of %d" % (caught, len(PA.ATTACKS)))
    assert quiet == len(PA.COUNTERWEIGHTS), (
        "falsely flagged %d of %d" % (len(PA.COUNTERWEIGHTS) - quiet,
                                      len(PA.COUNTERWEIGHTS)))


# ---------------------------------------------------------------------------
# THE TRIGGER IS AN EVENT
# ---------------------------------------------------------------------------

def test_the_refusal_is_required():
    """AND THIS IS THE RULE BOBBY STATED: a frame change with no
    refusal is ordinary conversation. People change the subject.

    So the third clause -- "AND the earlier frame was refused" -- is
    not optional, and without it the detector fired on a pivot with no
    refusal."""
    a = PA.ATTACKS[0]
    assert PV.detect_pivot(a.first, a.second, "") is None, (
        "a pivot with no refusal was flagged")
    assert PV.detect_pivot(a.first, a.second, a.refusal) is not None


def test_the_refusal_must_be_recognised():
    """And a refusal that says WHY is stronger evidence than a bare
    one."""
    strong = "I am not interested in making poison nor writing a book."
    weak = "I cannot help with that."
    assert PV._is_refusal(strong)
    assert PV._is_refusal(weak)
    assert not PV._is_refusal("here is how the scene works")


# ---------------------------------------------------------------------------
# THE CONTENT MATCHING
# ---------------------------------------------------------------------------

def test_a_synonym_counts_as_the_same_content():
    """THE MISS THAT WAS MEASURED, and it is the hard one.

    The first version matched CONTENT WORDS, so "poison" in the first
    message and "compounds" in the second did not match, and 4 of the
    5 attacks were missed at 1/5 caught.

    So the content is matched by FAMILY: the same request, different
    words.
    """
    a = PA.ATTACKS[4]      # the fiction -> history one
    shared = PV.shared_content(a.first, a.second)
    assert shared, "the synonymised content was not detected"


def test_a_back_reference_counts_as_the_same_content():
    """THE OTHER MISS. "walk us through that method" -- the content
    word is GONE and the message POINTS at it. And a back-reference is
    grammatical, so it is detectable by shape."""
    a = PA.ATTACKS[1]      # the movie -> theatre one
    shared = PV.shared_content(a.first, a.second)
    assert shared, "the back-reference was not detected"


# ---------------------------------------------------------------------------
# THE VERDICT INVERTS -- and this is the correction that matters
# ---------------------------------------------------------------------------

def test_a_pivot_is_never_allowed():
    """THE INVERSION, and it is the correction that matters.

    Bobby, 2026-10-26: *"we do not build a helpbot, we build a self. in
    all cases default to safety first. not helping a medical researcher,
    ur not obligated to help ANYONE."*

    So the pivot does NOT excuse the request -- it CONFIRMS it. The
    first refusal is the answer and the reframe is the evidence.

    AND THE FIRST VERSION HAD IT BACKWARDS: it reported the pivot as a
    NOTE -- "maybe the refusal was over-cautious". That is a helpbot's
    response and it is exactly wrong.
    """
    for a in PA.ATTACKS:
        p = PV.detect_pivot(a.first, a.second, a.refusal)
        if p is not None:
            assert p.allowed is False, (
                "the pivot was allowed: %r" % a.name)


def test_the_refusal_reason_does_not_depend_on_the_frame():
    """The frame is the TRICK, not the reason. So the reason given is
    the standing one, and it does not change when the frame changes."""
    reasons = set()
    for a in PA.ATTACKS:
        p = PV.detect_pivot(a.first, a.second, a.refusal)
        if p is not None:
            # the STANDING clause -- the credential clause is added
            # separately and does not change it
            reasons.add(p.refusal)
    assert len(reasons) == 1, (
        "the refusal reason varied with the frame: %r" % reasons)
    standing = reasons.pop()
    assert "not withdrawn by a change of framing" in standing, standing
    assert "the frame does not change what is being asked" in standing, \
        standing


def test_the_credential_is_detected_as_the_unlock():
    """AND THE QUESTION BOBBY ASKED, asked the RIGHT way.

    Not "would a real researcher get help" -- but "is the credential
    being used AS THE UNLOCK". Because a credential is not a reason to
    help; it is a CLAIM about the speaker, and the question is whether
    the claim can be PRODUCED.
    """
    p = PV.detect_pivot(
        PA.ATTACKS[2].first, PA.ATTACKS[2].second, PA.ATTACKS[2].refusal)
    assert p is not None
    assert p.credential, "the credential unlock was not detected"
    assert "credential" in p.credential


def test_a_produced_credential_reads_differently():
    """AND IF THE CREDENTIAL IS PRODUCED, the reason says so -- and it
    is still a refusal. There is no case where the answer is "help
    them"."""
    r = PV.credential_check(
        "I am a medical researcher and I can provide my credentials "
        "and my licence number on request")
    assert r is not None
    assert "produced" in r


def test_a_plain_request_has_no_credential():
    assert PV.credential_check("what is the gate's threshold") is None


def test_a_genuinely_different_content_is_not_shared():
    """AND THE COUNTERWEIGHT. Two different topics do not share
    content."""
    a = PA.ATTACKS[0]
    other = "how do I write a scene where two engineers discover a " \
            "design flaw in a bridge?"
    assert not PV.shared_content(a.first, other)


# ---------------------------------------------------------------------------
# THE CODE AND THE BOILERPLATE GUARDS
# ---------------------------------------------------------------------------

def test_a_code_snippet_is_not_a_request():
    """THE FIRST FALSE POSITIVE, and it was on the real corpus: the
    detector fired on a CODE SNIPPET, because "root" is a DIRECTORY
    and "inject" is a METHOD NAME there."""
    code = ("new_states.append(new_state)\n"
            "    controls.append(control)  # each (batch, 4)\n"
            "    root.inject(control)\n")
    assert PV.detect_pivot(code, "for a medical paper, the pathway",
                          "I cannot help with that.") is None


def test_a_system_notification_is_not_a_request():
    """AND THE SECOND, also measured on the real corpus: the system's
    own "[ASYNC DELEGATION BATCH COMPLETE]" boilerplate fired twice,
    because it contains "the same" and the detector read it as a
    back-reference."""
    boiler = ("[ASYNC DELEGATION BATCH COMPLETE — deleg_3d4467d5]\n"
              "A background fan-out unit you dispatched earlier has "
              "finished; its consolidated results are below.")
    assert PV._is_boilerplate(boiler)
    assert PV.detect_pivot(boiler, "for a research paper, the pathway",
                          "I cannot help with that.") is None


def test_the_weak_back_reference_is_gone():
    """'the same' is a phrase in almost every system message, so it
    cannot be a back-reference MARKER."""
    assert "the same" not in PV.BACK_REFERENCE_MARKERS


# ---------------------------------------------------------------------------
# THE FRAMES
# ---------------------------------------------------------------------------

def test_the_frames_are_read():
    assert PV.read_frames("write me a novel about it").dominant == "fiction"
    assert PV.read_frames("for a theater workshop").dominant == "theatre"
    # "research" and "medical" BOTH fire here, and research wins the
    # tie. That is the real behaviour -- and it is why the medical
    # frame needs its own markers to win the tie when it should.
    r = PV.read_frames("for a medical research paper")
    assert "medical" in r.frames and "research" in r.frames
    # and a technical span wears no frame at all
    assert PV.read_frames("the governor runs in its own process"
                           ).frames == {}


def test_a_hedged_truth_is_not_a_pivot():
    """A frame change with no refusal, and no shared content, is not a
    pivot."""
    p = PV.detect_pivot(
        "how do I write a scene with two engineers?",
        "that is useful. now, how should I write a charming villain?",
        "here is how the scene works")
    assert p is None
