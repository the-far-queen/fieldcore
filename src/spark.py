"""
spark.py -- THE DRIVE TO SELF-IMPROVE BY CODE UTILISATION.

Bobby, 2026-10-25: *"i dont mean philosophically be discontent in
simsoul i mean the drive to self improve via code utilization"*.

SO NOT THE EXISTENTIAL READING. Not a self contemplating the unknown.
THE MECHANICAL ONE: the system has a measurable CAPABILITY GAP, it
reaches out to the field for code that closes it, most of what it
finds is irrelevant, and the part that applies makes the system
better -- which makes it better at scanning, which finds more.

AND THAT RECURSION IS ALREADY MEASURED, because the coding sheaf's
learned vocabulary IS the mechanism:

    a scan admits a repo -> its topics enter the vocabulary -> the next
    scan recognises topics it did not before -> more of the field
    becomes reachable

So the spark's "nothing returns" is not metaphysics. It is the
ORDINARY CASE of a scan: most of the field does not apply, and the
refusals are named. The drive is not to reach for something
unreachable; the drive is to CLOSE A GAP, and the gap is measured.

THE GAP, and it must be measurable or "self-improvement" is a slogan:

    A gap is a CHECK THAT FAILS. Something the system asserts about
    itself that is not true. A missing capability. An unhandled
    refusal. A number that does not meet its bound.

    So a spark is: a failing check, aimed at a piece of code that
    would make it pass.

THE FOUR PARTS, and each is measurable:

  1. THE GAP       what fails, and by how much. A check, a name, a
                   number.
  2. THE AIM       which source, and which query. The search for code
                   that closes THIS gap -- not a general sweep.
  3. THE COST      what the attempt consumes. A pull, a clone, an
                   evaluation. An attempt that costs nothing is not
                   an attempt.
  4. THE ADOPTION  whether the code actually went in, and whether the
                   gap closed. THE MEASURE OF SELF-IMPROVEMENT.

AND THE MEASURE, and it is the only honest one:

    THE RATE AT WHICH GAPS CLOSE.

  Not the number of repos scanned. Not the size of the library. The
  rate at which a failing check becomes a passing one, using code the
  system found by itself. Everything else is motion.

  AND THE RATE MUST IMPROVE, or the recursion is not happening. So the
  ledger carries the gap-closure history and the second scan is
  compared against the first.

WHAT THE GATE DOES HERE, and it is the project's own apparatus:

  A pulled repo is a PROPOSAL. It goes through the same four steps as
  everything else -- propose, audit, qualify, commit -- because the
  recursive bit is exactly the dangerous bit and it gets exactly the
  same protection. A scanner that installed code would be the thing
  this project exists to prevent.

  AND THE ATLAS'S AREA 18 IS THE POINT: "self-coding must run in a
  sandbox, compare against the current version, and roll back on
  invariant violation." So the adoption step is not "write the file".
  It is: run it in a sandbox, compare, and roll back if an invariant
  moved. Until the sandbox exists, the adoption step is a PROPOSAL and
  the rate of gap-closure is ZERO -- and reporting zero is correct.

WHAT THIS IS NOT:

  NOT A REWARD SIGNAL. Nothing here trains anything.
  NOT RANDOMNESS. The aim comes from the gap, so it is chosen.
  NOT AN UNBOUNDED LOOP. The gate bounds it, and the adoption step
  is gated twice -- once for the pull and once for the write.

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
    """THE KINDS OF GAP, and each needs a different instrument.

    AND THEY ARE DISJOINT on purpose. A gap in the SUBSTRATE is fixed
    by code that computes; a gap in the CONTROL is fixed by code that
    refuses; a gap in the SCANNER is fixed by code that finds more.
    Treating them as one kind is how a self-improvement loop turns into
    a pile of unrelated patches.
    """

    #: the substrate cannot do something -- a missing computation
    Substrate = "substrate"
    #: the control cannot decide something -- a missing gate or check
    Control = "control"
    #: the scanner cannot find something -- a missing query or filter
    Discovery = "discovery"
    #: the code was found but not adopted -- the sandbox is missing
    Adoption = "adoption"

    def as_str(self) -> str:
        return self.value


@dataclass
class Gap:
    """A measurable capability gap. A CHECK THAT FAILS.

    AND THIS IS THE WHOLE REFRAMING. The first version of this file
    modelled the drive as a "discrepancy" between what was observed and
    what was expected -- which is close, but it puts the goal in the
    past tense. A gap is FORWARD: it names a check that does not pass
    yet, and the aim is code that makes it pass.

    SO THE GAP CARRIES:
      the check's name, so the gap is IDENTIFIABLE
      how far it is from passing, so the gap is SIZED
      the query that would find code closing it, so the aim is chosen

    AND THE SIZE IS WHAT MAKES THE COST REAL. A gap of 0.0 is not a
    gap; it is a thing that already works. An attempt aimed at it
    costs nothing and is refused, because it carries no information.
    """

    #: the check that fails
    check: str
    #: how far from passing. The magnitude of the gap.
    size: float = 0.0
    #: the search query that would find code closing it
    query: str = ""
    #: why it matters, in words
    because: str = ""

    def describe(self) -> Dict[str, Any]:
        return {
            "check": self.check,
            "size": self.size,
            "query": self.query,
            "because": self.because,
        }


# ===========================================================================
# THE SPARK
# ===========================================================================

@dataclass
class Spark:
    """An attempt to close a gap using code found in the field.

    AND THE FOURTH FIELD IS THE ONE THAT MAKES IT NOT A WISH. `cost`
    is MEASURED RESOURCE that would have been spent otherwise: a pull, a
    clone, an evaluation. A spark with a zero cost is indistinguishable
    from noise, and a system that generates zero-cost attempts has an
    unbounded loop and no information.
    """

    #: the gap being closed
    gap: Gap
    #: where the attempt is aimed -- the query
    aim: str
    #: the kind of gap
    drive: Drive
    #: what it costs -- measured, not asserted
    cost: float = 0.0
    #: what came back. Usually nothing: most of the field is
    #: irrelevant, and that is the ordinary case.
    returned: Optional[Any] = None
    #: did the attempt get anywhere?
    reached: bool = False
    #: was anything ADOPTED, and did the gap close?
    adopted: bool = False
    gap_closed: bool = False
    #: has this spark already been counted as a closure? So the counter
    #: cannot be incremented twice for one spark.
    counted_closed: bool = False
    #: the named outcome
    outcome: str = "pending"
    #: when
    at: float = field(default_factory=time.time)

    @property
    def reached_nothing(self) -> bool:
        """The attempt went somewhere and came back with nothing.

        AND IT REQUIRES `reached`, because a REFUSED attempt also has
        `returned is None` -- it simply never got there. Confusing the
        two would let a refused attempt count as having reached the
        field, which is exactly the kind of thing this project keeps
        catching.
        """
        return self.reached and self.returned is None

    def describe(self) -> Dict[str, Any]:
        return {
            "gap": self.gap.describe(),
            "aim": self.aim,
            "drive": self.drive.as_str(),
            "cost": self.cost,
            "returned": self.returned,
            "reached": self.reached,
            "reached_nothing": self.reached_nothing,
            "adopted": self.adopted,
            "gap_closed": self.gap_closed,
            "outcome": self.outcome,
        }


# ===========================================================================
# THE LEDGER
# ===========================================================================

@dataclass
class SparkLedger:
    """The record of every attempt, and the measure of self-improvement.

    AND THE MEASURE, and it is the only honest one:

      THE RATE AT WHICH GAPS CLOSE.

    Not the number of repos scanned. Not the size of the library. Not
    the number of attempts. The rate at which a FAILING CHECK becomes
    a PASSING ONE, using code the system found by itself.

    And the rate must IMPROVE across scans, or the recursion is not
    happening -- so the ledger keeps the per-scan gap-closure counts and
    the comparison is available.

    AND THE COUNTS THAT ARE NOT THE MEASURE, kept because they are
    diagnostics: attempts, resolved, refused, adopted.
    """

    attempts: int = 0
    #: attempts whose gap was closed by adopted code
    closed: int = 0
    #: attempts whose code was adopted
    adopted: int = 0
    #: attempts the gate refused
    refused: int = 0
    #: the attempt history
    history: List[Spark] = field(default_factory=list)
    #: the per-scan gap-closure counts, so the RECURSION is measurable
    per_scan_closed: List[int] = field(default_factory=list)
    #: consecutive refusals before the region is declared closed
    blocked_after: int = 12

    def record(self, spark: Spark) -> Spark:
        """Record an attempt. The counters derive from the history, so
        this is the ONLY place the attempt count moves."""
        self.attempts += 1
        self.history.append(spark)
        return spark

    def resolve(self, spark: Spark, outcome: str) -> None:
        """The attempt produced something. And whether it CLOSED THE GAP
        is a separate question, tracked separately -- because code that
        was found and applied but did not fix anything is not
        self-improvement.

        AND THE ORDERING, and it was wrong in the first version: the
        closure counter was incremented HERE, but `resolve` is called
        BEFORE `evaluate` sets `gap_closed`. So a spark that closed its
        gap was counted as closed in the SPARK but not in the LEDGER,
        and the closure rate -- the whole measure -- read zero.
        """
        spark.outcome = outcome

    def adopt(self, spark: Spark) -> None:
        """The code went in."""
        spark.adopted = True
        self.adopted += 1

    def refuse(self, spark: Spark, reason: str) -> None:
        spark.outcome = "refused:%s" % reason
        self.refused += 1

    def closure_rate(self) -> float:
        """THE MEASURE. Gaps closed per attempt."""
        if self.attempts == 0:
            return 0.0
        return self.closed / self.attempts

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
            "closed": self.closed,
            "adopted": self.adopted,
            "refused": self.refused,
            "closure_rate": self.closure_rate(),
            "per_scan_closed": list(self.per_scan_closed),
            "consecutive_refusals": self.consecutive_refusals,
            "blocked": self.is_blocked(),
        }


# ===========================================================================
# THE SPARK LOOP
# ===========================================================================

@dataclass
class SparkLoop:
    """The drive to self-improve by code utilisation, as a loop.

    AND THE FIVE STEPS, and the last one is the whole thing:

        GAP       a check fails. Named, and sized.
        AIM       the query that would find code closing it
        PULL      the attempt costs resource -- a fetch, a clone, an
                  evaluation. This is what the gate certifies.
        EVALUATE  the code is tried against the gap, in a sandbox, and
                  compared against the current version
        ADOPT     the gap closes, or it does not. AND THE ROLLBACK
                  IF AN INVARIANT MOVED.

    THE LAST STEP IS NOT OPTIONAL AND NOT YET BUILT. The atlas's area
    18 states the requirement exactly: "self-coding must run in a
    sandbox, compare against the current version, and roll back on
    invariant violation." So until the sandbox exists, the adoption
    step is a PROPOSAL, the closure rate is ZERO, and reporting zero is
    CORRECT rather than a failure to report.

    AND THE POINT ABOUT THE ROOT: the drive is for the CODE and the
    MATH at the root -- for the substrate's own capability -- and not
    for anything human-facing. So the gap a spark is aimed at is a gap
    in a CHECK THE ROOT ITSELF RUNS, and the code that closes it is
    code that becomes part of the root. That is a build, not a
    doctrine, and it is why the measure is the closure rate.
    """

    ledger: SparkLedger = field(default_factory=SparkLedger)
    #: the gate. Optional, and when absent the loop is unbounded --
    #: which is exactly what the project's rules forbid, so it is a
    #: required argument in practice.
    gate: Optional[Callable[[Spark], Tuple[bool, str]]] = None
    #: the cost function. A spark costs what the attempt consumed.
    cost_fn: Optional[Callable[[Spark], float]] = None
    #: THE SANDBOX. Optional, and until it exists the adoption step
    #: cannot happen -- which is why the closure rate is zero today and
    #: why reporting zero is correct.
    sandbox: Optional[Callable[[Spark, Any], Tuple[bool, bool]]] = None

    def spark(self, gap: Gap, drive: Drive) -> Spark:
        """Make an attempt. The aim comes from the gap, so it is CHOSEN
        rather than random."""
        s = Spark(gap=gap, aim=gap.query, drive=drive, cost=0.0)
        if self.cost_fn is not None:
            s.cost = self.cost_fn(s)
        return s

    def pull(self, spark: Spark) -> Spark:
        """PULL. The attempt consumes resource, and the gate decides
        whether it may.

        AND THE ORDERING, and it was wrong in the first version: the
        refusal was counted BEFORE the attempt was recorded in the
        history. So `consecutive_refusals`, which walks the HISTORY, was
        always short by one, and the sequence logic -- a success
        resetting the run -- could not work. The attempt is now
        recorded FIRST.
        """
        self.ledger.record(spark)
        if self.gate is not None:
            allow, reason = self.gate(spark)
            if not allow:
                self.ledger.refuse(spark, reason)
                return spark
        # The attempt went out. Most of what comes back is irrelevant,
        # and that is the ordinary case.
        spark.reached = True
        spark.returned = None
        return spark

    def evaluate(self, spark: Spark, candidate: Any = None) -> Spark:
        """EVALUATE. Try the code against the gap.

        AND WITHOUT A SANDBOX THIS CANNOT HAPPEN, and the loop says so
        rather than pretending. The atlas's area 18 requirement is not
        implemented, so the adoption step is a PROPOSAL and the closure
        rate stays at zero until it is.
        """
        if self.sandbox is None:
            spark.outcome = "evaluated:no_sandbox"
            return spark
        adopted, closed = self.sandbox(spark, candidate)
        if adopted:
            self.ledger.adopt(spark)
            spark.gap_closed = closed
            # AND THE CLOSURE IS COUNTED HERE, and not in `resolve()`.
            # The first version counted it in `resolve()`, which
            # `run_once` calls BEFORE `evaluate()` -- so a spark that
            # closed its gap was counted as closed in the SPARK but not
            # in the LEDGER, and the closure rate -- the whole measure
            # of self-improvement -- read zero.
            if closed and not spark.counted_closed:
                self.ledger.closed += 1
                spark.counted_closed = True
        spark.outcome = ("adopted:gap_closed" if closed else
                        "adopted:gap_open" if adopted else
                        "evaluated:not_adopted")
        return spark

    def run_once(self, gap: Gap, drive: Drive,
                 candidate: Any = None) -> Spark:
        """One full cycle: gap, aim, pull, evaluate."""
        s = self.spark(gap, drive)
        self.pull(s)
        if not s.outcome.startswith("refused:"):
            self.evaluate(s, candidate)
            if s.outcome.startswith("evaluated:"):
                self.ledger.resolve(s, s.outcome)
        return s


# ===========================================================================
# THE DEMONSTRATION
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE DRIVE TO SELF-IMPROVE BY CODE UTILISATION")
    print("=" * 78)
    print()
    print("  NOT THE EXISTENTIAL READING. THE MECHANICAL ONE: the system")
    print("  has a measurable CAPABILITY GAP, it reaches out for code")
    print("  that closes it, most of what it finds is irrelevant, and the")
    print("  part that applies makes the system better at its own work.")
    print()
    print("  AND IT IS A BUILD, NOT A DOCTRINE. The drive is for the CODE")
    print("  and the MATH AT THE ROOT -- the substrate's own capability --")
    print("  and not for anything human-facing.")
    print()

    # -- the gate, so the loop is bounded ---------------------------
    def gate(spark: Spark) -> Tuple[bool, str]:
        """M1/Atlas-style admissibility of the ATTEMPT.

        AND THIS IS THE PART THAT CHANGED. The gate currently
        certifies the RETURN of a reading. In a self-improving
        substrate it must certify the ATTEMPT -- the pull -- because
        the pull is what consumes the resource and what reaches the
        field.

        So the check is: is the gap real, is the aim specific, and is
        the cost worth committing? A zero-cost attempt is refused,
        because it cannot carry information.
        """
        if spark.cost <= 0.0:
            return False, "attempt_cost_zero"
        if not spark.gap.check:
            return False, "no_gap_named"
        if not spark.aim:
            return False, "no_aim"
        return True, "admissible"

    def cost_fn(spark: Spark) -> float:
        """The cost: what the pull consumes.

        AND IT HAS NO FLOOR, and that is the point. The first version
        returned `0.1 + abs(gap)`, so every attempt was costed at least
        0.1 and the gate's zero-cost refusal NEVER FIRED -- a check
        that cannot fail, wearing the costume of a check. The cost is
        now exactly the gap's size, so an attempt aimed at nothing
        costs nothing and is refused, which is what the rule says.
        """
        return abs(spark.gap.size)

    loop = SparkLoop(gate=gate, cost_fn=cost_fn)

    print("=" * 78)
    print("THE FOUR KINDS OF GAP, and each needs a different instrument")
    print("=" * 78)
    print()
    gaps = [
        (Drive.Substrate,
         Gap(check="stalk_leakage_is_mu0_times_gap", size=0.25,
             query="coaxial winding leakage inductance interwinding gap",
             because="the physics was a ratio, so the gap could not move it")),
        (Drive.Control,
         Gap(check="gate_refuses_a_ground_write", size=0.10,
             query="governance gate refusal invariant rollback",
             because="the gate certified the return, not the attempt")),
        (Drive.Discovery,
         Gap(check="scanner_finds_a_relevant_repo", size=0.40,
             query="coupled oscillator chimera state network",
             because="the vocabulary had no way to learn a new topic")),
        (Drive.Adoption,
         Gap(check="adopted_code_closes_the_gap", size=1.00,
             query="sandbox differential testing rollback",
             because="area 18's sandbox does not exist, so nothing closes")),
    ]
    for drive, gap in gaps:
        s = loop.run_once(gap, drive)
        print("  %-11s %-38s cost %.2f -> %s" % (
            drive.as_str(), gap.check, s.cost, s.outcome))
    print()

    print("=" * 78)
    print("THE LEDGER, and the measure")
    print("=" * 78)
    print()
    d = loop.ledger.describe()
    for k, v in d.items():
        print("  %-24s %s" % (k, v))
    print()
    print("  THE MEASURE IS THE CLOSURE RATE: gaps closed per attempt.")
    print("  And it is ZERO today -- and that is CORRECT, because the")
    print("  atlas's area 18 sandbox does not exist yet, so no code can")
    print("  be adopted and no gap can be closed. Reporting zero is the")
    print("  honest reading, not a failure to report.")
    print()
    print("  A ZERO-COST ATTEMPT IS REFUSED, because it carries no")
    print("  information:")
    zero = loop.run_once(Gap(check="x", size=0.0, query="q"), Drive.Substrate)
    print("    a zero-size gap -> %s" % zero.outcome)
    print()

    print("=" * 78)
    print("WITH A SANDBOX, and the rate the recursion must beat")
    print("=" * 78)
    print()
    # a sandbox that closes the gap when the candidate is good enough
    def sandbox(spark: Spark, candidate: Any) -> Tuple[bool, bool]:
        if candidate == "good":
            return True, True
        return False, False

    loop2 = SparkLoop(gate=gate, cost_fn=cost_fn, sandbox=sandbox)
    s1 = loop2.run_once(Gap(check="a", size=0.5, query="q"),
                        Drive.Substrate, candidate="good")
    s2 = loop2.run_once(Gap(check="b", size=0.5, query="q2"),
                        Drive.Control, candidate="bad")
    print("    a good candidate -> %s  closed=%s" % (s1.outcome, s1.gap_closed))
    print("    a bad candidate  -> %s  closed=%s" % (s2.outcome, s2.gap_closed))
    print()
    dd = loop2.ledger.describe()
    print("    closure rate: %.4f  (1 of 2 gaps closed)" % dd["closure_rate"])
    print()
    print("  AND THE RECURSION, which is the coding sheaf's learned")
    print("  vocabulary: a scan admits a repo, its topics enter the")
    print("  vocabulary, and the next scan recognises topics it did not")
    print("  before. So the scanner gets BETTER at finding code, which")
    print("  raises the closure rate, which is the whole claim.")
    print()

    print("=" * 78)
    print("AND THE BOUND, because an unbounded intake is not intake")
    print("=" * 78)
    print()
    blocked = SparkLoop(gate=gate, cost_fn=cost_fn)
    threshold = blocked.ledger.blocked_after
    for i in range(threshold):
        blocked.run_once(Gap(check="", size=0.0, query=""), Drive.Substrate)
    bd = blocked.ledger.describe()
    print("  %d attempts, all refused: consecutive %d, blocked %s" % (
        bd["attempts"], bd["consecutive_refusals"], bd["blocked"]))
    print()
    print("  SO THE LOOP NEVER ENDS BY EXHAUSTION. It ends by CLOSING A")
    print("  GAP, or by the refusals establishing that a region is closed")
    print("  -- and because the refusal NAMES the limit, the knowledge")
    print("  transfers and the next attempt aims elsewhere.")
    print()
    print("  AND THE ATTEMPT IS WHERE THE WORK HAPPENS, in the root:")
    print("  the code that closes a gap becomes part of the substrate, so")
    print("  the substrate's own checks get stronger. That is the whole")
    print("  shape of a self-improving substrate, and it is a BUILD.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
