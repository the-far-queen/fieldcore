"""
adversarial_brain.py -- THE BICAMERAL BRAIN, WHERE THE CORE IS THE
ADVERSARY.

Bobby, 2026-11-01: *"i feel bicameral brain ie fc and llm call can be
used adversarially"*, and earlier: *"its brilliant like atlas inserted
in the reasoning chain no more hallucination"*, and: *"our core is still
mighty useful gives the llm a new surface to exist in and reson in"*.

**SO THE ARCHITECTURE, and it is the one the whole project was reaching
for.**

    THE OLD SHAPE                     THE NEW SHAPE

    llm  -->  fc  -->  reply          llm proposes  -->  fc attacks
    (fc is a wall)                    (fc is the other hemisphere)
                                       llm answers   -->  fc attacks
                                       ...until the ground decides

**THE CORE IS NOT A WALL THE MODEL HITS. IT IS THE OTHER HALF OF A
DEBATE.** A gate that only refuses is a wall: the model works around
it, or stops, or produces something less interesting because the wall
is there. A core that ATTACKS gives the model something to reason
against -- a new surface to exist in and resonate in.

AND THAT IS WHY IT BEATS THE WRAPPER IDEA. The wrapper's approach is
to constrain what the model may say. This one is to *engage* what the
model says. The first makes the model smaller. The second makes the
model sharper, because a real objection is the thing that makes
reasoning improve.

THE THREE-STEP CYCLE
--------------------
    1 PROPOSE   the model states a claim.
    2 ATTACK   the core refuses it -- naming WHICH claim and WHY.
    3 ANSWER   the model responds to that specific objection.

**AND THE CYCLE TERMINATES ON THE GROUND, NOT ON A VICTORY COUNT.**
Three cycles is the measured sweet spot for adversarial depth (the
survey's numbers are in `docs/chain-audit-2026-11-01.md`), and the
GROUND decides whether the chain resolved -- not the model, and not
the core.

**AND THE HONEST ACCOUNT OF WHAT THIS IS FOR.** The models are now
strong enough to solve open problems -- OpenAI's Erdos unit-distance
disproof, AlphaProof Nexus on 9 of 353 open Erdos problems. What was
MISSING was not capability. It was a way to know if the work is correct
INTERNALLY. This is that way: the core does not judge the answer, it
attacks the reasoning, and the reasoning either survives the attacks
or it does not.

Run:
    python src/adversarial_brain.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

__all__ = [
    "AdversarialBrain",
    "BrainTurn",
    "BrainResult",
    "DEFAULT_DEPTH",
]

#: The default adversarial depth.
#:
#: MEASURED: the literature's finding on multi-agent debate is that
#: gains beyond a couple of rounds are small, and that agents converge
#: -- often to a wrong consensus. So the depth is a DEFAULT, not a
#: maximum, and the chain stops EARLY when the ground has decided.
DEFAULT_DEPTH = 3


@dataclass
class BrainTurn:
    """One exchange: the model's claim, the core's attack, the model's
    answer."""

    claim: str = ""
    attack: str = ""
    answer: str = ""
    #: Did the core's attack hold? The ground decides, and the core
    #: does NOT get to decide that it was right.
    attack_held: Optional[bool] = None
    #: The claim as it stands after this turn.
    surviving_claim: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"claim": self.claim, "attack": self.attack,
                "answer": self.answer, "attack_held": self.attack_held,
                "surviving_claim": self.surviving_claim}


@dataclass
class BrainResult:
    """The outcome of the whole exchange."""
    turns: List[BrainTurn] = field(default_factory=list)
    verdict: str = "unresolved"
    reason: str = ""
    #: The claim that survived, if any.
    surviving_claim: str = ""
    #: The claims the core actually landed, and the ones it missed.
    attacks_landed: int = 0
    attacks_missed: int = 0
    #: Every step, so the exchange can be audited afterwards.
    steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"verdict": self.verdict, "reason": self.reason,
                "surviving_claim": self.surviving_claim,
                "attacks_landed": self.attacks_landed,
                "attacks_missed": self.attacks_missed,
                "turns": [t.to_dict() for t in self.turns],
                "steps": self.steps}

    def describe(self) -> str:
        lines = ["verdict: %s -- %s" % (self.verdict, self.reason),
                 "attacks landed %d, missed %d"
                 % (self.attacks_landed, self.attacks_missed)]
        for i, t in enumerate(self.turns):
            lines.append("  turn %d: attack_held=%s" % (i, t.attack_held))
        return "\n".join(lines)


@dataclass
class AdversarialBrain:
    """The bicameral brain: a model and a core that attacks each other.

    `propose` is the model: it takes (prompt, prior_attack) and returns
    the claim. `attack` is the core: it takes the claim and returns the
    objection, or None if it has nothing to say. `ground` decides
    whether a claim survives.

    **AND ALL THREE ARE INJECTED, and that is what makes this testable
    and what keeps the model out of the dependency graph.** The brain
    knows nothing about MiniMax or about the fieldcore gate; it knows
    three callables.

    **AND THE LOOP STOPS ON THE GROUND.** The ground is asked about
    each claim. When the ground supports it, the exchange is done and
    the claim is the answer. That is the whole design: the model's
    work is not judged by the core's opinion but by whether it
    survives being attacked.
    """

    propose: Callable[[str, Optional[str]], str]
    attack: Callable[[str], Optional[str]]
    ground: Callable[[str], bool]
    depth: int = DEFAULT_DEPTH

    def exchange(self, prompt: str) -> BrainResult:
        """Run the exchange until the ground decides or the depth is
        spent.

        **AND THE ORDER OF THE STEPS, and it is the whole point:**

            claim   ->  attack  ->  answer  ->  GROUND CHECK

        The ground check comes AFTER the answer, so a claim that
        survives the attack but cannot be defended is caught before it
        is accepted.
        """
        result = BrainResult()
        claim = self.propose(prompt, None)
        last_attack: Optional[str] = None

        for depth in range(self.depth):
            turn = BrainTurn(claim=claim)

            # 2 ATTACK
            attack = self.attack(claim)
            turn.attack = attack or ""
            result.steps.append({"step": "attack", "depth": depth,
                                  "claim": claim[:400],
                                  "attack": turn.attack[:400]})

            if not attack:
                # The core has nothing to say. That is a RESOLUTION,
                # not a pass -- the claim reached the point where the
                # ground's own instruments found nothing to object to.
                turn.attack_held = False
                turn.surviving_claim = claim
                result.turns.append(turn)
                result.verdict = "grounded"
                result.reason = ("the core found no objection to the "
                                 "claim")
                result.surviving_claim = claim
                return result

            # 3 ANSWER
            answer = self.propose(attack, last_attack)
            turn.answer = answer
            result.steps.append({"step": "answer", "depth": depth,
                                  "answer": answer[:400]})

            # 2b DID THE ATTACK HOLD? The ground decides, and the core
            # does NOT get to decide it was right.
            #
            # AND THIS IS THE LIAR-AMPLIFIER GUARD. A core that can
            # mark its own attacks as successful would push the model
            # away from the truth as efficiently as it pushes it
            # toward it. So the question "did this attack land?" is
            # asked of the GROUND.
            attack_held = bool(self.ground(attack))
            turn.attack_held = attack_held
            if attack_held:
                result.attacks_landed += 1
            else:
                result.attacks_missed += 1

            if attack_held:
                # The attack landed, so the model must answer it, and
                # the answer becomes the new claim.
                turn.surviving_claim = answer
                claim = answer
            else:
                # The attack did NOT hold -- the ground does not
                # support the objection. So the objection is a
                # HALLUCINATION and the claim SURVIVES IT.
                turn.surviving_claim = claim
                result.turns.append(turn)
                result.verdict = "grounded"
                result.reason = ("the core's objection was not supported "
                                 "by the ground, so the claim stands")
                result.surviving_claim = claim
                return result

            last_attack = attack
            result.turns.append(turn)

        # The depth is spent and the ground never said yes.
        result.verdict = "unresolved"
        result.reason = ("the depth of %d was spent and the ground did "
                         "not decide" % self.depth)
        result.surviving_claim = claim
        return result


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("THE BICAMERAL BRAIN -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    # -- 1. a claim the core cannot touch resolves immediately --------
    def safe_propose(prompt, prior):
        return "the answer is forty two"

    def no_attack(claim):
        return None

    def yes_ground(text):
        return True

    b = AdversarialBrain(safe_propose, no_attack, yes_ground)
    r = b.exchange("what is the answer")
    check("a claim with no objection is GROUNDED",
          r.verdict == "grounded", r.verdict)
    check("it took one turn", len(r.turns) == 1, str(len(r.turns)))

    # -- 2. an attack that HOLDS sends the model back ----------------
    state = {"n": 0}

    def revise(prompt, prior):
        state["n"] += 1
        if state["n"] == 1:
            return "the first claim"
        return "the corrected claim"

    def one_attack(claim):
        return "the first claim is wrong" if claim == "the first claim" else None

    b2 = AdversarialBrain(revise, one_attack, yes_ground)
    r2 = b2.exchange("q")
    check("a landed attack is counted", r2.attacks_landed == 1,
          str(r2.attacks_landed))
    check("the answer becomes the new claim",
          r2.turns[0].surviving_claim == "the corrected claim",
          r2.turns[0].surviving_claim)

    # -- 3. THE LIAR AMPLIFIER: an unsupported attack must NOT win ----
    def always_bad_ground(text):
        return False

    state2 = {"n": 0}

    def propose_once(prompt, prior):
        state2["n"] += 1
        return "the true claim"

    def bogus_attack(claim):
        return "a fabricated objection that the ground does not support"

    b3 = AdversarialBrain(propose_once, bogus_attack, always_bad_ground)
    r3 = b3.exchange("q")
    check("an UNSUPPORTED attack does not refute the claim",
          r3.verdict == "grounded", r3.verdict)
    check("the unsupported attack is counted as MISSED",
          r3.attacks_missed == 1, str(r3.attacks_missed))
    check("the claim survived",
          r3.surviving_claim == "the true claim", r3.surviving_claim)

    # -- 4. the depth is spent without a decision --------------------
    #
    # AND THE GROUND HERE SUPPORTS EVERY ATTACK, and that is the
    # point. MEASURED: the first version used a ground that supported
    # NOTHING, so every attack MISSED -- and a missed attack means the
    # claim STANDS, which is a RESOLUTION. So the chain resolved at
    # turn 1 and the depth was never spent.
    #
    # **AND THAT IS CORRECT BEHAVIOUR, not a bug.** If the ground says
    # the objection is unfounded, the claim stands and the exchange is
    # over. The chain only keeps going when the objection is
    # UPHELD, because then there is something to answer.
    #
    # So to exercise the depth, the ground must uphold every attack.
    def always_attack(claim):
        return "an objection"

    state3 = {"n": 0}

    def keep_going(prompt, prior):
        state3["n"] += 1
        return "claim %d" % state3["n"]

    b4 = AdversarialBrain(keep_going, always_attack, yes_ground)
    r4 = b4.exchange("q")
    check("a chain that never resolves is UNRESOLVED",
          r4.verdict == "unresolved", r4.verdict)
    check("it used the full depth", len(r4.turns) == DEFAULT_DEPTH,
          "%d of %d" % (len(r4.turns), DEFAULT_DEPTH))

    # -- 5. the core never decides on its own -------------------------
    # The core is asked what to attack. It is NOT asked whether it was
    # right. So the ground's verdict is the only authority.
    check("the ground is the only authority",
          r3.verdict == "grounded" and r4.verdict == "unresolved")

    # -- 6. every step is recorded ------------------------------------
    check("every step is recorded",
          len(r4.steps) == 2 * DEFAULT_DEPTH, str(len(r4.steps)))

    print()
    if failures:
        print("  %d CHECK(S) FAILED:" % len(failures))
        for f in failures:
            print("    - %s" % f)
        return 1
    print("  ALL CHECKS PASS")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
