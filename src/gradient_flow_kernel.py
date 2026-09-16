"""
gradient_flow_kernel.py — actual gradient flow on the identity law.

Per Grok sharpen 2026-09-16 + master plan Step 2 (applied by Hermes).

The convergence_demo.py file is Bobby's pedagogical steel-ball-on-concave-surface
demo. It is kept as a teaching artifact. THIS file is the kernel-level demo that
matches the identity law stated in Part III of Grok's article.

Energy: F(ψ) = (1/2) * ||ψ - ψ0||²
Gradient: ∇F(ψ) = ψ - ψ0
Gradient flow: ψ̇ = -(ψ - ψ0)
Discrete step (with ball projection): ψ ← Π_{B_R(ψ0)}(ψ - η(ψ - ψ0))

Solutions decay as e^{-t}. This is the running numerical truth of the kernel,
not a museum exhibit.

CLI:
    python gradient_flow_kernel.py --steps 50 --R 3.0 --eta 0.1 --seed 0 --dim 16
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import List

import numpy as np


@dataclass
class FlowResult:
    drifts: List[float]
    energies: List[float]
    final_drift: float
    converged: bool
    steps: int
    dim: int
    R: float
    eta: float
    seed: int


def energy(psi: np.ndarray, psi0: np.ndarray) -> float:
    return 0.5 * float(np.sum((psi - psi0) ** 2))


def project_ball(psi: np.ndarray, psi0: np.ndarray, R: float) -> np.ndarray:
    """Project ψ onto the closed ball B_R(ψ0) by radial projection from ψ0."""
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


def gradient_flow(
    *,
    dim: int = 16,
    steps: int = 50,
    R: float = 3.0,
    eta: float = 0.1,
    seed: int = 0,
    psi0_first_axis: float = 1.0,
    initial_perturbation: float = 2.5,
    convergence_tol: float = 1e-6,
) -> FlowResult:
    """Run the projected gradient flow on F(ψ) = (1/2)||ψ-ψ0||².

    ψ0 = e_1 (first basis vector), scaled to psi0_first_axis.
    ψ(0) = ψ0 + perturbation, normalized then scaled to start inside the ball.
    """
    rng = np.random.RandomState(seed)

    psi0 = np.zeros(dim)
    psi0[0] = psi0_first_axis

    psi = psi0 + initial_perturbation * rng.randn(dim)
    n0 = float(np.linalg.norm(psi))
    if n0 > 0:
        psi = psi0 + (initial_perturbation / n0) * (psi - psi0)

    drifts: List[float] = []
    energies_list: List[float] = []

    for k in range(steps):
        d = float(np.linalg.norm(psi - psi0))
        e = energy(psi, psi0)
        drifts.append(d)
        energies_list.append(e)
        if d <= convergence_tol:
            return FlowResult(
                drifts=drifts,
                energies=energies_list,
                final_drift=d,
                converged=True,
                steps=k,
                dim=dim,
                R=R,
                eta=eta,
                seed=seed,
            )
        # Projected gradient step
        psi = psi - eta * (psi - psi0)
        psi = project_ball(psi, psi0, R)

    # Final record
    d = float(np.linalg.norm(psi - psi0))
    drifts.append(d)
    energies_list.append(energy(psi, psi0))
    return FlowResult(
        drifts=drifts,
        energies=energies_list,
        final_drift=d,
        converged=d <= convergence_tol,
        steps=steps,
        dim=dim,
        R=R,
        eta=eta,
        seed=seed,
    )


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Projected gradient flow on F(ψ) = (1/2)||ψ-ψ0||²")
    p.add_argument("--dim", type=int, default=16)
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--R", type=float, default=3.0)
    p.add_argument("--eta", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--perturb", type=float, default=2.5)
    p.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = p.parse_args(argv)

    result = gradient_flow(
        dim=args.dim,
        steps=args.steps,
        R=args.R,
        eta=args.eta,
        seed=args.seed,
        initial_perturbation=args.perturb,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2))
        return 0

    print("== gradient_flow_kernel ==")
    print(f"dim={result.dim}  R={result.R}  eta={result.eta}  seed={result.seed}  steps={result.steps}")
    print(f"final drift = {result.final_drift:.6e}  converged = {result.converged}")
    if result.drifts:
        monotonic = all(result.drifts[i] >= result.drifts[i+1] - 1e-12
                       for i in range(len(result.drifts)-1))
        print(f"drift monotonic non-increasing = {monotonic}")
        print(f"first 5 drifts = {[f'{x:.4f}' for x in result.drifts[:5]]}")
        print(f"last  5 drifts = {[f'{x:.4f}' for x in result.drifts[-5:]]}")
        # Theoretical decay check: at eta small, drift(t) ≈ drift(0) * (1-eta)^t for the unconstrained quadratic
        expected_decay_rate = eta  # for unprojected gradient on F = (1/2)||ψ-ψ0||²
        print(f"expected decay rate per step ≈ {expected_decay_rate}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
