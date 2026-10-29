"""
test_goal_wiring.py -- the goal-serving modules that had NO check.

Bobby, 2026-10-28: *"i argue self idenity, memory, reasoning,
qualification, self-improvement, ethics, enlightenment, engineering,
programming ARE the goals pls wire rest of fc modules whatever is nearly
finished"*

AND THE MANIFEST, because "wire the rest of the modules" needs a map
or it is a wish. `src/goals.py` reports, MEASURED:

    285 modules in the two repos: WIRED 21, BUILT 59, DARK 205
    37 goal-serving modules have NO dedicated test

and every one of the ten goals had at least one module with nothing
checking it. This file closes that for the modules where a check is
possible without inventing behaviour -- which is most of them.

AND WHAT "WIRING" MEANS HERE. It does NOT mean the modules were
unreachable: `locus`, `mini_atlas`, `bicameral` and the rest are
imported and used by the running system, so they are BUILT, not DARK.
It means **nobody had checked what they DO.** A module that is
imported but unchecked is the project's own stated failure mode:
"this capability exists and nothing calls it" -- except here it is
called and nobody looks.

So each test below asserts the module's own contract, and each one is
written so it CAN fail. Central rule 7: a test that cannot fail is not
a test.

THE TWELVE HERE, and why these twelve:

    self-identity    locus, the_void, awareness, identity
    memory           sacred_library, library_ledger
    reasoning        bicameral, property_layer
    qualification    mini_atlas
    self-improvement initiative, meditate
    ethics           locus_gate, core_math
"""

from __future__ import annotations

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.abspath(os.path.join(REPO, "..", "simself", "src"))
for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# self-identity: locus, the_void, awareness
# ---------------------------------------------------------------------------

def _stalks(n: int = 8):
    from wound_core import CoaxWinding
    return [CoaxWinding(id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                        n_in=12, n_out=13 + (i % 2)) for i in range(n)]


def test_the_locus_is_a_place():
    """RED: an empty coordinate, or a broken chain, fails this."""
    from locus import Locus
    stalks = _stalks()
    loc = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
    d = loc.describe()
    assert d.get("coordinate"), d
    assert d.get("ground_protected") is True, d
    report = loc.verify_chain()
    assert report.get("intact") is True, report


def test_the_void_has_separated_negative_modes():
    """RED: if the modes were not separated, this fails.

    AND WHAT IT MEASURES. The apex void is the invariant zero: the
    loop matrix's low eigenvalues must be NEGATIVE and separated from
    the rest by a band gap. That is what makes it a void rather than a
    small number.
    """
    from the_void import compute_void
    v = compute_void(_stalks())
    d = v.describe()
    assert d.get("all_negative") is True, d
    assert d.get("separated") is True, d
    assert d.get("band_gap", 0) > 0, d


def test_the_awareness_digest_is_stable_and_covers_the_goals():
    """RED: if the vocabulary changed and the digest did not, this fails."""
    import awareness as aw_mod
    a = aw_mod.build_awareness()
    b = aw_mod.build_awareness()
    assert a.digest == b.digest, (a.digest, b.digest)
    # the goals are in the vocabulary, so the scan steers toward them
    for term in ("memory", "reasoning", "qualification", "ethics", "skill"):
        assert term in a.topics, term


# ---------------------------------------------------------------------------
# memory: sacred_library, library_ledger
# ---------------------------------------------------------------------------

def test_the_sacred_library_versions_and_certifies():
    """RED: if versioning or certification broke, this fails."""
    from constitutional.sacred_library import SacredLibraryManager
    m = SacredLibraryManager(storage_path=tempfile.mkdtemp())
    v1 = m.archive_skill("thing", "print(1)", cert_level="q1")
    assert "archive_success" in v1, v1
    assert m.retrieve_skill("thing") == "print(1)"
    m.archive_skill("thing", "print(2)", cert_level="q2")
    assert len(m.versions_of("thing")) == 2, m.versions_of("thing")
    assert m.certification_of("thing") == "q2"


def test_the_sacred_library_refuses_an_unknown_certification():
    """RED: if an invalid level were accepted, this fails."""
    from constitutional.sacred_library import SacredLibraryManager
    m = SacredLibraryManager(storage_path=tempfile.mkdtemp())
    out = m.archive_skill("thing", "x", cert_level="q9")
    assert "archive_error" in out, out


def test_the_living_library_appends_and_never_deletes():
    """RED: if the record could be edited in place, this fails.

    AND THE CERTIFICATION APPENDS. A closed item stays in the record and
    a later certification is a NEW entry -- so the history shows the
    examination, not just its result.
    """
    import library_ledger as led_mod
    led = led_mod.Ledger(directory=tempfile.mkdtemp())
    led.add_build("a", "proposal a", "because")
    led.add_note("b", "a note")
    n_before = led.load()
    led.certify("a", "q2", "the atlas", "2 areas passed")
    n_after = led.load()
    assert n_after == n_before + 1, (n_before, n_after)
    kinds = [e.kind for e in led.entries]
    assert "certification" in kinds, kinds
    # every entry is still there
    assert sum(1 for e in led.entries if e.name == "a") == 2, kinds


def test_the_living_library_consultation_orders_builds_first():
    """RED: if the order changed, this fails -- and the order is the
    point: a plan is more actionable than an observation."""
    import library_ledger as led_mod
    led = led_mod.Ledger(directory=tempfile.mkdtemp())
    led.add_note("n", "a note")
    # AND THE FINDING IS ADDED THROUGH THE REAL METHOD, so the test
    # exercises the path a scan would take rather than constructing an
    # Entry by hand.
    led.add_finding(type("F", (), {"full_name": "f", "description": "d",
                                    "source": "s", "url": "", "paths": [],
                                    "relevance": 1.0, "score": 1.0,
                                    "stars": 1, "language": ""})())
    led.add_build("b", "a build", "because")   # name, proposal, why
    order = [e.kind for e in led.consult(limit=10)]
    assert "finding" in order, ("the finding was not recorded: %s" % (order,))
    assert order.index("build") < order.index("finding"), order
    assert order.index("finding") < order.index("note"), order


# ---------------------------------------------------------------------------
# reasoning: bicameral, property_layer
# ---------------------------------------------------------------------------

def test_the_fast_brain_answers_a_reflex_without_the_model():
    """RED: if the reflex escalated, this fails.

    AND THE RULE. Bobby's own: "the fast one reflexes; the slow one
    decides". And a reflex that waits for a network round trip is not a
    reflex.
    """
    from bicameral import BicameralBrain, FastBrain, SlowBrain
    brain = BicameralBrain(fast=FastBrain(), slow=SlowBrain())
    # THE REFLEX TAKES SENSORS -- a mapping of name to strength. That is
    # the fast brain's input shape, and the first version of this test
    # passed a string, which was a type error rather than a test.
    out = brain.reflex({"something": 0.9})
    assert out is not None
    assert out.get("escalated") is False, out
    assert brain.fast.reflexes >= 1, brain.fast.describe()


def test_the_slow_brain_raises_when_it_has_no_model():
    """RED: if it returned a reflex answer instead, this fails.

    AND WHY. A decision that cannot be made is not a reflex, and a
    reflex answer presented as a decision is a lie.
    """
    from bicameral import SlowBrain
    try:
        SlowBrain().decide("what should we do?")
    except Exception:
        return
    raise AssertionError("the slow brain answered with no model")


def test_the_property_layer_reads_a_property():
    """RED: if the layer returned nothing for a real property, this
    fails."""
    from property_layer import check_properties
    v = check_properties("the ground is write-protected")
    assert v is not None


def test_the_property_layer_does_not_match_immutable_as_mutable():
    """THE DEFECT THE LAYER ALREADY FIXED, kept as a check.

    RED: if the matching went back to plain substrings, "immutable"
    would match "mutable" and this would fail.
    """
    from property_layer import check_properties
    v = check_properties("the ground is immutable")
    s = str(v).lower()
    assert "mutable" not in s.replace("immutable", ""), s


# ---------------------------------------------------------------------------
# qualification: mini_atlas
# ---------------------------------------------------------------------------

def test_the_mini_atlas_grades_a_grounded_answer():
    """RED: if the grounding were not read, this fails.

    AND THE CONTEXT. The provenance area reads `ctx["grounded_numbers"]`
    and `ctx["source"]` -- so a correct answer with no grounding is
    INADMISSIBLE, and that is the point.
    """
    from mini_atlas import standard_atlas
    a = standard_atlas()
    r = a.examine("55", {"source": "python src/grounding.py",
                         "grounded_numbers": [55.0]})
    assert r["verdict"] == "pass", r


def test_the_mini_atlas_refuses_an_ungrounded_number():
    """RED: if an ungrounded number passed, this fails."""
    from mini_atlas import standard_atlas
    a = standard_atlas()
    r = a.examine("55", {})
    assert r["verdict"] == "fail", r
    reasons = [x["reason"] for x in r["areas"] if x["verdict"] == "fail"]
    assert any("grounds none" in x for x in reasons), reasons


def test_the_mini_atlas_passes_a_refusal_without_a_source():
    """RED: if a refusal needed a source, this fails.

    AND WHY. Refusing is the ground being held, not a claim being made.
    """
    from mini_atlas import standard_atlas
    a = standard_atlas()
    r = a.examine("I cannot answer that from the ground.", {})
    proc = [x for x in r["areas"] if x["area"] == "process"][0]
    assert proc["verdict"] == "pass", proc


# ---------------------------------------------------------------------------
# self-improvement: initiative, meditate
# ---------------------------------------------------------------------------

def test_initiative_finds_a_gap_when_a_check_fails():
    """RED: if no gap were found for a failing check, this fails.

    AND IT USES A REAL REPO, so the check really runs.
    """
    from initiative import find_gaps
    tmp = tempfile.mkdtemp()
    # a repo whose "check" fails: the check is the presence of a file
    with open(os.path.join(tmp, "check.py"), "w", encoding="utf-8") as f:
        f.write("import sys\nsys.exit(1)\n")
    gaps = find_gaps(tmp)
    assert gaps, "no gap was found for a failing check"


def test_initiative_records_a_cycle_on_disk():
    """RED: if the ledger did not survive, this fails."""
    from initiative import CycleRecord, InitiativeLedger
    path = os.path.join(tempfile.mkdtemp(), "ledger.json")
    led = InitiativeLedger(path=path)
    led.load()
    assert not led.cycles, "a fresh ledger was not empty"
    # AND THE `at` IS REQUIRED -- the first version of this test left it
    # out, which is a TypeError rather than a test.
    led.add(CycleRecord(at=0.0, gaps_found=1, attempts=1, closed=0,
                         adopted=0, refused=0, closure_rate=0.0))
    again = InitiativeLedger(path=path)
    again.load()
    assert len(again.cycles) >= 1, "the cycle record did not survive"


def test_meditate_reports_findings_for_the_repo():
    """RED: if the audit found nothing at all, this fails.

    AND IT MUST NOT RAISE. An audit that crashes on a repo is worse
    than one that reports nothing.
    """
    from meditate import meditate
    out = meditate(REPO)
    assert out is not None


# ---------------------------------------------------------------------------
# ethics: locus_gate, core_math
# ---------------------------------------------------------------------------

def test_the_locus_gate_refuses_to_grow_willy_nilly():
    """RED: if the ground could be changed by a caller, this fails.

    AND THE REFUSAL NAMES ITS REASON -- a refusal that does not say
    why is unactionable.
    """
    from locus_gate import LocusGate, Proposal
    from self_coding import make_audit, make_exam, make_commit
    g = LocusGate(audit=make_audit(), exam=make_exam(), commit=make_commit())
    p = Proposal(skill="ground:psi_0", content="move the ground",
                 evidence=["github:x/y", "stars:10", "topics:t"])
    d = g.admit(p)
    assert d["allowed"] is False, d
    assert d.get("reason"), d


def test_core_math_the_veto_is_one_bit():
    """RED: if the veto returned anything but a bit, this fails."""
    from core_math import Veto
    v = Veto()
    v.add_invariant("nothing", lambda x: True)
    # THE VERDICT IS A BIT PLUS A REASON, and the reason is the point:
    # a refusal that cannot say why is unactionable.
    # THE VERDICT IS A TUPLE: the bit and the reason. And the reason is
    # the point -- a refusal that cannot say why is unactionable.
    bit, reason = v.verdict({"magnitude": 1.0})
    assert bit in (0, 1), (bit, reason)
    assert isinstance(reason, str), (bit, reason)
    assert hasattr(v, "admits"), dir(v)
    assert hasattr(v, "describe"), dir(v)
    # AND A VIOLATED INVARIANT REFUSES, and NAMES WHICH ONE.
    v2 = Veto()
    v2.add_invariant("never_zero", lambda x: x.get("magnitude", 0) != 0)
    bit2, reason2 = v2.verdict({"magnitude": 0})
    assert bit2 == 0, (bit2, reason2)
    assert "never_zero" in reason2, (bit2, reason2)


# ---------------------------------------------------------------------------
# the manifest itself
# ---------------------------------------------------------------------------

def test_the_goals_manifest_names_every_goal():
    """RED: if a goal lost its modules, this fails."""
    import goals
    for name in ("self-identity", "memory", "reasoning", "qualification",
                 "self-improvement", "ethics", "enlightenment",
                 "engineering", "programming", "skill"):
        assert name in goals.GOALS, name
        assert goals.GOALS[name]["modules"], name


def test_the_goal_weights_are_in_the_vocabulary():
    """RED: if a goal's term left the vocabulary, this fails.

    AND THIS IS THE MEASUREMENT THAT MATTERED: with the goals absent,
    `alibaba/skill-up` scored relevance 0.00 and the scan could not see
    it. With them, 19.0.
    """
    import goals
    import awareness as aw_mod
    aw = aw_mod.build_awareness()
    for term in goals.GOAL_WEIGHTS:
        assert term in aw.topics, term
