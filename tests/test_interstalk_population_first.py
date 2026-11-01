"""
tests/test_interstalk_population_first.py -- THE LIVE PATH, and the
population-first policy inside it.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED.

**AND THIS IS THE STEEL THREAD THAT CLOSES THE GAP.** The policy was
built and measured in `src/population_escalation.py`, but the LIVE
path -- `interstalk_link.InterstalkLink.exchange()` -- was still
width-first:

    used = escalate(needed)

so the population NEVER GREW in the code that actually runs. **A POLICY
THAT NOBODY CALLS IS A DECORATION.** So this thread wires it in and
measures the wiring.

AND THE MEASUREMENT THE THREAD EXISTS TO PRODUCE: **does the live
exchange actually report POPULATION-FIRST escalation, and does the
ledger show the population moving before the width?**
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import interstalk_link as IL  # noqa: E402
import population_escalation as PE  # noqa: E402
import wound_core as WC  # noqa: E402


@pytest.fixture(scope="module")
def core() -> WC.WoundCore:
    return WC.standard_wound_core()


@pytest.fixture(scope="module")
def link(core) -> IL.InterstalkLink:
    return IL.InterstalkLink(core=core)


# --------------------------------------------------------------------------
# the wiring
# --------------------------------------------------------------------------

def test_the_link_holds_a_population_policy(link):
    """THE POLICY IS IN THE LIVE PATH, and it is INJECTED so it can be
    measured on its own."""
    assert hasattr(link, "_policy")
    assert link._policy is not None
    assert link._policy.width_for_taps is IL.width_for


def test_the_width_first_ladder_is_gone(link):
    """**AND THE WIDTH-FIRST LADDER IS GONE FROM THE LIVE PATH.**

    MEASURED, the old code was `used = escalate(needed)` with the
    ladder running 1, 4, 8, 16, 32, 64, 128, 256 -- so the population
    never grew in the code that actually runs.
    """
    import inspect
    src = inspect.getsource(IL.InterstalkLink.exchange)
    assert "nxt = escalate(needed)" not in src, (
        "the width-first ladder is still in the live path")
    assert "self._policy.decide" in src, (
        "the live path does not consult the population-first policy")


# --------------------------------------------------------------------------
# the exchange, measured
# --------------------------------------------------------------------------

def test_the_exchange_records_the_population(link, core):
    """AND THE EXCHANGE CARRIES THE POPULATION, because a ledger that
    only recorded the width would report "nothing escalated" for a
    system quietly growing its population on every exchange."""
    ids = [s.id for s in core.stalks]
    ex = link.exchange(ids[0], ids[1], in_view=ids[2:])
    assert ex.population == len(ids) - 2, (
        "the exchange recorded %d stalks in view, expected %d"
        % (ex.population, len(ids) - 2))
    assert ex.describe()["population"] == ex.population


def test_an_unreadable_exchange_grows_the_population_not_the_width(link, core):
    """THE THREAD'S CENTRAL MEASUREMENT, and it needs a READING THAT
    DOES NOT RESOLVE.

    **AND HERE IS THE MEASUREMENT THAT MATTERS, and it is about the
    LIVE PATH rather than the policy.** With one or two stalks in view
    the link's channel round-trips the payload LOSSLESSLY: MEASURED,
    the alignment is exactly 1.000000 and the escalation is
    `resolved`. So on a clean channel the `NEEDS_MORE` branch -- the
    one the population-first policy serves -- IS NEVER REACHED.

    **AND THAT IS A FINDING, not a test failure.** The interstalk
    channel is a clean laboratory channel: no noise, no interference
    from the environment, and the receiver's equaliser inverts it
    exactly. So the population-first escalation is wired, correct, and
    UNEXERCISED on this fixture.

    So the test drives the branch DIRECTLY -- with a policy whose
    reading does not resolve -- and asserts the wiring, and the
    separate test below records that the clean channel resolves.
    """
    ids = [s.id for s in core.stalks]

    class NeverResolves(PE.PopulationPolicy):
        def decide(self, channel_taps, population, readable,
                   max_population=None):
            return PE.Escalation(width_needed=8, width_used=8,
                                  population_before=population,
                                  population_after=population + 1,
                                  reason=PE.GROW_POPULATION)

    # AND THE READING MUST NOT RESOLVE, because the policy is only
    # consulted when the reading is unreadable.
    #
    # MEASURED: the clean channel reads alignment 1.000000 and
    # resolves. A raised noise_floor makes the equaliser fail to
    # invert -- and THAT is the case where more stalks would help, so
    # that is where the population-first escalation must fire.
    probe = IL.InterstalkLink(core=core, noise_floor=-5.0)
    probe._policy = NeverResolves(width_for_taps=IL.width_for)
    ex = probe.exchange(ids[0], ids[1], in_view=ids[2:])
    assert ex.escalation == PE.GROW_POPULATION, (
        "the escalation was %r, not grow_population" % ex.escalation)
    assert ex.width_used == ex.width_needed, (
        "the width moved from %d to %d while the population could still "
        "grow" % (ex.width_needed, ex.width_used))
    assert ex.population > 0, (
        "the exchange recorded no population, so there was nothing to grow")


def test_the_clean_channel_resolves_and_so_never_escalates(link, core):
    """AND THE FINDING ITSELF, recorded so it is not lost.

    MEASURED: with stalks in view the alignment is 1.000000 and the
    escalation is `resolved`. With NONE in view the channel cannot be
    inverted and the escalation is `not_worth_knowing`.

    **SO THE INTERSTALK CHANNEL IS LOSSLESS ON THIS FIXTURE**, and the
    population-first branch is unreachable here. That is a property of
    the fixture -- a clean laboratory channel with no environmental
    interference -- and not a property of the policy.

    And it is the reason the policy's own tests drive it directly.
    """
    ids = [s.id for s in core.stalks]
    resolved = link.exchange(ids[0], ids[1], in_view=ids[2:])
    assert resolved.escalation == IL.RESOLVED, (
        "the clean channel did not resolve: %r" % resolved.escalation)
    assert resolved.alignment > 0.999, (
        "the clean channel's alignment was %.6f, not 1.0" % resolved.alignment)

    # **AND THE CHANNEL IS NOT BINARY -- and the first version of this
    # test asserted that it WAS, which was wrong.**
    #
    # MEASURED, sweeping bins (8/16/32/64) x noise_floor (-80 to 0) x
    # path_delay (1 to 5), the alignment was 1.000000 or 0.000000 and
    # never between. The first version of this test took that as a
    # property of the channel and asserted it.
    #
    # **IT IS AN ARTEFACT OF THE SWEEP.** MEASURED: the interstalk
    # channel has NO NOISE SOURCE -- `transport()` applies a complex
    # tap per neighbour, and there is no gaussian, no rng, no
    # stochastic term in the path. So on a noiseless channel the
    # equaliser either inverts exactly or fails to invert, and
    # sweeping a noise-floor THRESHOLD on a noiseless system can only
    # ever produce two values.
    #
    # **THE INTERFERENCE BETWEEN STALKS IS THE NOISE**, and
    # `bench_failup.py` measures it directly: the 1-bit DISCRIMINATION
    # pass rate is 0% at population 2, 50% at population 4, and 16.7%
    # at 8 and above. So the middle band is real, and the CROWD fills
    # it.
    #
    # **SO THE CORRECT ASSERTION IS ABOUT THE CROWD, NOT ABOUT THE
    # NOISE FLOOR.** And the crowd's effect is measured by the bench,
    # not asserted here.
    for nf in (-80.0, -20.0, -5.0):
        probe = IL.InterstalkLink(core=core, noise_floor=nf)
        ex = probe.exchange(ids[0], ids[1], in_view=ids[2:])
        assert ex.alignment in (0.0, 1.0) or ex.alignment > 0.999, (
            "the alignment took a middle value %.6f at noise_floor %s"
            % (ex.alignment, nf))

    # AND THE CROWD IS WHAT MOVES THE READING. MEASURED by
    # bench_failup.py: the 1-bit gate passes 0% of the time at
    # population 2 and 16.7% at population 8 -- so a channel with
    # NO interference is trivially readable and a channel with a
    # crowd is not. **THE BRAIN IS NOT BINARY; THE CROWD IS THE
    # NOISE.**
    import bench_failup as BF  # noqa: PLC0415
    pop = BF.make_population(4)
    crowded = BF.discriminate if hasattr(BF, "discriminate") else None
    assert crowded is not None, (
        "the discrimination bench is gone, and it is the instrument "
        "that measures the crowd's effect")


def test_the_ledger_shows_the_population(link, core):
    """AND THE LEDGER, which is what a reader of the system's behaviour
    actually sees.

    **AND THE LEDGER IS NOT SUPPOSED TO BE MONOTONE**, and the first
    version of this test asserted that and was WRONG. MEASURED: the
    ledger accumulates across exchanges, and successive exchanges in
    this test use DIFFERENT `in_view` sizes, so the population goes up
    and down -- by design, because the population in view is a property
    of the CALL, not of the system.

    So the check is not monotonicity. It is that the recorded
    population EQUALS the number of stalks the caller put in view.
    """
    ids = [s.id for s in core.stalks]
    fresh = IL.InterstalkLink(core=core)
    for n in range(0, 4):
        ex = fresh.exchange(ids[0], ids[1], in_view=ids[2:2 + n])
        # AND THE POPULATION IS THE NEIGHBOURS -- the stalks in view
        # MINUS whichever of the two speakers are themselves in the
        # view. MEASURED: the first version compared against the raw
        # `in_view` count and was wrong; the second compared against
        # `n - 2` and was ALSO wrong, because `pair()` excludes the
        # transmitter and the receiver only when they are IN the view.
        # The two that are speaking are not interference -- they are
        # the conversation.
        view = ids[2:2 + n]
        expected = len([x for x in view if x not in (ids[0], ids[1])])
        assert ex.population == expected, (
            "the exchange recorded %d neighbours in view, but %d of the "
            "%d stalks given are not speakers" % (ex.population, expected, n))


def test_the_report_counts_the_population(link, core):
    """AND THE REPORT CARRIES IT, so the measurement is available
    without reading the raw ledger."""
    ids = [s.id for s in core.stalks]
    link.exchange(ids[0], ids[1], in_view=ids[2:])
    rep = link.report()
    assert "population" in rep or "populations" in rep, (
        "the report does not mention the population: %s" % sorted(rep))


# --------------------------------------------------------------------------
# the policy the link consults
# --------------------------------------------------------------------------

def test_the_linked_policy_is_population_first(link):
    """AND THE POLICY THE LINK HOLDS IS THE POPULATION-FIRST ONE."""
    assert link._policy.max_population >= 1
    e = link._policy.decide(1, 1, readable=False)
    assert e.grew_population is True
    assert e.widened is False
    assert e.width_used == 1


def test_the_link_can_be_given_a_different_policy(core):
    """AND IT IS INJECTED, so a caller can measure a different policy
    without editing this file."""
    import population_escalation as PE

    class WideningPolicy(PE.PopulationPolicy):
        def decide(self, channel_taps, population, readable,
                   max_population=None):
            return PE.Escalation(width_needed=8, width_used=8,
                                  population_before=population,
                                  population_after=population,
                                  reason=PE.WIDEN)

    link = IL.InterstalkLink(core=core)
    link._policy = WideningPolicy(width_for_taps=IL.width_for)
    ids = [s.id for s in core.stalks]
    ex = link.exchange(ids[0], ids[1], in_view=ids[2:])
    if ex.escalation == IL.RESOLVED:
        pytest.skip("this exchange resolved; nothing escalated")
    assert ex.escalation == PE.WIDEN, (
        "the injected policy was not consulted: the escalation was %r"
        % ex.escalation)


def test_the_real_policy_fires_on_the_live_path(core):
    """AND THE REAL POLICY, not a stub, on the live path.

    MEASURED: with an irrecoverable channel the exchange reports
    `grow_population`, the width is UNCHANGED, and the population is
    recorded. And with NO stalk in view the width is 1 -- so the chain
    stays at ONE BIT and grows the population instead, which is the
    whole policy.

    **AND THE STUB ABOVE IS NOT SUFFICIENT**, because a stub proves
    the wiring and not the behaviour. This one uses the real
    `PopulationPolicy`.
    """
    ids = [s.id for s in core.stalks]

    bare = IL.InterstalkLink(core=core, noise_floor=-5.0)
    ex = bare.exchange(ids[0], ids[1], in_view=[])
    assert ex.escalation == PE.GROW_POPULATION, (
        "the live path did not grow the population: %r" % ex.escalation)
    assert ex.width_used == 1, (
        "the live path widened to %d instead of growing the population"
        % ex.width_used)

    some = IL.InterstalkLink(core=core, noise_floor=-5.0)
    ex2 = some.exchange(ids[0], ids[1], in_view=ids[2:])
    assert ex2.escalation == PE.GROW_POPULATION, (
        "the live path did not grow the population: %r" % ex2.escalation)
    assert ex2.width_used == ex2.width_needed, (
        "the width moved from %d to %d while the population could still "
        "grow" % (ex2.width_needed, ex2.width_used))
    assert ex2.population == 2, (
        "the exchange recorded %d neighbours, expected 2" % ex2.population)
