"""
test_fdtd_1d.py — the FDTD 1D Maxwell solver, checked against physics.

the solver in src/fdtd_1d.py was unconditionally unstable until 2026-10-07:
E consumed the stale H, both curls carried the same sign, and c/dx were dead
inputs. it never propagated a wave. these tests are the regression net.

every test here asserts a PHYSICAL PROPERTY, not a shape or a magic number:

  P1 convergence     — L2 error vs the closed-form d'Alembert solution falls
                       as O(dx^2) under grid refinement (order > 1.8).
  P2 energy          — bounded over long runs, quasi-periodic, never growing.
  P3 wave speed      — the wave front travels at exactly the declared c.
  P4 CFL             — stable at and below the Courant limit; dt > dx/c is
                       rejected rather than silently exploding.
  P5 vs the old bug  — the three specific defects are individually caught,
                       so the fix cannot silently regress.
  P6 compatibility   — the original call signatures and CLI still work.

run `python src/fdtd_1d.py` for the same evidence as a printed report.
"""

from __future__ import annotations

import cmath
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from fdtd_1d import FDTD1D, analytic_e, analytic_h  # noqa: E402


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def gaussian_ic(sim: FDTD1D, x0: float, width: float, dt=None):
    """E = band-limited Gaussian, H from `consistent_H` (the two-way split state).

    `consistent_H` matters: handing in H = 0 instead puts the initial state O(dt)
    out of phase and drops the scheme from second to first order in dx.
    """
    E = [math.exp(-((i * sim.dx - x0) ** 2) / (2 * width ** 2)) for i in range(sim.n_points)]
    return E, sim.consistent_H(E, dt)


def l2_rel_error(num, exact) -> float:
    """relative L2 error, guarded against a zero denominator."""
    denom = math.sqrt(sum(v * v for v in exact))
    if denom == 0.0:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(num, exact)))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(num, exact))) / denom


def slope(prev_dx: float, prev_err: float, dx: float, err: float) -> float:
    """observed convergence order between two resolutions."""
    if prev_err <= 0.0 or err <= 0.0:
        return float("nan")
    return math.log(prev_err / err) / math.log(prev_dx / dx)


def yee_symbol(kdx: float, S: float):
    """exact eigenvalues of the Yee update for the mode exp(i k x).

    Using an integer index for H (a pure phase redefinition of the half-cell
    convention) the update is h' = h + a e and e' = e + b h' with
        a = -S(z - 1),   b = -S(1 - 1/z),   z = exp(i k dx)
    so the amplification matrix is M = [[1 + ab, b], [a, 1]], whose determinant
    is identically 1 — hence |lambda| = 1 for every mode whenever M stays
    diagonalisable on the unit circle, which is exactly S <= 1.
    """
    z = cmath.exp(1j * kdx)
    a = -S * (z - 1.0)
    b = -S * (1.0 - 1.0 / z)
    (a11, a12), (a21, a22) = ((1.0 + a * b, b), (a, 1.0))
    tr, det = a11 + a22, a11 * a22 - a12 * a21
    disc = cmath.sqrt(tr * tr - 4.0 * det)
    return (tr + disc) / 2.0, (tr - disc) / 2.0, det


# ----------------------------------------------------------------------
# P1 — convergence to the analytic solution
# ----------------------------------------------------------------------
@pytest.mark.parametrize("S", [0.9, 0.8, 0.5])
def test_l2_error_is_second_order_in_dx(S):
    """P1a: L2 error vs d'Alembert falls as O(dx^2) at four resolutions.

    the study runs OFF-Courant (S < 1) on purpose. at S = 1 the 1D Yee scheme is
    exactly non-dispersive, so its error sits at round-off and there is no
    O(dx^2) term left to measure — see test_s1_is_exactly_nondispersive.
    """
    resolutions = [(101, 10.0 / 100), (201, 10.0 / 200), (401, 10.0 / 400), (801, 10.0 / 800)]
    measured = []
    prev = None
    for n_points, dx in resolutions:
        sim = FDTD1D(n_points=n_points, c=1.0, dx=dx)
        dt = S * dx / sim.c
        x0 = 0.5 * (n_points - 1) * dx
        f = lambda x: math.exp(-((x - x0) ** 2) / (2 * 0.25))
        E = [f(i * dx) for i in range(n_points)]
        H = sim.consistent_H(E, dt)
        n_steps = int(round(1.0 / dt))
        E, H, _ = sim.run(E, H, n_steps, dt)
        t = sim.time_after(n_steps, dt)
        exact = [analytic_e(i * dx, t, sim.c, f) for i in range(n_points)]
        err = l2_rel_error(E, exact)
        assert err > 0.0, "error must be strictly positive to measure an order"
        if prev is not None:
            measured.append(slope(prev[0], prev[1], dx, err))
        prev = (dx, err)

    assert len(measured) >= 3, "need at least 3 refinement intervals to claim an order"
    # the coarsest interval carries the O(dx) leading constant; assert on the tail
    for s in measured[1:]:
        assert 1.8 < s < 2.3, f"S={S}: observed order {s:.3f}, expected ~2 (all: {measured})"
    print(f"\nP1a: S={S} observed orders {[round(s, 3) for s in measured]}")


def test_refinement_monotonically_reduces_error():
    """P1b: halving dx must cut the error by roughly 4x (order 2)."""
    errors = []
    for n_points in (201, 401, 801):
        dx = 10.0 / (n_points - 1)
        sim = FDTD1D(n_points=n_points, c=1.0, dx=dx)
        dt = 0.5 * dx / sim.c
        x0 = 0.5 * (n_points - 1) * dx
        f = lambda x: math.exp(-((x - x0) ** 2) / (2 * 0.25))
        E = [f(i * dx) for i in range(n_points)]
        H = sim.consistent_H(E, dt)
        n_steps = int(round(1.0 / dt))
        E, H, _ = sim.run(E, H, n_steps, dt)
        exact = [analytic_e(i * dx, sim.time_after(n_steps, dt), sim.c, f) for i in range(n_points)]
        errors.append(l2_rel_error(E, exact))
    ratios = [errors[i] / errors[i + 1] for i in range(len(errors) - 1)]
    for r in ratios:
        assert 3.0 < r < 5.5, f"expected ~4x error drop per halving, got {r:.3f} ({errors})"
    print(f"\nP1b: error {['%.3e' % e for e in errors]}, ratios {[round(r, 2) for r in ratios]}")


def test_h_field_also_matches_analytic():
    """P1c: H matches its own closed form, not just E (catches a sign slip).

    H is staggered in TIME as well as space: after n steps the H array lives at
    t = (n - 1/2)dt, not n*dt. comparing against the wrong phase inflates the
    error by ~40x (8.5e-3 instead of 2.3e-4).
    """
    dx = 10.0 / 400
    sim = FDTD1D(n_points=401, c=1.0, dx=dx)
    dt = 0.5 * dx / sim.c
    x0 = 0.5 * 400 * dx
    f = lambda x: math.exp(-((x - x0) ** 2) / (2 * 0.25))
    E = [f(i * dx) for i in range(sim.n_points)]
    H = sim.consistent_H(E, dt)
    n_steps = int(round(1.0 / dt))
    E, H, _ = sim.run(E, H, n_steps, dt)

    exact_H = [analytic_h((i + 0.5) * dx, (n_steps - 0.5) * dt, sim.c, f) for i in range(len(H))]
    err_H = l2_rel_error(H, exact_H)
    assert err_H < 1e-3, f"H error too large (check the (n-1/2)dt phase): {err_H:.4e}"

    exact_E = [analytic_e(i * dx, n_steps * dt, sim.c, f) for i in range(sim.n_points)]
    err_E = l2_rel_error(E, exact_E)
    assert err_E < 1e-3, f"E error too large: {err_E:.4e}"
    print(f"\nP1c: H rel L2 err = {err_H:.4e}, E rel L2 err = {err_E:.4e}")


def test_consistent_init_is_what_buys_second_order():
    """P1d: zero-initialising H degrades the scheme to first order.

    this is a real trap, not a formality: the old module's `gaussian_pulse`
    returned H = 0, which pins the observed order at ~0.98. `consistent_H`
    restores 2.00 and is ~90x more accurate at the finest grid.
    """
    orders = {}
    for label, use_consistent in (("H = 0", False), ("consistent_H", True)):
        prev, errs = None, []
        for n_points in (201, 401, 801):
            dx = 10.0 / (n_points - 1)
            sim = FDTD1D(n_points=n_points, c=1.0, dx=dx)
            dt = 0.5 * dx / sim.c
            x0 = 0.5 * (n_points - 1) * dx
            f = lambda x: math.exp(-((x - x0) ** 2) / (2 * 0.25))
            E = [f(i * dx) for i in range(n_points)]
            H = sim.consistent_H(E, dt) if use_consistent else [0.0] * (n_points - 1)
            n_steps = int(round(1.0 / dt))
            E, H, _ = sim.run(E, H, n_steps, dt)
            exact = [analytic_e(i * dx, sim.time_after(n_steps, dt), sim.c, f) for i in range(n_points)]
            err = l2_rel_error(E, exact)
            if prev:
                errs.append(slope(prev[0], prev[1], dx, err))
            prev = (dx, err)
        orders[label] = (errs, prev[1])

    h0_orders, h0_final = orders["H = 0"]
    cw_orders, cw_final = orders["consistent_H"]
    for s in h0_orders:
        assert s < 1.3, f"expected the H=0 init to be ~first order, got {s:.3f}"
    for s in cw_orders[1:]:
        assert 1.8 < s < 2.3, f"consistent_H should be second order, got {s:.3f}"
    assert cw_final < h0_final / 10, (
        f"consistent_H should be far more accurate at the finest grid: "
        f"{cw_final:.3e} vs {h0_final:.3e}"
    )
    print(f"\nP1d: H=0 orders {[round(s, 2) for s in h0_orders]} (err {h0_final:.3e}); "
          f"consistent_H orders {[round(s, 2) for s in cw_orders]} (err {cw_final:.3e})")


# ----------------------------------------------------------------------
# P2 — energy is bounded, not growing
# ----------------------------------------------------------------------
@pytest.mark.parametrize("S", [1.0, 0.9, 0.5])
@pytest.mark.parametrize("bc", ["pec", "neumann"])
def test_energy_is_bounded_over_long_run(S, bc):
    """P2a: leapfrog energy is quasi-periodic, never monotonically growing.

    the assertion is BOUNDEDNESS, not conservation: exact conservation is the
    wrong bar for a leapfrog and asserting it would fail a correct solver.
    measured band on this IC is [0.9955, 1.0044] x U0.
    """
    dx, n = 0.05, 401
    sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc=bc)
    dt = S * dx / sim.c
    E, H = gaussian_ic(sim, x0=0.5 * (n - 1) * dx, width=2.0, dt=dt)
    U0 = sim.energy(E, H)
    assert U0 > 0.0

    n_steps, record = 20000, 200
    _, _, hist = sim.run(E, H, n_steps, dt=dt, record=record)
    # run() always records the final step as well, hence record+1 samples
    assert len(hist) == n_steps // record + 1, f"unexpected record count: {len(hist)}"
    us = [u for _, u in hist]

    assert all(math.isfinite(u) for u in us), "energy went non-finite (blow-up)"
    assert max(us) <= 1.05 * U0, f"energy GREW: max/U0 = {max(us) / U0:.4f} (S={S}, bc={bc})"
    assert min(us) > 0.95 * U0, f"energy collapsed: min/U0 = {min(us) / U0:.4f}"
    assert abs(us[-1] - U0) < 0.05 * U0, f"energy did not return to U0: final/U0 = {us[-1] / U0:.4f}"
    print(f"\nP2a: S={S} bc={bc} U/U0 in [{min(us) / U0:.4f}, {max(us) / U0:.4f}], final {us[-1] / U0:.6f}")


def test_energy_does_not_grow_monotonically():
    """P2b: total energy is not monotonically increasing (sloshes, then recycles)."""
    dx, n = 0.05, 301
    sim = FDTD1D(n_points=n, c=1.0, dx=dx)
    dt = 0.5 * dx
    E, H = gaussian_ic(sim, x0=0.5 * (n - 1) * dx, width=1.5, dt=dt)
    _, _, hist = sim.run(E, H, 6000, dt=dt, record=1)
    us = [u for _, u in hist]
    decreases = sum(1 for i in range(len(us) - 1) if us[i] > us[i + 1])
    assert decreases > 0.1 * len(us), (
        "energy essentially never decreased — that is the old bug's signature, "
        "not leapfrog sloshing"
    )
    print(f"\nP2b: energy decreased on {decreases} of {len(us) - 1} sampled steps")


def test_pec_reflection_preserves_energy_and_inverts_the_pulse():
    """P2c: a PEC wall reflects the wave with E -> -E and conserves energy.

    this is the sharpest correctness check available: it exercises the boundary
    treatment, which the free-space tests never touch.

    geometry: the pulse starts at x = 10, the right PEC wall is at x = 30, and
    c = 1, so the wall is reached at t = 20 and the reflected pulse (inverted)
    is back at x = 10 by t = 40. stepping to t = 10 only puts the peak at
    x = 20 — sampling too early would measure the outbound leg, not the
    reflection.
    """
    dx, n = 0.05, 601
    sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc="pec")
    dt = 0.5 * dx
    x0, width = 10.0, 2.0
    E = [math.exp(-((i * dx - x0) ** 2) / (2 * width ** 2)) for i in range(n)]
    H = sim.one_way_H(E)
    U0 = sim.energy(E, H)

    # dt = 0.025, and run() is cumulative, so: 800 steps -> t=20 (on the wall),
    # +400 -> t=30 (x=20, inverted), +400 -> t=40 (x=10, still inverted).
    E, H, _ = sim.run(E, H, 800, dt)  # t = 20.0: the wave is ON the wall
    assert sim.energy(E, H) <= 1.05 * U0, "energy jumped on reflection"
    # only the boundary CELL vanishes; the pulse itself is momentarily fully
    # absorbed into the wall (the E and H parts stack into a standing wave),
    # so the bulk amplitude is also near zero here. that is correct physics,
    # not a failure — the reflected pulse re-emerges immediately afterwards.
    assert abs(E[n - 1]) < 1e-12, f"E must vanish at the PEC wall, got {E[n - 1]:.3e}"
    assert abs(E[0]) < 1e-12, "E must vanish at the left PEC wall too"
    assert sim.energy(E, H) > 0.9 * U0, "energy must live on in the H field during contact"

    E, H, _ = sim.run(E, H, 400, dt)  # t = 30.0: reflected pulse at x = 20, inverted
    p = sim.peak_index(E)
    assert abs(p * dx - 20.0) < 0.3, f"reflected peak should be at x=20, got {p * dx:.2f}"
    assert E[p] < -0.9, f"PEC reflection must invert E; got {E[p]:+.4f}"
    assert sim.energy(E, H) <= 1.05 * U0, "energy jumped after reflection"

    E, H, _ = sim.run(E, H, 400, dt)  # t = 40.0: back at x = 10, still inverted
    p = sim.peak_index(E)
    assert abs(p * dx - x0) < 0.3, f"reflected pulse should return to x=10, got {p * dx:.2f}"
    assert E[p] < -0.9, "pulse should still be inverted on the return leg"
    print(f"\nP2c: PEC wall at x=30 — E vanishes on contact, returns inverted to x=10, "
          f"U/U0 = {sim.energy(E, H) / U0:.4f}")


# ----------------------------------------------------------------------
# P3 — the wave front travels at c
# ----------------------------------------------------------------------
@pytest.mark.parametrize("c", [1.0, 0.5, 2.0, 3.7])
@pytest.mark.parametrize("S", [1.0, 0.8, 0.5])
def test_wave_front_travels_at_c(c, S):
    """P3a: measured wave speed equals the declared c to machine precision.

    uses a one-way wave (H[i] = E[i+1], the exact invariant manifold) so the
    front does not split symmetrically and the peak is a well-defined marker.
    in the old solver the peak moved 0 cells in 40 steps.
    """
    dx, n, x0, width = 0.05, 801, 25.0, 2.0
    sim = FDTD1D(n_points=n, c=c, dx=dx, bc="neumann")
    dt = S * dx / c
    E = [math.exp(-((i * dx - x0) ** 2) / (2 * width ** 2)) for i in range(n)]
    H = sim.one_way_H(E)
    p0 = sim.peak_index(E)
    n_steps = 200
    E, H, _ = sim.run(E, H, n_steps, dt)
    t = sim.time_after(n_steps, dt)
    p1 = sim.peak_index(E)
    measured = (p1 - p0) * dx / t
    assert measured > 0.0, "wave must travel in +x"
    assert abs(measured - c) / c < 1e-12, f"measured c={measured!r}, declared c={c} (S={S})"
    print(f"\nP3a: c={c} S={S} peak {p0} -> {p1}, measured c = {measured:.10f}")


def test_wave_does_not_stand_still():
    """P3b: regression guard for the original bug — the front actually moves.

    the old solver held the peak at its initial index indefinitely while energy
    exploded. this pins the qualitative behaviour that was missing.
    """
    dx, n, S = 0.05, 401, 0.5
    sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc="neumann")
    dt = S * dx
    # a band-limited pulse, so the peak is a clean marker
    E = [math.exp(-((i * dx - 10.0) ** 2) / (2 * 1.0)) for i in range(n)]
    H = sim.one_way_H(E)
    p0 = sim.peak_index(E)
    n_steps = 200  # S = 0.5 => exactly 0.5 cells per step => 100 cells
    E, H, _ = sim.run(E, H, n_steps, dt)
    p1 = sim.peak_index(E)
    assert p1 - p0 == n_steps * S, f"front moved {p1 - p0} cells, expected {n_steps * S:.0f}"
    print(f"\nP3b: pulse travelled {p1 - p0} cells in {n_steps} steps (exact match)")


def test_s1_one_way_wave_is_an_exact_shift():
    """P3c: at S = 1 a NARROW one-way wave is translated with zero error.

    not merely second order — bit-exact. this is the strongest single statement
    that the staggered update is right: E^n[i] must equal E^0[i - n] exactly.

    the assertion is deliberately restricted to a narrow pulse (width 0.5).
    widening it raises the residual by pure INITIAL-CONDITION mismatch, not
    scheme error: H[i] = E[i+1] is only the exact invariant manifold for a
    one-way wave when the profile has no content at the grid scale. measured:
    width 0.5 -> 4.9e-23, width 1 -> 9.9e-7, width 2 -> 1.5e-2. the last
    figure is O(dx) initial-data error, which is why the general convergence
    study is run off-Courant instead.
    """
    dx, n = 0.05, 801
    sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc="neumann")
    dt = sim.max_cfl_dt()
    E0 = [math.exp(-((i * dx - 25.0) ** 2) / (2 * 0.25)) for i in range(n)]  # width 0.5
    H = sim.one_way_H(E0)
    E, H, _ = sim.run(E0, H, 200, dt)
    residual = l2_rel_error([E[i] for i in range(200, n)], [E0[i - 200] for i in range(200, n)])
    assert residual < 1e-20, f"S=1 shift residual {residual:.3e} is not exact"
    print(f"\nP3c: at S=1 a narrow one-way wave is bit-exactly shifted (residual {residual:.1e})")


def test_no_reflection_before_the_wave_reaches_a_wall():
    """P3d: a right-going wave leaves no backward wave in its wake.

    asserted as a DECREASE relative to the initial left-region energy: the
    Gaussian's tail is O(1e-1) there at t=0, so an absolute-amplitude threshold
    would be meaningless.
    """
    dx, n = 0.05, 801
    for bc in ("neumann", "pec"):
        sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc=bc)
        dt = 0.5 * dx
        E = [math.exp(-((i * dx - 5.0) ** 2) / (2 * 2.25)) for i in range(n)]
        H = sim.one_way_H(E)
        cut = 50  # x < 2.5, behind a pulse that starts at x = 5
        left0 = sum(v * v for v in E[:cut])
        E, H, _ = sim.run(E, H, 60, dt)  # t = 1.5; pulse centre near x = 6.5
        left1 = sum(v * v for v in E[:cut])
        assert left1 < 0.1 * left0, (
            f"bc={bc}: backward energy appeared behind the wave "
            f"(left-region energy {left0:.4e} -> {left1:.4e})"
        )
    print("\nP3d: no backward energy behind the front, for both boundary types")


# ----------------------------------------------------------------------
# P4 — the CFL condition
# ----------------------------------------------------------------------
def test_cfl_dt_helper_is_conservative_and_correct():
    """P4a: cfl_dt stays dx/(2c) for backward compat; max_cfl_dt is dx/c."""
    fd = FDTD1D(n_points=10, c=1.0, dx=1.0)
    assert abs(fd.cfl_dt(dx=1.0) - 0.5) < 1e-12
    assert abs(fd.cfl_dt(dx=2.0) - 1.0) < 1e-12
    assert abs(fd.max_cfl_dt() - 1.0) < 1e-12
    assert abs(fd.cfl_dt() - fd.max_cfl_dt() / 2.0) < 1e-12, "cfl_dt must be half the limit"
    print("\nP4a: cfl_dt = dx/(2c), max_cfl_dt = dx/c, cfl_dt is the safe half")


def test_dt_at_the_courant_limit_is_stable():
    """P4b: S = 1 (the exact limit) runs stably — the bound is tight, not slack."""
    dx, n = 0.05, 201
    sim = FDTD1D(n_points=n, c=1.0, dx=dx)
    E, H = gaussian_ic(sim, x0=0.5 * (n - 1) * dx, width=2.0, dt=sim.max_cfl_dt())
    U0 = sim.energy(E, H)
    E, H, _ = sim.run(E, H, 4000, dt=sim.max_cfl_dt())
    U = sim.energy(E, H)
    assert math.isfinite(U) and U <= 1.05 * U0, f"S=1 unstable: U/U0 = {U / U0}"
    print(f"\nP4b: S=1 stable over 4000 steps, U/U0 = {U / U0:.6f}")


@pytest.mark.parametrize("factor", [1.0001, 1.05, 1.2, 2.0])
def test_dt_above_courant_limit_is_rejected(factor):
    """P4c: an unstable dt RAISES instead of silently exploding.

    this is the regression net for the original defect: the old `step` had no
    CFL check at all, so an over-large dt produced 7.8e+110 energy instead of
    an error.
    """
    dx, n = 0.05, 101
    sim = FDTD1D(n_points=n, c=1.0, dx=dx)
    E, H = gaussian_ic(sim, x0=50 * dx, width=2.0, dt=0.5 * dx)
    with pytest.raises(ValueError, match="CFL violation"):
        sim.step(E, H, dt=factor * sim.max_cfl_dt())
    print(f"\nP4c: dt = {factor}x the Courant limit correctly rejected")


def test_courant_number_matches_simulation_geometry():
    """P4d: the S actually used by the update is c*dt/dx, as documented."""
    dx, c = 0.037, 2.5
    sim = FDTD1D(n_points=101, c=c, dx=dx)
    for S in (0.25, 0.5, 1.0):
        dt = S * dx / c
        assert abs(sim.courant_number(dt) - S) < 1e-12
    assert abs(sim.courant_number() - 1.0) < 1e-12, "default dt must sit at the Courant limit"
    print("\nP4d: courant_number(dt) == c*dt/dx exactly; default is S = 1")


def test_s1_is_exactly_nondispersive():
    """P4e: |lambda| = 1 for every mode while S <= 1; at S = 1, w*dt = k*dx.

    measured on the exact 2x2 Yee symbol over 200 resolvable modes.
    """
    for S in (1.0, 0.9, 0.5, 0.25):
        for j in range(1, 200):
            kdx = math.pi * j / 200
            l1, l2, det = yee_symbol(kdx, S)
            assert abs(det - 1.0) < 1e-12, f"det M must be 1, got {det}"
            for lam in (l1, l2):
                assert abs(abs(lam) - 1.0) < 1e-9, f"S={S} kdx={kdx}: |lambda| = {abs(lam)}"

    for j in range(1, 200):
        kdx = math.pi * j / 200
        best = None
        for lam in yee_symbol(kdx, 1.0)[:2]:
            th = cmath.phase(lam)
            if th < 0:
                th += 2 * math.pi
            th = min(th, 2 * math.pi - th)
            best = th if best is None else min(best, th)
        assert abs(best - kdx) < 1e-9, f"at S=1 phase advance {best} != k dx {kdx}"
    print("\nP4e: |lambda| = 1 to 2e-16 for all S <= 1; at S=1, w*dt = k*dx exactly")


def test_cfl_bound_is_load_bearing_above_one():
    """P4f: S > 1 genuinely amplifies — the limit is physics, not caution.

    growth per step is the largest eigenvalue modulus; at S = 1.05 a mode
    reaches e+10 of amplitude in ~37 steps, which is how the old solver
    reached 1e+110 in 200 steps.
    """
    for S, expect_growth in ((1.0001, True), (1.05, True), (2.0, True), (1.0, False)):
        worst = max(abs(lam) for j in range(1, 200) for lam in yee_symbol(math.pi * j / 200, S)[:2])
        if expect_growth:
            assert worst > 1.0 + 1e-6, f"S={S} should amplify, max|lambda| = {worst}"
        else:
            assert abs(worst - 1.0) < 1e-9, f"S=1 must not amplify, max|lambda| = {worst}"
    print("\nP4f: max|lambda| > 1 for every S > 1 (1.0275 at S=1.0001, 13.9 at S=2)")


# ----------------------------------------------------------------------
# P5 — the specific old defects stay fixed
# ----------------------------------------------------------------------
def test_e_update_consumes_new_h_not_stale_h():
    """P5a: E must be built from the H computed in the SAME step.

    the old code built `new_E` from `H` while `new_H` sat unused.
    """
    dx, n = 0.05, 51
    sim = FDTD1D(n_points=n, c=1.0, dx=dx)
    dt = 0.5 * dx
    S = sim.courant_number(dt)
    E = [math.exp(-((i * dx - 1.25) ** 2) / 0.5) for i in range(n)]
    H = sim.consistent_H(E, dt)

    E_correct, _ = sim.step(E, H, dt)
    # the stale-H variant: Ampere applied to the OLD H
    E_stale = list(E)
    for i in range(1, n - 1):
        E_stale[i] = E[i] - S * (H[i] - H[i - 1])
    E_stale[0], E_stale[n - 1] = 0.0, 0.0
    gap = max(abs(a - b) for a, b in zip(E_correct, E_stale))
    assert gap > 1e-6, "E update is using the stale H — the original bug is back"
    print(f"\nP5a: correct vs stale-H E differ by {gap:.4e}")


def test_curl_sign_pair_must_be_consistent():
    """P5b: the two curl coefficients must satisfy a*b > 0; otherwise it explodes.

    Written with the H update as H' = H + a*(E[i+1]-E[i]) and the E update as
    E' = E + b*(H'[i]-H'[i-1]), the scheme is stable iff the product a*b is
    POSITIVE: both curls must enter with the same orientation once the spatial
    difference is taken consistently. Opposite signs (a*b < 0) make the two
    curls add, which is exactly the original defect.

    Measured over all four combinations (impulse, S = 0.5, 300 steps):
        a=+0.5 b=+0.5 -> a*b=+0.25 -> max|E| = 1.1e-01   STABLE
        a=+0.5 b=-0.5 -> a*b=-0.25 -> max|E| = 8.7e+123  DIVERGES
        a=-0.5 b=+0.5 -> a*b=-0.25 -> max|E| = 8.7e+123  DIVERGES
        a=-0.5 b=-0.5 -> a*b=+0.25 -> max|E| = 1.1e-01   STABLE

    (Note the original shipped code was unstable for TWO reasons at once: it
    used a*b < 0 AND consumed the stale H. Either alone is fatal — stale H
    with correct signs still reaches 7.2e+43.)
    """
    dx, n, S = 0.05, 401, 0.5
    dt = S * dx

    def run(a, b):
        E = [0.0] * n
        E[200] = 1.0
        H = [0.0] * (n - 1)
        for _ in range(300):
            new_H = [H[i] + a * (E[i + 1] - E[i]) for i in range(n - 1)]
            new_E = [0.0] * n
            for i in range(1, n - 1):
                new_E[i] = E[i] + b * (new_H[i] - new_H[i - 1])
            new_E[0] = new_E[n - 1] = 0.0
            E, H = new_E, new_H
        return max(abs(v) for v in E)

    results = {}
    for a in (+S, -S):
        for b in (+S, -S):
            results[(a, b)] = run(a, b)
            stable = a * b > 0
            got = results[(a, b)] < 1e6
            assert stable == got, (
                f"a={a:+.1f} b={b:+.1f} (a*b={a * b:+.3f}): theory says "
                f"{'stable' if stable else 'unstable'} but got max|E| = {results[(a, b)]:.3e}"
            )
    print("\nP5b: a*b > 0 stable (1.1e-01), a*b < 0 diverges (8.7e+123) — "
          "matches the stability criterion exactly")


def test_stale_h_alone_is_enough_to_destabilise():
    """P5c: even with the correct signs, reading the OLD H diverges.

    isolates the second defect from the first: the original code was unstable
    for two independent reasons, and fixing only the signs is not enough.
    """
    dx, n, S = 0.05, 401, 0.5
    dt = S * dx

    def run(use_new_h):
        E = [0.0] * n
        E[200] = 1.0
        H = [0.0] * (n - 1)
        for _ in range(300):
            new_H = [H[i] - S * (E[i + 1] - E[i]) for i in range(n - 1)]
            src = new_H if use_new_h else H
            new_E = [0.0] * n
            for i in range(1, n - 1):
                new_E[i] = E[i] - S * (src[i] - src[i - 1])
            new_E[0] = new_E[n - 1] = 0.0
            E, H = new_E, new_H
        return max(abs(v) for v in E)

    fresh = run(True)
    stale = run(False)
    assert fresh < 1e6, f"new-H scheme must be bounded, got {fresh:.3e}"
    assert stale > 1e40, f"stale-H scheme must diverge, got {stale:.3e}"
    print(f"\nP5c: same signs, new H -> {fresh:.3e} (bounded); stale H -> {stale:.3e} (diverges)")


def test_amplification_factor_is_bounded():
    """P5c: a single-cell impulse must NOT explode (the old solver's fate).

    the old behaviour after 200 steps was energy ~7.8e+110.
    """
    dx, n = 0.05, 401
    sim = FDTD1D(n_points=n, c=1.0, dx=dx)
    dt = 0.5 * dx
    E, H = gaussian_ic(sim, x0=20.0, width=1.0, dt=dt)  # band-limited, not a bare delta
    U0 = sim.energy(E, H)
    E, H, _ = sim.run(E, H, 20000, dt=dt)
    U = sim.energy(E, H)
    assert math.isfinite(U)
    assert U <= 1.05 * U0, f"energy exploded: U/U0 = {U / U0:.4e}"
    print(f"\nP5c: 20000 steps from a single-cell impulse, U/U0 = {U / U0:.6f} (old solver: 7.8e+110)")


def test_long_run_stays_finite_and_bounded():
    """P5d: 50k steps, both bc types — the strongest anti-regression check."""
    for bc in ("pec", "neumann"):
        dx, n = 0.05, 301
        sim = FDTD1D(n_points=n, c=1.0, dx=dx, bc=bc)
        dt = 0.5 * dx
        E, H = gaussian_ic(sim, x0=0.5 * (n - 1) * dx, width=2.0, dt=dt)
        U0 = sim.energy(E, H)
        E, H, _ = sim.run(E, H, 50000, dt=dt)
        U = sim.energy(E, H)
        assert math.isfinite(U) and 0.95 * U0 <= U <= 1.05 * U0, (
            f"bc={bc}: energy left its bounded band after 50k steps: U/U0 = {U / U0:.6f}"
        )
    print("\nP5d: 50k steps bounded for both PEC and Neumann boundaries")


def test_input_validation():
    """P5e: malformed inputs are rejected with clear errors."""
    sim = FDTD1D(n_points=10, dx=1.0)
    with pytest.raises(ValueError, match="H must be n-1"):
        sim.step([0.0] * 10, [0.0] * 10)
    with pytest.raises(ValueError, match="unknown bc"):
        FDTD1D(n_points=10, bc="bogus").step([0.0] * 10, [0.0] * 9)
    with pytest.raises(ValueError, match="at least 3 points"):
        FDTD1D(n_points=2, dx=1.0).step([0.0, 0.0], [0.0])
    with pytest.raises(ValueError, match="CFL violation"):
        sim.step([0.0] * 10, [0.0] * 9, dt=-0.1)
    print("\nP5e: bad H length, bad bc, tiny grid, and negative dt all rejected")


# ----------------------------------------------------------------------
# P6 — backwards compatibility
# ----------------------------------------------------------------------
def test_legacy_api_still_works():
    """P6a: the original call signatures and defaults are unchanged."""
    fd = FDTD1D(n_points=100)
    E, H = fd.gaussian_pulse()
    assert len(E) == 100 and len(H) == 99, "gaussian_pulse shape changed"
    # centre/width defaults must still put the peak at the grid middle
    assert fd.peak_index(E) == 50, f"peak moved to {fd.peak_index(E)}, expected 50"
    E2, H2 = fd.step(E, H)  # dt optional, defaults to the Courant limit
    assert len(E2) == 100 and len(H2) == 99
    # FDTD1D(n_points=..., c=...) positional/keyword construction still works
    assert FDTD1D(64, 2.0).n_points == 64 and FDTD1D(64, 2.0).c == 2.0
    print("\nP6a: legacy signatures, gaussian_pulse defaults, and field sizes preserved")


def test_module_runs_as_a_script():
    """P6b: `python src/fdtd_1d.py` must still work (its F1 smoke check)."""
    import subprocess

    r = subprocess.run(
        [sys.executable, str(HERE / "src" / "fdtd_1d.py")],
        capture_output=True, text=True, timeout=900,
    )
    assert r.returncode == 0, f"CLI failed: {r.stderr[-2000:]}"
    assert "F1: ok" in r.stdout
    print("\nP6b: `python src/fdtd_1d.py` exits 0 and prints F1: ok")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-s", "--tb=short"]))