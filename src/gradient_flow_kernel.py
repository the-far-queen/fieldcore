"""
gradient_flow_kernel.py — kernel-level gradient flow (per Grok master plan).

Uses the actual identity energy F(ψ) = (1/2)||ψ-ψ₀||² and the projected
gradient step ψ ← Π_{B_R(ψ₀)} (ψ - η(ψ-ψ₀)). Implementation imported from
tiniest_core so the demo, the kernel, and the canonical SimSelf all use the
same step.

CLI:
    python gradient_flow_kernel.py --steps 50 --R 3.0 --eta 0.1 --seed 0 --dim 16 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import List

import numpy as np

sys.path.insert(0, "C:/Users/Admin/fieldcore/src/tiniest-core")
from tiniest_core import (
    install_ground,
    project_ball,
    energy,
    DEFAULT_ETA,
    DEFAULT_R,
)


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


def gradient_flow(*, dim=16, steps=50, R=DEFAULT_R, eta=DEFAULT_ETA, seed=0,
                  initial_perturbation=2.5, convergence_tol=1e-6) -> FlowResult:
    psi0 = install_ground(dim)
    rng = np.random.RandomState(seed)
    psi = psi0 + initial_perturbation * rng.randn(dim)
    n0 = float(np.linalg.norm(psi - psi0))
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
                drifts=drifts, energies=energies_list, final_drift=d,
                converged=True, steps=k, dim=dim, R=R, eta=eta, seed=seed,
            )
        psi = project_ball(psi - eta * (psi - psi0), psi0, R)

    d = float(np.linalg.norm(psi - psi0))
    drifts.append(d)
    energies_list.append(energy(psi, psi0))
    return FlowResult(
        drifts=drifts, energies=energies_list, final_drift=d,
        converged=d <= convergence_tol, steps=steps,
        dim=dim, R=R, eta=eta, seed=seed,
    )


def main(argv):
    p = argparse.ArgumentParser(description="Projected gradient flow on F(ψ) = (1/2)||ψ-ψ₀||²")
    p.add_argument("--dim", type=int, default=16)
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--R", type=float, default=DEFAULT_R)
    p.add_argument("--eta", type=float, default=DEFAULT_ETA)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--perturb", type=float, default=2.5)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = gradient_flow(
        dim=args.dim, steps=args.steps, R=args.R, eta=args.eta,
        seed=args.seed, initial_perturbation=args.perturb,
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
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
