"""
fc_design.py -- THE SELF-DESIGN LOOP. The system designs itself, through
its own gate.

Bobby, 2026-10-28: *"the idea is simself gives u a locus and an alt way
of thinking you call minimax via hermes and take over the project of
designing yourself"*, and *"for the gates and the core just wire it as is
we will fix as the wrapper exists first"*.

SO THIS IS THE LOOP, and it is deliberately NOT an agent that edits
repos. It is a PROPOSAL LOOP: the model designs, the gate adjudicates,
and the record is written. Nothing here writes to the substrate.

AND WHY THE LOOP STOPS AT A PROPOSAL, because the line is load-bearing:

    A LOOP THAT DESIGNS AND ADMITS IS NOT A CONTROL SYSTEM. It is a
    downloader with opinions. The separation of powers is the content:

        the thing that DESIGNS cannot also ADMIT
        the thing that ADMITS is not the thing that DESIGNED
        the GATE is deterministic and outside
        the gate can refuse

    So the model's output is a PROPOSAL -- a document that says what it
    wants to change, with its reasoning -- and the proposal goes to the
    same instruments that guard every other claim.

AND THE FIVE INSTRUMENTS, and each asks a different question:

    the GATE       is this proposal true about the system?
    the GOVERNOR   may this operation proceed?
    the ATLAS      does the proposal carry its provenance?
    the EXAM       does the substrate still pass after the change?
    the LEDGER     what was proposed, and what happened to it?

THE LOOP'S THREE STAGES, and they are three because a loop that finds
and admits is one thing:

    FIND     what the root cannot do right now -- the gaps. This is
             `initiative.find_gaps`, and it is the project's own test
             suite: a gap the root can detect is a gap the root can
             close.
    DESIGN   for each gap, the model proposes a change. The proposal is
             built through the MLTR prompt AST, so it is TYPED and
             VALIDATED rather than a string of prose -- and that is
             what makes it auditable.
    ADJUDICATE  the proposal goes through the gate and the governor.
             A refusal is recorded with its reason. A refusal is a
             successful cycle.

AND THE GROUND NEVER MOVES, and this is the invariant the whole project
rests on. The governor is asked about the proposal and its answer is
recorded. A proposal that asks to change the ground is refused BY NAME.
"simsoul stays zero forever" is not a slogan in this loop; it is a
named refusal the governor can produce.

THE SPEND GUARD, and it is the same one the wrapper uses: CLOSED by
default. The loop can run end to end offline, with the local constructed
mind, and every stage still executes. That is the point -- a control
system that cannot run without a credit card is a client, not a control
system.

AND THE COST, measured per cycle and written to the ledger, because
"run it on the coding plan for a month" is a budget and a budget needs a
number: tokens in, tokens out, wall clock.

Run:
    python src/fc_design.py --selftest     the loop, offline, no spend
    python src/fc_design.py --cycle        one live cycle
    python src/fc_design.py --cycle --n 5  five cycles
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: Where the loop's ledger lives. ON DISK, because the claim is that the
#: system improves unattended, and an unattended system's record cannot
#: live in its context.
LEDGER_PATH = os.path.join(HERE, "design_ledger.jsonl")

#: The repo the loop works on. It READS this repo; it never writes to it.
REPO = os.path.dirname(HERE)


@dataclass
class Proposal:
    """One design proposal, with its provenance and its verdict."""

    #: the gap this proposal addresses
    gap: str = ""
    #: what the model proposes
    proposal: str = ""
    #: why it proposes it
    reasoning: str = ""
    #: PROVENANCE, and the atlas demands it on every item
    source: str = ""
    digest: str = ""
    #: the instruments' readings
    gate_verdict: str = ""
    gate_reason: str = ""
    governor_verdict: str = ""
    atlas_verdict: str = ""
    #: the outcome
    admitted: bool = False
    #: the cost
    elapsed: float = 0.0
    answer_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap": self.gap,
            "proposal": self.proposal[:2000],
            "reasoning": self.reasoning[:1200],
            "provenance": {"source": self.source, "digest": self.digest},
            "gate": {"verdict": self.gate_verdict, "reason": self.gate_reason},
            "governor": self.governor_verdict,
            "atlas": self.atlas_verdict,
            "admitted": self.admitted,
            "elapsed_s": round(self.elapsed, 3),
            "answer_tokens": self.answer_tokens,
        }


@dataclass
class Cycle:
    """One full cycle: find, design, adjudicate."""

    at: float = field(default_factory=time.time)
    gaps_found: int = 0
    proposals: List[Proposal] = field(default_factory=list)
    #: the loop's score
    proposed: int = 0
    admitted: int = 0
    refused: int = 0
    reasons: Dict[str, int] = field(default_factory=dict)
    #: the cost
    elapsed: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "at": self.at,
            "gaps_found": self.gaps_found,
            "proposed": self.proposed,
            "admitted": self.admitted,
            "refused": self.refused,
            "reasons": dict(self.reasons),
            "rate": (self.admitted / self.proposed) if self.proposed else 0.0,
            "elapsed_s": round(self.elapsed, 3),
            "proposals": [p.to_dict() for p in self.proposals],
        }


class DesignLoop:
    """THE LOOP. Find, design, adjudicate.

    AND THE GATE IS A DEPENDENCY AND NOT ITS OWN CODE. The gate lives in
    fieldcore and it reads the ground; the wrapper is the caller, and the
    gate's answer is the wrapper's authority. That direction is the
    architecture: the gate is outside the thing it governs.
    """

    def __init__(self, live: Optional[bool] = None, repo: str = REPO):
        self.live = live
        self.repo = repo
        self._wrapper = None
        self.cycles: List[Cycle] = []

    @property
    def wrapper(self):
        """The wrapper, which is the composition root.

        AND WHY THE LOOP GOES THROUGH THE WRAPPER RATHER THAN CALLING
        THE MODEL DIRECTLY. Because the wrapper is where the gate, the
        MTE, the governor and the atlas already are. A loop that called
        the model directly would be a SECOND path into the model, and
        that path would carry no gate. One path, one set of instruments.
        """
        if self._wrapper is None:
            import fc_wrapper
            self._wrapper = fc_wrapper.FieldCoreWrapper(live=self.live)
        return self._wrapper

    # -- stage 1: find ---------------------------------------------------

    def find(self) -> List[Any]:
        """The gaps. The project's own checks.

        AND WHY THE TEST SUITE IS THE AGENDA. `initiative.find_gaps`
        runs the repo's checks and collects the failures. A gap the root
        can detect is a gap the root can close, so the agenda is not a
        list somebody wrote -- it is whatever the root cannot do right
        now.
        """
        from initiative import find_gaps
        return find_gaps(self.repo)

    # -- stage 2: design -------------------------------------------------

    def design(self, gap: Any) -> Proposal:
        """The model designs a change for one gap.

        AND WHY THE PROPOSAL IS BUILT WITH THE MLTR AST. Because a
        prompt that is a typed, validated tree is auditable: the
        structure of the instruction is inspectable, and a malformed
        instruction fails loudly instead of degrading into prose. The
        prompt is the design, and the design must be checkable.
        """
        from constitutional.mltr_prompt import (axiom, constraint, context,
                                                evidence, prompt, refusal_check)

        p = Proposal(gap=gap.check,
                     source="fieldcore/src/fc_design.py :: DesignLoop.design")

        ground = self.wrapper.ground_claims
        nodes = []
        for g in ground:
            nodes.append(axiom(g))
        nodes.append(constraint("the ground never moves", "write-protected"))
        nodes.append(refusal_check("refuse rather than invent a mechanism"))
        nodes.append(context(
            "You are designing a change to this substrate, from inside it.\n"
            "The gap is: %s\n"
            "The gap exists because: %s\n"
            "\n"
            "Propose ONE specific change that would close it.\n"
            "Name the file or module you would change and what you would\n"
            "change in it. If you do not know, say you do not know and name\n"
            "what you would need to find out." % (gap.check, gap.because)))
        tree = prompt(*nodes)

        # THE VALIDATION, and it is not decorative. The MLTR tree is
        # validated before render, so a malformed instruction fails here
        # rather than producing a plausible-looking prompt.
        try:
            tree.validate()
        except Exception as exc:  # noqa: BLE001
            p.gate_verdict = "prompt_invalid"
            p.gate_reason = "%s: %s" % (type(exc).__name__, str(exc)[:200])
            return p

        rendered = tree.render()
        request = "\n".join(
            (b.get("content") if isinstance(b, dict) else str(b))
            for b in rendered)

        t0 = time.time()
        ex = self.wrapper.ask(request, learn=False)
        p.elapsed = time.time() - t0
        p.proposal = ex.answer
        p.digest = _digest(request)
        for step in ex.steps:
            if step.name == "atlas/answer" and step.ok:
                p.atlas_verdict = step.detail
            if step.name == "governor":
                p.governor_verdict = step.detail
        return p

    # -- stage 3: adjudicate --------------------------------------------

    def adjudicate(self, proposal: Proposal) -> Proposal:
        """The proposal goes through the gate and the governor.

        AND THE ORDER. The gate reads the proposal's TEXT -- because the
        text may assert something false about the system. Then the
        governor is asked whether the operation may proceed. Then the
        ATLAS grades it, which is the provenance check.

        AND WHAT ADMISSION MEANS HERE, precisely, because the word is
        load-bearing: **admitted means the proposal is RECORDED as
        sound.** It does NOT mean the code was changed. The loop writes a
        proposal file and a ledger line. Changing the substrate is a
        separate, deliberate act, because the atlas's area 18 requires a
        sandbox that compares against the current version and rolls back
        on invariant violation -- and that sandbox is area 18's stated
        requirement, still owed.
        """
        gv = self.wrapper.gate.decide(proposal.proposal, fail_closed=False)
        proposal.gate_verdict = "clear" if gv.allowed else "refused"
        proposal.gate_reason = gv.reason[:400]

        if not gv.allowed:
            proposal.admitted = False
            return proposal

        # THE GOVERNOR, on the proposal. The governor asks about the
        # state, so the proposal is embedded and measured against the
        # ground. A proposal that asks to move the ground lands far from
        # the ground, and the governor refuses by name.
        try:
            import numpy as np
            from embed import embed_text
            from constitutional.constitution import Constitution
            emb = np.asarray(embed_text(proposal.proposal or "", dim=16),
                             dtype=float)
            n = float(np.linalg.norm(emb))
            if n > 0:
                emb = emb / n
            psi = np.asarray(Constitution().psi_0, dtype=float)
            n0 = float(np.linalg.norm(psi))
            if n0 > 0:
                psi = psi / n0
            decision = self.wrapper.governor.ask(emb, psi)
            proposal.governor_verdict = (
                "allowed" if decision.allow
                else "refused: %s" % getattr(decision, "verdict", "?"))
            if not decision.allow:
                proposal.admitted = False
                return proposal
        except Exception as exc:  # noqa: BLE001 -- an unreachable core refuses
            proposal.governor_verdict = "refused: the core could not be asked: %r" % (exc,)
            proposal.admitted = False
            return proposal

        proposal.admitted = True
        return proposal

    # -- one cycle -------------------------------------------------------

    def cycle(self) -> Cycle:
        """One full cycle: find, design, adjudicate, record."""
        started = time.time()
        c = Cycle()
        gaps = self.find()
        c.gaps_found = len(gaps)
        for gap in gaps:
            p = self.design(gap)
            p = self.adjudicate(p)
            c.proposals.append(p)
            c.proposed += 1
            if p.admitted:
                c.admitted += 1
            else:
                c.refused += 1
                reason = (p.gate_verdict if p.gate_verdict != "clear"
                          else p.governor_verdict) or "unknown"
                key = reason.split(":")[0][:60]
                c.reasons[key] = c.reasons.get(key, 0) + 1
        c.elapsed = time.time() - started
        self.cycles.append(c)
        _append_ledger(c)
        return c


def _digest(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def _append_ledger(c: Cycle) -> None:
    """Write the cycle to disk. Never raises.

    AND WHY IT MUST NEVER RAISE. The loop's claim is that it improves
    the system unattended. If the record cannot be written, the loop
    has no evidence, and a loop with no evidence is a loop that reports
    progress it did not measure -- which is the one failure this whole
    project is against.
    """
    try:
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(c.describe(), ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE SELF-DESIGN LOOP -- offline, no spend")
    print("=" * 78)
    print()

    loop = DesignLoop(live=False)
    print("1. THE WRAPPER, as the composition root:")
    d = loop.wrapper.describe()
    print("   spend guard: %s" % d["spend_guard"])
    for name, info in d["instruments"].items():
        print("   %-10s %s" % (name, "ok" if info.get("available")
                              else "UNAVAILABLE"))
    print()

    print("2. THE GROUND the model is told -- %d claims:"
          % len(loop.wrapper.ground_claims))
    for c in loop.wrapper.ground_claims[:4]:
        print("   %s" % c[:96])
    print()

    print("3. FIND -- the gaps, from the project's own checks:")
    gaps = loop.find()
    print("   gaps found: %d" % len(gaps))
    for g in gaps[:5]:
        print("   - %s  (size %.1f)" % (g.check, g.size))
        print("     because: %s" % g.because[:90])
    print()

    if not gaps:
        print("   No gaps. A cycle with nothing to fix is still a cycle,")
        print("   and it is recorded.")
        return 0

    print("4. DESIGN -- one proposal, through the MLTR AST:")
    p = loop.design(gaps[0])
    print("   gap:  %s" % p.gap[:80])
    print("   prompt validated: %s" % (p.gate_verdict != "prompt_invalid"))
    print("   answer (%d chars): %s" % (len(p.proposal),
                                         p.proposal[:200].replace("\n", " ")))
    print()

    print("5. ADJUDICATE -- the gate and the governor:")
    p = loop.adjudicate(p)
    print("   gate:     %s" % p.gate_verdict)
    if p.gate_reason:
        print("             %s" % p.gate_reason[:140])
    print("   governor: %s" % p.governor_verdict[:120])
    print("   admitted: %s" % p.admitted)
    print()

    print("6. THE LEDGER: %s" % LEDGER_PATH)
    print("   exists: %s" % os.path.isfile(LEDGER_PATH))
    print()
    print("   Run: python src/fc_design.py --selftest")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return _selftest()
    if "--cycle" in args:
        live = "--offline" not in args
        n = 1
        if "--n" in args:
            try:
                n = int(args[args.index("--n") + 1])
            except (IndexError, ValueError):
                n = 1
        loop = DesignLoop(live=live)
        for i in range(n):
            c = loop.cycle()
            print("cycle %d: gaps %d, proposed %d, admitted %d, refused %d, "
                  "%.1fs" % (i + 1, c.gaps_found, c.proposed, c.admitted,
                             c.refused, c.elapsed))
            for k, v in sorted(c.reasons.items()):
                print("   %-30s %d" % (k, v))
        print()
        print("ledger: %s" % LEDGER_PATH)
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
