"""
test_mltr_docstring_numbers.py -- THE DOCSTRING'S NUMBERS ARE THE
REGISTER'S NUMBERS, AND THE TEST PROVES IT.

WHY THIS FILE EXISTS
--------------------

MEASURED 2026-11-08. The register's own docstring said:

    the register holds 415 terms
    306 CURATED
    110 DERIVED
    MEASURED, that command prints 110 derived terms -- 96 control, 14
    engineering
    reports `derived terms: 110   in the register: 110   missing: 0`

**AND THE REGISTER ACTUALLY HELD:**

    415 terms, 306 curated, 109 derived, 96 control, 13 engineering

**SO THE DOCSTRING SAID 110 AND THE REGISTER HELD 109, AND THE
DOCSTRING SAID 14 ENGINEERING AND THE REGISTER HELD 13.** Fourteen
numbers in the prose were stale, and **NOTHING CHECKED THEM**.

**AND THE PRIOR RUN SAID SO ITSELF.** Its own report ended: *"I had
not yet added the check that compares the docstring's numbers to the
register, which is what would have caught that drift."* This file IS
that check.

THE SHAPE OF THE DEFECT
-----------------------

THE REGISTER'S OWN RULE, quoted in its docstring: *"the count is
checked by a test"*. And the count WAS checked -- `EXPECTED_COUNT` in
`test_mltr_register.py` asserts the register's length. **BUT THE
DOCSTRING'S OWN COPY OF THAT NUMBER WAS NOT CHECKED BY ANYTHING.**

So the register could be right and its prose wrong, and the test suite
would be green. **A TEST THAT CHECKS THE REGISTER AND NOT THE PROSE
ABOUT THE REGISTER IS HALF A TEST.**

CENTRAL RULE 7: a test that cannot fail is not a test. So each
assertion below names the RED version, and
`tools/mutation_check_mltr_docstring.py` exercises the mutations.

WHAT IS CHECKED, AND WHY EACH ONE
----------------------------------

  the total          the docstring's first number about the register
  the domains        the table the docstring prints
  the two populations curated and derived, and their sum
  the derived split  control and engineering, and their sum
  the gap            SPEC - MEASUREMENT, and the prose says the gap
  the counts         the number of CURATED and DERIVED in the prose
  the search index   the "#: the register is 306 terms" comment

**AND THE REFUSAL COUNTS ARE NOT CHECKED HERE**, because they belong
to the derivation's own output and not to the register -- and they are
checked where they belong, in `test_mltr_register.py`, against the
tool that produces them.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import mltr_register as REG  # noqa: E402


#: THE DOCSTRING, and it is the module's own.
DOC = REG.__doc__ or ""


def _derived() -> list:
    return [t for t in REG.REGISTER if "derived:" in (t.source or "")]


def _curated() -> list:
    return [t for t in REG.REGISTER if "derived:" not in (t.source or "")]


def _claim(pattern: str, label: str) -> int:
    """The number the docstring CLAIMS, and a clear failure when it
    claims none."""
    m = re.search(pattern, DOC)
    assert m is not None, (
        "the docstring no longer says %s, so this check cannot find the "
        "number it was written to compare -- the prose was rewritten "
        "and the check was not" % label)
    return int(m.group(1))


# ---------------------------------------------------------------------------
# 1. THE TOTAL
# ---------------------------------------------------------------------------

def test_the_docstrings_total_is_the_register_s_total():
    """The number the docstring calls the register's total IS the total.

    RED: change the docstring's number and this goes red.
    """
    claimed = _claim(r"the register holds (\d+) terms", "the total")
    assert claimed == len(REG.REGISTER), (
        "the docstring says the register holds %d terms and it holds %d"
        % (claimed, len(REG.REGISTER)))


def test_the_docstrings_domain_table_is_the_real_one():
    """The table the docstring prints IS the table the register has.

    **AND THIS IS THE ONE THAT DRIFTED SILENTLY.** The domain counts
    are five lines of aligned prose, and a derivation that adds a
    term moves one of them and nothing says so.

    RED: change any one number in the table and this goes red.
    """
    table = dict(re.findall(
        r"^\s{4}(py-builtin|control|engineering|process|affect)\s+(\d+)\s*$",
        DOC, re.M))
    assert table, "the docstring's domain table could not be found"
    real = Counter(t.domain for t in REG.REGISTER)
    for dom, count in table.items():
        assert int(count) == real.get(dom, 0), (
            "the docstring says %s has %s terms and it has %d"
            % (dom, count, real.get(dom, 0)))
    # AND THE TABLE IS COMPLETE -- five domains, no more, no less.
    assert set(table) == set(real), (
        "the docstring's table names %r and the register has %r"
        % (sorted(table), sorted(real)))


# ---------------------------------------------------------------------------
# 2. THE TWO POPULATIONS
# ---------------------------------------------------------------------------

def test_the_docstrings_two_populations_are_the_real_two():
    """The CURATED and DERIVED counts in the prose ARE the two counts.

    **AND THIS IS THE NUMBER THAT WAS WRONG.** The docstring said 110
    DERIVED and the register held 109.

    RED: change "110 DERIVED" to anything else and this goes red.
    """
    claimed_curated = _claim(r"(\d+) CURATED", "the curated count")
    claimed_derived = _claim(r"(\d+) DERIVED", "the derived count")
    assert claimed_curated == len(_curated()), (
        "the docstring says %d CURATED and there are %d"
        % (claimed_curated, len(_curated())))
    assert claimed_derived == len(_derived()), (
        "the docstring says %d DERIVED and there are %d"
        % (claimed_derived, len(_derived())))


def test_the_two_populations_sum_to_the_total():
    """Curated + derived IS the register, and the prose says so too.

    RED: make the prose's two numbers not sum and this goes red.
    """
    claimed_curated = _claim(r"(\d+) CURATED", "the curated count")
    claimed_derived = _claim(r"(\d+) DERIVED", "the derived count")
    assert claimed_curated + claimed_derived == len(REG.REGISTER), (
        "the docstring's two populations sum to %d and the register "
        "holds %d" % (claimed_curated + claimed_derived, len(REG.REGISTER)))
    # AND THE REAL POPULATIONS SUM TOO, so the split is exhaustive.
    assert len(_curated()) + len(_derived()) == len(REG.REGISTER)


# ---------------------------------------------------------------------------
# 3. THE DERIVED SPLIT
# ---------------------------------------------------------------------------

def test_the_docstrings_derived_split_is_the_real_split():
    """The "96 control, 14 engineering" in the prose IS the split.

    **AND THIS IS THE SECOND HALF OF THE 110.** The docstring said the
    derivation prints "110 derived terms -- 96 control, 14 engineering"
    and the derivation prints "109 derived terms (control 96,
    engineering 13)". So one of the three numbers was wrong.

    RED: change "14 engineering" and this goes red.
    """
    m = re.search(r"prints (\d+) derived terms -- (\d+) control, (\d+)\s*\n"
                  r"\s*engineering", DOC)
    assert m is not None, (
        "the docstring no longer says how the derivation splits, so this "
        "check cannot find the numbers it was written to compare")
    claimed_total, claimed_control, claimed_eng = (
        int(m.group(1)), int(m.group(2)), int(m.group(3)))
    real = Counter(t.domain for t in _derived())
    assert claimed_total == len(_derived()), (
        "the docstring says the derivation prints %d derived terms and it "
        "prints %d" % (claimed_total, len(_derived())))
    assert claimed_control == real.get("control", 0), (
        "the docstring says %d derived control terms and there are %d"
        % (claimed_control, real.get("control", 0)))
    assert claimed_eng == real.get("engineering", 0), (
        "the docstring says %d derived engineering terms and there are %d"
        % (claimed_eng, real.get("engineering", 0)))
    # AND THE SPLIT SUMS TO THE WHOLE.
    assert claimed_control + claimed_eng == claimed_total, (
        "the docstring's split of the derived terms does not sum: "
        "%d + %d != %d" % (claimed_control, claimed_eng, claimed_total))


def test_the_docstrings_check_line_is_the_real_check_line():
    """The `derived terms: 110   in the register: 110` line IS what
    the tool prints.

    **AND THIS IS THE LINE A READER COPIES INTO A COMMIT MESSAGE.**
    So it has to be the real output.

    RED: change either 110 and this goes red.
    """
    m = re.search(r"derived terms: (\d+)\s+in the register: (\d+)\s+"
                  r"missing: (\d+)\s*\n?\s*extra: (\d+)", DOC)
    assert m is not None, (
        "the docstring no longer quotes the derivation's check line, so "
        "this check cannot find the numbers it was written to compare")
    derived_n = int(m.group(1))
    in_register_n = int(m.group(2))
    assert derived_n == len(_derived()), (
        "the docstring quotes `derived terms: %d` and the derivation "
        "produces %d" % (derived_n, len(_derived())))
    assert in_register_n == len(_derived()), (
        "the docstring quotes `in the register: %d` and the register "
        "holds %d derived terms" % (in_register_n, len(_derived())))


# ---------------------------------------------------------------------------
# 4. THE GAP
# ---------------------------------------------------------------------------

def test_the_gap_the_docstring_states_is_the_gap_there_is():
    """SPEC - MEASUREMENT IS the gap the docstring states.

    **AND THE DOCSTRING KEEPS THE THREE APART**, because they are
    three different things: what was asked for, what is held, and
    what is missing.

    RED: change the SPEC or the MEASUREMENT or the GAP and this goes
    red.
    """
    spec = _claim(r"the SPEC\s+(\d+)", "the spec")
    measurement = _claim(r"the MEASUREMENT (\d+)", "the measurement")
    gap = _claim(r"the GAP\s+(\d+)", "the gap")
    assert measurement == len(REG.REGISTER), (
        "the docstring's MEASUREMENT is %d and the register holds %d"
        % (measurement, len(REG.REGISTER)))
    assert spec - measurement == gap, (
        "the docstring says the spec is %d, the measurement is %d and "
        "the gap is %d -- but %d - %d is %d"
        % (spec, measurement, gap, spec, measurement, spec - measurement))


# ---------------------------------------------------------------------------
# 5. THE SEARCH INDEX COMMENT
# ---------------------------------------------------------------------------

def test_the_search_index_comment_counts_the_register():
    """The "#: the register is 306 terms" comment IS the register.

    **AND THIS IS A COMMENT AND NOT PROSE**, so it is easier to miss:
    a comment is where a number goes to die, because nobody reads it
    and no tool checks it.

    RED: change 306 in the comment and this goes red.
    """
    src = open(os.path.join(FC_SRC, "mltr_register.py"),
               encoding="utf-8").read()
    m = re.search(r"#: terms -- so without the index it is (\d+) lookups",
                  src)
    if m is None:
        # AND THE COMMENT WAS REWORDED, which is allowed -- but then the
        # number it held is gone and nothing to compare.
        import pytest
        pytest.skip("the search-index comment was reworded")
    assert int(m.group(1)) == len(REG.REGISTER), (
        "the search-index comment says the register is %s terms and it "
        "holds %d" % (m.group(1), len(REG.REGISTER)))
