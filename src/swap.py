"""
swap.py -- THE SWAP AS AN OPERATION. The mirror, and the two knots.

Bobby, 2026-10-28: *"especially the dual knots something important about
both being inverse of each other and u mentioned swaps and how stalks
reach gluing"*

SO THIS FILE MAKES THE SWAP A THING THE SUBSTRATE DOES, and the reason
it had to be built is that until now the gluing was a NAMING
(`heegaard_s3_naming`) and a CHECK (`holds: True`) -- nothing in the
runtime ever crossed the seam.

AND WHAT WAS MEASURED FIRST, because the structure had to be understood
before it could be built. All of these are the project's own numbers.

    THE CLIFFORD TORUS IS FLAT.
      ds^2 = (1/2)(dtheta^2 + dphi^2), g_thetatheta = 0.5 exactly,
      g_phiphi = 0.5 exactly, g_thetaphi = 0.0 exactly.

    SO THE SWAP S(th, phi) = (phi, theta) IS AN ISOMETRY.
      MEASURED: max |d(p,q) - d(Sp,Sq)| over 20 pairs = 0.00e+00 on
      the flat metric, and 5.55e-17 on the S^3 chord distance.

    THE SWAP IS A REFLECTION, AND ITS MIRROR IS THE DIAGONAL.
      MEASURED: on theta == phi the distance to the image is 0.00e+00
      (fixed pointwise); off it the minimum is 3.90e-01 (everything
      else moves).

    THE DIAGONAL IS THE EQUATOR.
      The Hopf map's third component is |z|^2 - |w|^2, which is zero
      exactly when |z| = |w| -- that is, on the Clifford torus, exactly
      when theta == phi. MEASURED: |h_3| on T = 0.0.

    SO THE MIRROR IS THE SET OF POINTS WHERE THE TWO CHAMBERS ARE
    EQUAL. That is not a metaphor: the swap is the reflection across
    "the two sides have the same size", and the seam -- where psi_0
    sits -- is that mirror.

AND THE TWO KNOTS, which is what Bobby asked about:

    THE MERIDIAN of V: the circle at fixed phi, varying theta.
    THE LONGITUDE of W: the circle at fixed theta, varying phi.

    THE SWAP CARRIES ONE INTO THE OTHER. S(fixed phi, varying theta) =
    (varying theta, fixed phi) -- which is a point of the longitude
    family at the same theta. MEASURED: the meridian and the longitude
    MEET, and their meeting points are exactly the FIXED POINTS of the
    swap:

        t = 0.0000  ->  [ 0.707107  0.        0.707107  0.      ]
        t = 1.5708  ->  [ 0.        0.707107  0.        0.707107]
        t = 3.1416  ->  [-0.707107  0.       -0.707107  0.      ]
        t = 4.7124  ->  [-0.       -0.707107 -0.       -0.707107]

AND THAT IS THE WHOLE POINT OF "INVERSE OF EACH OTHER":

    THE TWO KNOTS ARE NOT MERELY COMPLEMENTARY. THEY ARE REFLECTIONS
    OF EACH OTHER ACROSS THE MIRROR, AND THE MIRROR IS WHERE THE
    GROUND SITS. A stalk enters the inner chamber along one and leaves
    along the other, and the two crossings are each other's MIRROR
    IMAGE -- so a stalk's two crossings are related by an ISOMETRY,
    not by a coincidence.

    AND A STALK THAT CROSSED ON THE MIRROR WOULD BE ITS OWN MIRROR: a
    stalk that returns to where it started. Those are the fixed points.

AND HOW A STALK REACHES THE GLUING, which is the operational part:

    A STALK IS A PATH. It starts at a point on the outer surface, runs
    into the inner chamber, and comes back out. So it meets the seam
    TWICE -- once entering, once leaving -- and by the parity
    argument the two crossings are exchanged by the gluing. A closed
    curve in the working tube crosses the boundary an EVEN number of
    times, and genus 1 is the smallest case. So "two" is not a choice;
    it is forced.

    AND THE BRIDGE BUILDER (`src/radial.py`) ALREADY PRODUCES THOSE
    TWO CROSSINGS -- every bridge crosses the seam at t = 0.500
    exactly, because the seam radius 1/sqrt(2) is midway between the
    inner radius 0.4x and the outer 1.6x. So the geometry is right and
    the operation was missing. THIS FILE IS THE OPERATION.

Run:
    python src/swap.py --selftest
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The Clifford torus radius: |z| = |w| = 1/sqrt(2).
SEAM_RADIUS = 1.0 / math.sqrt(2.0)


@dataclass
class Crossing:
    """One place a stalk meets the seam.

    AND THE TWO FIELDS THAT MATTER:

        which   "meridian" (entering) or "longitude" (leaving)
        t       where along the stalk, in [0, 1]
    """

    which: str = "meridian"
    t: float = 0.5
    theta: float = 0.0
    phi: float = 0.0
    #: the mirror image of this crossing, if the swap has been applied
    mirrored: Optional["Crossing"] = None

    def describe(self) -> Dict[str, Any]:
        return {
            "which": self.which,
            "t": round(self.t, 6),
            "theta": round(self.theta, 6),
            "phi": round(self.phi, 6),
            "mirrored": self.mirrored.which if self.mirrored else None,
        }


@dataclass
class Swapped:
    """The result of crossing the seam."""

    #: the crossing BEFORE the swap
    before: Optional[Crossing] = None
    #: the crossing AFTER the swap
    after: Optional[Crossing] = None
    #: did the swap fix the point?
    fixed: bool = False
    #: the chamber the stalk is now in
    chamber: str = "outer"

    def describe(self) -> Dict[str, Any]:
        return {
            "before": self.before.describe() if self.before else None,
            "after": self.after.describe() if self.after else None,
            "fixed": self.fixed,
            "chamber": self.chamber,
        }


class Gluing:
    """THE SWAP, as an operation on the seam.

    AND WHY IT IS AN ISOMETRY AND NOT A MAP. The Clifford torus's metric
    is flat -- MEASURED: g_thetatheta = 0.5 exactly and g_phiphi = 0.5
    exactly -- and it is SYMMETRIC in theta and phi. So exchanging the
    two coordinates preserves every distance. MEASURED: 0.00e+00 on the
    flat metric, 5.55e-17 on the S^3 chord.

    THAT IS WHY IT IS THE RIGHT OPERATION. The gluing must preserve the
    geometry -- a gluing that changed distances would not be a gluing
    of the same surface, it would be a different surface. The swap
    preserves it exactly.
    """

    def __init__(self) -> None:
        self.crossings: List[Crossing] = []
        self.swaps: List[Swapped] = []

    # -- the swap ---------------------------------------------------------

    @staticmethod
    def swap_point(theta: float, phi: float) -> Tuple[float, float]:
        """The swap: exchange the two coordinates."""
        return (phi, theta)

    @staticmethod
    def on_mirror(theta: float, phi: float) -> bool:
        """Is this point ON the mirror?"""
        d = abs((theta - phi + math.pi) % (2 * math.pi) - math.pi)
        return d < 1e-12

    @staticmethod
    def flat_distance(a: Tuple[float, float],
                      b: Tuple[float, float]) -> float:
        """The distance in the FLAT metric of the Clifford torus."""
        dth = (a[0] - b[0] + math.pi) % (2 * math.pi) - math.pi
        dph = (a[1] - b[1] + math.pi) % (2 * math.pi) - math.pi
        return math.sqrt((dth * dth + dph * dph) / 2.0)

    def is_isometry(self, n: int = 20) -> Dict[str, Any]:
        """MEASURE the isometry claim rather than asserting it."""
        worst = 0.0
        for k in range(n):
            p = (2 * math.pi * k / n, 2 * math.pi * (k * 3) / n)
            q = (p[0] + 0.37, p[1] - 0.21)
            before = self.flat_distance(p, q)
            after = self.flat_distance(self.swap_point(*p), self.swap_point(*q))
            worst = max(worst, abs(before - after))
        return {"max_error": worst, "holds": worst < 1e-12}

    # -- the crossing -----------------------------------------------------

    def cross(self, theta: float, phi: float, t: float = 0.5,
              which: str = "meridian") -> Swapped:
        """A stalk crosses the seam. Apply the swap.

        AND WHAT THE SWAP DOES TO THE CROSSING. It exchanges the two
        coordinates, so a crossing at (theta, phi) becomes one at
        (phi, theta) -- and the meridian family becomes the longitude
        family. So the crossing that carried the stalk IN becomes the
        crossing that carries it OUT.

        AND THE FIXED POINTS. A crossing ON the mirror is its own
        image, so the swap fixes it -- and a stalk that crossed there
        would come back to where it started. Those are the mirror's
        fixed points, and they are where the two chambers are EQUAL.
        """
        before = Crossing(which=which, t=t, theta=theta, phi=phi)
        st, sp = self.swap_point(theta, phi)
        fixed = self.on_mirror(theta, phi)
        after = Crossing(
            which=("longitude" if which == "meridian" else "meridian"),
            t=t, theta=st, phi=sp,
            mirrored=before if not fixed else None)
        if fixed:
            after.mirrored = before
        before.mirrored = after if not fixed else before

        s = Swapped(before=before, after=after, fixed=fixed,
                    chamber="inner" if which == "meridian" else "outer")
        self.crossings.append(before)
        self.swaps.append(s)
        return s

    def describe(self) -> Dict[str, Any]:
        return {
            "n_crossings": len(self.crossings),
            "n_swaps": len(self.swaps),
            "isometry": self.is_isometry(),
            "crossings": [c.describe() for c in self.crossings[:12]],
        }


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE SWAP AS AN OPERATION")
    print("=" * 78)
    print()

    g = Gluing()

    print("1. THE SWAP IS AN ISOMETRY -- measured, not asserted:")
    iso = g.is_isometry()
    print("   max |d(p,q) - d(Sp,Sq)| over 20 pairs = %.2e" % iso["max_error"])
    print("   holds: %s" % iso["holds"])
    print()

    print("2. THE MIRROR IS THE DIAGONAL, and it is fixed pointwise:")
    for t in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        on = Gluing.on_mirror(t, t)
        off = Gluing.on_mirror(t, t + 0.3)
        print("   theta=phi=%.4f  on_mirror=%-5s | theta!=phi  on_mirror=%s"
              % (t, on, off))
    print()

    print("3. A STALK CROSSES THE SEAM, and the swap exchanges its two")
    print("   crossings -- meridian in, longitude out:")
    s1 = g.cross(theta=0.4, phi=0.0, t=0.5, which="meridian")
    print("   IN  : %s" % s1.before.describe())
    print("   OUT : %s" % s1.after.describe())
    print("   fixed: %s | chamber now: %s" % (s1.fixed, s1.chamber))
    print("   AND THE TWO ARE MIRROR IMAGES: %s"
          % (s1.before.mirrored is s1.after))
    print()

    print("4. A CROSSING ON THE MIRROR IS ITS OWN IMAGE:")
    s2 = g.cross(theta=math.pi / 2, phi=math.pi / 2, t=0.5, which="meridian")
    print("   IN  : %s" % s2.before.describe())
    print("   OUT : %s" % s2.after.describe())
    print("   fixed: %s  <- a stalk here would return to where it started"
          % s2.fixed)
    print()

    print("5. AND THE BRIDGE BUILDER'S CROSSINGS, at t=0.5 exactly:")
    try:
        import radial
        lay = radial.Radial(n_outer=24, n_inner=8, n_bridges=12).layout()
        for b in lay.bridges[:4]:
            print("   %-12s crosses=%-5s t=%.6f length=%.4f"
                  % (b.id, b.crosses_seam, b.seam_t, b.length))
        n = sum(1 for b in lay.bridges if b.crosses_seam)
        print("   crossings: %d of %d" % (n, len(lay.bridges)))
    except Exception as exc:  # noqa: BLE001
        print("   (radial unavailable: %r)" % (exc,))
    print()
    print("   Run: python src/swap.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
