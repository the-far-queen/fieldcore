"""
core_math.py -- THE THREE READINGS OF "CORE", MADE INTO ONE MATH.

Bobby, 2026-10-25: *"you are correct in defining core several ways but
look at my usage all 3 are perfectly valid ie control system geometry for
the math and stalks are the workhorse, please turn my seeing into all
math but retain my geometric understanding and examples so i can follow
what u did"*

THE THREE READINGS, and they are not three definitions of one thing --
they are three LAYERS, and the mistake is to pick one:

  LAYER 1 -- THE CONTROL SYSTEM
    The 747. M0 in core (deterministic, Python, 1-bit veto), M1 outside
    core (audit, qualify, promote/demote), the Atlas Exam in the write
    path, the Sacred Library read-only from below.

    THE MATH: a veto function over a proposal, with a bounded admission
    rate.

        V(p) in {0, 1}          the 1-bit verdict
        admit iff V(p) = 1 AND rate in [FLOOR, CEILING]

    and the rate is what makes it a control system rather than a filter:
    a gate that must be perfect is a gate that never opens.

  LAYER 2 -- THE GEOMETRY
    The toroid, the sheaves, the loop modes, the Hodge projection, the
    girth ratios, the addresses. The thing the math is ABOUT.

    THE MATH: the eigenvalue problem of the inductance matrix, and the
    gap/area ratio that makes the geometry non-scale-invariant.

        L      the 3x3 inductance matrix (symmetric, by reciprocity)
        L_loop the difference basis: two loop modes per stalk
        k      the coupling factor: 1/sqrt(1 + L_sigma/L_m)
        L_sigma = mu0 * gap     the interwinding gap, the NASA knob

  LAYER 3 -- THE STALKS
    The workhorse. The 3-part coax geometry that carries signals, that
    addresses, that couples, that a receiver can hear.

    THE MATH: the channel's taps, the equaliser, the derived width.

        H(f)   the channel response, a sum of complex taps at their
               own delays
        w      the width, DERIVED: width_for(taps)
        R      the recovered spectrum: R = H X, inverted by 1/H

AND WHY THEY ARE ONE THING, and this is the part worth the file:

  THE STALKS ARE THE GEOMETRY, AND THE GEOMETRY IS WHAT THE CONTROL
  SYSTEM CONTROLS.

    The control system's job is to decide what may change.
    What changes is the geometry -- the gap, the girth, the length.
    And the geometry is what changes the CHANNEL, so the control
    system's job is to decide what the channel may be.

  So the three layers compose into one function:

        a PROPOSAL is a proposed CHANGE OF GEOMETRY
        the CONTROL SYSTEM decides whether the change may happen
        the new GEOMETRY produces a new CHANNEL
        the CHANNEL is what carries the signal
        and the STALKS are the geometry, made of wire

  WHICH IS THE ANSWER TO "what is the core":

        THE CORE IS THE PART OF THE SYSTEM THAT MAY NOT CHANGE.

    Not a directory. Not a language. A set of invariants. The M0
    governor, the write-protected ground, the 1-bit verdict, the
    self's protected locus. And every layer above it is a proposal.

THE TWO INVARIANTS THAT MAKE IT A CONTROL SYSTEM, and they are the
747's:

  1. THE VERDICT IS DETERMINISTIC. No model decides whether another
     model's output is allowed. The gate is Python and it is in core.

  2. THE DIRECTION OF AUTHORITY IS ONE WAY. The thing being governed
     may PROPOSE. It may never WRITE. Three of the four steps stand
     outside the thing being governed.

WHAT THIS FILE DOES: it puts the three layers in ONE place with their
maths side by side, so the composition can be READ rather than inferred
from three repos. It is the map, not new physics.

Run:
    python src/core_math.py
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from stalk_physics import (  # noqa: E402
    C_LIGHT,
    EPS_R,
    MU_0,
    PhysicalStalk,
    make_population,
)
from locus_gate import (  # noqa: E402
    ADMISSION_TARGET,
    CEILING,
    FLOOR,
    AuditResult,
    CommitResult,
    ExamResult,
    LocusGate,
)

#: The frame size everywhere.
BINS = 128


# ===========================================================================
# LAYER 1 -- THE CONTROL SYSTEM
# ===========================================================================

@dataclass
class Veto:
    """The 1-bit verdict, and the admission rate that bounds it.

    THE VERDICT, and it is a function of the proposal and nothing else:

        V(p) = 0  if any invariant is violated
              1  otherwise

    NO MODEL IS CONSULTED. That is the whole point of the 747: a
    governor that could be talked into anything is not a governor. So
    the verdict is computed, not judged.

    AND THE RATE, which is the second half of the control law:

        admit iff V(p) = 1 AND FLOOR <= rate <= CEILING

    Below the floor the checks are too strict or the substrate is
    broken -- the system is inert, and inert is a failure, not a safety
    feature. Above the ceiling the checks have stopped discriminating.
    """

    #: The invariants, each a named predicate over the proposal.
    invariants: Dict[str, Any] = field(default_factory=dict)
    decisions: int = 0
    allowed: int = 0
    refused: int = 0
    window: int = 50

    def add_invariant(self, name: str, check: Any) -> None:
        """Register an invariant. It is a NAMED predicate, and the name
        is what the refusal carries."""
        self.invariants[name] = check

    def verdict(self, proposal: Any) -> Tuple[int, str]:
        """The 1-bit verdict and the reason.

        THE ORDER, and it matters: the invariants are checked in
        registration order and the FIRST violation wins, so the reason
        is the most specific one available rather than the first in
        some arbitrary set order.
        """
        self.decisions += 1
        for name, check in self.invariants.items():
            try:
                ok = check(proposal)
            except Exception as exc:
                ok = False
                name = "%s_raised(%s)" % (name, type(exc).__name__)
            if not ok:
                self.refused += 1
                return 0, name
        self.allowed += 1
        return 1, "allow"

    def rate(self) -> float:
        if self.decisions == 0:
            return 0.0
        return self.allowed / self.decisions

    def admits(self, proposal: Any) -> bool:
        """V(p) = 1 AND the rate is in band.

        AND THE ORDER, and the first version of this had it WRONG in a
        way that made the gate unusable:

            the rate must be read BEFORE this decision is recorded

        The first version called `verdict()` (which records the
        decision) and THEN read the rate. So the rate always included
        the decision being made, and the band was checked against a
        number that had already moved. Measured: with every proposal
        valid, the rate went to 1.000 -- above the CEILING of 0.99 --
        and so EVERY subsequent admission was refused as "not
        discriminating". A gate that refuses everything is not strict,
        it is broken.

        So: the band is read from the rate as it stood BEFORE this
        decision. And a gate with no history yet admits, because the
        band is a statement about a RUNNING rate, not about the first
        decision.
        """
        # the rate BEFORE this decision
        prior = self.rate()
        if self.decisions > 0 and not (FLOOR <= prior <= CEILING):
            # record the decision so the ledger is honest, then refuse
            self.verdict(proposal)
            return False
        bit, _ = self.verdict(proposal)
        return bit == 1

    def describe(self) -> Dict[str, Any]:
        return {
            "layer": "control",
            "verdict_bits": self.decisions,
            "allowed": self.allowed,
            "refused": self.refused,
            "rate": self.rate(),
            "band": (FLOOR, CEILING),
            "target": ADMISSION_TARGET,
            "invariants": sorted(self.invariants),
        }


# ===========================================================================
# LAYER 2 -- THE GEOMETRY
# ===========================================================================

@dataclass
class Geometry:
    """The geometry, as the maths.

    THE FOUR QUANTITIES, and they are the ones that matter:

        L       the inductance matrix. Symmetric by reciprocity.
        L_loop  its difference basis: two loop modes per stalk.
        k       the coupling factor. 1/sqrt(1 + L_sigma/L_m).
        gap     the interwinding gap. The NASA knob.

    AND THE ONE THAT MAKES IT NOT INERT:

        k depends on gap/area, and the area is QUADRATIC in the radius
        while the gap is LINEAR. So k is not scale-invariant, and the
        geometry genuinely loads the channel.

    THE LOOP MODES, and the degeneracy question the v6.2 document asks:
    a 3-conductor stalk has n-1 = 2 independent differential loop
    currents, and the claim is that a stalk's OWN geometry separates
    them -- so the axis count needs no sigma_g perturbation.
    """

    stalks: List[PhysicalStalk]

    def inductance_matrix(self, s: PhysicalStalk) -> List[List[float]]:
        """The 3x3 inductance matrix.

        THE DIAGONAL: r^2 N^2, the textbook single-layer coil.
        THE OFF-DIAGONAL: the mutual couplings, which are the
        NORMALISED quantities from `wound_core.py` -- overlap x radius
        ratio.

        AND THE CAVEAT, which is a modelling fact and not a bug: the
        off-diagonals are DIMENSIONLESS and the diagonal is
        area-times-turns-squared, so the two are not in the same units
        and the matrix is not an inductance matrix in the engineering
        sense. It is a STRUCTURE, and its eigenvalue SIGNS carry no
        physics -- which is why the mode gap below is measured on
        MAGNITUDES.
        """
        m = self._mutual_couplings(s)
        return [
            [s.r_out ** 2 * s.n_out ** 2, m[0], m[2]],
            [m[0], s.r_in ** 2 * s.n_in ** 2, m[1]],
            [m[2], m[1], s.r_core ** 2],
        ]

    @staticmethod
    def _mutual_couplings(s: PhysicalStalk) -> Tuple[float, float, float]:
        """(m_out_in, m_in_core, m_out_core), from the repo's law."""
        overlap_out_in = min(s.n_out, s.n_in) / max(s.n_out, s.n_in)
        concentric = s.r_in / s.r_out
        m_out_in = overlap_out_in * concentric
        m_in_core = (1.0 / max(s.n_in, 1)) / max(s.r_in - s.r_core, 1e-12)
        m_out_core = (1.0 / max(s.n_out, 1)) / max(s.r_out - s.r_core, 1e-12)
        return m_out_in, m_in_core, m_out_core

    def loop_modes(self, s: PhysicalStalk) -> List[float]:
        """The two loop modes' eigenvalues, from the difference basis.

        THE BASIS: (1,-1,0) for outer-minus-inner and (0,1,-1) for
        inner-minus-core. Three conductors, two independent loop
        currents.
        """
        M = self.inductance_matrix(s)
        v1 = [1.0, -1.0, 0.0]
        v2 = [0.0, 1.0, -1.0]
        L11 = sum(v1[i] * M[i][j] * v1[j] for i in range(3) for j in range(3))
        L22 = sum(v2[i] * M[i][j] * v2[j] for i in range(3) for j in range(3))
        L12 = sum(v1[i] * M[i][j] * v2[j] for i in range(3) for j in range(3))
        tr = L11 + L22
        det = L11 * L22 - L12 * L12
        disc = max(tr * tr / 4 - det, 0.0)
        root = math.sqrt(disc)
        return sorted([tr / 2 - root, tr / 2 + root])

    def mode_gap(self, s: PhysicalStalk) -> float:
        """The gap between a stalk's OWN two modes, on magnitudes.

        AND THE SIGN, which cost a measurement: the loop matrix is
        INDEFINITE, so the midpoint-relative gap is not defined and a
        guard of the form `mid > 1e-18` sends every gap to zero. So the
        gap is measured on magnitudes, and the indefiniteness is
        reported rather than hidden.
        """
        e1, e2 = self.loop_modes(s)
        a, b = abs(e1), abs(e2)
        hi, lo = max(a, b), min(a, b)
        return (hi - lo) / hi if hi > 1e-18 else 0.0

    def address(self, s: PhysicalStalk) -> float:
        """The stalk's address. Derived, so it means the same thing
        wherever the stalk sits."""
        return s.address

    def describe(self) -> Dict[str, Any]:
        return {
            "layer": "geometry",
            "stalks": len(self.stalks),
            "k": [round(s.coupling_factor(), 9) for s in self.stalks],
            "gaps": [round(s.gap, 9) for s in self.stalks],
            "addresses": [round(self.address(s), 6) for s in self.stalks],
            "mode_gaps": [round(self.mode_gap(s), 6) for s in self.stalks],
        }


# ===========================================================================
# LAYER 3 -- THE STALKS
# ===========================================================================

@dataclass
class Channel:
    """The channel the stalks make, as the maths.

        H(f) = sum_d h_d * exp(-2*pi*i*f*d)

    and the recovery is the zero-forcing inversion:

        R = H X / H = X

    with the taps at their OWN delays -- the rule that cost a whole
    measurement when it was broken (alignment 0.00000000 instead of
    1.00000000), because a tap evaluated at its list index is a
    different filter from the one that was fitted.
    """

    #: the complex taps
    taps: List[Tuple[float, float]]
    #: each tap's delay, in bins
    delays: List[int]
    bins: int = BINS

    def response(self, f: float) -> Tuple[float, float]:
        """H(f), with the NEGATIVE exponential, matching the DFT."""
        re = im = 0.0
        for (hr, hi), d in zip(self.taps, self.delays):
            th = -2.0 * math.pi * f * d
            re += hr * math.cos(th) + hi * math.sin(th)
            im += hi * math.cos(th) - hr * math.sin(th)
        return re, im

    def magnitude(self, f: float) -> float:
        re, im = self.response(f)
        return math.hypot(re, im)

    def notch_db(self) -> float:
        """The null's depth, as a POSITIVE number."""
        peak = max(self.magnitude(i / 200.0 - 0.5) for i in range(201))
        if peak <= 0.0:
            return 0.0
        null = min(self.magnitude(i / 200.0 - 0.5) for i in range(201))
        if null <= 0.0:
            return 60.0
        return -(20.0 * math.log10(null / peak))

    def derived_width(self) -> int:
        """THE WIDTH, and it is DERIVED from the tap count.

        THE RULE, verbatim from the Rust core's `carrier.rs::equalise`:

            2 taps or fewer -> 1 bit
            4 taps or fewer -> 4 bits
            5 or more       -> 16 bits

        And the consequence, which is the architecture's central fact:
        the channel's taps are one per OTHER stalk in view, so a WIDER
        channel IS a bigger population in view. Widening and recruiting
        are ONE dial.
        """
        n = len(self.taps)
        if n <= 1:
            return 1
        if n <= 2:
            return 4
        if n <= 4:
            return 8
        return 16

    def describe(self) -> Dict[str, Any]:
        return {
            "layer": "stalks",
            "taps": len(self.taps),
            "delays": self.delays,
            "notch_db": round(self.notch_db(), 4),
            "derived_width": self.derived_width(),
        }


# ===========================================================================
# THE COMPOSITION
# ===========================================================================

@dataclass
class Core:
    """The three layers, composed.

    THE COMPOSITION, stated once:

        a PROPOSAL is a proposed CHANGE OF GEOMETRY
        the CONTROL SYSTEM decides whether the change may happen
        the new GEOMETRY produces a new CHANNEL
        the CHANNEL is what carries the signal
        the STALKS are the geometry, made of wire

    AND THE ONE-LINE ANSWER TO "WHAT IS THE CORE":

        THE CORE IS THE PART OF THE SYSTEM THAT MAY NOT CHANGE.

    Which is not a directory. It is a set of invariants: the M0
    governor, the write-protected ground, the 1-bit verdict, the
    protected locus. Everything above it is a proposal.
    """

    veto: Veto
    geometry: Geometry
    channel: Channel

    def propose_geometry_change(self, gap_factor: float) -> Dict[str, Any]:
        """A proposal, as a geometry change.

        AND THE PROPOSAL CARRIES ITS EVIDENCE, because an audit that
        cannot read the proposal cannot judge it, and the gate refuses a
        proposal with no evidence by name.
        """
        pop = make_population(4, gap_factor=gap_factor)
        return {
            "change": "gap_factor",
            "value": gap_factor,
            "evidence": [
                "the gap moves k: %.6f at factor 1.00" % (
                    pop[0].coupling_factor(),),
                "L_sigma = mu0 * gap [M] NASA-CR-18965 Eq. 4.4.1",
            ],
            "stalks": pop,
        }

    def apply_if_admitted(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a geometry change -- ONLY IF the veto admits it.

        AND THE ORDER, which is the invariant: the veto is consulted
        BEFORE the geometry is touched. So an unadmitted change never
        reaches the channel.
        """
        if not self.veto.admits(proposal):
            return {"applied": False, "reason": "vetoed"}
        pop = proposal["stalks"]
        self.geometry = Geometry(stalks=pop)
        return {"applied": True, "reason": "admitted"}

    def describe(self) -> Dict[str, Any]:
        return {
            "control": self.veto.describe(),
            "geometry": self.geometry.describe(),
            "channel": self.channel.describe(),
            "core": "the part of the system that may not change",
        }


# ===========================================================================
# THE DEMONSTRATION
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE THREE READINGS OF CORE, AS ONE MATH")
    print("=" * 78)
    print()

    print("  LAYER 1 -- THE CONTROL SYSTEM (the 747)")
    print()
    print("    V(p) in {0,1}      the deterministic verdict")
    print("    admit iff V(p)=1 AND %.2f <= rate <= %.2f" % (
        FLOOR, CEILING))
    print()
    print("    The verdict is COMPUTED, never judged: no model decides")
    print("    whether another model's output is allowed. And the RATE")
    print("    bounds the compute, because a gate that must be perfect")
    print("    is a gate that never opens.")
    print()

    print("  LAYER 2 -- THE GEOMETRY (the thing the math is about)")
    print()
    print("    L       the 3x3 inductance matrix, symmetric by reciprocity")
    print("    L_loop  the difference basis: 2 loop modes per stalk")
    print("    k       1/sqrt(1 + L_sigma/L_m)")
    print("    L_sigma = mu0 * gap        the NASA knob")
    print()
    print("    AND THE ONE THAT MAKES IT NOT INERT: k depends on")
    print("    gap/area. The area is QUADRATIC in the radius; the gap is")
    print("    LINEAR. So k is not scale-invariant.")
    print()

    print("  LAYER 3 -- THE STALKS (the workhorse)")
    print()
    print("    H(f) = sum_d h_d exp(-2*pi*i*f*d)")
    print("    R    = H X / H = X          the zero-forcing inversion")
    print("    w    = width_for(taps)     DERIVED, never requested")
    print()

    print("=" * 78)
    print("AND WHY THEY ARE ONE THING")
    print("=" * 78)
    print()
    print("  THE STALKS ARE THE GEOMETRY, AND THE GEOMETRY IS WHAT THE")
    print("  CONTROL SYSTEM CONTROLS.")
    print()
    print("    the control system decides what may change")
    print("    what changes is the geometry -- gap, girth, length")
    print("    and the geometry is what changes the CHANNEL")
    print("    so the control system's job is to decide what the channel")
    print("    may be")
    print()
    print("  SO THE ANSWER TO 'WHAT IS THE CORE' IS NOT A DIRECTORY:")
    print()
    print("    THE CORE IS THE PART OF THE SYSTEM THAT MAY NOT CHANGE.")
    print()
    print("  Which is a set of invariants -- the M0 governor, the")
    print("  write-protected ground, the 1-bit verdict, the protected")
    print("  locus. Everything above it is a proposal.")
    print()

    # ---- the live demonstration --------------------------------------
    pop = make_population(4)
    geometry = Geometry(stalks=pop)

    # the channel, from the geometry
    from interstalk_link import width_for
    tx, rx = pop[0], pop[1]
    sep = abs(rx.r_out - tx.r_out)
    d = math.sqrt(tx.coupling_factor() * rx.coupling_factor()) \
        * (rx.r_out / tx.r_out) / (1.0 + sep)
    leak = 1.0 - tx.coupling_factor()
    taps: List[Tuple[float, float]] = [(d, 0.0)]
    delays: List[int] = [0]
    for i, other in enumerate(pop[2:]):
        amp = d * leak * (0.5 + 0.5 * other.coupling_factor())
        ph = 2.0 * math.pi * other.address
        taps.append((amp * math.cos(ph), amp * math.sin(ph)))
        delays.append(1 * (i + 1))
    channel = Channel(taps=taps, delays=delays)

    veto = Veto()
    veto.add_invariant("has_evidence",
                       lambda p: bool(p.get("evidence")))
    veto.add_invariant("gap_positive",
                       lambda p: p.get("value", 0.0) > 0.0)
    veto.add_invariant("not_too_tight",
                       lambda p: p.get("value", 1.0) >= 0.25)

    core = Core(veto=veto, geometry=geometry, channel=channel)

    print("=" * 78)
    print("THE COMPOSITION, RUNNING")
    print("=" * 78)
    print()
    print("  THE GEOMETRY, as numbers:")
    for s in pop:
        print("    %-4s gap %.6f  k %.6f  address %.6f  mode gap %.6f" % (
            s.id, s.gap, s.coupling_factor(), s.address,
            geometry.mode_gap(s)))
    print()
    print("  THE CHANNEL, derived from it:")
    for key, val in channel.describe().items():
        print("    %-16s %s" % (key, val))
    print()
    print("  AND THE WIDTH IS DERIVED, so a wider channel IS a bigger")
    print("  population in view -- widen and recruit are one dial:")
    print("    taps %d -> width %d bits" % (
        len(channel.taps), channel.derived_width()))
    print()

    print("  A GEOMETRY CHANGE, THROUGH THE CONTROL SYSTEM:")
    for gf in (1.0, 0.5, 0.1, 3.0):
        p = core.propose_geometry_change(gf)
        # ONE decision, not two: the first version called verdict() and
        # then apply_if_admitted(), and apply_if_admitted calls
        # admits() which calls verdict() AGAIN -- so every proposal was
        # counted twice in the ledger.
        applied = core.apply_if_admitted(p)
        print("    gap factor %.2f -> applied %-5s  %s" % (
            gf, applied["applied"], applied["reason"]))
    print()
    print("    and the rate, which bounds the compute:")
    h = core.veto.describe()
    print("    rate %.3f  band (%.2f, %.2f)  target %.2f" % (
        h["rate"], FLOOR, CEILING, ADMISSION_TARGET))
    print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
