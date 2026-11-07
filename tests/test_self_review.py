"""
test_self_review.py -- the self-improvement instrument's own checks.

Bobby, 2026-11-06: *"code best of hermes own self-improvement
techniques right into fieldcore"*.

**AND THESE CHECKS CAN FAIL.** That is the requirement, and it is
stated in the substrate's own vocabulary: a check that cannot go red
is a check that cannot catch anything.

**AND WHAT IS BEING PROVEN, and each one is a rule and not a shape:**

    1  THE REVIEWER PROPOSES; THE REGISTER ADMITS. Two steps, because
       the runtime's fork proposes and the store's gate decides.
    2  A LESSON WITH NO GROUNDING IS REFUSED, because a lesson nobody
       can point at is a story.
    3  A FACT GOES TO ONE STORE AND NEVER BOTH, because the runtime's
       own routing block says writing it to both bloats both.
    4  THE SAME LESSON IS NOT APPENDED TWICE, because the store is
       append-only and a second copy is permanent.
    5  THE CHAIN KNOWS WHAT IT IS APPENDING TO, and the digests are
       re-derived rather than checked against themselves.
    6  THE REVIEWER READS ARTIFACTS, NOT SOURCE -- and it reads EVERY
       refusal line, not the first.
    7  THE ROUTING IS DETERMINISTIC, so the same refusal always lands
       in the same store.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")

# AND THE SOURCE UNDER TEST IS THE ONE THE RUNNER NAMES, and not
# whatever is importable.
#
# MEASURED 2026-11-06: the mutation check ran the tests with
# PYTHONPATH pointing at the mutated copy -- and every one of the six
# mutations stayed GREEN. The cause: this file put `src` at the FRONT
# of sys.path, so the tests imported the REAL instrument and the
# mutated copy was never loaded. **A MUTATION THAT IS NOT LOADED IS
# NOT A MUTATION**, and it looks exactly like a working instrument.
#
# SO THE PATH IS HONOURED WHEN IT IS SET -- the runner's choice comes
# FIRST -- and the default is only used when nothing is named.
_MUTATED = os.environ.get("FC_SELFTEST_SRC")
if _MUTATED:
    SRC = os.path.abspath(_MUTATED)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import self_review as SR  # noqa: E402


def _grounding(path: str = "src/gate.py", line: int = 12,
               excerpt: str = "the ground does not move") -> SR.Grounding:
    return SR.Grounding(path, line, excerpt)


def _lesson(key: str = "k1", rule: str = "the rule",
            mechanism: str = "because the substrate is written this way",
            kind: SR.LessonKind = SR.LessonKind.REFUSAL_WORK,
            store: SR.Store = SR.Store.LESSON) -> SR.Lesson:
    return SR.Lesson(key=key, rule=rule, mechanism=mechanism, kind=kind,
                     grounding=_grounding(), store=store)


# ---------------------------------------------------------------------------
# 1. the reviewer proposes; the register admits
# ---------------------------------------------------------------------------

def test_the_review_proposes_and_the_register_admits(tmp_path):
    art = tmp_path / "out.txt"
    art.write_text("FAILED tests/test_x.py::test_y\n", encoding="utf-8")
    stores = SR.open_stores(str(tmp_path))
    res = SR.review([str(art)], stores)
    assert res.proposed, "the reviewer found nothing in a refusal"
    assert res.admitted, "the register admitted nothing"
    assert not res.refused, res.refused


def test_the_proposal_is_not_the_admission(tmp_path):
    """**THE TWO ARE SEPARATE STEPS.** A refused proposal is still a
    proposal, and the refusal must be visible.

    AND THE SAME REFUSAL TWICE IS PROPOSED TWICE AND ADMITTED ONCE --
    because the store is APPEND-ONLY and a second copy of a lesson is
    permanent. So the count of proposals is 2 and the count of
    admissions is 1.
    """
    art = tmp_path / "out.txt"
    art.write_text("FAILED tests/test_x.py::test_y\n"
                   "FAILED tests/test_x.py::test_y\n", encoding="utf-8")
    stores = SR.open_stores(str(tmp_path))
    res = SR.review([str(art)], stores)
    assert len(res.proposed) == 2, res.proposed
    assert len(res.admitted) == 1, res.admitted
    assert res.refused, "the second refusal was not visible"


def test_two_DIFFERENT_refusals_are_both_admitted(tmp_path):
    """**AND TWO DIFFERENT REFUSALS ARE TWO LESSONS.** A store that
    refuses everything after the first is a store that learns one
    thing."""
    art = tmp_path / "out.txt"
    art.write_text("FAILED tests/test_x.py::test_y\n"
                   "FAILED tests/test_z.py::test_w\n", encoding="utf-8")
    stores = SR.open_stores(str(tmp_path))
    res = SR.review([str(art)], stores)
    assert len(res.proposed) == 2
    assert len(res.admitted) == 2, res.admitted


# ---------------------------------------------------------------------------
# 2. a lesson with no grounding is refused
# ---------------------------------------------------------------------------

def test_a_lesson_with_no_grounding_is_refused():
    """**A LESSON NOBODY CAN POINT AT IS A STORY**, and the refusal
    happens where the grounding is BUILT -- so an ungrounded lesson
    cannot be constructed at all.

    AND THAT IS STRONGER THAN REFUSING IT AT ADMISSION. A refusal at
    admission means the object existed and was turned away; a refusal
    at construction means the object never existed.
    """
    with pytest.raises(ValueError):
        SR.Grounding("", 1, "x")
    with pytest.raises(ValueError):
        SR.Grounding("a.py", 1, "")
    with pytest.raises(ValueError):
        SR.Grounding("a.py", -1, "x")


def test_a_lesson_with_no_rule_is_refused(tmp_path):
    reg = SR.LessonRegister(str(tmp_path / "l.jsonl"))
    ok, why = reg.admit(_lesson(rule=""))
    assert not ok
    assert "rule" in why


def test_a_lesson_with_no_mechanism_is_refused(tmp_path):
    reg = SR.LessonRegister(str(tmp_path / "l.jsonl"))
    ok, why = reg.admit(_lesson(mechanism=""))
    assert not ok
    assert "mechanism" in why


def test_a_lesson_nobody_saw_is_refused(tmp_path):
    """**A LESSON NOBODY SAW HAPPEN IS A GUESS.**"""
    reg = SR.LessonRegister(str(tmp_path / "l.jsonl"))
    lesson = _lesson()
    lesson.occurrences = 0
    ok, why = reg.admit(lesson)
    assert not ok
    assert "occurrences" in why


# ---------------------------------------------------------------------------
# 3. a fact goes to ONE store
# ---------------------------------------------------------------------------

def test_a_refusal_about_the_substrate_routes_to_the_field_store():
    store, kind = SR.route_reason("the substrate does not have this shape")
    assert store is SR.Store.FIELD
    assert kind is SR.LessonKind.REFUSAL_SHAPE


def test_a_refusal_about_the_work_routes_to_the_lesson_store():
    store, kind = SR.route_reason("the command must be run before the count")
    assert store is SR.Store.LESSON
    assert kind is SR.LessonKind.REFUSAL_WORK


def test_the_two_stores_are_separate_files(tmp_path):
    stores = SR.open_stores(str(tmp_path))
    assert stores[SR.Store.FIELD].path != stores[SR.Store.LESSON].path


def test_a_refusal_routes_to_exactly_one_store(tmp_path):
    """**A FACT GOES TO ONE STORE AND NEVER BOTH.**"""
    art = tmp_path / "out.txt"
    art.write_text("the substrate does not have this shape\n"
                   "the probe must be able to fail\n",
                   encoding="utf-8")
    stores = SR.open_stores(str(tmp_path))
    res = SR.review([str(art)], stores)
    field = len(stores[SR.Store.FIELD].events)
    lesson = len(stores[SR.Store.LESSON].events)
    assert field + lesson == len(res.admitted)
    assert field >= 1 and lesson >= 1, (field, lesson)


def test_a_refusal_naming_the_source_routes_to_the_field_store():
    """**AND THE ROUTING IS BY THE WORDS THE REFUSAL USES**, so a
    refusal that names the substrate's SOURCE is a field fact."""
    store, _ = SR.route_reason("the module is not wired into the source")
    assert store is SR.Store.FIELD
    store, _ = SR.route_reason("the probe must be able to fail")
    assert store is SR.Store.LESSON


# ---------------------------------------------------------------------------
# 4. the same lesson is not appended twice
# ---------------------------------------------------------------------------

def test_the_same_lesson_is_refused_the_second_time(tmp_path):
    reg = SR.LessonRegister(str(tmp_path / "l.jsonl"))
    ok, _ = reg.admit(_lesson(key="k1"))
    assert ok
    ok2, why = reg.admit(_lesson(key="k2"))   # a DIFFERENT key, the SAME rule
    assert not ok2
    assert "already held" in why
    assert len(reg.events) == 1


# ---------------------------------------------------------------------------
# 5. the chain knows what it is appending to
# ---------------------------------------------------------------------------

def test_the_chain_verifies_clean(tmp_path):
    reg = SR.LessonRegister(str(tmp_path / "l.jsonl"))
    reg.admit(_lesson(key="k1"))
    reg.admit(_lesson(key="k2", rule="another rule"))
    assert reg.verify() == []


def test_the_chain_continues_across_a_reload(tmp_path):
    path = str(tmp_path / "l.jsonl")
    reg = SR.LessonRegister(path)
    reg.admit(_lesson(key="k1"))
    reloaded = SR.LessonRegister(path)
    assert reloaded.head() == reg.head()
    assert reloaded.verify() == []


def test_a_broken_link_is_caught(tmp_path):
    """**THE LINK IS CHECKED, AND THE LINK IS NOT THE DIGEST.**

    MEASURED 2026-11-06: the mutation that removed the link check
    stayed GREEN -- because the only test that caught a tampered chain
    caught it by the DIGEST. So a chain whose links were severed but
    whose digests still matched would have verified clean.

    **AND THE TWO CHECKS ARE NOT THE SAME CHECK.** The digest says
    "this event was not changed"; the link says "this event points at
    the one before it". A chain can have a correct digest and a broken
    link -- when an event is REMOVED from the middle.
    """
    path = tmp_path / "l.jsonl"
    reg = SR.LessonRegister(str(path))
    reg.admit(_lesson(key="k1"))
    reg.admit(_lesson(key="k2", rule="another rule"))
    reg.admit(_lesson(key="k3", rule="a third rule"))
    lines = path.read_text(encoding="utf-8").splitlines()
    # AND ONLY THE LINK IS BROKEN: the second event's `prev` is
    # rewritten to point at GENESIS, and its seq is RENUMBERED so the
    # seq check does not fire either.
    #
    # **AND THAT IS THE CASE THE SEQ CHECK CANNOT CATCH**, and it is
    # the case that matters: a chain whose links were rewritten to
    # point somewhere else -- which is what a REORDERED chain looks
    # like, and a reordered chain is a chain that no longer says what
    # it said.
    import json as _json
    ev = _json.loads(lines[1])
    ev["prev"] = SR.LessonRegister.GENESIS
    ev["seq"] = 0
    lines[1] = _json.dumps(ev, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    problems = SR.LessonRegister(str(path)).verify()
    assert any("link break" in x for x in problems), problems


def test_a_rewritten_event_is_caught(tmp_path):
    """**THE DIGESTS ARE RE-DERIVED, because a chain checked only
    against itself proves nothing.**"""
    path = tmp_path / "l.jsonl"
    reg = SR.LessonRegister(str(path))
    reg.admit(_lesson(key="k1"))
    lines = path.read_text(encoding="utf-8").splitlines()
    ev = json.loads(lines[0])
    ev["lesson"]["rule"] = "something else entirely"
    path.write_text(json.dumps(ev) + "\n", encoding="utf-8")
    problems = SR.LessonRegister(str(path)).verify()
    assert problems, "a rewritten event was not caught"


# ---------------------------------------------------------------------------
# 6. the reviewer reads artifacts, not source
# ---------------------------------------------------------------------------

def test_the_reviewer_reads_every_refusal_line(tmp_path):
    art = tmp_path / "out.txt"
    art.write_text("FAILED tests/test_a.py::test_b\n"
                   "the substrate does not have this shape\n"
                   "MISSING something_expected\n",
                   encoding="utf-8")
    readings = SR.read_artifacts([str(art)])
    assert len(readings) == 3, readings


def test_a_bare_refusal_sentence_is_read(tmp_path):
    """**A REVIEWER THAT ONLY READS MARKED LINES READS THE
    SUBSTRATE'S FORMATTING AND NOT ITS REFUSALS.**"""
    art = tmp_path / "out.txt"
    art.write_text("the substrate does not have this shape\n",
                   encoding="utf-8")
    readings = SR.read_artifacts([str(art)])
    assert readings, "a bare refusal was not read"
    assert "does not have" in readings[0].reason


def test_a_clean_artifact_proposes_nothing(tmp_path):
    art = tmp_path / "out.txt"
    art.write_text("1371 passed, 1 skipped\nVERDICT: PASS\n", encoding="utf-8")
    assert SR.read_artifacts([str(art)]) == []


def test_the_grounding_points_at_the_artifact(tmp_path):
    art = tmp_path / "out.txt"
    art.write_text("the substrate does not have this shape\n",
                   encoding="utf-8")
    readings = SR.read_artifacts([str(art)])
    lesson = readings[0].to_lesson("")
    assert lesson.grounding.path == str(art)
    assert lesson.grounding.line == 1
    assert "does not have" in lesson.grounding.excerpt


# ---------------------------------------------------------------------------
# 7. the routing is deterministic
# ---------------------------------------------------------------------------

def test_the_routing_puts_each_refusal_in_its_own_store(tmp_path):
    """**AND THE TWO STORES GET DIFFERENT REFUSALS.**

    MEASURED 2026-11-06: the mutation that collapsed the routing to
    one store stayed GREEN -- because the routing tests only checked
    the routing FUNCTION and never checked that the two stores
    actually received different lessons.

    **A ROUTE THAT IS NEVER EXERCISED IS A ROUTE THAT DOES NOT WORK.**
    """
    art = tmp_path / "out.txt"
    art.write_text("the substrate does not have this shape\n"
                   "the probe must be able to fail\n",
                   encoding="utf-8")
    stores = SR.open_stores(str(tmp_path))
    SR.review([str(art)], stores)
    field_rules = [l.rule for l in stores[SR.Store.FIELD].held()]
    lesson_rules = [l.rule for l in stores[SR.Store.LESSON].held()]
    # AND BOTH STORES MUST HOLD ONE, and not merely "the two differ".
    #
    # MEASURED 2026-11-06: the first version of this test asserted
    # only that the two lists DIFFER -- and an EMPTY list differs from
    # a full one, so the mutation that collapsed the routing to ONE
    # store left the LESSON store empty and the test still passed.
    #
    # **"THEY DIFFER" IS SATISFIED BY ONE OF THEM BEING EMPTY.**
    assert field_rules, "the FIELD store got nothing"
    assert lesson_rules, "the LESSON store got nothing"
    assert set(field_rules).isdisjoint(lesson_rules)


def test_the_routing_is_the_same_every_time():
    reasons = [
        "the substrate does not have this shape",
        "the command must be run before the count",
        "the module is not wired",
        "the check must be able to fail",
    ]
    first = [SR.route_reason(r) for r in reasons]
    second = [SR.route_reason(r) for r in reasons]
    assert first == second


def test_the_whitelist_is_a_whitelist():
    """**A BLACKLIST ADMITS EVERYTHING NEW.**"""
    assert "memory_add" in SR.WRITABLE_TOOLS
    assert "lesson_append" in SR.WRITABLE_TOOLS


# ---------------------------------------------------------------------------
# the module's own selftest
# ---------------------------------------------------------------------------

def test_the_module_selftest_passes():
    assert SR._selftest() == 0
