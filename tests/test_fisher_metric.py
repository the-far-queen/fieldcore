"""Tests for the Fisher metric and the natural-gradient correspondence.

Source: deepseek8 parts 05, 08, 09.

These tests are written to protect two things at once: the arithmetic, and
the claim that it is NOT original. The natural-gradient / Fisher reading of
attention has been published repeatedly (Amari 1985 for natural gradient;
2024 work on attention as natural gradient with respect to the attention
distribution's Fisher matrix). A test that quietly let this module claim
discovery would be worse than no test.

The one bug worth recording: the first version of `fisher_from_scores`
asserted that the Fisher metric is the COVARIANCE OF THE LOGITS and called
it exact. Measured against the direct definition it was wrong by 0.998.
The exact identity for a categorical is p - p p^T. The two agree only in
the small-logit regime where p is near uniform, which is exactly why the
error was invisible on inspection and only showed up when it was run.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fisher_metric import (  # noqa: E402
    attention_entropy, attention_matrix, compare, conditioning,
    dropped_terms, fisher_from_probabilities, fisher_from_samples,
    fisher_from_scores, inverse_fisher, inverse_metric_approximation,
    natural_gradient_step, softmax, transformer_block_step,
)


# --------------------------------------------------------------------- softmax


def test_softmax_sums_to_one():
    p = softmax(np.random.default_rng(0).normal(size=(20, 7)))
    assert np.allclose(p.sum(axis=1), 1.0)
    assert np.all(p >= 0)


def test_softmax_is_numerically_stable():
    """Rows with huge logits must not produce inf or nan."""
    p = softmax(np.array([[1000.0, 1001.0, 999.0], [-1000.0, -999.0, -1001.0]]))
    assert np.all(np.isfinite(p))
    assert np.allclose(p.sum(axis=1), 1.0)


# --------------------------------------------------------------------- Fisher


def test_fisher_identity_matches_the_direct_definition():
    """p - p p^T is the exact Fisher of a categorical. Asserted against a
    direct sum over samples, not against itself.
    """
    rng = np.random.default_rng(0)
    probs = softmax(rng.normal(size=(1, 6)))[0]
    # sample y FROM the model. Sampling y uniformly and then comparing
    # against p - p p^T compares two different distributions, which is how
    # this test failed the first time round.
    y = rng.choice(6, size=200_000, p=probs)
    onehot = np.eye(6)[y]
    logits = np.log(probs)                     # the same distribution
    exact = fisher_from_scores(logits)
    direct = fisher_from_samples(logits, onehot)
    assert np.abs(exact - direct).max() < 5e-3


def test_fisher_converges_at_monte_carlo_rate():
    """The residual between an analytic identity and a sampled estimate must
    fall as 1/sqrt(n). Asserting the RATE is what distinguishes a correct
    formula from a merely plausible one.
    """
    rng = np.random.default_rng(1)
    p = softmax(rng.normal(size=(1, 8)))[0]
    target = np.diag(p) - np.outer(p, p)

    def error(n: int) -> float:
        y = rng.choice(8, size=n, p=p)
        grads = np.eye(8)[y] - p
        return float(np.abs(grads.T @ grads / n - target).max())

    e_small, e_large = error(2_000), error(80_000)
    assert e_large < e_small
    # 40x more samples should give roughly sqrt(40) ~ 6x less error
    assert e_large < e_small / 3.0, (e_small, e_large)


def test_fisher_of_logits_is_not_logit_covariance():
    """The regression guard for the bug in the first version.

    These are genuinely different matrices. If they ever agree here, the
    small-logit regime has hidden the distinction again.
    """
    rng = np.random.default_rng(2)
    logits = rng.normal(size=(5_000, 6)) * 3.0     # large logits on purpose
    f = fisher_from_scores(logits)
    cov = np.cov(logits, rowvar=False)
    assert np.abs(f - cov).max() > 0.1


def test_fisher_is_symmetric_and_positive_semidefinite():
    rng = np.random.default_rng(3)
    f = fisher_from_scores(rng.normal(size=(500, 7)))
    assert np.allclose(f, f.T)
    assert np.linalg.eigvalsh(f).min() > -1e-9


def test_fisher_is_singular_when_support_is_deficient():
    """A distribution over fewer outcomes than dimensions has a null
    direction, so the inverse does not exist without regularisation.
    """
    p = np.zeros(5)
    p[:3] = 1.0 / 3.0
    f = fisher_from_probabilities(p)
    c = conditioning(f)
    assert c["invertible_without_ridge"] is False
    assert c["condition_number"] > 1e6 or math.isinf(c["condition_number"])


# --------------------------------------------------------------------- inverse


def test_inverse_is_symmetric_for_symmetric_positive_input():
    rng = np.random.default_rng(4)
    a = rng.normal(size=(6, 6))
    f = a @ a.T + np.eye(6)
    inv = inverse_fisher(f, ridge=0.0)
    assert np.allclose(inv, inv.T, atol=1e-8)
    assert np.allclose(inv @ f, np.eye(6), atol=1e-8)


def test_ridge_makes_a_singular_metric_invertible():
    p = np.zeros(5)
    p[:3] = 1.0 / 3.0
    f = fisher_from_probabilities(p)
    inv = inverse_fisher(f, ridge=1e-3)
    assert np.all(np.isfinite(inv))


def test_conditioning_reports_rank_deficiency():
    p = np.zeros(4)
    p[:2] = 0.5
    c = conditioning(fisher_from_probabilities(p))
    assert c["rank"] < c["dimension"]


# --------------------------------------------------------------------- attention


def test_attention_rows_are_distributions():
    rng = np.random.default_rng(5)
    q, k = rng.normal(size=(5, 8)), rng.normal(size=(7, 8))
    a = attention_matrix(q, k, dk=8.0)
    assert np.allclose(a.sum(axis=1), 1.0)
    assert a.shape == (5, 7)


def test_attention_survives_huge_logits():
    q = np.array([[1e4, -1e4]])
    k = np.array([[1e4, -1e4], [-1e4, 1e4]])
    a = attention_matrix(q, k, dk=2.0)
    assert np.all(np.isfinite(a))
    assert np.allclose(a.sum(axis=1), 1.0)


def test_uniform_attention_has_maximum_entropy():
    n = 8
    a = np.full((n, n), 1.0 / n)
    assert abs(attention_entropy(a) - math.log(n)) < 1e-9


def test_peaky_attention_has_low_entropy():
    a = np.eye(8)
    assert attention_entropy(a) < 1e-6


def test_entropy_is_bounded_by_log_n():
    rng = np.random.default_rng(6)
    for _ in range(20):
        a = attention_matrix(rng.normal(size=(4, 6)), rng.normal(size=(4, 6)), 4.0)
        assert 0.0 <= attention_entropy(a) <= math.log(6) + 1e-9


# --------------------------------------------------------------------- preconditioner


def test_preconditioner_has_identity_anti_term():
    a = np.eye(5)
    m = inverse_metric_approximation(1.0, a, 0.5, 4)
    assert np.allclose(m, 1.0 * np.eye(5) - 0.5 * np.eye(5))


def test_preconditioner_depends_on_both_scalars():
    a = np.full((4, 4), 0.25)
    assert not np.allclose(inverse_metric_approximation(1.0, a, 0.5, 4),
                           inverse_metric_approximation(2.0, a, 0.5, 4))


def test_uniform_attention_makes_the_preconditioner_uniform():
    """The degeneracy case, stated rather than discovered in use: when
    attention is uniform, the low-rank term is a constant and the
    preconditioner averages instead of preconditioning.
    """
    n = 6
    a = np.full((n, n), 1.0 / n)
    m = inverse_metric_approximation(1.0, a, 0.5, 4)
    row_sums = m.sum(axis=1)
    assert np.allclose(row_sums, row_sums[0])


# --------------------------------------------------------------------- the steps


def test_natural_gradient_step_moves_downhill_on_a_quadratic():
    """On F = 1/2||H - c||^2 the natural step must reduce the distance."""
    h = np.random.default_rng(7).normal(size=5) * 2.0
    c = np.zeros(5)
    fisher = np.eye(5)
    before = np.linalg.norm(h - c)
    after_h = natural_gradient_step(h, h - c, fisher)
    assert np.linalg.norm(after_h - c) < before


def test_transformer_block_step_adds_the_preconditioned_term():
    h = np.ones(4)
    a = np.eye(4)
    mlp = np.arange(4.0)
    out = transformer_block_step(h, a, mlp, alpha=1.0, delta=0.5)
    expected = h + (1.0 * np.eye(4) - 0.5 * np.eye(4)) @ mlp
    assert np.allclose(out, expected)


def test_the_two_rules_can_be_compared_and_can_disagree():
    """If `compare` could never report disagreement it would be decoration.
    """
    rng = np.random.default_rng(8)
    m = rng.normal(size=(6,))
    same = compare(m, m)
    assert same.relative_error == 0.0
    assert same.matches
    diff = compare(m, rng.normal(size=(6,)))
    assert diff.relative_error > 0.25
    assert not diff.matches


def test_dropped_terms_are_quantified_not_assumed_small():
    rng = np.random.default_rng(9)
    a = rng.normal(size=(5, 5))
    fisher = a @ a.T + np.eye(5)
    report = dropped_terms(rng.normal(size=5), rng.normal(size=5), fisher)
    for key in ("frobenius_exact_inverse", "frobenius_approx_inverse",
                "frobenius_discarded", "fraction_discarded"):
        assert key in report
    assert report["fraction_discarded"] >= 0.0
    assert math.isfinite(report["condition"])


def test_well_conditioned_metric_discards_little():
    """The approximation should be honest when the metric is benign, and
    the fraction discarded is the number that says so either way.
    """
    report = dropped_terms(np.zeros(4), np.zeros(4), np.eye(4))
    assert report["fraction_discarded"] < 1.0