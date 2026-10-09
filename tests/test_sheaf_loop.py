"""Tests for the sheaf control loop.

Source: deepseek8 part 120.

THE STRUCTURAL FINDING, which is the reason this suite exists as it does:

    for a two-open cover, rank(d^0) = rank([r_0 | -r_1]) <= overlap

always, so dim H^1 = overlap - rank(d^0) is STRUCTURALLY ZERO. Verified
over 3000 random covers with max H^1 = 0. The corpus's loop cannot reach
its own step 5 ("if H^1 != 0, generate questions") with two stalks of full
rank. Obstruction requires the stalk spaces to have codimension inside
the intersection.

`test_two_open_covers_structurally_never_obstruct` asserts this, so the
claim stays falsifiable and so nobody "fixes" the geometry by accident.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheaf_loop import (  # noqa: E402
    SheafControlLoop, compatible_sections, h1_from_scratch,
)


# --------------------------------------------------------------------- the cover


def test_cover_shapes_are_right():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=1)
    assert len(restr) == 2
    assert restr[0].shape == (4, 8)
    assert restr[1].shape == (4, 8)


def test_two_open_covers_structurally_never_obstruct():
    """The finding. Exhaustive enough to be a proof in practice: rank of
    [r_0 | -r_1] cannot exceed the overlap dimension, so H^1 cannot be
    positive for a cover whose stalks both span the whole overlap.
    """
    rng = np.random.default_rng(0)
    max_h1 = 0
    for _ in range(400):
        overlap = int(rng.integers(1, 9))
        d1 = int(rng.integers(overlap, overlap + 6))
        d2 = int(rng.integers(overlap, overlap + 6))
        a = rng.normal(size=(overlap, d1))
        b = rng.normal(size=(overlap, d2))
        rank = int(np.linalg.matrix_rank(np.hstack([a, -b])))
        max_h1 = max(max_h1, overlap - rank)
    assert max_h1 == 0


def test_codimension_makes_obstruction_possible():
    """The construction that gives the loop something to detect."""
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=1)
    sections = compatible_sections(restr, 8, seed=1)
    res = L.glue(sections, restr)
    assert res["h1_dim"] >= 1
    assert res["obstructed"] is True


def test_codim_zero_reproduces_the_unreachable_geometry():
    """The corpus geometry exactly, and it cannot obstruct -- which is the
    defect the codim parameter exists to work around.
    """
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=0)
    sections = compatible_sections(restr, 8, seed=1)
    assert L.glue(sections, restr)["h1_dim"] == 0


# --------------------------------------------------------------------- agreement


def test_loop_and_independent_checker_agree():
    rng = np.random.default_rng(1)
    for codim in (1, 2, 3):
        L = SheafControlLoop(n_stalks=2, dim=9, dim_intersection=5)
        restr, _ = L.build_cover(codim=codim)
        sections = compatible_sections(restr, 9, seed=codim)
        mine = L.glue(sections, restr)
        theirs = h1_from_scratch(restr, sections)
        assert mine["h0_dim"] == theirs["h0_dim"], codim
        assert mine["h1_dim"] == theirs["h1_dim"], codim


def test_h1_is_a_property_of_the_cover_not_the_data():
    """H^0 and H^1 must not change when only the sections change. The
    first version took the rank of the image difference, which made them
    data-dependent, and it disagreed with the checker by the full overlap.
    """
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=1)
    rng = np.random.default_rng(2)
    dims = set()
    for _ in range(12):
        res = L.glue([rng.normal(size=8), rng.normal(size=8)], restr)
        dims.add((res["h0_dim"], res["h1_dim"]))
    assert len(dims) == 1, dims


def test_h0_counts_global_sections():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=0)
    res = L.glue(compatible_sections(restr, 8, seed=3), restr)
    # C^0 has dimension 8+8=16, d^0 has rank = overlap
    assert res["h0_dim"] == 16 - restr[0].shape[0]
    assert res["glues"] is True


# --------------------------------------------------------------------- asking


def test_obstruction_produces_a_question_naming_a_coordinate():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    out = L.run_once(seed=4, codim=1)
    assert out["obstructed"] is True
    q = out["question"]
    assert q["question"]
    assert 0 <= q["direction_index"] < 4
    assert "disagree" in q["question"]


def test_the_question_names_the_largest_disagreement():
    """The direction matters; the norm alone would only say something is
    wrong.
    """
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    cocycle = np.array([0.1, -0.2, 3.0, -0.05])
    q = L.ask(cocycle, overlap=4)
    assert q["direction_index"] == 2
    assert "2" in q["question"]


def test_no_obstruction_means_no_question():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    out = L.run_once(seed=5, codim=0)
    assert out["obstructed"] is False
    assert "question" not in out or out.get("question") is None


def test_questions_are_remembered():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    L.run_once(seed=6, codim=1)
    L.run_once(seed=7, codim=1)
    assert len(L.questions_asked) == 2


# --------------------------------------------------------------------- resolving


def test_resolving_an_obstruction_removes_it():
    """The loop's purpose: an obstruction becomes an answer, and after the
    answer there is no obstruction left.
    """
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    out = L.run_once(seed=8, codim=1)
    assert out["obstructed"] is True
    idx = out["question"]["direction_index"]
    fixed = L.resolve(idx, 0.5)
    restr, _ = L.build_cover(codim=0)
    after = L.glue(fixed, restr)
    assert after["obstructed"] is False
    assert after["glues"] is True


def test_resolve_returns_full_width_sections():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    sections = L.resolve(1, 0.25)
    assert len(sections) == 2
    assert all(s.shape == (8,) for s in sections)


# --------------------------------------------------------------------- robustness


def test_wrong_width_sections_are_refused():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=1)
    with pytest.raises(ValueError):
        L.glue([np.zeros(4), np.zeros(8)], restr)


def test_history_records_each_pass():
    L = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    restr, _ = L.build_cover(codim=1)
    for _ in range(5):
        L.glue(compatible_sections(restr, 8, seed=1), restr)
    assert len(L.history) == 5
    assert all("h1_dim" in h for h in L.history)


def test_empty_cocycle_has_no_question():
    L = SheafControlLoop(n_stalks=2, dim=8)
    assert L.ask(np.zeros(0), overlap=4)["question"] is None


def test_a_larger_overlap_gives_a_larger_obstruction():
    L4 = SheafControlLoop(n_stalks=2, dim=8, dim_intersection=4)
    L6 = SheafControlLoop(n_stalks=2, dim=12, dim_intersection=6)
    r4 = L4.build_cover(codim=1)[0]
    r6 = L6.build_cover(codim=1)[0]
    h1_4 = L4.glue(compatible_sections(r4, 8, seed=1), r4)["h1_dim"]
    h1_6 = L6.glue(compatible_sections(r6, 12, seed=1), r6)["h1_dim"]
    assert h1_4 == 1 and h1_6 == 1      # exactly the codimension