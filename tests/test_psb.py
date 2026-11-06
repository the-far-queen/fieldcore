"""test_psb.py -- the PSB schema's checks, and they can fail.

Bobby, 2026-11-06.

**THE SCHEMA'S SOURCE:** `vault/10-minimax/20-writing/far-writing-canon/
2026-11-06-the-psb-schema.md`.

**AND WHAT THIS FILE IS FOR.** The spec document was written on
2026-11-06 and the CODE was not -- a subagent drafted the records and
the patch did not land. So the schema existed as a PROSE SPECIFICATION
and nothing enforced it. A schema that cannot be falsified is a
description of what is already there.

So this file asserts the ELEVEN INVARIANTS, one test each, plus the
admission, revision and retirement rules -- and each test is written
so that it fails when the invariant is broken.

**AND THE TWO INVARIANTS THAT CARRY THE MOST WEIGHT, AND WHY THEY
ARE HERE AND NOT JUST IN THE DOC.**

    I1  uniqueness -- a word in the registry twice is a word with two
        types. MEASURED: the machine-language register itself held
        "index" twice -- py-builtin ("the position of a value") and
        process ("a list for finding things"), with different
        glosses and different mmm values. The same failure at the PSB
        level would be worse, because the PSB is the thing that
        decides what a word IS.

    I4  senses is non-empty -- a PSB with no senses is a token with a
        nicer name. The substrate admits it, which means the substrate
        has something to admit it AS.
"""

from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import psb as PSB  # noqa: E402
from psb import Layer, PSBRegistry, Relation, Sense, Status  # noqa: E402


def _good(**over):
    """A PSB that passes every invariant."""
    base = dict(
        id="refuse",
        word="refuse",
        inflections=("refuse", "refuses", "refused", "refusing"),
        senses=(Sense(domain="control",
                      meaning="to decline to act",
                      contexts=("the operator refuses the change",),
                      snr=0.8),),
        relations=(),
        layer=Layer.SEMANTIC,
        provenance=("vault/20-writing/04-voice.md",),
        revision=1,
        status=Status.ADMITTED,
        admitted_at="2026-11-06",
    )
    base.update(over)
    return PSB.PSB(**base)


# -- I1: the id is lowercase, kebab-case, non-empty, and unique -------

def test_i1_an_empty_id_is_refused():
    ok, bad = PSB.validate_psb(_good(id="  "))
    assert not ok
    assert any("I1" in b for b in bad)


def test_i1_an_id_that_is_not_kebab_case_is_refused():
    ok, bad = PSB.validate_psb(_good(id="Refuse_One"))
    assert not ok
    assert any("I1" in b for b in bad)


def test_i1_a_duplicate_id_is_refused():
    """A word in the registry twice is a word with two types."""
    reg = PSBRegistry()
    assert PSB.admit_psb(_good(), reg)[0]
    ok, bad = PSB.admit_psb(_good(), reg)
    assert not ok
    assert any("I1" in b for b in bad)


# -- I2 and I3: the word and its inflections -------------------------

def test_i2_a_word_that_is_not_among_the_inflections_is_refused():
    """AND THE WORD MUST BE MISSING FROM THE INFLECTIONS.

    MEASURED 2026-11-06: the first version of this test passed
    inflections=("refuse", "refuses") for the word "refuse" -- and the
    word WAS among them, so the test asserted nothing and passed for
    the wrong reason. **A TEST THAT CANNOT FAIL IS NOT A TEST.**
    """
    ok, bad = PSB.validate_psb(
        _good(word="refuse", inflections=("refuses", "refused")))
    assert not ok
    assert any("I2" in b for b in bad)


def test_i3_empty_inflections_are_refused():
    ok, bad = PSB.validate_psb(_good(inflections=()))
    assert not ok
    assert any("I3" in b for b in bad)


def test_i3_an_inflection_that_is_not_a_surface_form_is_refused():
    """AND THE SURFACE-FORM TEST IS BY STEM.

    MEASURED 2026-11-06: the first version tested the prefix and the
    suffix, and it REJECTED "refusing" for the word "refuse" -- because
    English inflects the STEM, and the stem of "refuse" is "refus". So
    the check rejected the very thing the schema is for: one meaning
    with three surfaces.
    """
    ok, bad = PSB.validate_psb(_good(inflections=("refuse", "elephant")))
    assert not ok
    assert any("I3" in b for b in bad)


def test_i3_the_regular_inflections_are_accepted():
    """AND THE COUNTER-TEST, because a check that rejects everything
    passes the negative case."""
    for form in ("refuse", "refuses", "refused", "refusing"):
        ok, bad = PSB.validate_psb(_good(inflections=("refuse", form)))
        assert ok, bad


# -- I4: the senses are non-empty ------------------------------------

def test_i4_a_psb_with_no_senses_is_refused():
    """A PSB with no senses is a token with a nicer name."""
    ok, bad = PSB.validate_psb(_good(senses=()))
    assert not ok
    assert any("I4" in b for b in bad)


# -- I5: every sense is complete -------------------------------------

@pytest.mark.parametrize("bad_sense,fragment", [
    (Sense(domain="", meaning="m", contexts=("c",), snr=0.5), "domain"),
    (Sense(domain="d", meaning="", contexts=("c",), snr=0.5), "meaning"),
    (Sense(domain="d", meaning="m", contexts=(), snr=0.5), "contexts"),
    (Sense(domain="d", meaning="m", contexts=("c",), snr=1.5), "snr"),
    (Sense(domain="d", meaning="m", contexts=("c",), snr=-0.1), "snr"),
])
def test_i5_an_incomplete_sense_is_refused(bad_sense, fragment):
    """A sense without a context is a dictionary gloss -- the one thing
    the MMM exists to replace."""
    ok, bad = PSB.validate_psb(_good(senses=(bad_sense,)))
    assert not ok
    assert any("I5" in b and fragment in b for b in bad), bad


# -- I6: the relations name real PSBs --------------------------------

def test_i6_a_relation_to_a_missing_psb_is_refused():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.validate_psb(
        _good(id="other", relations=(Relation("other", "nowhere",
                                             "uses", "e"),)), reg)
    assert not ok
    assert any("I6" in b for b in bad)


def test_i6_a_self_edge_is_refused():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.validate_psb(
        _good(relations=(Relation("refuse", "refuse", "uses", "e"),)), reg)
    assert not ok
    assert any("I6" in b for b in bad)


def test_i6_a_relation_to_a_real_psb_is_accepted():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    PSB.admit_psb(_good(id="operator", word="operator",
                        inflections=("operator", "operators"),
                        senses=(Sense(domain="control",
                                      meaning="the one who acts",
                                      contexts=("the operator runs it",),
                                      snr=0.7),)), reg)
    ok, bad = PSB.validate_psb(
        _good(relations=(Relation("refuse", "operator", "opposed-to",
                                  "the operator refuses"),)), reg)
    assert ok, bad


# -- I7: the layer is one of the six ---------------------------------

def test_i7_a_layer_outside_the_six_is_refused():
    """AND THE LAYER MUST BE A LAYER THAT DOES NOT EXIST.

    MEASURED 2026-11-06: the first version of this test passed
    layer="semantic" -- and `Layer` is a `str` Enum, so "semantic" IS
    `Layer.SEMANTIC` and the test asserted nothing and passed for the
    wrong reason. The real failure case is a layer that is not one of
    the six -- and the best example is "integration", which the
    schema's own §5 says is the ACT that binds the six and is NOT one
    of them.
    """
    ok, bad = PSB.validate_psb(_good(layer="integration"))
    assert not ok
    assert any("I7" in b for b in bad)


def test_i7_there_are_exactly_six_layers():
    assert len(PSB.LAYERS) == 6


def test_i7_the_plain_string_form_of_a_layer_is_accepted():
    """AND THE COUNTER-TEST, because `Layer` is a `str` Enum and the
    schema says a layer is one of the six BY VALUE."""
    ok, bad = PSB.validate_psb(_good(layer="semantic"))
    assert ok, bad


# -- I8: an admitted PSB has provenance and an admitted_at -----------

def test_i8_an_admitted_psb_with_no_provenance_is_refused():
    """A field cannot be asserted into existence; it has to be filled."""
    ok, bad = PSB.validate_psb(_good(provenance=()))
    assert not ok
    assert any("I8" in b for b in bad)


def test_i8_an_admitted_psb_with_no_admitted_at_is_refused():
    ok, bad = PSB.validate_psb(_good(admitted_at=""))
    assert not ok
    assert any("I8" in b for b in bad)


# -- I9: the revision starts at 1 ------------------------------------

def test_i9_a_revision_below_one_is_refused():
    ok, bad = PSB.validate_psb(_good(revision=0))
    assert not ok
    assert any("I9" in b for b in bad)


# -- I10: a retired PSB says why -------------------------------------

def test_i10_a_retired_psb_with_no_reason_is_refused():
    """A retirement must be distinguishable from a deletion."""
    ok, bad = PSB.validate_psb(_good(status=Status.RETIRED, provenance=()))
    assert not ok
    assert any("I10" in b for b in bad)


# -- I11: the senses of one PSB have distinct domains ----------------

def test_i11_two_senses_in_one_domain_are_refused():
    ok, bad = PSB.validate_psb(_good(senses=(
        Sense(domain="control", meaning="m", contexts=("c",), snr=0.5),
        Sense(domain="control", meaning="n", contexts=("c",), snr=0.5),
    )))
    assert not ok
    assert any("I11" in b for b in bad)


def test_i11_six_senses_in_six_domains_are_accepted():
    """AND THE COUNTER-TEST, because the schema's worked example is
    "actor" with six domain senses."""
    senses = tuple(
        Sense(domain=d, meaning="m in %s" % d, contexts=("c",), snr=0.5)
        for d in ("theatrical", "agency", "social", "intelligence",
                  "technical", "legal"))
    ok, bad = PSB.validate_psb(_good(senses=senses))
    assert ok, bad


# -- admission, revision, retirement ---------------------------------

def test_a_valid_psb_is_admitted():
    reg = PSBRegistry()
    ok, bad = PSB.admit_psb(_good(), reg)
    assert ok, bad
    assert len(reg) == 1


def test_an_invalid_psb_is_not_admitted():
    """AND IT IS NOT IN THE REGISTRY, because a name in the admitted
    list is a PROMISE that the thing is going somewhere."""
    reg = PSBRegistry()
    ok, _ = PSB.admit_psb(_good(senses=()), reg)
    assert not ok
    assert len(reg) == 0


def test_a_revision_with_a_reason_lands_and_moves_the_number():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.revise_psb("refuse", {}, reg, reason="a new context")
    assert ok, bad
    assert reg.get("refuse").revision == 2
    assert any("revision:" in p for p in reg.get("refuse").provenance)


def test_a_revision_with_no_reason_is_refused():
    """A revision with no reason is a replacement, not a revision."""
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.revise_psb("refuse", {}, reg, reason="")
    assert not ok
    assert reg.get("refuse").revision == 1


def test_a_retirement_keeps_the_psb_readable():
    """A retirement is NOT a deletion."""
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.retire_psb("refuse", "the word was not the word", reg)
    assert ok, bad
    assert reg.get("refuse") is not None
    assert reg.get("refuse").status is Status.RETIRED
    assert any("retired:" in p for p in reg.get("refuse").provenance)


def test_a_retirement_with_no_reason_is_refused():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    ok, bad = PSB.retire_psb("refuse", "", reg)
    assert not ok
    assert reg.get("refuse").status is Status.ADMITTED


def test_the_history_keeps_the_superseded_versions():
    reg = PSBRegistry()
    PSB.admit_psb(_good(), reg)
    PSB.revise_psb("refuse", {}, reg, reason="a new context")
    hist = reg.history()
    assert len(hist) == 1
    assert hist[0].revision == 1


# -- and the derivation from the substrate's own register -------------

def test_the_derivation_names_the_fields_it_cannot_fill():
    """AND THE DERIVATION IS HONEST ABOUT WHAT IT DOES.

    A term in the MLTR register has a word, a domain and a gloss --
    so it is a CANDIDATE PSB. It does NOT have its inflections, its
    contexts, its snr or its relations, and I5 requires the contexts.
    So the derived PSBs are NOT admissible as they stand, and the
    check says so rather than pretending.
    """
    derived = PSB.derive_from_register()
    assert derived, "the register derived nothing -- the derivation is broken"
    for psb in derived[:20]:
        ok, bad = PSB.validate_psb(psb)
        assert not ok
        assert any("I3" in b or "I5" in b for b in bad)


def test_the_derivation_covers_the_whole_register():
    import mltr_register as MLTR
    derived = PSB.derive_from_register()
    assert len(derived) == len(MLTR.REGISTER)


def test_the_language_sheaf_reaches_the_psb_schema():
    """AND THE SCHEMA IS REACHED, not an orphan.

    MEASURED 2026-11-06: `tools/wiring_census.py` reports ORPHAN 0
    over 435 modules, and this import is what keeps it there.
    """
    from sheaves import Sheaves
    out = Sheaves().language_types()
    assert out.get("psb_n_layers") == 6, out.get("psb_error")
    assert out.get("psb_registry_ok") is True, out.get("psb_broken")
    assert out.get("psb_candidates", 0) > 0
