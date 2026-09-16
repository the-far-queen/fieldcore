"""
modal_field_core.py — substrate primitive wrapper (per Grok master plan, full rewrite 2026-09-16).

The previous version of this file claimed Hodge-ish control and built a
private metric. Per Grok (segment 02, applied 2026-09-16): "src/modal_field_core.py
must either integrate that metric or stop saying it does." This rewrite
integrates the kernel's projected gradient step and stops claiming Hodge.

The substrate primitive is the projected gradient step on
F(ψ) = (1/2) ||ψ - ψ₀||², implemented in tiniest_core. This module is a
thin wrapper that exposes the substrate operation as a single function.
"""

from __future__ import annotations

import numpy as np

from .tiniest_core.tiniest_core import (
    install_ground,
    project_ball,
    step,
    energy,
    DEFAULT_R,
    DEFAULT_ETA,
)


def substrate_step(psi: np.ndarray, psi0: np.ndarray,
                   eta: float = DEFAULT_ETA,
                   R: float = DEFAULT_R) -> np.ndarray:
    """One substrate step: the projected gradient step on F."""
    return step(psi, psi0, eta=eta, R=R)


def substrate_energy(psi: np.ndarray, psi0: np.ndarray) -> float:
    """F(ψ) = (1/2) ||ψ - ψ₀||²."""
    return energy(psi, psi0)


def substrate_install(dim: int = 16) -> np.ndarray:
    """Install ground as a unit vector in ℝ^dim."""
    return install_ground(dim)


if __name__ == "__main__":
    psi0 = substrate_install(16)
    psi = psi0 + 2.5 * np.random.RandomState(0).randn(16)
    for _ in range(20):
        psi = substrate_step(psi, psi0)
    print(f"final drift: {np.linalg.norm(psi - psi0):.6f}")
