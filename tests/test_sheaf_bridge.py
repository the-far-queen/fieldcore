"""
test_sheaf_bridge.py -- THE TWO SHEAFS, AND THE LINK BETWEEN THEM.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*.

**AND THE FC HAD THE OBSTRUCTION IN TWO FILES AND THE LINK BETWEEN THEM
IN NEITHER.** MEASURED 2026-11-07:

    coherence_spine.py   a SCALAR sheaf -- Sites joined by GluingMaps,
        with `globally_consistent()`, `coherence()`, `drift()` and a
        NAMED violation:
            'b->c: restricted 0.5 vs held 0.9, gap 0.4 > tolerance 0.01'

    sheaf_loop.py        a LINEAR sheaf -- the Cech complex over a
        two-open cover, with H^0, H^1 and a NAMED question:
            'stalks disagree on shared coordinate 0: -0.5598.
             Which value is authoritative?'

**AND BOTH DETECT THE SAME PHENOMENON, IN DIFFERENT ALGEBRAS.** The
scalar sheaf says "the seam breaks". The linear sheaf says "the
cocycle is non-zero". **AND NEITHER KNEW THE OTHER EXISTED.**

**AND THE FINDING THAT FORCED THE BRIDGE'S SHAPE:** `H^1 > 0` and "the
stalks disagree" are DIFFERENT CLAIMS. H^1 > 0 is a fact about the
COVER (the codimension); a non-zero COCYCLE is a fact about the DATA
(the stalks disagree). **AND THE LOOP WAS ASKING A QUESTION ABOUT A
ZERO DISAGREEMENT** -- it said "stalks disagree on shared coordinate 0:
+0.0000. Which value is authoritative?" while the stalks agreed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import sheaf_bridge as SB  # noqa: E402
import sheaf_loop as SL     # noqa: E402


# ---------------------------------------------------------------------------
# 1. the broken case: the two sheafs agree
# ---------------------------------------------------------------------------

def test_the_broken_case_agrees():
    b = SB.bridge(broken=True)
    assert not b.scalar_consistent, "the broken seam was not seen"
    assert b.violation is not None, "the violation was not named"
    assert "gap" in b.violation, b.violation
    assert b.cocycle_norm > 1e-12, "the stalks did not disagree"
    assert b.question, "the cocycle question was not asked"
    assert b.agree, "the two sheafs disagree about the broken case"
    assert b.refusal() is None


# ---------------------------------------------------------------------------
# 2. the coherent case: the two sheafs agree
# ---------------------------------------------------------------------------

def test_the_coherent_case_agrees():
    c = SB.bridge(broken=False)
    assert c.scalar_consistent, "the coherent sheaf was called broken"
    assert c.violation is None, "the coherent sheaf named a violation"
    assert c.scalar_coherence == 1.0, c.scalar_coherence
    assert c.cocycle_norm <= 1e-12, c.cocycle_norm
    assert c.agree, "the two sheafs disagree about the coherent case"


def test_the_agreement_is_not_vacuous():
    """**AND THE AGREEMENT IS NOT AN ARTEFACT OF TWO INSTRUMENTS THAT
    ALWAYS SAY NO.**"""
    loop = SB.linear_sheaf()
    out = loop.run_once(local_sections=SB.linear_sections(loop, agree=False))
    assert out["cocycle_norm"] > 1e-12, "the stalks never disagree"


# ---------------------------------------------------------------------------
# 3. the cover's obstruction is a DIFFERENT claim
# ---------------------------------------------------------------------------

def test_the_cover_obstruction_is_reported_separately():
    """**H^1 > 0 IS A FACT ABOUT THE COVER** -- and the bridge reports it
    without confusing it with the data's disagreement."""
    c = SB.bridge(broken=False)
    assert c.h1_dim >= 1, "the cover's obstruction is not reported"
    assert c.obstructed, "the cover's obstruction is not reported"
    assert c.cocycle_norm <= 1e-12, "the data were called obstructed"


# ---------------------------------------------------------------------------
# 4. a question about a zero disagreement is NOT asked
# ---------------------------------------------------------------------------

def test_no_question_about_a_zero_disagreement():
    """**AND THE STALKS AGREE. THE QUESTION WAS ABOUT A ZERO
    DISAGREEMENT, AND IT NAMED A DISAGREEMENT THAT WAS NOT THERE.**

    A question about nothing is worse than no question, because it looks
    like the loop did something.
    """
    loop = SB.linear_sheaf()
    out = loop.run_once(local_sections=SB.linear_sections(loop, agree=True))
    q = out.get("question") or {}
    assert q.get("question") is None, (
        "a question was asked about agreeing stalks: %r"
        % q.get("question"))


def test_a_question_is_still_asked_when_the_stalks_disagree():
    loop = SB.linear_sheaf()
    out = loop.run_once(local_sections=SB.linear_sections(loop, agree=False))
    q = out.get("question") or {}
    assert q.get("question"), "no question was asked about a real disagreement"
    assert "+0.0000" not in q["question"], (
        "the question named a zero disagreement: %r" % q["question"])


def test_the_empty_cocycle_is_still_handled():
    import numpy as np
    loop = SB.linear_sheaf()
    q = loop.ask(np.zeros(0), overlap=4)
    assert q["question"] is None


# ---------------------------------------------------------------------------
# 5. the refusal names both sheafs
# ---------------------------------------------------------------------------

def test_the_refusal_names_both_sheafs():
    bad = SB.Bridge(scalar_consistent=True, scalar_coherence=1.0,
                    scalar_drift=0.0, violation=None, h0_dim=3, h1_dim=0,
                    obstructed=False, cocycle_norm=0.0, question=None,
                    agree=False)
    r = bad.refusal()
    assert r is not None, "a disagreement did not refuse"
    assert "scalar sheaf" in r and "linear sheaf" in r, r


# ---------------------------------------------------------------------------
# 6. the selftest
# ---------------------------------------------------------------------------

def test_the_selftest_passes():
    assert SB._selftest() == 0
