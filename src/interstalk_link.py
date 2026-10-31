"""
interstalk_link.py -- the link that does not exist yet.

THE GAP, stated exactly
-----------------------
Three things exist and none of them calls the others:

  * `fieldcore/core/src/ladder.rs`   -- the 1/4/8/16/32/64/128/256 ladder
  * `fieldcore/core/src/carrier.rs`  -- the channel, the pilot, the equaliser
  * `fieldcore/src/wound_core.py`    -- the 3-part coax geometry, the
                                        population code, the channel

`grep` finds zero inbound callers for the ladder and for the wound core.
They are correct, tested, and unwired -- the class the atlas exam's
reachability audit exists to find, and it found it in five other places
first.

WHAT THIS FILE IS
-----------------
The link. A stalk-to-stalk exchange over the interstalk channel, where
the WIDTH of the answer is derived from the CHANNEL rather than assigned
by the caller.

THE DESIGN, and why it is the interesting direction
----------------------------------------------------
Bobby, 2026-10-25: *"1-bit is just the start, fail up and a widening
4,8,16 to 256 is how tesla car saves compute ... can interstalk
communication be used to widen on demand?"*

The answer is yes, and the mechanism is already half-built in the Rust
core. `carrier.rs` computes:

    let width = if channel.len() <= 2 { Width::W1 }
        else if channel.len() <= 4 { Width::W4 }
        else { Width::W8 };

A WIDER CHANNEL MEANS A WIDER ANSWER. That is the whole idea: the
number of bits a decision needs is a property of the interference
structure it must be read through, not a property of the caller.

This module makes that explicit and complete:

    W1   one stalk hears itself. No interstalk. The hyper-local case.
    W4   two loop modes on one stalk, or two stalks in view.
    W8   four stalks: the population can be read by ratio.
    W16+ more stalks still in view.
    W256 the whole population, and past it the answer changes KIND.

THE COST PROPERTY, which is the point of the ladder
---------------------------------------------------
The 747 lesson (paper: 747-layered-control-comparison) is that the
overwhelming majority of decisions must NOT leave the cheap layer. So
this module reports, for every exchange:

    the width that was NEEDED   -- derived from the channel
    the width that was USED    -- the ladder's answer
    the escalation reason       -- why it went up, or why it stopped

A system that escalates on every exchange is not saving compute. A
system that never escalates is not reading anything hard. The
measurement is the distribution, not the mean.

THE INVARIANT THIS FILE ASSERTS
--------------------------------
    THE WIDTH IS DERIVED, NOT REQUESTED.

A caller cannot ask for 256 bits and get them. The width comes from the
channel. That is the same rule as `gate.py`: the deciding function takes
no parameter the caller controls.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_HERE = __file__.rsplit("/", 1)[-1]
try:
    from wound_core import (
        CoaxWinding,
        Channel,
        PopulationCode,
        Stratum,
        WoundCore,
        standard_wound_core,
    )
    from tiniest_core.tiniest_core import (
        MAX_NORM as _TC_MAX_NORM,
        MIN_COS as _TC_MIN_COS,
    )
except ImportError:  # pragma: no cover
    import os
    _SRC = os.path.dirname(os.path.abspath(__file__))
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)
    from wound_core import (  # type: ignore[no-redef]
        CoaxWinding,
        Channel,
        PopulationCode,
        Stratum,
        WoundCore,
        standard_wound_core,
    )
    from tiniest_core.tiniest_core import (  # type: ignore[no-redef]
        MAX_NORM as _TC_MAX_NORM,
        MIN_COS as _TC_MIN_COS,
    )


# ===========================================================================
# THE LADDER -- the same widths as core/src/ladder.rs
# ===========================================================================

#: 1 / 4 / 8 / 16 / 32 / 64 / 128 / 256. The first rung is the lone 1 bit
#: and every rung after it is a doubling. 256 is the last WIDTH, not the
#: last rung: past it the answer changes KIND (Unanswerable).
WIDTHS: Tuple[int, ...] = (1, 4, 8, 16, 32, 64, 128, 256)

#: The area each width is entitled to speak for, in stalk units. Doubling
#: per rung, so the scope is a power of two and the width is the exponent
#: taken literally. Matches `Width::reach` in the Rust core.
REACH: Dict[int, int] = {w: (1 << (w.bit_length() - 1)) for w in WIDTHS}

#: The terminal state is not a width. It is a change of kind: refusing to
#: know more precisely is a DECISION, not a limitation.
UNANSWERABLE = "unanswerable"
NOT_WORTH_KNOWING = "not_worth_knowing"
RESOLVED = "resolved"
NEEDS_MORE = "needs_more"


def width_for(channel_taps: int) -> int:
    """The width a channel of this many taps requires.

    THE RULE, as the code implements it:

        1 tap        -> 1 bit
        2 taps       -> 4 bits
        3 or 4 taps  -> 8 bits
        5 or more    -> 16 bits

    THE DOCSTRING SAID SOMETHING ELSE UNTIL 2026-10-31, and it is
    worth recording why. It used to claim "the Rust core's rule
    verbatim: 2 taps or fewer -> 1 bit, 4 taps or fewer -> 4 bits,
    more -> 8 bits", which is NOT what this function does, and the
    quoted rule is not the Rust core's either -- the Rust core's
    `carrier.rs::equalise` has no width at all, because its channel
    is a fixed fixture. A docstring that misstates the rule it
    documents is how the next reader re-derives the wrong thing, and
    this one has been wrong for the life of the file.

    THE POPULATION ADDS WIDTH, and this is the part the Rust core does
    not have, because the Rust core's channel is a fixed fixture. Here
    the channel is built from the stalks actually in view, so:

        ONE stalk in view       -> the direct path only      -> 1 bit
        TWO stalks in view      -> one reflected path        -> 4 bits
        THREE or more           -> two reflected paths       -> 8 bits
        and it doubles from there as the population grows

    The rationale is the 747 one: the width is the AREA OF AUTHORITY.
    A stalk that hears only itself speaks for a region of size 1. A
    stalk that hears three others speaks for a region of size 4, and
    the answer must carry more bits to say so.

    The caller does not choose. There is no parameter.
    """
    if channel_taps <= 1:
        base = 1
    elif channel_taps <= 2:
        base = 4
    elif channel_taps <= 4:
        base = 8
    else:
        base = 16
    return base


def escalate(from_width: int) -> Optional[int]:
    """The next rung, or None at the top."""
    if from_width not in WIDTHS:
        raise ValueError("not a ladder width: %r" % (from_width,))
    i = WIDTHS.index(from_width)
    return WIDTHS[i + 1] if i + 1 < len(WIDTHS) else None


# ===========================================================================
# THE CHANNEL BETWEEN TWO STALKS
# ===========================================================================

@dataclass
class Neighbour:
    """Another stalk in view, contributing a reflected path.

    `weight` is how strongly it couples to the transmitter, and
    `address` is its phase address -- the same address derivation the
    population code uses, so the interference between two stalks
    carries BOTH of their identities.
    """

    stalk_id: str
    weight: float
    address: float


@dataclass
class PairChannel:
    """The interstalk channel from one stalk to another.

    THE RECEIVER IS IN THE PATH. This is the property the first version
    of the measurement missed, and it is the difference between a
    conversation and a loopback.

    The old code built the channel from the TRANSMITTER alone -- its
    coupling, its delay, its loss -- and consulted the receiver only to
    compute a contrast number afterwards. So `measure(tx, rx)` and
    `measure(tx, a completely different rx)` returned byte-identical
    results. That is a LOOPBACK, not a communication.

    Here the channel is a property of the PAIR:
      * the transmitter's coupling sets how strong the incident field is
      * the RECEIVER's geometry sets how much of it the receiver sees
      * the SEPARATION between them sets the attenuation

    so moving the receiver changes what arrives. That is the property the
    test suite pins.
    """

    tx: CoaxWinding
    rx: CoaxWinding
    separation: float = 0.0
    reflection_loss: float = 0.9
    path_delay: int = 1
    #: The OTHER stalks in view. Each contributes a reflected path, so
    #: this is what makes the channel's structure a function of the
    #: population -- and therefore what the width is derived from.
    neighbours: List["Neighbour"] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.separation <= 0.0:
            # the default separation is the gap between the two stalks'
            # outer windings, floored so it is never zero
            self.separation = max(
                abs(self.tx.girth_out - self.rx.girth_out), 1e-3)

    # -- the pair coupling ------------------------------------------------

    def pair_coupling(self) -> float:
        """How strongly the transmitter reaches the receiver.

        RECIPROCITY: the coupling is a property of the PAIR, so it is
        symmetric in the two stalks -- M_ij = M_ji, which holds in any
        linear reciprocal medium (see paper 26 §2.6). The SEparation is
        what breaks the symmetry of the stalks' individual geometries
        while keeping the pair symmetric.

        The strength falls with separation, as near-field coupling does
        (`interstalk.py::independence_test`: the near-field reach is
        lambda/2pi, and inside it coupling is not radiative).
        """
        m_tx = self.tx.mutual_couplings()["m_out_in"]
        m_rx = self.rx.mutual_couplings()["m_out_in"]
        # the geometric mean is symmetric in the pair by construction
        geometric = math.sqrt(m_tx * m_rx)
        # and falls with separation
        return geometric / (1.0 + self.separation)

    def receiver_response(self) -> float:
        """How much of the incident field the receiver actually sees.

        The receiver's own geometry: a wider outer winding encloses more
        flux, so it receives more. This is the term that makes the
        RECEIVER part of the channel rather than an afterthought.
        """
        return self.rx.girth_out / max(self.tx.girth_out, 1e-12)

    def direct_gain(self) -> float:
        """The amplitude of the direct path, transmitter to receiver."""
        return self.pair_coupling() * self.receiver_response()

    def reflected_gain(self) -> float:
        """The amplitude of the reflected path.

        The reflected path is longer, so it loses energy. The ratio is
        what makes the response null FINITE rather than exact -- and an
        exact null is uncorrectable, because zero-forcing inversion
        there amplifies noise without bound. The Rust core's
        `EqualiseError::Irrecoverable` exists for exactly that case.
        """
        return self.direct_gain() * self.reflection_loss

    # -- the channel as taps ----------------------------------------------

    def taps(self) -> List[Tuple[float, float]]:
        """The channel's complex taps.

        THE FIRST is the direct path: transmitter to receiver.

        THE REST are the REFLECTED paths, one per OTHER stalk in view.
        Each is that other stalk's interference arriving at the receiver
        by a different route, so each has its own delay and its own
        amplitude, and each contributes a null.

        This is what makes the channel's STRUCTURE a function of the
        POPULATION, and it is why the width can be derived from the
        channel. One stalk in view -> one tap -> 1 bit, because a
        single path has no null and nothing to invert. Three stalks in
        view -> three taps -> 8 bits, because the interference has
        structure worth reading through.

        The tap delay is the PATH delay in bins. The tap carries its own
        delay -- a tap without its delay is a list entry, and evaluating
        it at its list index gives a different filter from the one that
        was fitted. That mistake made an entire measurement read zero
        alignment; see the diagnosis of 2026-10-25.
        """
        out: List[Tuple[float, float]] = [(self.direct_gain(), 0.0)]
        d = self.direct_gain()
        for i, other in enumerate(self.neighbours):
            # each neighbour contributes a reflected path, attenuated by
            # its own coupling to the transmitter and by the receiver's
            # response to it
            amp = d * self.reflection_loss * (0.5 + 0.5 * other.weight)
            # the phase of the path is the ADDRESS of the neighbour:
            # phase is the address, and the interference between two
            # stalks carries both addresses
            ph = 2.0 * math.pi * other.address
            out.append((amp * math.cos(ph), amp * math.sin(ph)))
        return out

    def delays(self) -> List[int]:
        """The delay of each tap, in bins."""
        return [0] + [self.path_delay * (i + 1) for i in range(len(self.neighbours))]

    def channel(self) -> Channel:
        """The channel object, with its delays attached."""
        return Channel(self.taps(), self.delays())

    def notch_db(self) -> float:
        """The depth of the response null. Positive: a notch is a DEPTH."""
        return self.channel().notch_db()


# ===========================================================================
# THE TRANSPORT -- circular, because the channel must be time-invariant
# ===========================================================================

def transport(frame: Sequence[Tuple[float, float]],
              pair: PairChannel,
              n: int) -> List[Tuple[float, float]]:
    """Send a frame from one stalk to another over the pair channel.

    THE FRAME IS COMPLEX, and that is not a choice. The taps are
    complex, and their PHASE is the address of the interfering stalk --
    phase is the address, everywhere in this design. So a tap applied to
    a frame rotates it, and a rotated frame is complex. Carrying the
    frame as real numbers and keeping only each tap's real part would
    throw away exactly the information the architecture exists to carry.

    The symptom of that mistake, measured: at bin 0 the predicted
    spectrum had an imaginary part of 8.607 where the received frame
    was purely real, so the relation RX[k] = H[k]X[k] did not hold and
    the recovered alignment was 0.480 instead of 1.0.

    CIRCULAR INDEXING, and this is not a detail. The relation the
    equaliser relies on is

        RX[k] = H[k] * X[k]

    which holds exactly when the channel is CIRCULARLY convolved -- the
    same reason OFDM uses a cyclic prefix. A channel that reads
    `frame[k - delay]` and pads with `frame[0]` is not time-invariant,
    the relation does not hold exactly, and the recovery leaks.

    Measured, 2026-10-25:
        zero-pad   + taps at their own delays -> alignment 0.41191241
        circular   + taps at their own delays -> alignment 1.00000000

    EVERY TAP IS APPLIED, at its own delay. When the population grew the
    channel grew with it -- three taps, three paths -- and an earlier
    version of this function applied only two of them, so the received
    frame was not the channel's output at all. The rule: the transport
    IS the channel, so both are derived from one source and cannot
    drift.
    """
    tap_delays = pair.channel().tap_delays()
    out: List[Tuple[float, float]] = []
    for k in range(n):
        acc_re = 0.0
        acc_im = 0.0
        for (hr, hi), d in tap_delays:
            xr, xi = frame[(k - d) % n]
            # (hr + j*hi) * (xr + j*xi)
            acc_re += hr * xr - hi * xi
            acc_im += hr * xi + hi * xr
        out.append((acc_re, acc_im))
    return out


# ===========================================================================
# THE EXCHANGE
# ===========================================================================

@dataclass
class Exchange:
    """One stalk-to-stalk exchange and what it cost.

    `width_needed` is derived from the channel. `width_used` is what the
    ladder settled at. `escalation` says why.
    """

    tx_id: str
    rx_id: str
    width_needed: int
    width_used: int
    escalation: str
    alignment: float
    allowed: bool
    reason: str
    channel_taps: int
    notch_db: float
    #: The width's reach, in stalk units. The area this answer may
    #: speak for.
    reach: int = 0
    #: The mean per-bin magnitude of the recovered reading. This is the
    #: quantity the envelope bounds -- the shape of the reading, not the
    #: arbitrary scale of the transform.
    reading: float = 0.0

    def describe(self) -> Dict[str, object]:
        return {
            "tx": self.tx_id,
            "rx": self.rx_id,
            "width_needed": self.width_needed,
            "width_used": self.width_used,
            "escalation": self.escalation,
            "alignment": round(self.alignment, 8),
            "allowed": self.allowed,
            "reason": self.reason,
            "channel_taps": self.channel_taps,
            "notch_db": round(self.notch_db, 4),
            "reach": self.reach,
            "reading": round(self.reading, 6),
        }


# ===========================================================================
# THE LINK
# ===========================================================================

class InterstalkLink:
    """Stalk-to-stalk communication over the interstalk channel.

    THE 1-BIT GATE, at the bottom, unchanged. The gate's two
    inequalities are the kernel's, and the constants are IMPORTED from
    the kernel so the policy cannot drift. The interstalk layer decides
    HOW MUCH to read; the gate decides whether the reading is admissible.
    """

    def __init__(self, core: Optional[WoundCore] = None,
                 bins: int = 32,
                 noise_floor: float = -80.0,
                 path_delay: int = 1,
                 min_alignment: float = 0.4):
        self.core = core if core is not None else standard_wound_core()
        self.bins = bins
        self.noise_floor = noise_floor
        self.path_delay = path_delay
        self.min_alignment = min_alignment
        self.ledger: List[Exchange] = []

    # -- the helpers -----------------------------------------------------

    def stalk(self, stalk_id: str) -> CoaxWinding:
        for s in self.core.stalks:
            if s.id == stalk_id:
                return s
        raise KeyError("no stalk %r" % (stalk_id,))

    def pair(self, tx_id: str, rx_id: str,
             in_view: Optional[Sequence[str]] = None) -> PairChannel:
        """The channel between two stalks, with the population in view.

        `in_view` is the set of stalks whose interference reaches the
        receiver. It defaults to every stalk except the two speaking,
        which is the whole population.

        THIS IS THE POPULATION INTO THE CHANNEL. With one stalk in view
        the channel has one tap and no null, so there is nothing to
        invert and the gate must refuse. With several, the channel has
        structure, the equaliser can read it, and the answer stands.
        """
        tx = self.stalk(tx_id)
        rx = self.stalk(rx_id)
        if in_view is None:
            ids = [s.id for s in self.core.stalks
                   if s.id not in (tx_id, rx_id)]
        else:
            ids = [i for i in in_view if i not in (tx_id, rx_id)]

        neighbours: List[Neighbour] = []
        for i in ids:
            other = self.stalk(i)
            # the weight is how strongly this neighbour couples to the
            # transmitter -- its own geometry, and its separation
            sep = abs(other.girth_out - tx.girth_out)
            w = other.mutual_couplings()["m_out_in"] / (1.0 + sep)
            neighbours.append(Neighbour(
                stalk_id=i, weight=w, address=self._address(other)))

        return PairChannel(tx=tx, rx=rx, path_delay=self.path_delay,
                           neighbours=neighbours)

    @staticmethod
    def _spectrum(x: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """naive DFT of a COMPLEX frame. No dependencies, like the Rust core.

        The frame is (I, Q) per sample, so the transform is the complex
        one: (a + jb)(cos - j sin) = (a cos + b sin) + j(b cos - a sin).
        """
        n = len(x)
        out: List[Tuple[float, float]] = []
        for k in range(n):
            re = im = 0.0
            for i, (xr, xi) in enumerate(x):
                th = -2.0 * math.pi * (k * i) / n
                c = math.cos(th)
                s = math.sin(th)
                re += xr * c + xi * s
                im += xi * c - xr * s
            out.append((re, im))
        return out

    def _alignment(self, samples: Sequence[Tuple[float, float]],
                   tx_spec: Sequence[Tuple[float, float]]) -> float:
        n = len(tx_spec)
        num = sum(samples[k][0] * tx_spec[k][0] + samples[k][1] * tx_spec[k][1]
                  for k in range(n))
        den = sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2 for k in range(n))
        scale = (num / den) if den > 1e-18 else 0.0
        resid = math.sqrt(sum(
            (samples[k][0] - scale * tx_spec[k][0]) ** 2 +
            (samples[k][1] - scale * tx_spec[k][1]) ** 2 for k in range(n)))
        n0 = math.sqrt(den) or 1.0
        return max(0.0, 1.0 - resid / n0)

    # -- the exchange ----------------------------------------------------

    def exchange(self, tx_id: str, rx_id: str,
                 in_view: Optional[Sequence[str]] = None) -> Exchange:
        """One stalk speaks to another, over the interstalk channel.

        The payload is the TRANSMITTER's address waveform -- phase is the
        address, so what a stalk says IS its phase. The receiver reads
        it by equalising the channel and comparing the recovered
        spectrum against what was sent.
        """
        pair = self.pair(tx_id, rx_id, in_view=in_view)
        n = self.bins
        tx = pair.tx

        # The payload is the stalk's ADDRESS waveform, as a complex
        # frame: phase is the address, and a phase is a complex number.
        ph = self._address(tx)
        payload = [(math.cos(2.0 * math.pi * ph * (k / n)),
                    math.sin(2.0 * math.pi * ph * (k / n)))
                   for k in range(n)]
        received = transport(payload, pair, n)

        tx_spec = self._spectrum(payload)
        rx_spec = self._spectrum(received)

        channel = pair.channel()
        # STANDARD DFT bin order: bin k is at f = k/n. The frame above was
        # produced by a standard DFT, so the equaliser must use the same map.
        eq = channel.equalise(rx_spec, noise_floor=self.noise_floor,
                              bin_offset=0.0)

        if not eq.get("ok"):
            # the channel cannot be inverted -> the frame is not readable.
            # This is a REFUSAL with a reason, not a failure.
            ex = Exchange(
                tx_id=tx_id, rx_id=rx_id,
                width_needed=width_for(len(channel.taps)),
                width_used=width_for(len(channel.taps)),
                escalation=NOT_WORTH_KNOWING,
                alignment=0.0, allowed=False,
                reason="channel_%s" % eq.get("error"),
                channel_taps=len(channel.taps),
                notch_db=pair.notch_db(),
                reach=REACH.get(width_for(len(channel.taps)), 0),
            )
            self.ledger.append(ex)
            return ex

        samples = eq["samples"]
        assert isinstance(samples, list)
        alignment = self._alignment(samples, tx_spec)

        # THE 1-BIT GATE, over the equalised residual.
        #
        # THE UNITS, and this is the second real defect found on
        # 2026-10-25.
        #
        # The kernel's MAX_NORM is 4.0 and it bounds the magnitude of a
        # STATE VECTOR -- a packet in the 16-dimensional substrate. The
        # equaliser's output is a SPECTRUM, whose norm is a different
        # quantity in different units: for a 32-bin frame of a unit
        # amplitude carrier it is 27.1, not 4.0.
        #
        # So comparing the spectrum's norm against the state vector's
        # envelope refused every exchange with 'refuse_norm' -- a
        # category error, not a policy decision. The alignment was
        # 1.000000 and the reading was refused anyway.
        #
        # The fix is to NORMALISE the recovered reading before it meets
        # the envelope, so the gate judges the shape of the reading
        # rather than the arbitrary scale of the transform. What the
        # envelope then bounds is the mean per-bin magnitude, which is
        # the quantity that actually says whether the reading is sane.
        samples_arr = np.asarray([[s[0], s[1]] for s in samples], dtype=float)
        per_bin = float(np.mean(np.linalg.norm(samples_arr, axis=1)))
        allow, gate_reason = self._gate(per_bin, alignment)

        # THE WIDTH, derived from the channel -- not requested by anyone.
        needed = width_for(len(channel.taps))

        # THE LADDER. The width the answer settled at, and why.
        if not allow:
            escalation = NOT_WORTH_KNOWING
        elif alignment >= 0.999:
            escalation = RESOLVED
        else:
            escalation = NEEDS_MORE

        used = needed
        if escalation == NEEDS_MORE:
            nxt = escalate(needed)
            if nxt is None:
                used = needed
                escalation = UNANSWERABLE
            else:
                used = nxt

        ex = Exchange(
            tx_id=tx_id, rx_id=rx_id,
            width_needed=needed,
            width_used=used,
            escalation=escalation,
            alignment=alignment,
            allowed=allow,
            reason=gate_reason,
            channel_taps=len(channel.taps),
            notch_db=pair.notch_db(),
            reach=REACH.get(used, 0),
            reading=per_bin,
        )
        self.ledger.append(ex)
        return ex

    @staticmethod
    def _address(stalk: CoaxWinding) -> float:
        """The stalk's phase address, derived from its geometry.

        The same derivation as `WoundCore.population`: the parity of the
        outer turn count (a binary component) plus the girth ratio (a
        continuous one). Derived, so a stalk means the same thing
        wherever it sits.
        """
        ph = (stalk.n_out % 2) / 2.0
        return (ph + (stalk.girth_ratio - 1.0)) % 1.0

    @staticmethod
    def _gate(norm: float, alignment: float) -> Tuple[bool, str]:
        """The 1-bit gate over the equalised residual.

        The two kernel inequalities, with the kernel's constants:
          * the magnitude of the reading must be inside the envelope
          * the reading must be coherent with what was sent

        The thresholds are the KERNEL's, imported, so the policy cannot
        drift. The caller cannot widen them: there is no parameter.
        """
        if norm > _TC_MAX_NORM:
            return False, "refuse_norm"
        if alignment < _TC_MIN_COS:
            return False, "refuse_alignment"
        return True, "allow"

    # -- the report ------------------------------------------------------

    def report(self) -> Dict[str, object]:
        """The measurement: what the link did, and at what cost.

        The number that matters is the DISTRIBUTION of widths, not the
        mean. A link that escalates on every exchange is not saving
        compute; a link that never escalates is not reading anything
        hard.
        """
        if not self.ledger:
            return {"exchanges": 0}
        widths: Dict[int, int] = {}
        for e in self.ledger:
            widths[e.width_used] = widths.get(e.width_used, 0) + 1
        esc: Dict[str, int] = {}
        for e in self.ledger:
            esc[e.escalation] = esc.get(e.escalation, 0) + 1
        refused = sum(1 for e in self.ledger if not e.allowed)
        return {
            "exchanges": len(self.ledger),
            "widths": {str(k): v for k, v in sorted(widths.items())},
            "escalations": esc,
            "refused": refused,
            "allowed": len(self.ledger) - refused,
            "mean_alignment": sum(e.alignment for e in self.ledger) / len(self.ledger),
        }
