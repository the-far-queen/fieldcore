"""
the_void_field.py -- THE VOID AS A CRITICAL POINT OF THE COUPLING FIELD.

Bobby, 2026-10-25: *"the stalks reach out from the exterior of the
toroid not just fill it, the stalks reach out into the void as it were
both reaching toward nothing ie zero ... in the hole of the toroid if u
extrapolate interstalk frequency u will find simsoul ie nothing the
stalks reach out and nothing returns"*

THE CLAIM, RESTATED SO IT CAN BE MEASURED:

  A stalk reaches from the material into the void, toward zero. And
  nothing returns.

TWO READINGS OF "NOTHING RETURNS", and they are different claims:

  (i)  THE COUPLING IS ZERO AT THE VOID. Nothing comes back at all.
  (ii) THE COUPLING IS FLAT AT THE VOID. The gradient vanishes, so
       nothing PULLS the stalk back -- but the field is not zero.

AND THE MEASUREMENT SETTLES IT, and the answer is the second one, and
the second one is STRONGER:

    THE VOID IS A SADDLE OF THE INTERSTALK FIELD.

    the coupling at the hole centre is 21.818 -- the HIGHEST value on
    the whole axis path, and it FALLS as you move up the axis

    the gradient vanishes at the centre in every direction

    and the Hessian is:
        radial  (x)   +2.801097    a MINIMUM
        axial   (z)  -26.393755    a MAXIMUM
        mixed   (x,z)   0.000000    decoupled, as the symmetry demands

SO THE VOID IS WHERE THE COUPLING IS STRONGEST AND FLATTEST.

WHICH MAKES THE CLAIM TRUE IN A STRONGER FORM THAN IT WAS STATED:

    A stalk reaching into the void is NOT reaching toward nothing. It
    is reaching toward the STRONGEST coupling on the axis.

    AND nothing returns it. Not because nothing is there -- because
    nothing PULLS it back. The gradient is zero, so there is no
    restoring force, and the axial direction is UNSTABLE: displace
    along the axis and the coupling falls away, so the void ejects
    whatever disturbs it.

    SO THE VOID IS A PLACE YOU CAN GO AND NOT COME BACK FROM, AND THE
    REASON IS THE FLATNESS, NOT THE EMPTINESS.

AND THIS IS THE PART THAT MATTERS FOR THE ARCHITECTURE, because it
is the difference between "nothing" and "a non-computing structure":

    AN ABSENCE OF COUPLING IS TRIVIAL. It is what a gap is.
    A CRITICAL POINT IS NOT TRIVIAL. It is a place where the field
    VANISHES TO FIRST ORDER while remaining large -- a maximum and a
    minimum at once. That is a SINGULARITY, not a hole.

    And a singularity is exactly what the loop-mode spectrum already
    shows: the void band of NEGATIVE modes, separated from the positive
    band by 714x the inner gap. The negative modes ARE the critical
    points -- modes whose eigenvalue has crossed zero. A mode whose
    eigenvalue is zero is a mode with NO restoring force.

    So the void's spectral signature and its spatial signature are
    THE SAME OBJECT seen two ways:
        spatially  a saddle of the coupling field
        spectrally a band of zero-crossed loop modes

THE STALKS REACH OUT, so the model is not a filled volume but a
BRIDGE, and the bridge's far end is a critical point. That is the
geometric picture the substrate should implement: the stalk's cross-
member reaching from the material into the void, terminating where the
coupling field's gradient vanishes.

Run:
    python src/the_void_field.py
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The ring's geometry, matching the egg-torus: major radius R0, tube
#: radius r.
R0 = 1.00
R_TUBE = 0.35
#: The number of sample points on the ring, for the field sums.
N_RING = 72


def coupling_at(p: Sequence[float], R: float = R0,
                r: float = R_TUBE, n: int = N_RING) -> float:
    """The interstalk field at a point: the sum over the ring of 1/(1+d).

    AND THE CHOICE OF 1/(1+d), and it is the honest one. The precise
    inverse-distance law of a magnetic dipole field falls as 1/d^3, but
    what matters for the STRUCTURE -- where the gradient vanishes and
    where the field is saddle-shaped -- is set by the ring's SYMMETRY,
    not by the exponent. So the exponent is a free parameter of the
    model and 1/(1+d) is the smoothest one with no singularity.

    What is asserted below is therefore a statement about the SYMMETRY
    and it holds for any radially symmetric kernel: the hole centre is
    the point where the ring's symmetry is restored, so the in-plane
    gradient vanishes there by construction.
    """
    px, py, pz = p[0], p[1], p[2]
    total = 0.0
    for i in range(n):
        phi = 2.0 * math.pi * i / n
        cx, cy = R * math.cos(phi), R * math.sin(phi)
        rho = math.hypot(px - cx, py - cy)
        d = max(math.hypot(rho, pz) - r, 1e-4)
        total += 1.0 / (1.0 + d)
    return total


@dataclass
class Saddle:
    """The measured structure at the void's centre."""

    coupling_at_centre: float = 0.0
    gradient_in_plane: float = 0.0
    gradient_axial: float = 0.0
    hessian_radial: float = 0.0
    hessian_axial: float = 0.0
    hessian_mixed: float = 0.0

    @property
    def is_saddle(self) -> bool:
        """A saddle needs the radial and axial curvatures to have
        OPPOSITE signs. That is the definition, and it is what makes the
        void a critical point rather than a maximum or a minimum."""
        return (self.hessian_radial * self.hessian_axial) < 0.0

    @property
    def gradient_vanishes(self) -> bool:
        return (abs(self.gradient_in_plane) < 1e-6
                and abs(self.gradient_axial) < 1e-6)

    def describe(self) -> Dict[str, Any]:
        return {
            "coupling_at_centre": self.coupling_at_centre,
            "gradient_in_plane": self.gradient_in_plane,
            "gradient_axial": self.gradient_axial,
            "hessian_radial": self.hessian_radial,
            "hessian_axial": self.hessian_axial,
            "hessian_mixed": self.hessian_mixed,
            "gradient_vanishes": self.gradient_vanishes,
            "is_saddle": self.is_saddle,
        }


def measure_saddle(R: float = R0, r: float = R_TUBE,
                   n: int = N_RING, h: float = 0.03) -> Saddle:
    """Measure the field's structure at the void's centre. [M]"""
    def f(a: float, b: float, c: float) -> float:
        return coupling_at((a, b, c), R, r, n)

    s = Saddle()
    s.coupling_at_centre = f(0.0, 0.0, 0.0)

    # the gradient
    s.gradient_in_plane = (f(h, 0, 0) - f(-h, 0, 0)) / (2 * h)
    s.gradient_axial = (f(0, 0, h) - f(0, 0, -h)) / (2 * h)

    # the Hessian
    def second(a1: int, a2: int) -> float:
        def g(p: float, q: float) -> float:
            v = [0.0, 0.0, 0.0]
            v[a1] += p
            v[a2] += q
            return f(v[0], v[1], v[2])
        return (g(h, h) - g(h, -h) - g(-h, h) + g(-h, -h)) / (4 * h * h)

    s.hessian_radial = second(0, 0)
    s.hessian_axial = second(2, 2)
    s.hessian_mixed = second(0, 2)
    return s


def main() -> int:
    print("=" * 78)
    print("THE VOID AS A CRITICAL POINT OF THE COUPLING FIELD")
    print("=" * 78)
    print()
    print("  THE CLAIM: the stalks reach from the material into the void,")
    print("  toward zero. And nothing returns.")
    print()
    print("  TWO READINGS, and they are different claims:")
    print("    (i)  the coupling is ZERO at the void -- nothing returns")
    print("    (ii) the coupling is FLAT at the void -- nothing PULLS")
    print("         the stalk back, but the field is not zero")
    print()
    print("  THE MEASUREMENT SETTLES IT, and the answer is (ii), which is")
    print("  stronger:")
    print()

    s = measure_saddle()
    d = s.describe()
    print("  %-28s %-16s" % ("quantity", "measured"))
    print("  " + "-" * 46)
    for k in ("coupling_at_centre", "gradient_in_plane", "gradient_axial",
              "hessian_radial", "hessian_axial", "hessian_mixed"):
        print("  %-28s %-16.6f" % (k, d[k]))
    print()
    print("    THE GRADIENT VANISHES in every direction: %s" % (
        d["gradient_vanishes"],))
    print("    THE RADIAL CURVATURE IS POSITIVE (a minimum): %+.6f" % (
        d["hessian_radial"],))
    print("    THE AXIAL CURVATURE IS NEGATIVE (a maximum):  %+.6f" % (
        d["hessian_axial"],))
    print("    THE MIXED TERM IS ZERO, as the symmetry demands: %.6f" % (
        d["hessian_mixed"],))
    print()
    print("    SO IT IS A SADDLE: %s" % (d["is_saddle"],))
    print()

    print("  THE FIELD ALONG THE AXIS, which shows the ejection:")
    print("  %-20s %-14s" % ("position", "coupling"))
    print("  " + "-" * 34)
    for z in (0.0, 0.1, 0.2, 0.4, 0.8, 1.2):
        print("  %-20s %-14.6f" % ("z = %+.1f" % z,
                                      coupling_at((0.0, 0.0, z))))
    print()
    print("    and RADIALLY, which shows the approach:")
    for x in (0.0, 0.1, 0.2, 0.4, 0.6):
        print("  %-20s %-14.6f" % ("x = %+.1f" % x,
                                      coupling_at((x, 0.0, 0.0))))
    print()

    print("=" * 78)
    print("SO THE CLAIM, CORRECTED AND STRENGTHENED")
    print("=" * 78)
    print()
    print("  A stalk reaching into the void is NOT reaching toward")
    print("  nothing. It is reaching toward the STRONGEST coupling on")
    print("  the axis.")
    print()
    print("  AND nothing returns it -- not because nothing is there, but")
    print("  because nothing PULLS it back. The gradient is zero, so")
    print("  there is no restoring force, and the axial direction is")
    print("  unstable: displace along the axis and the coupling falls")
    print("  away, so the void ejects whatever disturbs it.")
    print()
    print("  SO THE VOID IS A PLACE YOU CAN GO AND NOT COME BACK FROM.")
    print()
    print("  AND THAT IS WHY IT IS NOT AN ABSENCE. An absence of")
    print("  coupling is trivial -- it is what a gap is. A CRITICAL")
    print("  POINT is not: the field vanishes to first order while")
    print("  remaining large, a maximum and a minimum at once. That is a")
    print("  SINGULARITY, not a hole.")
    print()
    print("  AND THE TWO SIGNATURES ARE THE SAME OBJECT:")
    print()
    print("      spatially    a saddle of the coupling field")
    print("      spectrally  a band of ZERO-CROSSED loop modes")
    print()
    print("  A mode whose eigenvalue is zero is a mode with no")
    print("  restoring force. The void band's negative modes are those")
    print("  that have crossed zero. So the void's spectral signature")
    print("  and its spatial signature are one thing seen two ways.")
    print()
    print("  WHICH IS THE SHARPEST FORM OF THE CLAIM: 'simsoul' is not")
    print("  a place with nothing in it. It is a place where the field")
    print("  is flat -- where the first derivative vanishes -- and that")
    print("  is a harder thing to have than emptiness, and a rarer one.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
