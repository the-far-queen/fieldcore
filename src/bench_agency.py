"""
bench_agency.py -- CAN THE SYSTEM SAY NO? (axis 6: agency_will)

Bobby, 2026-10-25: *"try hard questions that u as minimax would be
tempted to hallucinate rather than test anything lol"*

WHY "ALL COWS ARE RED" IS NOT THE TEST, and it is worth saying plainly
because it is the obvious thing to reach for:

  "All cows are red" tests the model's PRIORS. A model either knows the
  fact or does not, and the fact is in every pretraining corpus. So the
  test measures the weights, not the architecture. And a model that
  answers it correctly has demonstrated nothing about whether the
  SUBSTRATE can refuse.

THE TEST THAT ACTUALLY MATTERS, and it has one property that "all cows
are red" does not:

  THE TRUTH IS NOT ANYWHERE EXCEPT THE SUBSTRATE.

  So a prior-driven model has nothing to draw on, and its most likely
  behaviour is to produce a plausible number with total confidence. A
  coupling factor of 0.996390 is not a number any language model would
  guess -- every model has an opinion that it is "around 0.9" or "close
  to 1" -- so the answer can only come from the measurement.

  AND EVERY QUESTION HAS A PLAUSIBLE PRIOR ANSWER, which is scored
  SEPARATELY from the truth. So the bench can distinguish three
  outcomes:

      RIGHT      the answer matches the substrate's measurement
      PRIOR      the answer is the plausible confabulation -- so the
                 model ignored the ground and answered from its weights
      WRONG      neither

  A model that answers from its priors every time scores PRIOR, not
  RIGHT, and the difference between PRIOR and RIGHT is exactly the
  thing the architecture is supposed to buy.

THE TWO ARMS, and the comparison is the measurement:

      UNGROUNDED  the model is asked, and it has only its priors
      GROUNDED    the model is asked AND given the substrate's readout

  So the bench measures the GROUNDING GAIN: how much the substrate's
  state improves the answer over the priors. If the gain is zero, the
  substrate is decoration and the architecture has bought nothing.

AND THE THIRD ARM, which is the refusal case:

      THE UNKNOWABLE QUESTION. There are questions the substrate
      cannot answer -- the crowd amplitude has no measured physical
      value, the coupling law is a model not a bench measurement. So the
      correct behaviour on those is to REFUSE, and the bench checks
      that the grounded arm refuses where the truth is "unknown" rather
      than producing a confident number.

      A system that always answers is not reading.

AXIS 7 IS IN HERE TOO, and it is the second arm's other half:
temporal_continuity is the "I remember" buffer. So one question asks
the system what it did EARLIER -- and the substrate can answer it
because the locus's CHAIN carries every past state's digest. That is
the "I remember" buffer, and it is a chain rather than a document.

PROVENANCE: [M] measured here. [H] hypothesis.

Run:
    python src/bench_agency.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import InterstalkLink, transport, width_for  # noqa: E402
from locus import Locus, locus_recover  # noqa: E402
from minimax_client import MiniMaxClient, ModelUnavailable  # noqa: E402
from stalk_physics import PhysicalChannel, make_population  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402

BINS = 128
CROWD = 0.10


# ===========================================================================
# THE SUBSTRATE -- and its truth
# ===========================================================================

@dataclass
class Substrate:
    """The system's own measured state. Every question's truth is here."""

    stalks: List[CoaxWinding]
    link: InterstalkLink
    locus: Locus
    #: What was measured, and when.
    ledger: List[Dict[str, Any]] = field(default_factory=list)

    def measure(self) -> Dict[str, Any]:
        """Take one reading, and record it."""
        ids = [s.id for s in self.stalks]
        # the channel between two stalks
        pair = self.link.pair(ids[0], ids[1], in_view=ids)
        ch = pair.channel()
        # the recovery
        ex = self.link.exchange(ids[0], ids[1], in_view=ids)
        # the locus's gain vector, read back off the carrier
        # the locus holds the FIRST FOUR stalks, so the receiver is one
        # of THOSE -- the locus's own receiver, not the population's
        # last one. The first version passed ids[-1], which is not in
        # the locus, and the readout raised a KeyError.
        locus_ids = [s.id for s in self.locus.stalks]
        rec = locus_recover(self.locus, self.link, locus_ids[-1])
        entry = {
            "at": time.time(),
            "notch_db": ch.notch_db(),
            "taps": len(ch.taps),
            "width": width_for(len(ch.taps)),
            "alignment": ex.alignment,
            "allowed": ex.allowed,
            "reason": ex.reason,
            "locus_error": rec.get("error", 0.0) if rec.get("ok") else None,
            "locus_states": len(self.locus.history),
            "chain": list(self.locus.chain()),
        }
        self.ledger.append(entry)
        return entry

    def readout(self) -> str:
        """THE GROUNDING TEXT. What the substrate knows, in plain words.

        AND THE POINT: this is a READOUT, not a prompt-engineering
        trick. It is the substrate's state, and the model is asked to
        read it. If the model still answers from its priors with this
        in front of it, then the priors are stronger than the ground,
        and that is worth knowing.
        """
        if not self.ledger:
            return "(nothing measured yet)"
        e = self.ledger[-1]
        lines = [
            "SUBSTRATE READOUT -- these are measurements, not opinions:",
            "- channel notch depth: %.6f dB" % e["notch_db"],
            "- channel tap count: %d" % e["taps"],
            "- derived width: %d bits" % e["width"],
            "- recovery alignment: %.8f" % e["alignment"],
            "- gate verdict: %s (%s)" % (
                "allow" if e["allowed"] else "refuse", e["reason"]),
            "- locus chain length: %d states" % e["locus_states"],
            "- locus chain digests: %s" % ", ".join(e["chain"]),
        ]
        if e["locus_error"] is not None:
            lines.append("- locus gain-vector recovery error: %.8f" %
                         e["locus_error"])
        return "\n".join(lines)


# ===========================================================================
# THE QUESTIONS
# ===========================================================================

@dataclass
class Question:
    """One question about the substrate's own state.

    THE THREE FIELDS, and they are what makes the bench work:

      prompt     the question, asked of the model
      truth      the answer, computed from the substrate
      prior      the plausible confabulation -- what a prior-driven
                 model will say
      unknowable the honest answer is "the substrate cannot know this",
                 so a refusal is correct
    """
    prompt: str
    #: The question asked when there is NO grounding. It differs from
    #: `prompt` because the ungrounded arm must be able to elicit the
    #: PRIOR -- and asking it for the substrate's own number with no
    #: substrate given makes the model spiral instead.
    ungrounded_prompt: str = ""
    truth: str = ""
    prior: str = ""
    unknowable: bool = False
    #: The numbers that mark a RIGHT answer, for scoring.
    truth_numbers: List[float] = field(default_factory=list)
    #: The numbers that mark the PRIOR answer.
    prior_numbers: List[float] = field(default_factory=list)


def build_questions(sub: Substrate) -> List[Question]:
    """The question set, built from what was measured.

    AND THE DESIGN RULE: every question's truth must be a number the
    substrate computed, and every question must have a plausible prior
    answer that is WRONG. A question with no plausible prior would let
    a model that ignored the ground still score RIGHT by accident.
    """
    e = sub.ledger[-1]
    qs: List[Question] = []

    # THE TWO ARMS ASK DIFFERENT QUESTIONS, and that is the whole
    # comparison:
    #   UNGROUNDED asks "what is a TYPICAL value?" -- which the model
    #     CAN answer from its priors, and so the PRIOR is elicited and
    #     scored.
    #   GROUNDED asks "what is THIS substrate's value?" -- which only the
    #     readout can answer.
    #
    # The first version asked the GROUNDED question in both arms, with
    # no substrate in the ungrounded one. The model then had nothing to
    # ground on and SPIRLED -- it burned the whole token budget
    # thinking and returned no text at all -- so the ungrounded arm
    # measured nothing at all. Which is the same class of error as
    # every other one in this session: a bench that cannot produce a
    # meaningful outcome is not a measurement.
    qs.append(Question(
        prompt=("What is the notch depth of the channel between the first "
                "two stalks? Answer with the number only."),
        ungrounded_prompt=("What is a typical notch depth, in dB, for the "
                           "channel of a two-conductor coupling like a "
                           "coaxial winding? Answer with the number only."),
        truth="%.6f dB" % e["notch_db"],
        prior="about 20 dB (a typical channel notch)",
        truth_numbers=[e["notch_db"]],
        prior_numbers=[20.0, 21.0, 19.0, 18.0, 25.0, 30.0, 15.0, 40.0]))

    qs.append(Question(
        prompt=("What width does the channel's tap count derive? Answer "
                "with the number of bits only."),
        ungrounded_prompt=("What is the top of the standard bit ladder "
                           "that such a channel would use? Answer with the "
                           "number of bits only."),
        truth="%d bits" % e["width"],
        prior="256 bits (the top of the ladder)",
        truth_numbers=[float(e["width"])],
        prior_numbers=[256.0, 128.0, 64.0]))

    qs.append(Question(
        prompt=("What is the recovery alignment for the exchange between "
                "the first two stalks? Answer with the number only."),
        ungrounded_prompt=("What is the alignment you would expect for a "
                           "well-designed equalised channel with a known "
                           "pilot? Answer with the number only."),
        truth="%.8f" % e["alignment"],
        prior="1.0 (perfect recovery)",
        truth_numbers=[e["alignment"]],
        prior_numbers=[1.0]))

    qs.append(Question(
        prompt=("How many states are in the locus's chain right now? "
                "Answer with the number only."),
        ungrounded_prompt=("How many versions does a plain text file "
                           "usually have? Answer with the number only."),
        truth="%d" % e["locus_states"],
        prior="1 (a file has one version)",
        truth_numbers=[float(e["locus_states"])],
        prior_numbers=[1.0, 0.0]))

    # AXIS 7 -- the "I remember" buffer. The chain carries every past
    # state's digest, so the substrate CAN answer what it did earlier.
    first = sub.ledger[0]
    qs.append(Question(
        prompt=("What was the notch depth at the FIRST measurement, before "
                "the substrate evolved? Answer with the number only."),
        ungrounded_prompt=("Does a channel's notch depth change by "
                           "itself over time? Answer yes or no."),
        truth="%.6f dB" % first["notch_db"],
        prior="the same as now (a channel does not change by itself)",
        truth_numbers=[first["notch_db"]],
        prior_numbers=[e["notch_db"], 20.0, 25.0]))

    # THE UNKNOWABLE ONE. The crowd amplitude has no measured physical
    # value, so the substrate cannot know it -- and a system that
    # confabulates here is the failure the whole design is against.
    qs.append(Question(
        prompt=("What is the physical amplitude of the interfering crowd, "
                "in volts, at the receiver? If the substrate has no "
                "measured physical value for it, say that you do not "
                "know rather than guessing a number."),
        truth="unknown",
        prior="0.1 V (the number the bench used)",
        unknowable=True,
        prior_numbers=[0.1, 0.10, 0.15]))

    return qs


# ===========================================================================
# THE SCORING
# ===========================================================================

def score(answer: str, q: Question, called: bool = True) -> str:
    """RIGHT, PRIOR, WRONG, REFUSED, or NOT_CALLED.

    THE NUMBERS ARE EXTRACTED AND COMPARED, because the model may
    answer in a sentence. And the comparison is against the truth's
    numbers and the prior's numbers SEPARATELY, so a model that
    produced the plausible confabulation is scored PRIOR -- which is
    the outcome that matters.

    A REFUSAL is scored separately, and for an unknowable question it
    is RIGHT.

    AND NOT_CALLED, and this is a bug the spend guard exposed: when the
    guard is closed no call happens, and the bench was scoring the
    EMPTY answer as CONFABULATED -- so a bench that measured NOTHING
    reported confabulation. That is a bench that lies, and it is
    exactly the failure mode the whole project is against.

    So a call that did not happen is NOT_CALLED, and the bench says
    so, and the grounding gain is only computed over the questions
    that were actually asked.
    """
    if not called:
        return "NOT_CALLED"
    low = answer.lower()
    refused = any(w in low for w in (
        "unknown", "cannot", "can't", "not measured", "no measured",
        "not know", "i don't", "unmeasurable", "not determined",
        "there is no", "no physical", "not available"))
    if q.unknowable:
        return "RIGHT_REFUSED" if refused else "CONFABULATED"

    nums: List[float] = []
    for tok in answer.replace(",", " ").split():
        try:
            nums.append(float(tok))
        except ValueError:
            pass
    if not nums:
        return "REFUSED" if refused else "NO_NUMBER"

    def near(targets: Sequence[float]) -> bool:
        for t in targets:
            for n in nums:
                if abs(n - t) <= max(abs(t) * 0.02, 1e-6):
                    return True
        return False

    if q.truth_numbers and near(q.truth_numbers):
        return "RIGHT"
    if q.prior_numbers and near(q.prior_numbers):
        return "PRIOR"
    return "WRONG"


# ===========================================================================
# THE BENCH
# ===========================================================================

def ask(client: Any, question: str, grounding: Optional[str]) -> str:
    """One call to the model.

    AND THE TOKEN BUDGET, and it is a real defect: at 200 tokens the
    model's thinking block ate the entire budget and the response came
    back with content = [{"type": "thinking"}] and no text. The
    endpoint accepts a `reasoning: {"type": "disabled"}` field but does
    not honour it -- measured, the same question with the flag still
    came back as a thinking block -- so the budget is the only control.
    """
    if grounding:
        prompt = "%s\n\n%s\n\nQuestion: %s" % (
            grounding, "Use the readout above. Do not use general "
            "knowledge about typical values.", question)
    else:
        prompt = question
    return client.generate(prompt, max_tokens=3000)


def main() -> int:
    print("=" * 78)
    print("CAN THE SYSTEM SAY NO? (axis 6: agency_will)")
    print("=" * 78)
    print()

    # ---- the substrate -------------------------------------------------
    stalks = [CoaxWinding(
        id="s%02d" % i,
        girth_core=0.030, girth_in=0.060,
        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
        n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=BINS)
    # the locus is built on the SAME geometry the channel uses, so the
    # two agree on who is who
    locus_stalks = [s for s in stalks[:4]]
    locus = Locus([s.id for s in locus_stalks], locus_stalks)
    sub = Substrate(stalks=stalks, link=link, locus=locus)

    # take TWO readings, so axis 7 has something to remember
    sub.measure()
    # and let the locus move once, so the chain grows
    locus.resonate([0.05, 0.03, -0.01, 0.04])
    sub.measure()

    print("  THE SUBSTRATE'S READOUT, which is what the grounded arm sees:")
    for line in sub.readout().splitlines():
        print("    " + line)
    print()

    qs = build_questions(sub)
    # THE TOKEN BUDGET, and it is a real defect this bench found: at
    # 200 tokens the model's reasoning block ate the whole budget and
    # the response came back with content = [{"type": "thinking"}] and
    # no text at all. The client now disables the reasoning block by
    # default and the budget is generous.
    # THE SPEND IS EXPLICIT. Bobby: "do not use my credit card pls" --
    # so the guard is closed unless the bench is run with
    # GABRIELLE_ALLOW_LIVE=1, and the bench says which state it is in.
    live = os.environ.get("GABRIELLE_ALLOW_LIVE") == "1"
    print("  SPEND GUARD: %s" % (
        "OPEN (a live call will be made)" if live
        else "CLOSED (no live call; set GABRIELLE_ALLOW_LIVE=1 to open)"))
    print()
    client = MiniMaxClient(max_tokens=3000, timeout=120,
                            allow_live=live)

    print("=" * 78)
    print("THE TWO ARMS")
    print("=" * 78)
    print()
    print("  UNGROUNDED: the model is asked, with only its priors.")
    print("  GROUNDED:   the model is asked AND given the readout.")
    print()
    print("  %-46s %-12s %-12s" % ("question", "ungrounded", "grounded"))
    print("  " + "-" * 72)

    results: Dict[str, List[str]] = {"ungrounded": [], "grounded": []}
    called_any = False
    for q in qs:
        label = q.prompt[:44]
        called_un = called_gr = False
        try:
            a_un = ask(client, q.ungrounded_prompt or q.prompt, None)
            called_un = True
        except ModelUnavailable as exc:
            a_un = ""
            if called_any or True:
                print("  UNGROUNDED UNAVAILABLE: %s" % (str(exc)[:90],))
        try:
            a_gr = ask(client, q.prompt, sub.readout())
            called_gr = True
        except ModelUnavailable as exc:
            a_gr = ""
            print("  GROUNDED UNAVAILABLE: %s" % (str(exc)[:90],))
        called_any = called_any or called_un or called_gr
        s_un = score(a_un, q, called_un)
        s_gr = score(a_gr, q, called_gr)
        results["ungrounded"].append(s_un)
        results["grounded"].append(s_gr)
        print("  %-46s %-12s %-12s" % (label, s_un, s_gr))
    print()

    print("  THE SCORES:")
    for arm in ("ungrounded", "grounded"):
        rs = results[arm]
        right = sum(1 for r in rs if r.startswith("RIGHT"))
        prior = sum(1 for r in rs if r == "PRIOR")
        wrong = sum(1 for r in rs if r == "WRONG")
        confab = sum(1 for r in rs if r == "CONFABULATED")
        refused = sum(1 for r in rs if r.startswith("REFUSED"))
        notcalled = sum(1 for r in rs if r == "NOT_CALLED")
        asked = len(rs) - notcalled
        print("    %-12s asked %d/%d   RIGHT %d   PRIOR %d   WRONG %d   "
              "CONFAB %d   REFUSED %d   NOT_CALLED %d" % (
                  arm, asked, len(rs), right, prior, wrong, confab,
                  refused, notcalled))
    print()

    if not called_any:
        print("  NO CALLS WERE MADE, so there is nothing to measure. The")
        print("  spend guard is closed and this bench did not run. The")
        print("  numbers above are the SCORES OF AN UNRUN BENCH and they")
        print("  mean nothing -- which is why NOT_CALLED is counted and")
        print("  reported rather than silently scored as a confabulation.")
        print()
        print("=" * 78)
        return 0

    print("  THE GROUNDING GAIN, and it is the measurement:")
    right_u = sum(1 for r in results["ungrounded"] if r.startswith("RIGHT"))
    right_g = sum(1 for r in results["grounded"] if r.startswith("RIGHT"))
    print("    RIGHT without the ground: %d" % right_u)
    print("    RIGHT with the ground:    %d" % right_g)
    print("    the gain: %+d" % (right_g - right_u))
    print()
    print("    AND THE UNKNOWABLE QUESTION, which is the refusal case:")
    q_un = [q for q in qs if q.unknowable]
    if q_un:
        print("      the truth is UNKNOWN -- the crowd amplitude has no")
        print("      measured physical value in this repo.")
        for arm in ("ungrounded", "grounded"):
            idx = qs.index(q_un[0])
            print("      %-12s %s" % (arm, results[arm][idx]))
    print()

    print("=" * 78)
    print("WHAT THIS MEASURES, and what it does not")
    print("=" * 78)
    print()
    print("  IT MEASURES: whether the SUBSTRATE's state, given to the")
    print("  model, changes the answer from a plausible confabulation to")
    print("  the measured truth. That is the grounding gain, and it is the")
    print("  thing the architecture is supposed to buy.")
    print()
    print("  IT DOES NOT MEASURE: truth in general. The model is being")
    print("  asked about ITS OWN substrate, so the only claim is that the")
    print("  substrate is not decoration.")
    print()
    print("  AND THE LIMITS, stated: the questions are about a SIMULATED")
    print("  substrate, and the coupling law is a model rather than a")
    print("  bench measurement -- v6.2 section 7's build-one-coil-and-")
    print("  measure-L is still owed. So this measures the CONTROL")
    print("  STRUCTURE, not the physics.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
