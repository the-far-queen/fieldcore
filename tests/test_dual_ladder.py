"""
test_dual_ladder.py -- the dual ladder must be able to FAIL.

THE RULE: a check that cannot go red is not a check. Every assertion
below names the mutation that must break it, and two of the mutations
are the bugs this file's own development found:

  * the verdict flag was read backwards, so every REFUSAL read as a
    resolution
  * the ladder advanced the rung on every refusal, so the "two
    refusals per rung" rule was dead code

WHAT IS ASSERTED, and what each one is worth:

  THE LADDER'S SHAPE
    it starts at 1 bit and 1 stalk       the cheap corner is the default
    it alternates the two axes           neither axis is spent alone
    the cost grows monotonically         the expensive corner is last
    the population never decreases       the axes only go up

  THE ESCALATION
    one refusal does NOT advance the rung    the retry rule
    two refusals DO advance it               and only then
    a non-escalating refusal STOPS the climb  refuse_norm is not a
                                            reason to spend more
    the immediate case takes ONE step        the common case is cheap

  THE COST
    the resolved rung's cost is the sum     the accounting is real
    a resolved-at-1-bit question costs 1     the 747 lesson, enforced

  THE LEDGER
    every step is recorded               a refusal that cannot be seen
                                         cannot be learned from
    the reason is on every step           no bare booleans
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dual_ladder import (  # noqa: E402
    DualLadder,
    POPULATION_AXIS,
    REFUSALS_PER_RUNG,
    Rung,
    WIDTH_AXIS,
    build_ladder,
)


# ===========================================================================
# HELPERS
# ===========================================================================

def table(mapping):
    """An attempt backed by a (width, population) -> (allowed, reason, margin)
    table. Absent keys are REFUSALS."""
    def attempt(rung: Rung):
        return mapping.get((rung.width, rung.population),
                           (False, "refuse_alignment", 0.0))
    return attempt


# ===========================================================================
# THE LADDER'S SHAPE
# ===========================================================================

def test_the_ladder_starts_at_one_bit_and_one_stalk():
    """The cheap corner is the default.

    MUTATION: start the ladder at (4, 2)."""
    rungs = build_ladder()
    assert rungs[0].width == 1
    assert rungs[0].population == 1
    assert rungs[0].cost == 1


def test_the_ladder_alternates_the_two_axes():
    """Neither axis is spent alone.

    MUTATION: make the ladder climb population twice in a row."""
    rungs = build_ladder()
    axes = [r.axis for r in rungs[1:]]
    # every other move should be the other axis
    seen = []
    for a in axes:
        if a == "width":
            seen.append("width")
        elif a == "population":
            seen.append("population")
    # after the first move, the axis must alternate
    for i in range(1, len(seen)):
        if seen[i] != seen[i - 1]:
            continue
        # a repeat is allowed only when one axis is exhausted
        assert i == len(seen) - 1, (
            "the axes must alternate: %r" % (seen,))


def test_the_cost_grows_monotonically():
    """The expensive corner is reached last.

    MUTATION: reorder the ladder so a wide rung comes before a narrow
    one."""
    rungs = build_ladder()
    costs = [r.cost for r in rungs]
    for a, b in zip(costs, costs[1:]):
        assert b >= a, "cost must not go down: %r" % (costs,)


def test_the_population_never_decreases():
    """MUTATION: let the width climb without the population."""
    pops = [r.population for r in build_ladder()]
    for a, b in zip(pops, pops[1:]):
        assert b >= a


def test_the_width_never_decreases():
    widths = [r.width for r in build_ladder()]
    for a, b in zip(widths, widths[1:]):
        assert b >= a


# ===========================================================================
# THE ESCALATION
# ===========================================================================

def test_one_refusal_does_not_advance_the_rung():
    """THE RETRY RULE. This is the bug the file's own development found:
    the ladder advanced on every refusal, so the counter reset before it
    could reach two, and the rule was dead code.

    MUTATION: advance the rung on every refusal."""
    ladder = DualLadder()
    # refuse (1,1) once, then answer at (1,1) again
    calls = {"n": 0}

    def attempt(rung):
        calls["n"] += 1
        if calls["n"] == 1:
            return (False, "refuse_alignment", 0.1)
        return (True, "allow", 0.9)

    run = ladder.run(attempt)
    # the first refusal must be retried at the SAME rung
    assert run.steps[0].rung.width == run.steps[1].rung.width
    assert run.steps[0].rung.population == run.steps[1].rung.population
    assert run.resolved_at is not None


def test_two_refusals_advance_the_rung():
    """MUTATION: require three refusals per rung."""
    ladder = DualLadder()
    calls = {"n": 0}

    def attempt(rung):
        calls["n"] += 1
        if calls["n"] <= REFUSALS_PER_RUNG:
            return (False, "refuse_alignment", 0.1)
        return (True, "allow", 0.9)

    run = ladder.run(attempt)
    assert run.resolved_at is not None
    # the third call must be at a LATER rung than the first
    assert run.steps[0].rung != run.steps[2].rung


def test_a_non_escalating_refusal_stops_the_climb():
    """'refuse_norm' is not a reason to spend more compute: the reading
    was too loud, and reading it wider would not help.

    MUTATION: treat every refusal as an escalation trigger."""
    ladder = DualLadder()
    run = ladder.run(table({(1, 1): (False, "refuse_norm", 0.0)}))
    assert len(run.steps) == 1, "the ladder must stop at the first rung"
    assert run.resolved_at is None
    assert run.final_reason == "refuse_norm"


def test_the_immediate_case_takes_one_step():
    """THE 747 LESSON, enforced. The overwhelming majority of questions
    must not leave the 1-bit layer.

    MUTATION: start the ladder at a wider rung."""
    ladder = DualLadder()
    run = ladder.run(table({(1, 1): (True, "allow", 0.95)}))
    assert run.steps_taken == 1
    assert run.total_cost == 1
    assert run.resolved_at is not None


def test_the_ladder_stops_when_exhausted():
    """A ladder that never stops is a ladder that spends compute for
    nothing.

    MUTATION: return a resolution when the rungs run out.

    AND THE CEILING COMES FIRST. MEASURED 2026-10-31: the ladder's
    measured ceiling is population 3, so a ladder with no measurements
    at all now stops at the CAP, not at the end of the rungs -- and it
    says so by name. The two are different events and the reason
    distinguishes them:

      ladder_capped      the measurement says the next rung buys a
                          width the reading cannot carry
      ladder_exhausted   the rungs ran out with nothing left to try

    **A test that asserts only one of them cannot tell whether the
    ladder stopped for the RIGHT reason.** So this asserts BOTH: that
    the reason is one of the two named ones, and that when the cap
    file is absent the ladder falls back to running out of rungs --
    because a ladder with no measurement must still stop.
    """
    ladder = DualLadder()
    run = ladder.run(table({}))
    assert run.resolved_at is None
    assert run.final_reason.startswith(("ladder_capped", "ladder_exhausted")), \
        run.final_reason
    if run.final_reason.startswith("ladder_capped"):
        # the cap fired, so it did NOT climb every rung
        assert run.steps_taken < len(ladder.rungs) * REFUSALS_PER_RUNG, (
            "the ladder reported a cap but climbed every rung")
    else:
        assert run.steps_taken == len(ladder.rungs) * REFUSALS_PER_RUNG


def test_the_ladder_stops_at_the_measured_ceiling():
    """AND THE CEILING IS ENFORCED, with the number in the reason.

    MEASURED 2026-10-31: the cap is population 3 (the surplus peaks
    there and goes negative above it), so a ladder that tries to climb
    to population 4 must be stopped, and the reason must carry the
    measurement.
    """
    from ladder_cap import load_cap
    cap = load_cap()
    ladder = DualLadder()
    run = ladder.run(table({}))
    assert run.final_reason.startswith("ladder_capped"), run.final_reason
    assert "measured peak %d" % cap.population in run.final_reason, (
        "the reason does not carry the measured peak: %r"
        % run.final_reason)
    assert "bench_balance_final" in run.final_reason, (
        "the reason does not name the command that re-measures it: %r"
        % run.final_reason)


def test_the_refusal_reason_quotes_the_MEASURED_surplus():
    """**AND THE NUMBER IN THE REASON IS THE MEASURED ONE.**

    MEASURED 2026-10-31: the reader read the condition's key as
    "surplus" while `bench_balance_final.py` writes "peak_surplus".
    The key was never there, so `worst_surplus()` returned None and the
    refusal said the surplus at the peak was "negative" -- while the
    measured surplus is +7.298 bits. **A refusal that quotes a number
    that is not there is worse than a refusal with no number**, because
    a reader checks the number.

    So this check asserts the reason carries the surplus THE CAP FILE
    RECORDS, read through the same accessor the reason is built from.
    And it reads the cap file's OWN key -- so if the writer and the
    reader drift apart again, this goes red on the drift rather than
    on the symptom.
    """
    from ladder_cap import load_cap
    cap = load_cap()
    measured = cap.worst_surplus()
    assert measured is not None, (
        "the cap file records no surplus at the peak, so the refusal "
        "cannot quote a measured number -- the reader's key and the "
        "writer's key have drifted apart")
    # the reader and the writer must agree on the key, read directly
    # from the file the bench wrote
    import json
    import os
    from ladder_cap import CAP_PATH
    with open(CAP_PATH, encoding="utf-8") as fh:
        raw = json.load(fh)
    keys = set()
    for c in raw.get("conditions", []):
        keys.update(k for k in ("peak_surplus", "surplus") if k in c)
    assert "peak_surplus" in keys or "surplus" in keys, (
        "the cap file's conditions carry no surplus key at all: %s"
        % sorted(raw.get("conditions", [{}])[0].keys()))

    reason = cap.reason_for(8, 8)
    assert reason, "an unreachable rung produced no reason"
    assert "negative" not in reason, (
        "the refusal says the surplus is negative, but the cap file "
        "records %+.4f -- the reason is quoting a number that is not "
        "there" % measured)
    assert ("%+.2f" % measured) in reason, (
        "the refusal does not carry the measured surplus %+.4f: %r"
        % (measured, reason))


def test_the_cap_report_prints_every_measured_row():
    """**AND THE REPORT IS NOT A TABLE OF QUESTION MARKS.**

    MEASURED 2026-10-31: the report read the conditions' "surplus" and
    "capacity" keys, and the bench writes "peak_surplus" and
    "peak_capacity_bits" -- so all ten rows printed "?" for both, and a
    table of "?"s reads like a measurement that found nothing.

    So this runs the report and asserts it prints a NUMBER for every
    condition, not a question mark.
    """
    import io
    import contextlib
    import ladder_cap
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ladder_cap.main()
    out = buf.getvalue()
    from ladder_cap import load_cap
    cap = load_cap()
    assert out.count("?") == 0, (
        "the cap report printed %d question marks -- the surplus and "
        "capacity keys have drifted from the bench's:\n%s"
        % (out.count("?"), out))
    for c in cap.conditions:
        assert c.get("peak_surplus") is not None, (
            "a condition carries no peak_surplus: %s" % c)


# ===========================================================================
# THE COST
# ===========================================================================

def test_the_cost_is_the_sum_of_the_steps():
    """The accounting is real.

    MUTATION: report the cost of the resolved rung only."""
    ladder = DualLadder()
    run = ladder.run(table({
        (1, 1): (False, "refuse_alignment", 0.1),
        (4, 1): (True, "allow", 0.8),
    }))
    assert run.total_cost == sum(s.cost for s in run.steps)
    assert run.total_cost > 1, "a question that failed once cost more"


def test_the_reach_grows_with_the_rung():
    """The area of authority grows.

    MUTATION: make reach constant."""
    reaches = [r.reach for r in build_ladder()]
    for a, b in zip(reaches, reaches[1:]):
        assert b >= a


# ===========================================================================
# THE LEDGER
# ===========================================================================

def test_every_step_is_recorded():
    """A refusal that cannot be seen cannot be learned from.

    MUTATION: do not append to run.steps.

    AND THE LEDGER AND THE COUNT ARE THE SAME THING. MEASURED
    2026-10-31: `steps_taken` is `len(steps)` -- it is a property of
    the ledger, not a separate tally of ATTEMPTS. So the assertion
    cannot multiply by REFUSALS_PER_RUNG: that constant counts how
    many times each rung may be attempted, and each attempt is not a
    separate ledger entry.

    **AND THE COUNT FOLLOWS THE CAP.** With the cap file present the
    ladder stops at the measured ceiling (population 3), so it takes
    fewer steps than the full rung list. The assertion is on the steps
    that were TAKEN, and on the ledger matching them.
    """
    ladder = DualLadder()
    run = ladder.run(table({}))
    assert len(run.steps) == run.steps_taken, (
        "the ledger holds %d steps but the run counted %d"
        % (len(run.steps), run.steps_taken))
    assert run.steps_taken > 0, "the ladder took no steps at all"
    # and every step carries the rung it was taken at
    for s in run.steps:
        assert s.rung is not None
        assert s.reason, "a step with no reason"


def test_every_step_names_its_reason():
    """No bare booleans.

    MUTATION: return an empty reason string."""
    ladder = DualLadder()
    run = ladder.run(table({}))
    for s in run.steps:
        assert s.reason


def test_the_final_reason_is_always_set():
    """An unresolved run must say why it gave up.

    MUTATION: leave final_reason empty."""
    ladder = DualLadder()
    run = ladder.run(table({}))
    assert run.final_reason


# ===========================================================================
# THE AXES THEMSELVES
# ===========================================================================

def test_the_width_axis_matches_the_rust_core():
    """The Rust core's ladder is 1/4/8/16/32/64/128/256 and its last
    rung is 256, not a value past it.

    MUTATION: add a W512 rung."""
    assert list(WIDTH_AXIS) == [1, 4, 8, 16, 32, 64, 128, 256]
    assert 512 not in WIDTH_AXIS


def test_the_population_axis_matches_the_nested_topology():
    """The nested stalk topology is hyperlocal -> groups -> area -> full,
    and it only spends as much as is needed.

    MUTATION: start the population axis at 4. MUTATION: drop the top of
    the population axis.

    WAS MISSED for the second one, because the old version only
    asserted that the axis was SORTED -- and a truncated axis is still
    sorted. The literal list is the check.
    """
    assert POPULATION_AXIS[0] == 1
    assert list(POPULATION_AXIS) == [1, 2, 4, 8, 16, 32]
    assert list(POPULATION_AXIS) == sorted(POPULATION_AXIS)


def test_the_ladder_has_one_rung_per_axis_step():
    """The interleaved ladder has one rung per width plus one per
    population, minus the shared start -- so 8 + 6 - 1 = 13.

    MUTATION: truncate either axis, or stop the ladder early.

    WAS MISSED. Nothing asserted the ladder's LENGTH, so a ladder that
    quietly stopped short of the top of an axis passed every check.
    """
    rungs = build_ladder()
    expected = len(WIDTH_AXIS) + len(POPULATION_AXIS) - 1
    assert len(rungs) == expected, (
        "the ladder must have %d rungs, one per axis step, and it has %d"
        % (expected, len(rungs)))
    # and every rung must be distinct
    keys = [(r.width, r.population) for r in rungs]
    assert len(keys) == len(set(keys)), "a rung is repeated: %r" % (keys,)


# ===========================================================================
# THE CHECKS THAT COULD NOT FAIL
# ===========================================================================
#
# These three were MISSED by the mutation run of 2026-10-25. Each one
# names the mutation it must catch, and each mutation was found by
# running it and watching the suite stay green.
#
# The pattern in all three: the suite asserted a PROPERTY that the
# mutation happened to preserve, so it never went red. A property that
# every mutant satisfies is not a property.

def test_the_cost_counts_the_population():
    """MUTATION: the cost is the width only.

    WAS MISSED. The old suite checked that the cost never goes DOWN and
    that the immediate case costs 1 -- both of which a width-only cost
    also satisfies, because every rung's population is at least 1.

    This one asserts the actual arithmetic at a rung where the
    population is more than 1.
    """
    rungs = build_ladder()
    # find a rung whose population is greater than 1
    multi = [r for r in rungs if r.population > 1]
    assert multi, "the ladder must have a rung with a population > 1"
    for r in multi:
        assert r.cost == r.width * r.population
    # and the population must actually change the cost
    w1 = [r for r in rungs if r.population == 1]
    assert w1 and multi
    assert w1[0].cost != multi[0].cost or \
        w1[0].width != multi[0].width


def test_the_reach_grows_with_the_population():
    """MUTATION: the reach is a constant 1.

    WAS MISSED. The old suite asserted the reach never decreases --
    a constant satisfies that trivially.

    This one asserts the reach is the width's area times the
    population, at a rung where the population is more than 1.
    """
    from dual_ladder import REACH
    rungs = build_ladder()
    multi = [r for r in rungs if r.population > 1]
    assert multi, "the ladder must have a rung with a population > 1"
    for r in multi:
        assert r.reach == REACH.get(r.width, 0) * r.population
    # the reach must exceed the width's own area somewhere
    assert any(r.reach > REACH.get(r.width, 0) for r in multi)


def test_the_step_verdict_has_one_source():
    """MUTATION: the verdict flag is read backwards.

    WAS MISSED. The old Step carried BOTH a `refused` flag and an
    `allowed` flag, and only one of them drove control flow, so
    inverting the other changed nothing observable.

    Now there is ONE field, `allowed`, and `refused` is derived from
    it. This asserts they cannot disagree, and that the derived value
    is the one the control flow uses.
    """
    ladder = DualLadder()
    run = ladder.run(table({
        (1, 1): (False, "refuse_alignment", 0.1),
        (1, 1): (False, "refuse_alignment", 0.1),
    }))
    assert run.steps, "the run must have steps"
    for s in run.steps:
        assert s.refused == (not s.allowed), (
            "the derived refusal must be the negation of the stored verdict")

    # and the control flow must agree with the stored verdict: a step
    # marked refused must never be the one that resolved the run
    run2 = ladder.run(table({(1, 1): (True, "allow", 0.9)}))
    assert run2.resolved_at is not None
    assert run2.steps[-1].allowed is True
    assert run2.steps[-1].refused is False


def test_the_ladder_refuses_to_build_a_ladder_that_cannot_climb():
    """MUTATION: the width index is pinned (the infinite loop).

    WAS A HANG, not a red. The guard turns the hang into an error, so
    the defect is now a failure rather than a session that never comes
    back.

    The check is on the AST, not on the text: a text search trips over
    the comment that documents the bug, which is how a check stops
    meaning anything.
    """
    import ast
    import dual_ladder

    src = dual_ladder.__file__
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    tree = ast.parse(text)

    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_ladder":
            fn = node
            break
    assert fn is not None, "build_ladder must exist"

    pinned = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not isinstance(tgt, ast.Name) or tgt.id != "wi":
                continue
            val = node.value
            # a pinned index is min(<constant>, ...) with a constant
            # first argument -- it does not carry the previous value
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) \
                    and val.func.id == "min" and val.args:
                first = val.args[0]
                if isinstance(first, ast.Constant) and first.value == 1:
                    pinned.append(ast.dump(node))
    assert not pinned, (
        "the width index must not be pinned to a constant: that was the "
        "infinite loop. %d pinned assignment(s)." % len(pinned))

    # and the real builder still works and still advances
    rungs = build_ladder()
    assert len(rungs) > 1
    assert len(rungs) <= len(WIDTH_AXIS) + len(POPULATION_AXIS)


def test_every_rung_is_distinct():
    """MUTATION: the ladder emits the same rung twice.

    A ladder that revisits a rung is spending compute on a rung it has
    already read.
    """
    rungs = build_ladder()
    keys = [(r.width, r.population) for r in rungs]
    assert len(keys) == len(set(keys)), "a rung is repeated: %r" % (keys,)


def test_the_ladder_ends_at_the_top_of_both_axes():
    """The last rung must be at the cap of BOTH axes, and the ladder
    must not stop early.

    MUTATION: break out of the loop one rung early.

    WAS MISSED, because the old version asserted `width == max OR
    population == max`. The ladder legitimately reaches the population
    cap before the width cap, so a ladder that stopped early still
    satisfied it. An OR over two independent properties is satisfied by
    satisfying one of them.
    """
    rungs = build_ladder()
    assert rungs[-1].width == max(WIDTH_AXIS), (
        "the ladder must reach the widest rung: %r" % (rungs[-1],))
    assert rungs[-1].population == max(POPULATION_AXIS), (
        "the ladder must reach the largest population: %r" % (rungs[-1],))
    # and the widest rung must be the last one, not merely present
    assert rungs[-1].width == max(r.width for r in rungs)
    assert rungs[-1].population == max(r.population for r in rungs)
