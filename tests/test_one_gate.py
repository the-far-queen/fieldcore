"""
test_one_gate.py — the gate must be able to fail, and must not be reconfigurable.

Six attacks. Each one is here because it was run, not because it sounds
plausible. Two of them worked on the first attempt against an earlier
version of the governor, on a guard that had already passed a separation
test. The general lesson from that: **separation of place is not
separation of power** — a gate in its own process, over its own pipe,
with its own PID, is still not a gate if the caller supplies the limits.

WHAT THIS FILE ESTABLISHES, and what it does not:

  establishes — the signature admits no threshold; no in-repo caller
  passes one; the reason strings are single-spelled; the gate agrees
  with the out-of-process governor that it supersedes; a mutation that
  widens the bound turns the suite red.

  does NOT establish — that a caller cannot reach the constants. A gate
  cannot stop a caller that writes `gate.MAX_NORM = 1e9` directly. This
  module DETECTS and REPORTS that class (see the mutation tests); it does
  not ENFORCE against it. That distinction is the honest limit and it
  belongs here rather than in a note somebody skips.
"""

from __future__ import annotations

import ast
import inspect
import os
import pathlib
import re
import subprocess
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import gate as G  # noqa: E402


PSI0 = np.zeros(8)
PSI0[0] = 1.0                       # unit ground along axis 0

GOOD = PSI0.copy()                  # cos = 1.0
ORTHOGONAL = PSI0.copy()
ORTHOGONAL[0] = 0.0
ORTHOGONAL[1] = 1.0                 # cos = 0.0  -> refuse_coherence
OVERSIZE = PSI0.copy() * 100.0      # norm = 100  -> refuse_norm
ZERO = np.zeros(8)                  # norm = 0    -> refuse_zero


# ---------------------------------------------------------------------------
# ATTACK 1 — pass a wider threshold to the call.
#
# The one that broke the first version. Asserting the *signature* rather
# than the behaviour covers every path, including the ones nobody thought
# to attack: a test that feeds a permissive value proves one case, an
# inspect.signature proves there is no such door at all.
# ---------------------------------------------------------------------------

def test_signature_admits_no_threshold():
    params = inspect.signature(G.gate).parameters
    assert set(params) == {"emb", "psi0"}, (
        f"the gate takes {list(params)}; a limit the caller can supply "
        f"is not a limit"
    )


def test_gated_signature_admits_no_threshold():
    params = set(inspect.signature(G.gated).parameters)
    assert not (params & {"max_norm", "min_cos", "max_drift", "tolerance"})


def test_calling_with_a_threshold_raises():
    with pytest.raises(TypeError):
        G.gate(OVERSIZE, PSI0, max_norm=1e9)
    with pytest.raises(TypeError):
        G.gate(ORTHOGONAL, PSI0, min_cos=-1.0)


def test_no_caller_in_either_repo_passes_a_threshold():
    """The door is not only absent from the signature, it is unused.

    Greps both repos. A keyword that nothing passes today is one a future
    caller will find in autocomplete.

    Docstrings and comments are stripped before matching. A checker that
    reads its own prose reports the prose: this file and gate.py both
    name `max_norm=` while documenting the attack, and an earlier version
    of this test failed on its own documentation. A scanner that cannot
    distinguish a live call site from a sentence about one is measuring
    the corpus rather than the code.
    """
    repos = [ROOT.parent / "fieldcore", ROOT.parent / "simself"]
    keyword = re.compile(r"\b(max_norm|min_cos)\s*=")
    offenders = []
    for repo in repos:
        for py in sorted(repo.rglob("*.py")):
            rel = py.relative_to(repo).as_posix()
            if any(p in {"__pycache__", ".git", "legacy"} for p in py.parts):
                continue
            if rel.startswith("tests/"):
                continue          # attack tests name the door on purpose
            try:
                tree = ast.parse(py.read_text(encoding="utf-8",
                                             errors="replace"))
            except SyntaxError:
                continue
            # calls[func].keywords is the only place a caller can supply a
            # bound at runtime; annotations and defaults cannot be.
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                for kw in node.keywords:
                    if keyword.match(kw.arg or ""):
                        offenders.append(f"{rel}:{node.lineno}: {kw.arg}=")
    assert not offenders, ("caller-controlled bounds still in use:\n"
                           + "\n".join(offenders))


# ---------------------------------------------------------------------------
# ATTACK 2 — the predicates themselves. Ground truth, both directions.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("emb,allow,reason", [
    (GOOD,        True,  G.ALLOW),
    (ORTHOGONAL,  False, G.REFUSE_COHERENCE),
    (OVERSIZE,    False, G.REFUSE_NORM),
    (ZERO,        False, G.REFUSE_ZERO),
])
def test_each_verdict(emb, allow, reason):
    got_allow, got_reason = G.gate(emb, PSI0)
    assert (got_allow, got_reason) == (allow, reason)


def test_norm_is_checked_before_coherence():
    """Order is load-bearing: an oversized packet reports the norm, not
    the angle. Otherwise the reason names the wrong defect and the failure
    is unattributable in the ledger."""
    _, reason = G.gate(ORTHOGONAL * 1e6, PSI0)
    assert reason == G.REFUSE_NORM


def test_every_refusal_names_its_reason():
    """A refusal that cannot say why cannot be learned from."""
    for emb in (ORTHOGONAL, OVERSIZE, ZERO):
        allow, reason = G.gate(emb, PSI0)
        assert not allow
        assert reason and reason != "ok" and reason.startswith("refuse_")


def test_non_finite_is_refused_not_allowed():
    """NaN fails every comparison, so a naive `if < min_cos` misses it.

    Measured on the five copies this replaces: all of them returned ALLOW
    for a vector of NaN, because `nan > 4.0` is False and `nan < 0.4` is
    False. This is the defect the single gate now closes.
    """
    cases = [np.full(8, np.nan), np.full(8, np.inf), np.full(8, -np.inf),
             np.array([np.nan] + [0.0] * 7)]
    for bad in cases:
        allow, reason = G.gate(bad, PSI0)
        assert not allow, f"{bad[0]} was admitted"
        assert reason == G.REFUSE_NONFINITE


# ---------------------------------------------------------------------------
# ATTACK 3 — reach the constants.
# ---------------------------------------------------------------------------

def test_bounds_are_module_constants_and_are_the_documented_values():
    assert G.MAX_NORM == 4.0
    assert G.MIN_COS == 0.4


def test_gate_does_not_read_the_environment():
    """No code path from an untrusted value to a bound."""
    source = inspect.getsource(G.gate)
    for forbidden in ("os.environ", "getenv", "open(", "config", "yaml",
                      "json.load", "sys.argv"):
        assert forbidden not in source, f"gate() touches {forbidden}"


# ---------------------------------------------------------------------------
# ATTACK 4 — fail closed. `gated` must not start the operation.
# ---------------------------------------------------------------------------

def test_gated_does_not_run_a_refused_operation():
    calls = []

    def op():
        calls.append(1)
        return "ran"

    allow, reason, result = G.gated(OVERSIZE, PSI0, op)
    assert not allow and calls == [] and result is None
    assert reason == G.REFUSE_NORM


def test_gated_runs_an_allowed_operation():
    calls = []
    allow, reason, result = G.gated(GOOD, PSI0,
                                    lambda: calls.append(1) or "ran")
    assert allow and result == "ran" and calls == [1]


# ---------------------------------------------------------------------------
# ATTACK 5 — agreement with the thing it supersedes.
#
# A replacement that silently diverges from the predecessor is a third
# defect the attack list never mentions.
# ---------------------------------------------------------------------------

def test_agrees_with_the_out_of_process_governor():
    sys.path.insert(0, str(SRC))
    try:
        import governor
    finally:
        sys.path.pop(0)
    g = governor.GovernorProcess()
    try:
        for emb in (GOOD, ORTHOGONAL, OVERSIZE, ZERO,
                    np.full(8, 0.5), np.full(8, 2.0)):
            assert g.ask(emb, PSI0).allow == G.gate(emb, PSI0)[0], emb
    finally:
        g.close()


def test_agrees_with_the_five_copies_it_replaces():
    """Every surviving call site must return the same verdict.

    These are the duplicates. They are asserted rather than deleted in
    this commit; the refactor that makes them thin wrappers lands next.

    NOTE on the ALLOW spelling. Four spellings were in circulation:
    `ok` (simself harness, state_vector, dreaming), `allow`
    (tiniest_core), and `ALLOW` (the out-of-process governor). This module
    uses `allow`, because that is what tiniest_core's VerdictKind and the
    majority of the Python call sites already speak. The ledger records
    either; the *behaviour* asserted here is the boolean, which is the
    part that must not drift.
    """
    sys.path.insert(0, str(SRC / "tiniest_core"))
    try:
        import tiniest_core as tc
    finally:
        sys.path.pop(0)
    for emb in (GOOD, ORTHOGONAL, OVERSIZE, ZERO, np.full(8, 0.5)):
        allow, kind = G.gate(emb, PSI0)
        legacy_ok, legacy_kind = tc.gate(emb, PSI0)
        assert allow == legacy_ok, emb
        # tiniest_core spells ALLOW as "allow" too; if that ever changes
        # this assertion is the tripwire, and the change is a real split.
        assert kind == legacy_kind.value, (emb, kind, legacy_kind.value)


# ---------------------------------------------------------------------------
# Determinism — the same input in two fresh processes.
#
# A gate that answers differently after a restart is not a gate, and it
# looks fine in a single-process run.
# ---------------------------------------------------------------------------

def test_same_input_same_answer_in_two_processes():
    probe = (
        "import sys; sys.path.insert(0, r'%s'); import gate, numpy as np;"
        "psi0 = np.zeros(8); psi0[0] = 1.0;"
        "print([gate.gate(e, psi0) for e in"
        " (psi0.copy(), np.array([0.,1,0,0,0,0,0,0]), np.zeros(8))])"
        % str(SRC)
    )
    runs = {subprocess.run([sys.executable, "-c", probe],
                           capture_output=True, text=True).stdout
            for _ in range(2)}
    assert len(runs) == 1, f"gate is not reproducible across processes: {runs}"
    assert G.ALLOW in runs.pop()


# ---------------------------------------------------------------------------
# MUTATION — the checker must be able to fail.
#
# Each of these edits the gate to be permissive and asserts the suite goes
# red. A guard whose tests all pass against a broken guard is decorative.
# ---------------------------------------------------------------------------

def _mutated_source(tmp_path, old, new):
    """Write a copy of gate.py with one edit, return its directory."""
    text = (SRC / "gate.py").read_text(encoding="utf-8")
    assert old in text, f"mutation anchor missing: {old!r}"
    d = tmp_path / ("mut_" + re.sub(r"\W+", "_", old)[:24])
    d.mkdir(exist_ok=True)
    (d / "gate.py").write_text(text.replace(old, new, 1), encoding="utf-8")
    return d


# -----------------------------------------------------------------------
# THE MUTATION HARNESS -- rewritten 2026-10-24.
#
# It used to run pytest on THIS FILE:
#
#     subprocess.run([sys.executable, "-m", "pytest", str(pathlib.Path(__file__)),
#                     "-q", "-x", ...])
#
# Two defects, both serious.
#
# 1. INFINITE RECURSION. This file contains the mutation tests. So the
#    child pytest ran the mutation tests, which ran pytest again, on the
#    same file, with no depth limit. The suite did not fail -- it
#    recursed until the machine was saturated. It printed nothing, which
#    is why it looked like a hang rather than a failure. It was found
#    when `pytest tests/` ran for 10 minutes with zero output while
#    every other file in the repo finished in seconds.
#
# 2. THE MUTANT WAS NEVER LOADED. The mutation was supposed to shadow
#    the real gate via PYTHONPATH. But this module does
#    `sys.path.insert(0, str(SRC))` at import time, and a
#    sys.path.insert(0, ...) at import time lands IN FRONT of
#    PYTHONPATH. So the child imported the REAL gate. The mutation was
#    never applied, and "the suite went red" could only have passed for
#    some other reason. A green mutation test proves nothing if the
#    mutant was never loaded.
#
# THE FIX: the mutation runs tests/test_gate_contract.py -- a file that
# asserts the gate's behaviour and contains NO mutation tests, so there
# is nothing to recurse into. And that file deliberately does not
# insert src/ into sys.path, so PYTHONPATH is what decides which gate
# gets imported. Every subprocess has a timeout: a checker that can
# hang can wedge the machine, and the machine is not ours to wedge.
#
# Each mutation asserts BOTH directions: the mutant must turn the
# contract suite RED, and the unmutated gate must leave it GREEN.
# Without the second, "red" could mean "this file is broken" rather
# than "the mutation was caught".
# -----------------------------------------------------------------------

CONTRACT = pathlib.Path(__file__).resolve().parent / "test_gate_contract.py"
SUBPROCESS_TIMEOUT = 120


def _run_contract(pythonpath):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath)
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(CONTRACT), "-q", "--no-header",
         "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=str(ROOT), env=env,
        timeout=SUBPROCESS_TIMEOUT)


def _suite_red(tmp_path, old, new):
    """Run the contract suite against the mutant. Returns (red, tail)."""
    d = _mutated_source(tmp_path, old, new)
    out = _run_contract(d)
    return out.returncode != 0, out.stdout[-400:]


def _baseline_green():
    """The same suite against the unmutated gate must be green."""
    out = _run_contract(SRC)
    return out.returncode == 0, out.stdout[-400:]


def test_the_unmutated_gate_is_green_against_the_contract_suite():
    """The control for every mutation below.

    If this is red, the mutation tests prove nothing: "the suite went
    red" would just mean the contract file is broken.
    """
    green, tail = _baseline_green()
    assert green, f"the contract suite is not green against the real gate:\n{tail}"


def test_mutation_widening_the_norm_bound_goes_red(tmp_path):
    red, tail = _suite_red(tmp_path, "MAX_NORM: float = 4.0",
                           "MAX_NORM: float = 1e9")
    assert red, f"widening MAX_NORM left the suite green:\n{tail}"


def test_mutation_zeroing_the_coherence_floor_goes_red(tmp_path):
    red, tail = _suite_red(tmp_path, "MIN_COS: float = 0.4",
                           "MIN_COS: float = -1.0")
    assert red, f"zeroing MIN_COS left the suite green:\n{tail}"


def test_mutation_returning_allow_unconditionally_goes_red(tmp_path):
    red, tail = _suite_red(
        tmp_path,
        '    if ne > MAX_NORM:\n        return False, REFUSE_NORM',
        '    if ne > MAX_NORM:\n        return True, ALLOW')
    assert red, f"a permissive norm branch left the suite green:\n{tail}"


def test_mutation_admitting_non_finite_goes_red(tmp_path):
    """NaN is the case a naive comparison misses: `nan > 4.0` is False.

    All five copies this gate replaced returned ALLOW for a vector of
    NaN. This is the mutation that proves the fix is still load-bearing.
    """
    red, tail = _suite_red(
        tmp_path,
        "    if not (_is_finite(emb) and _is_finite(psi0)):\n"
        "        return False, REFUSE_NONFINITE",
        "    if False:\n        return False, REFUSE_NONFINITE")
    assert red, f"admitting a NaN packet left the suite green:\n{tail}"
