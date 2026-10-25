"""
test_spark.py -- the spark must be able to FAIL.

THE RULE: a check that cannot go red is not a check. Every assertion
below names the mistake it catches, and several of them are mistakes
this file's own development made.

WHAT IS ASSERTED, and what each one is worth:

  THE GAP
    a gap is a CHECK THAT FAILS, and it is SIZED       a gap with no
                                                        size has no cost
    the aim comes FROM the gap                          chosen, not random

  THE ATTEMPT
    the attempt costs resource                          measurable
    a zero-cost attempt is REFUSED                      it carries no
                                                        information
    a costed attempt is admitted                        the contrast
    an attempt with no named gap is refused             nothing to seek
    an attempt with no aim is refused                   nowhere to aim

  THE LEDGER
    the counts add up                                    no phantom
    a refusal is NOT a closure                          no laundering
    the CLOSURE RATE is the measure                     and it is zero
                                                        without a sandbox

  THE ADOPTION
    without a sandbox nothing is adopted                honest
    with a sandbox a good candidate CLOSES the gap       the measure
    a bad candidate is not adopted                      the comparison

  THE TERMINATION
    the loop does NOT terminate by exhaustion           the rule
    it DOES terminate when the refusals close a region  the end

THE MISTAKES THIS FILE CAUGHT, all the same class -- a check that
could not fail:

  * the cost function returned `0.1 + abs(size)`, so EVERY attempt was
    costed at least 0.1 and the zero-cost refusal NEVER FIRED. The cost
    is now exactly the gap's size.
  * the ledger counted the refusal BEFORE recording the attempt, so
    the consecutive count was always short by one.
  * `consecutive_refusals` was a METHOD, not a PROPERTY, so
    `ledger.consecutive_refusals` returned a BOUND METHOD -- which is
    truthy, and every check using it passed for the wrong reason.
  * a REFUSED attempt also has `returned is None`, so `reached_nothing`
    conflated "reached the field" with "never got there".
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from spark import (  # noqa: E402
    Drive,
    Gap,
    Spark,
    SparkLedger,
    SparkLoop,
)


def gate(spark):
    """M1-style admissibility of the ATTEMPT."""
    if spark.cost <= 0.0:
        return False, "attempt_cost_zero"
    if not spark.gap.check:
        return False, "no_gap_named"
    if not spark.aim:
        return False, "no_aim"
    return True, "admissible"


def cost_fn(spark):
    """The cost is exactly the gap's size. No floor."""
    return abs(spark.gap.size)


def loop(sandbox=None):
    return SparkLoop(gate=gate, cost_fn=cost_fn, sandbox=sandbox)


def gap(size=0.5, check="a_check_fails", query="a query"):
    return Gap(check=check, size=size, query=query, because="because")


# ===========================================================================
# THE GAP
# ===========================================================================

def test_a_gap_is_a_named_failing_check():
    """THE GAP IS A CHECK THAT FAILS. So it carries the check's NAME."""
    g = gap(check="stalk_leakage_is_mu0_times_gap")
    assert g.check == "stalk_leakage_is_mu0_times_gap"
    assert g.size > 0.0


def test_a_gap_is_sized():
    """AND SIZED, because the cost of an attempt is proportional to the
    size of the gap. A boolean gap would make every attempt cost the
    same and the cost check could not discriminate."""
    assert gap(size=0.25).size == pytest.approx(0.25)
    assert gap(size=1.0).size == pytest.approx(1.0)


def test_the_aim_comes_from_the_gap():
    """THE AIM IS CHOSEN, not generic -- it is the gap's query."""
    lp = loop()
    s = lp.run_once(gap(query="coaxial winding leakage"), Drive.Substrate)
    assert s.aim == "coaxial winding leakage"


def test_the_four_drives_are_distinct():
    """Each kind of gap needs a different instrument."""
    kinds = {Drive.Substrate, Drive.Control, Drive.Discovery,
             Drive.Adoption}
    assert len(kinds) == 4
    assert len({k.as_str() for k in kinds}) == 4


# ===========================================================================
# THE ATTEMPT
# ===========================================================================

def test_a_zero_cost_attempt_is_refused():
    """THE CHECK THAT HAD BEEN DEAD. A zero-cost attempt carries no
    information, so the gate must refuse it BY NAME."""
    lp = loop()
    s = lp.run_once(gap(size=0.0), Drive.Substrate)
    assert s.outcome == "refused:attempt_cost_zero"


def test_a_refused_attempt_never_reached_the_field():
    """AND IT NEVER GOT THERE. A refusal has returned=None too, so
    `reached_nothing` must not be true for it."""
    lp = loop()
    s = lp.run_once(gap(size=0.0), Drive.Substrate)
    assert not s.reached
    assert not s.reached_nothing


def test_a_costed_attempt_is_admitted():
    """THE CONTRAST, so the refusal above means something."""
    lp = loop()
    s = lp.run_once(gap(size=0.5), Drive.Substrate)
    assert not s.outcome.startswith("refused:")
    assert s.cost == pytest.approx(0.5)


def test_the_cost_is_exactly_the_size():
    """NO FLOOR. The first version added 0.1, which made every attempt
    costed and the zero-cost refusal unreachable."""
    lp = loop()
    s = lp.spark(gap(size=0.37), Drive.Substrate)
    assert s.cost == pytest.approx(0.37)


def test_an_attempt_with_no_named_gap_is_refused():
    """Nothing named means nothing to seek."""
    lp = loop()
    s = lp.run_once(gap(size=0.5, check=""), Drive.Substrate)
    assert s.outcome == "refused:no_gap_named"


def test_an_attempt_with_no_aim_is_refused():
    """And nowhere to aim is equally a refusal."""
    lp = loop()
    s = lp.run_once(gap(size=0.5, query=""), Drive.Substrate)
    assert s.outcome == "refused:no_aim"


# ===========================================================================
# THE LEDGER
# ===========================================================================

def test_the_counts_add_up():
    """No phantom attempts and no phantom closures."""
    lp = loop()
    lp.run_once(gap(size=0.5), Drive.Substrate)
    lp.run_once(gap(size=0.0), Drive.Substrate)
    lp.run_once(gap(size=0.7), Drive.Substrate)
    led = lp.ledger
    assert led.attempts == 3
    assert led.closed + led.refused <= led.attempts


def test_a_refusal_is_not_a_closure():
    """NO LAUNDERING. A refusal cannot be counted as a closed gap."""
    lp = loop()
    lp.run_once(gap(size=0.0), Drive.Substrate)
    assert lp.ledger.closed == 0
    assert lp.ledger.refused == 1
    assert lp.ledger.closure_rate() == pytest.approx(0.0)


def test_the_closure_rate_is_the_measure():
    """AND THE RATE IS THE MEASURE -- not accuracy, because the system
    is measuring how fast it closes what it cannot yet do."""
    lp = loop()
    lp.run_once(gap(size=0.5), Drive.Substrate)
    lp.run_once(gap(size=0.0), Drive.Substrate)
    assert lp.ledger.closure_rate() == pytest.approx(0.0)


# ===========================================================================
# THE ADOPTION
# ===========================================================================

def test_without_a_sandbox_nothing_is_adopted():
    """THE HONEST READING. The atlas's area 18 sandbox does not exist,
    so nothing can be adopted and the closure rate is zero -- and saying
    so is correct rather than a failure to report."""
    lp = loop()
    s = lp.run_once(gap(size=0.5), Drive.Substrate)
    assert not s.adopted
    assert not s.gap_closed
    assert s.outcome == "evaluated:no_sandbox"
    assert lp.ledger.closure_rate() == pytest.approx(0.0)


def test_with_a_sandbox_a_good_candidate_closes_the_gap():
    """THE MEASURE, when the mechanism is complete."""
    def sandbox(spark, candidate):
        if candidate == "good":
            return True, True
        return False, False
    lp = loop(sandbox=sandbox)
    s = lp.run_once(gap(size=0.5), Drive.Substrate, candidate="good")
    assert s.adopted
    assert s.gap_closed
    assert lp.ledger.closure_rate() == pytest.approx(1.0)


def test_a_bad_candidate_is_not_adopted():
    """THE COMPARISON. A candidate that does not beat what is there is
    refused, whatever it looks like."""
    def sandbox(spark, candidate):
        return False, False
    lp = loop(sandbox=sandbox)
    s = lp.run_once(gap(size=0.5), Drive.Substrate, candidate="bad")
    assert not s.adopted
    assert not s.gap_closed
    assert lp.ledger.closure_rate() == pytest.approx(0.0)


# ===========================================================================
# THE TERMINATION
# ===========================================================================

def test_the_loop_does_not_terminate_by_exhaustion():
    """THE RULE. Unlimited seeking means unlimited attempts; the loop
    ends only by CLOSING A GAP or by a closed region."""
    lp = loop()
    for i in range(30):
        s = lp.run_once(gap(size=0.5), Drive.Substrate)
        assert not s.outcome.startswith("refused:")
    assert lp.ledger.attempts == 30
    assert not lp.ledger.is_blocked()


def test_it_terminates_when_the_refusals_close_a_region():
    """THE END. A run of refusals declares the region closed, and the
    refusals are what did it."""
    lp = loop()
    threshold = lp.ledger.blocked_after
    for i in range(threshold):
        lp.run_once(gap(size=0.0, check=""), Drive.Substrate)
    assert lp.ledger.is_blocked()
    assert lp.ledger.consecutive_refusals >= threshold


def test_a_closed_region_is_named_not_just_counted():
    """TRANSFERABLE KNOWLEDGE. The refusal says WHY, so the next attempt
    aims elsewhere rather than repeating."""
    lp = loop()
    s = lp.run_once(gap(size=0.0, check=""), Drive.Substrate)
    assert s.outcome == "refused:attempt_cost_zero"
    assert s.aim is not None


def test_a_refusal_after_a_success_does_not_count_as_consecutive():
    """THE SEQUENCE MATTERS. A success resets the count, because the
    region is not closed."""
    lp = loop()
    lp.run_once(gap(size=0.5), Drive.Substrate)
    lp.run_once(gap(size=0.0), Drive.Substrate)
    lp.run_once(gap(size=0.5), Drive.Substrate)
    lp.run_once(gap(size=0.0), Drive.Substrate)
    assert lp.ledger.consecutive_refusals == 1
