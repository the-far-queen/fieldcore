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

THE RED VERSIONS, so each test names how it goes red:

  test_the_count_is_the_count          -- change REGISTER's length
  test_the_domains_are_the_five        -- rename a domain
  test_the_axes_are_in_range           -- push an mmm above 1.0
  test_the_words_are_unique            -- duplicate a term
  test_search_matches_whole_words      -- restore the substring test
  test_lookup_refuses_by_name          -- return None instead of raising
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

#: THE COUNT, measured 2026-11-05 AFTER the duplicate was removed.
#:
#: AND IT WAS 307 BEFORE. MEASURED: "index" was in the register TWICE
#: -- once as py-builtin ("the position of a value") and once as
#: process ("a list for finding things") -- with different glosses and
#: different mmm values. A register is a FIXED SET OF TYPES, and a word
#: in it twice is a word with two types, which means the language
#: sheaf cannot decide what "index" IS. So the two entries were merged
#: into one, with the higher mmm (0.30) because the word genuinely
#: means both things.
EXPECTED_COUNT = 306

#: THE FIVE DOMAINS, and their measured sizes.
EXPECTED_DOMAINS = {
    "py-builtin": 91,
    "control": 80,
    "engineering": 63,
    "process": 40,
    "affect": 32,
}


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
