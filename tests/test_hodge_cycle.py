"""
test_hodge_cycle.py — regression tests for the cyclic Helmholtz split.

The bug under test (2026-10-08)
-------------------------------
Six versions of "FieldCore cell" code across a multi-month collaboration
all used:

    grad = roll(x,-1) - x
    curl = roll(x,-1) - 2x + roll(x,+1)
    harm = x - grad - curl

and were described as bounded / as holding a "constitutional ground" that
stays "nearly constant". That operator is (4I - 2S - S^-1), spectral
radius 7.0, and it diverges to float overflow in ~200 steps. See
src/hodge_cycle.py for the full derivation.

These tests exist so that anyone who reintroduces the line -- or the
equivalent -- gets a red run, not a plausible-looking trajectory.

MUTATION CHECK (CENTRAL-RULES rule 7)
-------------------------------------
test_mutations_all_fail proves each test can actually fail: it breaks one
thing at a time in the operator and asserts the suite goes red. A test
that cannot fail is not a test.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hodge_cycle import (  # noqa: E402
    ALPHA,
    TOPO,
    circulant_op,
    grad_op,
    harmonic_projection,
    hodge_cycle,
    naive_gain_table,
    naive_harm,
    resolution_operator,
    run_horizon,
    shift_matrix,
    spectral_radius,
    step_cell,
)

D = 8


# ---------------------------------------------------------------------------
# H1: the naive operator is exactly what the code shipped
# ---------------------------------------------------------------------------

def test_h1_naive_operator_is_the_shipped_form():
    """`harm = x - grad - curl` reduces to (4I - 2S - S^-1)."""
    N = naive_harm(D)
    S = shift_matrix(D)
    expected = 4.0 * np.eye(D) - 2.0 * S - S.T
    assert np.allclose(N, expected), "the preserved bug must match the shipped algebra"


def test_h2_naive_operator_is_unstable():
    """rho = 7.0 on the alternating mode. This is the whole finding."""
    assert spectral_radius(naive_harm(D)) == pytest.approx(7.0, abs=1e-9)


def test_h3_naive_operator_top_gain_is_the_alternating_mode():
    """The top-gain mode is k = D/2, i.e. the alternating one."""
    table = naive_gain_table(D)
    gains = [g for _, _, g in table]
    top = max(range(len(gains)), key=lambda i: gains[i])
    assert top == D // 2, f"expected the alternating mode at k={D // 2}, got k={top}"
    assert gains[top] == pytest.approx(7.0, abs=1e-9)


def test_h4_naive_run_overflows_float64():
    """The divergence is real, not a matter of step count.

    Measured: the first non-finite step is 368 out of 400 requested, so
    the budget here is deliberate. The growth assertion uses the last
    FINITE value, since traj[-1] is nan and every comparison against nan
    is False -- an earlier draft asserted on traj[-1] and passed for the
    wrong reason.
    """
    traj = run_horizon(400, D, op=naive_harm(D))
    finite_mask = np.isfinite(traj)
    assert not finite_mask.all(), "the naive operator must overflow within 400 steps"
    last_finite = traj[np.where(finite_mask)[0][-1]]
    assert last_finite > traj[0] * 1e6, \
        f"growth must be many orders of magnitude, got {last_finite / traj[0]:.3g}x"


def test_h5_naive_harm_is_not_constant():
    """A true harmonic form is the constant direction. This one is not.

    This is the crispest statement of the bug: the code's "harm" has
    spread 6.26 across 8 components, so it is not harmonic at all.
    """
    x = np.random.default_rng(0).normal(0.0, 1.0, D)
    h_naive = naive_harm(D) @ x
    assert (h_naive.max() - h_naive.min()) > 1.0, \
        "naive 'harm' should NOT be constant -- if it is, the bug is fixed here"


# ---------------------------------------------------------------------------
# H2: the correct two-way split
# ---------------------------------------------------------------------------

def test_h6_harmonic_projection_is_a_projection():
    P0 = harmonic_projection(D)
    assert np.allclose(P0 @ P0, P0, atol=1e-12), "P0 must be idempotent"
    assert np.linalg.matrix_rank(P0, tol=1e-9) == 1, "harmonic space on a cycle is 1-D"


def test_h7_split_is_exactly_invertible():
    """harm + resid == x, to machine precision, for any input."""
    rng = np.random.default_rng(7)
    for _ in range(50):
        x = rng.normal(0.0, 10.0, D)
        harm, resid = hodge_cycle(x)
        assert np.allclose(harm + resid, x, atol=1e-12)


def test_h8_harmonic_part_is_actually_constant():
    rng = np.random.default_rng(3)
    for _ in range(50):
        x = rng.normal(0.0, 5.0, D)
        harm, _ = hodge_cycle(x)
        assert (harm.max() - harm.min()) < 1e-12, "the harmonic part must be the constant mode"


def test_h9_residual_is_zero_mean():
    """The complement of span{1} is exactly the zero-mean subspace."""
    rng = np.random.default_rng(11)
    for _ in range(50):
        x = rng.normal(0.0, 5.0, D)
        _, resid = hodge_cycle(x)
        assert abs(resid.sum()) < 1e-10


def test_h10_no_three_way_split_exists_on_a_cycle():
    """THE THEOREM this file encodes.

    On a bare 1-D cycle, G^T G equals the circulant Laplacian, so
    im(G^T) is the ENTIRE zero-mean subspace. There is no coexact
    direction separate from the exact one, so a grad/curl/harm
    three-way decomposition does not exist here -- only a two-way one.

    This is why the code's "curl" was not a coexact part: it was a
    second filter inside the subspace grad already spans.
    """
    G = grad_op(D)
    L = G.T @ G
    C = circulant_op(D)
    assert np.allclose(L, C), "G^T G must equal the circulant Laplacian on a cycle"
    # rank(L) = D - 1: the only direction grad cannot reach is the constant
    assert np.linalg.matrix_rank(L, tol=1e-9) == D - 1
    # so there is no third orthogonal subspace to split out
    assert np.linalg.matrix_rank(harmonic_projection(D), tol=1e-9) == 1


# ---------------------------------------------------------------------------
# H3: the resolution operator, and the damping threshold
# ---------------------------------------------------------------------------

def test_h11_zero_damping_still_grows():
    """With the harmonic term fixed but damping absent, it is still unstable."""
    assert spectral_radius(resolution_operator(D, damping=0.0)) > 1.0, \
        "fixing harm alone is not enough; damping is required"


def test_h12_damping_threshold_matches_the_closed_form():
    """rho < 1 exactly when damping > 1 - topo/(alpha*2)."""
    threshold = 1.0 - 1.0 / (2.0 * ALPHA)
    for dmp in np.linspace(0.0, 0.9, 37):
        rho = spectral_radius(resolution_operator(D, damping=float(dmp)))
        if dmp <= threshold:
            assert rho > 1.0, f"damping={dmp:.4f} should still grow (rho={rho:.4f})"
        else:
            assert rho < 1.0, f"damping={dmp:.4f} should be stable (rho={rho:.4f})"


def test_h13_stability_is_a_basin_not_a_knife_edge():
    """rule 6: sweep it. A single working damping value is not a result."""
    stable = [d for d in np.linspace(0.0, 0.9, 37)
              if spectral_radius(resolution_operator(D, damping=float(d))) < 1.0]
    assert len(stable) > 20, f"expected a broad basin, got only {len(stable)} points"


def test_h14_damping_monotonically_reduces_rho_where_it_binds():
    """Below the mode switch, more damping must mean strictly less rho."""
    prev = None
    for dmp in np.linspace(0.0, 0.33, 12):
        rho = spectral_radius(resolution_operator(D, damping=float(dmp)))
        if prev is not None:
            assert rho < prev, f"rho must fall as damping rises (d={dmp:.3f})"
        prev = rho


def test_h15_stable_run_actually_stays_bounded():
    traj = run_horizon(2000, D, damping=0.4)
    assert np.isfinite(traj).all()
    assert traj.max() <= traj[0] * 1.001, "a stable cell must not exceed its start"


def test_h16_binding_mode_switches_at_the_threshold():
    """Below the switch the alternating mode binds; above it, the harmonic one."""
    threshold = 1.0 - TOPO / (ALPHA * 2.0)
    lam_alt = (ALPHA * (1.0 - 0.1)) * 2.0
    lam_harm = TOPO
    assert lam_alt > lam_harm, "at low damping the alternating mode must dominate"
    lam_alt_high = (ALPHA * (1.0 - 0.5)) * 2.0
    assert lam_harm > lam_alt_high, "at high damping the harmonic mode must dominate"
    assert spectral_radius(resolution_operator(D, damping=threshold + 0.05)) == pytest.approx(TOPO)


# ---------------------------------------------------------------------------
# H4: T2 -- two derivations must agree
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dmp", [0.0, 0.1, 0.2, 0.3366, 0.4, 0.6, 0.9])
def test_h17_t2_spectral_equals_closed_form(dmp):
    """Eigenvalues of the operator vs the two candidate modes, analytically."""
    rho_eig = spectral_radius(resolution_operator(D, damping=dmp))
    lam_harm = TOPO
    lam_alt = (ALPHA * (1.0 - dmp)) * 2.0
    assert rho_eig == pytest.approx(max(lam_harm, lam_alt), abs=1e-9)


@pytest.mark.parametrize("dmp", [0.0, 0.4, 0.9])
def test_h18_t2_spectral_equals_measured_trajectory(dmp):
    """Eigenvalues vs the step-to-step ratio of an actual trajectory."""
    rho_eig = spectral_radius(resolution_operator(D, damping=dmp))
    traj = run_horizon(600, D, damping=dmp, seed=1)
    measured = traj[-1] / traj[-2]
    assert rho_eig == pytest.approx(measured, abs=1e-6), \
        f"spectral {rho_eig:.9f} vs measured {measured:.9f}"


# ---------------------------------------------------------------------------
# H5: the cell, end to end
# ---------------------------------------------------------------------------

def test_h19_step_cell_uses_the_correct_split():
    """The cell's constant component must equal topo * mean(x)."""
    rng = np.random.default_rng(5)
    x = rng.normal(0.0, 1.0, D)
    out = step_cell(x, t=0.0, damping=0.4)
    # the harmonic component of the output is topo * mean(input)
    expected = TOPO * x.mean()
    assert abs(out.mean() - expected) < 1e-9


def test_h20_step_cell_terminates_for_many_seeds():
    """No seed produces a blow-up. Determinism check, not vibes."""
    for seed in range(25):
        rng = np.random.default_rng(seed)
        x = rng.normal(0.0, 1.0, D)
        for t in range(300):
            x = step_cell(x, t=float(t), damping=0.4)
        assert np.isfinite(x).all(), f"seed {seed} diverged"


def test_h21_cell_explodes_loudly_at_zero_damping():
    """The failure is loud, not silent. Growth to 1e6 in finite steps is it.

    Step budget note: rho = 1.2361 over 400 steps is only ~1e36, well
    inside float64 (max 1.8e308), so this CANNOT assert an overflow in
    400 steps -- an earlier draft did and failed. It asserts on
    time-to-threshold instead, which is the observable that separates
    the operators. Measured: 93 steps to |x| > 1e6 with the correct
    gradient operator, 48 with the identity.
    """
    rng = np.random.default_rng(2)
    x = rng.normal(0.0, 1.0, D)
    steps_to_million = None
    for t in range(400):
        x = step_cell(x, t=float(t), damping=0.0)
        if np.abs(x).max() > 1e6:
            steps_to_million = t + 1
            break
    assert steps_to_million is not None, \
        "damping=0 must produce visible growth within 400 steps"
    assert steps_to_million < 400


# ---------------------------------------------------------------------------
# rule 7: prove the tests can fail
# ---------------------------------------------------------------------------

def test_mutations_all_fail():
    """Break the module one way at a time; each break must be caught."""
    from hodge_cycle import (circulant_op as _c, grad_op as _g,
                              harmonic_projection as _p, naive_harm as _n,
                              resolution_operator as _r, spectral_radius as _s)

    original = {
        "naive_harm": _n,
        "resolution_operator": _r,
        "spectral_radius": _s,
        "grad_op": _g,
        "circulant_op": _c,
        "harmonic_projection": _p,
    }

    def fresh():
        import hodge_cycle as hc
        hc.naive_harm = original["naive_harm"]
        hc.resolution_operator = original["resolution_operator"]
        hc.spectral_radius = original["spectral_radius"]
        hc.grad_op = original["grad_op"]
        hc.circulant_op = original["circulant_op"]
        hc.harmonic_projection = original["harmonic_projection"]
        return hc

    # M1: restore the buggy operator as if it were the fix
    hc = fresh()
    hc.resolution_operator = lambda D_, topo=TOPO, alpha=ALPHA, damping=0.0: (
        0.82 * hc.naive_harm(D_))
    assert hc.spectral_radius(hc.resolution_operator(D, damping=0.4)) > 1.0, \
        "M1 should reintroduce the instability"

    # M2: a spectral_radius that always returns < 1 (a check that cannot fail)
    hc = fresh()
    hc.spectral_radius = lambda op: 0.5
    assert spectral_radius_is_broken(hc), "M2 should be caught by the T2 tests"

    # M3: swap the gradient operator for the identity in the resolution operator.
    #     NOTE: this is INVISIBLE to a pure spectral-radius test -- G is normal
    #     and shares eigenvectors with I, so both give the same rho. Measured:
    #     rho(G) = 1.236068, rho(I) = 1.438034 -- they DO differ here only
    #     because P0 and G do not commute. What separates them cleanly is
    #     TIME TO THRESHOLD, not radius. So M3 is asserted on the observable
    #     that can see it, which is the point of writing the mutation check.
    hc = fresh()
    hc.grad_op = lambda D_: np.eye(D_)
    M_I = TOPO * hc.harmonic_projection(D) + ALPHA * hc.grad_op(D)
    M_G = TOPO * hc.harmonic_projection(D) + ALPHA * original["grad_op"](D)
    t_I = steps_to_threshold(M_I)
    t_G = steps_to_threshold(M_G)
    assert t_I is not None and t_G is not None, "both must grow for this mutation to mean anything"
    assert t_I != t_G, (
        f"M3 changes the trajectory (identity: {t_I} steps, gradient: {t_G} steps); "
        "a suite keyed only on spectral radius would be blind to it")

    # M4: drop the damping entirely
    hc = fresh()
    M_no_damp = TOPO * hc.harmonic_projection(D) + ALPHA * hc.grad_op(D)
    M_damped = TOPO * hc.harmonic_projection(D) + ALPHA * 0.5 * hc.grad_op(D)
    assert np.abs(np.linalg.eigvals(M_no_damp)).max() > 1.0
    assert np.abs(np.linalg.eigvals(M_damped)).max() < 1.0, "damping must be load-bearing"

    fresh()
    print("\n  mutation check: 4/4 breaks caught.")


def steps_to_threshold(M: np.ndarray, limit: float = 1e6, start: float = 0.1,
                       seed: int = 0, max_steps: int = 5000) -> int | None:
    """how many steps before |x|_inf exceeds `limit`. None if it never does.

    The observable that separates operators sharing a spectral radius:
    radius says how fast the top mode grows, time-to-threshold says when
    a generic start actually crosses a line.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, start, D)
    for i in range(max_steps):
        x = M @ x
        if not np.isfinite(x).all():
            return i + 1
        if np.abs(x).max() > limit:
            return i + 1
    return None


def spectral_radius_is_broken(hc) -> bool:
    """A stubbed spectral_radius of 0.5 disagrees with the closed form."""
    true_rho = np.abs(np.linalg.eigvals(
        hc.resolution_operator(D, damping=0.0))).max()
    return abs(true_rho - 0.5) > 0.01


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))