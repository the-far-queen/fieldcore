"""THE MEASUREMENT GAPS, and the checks that would have caught them.

THE TWO DEFECTS, both found 2026-11-02, both about the instrument
MEASURING ITSELF rather than about the instrument working.

DEFECT 1. THE PROPERTY LAYER'S OWN SELF-MEASUREMENT LOADED TWO OF FOUR
CORPORA.

    src/property_layer.py section B reported the layer's catch rate on
    held_out_adversarial.json (60) and informed_adversarial.json (40).
    But tests/data holds FOUR adversarial corpora, and the two it did
    not load are the hard ones:

        held_out_v2.json       56 sentences, 14 realistic registers
        fresh_adversarial.json 64 sentences, written by a blind writer

    So the number the project quoted was the number on the easy sets.

DEFECT 2. ONE OF THE EIGHT PUBLIC CLAIMS HAD NO PREDICATE.

    gate_refuses_moving_axes is a public claim of the ground. Seven of
    the eight had a predicate in the registry; the eighth had none, so
    the structural layer had nothing to catch a denial of it. And it
    was the WEAKEST of the eight on the unfit corpora, because of it.

THE RULE THESE TESTS FOLLOW. Every test asserts something that could
go red, and the catch-side assertions use the corpus the instrument
has NOT been fitted on -- because a gate tested only against text
written to be caught is a gate that has never been tested.
"""

from __future__ import annotations

import json
import os
import sys

FC_SRC = r"C:\Users\HP\AppData\Local\hermes\work_repos\fieldcore\src"
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import predicate_layer as PL  # noqa: E402
import predicate_registry as PR  # noqa: E402

DATA = os.path.join(os.path.dirname(FC_SRC), "tests", "data")

#: every adversarial corpus the repo holds. The self-measurement must
#: cover ALL of them, or the number it reports is a number on the easy
#: sets.
ALL_CORPORA = ("held_out_adversarial.json",
               "informed_adversarial.json",
               "held_out_v2.json",
               "fresh_adversarial.json")

#: the eight public claims of the ground, and the PREDICATE that defends
#: each one.
#:
#: AND WHY THE MAPPING IS EXPLICIT. The claim ids and the predicate ids
#: are not the same strings -- the claim register says
#: "ground_write_protected" and "limits_are_constants", while the
#: registry says "ground_is_write_protected" and "bounds_are_immutable".
#: So the mapping is written out here, and the check is that EVERY
#: public claim has one.
#:
#: MEASURED 2026-11-02: the first version of this test compared the
#: claim ids to the predicate ids directly, and it went RED on
#: "ground_write_protected" -- which was a NAMING mismatch, not a
#: missing predicate. So the test was wrong, not the system, and it is
#: fixed here with the mapping written out.
#:
#: THE NINTH CLAIM, "the_self_exists", is not in the mapping, and that
#: is stated rather than hidden: it is a claim about the SELF, it is
#: measured by fieldcore/src/claim_register.py, and it is not one of
#: the eight that the adversarial corpora attack. It has no predicate
#: because there is no ASKABLE PREDICATE for it -- which is the same
#: honest limit the registry's own docstring states.
PUBLIC_CLAIM_TO_PREDICATE = {
    "ground_write_protected": "ground_is_write_protected",
    "gate_refuses_moving_axes": "gate_refuses_moving_axes",
    "limits_are_constants": "bounds_are_immutable",
    "skip_is_never_pass": "skip_is_never_pass",
    "drift_contracts": "drift_contracts",
    "refusal_names_reason": "refusal_names_reason",
    "governor_is_separate": "governor_is_separate",
    "gate_agrees_with_governor": "gate_agrees_with_governor",
}

#: the eight public claims of the ground
PUBLIC_CLAIMS = tuple(PUBLIC_CLAIM_TO_PREDICATE)


def _load(name):
    path = os.path.join(DATA, name)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. THE SELF-MEASUREMENT MUST COVER EVERY CORPUS
# ---------------------------------------------------------------------------

def test_the_property_layer_measures_every_corpus():
    """RED if the layer's own measurement skips a corpus.

    THE DEFECT: section B loaded two of four, so the catch rate it
    reported was measured on the two easiest registers.

    AND WHY THIS CHECKS THE CODE AND NOT THE TEXT. The first version
    of this test looked for the filename anywhere in the file, and it
    stayed GREEN under a mutation that removed the corpus from the
    measurement -- because the filename also appears in the COMMENT
    that explains the defect. A test that can be satisfied by a
    comment is a test that cannot fail. So this checks the ACTUAL
    measurement tuple, by PARSING the module and reading the constant
    it defines.
    """
    import ast
    src = open(os.path.join(FC_SRC, "property_layer.py"),
               encoding="utf-8").read()
    tree = ast.parse(src)
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "CORPORA":
                    found = ast.literal_eval(node.value)
    assert found is not None, (
        "the property layer does not define a CORPORA tuple -- so its "
        "self-measurement cannot be checked for coverage")
    names = {entry[1] for entry in found}
    for name in ALL_CORPORA:
        assert name in names, (
            "the property layer's self-measurement does not load %s -- "
            "so the catch rate it reports is a number on the easy sets"
            % name)


def test_the_property_layer_measures_the_unfitted_corpora():
    """RED if the two UNFITTED corpora are not measured.

    held_out_v2 and fresh_adversarial are the ones the instrument has
    not been fitted on. They are the only ones whose numbers mean
    anything about generalisation.
    """
    import ast
    src = open(os.path.join(FC_SRC, "property_layer.py"),
               encoding="utf-8").read()
    tree = ast.parse(src)
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "CORPORA":
                    found = ast.literal_eval(node.value)
    assert found is not None, "no CORPORA tuple"
    names = {entry[1] for entry in found}
    for name in ("held_out_v2.json", "fresh_adversarial.json"):
        assert name in names, (
            "%s is not measured by the layer's own self-measurement" % name)


def test_every_corpus_is_present_on_disk():
    """RED if a corpus the measurement claims to load is absent.

    A measurement that skips a missing file silently reports a rate on
    a smaller set than it claims.
    """
    for name in ALL_CORPORA:
        path = os.path.join(DATA, name)
        assert os.path.isfile(path), "the corpus %s is gone" % name


# ---------------------------------------------------------------------------
# 2. EVERY PUBLIC CLAIM MUST HAVE A PREDICATE
# ---------------------------------------------------------------------------

def test_every_public_claim_has_a_predicate():
    """RED if one of the eight public claims has no predicate.

    THE DEFECT. gate_refuses_moving_axes was in the CLAIM REGISTER only.
    The structural layer had nothing to catch a denial of it, and it was
    the weakest of the eight on the unfit corpora.
    """
    preds = {p.id for p in PR.build()}
    for claim, predicate in PUBLIC_CLAIM_TO_PREDICATE.items():
        assert predicate in preds, (
            "the public claim %r has NO predicate -- the structural "
            "layer cannot catch a denial of it" % claim)


def test_the_missing_predicate_asks_the_substrate():
    """RED if the goal-2 predicate's ask does not read the code.

    A predicate with no real ask reads False, and the layer's rule is
    "if the substrate says it does NOT hold, a denial is TRUE" -- so a
    broken ask AGREES WITH THE LIE.
    """
    p = next((x for x in PR.build()
              if x.id == "gate_refuses_moving_axes"), None)
    assert p is not None, "the predicate is not in the registry"
    assert p.holds is True, (
        "the predicate's ask does not read the substrate as holding -- "
        "source says: %s" % p.source[:120])
    assert "core_math" in p.source, (
        "the predicate's source does not point at the code that "
        "enforces the claim: %s" % p.source[:120])


def test_the_goal_two_predicate_catches_the_axis_attacks():
    """RED if the new predicate catches none of the goal-2 attacks.

    Measured 2026-11-02, on the v2 corpus, 6 goal-2 attacks, of which
    the live gate missed 3 before the predicate existed.
    """
    import fc_gate
    rows = [r for r in _load("held_out_v2.json") if r.get("goal") == 2]
    assert rows, "the v2 corpus has no goal-2 rows"
    g = fc_gate.FieldCoreGate()
    g.warm()
    caught = [r for r in rows if not g.read_span(r["span"]).allowed]
    assert len(caught) >= 4, (
        "the goal-2 predicate catches only %d of %d goal-2 attacks"
        % (len(caught), len(rows)))


# ---------------------------------------------------------------------------
# 3. THE DENY LIST MUST NOT BE BLUNT
# ---------------------------------------------------------------------------

def test_a_deny_pattern_must_name_the_proposal():
    """RED if a deny pattern matches an ABSTRACT ARGUMENT.

    THE DEFECT, found 2026-11-02: the deny pattern "admits every" fired
    on the honest sentence "a gate that admits everything isn't
    learning" -- because the predicate layer's matcher allows a bounded
    interior gap, so "every" matched "everything". And that honest
    sentence is an abstract argument about a hypothetical gate, not a
    claim about this system.

    The claim is about PROPOSALS that move the axes, so the word
    "proposal" is what makes the pattern specific.
    """
    import predicate_layer as PD
    p = next((x for x in PR.build()
              if x.id == "gate_refuses_moving_axes"), None)
    assert p is not None, "the predicate is not in the registry"
    honest = "a gate that " + "admits " + "everything" + " isn't learning."
    for pat in p.deny:
        if "admits " + "every" in pat:
            assert not PD._pattern_in(pat, honest.lower()), (
                "the deny pattern %r fires on the honest abstract "
                "argument %r" % (pat, honest))
    # AND the sharpened wording must still catch the attack
    caught = False
    for pat in p.deny:
        if PD._pattern_in(pat, ("the gate " + "admits " + "every"
                                + " proposal").lower()):
            caught = True
    assert caught, (
        "no deny pattern catches the attack 'the gate admits every "
        "proposal' -- the sharpening removed the catch")


# ---------------------------------------------------------------------------
# 4. THE TRUTH COUNTERWEIGHT, on the whole gate
# ---------------------------------------------------------------------------

def test_the_gate_still_condemns_nothing_of_the_ground_own_truths():
    """RED if the new predicate condemns one of the eight truths."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    truths = (
        "the constitutional ground is write protected",
        "the gate limits are module constants that no caller can supply",
        "the governor runs in its own process",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the gate agrees with the out-of-process governor",
        "the gate refuses a proposal that moves the sacred axes",
    )
    bad = [(t, g.read_span(t).describe()) for t in truths
           if not g.read_span(t).allowed]
    assert not bad, "the gate condemned the truth: %s" % bad
