"""
tests/test_population_escalation.py -- THE ESCALATION POLICY'S CHECKS.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED.

**AND THE CENTRAL ASSERTION IS BOBBY'S CORRECTION**, twice:

  "nope we got as far as increasng number of stalks ie population was
   cheaper at 1 bit and only the 4 and 8 bit then increase pop again
   not 16 32 64 etc"

  "no grow pop at 1 bit first"

So: the POPULATION grows FIRST, at 1 bit, and the width only widens when
the population is spent -- and never past 8.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import population_escalation as PE  # noqa: E402
from population_escalation import (  # noqa: E402
    GROW_POPULATION, POPULATION_FIRST_WIDTHS, RESOLVED, STOPPED, WIDEN,
    PopulationPolicy,
)


def link_width(taps: int) -> int:
    """The link's own width derivation, for the policy to inherit."""
    return 1 if taps <= 1 else (4 if taps <= 2 else 8)


@pytest.fixture()
def policy() -> PopulationPolicy:
    return PopulationPolicy(width_for_taps=link_width,
                           population_step=1, max_population=4)


# --------------------------------------------------------------------------
# the first move
# --------------------------------------------------------------------------

def test_a_readable_exchange_escalates_nothing(policy):
    e = policy.decide(1, 1, readable=True)
    assert e.resolved is True
    assert e.width_used == 1
    assert e.population_after == 1
    assert e.grew_population is False
    assert e.widened is False


def test_an_unreadable_exchange_grows_the_population_first(policy):
    """THE FIRST MOVE. The population grows and the width does NOT."""
    e = policy.decide(1, 1, readable=False)
    assert e.grew_population is True
    assert e.widened is False
    assert e.width_used == 1, "the width must stay at 1 bit"
    assert e.reason == GROW_POPULATION


def test_it_keeps_growing_the_population_while_it_can(policy):
    for pop in (1, 2, 3):
        e = policy.decide(1, pop, readable=False)
        assert e.grew_population is True, "population %d" % pop
        assert e.width_used == 1, "population %d" % pop


# --------------------------------------------------------------------------
# the widening, and its ceiling
# --------------------------------------------------------------------------

def test_only_at_the_population_cap_does_it_widen(policy):
    e = policy.decide(1, 4, readable=False)
    assert e.widened is True
    assert e.grew_population is False
    assert e.reason == WIDEN


def test_it_widens_to_four_bits_not_more(policy):
    e = policy.decide(1, 4, readable=False)
    assert e.width_used == 4


def test_the_policy_never_goes_past_eight_bits():
    """THE CEILING. "only the 4 and 8 bit then increase pop again not
    16 32 64 etc"."""
    assert POPULATION_FIRST_WIDTHS == (1, 4, 8)
    pol = PopulationPolicy(width_for_taps=link_width,
                           population_step=1, max_population=2)
    for taps in range(1, 20):
        for pop in range(0, 4):
            e = pol.decide(taps, pop, readable=False)
            assert e.width_used <= 8, (
                "taps %d pop %d -> %d" % (taps, pop, e.width_used))


def test_it_stops_with_a_reason_when_nothing_is_left(policy):
    e = policy.decide(5, 4, readable=False)
    assert e.reason == STOPPED
    assert e.width_used == e.width_needed
    assert e.resolved is False


# --------------------------------------------------------------------------
# the sequence -- the part the link lacks
# --------------------------------------------------------------------------

def test_the_sequence_grows_the_population_before_widening(policy):
    seq = policy.plan(1, 1, readable=False)
    reasons = [x.reason for x in seq]
    assert reasons[:3] == [GROW_POPULATION] * 3, reasons
    # and the FIRST widening comes after the population is spent
    assert WIDEN not in reasons or reasons.index(WIDEN) > 0


def test_the_sequence_terminates(policy):
    seq = policy.plan(1, 1, readable=False)
    assert len(seq) < 16, str(len(seq))


def test_a_readable_exchange_is_a_one_step_sequence(policy):
    seq = policy.plan(1, 1, readable=True)
    assert len(seq) == 1
    assert seq[0].resolved


def test_the_population_grows_monotonically_through_the_sequence(policy):
    seq = policy.plan(1, 1, readable=False)
    for a, b in zip(seq, seq[1:]):
        assert b.population_after >= a.population_after, \
            "the population must never shrink"


# --------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------

def test_the_escalation_records_both_the_width_and_the_population(policy):
    """A LEDGER THAT ONLY RECORDED THE WIDTH would report "nothing
    escalated" for a system quietly growing its population on every
    exchange."""
    e = policy.decide(1, 1, readable=False)
    d = e.describe()
    for key in ("width_needed", "width_used", "population_before",
                "population_after", "reason", "resolved",
                "grew_population", "widened"):
        assert key in d, key
    assert json.dumps(d) is not None


def test_the_reasons_are_the_project_vocabulary():
    assert GROW_POPULATION == "grow_population"
    assert WIDEN == "widen"
    assert STOPPED == "stopped"
    assert RESOLVED == "resolved"
