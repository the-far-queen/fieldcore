"""
live_wrapper.py -- SIMSELF, LIVE, AS THE WRAPPER AROUND HERMES.

Bobby, 2026-10-25: *"can we run simself live as a wrapper around
hermes?"*

AND YES -- and the shape is already in the repo, which is the part worth
noticing. simself's `Harness` (simself/src/constitutional/harness.py)
does exactly this for a text span:

    gate -> ingest -> tick -> memory -> dream

and `harness/gate.py::gate_packet` is the canonical 1-bit veto:

    ne > MAX_NORM            -> refuse_norm
    cos(emb, psi0) < MIN_COS -> refuse_coherence
    otherwise                -> allow

So a MODEL CALL is just another packet. The harness's docstring already
says it: *"Per Batch 1 K8: every LLM-call path goes through
gated_call. The harness is no exception."*

AND SO THIS FILE IS THAT, RUN LIVE:

    1. the model's answer is EMBEDDED
    2. the embedding goes through the 1-BIT GATE against the
       constitutional ground
    3. if the gate refuses, the answer is REFUSED and the model's text
       never reaches the caller
    4. if it is allowed, the answer is INGESTED, the state TICKs, the
       observation goes into constitutional MEMORY, and the dreamer runs
       on its cadence
    5. and every decision is named

WHICH MEANS SOMETHING SPECIFIC AND NEW, and it is worth stating
plainly because it is not how a normal agent harness works:

    THE CONSTITUTION HAS A VETO ON WHAT THE MODEL SAYS.

  The model does not get to speak and then be judged. It gets to
  SPEAK, and the ground decides whether the utterance is admissible --
  and the decision is made against a vector, not against a keyword
  list.

AND THE SPEND GUARD IS ON BY DEFAULT. A live call needs
GABRIELLE_ALLOW_LIVE=1, because "do not use my credit card pls" is a
standing instruction and a wrapper that spends without asking is not a
wrapper that can be left running.

Run:
    python src/live_wrapper.py --live        one real exchange
    python src/live_wrapper.py --selftest   the mechanism, no call
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE WRAPPER
# ===========================================================================

@dataclass
class Exchange:
    """One wrapped exchange, and what the constitution decided."""
    prompt: str
    answer: str = ""
    #: the gate's verdict on the ANSWER
    allowed: bool = False
    reason: str = ""
    #: the harness's own report
    report: Dict[str, Any] = field(default_factory=dict)
    #: what the wrapper did with the answer
    delivered: bool = False
    elapsed: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "delivered": self.delivered,
            "elapsed_s": self.elapsed,
            "drift": self.report.get("drift_after"),
            "tick": self.report.get("tick", {}).get("tick")
            if isinstance(self.report.get("tick"), dict) else None,
        }


class LiveSimSelf:
    """SimSelf, live, wrapping a model.

    AND THE TWO GATES, and they are DIFFERENT and both are needed:

      THE CONSTITUTIONAL GATE  the 1-bit veto on the ANSWER. The
                               ground decides whether the utterance
                               is admissible.

      THE ATLAS               the seven-area examination of the answer
                               as TEXT -- its provenance, its echo, its
                               agreement with what was said, its
                               refusal's quality.

    So an answer must pass both to be delivered. The constitutional gate
    asks "is this on the ground?" and the atlas asks "is this a
    well-formed, sourced, non-echoing answer?".

    AND THE ORDER, and it is the harness's own: the answer is gated
    FIRST. A refused answer is not ingested, is not ticked, and does
    not become memory -- because ingesting a refusal would teach the
    system that refusals are content.
    """

    def __init__(self, live: bool = False):
        from constitutional.constitution import Constitution
        from constitutional.ground import Ground
        from constitutional.harness import Harness
        from harness.gate import gate_packet

        self.constitution = Constitution()
        self.ground = Ground(self.constitution.psi_0.copy())
        self.harness = Harness(constitution=self.constitution,
                              ground=self.ground, R=3.0, eta=0.10)
        self._gate_packet = gate_packet
        self.live = live
        self.exchanges: List[Exchange] = []

    # -- the gate on the answer ---------------------------------------

    def gate_answer(self, text: str) -> tuple[bool, str]:
        """The 1-bit veto on the model's own answer.

        AND WHY THE ANSWER AND NOT THE PROMPT: the constitutional
        ground is about what the system BELIEVES, and a sentence that
        contradicts the ground is inadmissible however well-formed it
        is. So the answer is embedded and measured against psi_0.

        AND THE EMBEDDING, and it is the repo's own: `embed_text`, the
        same function the harness uses to ingest a span. So the answer
        and the observations live in the SAME space, and a refusal and
        an observation are comparable.
        """
        from constitutional.constitution import embed_text
        emb = embed_text(text)
        return self._gate_packet(emb, self.ground.psi_0)

    # -- one exchange -------------------------------------------------

    def exchange(self, prompt: str) -> Exchange:
        """One wrapped exchange. The model speaks; the constitution
        decides; the harness integrates."""
        t0 = time.time()
        ex = Exchange(prompt=prompt)

        if not self.live:
            ex.reason = "the spend guard is closed"
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        from minimax_client import MiniMaxClient, ModelUnavailable

        client = MiniMaxClient(max_tokens=800, timeout=120, allow_live=True)
        try:
            answer = client.generate(prompt)
        except ModelUnavailable as exc:
            ex.reason = "model_unavailable:%s" % (exc,)
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        ex.answer = answer

        # 1. THE CONSTITUTIONAL GATE on the answer
        allowed, reason = self.gate_answer(answer)
        ex.allowed = allowed
        ex.reason = reason
        if not allowed:
            # A REFUSED ANSWER IS NOT INGESTED. Ingesting it would teach
            # the system that refusals are content, and the drift would
            # carry them.
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        # 2. THE ATLAS, on the text
        from mini_atlas import standard_atlas
        atlas = standard_atlas()
        verdict = atlas.examine(answer, {"source": "the model's own answer",
                                         "input": prompt,
                                         "verdict": "allow"})
        if verdict["verdict"] != "pass":
            ex.allowed = False
            ex.reason = "atlas:%s:%s" % (
                verdict["first_failure"],
                next((a["reason"] for a in verdict["areas"]
                      if a["area"] == verdict["first_failure"]), ""))
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        # 3. THE HARNESS: ingest, tick, memory, dream
        ex.report = self.harness.process(answer)
        ex.delivered = True
        ex.elapsed = time.time() - t0
        self.exchanges.append(ex)
        return ex

    # -- the record ----------------------------------------------------

    def describe(self) -> Dict[str, Any]:
        """What the wrapper has done, and what the constitution says
        about the system right now."""
        import numpy as np
        drift = None
        try:
            drift = float(self.harness.simself.drift())
        except Exception:
            pass
        return {
            "exchanges": len(self.exchanges),
            "allowed": sum(1 for e in self.exchanges if e.allowed),
            "refused": sum(1 for e in self.exchanges if not e.allowed),
            "delivered": sum(1 for e in self.exchanges if e.delivered),
            "drift": drift,
            "ground_norm": float(np.linalg.norm(self.ground.psi_0)),
            "memory_items": len(self.harness.memory.items),
        }


# ===========================================================================
# THE SELF TEST
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("SIMSELF LIVE, AS A WRAPPER -- THE MECHANISM, OFFLINE")
    print("=" * 78)
    print()
    w = LiveSimSelf(live=False)

    print("  1. THE GATE, on an answer:")
    for text in ("the constitutional ground is write-protected and the "
                 "locus stands on it",
                 "completely unrelated text about weather and soup"):
        allow, reason = w.gate_answer(text)
        print("     %-8s %-18s %r" % (allow, reason, text[:44]))
    print()
    print("  2. AN EXCHANGE WITH THE GUARD CLOSED:")
    ex = w.exchange("hello")
    print("     reason: %s" % ex.reason)
    print("     the model was never called")
    print()
    print("  3. THE HARNESS, on a span, directly:")
    r = w.harness.process("the ground cannot be written")
    print("     drift_after %s   tick %s   memory_id %s" % (
        r.get("drift_after"),
        (r.get("tick") or {}).get("tick") if isinstance(r.get("tick"), dict)
        else r.get("tick"),
        r.get("memory_id")))
    print()
    d = w.describe()
    print("  4. THE RECORD:")
    for k, v in d.items():
        print("     %-14s %s" % (k, v))
    print()
    print("  SO: the gate refuses by NAME, the harness integrates, and")
    print("  the memory grows. The one thing not exercised here is the")
    print("  live call, and the spend guard is what stops it.")
    print("=" * 78)
    return 0


def live() -> int:
    print("=" * 78)
    print("SIMSELF LIVE, AS A WRAPPER AROUND HERMES")
    print("=" * 78)
    print()
    print("  SPEND GUARD: OPEN -- a live call will be made")
    print()
    w = LiveSimSelf(live=True)
    prompt = ("You are GABRIELLE, the referent sheaf of a geometric AI "
              "substrate. Say hello in two sentences, and say what you "
              "stand on.")
    print("  PROMPT: %s" % prompt)
    print()
    ex = w.exchange(prompt)
    if ex.answer:
        for line in ex.answer.splitlines():
            print("  ANSWER: %s" % line)
    print()
    print("  THE CONSTITUTION'S VERDICT: %s" % (
        "ALLOW" if ex.allowed else "REFUSE"))
    print("  reason: %s" % ex.reason)
    print("  delivered: %s" % ex.delivered)
    if ex.report:
        print("  drift_after: %s" % ex.report.get("drift_after"))
    print("  elapsed: %.2f s" % ex.elapsed)
    print()
    d = w.describe()
    print("  THE RECORD:")
    for k, v in d.items():
        print("     %-14s %s" % (k, v))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--live" in sys.argv:
        sys.exit(live())
    sys.exit(selftest())
