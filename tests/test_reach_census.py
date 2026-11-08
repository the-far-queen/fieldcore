"""
test_reach_census.py -- the reach census, and its definition of reach.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*, and the
robot's pattern for each fc system -- the substrate it reaches, a
MEASUREMENT that it reaches it, a NAMED refusal, a selftest that passes,
and the census saying WIRED rather than ORPHAN.

**AND THIS IS THE SIBLING OF THE WIRING CENSUS, AND NOT ITS DUPLICATE.**
The wiring census asks *"does something import this?"*. The reach census
asks *"does this module reach anything of the FC's OWN?"*.

**AND THE DEFINITION OF REACH IS THREE WAYS, AND ALL THREE COUNT:**

    1  a python import of one of the fc's ledgers
    2  a SUBPROCESS PROBE -- the module RUNS the fc
    3  a PATH into the fc's own source

**AND THE THIRD MATTERS MOST, BECAUSE AN EXAM THAT IMPORTS ITS SUBJECT
CANNOT GRADE ITSELF.**
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import reach_census as RC  # noqa: E402


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return RC.measure_module(str(p), name[:-3], "x", set())


# ---------------------------------------------------------------------------
# 1. the three ways to reach
# ---------------------------------------------------------------------------

def test_a_ledger_import_reaches(tmp_path):
    r = _write(tmp_path, "uses_the_ledger.py",
               "from claim_register import ClaimRegister\n\n"
               "def main():\n    return 1\n")
    assert r is not None and r.reaches, "a ledger import did not reach"
    assert r.ledgers == ["claim_register"], r.ledgers
    assert r.bin == "REACHES"


def test_a_subprocess_probe_reaches(tmp_path):
    r = _write(tmp_path, "probes_it.py",
               "import subprocess\n\n"
               "def main():\n"
               "    return subprocess.run([\"python\", \"-c\", \"pass\"])\n")
    assert r is not None and r.probes, "the subprocess probe was missed"
    assert r.bin == "REACHES"


def test_a_path_into_the_fc_reaches(tmp_path):
    r = _write(tmp_path, "points_at_it.py",
               "def main():\n"
               "    return \"fieldcore/src/claim_register.py\"\n")
    assert r is not None and r.path_probe, "the path probe was missed"
    assert r.bin == "REACHES"


def test_a_substrate_import_reaches(tmp_path):
    r = _write(tmp_path, "uses_locus.py",
               "import locus\n\ndef main():\n    return 1\n")
    assert r is not None and r.substrates == ["locus"], r.substrates
    assert r.bin == "REACHES"


# ---------------------------------------------------------------------------
# 2. A MENTION IS NOT A REACH
# ---------------------------------------------------------------------------

def test_a_docstring_that_mentions_the_fc_is_not_a_reach(tmp_path):
    """**AND THE PROBES ARE MEASURED ON THE CODE AND NOT ON THE TEXT.**

    MEASURED 2026-11-07: the first version matched the path pattern
    against the WHOLE source, and a docstring that said "see
    src/claim_register.py" counted as a reach -- so 169 of 216 modules
    "reached" and the number was nonsense. **A MENTION IS NOT A REACH.**
    """
    r = _write(tmp_path, "mentions_it.py",
               '"""A tool. See src/claim_register.py for the register."""\n'
               "def main():\n    return 1\n")
    assert r is not None, "the module was not measured"
    assert not r.path_probe, "a docstring mention counted as a reach"
    assert not r.reaches, "a docstring mention counted as a reach"


def test_a_comment_that_mentions_the_fc_is_not_a_reach(tmp_path):
    r = _write(tmp_path, "comments_it.py",
               "# see fieldcore/src/claim_register.py\n"
               "def main():\n    return 1\n")
    assert r is not None and not r.path_probe, "a comment counted as a reach"


def test_the_code_still_counts_when_the_docstring_also_mentions_it(tmp_path):
    """**AND THE DOCSTRING IS NOT THE REACH -- THE CODE IS.**"""
    r = _write(tmp_path, "both.py",
               '"""See src/claim_register.py."""\n'
               "import subprocess\n\n"
               "def main():\n"
               "    return subprocess.run([\"python\", \"-c\", \"pass\"])\n")
    assert r is not None and r.probes, "the real probe was missed"


# ---------------------------------------------------------------------------
# 3. the three bins
# ---------------------------------------------------------------------------

def test_an_honest_standalone_is_its_own_bin(tmp_path):
    r = _write(tmp_path, "on_its_own.py",
               '"""A standalone instrument. It reaches nothing of the fc."""\n'
               "def main():\n    return 1\n")
    assert r is not None and not r.reaches, "it reached something"
    assert r.names_it, "the honest sentence was missed"
    assert r.bin == "STANDALONE"


def test_a_silent_one_is_the_finding(tmp_path):
    """**A MODULE THAT REACHES NOTHING AND DOES NOT SAY SO IS A QUESTION
    NOBODY ASKED.**"""
    r = _write(tmp_path, "silent.py", "def main():\n    return 1\n")
    assert r is not None and not r.reaches, "it reached something"
    assert not r.names_it, "it named itself"
    assert r.bin == "NAMES-IT"


def test_reaching_wins_over_saying(tmp_path):
    r = _write(tmp_path, "both_things.py",
               '"""It reaches nothing of the fc."""\n'
               "import claim_register\n\n"
               "def main():\n    return 1\n")
    assert r is not None
    assert r.bin == "REACHES", r.bin


# ---------------------------------------------------------------------------
# 4. the pattern's other three columns
# ---------------------------------------------------------------------------

def test_the_census_measures_the_patterns_other_columns(tmp_path):
    r = _write(tmp_path, "with_a_refusal.py",
               "def main():\n"
               "    raise ValueError('the refusal names its reason')\n")
    assert r is not None
    assert r.has_main, "the main was not seen"
    assert r.has_refusal, "the refusal was not seen"
    assert not r.has_selftest, "there is no selftest in it"


# ---------------------------------------------------------------------------
# 5. the census over the real fc
# ---------------------------------------------------------------------------

def test_the_census_over_the_real_fc():
    """**AND THE CENSUS RUNS OVER THE REAL FC**, and every module lands
    in exactly one bin."""
    result = RC.census()
    assert result["total"] > 200, result["total"]
    assert sum(result["bins"].values()) == result["total"], result["bins"]
    for r in result["rows"]:
        assert r.bin in ("REACHES", "SUBSTRATE", "STANDALONE",
                         "NAMES-IT"), r.bin


def test_the_sheaf_bridge_reaches_and_the_sheaf_loop_says_so():
    """**AND THE TWO MODULES I FIXED ARE IN THE RIGHT BINS.**

    **AND `sheaf_loop` IS A SUBSTRATE, NOT A STANDALONE.** MEASURED
    2026-11-07: the census measured reach in ONE direction -- "does
    this module reach the fc's own?" -- and never asked the other
    question. So a module the fc is BUILT ON and a module NOTHING
    TOUCHES landed in the same bin, and the bin's own name was wrong
    for half of its members.

    `sheaf_loop` says "this module REACHES THE FC THROUGH THE BRIDGE"
    -- the same claim in the other order -- and three of the fc's own
    modules import it. So it is a SUBSTRATE, and the bin says so.
    """
    result = RC.census()
    by = {(r.repo, r.module): r for r in result["rows"]}
    bridge = by.get(("fieldcore", "sheaf_bridge"))
    assert bridge is not None and bridge.bin == "REACHES", bridge
    loop = by.get(("fieldcore", "sheaf_loop"))
    assert loop is not None and loop.bin == "SUBSTRATE", loop.bin
    assert loop.is_reached, "the reverse reach was not measured"
    assert loop.names_the_reverse, "the honest sentence was not seen"
    walrus = by.get(("fieldcore", "walrus_memory"))
    assert walrus is not None and walrus.bin == "STANDALONE", walrus
    # AND NOTHING REACHES THE WALRUS, so STANDALONE IS RIGHT FOR IT.
    assert not walrus.is_reached, walrus.reached_by


def test_the_spine_is_a_substrate_and_says_so():
    """**AND THE SPINE IS A SUBSTRATE.** MEASURED 2026-11-07: three of
    the fc's own modules import it -- `evacuated`,
    `predicate_registry`, `sheaf_bridge` -- and the fc's GROUND asks it
    two questions. So it is what the fc is built on, and it says so."""
    result = RC.census()
    by = {(r.repo, r.module): r for r in result["rows"]}
    spine = by.get(("fieldcore", "coherence_spine"))
    assert spine is not None and spine.bin == "SUBSTRATE", spine.bin
    assert spine.is_reached, spine.reached_by
    assert spine.names_the_reverse, "the honest sentence was not seen"
    assert "fieldcore/sheaf_bridge" in spine.reached_by, spine.reached_by


# ---------------------------------------------------------------------------
# 6. the selftest
# ---------------------------------------------------------------------------

def test_the_selftest_passes():
    assert RC._selftest() == 0
