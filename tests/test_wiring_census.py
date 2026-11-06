"""
test_wiring_census.py -- the census must not drift, and it must fail.

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all
modules"*.

**WHAT THIS TEST IS.** The census (`tools/wiring_census.py`) says which
of the fc's modules are reached and which are not. It is the
instrument for "wire all modules", so two things must hold:

  1  the census's CLASSIFICATION of a known tree is right -- and that
     is checked against the fixture tree, whose every module's bin is
     written out by hand in the test. A census that is wrong on a tree
     whose answer is known cannot be trusted on a tree whose answer is
     not known.
  2  the census does not SILENTLY SKIP a repo. The first version
     surveyed only `fieldcore` -- 212 of 431 modules -- because a
     variable name was used for two different roots and the second
     assignment clobbered the first. Every run agreed with itself, so
     it looked like a settled measurement. This test is the thing that
     would have caught it: it asserts the census sees ALL FOUR REPOS.

**AND THE CHECKS CAN FAIL.** The mutation harness
(`tools/mutation_check_wiring_census.py`) breaks one rule of the census
at a time and shows the census changes. 5 of 5 caught.

Run:
    python -m pytest tests/test_wiring_census.py -q
    python tools/mutation_check_wiring_census.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import wiring_census as wc  # noqa: E402


FIXTURE_REPOS = REPO / "tests" / "fixtures" / "wiring_census" / "repos"

#: The ground truth for the fixture tree, written out by hand.
#:
#: AND WHY IT IS WRITTEN OUT AND NOT COMPUTED. If the expectation were
#: computed by the census itself, the test would compare the census
#: with the census and pass no matter what. The bins here are a
#: statement about python's import semantics, and they are what the
#: census must reproduce.
FIXTURE_BINS = {
    # an entry point: it has a __main__ guard
    "src/entry_static.py": "ENTRY",
    # reached by a static import from an entry point
    "src/cap_static.py": "WIRED",
    # an entry point that reaches a capability DYNAMICALLY
    "src/entry_dynamic.py": "ENTRY",
    # reached only by a dynamic import
    "src/cap_dynamic.py": "WIRED",
    # a bench: nothing imports it, and that is CORRECT
    "src/bench_probe.py": "ENTRY",
    # a capability nothing reaches
    "src/orphan_top.py": "ORPHAN",
    # a capability reached only by UNREACHABLE code
    "src/cap_island.py": "ISLAND",
    # a package whose init does `from . import x`
    "src/pkg/__init__.py": "ENTRY",
    # a module doing `from .result import ...` and `from .. import ...`
    "src/pkg/mod_rel.py": "WIRED",
    # the real result module, reached from inside its package
    "src/pkg/result.py": "WIRED",
    # reached from inside the package
    "src/pkg/cap_rel.py": "WIRED",
    # reached from inside a package, but ABOVE it
    "src/cap_top_level.py": "WIRED",
    # a DECOY with the same leaf name as pkg/result.py. Nothing
    # imports it, and a relative import that resolves to the wrong
    # place must not make it look reached.
    "src/other/result.py": "ORPHAN",
    # an empty package
    "src/other/__init__.py": "ORPHAN",
}


@pytest.fixture(scope="module")
def fixture_bins():
    mods = wc.census(repos=("fieldcore",), roots=("src",),
                     work_repos=str(FIXTURE_REPOS))
    return {m.rel: m.bin for m in mods}


def test_fixture_tree_bins_are_right(fixture_bins):
    """the census reproduces the hand-written ground truth."""
    wrong = []
    for path, want in sorted(FIXTURE_BINS.items()):
        got = fixture_bins.get(path, "(absent)")
        if got != want:
            wrong.append("%s: census says %s, truth says %s"
                         % (path, got, want))
    assert not wrong, ("the census disagrees with the ground truth:\n  "
                       + "\n  ".join(wrong))


def test_the_census_sees_every_module_of_the_fixture(fixture_bins):
    """no module is silently skipped."""
    missing = sorted(set(FIXTURE_BINS) - set(fixture_bins))
    assert not missing, ("the census lost these modules: %s" % missing)


def test_the_census_surveys_all_four_repos():
    """THE SILENT-SKIP CHECK, and the one that would have caught the
    clobbered root.

    MEASURED 2026-11-06: the census reported 212 modules in ONE repo
    and every run agreed with itself, so it read as a settled
    measurement. The cause was a name used for two different roots.
    """
    mods = wc.census()
    repos = {m.repo for m in mods}
    assert repos == set(wc.FC_REPOS), (
        "the census surveyed %s, expected %s -- one root is being "
        "clobbered" % (sorted(repos), sorted(wc.FC_REPOS)))


def test_the_census_finds_enough_modules_to_be_the_whole_fc():
    """a floor on the size of the survey.

    AND WHY A FLOOR AND NOT AN EXACT COUNT. The exact count moves
    every time a module is added, and a test that breaks on every
    commit is a test people disable. The floor catches the failure
    that actually happened -- a census that quietly surveys a
    fraction of the tree.
    """
    mods = wc.census()
    assert len(mods) >= 400, (
        "the census found %d modules, expected at least 400 -- it is "
        "surveying a fraction of the tree" % len(mods))


def test_the_orphan_bin_still_fires():
    """the census must still FIND orphans, and it finds some.

    AND WHY THIS MATTERS. If the census reported zero orphans, that
    would look like a clean system. It is not: the fc has real
    capabilities that nothing reaches, and the census is what makes
    them visible. A census that can only say "all clear" is not
    measuring anything.

    AND WHY THIS RUNS AGAINST THE FIXTURE AND NOT THE REAL TREE.
    MEASURED 2026-11-06: this assertion ran against the real tree and
    said the orphan count must be above zero. The real tree now has
    ZERO orphans, because `src/capability_wiring.py` was added and it
    reaches every capability the census had measured as unreached.

    That is the tree getting fixed, not the census getting weaker, and
    the distinction matters: a census whose orphan bin has stopped
    firing would ALSO report zero orphans, and the two are
    indistinguishable if the only evidence is the count. So the
    property is now asserted where it can be seen -- on the fixture
    tree, whose orphans are known by hand -- and the real tree's zero
    is asserted separately, as the result rather than as the
    instrument's health.
    """
    mods = wc.census(repos=("fieldcore",), roots=("src",),
                     work_repos=str(FIXTURE_REPOS))
    orphans = [m.rel for m in mods if m.bin == "ORPHAN"]
    assert orphans, (
        "the census found no orphans on the fixture tree -- the ORPHAN "
        "bin has stopped firing, and a census that can only say 'all "
        "clear' is not measuring anything")
    assert "src/orphan_top.py" in orphans, orphans
    assert "src/other/result.py" in orphans, orphans


def test_the_real_tree_has_no_orphans_left():
    """The fc is fully wired, and that is a RESULT, not a broken census.

    MEASURED 2026-11-06: the census measured 25 modules that nothing
    imported. `src/capability_wiring.py` now reaches every one of
    them, and the count is zero.

    The census rules were NOT changed to make this happen -- the
    mutation harness still proves the ORPHAN bin fires when it is
    broken (5 of 5 caught), and the fixture tree above still has its
    hand-written orphans.
    """
    s = wc.summarise(wc.census())
    assert s["orphan"] == 0, (
        "the census still reports %d orphans: %s"
        % (s["orphan"], s["orphans"]))
    assert s["wired"] > 0 and s["entry"] > 0


def test_a_package_init_is_reached_by_its_children():
    """the PACKAGE RULE.

    python executes a package's `__init__.py` before any of its
    children, so a package init is reached whenever a child is.
    MEASURED: without this rule the census reported 12 package inits
    as orphans -- including `simself/src/services/`.
    """
    mods = wc.census()
    pkgs = [m for m in mods if m.is_package_init]
    assert pkgs, "no package inits were found -- the scan is wrong"
    unreachable = [m.rel for m in pkgs if not m.reachable]
    # a package init with NO reachable child and no entry of its own
    # is genuinely unreached, and that is allowed. What is not allowed
    # is a package init whose children are all reached but which the
    # census calls unreachable.
    bad = []
    for m in pkgs:
        if m.reachable:
            continue
        children = [c for c in mods if c.package == m.dotted]
        if any(c.reachable for c in children):
            bad.append(m.rel)
    assert not bad, ("these package inits have reachable children but "
                      "read as unreachable: %s" % bad)
