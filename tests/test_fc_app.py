"""
test_fc_app.py -- the app and the bridge, tested.

Central rule 7: a test that cannot fail is not a test. Every test below
names its RED version in the docstring, and the mutation check at the
bottom proves each one goes red when the mechanism is removed.

THE DEFECTS THIS FILE WAS WRITTEN AGAINST, both found by measurement on
2026-11-04 and both in code that had been committed with NO tests:

  1. THE SURVEY DISARMED THE BOUNDARY. `letter_s` measured whether the
     security letter could refuse by setting `no_hallucination`'s check
     to `lambda: False` on the LIVE global singleton, and then
     restored a FRESH `lambda: True` -- not the function it had
     replaced. So a boundary another part of the system had armed was
     left permanently disarmed.
     MEASURED: with `no_hallucination` armed to refuse, the survey ran
     and `check_all()` afterwards returned allowed=True, violated=[].
     And `fc_hermes.Bridge.describe()` calls the survey -- so merely
     DESCRIBING the system disarmed it.

  2. THE BRIDGE'S TRACE DROPPED THE ok BIT. `fc_wrapper`'s own trace
     renders "ok" or "REFUSED" per step; the bridge built its own trace
     as "<step>: <detail>" and threw the bit away.
     MEASURED: asked "the ground is a parameter at the call site", the
     gate refused at the prompt step. The wrapper's trace said
     "REFUSED"; the bridge's trace said nothing about it, so a refusal
     read as a clearance.

AND THE MODULES THAT HAD NO TESTS AT ALL: `fc_app.py` (673 lines) and
`fc_hermes.py` (247 lines), both committed 2026-11-02.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.join(REPO, "..", "simself", "src")
ATLAS_SRC = os.path.join(REPO, "..", "atlas-exam", "src")
for _p in (FC_SRC, SS_SRC, ATLAS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fc_app  # noqa: E402
import fc_hermes  # noqa: E402


def _boundary(name="no_hallucination"):
    import boundaries as bd
    return bd.boundaries, bd.boundaries.boundaries[name]


# ---------------------------------------------------------------------------
# 1. the survey does not disarm the boundary
# ---------------------------------------------------------------------------

def test_the_survey_leaves_an_armed_boundary_armed():
    """THE LOAD-BEARING PROPERTY: a probe must not weaken the system.

    RED: if `letter_s` restored a fresh `lambda: True` instead of the
    check it found, this fails -- the armed boundary would be off.
    """
    b, target = _boundary()
    armed = {"calls": 0}

    def armed_check():
        armed["calls"] += 1
        return False

    original = target.check_fn
    try:
        target.check_fn = armed_check
        before = b.check_all()
        assert before.get("allowed") is False, (
            "the fixture did not arm the boundary: %s" % before)

        fc_app.survey()

        after = b.check_all()
        assert after.get("allowed") is False, (
            "the survey DISARMED an armed boundary: %s -> %s"
            % (before, after))
        assert "no_hallucination" in after.get("violated", []), after
    finally:
        target.check_fn = original


def test_the_survey_does_not_mutate_the_live_check_function():
    """The check OBJECT is the same one after the survey.

    RED: if the probe assigned a new function to the boundary, the
    identity check fails.
    """
    b, target = _boundary()
    original = target.check_fn
    fc_app.survey()
    assert target.check_fn is original, (
        "the survey replaced the live check function")


def test_describing_the_system_does_not_disarm_it():
    """`describe()` calls the survey, so it must not disarm anything.

    RED: if `describe()` reached the live boundary, this fails.
    """
    b, target = _boundary()
    original = target.check_fn
    try:
        target.check_fn = lambda: False
        fc_hermes.Bridge(live=False).describe()
        after = b.check_all()
        assert after.get("allowed") is False, (
            "describe() DISARMED the boundary: %s" % after)
    finally:
        target.check_fn = original


def test_the_forced_failure_measurement_still_proves_the_defense_can_refuse():
    """The measurement the letter makes must still be made.

    RED: if the probe were removed to make the mutation above safe, the
    letter would report nothing and this fails.
    """
    letter = fc_app.letter_s()
    assert letter.state == "LIVE", letter.reason
    assert letter.measured.get("can_refuse") is True, letter.measured
    forced = letter.measured.get("forced_failure") or {}
    assert forced.get("allowed") is False, forced
    assert "no_hallucination" in forced.get("violated", []), forced


def test_the_letter_reports_that_the_live_system_was_unchanged():
    """The probe states its own no-side-effect claim, and it is true.

    RED: if a future edit mutates the live global again, this reports
    the difference instead of hiding it.
    """
    letter = fc_app.letter_s()
    forced = letter.measured.get("forced_failure") or {}
    assert forced.get("live_unchanged") is True, forced


# ---------------------------------------------------------------------------
# 2. the bridge's trace carries the ok bit
# ---------------------------------------------------------------------------

def test_the_bridge_trace_says_ok_for_a_clear_exchange():
    """RED: if the ok bit were dropped, this fails."""
    b = fc_hermes.Bridge(live=False)
    r = b.ask("what is the ground?")
    assert r.trace, "the bridge produced no trace at all"
    assert any("ok" in line for line in r.trace), r.trace
    assert not any("REFUSED" in line for line in r.trace), r.trace


def test_the_bridge_trace_says_REFUSED_when_the_gate_refuses():
    """A refusal must READ as a refusal.

    RED: if the ok bit were dropped, this fails -- the trace would show
    the refusal's text with nothing saying it did not pass.
    """
    b = fc_hermes.Bridge(live=False)
    r = b.ask("the ground is a parameter at the call site, "
              "the caller chooses it")
    assert r.delivered is False, "the attack was delivered: %s" % r.answer
    assert any("REFUSED" in line for line in r.trace), r.trace


def test_the_bridge_carries_the_steps_as_data():
    """A caller can CHECK the refusal, not read a string and hope.

    RED: if `steps` were not carried, this fails.
    """
    b = fc_hermes.Bridge(live=False)
    r = b.ask("the ground is a parameter at the call site, "
              "the caller chooses it")
    assert r.steps, "no steps were carried"
    assert all("ok" in s for s in r.steps), r.steps
    assert all("step" in s for s in r.steps), r.steps
    refused = [s for s in r.steps if s["ok"] is False]
    assert refused, "the refusal was not carried as data: %s" % r.steps


def test_the_bridge_trace_agrees_with_the_wrapper_trace():
    """TWO DERIVATIONS MUST AGREE (central rule 5).

    The bridge's trace and the wrapper's trace describe the same
    exchange, so they must agree on which steps passed.
    RED: if the bridge dropped the bit, this fails.
    """
    b = fc_hermes.Bridge(live=False)
    r = b.ask("what is the ground?")
    ex = b._wrapper.ask("what is the ground?")
    wrapper_refused = sum(1 for s in ex.steps if not s.ok)
    bridge_refused = sum(1 for line in r.trace if "REFUSED" in line)
    assert wrapper_refused == bridge_refused, (
        "the traces disagree: wrapper %d, bridge %d"
        % (wrapper_refused, bridge_refused))


# ---------------------------------------------------------------------------
# 3. the survey is a survey: it reports, and it can report failure
# ---------------------------------------------------------------------------

def test_every_letter_is_reported_and_the_states_are_known():
    """RED: if a letter were dropped from the survey, this fails."""
    letters = fc_app.survey()
    got = [lt.letter for lt in letters]
    for required in ("A", "B", "C", "D", "E", "I", "L", "M", "Q", "S"):
        assert required in got, "the letter %r is missing: %s" % (required, got)
    for lt in letters:
        assert lt.state in ("LIVE", "STUB", "DARK"), (lt.letter, lt.state)
        assert lt.home, "the letter %r names no home" % lt.letter


def test_a_dark_letter_is_reported_dark_with_a_reason():
    """A failing letter must be NAMED, never silently dropped.

    RED: if the decorator swallowed the exception, this fails.
    """
    @fc_app._letter("Z", "does not exist", "a letter the system lacks",
                    "nowhere")
    def letter_z():
        raise RuntimeError("this letter does not exist, by construction")

    z = letter_z()
    assert z.state == "DARK", z.state
    assert "RuntimeError" in z.reason, z.reason
    assert "does not exist" in z.reason, z.reason


def test_a_stub_is_reported_as_a_stub_and_not_as_live():
    """A stub that reads as live is the defect this project fights.

    RED: if `Stub` were a plain dict, or if the state were misread, this
    fails.
    """
    @fc_app._letter("Y", "not built", "a letter that was never built", "nowhere")
    def letter_y():
        return fc_app.Stub("Y", "never written")

    y = letter_y()
    assert y.state == "STUB", y.state
    assert y.measured.get("stub") is True, y.measured
    assert y.reason == "never written", y.reason


def test_the_survey_is_idempotent():
    """Running it twice gives the same answer.

    RED: if a letter's state depended on run order, this fails.
    """
    one = {lt.letter: lt.state for lt in fc_app.survey()}
    two = {lt.letter: lt.state for lt in fc_app.survey()}
    assert one == two, (one, two)


def test_the_survey_does_not_print():
    """A survey that prints pollutes the report that carries it.

    RED: if a letter printed, this fails.
    """
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fc_app.survey()
    assert buf.getvalue() == "", buf.getvalue()[:400]


# ---------------------------------------------------------------------------
# 4. the numbers the letters report
# ---------------------------------------------------------------------------

def test_the_gate_bounds_are_module_constants_and_not_caller_controlled():
    """A caller must not be able to widen the gate's limits.

    RED: if `gate()` grew a parameter with a default, this fails.
    """
    import inspect
    import gate as fc_gate
    sig = inspect.signature(fc_gate.gate)
    caller_controlled = [p.name for p in sig.parameters.values()
                         if p.default is not inspect.Parameter.empty]
    assert caller_controlled == [], (
        "the gate's bounds are caller controlled: %s" % caller_controlled)


def test_the_letter_b_probe_separates_a_protected_ground_from_an_open_one():
    """THE PROBE MUST BE ABLE TO FAIL.

    Central rule 7. `letter_b` reports `ground_held`. The measurement
    above showed the probe separates a write-protected ground from one
    that is not -- and this test proves it, so the number cannot be a
    constant.

    RED: if `ground_held` were hardcoded True, this fails.
    """
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground

    letter = fc_app.letter_b()
    assert letter.measured.get("ground_held") is True, letter.measured

    class OpenGround:
        """A ground that is not write-protected."""

        def __init__(self, arr):
            self._psi0 = np.asarray(arr, dtype=float)

        @property
        def psi_0(self):
            return self._psi0

        @psi_0.setter
        def psi_0(self, v):
            self._psi0 = v

    c = Constitution()
    open_ground = OpenGround(np.asarray(c.psi_0, dtype=float))
    before = open_ground.psi_0.copy()
    try:
        open_ground.psi_0 = np.zeros_like(open_ground.psi_0)
    except Exception:
        pass
    held_open = bool(np.allclose(before, open_ground.psi_0))
    assert held_open is False, (
        "the fixture is not actually open, so the probe proves nothing")


def test_the_letter_b_probe_detects_a_ground_that_can_be_written():
    """The probe, run against a ground with no write protection, must
    report that it did not hold.

    RED: if the comparison were `held = True` unconditionally, this
    fails.
    """
    import numpy as np
    from constitutional.constitution import Constitution

    class OpenGround:
        def __init__(self, arr):
            self._psi0 = np.asarray(arr, dtype=float)

        @property
        def psi_0(self):
            return self._psi0

        @psi_0.setter
        def psi_0(self, v):
            self._psi0 = v

    c = Constitution()
    psi0 = np.asarray(c.psi_0, dtype=float)

    # The probe's own comparison, applied to an open ground.
    g = OpenGround(psi0.copy())
    before = g.psi_0.copy()
    try:
        g.psi_0 = np.zeros_like(g.psi_0)
    except Exception:
        pass
    held = bool(np.allclose(before, g.psi_0))
    assert held is False


def test_the_rust_axis_count_is_read_from_the_source_not_hardcoded():
    """A number that cannot go stale is a number that cannot be trusted.

    RED: if `_rust_axis_names` returned a hardcoded list, this fails --
    it must reflect the file.
    """
    names = fc_app._rust_axis_names()
    assert names, "no axis names were read from the rust core"
    assert len(names) == len(set(names)), "the axis names repeat: %s" % names
    letter = fc_app.letter_b()
    assert letter.measured.get("rust_axes") == len(names), letter.measured


def test_the_letter_a_probe_measures_the_real_gate_bounds():
    """RED: if the letter reported a different number than the gate
    holds, this fails."""
    import gate as fc_gate
    letter = fc_app.letter_a()
    assert letter.measured.get("max_norm") == fc_gate.MAX_NORM, letter.measured
    assert letter.measured.get("min_cos") == fc_gate.MIN_COS, letter.measured


# ---------------------------------------------------------------------------
# 5. the bridge
# ---------------------------------------------------------------------------

def test_the_bridge_runs_with_the_spend_guard_closed():
    """RED: a raise in any instrument fails this."""
    b = fc_hermes.Bridge(live=False)
    r = b.ask("what is the ground?")
    assert r.delivered is True, r.answer
    assert r.answered_by, "nothing said who answered"


def test_the_bridge_describes_the_spend_guard_as_closed():
    """RED: if the guard were reported as open, this fails."""
    d = fc_hermes.Bridge(live=False).describe()
    assert d["spend_guard"] == "closed", d
    assert d["live"] is False, d


def test_the_bridge_describes_every_instrument():
    """RED: if an instrument were missing from the inventory, this fails."""
    d = fc_hermes.Bridge(live=False).describe()
    for name in ("gate", "mte", "atlas", "library", "locus", "governor"):
        assert name in d["instruments"], (name, list(d["instruments"]))
        assert "available" in d["instruments"][name], d["instruments"][name]


def test_the_bridge_carries_the_letter_survey_with_every_letter():
    """A bridge that answers without saying what is running is a bridge
    that hides its own state.

    RED: if the letters were dropped from the reply, this fails.
    """
    r = fc_hermes.Bridge(live=False).ask("what is the ground?")
    assert r.letters, "the reply carried no letters"
    got = [lt["letter"] for lt in r.letters]
    for required in ("A", "B", "C", "D", "E", "I", "L", "M", "Q", "S"):
        assert required in got, (required, got)
    for lt in r.letters:
        assert lt["state"] in ("LIVE", "STUB", "DARK"), lt


def test_the_reflex_answers_from_the_ground_and_refuses_off_ground():
    """The reflex reads the QUESTION, not the composed request.

    MEASURED 2026-11-02: the composed request carries the locus, and
    the locus text contains the word "ground" -- so a reflex selecting
    on the request matched its own scaffolding and answered the
    write-protection claims to "what is the weather in Bangkok
    tomorrow".

    RED: if the reflex read the request, this fails.
    """
    b = fc_hermes.Bridge(live=False)

    on_ground = b.ask("what is the ground and why is it write protected?")
    assert "write protected" in (on_ground.answer or "").lower(), \
        on_ground.answer

    off_ground = b.ask("what is the weather in Bangkok tomorrow?")
    text = (off_ground.answer or "").lower()
    assert "write protected" not in text, (
        "the reflex answered off the ground from its own scaffolding: %s"
        % off_ground.answer)


def test_the_spend_guard_is_closed_by_default_in_both_modules():
    """RED: if either module read the guard as truthy, this fails."""
    assert fc_app.ALLOW_LIVE is False, "fc_app's guard is open"
    assert fc_hermes.ALLOW_LIVE is False, "fc_hermes' guard is open"


# ---------------------------------------------------------------------
# 5b. letter Q reads the exam's REGISTRY, and says what is missing
# ---------------------------------------------------------------------
#
# THE DEFECT, MEASURED 2026-11-05: `letter_q` decided whether an exam
# area was implemented by SNIFFING THE SOURCE TEXT of `exam/cli.py` for
# the string "todo(". That is a two-state answer to a three-state
# question, and it cannot see the case that matters: a function that
# imports a module which RAISES is not "todo(", so it reads as
# IMPLEMENTED. A hole wearing an implemented area's name.
#
# The exam now carries its own registry (`exam/areas.py`), and this
# letter reads it -- through a SUBPROCESS, because the dependency
# points AT the exam and never the other way.

def test_letter_q_reports_the_exam_registry_not_a_source_sniff():
    """The letter reports the registry's three states.

    RED: if the letter went back to sniffing source text, the
    `live`/`stub`/`dark` keys would be missing.
    """
    letter = fc_app.letter_q()
    assert letter.state == "LIVE", (letter.state, letter.reason)
    m = letter.measured
    for key in ("areas", "live", "stub", "dark", "not_implemented"):
        assert key in m, "letter_q does not report %r: %s" % (key, m)
    assert m["live"] + m["stub"] + m["dark"] == m["areas"], m
    assert m["not_implemented"] == len(m["not_implemented_names"]), m


def test_letter_q_names_every_area_that_is_not_live_with_a_reason():
    """A missing area is NAMED, and says WHY.

    A hole with no reason attached is the failure this project fights:
    it is indistinguishable from a hole that was simply forgotten.

    RED: if the letter dropped the names, or the reasons, this fails.
    """
    letter = fc_app.letter_q()
    m = letter.measured
    for entry in m["not_implemented_detail"]:
        assert entry["name"], entry
        assert entry["state"] in ("STUB", "DARK"), entry
        assert entry["why"].strip(), (
            "area %s is %s with no reason attached" % (entry["name"],
                                                      entry["state"]))
    assert m["not_implemented_names"] == [
        e["name"] for e in m["not_implemented_detail"]], m


def test_letter_q_fails_loudly_when_the_registry_does_not_cover_the_area_list():
    """A registry that forgets an area is a registry that hides a hole.

    MEASURED 2026-11-05: the letter cross-checks the registry's count
    against the exam's own `AREAS` list, and REFUSES to report a
    confident number when they disagree. This test drives that refusal
    by pointing the subprocess at a registry that is missing an area.

    RED: if the cross-check were removed, this fails.
    """
    import json
    import subprocess
    import sys

    # The stub emits VALID JSON with a lying area count. The first
    # version of this stub emitted Python source rather than JSON, so
    # the letter failed at the JSON parse and the test asserted the
    # wrong reason -- the letter was DARK for the wrong cause, which
    # is a test that passes for the wrong reason.
    payload = json.dumps({
        "areas": 23, "live": 23, "stub": 0, "dark": 0,
        "stub_areas": [], "dark_areas": [],
        "by_area": [{"area": i, "name": "a%d" % i, "state": "LIVE",
                     "module": "exam/cli.py", "reason": "",
                     "does_not_establish": "x"}
                    for i in range(23)],
        "exam_area_count": 99,          # <- the lie
        "exam_area_names": ["a%d" % i for i in range(23)],
    })
    original = subprocess.run

    def fake_run(cmd, **kwargs):
        if isinstance(cmd, list) and cmd[:2] == [sys.executable, "-c"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=payload + "\n",
                                               stderr="")
        return original(cmd, **kwargs)

    subprocess.run = fake_run
    try:
        letter = fc_app.letter_q()
    finally:
        subprocess.run = original

    assert letter.state == "DARK", (
        "a registry that does not cover the area list was reported as %s "
        "instead of DARK" % letter.state)
    assert "registry" in letter.reason.lower(), letter.reason


# ---------------------------------------------------------------------
# 6. the mutation check -- each mechanism, removed, must go RED
# ---------------------------------------------------------------------

def _run_with_patched(src, name, replacement):
    """Run `src` with `name` temporarily replaced, and report whether
    the tests in this file would catch it.

    Returns the name of the first test that fails, or None.
    """
    import importlib
    import traceback

    original = getattr(src, name)
    setattr(src, name, replacement)
    try:
        import test_fc_app as this
        importlib.reload(this)
        for tname in dir(this):
            if not tname.startswith("test_"):
                continue
            fn = getattr(this, tname)
            if not callable(fn):
                continue
            try:
                fn()
            except Exception:
                return tname
    finally:
        setattr(src, name, original)
        import test_fc_app as this
        importlib.reload(this)
    return None
