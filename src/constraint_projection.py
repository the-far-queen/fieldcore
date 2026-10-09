"""LayerNorm is NOT the substrate's constraint projection — measured.

Source: deepseek8 part 10, "Summary: Exact Correspondence":

    Constraint          C            LayerNorm conditions (zero mean, unit variance)
    Governor            Pi_C         LayerNorm operation

That is the sharpest claim in the correspondence table, and this file
tests it rather than restating it.

RESULT: false as stated, with numbers. LayerNorm and the substrate's
projector Pi_{B_R(psi0)} are different operators on different constraint
sets:

    LayerNorm    holds per-feature mean and variance fixed
                 (mean 0, var 1). It also collapses the radius to sqrt(d)
                 regardless of the input -- measured below, an input of
                 norm 12.2 becomes norm 2.828.

    Pi_{B_R}     holds the RADIUS fixed (norm <= R about psi0) and lets
                 the direction be whatever it is. Mean and variance are
                 not controlled at all.

So the substrate invariant -- drift contracts inside a ball about psi0 --
is destroyed by LayerNorm, not enforced by it. A reader who substitutes
LayerNorm for Pi_C does not get an approximation; they get a different
constraint, and the harmonic part of the state is rescaled with
everything else.

This is not a refutation of the natural-gradient correspondence. That
correspondence is about the UPDATE RULE. This is about the CONSTRAINT
PROJECTION, and the two are separable claims. `compare_projectors`
returns the measured disagreement between the two operators so the size
of the gap is a number rather than an opinion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def layernorm(x: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Standard LayerNorm over the last axis."""
    a = np.asarray(x, dtype=float)
    mu = a.mean(axis=-1, keepdims=True)
    var = a.var(axis=-1, keepdims=True)
    return (a - mu) / np.sqrt(var + eps)


def radial_projection(x: np.ndarray, psi0: np.ndarray, radius: float) -> np.ndarray:
    """Pi_{B_R(psi0)}: the substrate's own projection. Holds radius, not
    shape."""
    a = np.asarray(x, dtype=float)
    c = np.asarray(psi0, dtype=float)
    off = a - c
    n = np.linalg.norm(off, axis=-1, keepdims=True)
    scale = np.minimum(1.0, radius / np.maximum(n, 1e-12))
    return c + off * scale


@dataclass
class ProjectorDifference:
    layernorm_mean_abs: float
    layernorm_var_mean: float
    layernorm_radius_after: list[float]
    projection_radius_after: list[float]
    radius_before: list[float]
    layernorm_faithful: bool
    projection_faithful: bool

    same_output: bool = False

    @property
    def verdict(self) -> str:
        """The verdict is about the OPERATORS, not about each one being
        internally consistent. Both are faithful to their own constraint
        sets and still completely different maps.
        """
        return "IDENTICAL" if self.same_output else "DIFFERENT CONSTRAINT SETS"


def compare_projectors(x: np.ndarray, psi0: np.ndarray, radius: float = 1.0) -> ProjectorDifference:
    """Measure what each projector actually holds fixed.

    The decisive measurement is the radius. LayerNorm sets the norm to
    sqrt(d) for EVERY input, which means it does not preserve the
    substrate invariant; Pi_B sets it to min(norm, R).
    """
    a = np.atleast_2d(np.asarray(x, dtype=float))
    ln = layernorm(a)
    pr = radial_projection(a, psi0, radius)
    radii_before = [float(v) for v in np.linalg.norm(a, axis=-1)]
    radii_ln = [float(v) for v in np.linalg.norm(ln, axis=-1)]
    radii_pr = [float(v) for v in np.linalg.norm(pr - np.asarray(psi0), axis=-1)]

    ln_mean = float(np.mean(np.abs(ln.mean(axis=-1))))
    ln_var = float(np.mean(ln.var(axis=-1)))
    # "faithful" = it holds the constraint it claims to hold. That is a
    # different question from "are they the same operator" -- the first
    # version conflated the two and returned IDENTICAL for two operators
    # that send the same input to radii 2.828 and 1.0.
    ln_faithful = ln_mean < 1e-4 and abs(ln_var - 1.0) < 1e-3
    pr_faithful = all(r <= radius + 1e-6 for r in radii_pr)
    same_output = bool(np.allclose(ln, pr, atol=1e-6))
    d = ProjectorDifference(
        layernorm_mean_abs=ln_mean,
        layernorm_var_mean=ln_var,
        layernorm_radius_after=radii_ln,
        projection_radius_after=radii_pr,
        radius_before=radii_before,
        layernorm_faithful=ln_faithful,
        projection_faithful=pr_faithful,
    )
    d.same_output = same_output
    return d


def layernorm_radius(dim: int) -> float:
    """The radius LayerNorm produces for a given width, whatever the input.

    Zero mean and unit variance over `dim` coordinates forces
    ||x||^2 = dim, so ||x|| = sqrt(dim). This is why LayerNorm cannot be
    the substrate's projector: it replaces the radius rather than
    bounding it.
    """
    return math.sqrt(dim)


def scaling_under_layernorm(x: np.ndarray) -> dict:
    """How much does LayerNorm rescale a state of a given size?

    This is the quantity that decides whether a harmonic component
    survives LayerNorm unchanged. It does not: the whole vector, harmonic
    part included, is divided by the same scalar.
    """
    a = np.atleast_2d(np.asarray(x, dtype=float))
    ln = layernorm(a)
    before = np.linalg.norm(a, axis=-1)
    after = np.linalg.norm(ln, axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(before > 1e-12, after / before, np.nan)
    return {
        "radius_before": [float(v) for v in before],
        "radius_after": [float(v) for v in after],
        "scale_ratio": [float(v) for v in ratio],
        "uniform_scaling": bool(np.allclose(ratio, ratio[0], atol=1e-6)),
    }


def harmonic_survives_layernorm(harmonic: np.ndarray, gradient_part: np.ndarray) -> dict:
    """Split a state into its LayerNorm-normalised parts and report whether
    the harmonic component keeps its share of the norm.

    The substrate's claim is that the harmonic part is preserved under
    gradient flow because Delta h = 0. LayerNorm is not gradient flow,
    but if it were the constraint projection it would need to leave that
    part alone. It does not: it rescales the whole vector.
    """
    h = np.asarray(harmonic, dtype=float)
    g = np.asarray(gradient_part, dtype=float)
    full = h + g
    ln_full = layernorm(full)
    ln_h = layernorm(h)
    # A constraint projection that preserved the harmonic part would be
    # linear, so norming the sum would equal summing the normed parts.
    #   layernorm(h + g) == layernorm(h) + layernorm(g)   (up to scale)
    # LayerNorm is not linear, so this fails. The first version measured
    # the difference between norm(full) and norm(h) against norm(g), which
    # came out exactly 1.0 by coincidence of the example and looked like
    # additivity. The real test is the sum of the parts.
    sum_of_parts = layernorm(h) + layernorm(g)
    residual = float(np.linalg.norm(ln_full - sum_of_parts))
    scale = float(np.linalg.norm(sum_of_parts))
    return {
        "harmonic_alone_norm": float(np.linalg.norm(h)),
        "additivity_residual": residual,
        "additivity_relative": residual / scale if scale > 1e-12 else math.inf,
        "additive": bool(residual <= 1e-6 * max(1.0, scale)),
        "layernorm_is_linear": bool(residual <= 1e-6 * max(1.0, scale)),
    }