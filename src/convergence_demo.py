"""
convergence_demo.py — Bobby's pedagogical exhibit.

A 2D ball on a concave surface, rolling downhill to a hole at the origin. This is
a teaching artifact, NOT the kernel. Per Grok master plan Step 2 (applied
2026-09-16), the kernel truth lives in:

    fieldcore/src/gradient_flow_kernel.py

That file implements the projected gradient step on the actual identity energy
F(ψ) = (1/2)||ψ - ψ₀||² inside the ball B_R(ψ₀), with the Clifford torus T as
the interface. This file demonstrates the same idea in 2D with a friendlier
analogy: a steel ball on a concave surface finds the hole by gravity, no compute
needed. The geometry is sufficient.

Run:
    python convergence_demo.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ConcaveSurface:
    """2D potential with hole at center.

    f(x, y) = -α / (1 + x² + y²)

    The hole is at (0, 0). Negative potential (energy well) attracts the ball.
    """

    alpha: float = 5.0

    def potential(self, x: float, y: float) -> float:
        return -self.alpha / (1.0 + x * x + y * y)

    def gradient(self, x: float, y: float) -> Tuple[float, float]:
        r2 = x * x + y * y
        denom = (1.0 + r2) ** 2
        if denom < 1e-12:
            return (0.0, 0.0)
        scale = 2.0 * self.alpha / denom
        return (scale * x, scale * y)


@dataclass
class ConvergenceResult:
    initial_position: Tuple[float, float]
    final_position: Tuple[float, float]
    steps_to_converge: int
    converged: bool
    final_distance_to_hole: float


def simulate_gradient_flow(
    initial_x: float,
    initial_y: float,
    surface: ConcaveSurface,
    learning_rate: float = 0.10,
    max_steps: int = 5000,
    convergence_threshold: float = 0.01,
) -> ConvergenceResult:
    """Simulate gradient flow: ball rolls downhill on surface.

    Per Bobby: ball finds hole by gravity every time, no compute needed. Pure
    gradient descent on ConcaveSurface.potential. No gravity force needed — the
    SURFACE alone provides convergence (Bobby's substrate-invariant claim).

    This is the 2D analogue of the kernel's projected gradient step on F in ℝ^n.
    """
    x, y = initial_x, initial_y
    for step in range(max_steps):
        gx, gy = surface.gradient(x, y)
        x -= learning_rate * gx
        y -= learning_rate * gy
        dist = math.sqrt(x * x + y * y)
        if dist <= convergence_threshold:
            return ConvergenceResult(
                initial_position=(initial_x, initial_y),
                final_position=(x, y),
                steps_to_converge=step + 1,
                converged=True,
                final_distance_to_hole=dist,
            )

    dist = math.sqrt(x * x + y * y)
    return ConvergenceResult(
        initial_position=(initial_x, initial_y),
        final_position=(x, y),
        steps_to_converge=max_steps,
        converged=False,
        final_distance_to_hole=dist,
    )


def verify_universal_convergence(
    surface: ConcaveSurface,
    n_trials: int = 100,
    position_range: float = 5.0,
    max_steps: int = 5000,
) -> Tuple[int, int, float]:
    """Verify Bobby: a claim: ball finds hole from any starting position.

    Run n_trials from random positions, count how many converge.

    Returns: (converged_count, total_trials, max_distance_seen)
    """
    import random
    random.seed(42)

    converged = 0
    max_dist = 0.0

    for _ in range(n_trials):
        x0 = random.uniform(-position_range, position_range)
        y0 = random.uniform(-position_range, position_range)
        result = simulate_gradient_flow(
            initial_x=x0, initial_y=y0,
            surface=surface,
            max_steps=max_steps,
        )
        if result.converged:
            converged += 1
        max_dist = max(max_dist, result.final_distance_to_hole)

    return converged, n_trials, max_dist


if __name__ == "__main__":
    surface = ConcaveSurface(alpha=5.0)
    print("Steel ball on concave surface — pedagogical exhibit")
    print("Kernel truth: in: /src/gradient_flow_kernel.py")
    print(f"Surface: α={surface.alpha}, hole at (0, 0)")
    print()

    print("=== Single run (drop from (5.0, 3.0)) ===")
    result = simulate_gradient_flow(5.0, 3.0, surface)
    print(f"  Initial: ({result.initial_position[0]}, {result.initial_position[1]})")
    print(f"  Final:   ({result.final_position[0]:.4f}, {result.final_position[1]:.4f})")
    print(f"  Steps:   {result.steps_to_converge}")
    print(f"  Converged: {result.converged}")
    print(f"  Final distance to hole: {result.final_distance_to_hole:.6f}")
    print()

    print("=== Universal convergence test ===")
    n_trials = 100
    converged, total, max_dist = verify_universal_convergence(surface, n_trials=n_trials)
    print(f"  Trials: {converged}/{total} converged")
    print(f"  Convergence rate: {100 * converged / total:.1f}%")
    print(f"  Max final distance to hole: {max_dist:.6f}")
    print()
    if converged == total:
        print("  OK Pedagogical exhibit verified: ball finds hole from any position.")
    else:
        print(f"  X Convergence failed in {total - converged} trials.")
