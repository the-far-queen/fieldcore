"""
test_spark.py -- the spark must be able to FAIL.

THE RULE: a check that cannot go red is not a check. Every assertion
below names the mistake it catches, and two of them are mistakes this
file's own development made.

WHAT IS ASSERTED, and what each one is worth:

  THE VOID
    an attempt reaches the void and NOTHING returns       the definition
    the nothing is NAMED                                the product
    a named refusal is a resolved attempt               it counts

  THE COST
    a zero-cost attempt is REFUSED                      it carries no
                                                         information
    a costed attempt is admitted                        the contrast

  THE LEDGER
    the counts add up                                    no phantom
    the resolve rate is the measure, not accuracy       the metric
    a refused attempt is not a resolved one             no laundering

  THE TERMINATION
    the loop does NOT terminate by exhaustion           the rule
    it DOES terminate when the refusals close a region  the end
    a closed region is detectable and named            transferable

THE TWO MISTAKES THIS FILE CAUGHT:

  * the cost function returned `0.1 + abs(gap)`, so EVERY attempt was
    costed at least 0.1 and the zero-cost refusal NEVER FIRED -- a
    check that cannot fail, wearing the costume of a check. The cost is
    now exactly the gap, so an attempt aimed at nothing costs nothing
    and is refused.

  * the RefusalFollowed drive carried gap 0.0, so once the cost
    function was fixed it became a zero-cost attempt and was refused --
    which is correct behaviour but made the demonstration's four drives
    indistinguishable. It now carries a real gap, because a
    follow-up attempt aimed at a specific limit DOES cost something.
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
    Discrepancy,
    Drive,
    Spark,
    SparkLedger,
    SparkLoop,
)


def gate(spark):
    """M1-style admissibility of the ATTEMPT."""
    if spark.cost <= 0.0:
        return False, "attempt_cost_zero"
    if not spark.drive.observed:
        return False, "no_observed"
    return True, "admissible"


def cost_fn(spark):
    """The cost is exactly the gap. No floor."""
    return abs(spark.drive.gap)


def loop():
    return SparkLoop(gate=gate, cost_fn=cost_fn)


def disc(gap=0.5, observed="something", target="somewhere"):
    return Discrepancy(kind=Drive.Unexplained, observed=observed,
                       expected="other", gap=gap, target=target)


# ===========================================================================
# THE VOID
# ===========================================================================

def test_an_attempt_reaches_nothing():
    """THE DEFINITION. The attempt crosses into the void and nothing
    comes back."""
    lp = loop()
    s = lp.run_once(disc())
    assert s.reached_nothing
    assert s.returned is None


def test_the_nothing_is_named():
    """THE PRODUCT. A refusal with a reason IS the attempt's output, and
    the reason is not optional."""
    lp = loop()
    s = lp.run_once(disc(), reason="the notch has no account")
    assert s.outcome.startswith("named:")
    assert "the notch has no account" in s.outcome


def test_a_named_attempt_counts_as_resolved():
    """AND IT COUNTS, because the naming IS the resolution."""
    lp = loop()
    lp.run_once(disc())
    assert lp.ledger.resolved == 1
    assert lp.ledger.refused == 0


# ===========================================================================
# THE COST
# ===========================================================================

def test_a_zero_cost_attempt_is_refused():
    """THE CHECK THAT HAD BEEN DEAD. A zero-cost attempt carries no
    information, so the gate must refuse it BY NAME."""
    lp = loop()
    s = lp.run_once(disc(gap=0.0))
    assert s.outcome == "refused:attempt_cost_zero"
    assert not s.reached_nothing, (
        "a refused attempt never reached the void -- the gate stopped it")


def test_a_costed_attempt_is_admitted():
    """THE CONTRAST, so the refusal above means something."""
    lp = loop()
    s = lp.run_once(disc(gap=0.5))
    assert s.outcome.startswith("named:")
    assert s.cost == pytest.approx(0.5)


def test_the_cost_is_exactly_the_gap():
    """NO FLOOR. The first version added 0.1, which made every attempt
    costed and the zero-cost refusal unreachable."""
    lp = loop()
    s = lp.spark(disc(gap=0.37))
    assert s.cost == pytest.approx(0.37)


def test_an_attempt_with_no_observation_is_refused():
    """Nothing observed means nothing to seek, so there is no drive."""
    lp = loop()
    s = lp.run_once(disc(gap=0.5, observed=""))
    assert s.outcome == "refused:no_observed"


# ===========================================================================
# THE LEDGER
# ===========================================================================

def test_the_counts_add_up():
    """No phantom attempts and no phantom resolutions."""
    lp = loop()
    lp.run_once(disc(gap=0.5))
    lp.run_once(disc(gap=0.0))
    lp.run_once(disc(gap=0.7))
    led = lp.ledger
    assert led.attempts == 3
    assert led.resolved + led.refused == led.attempts


def test_a_refused_attempt_is_not_a_resolved_one():
    """NO LAUNDERING. A refusal cannot be counted as knowledge."""
    lp = loop()
    lp.run_once(disc(gap=0.0))
    assert lp.ledger.resolved == 0
    assert lp.ledger.refused == 1
    assert lp.ledger.resolve_rate() == pytest.approx(0.0)


def test_the_resolve_rate_is_the_measure():
    """AND THE RATE IS THE MEASURE -- not accuracy, because the system
    is measuring how fast it closes what it cannot yet explain."""
    lp = loop()
    lp.run_once(disc(gap=0.5))
    lp.run_once(disc(gap=0.0))
    assert lp.ledger.resolve_rate() == pytest.approx(0.5)


# ===========================================================================
# THE TERMINATION
# ===========================================================================

def test_the_loop_does_not_terminate_by_exhaustion():
    """THE RULE. Unlimited seeking means unlimited attempts; the loop
    ends only by RESOLUTION or by a closed region."""
    lp = loop()
    for i in range(30):
        s = lp.run_once(disc(gap=0.5))
        assert s.outcome.startswith("named:")
    assert lp.ledger.attempts == 30
    assert not lp.ledger.is_blocked()


def test_it_terminates_when_the_refusals_close_a_region():
    """THE END. A run of refusals declares the region closed, and the
    refusals are what did it."""
    lp = loop()
    threshold = lp.ledger.blocked_after
    for i in range(threshold):
        lp.run_once(disc(gap=0.0, observed=""))
    assert lp.ledger.is_blocked()
    assert lp.ledger.consecutive_refusals >= threshold


def test_a_closed_region_is_named_not_just_counted():
    """TRANSFERABLE KNOWLEDGE. The refusal says WHY, so the next attempt
    aims elsewhere rather than repeating."""
    lp = loop()
    s = lp.run_once(disc(gap=0.0, observed=""))
    assert s.outcome == "refused:attempt_cost_zero"
    # and the direction was recorded even though it was refused
    assert s.direction is not None


def test_a_refusal_after_a_success_does_not_count_as_consecutive():
    """THE SEQUENCE MATTERS. A success resets the count, because the
    region is not closed."""
    lp = loop()
    lp.run_once(disc(gap=0.5))
    lp.run_once(disc(gap=0.0, observed=""))
    lp.run_once(disc(gap=0.5))
    lp.run_once(disc(gap=0.0, observed=""))
    assert lp.ledger.consecutive_refusals == 1


# ===========================================================================
# THE DRIVES ARE DISJOINT AND MEASURABLE
# ===========================================================================

def test_the_four_drives_are_distinct():
    """Each drive is a different KIND of not-knowing, and a different
    instrument."""
    kinds = {Drive.Unexplained, Drive.Incapable, Drive.Unattempted,
             Drive.RefusalFollowed}
    assert len(kinds) == 4
    assert len({k.as_str() for k in kinds}) == 4


def test_a_refusal_followed_drive_costs_something():
    """A follow-up attempt aimed at a NAMED limit is not a zero-cost
    attempt -- and the first version of this file made it one, which
    made the four drives indistinguishable."""
    d = Discrepancy(kind=Drive.RefusalFollowed,
                    observed="the last attempt was refused",
                    expected="a costed attempt", gap=0.5,
                    target="the costed attempt")
    lp = loop()
    s = lp.run_once(d)
    assert s.outcome.startswith("named:")
    assert s.cost > 0.0
