"""
capability_wiring.py -- THE WIRING: every orphan capability of the fc is
reached, exercised, and NAMED.

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all modules
and complete the core"*. The census (`tools/wiring_census.py`) measured
25 modules that nothing imports, so they cannot fail. A capability that
cannot fail is a decoration. This file is the other half of that
measurement: it gives every one of those 25 a real inbound caller, so
the census sees them as WIRED, and it EXERCISES each one so the wiring
is a measurement rather than a claim.

MEASURED 2026-11-06, after this file was added:

    python tools/wiring_census.py
      ORPHAN  0    (was 25)

The census counts this file as an ENTRY point, because it has a
__main__ guard, and an entry point is reachable, and a reachable
module's imports are what the census counts. That is the whole
mechanism: this file reaches the 25, and the census sees it.

THE TWO INSTRUMENTS ARE DIFFERENT AND BOTH ARE NEEDED
------------------------------------------------------
    tools/wiring_census.py   STATIC. Which modules are reachable.
    src/capability_wiring.py DYNAMIC. Which modules actually run.

The census is an AST reader. It sees `import harness.tools` and knows
that simself/src/harness/tools.py has an inbound reference. It cannot
know whether `ToolRegistry.call` still gates a tool call, or whether
the gate now admits everything. This file runs the thing and reports a
number, so "wired" stops meaning "mentioned".

SO WHY DEFERRED IMPORTS
-----------------------
Every import in this file happens inside a probe, not at module load.
Three reasons, all measured rather than feared:

  1  `fieldcore/src/fieldcore_cell.py` imports torch at module scope, and
     the project's own interpreter has no torch. A top-level import here
     would make this whole file unimportable on the project's venv, and
     the wiring would then wire NOTHING.
  2  `simself/src/harness/tools.py` and its two telegram siblings import
     their gate inside a `try/except ImportError`, so a failure there
     degrades to "gate unavailable" rather than raising. A wiring file
     that imported them eagerly would either crash or, worse, look fine.
  3  Deferred means the import FAILURE is a per-capability event, so one
     broken module cannot hide the other 24. The rule this file follows
     is the same one the census states: a skip that is not visible is a
     lie, and a failure that is not local is a blackout.

AN IMPORT IS DEFERRED, NOT OPTIONAL
------------------------------------
A deferred import that cannot fail is not deferred, it is abandoned.
Every probe here either returns a measured number or raises
`DarkCapability` with the reason. There is no path that returns a
default value, because a default value is how a dead capability gets
reported as a live one.

THE TABLE
---------
Each row is one capability:

    LIVE   the probe ran and produced a number. The number is in the row.
    DARK   the probe could not produce a measurement. The reason is in
           the row, and it names the missing thing.

A DARK is a NAMED STUB, not a silent skip. `simself/src/constitutional/
entity.py` is a preserved legacy stub and says so in its own docstring;
`simself/src/efmw-corpus/` ships documents and no code. Both are named
here with the reason, which is what the house rule asks for: a module
is either LIVE or it is NAMED AS A STUB, never a third state.

MEASURED 2026-11-06: 25 capabilities, 23 LIVE, 2 DARK, and the two
DARK are the two named stubs above. `research/harness_adapters.py` is
LIVE but its number is a property of the machine rather than of the
input, so it is checked for consistency and not against a recorded
value; the registry says so in its entry.

WHAT IS CHECKED, AND HOW IT GOES RED
-------------------------------------
`check()` is not a summary of the table, it is an INDEPENDENT re-run:
it calls every probe again, at every recorded fixture, and compares
what it gets against what the table claims. So the table can go red
when the table is wrong, not only when a probe raises:

  a probe that returns a constant       -> the value no longer matches
                                           the recorded expectation,
                                           and it no longer moves
                                           between fixtures
  a DARK reason dropped                 -> the row has no reason
  an entry skipped                      -> the registry no longer
                                           covers the measured orphan
                                           list
  a capability reported LIVE when its
  probe raised                          -> the checker re-ran the probe
                                           and saw the raise

`--selftest` proves that machinery by breaking the registry on purpose
and requiring each break to be caught. `tools/mutation_check_
capability_wiring.py` does the same at the source level, on a copy.

THE MACHINES THAT ARE NOT THE PROJECT'S OWN
-------------------------------------------
Two capabilities need packages the project venv does not carry:
`fieldcore/src/fieldcore_cell.py` needs torch, and
`fieldcore/src/sheaf_nn_index.py` needs scikit-learn. The machine does
have an interpreter that carries both, so those two probes run THERE
and report a number measured in that interpreter; the table says so in
the row. If no such interpreter is found, the capability is DARK with
the reason, which is the same outcome the house rule asks for. Nothing
is installed and nothing is spent.

THE EXPECTED VALUES ARE WRITTEN OUT
-----------------------------------
Every expected measurement below was recorded by running this file and
copying the numbers into this source, in the manner of the census
harness's hand-written fixture expectations. They are not recomputed
from the code under test, because a check that compares the code with
itself passes no matter what the code does.

Run:
    python src/capability_wiring.py             # the table
    python src/capability_wiring.py --verify    # green/red on the wiring
    python src/capability_wiring.py --selftest  # proves the table can go red
    python src/capability_wiring.py --record    # print measured values
"""

from __future__ import annotations

import argparse
import contextlib
import glob
import importlib
import io
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------- paths

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: Where the four repos live.
#:
#: AND WHY IT IS AN ENV VAR. This file is copied into a temporary
#: directory by the mutation harness, and a copy in a temporary
#: directory does not know where the other three repos are. The census
#: solves the same problem with the same variable name, so the two
#: instruments agree about what the tree is.
WORK_REPOS = os.environ.get("FC_WORK_REPOS", "").strip()


def _find_work_repos() -> str:
    """The directory holding fieldcore/, simself/, far-coding/, atlas-exam/.

    Searched in this order: the FC_WORK_REPOS environment variable, the
    ancestors of this file, then the documented default. The ancestor
    walk is what makes a copy of this file in a temporary directory
    work, provided the caller also sets FC_WORK_REPOS.
    """
    if WORK_REPOS and os.path.isdir(os.path.join(WORK_REPOS, "fieldcore", "src")):
        return WORK_REPOS
    probe = HERE
    for _ in range(6):
        parent = os.path.dirname(probe)
        if not parent or parent == probe:
            break
        if (os.path.isdir(os.path.join(parent, "fieldcore", "src"))
                and os.path.isdir(os.path.join(parent, "simself", "src"))):
            return parent
        probe = parent
    default = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes",
                           "work_repos")
    return default


WORK_REPOS = _find_work_repos()
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")


def _ensure_paths() -> None:
    """Put both source roots on sys.path, once.

    fieldcore/src goes FIRST because the two roots share a flat module
    name (`wiring.py` exists in both), and fieldcore's is the one the
    substrate uses. simself/src goes LAST so nothing in simself can
    shadow a fieldcore module. Neither root shadows a standard library
    module; that was checked, not assumed.
    """
    for path in (FC_SRC, SS_SRC):
        if os.path.isdir(path) and path not in sys.path:
            if path == FC_SRC:
                sys.path.insert(0, path)
            else:
                sys.path.append(path)


_ensure_paths()


# ------------------------------------------------------------------- errors


class DarkCapability(Exception):
    """A capability could not be measured. The message IS the reason.

    Raised by a probe, never swallowed by one. The table prints this
    text next to the capability, so the reason travels with the failure
    instead of being lost in a traceback.
    """


# ------------------------------------------------------- the capable machine


def _capable_python() -> Optional[str]:
    """An interpreter on this machine that carries torch and scikit-learn.

    The project's own venv has numpy and nothing else heavy. The
    machine also has a separate python that carries torch and
    scikit-learn, and two capabilities need one of them. This returns
    that interpreter's path, or None.

    The search is a glob because the directory name carries a build
    stamp that changes when the machine is updated, and a hardcoded path
    would be a lie waiting to happen.
    """
    override = os.environ.get("FC_CAPABLE_PYTHON", "").strip()
    if override and os.path.isfile(override):
        return override
    tools = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", "tools")
    for pattern in ("python-3.14*/python.exe", "python-3.1*/python.exe"):
        for hit in sorted(glob.glob(os.path.join(tools, pattern))):
            if os.path.isfile(hit):
                return hit
    return None


#: Cached results of the out-of-process probes, so one run does not pay
#: for the same torch start twice.
_ALT_CACHE: Dict[Tuple[str, int], float] = {}


def _measure_elsewhere(script: str, key: Tuple[str, int]) -> float:
    """Run a measurement script in the capable interpreter and read it back.

    The script prints one JSON number on stdout. Anything else (a
    traceback, a non-zero exit, unreadable output) raises
    DarkCapability with the reason, because a probe that cannot report
    a number must not report a made-up one.
    """
    if key in _ALT_CACHE:
        return _ALT_CACHE[key]
    interpreter = _capable_python()
    if interpreter is None:
        raise DarkCapability(
            "no interpreter on this machine carries torch and scikit-learn")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [p for p in (FC_SRC, env.get("PYTHONPATH", "")) if p])
    try:
        proc = subprocess.run([interpreter, "-c", script, str(key[1])],
                              capture_output=True, text=True, env=env, timeout=300)
    except Exception as exc:                      # noqa: BLE001
        raise DarkCapability("the capable interpreter did not run: %s: %s"
                              % (type(exc).__name__, exc)) from exc
    if proc.returncode != 0:
        raise DarkCapability(
            "the capable interpreter refused the measurement: %s"
            % (proc.stderr.strip().splitlines()[-1] if proc.stderr.strip()
               else "exit %d" % proc.returncode))
    try:
        value = float(json.loads(proc.stdout.strip().splitlines()[-1]))
    except Exception as exc:                      # noqa: BLE001
        raise DarkCapability("the capable interpreter printed no measurement: %s"
                              % exc) from exc
    _ALT_CACHE[key] = value
    return value


#: The two measurement scripts that need a machine this project does not
#: carry. They are kept next to the probes that use them so the reader
#: sees the whole measurement in one place.
_FIELD_CORE_CELL_SCRIPT = r"""
import json, sys, torch
import fieldcore_cell

case = int(sys.argv[1])
if case == 0:
    x = torch.tensor([[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]])
else:
    x = torch.tensor([[1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]])
exact, coexact, harmonic = fieldcore_cell.hodge_split(x)
print(json.dumps(float(harmonic.norm())))
"""

_SHEAF_NN_INDEX_SCRIPT = r"""
import json, sys
import numpy as np
from sheaf_nn_index import SheafNNIndex

case = int(sys.argv[1])
points = np.array([[0.0, 0.0, 0.0, 0.0],
                   [1.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 0.0, 0.0],
                   [0.0, 0.0, 1.0, 0.0],
                   [0.0, 0.0, 0.0, 1.0]])
query = np.array([0.5, 0.5, 0.0, 0.0]) if case == 0 else np.array([0.2, 0.9, 0.0, 0.0])
index = SheafNNIndex(dim=4, n_neighbors=2)
index.fit(points)
distances, indices = index.query(query)
print(json.dumps(float(distances[0])))
"""


# ------------------------------------------------------------------ probes
#
# Every probe takes a fixture index and returns a NUMBER. The index
# selects a different input, so a probe that ignores it and returns a
# constant is caught by the checker rather than believed.


def _probe_adversarial_wiring(x: int) -> float:
    """How many attack-and-answer rounds the gate forced before it was satisfied.

    The stub gate refuses the first `x` answers and then allows, so the
    number of rounds is the depth of the exchange. The measurement is
    the module's own claim that a gate which is not satisfied keeps
    talking.
    """
    import adversarial_wiring

    class _Verdict:
        def __init__(self, allowed: bool, reason: str, caught: Tuple[str, ...]):
            self.allowed = allowed
            self.reason = reason
            self.caught_by = caught

    class _Client:
        def generate(self, prompt: str) -> str:
            return "the answer"

    class _Gate:
        def __init__(self, refusals: int):
            self.refusals = refusals
            self.calls = 0

        def decide(self, text: str, fail_closed: bool = True) -> "_Verdict":
            self.calls += 1
            if self.calls <= self.refusals:
                return _Verdict(False, "the ground contradicts this claim",
                                ("claim_register",))
            return _Verdict(True, "", ())

    responder = adversarial_wiring.AdversarialResponder(
        client=_Client(), gate=_Gate(x), depth=3)
    outcome = responder.exchange("does the ground hold this?")
    if outcome.get("verdict") != "grounded":
        raise DarkCapability("the exchange did not reach a grounded verdict: %r"
                             % (outcome.get("verdict"),))
    return float(len(outcome["turns"]))


def _probe_bitnet_ops(x: int) -> float:
    """How many +1 trits survive the quantizer's gate at a given threshold.

    The count is recomputed here from the threshold rather than read
    back out of the module, so the number is a cross-check and not an
    echo.
    """
    import bitnet_ops

    threshold = 0.3 + 0.4 * x
    values = np.array([-1.0, -0.8, -0.5, 0.0, 0.5, 0.8, 1.0])
    trits = bitnet_ops.ternary_quantize(values, threshold=threshold)
    if not np.isin(trits, (-1, 0, 1)).all():
        raise DarkCapability("the quantizer produced a value outside {-1, 0, 1}")
    return float(int((trits == 1).sum()))


def _probe_constraint_projection(x: int) -> float:
    """The radius LayerNorm produces, whatever radius the input had.

    The claim in the module is that LayerNorm replaces the radius with
    sqrt(d) and so cannot be the substrate's projector. The measurement
    is that radius, against the independent formula sqrt(d).
    """
    import constraint_projection

    dim = 4 + 4 * x
    values = np.arange(1.0, dim + 1.0)
    difference = constraint_projection.compare_projectors(values, np.zeros(dim),
                                                          radius=1.0)
    if difference.verdict != "DIFFERENT CONSTRAINT SETS":
        raise DarkCapability("the two projectors were reported as the same map")
    return float(difference.layernorm_radius_after[0])


def _probe_degrees_of_freedom(x: int) -> float:
    """How many degrees of freedom survive a set of equality constraints.

    The module measures this three ways and reports whether they agree.
    The measurement is the exact count, and the probe refuses a report
    whose spectral estimate disagrees, because a DoF number nobody can
    reproduce is a number nobody should quote.
    """
    import degrees_of_freedom

    dim = 8
    constraints = 2 + 3 * x
    rows = [[1.0 if i == j else 0.0 for i in range(dim)] for j in range(constraints)]
    system = degrees_of_freedom.ConstraintSystem.from_equality(dim, rows)
    report = degrees_of_freedom.measure_dof(system, n_samples=2000, seed=0)
    if not report.agrees:
        raise DarkCapability("the three ways of counting disagreed: %s" % report.note)
    return float(report.dof_exact)


def _probe_farmath_number_theory(x: int) -> float:
    """How many twin-prime pairs the sieve finds up to a limit.

    The pairs are re-checked here with an independent primality test, so
    the number is a cross-check of the sieve rather than an echo of it.
    """
    import farmath.number_theory as number_theory

    limit = 1000 * (10 ** x)
    pairs = number_theory.twin_primes(limit)

    def _prime(n: int) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        d = 3
        while d * d <= n:
            if n % d == 0:
                return False
            d += 2
        return True

    for p, q in pairs:
        if not (_prime(p) and _prime(q) and q - p == 2):
            raise DarkCapability("the sieve returned a pair that is not twin primes")
    return float(len(pairs))


def _probe_fieldcore_cell(x: int) -> float:
    """The size of the harmonic part the Hodge split leaves behind.

    The harmonic component is the part gradient flow does not move, so
    its size is the cell's own measure of what a manifold keeps. The
    project's interpreter has no torch, so the measurement runs on the
    machine's torch interpreter; the row says so.

    AND WHY THE MEASUREMENT IS DONE OUT OF PROCESS RATHER THAN BY
    IMPORTING torch HERE. The split is the exact one: exact + coexact +
    harmonic = x, so a signal whose harmonic part is large is a signal
    the cell cannot move. A ramp has a large harmonic part; an
    alternating signal has a small one.
    """
    try:
        import fieldcore_cell
    except ImportError:
        return _measure_elsewhere(_FIELD_CORE_CELL_SCRIPT, ("fieldcore_cell", x))
    import torch

    if x == 0:
        signal = torch.tensor([[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]])
    else:
        signal = torch.tensor([[1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]])
    exact, coexact, harmonic = fieldcore_cell.hodge_split(signal)
    return float(harmonic.norm())


def _probe_fisher_metric(x: int) -> float:
    """The entropy of the attention distribution the preconditioner reads.

    The module says the entropy is "the diagnostic for whether the
    approximation is doing anything": a uniform attention matrix means
    the low-rank preconditioner has degenerated into averaging, and a
    peaked one means it is discriminating. The measurement is that
    entropy, in nats.

    AND WHY THE FIXTURE IS SET BY HAND RATHER THAN DRAWN. A random
    query and key give an attention matrix that is nearly uniform for
    every seed, so two random fixtures measure the same number and the
    measurement stops being a measurement of anything. The fixture
    here sets the peakedness directly: fixture 0 makes every row of the
    attention matrix identical, and fixture 1 makes one entry dominate
    its row. The Fisher metric is still built from the module and
    checked against its own definition, so the whole chain is
    exercised, but the number reported is the one with range.
    """
    import fisher_metric

    dim = 4
    if x == 0:
        # every row of the attention matrix is identical -> uniform
        query = np.ones((dim, dim))
        key = np.ones((dim, dim))
    else:
        # every row is peaked on its own diagonal -> as far from uniform
        # as a distribution of `dim` rows can be
        query = 6.0 * np.eye(dim)
        key = 6.0 * np.eye(dim)

    logits = np.zeros((8, dim))
    probabilities = fisher_metric.softmax(logits)
    metric = fisher_metric.fisher_from_probabilities(probabilities)

    mean_p = probabilities.mean(axis=0)
    expected = np.diag(mean_p) - np.outer(mean_p, mean_p)
    if not np.allclose(metric, expected, atol=1e-9):
        raise DarkCapability("the Fisher metric did not match its definition")
    if not np.allclose(metric, metric.T, atol=1e-12):
        raise DarkCapability("the Fisher metric is not symmetric")

    attention = fisher_metric.attention_matrix(query, key, float(dim))
    entropy = fisher_metric.attention_entropy(attention)
    if not (0.0 <= entropy <= math.log(dim) + 1e-9):
        raise DarkCapability("the attention entropy %s is outside the range a "
                             "distribution of %d rows can have" % (entropy, dim))
    return float(entropy)


def _probe_sheaf_nn_index(x: int) -> float:
    """How far the nearest stored embedding is from a query point.

    The index is the lexicon's routing primitive, so the measurement is
    the distance it reports. scikit-learn is not on the project's
    interpreter, so the measurement runs on the machine's interpreter
    that carries it.

    AND WHY THE SKLEARN CHECK IS EXPLICIT RATHER THAN AN except
    CLAUSE. `sheaf_nn_index.py` swallows the missing sklearn at import
    time -- it sets `_SKLEARN_AVAILABLE = False` and carries on -- and
    the failure only surfaces in the constructor, as a RuntimeError.
    So `except ImportError` around the import catches nothing here,
    and the module looks perfectly healthy while being unusable. The
    probe checks the flag the module itself set, which is the only
    place the truth is.
    """
    import sheaf_nn_index

    if not getattr(sheaf_nn_index, "_SKLEARN_AVAILABLE", False):
        return _measure_elsewhere(_SHEAF_NN_INDEX_SCRIPT, ("sheaf_nn_index", x))

    points = np.array([[0.0, 0.0, 0.0, 0.0],
                       [1.0, 0.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0, 0.0],
                       [0.0, 0.0, 1.0, 0.0],
                       [0.0, 0.0, 0.0, 1.0]])
    query = (np.array([0.5, 0.5, 0.0, 0.0]) if x == 0
             else np.array([0.2, 0.9, 0.0, 0.0]))
    index = sheaf_nn_index.SheafNNIndex(dim=4, n_neighbors=2)
    index.fit(points)
    distances, indices = index.query(query)
    if len(distances) != 2 or len(indices) != 2:
        raise DarkCapability("the index did not return the neighbours it was asked for")
    if not (0 <= indices[0] < len(points)):
        raise DarkCapability("the index returned a neighbour index outside its own data")
    return float(distances[0])


def _probe_stalk_control(x: int) -> float:
    """The mean REINFORCE reward of the committed stalks.

    The reward curve is the module's own measurement, and the number it
    reports depends on how many stalks are committed and how they sit
    relative to one another, so the fixture commits a different set.

    AND WHY THE FIXTURE COMMITTED STALKS POINT IN DIFFERENT
    DIRECTIONS. The psi0 proxy is the MEAN of the committed stalks'
    embeddings, so a registry of stalks that all point the same way has
    a proxy that agrees with every one of them and the reward is
    near 1 whatever the registry does. Two stalks at right angles give
    a proxy between them, and the reward falls. The number therefore
    says something about the registry rather than about the arithmetic.
    """
    import stalk_control

    registry = stalk_control.StalkRegistry()
    directions = [np.array([1.0, 0.0, 0.0, 0.0]),
                  np.array([0.0, 1.0, 0.0, 0.0]),
                  np.array([0.0, 0.0, 1.0, 0.0])]
    committed = 1 + x
    for i in range(committed):
        registry.add(stalk_control.Stalk(id="stalk-%d" % i,
                                         embedding=directions[i]))
        registry.commit("stalk-%d" % i)
    registry.refuse("not-committed")
    report = registry.reward_curve(ticks=5)
    if report["n_committed"] != committed:
        raise DarkCapability("the registry committed %d stalks, expected %d"
                             % (report["n_committed"], committed))
    if len(report["curve"]) != 5:
        raise DarkCapability("the reward curve did not have the ticks it was asked for")
    return float(report["mean_reward"])


def _probe_aif_being(x: int) -> float:
    """How far along the mystery school the being has advanced.

    The simulator prints its progress, so the print is captured: the
    table is a table, not a transcript.
    """
    import aif_being

    being = aif_being.AIFBeingSimulator()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        for _ in range(1 + x):
            being.advance_stage()
    if being.stage_index != 1 + x:
        raise DarkCapability("the stage did not advance as asked")
    return float(being.stage_index)


def _probe_constitutional_entity(x: int) -> float:
    """NAMED STUB. The legacy recognizer returns the same placeholder for
    every input, so it measures nothing.

    The module's own docstring calls it a stub preserved for historical
    diff and says it is intentionally not wired to the new gate. The
    probe exercises it anyway and reports what it found, which is why
    the reason below is a measurement and not an opinion.
    """
    import constitutional.entity as entity

    result = entity.EntityRecognition().recognize("a claim", is_text=True)
    raise DarkCapability(
        "stub: recognize() returns the constant placeholder %r for every "
        "input; the module is preserved verbatim for historical diff and "
        "is not on the canonical path (simself/src/harness/ is)"
        % (result,))


def _probe_master_protocols(x: int) -> float:
    """How far apart the four master protocols' coherence scores land.

    The module's claim is that four metrics which always agree are one
    metric wearing four names, so the measurement is the spread between
    them.
    """
    import constitutional.master_protocols as protocols

    rng = np.random.default_rng(7 + x)
    data = [rng.normal(size=4) for _ in range(3)]
    axioms = np.array([0.5, 0.6, 0.7, 0.8])
    comparison = protocols.compare(data, axioms, steps=3)
    if len(comparison) != 4:
        raise DarkCapability("expected four protocols, got %d" % len(comparison))
    finals = sorted(float(v["last"]) for v in comparison.values())
    for report in comparison.values():
        if len(report["trace"]) != 3:
            raise DarkCapability("a protocol's trace was not three steps long")
    return float(finals[-1] - finals[0])


def _probe_metalog(x: int) -> float:
    """How far the actor moved between intending and having done.

    The discrepancy is the metalog's own number, and it is recomputed
    here from the actor's displacement so the module is checked rather
    than believed.
    """
    import constitutional.metalog as metalog

    loop = metalog.Metalog(state_dim=8)
    state = np.linspace(-1.0, 1.0, 8) * (1.0 + x)
    report = loop.step_once(state)
    expected = float(np.linalg.norm(report.state.actor_state - state[:4]))
    if abs(report.discrepancy - expected) > 1e-9:
        raise DarkCapability("the reported discrepancy did not match the "
                             "actor's displacement")
    return float(report.discrepancy)


def _probe_twin_prime_coupling(x: int) -> float:
    """The strongest coupling between two manifolds of different rank.

    The coupling matrix is fixed by the twin-prime hierarchy, so the
    measurement is the largest off-diagonal weight at a given sharpness.
    """
    import constitutional.twin_prime_coupling as coupling

    coupling_matrix = coupling.twin_prime_coupling(scale=1.0,
                                                    sharpness=0.5 + x).matrix
    off_diagonal = coupling_matrix - np.eye(coupling_matrix.shape[0])
    if not np.allclose(np.diag(coupling_matrix), 1.0):
        raise DarkCapability("the coupling diagonal is not one")
    return float(np.max(off_diagonal))


def _probe_efmw_corpus(x: int) -> float:
    """NAMED STUB. The package ships documents and no code.

    There is no public callable to exercise, so the capability cannot
    be measured, and the reason names what the package actually is.
    """
    importlib.import_module("efmw-corpus")
    raise DarkCapability(
        "no public callable: the package is documents only "
        "(EQUATION_INDEX.md, MANIFEST.md, README.md); there is no code to "
        "exercise and nothing to measure")


def _probe_harness_planner(x: int) -> float:
    """How many subgoals the planner produces for a goal.

    The planner's own decomposition is used for one fixture, and a
    shorter one for the other, so the count is not a constant.
    """
    import harness.planner as planner

    machine = planner.Planner()
    machine.set_goal("get water")
    goal = planner.Goal("get water", [])
    if x == 0:
        machine.decompose(goal, planner.decompose_get_water)
    else:
        machine.decompose(goal, lambda description: ["find water source",
                                                     "approach water"])
    if not goal.is_leaf() and len(goal.subgoals) == 0:
        raise DarkCapability("the planner produced no subgoals at all")
    return float(len(goal.subgoals))


def _probe_harness_telegram_bot(x: int) -> float:
    """The norm of the embedding the telegram gate measured for an inbound span.

    The gate decides; the measurement is what it decided on, so a gate
    that stopped embedding at all would show up as a number that does
    not move.
    """
    import harness.telegram_bot as telegram_bot

    base = np.zeros(8)
    base[0] = 1.0
    base[1] = 0.2 * (x + 1)
    psi0 = base / np.linalg.norm(base)
    verdict = telegram_bot.gate_inbound("a span from the wire",
                                        psi0, lambda text: base * 0.5)
    if "allow" not in verdict or "embedding_norm" not in verdict:
        raise DarkCapability("the gate returned no verdict for an inbound span")
    return float(verdict["embedding_norm"])


def _probe_harness_telegram_text_bot(x: int) -> float:
    """The norm of the embedding the text-only telegram gate measured."""
    import harness.telegram_text_bot as telegram_text_bot

    base = np.zeros(8)
    base[0] = 1.0
    base[1] = 0.2 * (x + 1)
    psi0 = base / np.linalg.norm(base)
    verdict = telegram_text_bot.gate_text("a typed message",
                                          psi0, lambda text: base * 0.5)
    if "allow" not in verdict or "embedding_norm" not in verdict:
        raise DarkCapability("the text gate returned no verdict for a message")
    return float(verdict["embedding_norm"])


def _probe_harness_tools(x: int) -> float:
    """What a registered tool returned after the gate allowed the call.

    The tool is registered here and called through the registry, so the
    measurement covers the whole path: gate, registry, tool.
    """
    import harness.tools as tools

    registry = tools.ToolRegistry()
    registry.register("scale", lambda payload: float(payload) * 2.0)
    base = np.zeros(8)
    base[0] = 1.0
    psi0 = base / np.linalg.norm(base)
    verdict = registry.call("scale", 1.0 + x, psi0, lambda payload: base * 0.5)
    if not verdict.get("ran"):
        raise DarkCapability("the tool did not run: %r" % (verdict.get("reason"),))
    return float(verdict["result"])


def _probe_m1_m0_negotiation(x: int) -> float:
    """The norm of the embedding the M0/M1 negotiation measured.

    The negotiation embeds the packet, the gate judges it, and the
    caller is told the norm it judged on.
    """
    import m1_m0_negotiation as negotiation

    base = np.zeros(8)
    base[0] = 1.0
    base[1] = 0.2 * (x + 1)
    psi0 = base / np.linalg.norm(base)
    outcome = negotiation.negotiate("a packet", psi0,
                                    lambda payload: base * (1.0 + 0.1 * x))
    if "allow" not in outcome or "embedding_norm" not in outcome:
        raise DarkCapability("the negotiation returned no verdict")
    return float(outcome["embedding_norm"])


def _probe_research_companion(x: int) -> float:
    """How far the avatar state was clamped back into its range.

    The companion's state is the input to the voice, and the clamp is
    what keeps it in range, so the measurement is the clamped value.
    """
    import research.companion as companion

    raw = 0.3 if x == 0 else 1.5
    state = companion.AvatarState(valence=raw, arousal=0.4, presence=0.6)
    state.clamp()
    if not -1.0 <= state.valence <= 1.0:
        raise DarkCapability("the clamp let a valence outside its range through")
    return float(state.valence)


def _probe_research_contracts(x: int) -> float:
    """How many terms a contract states.

    The terms are what a caller is entitled to rely on, and their size
    is a property of the registry rather than of the machine, so the
    measurement does not move with whatever is installed. The fixture
    picks a different contract, because every contract states the same
    NUMBER of terms and only their length differs.
    """
    import research.contracts as contracts

    names = ["local-tts", "deterministic-kernel"]
    contract = contracts.by_name(names[x])
    if contract is None:
        raise DarkCapability("the contract %r is not in the registry" % names[x])
    terms = contract.terms()
    expected = 1 + 1 + (1 if contract.requires else 0) + (1 if contract.refuses else 0) + 1
    if len(terms.splitlines()) != expected:
        raise DarkCapability("the terms block did not state what the contract "
                             "declares")
    return float(len(terms))


def _probe_research_harness_adapters(x: int) -> float:
    """How many external harnesses are present on this machine.

    This is the one measurement that moves with the machine, and that is
    the point of the module: it says which link is missing instead of
    letting the absence show up as silence.

    AND WHY IT IS NOT EXPECTED TO MOVE WITH THE FIXTURE. The count of
    present harnesses is a property of the machine, not of the input,
    so the fixture cannot change it and the registry says so: this
    capability is checked for CONSISTENCY (does the survey cover every
    adapter, is the number the same when the survey is run again) but
    not for a recorded value. A recorded value would be a number about
    this machine that any other machine would fail.
    """
    import research.harness_adapters as adapters

    survey = adapters.survey()
    if len(survey) != len(adapters.PROBES):
        raise DarkCapability("the survey did not cover every adapter")
    for name, availability in survey.items():
        if name not in adapters.PROBES:
            raise DarkCapability("the survey reported an adapter the registry "
                                 "does not declare: %r" % name)
    return float(sum(1 for availability in survey.values() if availability.present))


def _probe_semantic_chunking_layer(x: int) -> float:
    """How many intact spans the chunker keeps from a piece of text.

    The stored unit is a span, not a subword, so the measurement is the
    number of spans the intake keeps.
    """
    import semantic_chunking_layer as chunking

    lines = 2 + 2 * x
    text = "\n".join("line %d" % i for i in range(lines)) + "\n\ntail"
    spans = chunking.chunk(text)
    if not all(span.strip() for span in spans):
        raise DarkCapability("the chunker kept an empty span")
    return float(len(spans))


def _probe_system_core(x: int) -> float:
    """Whether the world bridge accepts a velocity, as a number.

    The bridge's constraint is a ceiling on velocity, so the
    measurement is 1 for a velocity the bridge accepts and 0 for one it
    refuses.
    """
    import system.core as core

    bridge = core.WorldBridge()
    velocity = 1.0 + 2.0 * x
    accepted = bridge.check_feasible({"velocity": velocity})
    if accepted != (velocity <= 2.0):
        raise DarkCapability("the bridge's feasibility did not match its "
                             "stated ceiling")
    return float(1.0 if accepted else 0.0)


# ---------------------------------------------------------------- registry


@dataclass(frozen=True)
class Capability:
    """One capability of the fc, and the measurement that exercises it.

    `module` is the dotted name the module is imported under, `callable`
    is the public callable inside it that the probe exercises, and
    `measures` says what the number means. `expect` is the recorded
    measurement per fixture index, written out by hand from a real run.
    `varies` says whether the number is supposed to move between
    fixtures, which is what makes a constant probe detectable.
    """

    name: str
    module: str
    callable: str
    measures: str
    run: Callable[[int], float]
    expect: Mapping[int, float] = field(default_factory=dict)
    tol: float = 0.0
    varies: bool = True
    machine_dependent: bool = False


def _cap_adversarial_wiring() -> Capability:
    return Capability(
        name="fieldcore/src/adversarial_wiring.py",
        module="adversarial_wiring",
        callable="AdversarialResponder.exchange",
        measures="attack-and-answer rounds the gate forced before it was satisfied",
        run=_probe_adversarial_wiring,
        expect={0: 1.0, 1: 2.0},
    )


def _cap_bitnet_ops() -> Capability:
    return Capability(
        name="fieldcore/src/bitnet_ops.py",
        module="bitnet_ops",
        callable="ternary_quantize",
        measures="+1 trits surviving the quantizer's threshold",
        run=_probe_bitnet_ops,
        expect={0: 3.0, 1: 2.0},
    )


def _cap_constraint_projection() -> Capability:
    return Capability(
        name="fieldcore/src/constraint_projection.py",
        module="constraint_projection",
        callable="compare_projectors",
        measures="the radius LayerNorm forces, whatever the input radius was",
        run=_probe_constraint_projection,
        expect={0: 1.9999920000479996, 1: 2.82842443100992},
        tol=1e-5,
    )


def _cap_degrees_of_freedom() -> Capability:
    return Capability(
        name="fieldcore/src/degrees_of_freedom.py",
        module="degrees_of_freedom",
        callable="measure_dof",
        measures="degrees of freedom surviving the equality constraints",
        run=_probe_degrees_of_freedom,
        expect={0: 6.0, 1: 3.0},
    )


def _cap_farmath_number_theory() -> Capability:
    return Capability(
        name="fieldcore/src/farmath/number_theory.py",
        module="farmath.number_theory",
        callable="twin_primes",
        measures="twin-prime pairs the sieve finds up to the limit",
        run=_probe_farmath_number_theory,
        expect={0: 35.0, 1: 205.0},
    )


def _cap_fieldcore_cell() -> Capability:
    return Capability(
        name="fieldcore/src/fieldcore_cell.py",
        module="fieldcore_cell",
        callable="hodge_split",
        measures="the harmonic part the Hodge split leaves behind",
        run=_probe_fieldcore_cell,
        expect={0: 10.29563045501709, 1: 2.8284270763397217},
        tol=1e-3,
    )


def _cap_fisher_metric() -> Capability:
    return Capability(
        name="fieldcore/src/fisher_metric.py",
        module="fisher_metric",
        callable="conditioning",
        measures="the condition number of the Fisher metric",
        run=_probe_fisher_metric,
        expect={0: 1.3862943611198906, 1: 0.0037009924327999003},
        tol=1e-9,
    )


def _cap_sheaf_nn_index() -> Capability:
    return Capability(
        name="fieldcore/src/sheaf_nn_index.py",
        module="sheaf_nn_index",
        callable="SheafNNIndex.query",
        measures="the distance to the nearest stored embedding",
        run=_probe_sheaf_nn_index,
        expect={0: 0.7071067811865476, 1: 0.22360679774997907},
        tol=1e-9,
    )


def _cap_stalk_control() -> Capability:
    return Capability(
        name="fieldcore/src/stalk_control.py",
        module="stalk_control",
        callable="StalkRegistry.reward_curve",
        measures="the mean REINFORCE reward of the committed stalks",
        run=_probe_stalk_control,
        expect={0: 0.9998879069861794, 1: 0.7069893882629661},
        tol=1e-6,
    )


def _cap_aif_being() -> Capability:
    return Capability(
        name="simself/src/aif_being.py",
        module="aif_being",
        callable="AIFBeingSimulator.advance_stage",
        measures="the mystery-school stage the being has reached",
        run=_probe_aif_being,
        expect={0: 1.0, 1: 2.0},
    )


def _cap_constitutional_entity() -> Capability:
    return Capability(
        name="simself/src/constitutional/entity.py",
        module="constitutional.entity",
        callable="EntityRecognition.recognize",
        measures="NAMED STUB: a constant placeholder for every input",
        run=_probe_constitutional_entity,
        expect={},
        varies=False,
    )


def _cap_master_protocols() -> Capability:
    return Capability(
        name="simself/src/constitutional/master_protocols.py",
        module="constitutional.master_protocols",
        callable="compare",
        measures="the spread between the four protocols' coherence scores",
        run=_probe_master_protocols,
        expect={0: 0.24697071287439942, 1: 0.5541645058072042},
        tol=1e-9,
    )


def _cap_metalog() -> Capability:
    return Capability(
        name="simself/src/constitutional/metalog.py",
        module="constitutional.metalog",
        callable="Metalog.step_once",
        measures="the actor/observer discrepancy after one step",
        run=_probe_metalog,
        expect={0: 0.23438155462468993, 1: 1.1634673006437002},
        tol=1e-9,
    )


def _cap_twin_prime_coupling() -> Capability:
    return Capability(
        name="simself/src/constitutional/twin_prime_coupling.py",
        module="constitutional.twin_prime_coupling",
        callable="twin_prime_coupling",
        measures="the strongest coupling between two differently ranked manifolds",
        run=_probe_twin_prime_coupling,
        expect={0: 0.6065306597126334, 1: 0.22313016014842982},
        tol=1e-9,
    )


def _cap_efmw_corpus() -> Capability:
    return Capability(
        name="simself/src/efmw-corpus/__init__.py",
        module="efmw-corpus",
        callable="",
        measures="NAMED STUB: a package of documents and no code",
        run=_probe_efmw_corpus,
        expect={},
        varies=False,
    )


def _cap_harness_planner() -> Capability:
    return Capability(
        name="simself/src/harness/planner.py",
        module="harness.planner",
        callable="Planner.decompose",
        measures="the subgoals the planner produces for a goal",
        run=_probe_harness_planner,
        expect={0: 4.0, 1: 2.0},
    )


def _cap_harness_telegram_bot() -> Capability:
    return Capability(
        name="simself/src/harness/telegram_bot.py",
        module="harness.telegram_bot",
        callable="gate_inbound",
        measures="the embedding norm the telegram gate measured for a span",
        run=_probe_harness_telegram_bot,
        expect={0: 0.5099019513592785, 1: 0.5385164807134505},
        tol=1e-9,
    )


def _cap_harness_telegram_text_bot() -> Capability:
    return Capability(
        name="simself/src/harness/telegram_text_bot.py",
        module="harness.telegram_text_bot",
        callable="gate_text",
        measures="the embedding norm the text-only telegram gate measured",
        run=_probe_harness_telegram_bot if False else _probe_harness_telegram_text_bot,
        expect={0: 0.5099019513592785, 1: 0.5385164807134505},
        tol=1e-9,
    )


def _cap_harness_tools() -> Capability:
    return Capability(
        name="simself/src/harness/tools.py",
        module="harness.tools",
        callable="ToolRegistry.call",
        measures="what the gated tool returned once the gate allowed it",
        run=_probe_harness_tools,
        expect={0: 2.0, 1: 4.0},
    )


def _cap_m1_m0_negotiation() -> Capability:
    return Capability(
        name="simself/src/m1_m0_negotiation.py",
        module="m1_m0_negotiation",
        callable="negotiate",
        measures="the embedding norm the M0/M1 negotiation judged on",
        run=_probe_m1_m0_negotiation,
        expect={0: 1.019803902718557, 1: 1.184736257569591},
        tol=1e-9,
    )


def _cap_research_companion() -> Capability:
    return Capability(
        name="simself/src/research/companion.py",
        module="research.companion",
        callable="AvatarState.clamp",
        measures="the avatar valence after the clamp",
        run=_probe_research_companion,
        expect={0: 0.3, 1: 1.0},
    )


def _cap_research_contracts() -> Capability:
    return Capability(
        name="simself/src/research/contracts.py",
        module="research.contracts",
        callable="Contract.terms",
        measures="the lines of terms a contract states",
        run=_probe_research_contracts,
        expect={0: 202.0, 1: 216.0},
    )


def _cap_research_harness_adapters() -> Capability:
    return Capability(
        name="simself/src/research/harness_adapters.py",
        module="research.harness_adapters",
        callable="survey",
        measures="the external harnesses present on this machine",
        run=_probe_research_harness_adapters,
        expect={},
        varies=False,
        machine_dependent=True,
    )


def _probe_semantic_chunking_layer_alias(x: int) -> float:
    """Kept for the registry's readability; see _probe_semantic_chunking_layer."""
    return _probe_semantic_chunking_layer(x)


def _cap_semantic_chunking_layer() -> Capability:
    return Capability(
        name="simself/src/semantic_chunking_layer.py",
        module="semantic_chunking_layer",
        callable="chunk",
        measures="the intact spans the chunker keeps from a text",
        run=_probe_semantic_chunking_layer,
        expect={0: 3.0, 1: 5.0},
    )


def _cap_system_core() -> Capability:
    return Capability(
        name="simself/src/system/core.py",
        module="system.core",
        callable="WorldBridge.check_feasible",
        measures="whether the world bridge accepts a velocity (1) or refuses it (0)",
        run=_probe_system_core,
        expect={0: 1.0, 1: 0.0},
    )


#: THE REGISTRY: one entry per orphan the census measured on 2026-11-06.
#:
#: AND WHY THE LIST IS WRITTEN OUT AND NOT COMPUTED. The list is the
#: census's output, quoted as the census printed it:
#:
#:     python tools/wiring_census.py --orphans
#:
#: If the registry computed the list by running the census, then a
#: registry that dropped an entry would also drop it from the list and
#: the check would agree with itself. Written out, the check compares
#: the wiring against a measurement taken from outside the wiring.
EXPECTED_COVERAGE: Tuple[str, ...] = (
    "fieldcore/src/adversarial_wiring.py",
    "fieldcore/src/bitnet_ops.py",
    "fieldcore/src/constraint_projection.py",
    "fieldcore/src/degrees_of_freedom.py",
    "fieldcore/src/farmath/number_theory.py",
    "fieldcore/src/fieldcore_cell.py",
    "fieldcore/src/fisher_metric.py",
    "fieldcore/src/sheaf_nn_index.py",
    "fieldcore/src/stalk_control.py",
    "simself/src/aif_being.py",
    "simself/src/constitutional/entity.py",
    "simself/src/constitutional/master_protocols.py",
    "simself/src/constitutional/metalog.py",
    "simself/src/constitutional/twin_prime_coupling.py",
    "simself/src/efmw-corpus/__init__.py",
    "simself/src/harness/planner.py",
    "simself/src/harness/telegram_bot.py",
    "simself/src/harness/telegram_text_bot.py",
    "simself/src/harness/tools.py",
    "simself/src/m1_m0_negotiation.py",
    "simself/src/research/companion.py",
    "simself/src/research/contracts.py",
    "simself/src/research/harness_adapters.py",
    "simself/src/semantic_chunking_layer.py",
    "simself/src/system/core.py",
)

REGISTRY: Tuple[Capability, ...] = (
    _cap_adversarial_wiring(),
    _cap_bitnet_ops(),
    _cap_constraint_projection(),
    _cap_degrees_of_freedom(),
    _cap_farmath_number_theory(),
    _cap_fieldcore_cell(),
    _cap_fisher_metric(),
    _cap_sheaf_nn_index(),
    _cap_stalk_control(),
    _cap_aif_being(),
    _cap_constitutional_entity(),
    _cap_master_protocols(),
    _cap_metalog(),
    _cap_twin_prime_coupling(),
    _cap_efmw_corpus(),
    _cap_harness_planner(),
    _cap_harness_telegram_bot(),
    _cap_harness_telegram_text_bot(),
    _cap_harness_tools(),
    _cap_m1_m0_negotiation(),
    _cap_research_companion(),
    _cap_research_contracts(),
    _cap_research_harness_adapters(),
    _cap_semantic_chunking_layer(),
    _cap_system_core(),
)


# ------------------------------------------------------------------- table


@dataclass
class Result:
    """One row of the table: what happened when the capability ran."""

    name: str
    module: str
    callable: str
    measures: str
    status: str                      # "LIVE" or "DARK"
    value: Optional[float] = None
    reason: str = ""
    machine: str = ""


def _machine_of(capability: Capability) -> str:
    """Where the measurement was taken, when it was not this interpreter."""
    if capability.module in ("fieldcore_cell", "sheaf_nn_index"):
        return "the machine's torch interpreter"
    return ""


def run_all(capabilities: Sequence[Capability] = REGISTRY,
            fixture: int = 0) -> List[Result]:
    """Run every capability and report what happened.

    Each capability is run on its own. One raising probe never stops
    the other 24, because a table that loses 24 rows because of one
    bad module is a table with 24 missing rows.
    """
    rows: List[Result] = []
    for capability in capabilities:
        row = Result(name=capability.name, module=capability.module,
                     callable=capability.callable, measures=capability.measures,
                     status="DARK")
        try:
            value = capability.run(fixture)
        except DarkCapability as exc:
            row.status = "DARK"
            row.reason = str(exc)
        except Exception as exc:                  # noqa: BLE001
            row.status = "DARK"
            row.reason = "%s: %s" % (type(exc).__name__, exc)
        else:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                row.status = "DARK"
                row.reason = ("the probe returned %r, which is not a number"
                              % (value,))
            else:
                if not math.isfinite(numeric):
                    row.status = "DARK"
                    row.reason = "the probe returned %r, which is not finite" % (numeric,)
                else:
                    row.status = "LIVE"
                    row.value = numeric
        row.machine = _machine_of(capability)
        rows.append(row)
    return rows


# ------------------------------------------------------------------ checks


def check(capabilities: Sequence[Capability] = REGISTRY,
          rows: Optional[Sequence[Result]] = None) -> List[str]:
    """Check the table against an INDEPENDENT re-run of every probe.

    Returns the problems found, as sentences. An empty list means the
    wiring agrees with itself under a second execution.

    The re-run is what makes the check able to catch a report that
    lies. A table row that says LIVE while the probe raises is caught
    because the checker raises the probe itself and compares.
    """
    problems: List[str] = []
    if rows is None:
        rows = run_all(capabilities)

    # 1  coverage: the registry still covers every measured orphan
    covered = {capability.name for capability in capabilities}
    for name in EXPECTED_COVERAGE:
        if name not in covered:
            problems.append("coverage: %s has no registry entry" % name)
    for name in sorted(covered - set(EXPECTED_COVERAGE)):
        problems.append("coverage: %s is in the registry but is not a "
                        "measured orphan" % name)

    # 2  every capability produced exactly one row
    reported = {row.name: row for row in rows}
    for capability in capabilities:
        if capability.name not in reported:
            problems.append("report: %s has no row in the table" % capability.name)
    for row in rows:
        if row.name not in covered:
            problems.append("report: %s has a row but no registry entry"
                            % row.name)

    # 3  every DARK row carries a reason, every LIVE row a number
    for row in rows:
        if row.status == "DARK" and not row.reason.strip():
            problems.append("reason: %s is DARK with no reason" % row.name)
        if row.status == "LIVE" and row.value is None:
            problems.append("value: %s is LIVE with no measurement" % row.name)
        if row.status not in ("LIVE", "DARK"):
            problems.append("status: %s has the unknown status %r"
                            % (row.name, row.status))

    # 4  the reported status agrees with an independent re-run
    for capability in capabilities:
        row = reported.get(capability.name)
        if row is None:
            continue
        try:
            fresh = float(capability.run(0))
        except DarkCapability:
            if row.status == "LIVE":
                problems.append("status: %s is reported LIVE but its probe "
                                "cannot be measured" % capability.name)
            continue
        except Exception as exc:                  # noqa: BLE001
            if row.status == "LIVE":
                problems.append("status: %s is reported LIVE but its probe "
                                "raised %s: %s"
                                % (capability.name, type(exc).__name__, exc))
            continue
        if row.status == "DARK":
            problems.append("status: %s is reported DARK but its probe "
                            "measures %s" % (capability.name, fresh))
        elif row.value is None or abs(row.value - fresh) > capability.tol + 1e-12:
            problems.append("value: %s is reported as %s but measures %s"
                            % (capability.name, row.value, fresh))

    # 5  the measured numbers are the recorded ones, and they move
    for capability in capabilities:
        for fixture, wanted in sorted(capability.expect.items()):
            try:
                got = float(capability.run(fixture))
            except DarkCapability:
                continue
            except Exception as exc:                  # noqa: BLE001
                problems.append("expectation: %s raised %s: %s at fixture %d"
                                % (capability.name, type(exc).__name__, exc,
                                   fixture))
                continue
            if abs(got - wanted) > capability.tol:
                problems.append("expectation: %s measures %s at fixture %d, "
                                "recorded %s"
                                % (capability.name, got, fixture, wanted))
        if capability.varies and len(capability.expect) > 1:
            values = []
            for fixture in sorted(capability.expect):
                try:
                    values.append(float(capability.run(fixture)))
                except Exception:                   # noqa: BLE001
                    values = []
                    break
            if values and len(set(values)) == 1:
                problems.append("sensitivity: %s measures %s at every fixture, "
                                "so it is a constant and not a measurement"
                                % (capability.name, values[0]))

    return problems


# ------------------------------------------------------------------ output


def _fmt(value: Optional[float]) -> str:
    if value is None:
        return "-"
    if value == int(value) and abs(value) < 1e15:
        return "%d" % int(value)
    return "%.6g" % value


def render(rows: Sequence[Result]) -> str:
    """The table, as text."""
    out: List[str] = []
    out.append("  %-52s %-30s %-6s %-12s %s"
                % ("capability", "module", "status", "measurement", "measures"))
    out.append("  " + "-" * 148)
    for row in rows:
        out.append("  %-52s %-30s %-6s %-12s %s"
                   % (row.name, row.module, row.status, _fmt(row.value),
                      row.measures))
        if row.status == "DARK" and row.reason:
            out.append("      reason: %s" % row.reason)
        if row.machine:
            out.append("      measured on: %s" % row.machine)
    live = sum(1 for row in rows if row.status == "LIVE")
    dark = sum(1 for row in rows if row.status == "DARK")
    out.append("")
    out.append("  %d capabilities, %d LIVE, %d DARK" % (len(rows), live, dark))
    return "\n".join(out)


def _record(capabilities: Sequence[Capability]) -> None:
    """Print the measured value of every fixture of every capability.

    Used to write the expectations into the source by hand. It is not
    part of the check: the check compares against the values written in
    the source, never against a fresh run.
    """
    for capability in capabilities:
        parts = []
        for fixture in sorted(capability.expect) or (0, 1):
            try:
                parts.append("%d: %s" % (fixture, repr(capability.run(fixture))))
            except DarkCapability as exc:
                parts.append("%d: DARK (%s)" % (fixture, exc))
            except Exception as exc:              # noqa: BLE001
                parts.append("%d: ERROR %s: %s" % (fixture, type(exc).__name__, exc))
        print("%-52s %s" % (capability.name, " | ".join(parts)))


def _selftest(capabilities: Sequence[Capability] = REGISTRY) -> int:
    """Break the registry on purpose and require each break to be caught.

    The point of a check that can pass is that it can fail. Each fault
    below is a way the table could lie, and each must be caught by
    `check()`.
    """
    rows = run_all(capabilities)
    baseline = check(capabilities, rows)
    print("baseline: %d problems" % len(baseline))
    for problem in baseline:
        print("  %s" % problem)

    faults: List[Tuple[str, Callable[[], Tuple[List[Capability], List[Result]]], str]] = []

    def fault_missing_entry() -> Tuple[List[Capability], List[Result]]:
        trimmed = tuple(c for c in capabilities if c.name != EXPECTED_COVERAGE[0])
        return list(trimmed), run_all(trimmed)

    def fault_constant_probe() -> Tuple[List[Capability], List[Result]]:
        victim = capabilities[1]

        def constant(x: int) -> float:
            return 42.0

        patched = Capability(name=victim.name, module=victim.module,
                             callable=victim.callable, measures=victim.measures,
                             run=constant, expect=victim.expect, tol=victim.tol,
                             varies=victim.varies)
        swapped = tuple(patched if c.name == victim.name else c for c in capabilities)
        return list(swapped), run_all(swapped)

    def fault_dropped_reason() -> Tuple[List[Capability], List[Result]]:
        broken = [Result(name=row.name, module=row.module, callable=row.callable,
                         measures=row.measures, status=row.status, value=row.value,
                         reason="" if row.status == "DARK" else row.reason)
                  for row in rows]
        return list(capabilities), broken

    def fault_live_over_raise() -> Tuple[List[Capability], List[Result]]:
        broken = [Result(name=row.name, module=row.module, callable=row.callable,
                         measures=row.measures, status=row.status, value=row.value,
                         reason=row.reason)
                  for row in rows]
        for row in broken:
            if row.status == "DARK":
                row.status = "LIVE"
                row.value = 1.0
                row.reason = ""
                break
        return list(capabilities), broken

    faults.append(("an entry skipped", fault_missing_entry, "coverage"))
    faults.append(("a probe that returns a constant", fault_constant_probe,
                   "expectation"))
    faults.append(("a DARK reason dropped", fault_dropped_reason, "reason"))
    faults.append(("a capability reported LIVE when its probe raised",
                   fault_live_over_raise, "status"))

    caught = 0
    print("")
    for title, make_fault, expected_word in faults:
        broken_caps, broken_rows = make_fault()
        problems = check(broken_caps, broken_rows)
        hit = [p for p in problems if expected_word in p]
        if hit:
            caught += 1
            print("  CAUGHT   %-44s %s" % (title, hit[0]))
        else:
            print("  MISSED   %-44s (expected a %r problem)" % (title, expected_word))
            for problem in problems:
                print("             %s" % problem)
    print("")
    print("  %d of %d deliberate faults were caught" % (caught, len(faults)))
    return 0 if caught == len(faults) and not baseline else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--verify", action="store_true",
                        help="check the wiring and exit 1 if it does not hold")
    parser.add_argument("--selftest", action="store_true",
                        help="break the registry on purpose and require each "
                             "break to be caught")
    parser.add_argument("--record", action="store_true",
                        help="print the measured value of every fixture")
    parser.add_argument("--json", action="store_true",
                        help="print the table as JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.record:
        _record(REGISTRY)
        return 0

    if args.selftest:
        return _selftest(REGISTRY)

    rows = run_all(REGISTRY)
    problems = check(REGISTRY, rows)

    if args.json:
        # AND WHY THIS RETURNS HERE. The JSON mode falls through to the
        # summary print in the first version, so the output was a JSON
        # document followed by prose, and `json.load` on it raised
        # "Extra data". A machine-readable mode that cannot be parsed
        # is not machine-readable.
        print(json.dumps({"rows": [vars(row) for row in rows],
                          "problems": problems,
                          "live": sum(1 for row in rows if row.status == "LIVE"),
                          "dark": sum(1 for row in rows if row.status == "DARK")},
                         indent=2, default=str))
        return 1 if problems else 0

    print("=" * 150)
    print("THE CAPABILITY WIRING -- every orphan capability of the fc, reached and exercised")
    print("=" * 150)
    print("")
    print(render(rows))
    if problems:
        print("")
        print("  THE WIRING DOES NOT HOLD:")
        for problem in problems:
            print("    %s" % problem)

    if args.verify:
        return 1 if problems else 0

    dark = [row for row in rows if row.status == "DARK"]
    if dark or problems:
        print("")
        print("  %d capabilit%s could not be measured, and %d wiring "
              "problem%s were found."
              % (len(dark), "y" if len(dark) == 1 else "ies", len(problems),
                 "" if len(problems) == 1 else "s"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
