"""
tests/test_bicameral_loop.py -- THE TWO TIME SCALES' CHECKS.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration.

**AND EVERY CHECK HERE IS ABOUT A ROBOT.** Bobby, 2026-11-01: *"also
can fc deeply if have microseconds to spare or in robot slice up time
between fast brain and learning my goal is robot operation"*. So the
fast path must not block, the deep path must be bounded, and a claim
nobody checked must be visible.

**AND THE TIMING CHECKS ARE TIMING CHECKS, not assertions about
values.** "the fast path is fast" is a claim about the wall clock, so
it is measured with the wall clock, and the budget is stated.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import bicameral_loop as bl  # noqa: E402
from bicameral_loop import BicameralLoop  # noqa: E402

#: The fast path's budget. A robot's reflex path is MILLISECONDS, so
#: the budget is generous on purpose -- the point is that the deep core
#: does not appear in it at all.
FAST_BUDGET_MS = 50.0


def _loop(deep=None, ground=None, **kw):
    return BicameralLoop(
        lambda p: "fast answer",
        deep if deep is not None else (lambda c: None),
        ground if ground is not None else (lambda t: True),
        **kw)


# --------------------------------------------------------------------------
# the fast path
# --------------------------------------------------------------------------

def test_the_fast_path_does_not_call_the_deep_core():
    """THE FIRST PROPERTY. The fast path answers in microseconds
    because the deep core is not on it at all."""
    calls = {"n": 0}

    def counted(claim):
        calls["n"] += 1
        return None

    loop = _loop(deep=counted)
    loop.ask("q")
    assert calls["n"] == 0


def test_the_fast_answer_is_provisional():
    """An unreviewed answer says so. A robot acting on a provisional
    answer should be able to know that it is provisional."""
    loop = _loop()
    answer = loop.ask("q")
    assert answer.provisional is True


def test_a_slow_core_does_not_slow_the_fast_path():
    """THE SECOND PROPERTY, and it is measured with a clock."""
    def very_slow(claim):
        time.sleep(0.5)
        return None

    loop = _loop(deep=very_slow)
    t0 = time.perf_counter()
    loop.ask("q")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < FAST_BUDGET_MS, "%.1f ms" % elapsed_ms


# --------------------------------------------------------------------------
# the deep path
# --------------------------------------------------------------------------

def test_the_slice_reviews_the_claims():
    loop = _loop(deep=lambda c: None)
    loop.ask("a claim")
    loop.ask("another claim")
    assert loop.review_slice(budget=0.5) == 2


def test_an_upheld_attack_overturns_the_claim():
    loop = _loop(deep=lambda c: "this claim is wrong",
                 ground=lambda t: "wrong" in t)
    loop.ask("a bad claim")
    loop.review_slice(budget=0.5)
    assert loop.overturned == 1
    assert any(c.overturned for c in loop.claims())


def test_a_claim_the_core_cannot_attack_is_reviewed_clean():
    loop = _loop(deep=lambda c: None)
    loop.ask("a claim")
    loop.review_slice(budget=0.5)
    claims = loop.claims()
    assert claims and claims[0].reviewed is True
    assert claims[0].attack == ""
    assert claims[0].overturned is False


def test_the_slice_respects_its_budget():
    """THE THIRD PROPERTY: the deep core may hold the machine only for
    a bounded slice, because a robot that stops moving is a broken
    robot."""
    def slow(claim):
        time.sleep(0.2)
        return None

    loop = _loop(deep=slow)
    for i in range(5):
        loop.ask("q%d" % i)
    t0 = time.perf_counter()
    loop.review_slice(budget=0.1)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.6, "%.3f s" % elapsed


def test_a_failed_core_overturns_nothing():
    """AN UNAVAILABLE CORE IS NOT A REFUTATION, and it must not read as
    a pass either."""
    def broken(claim):
        raise RuntimeError("the core is down")

    loop = _loop(deep=broken)
    loop.ask("a claim")
    loop.review_slice(budget=0.2)
    assert loop.overturned == 0
    assert any(e["event"] == "core_failed" for e in loop.ledger)


# --------------------------------------------------------------------------
# the queue
# --------------------------------------------------------------------------

def test_the_queue_is_bounded():
    """AN UNBOUNDED QUEUE ON A ROBOT IS A MEMORY LEAK THAT ENDS IN A
    CRASH DURING THE ONE OPERATION THAT MATTERED."""
    loop = _loop(queue_limit=5)
    for i in range(30):
        loop.ask("q%d" % i)
    assert len(loop.claims()) <= 5


def test_the_drops_are_recorded():
    """A DROPPED CLAIM IS A CLAIM NOBODY CHECKED, and that has to be
    visible."""
    loop = _loop(queue_limit=5)
    for i in range(30):
        loop.ask("q%d" % i)
    assert loop.dropped > 0
    assert any(e["event"] == "dropped" for e in loop.ledger)


def test_the_unreviewed_count_is_visible():
    loop = _loop()
    for i in range(3):
        loop.ask("q%d" % i)
    assert loop.provisional_count() == 3
    loop.review_slice(budget=0.5)
    assert loop.provisional_count() == 0


def test_the_loop_describes_itself():
    loop = _loop()
    loop.ask("q")
    d = loop.describe()
    assert d["claims"] == 1
    assert d["queue_limit"] > 0
    assert d["slice_seconds"] > 0
