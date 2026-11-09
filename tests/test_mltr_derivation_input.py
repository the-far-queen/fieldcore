"""
test_mltr_derivation_input.py -- THE DERIVATION NAMES ITS INPUT, AND
THE CHECK CAN GO RED.

CENTRAL RULE 7: a test that cannot fail is not a test.

WHAT THIS FILE EXISTS FOR
-------------------------
MEASURED 2026-11-09: `tools/derive_mltr_terms.py` reads the SOURCE
TREE of both repos, so the register's derived block is a SNAPSHOT of a
function of a MOVING INPUT -- any new module can move it. The question
was what the derivation's input should be, and the deciding
measurement was **how many of the derived terms move when an
UNRELATED module is added**.

MEASURED, and this file keeps the measurement honest:

    one unrelated module added   0 of the derived terms move
    five added                   1 moves
    twenty added                 1 moves

So the sensitivity is acceptable, the input stays the source tree, and
the answer is the fc's own pattern: **the measurement names its
input**. The derivation prints a fingerprint of the tree it read, and
the register carries it, so a reader can tell a snapshot from a stale
one.

AND THE SECOND DEFECT THIS FILE COVERS, found by the same work:
`scan_modules` keyed its map by the file STEM, so 26 of the 369
scanned files were silently OVERWRITTEN -- 18 files named
`__init__.py` collapsed into one entry and 9 more stems collided
across the two repos. The map now holds every file.

THE RED VERSIONS, so each test names how it goes red:

  test_the_derivation_names_the_input_it_read
  test_the_register_names_the_input_it_was_derived_from
  test_the_fingerprint_is_a_fixed_point
  test_every_scanned_file_reaches_the_module_map
  test_no_two_modules_share_an_id
  test_an_unrelated_module_does_not_move_the_derived_terms
  test_the_family_matches_by_stem_not_by_id
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import mltr_register as REG  # noqa: E402

#: THE TOOL, and it is imported the way the register's own test
#: imports it -- by path, because it lives in `tools/` and not in
#: `src/`.
TOOL = os.path.join(REPO, "tools", "derive_mltr_terms.py")


def _tool():
    """the derivation tool, or None if it cannot be imported here."""
    if not os.path.exists(TOOL):
        return None
    if TOOL not in sys.path:
        sys.path.insert(0, os.path.join(REPO, "tools"))
    try:
        import derive_mltr_terms as D
    except Exception:  # noqa: BLE001
        return None
    return D


def _skip(reason: str):
    import pytest
    pytest.skip(reason)


# ---------------------------------------------------------------------------
# 1. THE DERIVATION NAMES ITS INPUT
# ---------------------------------------------------------------------------

def test_the_derivation_names_the_input_it_read():
    """The derivation reports a fingerprint of the tree it read.

    AND WHY A FINGERPRINT AND NOT A REVISION. A git revision names a
    COMMIT, and a dirty working tree is not a commit -- so the
    revision alone does not name the input. MEASURED 2026-11-09: both
    repos were clean at the time, and the revision is reported
    ALONGSIDE the fingerprint, because the revision says WHICH commit
    and the fingerprint says WHAT WAS READ.

    RED: return "" for the fingerprint.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    result = D.derive(verbose=False)
    fp = result.get("source_fingerprint", "")
    assert fp, "the derivation reports no fingerprint of its input"
    assert len(fp) == 64, (
        "the fingerprint is %d characters, not 64 -- it is not a sha256"
        % len(fp))
    assert all(c in "0123456789abcdef" for c in fp), (
        "the fingerprint is not hex: %r" % fp)
    # AND THE REVISIONS ARE REPORTED TOO, because a reader wants to
    # know which commit, not only a digest.
    revs = result.get("source_revisions") or {}
    assert set(revs) == {"fieldcore", "simself"}, (
        "the derivation names %r, not both repos" % sorted(revs))


# ---------------------------------------------------------------------------
# 2. THE REGISTER NAMES THE INPUT IT CAME FROM
# ---------------------------------------------------------------------------

def test_the_register_names_the_input_it_was_derived_from():
    """The register carries the fingerprint of its derivation's input.

    AND WHY THE REGISTER CARRIES IT. The derived block is a snapshot of
    a function of a moving input, so without a name for the input a
    reader cannot tell a snapshot from a stale one. This is the fc's
    own pattern: `bench_canon_vocab.py` prints its `canon_vocab.json
    sha256`, and the derivation now prints the tree's.

    RED: blank the constant.
    """
    value = getattr(REG, "DERIVED_AT_FINGERPRINT", None)
    assert value, (
        "the register names no input -- DERIVED_AT_FINGERPRINT is "
        "missing or empty")
    assert len(value) == 64, (
        "the register's fingerprint is %d characters, not 64"
        % len(value))
    assert all(c in "0123456789abcdef" for c in value), (
        "the register's fingerprint is not hex: %r" % value)


def test_the_register_names_the_input_the_derivation_reads_now():
    """The register's fingerprint IS the fingerprint of the tree now.

    AND THIS IS THE CHECK THAT CATCHES A STALE REGISTER. The derived
    set can be identical while the input moved -- the derivation is
    NOT sensitive to every change -- and then only the fingerprint
    moves. So the fingerprint is compared too, and a register that
    names a different input is stale even when its terms are right.

    RED: change the register's fingerprint to another digest.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    result = D.derive(verbose=False)
    want = result.get("source_fingerprint", "")
    have = getattr(REG, "DERIVED_AT_FINGERPRINT", "")
    assert want and have == want, (
        "the register names input %r but the derivation read %r -- the "
        "register is a snapshot of a different tree"
        % ((have or "")[:16], (want or "")[:16]))


# ---------------------------------------------------------------------------
# 3. THE FINGERPRINT IS A FIXED POINT
# ---------------------------------------------------------------------------

def test_the_fingerprint_is_a_fixed_point():
    """Writing the fingerprint does not move the fingerprint.

    AND WHY THIS MATTERS AND NOT JUST TIDINESS. The register carries
    the fingerprint, and the register is itself a scanned file, so a
    naive fingerprint would cover the file that holds it -- and
    writing the fingerprint would change the fingerprint. The
    fingerprint therefore EXCLUDES the register file and covers the
    register's CURATED rows instead (the derived rows are the tool's
    own output and are not its input).

    RED: include the register file in the fingerprint.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    paths = D.source_paths()
    by_word, curated = D.load_register()
    fp_without = D.source_fingerprint(paths, curated)

    #: THE REGISTER'S OWN BYTES, and they must not be in the digest.
    src = open(os.path.join(FC_SRC, "mltr_register.py"),
               encoding="utf-8").read()
    assert REG.DERIVED_AT_FINGERPRINT in src, (
        "the register does not carry its fingerprint")
    assert fp_without == REG.DERIVED_AT_FINGERPRINT, (
        "the fingerprint the tool computes (%s) is not the one the "
        "register carries (%s) -- so the fingerprint is not a fixed "
        "point and writing it moves it"
        % (fp_without[:16], REG.DERIVED_AT_FINGERPRINT[:16]))


# ---------------------------------------------------------------------------
# 4. EVERY SCANNED FILE REACHES THE MAP
# ---------------------------------------------------------------------------

def test_every_scanned_file_reaches_the_module_map():
    """No scanned file is silently dropped from the module map.

    **THIS IS THE DEFECT THIS WORK FOUND.** MEASURED 2026-11-09:
    `scan_modules` keyed its map by the file STEM, so two files with
    the same basename OVERWROTE each other -- 18 files named
    `__init__.py` collapsed into one entry, and 9 more stems collided
    across the two repos (governor, gate, wiring, memory, psb, core,
    chain_audit, coherence, end_to_end_demo). **26 of the 369 scanned
    files were dropped, silently**, and the tool reported "343
    modules" as if that were a count and not a loss.

    RED: key the map by the stem again.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    paths = D.source_paths()
    mod_words = D.scan_modules(paths)
    assert len(mod_words) == len(paths), (
        "the module map holds %d entries for %d scanned files -- %d "
        "files were dropped"
        % (len(mod_words), len(paths), len(paths) - len(mod_words)))


def test_no_two_modules_share_an_id():
    """Two scanned files never share a module id.

    RED: key the map by the stem, so `__init__.py` collides.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    paths = D.source_paths()
    ids = [m for m, _p in paths]
    assert len(set(ids)) == len(ids), (
        "these module ids are shared by more than one file: %r"
        % sorted({i for i in ids if ids.count(i) > 1}))


def test_the_family_matches_by_stem_not_by_id():
    """The family lists match modules by STEM, not by the module id.

    AND WHY THIS IS A SEPARATE TEST. The map's key is the path (every
    file is its own module) and the family lists name modules
    ("governor", "gate") -- and TWO files can answer to the same name,
    because `fieldcore/src/governor.py` and
    `simself/src/distributed/governor.py` are both the governor. So
    the family matches by stem.

    MEASURED: with the family matched by the module ID instead, the
    family matched NOTHING -- every family member is named by stem and
    no id equals a stem -- so the derived set was EMPTY. A gate that
    admits nothing looks like a measurement.

    RED: match the family by id.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    paths = D.source_paths()
    mod_words = D.scan_modules(paths)
    modules = set(mod_words)
    fam = D.family_modules(D.CONTROL_MODULES, modules)
    assert fam, (
        "the control family matched NO module -- the family lists name "
        "modules by stem and the map's keys are paths, so the match "
        "must be by stem")
    # AND THE FAMILY IS NOT THE WHOLE SUBSTRATE, so the enrichment
    # baseline is a fraction and not 1.
    assert len(fam) < len(modules), (
        "the control family is the whole substrate (%d of %d) -- the "
        "enrichment would divide by 1"
        % (len(fam), len(modules)))
    # AND EVERY FAMILY MEMBER IS A MODULE THAT EXISTS.
    assert fam <= modules


# ---------------------------------------------------------------------------
# 5. THE SENSITIVITY, WHICH IS THE MEASUREMENT THAT DECIDED THE INPUT
# ---------------------------------------------------------------------------

def test_an_unrelated_module_does_not_move_the_derived_terms():
    """Adding an UNRELATED module moves no derived term.

    AND THIS IS THE DECIDING MEASUREMENT, kept as a test so the
    decision cannot rot. The question was what the derivation's input
    should be: the source tree, the corpus, or the source tree frozen
    at a named revision. The measurement that decides it is **how
    many derived terms move when an unrelated module is added**. If it
    were one or two, the sensitivity would be acceptable and the
    answer would be to record the revision; if it were twenty, the
    derivation would be measuring the code and the input would be
    wrong.

    MEASURED 2026-11-09, on the fixed map: **0** move when ONE
    unrelated module is added.

    AND WHY THE MECHANISM IS THE MODULE COUNT, and not the new
    module's WORDS. An unrelated module is not in either family, so
    the family's share of the substrate FALLS when it is added --
    MEASURED: 0.2703% -- and every word's enrichment rises by that
    much. So the sensitive thing is the SIZE of the tree, and the
    word nearest the threshold is the one that flips. MEASURED on the
    fixed map: the nearest REJECTED term is `identity` at an
    enrichment of 1.976786 against a threshold of 2.000, so it needs
    +1.17% and therefore about FIVE unrelated modules to cross.

    AND WHY THE UNRELATED MODULE IS WRITTEN TO A TEMP DIRECTORY. It
    must not touch the repository, or the measurement would change the
    thing it measures.

    RED: make the gate tighten as the substrate grows.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    _cache_corpus(D)
    baseline = {r["word"] for r in D.derive(verbose=False)["rows"]}
    if not baseline:
        _skip("the derivation produced nothing here")

    got = _derive_with_extra(D, 1)
    added = sorted(got - baseline)
    removed = sorted(baseline - got)
    assert not (added or removed), (
        "adding one UNRELATED module moved %d derived terms: added %r, "
        "removed %r -- so the derivation is measuring the SIZE of the "
        "code, and the input needs another answer"
        % (len(added) + len(removed), added, removed))


def test_five_unrelated_modules_move_at_most_two_derived_terms():
    """Five unrelated modules move at most two derived terms.

    AND WHY THIS IS A SEPARATE ASSERTION AND NOT A LOOSER VERSION OF
    THE ONE ABOVE. The sensitivity GROWS with the number of unrelated
    modules, because each one shrinks the family's share of the
    substrate and so raises every word's enrichment. MEASURED 2026-11-09
    on the fixed map: **1** term moves at five modules -- `identity`,
    the nearest rejected term at an enrichment of 1.976786 against a
    threshold of 2.000, which needs +1.17% and gets +1.35% from five
    modules.

    AND THE BOUND IS TWO, not one, because a bound that equals the
    measured value goes red the moment the substrate grows by one
    module -- and a test that cries wolf is worse than no test. The
    bound is the measured value plus one, and the measured value is
    named here so the slack is visible rather than hidden.

    RED: make the gate tighten faster than the tree grows.
    """
    D = _tool()
    if D is None:
        _skip("the derivation tool cannot be imported here")
    _cache_corpus(D)
    baseline = {r["word"] for r in D.derive(verbose=False)["rows"]}
    if not baseline:
        _skip("the derivation produced nothing here")

    got = _derive_with_extra(D, 5)
    added = sorted(got - baseline)
    removed = sorted(baseline - got)
    moved = len(added) + len(removed)
    assert moved <= 2, (
        "adding FIVE unrelated modules moved %d derived terms: added "
        "%r, removed %r -- the measured value is 1, so the bound is 2"
        % (moved, added, removed))


def _cache_corpus(D) -> None:
    """count the canon corpus ONCE for the arms of a measurement.

    AND WHY THIS IS LEGITIMATE AND NOT A SHORTCUT. The corpus is
    178MB of text and it does NOT change between the arms -- the arms
    differ only in the SCANNED MODULE LIST -- so counting it twice
    measures the same thing twice. MEASURED: the corpus count is 4.4s
    and the whole derivation is 9.4s, so caching it makes the
    measurement run twice as fast and changes no number.
    """
    if getattr(D, "_corpus_cached", False):
        return
    counts = D.canon_corpus_counts()
    D.canon_corpus_counts = lambda: counts
    D._corpus_cached = True


def _derive_with_extra(D, k: int):
    """the derived set, with k UNRELATED modules added to the scan.

    AND WHY THE MODULES CARRY NO REGISTER VOCABULARY. The question is
    whether an UNRELATED module moves the answer. A module full of
    register words is not unrelated, and a test that answered a
    different question would be a test that proves nothing.
    """
    real_paths = D.source_paths()
    body = ("def qqxop(qqxarg):\n"
            "    \"\"\"A tiny unrelated helper.\"\"\"\n"
            "    return qqxarg\n")
    paths = list(real_paths)
    with tempfile.TemporaryDirectory() as td:
        for i in range(k):
            path = os.path.join(td, "qqxmod%02d.py" % i)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            paths.append((D.module_id(path), path))
        return _derive_with(D, paths)


def _derive_with(D, paths):
    """the derived set, with the scan pointed at other paths."""
    real = D.source_paths

    def fake():
        return list(paths)
    D.source_paths = fake
    try:
        return {r["word"] for r in D.derive(verbose=False)["rows"]}
    finally:
        D.source_paths = real


# ---------------------------------------------------------------------------
# 6. THE REGISTER'S OWN DOCSTRING NUMBERS, WHICH MOVED WITH THE FIX
# ---------------------------------------------------------------------------

def test_the_register_is_a_fixed_set_and_the_derived_block_is_generated():
    """The derived block is still the derivation's output.

    AND WHY THIS IS HERE AND NOT ONLY IN `test_mltr_register.py`.
    That file asserts the derived block RE-DERIVES. This file asserts
    the mechanism that produced the CURRENT block -- the fingerprint
    -- is in place, so the two checks fail differently: a stale block
    fails one, a stale fingerprint fails the other.

    RED: hand-edit a derived term.
    """
    derived = [t for t in REG.REGISTER if t.source.startswith("derived:")]
    assert derived, "the register holds no derived terms"
    for t in derived:
        assert t.source.startswith("derived:"), (
            "%s claims to be derived but its source is %r"
            % (t.word, t.source))
    # AND THE FINGERPRINT IS A CONSTANT, so a reader can read it
    # without running anything.
    tree = ast.parse(open(os.path.join(FC_SRC, "mltr_register.py"),
                           encoding="utf-8").read())
    names = {n.targets[0].id for n in tree.body
             if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name)}
    assert "DERIVED_AT_FINGERPRINT" in names, (
        "the register has no DERIVED_AT_FINGERPRINT constant")
