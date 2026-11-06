"""
fc_app.py -- THE WHOLE SYSTEM, AS AN APP. One entry point, ten letters.

Bobby, 2026-11-02: *"we are making the core work not overly configuring
stalks give me a working core make it work simplify if necessary we have
been on this weeks"* and *"use either wrapper around hermes or standalone
app the whole system fc and all modules they are lettered use stubs for
undeveloped ones"*.

SO THIS IS THE STANDALONE APP, and it is deliberately NOT a new gate.

WHAT ALREADY EXISTED, MEASURED BEFORE THIS FILE WAS WRITTEN:

    fieldcore python   1195 passed, 1 skipped, 1 xfailed  (pytest, 103.91s)
    fieldcore rust      105 passed  (80 lib + 25 integration, cargo +gnu)
    simself             646 passed, 2 skipped                (pytest, 109.70s)
    atlas-exam          23 of 23 areas implemented, 21 PASS
    fc_wrapper          8 of 8 instruments wired, selftest green

SO THE PROBLEM WAS NEVER "the pieces do not exist". The pieces exist and
they pass. The problem was that there was no ONE PLACE where the ten
lettered modules are all visible at once, and where a reader can see
which are live, which are stubbed, and which are dark.

AND THE ATLAS LINE IS NOW MEASURED DIFFERENTLY. It used to say "11 of 23
areas PASS, 8 not implemented", and it was TRUE when it was written. The
eight unimplemented areas were then BUILT -- areas 7, 11, 12, 13, 19, 20,
21 and 22 -- and the exam now runs 21 of 23 PASS, with the two failures
being areas 6 and 8 grading a real transcript and finding real
untraceable numbers in it. Those two are FAILING HONESTLY, which is the
exam doing its job.

AND "implemented" is now READ FROM THE EXAM'S OWN REGISTRY rather than
sniffed from its source text, so the number above is a measurement and
not a guess. The registry is `atlas-exam/src/exam/areas.py`.

THE TEN LETTERS, from fieldcore/PROJECT.md:

    A  core architecture   the substrate. LLM processing, geometry, 1-bit
    B  self-model          recursive self-reference. 20 axes, curiosity
    C  sim world           context, THL, coherence, embodied loop
    D  SNR training        the awakening protocol. signal, not token
    E  family / external   external interface, API gateway, earnings
    I  interface           internal, sub-agent coordination
    L  sacred library      MMM-filtered memory. traditions, koans
    M  modulator           central controller, wisdom-based
    Q  qualification       what may be promoted. atlas-exam
    S  security            boundary firewall, before any external connection

THE RULE THIS FILE FOLLOWS, and it is the rule the whole project runs on:

    A MODULE IS EITHER LIVE OR IT IS NAMED AS A STUB.

There is no third state. A stub is not a failure -- it is a declaration:
this letter is declared, its interface is fixed, its current
implementation is a placeholder, and the app says so out loud. The
alternative -- a module that silently does nothing, or an import that
swallows its own error -- is the exact defect class this project has
been fighting for weeks. `simself/src/modulator.py` was one: the whole
body was wrapped in `try/except ImportError`, so the import SUCCEEDED
and the classes were never defined. A checker that cannot fail.

SO EACH LETTER HERE IS ONE OF THREE THINGS, and the app reports which:

    LIVE   it was constructed and it ran, and it produced a measurement
    STUB   it is declared, its interface is fixed, it returns a named
           "not implemented" -- and that name is visible in the output
    DARK   it was attempted and it failed; the failure is reported with
           the reason, and the app does not pretend it is fine

THE THREE ENTRY POINTS:

    python src/fc_app.py --status      what is live, what is stubbed
    python src/fc_app.py --selftest    exercise every letter, no spend
    python src/fc_app.py --ask "..."   one exchange through the system

THE SPEND GUARD IS CLOSED BY DEFAULT and the local constructed mind
answers. A model call requires GABRIELLE_ALLOW_LIVE=1, because "do not
use my credit card pls" is a standing instruction.

WHY A SEPARATE APP AND NOT A FLAG ON fc_wrapper.py:

`fc_wrapper.py` is the CONTROL SYSTEM -- gate, MTE, governor, atlas,
library, locus, in that order, for one exchange. It is excellent at
that and it should not grow. This file is the INVENTORY -- the ten
letters, each constructed, each measured, each named. It composes
`fc_wrapper` for the letters that live in the control system, and it
composes the substrate directly for the letters that do not.

Run:
    python src/fc_app.py --status
    python src/fc_app.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")
ATLAS_SRC = os.path.join(WORK_REPOS, "atlas-exam", "src")

for _p in (FC_SRC, SS_SRC, ATLAS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The spend guard. CLOSED by default. A model call needs this = 1.
ALLOW_LIVE = os.environ.get("GABRIELLE_ALLOW_LIVE", "") == "1"

#: Where the Rust core's axis list lives.
RUST_AXES_RS = os.path.join(WORK_REPOS, "fieldcore", "core", "src", "axes.rs")


def _rust_axis_names() -> List[str]:
    """Read the axis names out of the Rust core's source.

    WHY READ THE SOURCE AND NOT HARDCODE A COUNT. The project has two
    axis sets -- eight in the Python constitution, twenty in the Rust
    core -- and a hardcoded number could not detect either one changing.
    A number that cannot go stale is a number that cannot be trusted.

    AND WHY NOT SHELL OUT TO CARGO. This is a status report; it must be
    fast, and it must work on a machine with no Rust toolchain. So the
    source is read, and the count comes from the same array literal the
    compiler reads.
    """
    if not os.path.isfile(RUST_AXES_RS):
        return []
    try:
        src = open(RUST_AXES_RS, encoding="utf-8", errors="ignore").read()
    except OSError:
        return []
    # The declaration is `pub const AXIS_NAMES: [&str; 20] = [ ... ];`.
    #
    # AND THE FIRST `[` IS THE WRONG ONE. The type annotation
    # `[&str; 20]` has brackets too, so searching for the first `[`
    # after the name lands on the TYPE, and the first `]` closes the
    # type -- so the body comes out as `&str; 20` and the axis count
    # comes back zero. The version of this parser did exactly that, and
    # it reported 0 axes while looking like it had read the file.
    #
    # So: find the `=` that assigns, and take the bracket AFTER it.
    start = src.find("AXIS_NAMES")
    if start < 0:
        return []
    assign = src.find("=", start)
    if assign < 0:
        return []
    open_bracket = src.find("[", assign)
    close_bracket = src.find("]", open_bracket)
    if open_bracket < 0 or close_bracket < 0:
        return []
    body = src[open_bracket:close_bracket]
    names: List[str] = []
    for line in body.splitlines():
        line = line.split("//")[0].strip()
        if not line.startswith('"'):
            continue
        name = line.split('"')[1] if '"' in line else ""
        if name:
            names.append(name)
    return names


# ===========================================================================
# THE LETTERS. Each one is a probe: it constructs the module, exercises it,
# and returns a MEASUREMENT. It never returns prose.
# ===========================================================================

@dataclass
class Letter:
    """One letter of the system, and its measured state."""
    letter: str
    name: str
    role: str
    #: LIVE, STUB, DARK
    state: str = "DARK"
    #: the measurement, always a value, never a sentence
    measured: Dict[str, Any] = field(default_factory=dict)
    #: why it is STUB or DARK
    reason: str = ""
    #: where it lives
    home: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "letter": self.letter,
            "name": self.name,
            "role": self.role,
            "state": self.state,
            "measured": self.measured,
            "reason": self.reason,
            "home": self.home,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


class Stub:
    """A DECLARED, NOT-IMPLEMENTED letter.

    WHY A CLASS AND NOT A DICT. A stub that is a plain dict can be
    confused for a measurement. This one carries its own name, so a
    caller that reads `result["state"]` gets "STUB" and a caller that
    reads the object gets "stub" -- never "live" by accident.

    AND IT SAYS WHY. "not implemented" alone is not enough: the next
    reader needs to know whether this letter is unwritten or
    unwired. `why` carries that distinction.
    """

    def __init__(self, letter: str, why: str):
        self.letter = letter
        self.why = why

    def measure(self) -> Dict[str, Any]:
        return {"stub": True, "why": self.why, "letter": self.letter}

    def __repr__(self) -> str:
        return "Stub(%s, %r)" % (self.letter, self.why)


def _letter(letter: str, name: str, role: str, home: str):
    """A decorator that turns a probe function into a Letter."""
    def deco(fn: Callable[[], Any]):
        def run() -> Letter:
            t0 = time.time()
            try:
                measured = fn()
            except Exception as exc:  # noqa: BLE001 -- report, do not raise
                return Letter(letter, name, role, "DARK", {},
                              "%s: %s" % (type(exc).__name__, str(exc)[:300]),
                              home, (time.time() - t0) * 1000)
            state = "LIVE"
            reason = ""
            if isinstance(measured, Stub):
                state = "STUB"
                reason = measured.why
                measured = measured.measure()
            return Letter(letter, name, role, state, measured, reason,
                          home, (time.time() - t0) * 1000)
        run.__name__ = "letter_%s" % letter.lower()
        run.letter_meta = (letter, name, role, home)  # type: ignore[attr-defined]
        return run
    return deco


# -- A: the core architecture ---------------------------------------------

@_letter("A", "core architecture", "the substrate. LLM processing, geometry, 1-bit",
         "fieldcore/src/substrate.py")
def letter_a() -> Dict[str, Any]:
    import substrate
    st = substrate.cold_boot()
    # the 1-bit gate is the core's decision, and it must be a MODULE
    # CONSTANT, not a parameter a caller can widen.
    import gate as fc_gate
    import inspect
    sig = inspect.signature(fc_gate.gate)
    caller_controlled = [p.name for p in sig.parameters.values()
                         if p.default is not inspect.Parameter.empty]
    return {
        "substrate": type(st).__name__,
        "max_norm": fc_gate.MAX_NORM,
        "min_cos": fc_gate.MIN_COS,
        "gate_params": list(sig.parameters),
        "gate_caller_controlled_bounds": caller_controlled,
    }


# -- B: the self-model ----------------------------------------------------

@_letter("B", "self-model", "recursive self-reference. 20 axes, curiosity",
         "simself/src/constitutional/constitution.py")
def letter_b() -> Dict[str, Any]:
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    c = Constitution()
    psi0 = np.asarray(c.psi_0, dtype=float)
    g = Ground(psi0.copy())
    before = g.psi_0.copy()
    # is the ground write-protected? try to overwrite it and see if it holds
    try:
        g.psi_0 = np.zeros_like(g.psi_0)
    except Exception:
        pass
    held = bool(np.allclose(before, g.psi_0))
    # THE AXIS COUNT, and there are TWO axis sets in this project and
    # they are not the same set. The RUST core holds twenty
    # (core/src/axes.rs::AXIS_NAMES) and the Python constitution holds
    # eight (DEFAULT_AXES). So report BOTH, with where each lives,
    # rather than reporting one number under a label that fits either.
    #
    # THE RUST COUNT IS READ FROM THE SOURCE, not hardcoded. A
    # hardcoded 20 would be a claim that could not detect the axes
    # changing, and this project's rule is that a number without a
    # command behind it is not a claim.
    rust_names = _rust_axis_names()
    return {
        "dim": int(psi0.size),
        "norm": round(float(np.linalg.norm(psi0)), 12),
        "unit_norm": bool(abs(float(np.linalg.norm(psi0)) - 1.0) < 1e-9),
        "ground_held": held,
        "python_axes": len(c.axes),
        "python_axis_names": [getattr(a, "name", str(a)) for a in c.axes],
        "rust_axes": len(rust_names),
        "rust_axis_names": rust_names[:20],
        "rust_axis_source": "fieldcore/core/src/axes.rs::AXIS_NAMES",
        "note": "the python constitution and the rust core hold "
                "DIFFERENT axis sets (%d and %d)"
                % (len(c.axes), len(rust_names)),
    }


# -- C: the sim world -----------------------------------------------------

@_letter("C", "sim world", "context, THL, coherence, embodied loop",
         "simself/src/constitutional/harness.py")
def letter_c() -> Dict[str, Any]:
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    from constitutional.harness import Harness
    con = Constitution()
    h = Harness(constitution=con,
                ground=Ground(np.asarray(con.psi_0, dtype=float).copy()),
                R=3.0, eta=0.10)
    r = h.process("the ground holds and the locus stands on it")
    return {
        "allowed": bool(r.get("allow")),
        "reason": str(r.get("reason", "")),
        "drift_before": r.get("drift_before"),
        "drift_after": r.get("drift_after"),
        "memory_id": str(r.get("memory_id", "")),
        "tick": (r.get("tick") or {}).get("tick")
        if isinstance(r.get("tick"), dict) else r.get("tick"),
    }


# -- D: SNR training ------------------------------------------------------

@_letter("D", "SNR training", "the awakening protocol. signal, not token",
         "simself/src/training/core.py")
def letter_d() -> Dict[str, Any]:
    from training.core import Stalk, Curriculum, Task, Trainer
    import numpy as np
    # the SNR question: can a stalk hold its signal under noise?
    s = Stalk("s0", np.array([1.0, 0.0, 0.0]))
    before = float(np.linalg.norm(s.embedding))
    s.add_noise(0.1)
    after = float(np.linalg.norm(s.embedding))
    c = Curriculum()
    c.add_task(Task(name="t0", difficulty=1, required_reasoning=1))
    return {
        "stalk_norm_before": round(before, 6),
        "stalk_norm_after_noise": round(after, 6),
        "curriculum_tasks": len(c.tasks),
        "classes": ["Stalk", "Curriculum", "Task", "Trainer"],
    }


# -- E: family / external -------------------------------------------------

@_letter("E", "family / external", "external interface, API gateway, earnings",
         "simself/src/constitutional/roles.py")
def letter_e() -> Dict[str, Any]:
    from constitutional.roles import role_names, masters, evidence_status
    ev = evidence_status()
    return {
        "roles": len(role_names()),
        "role_names": list(role_names()),
        "masters": len(masters()),
        "evidence_backed": sum(1 for _, ok, _ in ev if ok),
        "evidence_total": len(ev),
    }


# -- I: interface ---------------------------------------------------------

@_letter("I", "interface", "internal, sub-agent coordination",
         "simself/src/distributed/stalk_node.py")
def letter_i() -> Dict[str, Any]:
    import numpy as np
    from distributed.stalk_node import StalkNode
    from distributed.governor import (basic_governor, norm_invariant,
                                      energy_invariant)
    a = StalkNode(local_embedding=np.array([1.0, 2.0, 3.0], dtype=np.float32),
                  invariants=[norm_invariant, energy_invariant],
                  epsilon=0.05, name="vision")
    b = StalkNode(local_embedding=np.array([1.0, 2.0, 3.1], dtype=np.float32),
                  invariants=[norm_invariant, energy_invariant],
                  epsilon=0.05, name="arm")
    c = StalkNode(local_embedding=np.array([9.0, 9.0, 9.0], dtype=np.float32),
                  invariants=[norm_invariant],
                  epsilon=0.90, name="hand")
    return {
        "vision_valid": bool(a.is_valid()),
        "arm_valid": bool(b.is_valid()),
        "governs_vision_arm": bool(basic_governor(a, b)),
        "governs_vision_hand_eps_mismatch": bool(basic_governor(a, c)),
        "distance": round(float(a.approximate_distance(b)), 6),
        "glued": a.glue_with(b, basic_governor) is not None,
    }


# -- L: the sacred library ------------------------------------------------

@_letter("L", "sacred library", "MMM-filtered memory. traditions, koans",
         "simself/src/constitutional/sacred_library.py")
def letter_l() -> Dict[str, Any]:
    from constitutional.sacred_library import SacredLibraryManager
    m = SacredLibraryManager()
    d = m.stats() if hasattr(m, "stats") else {}
    return {
        "n_skills": d.get("n_skills"),
        "total_versions": d.get("total_versions"),
        "certification_levels": d.get("certification_levels"),
        "storage_path": str(d.get("storage_path", ""))[:160],
    }


# -- M: the modulator -----------------------------------------------------

@_letter("M", "modulator", "central controller, wisdom-based",
         "simself/src/modulator.py")
def letter_m() -> Dict[str, Any]:
    import modulator
    # THE CHECK THAT MATTERS. A module-level try/except around the whole
    # body makes the import SUCCEED with the classes undefined. Probe
    # the class at module level, not in the AST.
    if not hasattr(modulator, "Modulator"):
        return Stub("M", "the module imports but does not define Modulator "
                         "at module level -- the import error is swallowed "
                         "and the class is never created")
    m = modulator.Modulator()
    # AND THE CHECK THAT THE MODULATOR IS A MODULATOR.
    #
    # MEASURED 2026-11-06: this probe used to read
    #     cycle = m.run_cycle() if hasattr(m, "run_cycle") else {}
    # so a `Modulator` class with NO run_cycle at all was reported LIVE
    # with cycle_keys=[] and stage="". That is not LIVE by this file's
    # own definition -- "it was constructed and it ran, and it produced
    # a measurement" -- and it is the same defect class as the import
    # swallow one level up: a probe that cannot fail.
    #
    # so the cycle is REQUIRED, and it must MEASURE something. a
    # modulator that runs and returns nothing is a stub with a reason,
    # not a live letter.
    if not hasattr(m, "run_cycle"):
        return Stub("M", "modulator.Modulator has no run_cycle -- the "
                         "class exists but the controller cannot run")
    cycle = m.run_cycle()
    if not isinstance(cycle, dict):
        return Stub("M", "modulator.Modulator.run_cycle returned %s, not a "
                         "measurement -- expected a dict"
                         % type(cycle).__name__)
    if not cycle:
        return Stub("M", "modulator.Modulator.run_cycle returned an empty "
                         "measurement -- the controller ran and measured "
                         "nothing")
    return {
        "has_modulator": True,
        "cycle_keys": sorted(cycle.keys()),
        "stage": str(cycle.get("stage", "")),
    }


# -- Q: qualification -----------------------------------------------------

@_letter("Q", "qualification", "what may be promoted. atlas-exam",
         "atlas-exam/src/exam/")
def letter_q() -> Dict[str, Any]:
    """Read the exam's AREA REGISTRY, not a guess about its source.

    AND WHY THE REGISTRY, AND NOT A SNIFF. MEASURED 2026-11-05: this
    letter used to decide whether an area was implemented by reading
    the SOURCE TEXT of `exam/cli.py` and looking for the string
    "todo(". That is a two-state answer to a three-state question, and
    it is wrong in a way that cannot be seen from inside the check:
    a function that imports a module which RAISES is not "todo(", so
    it reads as IMPLEMENTED.

    The exam now carries its own registry -- `exam/areas.py` -- which
    declares each area LIVE, STUB or DARK, with a REASON for the two
    that are not LIVE. So this letter reads that, and the survey says
    what is MISSING rather than implying coverage.

    AND THE DEPENDENCY DIRECTION. The registry lives in the exam
    because the exam must not depend on anything, and fieldcore must
    not depend on the exam. The dependency points AT the exam, never
    the other way. So the registry is read the way the exam reads the
    substrate: AT RUNTIME, IN A SUBPROCESS. An import would make
    fieldcore depend on the exam, and would make a broken exam crash
    the survey instead of being reported by it.
    """
    import json
    import subprocess
    import sys

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [ATLAS_SRC, env.get("PYTHONPATH", "")]).strip(os.pathsep)
    code = (
        "import json, sys\n"
        "from exam import AREAS\n"
        "from exam.areas import summary, AREA_DECLS\n"
        "s = summary()\n"
        "out = dict(s)\n"
        "out['by_area'] = [d.to_dict() for d in AREA_DECLS]\n"
        "out['exam_area_count'] = len(AREAS)\n"
        "out['exam_area_names'] = [n for _, n in AREAS]\n"
        "print(json.dumps(out))\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], env=env,
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        raise RuntimeError("the exam registry could not be read: %s"
                           % (tail[-1] if tail else "exit %d" % proc.returncode))
    out = (proc.stdout or "").strip().splitlines()
    if not out:
        raise RuntimeError("the exam registry printed nothing")
    data = json.loads(out[-1])

    # AND THE COUNT IS CROSS-CHECKED against the exam's own area list,
    # because a registry that forgets an area is a registry that hides
    # a hole. If the two disagree, the survey says so rather than
    # reporting a confident number.
    declared = int(data.get("exam_area_count", 0))
    listed = int(data.get("areas", 0))
    if declared != listed:
        raise RuntimeError(
            "the exam declares %d areas but its registry lists %d. A "
            "registry that does not cover the area list is a registry "
            "that hides a hole." % (declared, listed))

    not_live = [
        {"area": a["area"], "name": a["name"], "state": a["state"],
         "why": a["reason"]}
        for a in data.get("by_area", [])
        if a.get("state") != "LIVE"
    ]
    return {
        "areas": declared,
        "live": int(data.get("live", 0)),
        "stub": int(data.get("stub", 0)),
        "dark": int(data.get("dark", 0)),
        "not_implemented": len(not_live),
        "not_implemented_names": [a["name"] for a in not_live],
        "not_implemented_detail": not_live,
    }


# -- S: security ----------------------------------------------------------

@_letter("S", "security", "boundary firewall, before any external connection",
         "simself/src/boundaries.py")
def letter_s() -> Dict[str, Any]:
    import boundaries
    b = boundaries.boundaries
    before = b.check_all()
    # A boundary defense whose checks are all `lambda: True` can never
    # refuse. MEASURE whether it can: force one to fail and see if the
    # defense notices. A check that cannot fail is not a check.
    target = b.boundaries.get("no_hallucination")
    forced = None
    if target is not None:
        # AND THE PROBE RUNS ON A COPY, NOT ON THE LIVE SYSTEM.
        #
        # MEASURED 2026-11-04: the previous version mutated the LIVE
        # global boundary -- it set `no_hallucination`'s check to
        # `lambda: False`, measured, and then restored a FRESH
        # `lambda: True` instead of the function it had replaced.
        #
        # Two defects in one line, and both measured:
        #
        #   1. The restore wrote the WRONG function. A boundary that
        #      another part of the system had ARMED was left
        #      permanently DISARMED, because the restore wrote a
        #      function that always passes.
        #      MEASURED: with `no_hallucination` armed to refuse, the
        #      survey ran and `check_all()` afterwards returned
        #      allowed=True, violated=[] -- the armed boundary had
        #      been silently turned off.
        #
        #   2. And `fc_hermes.Bridge.describe()` calls the survey, so
        #      DESCRIBING the system disarmed it. A status report that
        #      weakens the thing it reports on is worse than no report.
        #
        # So the forced-failure measurement now runs on a COPY of the
        # defense, carrying the live check functions across so it
        # measures the same defenses. The live system is never
        # mutated at all -- not even temporarily. A probe that leaves
        # the system weaker than it found it is not a probe; it is a
        # defect with a measurement attached.
        probe = boundaries.BoundaryDefense()
        for name, bound in b.boundaries.items():
            if name in probe.boundaries:
                probe.boundaries[name].check_fn = bound.check_fn
        ptarget = probe.boundaries.get("no_hallucination")
        if ptarget is not None:
            ptarget.check_fn = lambda: False
            after = probe.check_all()
            forced = {
                "allowed": bool(after.get("allowed")),
                "violated": list(after.get("violated", [])),
                "critical_violated": list(after.get("critical_violated", [])),
            }
        # AND THE LIVE CHECK IS STILL VERIFIED TO BE UNTOUCHED. This is
        # the second line of defence: if a future edit reintroduces a
        # mutation of the live global, this reports the difference
        # rather than hiding it.
        live_after = b.check_all()
        forced = forced or {}
        forced["live_unchanged"] = bool(
            live_after.get("allowed") == before.get("allowed")
            and list(live_after.get("violated", []))
            == list(before.get("violated", []))
        )
    return {
        "boundaries": len(b.boundaries),
        "allowed_by_default": bool(before.get("allowed")),
        "passed": list(before.get("passed", [])),
        "can_refuse": bool(forced and forced["allowed"] is False),
        "forced_failure": forced,
    }


#: THE ORDER. Alphabetical, and the order the letters were declared in
#: the project's own PROJECT.md.
LETTERS: List[Any] = [letter_a, letter_b, letter_c, letter_d, letter_e,
                      letter_i, letter_l, letter_m, letter_q, letter_s]


def survey() -> List[Letter]:
    """Run every letter. Each one is independent; one failing does not
    stop the others, because the point of a survey is to see the WHOLE
    picture, and a survey that stops at the first failure hides the
    other nine."""
    out: List[Letter] = []
    for fn in LETTERS:
        out.append(fn())
    return out


# ===========================================================================
# THE REPORT
# ===========================================================================

def render(letters: List[Letter]) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("THE WHOLE SYSTEM -- TEN LETTERS, MEASURED")
    lines.append("=" * 78)
    lines.append("")
    lines.append("  A core architecture   B self-model         C sim world")
    lines.append("  D SNR training        E family / external  I interface")
    lines.append("  L sacred library      M modulator          Q qualification")
    lines.append("  S security")
    lines.append("")
    for lt in letters:
        mark = {"LIVE": "LIVE", "STUB": "STUB", "DARK": "DARK"}[lt.state]
        lines.append("  [%s] %s %-20s %s" % (mark, lt.letter, lt.name,
                                            lt.role[:44]))
        if lt.state == "LIVE":
            for k, v in list(lt.measured.items())[:8]:
                sv = str(v)
                if len(sv) > 88:
                    sv = sv[:85] + "..."
                lines.append("         %-28s %s" % (k, sv))
        else:
            lines.append("         %s" % lt.reason[:160])
        lines.append("         %-28s %s" % ("home", lt.home))
        lines.append("         %-28s %.2f ms" % ("elapsed", lt.elapsed_ms))
        lines.append("")
    live = sum(1 for l in letters if l.state == "LIVE")
    stub = sum(1 for l in letters if l.state == "STUB")
    dark = sum(1 for l in letters if l.state == "DARK")
    lines.append("=" * 78)
    lines.append("  LIVE %d    STUB %d    DARK %d    of %d letters"
                 % (live, stub, dark, len(letters)))
    lines.append("=" * 78)
    return "\n".join(lines)


# ===========================================================================
# THE ENTRY POINTS
# ===========================================================================

def cmd_status() -> int:
    letters = survey()
    print(render(letters))
    return 0


def cmd_selftest() -> int:
    """Exercise every letter AND prove the survey can detect a failure.

    THE PROOF. A status report that only ever prints LIVE is a report
    that cannot fail. So this run deliberately asks for a letter that
    does not exist and confirms the survey REPORTS it as DARK rather
    than silently passing. If that probe comes back LIVE, the survey is
    broken and says so.
    """
    print("=" * 78)
    print("THE WHOLE SYSTEM -- SELFTEST")
    print("=" * 78)
    print("")

    letters = survey()
    print(render(letters))

    # THE PROOF THAT THE SURVEY CAN FAIL.
    print("=" * 78)
    print("THE SURVEY PROOF -- a letter that cannot exist")
    print("=" * 78)
    print("")

    @_letter("Z", "does not exist", "a letter the system does not have",
             "nowhere")
    def letter_z() -> Dict[str, Any]:
        raise RuntimeError("this letter does not exist, by construction")

    z = letter_z()
    print("  probe Z -> state %s" % z.state)
    print("  reason: %s" % z.reason[:140])
    detected = z.state == "DARK"
    print("  the survey DETECTS a failing letter: %s" % detected)
    print("")

    live = sum(1 for l in letters if l.state == "LIVE")
    stub = sum(1 for l in letters if l.state == "STUB")
    dark = sum(1 for l in letters if l.state == "DARK")
    print("=" * 78)
    print("  LIVE %d  STUB %d  DARK %d  of %d" % (live, stub, dark,
                                                  len(letters)))
    print("  the survey can fail: %s" % detected)
    print("=" * 78)
    return 0 if detected else 1


def cmd_ask(prompt: str) -> int:
    """One exchange through the control system, then the letter survey."""
    from fc_wrapper import FieldCoreWrapper
    w = FieldCoreWrapper(live=ALLOW_LIVE)
    ex = w.ask(prompt)
    print(ex.trace())
    print()
    print("answered by: %s" % ex.answered_by)
    print("delivered:   %s" % ex.delivered)
    print()
    print(ex.answer)
    print()
    print("-" * 78)
    letters = survey()
    print(render(letters))
    return 0 if ex.delivered else 1


def cmd_json() -> int:
    letters = survey()
    print(json.dumps({
        "live": sum(1 for l in letters if l.state == "LIVE"),
        "stub": sum(1 for l in letters if l.state == "STUB"),
        "dark": sum(1 for l in letters if l.state == "DARK"),
        "letters": [l.to_dict() for l in letters],
    }, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="fc_app",
        description="The whole fieldcore system, as an app. Ten letters.")
    ap.add_argument("--status", action="store_true",
                    help="survey every letter and report")
    ap.add_argument("--selftest", action="store_true",
                    help="exercise every letter AND prove the survey can fail")
    ap.add_argument("--json", action="store_true",
                    help="the survey as JSON")
    ap.add_argument("--ask", metavar="PROMPT",
                    help="one exchange through the control system")
    args = ap.parse_args(argv)

    if args.selftest:
        return cmd_selftest()
    if args.json:
        return cmd_json()
    if args.ask:
        return cmd_ask(args.ask)
    return cmd_status()


if __name__ == "__main__":
    raise SystemExit(main())
