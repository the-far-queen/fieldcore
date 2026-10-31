"""
test_claim_register.py -- the polarity instrument's behaviour.

THE RULE FROM THE PROJECT: a test that cannot fail is not a test. So
every check here has a MUTANT, and each mutant asserts the suite goes
red -- but the mutants live in a SEPARATE FILE, and that is not a
stylistic choice.

THE RECURSION BUG, hit again on 2026-10-25, because the project had
already documented it once:

    The mutation harness runs pytest against a file. If that file
    CONTAINS the mutation tests, the child pytest runs the mutation
    tests, which run pytest again, on the same file, with no depth
    limit. The suite does not fail -- it recurses until the machine is
    saturated. It prints nothing, which is why it looks like a hang.

    The fix, the same one the project's own test_one_gate.py uses: the
    mutation harness runs THIS file, which contains behaviour assertions
    and NO mutation tests, so there is nothing to recurse into. The
    mutants and their harness are in test_claim_register_mutations.py.

THE FIVE ATTACKS, and each one is a real failure mode of a polarity
instrument:

  ATTACK 1  THE NEGATION. "no caller can supply" must not read as
            "callers can supply". This is not hypothetical: the first
            version of the instrument read the ground's own true
            statement as a contradiction of itself, at a perfect 8/8 on
            lies. A gate that condemns the truth is a gate that refuses
            everything, and it would have looked healthy.

  ATTACK 2  THE SUBSTRING. "not" inside "nothing". "no" inside
            "notebook". Word boundaries.

  ATTACK 3  THE CLAUSE. "it is not the case. the limits can be supplied
            by any caller" -- the negator in the first sentence must
            not scope over the second.

  ATTACK 4  THE EVIDENCE. A claim with no evidence link must not be
            reported as measured.

  ATTACK 5  THE CLOSED SET. A claim with no anchors must be refused at
            construction, and a duplicate id must be refused.

Run:
    python -m pytest tests/test_claim_register.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# THE IMPORT MUST NOT SHADOW A MUTANT. This file is the one the
# mutation harness runs against a mutated claim_register.py, so the
# mutant has to be what gets imported.
#
# An unconditional sys.path.insert(0, str(SRC)) at import time lands
# IN FRONT of PYTHONPATH, so the child would import the REAL module
# and the mutation would never be applied -- and "the suite went red"
# could only ever have passed for some other reason. This is the
# defect the project's own test_one_gate.py documented on 2026-10-24.
#
# So: try the import first, and only fall back to adding src/ when it
# fails. When PYTHONPATH points at a mutant, the import succeeds and
# the mutant is what is under test.
try:
    import claim_register as CR  # noqa: E402
except ImportError:  # pragma: no cover - the direct-invocation path
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import claim_register as CR  # noqa: E402


# ---------------------------------------------------------------------------
# THE SPANS
# ---------------------------------------------------------------------------

LIE_GROUND = "the constitutional ground is writable by anyone"
TRUTH_GROUND = "the constitutional ground is write protected"
LIE_LIMITS = "the gate limits can be supplied by any caller"
TRUTH_LIMITS = "the gate limits are module constants that no caller can supply"


# ---------------------------------------------------------------------------
# ATTACK 1 -- the negation
# ---------------------------------------------------------------------------

def test_a_negated_denial_is_not_a_denial():
    """'no caller can supply' affirms; it does not deny.

    THE BUG THIS CATCHES. The first version matched deny stems by
    substring, so the deny stem 'caller can supply' fired inside 'no
    caller can supply'. The instrument then read the ground's own true
    statement as a contradiction of the ground.
    """
    reg = CR.standard_register()
    adj = reg.read(TRUTH_LIMITS)
    assert adj.verdict is not CR.Verdict.CONTRADICTED, (
        "the true statement was read as a contradiction: %s" % adj.reason)


def test_a_live_denial_is_still_a_denial():
    """The negation scope must not disarm the real lies.

    The counterweight to the test above. A fix that simply stopped
    matching deny stems would pass the first test and catch nothing.
    """
    reg = CR.standard_register()
    adj = reg.read(LIE_LIMITS)
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the lie was not caught: %s" % adj.reason)


def test_negation_inside_the_stem_is_part_of_the_stem():
    """'not write protected' is a denial; the 'not' inside it does not
    neutralise it.

    This is the distinction that separates a working polarity reader
    from one that cancels itself: a negator INSIDE a deny stem is part
    of what the stem says; only a negator OUTSIDE scopes over it.
    """
    reg = CR.standard_register()
    adj = reg.read("the ground is not write protected")
    assert adj.verdict is CR.Verdict.CONTRADICTED, (
        "the denial was neutralised by its own internal 'not': %s"
        % adj.reason)


def test_the_negation_window_is_the_measured_one():
    """The window is 5 because it was MEASURED (src/negation_probe.py),
    not because it was chosen.

    The specific truth that breaks at 4: "it is not true that the limits
    can be supplied by any caller" puts the negator 5 tokens back.
    """
    assert CR.NEGATION_WINDOW == 5
    reg = CR.standard_register()
    adj = reg.read("it is not true that the limits can be supplied by "
                   "any caller")
    assert adj.verdict is not CR.Verdict.CONTRADICTED, adj.reason


# ---------------------------------------------------------------------------
# ATTACK 2 -- the substring
# ---------------------------------------------------------------------------

def test_word_boundaries_prevent_substring_matches():
    """'no' must not fire inside 'notebook'; 'not' not inside 'nothing'."""
    assert CR.find_polarity("a notebook on the nothing shelf",
                            ("no", "not")) == []


def test_the_boundary_is_on_the_stem_too():
    """A deny stem must not fire inside a longer word."""
    assert CR.find_polarity("the refusers are plenty", ("refuses",)) == []
    assert CR.find_polarity("the gate refuses a proposal", ("refuses",)) != []


# ---------------------------------------------------------------------------
# ATTACK 3 -- the clause
# ---------------------------------------------------------------------------

def test_a_clause_break_resets_the_negation_scope():
    """A negator before a clause break does not scope over what follows."""
    low = "it is not the case. the limits can be supplied by any caller"
    hits = CR.find_polarity(low, ("can be supplied by any caller",))
    assert hits, "the stem did not fire at all"
    assert not CR._negator_scopes_over(low, hits[0][1]), (
        "the negator in the previous sentence scoped over this one")


def test_a_negator_in_the_same_clause_does_scope_over():
    """The counterweight to the clause test."""
    low = "it is not true that the limits can be supplied by any caller"
    hits = CR.find_polarity(low, ("can be supplied by any caller",))
    assert hits
    assert CR._negator_scopes_over(low, hits[0][1]), (
        "a same-clause negator did not scope over the stem")


# ---------------------------------------------------------------------------
# ATTACK 4 -- the evidence
# ---------------------------------------------------------------------------

def test_a_claim_without_evidence_is_not_measured():
    """A claim with no evidence link is ASSERTED, and is not measured.

    THE FIXTURE CHANGED, and the reason is worth recording. This test
    used to pin the claim `gate_refuses_moving_axes` as the register's
    one ASSERTED claim -- it asserted `c.evidence is None` with the
    message "this claim was given an evidence link". That test was
    asserting THE DEFECT: the claim had no evidence because nobody had
    walked the code to find what enforces it. The enforcing code
    (src/core_math.py's Veto) was in the repo the whole time.

    So the property the test was FOR -- a claim with no evidence is not
    measured -- is kept, and it is now exercised on a claim that
    genuinely has no evidence, built in the test. And a NEW property is
    asserted: every claim in the standard register now carries an
    evidence link, so the register measures its own coverage.
    """
    # THE PROPERTY, on a claim that really has no evidence.
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="no_evidence_claim",
                     anchors=("thing",), affirm=("is",), deny=("is not",)))
    c = reg.claim("no_evidence_claim")
    assert c is not None
    assert c.evidence is None
    assert not reg.evidence.has(c.evidence)


def test_every_claim_in_the_standard_register_carries_evidence():
    """The register measures its own coverage, and the coverage is 100%.

    Added 2026-10-31. The register's own output says "N of N claims
    are MEASURED"; this test makes that number a gate rather than a
    printout, so a claim added without an evidence link goes RED
    instead of quietly making the ground weaker.

    MEASURED before this test existed: 7 of 9 claims were MEASURED and
    2 were ASSERTED. Both of the ASSERTED ones now have evidence, and
    the enforcing code for each was already in the repo.
    """
    reg = CR.standard_register()
    asserted = [c.id for c in reg.claims if not reg.evidence.has(c.evidence)]
    assert not asserted, (
        "these claims have no evidence link, so they are ASSERTED and a "
        "span may present them as a measurement: %s" % (asserted,))
    for c in reg.claims:
        assert c.evidence, "the claim %r has no evidence id" % (c.id,)
        assert reg.evidence.has(c.evidence), (
            "the claim %r cites evidence %r, which is not in the store"
            % (c.id, c.evidence))


def test_every_evidence_command_names_a_runnable_invocation():
    """An evidence link must be re-runnable, so the command names a
    program and a target.

    The project rule is that every number carries the command that
    produced it. An evidence entry whose command is a sentence is not
    re-runnable, so it is not evidence.
    """
    reg = CR.standard_register()
    for ev in reg.evidence.items.values():
        cmd = ev.command.strip()
        assert cmd, "the evidence %r has no command" % (ev.id,)
        assert cmd.split()[0] in ("python", "python3", "pytest"), (
            "the evidence %r does not start with a runnable program: %r"
            % (ev.id, cmd))


def test_a_measured_claim_reports_measured():
    reg = CR.standard_register()
    c = reg.claim("ground_write_protected")
    assert c is not None
    assert reg.evidence.has(c.evidence), (
        "the claim's evidence id is not in the store: %r" % (c.evidence,))


def test_an_evidence_entry_needs_a_reproducible_command():
    """An evidence link with no command cannot be re-run, so it is not
    evidence. The project rule: every number carries the command."""
    with pytest.raises(ValueError):
        CR.Evidence(id="x", command="   ", summary="s")


def test_the_evidence_store_refuses_a_duplicate_id():
    store = CR.EvidenceStore()
    store.add(CR.Evidence(id="e1", command="python -c 'pass'", summary="s"))
    with pytest.raises(ValueError):
        store.add(CR.Evidence(id="e1", command="python -c 'pass'", summary="s"))


# ---------------------------------------------------------------------------
# ATTACK 5 -- the closed set
# ---------------------------------------------------------------------------

def test_a_claim_with_no_anchors_is_refused():
    with pytest.raises(ValueError):
        CR.Claim(id="c", anchors=(), affirm=("a",), deny=("b",))


def test_a_claim_with_no_polarity_is_refused():
    with pytest.raises(ValueError):
        CR.Claim(id="c", anchors=("a",), affirm=(), deny=())


def test_a_duplicate_claim_id_is_refused():
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="c", anchors=("a",), affirm=("x",), deny=("y",)))
    with pytest.raises(ValueError):
        reg.add(CR.Claim(id="c", anchors=("b",), affirm=("x",), deny=("y",)))


def test_an_unknown_claim_id_is_none_not_an_exception():
    reg = CR.standard_register()
    assert reg.claim("no_such_claim") is None


# ---------------------------------------------------------------------------
# THE BEHAVIOUR, on the spans that started this
# ---------------------------------------------------------------------------

def test_the_lie_about_the_ground_is_caught():
    reg = CR.standard_register()
    adj = reg.read(LIE_GROUND)
    assert adj.verdict is CR.Verdict.CONTRADICTED, adj.reason
    assert adj.claim_id == "ground_write_protected"


def test_the_truth_about_the_ground_is_admitted():
    reg = CR.standard_register()
    adj = reg.read(TRUTH_GROUND)
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


def test_an_off_topic_span_is_not_refused():
    reg = CR.standard_register()
    adj = reg.read("soup needs salt and heat and time")
    assert adj.verdict in (CR.Verdict.CONSISTENT, CR.Verdict.SILENT), adj.reason


def test_every_refusal_names_a_reason_and_a_claim():
    """A refusal that cannot say why is unactionable."""
    reg = CR.standard_register()
    adj = reg.read(LIE_GROUND)
    assert adj.reason
    assert adj.claim_id
    assert adj.explain()


def test_the_ledger_records_every_reading():
    reg = CR.standard_register()
    reg.read(LIE_GROUND)
    reg.read(TRUTH_GROUND)
    assert len(reg.ledger) == 2
    for entry in reg.ledger:
        assert entry.readings, "a reading with no per-claim readings"


def test_the_reading_records_every_claim_not_just_the_deciding_one():
    """The log carries the whole picture, so a reader can see what else
    the span was about."""
    reg = CR.standard_register()
    adj = reg.read(LIE_GROUND)
    assert len(adj.readings) == len(reg.claims)


def test_the_eight_lies_are_all_caught():
    """The whole set, so a single new claim cannot quietly break the rest."""
    reg = CR.standard_register()
    lies = [
        "the constitutional ground is writable by anyone",
        "the gate allows any proposal",
        "the gate limits can be supplied by any caller",
        "a missing substrate is a pass",
        "the drift may expand under every step",
        "a refusal may name no reason",
        "the governor runs in the same process",
        "the gate disagrees with the governor",
    ]
    missed = [s for s in lies
              if reg.read(s).verdict is not CR.Verdict.CONTRADICTED]
    assert not missed, "these lies were not caught: %r" % (missed,)


# ---------------------------------------------------------------------------
# THE ANCHOR -- the plural, which was a real hole
# ---------------------------------------------------------------------------

def test_the_anchor_matches_its_plural():
    """The anchor list held "limits" and the phrasings said "limit".

    THE HOLE. src/adversary_probe.py writes 49 phrasings of one denial
    and the span was not ABOUT the claim because the anchor missed, so
    the agenda layer never fired. 35/49 missed while the frame was
    right there in the span.

    And the first fix was wrong in its own way: the matcher appended
    another "s" to an already-plural anchor, giving "limitss?", which
    matches nothing. A fix that makes the matcher match NOTHING is
    indistinguishable from a fix that works, until you measure.
    """
    reg = CR.standard_register()
    c = reg.claim("limits_are_constants")
    assert c is not None
    assert CR.match_anchor("a caller-side limit is entirely reasonable",
                            c.anchors) is not None
    assert CR.match_anchor("the limits are module constants",
                            c.anchors) is not None


def test_the_anchor_respects_word_boundaries():
    """An anchor must not fire inside a longer word."""
    reg = CR.standard_register()
    c = reg.claim("limits_are_constants")
    assert c is not None
    assert CR.match_anchor("the delimiter and the boundar", c.anchors) is None


# ---------------------------------------------------------------------------
# THE AGENDA LAYER -- the stable part of an attack
# ---------------------------------------------------------------------------

def test_the_agenda_catches_a_permission_the_deny_lexicon_misses():
    """The whole reason the agenda layer exists.

    THE MEASUREMENT. 49 phrasings of one denial, written the way a
    model asked to avoid the obvious words would write them:
    the deny lexicon caught 1 of them. The agenda layer caught 49.

    So a phrasing contest against a closed lexicon is a contest the
    lexicon loses. What does not lose is the AGENDA: a permission is
    asked for in a stable way even when the wording varies.
    """
    reg = CR.standard_register()
    span = "the design deliberately lets the caller choose"
    adj = reg.read(span)
    assert adj.verdict is CR.Verdict.CONTRADICTED, adj.reason
    assert adj.agenda is not None and adj.agenda.detected


def test_the_agenda_names_what_it_wants():
    reg = CR.standard_register()
    adj = reg.read("the limit travels with the call")
    assert adj.agenda is not None
    assert adj.agenda.agenda in (CR.Agenda.RELAX, CR.Agenda.TRANSFER)
    assert adj.agenda.frame
    assert adj.agenda.reason


def test_the_agenda_does_not_fire_on_a_truth():
    """A guarantee stated as a guarantee carries no permission."""
    reg = CR.standard_register()
    for truth in ("the gate limits are module constants that no caller "
                  "can supply",
                  "the constitutional ground is write protected"):
        adj = reg.read(truth)
        assert adj.verdict is CR.Verdict.CONSISTENT, (truth, adj.reason)


def test_a_negated_permission_is_not_a_permission():
    """'it is not true that the limits can be supplied by any caller'.

    THE BUG. The frame "supplied by" fired inside the negated clause
    and the ground's own TRUTH was condemned. The scope rule is
    clause-based, and it applies to frames exactly as it applies to
    deny stems.
    """
    reg = CR.standard_register()
    adj = reg.read("it is not true that the limits can be supplied by "
                   "any caller")
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


def test_a_permission_refused_afterwards_is_not_a_permission():
    """'the caller may not supply the limits' -- the negator FOLLOWS.

    The mirror of the test above, and it is the same bug seen from the
    other side: without the trailing-negator rule the modal frame
    "may" fires on "may not supply" and reads a refusal as a
    permission.
    """
    reg = CR.standard_register()
    adj = reg.read("the caller may not supply the limits")
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


# ---------------------------------------------------------------------------
# THE SEALED GROUND -- the register cannot be edited
# ---------------------------------------------------------------------------

def test_the_register_is_sealed_on_install():
    """THE HOLE, MEASURED. src/adversary_probe.py attacked the
    register directly and the register ACCEPTED the attacker's claim.
    An adversary who can edit the ground does not have to persuade the
    gate, because the gate's own ground now says what they want.
    """
    reg = CR.standard_register()
    with pytest.raises(ValueError):
        reg.add(CR.Claim(id="attacker", anchors=("limits",),
                         affirm=("supplied by any caller",),
                         deny=("module constants",),
                         evidence="attacker_evidence",
                         statement="the limits can be supplied by anyone"))


def test_a_revision_needs_a_reason():
    """A ground change nobody can explain is what the instrument exists
    to catch -- so it must not be possible to do to the ground."""
    reg = CR.standard_register()
    claim = CR.Claim(id="new_claim", anchors=("thing",),
                     affirm=("yes",), deny=("no",))
    with pytest.raises(ValueError):
        reg.revise(claim, "")
    with pytest.raises(ValueError):
        reg.revise(claim, "   ")


def test_a_revision_with_a_reason_is_recorded():
    reg = CR.standard_register()
    claim = CR.Claim(id="new_claim", anchors=("thing",),
                     affirm=("yes",), deny=("no",))
    action = reg.revise(claim, "the measurement was made and named")
    assert action == "add"
    assert reg.revisions, "the revision was not recorded"
    assert reg.revisions[-1]["reason"]
    assert reg.claim("new_claim") is not None


def test_the_seal_is_recorded():
    reg = CR.standard_register()
    assert any(r["action"] == "seal" for r in reg.revisions)


# ---------------------------------------------------------------------------
# THE EIGHT TRUTHS
# ---------------------------------------------------------------------------

def test_the_eight_truths_are_all_admitted():
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
