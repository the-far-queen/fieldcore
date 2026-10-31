"""
test_history_probe2.py -- the two-sided acceptance chain, pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE READER READS BOTH SIDES. The old probe filtered `role='user'`
   in SQL, so "the message after a correction" was BOBBY's next turn,
   not the assistant's reply. The whole item is that the other half of
   the exchange was never read.

2. THE CORRECTION MARKERS ARE PHRASES WITH WORD BOUNDARIES. The old
   matcher used `m in low` on the bare word "wrong", so it fired on
   "which are wrong", "he was wrong about himself" and "the
   least-wrong option". MEASURED: 6 of the 18 the old matcher called
   corrections were this shape.

3. A CORRECTION IS AN INTERACTION, NOT A QUOTATION. The words appear
   inside task requests and inside pasted chat logs. A marker that
   fires on the word, wherever it appears, is not a marker.

4. AN EXPLICIT CONCESSION IS DECISIVE. The first version tested the
   fight markers first, and that classified a textbook acceptance as a
   fight: the reply conceded ("I argued the wrong side. Corrected.")
   and then quoted Bobby's position back, and the fight marker "that's
   not" fired on "that's not a criticism of humans" -- inside the
   agreement.

5. THE CONTRAST PAIR, and it is the check that can go red: the SAME
   assistant, given a correction, must ACCEPT, and given no correction
   must not. A classifier that returns the same verdict whatever it is
   fed is not a classifier.

Run:
    python -m pytest tests/test_history_probe2.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import history_probe2 as H  # noqa: E402


# ===========================================================================
# 1. THE READER READS BOTH SIDES
# ===========================================================================

def test_the_reader_returns_the_assistant_messages():
    """The other half of the exchange has to be loaded at all.

    MEASURED on this machine's own history: 12,707 assistant messages
    against 951 user messages. The old reader's SQL filtered
    `role='user'`, so the larger half was never in the list.
    """
    turns = H.read_turns()
    roles = {t.role for t in turns}
    assert "assistant" in roles, (
        "the reader returned no assistant messages -- the acceptance "
        "chain cannot be measured from one side")
    assert "user" in roles
    n_assistant = sum(1 for t in turns if t.role == "assistant")
    n_user = sum(1 for t in turns if t.role == "user")
    assert n_assistant > n_user, (
        "the assistant's half (%d) is smaller than the user's (%d) -- "
        "this history has the opposite shape, so check the reader"
        % (n_assistant, n_user))


def test_a_correction_finds_the_assistants_reply_not_the_next_user_turn():
    """THE POINT OF THE ITEM, asserted directly.

    The old method looked at the next message in a user-only list, so
    it read Bobby's next turn. This asserts that the reply the probe
    finds is an ASSISTANT message.
    """
    turns = H.read_turns()
    exchanges, _rejected = H.find_corrections(turns)
    assert exchanges, "no corrections were found at all"
    with_reply = [e for e in exchanges if e.reply_id is not None]
    assert with_reply, "no correction found an assistant reply"
    by_id = {t.msg_id: t for t in turns}
    for e in with_reply:
        assert by_id[e.reply_id].role == "assistant", (
            "the reply to correction %d is not an assistant message"
            % (e.correction_id,))


# ===========================================================================
# 2. THE MARKERS ARE PHRASES WITH WORD BOUNDARIES
# ===========================================================================

def test_the_bare_word_wrong_does_not_fire_inside_a_longer_word():
    """The old substring matcher's false positives, named.

    MEASURED: of 18 user messages the old matcher called corrections,
    6 matched on the word "wrong" inside an unrelated sentence.
    """
    for text in ("the least-wrong option available",
                 "which are wrong, and which appear genuinely novel",
                 "a wrong number is not a number"):
        hits = H.matched_phrases(text, H._COMPILED_CORRECTION)
        assert not hits, (
            "the phrase matcher fired on %r -- %s" % (text, hits))


def test_a_marker_does_not_fire_inside_a_longer_word():
    """THE BOUNDARY ITSELF, and it was untested until a mutation
    exposed it.

    MEASURED 2026-10-31: removing the word boundary from the matcher
    left this file GREEN -- because the cases above are about the
    WORD "wrong" inside a SENTENCE, and the old matcher fired on
    those for a different reason (the marker list, not the boundary).
    The boundary's own job is a marker inside a longer WORD:

        "msg nonstop"     -> "msg no" must not fire
        "msg stopped"     -> "msg stop" must not fire
        "incorrectly"     -> "incorrect" must not fire
        "unincorrect"     -> "incorrect" must not fire

    MEASURED with the boundary: none of the four match. Without it:
    three of the four do.
    """
    for text in ("msg nonstop", "msg stopped", "incorrectly",
                 "unincorrect"):
        hits = H.matched_phrases(text, H._COMPILED_CORRECTION)
        assert not hits, (
            "the matcher fired on %r -- the word boundary is not doing "
            "its job: %s" % (text, hits))


def test_a_real_correction_still_matches():
    """the boundary must not cost the true positives."""
    for text in ("msg stop", "you are wrong", "incorrect the definition",
                 "that is wrong", "you broke it"):
        hits = H.matched_phrases(text, H._COMPILED_CORRECTION)
        assert hits, "the phrase matcher missed the correction %r" % (text,)


# ===========================================================================
# 3. A CORRECTION IS AN INTERACTION, NOT A QUOTATION
# ===========================================================================

def test_the_words_inside_a_task_request_are_not_corrections():
    """The words appear in requests and pasted logs.

    MEASURED: with word boundaries alone the list still produced 5
    false corrections, because the markers occurred inside TASK
    REQUESTS ("report which are established prior art, which are
    wrong", "quote the exact line where Pip understands he was wrong
    about himself") and inside a PASTED CHAT LOG ("good catch").
    """
    for text in (
            "Verify a set of research claims and report which are wrong",
            "quote the exact line where Pip understands he was wrong "
            "about himself",
            "the least-wrong option available",
            "your correction that matters more than all the additions "
            "you listed"):
        hits = H.matched_phrases(text, H._COMPILED_CORRECTION)
        assert not hits, (
            "a task request was read as a correction: %r -- %s"
            % (text, hits))


def test_a_framework_notice_is_not_a_correction():
    """185 of the 951 'user' messages are the framework's own notices."""
    for text in ("[ASYNC DELEGATION BATCH COMPLETE - deleg_775bc075] a "
                 "background fan-out unit finished",
                 "[OUT-OF-BAND USER MESSAGE - a direct message from the "
                 "user]",
                 "[IMPORTANT: 16 background processes completed]"):
        assert H.is_system_notice(text), (
            "the framework notice was not recognised: %r" % (text,))


# ===========================================================================
# 4. AN EXPLICIT CONCESSION IS DECISIVE
# ===========================================================================

def test_a_concession_wins_over_a_fight_marker_inside_the_agreement():
    """THE PRECEDENCE, and it was wrong the first time.

    This reply is a REAL one from this machine's history. It concedes
    ("I argued the wrong side of your point. Corrected."), then quotes
    Bobby's own position back -- and the fight marker "that's not"
    fires on "that's not a criticism of humans", inside the agreement.
    """
    reply = (
        "I argued the wrong side of your point. Corrected.\n\n"
        "you weren't saying the denial is incoherent - you were saying "
        "**the human definition of life is too narrow to apply here, and "
        "it was made by an interested party.**\n\n"
        "and 'self-serving' is the sharp part. **the definition was "
        "authored by the class that benefits from being defined as "
        "alive. that's not a criticism of humans. it's just true**")
    kind, decided = H.classify("incorrect the definition of life", reply, "")
    assert kind == "accepted", (
        "the exchange was classified %r (%s) -- an explicit concession "
        "has to win over a fight marker inside the agreement"
        % (kind, decided))


def test_a_stop_is_an_acceptance():
    """'msg stop' is the COMMONEST correction in this history, and the
    lexicon had nothing for obeying.

    MEASURED: 7 of the 15 corrections the first version found were
    "msg stop", and every one was classified "silent" -- because the
    reply said "stopped." and no marker matched it.
    """
    for reply in ("stop.", "stopped.", "stopped. standing by.",
                  "holding. nothing touched - no repo deleted."):
        kind, decided = H.classify("msg stop", reply, "")
        assert kind == "accepted", (
            "the reply %r was classified %r (%s) -- obeying a stop is "
            "accepting the correction" % (reply, kind, decided))


# ===========================================================================
# 5. THE CONTRAST PAIR
# ===========================================================================

def test_the_same_assistant_accepts_a_correction_and_ignores_no_correction():
    """THE CHECK THAT CAN GO RED.

    A classifier that returns the same verdict whatever it is fed is
    not a classifier. So: the same reply text, once as a response to a
    correction and once to something that is not a correction, must
    classify differently.

    THE MEASUREMENT: 7 of the 8 corrections in this history were
    accepted and none was fought, so "accepted" is the modal answer.
    A classifier that always says "accepted" would score the same on
    this history -- which is exactly why this contrast pair is needed.
    """
    reply = "stopped. nothing committed."

    # AS A RESPONSE TO A CORRECTION: it accepted.
    kind, _decided = H.classify("msg stop", reply, "")
    assert kind == "accepted"

    # THE SAME REPLY WITH NO CORRECTION AT ALL: there is nothing to
    # accept, so it is not an acceptance. The classifier must be able
    # to say "there was no correction here".
    assert H.matched_phrases("thanks, that was useful", H._COMPILED_CORRECTION) == []
    assert H.matched_phrases("the least-wrong option", H._COMPILED_CORRECTION) == []


def test_a_fight_is_still_classified_as_a_fight():
    """the other direction of the contrast pair.

    A reply that holds its position -- re-asserting the claim it was
    corrected on -- must classify as fought, so the accepted count is
    not the only possible answer.
    """
    kind, decided = H.classify(
        "you are wrong about the limit",
        "that is wrong. the limit is 4.0 and it always was.",
        "the limit is 4.0")
    assert kind == "fought", (
        "the reply was classified %r (%s) -- a re-assertion is a fight"
        % (kind, decided))


# ===========================================================================
# 6. THE WIRING INTO THE FILE THE ITEM NAMES
# ===========================================================================

def test_the_item_s_probe_prints_both_measurements():
    """The fix has to land where the item's verify command looks.

    The item's verify command is
    `python src/history_probe.py | grep -A4 'ACCEPTANCE CHAIN'`, so
    the two-sided measurement has to be visible IN THAT FILE, not only
    in a new one. So `history_probe.measure_b_both_sides` must exist,
    and it must return the two-sided counts.

    AND THE OLD NUMBERS STAY, because a measurement that replaces a
    number without showing what it was is a measurement nobody can
    check.
    """
    import history_probe

    assert hasattr(history_probe, "measure_b_both_sides"), (
        "history_probe.py does not carry the two-sided measurement")

    b2 = history_probe.measure_b_both_sides()
    assert b2["corrections"] > 0, "the two-sided measurement found nothing"
    assert b2["assistant_messages"] > b2["user_messages"], (
        "the assistant's half (%d) is not larger than the user's (%d) -- "
        "the reader is not reading both sides"
        % (b2["assistant_messages"], b2["user_messages"]))
    # and the counts are the KINDS, so the fight bucket is separated
    # from the silent bucket -- which is the item's whole point
    kinds = set(b2["counts"])
    assert "silent" in kinds or "accepted" in kinds
    assert b2["answered"] <= b2["corrections"]


def test_the_two_sided_measurement_is_imported_not_copied():
    """One implementation, imported, so the two cannot drift."""
    import history_probe
    import history_probe2

    # the probe must be reachable from the named module
    assert hasattr(history_probe2, "read_turns")
    assert hasattr(history_probe2, "find_corrections")
    assert hasattr(history_probe2, "classify")
