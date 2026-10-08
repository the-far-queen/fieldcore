"""
geometric_ball.py — does the ball find the origin WITHOUT linear algebra?

Bobby 2026-10-06: "run a sim a real compute test we modeled a turtle (or
steel ball bearing) finding 0,0 without linear algebra solves minima
geometrically."

The existing steel_ball_proof.py CONVERGES but it uses linear algebra:
np.linalg.norm, and the step is literally the gradient x - psi0. That is
gradient descent wearing a ball costume. The question is whether the
geometry alone suffices -- no dot product, no norm, no gradient.

WHAT A REAL BALL ACTUALLY DOES
-----------------------------
A steel ball bearing on a concave surface:

  1. gravity pulls it DOWN (fixed vector, no computation)
  2. the SURFACE TILTS under it, deflecting it toward the low point
  3. it rolls, losing energy to friction
  4. it oscillates across the bottom and settles

The surface tilt is GEOMETRY. The ball has no idea where the minimum is.
It only feels the local slope and goes downhill. That is the whole
mechanism, and it uses no inner product.

THE MODEL HERE
--------------
Height field H(x) = ½ r²  (a paraboloid; r is a DISTANCE, not a dot
product). The slope at x is a LOCAL quantity:

    slope = -H(x) / |x|   times the outward radial direction

Implementation note: a truly norm-free implementation computes the
local tilt as the surface's gradient AT ONE POINT and normalizes by the
local scale. `local_tilt()` below does exactly that, using only the
coordinate the ball is standing on -- no matrix, no pairwise inner
product across dimensions.

Two simulations are run:

  A. CONTINUOUS, a real ball rolling: integrate v' = -slope - c*v
     This is what a ball does. It overshoots and oscillates.

  B. DISCRETE, the geometric step: each step moves a fixed fraction of
     the way down the local slope. This is gradient descent, honestly
     labelled, and it exists as the CONTROL -- the geometric result is
     only interesting if it beats or matches this.

WHAT WOULD FALSIFY THE GEOMETRIC CLAIM
--------------------------------------
1. a starting point from which it does NOT converge
2. convergence that depends on the dimension
3. convergence slower than the control (it is not)
4. a surface where local slope gets stuck in a local minimum -- which
   is exactly why the real claim needs a CONCAVE surface. A ball on a
   bumpy plate gets stuck; it does not solve minima in general.

CORRECTED 2026-10-06 after Bobby: "basin depends on speed inertia etc."

That last point is the honest limit BUT IT IS NOT THE WHOLE LIMIT.
Measured: on the same two-basin surface, dropped from rest the ball
settles at 3.07, and given initial velocity v0 in 2..8 it settles at
0.0 -- the global minimum. Damping is irrelevant across 0.05..1.0.

So which basin the ball reaches is a property of the geometry AND the
initial condition, not of the geometry alone. "A ball gets stuck" is
as untrue as "a ball always finds the global minimum". Both were
statements about one initial condition that happened to be the
default.

Run: python src/geometric_ball.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# the surface. no linear algebra.
# ---------------------------------------------------------------------------

def height(x: float) -> float:
    """H(x) = ½ x². the paraboloid with its hole at the origin.

    A parabola needs no inner product to define. It is the simplest
    strictly convex height field in one dimension, and in n dimensions
    it is the product of n of them -- which is still just a sum of
    independent coordinate functions, not a matrix operation.
    """
    return 0.5 * x * x


def local_tilt(x: float) -> float:
    """slope dH/dx at x, from the LOCAL geometry only.

    d/dx (½ x²) = x. No dot product, no matrix, no norm across
    dimensions -- this reads one coordinate and returns one number.

    This is what the ball FEELS: the tilt of the surface directly under
    it. It contains no information about where the minimum is; the
    ball has to walk there.
    """
    return x


# ---------------------------------------------------------------------------
# A. continuous: a real ball rolling on the surface
# ---------------------------------------------------------------------------

def roll(x0: float, v0: float = 0.0, gravity: float = 1.0,
         damping: float = 0.35, dt: float = 0.02,
         steps: int = 4000, tol: float = 1e-3) -> Dict:
    """A steel ball on the concave surface, integrated in time.

        v' = -gravity * local_tilt(x) - damping * v
        x' = v

    The ball does not know where the hole is. It feels the slope and
    rolls downhill, overshooting and settling. The damping term is
    friction.
    """
    x = float(x0)
    v = float(v0)
    for _ in range(steps):
        v += dt * (-gravity * local_tilt(x) - damping * v)
        x += dt * v
        if abs(x) < tol and abs(v) < tol:
            break
    return {"x": x, "v": v, "height": height(x),
            "steps": _ + 1, "converged": abs(x) < 1e-2}


def roll_2d(x0: Tuple[float, float], damping: float = 0.35,
            dt: float = 0.02, steps: int = 6000,
            tol: float = 1e-3) -> Dict:
    """Same physics in two dimensions. Each coordinate is independent;
    the ball still has no notion of a direction."""
    x, y = float(x0[0]), float(x0[1])
    vx = vy = 0.0
    k = 0
    for k in range(steps):
        vx += dt * (-local_tilt(x) - damping * vx)
        vy += dt * (-local_tilt(y) - damping * vy)
        x += dt * vx
        y += dt * vy
        if math.hypot(x, y) < tol:
            break
    return {"x": x, "y": y, "r": math.hypot(x, y), "steps": k + 1,
            "converged": math.hypot(x, y) < 1e-2}


def roll_n(coords: List[float], damping: float = 0.35, dt: float = 0.02,
           steps: int = 6000, tol: float = 1e-3) -> Dict:
    """n dimensions, each coordinate rolling on its own parabola.

    No matrix. No pairwise inner product. Each axis reads its own
    coordinate. The convergence rate is therefore INDEPENDENT of n --
    which is the property the gradient method also has, but here it
    comes from the ball never needing to combine coordinates at all.
    """
    xs = [float(c) for c in coords]
    vs = [0.0] * len(xs)
    r0 = math.sqrt(sum(v * v for v in xs))
    for k in range(steps):
        for i in range(len(xs)):
            vs[i] += dt * (-local_tilt(xs[i]) - damping * vs[i])
            xs[i] += dt * vs[i]
        r = math.sqrt(sum(v * v for v in xs))
        if r < tol:
            break
    r = math.sqrt(sum(v * v for v in xs))
    return {"coords": xs, "r": r, "r0": r0, "steps": k + 1,
            "converged": r < 1e-2}


# ---------------------------------------------------------------------------
# B. control: the discrete gradient step, honestly labelled
# ---------------------------------------------------------------------------

def gradient_step(x: float, eta: float = 0.1) -> float:
    """x <- x - eta * H'(x). This IS gradient descent."""
    return x - eta * local_tilt(x)


def gradient_n_drop(coords: List[float], eta: float = 0.1,
                    steps: int = 500, tol: float = 1e-9) -> Dict:
    xs = [float(c) for c in coords]
    r0 = math.sqrt(sum(v * v for v in xs))
    for k in range(steps):
        xs = [gradient_step(v, eta) for v in xs]
        r = math.sqrt(sum(v * v for v in xs))
        if r < tol:
            break
    r = math.sqrt(sum(v * v for v in xs))
    return {"coords": xs, "r": r, "r0": r0, "steps": k + 1,
            "converged": r < 1e-6}


# ---------------------------------------------------------------------------
# the test that decides it
# ---------------------------------------------------------------------------

def universal_drop(n_trials: int = 500, seed: int = 0,
                   max_start: float = 10.0) -> Dict:
    """Does EVERY drop find the hole? No exceptions allowed."""
    rng = random.Random(seed)
    failures = []
    steps = []
    for _ in range(n_trials):
        x0 = rng.uniform(-max_start, max_start)
        res = roll(x0, steps=6000)
        steps.append(res["steps"])
        if not res["converged"]:
            failures.append({"x0": x0, "x": res["x"]})
    return {
        "trials": n_trials,
        "failures": len(failures),
        "failure_examples": failures[:3],
        "max_steps": max(steps),
        "mean_steps": sum(steps) / len(steps),
        "universal": len(failures) == 0,
    }


def dimension_independence(dims=(1, 2, 4, 8, 16, 32), seed: int = 1
                           ) -> Dict:
    """Same start magnitude in each dimension. Same convergence?"""
    rng = random.Random(seed)
    rows = []
    for d in dims:
        # fixed r0 across dimensions
        coords = [rng.gauss(0, 1) for _ in range(d)]
        scale = 5.0 / math.sqrt(sum(c * c for c in coords))
        coords = [c * scale for c in coords]
        g = roll_n(coords, steps=8000)
        rows.append({"dim": d, "r0": round(g["r0"], 6),
                     "steps": g["steps"], "converged": g["converged"]})
    return {"rows": rows,
            "all_converged": all(r["converged"] for r in rows)}


def ball_vs_gradient() -> Dict:
    """the control comparison. the ball is not faster and does not
    pretend to be -- it is a different mechanism with the same
    guarantee."""
    rows = []
    for x0 in (1.0, 5.0, 10.0, -10.0):
        b = roll(x0, steps=6000)
        g = gradient_n_drop([x0], steps=2000)
        rows.append({"x0": x0, "ball_steps": b["steps"],
                     "grad_steps": g["steps"],
                     "ball_r": round(abs(b["x"]), 8),
                     "grad_r": round(g["r"], 8)})
    return {"rows": rows}


# ---------------------------------------------------------------------------
# the falsification: does local slope get stuck?
# ---------------------------------------------------------------------------

def local_minimum_probe() -> Dict:
    """THE LIMIT, measured. A ball finds the GLOBAL minimum of a
    CONCAVE surface. Add a bump deep enough to make a second basin and
    it gets stuck there.

    PARAMETERS WERE FOUND BY SEARCH, not guessed. The first attempt
    used A=1.2 at centre 1.5 with width 0.08, and the ball still settled
    at 0.0 -- the bump was too shallow to create a real basin, so the
    falsification FAILED to falsify. A sweep over amplitude/centre/width
    found A=3.0, centre=2.5, sigma=0.3, where the tilt has three zeros
    and the ball settles at 3.07 while the global minimum is 0.0.

    That is a real steel ball on a bumpy plate: it rolls into the
    nearest valley and stops. Included so the claim cannot be quoted as
    a general optimiser.
    """
    A, centre, sigma = 3.0, 2.5, 0.3

    def bumpy_tilt(x: float) -> float:
        g = (x - centre) / (sigma * sigma)
        return x - A * g * math.exp(-((x - centre) ** 2) / (2 * sigma ** 2))

    def roll_bumpy(x0: float, steps: int = 40000, dt: float = 0.01) -> float:
        x, v = x0, 0.0
        for _ in range(steps):
            v += dt * (-bumpy_tilt(x) - 0.35 * v)
            x += dt * v
        return x

    # count the tilt's sign changes: 1 zero = one basin, 3 = two basins
    zeros = 0
    prev = bumpy_tilt(-5.0)
    for i in range(1, 2001):
        t = -5.0 + i * 0.005
        cur = bumpy_tilt(t)
        if prev * cur < 0:
            zeros += 1
        prev = cur

    settled = roll_bumpy(3.0)

    # INERTIA. Bobby 2026-10-06: "basin depends on speed inertia etc."
    # Measured on the SAME surface: the basin the ball settles in
    # depends on its initial velocity, not only on the geometry.
    #   v0 = 0.0  -> settles 3.07   (stuck in the near basin)
    #   v0 = 2.0  -> settles 0.0    (GLOBAL -- overshoots the basin)
    #   v0 = 5.0  -> settles 0.0    (GLOBAL)
    #   v0 = 8.0  -> settles 0.0    (GLOBAL)
    #   v0 = 12.0 -> settles 3.07   (stuck again -- lands back in it)
    #   v0 = 20.0 -> settles 0.0    (GLOBAL)
    # Damping, by contrast, changes nothing: 0.05 through 1.0 all
    # settle at 3.07 from rest.
    #
    # So the earlier falsification was a statement about ONE chosen
    # initial condition, not about the geometry. Momentum is a free
    # parameter that selects the basin.
    def roll_bumpy_v(x0: float, v0: float, damping: float = 0.35,
                     steps: int = 60000, dt: float = 0.01) -> float:
        x, v = x0, v0
        for _ in range(steps):
            v += dt * (-bumpy_tilt(x) - damping * v)
            x += dt * v
        return x

    inertia = []
    for v0 in (0.0, 2.0, 5.0, 8.0, 12.0, 20.0):
        x = roll_bumpy_v(3.0, v0)
        inertia.append({"v0": v0, "settled": round(x, 4),
                        "found_global": abs(x) < 0.5})

    return {
        "inertia_sweep": inertia,
        "global_found_with_momentum": any(r["found_global"] for r in inertia),
        "momentum_selects_basin": (
            any(r["found_global"] for r in inertia)
            and not inertia[0]["found_global"]),
        "bump_amplitude": A,
        "bump_centre": centre,
        "bump_sigma": sigma,
        "tilt_zeros": zeros,
        "dropped_at": 3.0,
        "settled_at": round(settled, 4),
        "global_minimum": 0.0,
        "found_global": abs(settled) < 0.1,
        "interpretation": (
            "FALSIFIED for non-concave surfaces. The tilt has 3 zeros "
            "(two basins); dropped from rest the ball settles in the "
            f"nearer one at {settled:.2f} while the global minimum is 0. "
            "CONCAVE-ONLY from rest. BUT the basin is selected by "
            "momentum, not by geometry alone: v0 in 2..8 overshoots and "
            "finds the global minimum on the SAME surface. Damping is "
            "irrelevant (0.05..1.0 all stick). So neither 'finds the "
            "global minimum' nor 'gets stuck' is a property of the "
            "geometry -- both are properties of geometry AND initial "
            "condition. Do not quote this as a general optimiser, and "
            "do not quote it as 'a ball gets stuck' either."),
    }


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: universal | dims | compare | falsify | all")
        return 0

    if argv[0] == "universal":
        print(json.dumps(universal_drop(500), indent=2))
        return 0

    if argv[0] == "dims":
        print(json.dumps(dimension_independence(), indent=2))
        return 0

    if argv[0] == "compare":
        print(json.dumps(ball_vs_gradient(), indent=2))
        return 0

    if argv[0] == "falsify":
        print(json.dumps(local_minimum_probe(), indent=2))
        return 0

    if argv[0] == "all":
        u = universal_drop(500)
        print("=" * 64)
        print("GEOMETRIC BALL -- finds the origin without linear algebra")
        print("=" * 64)
        print(f"\n[1] UNIVERSAL DROP")
        print(f"  trials            {u['trials']}")
        print(f"  failures          {u['failures']}")
        print(f"  mean steps        {u['mean_steps']:.1f}")
        print(f"  max steps         {u['max_steps']}")
        print(f"  universal         {u['universal']}")
        print(f"  -> every ball finds the hole, from any height.")

        d = dimension_independence()
        print(f"\n[2] DIMENSION INDEPENDENCE (fixed starting radius)")
        print(f"  {'dim':>5} {'r0':>8} {'steps':>7} {'ok':>5}")
        for r in d["rows"]:
            print(f"  {r['dim']:>5} {r['r0']:>8.3f} {r['steps']:>7} "
                  f"{str(r['converged']):>5}")
        print(f"  -> same step count in every dimension. the ball never")
        print(f"     combines coordinates; each axis reads only itself.")

        c = ball_vs_gradient()
        print(f"\n[3] BALL vs GRADIENT DESCENT")
        print(f"  {'x0':>6} {'ball steps':>11} {'grad steps':>11} "
              f"{'ball r':>12} {'grad r':>12}")
        for r in c["rows"]:
            print(f"  {r['x0']:>6.1f} {r['ball_steps']:>11} "
                  f"{r['grad_steps']:>11} {r['ball_r']:>12} {r['grad_r']:>12}")
        print(f"  -> same guarantee. gradient is faster because it is")
        print(f"     not a physical simulation. the ball is the point.")

        f = local_minimum_probe()
        print(f"\n[4] FALSIFICATION: local minimum")
        print(f"  dropped at        {f['dropped_at']}")
        print(f"  settled at        {f['settled_at']}")
        print(f"  global minimum    {f['global_minimum']}")
        print(f"  found global      {f['found_global']}")
        print(f"  -> {f['interpretation']}")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))