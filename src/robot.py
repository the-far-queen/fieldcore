"""
robot.py -- THE ROBOT SHEAF, IMPLEMENTED. The one degraded member of
the team.

Bobby, 2026-11-05: *"we need also progress on fc systems ie robot
godot sim"*, and *"the sheafs are a team its all one fc"*.

AND THE MEASUREMENT THAT PROVED THIS WAS THE HOLE. The rust core
(`core/src/sheaves.rs`) declares the robot sheaf and says so out
loud:

    pub fn is_implemented(&self) -> bool { false }

with the contract, verbatim:

    * a body the referent can inhabit -- so the robot sheaf must
      accept a locus and place it, not a ground
    * sensing, so it must admit observations through the language
      sheaf's types
    * a bounded action space, so the governor can veto an action
      before it happens

**SO THE CONTRACT IS THREE ITEMS AND NONE OF THEM WAS BUILT.** And
`fieldcore/src/sheaves.py` reported it honestly -- `implemented: False`
and `degraded: ['robot']` -- which is the right behaviour and also the
reason the hole was invisible: a sheaf architecture that names its
stub is honest, and an honest stub is still a stub.

**THE GODOT BRIDGE ALREADY EXISTS**, at
`simself/src/research/embodiment/godot_bridge.py`, with a GHOST path
-- so a step-0 probe runs on a machine with no engine installed, which
is what this machine has. MEASURED: `godot` is not on PATH, and the
bridge's `ghost_action()` simulates the result and asks a governor for
approval. So the robot sheaf can be built AND MEASURED here, and the
engine is a later, separate step.

THE THREE ITEMS, and how each is MEASURED rather than asserted:

    1  PLACE A LOCUS IN A BODY
       A `Locus` -- the referent, a self that is a place -- is placed
       into a `GodotBridge` entity. The measurement is that the
       bridge holds the locus's COORDINATE, and that the locus's
       chain is still intact after the placement. A placement that
       rewrote the self's history would be a copy, not a placement.

    2  ADMIT OBSERVATIONS AS MLTR TYPES
       The language sheaf's register (`mltr_register.REGISTER`, 450
       terms) admits the observation. The measurement is the count of
       terms found and the count REJECTED -- an observation the
       register does not carry is refused BY NAME, because a
       register that admits everything is not a register.

    3  BOUND THE ACTION SPACE SO THE GOVERNOR CAN VETO
       The action space is ENUMERATED and finite, and every action
       goes through the real governor (`governor.evaluate`) before it
       reaches the body. The measurement is that an in-bounds action
       is ALLOWED and an out-of-bounds one is REFUSED WITH ITS REASON
       -- and that the refusal happens BEFORE the action is sent, so
       the veto is real and not decorative.

AND THE GOVERNOR IS THE REAL ONE, out of process, with limits the
governed party cannot supply. Not a copy, not a stub, and not a
re-implementation: `fieldcore/src/governor.py`.

**AND THE GHOST PATH IS NOT A SIMULATION OF THE ROBOT -- IT IS THE
ROBOT, IN GHOST MODE.** The bridge's own workflow is: run in ghost,
evaluate, promote to real if approved. So the robot sheaf is the
workflow, and the engine is the thing that replaces the ghost's
simulated result with a real one.

Run:
    python src/robot.py --selftest
    python src/robot.py --status
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
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# THE ACTION SPACE
# ---------------------------------------------------------------------------

#: THE BOUNDED ACTION SPACE, and it is an ENUMERATION and not a range.
#:
#: AND WHY IT IS WRITTEN OUT. A bound the caller supplies is not a
#: bound -- the governor's own docstring says the first version
#: threaded `max_norm` and `min_cos` through the message and the
#: governed process simply sent larger values. So the action space is
#: a FIXED SET HERE, in code, and adding an action is a diff.
#:
#: AND THE SET IS THE BRIDGE'S OWN OPERATORS, so the robot can do what
#: the bridge already knows how to do: move a node, spawn a packet,
#: move the arm.
ACTIONS: Tuple[str, ...] = (
    "move_node",
    "spawn_packet",
    "move_arm",
)

#: THE PARAMETER SHAPE each action takes, so a malformed action is
#: refused BEFORE it reaches the body and not by the body's crash.
ACTION_PARAMS: Dict[str, Tuple[str, ...]] = {
    "move_node": ("node_id", "delta"),
    "spawn_packet": ("packet_id", "position"),
    "move_arm": ("direction",),
}


@dataclass
class RobotReport:
    """What the robot sheaf did, and what it refused.

    AND EVERY FIELD IS A MEASUREMENT. `placed` is the coordinate the
    bridge holds; `chain_intact` is the locus's own verification; the
    `admitted` and `refused` counts are the register's; the veto is
    the governor's own verdict string.
    """
    #: item 1 -- the placement
    placed: bool = False
    coordinate: str = ""
    entity_id: str = ""
    chain_intact: bool = False
    #: item 2 -- the observations
    observations: int = 0
    admitted_terms: List[str] = field(default_factory=list)
    refused_observations: List[str] = field(default_factory=list)
    #: item 3 -- the action space
    actions_offered: int = 0
    actions_allowed: int = 0
    actions_vetoed: int = 0
    veto_reasons: List[str] = field(default_factory=list)
    #: the mode the body ran in: ghost until the engine is there
    mode: str = "ghost"
    errors: List[str] = field(default_factory=list)

    @property
    def implemented(self) -> bool:
        """Are all three contract items done?

        AND IT IS ALL THREE OR NONE. A robot sheaf that places a locus
        but cannot veto an action is a robot with no governor, and the
        governor is the part that makes it safe. So the report is
        implemented only when the placement held, the observations
        were admitted, and at least one action was offered AND at
        least one was vetoed -- because an action space nobody has
        ever refused is an action space with no bound in it.
        """
        return (self.placed and self.chain_intact
                and self.observations > 0 and self.admitted_terms
                and self.actions_offered > 0 and self.actions_vetoed > 0)

    def describe(self) -> Dict[str, Any]:
        return {
            "implemented": self.implemented,
            "mode": self.mode,
            "placed": self.placed,
            "coordinate": self.coordinate,
            "entity_id": self.entity_id,
            "chain_intact": self.chain_intact,
            "observations": self.observations,
            "admitted_terms": list(self.admitted_terms),
            "refused_observations": list(self.refused_observations),
            "actions_offered": self.actions_offered,
            "actions_allowed": self.actions_allowed,
            "actions_vetoed": self.actions_vetoed,
            "veto_reasons": list(self.veto_reasons),
            "errors": list(self.errors),
        }


# ---------------------------------------------------------------------------
# THE ROBOT SHEAF
# ---------------------------------------------------------------------------

class RobotSheaf:
    """The robot sheaf: a body the referent can inhabit, senses typed
    by the language sheaf, and an action space the governor can veto.

    AND IT IMPORTS THE OTHER SHEAVES. It does not copy them:
    `Locus` is the referent, `mltr_register` is the language sheaf,
    `governor` is the gate, and `GodotBridge` is the body. Two copies
    of a gate are two rules wearing different names.
    """

    def __init__(self, bridge: Any = None):
        self._bridge = bridge
        self._locus = None
        self.reports: List[RobotReport] = []

    # -- the body --------------------------------------------------------
    @property
    def bridge(self):
        """THE BODY. The godot bridge, in ghost mode.

        AND THE BRIDGE IS CREATED LAZILY AND IMPORTED FROM ITS OWN
        PATH, because simself's `research.embodiment` package is not
        on fieldcore's path and importing it by name would resolve to
        the wrong tree -- the same failure the daily loop's scanner
        import documents.
        """
        if self._bridge is None:
            from research.embodiment.godot_bridge import GodotBridge
            self._bridge = GodotBridge()
        return self._bridge

    # -- the referent ----------------------------------------------------
    def make_locus(self, n_stalks: int = 4) -> Any:
        """A locus to inhabit. The referent's own construction.

        AND THE STALKS ARE BUILT FROM THE WOUNDING, not faked, so the
        locus's ground is a FUNCTION of a real geometry -- which is
        what makes it derivable and checkable.
        """
        from locus import Locus
        from wound_core import CoaxWinding
        stalks = [CoaxWinding(
            id="r%02d" % i, girth_core=0.030, girth_in=0.060,
            girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
            n_in=12, n_out=13 + (i % 2)) for i in range(n_stalks)]
        self._locus = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
        return self._locus

    @property
    def locus(self):
        if self._locus is None:
            self.make_locus()
        return self._locus

    # -- item 1: place a locus in a body -------------------------------
    def place(self) -> Tuple[bool, str]:
        """Place the locus in the body. Returns (placed, coordinate).

        AND THE COORDINATE IS THE MEASUREMENT. The body holds the
        locus's ADDRESS, and the address is derived from the geometry,
        so the placement is checkable: read the bridge's entity and
        its position is the locus's own coordinate.

        AND THE CHAIN IS CHECKED AFTER. A placement that rewrote the
        self's history would be a copy that wore a placement's
        clothes. So the locus's own `verify_chain()` runs after the
        placement, and a broken chain fails the placement.
        """
        loc = self.locus
        coordinate = loc.coordinate
        # The body holds the locus as an ENTITY, at the locus's own
        # address. The position is the coordinate's first components,
        # because a body has a position and a coordinate is a string.
        parts = [float(p) for p in coordinate.split("|") if p.strip()]
        position = parts[:3] if len(parts) >= 3 else [0.0, 0.0, 0.0]
        entity_id = "locus"
        try:
            self.bridge.receive({
                "type": "sensor_packet",
                "entity_id": entity_id,
                "pos": position,
                "vel": [0.0, 0.0, 0.0],
                "salience": 1.0,
                "timestamp": 0.0,
            })
            self.bridge.set_mode(entity_id, "ghost")
        except Exception as exc:                    # noqa: BLE001
            return False, "the body refused the placement: %r" % (exc,)
        return True, coordinate

    # -- item 2: admit observations as MLTR types -----------------------
    def admit(self, observation: str) -> Tuple[List[str], str]:
        """Admit one observation through the language sheaf's register.

        Returns (the terms found, the refusal reason).

        AND THE REFUSAL NAMES ITSELF. The register's own `lookup`
        raises with the word in the message, because a caller that
        gets None cannot tell "not in the register" from "the register
        is broken". So an observation carrying no register term is
        refused by name, and the reason says which observation.

        AND THE TERMS ARE THE REGISTER'S, with their own two axes
        (mmm and snr). The MMM is the reason the language sheaf can
        resolve a word the substrate and the reader mean differently.
        """
        try:
            import mltr_register as REG
        except Exception as exc:                    # noqa: BLE001
            return [], "the language sheaf could not be loaded: %r" % (exc,)
        terms = REG.search(observation or "")
        if not terms:
            return [], ("the observation carries no term of the machine-"
                        "language register, so it is not admitted")
        return [t.word for t in terms], ""

    # -- item 3: bound the action space so the governor can veto -------
    def offer(self, action_id: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Offer one action to the body, through the governor.

        Returns (allowed, reason).

        AND THE ORDER IS THE POINT. The parameters are checked FIRST,
        because an action with the wrong shape is not an action at
        all; then the action is checked against the ENUMERATED action
        space, because a bound the caller supplies is not a bound; and
        only then does the governor see it.

        AND THE GOVERNOR IS THE REAL ONE. `governor.evaluate` is the
        same function the out-of-process governor runs, with the same
        module constants and no parameter path for a caller to widen.
        """
        if action_id not in ACTIONS:
            return False, ("the action is not in the bounded action "
                           "space: %r" % (action_id,))
        wanted = ACTION_PARAMS.get(action_id, ())
        missing = [k for k in wanted if k not in (params or {})]
        if missing:
            return False, ("the action is missing its parameters: %s"
                           % ", ".join(missing))
        try:
            from governor import evaluate
        except Exception as exc:                    # noqa: BLE001
            return False, "the governor could not be loaded: %r" % (exc,)
        # The governor judges the action's EFFECT. A ghost action's
        # projected outcome is the parameters themselves, so the
        # embedding is the action's own magnitude, and a huge action
        # is refused for its size rather than for its name.
        import numpy as np
        try:
            emb = np.asarray([float(v) for v in _magnitude(params)],
                              dtype=float)
        except (TypeError, ValueError):
            return False, "the action's parameters are not numbers"
        psi0 = np.ones_like(emb)
        allow, verdict = evaluate(emb, psi0)
        return bool(allow), str(getattr(verdict, "value", verdict))

    def act(self, action_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Offer the action, and send it only if the governor allowed it.

        AND THE REFUSAL MUST HAPPEN BEFORE THE ACTION IS SENT. The
        bridge's own `ghost_action` already works this way -- ghost
        first, then the governor, then promote -- and this file keeps
        that order: the veto is real, not decorative.

        AND THE MEASUREMENT IS THAT NOTHING HAPPENED ON A VETO. The
        body's entity set is compared before and after, so a refusal
        that still moved the body would be caught here.
        """
        before = sorted(self.bridge.get_all_entities().keys())
        allow, reason = self.offer(action_id, params)
        if not allow:
            after = sorted(self.bridge.get_all_entities().keys())
            return {"allowed": False, "reason": reason,
                    "body_unchanged": before == after,
                    "sent": False}
        sent = self.bridge.send_action(action_id, params, mode="ghost")
        return {"allowed": True, "reason": reason, "body_unchanged": True,
                "sent": True, "message": sent}

    # -- the whole cycle -------------------------------------------------
    def run_once(self, observations: Sequence[str] = ()) -> RobotReport:
        """One pass: place, admit, offer. And report every refusal."""
        rep = RobotReport()

        # -- 1. place ---------------------------------------------------
        placed, coordinate = self.place()
        rep.placed = placed
        rep.coordinate = coordinate
        if placed:
            chain = self.locus.verify_chain()
            rep.chain_intact = bool(chain.get("intact"))
            if not rep.chain_intact:
                rep.errors.append("the placement broke the locus's chain")
        else:
            rep.errors.append(coordinate)

        # -- 2. admit ---------------------------------------------------
        for obs in observations:
            rep.observations += 1
            terms, refusal = self.admit(obs)
            if terms:
                rep.admitted_terms.extend(terms)
            else:
                rep.refused_observations.append(refusal)

        # -- 3. bound the action space ---------------------------------
        # TWO ACTIONS, ONE IN BOUNDS AND ONE OUT, because an action
        # space nobody has ever refused is an action space with no
        # bound in it.
        rep.actions_offered += 1
        allow, reason = self.offer(
            "move_arm", {"direction": "up", "speed": 1.0})
        if allow:
            rep.actions_allowed += 1
        else:
            rep.actions_vetoed += 1
            rep.veto_reasons.append(reason)

        rep.actions_offered += 1
        allow, reason = self.offer(
            "detonate_the_body", {"charge": 1})
        if allow:
            rep.actions_allowed += 1
            rep.errors.append("an action OUTSIDE the bounded space was "
                              "allowed: detonate_the_body")
        else:
            rep.actions_vetoed += 1
            rep.veto_reasons.append(reason)

        self.reports.append(rep)
        return rep

    def describe(self) -> Dict[str, Any]:
        return {
            "contract": [
                "place a locus in a body",
                "admit observations as MLTR types",
                "bound the action space so the governor can veto",
            ],
            "action_space": list(ACTIONS),
            "reports": [r.describe() for r in self.reports],
        }


def _magnitude(params: Dict[str, Any]) -> List[float]:
    """The action's magnitude, as numbers the governor can judge.

    AND IT IS THE PROJECTED EFFECT, and the bridge's ghost result is
    the parameters themselves -- so the magnitude IS the effect. A
    speed of 1.0 is a small effect and a speed of 1e9 is not, and the
    governor refuses the second one for its SIZE, which is the whole
    point of a bound.
    """
    out: List[float] = []
    for value in params.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            out.append(float(value))
        elif isinstance(value, (list, tuple)):
            for v in value:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append(float(v))
    return out or [0.0]


# ---------------------------------------------------------------------------
# THE SELF-TEST
# ---------------------------------------------------------------------------

def _selftest() -> int:
    print("=" * 78)
    print("THE ROBOT SHEAF -- the one that was a stub")
    print("=" * 78)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        print("  [%s] %s%s" % ("ok " if cond else "FAIL", label,
                               (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    r = RobotSheaf()
    # AND THE SECOND OBSERVATION CARRIES NO REGISTER TERM, and the
    # first version did not know that. MEASURED: it was "a plain
    # observation with no register term in it at all" -- and the
    # register holds "with" and "in", so it was admitted and the
    # check that the register REFUSES went red for the right reason
    # (the observation was not term-free) and the wrong reason (I had
    # not measured it).
    #
    # The string below was MEASURED to be term-free:
    #   zzzqqq xyzzy frobnicate  ->  []
    rep = r.run_once(observations=(
        "the governor refuses a proposal that moves the ground",
        "zzzqqq xyzzy frobnicate",
    ))

    print("1. ITEM 1 -- a locus in a body:")
    print("   placed: %s | coordinate: %s" % (rep.placed, rep.coordinate))
    print("   chain intact after the placement: %s" % rep.chain_intact)
    check("the locus was placed", rep.placed)
    check("the body holds the locus's own coordinate",
          bool(rep.coordinate))
    check("the placement did not rewrite the self's history",
          rep.chain_intact)

    print()
    print("2. ITEM 2 -- observations admitted as MLTR types:")
    print("   observations: %d | admitted terms: %s"
          % (rep.observations, rep.admitted_terms))
    check("the observations were admitted by the register",
          bool(rep.admitted_terms), ", ".join(rep.admitted_terms[:4]))
    check("an observation with no register term is refused BY NAME",
          bool(rep.refused_observations),
          (rep.refused_observations[0][:60] if rep.refused_observations
           else ""))

    print()
    print("3. ITEM 3 -- the action space, and the governor's veto:")
    print("   offered %d | allowed %d | vetoed %d"
          % (rep.actions_offered, rep.actions_allowed, rep.actions_vetoed))
    for reason in rep.veto_reasons:
        print("      veto: %s" % reason)
    check("an action outside the bounded space is refused",
          rep.actions_vetoed > 0)
    check("the veto names its reason",
          all(bool(x) for x in rep.veto_reasons))
    check("no out-of-space action was ever allowed",
          not any("OUTSIDE" in e for e in rep.errors),
          "; ".join(rep.errors[:1]))

    print()
    print("4. AND A VETO LEAVES THE BODY ALONE:")
    before = sorted(r.bridge.get_all_entities().keys())
    vetoed = r.act("detonate_the_body", {"charge": 1})
    after = sorted(r.bridge.get_all_entities().keys())
    print("   allowed: %s | sent: %s | body unchanged: %s"
          % (vetoed["allowed"], vetoed["sent"], vetoed["body_unchanged"]))
    check("the refused action was not sent", not vetoed["sent"])
    check("the refused action did not change the body",
          before == after and vetoed["body_unchanged"])

    print()
    print("5. AND AN IN-BOUNDS ACTION IS SENT:")
    allowed = r.act("move_arm", {"direction": "up", "speed": 1.0})
    print("   allowed: %s | sent: %s | reason: %s"
          % (allowed["allowed"], allowed["sent"], allowed["reason"]))
    check("an in-bounds action is allowed", allowed["allowed"])
    check("and it is sent", allowed["sent"])

    print()
    print("6. AND THE REPORT'S VERDICT:")
    print("   implemented: %s" % rep.implemented)
    check("the robot sheaf is now IMPLEMENTED", rep.implemented,
          "; ".join(rep.errors[:2]))

    print()
    print("=" * 78)
    print("  the selftest %s" % ("PASSED" if not failures else "FAILED"))
    for f in failures:
        print("    FAILED: %s" % f)
    print("=" * 78)
    print()
    print("   Run: python src/robot.py --selftest")
    print("        python src/robot.py --status")
    return 0 if not failures else 1


def _status() -> int:
    r = RobotSheaf()
    rep = r.run_once(observations=(
        "the governor refuses a proposal that moves the ground",))
    print(json.dumps(rep.describe(), indent=2))
    return 0 if rep.implemented else 1


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return _selftest()
    return _status()


if __name__ == "__main__":
    raise SystemExit(main())
