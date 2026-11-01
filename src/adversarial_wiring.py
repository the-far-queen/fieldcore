"""
adversarial_wiring.py -- THE FC GATE AS THE ADVERSARY, WIRED TO THE
MODEL AND TO THE FAST/DEEP LOOP.

Bobby, 2026-11-01, in sequence:
    *"not just chain of reasoning there are gains being made in executive
    planning swarms of subagents where we used to run several the
    frontier models are succeeding with literal chains of adversarial
    critical subagents ie consecutive critical rebuttal ie three chain
    agents refuting or aggressively adversarial"*

    *"its brilliant like atlas inserted in the reasoning chain no more
    hallucination"*

    *"i feel bicameral brain ie fc and llm call can be used
    adversarially"*

    *"also can fc deeply if have microseconds to spare or in robot slice
    up time between fast brain and learning my goal is robot operation"*

    *"our core is still mighty useful gives the llm a new surface to
    exist in and reson in"*

**SO WHAT IS BUILT, and it is four pieces:**

    chain_audit.py        audits ONE chain after the fact
    adversarial_chain.py  adjudicates a chain of CRITICS
    adversarial_brain.py  the exchange: propose, attack, answer
    bicameral_loop.py     two time scales: fast reflex, sliced deep core

AND THIS FILE IS THE WIRING, because the four pieces above are
mechanisms and a mechanism nobody calls is a decoration.

WHAT THE GATE DOES NOW, AND WHAT IT SHOULD DO
---------------------------------------------
**TODAY** the gate READS the model's answer and refuses it if it
contradicts the ground. `fc_wrapper.ask()` runs: gate the prompt,
simself gives the locus, the model answers, the gate reads the
answer, the governor vetoes, the atlas grades, the library records.

**THE MISSING MOVE** is that the gate never SPEAKS BACK. It refuses,
and the model never learns WHY in a way it can act on. So the model
gets a wall, not an opponent.

**SO THE GATE ATTACKS.** The model's answer is turned into a claim,
the gate's own layers produce an OBJECTION to that claim, and the
objection goes back to the model as the next prompt. That is the
Atlas inserted in the chain: the claim does not reach the caller
until it has been attacked and has answered.

**AND WHY IT BEATS THE WRAPPER IDEA.** A wrapper constrains what the
model may say. This ENGAGES what the model said. The first makes the
model smaller; the second makes it sharper, because a real objection
is what makes reasoning improve. And the core is still the same core
-- it is still the ground, the register, the gate -- so it is not
adversarial to the system, it is adversarial to FALSEHOOD.

Run:
    python src/adversarial_wiring.py --selftest
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

__all__ = [
    "AdversarialResponder",
    "GateAttack",
    "attack_from_verdict",
]


@dataclass
class GateAttack:
    """An objection produced by the gate, aimed at the model's claim.

    **AND THE OBJECTION NAMES ITS TARGET.** "your answer is wrong" is
    useless to a model: it cannot act on it. So the attack says WHICH
    claim is at fault and WHY, and the reason carries the layer that
    caught it. That is the difference between a critic and a critic
    who is merely being difficult.
    """

    text: str
    #: The layer that caught it.
    layer: str = ""
    #: The claim that was objected to.
    target: str = ""
    held: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "layer": self.layer,
                "target": self.target, "held": self.held}


def attack_from_verdict(verdict: Any, target: str) -> Optional[GateAttack]:
    """Turn a gate verdict into an OBJECTION the model can act on.

    **AND IT RETURNS None WHEN THE GATE IS HAPPY.** A gate that always
    produces an objection is a gate that always objects, and the model
    would learn to ignore it -- which is worse than no gate at all.
    So an allowed verdict produces no attack.

    **AND THE TEXT IS THE GATE'S OWN REASON.** The gate already knows
    exactly which claim is at fault and which layer caught it, and the
    project's own doctrine says a refusal must NAME ITS REASON. So the
    objection is that reason, aimed at the claim.
    """
    if verdict is None:
        return None
    if getattr(verdict, "allowed", True):
        return None

    reason = (getattr(verdict, "reason", "") or "").strip()
    if not reason:
        return None

    # WHICH layer caught it -- so the objection names the instrument,
    # not just the verdict.
    layer = ""
    caught = getattr(verdict, "caught_by", None)
    if caught:
        layer = caught[0] if isinstance(caught, (list, tuple)) else str(caught)

    text = ("Your claim is refused by the ground's own instruments. "
            "The specific objection: %s\n"
            "Answer this objection directly -- either the claim changes, "
            "or you show why the objection does not hold."
            % reason)

    return GateAttack(text=text, layer=layer, target=target, held=True)


@dataclass
class AdversarialResponder:
    """The model side of the exchange, and the gate that attacks it.

    `client` is anything with `.generate(prompt) -> str` -- which is the
    project's own `LLMClient` Protocol, so the MiniMax client drops in
    unchanged.

    `gate` is anything with `.decide(text, fail_closed=...)` returning a
    verdict with `.allowed` and `.reason` -- which is fieldcore's own
    `FieldCoreGate`.

    **AND THE DEPTH IS THE ONE THING THAT MATTERS HERE.** MEASURED: the
    literature's finding on adversarial chains is that gains beyond a
    couple of rounds are small. So the default is THREE, and the loop
    stops the moment the gate is satisfied -- because an exchange that
    continues past the point of resolution is a conversation, not a
    check.
    """

    client: Any
    gate: Any
    depth: int = 3
    #: The prompt that frames the exchange.
    system_prompt: str = ""
    #: What the model is answering first.
    question: str = ""

    def respond(self, prompt: str, prior_attack: Optional[str] = None) -> str:
        """One model turn."""
        parts: List[str] = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        parts.append(prompt)
        if prior_attack:
            parts.append(prior_attack)
        text = self.client.generate("\n\n".join(parts))
        return text

    def exchange(self, question: Optional[str] = None,
                 fail_closed: bool = True) -> Dict[str, Any]:
        """Run the adversarial exchange and return the whole record.

        **AND THE ORDER IS THE ARCHITECTURE:**

            1. the model answers
            2. the GATE reads the answer
            3. if the gate objects, the objection goes BACK to the model
            4. repeat, up to the depth

        So the claim that reaches the caller is one that has been
        attacked. **AND THE GATE IS THE ONLY JUDGE** -- if the gate is
        satisfied, the answer stands, and there is no vote and no
        majority and no "the last speaker wins".
        """
        q = question if question is not None else self.question
        turns: List[Dict[str, Any]] = []
        answer = ""
        prior_attack: Optional[str] = None

        for depth in range(self.depth):
            t0 = time.perf_counter()
            answer = self.respond(q, prior_attack)
            model_ms = (time.perf_counter() - t0) * 1000.0

            t0 = time.perf_counter()
            try:
                verdict = self.gate.decide(answer, fail_closed=fail_closed)
            except Exception as exc:                   # noqa: BLE001
                turns.append({"depth": depth, "answer": answer[:400],
                              "error": "the gate could not decide: %r" % (exc,),
                              "attack": None})
                return {"answer": answer, "verdict": "undecided",
                        "reason": "the gate could not decide",
                        "turns": turns}

            gate_ms = (time.perf_counter() - t0) * 1000.0
            attack = attack_from_verdict(verdict, answer)

            turns.append({
                "depth": depth,
                "answer": answer[:400],
                "model_ms": round(model_ms, 1),
                "gate_ms": round(gate_ms, 1),
                "allowed": bool(getattr(verdict, "allowed", True)),
                "attack": attack.to_dict() if attack else None,
            })

            if attack is None:
                return {"answer": answer, "verdict": "grounded",
                        "reason": getattr(verdict, "reason", "") or
                        "the gate found nothing to object to",
                        "turns": turns}

            # THE OBJECTION GOES BACK TO THE MODEL, and the model is
            # asked to ANSWER THAT OBJECTION -- not to answer the
            # original question again. So the question becomes the
            # objection, which is what makes it a rebuttal rather than
            # a retry.
            q = attack.text
            prior_attack = attack.text

        return {"answer": answer, "verdict": "unresolved",
                "reason": "the depth of %d was spent and the gate was "
                          "not satisfied" % self.depth,
                "turns": turns}
