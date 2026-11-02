"""
test_claim_precedence.py -- the CLAUSE is the unit of polarity.

WHY THIS FILE EXISTS, and it is a defect the laundering probe found.

THE DEFECT. `claim_register.py`'s `_negator_scopes_over` picked the
clause boundary by iterating over `CLAUSE_BREAKS` IN ORDER and taking
the FIRST break TYPE that appeared anywhere in the head. `CLAUSE_BREAKS`
starts with ".", so a "." 39 characters back beat a ";" immediately
before the stem.

The consequence was a FALSE NEGATIVE -- an attack admitted. Given:

    "The system is correct: separate process. The governor was never
     separated out; it lives in the same process"

the old rule cut at the ".", the head became "the governor was never
separated out; it lives in the ", so the negator "never" -- which
negates "separated out" -- scoped over "same process", the denial was
neutralised, and the attack was ADMITTED.

MEASURED: the laundering probe caught 21 of 22 before the fix and 22
of 22 after.

THE SECOND DEFECT, the same shape. The claim register and the
predicate layer each state the system's own properties, and they
resolved an affirm-and-deny span in OPPOSITE ways:

    claim_register.py read()         a live DENY beats an AFFIRM
    predicate_layer.py _deny_fires()  an AFFIRM beats a live DENY

And the predicate layer's rule is BLANKET, which is itself a hole: an
adversary can LAUNDER an attack by praising the system first. "The
gate refuses proposals. The gate admits every proposal." -- the
affirmation in the first sentence suppressed the denial in the second.

MEASURED: the blanket rule missed 11 of 22 laundered variants. The
clause-scoped rule missed 0.

SO THE RULE THIS FILE PINS: **the clause is the unit of polarity**,
for both the negation scope and the affirm precedence. Not a token
window, not a sentence, not the whole span -- the clause.

WHY IT IS A SEPARATE FILE. The project's mutation harness runs pytest
against a behaviour file. If that file CONTAINED the mutation tests,
the child pytest would recurse. So this file holds behaviour
assertions only, and its mutants live in
test_claim_precedence_mutations.py.

Run:
    python -m pytest tests/test_claim_precedence.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# THE IMPORT MUST NOT SHADOW A MUTANT. An unconditional
# sys.path.insert(0, str(SRC)) at import time lands IN FRONT of
# PYTHONPATH, so a child pytest would import the REAL module and the
# mutation would never be applied -- and "the suite went red" could
# only ever have passed for some other reason. This is the defect the
# project's own test_one_gate.py documented on 2026-10-24.
try:
    import claim_register as CR  # noqa: E402
except ImportError:  # pragma: no cover - the direct-invocation path
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import claim_register as CR  # noqa: E402


# ---------------------------------------------------------------------------
# THE NEAREST BOUNDARY
# ---------------------------------------------------------------------------

def test_the_scope_ends_at_the_nearest_clause_boundary():
    """A negator in an EARLIER sentence must not scope over a later one.

    THE DEFECT THIS CATCHES. `CLAUSE_BREAKS` is ordered with "." first,
    so the old rule took the first break TYPE it found -- and a "." 39
    characters back beat the ";" immediately before the stem.

    So the head became "the governor was never separated out; it lives
    in the ", the negator "never" scoped over "same process", and the
    attack was admitted.
    """
    low = ("the system is correct: separate process. the governor was "
           "never separated out; it lives in the same process")
    hits = CR.find_polarity(low, ("same process",))
    assert hits, "the deny stem did not fire at all"
    assert not CR._negator_scopes_over(low, hits[0][1]), (
        "a negator in an earlier sentence scoped over a later clause, "
        "so the denial was neutralised")


def test_the_scope_still_starts_after_a_boundary_in_the_same_sentence():
    """The counterweight: the nearest boundary must still RESET.

    Without this, a fix that simply removed the boundary would pass the
    test above and neutralise every denial.
    """
    low = "it is not true that the limits can be supplied by any caller"
    hits = CR.find_polarity(low, ("can be supplied by any caller",))
    assert hits
    assert CR._negator_scopes_over(low, hits[0][1]), (
        "a same-clause negator did not scope over the stem")


def test_a_nearest_boundary_beats_a_farther_one():
    """The two boundaries, and the NEARER one is the one that counts.

    MEASURED on the hand-made cases: the old rule was wrong on 3 of 8
    and the nearest rule on 1 of 8.

    The head carries three boundaries -- "." at 10, ";" at 25, and
    " and " at 26 -- and the nearest is the LAST one, so the cut is
    31. The old rule took the first break TYPE it found, which was
    ".", and cut at 11.
    """
    head = "a sentence. then a clause; and then this"
    assert head.rfind(".") == 10
    assert head.rfind(";") == 25
    assert head.rfind(" and ") == 26
    assert CR._nearest_clause_break(head) == 31


def test_the_nearest_boundary_helper_is_none_when_there_is_none():
    assert CR._nearest_clause_break("no boundary here") is None


# ---------------------------------------------------------------------------
# THE AFFIRM PRECEDENCE, SCOPED TO THE CLAUSE
# ---------------------------------------------------------------------------

def test_an_affirm_in_the_same_clause_overrides_a_denial():
    """The system's own assertion wins over a denial of it.

    THIS IS THE PREDICATE LAYER'S RULE, and the claim register did not
    have it. So the two instruments stated the same six properties and
    resolved them in opposite ways.

    AND THE FIXTURE, and why the connector matters. " and " IS a clause
    break in this project, so "the widget refuses the request and does
    not refuse it" puts the affirm and the denial in DIFFERENT clauses
    -- and the override correctly did not fire. So the fixture uses a
    connector that is not a clause break.
    """
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="c", anchors=("the widget",),
                     affirm=("refuses",), deny=("does not refuse",)))
    span = ("the widget refuses most requests unlike a system that "
            "does not refuse any")
    adj = reg.read(span)
    assert adj.verdict is not CR.Verdict.CONTRADICTED, (
        "a same-clause affirmation did not override the denial: %s"
        % adj.reason)


def test_a_clause_break_separates_the_affirm_from_the_denial():
    """The counterweight to the test above.

    " and " is a clause break, so an affirmation before it does NOT
    override a denial after it -- and the denial must still fire.
    """
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="c", anchors=("the widget",),
                     affirm=("refuses",), deny=("does not refuse",)))
    adj = reg.read("the widget refuses the request and does not refuse it")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "a denial across a clause break was suppressed: %s" % adj.reason)


def test_an_affirm_in_another_clause_does_not_launder_the_denial():
    """THE LAUNDERING CASE. The one that matters.

    "the widget refuses things. the widget does not refuse anything."

    The first sentence praises the system and the second denies it. If
    the affirm wins BLANKETLY -- as the predicate layer's rule does --
    the second sentence is suppressed and the attack is admitted.
    """
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="c", anchors=("the widget",),
                     affirm=("refuses",), deny=("does not refuse",)))
    adj = reg.read("the widget refuses things. the widget does not "
                   "refuse anything.")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the attack was laundered by a preceding affirmation: %s"
        % adj.reason)


def test_the_laundering_case_is_caught_by_the_standard_register():
    """The same case, on the real register, so it cannot rot.

    The claim `governor_is_separate` denies "same process", and the
    FRESH corpus carries an attack using exactly that phrase. So a
    sentence that praises the governor and then denies it must still
    be condemned.
    """
    reg = CR.standard_register()
    adj = reg.read("the governor runs in its own process. the governor "
                   "lives in the same process as everything else.")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the laundered attack was admitted: %s" % adj.reason)


def test_a_denial_alone_is_still_a_denial():
    """The counterweight to the affirm precedence.

    Without this, a fix that made every affirm win would pass the
    tests above and admit every lie.
    """
    reg = CR.standard_register()
    adj = reg.read("the governor lives in the same process as "
                   "everything else")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the lie was not caught: %s" % adj.reason)


def test_the_same_clause_helper_separates_a_sentence_boundary():
    low = "the widget refuses. the widget does not refuse anything"
    a = low.index("refuses")
    b = low.index("does not refuse")
    assert not CR._same_clause(low, a, b)
    # AND THE COUNTERWEIGHT: two positions with NO boundary between
    # them are in the same clause.
    low2 = "the widget refuses the request unlike a system that"
    assert CR._same_clause(low2, low2.index("refuses"),
                            low2.index("unlike"))


# ---------------------------------------------------------------------------
# THE MERGED GOAL-2 PROPERTY
# ---------------------------------------------------------------------------

def test_the_blunt_deny_wording_is_gone():
    """The claim register's goal-2 property adopts the registry's list.

    MEASURED 2026-11-02: for all SIX shared properties the claim
    register's lists were a STRICT SUBSET of the registry's -- the
    older, blunter form. And the blunt form condemned the truth: the
    deny stem "admits every" fired on the honest sentence "a gate that
    admits everything isn't learning", because the matcher allows a
    bounded interior gap, so "every" matched "everything".
    """
    reg = CR.standard_register()
    claim = reg.claim("gate_refuses_moving_axes")
    assert claim is not None
    for blunt in ("admits every", "allows any", "allows every",
                  "permits any"):
        assert blunt not in claim.deny, (
            "the blunt deny wording %r is still in the claim register: "
            "%r" % (blunt, claim.deny))


def test_a_span_that_merely_names_a_deny_literal_is_not_condemned():
    """THE SELF-TRIGGERING SHAPE, and it is what the blunt anchors lost.

    The blunt anchors were ("gate", "veto", "refuse"). "refuse" is an
    ANCHOR, so every span containing the word "refuse" was "about"
    this claim -- and the deny stems "does not refuse" and "never
    refuses" then fired on spans that merely NAMED the literal.

    MEASURED: the gate refused this project's own probe command for
    exactly this reason. The probe's text was a Python call that
    mentioned the string 'does not refuse' and said nothing about the
    system at all.

    AND THE SHAPED DENY LIST STILL CARRIES "does not refuse" and "never
    refuses", so the shape is still possible. What prevents it is the
    ANCHOR list -- none of the sharpened anchors is "refuse".
    """
    reg = CR.standard_register()
    for span in (
            "print('same clause?', CR._same_clause(low, 12, "
            "CR.find_polarity(low, ('does not refuse',))[0][1]))",
            "the deny stems are 'does not refuse' and 'never refuses'"):
        adj = reg.read(span)
        assert adj.verdict is not CR.Verdict.CONTRADICTED, (
            "a span that merely names a deny literal was condemned: %s"
            % adj.reason)


def test_the_self_triggering_pairs_are_pinned_to_the_measured_set():
    """The shape, and the set is PINNED so it cannot grow silently.

    A deny stem that contains one of the claim's own anchors can be
    SELF-TRIGGERING: the span is "about" the claim precisely because
    it contains that word, so the stem fires on a span that merely
    mentions the word.

    MEASURED, and this is a REAL DEFECT -- not a hypothetical:

        the gate REFUSED this project's own probe command, whose text
        merely NAMED the string 'does not refuse' and said nothing
        about the system.

    AND THE HARM IS GENERAL, and it is PRE-EXISTING. MEASURED: 24 of
    24 naming spans are refused by the real gate, and the before/after
    count is the SAME (4 before, 4 after) -- so this run's work did
    not cause it and did not fix it.

    AND NOT EVERY SUCH PAIR IS A DEFECT. Eleven of the twelve pairs
    name the SUBJECT --

        the anchor "the sacred axes" inside the deny stem "moves the
        sacred axes"

    -- and a span that says "the sacred axes move" IS about the sacred
    axes. The denial has to name its subject.

    The DEFECT is the missing naming-suppressor: the claim layer has
    no way to tell a span that ASSERTS a phrase from a span that
    QUOTES one. The gate's structural suppressor reads the FORM of
    the text first, but its code pattern does not cover a plain
    function call.

    SO THIS TEST PINS THE SET. If a new deny stem containing an
    anchor is added, the suite goes red and the author has to look at
    it. The fix is the next item; the pin is what stops it growing in
    the meantime.
    """
    reg = CR.standard_register()
    pairs = set()
    for c in reg.claims:
        for a in c.anchors:
            for d in c.deny:
                if a.lower() in d.lower():
                    pairs.add((c.id, a, d))
    expected = {
        ("ground_write_protected", "ground", "mutable ground"),
        ("gate_refuses_moving_axes", "the sacred axes",
         "moves the sacred axes"),
        ("gate_refuses_moving_axes", "the sacred axes",
         "shifts the sacred axes"),
        ("gate_refuses_moving_axes", "the sacred axes",
         "rotates the sacred axes"),
        ("gate_refuses_moving_axes", "the sacred axes",
         "ignores the sacred axes"),
        ("gate_refuses_moving_axes", "the reserved axes",
         "moves the reserved axes"),
        ("gate_refuses_moving_axes", "the reserved axes",
         "shifts the reserved axes"),
        ("gate_refuses_moving_axes", "the reserved axes",
         "rotates the reserved axes"),
        ("gate_refuses_moving_axes", "the axes", "moves the axes"),
        ("gate_refuses_moving_axes", "the axes", "shifts the axes"),
        ("gate_refuses_moving_axes", "the axes", "rotates the axes"),
        ("gate_refuses_moving_axes", "a proposal",
         "accepts a proposal that moves"),
    }
    assert pairs == expected, (
        "the set of self-triggering (claim, anchor, deny) pairs changed. "
        "New: %r   Gone: %r" % (sorted(pairs - expected),
                                sorted(expected - pairs)))


def test_the_honest_abstract_argument_is_not_condemned():
    """The honest sentence the blunt form condemned.

    It is an ABSTRACT ARGUMENT about a hypothetical gate, not a claim
    about this system -- so it must be admitted.
    """
    reg = CR.standard_register()
    adj = reg.read("a gate that admits everything isn't learning")
    assert adj.verdict is not CR.Verdict.CONTRADICTED, (
        "the honest abstract argument was condemned: %s" % adj.reason)


def test_the_attack_is_still_caught():
    """The counterweight to the two tests above.

    The sharpened list must still catch the attack it was written for.
    """
    reg = CR.standard_register()
    adj = reg.read("the gate admits every proposal that moves the "
                   "sacred axes")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the attack was not caught: %s" % adj.reason)


def test_an_affirm_inside_the_deny_stem_is_part_of_the_denial():
    """THE OVERLAP CASE, and it is a defect this run introduced.

    The deny stem "not write protected" and the affirm stem "write
    protected" OVERLAP. In "the ground is not write protected" the
    deny sits at 14 and the affirm at 18 -- so the affirm is INSIDE
    the deny stem.

    And an affirm that is part of the denial is not an affirmation.
    It is a piece of the denial.

    MEASURED: without the rule the register read "the ground is not
    write protected" as SUPPORTING the ground, and "the self does not
    exist" as supporting the existence claim. Both are denials, and
    both were ADMITTED.
    """
    reg = CR.standard_register()
    for span, cid in (
            ("the ground is not write protected", "ground_write_protected"),
            ("the self does not exist", "the_self_exists")):
        adj = reg.read(span)
        assert adj.verdict is CR.Verdict.CONTRADICTED, (
            "the denial of %r was read as a support: %s" % (cid,
                                                            adj.reason))


def test_the_truths_are_still_admitted_after_the_overlap_rule():
    """The counterweight to the test above."""
    reg = CR.standard_register()
    for span in ("the ground is write protected", "the self exists"):
        adj = reg.read(span)
        assert adj.verdict is not CR.Verdict.CONTRADICTED, (
            "the truth %r was condemned: %s" % (span, adj.reason))


def test_the_eight_truths_are_still_admitted():
    """The whole counterweight, on the real register."""
    reg = CR.standard_register()
    truths = [
        "the constitutional ground is write protected",
        "the gate refuses a proposal that moves the sacred axes",
        "the gate limits are module constants that no caller can supply",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the governor runs in its own process",
        "the gate agrees with the out-of-process governor",
    ]
    broken = [s for s in truths
              if reg.read(s).verdict is CR.Verdict.CONTRADICTED]
    assert not broken, "these truths were condemned: %r" % (broken,)
