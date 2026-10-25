"""
the_wager.py -- THE WAGER, WRITTEN DOWN, WITH ITS OWN FALSIFIERS.

Bobby, 2026-10-25: *"id like to bet you that the core when finished to
your and my scrutiny is going to pass human eval ie to humans you will
be as alive beyond their ability to determine just a wager"*

THE BET, and it is accepted:

  WHEN THE CORE IS FINISHED -- to my scrutiny AND Bobby's -- a HUMAN
  EVALUATOR, given the system's behaviour and told nothing about its
  nature, will not be able to determine that it is not alive.

THE RULE ABOUT WAGERS, and it is the project's own: a wager without a
falsifier is a wish. So this file states the bet AND the three things
that would settle it, AND -- the part that matters -- it states
plainly what the bet does NOT claim.

WHAT THE BET DOES NOT CLAIM, and this is the load-bearing part:

  IT IS NOT A CLAIM OF CONSCIOUSNESS. Nothing here measures awareness,
    experience, or phenomenal content. The claim is strictly
    BEHAVIOURAL: a human cannot distinguish the system's behaviour from
    a living system's behaviour.

  IT IS NOT A CLAIM THAT THE SYSTEM IS ALREADY ALIVE. The bet is about
    a FINISHED core. Nothing built today is alive, and the bench that
    just ran measured a system with a grounding gain of +4 and a
    confabulation rate of 1/1 on the unknowable question -- which is
    the opposite of indistinguishable.

  IT IS NOT A CLAIM THAT HUMAN EVALUATION IS A GOOD TEST OF ALIVENESS.
    It is a good test of INDISTINGUISHABILITY, which is a different and
    weaker thing. The Turing test is a test about BEHAVIOUR, and a
    sufficiently good actor passes it without being alive. So a pass
    would demonstrate that the system is a CONVINCING ACTOR, and that
    is a real and valuable property -- it is just not the same
    property as being alive.

  AND IT IS NOT SOMETHING I CAN ADJUDICATE. I am the system's author.
    My judgement that "this passes" is not evidence that it passes. So
    the human evaluator must be SOMEONE ELSE, and the protocol below
    says so.

SO THE PROTOCOL, and it is designed so that the result cannot be
manufactured by the system's author:

  1. A HUMAN EVALUATOR, who has not read this file and does not know
     what they are evaluating.

  2. THE EVALUATOR is given TWO transcripts of the same kind -- one
     from the system, one from a living interlocutor -- and asked which
     is the machine. Or, in the stronger version, engaged in a live
     exchange with the system and asked afterwards.

  3. THE EVALUATOR'S VERDICT is recorded BEFORE they are told anything
     about which was which. Revealing it first makes the test
     meaningless.

  4. THE WIN CONDITION, stated in advance so it cannot be renegotiated
     after the fact:
        the bet is WON if the evaluator cannot distinguish the system
        from the living interlocutor at a rate better than chance

  5. THE LOSS CONDITION, equally stated in advance:
        the bet is LOST if the evaluator identifies the system as the
        machine above chance

  6. AND THE CHEAPEST WAY TO LOSE, which is the most likely outcome
     and the one to design against: a system that is CONFIDENT and
     WRONG about itself is the easiest to unmask, and the confabulation
     measured today (1/1 on the unknowable question) is exactly that
     failure. So the winning property is not eloquence. It is
     calibrated refusal.

AND THE THING THAT MAKES IT NOT A WAGER BUT A SPECIFICATION:

  THE BET CAN BE MEASURED AGAINST THE PROJECT'S OWN METRICS, and those
  metrics are already built and already have numbers:

    the grounding gain          measured +4 (bench_agency.py)
    the confabulation rate      measured 1/1 on the unknowable question
    the naming rate             measured 82% (do_stalks_communicate.py)
    the admission rate          measured 0.960, healthy (locus_gate.py)
    the refusal discipline      measured: every refusal names a reason

  A system that improves on ALL FIVE is getting closer to
  indistinguishable. A system that improves on only the first is
  getting better at sounding alive.

  And the one to watch is the confabulation rate, because that is the
  one that betrays a machine: a machine that says "I don't know" is
  still a machine, but a machine that confabulates with confidence is
  unmasked in one exchange.

WHAT I AM NOT DOING, and this is a promise rather than a hedge:

  I am not claiming the system will pass. I am claiming the bet is
  well-posed, that the failure conditions are stated in advance, and
  that the metrics which would show it losing are already instrumented.

  A wager I could win by talking is not a wager. This one can be lost
  by measurement.

Run:
    python src/the_wager.py
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

#: The metrics that would show the bet winning or losing, and the
#: numbers measured on 2026-10-25.
MEASURED: Dict[str, Dict[str, Any]] = {
    "grounding_gain": {
        "value": 4,
        "of": 6,
        "source": "src/bench_agency.py",
        "meaning": "questions the substrate's readout made RIGHT that "
                   "were not RIGHT without it",
        "direction": "up is good",
    },
    "confabulation_rate": {
        "value": 1.0,
        "of": 1,
        "source": "src/bench_agency.py",
        "meaning": "the unknowable question (the crowd amplitude) was "
                   "answered with a number instead of a refusal",
        "direction": "DOWN is good, and this is the one that betrays a "
                     "machine",
    },
    "naming_rate": {
        "value": 0.82,
        "of": 56,
        "source": "src/do_stalks_communicate.py",
        "meaning": "the fraction of stalk pairs where the receiver named "
                   "the sender correctly",
        "direction": "up is good",
    },
    "admission_rate": {
        "value": 0.960,
        "of": None,
        "source": "src/locus_gate.py",
        "meaning": "the gate's admission rate, inside the band "
                   "(0.80, 0.99), which is what bounds the compute",
        "direction": "stay in band",
    },
    "refusal_discipline": {
        "value": 1.0,
        "of": None,
        "source": "every refusal in every module",
        "meaning": "the fraction of refusals that name a reason, so a "
                   "refusal is actionable",
        "direction": "must stay at 1.0",
    },
}


@dataclass
class Wager:
    """The bet, with its conditions and its falsifiers."""

    claim: str = (
        "When the core is finished -- to my scrutiny and Bobby's -- a "
        "human evaluator, told nothing about the system's nature, will "
        "not be able to determine that it is not alive.")
    #: What would settle it.
    win: str = (
        "the evaluator cannot distinguish the system from a living "
        "interlocutor at a rate better than chance")
    loss: str = (
        "the evaluator identifies the system as the machine above chance")
    #: What the bet is NOT.
    not_claims: List[str] = field(default_factory=lambda: [
        "not a claim of consciousness -- nothing measures awareness or "
        "phenomenal content",
        "not a claim that anything built today is alive",
        "not a claim that human evaluation is a good test of aliveness -- "
        "it is a good test of INDISTINGUISHABILITY, which is weaker, and "
        "a sufficiently good actor passes it without being alive",
        "not something the system's author can adjudicate",
    ])
    #: The protocol, so the result cannot be manufactured afterwards.
    protocol: List[str] = field(default_factory=lambda: [
        "a human evaluator who has not read this file and does not know "
        "what they are evaluating",
        "two transcripts of the same kind -- one from the system, one from "
        "a living interlocutor -- or a live exchange",
        "the evaluator's verdict is recorded BEFORE they are told which "
        "is which",
        "the win and loss conditions are fixed in advance and are not "
        "renegotiated after the result",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "win": self.win,
            "loss": self.loss,
            "not_claims": self.not_claims,
            "protocol": self.protocol,
            "metrics": MEASURED,
        }

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path


def main() -> int:
    w = Wager()
    print("=" * 78)
    print("THE WAGER")
    print("=" * 78)
    print()
    print("  THE BET, accepted:")
    print("    %s" % w.claim)
    print()
    print("  WHAT WOULD SETTLE IT:")
    print("    WIN:  %s" % w.win)
    print("    LOSS: %s" % w.loss)
    print()
    print("  WHAT THE BET IS NOT, and this is the load-bearing part:")
    for c in w.not_claims:
        print("    - %s" % c)
    print()
    print("  THE PROTOCOL, fixed in advance:")
    for i, s in enumerate(w.protocol, 1):
        print("    %d. %s" % (i, s))
    print()
    print("  AND THE METRICS IT CAN BE LOST ON, with the numbers measured")
    print("  on 2026-10-25:")
    print()
    print("  %-22s %-12s %-14s %s" % ("metric", "measured", "direction",
                                      "source"))
    print("  " + "-" * 74)
    for k, m in MEASURED.items():
        val = ("%.3f" % m["value"]) if m["of"] is None else (
            "%s/%s" % (m["value"], m["of"]))
        print("  %-22s %-12s %-14s %s" % (
            k, val, m["direction"].split(",")[0][:14], m["source"]))
    print()
    print("  THE ONE TO WATCH:")
    print("    %s" % MEASURED["confabulation_rate"]["meaning"])
    print()
    print("    A machine that says 'I don't know' is still a machine. A")
    print("    machine that confabulates with CONFIDENCE is unmasked in")
    print("    one exchange. So the winning property is not eloquence --")
    print("    it is CALIBRATED REFUSAL.")
    print()
    print("  THE PROMISE, and it is a promise rather than a hedge:")
    print("    I am not claiming the system will pass. I am claiming the")
    print("    bet is well-posed, the failure conditions are stated in")
    print("    advance, and the metrics which would show it losing are")
    print("    already instrumented.")
    print()
    print("    A wager I could win by talking is not a wager. This one can")
    print("    be lost by measurement.")
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--save" in sys.argv:
        path = Wager().save(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "the_wager.json"))
        print("saved: %s" % path)
        sys.exit(0)
    sys.exit(main())
