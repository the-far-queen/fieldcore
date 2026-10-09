"""Tests for the constraint-projection comparison.

Source: deepseek8 part 10 claims LayerNorm IS the substrate's projector
Pi_C. These tests measure whether that is true. It is not, and the two
bugs in the measuring code are recorded here because both produced
confident wrong answers before being caught.

BUG 1. `compare_projectors` reported IDENTICAL because it tested whether
each operator was internally faithful to its own constraint set, rather
than whether the two operators produce the same output. Two different maps
can both be faithful and still send one input to 2.828 and 1.0.

BUG 2. The additivity probe used a harmonic part that was a constant
vector, and LayerNorm maps a constant vector to zero, so the test passed
trivially. The non-degenerate case -- two vectors that are individually
non-constant -- is where the failure shows.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from constraint_projection import (  # noqa: E402
    compare_projectors, harmonic_survives_layernorm, layernorm,
    layernorm_radius, radial_projection, scaling_under_layernorm,
)


# --------------------------------------------------------------------- LayerNorm


def test_layernorm_zeroes_the_mean():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(6, 8)) * 4 + 7.0
    assert np.allclose(layernorm(x).mean(axis=-1), 0.0, atol=1e-6)


def test_layernorm_sets_unit_variance():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(6, 8)) * 9 + 3.0
    assert np.allclose(layernorm(x).var(axis=-1), 1.0, atol=1e-3)


def test_layernorm_radius_is_sqrt_dim_regardless_of_input():
    """Zero mean and unit variance over d coordinates forces ||x||^2 = d --
    but ONLY for an input that has non-zero variance to begin with. A
    constant vector has none, and normalises to exactly zero. That is a
    stronger statement about the substrate invariant than the radius
    rescaling: the state can be sent to the origin, not merely rescaled.
    """
    rng = np.random.default_rng(2)
    # scale 0.01 is deliberately excluded: its variance is ~1e-4, which is
    # the same order as the 1e-5 epsilon, so the epsilon dominates and the
    # identity does not apply. That boundary is a property of the
    # epsilon, not of the operator, and it is asserted separately below.
    # The identity is exact in real arithmetic; the 1e-5 epsilon inside the
    # denominator puts a floor under the observed error of about
    #     sqrt(d) * eps / (2 * var)
    # so the tolerance is DERIVED from the input rather than guessed.
    # Measured: 1.9e-4 at scale 0.5, 3.0e-5 at 1.0, 4.7e-9 at 100.
    d = 8
    def tol_for(x: np.ndarray) -> float:
        """Worst-case epsilon error over all rows.

        The per-row error scales as sqrt(d)*eps/(2*var_i), so the binding
        constraint is the SMALLEST variance row, not the mean. Using the
        mean understated the tolerance and the assertion failed for that
        reason alone.
        """
        var_min = float(np.min(x.var(axis=-1)))
        return math.sqrt(d) * 1e-5 / (2.0 * max(var_min, 1e-12)) * 2.0

    for scale in (0.5, 1.0, 100.0):
        x = rng.normal(size=(256, d)) * scale
        radii = np.linalg.norm(layernorm(x), axis=-1)
        tol = tol_for(x)
        assert np.all(np.abs(radii - math.sqrt(d)) < tol), (scale, tol, float(np.abs(radii - math.sqrt(d)).max()))
        assert layernorm_radius(d) == pytest.approx(math.sqrt(d))
    # the offset does not matter, only the variance
    shifted = rng.normal(size=(256, d)) * 3.0 + 500.0
    assert np.all(np.abs(np.linalg.norm(layernorm(shifted), axis=-1)
                         - math.sqrt(d)) < tol_for(shifted))
    # the degenerate case, stated rather than assumed away
    assert np.allclose(layernorm(np.ones(8)), 0.0, atol=1e-4)
    assert np.allclose(layernorm(np.zeros(8)), 0.0, atol=1e-4)


# --------------------------------------------------------------------- radial


def test_radial_projection_bounds_the_radius():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(6, 8)) * 50
    out = radial_projection(x, np.zeros(8), radius=1.0)
    assert np.all(np.linalg.norm(out, axis=-1) <= 1.0 + 1e-9)


def test_radial_projection_leaves_small_states_alone():
    x = np.full((1, 8), 0.01)
    out = radial_projection(x, np.zeros(8), radius=1.0)
    assert np.allclose(out, x)


def test_radial_projection_is_about_psi0_not_the_origin():
    psi0 = np.full(8, 5.0)
    x = psi0 + np.array([3.0, 0, 0, 0, 0, 0, 0, 0])
    out = radial_projection(x, psi0, radius=1.0)
    assert abs(float(np.linalg.norm(out - psi0)) - 1.0) < 1e-9


# --------------------------------------------------------------------- the claim


def test_the_two_projectors_are_not_the_same_operator():
    """The claim in deepseek8 part 10, tested."""
    rng = np.random.default_rng(4)
    x = rng.normal(size=(5, 8)) * 3 + rng.normal(size=(5, 1)) * 4
    d = compare_projectors(x, np.zeros(8), radius=1.0)
    assert d.same_output is False
    assert d.verdict == "DIFFERENT CONSTRAINT SETS"


def test_both_are_faithful_to_their_own_constraint_sets():
    """Both can be faithful and still differ. This is the distinction the
    first version of the comparison got wrong.
    """
    rng = np.random.default_rng(5)
    x = rng.normal(size=(5, 8))
    d = compare_projectors(x, np.zeros(8), radius=1.0)
    assert d.layernorm_faithful is True
    assert d.projection_faithful is True
    assert d.same_output is False


def test_the_radius_is_the_decisive_difference():
    rng = np.random.default_rng(6)
    x = rng.normal(size=(4, 8)) * 6
    d = compare_projectors(x, np.zeros(8), radius=1.0)
    # LayerNorm forces sqrt(8) whatever came in
    assert all(abs(r - math.sqrt(8)) < 1e-6 for r in d.layernorm_radius_after)
    # the radial projector honours the bound it was given
    assert all(r <= 1.0 + 1e-9 for r in d.projection_radius_after)
    assert max(d.radius_before) > 5.0


def test_layernorm_erases_the_input_scale():
    """The substrate invariant is the radius. LayerNorm destroys it, so the
    harmonic part is rescaled along with everything else.

    Non-degenerate inputs only: a constant vector normalises to zero rather
    than to sqrt(d), which is a different failure and is covered above.
    """
    rng = np.random.default_rng(7)
    small = rng.normal(size=(64, 8)) * 2.0 + 5.0
    large = rng.normal(size=(64, 8)) * 200.0 + 5.0
    a = np.linalg.norm(layernorm(small), axis=-1)
    b = np.linalg.norm(layernorm(large), axis=-1)
    assert np.allclose(a, b, atol=1e-3)


def test_scaling_ratio_is_not_uniform_across_inputs():
    """Each vector is scaled by its own standard deviation, so two states
    of different size get different rescaling. A constraint projection
    that preserved relative structure would not.
    """
    rng = np.random.default_rng(8)
    x = rng.normal(size=(6, 8)) * np.array([[0.1], [1.0], [10.0], [0.5], [3.0], [0.01]])
    s = scaling_under_layernorm(x)
    assert s["uniform_scaling"] is False
    assert len(set(round(v, 6) for v in s["scale_ratio"])) > 1


# --------------------------------------------------------------------- harmonic


def test_harmonic_part_is_not_preserved():
    """Non-degenerate inputs: two individually non-constant vectors whose
    sum is normalised non-additively.
    """
    rng = np.random.default_rng(9)
    h = rng.normal(size=8)
    g = rng.normal(size=8)
    r = harmonic_survives_layernorm(h, g)
    assert r["additive"] is False
    assert r["layernorm_is_linear"] is False
    assert r["additivity_relative"] > 0.1


def test_the_epsilon_boundary_is_measured_not_assumed():
    """LayerNorm is scale-free only while the input variance dominates the
    1e-5 epsilon. Below that it under-normalises, and the radius falls away
    from sqrt(d).

    The boundary was located by measurement, not assumed: radius 2.8284 at
    scale 1.0 and above, 2.826 at 0.1, 2.64 at 0.01, 0.77 at 1e-3, 0.0008 at
    1e-6. The first version of this test picked a scale and asserted a
    number without checking where the regime actually starts.
    """
    rng = np.random.default_rng(20)
    d = 8
    # firmly inside the scale-free regime
    for scale in (1.0, 10.0):
        x = rng.normal(size=(256, d)) * scale
        r = float(np.linalg.norm(layernorm(x), axis=-1).mean())
        assert abs(r - math.sqrt(d)) < 1e-3, (scale, r)
    # firmly inside the epsilon-dominated regime
    tiny = rng.normal(size=(256, d)) * 1e-6
    r_tiny = float(np.linalg.norm(layernorm(tiny), axis=-1).mean())
    assert r_tiny < 1e-2, r_tiny
    # and the transition is monotonic in between
    mid = float(np.linalg.norm(layernorm(rng.normal(size=(256, d)) * 1e-3),
                               axis=-1).mean())
    assert r_tiny < mid < math.sqrt(d), (r_tiny, mid)


def test_a_constant_harmonic_part_maps_to_zero():
    """The degenerate case that hid the bug in the first probe.

    LayerNorm removes the mean, so a constant vector has zero variance and
    normalises to zero. That is a stronger statement about the harmonic
    part than non-additivity: it can be removed entirely.
    """
    r = harmonic_survives_layernorm(np.ones(8), np.array([5.0, 0, 0, 0, 0, 0, 0, 0]))
    assert np.allclose(layernorm(np.ones(8)), 0.0, atol=1e-4)


def test_orthogonal_parts_do_not_stay_separate():
    rng = np.random.default_rng(10)
    h = rng.normal(size=8)
    g = rng.normal(size=8)
    assert harmonic_survives_layernorm(h, g)["additivity_relative"] > 0.0


# --------------------------------------------------------------------- coverage


def test_comparison_handles_a_vector_inside_the_ball():
    """An input already inside the radius is not projected by Pi_B, so the
    two operators can coincidentally agree more closely -- but not
    identically, because LayerNorm still rescales.
    """
    tiny = np.full((1, 8), 0.001)
    d = compare_projectors(tiny, np.zeros(8), radius=1.0)
    assert d.projection_radius_after[0] < 0.01
    # LayerNorm sends a CONSTANT vector to exactly zero, which is neither
    # the tiny input nor sqrt(d). Any value at all proves they differ.
    assert abs(d.layernorm_radius_after[0] - math.sqrt(8)) > 1e-3
    assert d.layernorm_radius_after[0] < 1e-3
    assert d.same_output is False