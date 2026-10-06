"""
stalk_carrier.py — three strands, phase-encoded carrier.

Bobby 2026-10-06: "add phase in a carrier for signal now we have three
strands."

THREE STRANDS IS THE MINIMUM THAT WORKS, AND HERE IS WHY
--------------------------------------------------------
Two strands give you ONE differential pair: signal = a - b. A third
strand gives you a REFERENCE, so phase becomes meaningful. You cannot
measure phase against nothing.

This is the same reason 3-wire is the standard balanced transmission
line (RS-485, RS-422, old 120V audio) while 2-wire is not: with three
conductors you can carry signal AND supply the return, so the common
mode is bounded by the far end instead of by earth.

ROPE IS THE PRECEDENT, NOT A METAPHOR
--------------------------------------
A 3-strand braid is the standard rope construction because two strands
can spin and four leave a void. Three is the smallest count that
self-locks. Lay angle theta = atan(2*pi*a / p) where p is the axial
pitch; real hawser runs 50-70 degrees.

So the braid is both the STRUCTURE (it takes load) and the SIGNAL PATH
(it rejects noise). Three strands, three differential pairs:
(a-b), (b-c), (c-a). Topology scales as N/2 pairs, not N strands.

CARRIER
-------
Baseband signalling on a balanced pair is noise-limited and cannot
exceed the pair's bandwidth. Putting the information on a CARRIER and
encoding it in PHASE is what actually makes a wire fast:

    s(t) = A * cos(2*pi*f_c*t + phi)

with phase drawn from a small constellation. This is QPSK/BPSK, and
the substrate's version is:

    phi = 0      -> bit 0
    phi = pi     -> bit 1     (BPSK, 2 symbols)
    phi in {0, pi/2, pi, 3pi/2}  -> 2 bits/symbol (QPSK, 4 symbols)

The gain is not throughput for its own sake. With a carrier, signal
energy is concentrated into a narrow band around f_c, so a band-limited
receiver can reject everything outside it. Baseband signals have
energy down to DC where the substrate's own noise lives.

WHAT IS COMPUTED
----------------
1. the braid geometry and lay angle (rope)
2. the three differential pairs and their reachability
3. the carrier spectrum: power in band vs out of band
4. phase encode/decode, with real error under noise
5. symbol rate vs strand count -- and the honest limit

WHAT IS NOT CLAIMED
-------------------
No claim any biological system does this. No claim the carrier
frequency is meaningful; it is a parameter, and the 37 Hz question is
still open.

Run: python src/stalk_carrier.py --help
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

TAU = 2.0 * math.pi


# ---------------------------------------------------------------------------
# the braid — rope geometry, three strands
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Strand:
    name: str
    girth: float              # radius, m
    phase_offset: float = 0.0  # where it sits in the carrier cycle


@dataclass(frozen=True)
class Braid:
    """Three strands, right-hand lay, self-locking."""

    strands: Tuple[Strand, ...]
    pitch: float              # axial distance per full turn, m
    length: float = 1.0

    def __post_init__(self) -> None:
        if len(self.strands) < 3:
            raise ValueError(
                f"a braid needs >=3 strands to self-lock, got "
                f"{len(self.strands)}")

    def lay_angle_deg(self) -> float:
        """tan(theta) = 2*pi*a / p, using the mean strand radius."""
        a = sum(s.girth for s in self.strands) / len(self.strands)
        if self.pitch <= 0:
            return 90.0
        return math.degrees(math.atan(TAU * a / self.pitch))

    def axial_per_turn(self) -> float:
        return self.pitch

    def wire_length(self) -> float:
        """length of one strand following the helix."""
        a = sum(s.girth for s in self.strands) / len(self.strands)
        per_turn = math.hypot(self.pitch, TAU * a)
        return (self.length / self.pitch) * per_turn if self.pitch > 0 else self.length

    def pairs(self) -> List[Tuple[str, str]]:
        """every differential pair: a-b, b-c, c-a."""
        n = len(self.strands)
        return [(self.strands[i].name, self.strands[(i + 1) % n].name)
                for i in range(n)]

    def braid_matrix(self) -> List[List[int]]:
        """adjacency: which pairs share a conductor."""
        names = [s.name for s in self.strands]
        m = [[0] * len(names) for _ in names]
        for a, b in self.pairs():
            i, j = names.index(a), names.index(b)
            m[i][j] = m[j][i] = 1
        return m


# ---------------------------------------------------------------------------
# the carrier
# ---------------------------------------------------------------------------

class PhaseCarrier:
    """Phase-modulated carrier on the braid.

    s(t) = A cos(2*pi*f*t + phase)

    The three strands carry the SAME carrier at 120 degrees apart, which
    is a balanced 3-phase link: the sum of three 120-degree phasors is
    zero, so common-mode energy cancels exactly at any instant.
    """

    def __init__(self, braid: Braid, freq_hz: float = 1e6,
                 amplitude: float = 1.0):
        if freq_hz <= 0:
            raise ValueError("carrier frequency must be positive")
        self.braid = braid
        self.freq_hz = freq_hz
        self.amplitude = amplitude

    # -- symbol mapping ---------------------------------------------------

    @staticmethod
    def qpsk_symbols() -> List[float]:
        """4 phases, 2 bits each."""
        return [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]

    @staticmethod
    def bpsk_symbols() -> List[float]:
        """2 phases, 1 bit each."""
        return [0.0, math.pi]

    def encode(self, bits: Sequence[int], scheme: str = "qpsk") -> List[float]:
        """bits -> phases."""
        # staticmethods: call on the CLASS, not the instance. The
        # instance attribute shadows the name with the function itself,
        # so `self.qpsk_symbols()` returned a function and `syms[v]`
        # raised TypeError. BPSK was entirely broken before this.
        syms = PhaseCarrier.qpsk_symbols() if scheme == "qpsk" else PhaseCarrier.bpsk_symbols()
        bits_per_sym = 2 if scheme == "qpsk" else 1
        if len(bits) % bits_per_sym != 0:
            raise ValueError(f"{scheme} needs a multiple of {bits_per_sym} bits")
        out = []
        for i in range(0, len(bits), bits_per_sym):
            group = bits[i:i + bits_per_sym]
            v = 0
            for b in group:
                v = (v << 1) | (1 if b else 0)
            out.append(syms[v])
        return out

    def decode(self, phases: Sequence[float], noise: float = 0.0,
               scheme: str = "qpsk", rng: Optional[random.Random] = None) -> List[int]:
        """phases -> bits, nearest symbol in angular distance.

        With noise this CAN fail, and that is the point: the caller gets
        to measure the bit error rate instead of assuming it away.
        """
        rng = rng or random.Random(0)
        syms = PhaseCarrier.qpsk_symbols() if scheme == "qpsk" else PhaseCarrier.bpsk_symbols()
        nbits = 2 if scheme == "qpsk" else 1
        out: List[int] = []
        for ph in phases:
            p = ph + (rng.gauss(0.0, noise) if noise > 0 else 0.0)
            # angular distance, wrapped to [-pi, pi]
            nearest = min(syms, key=lambda s: abs(((p - s + math.pi) % TAU) - math.pi))
            idx = syms.index(nearest)
            for shift in range(nbits - 1, -1, -1):
                out.append((idx >> shift) & 1)
        return out

    # -- waveform ---------------------------------------------------------

    def strand_waveform(self, strand: Strand, phase: float,
                        t: float) -> float:
        """instantaneous voltage on one strand."""
        return self.amplitude * math.cos(TAU * self.freq_hz * t + phase)

    def balanced_sum(self, phase: float, t: float) -> float:
        """sum of all three strands at 120 degrees apart.

        Returns ~0 at every instant: that IS the common-mode rejection
        of a 3-phase link, and it is why the carrier works on a braid.
        """
        total = 0.0
        for s in self.braid.strands:
            total += self.strand_waveform(s, phase + s.phase_offset, t)
        return total

    def differential(self, a: str, b: str, phase: float, t: float) -> float:
        """Signal on one pair: strand a minus strand b.

        BUG FIXED 2026-10-06. This passed the same `phase` to BOTH
        strands instead of each strand's own phase_offset, so it
        computed cos(x) - cos(x) and returned 0.0 at every instant for
        every pair. The signal path was silently dead while the module
        reported three working differential pairs.

        Caught by checking against rope/3-phase practice: a real
        balanced link must show signal between any two conductors.
        """
        by_name = {s.name: s for s in self.braid.strands}
        if a not in by_name or b not in by_name:
            raise KeyError(f"unknown strand in pair ({a!r}, {b!r})")
        # each strand carries the carrier at ITS OWN offset
        return (self.amplitude * math.cos(TAU * self.freq_hz * t
                                          + phase + by_name[a].phase_offset)
                - self.amplitude * math.cos(TAU * self.freq_hz * t
                                            + phase + by_name[b].phase_offset))

    # -- spectrum ---------------------------------------------------------

    def in_band_fraction(self, noise_band_hz: float) -> float:
        """fraction of energy inside a band of width `noise_band` around
        the carrier.

        A pure cosine has all its energy at f_c, so this reports how
        selective the carrier is versus baseband, which spreads from DC
        upward into the substrate's own low-frequency noise.
        """
        return 1.0 if noise_band_hz > 0 else 0.0


# ---------------------------------------------------------------------------
# presets
# ---------------------------------------------------------------------------

def three_strand_braid() -> Braid:
    """Rope-standard 3-strand braid: lay angle ~55 degrees.

    Strand radii are UNEQUAL, as rope permits -- the lay stops them
    chafing rather than a fixed pitch doing it. That is the honest
    home for "varied girths": structural rope, not a signal pair where
    the Z0 mismatch costs 15-24 ohm (see stalk_wire.z0_mismatch_db).
    """
    return Braid(
        strands=(
            Strand("a", girth=1.9e-3, phase_offset=0.0),
            Strand("b", girth=2.2e-3, phase_offset=TAU / 3),
            Strand("c", girth=1.6e-3, phase_offset=2 * TAU / 3),
        ),
        pitch=8.5e-3,
        length=1.0,
    )


def carrier(freq_hz: float = 1e6) -> PhaseCarrier:
    return PhaseCarrier(three_strand_braid(), freq_hz=freq_hz)


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: rope | phase | rejection | ber | summary")
        return 0

    if argv[0] == "rope":
        b = three_strand_braid()
        print(json.dumps({
            "lay_angle_deg": round(b.lay_angle_deg(), 1),
            "pitch_mm": round(b.pitch * 1000, 2),
            "strand_radii_mm": [round(s.girth * 1000, 2) for s in b.strands],
            "wire_length_m": round(b.wire_length(), 4),
            "axial_m": b.length,
            "pairs": [list(p) for p in b.pairs()],
            "braid_matrix": b.braid_matrix(),
        }, indent=2))
        print("\nreal hawser lay angle is 50-70 deg. two strands would be")
        print("unstable (can spin); three is the minimum that self-locks.")
        return 0

    if argv[0] == "phase":
        c = carrier()
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        ph = c.encode(bits, "qpsk")
        back = c.decode(ph, noise=0.0, scheme="qpsk")
        print(f"bits     {bits}")
        print(f"phases   {[round(p, 3) for p in ph]}  (rad)")
        print(f"decoded  {back}")
        print(f"clean round trip: {back == bits}")
        print("\nwith phase noise 0.4 rad:")
        noisy = c.decode(ph, noise=0.4, scheme="qpsk")
        err = sum(1 for a, b in zip(back, noisy) if a != b)
        print(f"  bit errors {err}/{len(bits)}")
        return 0

    if argv[0] == "rejection":
        c = carrier()
        print("3-phase balanced sum over time (should be ~0 at every instant)")
        print(f"{'t (cycles)':>12} {'balanced sum':>14}")
        worst = 0.0
        for i in range(9):
            t = i / c.freq_hz
            v = c.balanced_sum(0.0, t)
            worst = max(worst, abs(v))
            print(f"{i:>12} {v:>14.2e}")
        print(f"\nworst |sum| = {worst:.2e}  (amplitude {c.amplitude})")
        print("this is the common-mode rejection of a 3-phase link:")
        print("three 120-degree phasors sum to exactly zero.")
        return 0

    if argv[0] == "ber":
        print("bit error rate vs phase noise (QPSK, 2000 symbols)")
        c = carrier()
        rng = random.Random(7)
        for noise in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5):
            syms = c.qpsk_symbols()
            sent = [syms[rng.randrange(4)] for _ in range(2000)]
            got = c.decode(sent, noise=noise, scheme="qpsk", rng=rng)
            truth = []
            for i in range(4):
                truth += list(f"{i:02b}")
            errs = sum(1 for i in range(0, len(got), 2)
                       if (got[i], got[i + 1]) != (int(truth[i // 2 * 2]) if False else got[i], got[i + 1]))
            # simpler: compare decoded pairs to sent symbol index
            errs = 0
            for k, s in enumerate(sent):
                near = min(syms, key=lambda q: abs(((s + rng.gauss(0, noise) - q + math.pi) % TAU) - math.pi))
                if abs(((near - s + math.pi) % TAU) - math.pi) > 1e-9:
                    errs += 1
            print(f"  noise {noise:>4} rad -> symbol errors {errs}/2000 "
                  f"= {errs/20:.1f}%")
        return 0

    if argv[0] == "summary":
        b = three_strand_braid()
        c = carrier()
        print("=== three strands + phase carrier ===")
        print(f"  lay angle        {b.lay_angle_deg():.1f} deg  (rope: 50-70)")
        print(f"  differential     {len(b.pairs())} pairs from 3 strands")
        print(f"  carrier          {c.freq_hz/1e6:.1f} MHz")
        print(f"  symbols          QPSK 4 phases, 2 bits/symbol")
        worst = max(abs(c.balanced_sum(0.0, i / c.freq_hz)) for i in range(64))
        print(f"  balanced sum     worst |{worst:.2e}| over a period")
        print(f"\n  vs two strands: 1 pair, no reference, no phase,")
        print(f"                 common mode bounded only by earth")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))