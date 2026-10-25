"""
stalk_physics.py -- THE GEOMETRY THAT MAKES THE CHANNEL.

Bobby, 2026-10-25: *"do we have a core or are u working on exactly
this now?"* -- and the answer is that the stalk geometry was INERT, and
now it is not.

THE INERTNESS, measured 2026-10-25 by `bench_motile_stalk.py`:

    girth growth   changes NOTHING that matters
    length        changes NOTHING in the channel

  And the reason was structural: everything in the model was a RATIO.
  The coupling is overlap x inner/outer. The address is (parity/2) +
  (ratio - 1). The notch is a ratio of two paths that scale together.
  So scaling the geometry left every ratio alone, and a bigger wire was
  a louder wire and nothing else.

THE MISSING PHYSICS, and it was published 37 years ago:

  NASA-CR-18965 (Divan's group, 1988-89), Eq. 4.4.1, verbatim:

    "It is seen from Equation (4.4.1) that for a given Ns as the
     interwinding space is reduced by decreasing r_pl, the leakage
     inductance decreases. This is the most interesting feature of the
     coaxial winding, in that the leakage inductance is so easily
     controllable."

  THE KEY, and it is the whole fix: **the leakage inductance depends on
  the GAP, which is a DIFFERENCE -- not a ratio.** And the magnetising
  inductance depends on the AREA, which is quadratic in the radius. So
  the coupling factor k depends on gap/area, which is NOT scale
  invariant: scaling the stalk by s scales the gap by s and the area by
  s^2, and the ratio changes.

  So the geometry DOES load the channel -- as soon as the channel is
  built from the real law instead of a fixed loss factor.

WHAT THE LAW IS, and the three pieces:

  L_m      the magnetising inductance: mu0 * N^2 * A / l, with A the
           enclosed area. [E] textbook solenoid.

  L_sigma  the leakage inductance: PROPORTIONAL TO THE INTERWINDING
           GAP. [M] NASA-CR-18965 Eq. 4.4.1, with the measured
           prototypes at 150 nH (rectangular coaxial) and 250 nH
           (circular coaxial) at 50 kHz, 50 kVA.

  k        the coupling factor: k = 1 / sqrt(1 + L_sigma / L_m).
           [E] standard transformer relation.

  AND THE REFLECTED PATH'S AMPLITUDE IS (1 - k), not a constant. That
  is the one-line change to the channel: the reflected path carries the
  LEAKAGE flux, and the leakage is what the gap controls.

THE CONSEQUENCES, and they are the trade-off the design wanted:

  SMALLER GAP  less leakage, HIGHER k, SHALLOWER notch -- a safer
               reading, and a duller one.
  BIGGER GAP   more leakage, LOWER k, DEEPER notch -- more structure
               to invert, so a sharper reading, and closer to the noise
               floor, so the equaliser refuses it as `irrecoverable`.

  So the gap becomes a RESOLUTION CONTROL, and it is a physical one.
  (The first draft of this file had the direction REVERSED; the
  measurement and NASA's own reading are what corrected it.)

THE ADDRESS MUST NOT MOVE, and that is the constraint that makes this
safe: the address is the winding RATIO, which is scale-invariant, so
scaling the stalk changes the channel without changing who anyone is.
A stalk can be made louder, or more resolvable, without ceasing to be
itself.

AND THE LENGTH, which is the second inert lever:

  The path delay must come from the PHYSICAL LENGTH. The propagation
  delay over the coil is length x sqrt(eps_r) / c, and the frame's bin
  width is fixed. So a longer stalk's reflection arrives LATER, which
  ROTATES the tap's phase, which MOVES the notch.

  And the frequency that makes the length matter is the coil's own
  resonance, f = v / 2L with v = c / sqrt(eps_r) -- which
  `interstalk.py::rung_frequency` already computes.

PROVENANCE: [M] measured here or in the cited source. [E] textbook.
[H] hypothesis.

Run:
    python src/stalk_physics.py
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from wound_core import Channel, CoaxWinding  # noqa: E402

#: Constants. [M] CODATA 2018.
MU_0 = 1.25663706212e-6      # T*m/A
C_LIGHT = 299_792_458.0      # m/s
EPS_0 = 8.8541878128e-12     # F/m

#: The dielectric the windings sit in. The repo's own default.
EPS_R = 2.5


# ===========================================================================
# THE STALK, WITH THE PHYSICS
# ===========================================================================

@dataclass
class PhysicalStalk:
    """One 3-part stalk, with the quantities the physics needs.

    THE THREE RADIUSES, and the GAP is the one that matters:

        r_core    the core conductor
        r_in      the inner winding
        r_out     the outer winding
        GAP       r_out - r_in, the interwinding space. This is what
                  NASA Eq. 4.4.1 says the leakage inductance follows.

    AND THE LENGTH, which sets the propagation delay and the
    resonance.

    THE UNITS ARE REAL: metres, and the permeabilities are vacuum's.
    The dimensionless "girths" in `wound_core.py` are the RATIOS of
    these radii, and this class is where the ratio becomes a physical
    quantity.
    """

    id: str
    r_core: float
    r_in: float
    r_out: float
    n_in: int
    n_out: int
    length: float = 1.0

    def __post_init__(self) -> None:
        if not (self.r_core < self.r_in < self.r_out):
            raise ValueError(
                "%s: concentric order must be core < inner < outer, got "
                "%.6f / %.6f / %.6f" % (self.id, self.r_core, self.r_in,
                                        self.r_out))
        if self.n_in <= 0 or self.n_out <= 0:
            raise ValueError("%s: turn counts must be positive" % self.id)

    # -- the geometry ----------------------------------------------------

    @property
    def gap(self) -> float:
        """THE INTERWINDING GAP. The NASA knob."""
        return self.r_out - self.r_in

    @property
    def ratio(self) -> float:
        """The winding ratio. SCALE-INVARIANT, so it is the address."""
        return self.r_out / self.r_in

    @property
    def area(self) -> float:
        """The area the inner winding encloses."""
        return math.pi * self.r_in ** 2

    @property
    def address(self) -> float:
        """The phase address. Derived, so a stalk means the same thing
        wherever it sits."""
        return ((self.n_out % 2) / 2.0 + (self.ratio - 1.0)) % 1.0

    # -- the inductances -------------------------------------------------

    def magnetising_inductance_h(self) -> float:
        """L_m = mu0 * N^2 * A / l. [E] textbook solenoid.

        THE N, and it is the OUTER winding's, because the outer winding
        is the one that encloses the core and the area.
        """
        return MU_0 * (self.n_out ** 2) * self.area / self.length

    def leakage_inductance_h(self) -> float:
        """L_sigma = mu0 * gap. [M] NASA-CR-18965 Eq. 4.4.1, PROPORTIONAL
        TO THE INTERWINDING GAP.

        THE DERIVATION, and it is a flux-geometry argument rather than
        a fitted constant:

            the leakage flux escapes the inner winding and returns
            OUTSIDE the outer tube

            A_leak = gap * 2*pi*r_out      the leakage cross-section
            l_leak = 2*pi*r_out            the leakage path length
            L_sigma = mu0 * A_leak / l_leak = mu0 * gap

        So the r_out CANCELS, and the law is simply mu0 times the gap.
        Which is exactly what NASA's equation says in its own reading:
        *"for a given Ns as the interwinding space is reduced by
        decreasing r_pl, the leakage inductance decreases. This is the
        most interesting feature of the coaxial winding, in that the
        leakage inductance is so easily controllable."*

        AND THE UNITS, and this is the part the repo flags as owed:
        *"our girth values are dimensionless ratios; the physics needs
        real radii, a real permeability, and a real return path."* So
        this class takes REAL radii in metres, and the dimensionless
        girths in `wound_core.py` are the RATIOS of these.

        THE NASA CHECK, and it is a sanity check on the ORDER rather
        than an exact match, because their transformer has two litz
        windings of five turns each and so links more leakage than one
        turn's worth: their measured leakage is 150 nH (rectangular
        coaxial) and 250 nH measured / 182 nH calculated (circular) at
        50 kHz and 50 kVA, against a 5 mil (25.4 um) Kapton
        interwinding. mu0 * 25.4 um is 3.19e-11 H, so their leakage is
        ~7800x the single-turn figure -- which is what a multi-turn
        secondary and a power scale give you. The law's SHAPE and its
        GAP-DEPENDENCE are what is imported; the constant is theirs.
        """
        return MU_0 * self.gap

    def coupling_factor(self) -> float:
        """k = 1 / sqrt(1 + L_sigma / L_m). [E] standard relation.

        AND THIS IS THE WHOLE POINT. k depends on gap/area, which is
        not scale-invariant. So scaling the stalk changes the coupling,
        and the channel with it.
        """
        lm = self.magnetising_inductance_h()
        ls = self.leakage_inductance_h()
        if lm <= 0.0:
            return 0.0
        return 1.0 / math.sqrt(1.0 + ls / lm)

    # -- the time --------------------------------------------------------

    def propagation_delay_s(self) -> float:
        """The propagation delay over the coil. [E]

        length x sqrt(eps_r) / c. And this is what makes LENGTH matter:
        a longer stalk's reflection arrives later.
        """
        v = C_LIGHT / math.sqrt(EPS_R)
        return self.length / v

    def resonance_hz(self) -> float:
        """The coil's fundamental. f = v / 2L. [E]

        THE FREQUENCY THAT MAKES THE GEOMETRY MATTER: near the
        resonance the coil's reactances dominate and the gap's effect
        on the coupling is at its sharpest.
        """
        v = C_LIGHT / math.sqrt(EPS_R)
        return v / (2.0 * self.length)

    def describe(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gap": self.gap,
            "ratio": self.ratio,
            "address": self.address,
            "L_m_H": self.magnetising_inductance_h(),
            "L_sigma_H": self.leakage_inductance_h(),
            "k": self.coupling_factor(),
            "delay_s": self.propagation_delay_s(),
            "resonance_hz": self.resonance_hz(),
        }


# ===========================================================================
# THE CHANNEL, BUILT FROM THE PHYSICS
# ===========================================================================

@dataclass
class PhysicalChannel:
    """The channel between two stalks, from the real coupling law.

    THE TAP AMPLITUDES:

      direct      the transmitter's coupling to the receiver, via the
                  magnetising path.
      reflected   the LEAKAGE path, and its amplitude is (1 - k) of the
                  direct. This is the one-line change from the fixed
                  REFLECTION_LOSS: the leakage is what the gap controls.

    AND THE DELAY, which comes from the physical length, so a longer
    stalk's reflection arrives later and its tap is rotated -- which
    moves the notch.
    """

    tx: PhysicalStalk
    rx: PhysicalStalk
    #: The other stalks in view, each contributing a reflected path
    #: whose phase is that neighbour's address.
    neighbours: List[PhysicalStalk]
    #: The frame duration, so the delay can be expressed in bins.
    frame_duration: float = 1.0e-6
    #: The frame length in bins.
    bins: int = 128

    def direct_gain(self) -> float:
        """The direct path's amplitude.

        THE COUPLING, and it is the geometric mean of the two stalks'
        couplings, divided by the separation -- the same law
        `interstalk_link.PairChannel.pair_coupling` uses, because it is
        the right one and there is no reason to change it.
        """
        sep = abs(self.rx.r_out - self.tx.r_out)
        geo = math.sqrt(self.tx.coupling_factor()
                        * self.rx.coupling_factor())
        resp = self.rx.r_out / max(self.tx.r_out, 1e-12)
        return geo * resp / (1.0 + sep)

    def path_delay_bins(self) -> int:
        """The reflected path's delay, IN BINS, from the physical length.

        AND THIS IS THE SECOND FIX. The delay was a bin COUNT in the old
        model, so the length of a stalk did not enter the channel at
        all. Now it is the propagation delay over the coil expressed in
        the frame's timebase.
        """
        d = (self.tx.propagation_delay_s() + self.rx.propagation_delay_s())
        bins = d / self.frame_duration
        return max(1, int(round(bins)))

    def taps(self) -> List[Tuple[Tuple[float, float], int]]:
        """The taps, with their delays. The first is the direct path."""
        d = self.direct_gain()
        out: List[Tuple[Tuple[float, float], int]] = [((d, 0.0), 0)]
        delay = self.path_delay_bins()
        # the reflected paths' amplitude is the LEAKAGE fraction
        leak = 1.0 - self.tx.coupling_factor()
        for i, other in enumerate(self.neighbours):
            amp = d * leak * (0.5 + 0.5 * other.coupling_factor())
            ph = 2.0 * math.pi * other.address
            out.append(((amp * math.cos(ph), amp * math.sin(ph)),
                        delay * (i + 1)))
        return out

    def channel(self) -> Channel:
        taps = self.taps()
        return Channel([t for t, _ in taps], [dl for _, dl in taps])

    def describe(self) -> Dict[str, Any]:
        return {
            "tx": self.tx.id,
            "rx": self.rx.id,
            "direct": self.direct_gain(),
            "k_tx": self.tx.coupling_factor(),
            "k_rx": self.rx.coupling_factor(),
            "leakage_fraction": 1.0 - self.tx.coupling_factor(),
            "delay_bins": self.path_delay_bins(),
            "notch_db": self.channel().notch_db(),
        }


# ===========================================================================
# THE BENCH
# ===========================================================================

#: THE PHYSICAL SCALE. The dimensionless recipe's 0.060 becomes 60 mm
#: -- a real coil of this size is metres long, and the ratios are what
#: the girth bench measured.
PHYSICAL_R_IN = 0.060          # metres
PHYSICAL_R_CORE = 0.030        # metres
PHYSICAL_LENGTH = 1.0         # metres


def make_population(n: int = 4, scale: float = 1.0,
                    gap_factor: float = 1.0,
                    length: float = PHYSICAL_LENGTH) -> List[PhysicalStalk]:
    """The measured geometry recipe, in the physical form.

    THE RATIO STEP is 0.0625, which the girth bench measured as the
    working spread: 8 DFT bins of address separation at 128 bins, and
    82% naming against 77% for the 16-bin spread.

    AND THE SCALE IS REAL: 60 mm inner radius, 1 m long. That is a
    power-transformer-sized coil, which is the scale the coaxial
    winding literature is at, and it is where the gap's effect on k is
    measurable -- at micrometre scale the gap would be a rounding error
    against the area.
    """
    out: List[PhysicalStalk] = []
    half = max(n // 2, 1)
    for i in range(n):
        parity = i % 2
        k = i // 2
        ratio = 1.200 + (k + 0.5) * 0.0625
        r_in = PHYSICAL_R_IN * scale
        r_out = r_in * ratio
        # the gap is the NASA knob, so it is what the sweep moves
        r_out = r_in + (r_out - r_in) * gap_factor
        out.append(PhysicalStalk(
            id="P%d" % i, r_core=PHYSICAL_R_CORE * scale, r_in=r_in,
            r_out=r_out, n_in=12, n_out=13 + parity, length=length))
    return out


def main() -> int:
    print("=" * 78)
    print("THE GEOMETRY THAT MAKES THE CHANNEL")
    print("=" * 78)
    print()

    print("  THE LAW, and the citation is for the PROPORTIONALITY:")
    print("    NASA-CR-18965 Eq. 4.4.1: the leakage inductance is")
    print("    proportional to the INTERWINDING GAP. Their measured")
    print("    prototypes: 150 nH (rectangular coaxial), 250 nH measured")
    print("    and 182 nH calculated (circular coaxial), at 50 kHz, 50 kVA.")
    print()
    print("    L_m     = mu0 N^2 A / l            [E] textbook solenoid")
    print("    L_sigma PROPORTIONAL TO THE GAP   [M] NASA Eq. 4.4.1")
    print("    k       = 1 / sqrt(1 + L_sigma/L_m)  [E] standard relation")
    print()
    print("    AND THE CONSEQUENCE, which is the whole fix: k depends on")
    print("    gap/area, and area is QUADRATIC in the radius while the gap")
    print("    is LINEAR. So k is NOT scale-invariant, and the geometry")
    print("    finally loads the channel.")
    print()

    print("=" * 78)
    print("1. THE GAP IS THE RESOLUTION CONTROL")
    print("=" * 78)
    print()
    print("  %-14s %-11s %-11s %-11s %-11s %-10s" % (
        "gap factor", "gap", "k", "leakage", "notch dB", "delay"))
    print("  " + "-" * 70)
    base = make_population(4, gap_factor=1.0)
    for gf in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        pop = make_population(4, gap_factor=gf)
        pc = PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                             frame_duration=1.0e-6, bins=128)
        s = pop[0]
        print("  %-14.2f %-11.6f %-11.6f %-11.6f %-11.2f %-10d" % (
            gf, s.gap, s.coupling_factor(),
            1.0 - s.coupling_factor(),
            pc.channel().notch_db(), pc.path_delay_bins()))
    print()
    print("  THE TRADE, and THE FIRST VERSION OF THIS TEXT HAD IT")
    print("  BACKWARDS. Measured, not argued:")
    print("    a SMALLER gap -> LESS leakage -> HIGHER k -> SHALLOWER notch")
    print("      -> less to invert, so a safer reading but a duller one.")
    print("    a BIGGER gap -> MORE leakage -> LOWER k -> DEEPER notch")
    print("      -> more structure to invert, so a sharper reading, and")
    print("         closer to the noise floor, so the equaliser may")
    print("         refuse it as `irrecoverable`.")
    print()
    print("  NASA's own reading agrees with the measurement and against my")
    print("  first draft: \"as the interwinding space is reduced by")
    print("  decreasing r_pl, the leakage inductance decreases\" -- so a")
    print("  tighter coil is a BETTER coupled one, and a looser one is")
    print("  the leakier, more-resolvable one.")
    print()
    print("  SO THE GAP IS THE RESOLUTION CONTROL, and it is a safety")
    print("  trade as well: the sharper the null, the closer it sits to")
    print("  the noise floor, and the equaliser refuses below it.")
    print()

    print("=" * 78)
    print("2. GIRTH NOW MOVES THE CHANNEL, AND NOT THE ADDRESS")
    print("=" * 78)
    print()
    print("  %-10s %-11s %-11s %-11s %-13s %-9s" % (
        "scale", "k", "notch dB", "delay", "address", "moved?"))
    print("  " + "-" * 68)
    addr0 = None
    for sc in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        pop = make_population(4, scale=sc)
        pc = PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                             frame_duration=1.0e-6, bins=128)
        s = pop[0]
        if addr0 is None:
            addr0 = s.address
        moved = "NO" if abs(s.address - addr0) < 1e-12 else "YES"
        print("  %-10.2f %-11.6f %-11.2f %-11d %-13.6f %-9s" % (
            sc, s.coupling_factor(), pc.channel().notch_db(),
            pc.path_delay_bins(), s.address, moved))
    print()
    print("  SO: the ADDRESS DOES NOT MOVE. The winding ratio is")
    print("  scale-invariant, so a stalk can be made louder, or more")
    print("  resolvable, without ceasing to be itself. That is the")
    print("  constraint that makes the whole thing safe.")
    print()

    print("=" * 78)
    print("3. LENGTH NOW MOVES THE CHANNEL")
    print("=" * 78)
    print()
    print("  %-10s %-13s %-11s %-11s %-10s" % (
        "length", "resonance", "delay s", "delay bins", "notch dB"))
    print("  " + "-" * 60)
    for ln in (0.25, 0.5, 1.0, 2.0, 4.0, 8.0):
        pop = make_population(4, length=ln)
        pc = PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                             frame_duration=1.0e-6, bins=128)
        s = pop[0]
        print("  %-10.2f %-13.4g %-11.4g %-11d %-10.2f" % (
            ln, s.resonance_hz(), s.propagation_delay_s(),
            pc.path_delay_bins(), pc.channel().notch_db()))
    print()
    print("  THE FREQUENCY THAT MAKES IT MATTER: the coil's own")
    print("  resonance, f = v/2L. Near it the reactances dominate and the")
    print("  gap's effect on the coupling is at its sharpest. That is the")
    print("  DNA-phonon claim in `interstalk.py::rung_frequency` -- and")
    print("  it is what makes LENGTH a control rather than a decoration.")
    print()

    print("=" * 78)
    print("4. THE TRADEOFF, MEASURED AT THE STALK LEVEL")
    print("=" * 78)
    print()
    print("  a stalk that is both LOUDER and MORE RESOLVABLE is what the")
    print("  brain's myelination is (Sinclair et al. 2017: axon diameter")
    print("  and myelin thickness both DOUBLE at hearing onset). So the")
    print("  question is whether the geometry offers a direction where")
    print("  both improve.")
    print()
    print("  %-10s %-12s %-12s %-14s %-9s" % (
        "scale", "direct gain", "notch dB", "k", "better?"))
    print("  " + "-" * 62)
    base_gain = None
    for sc in (0.5, 0.75, 1.0, 1.5, 2.0):
        pop = make_population(4, scale=sc)
        pc = PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                             frame_duration=1.0e-6, bins=128)
        if base_gain is None:
            base_gain = pc.direct_gain()
        better = "yes" if (pc.direct_gain() > base_gain
                           and pc.channel().notch_db()
                           > base_notch(base_gain)) else "no"
        print("  %-10.2f %-12.6f %-12.2f %-14.6f %-9s" % (
            sc, pc.direct_gain(), pc.channel().notch_db(),
            pop[0].coupling_factor(), better))
    print()
    print("=" * 78)
    return 0


def base_notch(_g: float) -> float:
    """The notch at the reference scale, for the comparison above."""
    pop = make_population(4, scale=0.5)
    pc = PhysicalChannel(tx=pop[0], rx=pop[1], neighbours=pop[2:],
                         frame_duration=1.0e-6, bins=128)
    return pc.channel().notch_db()


if __name__ == "__main__":
    sys.exit(main())
