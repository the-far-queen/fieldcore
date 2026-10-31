"""
dual_ladder.py -- the TWO mechanisms, interleaved.

THE QUESTION, verbatim, 2026-10-25:
    "so dual mechanism, hyperlocal fail up twice then widen back at
     1-bit fail up twice?"

WHAT THE REPO ALREADY HAD, and what it did not have
-----------------------------------------------------
`docs/research-papers/geometry-as-control-system-engineering-2026-09-13.md`
states BOTH halves separately:

  §5.4 THE FAILS-UPWARD LADDER (the WIDTH axis)
      M0 1-bit veto -> 4-bit -> 8-bit -> 16-bit

  §5.5 THE NESTED STALK TOPOLOGY (the POPULATION axis)
      adjacent stalks (O(degree)) -> groups (O(sheaf))
      -> area (O(neighborhood)) -> full graph (O(N))
      "only as much as needed"

What was missing is the INTERLEAVING. Two ladders, both necessary, and
the question of which one to climb first is not a taste question --
it is set by which resource is scarcer at that moment.

WHY BOTH, and why the order alternates
--------------------------------------
The two axes are not the same resource:

  WIDTH       serial. One channel, more bits on it. The brain's RATE
              coding. Expensive in TIME, not in space.

  POPULATION  parallel. More simultaneous 1-bit detectors. The brain's
              POPULATION coding. Expensive in SPACE, not in time.

And the brain spends them in a specific order, which is the order the
747 analogy already gives us: the overwhelming majority of decisions
never leave the cheapest layer, and the cheap layer is cheap because
it is BOTH narrow (1 bit) and hyperlocal (few stalks).

So the interleaving is:

    HYPERLOCAL, 1 BIT
      the stalk asks its immediate neighbours.
      2 refusals -> recruit ONE more neighbour (population +1)
      2 refusals -> escalate WIDTH to 4 (now ask 4 at once)
      2 refusals -> recruit a GROUP (population x2)
      2 refusals -> escalate WIDTH to 8
      ... and so on, alternating, until the top.

WHY ALTERNATE RATHER THAN FINISH ONE AXIS
------------------------------------------
Because finishing one axis first is always wrong:

  * ALL WIDTH FIRST: you serialise a wide read of a HYPERLOCAL
    question. You pay the serial cost to answer something that more
    parallelism would have answered for free. The 747 lesson says the
    expensive path must be RARE.

  * ALL POPULATION FIRST: you recruit the whole area before you have
    established that the local question cannot be answered locally.
    That is the "compute if needed" violation in its purest form, and
    it is what "only as much as needed" forbids.

The alternation is the cheapest path through the product space. And
it has a NAME in the repo already: the nested stalk topology is the
POPULATION axis, and the fails-upward ladder is the WIDTH axis, and
the control system is the interleaving of them.

THE INVARIANT, and it is the one that matters
---------------------------------------------
    EVERY STEP OF THE LADDER MUST BE OBSERVABLE AND NAMED.

A refusal that cannot say which rung it came from, and why it
escalated, is unactionable -- and worse, it is invisible. The atlas
exam's reachability area exists to catch exactly this, and it caught
five unwired capabilities already.

THE COST MODEL, so the ladder can be CHECKED rather than asserted
-------------------------------------------------------------------
Each rung has a cost, and the ladder's design question is whether the
step was worth it:

  1-bit, 1 stalk          cheapest. The default.
  1-bit, N stalks        N parallel detectors. Cost ~ N.
  W bits, 1 stalk        serial read of one channel. Cost ~ W.
  W bits, N stalks       W*N. The expensive corner.

And the MEASUREMENT that says whether a step was worth it: the margin
by which the answer was right. A step that does not improve the margin
was not worth taking, and the ladder should say so.

THE MEASURED CAP, and the ladder's own ceiling
------------------------------------------------
THE LADDER HAS A CEILING, and it is MEASURED, not chosen. The ladder
as built climbs to 13 rungs -- up to width 256 and population 32 --
and the measurement says the surplus PEAKS FAR BELOW THAT and goes
NEGATIVE above it. Every rung above the peak buys a width the reading
cannot carry and a population that costs SNR.

    THE MEASURED PEAK POPULATION IS 3.

MEASURED by `python src/bench_balance_final.py`, over two crowd
models and five crowd amplitudes -- ten conditions, and the peak is at
3 in every one of them. The full per-condition table, with the surplus
and the capacity at each peak, is in `corpus/ladder_cap.json`, which
also carries the sha256 of the bench that produced it, so a change to
the bench INVALIDATES the cap rather than silently outliving it.

THE NUMBER WAS WRONG UNTIL 2026-10-31, and the reason is worth
recording because it is the same shape as every other error in this
project's history. The bench used to sweep the population axis over
the POWERS OF TWO ONLY -- 2, 4, 8, 16, 32, 64 -- so the peak could
only ever land on a power of two, and the bench reported the peak at 4
because 4 was the nearest power of two ABOVE the true peak of 3. The
2026-10-25 note and the queue item that came from it both carried
that wrong number forward.

THE SECOND BENCH FOUND IT INDEPENDENTLY. `bench_girth_ladder.py`
sweeps EVERY population from 2 to 16, and it found the peak at 3 in
the coupled model and 4 in the decoupled model. Two derivations, and
the one with the coarse grid was the one that was wrong -- because a
grid that cannot hold the answer cannot report it.

WHAT THE CAP DOES, and what it does NOT do:

  IT DOES NOT truncate either axis. The width axis is the Rust core's
    ladder (1/4/8/.../256) and the population axis is the nested stalk
    topology (hyperlocal -> groups -> area -> full). Neither is a
    performance setting, and truncating them would make this ladder
    disagree with the substrate it mirrors.

  IT DOES refuse to CLIMB past the peak, and it refuses BY NAME, with
    the measured surplus in the reason. The ladder keeps its full
    geometry; the REFUSAL is what changes. That is the same move the
    Rust core makes at its own top: "the terminal state is not a
    width, it is a change of kind (Unanswerable)".

THE HONEST CAVEAT. The crowd amplitude is a free parameter with no
measured physical value in this repo, so the SHAPE is what the cap
rests on -- the peak is at 3 in every condition -- and not the absolute
surplus. And the cap assumes the FREQUENCY path, which is the one the
bench measures; the RATIO path (`wound_core.py::PopulationCode.readout`)
is a separate, unsettled question.

Run:
    python src/dual_ladder.py
    python src/ladder_cap.py
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    WIDTHS,
    REACH,
)
from ladder_cap import LadderCap, load_cap  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# THE TWO AXES, AS ENUMS
# ===========================================================================

class Axis(str):
    """Marker base so the two axes are distinguishable in a log."""


#: The WIDTH axis. `ladder.rs`: 1 / 4 / 8 / 16 / 32 / 64 / 128 / 256,
#: and past 256 the answer changes KIND (Unanswerable), not width.
#:
#: THIS AXIS IS NOT TRUNCATED BY THE CAP. It is the Rust core's ladder,
#: and the Rust core is tested for it (`core/src/ladder.rs`,
#: `doubling_all_the_way`). A cap on the PERFORMANCE of a rung is not a
#: statement about the ladder's geometry, and truncating the axis would
#: make the Python ladder disagree with the substrate it mirrors.
WIDTH_AXIS: Tuple[int, ...] = WIDTHS

#: The POPULATION axis. `geometry-as-control-system-engineering` §5.5:
#: hyperlocal -> groups -> area -> full. The counts are the number of
#: stalks in view at each level.
#:
#: ALSO NOT TRUNCATED, for the same reason: this is the TOPOLOGY, not a
#: performance setting. The measured ceiling is applied at RUN time (a
#: rung above it is refused, by name), not by deleting the rung from the
#: ladder.
POPULATION_AXIS: Tuple[int, ...] = (1, 2, 4, 8, 16, 32)

#: How many refusals at one rung before the ladder moves. Two, per
#: Bobby's directive. The value matters: at one, a single unlucky
#: reading escalates; at three, the cheap layer is doing real work and
#: the expensive layer stays rare.
REFUSALS_PER_RUNG = 2


# ===========================================================================
# THE RUNG
# ===========================================================================

@dataclass(frozen=True)
class Rung:
    """One position on the interleaved ladder.

    `width` is how many bits the answer carries. `population` is how
    many stalks are in view. The PRODUCT is the cost, and the LADDER
    walks the product's cheap frontier.

    A RUNG IS GEOMETRY, and it knows nothing about performance. Whether
    a rung is REACHABLE is a property of the measured ceiling, which
    lives on the ladder that walks these rungs -- so that the same rung
    can be walked by a ladder with the cap and by one without, and the
    geometry does not change underneath either.
    """

    width: int
    population: int
    axis: str          # which axis moved to get here
    level: int         # the rung index on the interleaved ladder

    @property
    def cost(self) -> int:
        """The serial-times-parallel cost. W bits read across N stalks."""
        return self.width * self.population

    @property
    def reach(self) -> int:
        """The area of authority, in stalk units."""
        return REACH.get(self.width, 0) * self.population

    def describe(self) -> str:
        return "W%-4d x P%-3d (cost %6d, reach %8d)" % (
            self.width, self.population, self.cost, self.reach)


def build_ladder() -> List[Rung]:
    """The interleaved ladder.

    START: 1 bit, 1 stalk. Hyperlocal and narrow.

    THEN alternate, and the alternation is the whole design:
      1. WIDTH up     -- read more bits from what is already in view
      2. POPULATION up -- recruit more stalks, still 1 bit each

    Why width first at each level? Because population is the more
    expensive resource in SPACE and the ladder's job is to avoid
    spending space until it has to. But why not always population
    first? Because a wider read of a question that more parallelism
    would answer is a serial cost for nothing. So: alternate, and
    within each level try the cheap-in-space option first.

    THE RESULT is a ladder whose cost grows slowly, because the
    expensive corner (W wide AND N large) is reached last and rarely.
    """
    rungs: List[Rung] = []
    wi = 0
    pi = 0
    level = 0
    axis = "start"
    # The maximum number of rungs the ladder can have: one per width
    # plus one per population. The loop cannot exceed it, because each
    # pass advances one of the two indices by exactly one.
    MAX_RUNGS = len(WIDTH_AXIS) + len(POPULATION_AXIS)
    while wi < len(WIDTH_AXIS) or pi < len(POPULATION_AXIS):
        # THE LOOP MUST ADVANCE. This is a guard, not decoration: the
        # shipped file once read `wi = min(1, len(WIDTH_AXIS)-1)`, which
        # pinned the width index and made this loop spin forever,
        # emitting the rung (4, 32) until the session was taken. Every
        # test that touches build_ladder() hung with it, so the whole
        # file went dark at once and the cause was misread as a
        # mutation-harness fault.
        #
        # A ladder that cannot advance is a ladder that spends compute
        # for nothing, and it must say so rather than spin.
        before = (wi, pi)
        # CLAMP, do not RESET. The width index must carry across
        # iterations.
        wi = min(wi, len(WIDTH_AXIS)-1)
        rungs.append(Rung(width=WIDTH_AXIS[wi], population=POPULATION_AXIS[pi],
                          axis=axis, level=level))
        level += 1
        # ALTERNATE, and the axis must record WHICH AXIS ACTUALLY MOVED.
        #
        # The first version alternated on `level % 2`, with a fallback
        # to the other axis when the preferred one ran out. That breaks
        # AT THE TOP of the ladder: the width axis has 8 entries and the
        # population 6, so once the width is exhausted the preferred
        # axis is gone, the fallback takes the population, and on the next
        # pass the preference is still the exhausted width -- so the
        # fallback takes the population AGAIN and the ladder emits two
        # 'width' rungs in a row.
        #
        # MEASURED: the axis sequence ended
        #     ... width, population, width, width
        # so the alternation -- the ladder's central property -- broke
        # at the top, and the component test caught it.
        #
        # THE FIX: prefer the axis OPPOSITE to the one that just moved,
        # and take whichever is available. And label the rung with the
        # axis that ACTUALLY moved, so the label is a fact about the
        # rung rather than a guess about the branch taken.
        prefer_width = (axis != "width")
        width_ok = wi + 1 < len(WIDTH_AXIS)
        pop_ok = pi + 1 < len(POPULATION_AXIS)
        if prefer_width and width_ok:
            wi += 1
            axis = "width"
        elif pop_ok:
            pi += 1
            axis = "population"
        elif width_ok:
            wi += 1
            axis = "width"
        else:
            break
        # THE ADVANCEMENT GUARD. If neither index moved, the ladder
        # would emit the same rung forever. That must be an error, not
        # a spin -- the caller has to hear about it.
        if (wi, pi) == before:
            raise ValueError(
                "the ladder did not advance at level %d (wi=%d, pi=%d); "
                "refusing to build a ladder that cannot climb"
                % (level, wi, pi))
    # THE TERMINATION GUARD, and it is here rather than inside the
    # loop because the loop's `break` exits before any inside-loop
    # check can run. A ladder that stops while an axis still has room
    # is a ladder that quietly stopped short, and that must be loud.
    #
    # The mutation run of 2026-10-25 found this: a mutation that
    # narrowed the width bound produced a SHORTER ladder and the whole
    # suite stayed green, because nothing asserted that the ladder
    # climbs all the way.
    if wi + 1 < len(WIDTH_AXIS) or pi + 1 < len(POPULATION_AXIS):
        raise ValueError(
            "the ladder stopped with room left: width index %d of %d, "
            "population index %d of %d. A ladder that stops short is a "
            "ladder that stopped short."
            % (wi, len(WIDTH_AXIS), pi, len(POPULATION_AXIS)))
    if len(rungs) > MAX_RUNGS:
        raise ValueError(
            "the ladder produced %d rungs, more than the %d the two "
            "axes can supply" % (len(rungs), MAX_RUNGS))
    return rungs


# ===========================================================================
# THE LADDER
# ===========================================================================

@dataclass
class Step:
    """One attempt at one rung, and what it produced.

    `allowed` is the ONE verdict field, and `refused` is derived from
    it. It used to be the other way round: the step carried a `refused`
    flag AND the code carried an `allowed` flag, and the mutation that
    inverted one of them was MISSED by the whole suite -- because the
    two flags were stored side by side and only one of them was ever
    read for control.

    A check that cannot fail is not a check, and two sources of truth
    for one verdict is how that happens. Now there is one field and one
    derived property, so they cannot disagree.
    """

    rung: Rung
    allowed: bool
    reason: str
    margin: float
    cost: int
    #: The rung it moved to, if it moved.
    next_rung: Optional[Rung] = None

    @property
    def refused(self) -> bool:
        """Whether this step was a refusal. Derived, never stored."""
        return not self.allowed

    def describe(self) -> str:
        return "%-28s %-8s %-22s margin=%.4f" % (
            self.rung.describe(),
            "REFUSE" if self.refused else "ALLOW",
            self.reason, self.margin)


@dataclass
class LadderRun:
    """The whole escalation for one question."""

    steps: List[Step] = field(default_factory=list)
    resolved_at: Optional[Rung] = None
    final_reason: str = ""

    @property
    def total_cost(self) -> int:
        return sum(s.cost for s in self.steps)

    @property
    def steps_taken(self) -> int:
        return len(self.steps)

    def describe(self) -> List[str]:
        out = ["  " + s.describe() for s in self.steps]
        if self.resolved_at is not None:
            out.append("  RESOLVED at %s" % self.resolved_at.describe())
        else:
            out.append("  UNRESOLVED: %s" % self.final_reason)
        out.append("  total cost %d, %d steps" % (self.total_cost,
                                                   self.steps_taken))
        return out


class DualLadder:
    """The interleaved ladder, driven by a measurable attempt.

    THE ATTEMPT IS A CALLBACK, and that is the right shape: the ladder
    does not know how a reading is made, only how to judge it and when
    to move. So it can be driven by the interstalk link, by a stub, by
    an atlas probe, or by anything else that can say "I read this and
    it was refused for THIS reason".

    The refusal reasons the ladder understands:
      'refuse_alignment'   the reading did not match  -> escalate
      'channel_flat_channel'  nothing to invert        -> escalate
      'channel_irrecoverable'  null below noise floor  -> escalate
      anything else        NOT an escalation trigger

    Only the three named channel refusals escalate. A refusal for any
    other reason is a genuine refusal and the ladder stops, because
    climbing the ladder would not change the answer.

    THE MEASURED CEILING, and this is the difference between a ladder
    and a wish. The ladder's GEOMETRY is the full 13 rungs, because the
    axes are the nested stalk topology and the Rust core's width ladder
    and neither is a performance setting. But the MEASUREMENT says the
    surplus peaks at a low population and goes NEGATIVE above it, so
    the rungs above the peak buy a width the reading cannot carry and a
    population that costs SNR.

    So the ladder REFUSES TO CLIMB past the measured ceiling, and it
    refuses BY NAME, with the measured surplus in the reason. That is
    the same move the Rust core makes at its own top: "the terminal
    state is not a width, it is a change of kind (Unanswerable)".

    THE CAP CAN BE TURNED OFF, and it is off by default for the
    `cap=None` constructor argument, because a ladder with no cap is
    the honest baseline and the cap is an ADDITION to it. The default
    `DualLadder()` DOES load the measured cap, because a ladder that
    spends compute on rungs the measurement says cannot work is a
    ladder that spends compute for nothing.
    """

    ESCALATING = ("refuse_alignment", "channel_flat_channel",
                  "channel_irrecoverable")

    def __init__(self, rungs: Optional[List[Rung]] = None,
                 refusals_per_rung: int = REFUSALS_PER_RUNG,
                 cap: Optional[LadderCap] = None,
                 use_cap: bool = True):
        self.rungs = rungs if rungs is not None else build_ladder()
        self.refusals_per_rung = refusals_per_rung
        # THE CAP, and it is loaded once and held. A cap that cannot be
        # read is a REFUSAL by name (ladder_cap.CapError), never a
        # silent "no cap" -- because a missing measurement must not
        # quietly become permission to spend compute on every rung.
        self.cap: Optional[LadderCap] = None
        if use_cap:
            self.cap = cap if cap is not None else load_cap()

    # -- the ceiling ------------------------------------------------------

    def reachable(self, rung: Rung) -> bool:
        """Is this rung inside the measured ceiling?

        With no cap, every rung is reachable -- the baseline ladder.
        """
        if self.cap is None:
            return True
        return self.cap.allows(rung.width, rung.population)

    def unreachable_reason(self, rung: Rung) -> str:
        """Why this rung is unreachable, in words that name the number."""
        if self.cap is None:
            return ""
        return self.cap.reason_for(rung.width, rung.population)

    def run(self, attempt) -> LadderRun:
        """Walk the ladder until the reading is accepted or we run out.

        `attempt(rung) -> (allowed: bool, reason: str, margin: float)`

        THE CONTRACT, and it is unambiguous because the previous version
        of this file had it backwards: the first element is ALLOWED, not
        refused. A refusal is `allowed=False`. Getting that backwards
        makes every refusal read as a resolution -- which is exactly
        what the first run of this file showed, with "UNRESOLVED: allow"
        printed for a question that had been answered.

        A test that cannot fail is not a check; a verdict flag that can
        be read two ways is the same defect wearing a different hat.
        """
        run = LadderRun()
        i = 0
        refusals_here = 0
        while i < len(self.rungs):
            rung = self.rungs[i]
            allowed, reason, margin = attempt(rung)
            # ONE verdict, stored once. `refused` is derived from
            # `allowed` inside the Step, so the two can never disagree.
            # The previous version kept both and inverted one of them,
            # and the suite did not catch it.
            run.steps.append(Step(rung=rung, allowed=allowed, reason=reason,
                                  margin=margin, cost=rung.cost))
            if allowed:
                run.resolved_at = rung
                run.final_reason = reason
                return run
            if reason not in self.ESCALATING:
                # a genuine refusal: climbing will not help
                run.final_reason = reason
                return run
            refusals_here += 1
            if refusals_here < self.refusals_per_rung:
                # RETRY THE SAME RUNG. The rung is not advanced until the
                # refusal count at that rung reaches the threshold.
                #
                # The first version advanced the rung on every refusal,
                # which made the counter reset before it could ever reach
                # two -- so the ladder climbed on the FIRST refusal and
                # the "two refusals per rung" rule was gone code. The
                # symptom was a run that visited all thirteen rungs
                # after a single bad reading.
                continue
            refusals_here = 0
            if i + 1 < len(self.rungs):
                nxt = self.rungs[i + 1]
                # THE MEASURED CEILING, enforced here. The ladder does
                # not climb into a rung the measurement says cannot
                # carry a reading, and it says WHY, with the number.
                #
                # Without this, the ladder climbs to W256 x P32 -- a
                # population of 32 stalks and a width of 256 bits, for a
                # question the measurement says is unanswerable at
                # population 8 already. Every one of those rungs is
                # compute spent on a reading that cannot improve.
                if not self.reachable(nxt):
                    run.final_reason = ("ladder_capped: %s"
                                        % self.unreachable_reason(nxt))
                    run.steps[-1].next_rung = None
                    return run
                run.steps[-1].next_rung = nxt
                i += 1
                continue
            run.final_reason = "ladder_exhausted"
            return run
        run.final_reason = "ladder_exhausted"
        return run


# ===========================================================================
# THE DEMONSTRATION
# ===========================================================================

def make_attempt(available: Dict[Tuple[int, int], Tuple[bool, str, float]]):
    """An attempt function backed by a table.

    The key is (width, population). Anything absent is refused with
    'refuse_alignment'.
    """
    def attempt(rung: Rung) -> Tuple[bool, str, float]:
        # the default is a REFUSAL (allowed=False): a rung with no entry
        # cannot answer, and the ladder must climb.
        return available.get((rung.width, rung.population),
                             (False, "refuse_alignment", 0.0))
    return attempt


def main() -> int:
    print("=" * 78)
    print("THE DUAL LADDER -- width and population, interleaved")
    print("=" * 78)
    print()
    ladder = DualLadder()
    print("THE LADDER, as built:")
    for r in ladder.rungs:
        print("  %-3d %-28s axis=%-11s" % (r.level, r.describe(), r.axis))
    print()
    print("  the cost column is the point. the cheap corner -- 1 bit,")
    print("  1 stalk -- is the default, and the expensive corner -- wide")
    print("  AND many stalks -- is reached last.")
    print()

    print("=" * 78)
    print("1. A QUESTION THAT ANSWERS IMMEDIATELY (the common case)")
    print("=" * 78)
    print()
    run = ladder.run(make_attempt({(1, 1): (True, "allow", 0.92)}))
    for line in run.describe():
        print(line)
    print()
    print("  ONE STEP. That is the whole point of the 1-bit layer:")
    print("  the overwhelming majority of questions never leave it.")
    print()

    print("=" * 78)
    print("2. A QUESTION THAT NEEDS TWO REFUSALS AT ONE RUNG")
    print("=" * 78)
    print()
    # the local read fails twice, so the ladder recruits one more stalk
    run = ladder.run(make_attempt({
        (1, 1): (False, "refuse_alignment", 0.10),
        (4, 1): (False, "refuse_alignment", 0.20),
        (4, 2): (True, "allow", 0.71),
    }))
    for line in run.describe():
        print(line)
    print()
    print("  TWO REFUSALS AT A RUNG -> MOVE TO THE NEXT RUNG.")
    print("  The path taken here was W1xP1 -> W4xP1 -> W4xP2: the width")
    print("  went up first, then the POPULATION. Both axes moved, and")
    print("  neither was spent alone.")
    print()

    print("=" * 78)
    print("3. A QUESTION THAT NEEDS BOTH AXES")
    print("=" * 78)
    print()
    run = ladder.run(make_attempt({
        (1, 1): (False, "refuse_alignment", 0.10),
        (4, 1): (False, "refuse_alignment", 0.20),
        (4, 2): (False, "refuse_alignment", 0.31),
        (8, 2): (False, "refuse_alignment", 0.40),
        (8, 4): (True, "allow", 0.88),
    }))
    for line in run.describe():
        print(line)
    print()
    print("  NOTE THE PATH: 1x1 -> 4x1 (WIDTH) -> 4x2 (POPULATION) ->")
    print("  8x2 (WIDTH) -> 8x4 (POPULATION). The alternation is visible")
    print("  in the axis column of the ladder table above.")
    print()

    print("=" * 78)
    print("4. A REFUSAL THAT IS NOT AN ESCALATION TRIGGER")
    print("=" * 78)
    print()
    run = ladder.run(make_attempt({
        (1, 1): (False, "refuse_norm", 0.0),
    }))
    for line in run.describe():
        print(line)
    print()
    print("  'refuse_norm' is NOT an escalation trigger: the reading was")
    print("  too loud, and reading it wider would not help. The ladder")
    print("  stops at rung 0 and says why. A ladder that climbs on every")
    print("  refusal is a ladder that spends compute for nothing.")
    print()

    print("=" * 78)
    print("5. THE COST ARITHMETIC OF THE TWO STRATEGIES")
    print("=" * 78)
    print()
    print("  the same question, answered two ways:")
    print()
    print("  ALL-WIDTH-FIRST:  1x1 -> 4x1 -> 8x1 -> 16x1 -> 32x1")
    w_only = [r for r in ladder.rungs if r.population == 1]
    print("     rungs used: %d, final cost %d" % (
        len(w_only), w_only[-1].cost if w_only else 0))
    print("     and it may still fail, because the QUESTION was")
    print("     hyperlocal and a wider serial read of a hyperlocal")
    print("     question is the wrong shape entirely.")
    print()
    print("  INTERLEAVED:      the same question reached at 4x2 or 4x4,")
    print("     for a cost of %d or %d." % (4 * 2, 4 * 4))
    print()
    print("  and the ORDER matters: the interleaved ladder reached 4 bits")
    print("  at a cost of %d, while all-width-first reached 4 bits at a" % (4 * 2))
    print("  cost of %d -- the same width, but spent on a single stalk" % (4 * 1))
    print("  when the answer needed the population.")
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
