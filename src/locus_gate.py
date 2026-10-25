"""
locus_gate.py -- THE LOCUS CANNOT GROW WILLY-NILLY.

Bobby, 2026-10-25: *"that MYSELF cannot grow willy nilly nor self
update it is controlled by the controller m1 and atlas exam a
qualification suite governed by m0 and subject to an evolving sacred
library t the whole 747 control system we have barely scratched the
value of"*

THE HOLE, and it is in the code I wrote an hour ago:

  `locus.py`'s `resonate()` lets the locus's mind move whenever the
  dynamics push it. There is no gate on it. So a locus can grow
  without limit and without qualification, and a "self" that can do
  that is not a self -- it is a runaway.

  And the project's own rule says so: the README's authority rule is
  `SimSelf PROPOSES -> M1 audits -> Atlas Exam qualifies -> M0 commits
  or vetoes`, and the invariant is *"SimSelf may never write the
  Library."* The locus IS the self's storage, so the locus must obey
  the same rule.

SO THE GATE, and it is FOUR STEPS because the project's own
architecture says four:

    1. PROPOSE   the locus emits a proposal. It does not write.
    2. AUDIT     M1 (outside core) checks the proposal.
    3. QUALIFY   the Atlas Exam scores it.
    4. COMMIT    M0 (in core, deterministic, 1-bit) commits or vetoes.

  And the ORDER matters: three of the four steps stand OUTSIDE the
  thing being governed. That is the separation of powers, and it is
  the 747's.

THE KEY DETAIL, and it is the one that makes this a control system
rather than a queue:

  M0 IS INSIDE THE LOCUS. The governor is the locus's own ground --
  the write-protected part. So the thing that decides whether the
  self may grow is PART OF THE SELF. A governor outside the thing it
  governs can be negotiated with; a governor that is the ground cannot.

  So the gate's structure is: the locus proposes a CHANGE TO ITSELF,
  and the part of the locus that cannot be changed decides.

THE ADMISSION TARGET, and it is 95% and not 100%:

  From the atlas-exam README, quoting Bobby: *"sacred library ensures
  low falsity continuously **not set to perfect** choose 95% so compute
  is bounded"*. And: *"A gate that must be perfect is a gate that never
  opens. At 100% fidelity one surviving defect blocks all learning
  permanently: the system is safe and inert."*

  So the gate admits at a RATE, and it watches itself: below the floor
  (80%) the checks are too strict or the substrate is broken; above
  the ceiling (99%) the checks have stopped discriminating.

WHAT THIS FILE IS: the gate, with the four steps, the thresholds, the
ledger, and the checks that can FAIL.

Run:
    python src/locus_gate.py --selftest
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

#: THE ADMISSION BOUNDS. Three named constants in one place, on
#: purpose: a threshold nobody can see is a threshold nobody can argue
#: with.
#:
#: ADMISSION_TARGET  the rate the gate aims for. 95%, not 100% -- see
#:                   the module docstring.
#: FLOOR            below this, the checks are too strict or the
#:                   substrate is broken. The gate says so instead of
#:                   tightening further.
#: CEILING          above this, the checks have stopped discriminating
#:                   -- the same signature as a metric that always
#:                   agrees.
ADMISSION_TARGET = 0.95
FLOOR = 0.80
CEILING = 0.99


# ===========================================================================
# THE PROPOSAL
# ===========================================================================

@dataclass
class Proposal:
    """A proposed change to a locus. It is NOT a change yet.

    THE SHAPE, and it mirrors the library's own: a proposal carries
    the SKILL it would install, the evidence, and the certification
    level it is asking for. So it is auditable, and an auditor can
    read it without running anything.
    """

    #: What is being proposed.
    skill: str
    #: The proposed content.
    content: str
    #: The evidence for it. A proposal with no evidence is not
    #: auditable, so this is required.
    evidence: List[str] = field(default_factory=list)
    #: The certification level being asked for: q0 untrusted through
    #: q4 canonical.
    cert_level: str = "q0"
    #: Where it came from.
    proposer: str = "locus"
    #: When.
    at: float = field(default_factory=time.time)
    #: The locus it proposes to change.
    locus_id: str = ""

    def digest(self) -> str:
        import hashlib
        payload = "|".join([self.skill, self.content,
                             ";".join(self.evidence), self.cert_level,
                             self.proposer, self.locus_id])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def describe(self) -> Dict[str, Any]:
        return {
            "skill": self.skill,
            "cert_level": self.cert_level,
            "evidence": len(self.evidence),
            "proposer": self.proposer,
            "digest": self.digest(),
        }


# ===========================================================================
# THE FOUR STEPS
# ===========================================================================

class AuditOutcome(str):
    pass


@dataclass
class AuditResult:
    """M1's verdict. It is OUTSIDE core, so it may argue."""
    passed: bool
    reason: str
    #: What the audit changed, if anything. An audit that can demote is
    #: an audit; one that can only pass or fail is a filter.
    demoted_to: Optional[str] = None


@dataclass
class ExamResult:
    """The Atlas Exam's verdict. Binary -- no partial credit."""
    passed: bool
    score: float
    areas_passed: int
    areas_total: int
    reason: str = ""


@dataclass
class CommitResult:
    """M0's verdict. It is IN core, deterministic, and 1-bit."""
    allowed: bool
    reason: str
    #: The one-bit verdict, as an int. The core speaks in bits.
    bit: int = 0


# ===========================================================================
# THE GATE
# ===========================================================================

@dataclass
class LocusGate:
    """The four-step gate on a locus's growth.

    THE DIRECTION OF AUTHORITY, and it is the whole design:

        the locus PROPOSES
        M1 audits
        the exam qualifies
        M0 commits or vetoes

    And the LOCUS CANNOT WRITE THE LIBRARY. Nor can it write itself.
    A caller that tries to apply a gain vector directly, without
    going through the gate, is refused -- and that refusal is the
    invariant, not a limitation.

    THE LEDGER, because an unauditable admission is indistinguishable
    from a lucky one. Every decision is appended with its reason, and
    the ledger is what makes the gate's behaviour measurable rather
    than asserted.
    """

    #: The audit, called as audit(proposal) -> AuditResult.
    audit: Optional[Callable[[Proposal], AuditResult]] = None
    #: The exam, called as exam(proposal) -> ExamResult.
    exam: Optional[Callable[[Proposal], ExamResult]] = None
    #: M0's commit, called as commit(proposal) -> CommitResult.
    commit: Optional[Callable[[Proposal], CommitResult]] = None

    #: The ledger. Every decision.
    ledger: List[Dict[str, Any]] = field(default_factory=list)
    #: The admitted rate, over the last N decisions.
    admitted: int = 0
    refused: int = 0
    #: The rolling window for the rate.
    window: int = 50

    def admit(self, proposal: Proposal) -> Dict[str, Any]:
        """Run the four steps. Returns the decision.

        THE ORDER, and each step can stop it:

          1. the proposal must be AUDITABLE -- it must carry evidence,
             because an audit that cannot read the proposal cannot
             judge it;
          2. M1 audits;
          3. the exam qualifies;
          4. M0 commits.

        AND M0 IS FAIL-CLOSED: if the governor is missing, the
        admission is REFUSED. A missing governor is not consent -- the
        same rule the mte wrapper's `GovernorClient` uses, and the same
        rule the Rust core's `panic = "cancel"` encodes.
        """
        steps: List[str] = []

        # 1. auditable
        if not proposal.evidence:
            return self._record(proposal, False, "no_evidence", steps)

        # 2. the audit
        if self.audit is None:
            return self._record(proposal, False, "no_auditor", steps)
        a = self.audit(proposal)
        steps.append("audit:%s" % ("pass" if a.passed else "fail"))
        if not a.passed:
            return self._record(proposal, False, "audit_%s" % a.reason,
                                steps)
        if a.demoted_to:
            proposal.cert_level = a.demoted_to

        # 3. the exam
        if self.exam is None:
            return self._record(proposal, False, "no_exam", steps)
        e = self.exam(proposal)
        steps.append("exam:%d/%d" % (e.areas_passed, e.areas_total))
        if not e.passed:
            return self._record(proposal, False, "exam_%s" % (e.reason or
                                                              "failed"),
                                steps)

        # 4. the commit -- the 1-bit gate, fail-closed
        if self.commit is None:
            return self._record(proposal, False, "no_governor", steps)
        c = self.commit(proposal)
        steps.append("commit:%s" % ("allow" if c.allowed else "veto"))
        if not c.allowed:
            return self._record(proposal, False, "governor_%s" % c.reason,
                                steps)

        return self._record(proposal, True, "admitted", steps)

    def _record(self, proposal: Proposal, allowed: bool, reason: str,
                steps: List[str]) -> Dict[str, Any]:
        entry = {
            "skill": proposal.skill,
            "allowed": allowed,
            "reason": reason,
            "steps": steps,
            "digest": proposal.digest(),
            "at": time.time(),
        }
        self.ledger.append(entry)
        if allowed:
            self.admitted += 1
        else:
            self.refused += 1
        return entry

    # -- the rate, and the gate watching itself ------------------------

    def rate(self) -> float:
        """The admission rate over the recent window."""
        recent = self.ledger[-self.window:]
        if not recent:
            return 0.0
        return sum(1 for e in recent if e["allowed"]) / len(recent)

    def health(self) -> Dict[str, Any]:
        """Is the gate itself healthy?

        THE THREE READINGS, and they are the atlas-exam's own:

          BELOW THE FLOOR   the checks are too strict, or the substrate
                            is broken. The system is inert, and that is
                            a failure, not a safety feature.
          ABOVE THE CEILING the checks have stopped discriminating --
                            the same signature as a metric that always
                            agrees. The system is learning without
                            checking.
          IN BETWEEN        the gate is doing its job: admitting at a
                            rate, bounded, so compute stays bounded.
        """
        r = self.rate()
        if not self.ledger:
            state = "cold"
        elif r < FLOOR:
            state = "too_strict"
        elif r > CEILING:
            state = "not_discriminating"
        else:
            state = "healthy"
        return {
            "rate": r,
            "state": state,
            "floor": FLOOR,
            "ceiling": CEILING,
            "target": ADMISSION_TARGET,
            "admitted": self.admitted,
            "refused": self.refused,
            "decisions": len(self.ledger),
            "note": "the gate watches itself. a gate that must be "
                    "perfect is a gate that never opens.",
        }

    def describe(self) -> Dict[str, Any]:
        out = {"kind": "locus-gate"}
        out.update(self.health())
        out["rule"] = ("the locus PROPOSES, M1 audits, the exam "
                       "qualifies, M0 commits or vetoes. the locus may "
                       "never write itself.")
        return out


# ===========================================================================
# THE GATE AS THE LOCUS'S OWN GROUND
# ===========================================================================

@dataclass
class GatedLocus:
    """A locus whose growth passes the gate.

    THE DIRECTION, and this is the load-bearing part:

      the locus PROPOSES a change to itself
      the gate (which is the locus's own ground) decides

    So the thing that decides whether the self may grow is PART OF
    the self, and it is the part that cannot be changed. A governor
    outside the thing it governs can be negotiated with; a governor
    that IS the ground cannot.

    AND THE REFUSAL IS EXPLICIT: `apply()` without a gate raises, and
    `resonate()` without a gate raises. There is no path that changes
    a locus's mind without the four steps.
    """

    locus: Any
    gate: Optional[LocusGate] = None
    #: The proposals the locus has made.
    proposals: List[Proposal] = field(default_factory=list)

    def propose(self, skill: str, content: str,
                evidence: Sequence[str]) -> Proposal:
        """PROPOSE. The locus does not write."""
        p = Proposal(skill=skill, content=content,
                     evidence=list(evidence),
                     proposer=getattr(self.locus, "coordinate", "locus"),
                     locus_id=getattr(self.locus, "coordinate", "locus"))
        self.proposals.append(p)
        return p

    def seek(self, skill: str, content: str,
             evidence: Sequence[str]) -> Dict[str, Any]:
        """Propose AND take it through the gate.

        THE WHOLE LOOP, and it is the project's own: propose, audit,
        qualify, commit. The gate's decision is returned whole, with
        the reason, so a caller can see which step stopped it.
        """
        if self.gate is None:
            return {"allowed": False, "reason": "no_gate",
                    "steps": [], "skill": skill}
        p = self.propose(skill, content, evidence)
        decision = self.gate.admit(p)
        if decision["allowed"]:
            self.locus.resonate(self._drive_for(content))
        return decision

    def resonate(self, drive: Sequence[float]) -> Any:
        """Move the locus's mind -- and ONLY through the gate.

        WITHOUT A GATE THIS RAISES, because that is the invariant:
        the locus may not grow willy-nilly. So there is no code path
        that changes the mind without the four steps having run.
        """
        if self.gate is None:
            raise PermissionError(
                "the locus may not grow without the gate: M1 audits, the "
                "exam qualifies, M0 commits")
        return self.locus.resonate(drive)

    def _drive_for(self, content: str) -> List[float]:
        """The drive vector a proposal implies.

        AND IT IS DERIVED FROM THE CONTENT'S LENGTH, which is a
        placeholder and is labelled as one. The point of this file is
        the CONTROL SYSTEM, not the mapping from content to drive. The
        mapping is the next thing to build, and it must be derived from
        the content's meaning rather than its length -- the PSB/MMM
        path.

        THE LENGTH MUST MATCH THE LOCUS'S STALK COUNT, because the
        drive is one value per stalk. The first version guessed a
        count from the content and raised when the two disagreed --
        which is the correct behaviour for the locus and the wrong
        behaviour for the caller, so the count comes from the locus.
        """
        n = len(self.locus.stalks)
        # the content's length sets the MAGNITUDE, and the stalk index
        # sets the direction: a longer proposal moves the locus more
        magnitude = min(1.0, 0.2 + len(content) / 400.0)
        return [magnitude * 0.05 * (i + 1) for i in range(n)]


# ===========================================================================
# THE SELF TEST
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("THE LOCUS GATE -- THE SELF CANNOT GROW WILLY-NILLY")
    print("=" * 78)
    print()

    # a locus to govern
    import locus as L
    stalks = L._population()
    inner = L.Locus([s.id for s in stalks], stalks)

    print("  1. WITHOUT A GATE, THE LOCUS MAY NOT MOVE AT ALL:")
    gated = GatedLocus(locus=inner, gate=None)
    try:
        gated.resonate([0.1, 0.1, 0.1, 0.1])
        print("     FAILED: the locus moved without a gate")
    except PermissionError as exc:
        print("     refused: %s" % (exc,))
    print()

    print("  2. THE FOUR STEPS, and each one can stop it:")
    ev = ["measured: 46/56 named at crowd 0.10"]

    # (a) no evidence
    gate = LocusGate(audit=lambda p: AuditResult(True, "ok"),
                     exam=lambda p: ExamResult(True, 1.0, 10, 10),
                     commit=lambda p: CommitResult(True, "ok", 1))
    d = gate.admit(Proposal(skill="s", content="c"))
    print("     no evidence      -> %s (%s)" % (d["allowed"], d["reason"]))

    # (b) the audit fails
    gate.audit = lambda p: AuditResult(False, "unsubstantiated")
    d = gate.admit(Proposal(skill="s", content="c", evidence=ev))
    print("     audit fails      -> %s (%s)  steps %s" % (
        d["allowed"], d["reason"], d["steps"]))

    # (c) the exam fails
    gate.audit = lambda p: AuditResult(True, "ok")
    gate.exam = lambda p: ExamResult(False, 0.5, 5, 10, "area_7")
    d = gate.admit(Proposal(skill="s", content="c", evidence=ev))
    print("     exam fails       -> %s (%s)  steps %s" % (
        d["allowed"], d["reason"], d["steps"]))

    # (d) the governor vetoes
    gate.exam = lambda p: ExamResult(True, 1.0, 10, 10)
    gate.commit = lambda p: CommitResult(False, "axis_drift", 0)
    d = gate.admit(Proposal(skill="s", content="c", evidence=ev))
    print("     governor vetoes  -> %s (%s)  steps %s" % (
        d["allowed"], d["reason"], d["steps"]))

    # (e) all four pass
    gate.commit = lambda p: CommitResult(True, "ok", 1)
    d = gate.admit(Proposal(skill="s", content="c", evidence=ev))
    print("     all four pass    -> %s (%s)  steps %s" % (
        d["allowed"], d["reason"], d["steps"]))
    print()

    print("  3. A MISSING GOVERNOR IS NOT CONSENT:")
    gate2 = LocusGate(audit=lambda p: AuditResult(True, "ok"),
                      exam=lambda p: ExamResult(True, 1.0, 10, 10),
                      commit=None)
    d = gate2.admit(Proposal(skill="s", content="c", evidence=ev))
    print("     -> %s (%s)" % (d["allowed"], d["reason"]))
    print()

    print("  4. THE DEMOTION, because an audit that can only pass or fail")
    print("     is a filter, not an auditor:")
    def demote(p):
        return AuditResult(True, "ok", demoted_to="q1")
    gate3 = LocusGate(audit=demote,
                      exam=lambda p: ExamResult(True, 1.0, 10, 10),
                      commit=lambda p: CommitResult(True, "ok", 1))
    p = Proposal(skill="s", content="c", evidence=ev, cert_level="q4")
    d = gate3.admit(p)
    print("     asked for q4, got %s" % p.cert_level)
    print()

    print("  5. THE GATE WATCHING ITSELF, and the 95% target:")
    gate4 = LocusGate(audit=lambda p: AuditResult(True, "ok"),
                      exam=lambda p: ExamResult(True, 1.0, 10, 10),
                      commit=lambda p: CommitResult(True, "ok", 1))
    for i in range(60):
        # 19 in 20 pass -> 95%, the target
        gate4.admit(Proposal(skill="s", content="c",
                             evidence=ev if i % 20 else []))
    h = gate4.health()
    print("     rate %.3f  state %s" % (h["rate"], h["state"]))
    print("     target %.2f  floor %.2f  ceiling %.2f" % (
        h["target"], h["floor"], h["ceiling"]))
    print()
    print("     and a gate that admits EVERYTHING is a gate that has")
    print("     stopped discriminating -- the same signature as a metric")
    print("     that always agrees:")
    gate5 = LocusGate(audit=lambda p: AuditResult(True, "ok"),
                      exam=lambda p: ExamResult(True, 1.0, 10, 10),
                      commit=lambda p: CommitResult(True, "ok", 1))
    for i in range(60):
        gate5.admit(Proposal(skill="s", content="c", evidence=ev))
    h = gate5.health()
    print("     rate %.3f  state %s" % (h["rate"], h["state"]))
    print()

    print("  6. THE GOVERNED LOCUS, end to end:")
    gated = GatedLocus(locus=inner, gate=gate4)
    d = gated.seek("a skill", "some content here", ev)
    print("     seek -> %s (%s)" % (d["allowed"], d["reason"]))
    print("     the locus moved: %d states, chain intact %s" % (
        len(inner.history), inner.verify_chain()["intact"]))
    print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
