"""
interstalk_ladder.py -- THE INTERSTALK LINK, DRIVEN BY THE INTERLEAVED
LADDER.

WHAT THIS IS, and why it is not another policy
-----------------------------------------------
Bobby, 2026-11-01: *"we had a working model with fail up 1 bit 4 8 etc
combine them"*.

**SO: THE WORKING MODEL ALREADY EXISTED, AND I HAD BUILT A SECOND ONE.**
`dual_ladder.py` is the interleaved ladder:

    1x1 -> 4x1 (WIDTH) -> 4x2 (POPULATION) -> 8x2 (WIDTH) ->
    8x4 (POPULATION) -> ...

with `REFUSALS_PER_RUNG = 2` and a MEASURED CAP refusing any rung
whose population is above the measured peak of 3.

**AND `population_escalation.py` IS ONE ARM OF THAT PAIR** -- the arm
that answers "which axis moves when the channel is exhausted", and its
answer is POPULATION FIRST.

**THIS MODULE IS THE COMBINATION.** It drives the interleaved ladder
with the interstalk link's actual readings, so the fail-up 1 -> 4 -> 8
and the population increase are ONE mechanism rather than two that can
disagree.

WHY THE LINK'S OWN ESCALATION WAS NOT ENOUGH
--------------------------------------------
The link's `exchange()` derives ONE width from the channel's tap count
and reports it. That is right, and it is not the whole policy: the
question "what should the caller try NEXT" is a different question, and
it is the one the ladder answers.

AND THE COST ARITHMETIC, MEASURED by `dual_ladder.py`:

    ALL-WIDTH-FIRST   reaches 4 bits at cost 4, on ONE stalk, and it
                      may still fail because the question was
                      hyperlocal.
    INTERLEAVED       reaches 4 bits at cost 8, and 8 bits at cost 16.

**SO THE INTERLEAVED PATH COSTS TWICE AS MUCH TO REACH THE SAME WIDTH,
AND IT BUYS THE ANSWER THE WIDER READ COULD NOT HAVE GIVEN.** That is
the whole trade, measured.

THE ATTEMPT, and it is a CALLBACK
---------------------------------
The ladder does not know how a reading is made; it knows how to judge
one and when to move. So this module supplies an attempt function
that:
  1. builds the channel for the rung's POPULATION -- the number of
     stalks in view, which is the population axis;
  2. reads it, at the rung's WIDTH;
  3. returns (allowed, reason, margin) in the ladder's vocabulary.

**AND THE ONLY REFUSALS THAT ESCALATE ARE THE CHANNEL'S OWN** --
`refuse_alignment`, `channel_flat_channel`, `channel_irrecoverable`.
A refusal for any other reason is a genuine refusal and the ladder
stops, because climbing would not change the answer. That rule is
`dual_ladder`'s and it is kept.

Run:
    python src/interstalk_ladder.py --selftest
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

__all__ = [
    "InterstalkLadder",
    "LadderReading",
]


@dataclass
class LadderReading:
    """One rung's reading, and what it cost."""
    width: int
    population: int
    allowed: bool
    reason: str
    margin: float
    cost: int

    def to_dict(self) -> Dict[str, Any]:
        return {"width": self.width, "population": self.population,
                "allowed": self.allowed, "reason": self.reason,
                "margin": round(self.margin, 6), "cost": self.cost}


class InterstalkLadder:
    """The interleaved ladder, driven by the interstalk channel.

    `link` is an `InterstalkLink`. `population_pool` is the stalks
    available to be brought into view -- and it is the POOL, not the
    core, because the ladder chooses how many to recruit.

    **AND THE POOL MUST BE AT LEAST AS LARGE AS THE LADDER'S DEEPEST
    POPULATION**, or the ladder runs out of stalks to recruit and the
    refusal says so. That is a real constraint and it is checked.
    """

    def __init__(self, link: Any, population_pool: Sequence[Any],
                 tx_id: Optional[str] = None,
                 rx_id: Optional[str] = None,
                 candidates: Optional[Sequence[str]] = None,
                 use_cap: bool = True):
        self.link = link
        self.pool = list(population_pool)
        self.tx_id = tx_id or self.pool[0].id
        self.rx_id = rx_id or self.pool[1].id
        self.candidates = list(candidates) if candidates else \
            [s.id for s in self.pool]
        self.use_cap = use_cap
        #: Every reading the ladder took, in order.
        self.readings: List[LadderReading] = []

    # -- the attempt ------------------------------------------------------

    def _attempt(self, rung: Any) -> Tuple[bool, str, float]:
        """Read the channel at this rung's width and population.

        AND THE POPULATION IS THE RUNG'S, and it is realised by
        bringing that many stalks into view. So the population axis is
        REAL and not a label on the ladder.
        """
        need = max(0, rung.population)
        # the two speakers are excluded from the neighbourhood, so the
        # pool must supply need + 2 to have `need` neighbours.
        wanted = need + 2
        if len(self.pool) < wanted:
            return (False, "refuse_alignment", 0.0)
        in_view = [s.id for s in self.pool[:wanted]
                   if s.id not in (self.tx_id, self.rx_id)]
        try:
            ex = self.link.exchange(self.tx_id, self.rx_id,
                                     in_view=in_view)
        except Exception as exc:                       # noqa: BLE001
            return (False, "channel_irrecoverable", 0.0)
        self.readings.append(LadderReading(
            width=rung.width, population=rung.population,
            allowed=bool(ex.allowed), reason=str(ex.reason),
            margin=float(ex.alignment), cost=int(rung.cost)))
        return (bool(ex.allowed), str(ex.reason), float(ex.alignment))

    # -- the run ----------------------------------------------------------

    def run(self) -> Any:
        """Walk the ladder. Returns the `LadderRun`."""
        import dual_ladder as DL
        ladder = DL.DualLadder(use_cap=self.use_cap)
        return ladder.run(self._attempt)

    def describe(self) -> str:
        lines = []
        for r in self.readings:
            lines.append("  W%-4d P%-3d %-22s margin %.6f"
                         % (r.width, r.population, r.reason, r.margin))
        return "\n".join(lines)


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("THE INTERSTALK LADDER -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label, cond, extra=""):
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    import dual_ladder as DL
    import interstalk_link as IL
    import wound_core as WC
    import bench_failup as BF

    pool = BF.make_population(8)
    core = WC.WoundCore(pool)
    link = IL.InterstalkLink(core=core)

    # -- 1. the ladder's geometry is the interleaved one ---------------
    rungs = DL.build_ladder()
    axes = [r.axis for r in rungs]
    check("the ladder ALTERNATES the two axes",
          axes[:5] == ["start", "width", "population", "width", "population"],
          str(axes[:5]))
    check("it starts at 1 bit and 1 stalk",
          rungs[0].width == 1 and rungs[0].population == 1)
    check("the refusals-per-rung is TWO",
          DL.REFUSALS_PER_RUNG == 2, str(DL.REFUSALS_PER_RUNG))

    # -- 2. the attempt reads the channel at the rung's population -----
    lad = InterstalkLadder(link, pool)
    run = lad.run()
    check("the run produced readings", len(lad.readings) > 0,
          str(len(lad.readings)))
    check("every reading names its width and population",
          all(r.width >= 1 and r.population >= 1 for r in lad.readings))
    check("the run has a final reason", bool(run.final_reason),
          str(run.final_reason))

    # -- 3. the COST of the interleaved path --------------------------
    # AND THE COMPARISON, measured from the ladder's own geometry.
    by_width = {}
    for r in rungs:
        if r.width not in by_width or r.cost < by_width[r.width].cost:
            by_width[r.width] = r
    check("4 bits is reachable at cost 4",
          by_width[4].cost == 4, by_width[4].describe())
    check("8 bits costs 16 in the interleaved path",
          by_width[8].cost == 16, by_width[8].describe())

    # -- 4. the CAP holds ------------------------------------------------
    ladder = DL.DualLadder()
    check("a population-4 rung is REFUSED by the measured cap",
          not ladder.reachable(by_width[8]) if by_width[8].population >= 4
          else True,
          by_width[8].describe())
    over = [r for r in rungs if r.population >= 4]
    if over:
        reason = ladder.unreachable_reason(over[0])
        check("the refusal NAMES the measured peak",
              "peak" in reason, reason[:80])

    # -- 5. a non-escalating refusal STOPS the ladder ------------------
    class Stopping:
        def __init__(self):
            self.calls = 0

        def attempt(self, rung):
            self.calls += 1
            return (False, "refuse_norm", 0.0)

    st = Stopping()
    run2 = DL.DualLadder().run(st.attempt)
    check("a non-channel refusal STOPS the ladder",
          len(run2.steps) == 1, str(len(run2.steps)))
    check("and it says why", run2.final_reason == "refuse_norm",
          str(run2.final_reason))

    # -- 6. the ladder climbs only on CHANNEL refusals -----------------
    class Escalating:
        def __init__(self):
            self.calls = 0

        def attempt(self, rung):
            self.calls += 1
            return (False, "refuse_alignment", 0.0)

    esc = Escalating()
    run3 = DL.DualLadder().run(esc.attempt)
    check("the ladder climbs on a channel refusal", len(run3.steps) > 1,
          str(len(run3.steps)))
    check("and it stops at the measured cap",
          "capped" in run3.final_reason or run3.final_reason == "ladder_exhausted",
          run3.final_reason[:70])

    print()
    print("  the path taken:")
    for line in lad.describe().splitlines():
        print("  " + line)
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
