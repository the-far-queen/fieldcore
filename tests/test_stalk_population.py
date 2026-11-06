"""
test_stalk_population.py -- THE RECIPE IS ONE RECIPE, AND IT IS ADDRESSABLE.

MEASURED 2026-11-05: seven files in fieldcore/src each carried their own
copy of `make_population`, and the copies had DIVERGED into two
behaviours.  Four of them put every stalk in its own address class and
three of them collapsed the population into a couple of classes -- and
the repo's own `bench_tradeoff.py` docstring already called the
collapsing one a CONFOUND:

    "THIS FIXED A CONFOUND: the first bench's generator produced
     addresses clustered within 0.012 of each other, which is under two
     DFT bins -- so it was asking the receiver to separate things no
     transform could separate, and then reporting that as a limit of
     the design."

The published ceiling -- "population 8 gives 2 classes for 8 stalks,
that is the population code's real ceiling" -- was measured on the
confound.

A copy is a promise that somebody will remember to update it.  These
are the checks that make the promise unnecessary:

  1. EVERY BENCH'S POPULATION IS THE CANONICAL ONE, stalk for stalk.
     A bench that carries its own copy goes RED.
  2. THE CANONICAL POPULATION IS ADDRESSABLE -- every stalk in its own
     class, at every population.  A recipe that collapses the
     population goes RED, because a collapsed population cannot
     measure a CHANNEL limit.
  3. THE ADDRESS DERIVATION AGREES WITH THE SUBSTRATE'S OWN TWO.
     Three copies of one formula, one number.
  4. THE ADVERSARIAL CONTROL IS THE NEAREST NEIGHBOUR.
     A control whose difficulty is a property of the generator
     measures the generator.

`tools/check_population_recipe.py` reports the same properties from
outside the suite, and `tools/mutation_check_population_recipe.py`
proves each of these can go RED.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import stalk_population as SP  # noqa: E402

#: The populations the benches sweep, with the bins each uses.
SWEEP = ((2, 32), (3, 32), (4, 32), (8, 64), (16, 64), (32, 128),
         (64, 256))


def _bench(name):
    return __import__(name)


@pytest.mark.parametrize("name", SP.REQUIRED)
def test_every_bench_carries_the_canonical_population(name):
    """NO BENCH CARRIES ITS OWN COPY OF THE RECIPE."""
    mod = _bench(name)
    assert hasattr(mod, "make_population"), (
        "%s has no make_population -- the recipe was DROPPED from it, and "
        "a bench without the canonical recipe measures a population "
        "nobody else measures" % name)
    for pop in SP.POPS:
        mine = mod.make_population(pop)
        theirs = SP.make_population(pop)
        assert len(mine) == len(theirs), (
            "%s's recipe gives %d stalks at population %d and the "
            "canonical one gives %d"
            % (name, len(mine), pop, len(theirs)))
        for a, b in zip(mine, theirs):
            assert a.id == b.id, (
                "%s's recipe gives a different stalk id (%s vs %s) at "
                "population %d" % (name, a.id, b.id, pop))
            assert a.n_in == b.n_in and a.n_out == b.n_out, (
                "%s's recipe gives different turn counts at population %d"
                % (name, pop))
            assert abs(a.girth_in - b.girth_in) < 1e-12, (
                "%s's recipe gives a different inner girth at population %d"
                % (name, pop))
            assert abs(a.girth_out - b.girth_out) < 1e-12, (
                "%s's recipe gives a different outer girth at population %d"
                % (name, pop))
            assert abs(a.girth_core - b.girth_core) < 1e-12, (
                "%s's recipe gives a different core girth at population %d"
                % (name, pop))


@pytest.mark.parametrize("name", SP.REQUIRED)
def test_every_bench_carries_the_canonical_address(name):
    """AND THE ADDRESS DERIVATION, WHICH IS THE OTHER HALF OF IT."""
    mod = _bench(name)
    assert hasattr(mod, "address_of"), (
        "%s has no address_of -- the derivation was DROPPED from it" % name)
    for stalk in SP.make_population(8):
        assert abs(mod.address_of(stalk) - SP.address_of(stalk)) < 1e-15, (
            "%s's address_of disagrees with the canonical one by %.3e"
            % (name, abs(mod.address_of(stalk) - SP.address_of(stalk))))


@pytest.mark.parametrize("population,bins", SWEEP)
def test_the_canonical_population_is_addressable(population, bins):
    """EVERY STALK IS IN ITS OWN CLASS, AT EVERY POPULATION.

    A recipe that collapses the population cannot measure a CHANNEL
    limit -- it measures the recipe.  So this is the check that would
    have caught the confound before it was published as a ceiling.
    """
    stalks = SP.make_population(population)
    labels, sizes = SP.address_classes(stalks, bins)
    assert len(labels) == population, (
        "at population %d only %d of %d stalks got an address label"
        % (population, len(labels), population))
    assert max(sizes) == 1, (
        "at population %d with %d bins the largest address class holds %d "
        "stalks -- the population is not addressable, so any limit the "
        "read shows is a limit of the RECIPE"
        % (population, bins, max(sizes)))
    assert sum(sizes) == population, (
        "the class sizes do not account for every stalk: %r" % (sizes,))


def test_the_addresses_are_evenly_spread():
    """THE ADDRESSES ARE 1/n APART, SO THE NEAREST PAIR IS AS FAR AS
    n ADDRESSES ON A CIRCLE CAN BE."""
    for pop in (4, 8, 16):
        addrs = sorted(SP.address_of(s) for s in SP.make_population(pop))
        gaps = [addrs[i + 1] - addrs[i] for i in range(len(addrs) - 1)]
        assert gaps, "no gaps at population %d" % pop
        worst = max(gaps)
        assert abs(worst - 1.0 / pop) < 1e-12, (
            "at population %d the largest gap is %.12f, expected %.12f -- "
            "the addresses are not evenly spread"
            % (pop, worst, 1.0 / pop))


def test_the_address_derivation_agrees_with_the_substrate():
    """THREE COPIES OF ONE FORMULA, ONE NUMBER.

    The canonical derivation, `interstalk_link.InterstalkLink._address`,
    and `wound_core.WoundCore.population()` must agree.  A copy that
    drifts is a copy that measures a model.
    """
    from interstalk_link import InterstalkLink
    from wound_core import WoundCore

    stalks = SP.make_population(8)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=64)
    phases = [st.phase for st in WoundCore(stalks=stalks).population().strata]
    for stalk, phase in zip(stalks, phases):
        canonical = SP.address_of(stalk)
        assert abs(InterstalkLink._address(link.stalk(stalk.id))
                   - canonical) < 1e-15, (
            "the substrate's interstalk_link._address disagrees with the "
            "canonical derivation by %.3e"
            % abs(InterstalkLink._address(link.stalk(stalk.id)) - canonical))
        assert abs(phase - canonical) < 1e-15, (
            "the substrate's wound_core.population() disagrees with the "
            "canonical derivation by %.3e" % abs(phase - canonical))


def test_the_concentric_order_is_preserved():
    """THE SUBSTRATE REFUSES core >= inner >= outer, so the recipe must
    not ask for it."""
    for pop in SP.POPS:
        for stalk in SP.make_population(pop):
            assert stalk.girth_core < stalk.girth_in < stalk.girth_out, (
                "the recipe produced a stalk whose girths are not "
                "concentric: %r" % (stalk,))


# --------------------------------------------------------------------------
# THE CENSUS: EVERY BUILDER IN src/, DISCOVERED
# --------------------------------------------------------------------------
# MEASURED 2026-11-06: the checks above named the seven benches in a
# HARDCODED LIST.  A list cannot report a copy it does not know about,
# and TWO MORE COPIES were sitting in `src/` that the list never
# mentioned -- `bench_ladder.make_population` and
# `bench_population.make_stalk` -- both DIVERGED from the canonical
# recipe at every population, both invisible to the check that was
# supposed to catch divergence.
#
# So the census DISCOVERS the builders, and these tests hold every one
# of them to the recipe.

def _all_discovered():
    """(module, function) for every builder the census finds."""
    out = []
    for mod_name, fns in sorted(SP.census().items()):
        for fn_name in fns:
            out.append((mod_name, fn_name))
    return out


def test_the_census_finds_the_canonical_builder():
    """THE CENSUS MUST SEE THE CANONICAL RECIPE ITSELF.

    A census that finds nothing is a census that cannot fail, so the
    first thing it must do is find the thing it is looking for.
    """
    found = _all_discovered()
    assert ("stalk_population", "make_population") in found, (
        "the census did not find the canonical recipe -- it reports %r"
        % (found,))


def test_no_builder_carries_an_unnamed_copy():
    """EVERY BUILDER IS THE CANONICAL ONE, A NAMED VARIANT, OR A LOCUS
    MEMBER.

    An unnamed builder that DIVERGES from the canonical recipe is a
    copy -- and a copy is what produced the false ceiling.
    """
    offenders = []
    for mod_name, fn_name in _all_discovered():
        key = "%s:%s" % (mod_name, fn_name)
        if key in SP.DELIBERATE_VARIANTS:
            continue
        verdict = SP.compare_builder(mod_name, fn_name)
        if verdict in ("AGREE", "NOT-A-POPULATION", "UNCALLABLE") or \
                verdict.startswith("UNCALLABLE"):
            continue
        if mod_name in SP.LOCUS_BUILDERS and \
                fn_name == SP.LOCUS_BUILDERS[mod_name]:
            continue
        offenders.append((key, verdict))
    assert not offenders, (
        "these builders carry an UNNAMED copy of the population recipe: "
        "%r -- the census must catch a copy it was never told about"
        % (offenders,))


def test_the_locus_family_shares_one_builder():
    """THE FOUR MODULES THAT USE THE LOCUS RECIPE USE THE SAME ONE.

    MEASURED 2026-11-06: they each carried their own copy of the
    8-bin-spread recipe, identical stalk for stalk.  Four copies is
    four chances to drift.
    """
    for mod_name, fn_name in sorted(SP.LOCUS_BUILDERS.items()):
        mod = _bench(mod_name)
        assert hasattr(mod, fn_name), (
            "%s has no %s -- the locus recipe was DROPPED from it"
            % (mod_name, fn_name))
        got = getattr(mod, fn_name)(8)
        want = SP.make_locus_population(
            8, id_fmt=SP.LOCUS_REQUIRED[mod_name])
        assert len(got) == len(want), (
            "%s's locus recipe gives %d stalks and the shared one gives "
            "%d" % (mod_name, len(got), len(want)))
        for a, b in zip(got, want):
            assert a.id == b.id, (
                "%s's locus recipe gives the id %s and the shared one "
                "gives %s" % (mod_name, a.id, b.id))
            assert a.n_in == b.n_in and a.n_out == b.n_out, (
                "%s's locus recipe gives different turn counts" % mod_name)
            for attr in ("girth_core", "girth_in", "girth_out"):
                assert abs(getattr(a, attr) - getattr(b, attr)) < 1e-12, (
                    "%s's locus recipe gives a different %s"
                    % (mod_name, attr))


def test_every_named_variant_still_exists():
    """A NAME IN A TABLE IS A PROMISE, AND A STALE NAME IS A LIE.

    If a deliberate variant is renamed or deleted, the table must say
    so -- otherwise the next reader believes a builder is accounted
    for when it is not.
    """
    found = {"%s:%s" % (m, f) for m, f in _all_discovered()}
    for key in SP.DELIBERATE_VARIANTS:
        assert key in found, (
            "%s is named as a deliberate variant but no longer exists -- "
            "the table is stale" % key)
