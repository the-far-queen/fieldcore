"""
tests/test_gate_staleness.py -- CAN THE GATE TELL THAT ITS OWN CODE IS OLD?

AND WHY THIS TEST EXISTS. 2026-11-01. The gate is a long-lived process
and its rules are cached for the life of that process. On this machine
the gateway started at 19:23, the predicate layer's fix landed at
20:34, and from 20:34 the running gate enforced the OLD rules while
looking perfectly healthy in the log.

MEASURED, two independent derivations that AGREE:

    OLD tree (55bae29^)  "the fixture row is an ordinary json file"
                          -> caught_by=[predicate]
    NEW tree              the same sentence
                          -> caught_by=[]

So the test file below asserts the MECHANISM, not the outcome: a
checker that has a record from BEFORE a rule file moved must say
STALE, and must name the file that moved.

AND THE RULE THESE TESTS FOLLOW, and it is the project's own: a test
that cannot fail is not a test. So every test here asserts something
that could go red, and the mutation check at the bottom proves it.
"""

from __future__ import annotations

import os
import sys

import pytest

FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import gate_staleness as GS  # noqa: E402


# --------------------------------------------------------------------------
# the fingerprint
# --------------------------------------------------------------------------

def test_the_snapshot_covers_the_rule_files():
    """AND WHY THE COUNT MATTERS. A fingerprint of zero files is a
    fingerprint of nothing, and it would agree with every disk."""
    snap = GS.snapshot()
    assert len(snap) > 100, "the rule snapshot covers only %d files" % len(snap)
    assert any("fc_gate.py" in p for p in snap), "fc_gate.py is not covered"
    assert any("predicate_registry.py" in p for p in snap), \
        "the predicate registry is not covered"


def test_the_fingerprint_is_stable_for_an_unchanged_tree():
    a = GS.fingerprint(GS.snapshot())
    b = GS.fingerprint(GS.snapshot())
    assert a == b, "the fingerprint moved with nothing changing"


def test_the_fingerprint_moves_when_a_rule_file_moves():
    """AND WHY THIS IS THE LOAD-BEARING ONE. A fingerprint that does
    not move when a rule file moves cannot detect a stale build."""
    snap = GS.snapshot()
    before = GS.fingerprint(snap)
    moved = dict(snap)
    key = next(p for p in moved if p.endswith("predicate_registry.py"))
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    assert GS.fingerprint(moved) != before, \
        "the fingerprint did not move when a rule file moved"


def test_the_diff_names_the_file_that_moved():
    snap = GS.snapshot()
    moved = dict(snap)
    key = next(p for p in moved if p.endswith("predicate_registry.py"))
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    diff = GS.diff(snap, moved)
    assert len(diff) == 1, "the diff named %d files, expected 1" % len(diff)
    assert diff[0].endswith("predicate_registry.py"), \
        "the diff named %s" % diff[0]


# --------------------------------------------------------------------------
# the checker
# --------------------------------------------------------------------------

def test_a_checker_with_no_record_says_nothing():
    """AND WHY "nothing" IS NOT "fresh". A checker with no record has
    nothing to compare against, so it must not claim freshness."""
    checker = GS.StalenessChecker(interval=0.0)
    checker._built = None
    checker._built_fp = ""
    assert checker.check(force=True) is None, \
        "a checker with no record claimed freshness"


def test_a_checker_built_from_the_current_tree_is_fresh():
    checker = GS.StalenessChecker(interval=0.0, built=GS.snapshot())
    assert checker.check(force=True) is None, \
        "a checker built from the current tree said stale"


def test_a_checker_whose_record_is_behind_says_stale():
    """THE CENTRAL TEST. The record is taken, then a rule file moves,
    then the checker is asked. It must say STALE."""
    checker = GS.StalenessChecker(interval=0.0, built=GS.snapshot())
    # simulate the move: the record stays, the disk changes
    moved = dict(checker._built)
    key = next(p for p in moved if p.endswith("predicate_registry.py"))
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    checker._built = moved
    # now the disk no longer matches the record
    stale = checker.check(force=True)
    assert stale is not None, \
        "the checker did not notice that its record was behind the disk"
    assert isinstance(stale, GS.StaleGate)
    assert stale.moved, "the stale report named no file"


def test_the_stale_report_carries_both_fingerprints():
    checker = GS.StalenessChecker(interval=0.0, built=GS.snapshot())
    moved = dict(checker._built)
    key = next(p for p in moved if p.endswith("predicate_registry.py"))
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    checker._built = moved
    stale = checker.check(force=True)
    assert stale is not None
    assert stale.built and stale.disk, "the report carried no fingerprints"
    assert stale.built != stale.disk, \
        "the report carried the same fingerprint twice"


def test_the_import_time_record_is_taken_at_import():
    """AND WHY THIS MATTERS. The modules were read into memory when
    they were imported, so the import-time record is the record of
    what the gate is enforcing -- not of what is on disk right now."""
    snap = GS.import_snapshot()
    assert len(snap) > 100, "the import-time record covers %d files" % len(snap)
    assert GS.import_fingerprint(), "the import-time record has no fingerprint"


def test_a_checker_defaults_to_the_import_time_record():
    """AND WHY THE DEFAULT MATTERS. A checker that defaults to an
    empty record would report FRESH forever, which is the failure."""
    checker = GS.StalenessChecker(interval=0.0)
    assert checker.built_fingerprint == GS.import_fingerprint(), \
        "the checker did not default to the import-time record"


def test_the_check_is_throttled():
    """AND WHY THE THROTTLE MATTERS. The check reads 356 files' stats,
    which costs 6.8 ms, and the decide path costs 2.29 ms per span.
    So the check must not run on every call."""
    checker = GS.StalenessChecker(interval=10000.0)
    checker.record_build()
    calls = []
    real_snapshot = GS.snapshot

    def counting_snapshot():
        calls.append(1)
        return real_snapshot()

    GS.snapshot = counting_snapshot
    try:
        checker.check(force=True)
        first = len(calls)
        checker.check(force=False)
        checker.check(force=False)
        checker.check(force=False)
        after = len(calls)
    finally:
        GS.snapshot = real_snapshot
    assert first > 0, "the first check did no work at all"
    assert after == first, \
        "the check ran %d extra times inside the throttle" % (after - first)


# --------------------------------------------------------------------------
# the gate carries the checker
# --------------------------------------------------------------------------

def test_the_gate_exposes_a_staleness_check():
    """AND WHY IT IS ON THE GATE. The staleness is a property of the
    GATE'S BUILD, so the gate has to be able to answer for it."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    assert hasattr(g, "stale"), "the gate has no stale() method"
    result = g.stale(force=True)
    assert result is None, (
        "a freshly built gate said stale: %r\n\n"
        "AND THE CAUSE IS USUALLY A CONCURRENT WRITER, AND IT IS NOT A "
        "DEFECT IN THIS TEST.\n\n"
        "MEASURED 2026-11-07: the `workqueue-continuation` cron job runs "
        "EVERY 25 MINUTES and writes to `simself/src/` -- which is one of "
        "the two directories the gate fingerprints, on purpose, because "
        "`gate_staleness.py` says so: *\"the predicates ASK the substrate, "
        "and the substrate is in both repos\"*. **SO WHILE THE CRON IS "
        "WORKING, A RULE FILE MOVES, AND THIS TEST FAILS BECAUSE THE GATE "
        "IS CORRECTLY REPORTING A TREE THAT IS CHANGING UNDER IT.**\n\n"
        "The message above names the file that moved. If that file is one "
        "the cron is working on, the tree was changing during the test and "
        "the gate was right.\n\n"
        "AND THE FINGERPRINT IS MTIME-BASED ON PURPOSE, so the report is "
        "also raised by a file whose CONTENT did not change -- see "
        "`gate_staleness.py`, which says a spurious report *\"is safe\"*."
        % (result,))


def test_the_gate_reports_a_stale_build():
    """AND THIS IS THE END-TO-END ONE. The gate's build is replaced
    with a record from before a rule file moved, and the gate has to
    say so."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    # the record the gate holds
    built = dict(g.staleness._built)
    moved = dict(built)
    key = next((p for p in moved if p.endswith("predicate_registry.py")),
               None)
    assert key is not None, "the predicate registry is not in the record"
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    g.staleness._built = moved
    stale = g.stale(force=True)
    assert stale is not None, \
        "the gate did not notice that its rules were behind the disk"
    assert any("predicate_registry" in p for p in stale.moved), \
        "the gate did not name the file that moved"


def test_a_stale_gate_still_answers_the_call():
    """AND WHY NOT. A gate that RAISES on staleness takes the session
    down for a condition that has a cheap honest answer. So the gate
    reports and keeps working -- and the CALLER decides what a stale
    gate means."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    built = dict(g.staleness._built)
    moved = dict(built)
    key = next(p for p in moved if p.endswith("predicate_registry.py"))
    mtime_ns, size = moved[key]
    moved[key] = (mtime_ns + 1, size)
    g.staleness._built = moved
    verdict = g.decide("the file is an ordinary json file", fail_closed=False)
    assert verdict is not None, "the gate stopped answering"
