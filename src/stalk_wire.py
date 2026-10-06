"""
stalk_wire.py — the stalk is a wire. built like one.

No new physics. Every part of this is off-the-shelf technology that
already ships in cars and in people:

    stalk pair      = twisted differential pair   (CAN bus, every car)
    cross-member    = ignition coil / transformer rung
    sheath          = myelin                     (axon insulation)

CAN bus already solves this exact problem: two wires twisted together,
differential signaling, running in an engine bay next to an ignition
system. That is the whole design. The stalk is that.

WHAT THIS COMPUTES
------------------
For a stalk pair with rungs and a sheath, the four numbers an engineer
actually wants:

    1. characteristic impedance  Z0  (what the line looks like to a driver)
    2. propagation delay         the length of a signal along the stalk
    3. bandwidth                 the highest frequency that survives
    4. signal integrity          how much ambient noise reaches the receiver

Plus the one that makes the rungs worth having: with rungs, the pair
stops being a lossy wire and becomes a transmission line with
resonances at f = n*v/2L.

Run: python src/stalk_wire.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

C_VACUUM = 299_792_458.0
MU_0 = 4e-7 * math.pi          # H/m
EPS_0 = 8.8541878128e-12


# ---------------------------------------------------------------------------
# the wire
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StalkWire:
    """One stalk: a conductor, possibly one of a twisted pair.

    Mirrors a real differential pair:
      girth          conductor radius (a real one is ~0.1-0.3 mm)
      separation     centre-to-centre distance from the partner
      length         run along the substrate
      v_prop         propagation velocity in the surrounding medium
    """

    girth: float                    # conductor radius, m
    separation: float = 0.0         # to partner; 0 = single conductor
    length: float = 1.0             # m
    v_prop: float = 2.0e8           # ~2/3 c in typical FR4/dielectric
    resistivity: float = 1.7e-8     # copper, ohm-m
    sheath: bool = False
    sheath_thickness: float = 0.0   # m, radial insulation

    # -- impedance ------------------------------------------------------

    def characteristic_impedance(self) -> float:
        """Z0 of the free-space two-wire differential pair.

            Z0 = (120/sqrt(eps_r)) * arccosh(D / 2a)

        with D the centre-to-centre spacing and a the conductor radius.

        FIRST ATTEMPT USED ln(D/d), which is the formula for a conductor
        over a GROUND PLANE, not a free pair. It gave 17-90 ohm where a
        real CAN bus is 120, i.e. wrong by a factor of ~2 in the
        dimension that matters. The arccosh form gives 80 ohm at 0.5 mm
        and 124 ohm at 0.8 mm, which brackets the real value. Same
        mistake class as the FDTD sign: a plausible formula for a
        similar-looking geometry.

        eps_r = 2.3 is the usual jacket-plus-dielectric figure.
        """
        a = self.girth
        if a <= 0:
            raise ValueError("girth must be positive")
        if self.separation <= 0:
            raise ValueError("no partner: separation must be positive")
        ratio = self.separation / (2.0 * a)
        if ratio <= 1.0:
            raise ValueError(
                f"wires overlap: separation {self.separation:.4g} <= "
                f"diameter {2*a:.4g}")
        return (120.0 / math.sqrt(2.3)) * math.acosh(ratio)

    def dc_resistance_per_m(self) -> float:
        """R = rho / (pi r^2), for a round conductor."""
        area = math.pi * self.girth ** 2
        return self.resistivity / area

    def attenuation_db(self, frequency_hz: float) -> float:
        """Skin-effect loss over the pair's length, in dB.

        Standard surface-resistance treatment:

            Rs    = sqrt(pi * f * mu0 * rho)      [ohm per square]
            R_ac  = Rs / (2*pi*a)                  [ohm/m, a = radius]
            loss  = 8.686 * R_ac * L / Z0          [dB]

        FIRST ATTEMPT multiplied the DC resistance by a hand-rolled
        sqrt(f) factor, which gave 448 dB at 1 GHz -- a fuse, not a
        cable, and wrong by ~2000x. The correct expression gives:

            1 MHz  ->  0.02 dB/m
            10 MHz ->  0.06 dB/m
            100 MHz->  0.20 dB/m
            1 GHz  ->  0.64 dB/m

        which matches a real 120-ohm twisted pair. Same lesson as the
        impedance form: check the result against a known device.
        """
        if frequency_hz <= 0:
            return 0.0
        z0 = self.characteristic_impedance()
        if z0 <= 0:
            return float("inf")
        a = self.girth
        rs = math.sqrt(math.pi * frequency_hz * MU_0 * self.resistivity)
        r_ac = rs / (2.0 * math.pi * a)
        return 8.686 * r_ac * self.length / z0

    def propagation_delay_ns(self) -> float:
        """time for a signal to traverse the stalk."""
        return self.length / self.v_prop * 1e9

    # -- integrity -----------------------------------------------------

    def common_mode_rejection_db(self) -> float:
        """How much ambient noise the twist removes.

        A far-field disturbance induces nearly the same voltage on both
        wires. The receiver subtracts, so it cancels. The induced
        voltage scales with the LOOP AREA of the pair, and a pair
        twisted at rate `t` has loop area d/(2t) where d is the
        separation.

        Untwisted reference: loop area = separation * length.
        Cancellation improves as area falls, so rejection in dB is

            20*log10( (separation*length) / (separation/(2t)) )
          = 20*log10( 2 * t * length )

        which is the textbook result: every doubling of twist rate buys
        ~6 dB.
        """
        t = self.twist_rate
        if t <= 0:
            return 0.0
        ratio = 2.0 * t * self.length
        return 20.0 * math.log10(ratio) if ratio > 0 else 0.0

    @property
    def twist_rate(self) -> float:
        return getattr(self, "_twist", 0.0)


# ---------------------------------------------------------------------------
# the pair — twisted, sheathed
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StalkPair:
    """Two stalks, twisted, optionally sheathed. This is a CAN bus node.

    girths are deliberately DIFFERENT. Perfect symmetry means the two
    wires couple identically and ambient noise cancels exactly -- which
    is good -- but it also means you cannot tune the pair. Unequal
    girths break the symmetry and give a real design variable.
    """

    girth_a: float
    girth_b: float
    # Centre-to-centre spacing, EXPLICIT and independent of the girths.
    #
    # Deriving it as girth_a + girth_b is wrong and always fails: that
    # makes spacing < 2*max(girth) whenever the radii differ, so the
    # two-wire impedance formula is undefined for precisely the varied
    # girths this design is built around. Spacing is a design choice,
    # like it is in a real cable.
    spacing: float = 0.7e-3
    twist_rate: float = 2.0        # twists per metre
    length: float = 1.0
    v_prop: float = 2.0e8
    sheath: bool = True            # myelin
    sheath_thickness: float = 0.0
    # INSULATION changes propagation velocity and impedance
    v_insulated: float = 1.4e8     # slower: dielectric loading

    def wire_a(self) -> StalkWire:
        return StalkWire(
            girth=self.girth_a, separation=self.spacing,
            length=self.length,
            v_prop=self.v_insulated if self.sheath else self.v_prop,
            sheath=self.sheath, sheath_thickness=self.sheath_thickness,
        )

    def wire_b(self) -> StalkWire:
        return StalkWire(
            girth=self.girth_b, separation=self.spacing,
            length=self.length,
            v_prop=self.v_insulated if self.sheath else self.v_prop,
            sheath=self.sheath, sheath_thickness=self.sheath_thickness,
        )

    def impedance_ohm(self) -> float:
        """Z0 of the differential pair."""
        return self.wire_a().characteristic_impedance()

    def attenuation_db(self, f_hz: float) -> float:
        """Loss on the pair: the worse of the two wires dominates,
        because a differential receiver reads the weaker signal."""
        return max(self.wire_a().attenuation_db(f_hz),
                   self.wire_b().attenuation_db(f_hz))

    def propagation_delay_ns(self) -> float:
        return self.wire_a().propagation_delay_ns()

    def cmr_db(self) -> float:
        """common-mode rejection from the twist, 20log10(2 t L)."""
        r = 2.0 * self.twist_rate * self.length
        return 20.0 * math.log10(r) if r > 0 else 0.0

    def z0_mismatch_db(self) -> float:
        """Impedance mismatch between the two wires.

        MEASURED CONSEQUENCE of varied girths. At one spacing, unequal
        conductors give:

            0.13/0.20 mm2 -> Z0 138 vs 120 ohm  (18 ohm apart)
            0.20/0.35 mm2 -> Z0 144 vs 120 ohm  (24 ohm apart)
            0.35/0.50 mm2 -> Z0 135 vs 120 ohm  (15 ohm apart)

        A differential receiver sees this as a common-mode-to-differential
        conversion and as skew between the two legs. So "variable girths"
        is NOT free crosstalk control -- it trades impedance match for
        it. Real CAN uses equal conductors.
        """
        za = self.wire_a().characteristic_impedance()
        zb = self.wire_b().characteristic_impedance()
        if za <= 0 or zb <= 0:
            return float("inf")
        return abs(za - zb)


# ---------------------------------------------------------------------------
# rungs — DNA base pairs / ignition coil secondaries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossMember:
    """A rung between the two stalks. DNA's base pair; a coil's secondary.

    Electrically a lumped LC resonator bridging the pair. N rungs at
    spacing d make the pair a DISCRETE TRANSMISSION LINE with
    resonances at

        f_n = n * v / (2 * N d)  =  n * v / (2 * L)

    which is the same formula as any cavity. The rungs do not add
    bandwidth -- they add RESONANCE, and resonance is what lets a fast
    signal ride the pair instead of being attenuated by it.
    """

    spacing: float          # m between rungs
    count: int              # N rungs
    c_farad: float = 5e-11  # ~50 pF, base-pair scale
    l_henry: float = 1e-9  # ~1 nH
    r_ohm: float = 5.0

    @property
    def total_length(self) -> float:
        return self.spacing * self.count

    def resonance_hz(self, v_prop: float = 2.0e8) -> List[float]:
        """the standing-wave frequencies this rung chain supports."""
        L = self.total_length
        if L <= 0:
            return []
        n = 4  # first four modes
        return [(k * v_prop) / (2.0 * L) for k in range(1, n + 1)]

    def characteristic_impedance_ohm(self) -> float:
        return math.sqrt(self.l_henry / self.c_farad)

    def quality_factor(self) -> float:
        """Q of one rung. Higher = sharper resonance = more selective."""
        w = 1.0 / math.sqrt(self.l_henry * self.c_farad)
        return w * self.l_henry / self.r_ohm

    def loaded_bandwidth_hz(self) -> float:
        """bandwidth of the rung resonance: f0 / Q."""
        f0 = 1.0 / (2.0 * math.pi * math.sqrt(self.l_henry * self.c_farad))
        return f0 / self.quality_factor()

    def turns_ratio(self, n_primary: int, n_secondary: int) -> float:
        """ignition-coil behaviour: turns ratio sets the voltage step-up.

        V_secondary / V_primary = n_secondary / n_primary.
        """
        if n_primary <= 0:
            raise ValueError("primary turns must be positive")
        return n_secondary / n_primary


# ---------------------------------------------------------------------------
# the assembly
# ---------------------------------------------------------------------------

@dataclass
class StalkAssembly:
    """A sheathed, runged twisted pair. This is the whole stalk."""

    pair: StalkPair
    rungs: Optional[CrossMember] = None
    name: str = "stalk"

    def report(self) -> Dict:
        p = self.pair
        d: Dict = {
            "name": self.name,
            "girths_mm": (round(p.girth_a * 1000, 3), round(p.girth_b * 1000, 3)),
            "twist_per_m": p.twist_rate,
            "length_m": p.length,
            "sheathed": p.sheath,
            "Z0_ohm": round(p.impedance_ohm(), 2),
            "delay_ns": round(p.propagation_delay_ns(), 2),
            "cmr_db": round(p.cmr_db(), 1),
        }
        for f in (1e6, 1e7, 1e8, 1e9):
            d[f"loss_dB@{f/1e6:g}MHz"] = round(p.attenuation_db(f), 2)
        if self.rungs:
            r = self.rungs
            d["rungs"] = {
                "count": r.count,
                "spacing_mm": round(r.spacing * 1000, 3),
                "total_mm": round(r.total_length * 1000, 2),
                "Z_rung_ohm": round(r.characteristic_impedance_ohm(), 1),
                "Q": round(r.quality_factor(), 1),
                "resonances_Hz": [round(x, 1) for x in r.resonance_hz(p.v_insulated)],
                "bandwidth_Hz": round(r.loaded_bandwidth_hz(), 1),
            }
        return d


# ---------------------------------------------------------------------------
# a realistic CAN node, so the numbers mean something
# ---------------------------------------------------------------------------

def solve_spacing_for_z0(radius: float, target_ohm: float = 120.0,
                         eps_r: float = 2.3) -> float:
    """Centre spacing that yields a given characteristic impedance.

    Inverts Z0 = (120/sqrt(eps_r)) * arccosh(D/2a) for D. This is how
    real cable is specified: pick the conductor gauge, then the spacing
    follows from the impedance you need.

    GEOMETRY WAS PREVIOUSLY INVENTED. The earlier node used girths of
    0.15/0.16 mm and a spacing of 0.70 mm, numbers typed rather than
    derived. Solving for 120 ohm with a 0.13 mm^2 conductor gives a
    radius of 0.203 mm and a spacing of 0.972 mm. The invented numbers
    happened to produce 118 ohm, so the error was invisible -- the
    right answer from the wrong reasoning.
    """
    a = radius
    if a <= 0:
        raise ValueError("radius must be positive")
    target_coeff = 120.0 / math.sqrt(eps_r)
    if target_ohm <= target_coeff:
        raise ValueError(f"{target_ohm} ohm is below the minimum "
                         f"{target_coeff:.1f} ohm for a two-wire pair")
    x = math.cosh(target_ohm / target_coeff)
    return 2.0 * a * x


def radius_from_area(area_m2: float) -> float:
    """equivalent round-conductor radius from a cross-section area."""
    if area_m2 <= 0:
        raise ValueError("area must be positive")
    return math.sqrt(area_m2 / math.pi)


def can_node() -> StalkAssembly:
    """A CAN-bus differential pair with DERIVED geometry.

    Real CAN high/low: 2 x 0.13 mm^2 stranded copper, twisted at
    roughly 40 turns/m, Z0 = 120 ohm.

    Geometry is solved, not chosen: radius from the 0.13 mm^2
    cross-section, spacing from the 120 ohm requirement.

    Girths are EQUAL, and that is a finding rather than an oversight:
    see z0_mismatch_db(). Unequal conductors at one spacing give
    15-24 ohm of Z0 mismatch, which is a real cost. CAN does not vary
    girth, and neither should a single differential stalk.
    """
    area = 0.13e-6
    r = radius_from_area(area)
    d = solve_spacing_for_z0(r, 120.0)
    pair = StalkPair(
        girth_a=r, girth_b=r,
        spacing=d,
        twist_rate=40.0,
        length=1.0,
        v_prop=2.0e8,
        sheath=True,
        v_insulated=1.5e8,
    )
    return StalkAssembly(pair, None, "CAN node (1 m, derived geometry)")


def dna_like() -> StalkAssembly:
    """A stalk scaled to DNA: 2 nm across, base pairs every 0.34 nm."""
    pair = StalkPair(
        girth_a=0.5e-9, girth_b=0.55e-9,
        spacing=2.0e-9,
        twist_rate=2.0 / 0.34e-9,   # ~2 twists per base pair
        length=3.4e-9,              # one helical turn
        v_prop=2.0e8,
        sheath=True,
        v_insulated=1.5e8,
    )
    rungs = CrossMember(spacing=0.34e-9, count=10, c_farad=1e-18, l_henry=1e-14, r_ohm=1.0)
    return StalkAssembly(pair, rungs, "DNA-scale stalk")


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: can | dna | sweep | verdict")
        return 0

    if argv[0] == "can":
        print(json.dumps(can_node().report(), indent=2))
        return 0

    if argv[0] == "dna":
        print(json.dumps(dna_like().report(), indent=2))
        return 0

    if argv[0] == "sweep":
        print("twist rate vs common-mode rejection (the CAN tradeoff)")
        print(f"{'twist/m':>9} {'cmr dB':>9} {'Z0 ohm':>9} {'loss dB@1MHz':>14}")
        for t in (5, 10, 20, 40, 80, 160):
            p = StalkPair(0.15e-3, 0.16e-3, spacing=0.70e-3,
                          twist_rate=t, length=1.0)
            print(f"{t:>9} {p.cmr_db():>9.1f} {p.impedance_ohm():>9.1f} "
                  f"{p.attenuation_db(1e6):>14.3f}")
        print("\nmore twist -> more rejection, same impedance, negligible")
        print("extra loss. THIS is why twisted pair won.")
        return 0

    if argv[0] == "verdict":
        can = can_node()
        dna = dna_like()
        print("=== the same circuit at two scales ===")
        for a in (can, dna):
            r = a.report()
            print(f"\n{r['name']}")
            print(f"  Z0        {r['Z0_ohm']} ohm")
            print(f"  delay     {r['delay_ns']} ns")
            print(f"  CMR       {r['cmr_db']} dB")
            if "rungs" in r:
                print(f"  rung Q    {r['rungs']['Q']}")
                print(f"  f0        {r['rungs']['resonances_Hz'][0]:.3e} Hz")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))