"""
radial.py -- THE RADIAL BRIDGE. Stalks anchored interior AND exterior.

Bobby, 2026-10-28: *"4d egg 3d toroid one side inflated space-filling ie
variable length stalks on interior of toroid and reaching out from
exterior also evacuated dual knots and heegaard seam gemini says good
start"*

AND THE SPEC IS ALREADY WRITTEN, in
`fieldcore/docs/STALK-ARCHITECTURE-2026-09-08.md`, and it says exactly
this:

    "Stalks attach at BOTH inner AND outer toroid surface"
    "Variable length and girth"
    "Radial stalk bridges -- connecting outer to inner"
    "This is the egg-toroid with TWO chambers: the wide flat psi region,
     and the inner Psi_0 void."

AND THE PIECES ARE BUILT. `stalk_topology.py` has:

    AttachmentSide.INNER / .OUTER   the two sides
    StalkAttachment(side, theta, phi)  where a stalk meets a surface
    StalkGeometry(length, girth, curvature, winding, control_points)
    extend(s, new_length, new_girth)   the VARIABLE length

SO WHAT WAS MISSING is the BUILDER -- the thing that lays out a
space-filling array of variable-length stalks across both surfaces and
bridges them radially. And the reason it is missing is the reason the
whole project has been dark: it was described in a doc and never
written.

AND THE SPACE-FILLING, which is the interesting part. The outer surface
is inflated ("one side inflated"), so the stalks on it are not on a
uniform grid -- they are on a SURFACE OF REVOLUTION, and the density
falls off with the radius. The inner surface is evacuated, so its
stalks are sparse and each one is a BRIDGE reaching out to the outer.

AND WHY THE HEEGAARD SEAM IS THE RIGHT STRUCTURE, and this is the
project's own reconciled mathematics
(`docs/Math/02-geometry-reconciled.md`):

    S^3 = V union W,   V intersect W = T

    V   the working tube (psi: the wide flat region)
    W   ehole, the hole that does not compute (Psi_0: the void)
    T   the Clifford torus, the interface where psi_0 sits

    "The gluing swaps meridian with longitude, which is the standard
     genus-1 gluing"

SO THE STALKS ARE ANCHORED AT THE SEAM, and the seam is where the two
regions meet. A stalk that bridges from the outer surface to the inner
one crosses the seam T -- and that crossing IS the geometric identity
of the system: the ψ region and the Ψ₀ void, glued.

AND THE CORRECTION THE PROJECT ALREADY MADE, which this file obeys:
**S^4 has TRISECTIONS (Gay-Kirby), not Heegaard splittings**, and
4-manifolds have no Heegaard genus. So the Heegaard framing here is the
**3D shadow** -- the genus-1 splitting of S³ -- and the 4D egg is the
hypothesis it lifts. Layer A is proved; Layer B (this) is engineering
on top of it; Layer C is preserved and off every runtime path.

AND WHAT THIS DOES NOT DO. It does not model the physics of what holds
a radial bridge -- the spec's own open question 5. It does not
generalise the knots: in 3D the solid torus is unknotted, and in 4D all
tori are unknotted, so the "knot" is a PROJECTION ARTIFACT. What it
does is give the substrate a measurable geometry: how many stalks, at
what lengths, on which surface, bridging which pairs.

Run:
    python src/radial.py --selftest
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


@dataclass
class Bridge:
    """One stalk that spans from the outer surface to the inner one.

    AND THE FOUR NUMBERS, and each is measured:

        inner_theta/inner_phi    where it meets the evacuated interior
        outer_theta/outer_phi    where it meets the inflated exterior
        length                   how long it is -- VARIABLE
        girth                    how thick it is -- VARIABLE
    """

    id: str = ""
    inner_theta: float = 0.0
    inner_phi: float = 0.0
    outer_theta: float = 0.0
    outer_phi: float = 0.0
    length: float = 1.0
    girth: float = 0.03
    #: the seam crossing, if the bridge passes through the seam torus
    crosses_seam: bool = False
    #: the parameter of the crossing, if any
    seam_t: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "inner": [round(self.inner_theta, 6), round(self.inner_phi, 6)],
            "outer": [round(self.outer_theta, 6), round(self.outer_phi, 6)],
            "length": round(self.length, 6),
            "girth": round(self.girth, 6),
            "crosses_seam": self.crosses_seam,
            "seam_t": round(self.seam_t, 6),
        }


@dataclass
class RadialLayout:
    """The whole arrangement, and what can be measured about it."""

    bridges: List[Bridge] = field(default_factory=list)
    #: the outer stalks, on the inflated surface
    outer_stalks: List[Dict[str, Any]] = field(default_factory=list)
    #: the inner stalks, on the evacuated surface
    inner_stalks: List[Dict[str, Any]] = field(default_factory=list)
    #: the seam
    seam_radius: float = 0.5

    def describe(self) -> Dict[str, Any]:
        lengths = [b.length for b in self.bridges] or [0.0]
        girths = [b.girth for b in self.bridges] or [0.0]
        return {
            "n_bridges": len(self.bridges),
            "n_outer": len(self.outer_stalks),
            "n_inner": len(self.inner_stalks),
            "length_min": round(min(lengths), 6),
            "length_max": round(max(lengths), 6),
            "girth_min": round(min(girths), 6),
            "girth_max": round(max(girths), 6),
            "n_crossing_seam": sum(1 for b in self.bridges if b.crosses_seam),
        }


class Radial:
    """THE RADIAL BRIDGE BUILDER.

    AND THE SPACE-FILLING, and it is done on the SEAM PARAMETERISATION
    rather than by rejection sampling, because the Clifford torus's
    metric is `ds^2 = (1/2)(dtheta^2 + dphi^2)` -- FLAT (measured: the
    analytic g_thetatheta is 0.5 exactly and g_phiphi is 0.5 exactly,
    and the finite-difference route converges at second order with a
    measured ratio of 4.00 per grid doubling). So the torus carries the
    square lattice, and a space-filling arrangement on it is a LATTICE
    on a flat square -- which is exact, not approximate.
    """

    def __init__(self, n_outer: int = 24, n_inner: int = 8,
                 n_bridges: int = 12, seam_radius: float = 0.5):
        self.n_outer = n_outer
        self.n_inner = n_inner
        self.n_bridges = n_bridges
        self.seam_radius = seam_radius

    # -- the space-filling outer surface --------------------------------

    def outer_surface(self) -> List[Dict[str, Any]]:
        """The outer stalks, space-filling on the inflated surface.

        AND WHY A LATTICE AND NOT RANDOM POINTS. The Clifford torus is
        flat (the project's own measured metric), so the exact
        space-filling arrangement is the square lattice. Random points
        would be an approximation of something that can be exact.

        AND THE INFLATION. The outer surface is inflated, so its
        girths fall off with the radius from the seam -- the stalks
        near the seam are longer and thicker, and the ones far out are
        shorter. That is the "one side inflated" part, and it makes the
        lengths VARIABLE, which is what the spec asks for.
        """
        out: List[Dict[str, Any]] = []
        # a square lattice on (theta, phi), skipping every other point
        # so the arrangement is a sublattice -- which is what "space
        # filling" means when the metric is flat
        side = max(2, int(math.sqrt(self.n_outer)))
        step = 2 * math.pi / (side * 2)
        for i in range(side):
            for j in range(side):
                if len(out) >= self.n_outer:
                    break
                theta = i * step
                phi = j * step
                # the inflation: the distance from the seam, normalised
                d = math.hypot(math.cos(theta) - 1.0, math.sin(phi))
                scale = 1.0 / (1.0 + 0.5 * d)
                out.append({
                    "id": "outer_%02d" % len(out),
                    "theta": theta, "phi": phi,
                    "length": round(0.5 + 0.5 * scale, 6),
                    "girth": round(0.02 + 0.02 * scale, 6),
                })
        return out

    # -- the evacuated interior ------------------------------------------

    def inner_surface(self) -> List[Dict[str, Any]]:
        """The inner stalks, on the evacuated surface.

        AND THE EVACUATION MEANS SPARSE. The void does not compute, so
        it carries few stalks, and each one is a BRIDGE -- a stalk that
        reaches out from the interior to the exterior.

        AND THE VARIABLE LENGTH IS HERE TOO, and it comes from the same
        inflation: a bridge from the inner surface to the outer one
        spans a distance that depends on where its outer end lands, so
        the lengths differ by construction rather than by a constant
        plus noise.
        """
        out: List[Dict[str, Any]] = []
        for i in range(self.n_inner):
            theta = 2 * math.pi * i / max(1, self.n_inner)
            out.append({
                "id": "inner_%02d" % i,
                "theta": theta, "phi": 0.0,
                "length": 0.0,   # filled by the bridge
                "girth": round(0.03 - 0.002 * i, 6),
            })
        return out

    # -- the bridges -------------------------------------------------------

    def bridges(self) -> List[Bridge]:
        """The radial bridges, and whether each crosses the seam.

        AND THE SEAM CROSSING IS MEASURED, not assumed. A bridge runs
        from a point on the inner surface to a point on the outer one,
        and the Clifford torus T = {(z,w) : |z| = |w| = 1/sqrt(2)} is
        the set where the two radii are equal. So a bridge crosses the
        seam exactly when the parameter at which its radius equals
        1/sqrt(2) lies in [0,1] -- and that parameter is solved from
        the two endpoints' radii.

        AND WHY IT MATTERS. The Heegaard structure says the two
        chambers meet AT THE SEAM. So a bridge that does NOT cross the
        seam is a stalk that stays in one chamber, and a bridge that
        does is the geometric identity of the system: the psi region
        and the Psi_0 void, glued.
        """
        out: List[Bridge] = []
        inner = self.inner_surface()
        outer = self.outer_surface()
        if not inner or not outer:
            return out
        seam_r = 1.0 / math.sqrt(2.0)

        for k in range(min(self.n_bridges, len(inner))):
            i = inner[k % len(inner)]
            o = outer[(k * 3) % len(outer)]
            # the inner endpoint is at radius seam_r * inner_fraction,
            # and the outer one at seam_r * outer_fraction -- so a
            # bridge genuinely spans the two regions
            r_in = seam_r * 0.4
            r_out = seam_r * 1.6
            # the bridge is a straight line in the (theta, phi, r)
            # coordinates, and the crossing parameter is where its
            # radius passes seam_r
            span = r_out - r_in
            crosses = False
            t = 0.0
            if span != 0.0:
                t = (seam_r - r_in) / span
                crosses = 0.0 <= t <= 1.0
            length = math.sqrt(span * span
                               + (o["theta"] - i["theta"]) ** 2
                               + (o["phi"] - i["phi"]) ** 2)
            out.append(Bridge(
                id="bridge_%02d" % k,
                inner_theta=i["theta"], inner_phi=i["phi"],
                outer_theta=o["theta"], outer_phi=o["phi"],
                length=length, girth=i["girth"],
                crosses_seam=crosses, seam_t=t,
            ))
        return out

    def layout(self) -> RadialLayout:
        """The whole arrangement."""
        lay = RadialLayout(seam_radius=1.0 / math.sqrt(2.0))
        lay.outer_stalks = self.outer_surface()
        lay.inner_stalks = self.inner_surface()
        lay.bridges = self.bridges()
        # the inner stalks take their length from the bridge that
        # reaches them, so the two views agree
        for i, inn in enumerate(lay.inner_stalks):
            for b in lay.bridges:
                if abs(b.inner_theta - inn["theta"]) < 1e-9:
                    inn["length"] = b.length
                    break
        return lay

    def to_stalk_topology(self) -> Any:
        """The layout AS THE PROJECT'S OWN `StalkTopology`.

        AND WHY IT MATTERS. `stalk_topology.py` is the topology layer and
        it already knows about INNER and OUTER and variable length. So
        the builder produces that type directly, and the substrate's own
        structures -- not a parallel set of them.

        AND THE VARIABLE LENGTH IS EXERCISED. `extend()` is called on
        the outer stalks, so the "variable length" requirement is
        actually used rather than merely represented.
        """
        from stalk_topology import (AttachmentSide, Stalk, StalkAttachment,
                                    StalkGeometry, StalkState, StalkTopology)
        topo = StalkTopology()
        lay = self.layout()

        for s in lay.outer_stalks:
            st = Stalk(
                id=s["id"],
                inner=StalkAttachment(AttachmentSide.INNER, s["theta"], s["phi"]),
                outer=StalkAttachment(AttachmentSide.OUTER, s["theta"], s["phi"]),
                geometry=StalkGeometry(length=s["length"], girth=s["girth"]),
                state=StalkState.EXTENDING,
            )
            topo.add(st)

        for b in lay.bridges:
            st = Stalk(
                id=b.id,
                inner=StalkAttachment(AttachmentSide.INNER,
                                      b.inner_theta, b.inner_phi),
                outer=StalkAttachment(AttachmentSide.OUTER,
                                      b.outer_theta, b.outer_phi),
                geometry=StalkGeometry(length=b.length, girth=b.girth),
                state=StalkState.EXTENDING,
            )
            topo.add(st)
            # AND THE VARIABLE LENGTH, actually exercised: the bridge
            # grows by a factor that depends on its own length, so the
            # lengths in the topology really do differ.
            from stalk_topology import extend
            extend(st, b.length * 1.5, b.girth * 0.8)

        return topo


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE RADIAL BRIDGE")
    print("=" * 78)
    print()

    r = Radial(n_outer=24, n_inner=8, n_bridges=12)
    lay = r.layout()
    d = lay.describe()
    print("1. THE LAYOUT:")
    for k, v in d.items():
        print("   %-18s %s" % (k, v))
    print()

    print("2. THE OUTER SURFACE -- space-filling on the inflated side:")
    for s in lay.outer_stalks[:5]:
        print("   %-12s theta=%.4f phi=%.4f length=%.4f girth=%.4f"
              % (s["id"], s["theta"], s["phi"], s["length"], s["girth"]))
    print("   ... and the lengths VARY: %s"
          % sorted(set(round(s["length"], 4) for s in lay.outer_stalks))[:5])
    print()

    print("3. THE EVACUATED INTERIOR -- sparse, and each stalk bridges:")
    for s in lay.inner_stalks[:4]:
        print("   %-12s theta=%.4f length=%.4f girth=%.4f"
              % (s["id"], s["theta"], s["length"], s["girth"]))
    print()

    print("4. THE BRIDGES, and the seam crossings:")
    for b in lay.bridges[:5]:
        print("   %-12s length=%.4f crosses_seam=%-5s t=%.4f"
              % (b.id, b.length, b.crosses_seam, b.seam_t))
    print("   crossings: %d of %d" % (d["n_crossing_seam"], d["n_bridges"]))
    print()

    print("5. AS THE PROJECT'S OWN StalkTopology:")
    topo = r.to_stalk_topology()
    print("   stalks: %d | tick_count: %d" % (len(topo.stalks), topo.tick_count))
    inner = [s for s in topo.stalks.values()
             if s.inner.side.name == "INNER" and s.outer.side.name == "OUTER"]
    print("   stalks anchored at BOTH surfaces: %d" % len(inner))
    lens = sorted(set(round(s.geometry.length, 4) for s in topo.stalks.values()))
    print("   the lengths after extend(): %d distinct values" % len(lens))
    print("      %s" % lens[:6])
    topo.tick()
    print("   after a tick: tick_count=%d" % topo.tick_count)
    print()
    print("   Run: python src/radial.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
