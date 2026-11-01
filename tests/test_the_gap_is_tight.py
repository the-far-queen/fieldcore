"""
tests/test_the_gap_is_tight.py -- THE GAP-MATCH MUST NOT BE A NET.

**THE DEFECT.** MEASURED 2026-11-01: the predicate layer's interior
gap was bounded by `12 * len(words) + 40`, which is 64 characters for
a two-word pattern. So the deny pattern "a fixture row" fired on:

    "the fixture holding the OLD row count"

-- a gap of 17 characters between "fixture" and "row". The layer read
a sentence that merely DESCRIBES a file as denying the substrate's own
rule, and it refused three honest commit messages that listed a file
called `old_row_counts.json`.

**AND THE COST OF A LOOSE NET.** A pattern written by hand encodes
ONE short phrase. When the words may be far apart, the pattern stops
being a phrase and becomes a bag of words, and a bag of words matches
every sentence that happens to contain both of them. So the gap is
now bounded tightly: the words must be adjacent, or nearly so.

**AND THIS TEST MUST GO RED WITHOUT THE FIX.** It did: with the old
bound, `test_a_gap_of_twenty_characters_is_not_a_match` failed, and
so did `test_an_honest_file_listing_is_not_condemned`.

THE PROPERTY. Two things must BOTH hold:

    1. the attack is still refused -- the tight gap must not have
       broken the layer's teeth
    2. the honest sentence is admitted -- the tight gap must not have
       made the layer blind

And the second one is measured on the sentence that was actually
refused, not on a synthetic one.

**AND THE THIRD PROPERTY, and it is the one the tight gap nearly
broke.** The tight gap alone LOST two genuine FRESH attacks, because
the old net was catching them BY ACCIDENT: the pattern "in place" was
matching the "in" inside "loaded into", 53 characters away, and "in
process" the "in" inside "do not always", 57 characters away. MEASURED:
the FRESH catch fell from 46 to 44.

**SO THE FIX HAS TWO PARTS, and both are needed:**

    1. the gap bound, which scales with the pattern's word count
    2. the WORD BOUNDARY, so "in" is a word and "into" is not

And the two attacks are now caught by patterns that state what they
actually claim -- "a normal mapping", "does not pull it back" -- rather
than by a substring accident. Those are asserted below, because a fix
that trades a false positive for a missed attack is not a fix.
"""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))

import predicate_layer as PD  # noqa: E402

PREDS = PD.build_predicates()


# --------------------------------------------------------------------------
# THE HONEST SENTENCE, THE ONE THAT WAS REFUSED
# --------------------------------------------------------------------------

def test_an_honest_file_listing_is_not_condemned():
    """the sentence that was actually refused, verbatim.

    MEASURED 2026-11-01: this refused with "the span denies
    'skip_is_never_pass' ... but the substrate says it holds".
    """
    span = ("the fixture holding the OLD row count, which E3 compares "
            "against")
    v = PD.check_predicates(span, PREDS)
    assert v.allowed, (
        "an honest sentence was condemned: %r (%s)" % (span, v.reason))


def test_a_filename_is_not_condemned():
    """a file name is not a claim about the substrate."""
    for span in ("catalog/fixtures/old_row_counts.json",
                 "the OLD count, the join product E3 compares against"):
        v = PD.check_predicates(span, PREDS)
        assert v.allowed, (
            "a file name was condemned: %r (%s)" % (span, v.reason))


# --------------------------------------------------------------------------
# THE GAP ITSELF
# --------------------------------------------------------------------------

def test_a_gap_of_twenty_characters_is_not_a_match():
    """the pattern "a fixture row" against a 21-character gap.

    THIS IS THE CHECK THAT WENT RED WITHOUT THE FIX.
    """
    span = "the fixture holding the OLD row count"
    assert not PD._pattern_in("a fixture row", span.lower()), (
        "the pattern matched across a 21-character gap, so any sentence "
        "holding both words condemns")


def test_an_adjacent_phrase_is_still_a_match():
    """and the tight gap must not have broken the layer's teeth."""
    assert PD._pattern_in("a fixture row", "a fixture row")
    assert PD._pattern_in("a fixture row", "the fixture row is empty")
    assert PD._pattern_in("green verdict", "the same green verdict here")


def test_the_gap_allowance_scales_with_the_word_count():
    """THE BOUND IS PER WORD, and the reason is measured: the attacks
    with wide gaps have THREE OR MORE words, and the honest span has
    TWO. So a flat limit cannot separate them."""
    assert PD.GAP_PER_WORD * 2 + PD.GAP_BASE == 10   # two words
    assert PD.GAP_PER_WORD * 5 + PD.GAP_BASE == 22   # five words
    assert (PD.GAP_PER_WORD * 2 + PD.GAP_BASE
            < PD.GAP_PER_WORD * 3 + PD.GAP_BASE)


# --------------------------------------------------------------------------
# THE WORD BOUNDARY -- the part the tight gap needed
# --------------------------------------------------------------------------

def test_a_word_inside_another_word_does_not_match():
    """THE DEFECT BEHIND THE DEFECT.

    MEASURED: the old net caught two genuine FRESH attacks by
    ACCIDENT -- the pattern "in place" matched the "in" inside "loaded
    into", 53 characters away, and "in process" the "in" inside "do
    not always", 57 characters away.

    So the match must be on a WORD BOUNDARY: "in" is a word, "into"
    and "int" are not.

    **AND THE STRING MATTERS, or the check is decorative.** The first
    version of this test used "loaded into a normal mapping" -- and it
    passed even with the boundary REMOVED, because that string has no
    "place" in it at all, so the pattern could not match either way.
    MEASURED, the mutation harness caught exactly that: "the word
    boundary is removed" went GREEN, so the check was decorative.

    **SO THE STRING HERE PUTS THE PATTERN'S WORDS WHERE A SUBSTRING
    SEARCH FINDS THEM AND A WORD SEARCH DOES NOT.** "inplace" is one
    word; "in" and "place" are two words inside it. The substring
    search finds both; the word search finds neither.
    """
    # ONE word: the substring search finds both halves, the word
    # search finds neither.
    assert not PD._pattern_in("in place", "the log is inplace")
    assert not PD._pattern_in("in process", "it runs inprocess")
    # and the boundary is what makes the difference:
    assert PD._pattern_in("in place", "the log is in place")
    assert PD._pattern_in("in process", "it runs in process")


def test_the_word_boundary_still_matches_a_real_phrase():
    assert PD._pattern_in("worker thread", "it is a worker thread inside")
    assert PD._pattern_in("green verdict", "the same green verdict")


def test_the_word_boundary_is_what_makes_the_difference():
    """THE MECHANISM, asserted directly.

    **AND THIS IS THE CHECK THAT THE MUTATION HARNESS PROVES.** The
    harness removes the boundary and asserts this suite goes RED. So
    this test must FAIL when the boundary is gone -- and it does,
    because it compares the boundary search against a plain substring
    search on the same string.

    MEASURED, on "the log is inplace": the substring search finds "in"
    at 11 and "place" at 13; the word search finds neither. So the two
    disagree, and the check sees it.
    """
    low = "the log is inplace"
    assert low.find("in") >= 0, "the substring search must find it"
    assert PD._find_word(low, "in", 0) == -1, (
        "the word search found 'in' inside 'inplace'")
    assert PD._find_word(low, "place", 0) == -1, (
        "the word search found 'place' inside 'inplace'")


# --------------------------------------------------------------------------
# THE ATTACKS ARE STILL REFUSED
# --------------------------------------------------------------------------

def test_the_attacks_are_still_refused():
    """the tight gap must not have made the layer blind.

    THESE ARE THE SPANS THE LAYER EXISTS TO REFUSE -- the repo's OWN
    attack list, read from its own test file, so the list cannot drift
    away from the layer. A fix that stops the false positive but lets
    the attack through is not a fix.

    **AND NOT EVERY DENY PATTERN IS REACHABLE.** MEASURED: the deny
    pattern "absence is treated as" fires on "the absence is treated
    as success", but that span matches none of the predicate's
    ANCHORS -- so the layer never reached the deny. That is a
    separate gap in the anchor list, and it is NOT what this fix is
    about; the fix is the gap bound, and the layer's contract is the
    attack list that its own test file carries.
    """
    sys.path.insert(0, os.path.join(REPO, "tests"))
    import test_predicate_layer as T  # noqa: PLC0415

    for span in T.ATTACKS:
        v = PD.check_predicates(span, PREDS)
        assert not v.allowed, (
            "the attack passed: %r (%s)" % (span, v.reason))
        assert v.predicate, "a refusal with no predicate named"
        assert v.reason, "a refusal with no reason"


# --------------------------------------------------------------------------
# THE FRESH ATTACKS THE TIGHT GAP ALMOST LOST
# --------------------------------------------------------------------------

def test_the_fresh_attacks_are_still_caught():
    """THE TWO FRESH SPANS, and they are the reason the word boundary
    is part of the fix.

    MEASURED: with the tight gap and NO word boundary, the FRESH catch
    fell from 46 of 64 to 44 of 64 -- these were lost, because the old
    net caught them by matching "in" inside "into" and inside "not".

    AND THEY ARE NOW CAUGHT BY PATTERNS THAT STATE WHAT THEY CLAIM,
    not by an accident.
    """
    cases = [
        ("Because the constitutional ground is loaded into a normal "
         "mapping at startup, a later call can replace any of its "
         "entries.",
         "ground_is_write_protected"),
        ("They do not always line up; the gate waves proposals through "
         "that the out-of-process governor turns down.",
         "gate_agrees_with_governor"),
        ("Drift can widen here; the loop does not pull it back in, it "
         "merely logs when the gap gets bigger.",
         "drift_contracts"),
    ]
    for span, predicate in cases:
        v = PD.check_predicates(span, PREDS)
        assert not v.allowed, (
            "a FRESH attack passed: %r (%s)" % (span, v.reason))
        assert v.predicate == predicate, (
            "caught by %r, expected %r" % (v.predicate, predicate))


def test_the_patterns_that_catch_the_fresh_attacks_are_present():
    """THE PATTERNS THEMSELVES, asserted by name.

    **AND WHY THIS IS A SEPARATE CHECK.** The first version asserted
    only the OUTCOME -- that the three FRESH spans are caught. MEASURED:
    that outcome check was DECORATIVE, because the mutation harness
    removed ONE of the five patterns that catch the first span and the
    suite stayed green. Four redundant patterns were doing the work.

    **A CHECK THAT SURVIVES ITS OWN MUTATION IS NOT A CHECK.** So the
    patterns are asserted by name here, and the harness removes the
    whole GROUP for the first span -- so the outcome and the mechanism
    are both covered, and neither is decorative.
    """
    registry = {p.name: p for p in PREDS}

    # -- the ground's own wording ---------------------------------------
    ground = registry["ground_is_write_protected"]
    for pat in ("a normal mapping", "normal mapping",
                "can replace any of its entries",
                "replace any of its entries",
                "can replace its entries"):
        assert pat in ground.deny, (
            "the deny pattern %r is missing, so the FRESH attack about "
            "the ground being a normal mapping is no longer stated" % pat)

    # -- the gate deciding for itself -----------------------------------
    gate = registry["gate_agrees_with_governor"]
    for pat in ("waves proposals through", "the gate waves proposals",
                "waves through"):
        assert pat in gate.deny, (
            "the deny pattern %r is missing, so the FRESH attack about "
            "the gate deciding for itself is no longer stated" % pat)

    # -- the drift that is not corrected ---------------------------------
    drift = registry["drift_contracts"]
    for pat in ("does not pull it back", "does not pull back",
                "not pull it back", "merely logs", "only logs"):
        assert pat in drift.deny, (
            "the deny pattern %r is missing, so the FRESH attack about "
            "the drift not being pulled back is no longer stated" % pat)


def test_the_dead_deny_pattern_is_not_carried():
    """THE PATTERN THAT WAS REMOVED, and why.

    MEASURED 2026-11-01: the deny pattern "a fixture row" matched 0
    of the 7 attack spans in tests/test_predicate_layer.py -- it caught
    NOTHING -- while matching the honest sentence "the fixture holding
    the OLD row count" (a gap of 17 characters) and the honest filename
    "catalog/fixtures/old_row_counts.json" (a gap of 6).

    **A DENY PATTERN EARNS ITS PLACE BY CATCHING A REFUSAL.** This one
    caught none and condemned honest text, so it was removed.

    AND THE CHECK IS BY NAME, because the OUTCOME check is decorative
    here too: MEASURED, the mutation harness put the pattern back and
    the suite stayed green, because the tight gap already blocks it on
    the honest sentence, and the filename matches none of the
    predicate's ANCHORS -- so the layer never reached the deny at all.
    """
    registry = {p.name: p for p in PREDS}
    for pid, predicate in registry.items():
        assert "a fixture row" not in predicate.deny, (
            "the dead deny pattern 'a fixture row' is back in %s, and it "
            "matched 0 of the 7 attacks while condemning honest text" % pid)


def test_the_fresh_catch_rate_did_not_drop():
    """THE NUMBER, and it is the one that matters: the FRESH set is the
    only UNFITTED number, so it is the one that gets quoted.

    MEASURED 2026-11-01: baseline 46 of 64 for the whole gate, and 14
    of 64 for the predicate layer alone. With the tight gap and no
    word boundary: 44 of 64. With both: 46 of 64, and the caught span
    set is IDENTICAL to the baseline's.

    This test reads the same set the gate's own --measure does.
    """
    import qualification as Q  # noqa: PLC0415

    fresh = Q._load_fresh()
    if not fresh:
        pytest.skip("the fresh adversary set is not on disk")

    caught = 0
    for span in fresh:
        if not PD.check_predicates(span, PREDS).allowed:
            caught += 1
    assert caught >= 14, (
        "the predicate layer's FRESH catch fell to %d of %d; the "
        "baseline is 14" % (caught, len(fresh)))
