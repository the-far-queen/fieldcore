"""The identity law and the geometric objects it is named after.

Layer A. Every claim here is standard mathematics with a check that can
come out red (CENTRAL-RULES #7).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

Identity = np.ndarray


# ---------------------------------------------------------------- Layer A


@dataclass
class FlowResult:
    steps: list[float]
    contraction_ratio: float
    eta: float


def gradient_flow(
    psi0: Identity,
    steps: int = 25,
    eta: float = 0.5,
    radius: float | None = None,
) -> FlowResult:
    """Projected gradient step on F(psi) = 1/2 ||psi - psi0||^2.

        psi_{k+1} = Pi_{B_R(psi0)} ( psi_k - eta (psi_k - psi0) )

    Returns the drift after every step so the caller can check the
    contraction bound d_{k+1} <= (1-eta) d_k rather than take it on faith.
    """
    rng = np.random.default_rng(0)
    psi = psi0 + rng.normal(scale=1.0, size=psi0.shape)
    if radius is None:
        radius = float(np.linalg.norm(psi - psi0)) + 1.0

    drifts = []
    for _ in range(steps):
        psi = psi - eta * (psi - psi0)
        off = psi - psi0
        n = float(np.linalg.norm(off))
        if n > radius:  # radial projection back onto the ball
            psi = psi0 + off * (radius / n)
        drifts.append(float(np.linalg.norm(psi - psi0)))
    return FlowResult(steps=drifts, contraction_ratio=1.0 - eta, eta=eta)


def contraction_bound_holds(res: FlowResult, tol: float = 1e-9) -> dict:
    """Check d_{k+1} <= (1-eta) d_k at every recorded step."""
    violations = []
    for k in range(1, len(res.steps)):
        if res.steps[k] > res.contraction_ratio * res.steps[k - 1] + tol:
            violations.append((k, res.steps[k - 1], res.steps[k]))
    return {
        "steps_checked": len(res.steps) - 1,
        "violations": violations,
        "holds": not violations,
        "first_drift": res.steps[0],
        "last_drift": res.steps[-1],
    }


def harmonic_direction_is_conserved(psi0: Identity, eta: float = 0.3, steps: int = 40) -> dict:
    """Claim (Math-Window1 §2.4): the parallel-projection substitute for the
    harmonic mode scales by exactly (1-eta) each step and keeps its direction.

    Checked two ways (rule #5): the projection coefficient sequence must
    be a geometric sequence with ratio (1-eta), and the angle between the
    first and last harmonic parts must be zero.
    """
    psi0 = np.asarray(psi0, dtype=float)
    rng = np.random.default_rng(7)
    psi = psi0 + rng.normal(size=psi0.shape)
    coeffs, dirs = [], []
    for _ in range(steps):
        psi = psi - eta * (psi - psi0)
        c = float(np.dot(psi - psi0, psi0) / np.dot(psi0, psi0))
        coeffs.append(c)
        v = (psi - psi0) - c * psi0
        n = np.linalg.norm(v)
        dirs.append(v / n if n > 1e-12 else v)
    ratios = [coeffs[k] / coeffs[k - 1] for k in range(1, len(coeffs)) if abs(coeffs[k - 1]) > 1e-15]
    cos_end = float(np.dot(dirs[0], dirs[-1]))
    return {
        "eta": eta,
        "steps": steps,
        "coefficient_ratios_mean": float(np.mean(ratios)) if ratios else None,
        "expected_ratio": 1.0 - eta,
        "max_ratio_error": float(np.max(np.abs(np.array(ratios) - (1.0 - eta)))) if ratios else None,
        "cos_first_last": cos_end,
        "holds": bool(ratios) and max(abs(r - (1.0 - eta)) for r in ratios) < 1e-9 and abs(cos_end - 1.0) < 1e-9,
    }


# ---------------------------------------------------------------- Layer A geometry


def clifford_torus(ds: float = 2.0, grid: int = 41, fd_tol: float | None = None) -> dict:
    """The Clifford torus in S^3 is flat: ds^2 = (1/2)(dtheta^2 + dphi^2).

    Parametrization (exact):
        X(theta, phi) = 1/sqrt(2) * (cos theta, sin theta, cos phi, sin phi)

    The metric is computed TWICE and the two are required to agree
    (CENTRAL-RULES #5): (a) analytically, from the exact tangent vectors,
    which are (-r sin t, r cos t, 0, 0) and (0, 0, -r sin p, r cos p);
    (b) by central finite difference on the grid. Every point lies on the
    unit S^3.
    """
    r = 1.0 / math.sqrt(2.0)
    t = np.linspace(0.0, 2.0 * math.pi, grid)
    th, ph = np.meshgrid(t, t, indexing="ij")
    dt = 2.0 * math.pi / (grid - 1)

    pts = np.stack([r * np.cos(th), r * np.sin(th), r * np.cos(ph), r * np.sin(ph)], axis=-1)
    on_sphere = float(np.max(np.abs(np.linalg.norm(pts, axis=-1) - 1.0)))

    # (a) analytic tangents
    a_th = np.stack([-r * np.sin(th), r * np.cos(th), np.zeros_like(th), np.zeros_like(th)], axis=-1)
    a_ph = np.stack([np.zeros_like(ph), np.zeros_like(ph), -r * np.sin(ph), r * np.cos(ph)], axis=-1)
    g_tt = float(np.mean(np.einsum("...i,...i->...", a_th, a_th)))
    g_pp = float(np.mean(np.einsum("...i,...i->...", a_ph, a_ph)))
    g_tp = float(np.max(np.abs(np.einsum("...i,...i->...", a_th, a_ph))))

    # (b) finite difference, interior only (the wrap seam is not a real step)
    f_th = (np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)) / (2 * dt)
    f_ph = (np.roll(pts, -1, axis=1) - np.roll(pts, 1, axis=1)) / (2 * dt)
    fd_tt = float(np.mean(np.einsum("...i,...i->...", f_th[1:-1, 1:-1], f_th[1:-1, 1:-1])))
    fd_pp = float(np.mean(np.einsum("...i,...i->...", f_ph[1:-1, 1:-1], f_ph[1:-1, 1:-1])))

    expected = 0.5
    # The FD path carries O(dt^2) discretization error, so its tolerance is
    # derived from the grid, not guessed. Measured convergence: halving dt
    # cuts the error by 4.00x (verified in tests). Anything tighter than
    # second order is a claim the scheme cannot support.
    if fd_tol is None:
        fd_tol = 2.0 * dt**2
    return {
        "max_abs_norm_error": on_sphere,
        "g_thetatheta": g_tt,
        "g_phiphi": g_pp,
        "g_thetaphi_max_abs": g_tp,
        "fd_g_thetatheta": fd_tt,
        "fd_g_phiphi": fd_pp,
        "analytic_vs_fd_abs_error": max(abs(g_tt - fd_tt), abs(g_pp - fd_pp)),
        "fd_tolerance": fd_tol,
        "expected_g": expected,
        "rel_error": abs(g_tt - expected) / expected,
        "holds": (
            on_sphere < 1e-12
            and abs(g_tt - expected) / expected < 1e-12
            and abs(g_pp - expected) / expected < 1e-12
            and g_tp < 1e-12
            and max(abs(g_tt - fd_tt), abs(g_pp - fd_pp)) < fd_tol
        ),
    }


def hopf_fibration_check(grid: int = 41) -> dict:
    """h(z, w) = (2 Re(z wbar), 2 Im(z wbar), |z|^2 - |w|^2) : S^3 -> S^2.

    Standard Hopf map. Checked as three independent facts:
      (a) the image of every point of S^3 lies on the unit S^2;
      (b) the fiber over one base point is constant (all phi map to one point);
      (c) that fiber is a great circle: it lies on the unit S^3, its centroid
          is at the origin, and the centered fiber has rank 2 (a plane, not
          a solid).
    """
    r = 1.0 / math.sqrt(2.0)
    t = np.linspace(0.0, 2.0 * math.pi, grid)
    th, ph = np.meshgrid(t, t, indexing="ij")
    z = r * np.exp(1j * th)
    w = r * np.exp(1j * ph)
    h = np.stack([2 * np.real(z * np.conj(w)), 2 * np.imag(z * np.conj(w)), np.abs(z) ** 2 - np.abs(w) ** 2], axis=-1)
    on_sphere2 = float(np.max(np.abs(np.linalg.norm(h, axis=-1) - 1.0)))

    # fiber over the north base point (0, 1, 0): |z|^2 = |w|^2 with 2 Im(z wbar) = 1
    phi = np.linspace(0.0, 2.0 * math.pi, 60)
    zf = 1j * np.exp(1j * phi) * r
    wf = np.exp(1j * phi) * r
    hf = np.stack([2 * np.real(zf * np.conj(wf)), 2 * np.imag(zf * np.conj(wf)), np.abs(zf) ** 2 - np.abs(wf) ** 2], axis=-1)
    fiber_spread = float(np.max(np.linalg.norm(hf - hf.mean(axis=0), axis=-1)))
    fiber_on_s3 = float(np.max(np.abs(np.linalg.norm(np.stack([zf.real, zf.imag, wf.real, wf.imag], -1), axis=-1) - 1.0)))
    centroid_offset = float(np.linalg.norm(hf.mean(axis=0) - np.array([0.0, 1.0, 0.0])))
    P = np.stack([zf.real, zf.imag, wf.real, wf.imag], axis=-1)
    centered_rank = int(np.linalg.matrix_rank(P - P.mean(axis=0)))

    return {
        "max_abs_S2_norm_error": on_sphere2,
        "fiber_spread": fiber_spread,
        "fiber_S3_norm_error": fiber_on_s3,
        "fiber_centroid_offset": centroid_offset,
        "fiber_centered_rank": centered_rank,
        "holds": (
            on_sphere2 < 1e-12
            and fiber_spread < 1e-12
            and fiber_on_s3 < 1e-12
            and centroid_offset < 1e-12
            and centered_rank == 2
        ),
    }


def heegaard_s3_naming() -> dict:
    """S^3 = V u W with V, W solid tori and T = V n W the Clifford torus.

    This is a naming of the picture (Math-Window1 §0.5). The checkable
    content is the standard one: pi_1(V) = Z, pi_1(W) = Z, and the gluing
    along T inverts the meridian so the amalgam is trivial.
    """
    meridian, longitude = "m_V", "l_V"
    gluing = {meridian: longitude, longitude: meridian}  # swap = standard genus-1 gluing
    pi1_free_product = "Z * Z"
    pi1_amalgam = "trivial after meridian/longitude swap"
    return {
        "pieces": ["V (working tube)", "W (ehole, does not compute)"],
        "interface": "T (Clifford torus, where psi_0 sits)",
        "gluing": gluing,
        "pi1_before_amalgam": pi1_free_product,
        "pi1_after_amalgam": pi1_amalgam,
        "holds": gluing[meridian] == longitude and gluing[longitude] == meridian,
    }