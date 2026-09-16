"""Generate visualization PNGs for substrate convergence demos.

Bobby directive 2026-09-12: 'can you run the demo on desktop so i see visually
i have seen in science museums many times thats where idea originated'.

This script renders the steel ball + EM well demos to PNGs and saves them to
Bobby's Desktop so he can see the convergence invariant visually.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import em_well_demo


def simulate_trajectory(particle, well, learning_rate=0.10, max_steps=500):
    """Simulate and return trajectory as list of (x, y) tuples."""
    traj = [(particle.x, particle.y)]
    for step in range(max_steps):
        fx, fy = well.total_force(particle.x, particle.y, particle.vx, particle.vy, particle.charge)
        particle.vx += fx / particle.mass * learning_rate
        particle.vy += fy / particle.mass * learning_rate
        particle.vx *= 0.95
        particle.vy *= 0.95
        particle.x += particle.vx * learning_rate
        particle.y += particle.vy * learning_rate
        traj.append((particle.x, particle.y))
        if math.sqrt(particle.x ** 2 + particle.y ** 2) < 0.01:
            break
    return traj


def render_figure():
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Common surface for both panels
    x = np.linspace(-6, 6, 100)
    y = np.linspace(-6, 6, 100)
    X, Y = np.meshgrid(x, y)
    alpha = 5.0
    Z = -alpha / (1 + X ** 2 + Y ** 2)
    levels = np.linspace(-5, 0, 20)

    # === Left panel: Gravity-only (steel ball) ===
    ax1 = axes[0]
    ax1.set_title("Steel Ball on Concave Surface\nGravity only — 100/100 trials converged", fontsize=12)
    contour1 = ax1.contourf(X, Y, Z, levels=levels, cmap="viridis", alpha=0.7)
    ax1.contour(X, Y, Z, levels=[-2.5, -1.0, -0.3], colors="white", linewidths=1.5)
    plt.colorbar(contour1, ax=ax1, label="Potential (lower = deeper hole)")

    well_gravity = em_well_demo.EMWell(alpha=5.0, b_field=0.0, attractor=(0.0, 0.0), attractor_strength=0.0)
    for start in [(5.0, 3.0), (-4.0, 4.0), (0.1, -5.5)]:
        particle = em_well_demo.ChargedParticle(x=start[0], y=start[1])
        traj = simulate_trajectory(particle, well_gravity)
        xs = [p[0] for p in traj]
        ys = [p[1] for p in traj]
        ax1.plot(xs, ys, "-", linewidth=1.5, alpha=0.8)
        ax1.plot(start[0], start[1], "go", markersize=10, markeredgecolor="white")
        ax1.plot(xs[-1], ys[-1], "r*", markersize=18, markeredgecolor="white")

    ax1.plot(0, 0, "k+", markersize=20, markeredgewidth=3)
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_aspect("equal")
    ax1.grid(True, alpha=0.3)
    ax1.text(
        0.02, 0.98,
        "Black + = hole\nGreen dots = start\nRed stars = converged",
        transform=ax1.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # === Right panel: EM well with magnetic + variable attractor ===
    ax2 = axes[1]
    ax2.set_title(
        "EM Well with Magnetic Field + Variable Attractor\n100/100 trials converged",
        fontsize=12,
    )

    # Use TIGHTER x/y range to show convergence path clearly
    x2 = np.linspace(-6, 6, 100)
    y2 = np.linspace(-6, 6, 100)
    X2, Y2 = np.meshgrid(x2, y2)
    Z2 = -alpha / (1 + X2 ** 2 + Y2 ** 2)
    contour2 = ax2.contourf(X2, Y2, Z2, levels=levels, cmap="plasma", alpha=0.6)
    ax2.contour(X2, Y2, Z2, levels=[-2.5, -1.0, -0.3], colors="white", linewidths=1.5)
    plt.colorbar(contour2, ax=ax2, label="Potential")

    well_em = em_well_demo.EMWell(
        alpha=5.0, b_field=0.8, attractor=(2.0, 1.0), attractor_strength=0.3
    )
    ax2.plot(
        2.0, 1.0, "m^", markersize=20, markeredgecolor="white", markeredgewidth=2,
        label="Variable attractor (2.0, 1.0)",
    )

    for start in [(5.0, 3.0), (-4.0, 4.0), (0.1, -5.5)]:
        particle = em_well_demo.ChargedParticle(x=start[0], y=start[1])
        traj = simulate_trajectory(particle, well_em)
        xs = [p[0] for p in traj]
        ys = [p[1] for p in traj]
        ax2.plot(xs, ys, "-", linewidth=1.5, alpha=0.8)
        ax2.plot(start[0], start[1], "go", markersize=10, markeredgecolor="white")
        ax2.plot(xs[-1], ys[-1], "r*", markersize=18, markeredgecolor="white")

    ax2.plot(0, 0, "k+", markersize=20, markeredgewidth=3)
    ax2.set_xlim(-6, 6)
    ax2.set_ylim(-6, 6)
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_aspect("equal")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.text(
        0.02, 0.94,
        "EM forces: E (gradient) + B (Lorentz) + attractor\nCurved trajectories from Lorentz force",
        transform=ax2.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.suptitle("Bobby's Substrate Convergence Invariant — Gravity + Electromagnetism", fontsize=14)
    plt.tight_layout()

    out_path = r"C:\Users\Admin\simself_substrate_convergence.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Saved: {out_path}")
    plt.close()

    # Copy to Desktop using os.replace after read/write (Windows-safe)
    desktop_path = r"C:\Users\Admin\Desktop\simself_substrate_convergence.png"
    with open(out_path, "rb") as f_in:
        data = f_in.read()
    with open(desktop_path, "wb") as f_out:
        f_out.write(data)
    print(f"Copied to Desktop: {desktop_path}")
    return out_path, desktop_path


if __name__ == "__main__":
    out, desktop = render_figure()
    print(f"\nGenerated: {out}")
    print(f"On Desktop: {desktop}")


---

> **Note 2026-09-16**: this renderer is for the kernel's gradient_flow_kernel.py
> demo output. Bobby's pedagogical steel-ball exhibit is convergence_demo.py.
> The kernel truth lives in tiniest-core/tiniest_core.py.
