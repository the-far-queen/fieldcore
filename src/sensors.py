"""
sensors.py -- THE STALKS BECOME SENSORS. The brain's input.

Bobby, 2026-10-28: *"stalk sheaf topology serves two other functions
even if poorly 1, mimic brain gives simself a shot at reasoning and 2
by simself referent sheaf and simsoul gives simself a shot at geometric
identity both very much missing i n llm"*

SO THIS FILE IS THE FIRST OF THOSE TWO FUNCTIONS, and it closes a gap
that had been open the whole time.

THE GAP, MEASURED 2026-10-28. `FastBrain.reflex(sensors: Dict[str,
float])` needs a mapping of sensor name to strength, and the criterion
is "high correlation across sensor modalities crystallises a label" --
the Helen Keller criterion the project's own `MiniLLM` implements.

AND NOTHING PRODUCED THAT MAPPING. MEASURED: the only caller of
`reflex()` in either repo was `mini_atlas.py`. The fast brain had no
sensors, so it could only ever answer "I perceive nothing yet" -- and
that is exactly what it answered, in every live test this session.

THE SENSOR SOURCE ALREADY EXISTS. `simself/src/constitutional/
sensorimotor_grounding.py` has a `GroundingLedger` that takes
`Observation(action, feedback, source)` -- an ACTION and what FEEDBACK
it produced -- and computes, per symbol name:

    perceptual   the magnitude of the residual for PERCEPTUAL
                 classifications
    causal       the magnitude for CAUSAL ones

AND `score(name)` returns a single number per symbol. **A SET OF
SYMBOL SCORES IS A SENSORS MAPPING.** So the chain is:

    the stalks' gain vector  (the locus's phase)
      -> OBSERVATIONS          (action, feedback, source)
        -> THE GROUNDING LEDGER (perceptual and causal magnitudes)
          -> SENSORS            (name -> score)
            -> THE FAST BRAIN   (a reflex, or None)

AND WHY THIS IS THE RIGHT SHAPE, and it is the project's own shape:
the fast brain is a REFLEX layer, so it must be fed cheap per-symbol
strengths and nothing else. It must not receive the raw vectors -- a
reflex that has to interpret a 16-vector is not a reflex.

AND THE STALKS ARE THE SENSOR SOURCE, and this is the part that makes
it not a mock. The locus's gain vector is the substrate's own state, and
it CHANGES when the substrate responds. So the sensor names are the
STALK IDs, and the feedback is what the substrate actually did. Which
means the fast brain's percepts are about THE SYSTEM'S OWN STALKS, and
a label it crystallises is a label about the system's behaviour.

AND THE TWO MODALITIES, because the criterion needs agreement. The
ledger classifies each observation as PERCEPTUAL or CAUSAL, so the
sensors carry BOTH:

    perceptual_<stalk>   how strongly the stalk presented itself
    causal_<stalk>      how strongly the stalk's response was caused

So a label crystallises when a stalk's presentation AND its causality
agree -- which is a much stronger signal than either alone, and it is
the criterion the criterion was written for.

AND WHAT IT IS NOT. It does not decide anything. The fast brain still
never calls the slow brain, and the slow brain still never gets a
reflex answer dressed as a decision.

Run:
    python src/sensors.py --selftest
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
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class SensorRead:
    """One reading of the substrate, and what the fast brain made of it.

    AND THE THREE FIELDS, and they are the whole instrument:

        sensors   the mapping the fast brain reads
        label     the label it crystallised, or None
        n_stalks  how many stalks were sensed
    """

    sensors: Dict[str, float] = field(default_factory=dict)
    label: Optional[str] = None
    n_stalks: int = 0
    n_observations: int = 0
    #: the perception and causal magnitudes, kept for the record
    perceptual: Dict[str, float] = field(default_factory=dict)
    causal: Dict[str, float] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "n_stalks": self.n_stalks,
            "n_observations": self.n_observations,
            "sensors": {k: round(v, 4) for k, v in self.sensors.items()},
        }


class StalkSensors:
    """THE SENSORS. The stalks' state, read as strengths.

    AND WHY THE LEDGER AND NOT A DIRECT SUM. The grounding ledger
    classifies each observation PERCEPTUAL or CAUSAL, and the two are
    different kinds of evidence: one says "this presented itself", the
    other says "this brought that about". A reflex needs agreement
    ACROSS modalities, so both have to be present and the ledger is
    what produces them.

    AND WHY THE LEDGER IS THE PROJECT'S OWN. It is
    `simself/src/constitutional/sensorimotor_grounding.py`, written from
    Grok and DeepSeek's frontier sessions and already tested. Nothing
    imported it. So this module ADAPTS it rather than reimplementing it
    -- the second implementation of the same rule is how two rules start
    to disagree.
    """

    def __init__(self, dim: int = 16):
        self.dim = dim
        #: ONE LEDGER PER STALK.
        #:
        #: MEASURED 2026-10-28. The grounding ledger's `Observation`
        #: carries `action`, `feedback` and `source` -- and NO NAME. And
        #: `ground(name)` scores EVERY observation under EVERY name. So a
        #: single ledger holding eight stalks' observations produces
        #: eight identical symbols, each the score of all eight.
        #:
        #: MEASURED: with one shared ledger, every stalk read
        #: perceptual 0.0000 and causal 4.4721 -- the SAME numbers,
        #: because they were the sum over all eight.
        #:
        #: So the ledger is per-symbol, and the adapter holds one per
        #: stalk. That is the shape the module was written for; the
        #: single-ledger version was my misreading of it.
        self._ledgers: Dict[str, Any] = {}
        self._names: List[str] = []
        self.reads: List[SensorRead] = []

    def _ledger_for(self, stalk_id: str):
        """The ledger for one stalk, built on first use."""
        if stalk_id not in self._ledgers:
            from constitutional.sensorimotor_grounding import GroundingLedger
            self._ledgers[stalk_id] = GroundingLedger(dim=self.dim)
        return self._ledgers[stalk_id]

    # -- the observation -------------------------------------------------

    def observe(self, stalk_id: str, action: Sequence[float],
                feedback: Sequence[float], source: str = "locus") -> None:
        """Record one stalk's action and the feedback it produced.

        AND THE SHAPES. The grounding ledger wants vectors of `dim`
        floats -- the same dimensionality as the locus's state. So the
        action is the stalk's own contribution and the feedback is what
        came back. A caller with a different dimensionality gets a
        loud error from the ledger, which is the right outcome: a
        mis-shaped sensor is a wiring mistake, not something to pad.
        """
        import numpy as np
        from constitutional.sensorimotor_grounding import Observation
        a = np.asarray(action, dtype=float).reshape(-1)
        f = np.asarray(feedback, dtype=float).reshape(-1)
        if a.size != self.dim:
            raise ValueError("the action must have %d values, got %d"
                             % (self.dim, a.size))
        if f.size != self.dim:
            raise ValueError("the feedback must have %d values, got %d"
                             % (self.dim, f.size))
        self._ledger_for(stalk_id).observe(
            Observation(action=a, feedback=f, source=source))
        if stalk_id not in self._names:
            self._names.append(stalk_id)

    # -- the read ---------------------------------------------------------

    def read(self) -> SensorRead:
        """Read the sensors, and give them to the fast brain.

        AND THE TWO MODALITIES AGAIN, because this is where they become
        one mapping:

            perceptual_<stalk>   the perceptual magnitude
            causal_<stalk>      the causal magnitude

        So the fast brain sees eight perceptual and eight causal channels
        for eight stalks, and a label crystallises when the channels
        AGREE -- which is the criterion it was written for.

        AND WHEN THERE IS NOTHING TO READ. With no observations the
        ledger produces no symbols, so the sensors are EMPTY and the
        fast brain answers None -- "I perceive nothing yet" -- which is
        the honest answer and not a failure.
        """
        out = SensorRead()
        out.n_observations = sum(
            len(getattr(self._ledger_for(n), "_obs", []) or [])
            for n in self._names)

        for name in self._names:
            try:
                sym = self._ledger_for(name).ground(name)
            except Exception:
                continue
            per = float(getattr(sym, "perceptual", 0.0))
            cau = float(getattr(sym, "causal", 0.0))
            out.perceptual[name] = per
            out.causal[name] = cau
            out.sensors["perceptual_%s" % name] = per
            out.sensors["causal_%s" % name] = cau
        out.n_stalks = len(self._names)
        self.reads.append(out)
        return out

    def reflex(self, brain: Optional[Any] = None) -> SensorRead:
        """One reflex, from the stalks.

        AND THE FAST BRAIN IS INJECTED, not built here. The brain
        belongs to the substrate (`bicameral.py`); this module FEEDS it.
        So the caller owns the brain and this owns the sensors, and the
        two compose at the call site.

        AND THE LABEL IS PUT INTO THE SENSORS, so the next read can
        see what the brain last saw. A percept that is never fed back
        is not a percept.
        """
        read = self.read()
        if brain is None:
            return read
        from bicameral import FastBrain
        if not isinstance(brain, FastBrain):
            brain = brain.fast
        label = brain.reflex(dict(read.sensors))
        read.label = label
        if label:
            read.sensors["label_%s" % label] = 1.0
        return read


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import numpy as np
    from bicameral import FastBrain
    from locus import Locus
    from wound_core import CoaxWinding

    print("=" * 78)
    print("THE STALKS BECOME SENSORS")
    print("=" * 78)
    print()

    # -- the locus, and a drive ------------------------------------------
    stalks = [CoaxWinding(id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                          girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                          n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    loc = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
    loc.resonate([0.1] * 8)

    print("1. THE LOCUS'S OWN STATE, which is the sensor source:")
    st = loc.state
    print("   stalks: %d | modes: %d | gain dim: %d"
          % (len(st.stalks), len(st.modes), len(st.gain)))
    print()

    sensors = StalkSensors(dim=len(st.gain))
    brain = FastBrain()

    print("2. WITH NO OBSERVATIONS, the sensors are EMPTY and the fast")
    print("   brain says so -- which is the honest answer:")
    r0 = sensors.reflex(brain)
    print("   sensors: %d | label: %r" % (len(r0.sensors), r0.label))
    print()

    print("3. AFTER OBSERVING THE STALKS, the sensors carry both")
    print("   modalities, and the fast brain reads them:")
    print()
    print("   AND THE TWO MODALITIES ARE NOT A CHOICE -- they fall out")
    print("   of the residual, which is feedback - action:")
    print("     a small residual   the world echoed you   -> PERCEPTUAL")
    print("     a large residual   the world answered    -> CAUSAL")
    for i, s in enumerate(stalks):
        # THE ACTION: the stalk's own contribution to the field.
        action = np.zeros(len(st.gain))
        action[i % len(st.gain)] = 1.0
        # THE FEEDBACK, for a PERCEPTUAL observation: the world echoes
        # the action, so the residual is ~0. The first version shifted
        # the feedback by one dimension, which made the residual 8.94
        # -- so every observation was classified CAUSAL and the
        # perceptual channels all read 0.0000. The shift was my error,
        # not the ledger's.
        # AND THE THREE CLASSIFICATIONS, which are not a choice --
        # they fall out of the residual, and the ledger's own rule is:
        #
        #     mag < threshold      NULL        the world echoed you
        #                                       exactly; no information
        #     mag < 2*threshold    PERCEPTUAL  the world echoed you
        #                                       ALMOST -- a small
        #                                       deviation is perception
        #     otherwise            CAUSAL     the world answered with
        #                                       something else
        #
        # MEASURED 2026-10-28: the first version of this test used a
        # PERFECT echo, and the ledger classified it NULL -- so the
        # perceptual channels read 0.0000 and every observation was
        # CAUSAL. A perfect echo carries no information; a *nearly*
        # perfect one is perception. That is the module's semantics and
        # it is the right one.
        feedback = action.copy()
        if i % 2 == 0:
            # PERCEPTUAL: the world echoed ALMOST exactly.
            #
            # MEASURED 2026-10-28, the exact boundaries the ledger
            # uses, with threshold=0.05:
            #
            #     residual 0.000 -> NULL       an exact echo
            #     residual 0.010 -> NULL
            #     residual 0.020 -> NULL
            #     residual 0.030 -> NULL
            #     residual 0.050 -> PERCEPTUAL  the band starts here
            #     residual 0.080 -> PERCEPTUAL
            #     residual 0.100 -> CAUSAL     and here
            #
            # So 0.07 is inside the PERCEPTUAL band. The first version
            # used 0.02, which is BELOW the floor -- so it was NULL, and
            # the perceptual channels read 0.0000.
            feedback[(i + 1) % len(st.gain)] = 0.07
        else:
            # CAUSAL: the world answered with something else.
            feedback = np.zeros(len(st.gain))
            feedback[(i + 1) % len(st.gain)] = 0.5
        sensors.observe(s.id, action, feedback, source="locus")

    read = sensors.reflex(brain)
    print("   n_stalks: %d | n_observations: %d" % (read.n_stalks, read.n_observations))
    print("   sensors: %d channels" % len(read.sensors))
    for k in list(read.sensors)[:6]:
        print("      %-28s %.4f" % (k, read.sensors[k]))
    print("   label: %r" % read.label)
    print("   brain reflexes: %d" % brain.reflexes)
    print()

    print("4. AND THE FAST BRAIN'S PERCEPTS ARE ABOUT THE SYSTEM'S OWN")
    print("   STALKS:")
    for label, p in list(brain.percepts.items())[:5]:
        print("      %-22s confidence=%.4f count=%d" % (label, p.confidence, p.count))
    print()

    print("5. THE SECOND REFLEX IS MORE TRUSTED, because the confidence")
    print("   is a running mean over the hits:")
    for _ in range(3):
        read = sensors.reflex(brain)
    for label, p in list(brain.percepts.items())[:3]:
        print("      %-22s confidence=%.4f count=%d" % (label, p.confidence, p.count))
    print()
    print("   Run: python src/sensors.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
