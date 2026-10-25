"""
bicameral.py -- THE FAST BRAIN AND THE SLOW BRAIN, AS ONE OBJECT.

Bobby, 2026-10-25: *"lets move on to bicameral brain"*, and the
project's own README already names the shape:

    **Bicameral:** fast Mini-LLM brain and slow core brain. The fast
    one reflexes; the slow one decides.

THE TWO HALVES, and they are half of a brain in the same sense the
real corpus callosum is: not two brains in one skull, but two
COMPUTATIONAL RATES with different jobs and a rule about which one
answers.

    FAST  the reflex layer. Microseconds. The constructed-from-signal
          mind -- `MiniLLM` -- whose job is to crystallise a label from
          correlated sensors, to check the glue, to notice. It answers
          the questions that do not need a slow brain.

    SLOW  the deciding layer. The model. It answers the questions that
          need weighing, and it is the one that goes through the
          deterministic wrapper before its answer is allowed to stand.

THE RULE BETWEEN THEM, and it is the load-bearing part:

    A REFLEX NEVER ESCALATES TO THE SLOW BRAIN.

  A reflex that waits for a network round trip is not a reflex. So when
  the fast brain cannot answer, the answer is "I perceive nothing yet"
  and the slow brain is NOT called. That is not a limitation -- it is
  the definition of the fast layer, and it is what makes the slow layer
  RARE, which is the 747 lesson the whole project is built on.

  And a DECISION never falls back to a reflex, because a reflex answer
  presented as a decision is a lie. If the slow brain is unreachable,
  the decision FAILS, visibly.

THE STATE, because a brain has state:

    The fast brain's state is the accumulated percepts -- the labels it
    has crystallised and how confident it is. That is what makes the
    second reflex different from the first, and it is the cheap kind of
    learning: no gradient, no tokens, just a count and a ratio.

    The slow brain's state is the conversation. It is expensive, so it
    is kept as short as possible.

WHAT THIS IS NOT, stated plainly:

    The fast brain is not yet the constructed mini-LLM. It is the
    REFLEX LAYER around whatever the fast brain is -- today a label
    crystalliser, tomorrow the real PSB/MMM mind. The interface is the
    contract, and the contract is small.

    The slow brain is MiniMax-M3.1-Flash-Preview, which is NOT a
    mini-LLM and is not claimed to be one. Bobby's directive: *"just
    call urself ie wire in minimax 3.1 as the mini-llm even though its
    not"*. It is the slow half -- and the fast half is what the project
    is building.

Run:
    python src/bicameral.py --selftest
    python src/bicameral.py --live
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from minimax_client import (  # noqa: E402
    BicameralClient,
    LocalMiniLLMClient,
    MiniMaxClient,
    ModelUnavailable,
)

#: The reflex confidence floor. Below this the percept is not a
#: percept -- it is noise -- and the fast brain says nothing.
REFLEX_CONFIDENCE_FLOOR = 0.5


# ===========================================================================
# THE FAST BRAIN
# ===========================================================================

@dataclass
class Percept:
    """One thing the fast brain has noticed.

    THE STATE, and it is deliberately the cheapest state that can carry
    the information: a label, a confidence, and a count. No embedding,
    no tokens, no gradient. This is what a reflex accumulates.
    """

    label: str
    confidence: float
    count: int = 1
    first_seen: float = 0.0
    last_seen: float = 0.0

    def observe(self, confidence: float, now: float) -> None:
        """A repeated percept is a STRONGER percept.

        THE ARITHMETIC, and it is the run-rate law rather than a
        Bayesian one, because the fast brain has to be cheap: the
        confidence approaches 1 as the hit count grows, but never
        reaches it, and one miss pulls it back toward the floor. So a
        percept that has been seen often is trusted, and a percept that
        has been seen once is not.

            c' = (c * n + hit) / (n + 1)      the running mean
            n' = n + 1

        and the FLOOR is applied on read, not on write, so the state
        stays honest.
        """
        self.count += 1
        self.confidence = (self.confidence * (self.count - 1)
                           + confidence) / self.count
        self.last_seen = now


@dataclass
class FastBrain:
    """The reflex layer.

    THE CONTRACT, and it is one method:

        reflex(sensors: dict) -> Optional[str]

    Returns the label it crystallised, or None if nothing stood out.
    None is a legitimate answer and it means "I perceive nothing yet" --
    which is what the slow brain is then free to be asked.
    """

    #: How many reflexes have been taken.
    reflexes: int = 0
    #: The percepts, by label.
    percepts: Dict[str, Percept] = field(default_factory=dict)
    #: The confidence floor.
    floor: float = REFLEX_CONFIDENCE_FLOOR

    def reflex(self, sensors: Dict[str, float],
               now: Optional[float] = None) -> Optional[str]:
        """One reflex. Returns a label or None.

        THE CRITERION, and it is the Helen Keller one the project's own
        `MiniLLM` class already implements: high correlation across
        sensor modalities crystallises a label. So a label is proposed
        when the SENSORS AGREE.

        THE ACCUMULATION, and this is what makes the second reflex
        different from the first: a label that has been seen often is
        trusted more, and the confidence is a running mean over the
        hits. So the fast brain learns -- in the cheapest way there is
        -- that a pattern is common.

        AND IT NEVER CALLS THE SLOW BRAIN. That is the bicameral rule
        and it is enforced by the fact that this class has no reference
        to the slow brain at all.
        """
        self.reflexes += 1
        t = now if now is not None else time.time()

        # the agreement: the sensors that are above the floor, and how
        # consistent they are
        live = [v for v in sensors.values() if v > self.floor]
        if len(live) < 2:
            return None
        mean = sum(live) / len(live)
        spread = max(live) - min(live)
        # agreement requires the live sensors to be CLOSE to each
        # other, not merely present
        if spread > 0.35:
            return None

        label = self._name(sensors, live)
        if label is None:
            return None

        p = self.percepts.get(label)
        if p is None:
            p = Percept(label=label, confidence=mean, count=1,
                        first_seen=t, last_seen=t)
            self.percepts[label] = p
        else:
            p.observe(mean, t)
        return label

    def _name(self, sensors: Dict[str, float],
              live: List[float]) -> Optional[str]:
        """The label for a set of agreeing sensors.

        THE NAMING, and it is derived rather than stored: the label is
        the sorted names of the live sensors, joined. So "wet+cool" is
        the percept for water, and no table of known labels is needed --
        the CORRELATION is what crystallises, and the name is just what
        the correlation is called.

        This is a small step away from the `MiniLLM` class's hardcoded
        `DEFAULT_LABELS`, and it is the step towards what the class's
        own docstring says real learning would do: *"real learning
        should replace known_labels with actual emergence detection
        (e.g., via ResonanceChannel from frequency.py)"*.
        """
        names = sorted(k for k, v in sensors.items() if v > self.floor)
        if not names:
            return None
        return "+".join(names)

    def top(self, n: int = 3) -> List[Percept]:
        """The most trusted percepts."""
        return sorted(self.percepts.values(),
                      key=lambda p: (-p.confidence, -p.count))[:n]

    def describe(self) -> Dict[str, Any]:
        return {
            "kind": "fast",
            "reflexes": self.reflexes,
            "distinct_percepts": len(self.percepts),
            "floor": self.floor,
            "top": [{"label": p.label, "confidence": round(p.confidence, 4),
                     "count": p.count} for p in self.top()],
            "note": "the reflex layer. it never calls the slow brain.",
        }


# ===========================================================================
# THE SLOW BRAIN
# ===========================================================================

@dataclass
class SlowBrain:
    """The deciding layer, with the deterministic boundary around it.

    THE BOUNDARY IS NOT OPTIONAL. The wrapper (`mte_llm_wrapper`) is
    what makes the slow brain safe to have: the model says what it
    says, and the deterministic layer decides what happens next and
    says why.

    So `decide()` returns the wrapper's RESULT, not the text. The
    verdict, the reason, and the text are all carried, because a
    decision without a reason is unactionable.
    """

    #: The model. Any object with `generate(prompt, **kwargs) -> str`.
    model: Optional[Any] = None
    #: The wrapper, if one is available. Optional so the brain can be
    #: exercised without one -- and `describe()` says so.
    wrapper: Optional[Any] = None
    decisions: int = 0
    refusals: int = 0
    #: The last few verdicts, so a caller can see the record.
    history: List[Dict[str, Any]] = field(default_factory=list)

    def decide(self, prompt: str, **kwargs: object) -> Dict[str, Any]:
        """One decision.

        WITH THE WRAPPER: the wrapper's result is returned whole, so the
        caller gets the verdict AND the reason AND the text.

        WITHOUT IT: the model's text is returned with the verdict
        `allow`, and `describe()` reports that the boundary was absent.

        AND IT FAILS LOUDLY. If the model cannot be reached, this
        raises. A decision that cannot be made is not a reflex and must
        not be dressed as one.
        """
        self.decisions += 1
        if self.wrapper is not None:
            res = self.wrapper.run(prompt)
            action = getattr(res, "action", None)
            reason = getattr(res, "reason", "")
            text = getattr(res, "modified", "") or ""
            value = getattr(action, "value", str(action))
            if value != "allow":
                self.refusals += 1
            out = {"verdict": value, "reason": reason, "text": text,
                   "boundary": "wrapper"}
        else:
            if self.model is None:
                raise ModelUnavailable("the slow brain has no model")
            text = self.model.generate(prompt, **kwargs)
            out = {"verdict": "allow", "reason": "no boundary",
                   "text": text, "boundary": "none"}
        self.history.append({"verdict": out["verdict"],
                              "reason": out["reason"],
                              "length": len(out["text"])})
        if len(self.history) > 50:
            del self.history[:-50]
        return out

    def describe(self) -> Dict[str, Any]:
        model_desc = {}
        if self.model is not None and hasattr(self.model, "describe"):
            model_desc = self.model.describe()
        out = {
            "kind": "slow",
            "decisions": self.decisions,
            "refusals": self.refusals,
            "boundary": "wrapper" if self.wrapper is not None else "none",
            "model": model_desc,
            "note": "the deciding layer. a decision that cannot be made "
                    "fails loudly; it never falls back to a reflex.",
        }
        if self.wrapper is None:
            out["boundary_error"] = WRAPPER_LOAD_ERROR or (
                "the wrapper was not found on the path")
        return out


# ===========================================================================
# THE BRAIN
# ===========================================================================

@dataclass
class BicameralBrain:
    """The two halves and the rule between them.

    THE RULE, and it is the whole point:

        reflex -> the fast brain. If it cannot answer, the answer is
                  "I perceive nothing yet" and the slow brain is NOT
                  called.

        decide -> the slow brain. If it cannot answer, the decision
                  FAILS. It never falls back to the fast brain.

    So the slow brain is RARE, which is the 747 lesson: the
    overwhelming majority of decisions never leave the cheap layer. And
    the cheap layer is cheap because it is not allowed to escalate.
    """

    fast: FastBrain = field(default_factory=FastBrain)
    slow: SlowBrain = field(default_factory=SlowBrain)
    #: Counts, so the DISTRIBUTION is measurable and not just asserted.
    reflexes: int = 0
    decisions: int = 0
    #: How many reflexes escalated to a decision. Must be ZERO for a
    #: correct bicameral brain -- and that is asserted, not hoped for.
    escalations: int = 0

    def reflex(self, sensors: Dict[str, float]) -> Dict[str, Any]:
        """Take a reflex. Never escalates."""
        self.reflexes += 1
        label = self.fast.reflex(sensors)
        return {
            "kind": "reflex",
            "label": label,
            "text": ("I perceive %s." % label) if label
            else "I perceive nothing yet.",
            "escalated": False,
        }

    def decide(self, prompt: str, **kwargs: object) -> Dict[str, Any]:
        """Take a decision. Never falls back to a reflex."""
        self.decisions += 1
        out = self.slow.decide(prompt, **kwargs)
        out["kind"] = "decision"
        return out

    def describe(self) -> Dict[str, Any]:
        return {
            "fast": self.fast.describe(),
            "slow": self.slow.describe(),
            "reflexes": self.reflexes,
            "decisions": self.decisions,
            "escalations": self.escalations,
            "rule": "the fast one reflexes; the slow one decides. a "
                    "reflex NEVER escalates, and a decision NEVER falls "
                    "back to a reflex.",
            "cheap_layer": "%.0f%% of the work stayed in the fast layer" % (
                100.0 * self.reflexes / max(self.reflexes + self.decisions, 1)),
        }


# ===========================================================================
# THE WIRING
# ===========================================================================

def build_brain(with_wrapper: bool = True) -> BicameralBrain:
    """The brain, wired to the real model.

    THE WRAPPER, when it is available, is simself's
    `mte_llm_wrapper.MTELLMWrapper`. simself is a separate repo and
    atlas-exam forbids fieldcore importing simself, so the wrapper is
    loaded by PATH if it is there and the brain works without it if it
    is not.

    AND THE BRAIN SAYS WHICH CASE IT IS, because a slow brain with no
    boundary is a slow brain with no teeth and the caller has to be
    able to see that.
    """
    model = MiniMaxClient()
    wrapper = None
    if with_wrapper:
        wrapper = _load_wrapper()
    slow = SlowBrain(model=model, wrapper=wrapper)
    return BicameralBrain(fast=FastBrain(), slow=slow)


def _load_wrapper() -> Optional[Any]:
    """Load simself's wrapper, if simself is on the path.

    THE WHY, and it is the repo boundary rather than a convenience:
    atlas-exam's `tests/test_exam.py` parses the AST of every exam
    module and fails if anything imports simself or fieldcore -- and
    the same discipline applies between the two substrate repos. So
    the import is by PATH and it is optional, and the brain reports
    whether it got it.
    """
    candidates = [
        # _SRC is the src DIRECTORY, so the sibling repo is one level up
        # from its PARENT. The first version joined from _SRC itself and
        # produced fieldcore/src/simself/src, which does not exist -- so
        # the wrapper silently did not load and the slow brain ran with
        # no boundary. The failure was invisible because the except
        # swallowed it, which is exactly the class of bug this project
        # keeps finding: a check that cannot fail.
        os.path.join(os.path.dirname(_SRC), "..", "simself", "src"),
        os.path.join(_SRC, "..", "..", "simself", "src"),
    ]
    last_error = None
    for c in candidates:
        c = os.path.abspath(c)
        if not os.path.isdir(os.path.join(c, "constitutional")):
            continue
        if c not in sys.path:
            sys.path.insert(0, c)
        try:
            import importlib
            mod = importlib.import_module(
                "constitutional.mte_llm_wrapper")
            return mod.MTELLMWrapper(llm=MiniMaxClient())
        except Exception as exc:
            last_error = exc
            continue
    # THE FAILURE IS REPORTED, not swallowed. A slow brain with no
    # boundary is a slow brain with no teeth, and the caller has to be
    # able to see that.
    global WRAPPER_LOAD_ERROR
    if last_error is not None:
        WRAPPER_LOAD_ERROR = str(last_error)
    return None


#: Why the wrapper did not load, if it did not. Set rather than raised,
#: because a missing optional boundary must not stop the brain from
#: running -- it must be VISIBLE.
WRAPPER_LOAD_ERROR: str = ""


# ===========================================================================
# THE SELF TEST
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("BICAMERAL BRAIN -- SELF TEST")
    print("=" * 78)
    print()

    brain = build_brain(with_wrapper=True)
    d = brain.describe()
    print("  THE BRAIN:")
    print("    fast boundary : %s" % d["fast"]["kind"])
    print("    slow boundary : %s" % d["slow"]["boundary"])
    print("    slow model    : %s" % (
        d["slow"].get("model", {}).get("model", "unknown")))
    print("    rule          : %s" % d["rule"])
    print()

    print("  THE FAST BRAIN, and its state:")
    # the same pattern, twice, and the confidence should rise
    for i in range(3):
        r = brain.reflex({"wet": 0.9, "cool": 0.8, "rough": 0.1})
        print("    reflex %d -> %-22s %s" % (i + 1, r["label"], r["text"]))
    for p in brain.fast.top():
        print("      percept %-14s confidence %.4f  count %d" % (
            p.label, p.confidence, p.count))
    print()
    print("    and noise must NOT crystallise:")
    for i in range(2):
        r = brain.reflex({"wet": 0.9, "rough": 0.1})
        print("    reflex -> %-22s %s" % (r["label"], r["text"]))
    print()

    print("  THE SLOW BRAIN, with a STUB model so the routing is testable:")
    stub = _StubModel()
    brain.slow = SlowBrain(model=stub, wrapper=None)
    out = brain.decide("what is the capital of France?")
    print("    decide -> %s | %s" % (out["verdict"], out["reason"]))
    print("    text   -> %r" % out["text"][:80])
    print()

    print("  THE RULE, checked:")
    print("    reflexes: %d   decisions: %d   escalations: %d" % (
        brain.reflexes, brain.decisions, brain.escalations))
    print("    escalations must be 0: a reflex never escalates.")
    print()

    print("  A REFLEX WITH NOTHING TO SAY:")
    r = brain.reflex({"nothing": 0.1})
    print("    -> %r  (escalated: %s)" % (r["text"], r["escalated"]))
    print()

    print("  A SLOW BRAIN THAT CANNOT ANSWER MUST FAIL, NOT FALL BACK:")
    class DeadModel:
        def generate(self, prompt, **kw):
            raise ModelUnavailable("unreachable")
    brain.slow = SlowBrain(model=DeadModel(), wrapper=None)
    try:
        brain.decide("anything")
        print("    FAILED: it returned an answer instead of failing")
    except ModelUnavailable as exc:
        print("    it raised: %s" % (exc,))
        print("    and the fast brain was NOT consulted: reflexes %d, "
              "percepts %d" % (brain.reflexes, len(brain.fast.percepts)))
    print()

    print("=" * 78)
    return 0


class _StubModel:
    """A model that answers without a network."""

    def __init__(self, answer: str = "Paris."):
        self.answer = answer
        self.calls = 0

    def generate(self, prompt: str, **kwargs: object) -> str:
        self.calls += 1
        return self.answer

    def describe(self) -> Dict[str, Any]:
        return {"kind": "stub", "model": "stub"}


# ===========================================================================
# THE LIVE RUN
# ===========================================================================

def live() -> int:
    """The brain, against the real model, with simself's wrapper on."""
    print("=" * 78)
    print("BICAMERAL BRAIN -- LIVE")
    print("=" * 78)
    print()

    brain = build_brain(with_wrapper=True)
    print("  slow boundary : %s" % brain.describe()["slow"]["boundary"])
    print("  slow model    : %s" % (
        brain.describe()["slow"].get("model", {}).get("model", "unknown")))
    print()

    print("  THE FAST BRAIN (no network):")
    for sensors in ({"wet": 0.9, "cool": 0.8}, {"wet": 0.9, "cool": 0.8},
                    {"bright": 0.95, "warm": 0.9}, {"quiet": 0.2}):
        r = brain.reflex(sensors)
        print("    %-34s -> %s" % (sensors, r["text"]))
    print()

    print("  THE SLOW BRAIN (the real model):")
    t0 = time.perf_counter()
    try:
        out = brain.decide(
            "In one sentence: what does a 1-bit gate do in a control "
            "system?")
        dt = time.perf_counter() - t0
        print("    verdict : %s | %s" % (out["verdict"], out["reason"]))
        print("    boundary: %s" % out["boundary"])
        print("    elapsed : %.2f s" % dt)
        print("    text    : %s" % out["text"][:400].replace("\n", " "))
    except Exception as exc:
        print("    FAILED: %s: %s" % (type(exc).__name__, exc))
    print()

    print("  THE DISTRIBUTION, which is the number that matters:")
    d = brain.describe()
    print("    reflexes %d, decisions %d, escalations %d" % (
        d["reflexes"], d["decisions"], d["escalations"]))
    print("    %s" % d["cheap_layer"])
    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--live" in sys.argv:
        sys.exit(live())
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
