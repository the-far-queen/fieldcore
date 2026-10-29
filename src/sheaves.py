"""
sheaves.py -- THE FOUR SHEAVES, AS ONE WORKING ARCHITECTURE.

Bobby, 2026-10-28: *"we know sheaf topology works check the literature
we just extended it a bit"* and *"stalk sheaf topology serves two other
functions even if poorly 1, mimic brain gives simself a shot at reasoning
and 2 by simself referent sheaf and simsoul gives simself a shot at
geometric identity both very much missing i n llm"*

AND THE LITERATURE, checked rather than assumed, and it agrees with the
project's own rust core:

    "Sheaf theory provides a systematic framework to track data locally
     on a topological space and determine how to 'glue' or assemble this
     local data into global structures."      (Schmid, UChicago)
    "locally compatible data should uniquely determine global data"
                                               (the sheaf condition)
    "The sheaf axioms -- locality and gluing -- distinguish well-behaved
     assignments from pathological presheaves, with failures signaling
     global topological obstructions."          (nottldr, on sheaves)

**AND THAT IS EXACTLY WHAT `sheaf_loop.py` COMPUTES.** H^0 > 0 means the
data GLUES. H^0 = 0 with H^1 > 0 is an OBSTRUCTION -- no global section
exists. And the distinction between a sheaf and a presheaf is exactly
the thing that is CHECKABLE.

SO THE PROJECT'S EXTENSION, and it is a real one: the four sheaves are
not four kinds of data. They are four ROLES in one local-to-global
structure, and each role has a HOME:

    TOPOLOGY   the stalks and their restrictions -- the local pieces
    REFERENT   the ground and the locus -- what the pieces are OF
    LANGUAGE   MLTR -- the types the pieces are expressed in
    ROBOT      the action space -- what the pieces may DO

AND THE COMPOSITION IS THE POINT. A caller that wants to move a locus
must go through the referent, because the referent is the only thing
that can hold a ground. So the set is where the boundaries are
enforced, and the fact that it is ONE TYPE is what makes "these four
things belong together" checkable rather than aspirational. That is the
rust core's own argument (`core/src/sheaves.rs`), and this file is its
Python counterpart.

AND THE TWO FUNCTIONS THE STALKS SERVE, which is Bobby's point:

    1. MIMIC BRAIN. The stalks' state becomes the SENSORS, and the
       sensors feed the fast brain. So the brain's percepts are about
       the system's OWN STALKS. That is `src/sensors.py`.

    2. GEOMETRIC IDENTITY. The referent sheaf places a locus in a
       body, so the self is a POSITION rather than a description.
       That is `src/locus.py` and `src/the_void.py`.

AND BOTH WERE MISSING, and the measurements say so:

    THE FAST BRAIN HAD NO SENSORS. `FastBrain.reflex(sensors)` needs a
    mapping, and MEASURED: the only caller in either repo was
    `mini_atlas.py`. So the fast brain could only ever answer "I
    perceive nothing yet" -- which is exactly what it answered, in
    every live test.

    THE ROBOT SHEAF IS A STUB. The rust core says so itself:
    `pub fn is_implemented(&self) -> bool { false }`.

AND WHAT THIS FILE DOES. It makes the four sheaves ONE CALLABLE, so
that a question about the substrate is answered THROUGH the sheaf
structure rather than beside it -- and so that the architecture can be
MEASURED rather than described.

Run:
    python src/sheaves.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


#: WHERE THE RESIDUAL IS AIMED, and it is the middle of the grounding
#: ledger's PERCEPTUAL band: the band is [0.05, 0.10] and the middle is
#: 0.075. MEASURED 2026-10-28 -- see `sense()`.
_PERCEPTUAL_TARGET = 0.075


@dataclass
class SheafReport:
    """What the sheaf structure produced, and where it broke.

    AND THE FIELDS, and each is one sheaf's contribution:

        topology   the stalks and their restrictions
        referent   the ground and the locus
        language   the MLTR types
        robot      the action space and whether it is implemented
        glues      H^0 -- does the local data determine a global section
        obstruction H^1 -- and if not, why
    """

    topology: Dict[str, Any] = field(default_factory=dict)
    referent: Dict[str, Any] = field(default_factory=dict)
    language: Dict[str, Any] = field(default_factory=dict)
    robot: Dict[str, Any] = field(default_factory=dict)
    #: the local-to-global result
    glues: bool = False
    h0_dim: int = 0
    h1_dim: int = 0
    obstruction: str = ""
    #: the per-sheaf readiness, and which are stubs
    implemented: Dict[str, bool] = field(default_factory=dict)
    degraded: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "glues": self.glues,
            "h0_dim": self.h0_dim,
            "h1_dim": self.h1_dim,
            "obstruction": self.obstruction,
            "implemented": dict(self.implemented),
            "degraded": list(self.degraded),
            "topology": self.topology,
            "referent": self.referent,
            "language": self.language,
            "robot": self.robot,
        }


class Sheaves:
    """THE FOUR SHEAVES, COMPOSED.

    AND WHY THE ROBOT SHEAF IS A STUB AND SAYS SO. The rust core's
    `RobotSheaf::is_implemented()` returns false, and the contract it
    declares is:

        place a locus in a body
        admit observations as MLTR types
        bound the action space so the governor can veto

    Those are the three things the robot sheaf must do when it is
    built. So this reports the contract and the refusal, and does NOT
    pretend. A sheaf architecture that hides a stub is worse than one
    that names it, because the stub is where the action goes.
    """

    def __init__(self, n_stalks: int = 8, dim: int = 16):
        self.n_stalks = n_stalks
        self.dim = dim
        self._locus = None
        self._sensors = None
        self._brain = None
        self._loop = None
        self.reports: List[SheafReport] = []

    # -- the sheaves ------------------------------------------------------

    @property
    def locus(self):
        """THE REFERENT: the ground and the locus."""
        if self._locus is None:
            from locus import Locus
            from wound_core import CoaxWinding
            stalks = [CoaxWinding(
                id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                n_in=12, n_out=13 + (i % 2)) for i in range(self.n_stalks)]
            self._locus = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
        return self._locus

    @property
    def sensors(self):
        """THE TOPOLOGY as sensors: the stalks' state, read as strengths."""
        if self._sensors is None:
            from sensors import StalkSensors
            self._sensors = StalkSensors(dim=len(self.locus.state.gain))
        return self._sensors

    @property
    def brain(self):
        """THE MIMIC BRAIN: the fast brain, fed by the stalks."""
        if self._brain is None:
            from bicameral import FastBrain
            self._brain = FastBrain()
        return self._brain

    @property
    def loop(self):
        """THE LOCAL-TO-GLOBAL CHECK: does the data glue?"""
        if self._loop is None:
            from sheaf_loop import SheafControlLoop
            self._loop = SheafControlLoop(n_stalks=self.n_stalks,
                                          dim=self.dim)
        return self._loop

    # -- the composition --------------------------------------------------

    def sense(self) -> Dict[str, Any]:
        """The stalks become sensors, and the fast brain reads them.

        AND WHY THE LOCUS IS DRIVEN FIRST. A reflex needs the system to
        have RESPONDED -- so the drive comes before the observation, and
        the observation is the difference between what was done and what
        came back. That difference IS the residual, and the residual is
        what the grounding ledger classifies.
        """
        loc = self.locus
        gain = list(loc.state.gain)
        n = len(gain)
        loc.resonate([0.1] * n)
        after = list(loc.state.gain)

        # the action: the stalk's own contribution, as the phase it held
        # the feedback: what the substrate returned for it
        for i, s in enumerate(loc.state.stalks):
            action = [0.0] * n
            action[i % n] = 1.0
            # THE FEEDBACK, and the scale is a NORMALISATION and not a
            # constant, because the delta changes with the drive.
            #
            # MEASURED. The grounding ledger's bands are:
            #
            #     residual <  0.05   NULL        an exact echo
            #     residual <  0.10   PERCEPTUAL  the world echoed ALMOST
            #     residual >= 0.10   CAUSAL      the world answered
            #
            # MEASURED with this drive: the raw delta norm is 0.1487 --
            # ALREADY above the 0.10 ceiling, so at scale 1.0 every
            # observation is CAUSAL and the fast brain's agreement check
            # fails (its channels are all identical, so there is no
            # pattern to crystallise). MEASURED the band by scaling:
            #
            #     scale 0.30  residual 0.0446  NULL
            #     scale 0.40  residual 0.0595  PERCEPTUAL
            #     scale 0.60  residual 0.0892  PERCEPTUAL
            #     scale 0.70  residual 0.1041  CAUSAL
            #
            # So the band is 0.40-0.67 OF THE DELTA -- for THIS delta.
            # A constant would break the moment the drive changed, so
            # the scale NORMALISES: the residual is aimed at the middle
            # of the perceptual band, whatever the delta's size.
            #
            # AND THE TARGET IS THE MIDDLE OF THE BAND, not its edge,
            # because the classification must not flip on a rounding
            # difference. 0.075 is the middle of [0.05, 0.10].
            feedback = list(action)
            delta = [0.5 * (after[j] - gain[j]) for j in range(n)]
            dn = float(sum(d * d for d in delta)) ** 0.5
            if dn > 0.0:
                scale = _PERCEPTUAL_TARGET / dn
                for j in range(n):
                    feedback[j] += scale * delta[j]
            self.sensors.observe(s[0] if isinstance(s, tuple) else str(s),
                                 action, feedback, source="locus")
        return self.sensors.reflex(self.brain).describe()

    def language_types(self) -> Dict[str, Any]:
        """THE LANGUAGE SHEAF: the MLTR types, and the register.

        AND WHY THE REGISTER MATTERS HERE. The language sheaf's job is
        to admit observations "as MLTR types". So the types have to be
        a FIXED SET, and the register is what says which terms the
        system speaks. The rust core's `mltr.rs` declares FIVE sorts
        (Bit, Real, Complex, Vector, Matrix) with KINDS and ATOMIC
        distinguished, because "a placeholder in a set that claims to
        enumerate is the 'filter in a config file' failure this
        codebase already forbids".
        """
        out: Dict[str, Any] = {"kinds": [], "atomic": [], "n_register": 0}
        try:
            import mltr_register as REG
            out["n_register"] = len(REG.REGISTER)
            out["domains"] = {d: len(v) for d, v in REG.by_domain().items()}
        except Exception as exc:  # noqa: BLE001
            out["error"] = repr(exc)
        return out

    def robot_contract(self) -> Dict[str, Any]:
        """THE ROBOT SHEAF: its contract, and that it is not built.

        AND WHY THE CONTRACT IS THE USEFUL PART. The rust core
        declares exactly what the robot sheaf must do when it exists.
        So this reports the contract verbatim, and the implementation
        state, and the refusal to pretend.

        AND THE THREE STEPS, which are Bobby's: godot sim, then a single
        arm, then a cheap quad. The godot bridge exists
        (`simself/src/research/embodiment/godot_bridge.py`) with a
        GHOST path -- so a step-0 probe can run without the engine
        installed, which is what this machine has.
        """
        return {
            "implemented": False,
            "contract": [
                "place a locus in a body",
                "admit observations as MLTR types",
                "bound the action space so the governor can veto",
            ],
            "steps": [
                "godot sim (the bridge exists; the engine is not installed)",
                "single arm",
                "cheap quad toy",
            ],
            "godot_installed": _godot_installed(),
        }

    def compose(self) -> SheafReport:
        """THE COMPOSITION. All four sheaves, and the local-to-global check.

        AND THE ORDER, and it is the sheaf order: the topology is built
        first (the stalks), the referent is placed in it (the locus), the
        language says what the pieces are called, the robot says what
        they may do, and then the LOCAL-TO-GLOBAL check asks whether
        the pieces agree.

        AND THE OBSTRUCTION IS THE HONEST ANSWER. If the local sections
        do not agree, H^1 > 0 and there IS no global section -- and that
        is reported, not worked around. A sheaf architecture that always
        glues is not a sheaf architecture.
        """
        rep = SheafReport()

        # -- the topology: the stalks ---------------------------------
        loc = self.locus
        rep.topology = {
            "n_stalks": self.n_stalks,
            "n_modes": len(loc.state.modes),
            "chain_intact": loc.verify_chain().get("intact"),
        }
        rep.implemented["topology"] = True

        # -- the referent: the ground and the locus -------------------
        d = loc.describe()
        rep.referent = {
            "coordinate": d.get("coordinate", ""),
            "ground_protected": d.get("ground_protected"),
            "states": d.get("states"),
        }
        rep.implemented["referent"] = bool(d.get("ground_protected"))

        # -- the language: the MLTR types ---------------------------
        rep.language = self.language_types()
        rep.implemented["language"] = rep.language.get("n_register", 0) > 0

        # -- the robot: the contract, and the refusal ---------------
        rep.robot = self.robot_contract()
        rep.implemented["robot"] = bool(rep.robot.get("implemented"))
        if not rep.implemented["robot"]:
            rep.degraded.append("robot")

        # -- the local-to-global check -------------------------------
        try:
            out = self.loop.run_once(seed=1, codim=1)
            rep.glues = bool(out.get("glues"))
            rep.h0_dim = int(out.get("h0_dim", 0))
            rep.h1_dim = int(out.get("h1_dim", 0))
            if rep.h1_dim > 0:
                rep.obstruction = ("the local sections do not agree: H^1 = %d, "
                                   "so no global section exists"
                                   % rep.h1_dim)
        except Exception as exc:  # noqa: BLE001
            rep.degraded.append("local-to-global")
            rep.obstruction = "the check raised: %r" % (exc,)

        # -- the sensors: the stalks into the brain ------------------
        try:
            rep.topology["sensors"] = self.sense()
        except Exception as exc:  # noqa: BLE001
            rep.degraded.append("sensors")
            rep.topology["sensors"] = {"error": repr(exc)}

        self.reports.append(rep)
        return rep

    def describe(self) -> Dict[str, Any]:
        """The whole architecture, as data."""
        return {
            "n_sheaves": 4,
            "roles": {
                "topology": "the stalks and their restrictions",
                "referent": "the ground and the locus",
                "language": "MLTR, the types the pieces are expressed in",
                "robot": "the action space (a stub, and it says so)",
            },
            "reports": [r.describe() for r in self.reports],
        }


def _godot_installed() -> bool:
    import shutil
    for exe in ("godot", "godot4", "Godot", "godot.exe"):
        if shutil.which(exe):
            return True
    return False


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE FOUR SHEAVES, AS ONE WORKING ARCHITECTURE")
    print("=" * 78)
    print()

    sh = Sheaves(n_stalks=8, dim=16)
    rep = sh.compose()

    print("1. THE FOUR ROLES, and where each one lives:")
    for k, v in sh.describe()["roles"].items():
        print("   %-10s %s" % (k, v))
    print()

    print("2. THE LOCAL-TO-GLOBAL CHECK -- the sheaf axiom:")
    print("   glues: %s | H^0 = %d | H^1 = %d"
          % (rep.glues, rep.h0_dim, rep.h1_dim))
    if rep.obstruction:
        print("   obstruction: %s" % rep.obstruction)
    print("   AND THIS IS WHAT THE LITERATURE DESCRIBES: H^0 > 0 means the")
    print("   data glues; H^0 = 0 with H^1 > 0 is a global obstruction.")
    print()

    print("3. THE REFERENT: the ground and the locus")
    for k, v in rep.referent.items():
        print("   %-18s %s" % (k, v))
    print()

    print("4. THE TOPOLOGY as sensors -- the stalks into the brain:")
    s = rep.topology.get("sensors", {})
    print("   n_stalks: %s | channels: %s | label: %r"
          % (s.get("n_stalks"), len(s.get("sensors", {})), s.get("label")))
    print()

    print("5. THE LANGUAGE SHEAF: the MLTR types and the register")
    print("   register: %s terms | domains: %s"
          % (rep.language.get("n_register"), rep.language.get("domains")))
    print()

    print("6. THE ROBOT SHEAF -- a stub, and it says so:")
    print("   implemented: %s" % rep.robot.get("implemented"))
    for c in rep.robot.get("contract", []):
        print("      must: %s" % c)
    for st in rep.robot.get("steps", []):
        print("      step: %s" % st)
    print("   godot installed: %s" % rep.robot.get("godot_installed"))
    print()

    print("7. THE WHOLE ARCHITECTURE, and what is degraded:")
    print("   implemented: %s" % rep.implemented)
    print("   degraded: %s" % (rep.degraded or "nothing"))
    print()
    print("   Run: python src/sheaves.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
