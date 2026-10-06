"""
basin_landscape.py — a landscape of bumps and basins, and which one the
ball actually reaches.

Bobby 2026-10-06: "add bumps and basins", after "basin depends on
speed inertia etc."

WHY THIS EXISTS
---------------
geometric_ball.py has ONE bump and found that the basin depends on
initial momentum. That is a fact about one surface. It does not tell
you:

  - whether a bump field has many basins or one
  - whether momentum reliably escapes them, or just escapes this one
  - what happens with several bumps of different depth and width
  - whether a shallow wide basin captures differently from a deep
    narrow one

So this builds a configurable height field from a LIST of bumps and
measures, rather than asserting:

    H(x) = ½x²  +  sum_i  A_i * exp(-((x - c_i)² / 2σ_i²))

The paraboloid is the base (globally concave, unique minimum at 0). Each
bump carves a potential side-basin. Everything the ball does after that
is decided by the bumps, and the ball is integrated with real inertia,
damping, and gravity so the result is a physical trajectory rather than
a descent rule.

WHAT IS MEASURED, NOT ASSUMED
-----------------------------
1. how many basins the surface actually has (tilt sign changes)
2. which basin the ball lands in, from rest and from several speeds
3. whether faster is better -- measured, not assumed, because the
   one-bump case was NON-MONOTONE: v0=8 escaped, v0=12 did not
4. the escape fraction across many speeds and many surfaces

Run: python src/basin_landscape.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Bump:
    """One Gaussian bump on the paraboloid base."""
    centre: float
    amplitude: float
    sigma: float = 0.3

    def tilt(self, x: float) -> float:
        """d/dx of A exp(-((x-c)^2 / 2 sigma^2))"""
        g = (x - self.centre) / (self.sigma * self.sigma)
        return -self.amplitude * g * math.exp(
            -((x - self.centre) ** 2) / (2 * self.sigma ** 2))

    def value(self, x: float) -> float:
        return self.amplitude * math.exp(
            -((x - self.centre) ** 2) / (2 * self.sigma ** 2))

    def curvature(self, x: float) -> float:
        """d2/dx2 of the Gaussian bump.

        An earlier version of the probe function bound x incorrectly and
        returned an identical value at every point, which made five
        distinct roots look identical. A number that never varies is a
        number that cannot be trusted.
        """
        u = (x - self.centre) / self.sigma
        return (self.amplitude / (self.sigma ** 2)) * (u * u - 1.0) * math.exp(
            -(u * u) / 2.0)


class Landscape:
    """Base paraboloid plus a list of bumps."""

    def __init__(self, bumps: Sequence[Bump] = (), origin: float = 0.0):
        self.bumps = list(bumps)
        self.origin = origin

    def height(self, x: float) -> float:
        return 0.5 * (x - self.origin) ** 2 + sum(b.value(x) for b in self.bumps)

    def tilt(self, x: float) -> float:
        """the slope the ball feels at x -- local geometry only"""
        return (x - self.origin) + sum(b.tilt(x) for b in self.bumps)

    def curvature(self, x: float) -> float:
        """H''(x). Positive at a minimum, negative at a maximum."""
        return 1.0 + sum(b.curvature(x) for b in self.bumps)

    def curvature_matches_finite_difference(self, tol: float = 1e-4) -> bool:
        """H'' must equal the finite-difference derivative of the tilt.

        THIS IS THE SELF-CHECK. Two detectors in this file were wrong in
        ways that were stable across every resolution and raised nothing.
        The one thing that catches that is an independent method: if the
        analytic curvature and a finite difference of the tilt disagree,
        the analytic expression is wrong, full stop.
        """
        h = 1e-5
        for x in (-6.0, -3.0, -1.0, 0.05, 2.0, 5.0, 8.0):
            fd = (self.tilt(x + h) - self.tilt(x - h)) / (2 * h)
            if abs(fd - self.curvature(x)) > tol:
                return False
        return True

    def basin_count(self, lo: float = -12.0, hi: float = 12.0,
                    steps: int = 24000) -> int:
        """number of sign changes in the tilt = number of basins.

        A smooth landscape with m local minima has m+1 sign changes.
        """
        zeros = 0
        prev = self.tilt(lo)
        for i in range(1, steps + 1):
            x = lo + (hi - lo) * i / steps
            cur = self.tilt(x)
            if prev == 0.0:
                zeros += 1
            elif prev * cur < 0:
                zeros += 1
            prev = cur
        return zeros

    def extrema(self, lo: float = -12.0, hi: float = 12.0,
                steps: int = 96000) -> Tuple[List[float], List[float]]:
        """bracketed minima and maxima, classified by H''.

        The previous version classified by TILT SIGN DIRECTION, which
        is only valid when bumps do not overlap. With overlapping bumps
        the tilt can cross - to + at what is genuinely a minimum, so the
        labels inverted and the counts disagreed at every resolution.

        Ground truth is H'' > 0 for a minimum. The sign-change scan only
        finds CANDIDATES; the curvature decides what they are.
        """
        mins: List[float] = []
        maxs: List[float] = []
        x_prev = lo
        t_prev = self.tilt(lo)
        for i in range(1, steps + 1):
            x = lo + (hi - lo) * i / steps
            t = self.tilt(x)
            if t * t_prev < 0:
                mid = 0.5 * (x_prev + x)
                # refine with a few bisection steps
                a, b = x_prev, x
                for _ in range(40):
                    m = 0.5 * (a + b)
                    if self.tilt(a) * self.tilt(m) <= 0:
                        b = m
                    else:
                        a = m
                root = 0.5 * (a + b)
                (mins if self.curvature(root) > 0 else maxs).append(
                    round(root, 4))
            x_prev, t_prev = x, t
        return sorted(mins), sorted(maxs)

    def minima(self, **kw) -> List[float]:
        return self.extrema(**kw)[0]

    def maxima(self, **kw) -> List[float]:
        return self.extrema(**kw)[1]

    def structure_is_consistent(self) -> bool:
        """In 1D extrema alternate, so a landscape starting below its
        central minimum has one MORE minimum than maximum.

        `minima == maxima + 1` is the invariant. An earlier detector
        returned 4 minima and 5 maxima, which violates it -- that is
        how the mislabeling was caught.
        """
        m, M = self.minima(), self.maxima()
        return len(m) == len(M) + 1

    def to_dict(self) -> Dict:
        return {
            "origin": self.origin,
            "bumps": [asdict(b) for b in self.bumps],
            "tilt_sign_changes": self.basin_count(),
            "minima": self.minima(),
            "maxima": self.maxima(),
            "structure_consistent": self.structure_is_consistent(),
            "curvature_verified": self.curvature_matches_finite_difference(),
        }


# ---------------------------------------------------------------------------
# the ball, with real inertia
# ---------------------------------------------------------------------------

def drop(land: Landscape, x0: float, v0: float = 0.0, gravity: float = 1.0,
         damping: float = 0.35, dt: float = 0.01,
         steps: int = 200000, tol: float = 1e-4) -> Dict:
    """Integrate  v' = -gravity*tilt(x) - damping*v ,  x' = v.

    Real dynamics: the ball carries momentum, overshoots, and settles.
    Which basin it ends in is an outcome, not an input.
    """
    x, v = float(x0), float(v0)
    k = 0
    for k in range(steps):
        v += dt * (-gravity * land.tilt(x) - damping * v)
        x += dt * v
        if abs(v) < tol and abs(land.tilt(x)) < tol:
            break
    return {"settled": round(x, 4), "v": v, "steps": k + 1,
            "nearest_minimum": _nearest(land, x)}


def _nearest(land: Landscape, x: float) -> Optional[float]:
    mins = land.minima()
    return min(mins, key=lambda m: abs(m - x)) if mins else None


def escape_fraction(land: Landscape, x0: float,
                    speeds: Sequence[float] = (0, 1, 2, 4, 6, 8, 12, 16, 20, 30),
                    damping: float = 0.35) -> Dict:
    """over a range of initial speeds, what fraction reach the GLOBAL
    basin? measured, because the one-bump case was non-monotone."""
    global_m = min(land.minima(), key=abs) if land.minima() else 0.0
    rows = []
    hits = 0
    for v0 in speeds:
        r = drop(land, x0, v0, damping=damping)
        ok = r["nearest_minimum"] is not None and \
            abs(r["nearest_minimum"] - global_m) < 0.05
        hits += 1 if ok else 0
        rows.append({"v0": v0, "settled": r["settled"],
                     "basin": r["nearest_minimum"], "found_global": ok})
    return {"speeds": rows, "hits": hits, "trials": len(speeds),
            "fraction": hits / max(len(speeds), 1)}


# ---------------------------------------------------------------------------
# presets: surfaces worth comparing
# ---------------------------------------------------------------------------

def one_bump() -> Landscape:
    """the case already measured: A=3.0, c=2.5, sigma=0.3"""
    return Landscape([Bump(centre=2.5, amplitude=3.0, sigma=0.3)])


def many_bumps() -> Landscape:
    """a chain of nine bumps of varying depth and width"""
    return Landscape([
        Bump(-4.0, 1.0, 0.5), Bump(-3.0, 2.5, 0.3),
        Bump(-2.0, 0.8, 0.8), Bump(-1.0, 3.5, 0.25),
        Bump(1.0, 3.5, 0.25), Bump(2.0, 2.5, 0.3),
        Bump(3.0, 1.5, 0.6), Bump(4.0, 0.6, 1.0),
        Bump(5.5, 2.0, 0.4),
    ])


def deep_narrow_vs_shallow_wide() -> Landscape:
    """a deep narrow basin beside a shallow wide one"""
    return Landscape([
        Bump(1.2, 4.0, 0.15),    # deep, narrow
        Bump(4.0, 1.0, 1.2),     # shallow, wide
    ])


def random_landscape(seed: int = 0, n: int = 6) -> Landscape:
    rng = random.Random(seed)
    bumps = []
    for _ in range(n):
        bumps.append(Bump(
            centre=rng.uniform(-5, 5),
            amplitude=rng.uniform(0.4, 4.0),
            sigma=rng.uniform(0.2, 1.0),
        ))
    return Landscape(bumps)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def report(land: Landscape, x0: float, name: str) -> Dict:
    info = land.to_dict()
    esc = escape_fraction(land, x0)
    return {"name": name, "surface": info,
            "dropped_at": x0, "escape": esc}


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: surfaces | escape | monotone | all")
        return 0

    if argv[0] == "surfaces":
        for land, name in ((one_bump(), "one bump"),
                           (deep_narrow_vs_shallow_wide(), "deep vs shallow"),
                           (many_bumps(), "nine bumps"),
                           (random_landscape(0), "random seed 0")):
            d = land.to_dict()
            print(f"\n{name}:")
            print(f"  tilt sign changes : {d['tilt_sign_changes']}")
            print(f"  local minima      : {d['minima']}")
        return 0

    if argv[0] == "escape":
        for land, name, x0 in ((one_bump(), "one bump", 3.0),
                               (deep_narrow_vs_shallow_wide(), "deep vs shallow", 1.2),
                               (many_bumps(), "nine bumps", 5.5)):
            r = report(land, x0, name)
            print(f"\n{name}  (dropped at {x0})")
            print(f"  basins: {r['surface']['minima']}")
            print(f"  {'v0':>5} {'settled':>9} {'basin':>9}  outcome")
            for row in r["escape"]["speeds"]:
                print(f"  {row['v0']:>5} {row['settled']:>9} "
                      f"{str(row['basin']):>9}  "
                      f"{'GLOBAL' if row['found_global'] else 'stuck'}")
            print(f"  escape fraction {r['escape']['hits']}/"
                  f"{r['escape']['trials']} = {r['escape']['fraction']:.2f}")
        return 0

    if argv[0] == "monotone":
        print("IS 'FASTER IS BETTER' TRUE? measured, not assumed.")
        print("the one-bump case was non-monotone: v0=8 escaped,")
        print("v0=12 did not.\n")
        for land, name, x0 in ((one_bump(), "one bump", 3.0),
                               (deep_narrow_vs_shallow_wide(), "deep vs shallow", 1.2),
                               (many_bumps(), "nine bumps", 5.5)):
            e = escape_fraction(land, x0)
            flags = ["G" if r["found_global"] else "." for r in e["speeds"]]
            print(f"  {name:16} speeds {e['speeds'][0]['v0']}.."
                  f"{e['speeds'][-1]['v0']}  {''.join(flags)}  "
                  f"({e['fraction']*100:.0f}% global)")
        print("\n  G = reached the global basin, . = trapped in another")
        print("  non-monotone patterns (G...G.G) mean speed is not a")
        print("  monotone escape parameter. the ball lands in whichever")
        print("  basin it happens to arrive at.")
        return 0

    if argv[0] == "all":
        return _main(["surfaces"]) and _main(["monotone"]) or 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))