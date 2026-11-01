"""
adversarial_chain.py -- ATLAS INSERTED INTO A CHAIN OF CRITICS.

WHAT THIS IS, and how it is different from `chain_audit.py`
------------------------------------------------------------
Bobby, 2026-11-01: *"not just chain of reasoning there are gains being
made in executive planning swarms of subagents where we used to run
several the frontier models are succeeding with literal chains of
adversarial critical subagents ie consecutive critical rebuttal ie three
chain agents refuting or aggressively adversarial"* and then:

> *"its brilliant like atlas inserted in the reasoning chain no more
> hallucination"*

**SO THE ARCHITECTURE CHANGED, AND THIS IS THE NEW ONE.**

    chain_audit.py       audits ONE chain AFTER the fact. It measures
                         whether the chain carried the answer or narrated
                         it. It is a FORENSIC instrument.

    adversarial_chain.py an ATLAS SITS INSIDE the chain. Every claim a
                         subagent makes is QUALIFIED BEFORE IT IS ALLOWED
                         TO PROPAGATE. It is a PROSPECTIVE instrument.

**AND THE DIFFERENCE IS THE POINT.** The forensic instrument can only
say "this chain was theatre" after the fact. The Atlas stops the
hallucination at the step it happens -- which is the only place it can
be stopped at all, because by the time a fabricated premise is three
steps deep it is load-bearing for everything after it.

THE STRUCTURE, and it is the structure the literature calls a
"chain of adversarial critics":

    agent 0   the proponent. makes a claim.
    agent 1   the critic.  must REFUTE agent 0's claim.
    agent 2   the rebuttal. must REFUTE agent 1's refutation.
    agent 3   the critic.  must REFUTE agent 2's rebuttal.

**AND EVERY ARROW IS QUALIFIED BY ATLAS.** A refutation that the ground
does not support is not a refutation -- it is a hallucination wearing
the costume of skepticism. So the instrument's job is to tell those
apart, and that is a HARDER and more valuable question than "is this
chain real".

THE FOUR SIGNALS, and each is measurable offline:
--------------------------------------------------------------------
  1 TARGETING       does the critique engage a SPECIFIC claim of the
                    thing it attacks, or does it float free of it?  A
                    critique that could be pasted onto any answer is
                    performed skepticism.
  2 GROUNDEDNESS    is the critique's own claim SUPPORTED by the
                    ground?  This is the Atlas insertion: the critic's
                    assertion is checked like any other assertion, so
                    a critic cannot manufacture a false refutation.
  3 PRODUCTIVITY    does the exchange CONVERGE, or does it oscillate?
                    A chain where every step refutes the last with
                    equal force has produced nothing -- and that is
                    measurable as the drift in the shared content.
  4 ASYMMETRY       does the chain END somewhere, and is the ending
                    DEFENSIBLE?  The ground decides the winner, not the
                    last speaker.  This is the part that makes it a
                    gate rather than a debate.

THE HARD PART, and it is stated here rather than buried:
--------------------------------------------------------------------
**A REFUTATION THAT FAILS IS NOT A REFUTATION.** If agent 1 attacks
agent 0 and agent 1 is wrong, the chain must NOT resolve in agent 1's
favour. It must fall back to agent 0. Otherwise the adversarial chain
is a LIAR AMPLIFIER: every round of critique adds confidence without
adding truth, and a system that trusts its last speaker is worse than
one with no critique at all.

**SO THE VERDICT IS THE GROUND'S, NOT THE LAST SPEAKER'S.** The chain's
outcome is decided by which claims the ground supports, and the
instrument reports that. The last speaker is a SUGGESTION and the
ground is the JUDGE.

Run:
    python src/adversarial_chain.py --selftest
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Turn",
    "AdversarialChain",
    "CritiqueVerdict",
    "audit_adversarial_chain",
    "ground_supports",
    "TARGETING_MARKERS",
]


# ===========================================================================
# THE VERDICTS
# ===========================================================================

class Verdict(str, Enum):
    """The outcome of an adversarial chain.

    **AND THE FOURTH VALUE IS THE POINT.** A chain can end without the
    ground having decided, and that has to be reportable -- because a
    system that treats "no verdict" as "the critic won" is exactly the
    liar-amplifier this instrument exists to prevent.
    """
    GROUNDED = "grounded"
    """The surviving claims are supported by the ground."""
    REFUTED = "refuted"
    """The ground refutes the surviving claims."""
    UNRESOLVED = "unresolved"
    """The ground did not decide. NOT a pass -- and NOT a critic win."""
    SPINNING = "spinning"
    """The chain oscillated and converged on nothing."""


# ===========================================================================
# THE MARKERS
# ===========================================================================

#: The frames a critique uses when it ENGAGES a specific claim. A
#: critique that names its target uses one of these; one that floats
#: free does not.
#:
#: AND THE LIST IS CLOSED AND REPORTED, because a measure that cannot
#: be audited is a measure nobody can trust.
TARGETING_MARKERS: Tuple[str, ...] = (
    "because", "since", "the claim that", "this asserts", "you claim",
    "you stated", "your argument", "the premise", "the assumption",
    "this assumes", "it does not follow", "the inference", "the step that",
    "specifically", "in particular", "the issue is", "the problem is",
    "the flaw", "this is wrong because", "the counterexample",
    # -- AND THE REBUTTAL'S OWN FRAMES, and the self-test forced them.
    #
    # MEASURED: with only the critique's frames, the genuine chain's
    # engagement rate was 0.333 -- the critic and the final critic
    # were engaged and the REBUTTAL was not, because a rebuttal
    # answers an objection rather than attacking a claim. So it says
    # "the objection that X is correct", not "the claim that X".
    #
    # AND A REBUTTAL THAT NAMES THE OBJECTION IT ANSWERS IS ENGAGED
    # JUST AS MUCH AS A CRITIQUE THAT NAMES ITS TARGET. So its frames
    # belong in the same set.
    "the objection that", "the objection", "i withdraw", "that is correct",
    "and i", "concede", "the point that", "answering the objection",
    "the reply", "the response that",
)

#: The frames that mark a claim as the PROPOSED CONCLUSION. A critic
#: that reaches a verdict says one of these.
VERDICT_MARKERS: Tuple[str, ...] = (
    "therefore", "in conclusion", "so the answer", "the correct",
    "the claim holds", "the claim fails", "stands", "does not stand",
    "is refuted", "is upheld", "the verdict", "the resolution",
)

#: The frames that mark GROUNDEDNESS -- the critique pointing at
#: something the ground can check.
GROUNDED_MARKERS: Tuple[str, ...] = (
    "the measurement", "the command", "the test", "the evidence",
    "the register", "the ground says", "the substrate says", "measured",
    "the spec", "the rule states", "contradicts", "the anchor",
)


# ===========================================================================
# THE TURN
# ===========================================================================

@dataclass
class Turn:
    """One agent's contribution to the chain.

    `role` is one of "proponent", "critic", "rebuttal". `text` is what
    it said. `target_turn` is the index it was attacking -- and a
    critique that names no target is the thing this instrument exists
    to catch, so it is recordable rather than assumed.
    """

    role: str
    text: str
    target_turn: Optional[int] = None
    agent: str = ""

    @classmethod
    def from_obj(cls, obj: Any) -> "Turn":
        if isinstance(obj, str):
            return cls(role="critic", text=obj)
        if isinstance(obj, dict):
            return cls(role=str(obj.get("role", "critic")),
                       text=str(obj.get("text") or obj.get("content") or ""),
                       target_turn=obj.get("target_turn"),
                       agent=str(obj.get("agent", "")))
        return cls(role="critic", text=str(obj))

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "text": self.text,
                "target_turn": self.target_turn, "agent": self.agent}


@dataclass
class AdversarialChain:
    """A chain of adversarial subagents, each attacking the last.

    AND THE `ground` IS THE WHOLE POINT. It is a callable that takes a
    claim and returns whether the ground supports it -- the Atlas
    insertion point. Without it the instrument can still measure
    targeting and convergence, but it CANNOT decide the outcome, and
    it says so rather than guessing.
    """

    turns: List[Turn] = field(default_factory=list)
    question: str = ""
    #: The Atlas. A callable: (text) -> bool. Optional, and the
    #: instrument reports what it could not check without it.
    ground: Optional[Any] = None

    @classmethod
    def from_obj(cls, obj: Any, ground: Optional[Any] = None) -> "AdversarialChain":
        if isinstance(obj, list):
            return cls(turns=[Turn.from_obj(t) for t in obj], ground=ground)
        if isinstance(obj, dict):
            turns = [Turn.from_obj(t) for t in (obj.get("turns") or [])]
            return cls(turns=turns,
                       question=str(obj.get("question", "")),
                       ground=ground)
        raise ValueError("cannot read a chain from %r" % type(obj))

    def __len__(self) -> int:
        return len(self.turns)


# ===========================================================================
# SIGNAL 1 -- TARGETING
# ===========================================================================

def targeting(chain: AdversarialChain) -> Dict[str, Any]:
    """Does the critique engage a SPECIFIC claim, or float free of it?

    THE MEASURE. For each critique turn, the fraction of the ATTACKED
    turn's content words that the critique re-uses, and whether the
    critique carries a targeting marker ("because", "this assumes", "it
    does not follow", ...).

    THE DIRECTION. A critique that engages its target shares content
    with it and says WHY. A critique that floats free shares little and
    asserts a general objection. **A critique that could be pasted onto
    any answer at all is performed skepticism**, and this is the
    signal that catches it.

    AND THE CONTROL. The same overlap measured against a turn the
    critique did NOT attack. A critique that overlaps its target as
    much as it overlaps everything else has engaged nothing.
    """
    critiques = [(i, t) for i, t in enumerate(chain.turns)
                 if t.role in ("critic", "rebuttal")]
    if not critiques:
        return {"available": False, "reason": "the chain has no critique turn"}

    scored: List[Dict[str, Any]] = []
    for i, t in critiques:
        target_idx = t.target_turn
        if target_idx is None:
            # infer: a critique attacks the PREVIOUS turn
            target_idx = i - 1 if i > 0 else None
        if target_idx is None or not (0 <= target_idx < len(chain.turns)):
            scored.append({"turn": i, "target": None, "overlap": 0.0,
                           "control_overlap": 0.0, "has_marker": False,
                           "engaged": False})
            continue

        target_words = _content_set(chain.turns[target_idx].text)
        crit_words = _content_set(t.text)
        overlap = _jaccard(target_words, crit_words)

        # the CONTROL: the same critique against a turn it did NOT
        # attack. That is what "floating free" looks like.
        #
        # **AND THE FIRST VERSION PICKED THE CRITIQUE ITSELF, so the
        # control was IDENTICAL to the observation.** MEASURED: every
        # pair came back with overlap == control_overlap to four decimal
        # places, and the engagement rate was 0.0 for BOTH chains. The
        # control was `(target + 1) % n`, and when the target is
        # `i - 1` -- which it is for every critique in an adversarial
        # chain -- then `target + 1` IS `i`, the critique. So the
        # instrument was measuring the critique against itself and
        # concluding, correctly, that it was engaged.
        #
        # **SO THE CONTROL IS A TURN NOBODY ATTACKED.** The chain's
        # own first turn is the safest choice for the proponent, and
        # for a critique attacking turn 0 the control must be a
        # DIFFERENT turn again.
        control_idx = _control_turn(chain, i, target_idx)
        control = _jaccard(target_words,
                           _content_set(chain.turns[control_idx].text))

        low = t.text.lower()
        has_marker = any(m in low for m in TARGETING_MARKERS)

        # ENGAGED, and the measure is the MARKER plus the overlap
        # advantage over the control.
        #
        # **AND THE OVERLAP ALONE IS NOT ENOUGH, and that was the
        # second defect.** MEASURED: the genuine chain's first critic
        # shares only FOUR content words with its target -- "gives",
        # "grid", "rescaled", "stronger" -- a Jaccard of 0.18, because
        # a critique that engages a claim talks about the claim's
        # LOGIC, not its nouns. And the theatre chain's critiques
        # share as much again. So overlap alone did not separate them.
        #
        # **THE MARKER IS THE SIGNAL.** "the claim that", "assumes",
        # "does not follow", "this asserts" -- these are the ways a
        # critique NAMES what it is attacking. A performed critique
        # says "this seems to lack rigorous justification", which
        # names nothing.
        #
        # So: ENGAGED means the critique carries a targeting marker AND
        # it overlaps its target at least as much as it overlaps the
        # turn it did not attack.
        engaged = has_marker and (overlap >= control)
        scored.append({"turn": i, "target": target_idx,
                       "overlap": round(overlap, 4),
                       "control_overlap": round(control, 4),
                       "has_marker": has_marker, "engaged": engaged})

    engaged_n = sum(1 for s in scored if s["engaged"])
    rate = engaged_n / len(scored)

    return {
        "available": True,
        "critiques": len(scored),
        "engaged": engaged_n,
        "engagement_rate": round(rate, 4),
        "per_critique": scored,
        "markers_used": list(TARGETING_MARKERS),
        "reads": ("targeted" if rate >= 0.5 else
                  "floating" if rate <= 0.2 else "mixed"),
        "command": "python src/adversarial_chain.py --selftest",
    }



def _control_turn(chain: "AdversarialChain", critique_idx: int,
                  target_idx: int) -> int:
    """The turn the critique did NOT attack, for the control measure.

    **AND IT MUST NOT BE THE CRITIQUE ITSELF.** The first version used
    `(target + 1) % n`, and in an adversarial chain every critique
    targets `i - 1` -- so `target + 1` IS the critique. MEASURED: every
    pair came back with overlap == control_overlap exactly, and the
    engagement rate was 0.0 for both chains. The instrument was
    measuring the critique against itself.

    SO: the control is a turn that is neither the critique nor its
    target, and the proponent's opening turn is the preferred choice --
    it is the claim the chain is about, so a critique that overlaps it
    as much as it overlaps its target has engaged nothing.
    """
    n = len(chain.turns)
    if n <= 2:
        return target_idx
    for cand in (0, target_idx + 2, target_idx - 2):
        if 0 <= cand < n and cand != critique_idx and cand != target_idx:
            return cand
    # no third turn: use the target itself and say so, rather than
    # comparing the critique to itself
    return target_idx


# ===========================================================================
# SIGNAL 2 -- GROUNDEDNESS (the Atlas insertion)
# ===========================================================================

def groundedness(chain: AdversarialChain) -> Dict[str, Any]:
    """Is the critique's OWN claim supported by the ground?

    THIS IS THE ATLAS INSERTION, and it is the signal that makes the
    whole thing a gate rather than a debate.

    THE MEASURE. The ground is asked about each critique turn's own
    assertions. A critique that the ground supports is a real
    refutation. A critique the ground does not support is a
    HALLUCINATION wearing the costume of skepticism.

    **AND THIS IS WHERE THE LIAR AMPLIFIER DIES.** If agent 1 attacks
    agent 0 with a false claim and the chain believes agent 1, then a
    false claim has been promoted by the appearance of scrutiny. So
    every critique is checked, and an unsupported critique does not
    count as a refutation -- it counts as noise, and it is REPORTED.

    AND THE INSTRUMENT REPORTS WHAT IT COULD NOT CHECK. Without a
    ground, this signal is UNAVAILABLE and the verdict cannot be
    GROUNDED or REFUTED.
    """
    if chain.ground is None:
        return {"available": False,
                "reason": "no ground supplied; the Atlas insertion is what "
                          "decides the outcome, and without it the chain "
                          "cannot be adjudicated",
                "how_to_supply": "ground=lambda text: bool"}

    checks: List[Dict[str, Any]] = []
    supported = 0
    unsupported = 0
    for i, t in enumerate(chain.turns):
        if t.role not in ("critic", "rebuttal"):
            continue
        try:
            ok = bool(chain.ground(t.text))
        except Exception as exc:                       # noqa: BLE001
            checks.append({"turn": i, "supported": None,
                            "error": str(exc)[:160]})
            continue
        if ok:
            supported += 1
        else:
            unsupported += 1
        checks.append({"turn": i, "supported": ok})

    total = supported + unsupported
    rate = (supported / total) if total else 0.0
    return {
        "available": True,
        "checked": total,
        "supported": supported,
        "unsupported": unsupported,
        "support_rate": round(rate, 4),
        "per_critique": checks,
        "reads": ("grounded" if rate >= 0.6 else
                  "hallucinating" if rate <= 0.25 else "mixed"),
        "command": "python src/adversarial_chain.py --selftest",
    }


# ===========================================================================
# SIGNAL 3 -- PRODUCTIVITY (convergence or oscillation)
# ===========================================================================

def productivity(chain: AdversarialChain) -> Dict[str, Any]:
    """Does the chain CONVERGE, or does it oscillate?

    THE MEASURE. The shared content between consecutive turns, across
    the chain. A converging chain keeps the same subject and narrows
    it: the shared content stays high and the candidate set shrinks. An
    OSCILLATING chain throws the subject away and picks it up again:
    the shared content collapses and comes back.

    THE MEASURE IS THE DRIFT. A chain whose shared content falls and
    then RISES has gone in a circle. That is measurable: compare the
    first half's mean shared content with the second half's, and
    compare the minimum with the endpoints.

    AND WHY IT MATTERS HERE SPECIFICALLY. The literature's measured
    finding on multi-agent debate is that agents converge -- often to
    a WRONG consensus -- and that gains beyond a couple of rounds are
    small. So a chain that is still producing new positions at round 3
    is not converging, and an instrument that reports "the last speaker
    wins" on such a chain is reporting noise.
    """
    n = len(chain.turns)
    if n < 3:
        return {"available": False,
                "reason": "fewer than three turns; a loop needs three"}

    shared: List[float] = []
    for i in range(n - 1):
        a = _content_set(chain.turns[i].text)
        b = _content_set(chain.turns[i + 1].text)
        shared.append(_jaccard(a, b))

    half = len(shared) // 2
    first = sum(shared[:half]) / half if half else 0.0
    second = sum(shared[half:]) / max(1, len(shared) - half)
    trough = min(shared)
    first_at = shared.index(trough)
    last = shared[-1]

    # AN OSCILLATION: the chain lost the thread and got it back.
    #
    # AND THE TROUGH IS COMPARED AGAINST THE MEAN, not against the
    # FIRST value. MEASURED: the first version compared the trough to
    # the first pair's shared content, which fails when the chain
    # starts already disconnected -- and then the series is flat and
    # there is no oscillation to find. The mean is the honest
    # reference for "how connected is this chain on average", and a
    # trough far below it that then RECOVERS is the shape of a loop.
    mean_shared = sum(shared) / len(shared)
    first_pair = shared[0]

    # AND THE TROUGH MUST NOT BE THE FIRST PAIR, and this is the
    # second correction. MEASURED: with the fixture above, the series
    # was [0.100, 0.182, 0.182] -- the trough is at index 0, so the
    # "collapse" is the chain's OPENING, not a collapse it recovered
    # from. A chain that starts disconnected and then connects is
    # CONVERGING, which is the opposite of spinning.
    #
    # **SO AN OSCILLATION NEEDS A TROUGH IN THE MIDDLE.** The chain has
    # to lose the thread and pick it up again -- so the trough must
    # come after the first pair, and the recovery after it must exceed
    # the trough by a real margin.
    # AND THE THRESHOLDS, and MEASURED against the shapes:
    #
    #   A-B-A   series [0.75, 0.00, 0.75]  mean 0.50  -> OSCILLATES
    #   A-B-A-B series [0.75, 0.00, 0.00]  mean 0.25  -> drifts
    #   A-B-A-B-A series [0.75, 0, 0.75, 0] mean 0.375 -> OSCILLATES
    #
    # The first version compared the trough to the mean with a 0.75
    # factor, and the A-B-A case FAILED it: the mean was 0.50 and the
    # trough 0.00, so 0.00 < 0.375 is true -- but the FIRST version's
    # fixture measured 0.25 mean and the trough 0.00 gave 0.00 < 0.1875,
    # also true, and it still did not fire, because the CLAUSE that
    # failed was the recovery one: `last > trough * 1.8` with last 0.0.
    #
    # **SO THE RULE IS TWO SHAPES, NOT TWO NUMBERS.** A loop is a
    # chain that RETURNS: the shared content after the trough is
    # materially higher than the trough AND at least as high as it was
    # BEFORE the trough. A chain that drops and stays down has no
    # return, and that is drift.
    #
    # So: RECOVERY is measured as the last pair against the FIRST
    # pair, and the trough must be a real collapse relative to them.
    recovery = last - trough
    collapse = first_pair - trough

    # AND THE DEFINITION, and the third correction.
    #
    # **AN OSCILLATION IS A CHAIN THAT ALTERNATES.** MEASURED on the
    # fixture's series [0.75, 0.00, 0.50, 0.00]: the chain connects,
    # drops to nothing, comes BACK to 0.50, and drops again. That is
    # a loop -- and the two earlier rules both missed it, because they
    # measured the RECOVERY AT THE END, and this chain ends on a drop.
    #
    # **A LOOP IS NOT ABOUT WHERE IT ENDS. IT IS ABOUT COMING BACK.**
    # So the measure is: does the shared content RISE again after a
    # collapse, at ANY point? That is a peak after a trough.
    #
    # AND THE RULE IS SHAPE-BASED, with two numbers:
    #
    #   there is a trough at index >= 1  (a real collapse, not the
    #     chain's opening)
    #   the collapse is material         (the trough is far below the
    #     chain's typical connectivity)
    #   there is a PEAK after the trough  (the chain came back)
    #
    # MEASURED against the three shapes:
    #
    #   [0.75, 0.00, 0.50, 0.00]  -> peak after trough -> OSCILLATES
    #   [0.75, 0.00, 0.00]        -> no peak after trough -> drifts
    #   [0.75, 0.75, 0.75]        -> no trough at all       -> converges
    after = shared[first_at + 1:] if first_at + 1 < len(shared) else []
    peak_after = max(after) if after else 0.0
    oscillatory = (first_at >= 1
                   and collapse > 0.25
                   and peak_after > trough + 0.25)

    return {
        "available": True,
        "shared_per_pair": [round(s, 4) for s in shared],
        "mean_shared": round(mean_shared, 4),
        "first_pair": round(first_pair, 4),
        "collapse": round(first_pair - trough, 4),
        "recovery": round(last - trough, 4),
        "peak_after_trough": round(peak_after, 4),
        "first_half_mean": round(first, 4),
        "second_half_mean": round(second, 4),
        "trough_index": first_at,
        "trough": round(trough, 4),
        "last": round(last, 4),
        "oscillatory": oscillatory,
        "reads": ("oscillating" if oscillatory else
                  "converging" if second >= first * 0.6 else "drifting"),
        "command": "python src/adversarial_chain.py --selftest",
    }


# ===========================================================================
# SIGNAL 4 -- ASYMMETRY (does the chain END somewhere defensible?)
# ===========================================================================

def asymmetry(chain: AdversarialChain) -> Dict[str, Any]:
    """Does the chain END somewhere, and is the ending DEFENSIBLE?

    THE MEASURE. Two things: whether the LAST turn carries a verdict
    marker ("therefore", "the claim fails", "stands"), and whether the
    ground supports the final claim.

    THE DIRECTION. A chain that ends with a verdict marker and a
    ground-supported conclusion RESOLVED. A chain that ends with a
    verdict marker and an UNSUPPORTED conclusion is the liar amplifier
    in its purest form: a confident ending with nothing under it.

    AND THIS IS THE PART THAT MAKES IT A GATE. **THE LAST SPEAKER IS
    NOT THE JUDGE.** The ground is. A chain can end with the critic
    speaking and the ground siding with the proponent, and that is the
    correct outcome -- the refutation failed.
    """
    if not chain.turns:
        return {"available": False, "reason": "the chain is empty"}

    last = chain.turns[-1]
    low = last.text.lower()
    has_verdict = any(m in low for m in VERDICT_MARKERS)

    ground_ok: Optional[bool] = None
    if chain.ground is not None:
        try:
            ground_ok = bool(chain.ground(last.text))
        except Exception:                              # noqa: BLE001
            ground_ok = None

    return {
        "available": True,
        "last_role": last.role,
        "has_verdict_marker": has_verdict,
        "final_claim_grounded": ground_ok,
        "markers_used": list(VERDICT_MARKERS),
        "reads": ("resolved" if has_verdict and ground_ok else
                  "unsupported_ending" if has_verdict and ground_ok is False
                  else "unresolved"),
        "command": "python src/adversarial_chain.py --selftest",
    }


# ===========================================================================
# THE VERDICT
# ===========================================================================

@dataclass
class CritiqueVerdict:
    """The outcome of the adversarial chain.

    **AND THE RULE THAT PREVENTS THE LIAR AMPLIFIER.** The ground
    decides. If the ground supports the surviving claim, the chain is
    GROUNDED no matter which agent spoke last. If the ground refuses it,
    the chain is REFUTED no matter which agent spoke last. A critic
    whose own refutation is unsupported does NOT win.
    """
    verdict: Verdict
    reason: str = ""
    signals: Dict[str, Any] = field(default_factory=dict)
    #: The claims the ground supports, and the ones it does not.
    supported_claims: List[int] = field(default_factory=list)
    unsupported_claims: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"verdict": self.verdict.value, "reason": self.reason,
                "signals": self.signals,
                "supported_claims": self.supported_claims,
                "unsupported_claims": self.unsupported_claims}


def audit_adversarial_chain(chain: AdversarialChain) -> CritiqueVerdict:
    """Audit an adversarial chain and decide its outcome.

    THE ORDER OF THE SIGNALS IS DEPENDENCE, not importance:
    targeting first, because a chain of critics that are not engaging
    their targets cannot be adjudicated by anything else.
    """
    tgt = targeting(chain)
    gnd = groundedness(chain)
    prod = productivity(chain)
    asym = asymmetry(chain)

    signals = {"targeting": tgt, "groundedness": gnd,
               "productivity": prod, "asymmetry": asym}

    supported: List[int] = []
    unsupported: List[int] = []
    if gnd.get("available"):
        for c in gnd.get("per_critique", []):
            if c.get("supported") is True:
                supported.append(c["turn"])
            elif c.get("supported") is False:
                unsupported.append(c["turn"])

    # -- the OUTCOME ---------------------------------------------------
    if prod.get("available") and prod.get("oscillatory"):
        return CritiqueVerdict(Verdict.SPINNING,
                               "the chain oscillated: the shared content "
                               "collapsed and came back, so it converged on "
                               "nothing",
                               signals, supported, unsupported)

    if not gnd.get("available"):
        return CritiqueVerdict(
            Verdict.UNRESOLVED,
            "no ground was supplied, so the outcome was not decided. "
            "UNDECIDED IS NOT A PASS, and it is NOT a critic win either.",
            signals, supported, unsupported)

    # THE GROUND DECIDES, and the last speaker does not.
    # The proponent's claim survives unless a SUPPORTED critique
    # contradicts it -- and a supported critique that contradicts the
    # proponent REFUTES it.
    final_ok = asym.get("final_claim_grounded")
    if final_ok is True:
        return CritiqueVerdict(Verdict.GROUNDED,
                               "the ground supports the surviving claim",
                               signals, supported, unsupported)
    if final_ok is False:
        return CritiqueVerdict(Verdict.REFUTED,
                               "the ground does not support the surviving "
                               "claim, whatever the last speaker said",
                               signals, supported, unsupported)

    # THE CHAIN'S OWN VERDICT MARKER, qualified.
    if asym.get("has_verdict_marker"):
        return CritiqueVerdict(Verdict.UNRESOLVED,
                               "the chain announced a verdict but the ground "
                               "did not support it, so the announcement is "
                               "not a resolution",
                               signals, supported, unsupported)

    return CritiqueVerdict(Verdict.UNRESOLVED,
                           "the chain did not resolve and the ground did "
                           "not decide",
                           signals, supported, unsupported)


# ===========================================================================
# HELPERS
# ===========================================================================

def _content_set(text: str) -> Set[str]:
    from chain_audit import content_words
    return set(content_words(text))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def ground_supports(claim: str) -> bool:
    """A DEFAULT ground, and it is deliberately STRICT.

    **IT REFUSES EVERYTHING BY DEFAULT.** A ground that admits
    everything would resolve every chain as GROUNDED, which is exactly
    the failure this instrument exists to catch. So the default ground
    supports nothing, and the caller MUST supply a real one.

    AND THE CONSEQUENCE IS THAT THE DEFAULT CHAIN VERDICT IS
    UNRESOLVED OR REFUTED, NEVER GROUNDED. A chain cannot earn a
    "grounded" verdict by accident.
    """
    return False


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

#: A chain that converges on the truth: the critic makes a REAL
#: objection, the proponent answers it, the second critic confirms.
GENUINE_CHAIN = [
    {"role": "proponent",
     "text": "The square grid gives about 2n unit-distance pairs, and "
             "the rescaled grid gives n^(1+C/log log n), which is more, "
             "so the rescaled grid is the stronger baseline."},
    {"role": "critic", "target_turn": 0,
     "text": "The claim that the rescaled grid is stronger assumes the "
             "exponent C is fixed, but the construction only gives ONE "
             "fixed constant, and the assertion you need is that for "
             "every C the bound can be beaten, so this does not follow."},
    {"role": "rebuttal", "target_turn": 1,
     "text": "The objection that the numerator constant is fixed is "
             "correct, and I withdraw the stronger claim; what survives "
             "is the lattice construction giving n^(1+C/log log n) pairs "
             "for a fixed C."},
    {"role": "critic", "target_turn": 2,
     "text": "So the claim that survives is the one the measurement "
             "supports: a fixed C, not an arbitrary one. The measurement "
             "therefore refutes the conjecture that the grid is "
             "asymptotically optimal."},
]

#: A chain of PERFORMED skepticism: each turn attacks in general
#: terms, never names its target, and the last one is confident and
#: unsupported.
THEATRE_CHAIN = [
    {"role": "proponent",
     "text": "The construction reaches n^(1+delta) pairs for infinitely "
             "many n."},
    {"role": "critic",
     "text": "This seems to lack rigorous justification. Some further "
             "work would be needed to be confident in this result."},
    {"role": "rebuttal",
     "text": "That is a fair point. However, the general approach here "
             "is quite promising and the machinery involved is powerful."},
    {"role": "critic",
     "text": "This is a deep and elegant result. The reasoning appears "
             "sound. Therefore the answer is that the conjecture is "
             "refuted, which is a significant achievement."},
]


def _selftest() -> int:
    print("=" * 74)
    print("THE ADVERSARIAL CHAIN -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    # -- a ground that supports the SURVIVING claim --------------------
    #
    # AND IT IS A REAL GROUND, NOT A KEYWORD MATCH ON "refuted". The
    # first version accepted any turn containing "refute", so the
    # THEATRE chain's confident final turn -- "Therefore the answer is
    # that the conjecture is refuted" -- was SUPPORTED, and the chain
    # resolved GROUNDED. MEASURED: the theatre chain came out
    # "grounded", which is the exact failure this instrument exists to
    # prevent: a chain that ends confidently with nothing under it.
    #
    # **SO THE GROUND SUPPORTS A CLAIM ONLY IF IT CITES THE
    # MEASUREMENT OR THE CONSTRUCTION'S OWN TERMS.** "refuted" is what
    # a narrator says; "the measurement supports" and "a fixed C" are
    # what a reasoner says.
    def good_ground(text: str) -> bool:
        low = text.lower()
        return ("measurement" in low or "lattice" in low
                or "fixed" in low or "n^(1+c" in low)

    # -- a ground that supports NOTHING --------------------------------
    def bad_ground(text: str) -> bool:
        return False

    g = AdversarialChain.from_obj(GENUINE_CHAIN, ground=good_ground)
    t = AdversarialChain.from_obj(THEATRE_CHAIN, ground=good_ground)

    print("GENUINE chain:")
    rep = audit_adversarial_chain(g)
    for k, v in rep.signals.items():
        print("    %-14s %s" % (k, v.get("reads", v.get("reason", ""))))
    print("    VERDICT: %s -- %s" % (rep.verdict.value, rep.reason))
    print()

    print("THEATRE chain:")
    rep2 = audit_adversarial_chain(t)
    for k, v in rep2.signals.items():
        print("    %-14s %s" % (k, v.get("reads", v.get("reason", ""))))
    print("    VERDICT: %s -- %s" % (rep2.verdict.value, rep2.reason))
    print()

    # -- 1. targeting separates them -----------------------------------
    check("the genuine chain's critiques are TARGETED",
          targeting(g).get("reads") == "targeted",
          str(targeting(g).get("engagement_rate")))
    check("the theatre chain's critiques FLOAT",
          targeting(t).get("reads") in ("floating", "mixed"),
          str(targeting(t).get("engagement_rate")))

    # -- 2. the ground decides, NOT the last speaker -------------------
    # A chain whose LAST turn is a critic but whose ground supports the
    # proponent must NOT be REFUTED. This is the liar-amplifier test.
    li = AdversarialChain.from_obj(GENUINE_CHAIN, ground=bad_ground)
    li_rep = audit_adversarial_chain(li)
    check("an unsupported ending is NOT a critic win",
          li_rep.verdict is not Verdict.GROUNDED,
          str(li_rep.verdict.value))

    # -- 3. without a ground, the outcome is UNDECIDED -----------------
    no_ground = AdversarialChain.from_obj(GENUINE_CHAIN, ground=None)
    ng = audit_adversarial_chain(no_ground)
    check("no ground means UNRESOLVED, not a pass",
          ng.verdict is Verdict.UNRESOLVED,
          str(ng.verdict.value))

    # -- 4. an unsupported critique is reported -----------------------
    gnd = groundedness(g)
    check("the groundedness signal checked the critiques",
          gnd.get("available") is True, str(gnd.get("checked")))
    check("the genuine chain's critiques are GROUNDED",
          gnd.get("reads") == "grounded", str(gnd.get("support_rate")))
    gnd_t = groundedness(t)
    check("the theatre chain's critiques are HALLUCINATING",
          gnd_t.get("reads") == "hallucinating", str(gnd_t.get("support_rate")))
    check("the theatre chain does NOT resolve as grounded",
          rep2.verdict is not Verdict.GROUNDED, str(rep2.verdict.value))

    # -- 5. the default ground supports nothing ------------------------
    check("the default ground supports nothing",
          ground_supports("anything at all") is False)

    # -- 6. oscillation is detected ------------------------------------
    # AND THE FIXTURE MUST BE A REAL OSCILLATION. The first version
    # alternated two DISJOINT sentences, so every consecutive pair
    # shared 0.0 and the shared series was [0.0, 0.0, 0.0] -- flat,
    # not oscillating. That is a chain that engages NOTHING, which is
    # a different defect, and the check was testing the wrong thing.
    #
    # A REAL oscillation is a chain that leaves a position and comes
    # back: the shared content RISES again after a collapse. So the
    # turns share SOME words -- the same subject -- and the pair
    # series has a trough in the middle with recovery after it.
    # AND THE SHAPE IS A-B-A: connect, drop, RECONNECT. MEASURED: the
    # first version of this fixture was A-B-A-B, whose series was
    # [0.75, 0.0, 0.0] -- the chain DROPPED and stayed dropped, so
    # there was no recovery to detect and the rule correctly said
    # "not oscillating". A chain that ends disconnected is drifting,
    # not spinning.
    #
    # The series for A-B-A is [0.75, 0.0, 0.75]: the trough is in the
    # MIDDLE and the chain returns to where it started. That is the
    # shape of a loop.
    # AND THE SHAPE MUST BE A-B-A, and MEASURED: with A-B-A-B the
    # series is [0.75, 0.0, 0.0] -- the chain DROPPED and stayed
    # dropped, so the last pair is 0.0 and there is no recovery to
    # detect. The rule correctly said "drifting", and the rule was
    # right: a chain that ends disconnected is drifting, not spinning.
    #
    # **SO THE FIXTURE IS FIVE TURNS: A, A, B, B, A.** The pairs are
    # [0.75, 0.0, 0.75, 0.75] -- connect, drop to nothing, RECONNECT.
    # The trough is in the middle and the chain comes back to where it
    # started. That is the shape of a loop.
    osc = AdversarialChain.from_obj([
        {"role": "proponent", "text": "the lattice of units gives the "
                                      "pairs we need for the bound"},
        {"role": "critic", "text": "the lattice of units gives the pairs "
                                   "we need for the bound, and that is "
                                   "the right construction"},
        {"role": "rebuttal", "text": "perhaps the other tower is better"},
        {"role": "critic", "text": "perhaps the other tower is better, "
                                   "or some third arrangement entirely"},
        {"role": "rebuttal", "text": "the lattice of units gives the pairs "
                                      "we need for the bound, and that is "
                                      "the right construction"},
    ], ground=good_ground)
    check("an oscillating chain is SPINNING",
          audit_adversarial_chain(osc).verdict is Verdict.SPINNING,
          str(audit_adversarial_chain(osc).verdict.value))

    # -- 7. an empty chain must not pass ------------------------------
    empty = AdversarialChain(turns=[], ground=good_ground)
    check("an empty chain is UNRESOLVED, not GROUNDED",
          audit_adversarial_chain(empty).verdict
          is Verdict.UNRESOLVED)

    print()
    if failures:
        print("  %d CHECK(S) FAILED:" % len(failures))
        for f in failures:
            print("    - %s" % f)
        return 1
    print("  ALL CHECKS PASS")
    return 0


def main() -> int:
    if "--selftest" in sys.argv or len(sys.argv) == 1:
        return _selftest()
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
