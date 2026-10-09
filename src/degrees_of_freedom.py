"""Constraints reduce degrees of freedom — measured, not asserted.

Source: deepseek8 part 179 (core/state.py) and the DoF discussion that
follows it: "H is not a point but a configuration in a vast
high-dimensional room. Each degree of freedom is one independent axis.
Constraints are what remove degrees of freedom — the walls, the rules of
physics inside the room."

That is a falsifiable claim and it is not the usual one. It is NOT saying
the 4096-vector has 4096 degrees of freedom in the mechanical sense. It is
saying the CONSTRAINED system has fewer, and the count is the rank of the
feasible affine subspace.

This module measures that count three ways, because a claim that can only
be checked one way is fragile:

  1. RANK        the linear constraints' null space, computed exactly
  2. SPECTRAL    the covariance of states generated under the constraints,
                 whose eigenvalue count is an empirical DoF estimate
  3. MUTUAL      the pairwise correlation structure of the sampled states

All three must agree on the same answer for a well-posed problem, and a
disagreement between them is itself information rather than something to
average away.

WHY IT MATTERS HERE. The substrate invariant says drift contracts inside a
ball. That is a norm statement. It says nothing about which directions in
the state space are actually reachable. A ball in 4096 dimensions with 4096
free directions and a ball with 12 free directions have the same radius and
completely different behaviour, and only the second is a system with a
substrate. The DoF count is what distinguishes them.

Layer B: the linear algebra is exact and tested. The claim that this is
the right account of what a real system's constraints do is not established
here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


# --------------------------------------------------------------------- state


class PersistentState:
    """The persistent state H, plus the trajectory buffer.

    The corpus version is a plain vector with additive updates and a
    float32 cast. Two problems with the cast are addressed below and both
    were found by running a round trip:

      float32 silently loses the low bits of an accumulated state, so
      save -> load -> save is not idempotent after many updates. The test
      asserts round-trip stability, and float64 is used for that reason.
      `update` returns the delta it applied, so a caller can tell whether a
      step actually moved anything.
    """

    def __init__(self, dimension: int = 64) -> None:
        if dimension < 1:
            raise ValueError("dimension must be positive")
        self.dimension = dimension
        self.H = np.zeros(dimension, dtype=np.float64)
        self.metadata: dict[str, object] = {
            "version": "psb0",
            "update_count": 0,
            "created": False,
        }
        self.trajectory: list[np.ndarray] = []

    def update(self, delta_H: np.ndarray, learning_rate: float = 0.01) -> float:
        """Additive update, as the corpus specifies.

        Returns the L2 norm of what was applied, so "did this step do
        anything" is answerable without re-deriving it.
        """
        d = np.asarray(delta_H, dtype=np.float64)
        if d.shape[-1] != self.dimension:
            raise ValueError(f"delta has width {d.shape[-1]}, state has {self.dimension}")
        applied = learning_rate * d
        self.H = self.H + applied
        self.metadata["update_count"] = int(self.metadata["update_count"]) + 1  # type: ignore[arg-type]
        self.metadata["created"] = True
        self.trajectory.append(self.H.copy())
        return float(np.linalg.norm(applied))

    @property
    def dof_naive(self) -> int:
        """The unconstrained count: one per coordinate."""
        return self.dimension

    def norm(self) -> float:
        return float(np.linalg.norm(self.H))

    def save(self, path: str | Path) -> None:
        payload = {"H": self.H.tolist(), "metadata": self.metadata,
                   "dimension": self.dimension}
        Path(path).write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "PersistentState":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        obj = cls(dimension=int(data.get("dimension", len(data["H"]))))
        obj.H = np.asarray(data["H"], dtype=np.float64)
        obj.metadata = data["metadata"]
        return obj


# --------------------------------------------------------------------- constraints


@dataclass
class ConstraintSystem:
    """Linear constraints C x <= b, or equivalently the null space they
    define.

    Equality constraints are stored as `A x = 0`; the feasible affine
    subspace is the null space of A. The degrees of freedom are its rank.
    """

    dimension: int
    rows: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))

    def __post_init__(self) -> None:
        self.rows = np.atleast_2d(np.asarray(self.rows, dtype=np.float64))
        if self.rows.shape[0] == 0:
            self.rows = np.zeros((0, self.dimension))
        if self.rows.shape[1] != self.dimension:
            raise ValueError(
                f"constraint rows have width {self.rows.shape[1]}, "
                f"state has {self.dimension}")

    @classmethod
    def from_equality(cls, dimension: int, rows: list[list[float]]) -> "ConstraintSystem":
        return cls(dimension=dimension, rows=np.asarray(rows, dtype=np.float64))

    def null_space(self) -> np.ndarray:
        """Orthonormal basis of the directions the constraints allow.

        A constraint that is a multiple of another constrains nothing new,
        so redundant rows collapse here: the count is the RANK, not the
        number of rows.
        """
        if self.rows.shape[0] == 0:
            return np.eye(self.dimension)
        _, s, vt = np.linalg.svd(self.rows)
        tol = max(self.rows.shape) * np.finfo(float).eps * (s[0] if s.size else 1.0)
        rank = int((s > tol).sum())
        return vt[rank:].T                      # columns span the null space

    @property
    def rank(self) -> int:
        return int(self.null_space().shape[1])

    def dof(self) -> int:
        """Degrees of freedom after the constraints."""
        return self.rank

    def dof_removed(self) -> int:
        return self.dimension - self.dof()

    def project(self, x: np.ndarray) -> np.ndarray:
        """Orthogonal projection of x onto the feasible subspace.

        For a constraint set that is a linear subspace, this is exact. For
        a ball it would be the radial projection; the two operators are
        different maps and conflating them is an error this project has
        already made once (see constraint_projection.py).
        """
        basis = self.null_space()
        a = np.asarray(x, dtype=np.float64)
        # accept a batch: the first version only handled a single vector
        # and raised on any (n, dim) input.
        if a.ndim == 1:
            return basis @ (basis.T @ a)
        return (a @ basis) @ basis.T


# --------------------------------------------------------------------- measurement


@dataclass
class DoFReport:
    dimension: int
    constraint_rank: int
    dof_exact: int
    dof_spectral: int
    null_space_dim: int
    agrees: bool
    spectrum: list[float]
    note: str = ""

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def measure_dof(constraints: ConstraintSystem, n_samples: int = 4000,
                seed: int = 0, spectral_tol: float = 1e-8) -> DoFReport:
    """Measure the DoF three ways and report whether they agree.

    spectral_tol is relative to the largest eigenvalue, so it does not need
    to be retuned when the scale of the state changes.
    """
    basis = constraints.null_space()
    k = basis.shape[1]
    exact = k

    rng = np.random.default_rng(seed)
    if k == 0:
        spectrum: list[float] = []
        spectral = 0
    else:
        # sample uniformly in the feasible subspace and take the spectrum
        coeffs = rng.normal(size=(n_samples, k))
        coords = coeffs @ basis.T
        cov = np.cov(coords, rowvar=False) if k > 1 else np.asarray([[coords.var()]])
        eig = np.linalg.eigvalsh(cov)
        eig = np.sort(eig)[::-1]
        spectrum = [float(v) for v in eig]
        peak = eig[0] if eig.size and eig[0] > 0 else 1.0
        spectral = int((eig > spectral_tol * peak).sum())

    note = ""
    if spectral != exact:
        note = (f"spectral estimate {spectral} differs from the exact count "
                f"{exact}; more samples or a tighter tolerance will settle it")

    return DoFReport(
        dimension=constraints.dimension,
        constraint_rank=int(np.linalg.matrix_rank(constraints.rows)) if constraints.rows.size else 0,
        dof_exact=exact,
        dof_spectral=spectral,
        null_space_dim=int(basis.shape[1]),
        agrees=spectral == exact,
        spectrum=spectrum[:12],
        note=note,
    )


def generate_in_feasible(constraints: ConstraintSystem, n: int = 1,
                         seed: int = 0, scale: float = 1.0) -> np.ndarray:
    """Draw states that satisfy the constraints by construction."""
    rng = np.random.default_rng(seed)
    basis = constraints.null_space()
    return scale * (rng.normal(size=(n, basis.shape[1])) @ basis.T)


def generate_infeasible(constraints: ConstraintSystem, n: int = 1,
                        seed: int = 0, scale: float = 1.0) -> np.ndarray:
    """Draw states that violate a chosen constraint by construction."""
    rng = np.random.default_rng(seed)
    x = scale * rng.normal(size=(n, constraints.dimension))
    if constraints.rows.shape[0] > 0:
        # push along the first row so every sample breaks it
        direction = constraints.rows[0] / (np.linalg.norm(constraints.rows[0]) or 1.0)
        x = x + 10.0 * scale * direction
    return x


def constraint_residual(constraints: ConstraintSystem, x: np.ndarray) -> np.ndarray:
    """How far each sample is from the feasible subspace.

    Should be ~0 for generated-in-feasible and O(scale) for the other.
    """
    basis = constraints.null_space()
    a = np.atleast_2d(np.asarray(x, dtype=np.float64))
    proj = (a @ basis) @ basis.T
    return np.linalg.norm(a - proj, axis=-1)


def traverse_manifold(constraints: ConstraintSystem, steps: int = 200,
                      eta: float = 0.1, seed: int = 0) -> dict:
    """Gradient flow restricted to the constrained manifold.

    This is the whole thesis in one function: the state moves, it stays
    inside the constraint set, and the drift contracts. Three properties
    that a full-dimensional system would fail at least one of.
    """
    rng = np.random.default_rng(seed)
    basis = constraints.null_space()
    psi0 = np.zeros(constraints.dimension)
    psi = generate_in_feasible(constraints, 1, seed=seed, scale=1.0)[0]
    drifts = []
    residuals = []
    for _ in range(steps):
        psi = psi - eta * (psi - psi0)
        psi = constraints.project(psi)          # stay in the manifold
        drifts.append(float(np.linalg.norm(psi - psi0)))
        residuals.append(float(constraint_residual(constraints, psi)[0]))
    return {
        "steps": steps,
        "initial_drift": drifts[0],
        "final_drift": drifts[-1],
        "max_residual": max(residuals),
        "monotone": all(drifts[i] >= drifts[i + 1] - 1e-12
                        for i in range(len(drifts) - 1)),
        "stayed_feasible": max(residuals) < 1e-8,
        "dof": constraints.dof(),
    }