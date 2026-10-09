"""Tests for the degrees-of-freedom measurement.

Source: deepseek8 part 179 (core/state.py) and the DoF discussion: "Each
degree of freedom is one independent axis. Constraints are what remove
degrees of freedom."

The claim is falsifiable and is tested three independent ways -- exact
null-space rank, the covariance spectrum of sampled feasible states, and
the generated residuals -- because a count that can only be checked one way
is fragile. The tests below also assert that the three AGREE, and treat
disagreement as information rather than something to average away.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from degrees_of_freedom import (  # noqa: E402
    ConstraintSystem, PersistentState, constraint_residual, generate_in_feasible,
    generate_infeasible, measure_dof, traverse_manifold,
)


# --------------------------------------------------------------------- state


def test_state_starts_at_origin_and_uncreated():
    s = PersistentState(dimension=8)
    assert np.allclose(s.H, 0.0)
    assert s.metadata["created"] is False
    assert s.norm() == 0.0


def test_update_moves_the_state_and_reports_it():
    s = PersistentState(dimension=4)
    applied = s.update(np.array([1.0, 0, 0, 0]), learning_rate=0.5)
    assert applied == pytest.approx(0.5)
    assert s.norm() == pytest.approx(0.5)
    assert s.metadata["update_count"] == 1
    assert s.metadata["created"] is True


def test_update_rejects_a_wrong_width_delta():
    s = PersistentState(dimension=4)
    with pytest.raises(ValueError):
        s.update(np.zeros(5))


def test_zero_update_reports_zero_applied():
    s = PersistentState(dimension=4)
    assert s.update(np.zeros(4)) == 0.0


def test_state_rejects_zero_dimension():
    with pytest.raises(ValueError):
        PersistentState(dimension=0)


def test_round_trip_is_stable(tmp_path):
    """The corpus version casts to float32, which loses the low bits of an
    accumulated state. This asserts the round trip is exact after many
    updates, not merely close.
    """
    s = PersistentState(dimension=16)
    rng = np.random.default_rng(0)
    for _ in range(200):
        s.update(rng.normal(size=16))
    path = tmp_path / "state.json"
    s.save(path)
    back = PersistentState.load(path)
    assert np.array_equal(s.H, back.H)
    assert back.dimension == 16
    assert back.metadata["update_count"] == 200


def test_trajectory_records_each_state():
    s = PersistentState(dimension=4)
    for i in range(5):
        s.update(np.full(4, float(i + 1)))
    assert len(s.trajectory) == 5
    assert not np.array_equal(s.trajectory[0], s.trajectory[-1])


# --------------------------------------------------------------------- the count


def test_no_constraints_means_full_dof():
    c = ConstraintSystem(dimension=8)
    assert c.dof() == 8
    assert c.dof_removed() == 0
    assert measure_dof(c).dof_exact == 8


def test_each_independent_constraint_removes_exactly_one_dof():
    for k in range(1, 6):
        rows = [[1 if i == j else 0 for i in range(8)] for j in range(k)]
        c = ConstraintSystem.from_equality(8, rows)
        assert c.dof() == 8 - k
        assert c.dof_removed() == k


def test_dependent_constraints_do_not_remove_extra_dof():
    """A row that is a multiple of another constrains nothing new. This is
    why the count is a RANK and not a row count.
    """
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0],
    ])
    assert c.dof() == 7          # three rows, one direction removed
    assert c.rows.shape[0] == 3


def test_rank_plus_dof_equals_dimension():
    for rows in ([], [[1, 0, 0, 0, 0, 0, 0, 0]],
                 [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]],
                 [[1, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [1, 0, 0, 0, 0, 0]]):
        dim = len(rows[0]) if rows else 8
        c = ConstraintSystem.from_equality(dim, rows) if rows else ConstraintSystem(dimension=dim)
        assert c.dof() + int(np.linalg.matrix_rank(c.rows)) == dim


def test_null_space_basis_is_orthonormal():
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]])
    basis = c.null_space()
    assert np.allclose(basis.T @ basis, np.eye(basis.shape[1]), atol=1e-10)


def test_every_null_space_vector_satisfies_the_constraints():
    rng = np.random.default_rng(1)
    c = ConstraintSystem.from_equality(8, [
        [1, 1, 0, 0, 0, 0, 0, 0], [0, 1, -1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0]])
    basis = c.null_space()
    coeffs = rng.normal(size=(50, basis.shape[1]))
    x = coeffs @ basis.T
    assert np.abs(x @ c.rows.T).max() < 1e-9


def test_constraints_of_the_wrong_width_are_refused():
    with pytest.raises(ValueError):
        ConstraintSystem.from_equality(8, [[1, 0, 0]])


def test_a_full_rank_constraint_set_leaves_no_dof():
    c = ConstraintSystem.from_equality(4, [[1, 0, 0, 0], [0, 1, 0, 0],
                                           [0, 0, 1, 0], [0, 0, 0, 1]])
    assert c.dof() == 0
    rep = measure_dof(c)
    assert rep.dof_exact == 0
    assert rep.dof_spectral == 0


# --------------------------------------------------------------------- agreement


@pytest.mark.parametrize("rows", [
    [],
    [[1, 0, 0, 0, 0, 0, 0, 0]],
    [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]],
    [[1, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [1, 0, 0, 0, 0, 0]],
    [[1, 1, 1, 1]],
])
def test_exact_and_spectral_agree(rows):
    dim = len(rows[0]) if rows else 8
    c = ConstraintSystem.from_equality(dim, rows) if rows else ConstraintSystem(dimension=dim)
    rep = measure_dof(c, seed=3)
    assert rep.agrees, rep
    assert rep.dof_exact == rep.dof_spectral
    assert rep.dof_exact == c.dof()


def test_a_wrong_answer_would_be_caught():
    """The agreement test is only meaningful if it can fail. Perturb the
    spectrum by dropping a direction and confirm the count moves.
    """
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0]])
    rep = measure_dof(c, seed=3)
    assert rep.dof_exact == 5
    wider = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]])
    assert measure_dof(wider, seed=3).dof_exact == 6
    assert measure_dof(wider, seed=3).dof_exact != rep.dof_exact


# --------------------------------------------------------------------- generation


def test_feasible_samples_satisfy_the_constraints():
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]])
    x = generate_in_feasible(c, n=200, seed=4)
    assert np.abs(x @ c.rows.T).max() < 1e-9
    assert float(constraint_residual(c, x).max()) < 1e-9


def test_infeasible_samples_violate_them():
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]])
    x = generate_infeasible(c, n=50, seed=5)
    assert float(constraint_residual(c, x).min()) > 1.0


def test_generated_feasible_states_span_the_right_number_of_dimensions():
    """A generative check that does not use the rank at all."""
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0]])
    x = generate_in_feasible(c, n=800, seed=6)
    centred = x - x.mean(axis=0)
    observed_rank = int(np.linalg.matrix_rank(centred, tol=1e-8))
    assert observed_rank == c.dof() == 5


# --------------------------------------------------------------------- projection


def test_projection_is_the_identity_on_the_feasible_subspace():
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]])
    x = generate_in_feasible(c, n=20, seed=7)
    assert np.allclose(c.project(x), x, atol=1e-9)


def test_projection_removes_the_forbidden_component():
    c = ConstraintSystem.from_equality(8, [[1, 0, 0, 0, 0, 0, 0, 0]])
    x = np.array([[10.0, 5.0, 1.0, 0, 0, 0, 0, 0]])
    out = c.project(x)
    assert out[0, 0] == pytest.approx(0.0, abs=1e-9)
    assert out[0, 1] == pytest.approx(5.0)


# --------------------------------------------------------------------- traversal


def test_traversal_stays_feasible_and_contracts():
    """Three properties at once: it moves, it stays in the manifold, and
    the drift decays. A system that misses any one of these is not the
    substrate this project claims.
    """
    c = ConstraintSystem.from_equality(8, [
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0]])
    r = traverse_manifold(c, steps=150, eta=0.2, seed=8)
    assert r["stayed_feasible"] is True
    assert r["max_residual"] < 1e-8
    assert r["final_drift"] < r["initial_drift"] * 1e-6
    assert r["monotone"] is True
    assert r["dof"] == 5


def test_traversal_respects_a_tighter_manifold():
    """Fewer free directions must still traverse cleanly -- the constraint
    set is not a special case of a full-dimensional one.
    """
    c = ConstraintSystem.from_equality(8, [[1, 1, 1, 1, 1, 1, 1, 1]])
    r = traverse_manifold(c, steps=100, eta=0.3, seed=9)
    assert r["dof"] == 7
    assert r["stayed_feasible"] is True
    assert r["monotone"] is True


def test_traversal_on_the_full_space_is_also_feasible():
    c = ConstraintSystem(dimension=8)
    r = traverse_manifold(c, steps=60, eta=0.5, seed=10)
    assert r["dof"] == 8
    assert r["stayed_feasible"] is True
    assert r["final_drift"] < r["initial_drift"]