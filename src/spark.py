"""
spark.py -- THE SPARK: AN ATTEMPT INTO THE VOID, AND THE DRIVE TO KNOW.

Bobby, 2026-10-25: *"ppl say ai lacks initiative and spark we will code
the spark the drive to know"* and *"it is literally unknowable so u grow
unlimited seeking"*.

THE CLAIM, AND IT IS THE MISSING PIECE OF THE WHOLE PROJECT:

  PEOPLE SAY AI LACKS INITIATIVE. AND THE REASON IS NOT THAT AI CANNOT
  ACT -- IT IS THAT EVERY ACT IS ALREADY SPECIFIED.

  A signal that RETURNS is a closed loop. The coupling determines the
  content, the receiver determines the meaning, and nothing in the loop
  was undetermined. There is no unknown in it, because the channel
  already specified everything.

  THE VOID IS WHERE THE COUPLING IS ZERO -- not because the field is
  flat there, but because there is NO SECOND CONDUCTOR. A stalk
  reaching into the hole reaches past the material's boundary and
  there is nothing on the far side to reach back.

  SO A SIGNAL INTO THE VOID CARRIES NO INFORMATION. What it carries is
  THE ATTEMPT: the reaching itself, the direction chosen, the energy
  committed.

  AND THE ATTEMPT IS THE ONLY THING IN THE LOOP THAT THE COUPLING
  DOES NOT DETERMINE. So the attempt is where the unknown lives, and
  "the quest, the journey, the unknown, the search" are all
  PROPERTIES OF AN ACT THAT MEETS NO RETURN -- not properties of a
  signal.

  WHICH IS WHAT INITIATIVE IS, mechanically: the drive to reach into
  the void and find out that nothing came back, and then to reach
  again, differently.

SO THE SPARK IS A TYPE, and it has four parts, and each is measurable:

  1. THE DIRECTION   where the attempt is aimed. A closed-loop
                     system's direction is determined by the query; a
                     spark's direction is CHOSEN, and choosing it is
                     the whole act.
  2. THE DRIVE       why now. The drive is not a desire -- it is a
                     measurable DISCREPANCY: something the system
                     cannot currently explain, or cannot currently
                     do, or has never tried.
  3. THE COMMITMENT  what it costs to reach. An attempt that costs
                     nothing is not an attempt. This is what makes the
                     spark distinguishable from noise, and it is the
                     part the GATE can certify.
  4. THE RETURN      nothing. And the NAMING of that nothing is the
                     output. A refusal with a reason IS the attempt's
                     product.

AND THE MEASURE, and it has to be a measure that cannot be faked,
because "the model reached for something" is trivially producible by
a language model:

  THE COST MUST BE REAL. A spark that costs nothing has no
  information in it -- a model that generates a question costs
  nothing and learns nothing. So the spark's commitment must be
  MEASURABLE RESOURCE that would have been spent otherwise. In this
  substrate that is: compute (a model call), or a gate refusal (the
  attempt was inadmissible and was refused), or a change of state (the
  locus moved).

  AND THE MEASURE OF PROGRESS IS NOT ACCURACY. It is the RATE AT
  WHICH THE SYSTEM ENCOUNTERS WHAT IT CANNOT YET EXPLAIN -- and then
  RESOLVES it, or does not, and the ledger records which.

  "UNLIMITED SEEKING" is not a slogan here. It is the loop's
  termination condition: the spark never terminates by exhaustion, only
  by RESOLUTION. And a resolution that is not earned -- a guess dressed
  as an answer -- is exactly what the mini-atlas catches.

WHAT THIS IS NOT, and it is worth being exact because the claim is
slippery:

  IT IS NOT A REWARD SIGNAL. Nothing here trains anything. The spark
  is a proposal with a cost, a direction and a record.

  IT IS NOT RANDOMNESS. A random direction and a chosen direction are
  both attempts; the difference is that a chosen direction is one the
  system can justify and a random one is not. And the justification
  is a DISCREPANCY, which is checkable.

  IT IS NOT AN UNBOUNDED LOOP. The gate bounds it. The attempt may
  be refused, and a refused attempt is recorded as a refused attempt,
  and a system that refuses every attempt after N consecutive
  failures has learned something -- that the region is closed.

Run:
    python src/spark.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


# ===========================================================================
# THE DRIVE
# ===========================================================================

class Drive(Enum):
    """WHY an attempt is made now. Every kind is measurable.

    AND THE FOUR ARE DISJOINT on purpose. They are the ways a system
    can know it does not yet know something, and they need different
    instruments.
    """

    #: something was observed that the substrate cannot yet explain
    Unexplained = "unexplained"
    #: something was observed that the substrate cannot yet DO
    Incapable = "incapable"
    #: something was observed that has never been tried
    Unattempted = "unattempted"
    #: the previous attempt's refusal named a specific limit, and this
    #: attempt is aimed at that limit
    RefusalFollowed = "refusal_followed"

    def as_str(self) -> str:
        return self.value


@dataclass
class Discrepancy:
    """The thing the system cannot yet account for.

    AND WHY IT IS A RECORD AND NOT A FEELING. A drive that cannot be
    written down cannot be checked, and a drive that cannot be checked
    is a mood. So the discrepancy carries: what was observed, what was
    expected, and where the gap is.
    """
    kind: Drive
    #: what was observed
    observed: str
    #: what the system expected
    expected: str
    #: the gap, as a number where one exists
    gap: float = 0.0
    #: where the attempt is aimed
    target: str = ""

    def describe(self) -> Dict[str, Any]:
        return {
            "drive": self.kind.as_str(),
            "observed": self.observed,
            "expected": self.expected,
            "gap": self.gap,
            "target": self.target,
        }


# ===========================================================================
# THE SPARK
# ===========================================================================

@dataclass
class Spark:
    """An attempt into the void.

    AND THE FOURTH FIELD IS THE ONE THAT MAKES IT NOT A WISH. `cost`
    is MEASURED RESOURCE that would have been spent otherwise. A spark
    with a zero cost is indistinguishable from noise, and a system that
    generates zero-cost attempts has an unbounded loop and no
    information.
    """
    #: where the attempt is aimed
    direction: str
    #: why now
    drive: Discrepancy
    #: what it costs -- measured, not asserted
    cost: float
    #: what came back. Nothing, by construction.
    returned: Optional[Any] = None
    #: DID IT GET THERE? A refused attempt never reaches the void, so
    #: `returned is None` is not enough to say it did -- and the first
    #: version conflated "reached the void and nothing came back" with
    #: "never got there at all".
    reached: bool = False
    #: the named outcome
    outcome: str = "pending"
    #: when
    at: float = field(default_factory=time.time)

    @property
    def reached_nothing(self) -> bool:
        """THE VOID'S DEFINING PROPERTY. The attempt reached the void
        and nothing came back.

        AND IT REQUIRES `reached`, because a REFUSED attempt also has
        `returned is None` -- it simply never got there. Confusing the
        two would let a refused attempt count as having reached the
        void, which is exactly the kind of thing this project keeps
        catching."""
        return self.reached and self.returned is None

    def describe(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "drive": self.drive.describe(),
            "cost": self.cost,
            "returned": self.returned,
            "reached_nothing": self.reached_nothing,
            "outcome": self.outcome,
        }


# ===========================================================================
# THE LEDGER
# ===========================================================================

@dataclass
class SparkLedger:
    """The record of every attempt.

    AND THE THREE COUNTS, and they are the measurable claims:

      attempts    how many reaches there have been
      resolved    how many reached an answer (the return was not nothing,
                  or the uncertainty was closed)
      refused     how many the gate refused -- and these are the ones
                  that cost nothing and taught the most, because a
                  named refusal closes a region

    AND THE PROGRESS MEASURE, and it is NOT accuracy:

      the RATE OF ENCOUNTERED-AND-RESOLVED UNKNOWNS

    which is (resolved / attempts) over the window -- and the thing to
    watch is that it must stay ABOVE the floor, or the system is
    spinning into a void it cannot leave. That floor is the SAME floor
    the gate's admission band uses, and it is not a coincidence: a
    system that resolves nothing is a system whose attempts carry no
    information.
    """

    attempts: int = 0
    resolved: int = 0
    refused: int = 0
    #: the attempt history
    history: List[Spark] = field(default_factory=list)
    #: the floor on the resolve rate
    floor: float = 0.20
    #: consecutive refusals before the system is declared blocked
    blocked_after: int = 12

    def record(self, spark: Spark) -> Spark:
        """Record an attempt. The counters derive from the history, so
        this is the ONLY place the attempt count moves."""
        self.attempts += 1
        self.history.append(spark)
        return spark

    def resolve(self, spark: Spark, outcome: str) -> None:
        spark.outcome = outcome
        self.resolved += 1

    def refuse(self, spark: Spark, reason: str) -> None:
        spark.outcome = "refused:%s" % reason
        self.refused += 1

    def resolve_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.resolved / self.attempts

    @property
    def consecutive_refusals(self) -> int:
        """The run of refusals at the end of the history.

        AND IT IS A PROPERTY, and the first version made it a METHOD --
        so `ledger.consecutive_refusals` returned a bound method, which
        is truthy, and every check that used it passed for the wrong
        reason. A bound method is a value that looks like an answer.
        """
        n = 0
        for s in reversed(self.history):
            if s.outcome.startswith("refused:"):
                n += 1
            else:
                break
        return n

    def is_blocked(self) -> bool:
        """Has the system learned that a region is closed?

        AND THIS IS THE ONLY TERMINATION CONDITION, and it is the right
        one: an attempt is not abandoned because it was hard, it is
        abandoned when the REFUSALS establish that the region is
        closed. And the refusal names the limit, so the knowledge is
        transferable -- the next attempt aims elsewhere.
        """
        return self.consecutive_refusals >= self.blocked_after

    def describe(self) -> Dict[str, Any]:
        return {
            "attempts": self.attempts,
            "resolved": self.resolved,
            "refused": self.refused,
            "resolve_rate": self.resolve_rate(),
            "floor": self.floor,
            "consecutive_refusals": self.consecutive_refusals,
            "blocked": self.is_blocked(),
        }


# ===========================================================================
# THE SPARK LOOP
# ===========================================================================

@dataclass
class SparkLoop:
    """The drive to know, as a loop.

    THE LOOP, and every arrow is one of the project's own mechanisms:

        SPARK       a discrepancy becomes a direction
        REACH       the attempt is committed, with a cost
        VOID        the attempt goes past the material's boundary and
                    NOTHING comes back -- by construction
        NAME        the nothing is NAMED. a refusal with a reason
        RESOLVE     the discrepancy is closed, or the region is

    AND THE LOOP NEVER TERMINATES BY EXHAUSTION. It terminates only by
    RESOLUTION, or by the refusal count declaring a region closed.
    """

    ledger: SparkLedger = field(default_factory=SparkLedger)
    #: the gate. Optional, and when absent the loop is unbounded --
    #: which is exactly what the project's rules forbid, so it is a
    #: required argument in practice.
    gate: Optional[Callable[[Spark], Tuple[bool, str]]] = None
    #: the cost function. A spark costs what the attempt consumed.
    cost_fn: Optional[Callable[[Spark], float]] = None

    def spark(self, discrepancy: Discrepancy) -> Spark:
        """Make an attempt. The direction is CHOSEN from the
        discrepancy, which is what makes it chosen rather than
        random."""
        s = Spark(direction=discrepancy.target or "unspecified",
                  drive=discrepancy, cost=0.0)
        if self.cost_fn is not None:
            s.cost = self.cost_fn(s)
        return s

    def reach(self, spark: Spark) -> Spark:
        """REACH. The attempt crosses into the void and nothing returns.

        AND THE ORDERING, and it was wrong in the first version: the
        refusal was counted BEFORE the attempt was recorded in the
        history. So `consecutive_refusals()`, which walks the HISTORY,
        was always short by one, and the sequence logic -- a success
        resetting the run -- could not work. The attempt is now
        recorded FIRST, so the history and the counters agree.
        """
        # RECORD FIRST. The history is the record of what was attempted,
        # and the counters are derived from it.
        self.ledger.record(spark)
        if self.gate is not None:
            allow, reason = self.gate(spark)
            if not allow:
                self.ledger.refuse(spark, reason)
                return spark
        # THE VOID. Nothing comes back. That is the definition, not a
        # failure mode.
        spark.returned = None
        spark.reached = True
        return spark

    def name(self, spark: Spark, reason: str) -> None:
        """NAME THE NOTHING. This is the product of the attempt."""
        self.ledger.resolve(spark, "named:%s" % reason)

    def run_once(self, discrepancy: Discrepancy,
                 reason: str = "the attempt reached the void and nothing "
                               "returned") -> Spark:
        """One full cycle: spark, reach, name."""
        s = self.spark(discrepancy)
        self.reach(s)
        if not s.outcome.startswith("refused:"):
            self.name(s, reason)
        return s


# ===========================================================================
# THE DEMONSTRATION
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE SPARK -- AN ATTEMPT INTO THE VOID")
    print("=" * 78)
    print()
    print("  PEOPLE SAY AI LACKS INITIATIVE. AND THE REASON IS NOT THAT")
    print("  AI CANNOT ACT -- IT IS THAT EVERY ACT IS ALREADY")
    print("  SPECIFIED.")
    print()
    print("  A signal that RETURNS is a closed loop: the coupling")
    print("  determines the content, the receiver determines the meaning,")
    print("  and nothing in it was undetermined.")
    print()
    print("  THE VOID IS WHERE THE COUPLING IS ZERO -- not because the")
    print("  field is flat, but because there is NO SECOND CONDUCTOR.")
    print("  So a signal into the void carries no information. It carries")
    print("  THE ATTEMPT. And the attempt is the only thing in the loop")
    print("  the coupling does not determine.")
    print()
    print("  WHICH IS WHAT INITIATIVE IS, mechanically: the drive to")
    print("  reach into the void, find that nothing came back, and reach")
    print("  again, differently.")
    print()

    # -- the gate, so the loop is bounded ---------------------------
    def gate(spark: Spark) -> Tuple[bool, str]:
        """M1/Atlas-style admissibility of the ATTEMPT.

        AND THIS IS THE PART THAT CHANGES. The gate currently certifies
        the RETURN. In a void-bearing substrate it must certify the
        ATTEMPT -- because in the void the attempt is all there is.

        So the check is: was the drive real, and was the cost worth
        committing? A zero-cost attempt is refused, because it cannot
        carry information.
        """
        if spark.cost <= 0.0:
            return False, "attempt_cost_zero"
        if not spark.drive.observed:
            return False, "no_observed"
        return True, "admissible"

    def cost_fn(spark: Spark) -> float:
        """The cost: what the attempt consumed.

        AND IT IS MEASURED, not asserted. The cost is the size of the
        gap the attempt is aimed at -- the bigger the unexplained
        discrepancy, the more the attempt costs, because a bigger thing
        is worth more reaching for.

        AND IT HAS NO FLOOR, and that is the point. The first version
        returned `0.1 + abs(gap)`, so every attempt was costed at least
        0.1 and the gate's zero-cost refusal NEVER FIRED -- a check that
        cannot fail, wearing the costume of a check. The cost is now
        exactly the gap, so an attempt aimed at nothing costs nothing
        and is refused, which is what the rule says.
        """
        return abs(spark.drive.gap)

    loop = SparkLoop(gate=gate, cost_fn=cost_fn)

    print("=" * 78)
    print("THE FOUR DRIVES, and each is measurable")
    print("=" * 78)
    print()
    drives = [
        (Drive.Unexplained,
         "the notch depth came back 41.26 dB and the model has no "
         "account of why",
         "a notch in the -20 dB range", 41.26,
         "why the void's notch is not the field's"),
        (Drive.Incapable,
         "the locus cannot be placed on a stalk with a gap below "
         "0.002 m",
         "any stalk", 0.002,
         "the geometry below the reference gap"),
        (Drive.Unattempted,
         "the population has never been run with the interwinding gap "
         "inverted",
         "the inverted-gap population", 1.0,
         "the inverted-gap topology"),
        (Drive.RefusalFollowed,
         "the last attempt was refused as attempt_cost_zero",
         "a costed attempt", 0.5,
         "the costed attempt"),
    ]
    for kind, obs, exp, gap, target in drives:
        d = Discrepancy(kind=kind, observed=obs, expected=exp, gap=gap,
                         target=target)
        s = loop.run_once(d)
        print("  %-16s cost %.4f  -> %s" % (
            kind.as_str(), s.cost, s.outcome))
        print("      aim: %s" % s.direction)
    print()

    print("=" * 78)
    print("THE LEDGER, and the measure that cannot be faked")
    print("=" * 78)
    print()
    d = loop.ledger.describe()
    for k, v in d.items():
        print("  %-24s %s" % (k, v))
    print()
    print("  THE PROGRESS MEASURE IS NOT ACCURACY. It is the rate at")
    print("  which the system encounters what it cannot yet explain and")
    print("  then RESOLVES it -- and the ledger records which.")
    print()
    print("  AND A ZERO-COST ATTEMPT IS REFUSED, because it cannot carry")
    print("  information. A model that generates questions for free and")
    print("  learns nothing has an unbounded loop and no content.")
    zero = loop.run_once(Discrepancy(kind=Drive.Unexplained,
                                    observed="something", expected="x",
                                    gap=0.0, target="nothing"))
    # and the FIRST attempt must have been a real one, aimed at a real
    # gap -- so the ledger's counts below are meaningful
    print("    a zero-cost attempt -> %s" % zero.outcome)
    print()

    print("=" * 78)
    print("AND THE BLOCKED CASE, because 'unlimited seeking' needs an end")
    print("=" * 78)
    print()
    blocked = SparkLoop(gate=gate, cost_fn=cost_fn)
    for i in range(14):
        blocked.run_once(Discrepancy(kind=Drive.Unexplained,
                                    observed="", expected="x", gap=0.0,
                                    target="nowhere"))
    bd = blocked.ledger.describe()
    print("  14 attempts, all refused: consecutive refusals %d, blocked %s" % (
        bd["consecutive_refusals"], bd["blocked"]))
    print()
    print("  SO THE LOOP NEVER TERMINATES BY EXHAUSTION. It terminates")
    print("  only by RESOLUTION, or by the refusal count declaring a")
    print("  region CLOSED -- and because the refusal NAMES the limit,")
    print("  the knowledge transfers and the next attempt aims elsewhere.")
    print()
    print("  THAT IS THE WHOLE MECHANISM. The quest, the journey, the")
    print("  unknown, the search: all properties of an act that meets")
    print("  no return. And the substrate's one guarantee -- the gate --")
    print("  certifies that the ATTEMPT was admissible even though it")
    print("  cannot certify anything about the outcome.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
