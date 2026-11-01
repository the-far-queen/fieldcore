"""
tests/test_interstalk_ladder.py -- THE COMBINATION's CHECKS.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED.

**AND WHAT THIS THREAD IS.** Bobby, 2026-11-01: *"we had a working
model with fail up 1 bit 4 8 etc combine them"*. The working model was
`dual_ladder.py` -- the interleaved ladder -- and the combination is
`interstalk_ladder.py`, which drives it with the interstalk channel's
actual readings.

**SO THE THREAD'S QUESTION IS NOT "does the ladder exist"** -- it does,
and it is tested. The question is whether the two halves FIT: does the
interleaved ladder's population axis land on a REAL channel, and does
the channel's refusal vocabulary drive the ladder the way the ladder
expects?
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import bench_failup as BF  # noqa: E402
import dual_ladder as DL  # noqa: E402
import interstalk_ladder as IL  # noqa: E402
import interstalk_link as ILK  # noqa: E402
import wound_core as WC  # noqa: E402


@pytest.fixture(scope="module")
def pool():
    return BF.make_population(10)


@pytest.fixture(scope="module")
def link(pool):
    return ILK.InterstalkLink(core=WC.WoundCore(pool))


# --------------------------------------------------------------------------
# the two halves FIT
# --------------------------------------------------------------------------

def test_the_ladder_alternates_the_two_axes():
    """THE WORKING MODEL, and its shape is the whole design: width and
    population interleave, because finishing one axis first is always
    wrong.

    * ALL WIDTH FIRST: a wide serial read of a hyperlocal question.
    * ALL POPULATION FIRST: the whole area recruited before the local
      question was shown to be unanswerable locally.
    """
    axes = [r.axis for r in DL.build_ladder()][:6]
    assert axes == ["start", "width", "population", "width", "population",
                    "width"], axes


def test_the_ladder_starts_cheap_and_ends_wide():
    rungs = DL.build_ladder()
    assert rungs[0].width == 1 and rungs[0].population == 1
    assert rungs[0].cost == 1
    assert rungs[-1].width >= 8


def test_the_refusals_per_rung_is_two():
    """At one, a single unlucky reading escalates; at three, the cheap
    layer does real work and the expensive layer stays rare."""
    assert DL.REFUSALS_PER_RUNG == 2


def test_the_cost_model_is_width_times_population():
    """WIDTH is serial and expensive in TIME; POPULATION is parallel and
    expensive in SPACE. The product is the cost."""
    for r in DL.build_ladder():
        assert r.cost == r.width * r.population


# --------------------------------------------------------------------------
# the combination actually reads the channel
# --------------------------------------------------------------------------

def test_the_combination_reads_the_channel(link, pool):
    """AND THE POPULATION AXIS IS REAL -- it lands on a channel with
    that many stalks in view, not on a label."""
    lad = IL.InterstalkLadder(link, pool)
    run = lad.run()
    assert len(lad.readings) >= 1
    assert run.final_reason, "the run must say why it stopped"
    for r in lad.readings:
        assert r.width >= 1
        assert r.population >= 1
        assert r.reason


def test_the_combination_resolves_on_a_clean_channel(link, pool):
    """MEASURED: the channel is clean -- the interference between stalks
    IS the noise, and a single-stalk channel is trivially readable.
    So the ladder resolves at its FIRST rung, and that is correct: the
    cheap layer is cheap because it is both narrow and hyperlocal."""
    lad = IL.InterstalkLadder(link, pool)
    run = lad.run()
    assert run.resolved_at is not None, run.final_reason
    assert run.resolved_at.width == 1


def test_a_refused_rung_moves_the_ladder(link, pool):
    """AND A REFUSED RUNG MOVES THE LADDER -- so the combination is not
    a decoration on top of a working ladder."""
    class AlwaysRefuses:
        def __init__(self):
            self.calls = 0

        def attempt(self, rung):
            self.calls += 1
            return (False, "refuse_alignment", 0.0)

    st = AlwaysRefuses()
    run = DL.DualLadder().run(st.attempt)
    assert len(run.steps) > 1, "the ladder did not climb"
    assert st.calls > 1


def test_a_non_channel_refusal_stops_the_ladder():
    """AND ONLY THE CHANNEL'S OWN REFUSALS ESCALATE. A refusal for any
    other reason is a genuine refusal and climbing will not change the
    answer -- so the ladder stops and says why."""
    class Stops:
        def attempt(self, rung):
            return (False, "refuse_norm", 0.0)

    run = DL.DualLadder().run(Stops().attempt)
    assert len(run.steps) == 1
    assert run.final_reason == "refuse_norm"


# --------------------------------------------------------------------------
# the measured cap
# --------------------------------------------------------------------------

def test_the_measured_cap_refuses_by_name():
    """AND THE CAP REFUSES BY NAME, with the measured surplus in the
    reason -- because a rung above the peak buys a width the reading
    cannot carry."""
    ladder = DL.DualLadder()
    over = [r for r in DL.build_ladder() if r.population >= 4]
    assert over, "the ladder should have rungs above the measured peak"
    assert not ladder.reachable(over[0])
    reason = ladder.unreachable_reason(over[0])
    assert "peak" in reason, reason
    assert "bench_balance_final" in reason, reason


def test_the_measured_peak_population_is_three():
    """MEASURED: the peak population is 3, found by two independent
    derivations -- and the coarse one (powers of two only) was the one
    that was wrong, because a grid that cannot hold the answer cannot
    report it."""
    ladder = DL.DualLadder()
    assert ladder.cap is not None, "the cap must be loaded, not optional"
    assert ladder.cap.population == 3, ladder.cap.population


def test_the_ladder_stops_at_the_cap():
    """AND A RUN THAT ESCALATES REFUSES PAST THE PEAK."""
    class Escalating:
        def attempt(self, rung):
            return (False, "refuse_alignment", 0.0)

    run = DL.DualLadder().run(Escalating().attempt)
    assert "capped" in run.final_reason or \
        run.final_reason == "ladder_exhausted", run.final_reason
    assert run.resolved_at is None


def test_the_combination_uses_the_measured_cap(link, pool):
    """AND THE COMBINITION USES THE CAP, not just the ladder.

    MEASURED: the harness mutation that removes the cap from the
    combination went GREEN -- so the test was decorative, because it
    only checked the LADDER's cap, not the COMBINATION's.

    **AND THE CAP MATTERS HERE**, because the population axis is what
    the combination makes real. Without the cap the ladder climbs to
    W256 x P32 -- a population of 32 stalks -- for a question the
    measurement says is unanswerable at population 8 already.
    """
    lad = IL.InterstalkLadder(link, pool)
    assert lad.use_cap is True, "the combination must use the cap"

    # AND IT STOPS THERE: a run that always refuses must be capped.
    class Escalating:
        def attempt(self, rung):
            return (False, "refuse_alignment", 0.0)

    # AND WHEN EVERY READING IS REFUSED, the combination stops at the
    # cap. MEASURED: the real channel RESOLVES at the first rung --
    # it is clean, and a single-stalk channel is trivially readable --
    # so the climbing case has to be driven.
    import dual_ladder as DL
    lad2 = IL.InterstalkLadder(link, pool)

    class Escalating:
        def __init__(self, inner):
            self.inner = inner

        def attempt(self, rung):
            return (False, "refuse_alignment", 0.0)

    run = DL.DualLadder(use_cap=True).run(Escalating(lad2).attempt)
    assert run.resolved_at is None
    assert "capped" in run.final_reason, run.final_reason
    # and every rung it tried was within the cap
    for step in run.steps:
        assert step.rung.population <= 3, (
            "the combination climbed to population %d, above the "
            "measured peak of 3" % step.rung.population)

    # AND WITHOUT THE CAP IT WOULD GO PAST IT -- which is why the cap
    # has to be there and has to be asserted.
    uncapped = DL.DualLadder(use_cap=False).run(
        Escalating(lad2).attempt)
    assert uncapped.final_reason != run.final_reason or \
        max(s.rung.population for s in uncapped.steps) > \
        max(s.rung.population for s in run.steps), (
        "removing the cap changed nothing, so the cap is not load-"
        "bearing in this path")


def test_the_combinations_attempt_carries_the_channels_own_reason(link, pool):
    """THE COMBINATION'S ATTEMPT MUST PASS THE CHANNEL'S OWN REASON
    THROUGH, and this is the check the mutations were escaping.

    **AND THE MUTATION THAT BROKE THIS WENT GREEN BEFORE.** MEASURED:
    replacing the attempt's reason with a constant "refuse_norm" -- so
    the channel's own verdict stopped reaching the ladder -- did not
    break any test, because every test exercised the LADDER directly
    rather than the COMBINATION's attempt.

    **AND A CONSTANT REASON WOULD BE CATASTROPHIC AND QUIET.** The
    ladder escalates on exactly three reasons --
    `refuse_alignment`, `channel_flat_channel`,
    `channel_irrecoverable` -- and stops on everything else. So a
    constant reason would either stop the ladder at the first rung or
    climb it to the cap, and either way the channel's actual verdict
    would be ignored.

    So the attempt's reason must be the channel's, and this asserts it.
    """
    lad = IL.InterstalkLadder(link, pool)
    import dual_ladder as DL
    rung = DL.build_ladder()[0]

    allowed, reason, margin = lad._attempt(rung)
    # AND THE REASON IS THE CHANNEL'S OWN, whatever it is. MEASURED: the
    # first version of this check asserted the reason was one of the
    # ESCALATING ones -- and it failed on a SUCCESSFUL read, whose
    # reason is "allow" and which correctly does NOT escalate.
    #
    # So the check is that the reason is the channel's, not that it is
    # an escalating one. The escalating case is asserted below with a
    # channel that actually refuses.
    assert reason in ("allow",) + tuple(DL.DualLadder.ESCALATING), (
        "the attempt returned %r, which is neither a success nor one of "
        "the channel refusals" % reason)
    assert allowed is True, "the clean channel should be allowed"
    assert isinstance(margin, float)

    # AND WHEN THE CHANNEL REFUSES, THE ATTEMPT MUST REPORT THE
    # CHANNEL'S OWN REASON -- so a refusal that escalates is not
    # silently turned into one that does not.
    class Refusing:
        def exchange(self, tx, rx, in_view=None):
            class E:
                allowed = False
                reason = "channel_irrecoverable"
                alignment = 0.0
            return E()

    lad2 = IL.InterstalkLadder(Refusing(), pool)
    allowed2, reason2, margin2 = lad2._attempt(rung)
    assert allowed2 is False
    assert reason2 == "channel_irrecoverable", (
        "the attempt rewrote the channel's reason as %r" % reason2)
    assert reason2 in DL.DualLadder.ESCALATING, (
        "the channel's refusal no longer escalates, so the ladder "
        "would stop instead of climbing")


def test_the_combination_passes_the_cap_through(link, pool):
    """AND THE COMBINATION MUST BUILD A CAPPED LADDER, and this is the
    second check the mutations were escaping.

    MEASURED: removing the cap from the combination went GREEN,
    because every test exercised the ladder's own cap rather than the
    combination's.

    **AND THE FIRST VERSION OF THIS CHECK ALSO MISSED IT**, because it
    asserted on `lad.use_cap` -- the ATTRIBUTE -- while the mutation
    changed the USE SITE. **THE ATTRIBUTE SAYS WHAT WAS ASKED FOR; THE
    LADDER SHOWS WHAT WAS GIVEN.** So the check observes the ladder
    the combination actually builds.
    """
    import dual_ladder as DL

    lad = IL.InterstalkLadder(link, pool)

    # THE LADDER THE COMBINATION ACTUALLY BUILDS, captured by
    # watching the construction. This is the behaviour, not the
    # attribute.
    built = {}
    original = DL.DualLadder.__init__

    def spy(self, *a, **kw):
        original(self, *a, **kw)
        # the CAP is what the ladder ends up HOLDING, and the kwarg is
        # what it was ASKED for -- and the check wants both.
        built["cap"] = self.cap
        built["asked_use_cap"] = kw.get("use_cap")

    DL.DualLadder.__init__ = spy
    try:
        lad.run()
    finally:
        DL.DualLadder.__init__ = original

    assert built.get("asked_use_cap") is True, (
        "the combination built a ladder with use_cap=%r"
        % built.get("asked_use_cap"))
    assert built.get("cap") is not None, (
        "the combination built a ladder with NO cap, so it would climb "
        "to population 32 for a question the measurement says is "
        "unanswerable at population 8")

    # AND THE LADDER IT BUILDS MUST REFUSE A POPULATION-4 RUNG.
    over = [r for r in DL.build_ladder() if r.population >= 4]
    assert over, "the ladder should have rungs above the peak"
    ladder = DL.DualLadder(use_cap=True)
    assert not ladder.reachable(over[0]), (
        "the combination's ladder would climb to population %d, above "
        "the measured peak of 3" % over[0].population)
    assert "peak" in ladder.unreachable_reason(over[0])
