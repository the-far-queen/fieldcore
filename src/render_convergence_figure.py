"""
render_convergence_figure.py — render the kernel's gradient_flow_kernel.py
output to PNG.

Bobby's pedagogical steel-ball exhibit is convergence_demo.py. The kernel
truth is in fieldcore/src/tiniest_core/tiniest_core.py, with the projected
gradient step on F(psi) = (1/2)||psi - psi_0||^2.

Note 2026-09-16: this renderer uses matplotlib. If matplotlib is not
installed, the script exits gracefully with a message.
"""
from __future__ import annotations

import os
import sys

try:
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "tiniest_core")))

if MATPLOTLIB_AVAILABLE:
    from tiniest_core import gradient_flow_kernel


def render(out_path="convergence.png", steps=50, R=3.0, eta=0.1, seed=0):
    """Run the kernel, plot the drift decay, save PNG."""
    if not MATPLOTLIB_AVAILABLE or plt is None:
        print("matplotlib not installed; cannot render PNG.")
        return ""
    matplotlib.use("Agg")
    result = gradient_flow_kernel(steps=steps, R=R, eta=eta, seed=seed)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(result.drifts, marker="o", linewidth=1)
    ax.set_xlabel("tick")
    ax.set_ylabel("||psi - psi_0||")
    ax.set_title("Projected gradient flow on F(psi) = (1/2)||psi-psi_0||^2")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print("Wrote " + out_path)
    return out_path


if __name__ == "__main__":
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib not installed; render_convergence_figure.py renders to PNG. Skipping.")
        sys.exit(0)
    render()
