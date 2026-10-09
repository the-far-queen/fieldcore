"""Tests for the out-of-process governor.

Bobby 2026-10-09: "the 747 is well established, governor misplaced."

The placement fix is the point of this suite. Three properties are checked
that the in-process version could never provide:

  1. PROCESS SEPARATION  the governor runs in a different OS process
  2. AUTHORITY           the governed process cannot supply or alter the
                         governor's thresholds
  3. FAIL-CLOSED         absence of an answer is a refusal

The authority tests exist because the first version threaded the limits
through the pipe from the caller, and a governed process walked straight
through the gate by sending a larger limit. A gate whose limits can be
supplied by the thing it gates is not a gate, so every attack that worked
against the first version is now a permanent test.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import governor as G  # noqa: E402

PSI0 = np.array([1.0, 0, 0, 0, 0, 0, 0, 0])
GOOD = np.array([1.0, 0.1, 0, 0, 0, 0, 0, 0])
ORTHOGONAL = np.array([0.0, 1.0, 0, 0, 0, 0, 0, 0])
OVERSIZE = np.array([20.0, 0, 0, 0, 0, 0, 0, 0])


@pytest.fixture()
def gov():
    g = G.GovernorProcess()
    yield g
    g.close()


# ---------------------------------------------------------------- the verdicts


def test_allows_a_coherent_in_bound_state(gov):
    d = gov.ask(GOOD, PSI0)
    assert d.allow and d.verdict is G.Verdict.ALLOW
    assert bool(d) is True


def test_refuses_out_of_bound_norm(gov):
    d = gov.ask(OVERSIZE, PSI0)
    assert not d.allow and d.verdict is G.Verdict.REFUSE_NORM


def test_refuses_orthogonal(gov):
    d = gov.ask(ORTHOGONAL, PSI0)
    assert not d.allow and d.verdict is G.Verdict.REFUSE_COHERENCE


def test_refuses_zero_state(gov):
    d = gov.ask(np.zeros(8), PSI0)
    assert not d.allow


def test_every_refusal_carries_a_reason(gov):
    """A refusal a caller cannot interpret is a refusal nobody can act on.
    """
    for bad in (OVERSIZE, ORTHOGONAL, np.zeros(8), "junk", None,
                np.array([np.nan] * 8), np.array([np.inf] * 8)):
        d = gov.ask(bad, PSI0)
        assert d.verdict.value.startswith("REFUSE") or d.allow
        assert d.verdict is not G.Verdict.ALLOW or d.allow


def test_malformed_input_does_not_raise(gov):
    """An exception is not a verdict. Anything unparseable is refused."""
    for bad in ("not an array", None, [[["nested"]]], {"a": 1}, object()):
        d = gov.ask(bad, PSI0)
        assert isinstance(d, G.Decision)


# ---------------------------------------------------------------- separation


def test_governor_runs_in_a_different_process(gov):
    assert gov.pid != os.getpid()


def test_report_shows_two_pids():
    r = G.report()
    assert r["governor_pid"] != r["caller_pid"]
    assert r["same_process"] is False


def test_pids_are_reported_and_positive(gov):
    assert gov.pid > 0


# ---------------------------------------------------------------- authority


def test_caller_cannot_pass_thresholds(gov):
    """The attack that broke the first version."""
    with pytest.raises(TypeError):
        gov.ask(ORTHOGONAL, PSI0, max_norm=1000.0)
    with pytest.raises(TypeError):
        gov.ask(ORTHOGONAL, PSI0, min_cos=-1.0)


def test_forged_message_cannot_widen_the_limits(gov):
    """Bypass the API and write the pipe directly. The governor must use
    its OWN constants and ignore any limits in the message.
    """
    gov._parent_conn.send({"emb": OVERSIZE, "psi0": PSI0,
                           "max_norm": 1000.0, "min_cos": -1.0})
    assert gov._parent_conn.poll(5.0), "no reply from the governor"
    reply = gov._parent_conn.recv()
    assert reply["allow"] is False
    assert reply["verdict"] == G.Verdict.REFUSE_NORM.value


def test_mutating_caller_side_constants_does_not_help(gov):
    """The caller can reassign its own module constants; the governor runs
    in another address space and never sees them.
    """
    original_norm, original_cos = G.MAX_NORM, G.MIN_COS
    try:
        G.MAX_NORM = 1e9
        G.MIN_COS = -1e9
        assert not gov.ask(ORTHOGONAL, PSI0).allow
        assert not gov.ask(OVERSIZE, PSI0).allow
    finally:
        G.MAX_NORM, G.MIN_COS = original_norm, original_cos


def test_evaluate_has_no_limit_parameters():
    """Structural, not behavioural: the function that decides cannot be
    given different limits by anyone.
    """
    import inspect

    params = inspect.signature(G.evaluate).parameters
    assert "max_norm" not in params
    assert "min_cos" not in params


# ---------------------------------------------------------------- fail-closed


def test_ask_after_close_is_refused(gov):
    gov.close()
    d = gov.ask(GOOD, PSI0)
    assert not d.allow
    assert d.verdict is G.Verdict.REFUSE_UNREACHABLE


def test_absent_governor_refuses():
    """Envelope semantics: no answer means no passage."""
    g = G.GovernorProcess()
    g.close()                          # the process is gone
    d = g.ask(GOOD, PSI0)
    assert not d.allow
    assert d.verdict is G.Verdict.REFUSE_UNREACHABLE


def test_timeout_refuses(gov):
    d = gov.ask(GOOD, PSI0, timeout=0.000001)
    assert not d.allow
    assert d.verdict is G.Verdict.REFUSE_TIMEOUT


# ---------------------------------------------------------------- durability


def test_survives_a_surge_of_malformed_requests(gov):
    """One bad call must never take out the safety channel, or a single
    malformed message would disable refusal for everything after it.
    """
    for _ in range(150):
        gov.ask("garbage", PSI0)
    assert gov.alive
    assert gov.ask(GOOD, PSI0).allow


def test_still_correct_after_the_surge(gov):
    for _ in range(50):
        gov.ask(np.array([np.nan] * 8), PSI0)
    assert not gov.ask(ORTHOGONAL, PSI0).allow
    assert gov.ask(GOOD, PSI0).allow


# ---------------------------------------------------------------- the wrapper


@pytest.fixture(autouse=True)
def _fresh_shared():
    """The module-level governor is process-global, so a test that closes it
    leaves every later test without one. Reset it around each test that
    uses the shared path.
    """
    yield
    globals().pop("_GOV", None)
    if "_GOV" in vars(G):
        del vars(G)["_GOV"]


def test_guarded_run_runs_only_when_allowed():
    calls = []

    def op():
        calls.append(1)
        return "ran"

    d, out = G.guarded_run(GOOD, PSI0, op)
    assert d.allow and out == "ran" and calls == [1]

    d2, out2 = G.guarded_run(ORTHOGONAL, PSI0, op)
    assert not d2.allow and out2 is None and calls == [1]


def test_guarded_run_refuses_when_governor_is_gone():
    gov = G._shared()
    assert gov.alive
    gov.close()
    calls = []
    d, out = G.guarded_run(GOOD, PSI0, lambda: calls.append(1))
    assert not d.allow and out is None and calls == []


# ---------------------------------------------------------------- the old way


def test_in_process_gate_is_still_available_for_comparison():
    """The in-core gate is not deleted. It is the thing being replaced, and
    it must keep working so the two can be compared.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "tiniest_core"))
    try:
        import tiniest_core as tc
    finally:
        sys.path.pop(0)
    ok, kind = tc.gate(GOOD, PSI0)
    assert ok
    bad, kind2 = tc.gate(OVERSIZE, PSI0)
    assert not bad


def test_both_gates_agree_on_the_same_inputs():
    """The out-of-process governor must not silently diverge from the
    in-core predicate it replaces.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "tiniest_core"))
    try:
        import tiniest_core as tc
    finally:
        sys.path.pop(0)
    g = G.GovernorProcess()
    try:
        for emb in (GOOD, ORTHOGONAL, OVERSIZE, np.zeros(8),
                    np.array([1.0, 1, 1, 1, 1, 1, 1, 1]),
                    np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])):
            legacy, _ = tc.gate(emb, PSI0)
            assert g.ask(emb, PSI0).allow == legacy, emb
    finally:
        g.close()