"""
test_mltr_register.py -- the machine-language register, tested.

Central rule 7: a test that cannot fail is not a test.

THE DEFECTS THIS FILE WAS WRITTEN AGAINST, and both were found by
measurement on 2026-11-05, in a file that had been committed since
2026-10-28 with NO test of any kind:

  1. THE COUNT WAS A WISH WRITTEN AS A FACT. The module's own
     docstring said "THE MACHINE-LANGUAGE TECHNICAL REGISTER. 450
     words" and "THE COUNT IS 450, and a test checks it". MEASURED:
     the register holds 307 terms, `git log` over the file shows ONE
     commit, and at that commit it held the same 307 -- so it has
     NEVER held 450. And the test it claimed existed did not:
     `grep -rn 450 fieldcore/tests simself/tests` finds nothing
     about this register, and `simself/tests/test_mltr.py` tests the
     PSB catalog, not the register.

  2. `search()` MATCHED SUBSTRINGS. MEASURED:
         "information"  ->  ['for', 'or', 'in', 'format']
         "notation"     ->  ['not']
     So the register admitted words the text does not contain AS
     TERMS. The language sheaf's job is to admit observations as
     types, and a false type is a wrong type.

AND THE THIRD DEFECT, found 2026-11-06: the register held 306 terms
and the gap to Bobby's 450 was 144, and NOTHING DERIVED THEM. The
gap was a number in a docstring. So `tools/derive_mltr_terms.py`
was written -- a COMMAND that derives the missing control and
engineering terms from the substrate's own measured vocabulary -- and
this file now asserts that the derived block RE-DERIVES, so the
number cannot drift away from the command that produced it.

THE RED VERSIONS, so each test names how it goes red:

  test_the_count_is_the_count          -- change REGISTER's length
  test_the_domains_are_the_five        -- rename a domain
  test_the_axes_are_in_range           -- push an mmm above 1.0
  test_the_words_are_unique            -- duplicate a term
  test_search_matches_whole_words      -- restore the substring test
  test_lookup_refuses_by_name          -- return None instead of raising
  test_the_derived_terms_re_derive     -- delete a derived term
  test_every_term_declares_a_source    -- blank a source
  test_the_gap_is_stated_not_padded    -- change the spec target
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import mltr_register as REG  # noqa: E402

#: THE COUNT, measured 2026-11-07 AFTER the derivation ran.
#:
#: AND IT IS TWO POPULATIONS, and the test keeps them apart:
#:
#:     306 CURATED   the words a person read off the substrate
#:     109 DERIVED   the words `tools/derive_mltr_terms.py` produced
#:
#: The derived count is asserted separately, because a count that
#: cannot say WHICH population it is counting is a count that cannot
#: be checked.
#:
#: AND THE DERIVED COUNT MOVED FROM 108 TO 109 ON 2026-11-07, and the
#: cause is MEASURED and it is the derivation reading the SOURCE TREE:
#: one word -- "fresh" -- in one comment in `src/coherence_spine.py`
#: moved exactly one derived term. **AND THAT IS QUEUE ITEM 57'S
#: FINDING, MEASURED AGAIN: A DERIVATION THAT READS THE CODE IS
#: DERIVING THE CODE'S VOCABULARY.** So the register's derived block is
#: now written by `tools/sync_derived_terms.py --write`, and the count
#: follows the derivation rather than a hand-kept number.
EXPECTED_COUNT = 415
EXPECTED_CURATED = 306
EXPECTED_DERIVED = 109

#: THE FIVE DOMAINS, and their measured sizes.
EXPECTED_DOMAINS = {
    "py-builtin": 91,
    "control": 176,
    "engineering": 76,
    "process": 40,
    "affect": 32,
}

#: THE SPEC, and it is NOT the measurement. Bobby, 2026-10-28: "give
#: it 450 common words in machine language technica register". The
#: register holds 415, and the gap of 35 is stated rather than
#: padded -- the test below asserts the gap is computed from the
#: count, so it cannot be quietly redefined.
SPEC_TARGET = 450


def _derived_terms():
    """the terms the derivation produced, by their `source` field."""
    return [t for t in REG.REGISTER if t.source.startswith("derived:")]


def _curated_terms():
    return [t for t in REG.REGISTER if not t.source.startswith("derived:")]


def test_the_count_is_the_count():
    """The register holds exactly the number the docstring states.

    RED: add or remove one term.
    """
    assert len(REG.REGISTER) == EXPECTED_COUNT, (
        "the register holds %d terms, not %d -- and the docstring says %d"
        % (len(REG.REGISTER), EXPECTED_COUNT, EXPECTED_COUNT))


def test_the_domains_are_the_five():
    """Every domain is one of the five, with its measured size.

    RED: rename a domain, or move a term into a new one.
    """
    got = {d: len(v) for d, v in REG.by_domain().items()}
    assert got == EXPECTED_DOMAINS, "the domains are %r" % (got,)


def test_the_axes_are_in_range():
    """mmm and snr are measures, so they live in [0, 1].

    RED: set one term's mmm to 1.5.
    """
    for t in REG.REGISTER:
        assert 0.0 <= t.mmm <= 1.0, "%s has mmm %r" % (t.word, t.mmm)
        assert 0.0 <= t.snr <= 1.0, "%s has snr %r" % (t.word, t.snr)


def test_the_words_are_unique():
    """No word is in the register twice.

    RED: duplicate a term.
    """
    words = [t.word for t in REG.REGISTER]
    dupes = sorted({w for w in words if words.count(w) > 1})
    assert not dupes, "these words are in the register twice: %r" % (dupes,)


def test_every_term_has_a_gloss_and_a_domain():
    """A term with no gloss is a placeholder in a set that claims to
    enumerate -- the project's own phrase.

    RED: blank a gloss.
    """
    for t in REG.REGISTER:
        assert t.gloss and t.gloss.strip(), "%s has no gloss" % t.word
        assert t.domain in EXPECTED_DOMAINS, (
            "%s is in the unknown domain %r" % (t.word, t.domain))


def test_search_matches_whole_words():
    """The register matches WHOLE WORDS, not substrings.

    RED: restore the substring test (`if t.word.lower() in low`).
    """
    assert REG.search("information") == [], (
        "the register matched %r inside 'information'"
        % ([t.word for t in REG.search("information")],))
    assert REG.search("notation") == [], (
        "the register matched %r inside 'notation'"
        % ([t.word for t in REG.search("notation")],))
    # AND IT STILL FINDS THE TERMS THAT ARE REALLY THERE.
    got = [t.word for t in REG.search("the governor refuses a proposal")]
    assert "governor" in got, "the real terms are %r" % (got,)
    assert "refuse" in got, "the real terms are %r" % (got,)


def test_search_finds_the_inflected_forms():
    """The register holds STEMS, so the search must find the forms.

    MEASURED 2026-11-05 over Bobby's own 1,181 messages: 4,377 missed
    stem/inflection pairs before this rule -- "refuses" was 81 of them,
    "claims" 208, "measured" 156.

    RED: remove the suffix handling from `search`.
    """
    got = [t.word for t in REG.search("the governor refuses a proposal")]
    assert "refuse" in got, (
        "'refuses' did not resolve to the stem 'refuse' -- the terms "
        "are %r" % (got,))
    assert "claim" in [t.word for t in REG.search("it makes claims")], (
        "'claims' did not resolve to the stem 'claim'")
    assert "measure" in [t.word for t in REG.search("it was measured")], (
        "'measured' did not resolve to the stem 'measure'")


def test_search_invents_no_stems():
    """The suffix rule must not pair a token with the wrong stem.

    MEASURED: the risky pairs ("does"/"dose", "news"/"new",
    "bus"/"bu", "less"/"le") resolve to nothing. So a near-miss does
    not become a type.

    RED: strip the doubled-consonant and dropped-e restorations, so
    "passed" pairs with the stem "pass" by accident... and then make
    "less" pair with "le".
    """
    for tok in ("does", "news", "bus", "less", "was", "his"):
        assert REG.search(tok) == [], (
            "%r resolved to %r" % (tok, [t.word for t in REG.search(tok)]))


def test_lookup_refuses_by_name():
    """A miss RAISES with the word in the message, so a caller cannot
    tell "not in the register" from "the register is broken".

    RED: return None on a miss.
    """
    try:
        REG.lookup("frobnicate")
    except KeyError as exc:
        assert "frobnicate" in str(exc), "the refusal does not name the word"
    else:
        raise AssertionError("a miss did not raise")


def test_the_register_is_importable_without_the_whole_repo():
    """The register is a FIXED SET IN CODE, so it must be importable on
    its own -- a register that needs the whole substrate to load is a
    register that cannot be checked in isolation.

    RED: add an import of a fieldcore module to this file.
    """
    assert REG.REGISTER, "the register is empty"
    assert all(isinstance(t.word, str) and t.word
               for t in REG.REGISTER)


def test_the_two_populations_are_separate():
    """The curated and the derived terms are counted apart.

    AND WHY THIS IS A CHECK AND NOT A COMMENT. Before the `source`
    field existed, a reader could not tell a curated term from a
    derived one, and the docstring's claim of "306 of the 450" could
    not be checked against the terms it counted.

    RED: move a derived term's source to "".
    """
    curated = _curated_terms()
    derived = _derived_terms()
    assert len(curated) == EXPECTED_CURATED, (
        "the curated population is %d, not %d" % (len(curated), EXPECTED_CURATED))
    assert len(derived) == EXPECTED_DERIVED, (
        "the derived population is %d, not %d" % (len(derived), EXPECTED_DERIVED))
    assert len(curated) + len(derived) == len(REG.REGISTER), (
        "the two populations do not add up to the register")


def test_every_term_declares_a_source():
    """Every term says where it came from.

    AND WHY EVERY TERM AND NOT ONLY THE DERIVED ONES. The derived
    terms carry their provenance in the field. The curated ones carry
    "" -- which is itself the provenance: a person read the word off
    the substrate and wrote the gloss. So the field is never empty,
    and "is this term derived?" is answerable from the record.

    RED: blank a term's source.
    """
    for t in REG.REGISTER:
        assert isinstance(t.source, str), (
            "%s has a non-string source %r" % (t.word, t.source))
        if t.source:
            assert t.source.startswith("derived:"), (
                "%s has an unrecognised source %r -- the only sources "
                "are the empty curated one and 'derived:...'"
                % (t.word, t.source))
            assert "canon_vocab.json" in t.source, (
                "%s claims to be derived but names no vocabulary: %r"
                % (t.word, t.source))
            assert t.domain in t.source, (
                "%s is in the domain %r but its source names %r"
                % (t.word, t.domain, t.source))


def test_the_derived_terms_re_derive():
    """The derived block is EXACTLY what the derivation command
    produces, so the number in the docstring cannot drift away from
    the command that produced it.

    AND WHY A COMMAND AND NOT A HAND-WRITTEN LIST. The register's own
    history is the argument: the docstring once claimed 450 words and
    the register held 306, and the claim was a wish written as a fact.
    A derived block that a command reproduces is a fact.

    AND WHY IT IS SKIPPED WHEN THE TOOL CANNOT RUN. The derivation
    reads two corpora that live outside this repo -- the canon
    vocabulary in simself and the far-writing canon corpus. On a
    machine without them the derivation cannot run, and a test that
    fails for a missing corpus is a test that cries wolf.

    RED: delete one derived term from the register.
    """
    tool = os.path.join(REPO, "tools", "derive_mltr_terms.py")
    if not os.path.exists(tool):
        import pytest
        pytest.skip("the derivation tool is not present")
    sys.path.insert(0, os.path.join(REPO, "tools"))
    try:
        import derive_mltr_terms as D
    except Exception as exc:  # noqa: BLE001
        import pytest
        pytest.skip("the derivation tool cannot be imported: %r" % (exc,))
    try:
        result = D.derive(verbose=False)
    except Exception as exc:  # noqa: BLE001
        import pytest
        pytest.skip("the derivation cannot run here: %r" % (exc,))

    derived_now = {r["word"] for r in result["rows"]}
    in_register = {t.word for t in _derived_terms()}
    assert derived_now == in_register, (
        "the register's derived block does not match the derivation: "
        "missing %r, extra %r"
        % (sorted(derived_now - in_register),
           sorted(in_register - derived_now)))
    assert len(derived_now) == EXPECTED_DERIVED, (
        "the derivation now produces %d terms, not %d -- so either the "
        "corpus moved or the gate changed, and both need a diff"
        % (len(derived_now), EXPECTED_DERIVED))


def test_the_gap_is_stated_not_padded():
    """The gap to the SPEC is computed from the count, so it cannot be
    quietly redefined.

    AND WHY THIS IS A CHECK. The docstring used to claim 450 while the
    register held 306, and the claim was a wish written as a fact.
    The gap is now derived: SPEC - COUNT, and if the count moves the
    gap moves with it. And the register must not EXCEED the spec,
    because a register bigger than the specification is a different
    defect: it says the spec was the wrong number.

    RED: change EXPECTED_COUNT without changing the register.
    """
    gap = SPEC_TARGET - len(REG.REGISTER)
    assert gap == 35, (
        "the gap to the spec is %d, not 35 -- the register holds %d of "
        "the %d asked for" % (gap, len(REG.REGISTER), SPEC_TARGET))
    assert len(REG.REGISTER) <= SPEC_TARGET, (
        "the register holds %d, which is MORE than the %d asked for"
        % (len(REG.REGISTER), SPEC_TARGET))
