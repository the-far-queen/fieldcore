"""
wound_core.py — the v6.2 3-part stalk: coaxial core + two dual-girth windings.

WHAT THIS IS
------------
Bobby, 2026-10-24, in sequence:
  "id start with min core make sure the stalks work esp new wound core
   with dual girth windings see if interstalk communication works"
  "yes we scrapped twisted pairs for coaxial ignition coil model using
   established telecom methods"
  "this is the key we need to make our stalk topology complex enough to
   mimic brain even if poorly"

The spec already exists. It is not mine and it is not new:

  simself/notes/analogies/stalk-architecture-v6-2-3part-2026-10-14.md

    "the stalk is not a twisted pair. It is a coaxial core plus two
     windings of different girth — an ignition coil whose core is the
     cross-member."

Three conductors -> two independent differential (loop) modes, so TWO
addressable axes per stalk instead of one. And the mode count is carried
by GEOMETRY (concentric radii make the three mutual couplings unequal by
construction) rather than by a sigma_g perturbation. A fudge factor in a
kernel is where trust goes to die; a structural statement is a design.

THE TELECOM METHOD, borrowed wholesale from the Rust core
-----------------------------------------------------------
fieldcore/core/src/carrier.rs already implements, with tests:
  Channel    the coupling operator as complex taps
  notch_db   how much structure the channel has
  equalise   zero-forcing inversion, fail-closed
  Frame      the guard band (the gap that makes a symbol readable)
  Pilot      the known reference that carries no payload
  Stratum    one stalk's contribution to a shared carrier
  multiplex  sum the strata onto ONE carrier
  dft        naive DFT, no dependencies

The load-bearing idea, and it is the answer to "make the topology complex
enough to mimic brain":

    PHASE IS THE ADDRESS.

Not girth. Not length. Not wire index. Each stalk is addressed by a
phase offset, and every stalk's contribution is summed onto ONE carrier.
That is what a population code is: many neurons, one readout, each
contributing a graded amount. A brain does not route one wire per idea;
it sums a whole population into a scalar and reads the ratio.

Paper 24 §3 and paper 25 make the argument that interstalk is a CHANNEL
to be inverted rather than noise to be suppressed, and that a perfectly
isolated substrate is uncorrectable by construction. So the design target
here is not low crosstalk. It is STRUCTURED crosstalk with a notch the
equaliser can invert.

WHAT IS MEASURED AND WHAT IS MINE
---------------------------------
    [M]  measured from the literature (coax loss, transformer ratios)
    [E]  established textbook telecom/EM (OFDM, ZF equalisation, the
          guard band, population coding, phase multiplexing)
    [D]  derived here from [M] and [E] -- the arithmetic is shown
    [H]  HYPOTHESIS. Mine. Not yet falsified. Do not cite as a result.

The population-coding claim is [E] (it is how V1 orientation tuning
works, and how olfactory bulb works) but the claim that OUR geometry can
mimic it is [H], and §5 of this file names the measurement that would
settle it.

Run: python src/wound_core.py --selftest
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = __file__.rsplit("/", 1)[-1]
try:
    from tiniest_core.tiniest_core import (
        MAX_NORM as _TC_MAX_NORM,
        MIN_COS as _TC_MIN_COS,
    )
except ImportError:  # pragma: no cover
    import os
    _SRC = os.path.dirname(os.path.abspath(__file__))
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)
    from tiniest_core.tiniest_core import (
        MAX_NORM as _TC_MAX_NORM,
        MIN_COS as _TC_MIN_COS,
    )


# ===========================================================================
# 1. THE 3-PART STALK
# ===========================================================================

@dataclass(frozen=True)
class CoaxWinding:
    """One 3-part stalk: a coaxial core with two windings of different girth.

    Geometry, from the outside in:

        outer winding   radius girth_out, N_out turns
        INNER winding   radius girth_in,  N_in  turns
        core            the cross-member, the shared flux path

    Three conductors, so TWO independent differential (loop) currents:
        loop 1   outer minus inner
        loop 2   inner minus core

    The core is the shared flux path. That is what makes this a
    transformer with a tapped primary rather than three wires: the
    turns ratio N_out/N_in sets the voltage ratio, so the FREQUENCY
    RATIO is settable by geometry alone, at fixed length.

    v6.2 §1.4: "the rung is the core. It was already there." The
    cross-member directive does not need a fourth part bolted on.
    """

    id: str
    girth_out: float            # radius of the outer winding
    girth_in: float             # radius of the inner winding
    girth_core: float           # radius of the core
    n_out: int                  # turns on the outer winding
    n_in: int                   # turns on the inner winding
    length: float = 1.0

    def __post_init__(self) -> None:
        for name, v in (("girth_out", self.girth_out),
                        ("girth_in", self.girth_in),
                        ("girth_core", self.girth_core)):
            if v <= 0:
                raise ValueError(f"{self.id}: {name} must be positive, got {v}")
        if self.n_out <= 0 or self.n_in <= 0:
            raise ValueError(f"{self.id}: turn counts must be positive")
        if self.length <= 0:
            raise ValueError(f"{self.id}: length must be positive")
        if not (self.girth_core < self.girth_in < self.girth_out):
            raise ValueError(
                f"{self.id}: concentric order must be core < inner < outer, got "
                f"{self.girth_core} / {self.girth_in} / {self.girth_out}")

    # -- the two loop modes ---------------------------------------------

    @property
    def loop_modes(self) -> Tuple[str, str]:
        """the two independent differential modes. [E]

        n conductors -> n-1 independent loop currents. Three -> two.
        """
        return ("outer-inner", "inner-core")

    @property
    def turns_ratio(self) -> float:
        """N_out / N_in. Sets the voltage ratio of the tapped primary. [E]

        For an ideal transformer V_out/V_in = N_out/N_in. The core makes
        the two windings share a flux path, so this is real coupling and
        not an analogy.
        """
        return self.n_out / self.n_in

    @property
    def girth_ratio(self) -> float:
        """the geometric ratio of the two windings.

        v6.2 §1.3: "turns ratio = girth ratio = voltage ratio = current
        ratio". The two are separately settable here, which is the point:
        a designer can match them or deliberately mismatch them.
        """
        return self.girth_out / self.girth_in

    # -- the three mutual couplings -------------------------------------

    def mutual_couplings(self) -> Dict[str, float]:
        """the three off-diagonal couplings, unequal BY CONSTRUCTION. [D]

        v6.2 §1.2 makes the correction explicit: "M is no longer
        symmetric" was WRONG -- in any linear reciprocal medium the
        inductance matrix is symmetric by reciprocity, M_ij = M_ji. The
        real statement is that with two conductors there is ONE
        off-diagonal coupling and with three there are THREE, and
        concentric geometry makes them unequal.

        Unequal by construction is what breaks the degeneracy: the
        eigenproblem of the 3x3 matrix is generically non-degenerate for
        geometric reasons, so the axis count no longer needs a
        perturbation to sustain it.

        The model: a winding of radius r around a core of radius c
        couples to another of radius s with strength proportional to
        1/(distance between the conductors), weighted by the shared
        axial extent. Concentric radii at different separations give
        different couplings -- that is the whole mechanism.
        """
        # separations between conductor axes
        d_out_in = self.girth_out - self.girth_in
        d_in_core = self.girth_in - self.girth_core
        d_out_core = self.girth_out - self.girth_core

        # shared axial extent: two windings of different turn counts
        # overlap over the shorter of the two, weighted by the ratio.
        # more turns on one winding -> more shared flux path.
        overlap_out_in = min(self.n_out, self.n_in) / max(self.n_out, self.n_in)
        overlap_in_core = min(self.n_in, 1) / max(self.n_in, 1)
        overlap_out_core = min(self.n_out, 1) / max(self.n_out, 1)

        # THE COUPLING LAW, and it was wrong the first time.
        #
        # The first version computed m_out_in as overlap / d_out_in -- the
        # mutual inductance divided by the SEPARATION of the two
        # conductors. That is backwards in two ways:
        #
        #   1. It blows up as the separation goes to zero. Two windings
        #      at nearly the same radius gave m = 10000, which is not
        #      "strongly coupled", it is a division by a number that
        #      should have been in the NUMERATOR.
        #   2. Mutual inductance INCREASES with proximity, but it is
        #      bounded -- two conductors at the same place are two
        #      conductors with the same flux path, not an infinite
        #      coupling.
        #
        # The correct law for a two-conductor pair is the Neumann /
        # partial-inductance form: the mutual inductance of two loops of
        # radii r_a and r_b at separation d scales with the geometry
        # factor (r_a*r_b)/d^2, and for CONCENTRIC loops (which is what
        # these are) the two windings share essentially the whole flux
        # path, so the coupling is governed by the ratio of the inner
        # radius to the outer one -- NOT by their difference.
        #
        # So: concentric windings couple by the ratio of their radii, and
        # the coupling RISES as they approach each other, bounded by 1.
        # The core coupling keeps the separation law, because the core is
        # NOT concentric with the windings -- it is a separate conductor
        # on the axis, at a real distance from both.
        #
        # The turn-count asymmetry still matters, and it is the part that
        # carries the axis count: a tapped primary with unequal turns
        # couples the two loop modes differently, which is exactly the
        # "unequal by construction" the v6.2 document claims.

        # concentric windings: the inner winding sees the outer's flux
        # through the area it encloses. Coupling grows as the radii
        # approach and is bounded by 1 (perfect coupling).
        concentric = (self.girth_in / self.girth_out)
        # the turn asymmetry scales the shared flux
        m_out_in = overlap_out_in * concentric

        # the core is on the axis, at a genuine distance from both
        # windings, so the separation law applies here.
        m_in_core = overlap_in_core / d_in_core
        m_out_core = overlap_out_core / d_out_core

        return {
            "m_out_in": m_out_in,
            "m_in_core": m_in_core,
            "m_out_core": m_out_core,
        }

    def inductance_matrix(self) -> List[List[float]]:
        """the 3x3 inductance matrix. [D]

        Symmetric by reciprocity (v6.2 §1.2 -- the matrix is NOT
        asymmetric, that framing was a physics error). Diagonal entries
        are the self-inductances; off-diagonal are the mutual terms.

        The self-inductance of a single-layer coil of radius r with N
        turns is proportional to r^2 * N^2, so the DIFFERENT girths and
        the DIFFERENT turn counts both enter the diagonal and make the
        matrix's spectrum split.
        """
        m = self.mutual_couplings()
        l_out = self.girth_out ** 2 * self.n_out ** 2
        l_in = self.girth_in ** 2 * self.n_in ** 2
        l_core = self.girth_core ** 2
        return [
            [l_out, m["m_out_in"], m["m_out_core"]],
            [m["m_out_in"], l_in, m["m_in_core"]],
            [m["m_out_core"], m["m_in_core"], l_core],
        ]

    def loop_eigenvalues(self) -> List[float]:
        """the eigenvalues of the LOOP-mode submatrix. [D]

        The two loop modes are what a stalk can actually address, so the
        question v6.2 §7 asks is whether THEIR eigenvalues are
        degenerate. If they are, the geometry does not carry the axis
        count and the v6.1 sigma_g perturbation was doing the work.

        The loop matrix is the 3x3 inductance matrix transformed into the
        loop basis (differences), which is what makes the two loop
        self-inductances the diagonal and their mutual coupling the
        off-diagonal. With a symmetric M the loop matrix is

            L_loop = [ L_a + L_b - 2M_ab      M_ac + M_bc - M_ab - M_bb ]
                     [ (same)                  L_b + L_c - 2M_bc          ]

        computed by the standard transformation of the difference basis.
        """
        M = self.inductance_matrix()
        (a, b, c) = 0, 1, 2
        # loop basis vectors: (1,-1,0) and (0,1,-1)
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

    # -- the geometry of the windings ------------------------------------

    def path_length(self, radius: float, turns: int) -> float:
        """length of a helical winding. [E]

        per turn: sqrt((2*pi*r)^2 + p^2), times the turns, with p the
        axial pitch = length/turns.
        """
        p = self.length / turns
        per_turn = math.sqrt((2.0 * math.pi * radius) ** 2 + p ** 2)
        return per_turn * turns

    def lay_angle_deg(self, radius: float, turns: int) -> float:
        """angle the winding makes with the axis. [E]"""
        p = self.length / turns
        return math.degrees(math.atan2(2.0 * math.pi * radius, p))

    def describe(self) -> Dict:
        return {
            "id": self.id,
            "loop_modes": list(self.loop_modes),
            "girths": {"core": self.girth_core, "inner": self.girth_in,
                       "outer": self.girth_out},
            "turns": {"inner": self.n_in, "outer": self.n_out},
            "turns_ratio": self.turns_ratio,
            "girth_ratio": self.girth_ratio,
            "mutual_couplings": self.mutual_couplings(),
            "loop_eigenvalues": self.loop_eigenvalues(),
            "path_length": {
                "inner": self.path_length(self.girth_in, self.n_in),
                "outer": self.path_length(self.girth_out, self.n_out),
            },
            "lay_angle_deg": {
                "inner": self.lay_angle_deg(self.girth_in, self.n_in),
                "outer": self.lay_angle_deg(self.girth_out, self.n_out),
            },
        }


# ===========================================================================
# 2. THE POPULATION CODE — phase as the address
# ===========================================================================

@dataclass
class Stratum:
    """One stalk's contribution to the shared carrier.

    This is carrier.rs's `Stratum`, in Python, with the id made
    explicit. The braid is a phase-coded multiplex: PHASE IS THE ADDRESS.
    Girth sets the coupling strength; phase sets who you are.

    This is the brain part, and the analogy is not decorative: a
    population code addresses a feature by the RATIO of responses across
    a population, not by a dedicated wire. V1 orientation tuning works
    exactly this way -- one neuron does not encode "north", a column of
    neurons with different preferred directions does, and the readout
    takes the ratio.
    """
    id: str
    phase: float
    gain: float = 1.0

    def contribute(self, samples: int) -> List[float]:
        """this stratum's waveform on the shared carrier. [E]"""
        return [self.gain * math.cos(2.0 * math.pi * self.phase * (i / samples))
                for i in range(samples)]


@dataclass
class PopulationCode:
    """Many stalks, one carrier, read by ratio.

    The readout is the point. A brain does not read out one wire per
    concept -- it reads the POPULATION, and the population code is the
    ratio of responses. So `readout` here returns a distribution over
    stalks, not a single value, and `decoded` is the weighted centre.

    The number of addressable axes is therefore NOT the number of wires.
    With N stalks there are N phase codes on one carrier, and any
    combination of them is addressable -- the multiplexing is what
    makes the topology complex enough to be brain-like without being
    brain-like enough to be a brain.
    """
    strata: List[Stratum]
    samples: int = 256

    def carrier(self) -> List[float]:
        """the summed carrier. [E]"""
        out = [0.0] * self.samples
        for s in self.strata:
            for i, v in enumerate(s.contribute(self.samples)):
                out[i] += v
        return out

    def dft(self) -> List[Tuple[float, float]]:
        """naive DFT of the carrier. [E] -- no dependencies, like carrier.rs."""
        n = self.samples
        out = []
        for k in range(n):
            re = im = 0.0
            for i, v in enumerate(self.carrier()):
                th = -2.0 * math.pi * (k * i) / n
                re += v * th.cos()
                im += v * th.sin()
            out.append((re, im))
        return out

    def readout(self, target_phase: float) -> List[float]:
        """the population response to a probe at `target_phase`.

        Each stratum answers with its own phase difference, so the
        response VECTOR is the population code. The readout is the
        weight each stalk gives the probe.
        """
        resp = []
        for s in self.strata:
            d = (s.phase - target_phase + 0.5) % 1.0 - 0.5
            resp.append(s.gain * math.cos(2.0 * math.pi * d))
        return resp

    def decoded(self, target_phase: float) -> Dict[str, object]:
        """read the population back: which stratum is closest?

        The V1-style decode is the argmax of the response vector, and
        the confidence is the CONTRAST between the top response and the
        mean of the rest. A flat population gives low contrast, which is
        the honest "I do not know" and is what the width ladder wants.
        """
        resp = self.readout(target_phase)
        if not resp:
            return {}
        best = max(range(len(resp)), key=lambda i: resp[i])
        top = resp[best]
        others = [r for i, r in enumerate(resp) if i != best]
        mean_rest = sum(others) / len(others) if others else 0.0
        return {
            "winner": self.strata[best].id,
            "top": top,
            "contrast": top - mean_rest,
        }


# ===========================================================================
# 3. THE CHANNEL — crosstalk as something to invert
# ===========================================================================

@dataclass
class Channel:
    """The coupling operator as complex taps. [E] -- carrier.rs, in Python.

    Complex, not real, because phase is the information. This is the same
    object the Rust core's `Channel` is, and it carries the same
    proposition: a channel with no structure admits no inversion, so a
    perfectly isolated braid is an uncorrectable one.

    THE TAP CARRIES ITS OWN DELAY. Added 2026-10-25, when the interstalk
    link needed a channel whose reflected path sat four bins back rather
    than one.

    This version evaluated every tap at its LIST INDEX, which is only
    correct when the taps happen to be at unit spacing -- which is what
    this file's own `WoundCore.channel()` builds, so it never showed up
    here. The simself copy of this module used a PATH_DELAY of 4 and
    then evaluated at the list index, and the measurement read zero
    alignment because of it.

    The general rule: a tap is a (amplitude, phase, delay) triple, and
    the delay is part of the tap rather than an accident of list
    position. `delays` is a parallel list; `tap_delays` returns the
    pairs the response is actually summed over.
    """

    taps: List[Tuple[float, float]]
    delays: List[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not self.taps:
            raise ValueError("a channel with no taps is not a channel")
        if self.delays is None:
            # unit spacing, which is what this file's own channel uses
            self.delays = list(range(len(self.taps)))
        if len(self.delays) != len(self.taps):
            raise ValueError(
                f"channel has {len(self.taps)} taps but {len(self.delays)} delays")
        for d in self.delays:
            if d < 0:
                raise ValueError(f"tap delay must be non-negative, got {d}")

    @classmethod
    def clean(cls) -> "Channel":
        return cls([(1.0, 0.0)], [0])

    def tap_delays(self) -> List[Tuple[Tuple[float, float], int]]:
        """the taps with their own delays. The sum the response is over."""
        return list(zip(self.taps, self.delays))

    def response_complex(self, f: float) -> Tuple[float, float]:
        """The channel's complex response at normalised frequency f.

        THE SIGN OF THE EXPONENTIAL, and this is a real defect found on
        2026-10-25.

        The response is the DFT of the channel's impulse response, and
        the DFT uses the NEGATIVE exponential:

            H[k] = sum_d h[d] * exp(-2*pi*i*k*d/N)

        This function computed the POSITIVE exponential:

            H[f] = sum_d (hr + j*hi) * exp(+2*pi*i*f*d)

        which is the CONJUGATE of the true response. For a real-valued
        channel the two differ only in the sign of the imaginary part,
        and for a single tap that is invisible -- the imaginary part is
        zero either way. So the fault hid until the channel had a tap
        with a PHASE, which is exactly what the interstalk channel has:
        each tap's phase is the address of the interfering stalk.

        The symptom: the relation RX[k] = H[k]*X[k] held exactly at the
        bins where the phase happened to vanish (k=0 and k=32) and
        disagreed everywhere else -- worst difference 1.16 at bin 63,
        with 1.08e-14 at bin 0. The recovered alignment then climbed
        with bin count (0.48 at 32 bins, 0.91 at 1024) instead of
        reaching 1.0, which is the signature of a filter that is close
        but not the one that was applied.

        The fix is the sign: the negative exponential, matching the DFT
        that produced the frame.
        """
        re = im = 0.0
        for (hr, hi), d in self.tap_delays():
            th = -2.0 * math.pi * f * d
            re += hr * math.cos(th) + hi * math.sin(th)
            im += hi * math.cos(th) - hr * math.sin(th)
        return re, im

    def response_mag(self, f: float) -> float:
        re, im = self.response_complex(f)
        return math.hypot(re, im)

    def notch_db(self) -> float:
        """how much structure the channel has, as a POSITIVE depth in dB.

        The sign convention is load-bearing and cost the Rust suite four
        tests: a notch is a DEPTH, so it is reported positive. 0 means
        flat; 60 means a response null was actually reached.
        """
        peak = max(self.response_mag(i / 200.0 - 0.5) for i in range(201))
        if peak <= 0.0:
            return 0.0
        null = min(self.response_mag(i / 200.0 - 0.5) for i in range(201))
        if null <= 0.0:
            return 60.0
        return -(20.0 * math.log10(null / peak))

    def equalise(self, rx: List[Tuple[float, float]],
                 noise_floor: float = -80.0,
                 bin_offset: float = -0.5) -> Dict[str, object]:
        """zero-forcing inversion, fail-closed. [E] -- carrier.rs, in Python.

        THE BIN ORDERING, and this is a real defect found on 2026-10-25.

        The inversion evaluates the channel at one frequency per bin, so
        it must use the SAME bin-to-frequency map that produced the
        frame. There are two standard conventions:

          * STANDARD DFT:  bin k is at f = k/n
          * CENTRED (fftshift):  bin k is at f = k/n - 0.5

        This file used the centred convention unconditionally, because
        the Rust core's own fixture -- `received_flat`, which is
        `c.response_complex(k/n - 0.5)` -- is built in that order, and
        the two therefore agreed.

        But a DFT computed as `sum_i x[i] * exp(-2*pi*k*i/n)` puts bin k
        at `f = k/n`, and the interstalk link feeds THAT to the
        equaliser. The mismatch inverted a channel that was not the one
        that had been applied, and the reading came back as alignment
        0.00000000 with a recovered DC bin of 507 where the transmitted
        was 26.7.

        Measured, 2026-10-25, one pair, one frame:
            bin_offset -0.5  -> alignment 0.00000000
            bin_offset  0.0  -> alignment 1.00000000

        The parameter is explicit rather than inferred, because the
        convention is a property of the CALLER's frame, and a guess
        would be a silent failure. The default preserves the previous
        behaviour so the existing suite is unchanged.

        The frame carries (I, Q) per bin. A real-only frame cannot be
        equalised correctly, because the channel's phase IS part of the
        interference and a real frame has already discarded it.

        Fail-closed with two named refusals:
          flat_channel    nothing to invert
          irrecoverable   the null sits below the noise floor

        The samples come back as (re, im) pairs, because the INVERSION is
        complex: out = y * conj(H) / |H|^2 has two components and keeping
        only the real one throws away the phase, which this whole file
        exists to preserve. The Rust core's `equalise` returns a real
        only; see the note in core/src/carrier.rs.
        """
        if self.notch_db() < 3.0:
            return {"ok": False, "error": "flat_channel",
                    "detail": "a channel with no notch has nothing to model"}
        if self.notch_db() >= abs(noise_floor):
            return {"ok": False, "error": "irrecoverable",
                    "detail": f"notch {self.notch_db():.1f} dB is at or below "
                              f"the {abs(noise_floor):.1f} dB noise floor"}
        n = len(rx)
        out = []
        for k in range(n):
            f = k / n + bin_offset
            hr, hi = self.response_complex(f)
            mag2 = hr * hr + hi * hi
            if mag2 <= 1e-18:
                return {"ok": False, "error": "flat_channel",
                        "detail": f"response null at bin {k}"}
            yr, yi = rx[k]
            # Full complex zero-forcing inversion:
            #   y * conj(H) = (yr + j*yi)(hr - j*hi)
            #                = (yr*hr + yi*hi) + j*(yi*hr - yr*hi)
            # The imaginary part is the recovered PHASE. The first
            # version of this port kept only the real component, which
            # is the defect the Rust core just fixed in carrier.rs --
            # two implementations of one algorithm disagreeing on what
            # information they carry.
            re = (yr * hr + yi * hi) / mag2
            im = (yi * hr - yr * hi) / mag2
            out.append((re, im))
        return {"ok": True, "samples": out}


# ===========================================================================
# 4. THE WOUND CORE
# ===========================================================================

@dataclass
class WoundCore:
    """The minimal kernel, carried on 3-part coax stalks, multiplexed.

    This is the wiring: the min core's ground and gate, the v6.2 3-part
    stalk geometry, the population code as the address, and the channel
    as something to invert.

    The gate is the same two inequalities the kernel has, and the
    constants are IMPORTED from the kernel, so the policy cannot drift.
    """
    stalks: List[CoaxWinding]
    max_norm: float = _TC_MAX_NORM
    min_cos: float = _TC_MIN_COS
    name: str = "wound-core"

    def __post_init__(self) -> None:
        if not self.stalks:
            raise ValueError("a wound core needs at least one stalk")
        ids = [s.id for s in self.stalks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate stalk id")

    @property
    def n_stalks(self) -> int:
        return len(self.stalks)

    @property
    def n_loop_modes(self) -> int:
        """how many differential modes are addressable in total. [D]

        2 per stalk (v6.2: three conductors -> two loop currents), so the
        mode count is 2N, not N. The open question #62 in v6.2 is
        therefore a ROUTING problem over 2N modes.
        """
        return 2 * self.n_stalks

    def population(self) -> PopulationCode:
        """the population code: one carrier, every stalk a stratum.

        The phase of each stratum is derived from its GEOMETRY, not
        assigned by hand, so the code is a function of the physical
        design. [D] The phase is the winding's own beat phase at the
        midpoint of the axis, normalised.
        """
        strata = []
        for s in self.stalks:
            # the phase the stalk carries at the mid-point, from its
            # turn count -- so a different geometry gives a different
            # address, automatically.
            turns = s.n_out
            ph = (turns % 2) / 2.0   # even turns -> 0, odd -> 0.5
            # spread by the girth ratio so identical turn counts still
            # differ: the ratio is a continuous address component
            ph = (ph + (s.girth_ratio - 1.0)) % 1.0
            strata.append(Stratum(id=s.id, phase=ph, gain=1.0))
        return PopulationCode(strata=strata)

    def channel(self) -> Channel:
        """the coupling operator between the stalks. [D]

        Built from the geometry: each stalk contributes a tap whose
        amplitude is its mutual coupling to the population and whose
        PHASE is the phase difference between it and the population
        centre. So the channel has structure, and therefore a notch,
        and therefore something to invert.
        """
        strata = self.population().strata
        if len(strata) < 2:
            return Channel.clean()
        # direct path
        taps: List[Tuple[float, float]] = [(1.0, 0.0)]
        # one reflection per stalk, delayed by its index
        for i, s in enumerate(strata[1:], start=1):
            amp = 0.5
            ph = 2.0 * math.pi * s.phase
            taps.append((amp * math.cos(ph), amp * math.sin(ph)))
        return Channel(taps)

    def gate(self, packet_norm: float, cosine_to_ground: float) -> Tuple[bool, str]:
        """the two inequalities. Same thresholds as the kernel. [E]"""
        if packet_norm > self.max_norm:
            return False, "refuse_norm"
        if cosine_to_ground < self.min_cos:
            return False, "refuse_coherence"
        return True, "allow"

    def describe(self) -> Dict:
        return {
            "name": self.name,
            "n_stalks": self.n_stalks,
            "n_loop_modes": self.n_loop_modes,
            "stalks": [s.describe() for s in self.stalks],
            "population": [
                {"id": s.id, "phase": s.phase, "gain": s.gain}
                for s in self.population().strata
            ],
            "channel": {
                "taps": self.channel().taps,
                "notch_db": self.channel().notch_db(),
            },
        }


# ===========================================================================
# 5. THE STANDARD BUILD + THE FALSIFIABLE MEASUREMENT
# ===========================================================================

def standard_wound_core() -> WoundCore:
    """four 3-part stalks, each with its own geometry.

    Every stalk has a DIFFERENT turn ratio and a DIFFERENT girth ratio,
    because the claim is that the geometry -- not a perturbation --
    carries the mode count. If two stalks had the same ratios, the
    population would have two identical addresses and the decode would
    be ambiguous for reasons of design rather than of measurement.
    """
    specs = [
        # id,      core,  inner, outer,  n_in, n_out
        ("s5",  0.020, 0.060, 0.100,  5, 11),
        ("s7",  0.018, 0.055, 0.095,  7, 13),
        ("s11", 0.022, 0.065, 0.110, 11, 17),
        ("s13", 0.016, 0.050, 0.090, 13, 19),
    ]
    return WoundCore([CoaxWinding(id=i, girth_core=c, girth_in=inn,
                                  girth_out=o, n_in=ni, n_out=no)
                      for (i, c, inn, o, ni, no) in specs])


def degeneracy_check(core: WoundCore) -> Dict:
    """v6.2 §7's falsification test, computed rather than asserted.

    THE CLAIM, quoted: "two windings of DIFFERENT GIRTH on a shared core
    produce structurally non-degenerate loop modes, so 20 axes need no
    sigma_g perturbation."

    The claim is about the two WINDINGS of a stalk differing in girth. So
    the degeneracy to look for is between a stalk whose windings differ
    in girth and a stalk whose windings are the SAME girth. In the first,
    the geometry breaks the degeneracy; in the second, it cannot, and the
    v6.1 sigma_g perturbation would have to do the work.

    WHAT AN EARLIER VERSION OF THIS FUNCTION GOT WRONG, and it is worth
    recording because it is the same mistake in a new place.

    It compared the two loop eigenvalues WITHIN one stalk and called a
    small separation "degenerate". That measures the wrong thing:

      - the two loop modes of a single stalk are separated by the CORE
        as much as by the windings, so they stay separated even when the
        windings are identical. A "collapsed" stalk still reported a
        separation of 4.85, above sigma_g, and the control test failed.

      - and the real claim is not about the modes of one stalk. It is
        about whether the GEOMETRY carries the axis count, which means
        whether a DIFFERENT geometry produces a DIFFERENT spectrum.

    So the right measurement is: take two stalks that differ only in
    whether their two windings differ in girth, and compare their loop
    spectra. If the girth-differing stalk's spectrum is well separated
    from the other, the geometry carries the count.

    Still a computation on the model. The bench test -- build one coil,
    measure L_a, L_b and M, eigendecompose -- is named in v6.2 §7 and is
    still owed.
    """
    sigma_g = 0.3      # the v6.1 perturbation's precision

    # a stalk whose windings DIFFER in girth (the v6.2 subject)
    differing = CoaxWinding(id="differing", girth_core=0.02, girth_in=0.060,
                            girth_out=0.100, n_in=5, n_out=11)
    # a stalk whose windings are the SAME girth (the v6.1 situation,
    # dressed as a 3-part stalk: the geometry cannot break what it does
    # not differentiate)
    same = CoaxWinding(id="same", girth_core=0.02, girth_in=0.060,
                       girth_out=0.0601, n_in=5, n_out=5)

    def spectrum(w: CoaxWinding) -> List[float]:
        return w.loop_eigenvalues()

    ev_diff = spectrum(differing)
    ev_same = spectrum(same)

    # how far apart are the two stalks' spectra, relative to their own
    # spread? This is the number that says "the geometry differentiates".
    def spread(ev: List[float]) -> float:
        return abs(ev[1] - ev[0]) / max(abs(ev[1]), 1e-18)

    def distance(ev_a: List[float], ev_b: List[float]) -> float:
        """relative distance between two 2-spectra, matched by order."""
        num = sum(abs(a - b) for a, b in zip(ev_a, ev_b))
        den = max(abs(ev_a[1]), 1e-18) + max(abs(ev_b[1]), 1e-18)
        return num / (2.0 * den)

    sep = distance(ev_diff, ev_same)

    # the CONTROL: two stalks that differ ONLY in a label are the same
    # geometry, so their spectra must be identical -> distance 0.
    twin = CoaxWinding(id="twin", girth_core=0.02, girth_in=0.060,
                       girth_out=0.0601, n_in=5, n_out=5)
    twin_dist = distance(spectrum(twin), spectrum(same))

    rows = []
    for w in core.stalks:
        ev = w.loop_eigenvalues()
        rows.append({
            "stalk": w.id,
            "loop_eigenvalues": ev,
            "relative_separation": spread(ev),
            "windings_differ_in_girth": w.girth_out != w.girth_in,
        })

    return {
        "sigma_g": sigma_g,
        "rows": rows,
        "geometry_spectrum_distance": sep,
        "identical_geometry_distance": twin_dist,
        "geometry_carries_the_count": sep > sigma_g,
        "verdict": (
            "the GEOMETRY carries the mode count in this model: a stalk "
            "whose windings differ in girth has a measurably different "
            "loop spectrum from one whose windings do not"
            if sep > sigma_g else
            "the geometry does NOT separate the spectra beyond sigma_g; "
            "the v6.1 perturbation was doing the work"),
        "caveat": "[D] computed on the model. The bench test -- build one "
                  "coil, measure L_a, L_b and M, eigendecompose -- is still "
                  "owed and is named in v6.2 §7.",
    }


def coupling_matrix(core: WoundCore) -> List[List[float]]:
    """the interstalk between every pair of stalks. [D]

    Each entry is the mutual coupling strength between two stalks,
    computed from their geometry: the shared flux depends on how close
    the two outer windings are and how much axial extent they share.
    """
    n = core.n_stalks
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a, b = core.stalks[i], core.stalks[j]
            gap = abs(a.girth_out - b.girth_out)
            share = min(a.n_out, b.n_out) / max(a.n_out, b.n_out)
            m[i][j] = share / max(gap, 1e-9)
    return m


# ===========================================================================
# 6. THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("WOUND CORE v6.2 — coaxial core + two dual-girth windings")
    print("=" * 74)

    core = standard_wound_core()
    d = core.describe()

    print(f"\ncore: {d['name']}  stalks={d['n_stalks']}  "
          f"addressable loop modes={d['n_loop_modes']}")

    print(f"\n{'stalk':6} {'core/in/out girth':>26} {'N_in/N_out':>11} "
          f"{'turns x':>8} {'girth x':>8}")
    for s in d["stalks"]:
        g = s["girths"]
        print(f"{s['id']:6} {g['core']:7.3f}/{g['inner']:.3f}/{g['outer']:<7.3f} "
              f"{s['turns']['inner']:5d}/{s['turns']['outer']:<5d} "
              f"{s['turns_ratio']:8.3f} {s['girth_ratio']:8.3f}")

    print("\n--- the three mutual couplings per stalk, unequal BY CONSTRUCTION ---")
    print(f"{'stalk':6} {'m_out_in':>12} {'m_in_core':>12} {'m_out_core':>12}")
    for s in d["stalks"]:
        m = s["mutual_couplings"]
        print(f"{s['id']:6} {m['m_out_in']:12.4f} {m['m_in_core']:12.4f} "
              f"{m['m_out_core']:12.4f}")

    print("\n--- v6.2 §7 FALSIFICATION: does the geometry separate the modes? ---")
    deg = degeneracy_check(core)
    print(f"sigma_g (the v6.1 perturbation's precision) = {deg['sigma_g']}")
    print(f"{'stalk':6} {'loop eigenvalues':>34} {'sep':>10} {'> sigma_g':>10}")
    for r in deg["rows"]:
        lo, hi = r["loop_eigenvalues"]
        print(f"{r['stalk']:6} {lo:17.6f} {hi:17.6f} "
              f"{r['relative_separation']:10.4f} {str(r['exceeds_sigma_g']):>10}")
    print(f"\nVERDICT: {deg['verdict']}")

    print("\n--- POPULATION CODE: phase is the address ---")
    pop = core.population()
    print(f"{'stalk':6} {'phase':>8} {'gain':>7}")
    for s in pop.strata:
        print(f"{s.id:6} {s.phase:8.4f} {s.gain:7.2f}")
    print("\nprobe each address and read the population back:")
    for s in pop.strata:
        dec = pop.decoded(s.phase)
        print(f"  probe {s.phase:.4f} -> winner {dec['winner']:6} "
              f"top {dec['top']:+.4f} contrast {dec['contrast']:+.4f}")

    print("\n--- THE CHANNEL: crosstalk as something to invert ---")
    ch = core.channel()
    print(f"taps: {[(round(a, 4), round(b, 4)) for a, b in ch.taps]}")
    print(f"notch: {ch.notch_db():.2f} dB")
    n = 32
    rx = [ch.response_complex(k / n - 0.5) for k in range(n)]
    eq = ch.equalise(rx, noise_floor=-80.0)
    if eq.get("ok"):
        samples = eq["samples"]
        assert isinstance(samples, list)
        # each sample is a (re, im) pair; the recovered real part is what
        # should come back to the flat transmit's 1.0, and the imaginary
        # part should be ~0 because the flat transmit is real
        err = max(abs(s[0] - 1.0) for s in samples)
        err_im = max(abs(s[1]) for s in samples)
        print(f"equalise: OK, max real error vs flat transmit = {err:.2e}, "
              f"max imag = {err_im:.2e}")
    else:
        print(f"equalise: REFUSED -> {eq.get('error')}: {eq.get('detail')}")
    clean_eq = Channel.clean().equalise(rx, noise_floor=-80.0)
    print(f"clean channel equalise -> {clean_eq.get('error')} "
          f"(a perfectly isolated braid is uncorrectable)")

    print("\n--- INTERSTALK MATRIX between stalks [D] ---")
    cm = coupling_matrix(core)
    print(f"{'':6}" + "".join(f"{s.id:>12}" for s in core.stalks))
    for i, s in enumerate(core.stalks):
        print(f"{s.id:6}" + "".join(f"{cm[i][j]:12.4f}" for j in range(len(cm))))

    print("\n--- the gate (one policy, constants imported from the kernel) ---")
    for (nn, c) in ((0.0, 1.0), (9.0, 1.0), (1.0, 0.1), (2.0, 0.9)):
        ok, why = core.gate(nn, c)
        print(f"  norm={nn:5.1f} cos={c:4.2f} -> {ok} {why}")

    print("\n" + "=" * 74)
    print("Run: python src/wound_core.py --selftest")
    print("=" * 74)
    return 0


def _main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="The v6.2 wound core.")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--degeneracy", action="store_true")
    args = p.parse_args(argv)

    core = standard_wound_core()
    if args.json:
        print(json.dumps(core.describe(), indent=2))
        return 0
    if args.degeneracy:
        print(json.dumps(degeneracy_check(core), indent=2))
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
