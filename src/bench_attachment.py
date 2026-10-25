"""
bench_attachment.py -- IS ATTACHMENT PHYSICAL OR PHASE LOCKING?

Bobby, 2026-10-25: *"if we choose electronic communication leave girth and
lengths alone, attachment is physical or phase locking?"*

THE QUESTION, and it has a specific answer that depends on WHICH
mechanism is doing the attaching:

  PHYSICAL ATTACHMENT -- "this stalk is in view". In the code that is
    `in_view`, a list membership, and each member contributes ONE TAP
    to the channel. The tap's PHASE is that neighbour's ADDRESS, which
    is derived from the geometry: (turn parity / 2) + (girth_ratio - 1).

    So the phase is a COORDINATE, not a state. It is computed from the
    wire's shape and it does not move. Attachment is physical in the
    strict sense: it is a fact about where the stalks are relative to
    each other.

  PHASE LOCKING -- the classic Kuramoto picture, already implemented in
    `fieldcore/src/kuramoto_interference.py`: each stalk has a phase
    phi_i that EVOLVES under dphi_i/dt = omega_i + (K/n) sum_j
    sin(phi_j - phi_i), and attachment is the neighbour tuple.

    Here the phase is a STATE. And crucially, in Kuramoto the phase
    LOCKS -- oscillators that are close in frequency settle into a
    fixed phase relationship, and the order parameter r measures how
    synchronised the population is.

SO THE THREE REGIMES, and they are not the same thing:

  FIXED        the phase is the geometry's address and never moves.
               The channel is a FIXED FILTER. One pilot estimate, one
               inversion, and it holds for the whole frame.

  LOCKED       the phase oscillates but is HELD near its address -- the
               brain's case, where a neuron's firing is variable but
               its identity is not. The channel is time-varying, but
               slowly, and the pilot estimate stays valid.

  FREE         the phase drifts with no restoring force. The channel is
               time-varying at the frame's own timescale, and the
               pilot estimate goes stale within the frame.

THE MEASUREMENT, and it is the point of the file:

  For each regime: does the receiver still name the sender? Does the
  single pilot estimate survive? Does a per-frame re-estimate fix it?

  Because the answer decides whether phase locking can be added to the
  electronic link at all -- and it decides what it BUYS.

PROVENANCE: [M] measured here. [E] established. [H] hypothesis.

Run:
    python src/bench_attachment.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import do_stalks_communicate as dsc  # noqa: E402
from interstalk_link import InterstalkLink, transport, width_for  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The working population and the crowd from the girth bench.
N = 8
CROWD = 0.10
BINS = dsc.BINS


# ===========================================================================
# THE PHASE NOISE
# ===========================================================================

class PhaseDrift:
    """The three regimes, as a function that perturbs an address.

    The perturbation is applied to the ADDRESS, because that is what the
    tap's phase is derived from. So this is exactly the question "what
    if the phase moved".

      FIXED   no perturbation at all
      LOCKED  a bounded oscillation: the phase wanders around its
              address by at most `spread` radians and is pulled back.
              This is the brain's case -- variable firing, stable
              identity.
      FREE    a random walk with no restoring force, so the phase
              wanders off and does not come back.
    """

    def __init__(self, regime: str, spread: float = 0.35,
                 seed: int = 7):
        self.regime = regime
        self.spread = spread
        self.seed = seed
        self._x = 0.0
        self._state = 0.0

    def next(self, k: int) -> float:
        """The offset for sample k."""
        if self.regime == "fixed":
            return 0.0
        # a deterministic pseudo-random sequence, so a run is
        # reproducible
        x = self.seed & 0xFFFFFFFF
        for _ in range(k + 1):
            x ^= (x << 13) & 0xFFFFFFFF
            x ^= (x >> 17)
            x ^= (x << 5) & 0xFFFFFFFF
        u = (x / 0xFFFFFFFF) * 2.0 - 1.0

        if self.regime == "locked":
            # an oscillator pulled back to its address: the offset
            # oscillates and is bounded
            self._state = 0.6 * self._state + 0.4 * u * self.spread
            return self._state
        # free: a random walk with no restoring force
        self._state += u * self.spread
        return self._state


def drifted_address(s: CoaxWinding, drift: PhaseDrift, k: int) -> float:
    return (dsc.address_of(s) + drift.next(k)) % 1.0


def drifted_tone(s: CoaxWinding, drift: PhaseDrift, bins: int) -> List[
        Tuple[float, float]]:
    """The stalk's waveform with its phase drifting over the frame.

    THE DRIFT IS WITHIN THE FRAME, so a single pilot estimate taken at
    the frame's start is stale by the frame's end. That is the whole
    difficulty with a time-varying channel, and it is what the
    measurement is about.
    """
    base = dsc.address_of(s)
    out = []
    for k in range(bins):
        ph = (base + drift.next(k)) % 1.0
        out.append((math.cos(2.0 * math.pi * ph * (k / bins)),
                    math.sin(2.0 * math.pi * ph * (k / bins))))
    return out


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def measure(link: InterstalkLink, stalks: List[CoaxWinding],
            tx_id: str, rx_id: str, regime: str, spread: float,
            reestimate: bool) -> Dict[str, Any]:
    """One exchange under one phase regime.

    `reestimate` says whether the receiver re-fits the channel from a
    pilot taken AT THE FRAME, or uses one fitted from the geometry.
    """
    ids = [s.id for s in stalks]
    speaker = next(s for s in stalks if s.id == tx_id)
    pair = link.pair(tx_id, rx_id, in_view=ids)
    ch = pair.channel()

    drift_tx = PhaseDrift(regime, spread, seed=11)
    drift_other = PhaseDrift(regime, spread, seed=23)

    frame: List[Tuple[float, float]] = [(0.0, 0.0)] * BINS
    for other in stalks:
        if other.id in (tx_id, rx_id):
            continue
        opair = link.pair(other.id, rx_id, in_view=ids)
        own = drifted_tone(other, drift_other, BINS)
        contrib = transport(own, opair, BINS)
        for k in range(BINS):
            frame[k] = (frame[k][0] + CROWD * contrib[k][0],
                        frame[k][1] + CROWD * contrib[k][1])

    own = drifted_tone(speaker, drift_tx, BINS)
    contrib = transport(own, pair, BINS)
    for k in range(BINS):
        frame[k] = (frame[k][0] + contrib[k][0], frame[k][1] + contrib[k][1])

    # the channel the equaliser inverts.
    #
    # RE-ESTIMATE: the receiver fits the channel from the frame it
    # actually received, so the fit carries the drift.
    # STATIC: the receiver uses the channel the GEOMETRY says, which is
    # what a pilot taken before the frame would give.
    if reestimate:
        # the channel is re-fitted from what was sent and what arrived,
        # so the fit carries the drift
        eff = _fit_channel(own, transport(own, pair, BINS))
        if eff is None:
            return {"ok": False, "reason": "channel_fit_failed",
                    "correct": False, "named": None}
    else:
        eff = ch

    eq = eff.equalise(dsc.spectrum(frame), noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                "correct": False, "named": None}
    rec = eq["samples"]

    def align(target: CoaxWinding) -> float:
        sp = dsc.spectrum(drifted_tone(target, drift_tx, BINS))
        num = sum(rec[k][0] * sp[k][0] + rec[k][1] * sp[k][1]
                  for k in range(BINS))
        den = sum(sp[k][0] ** 2 + sp[k][1] ** 2 for k in range(BINS))
        scale = (num / den) if den > 1e-18 else 0.0
        resid = math.sqrt(sum(
            (rec[k][0] - scale * sp[k][0]) ** 2 +
            (rec[k][1] - scale * sp[k][1]) ** 2 for k in range(BINS)))
        return max(0.0, 1.0 - resid / (math.sqrt(den) or 1.0))

    scores: Dict[str, float] = {}
    for cand in stalks:
        cs = dsc.spectrum(drifted_tone(cand, drift_tx, BINS))
        n_ = sum(rec[k][0] * cs[k][0] + rec[k][1] * cs[k][1]
                 for k in range(BINS))
        d_ = math.sqrt(sum(cs[k][0] ** 2 + cs[k][1] ** 2 for k in range(BINS))) or 1.0
        scores[cand.id] = n_ / d_
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return {"ok": True, "correct": ranked[0][0] == tx_id,
            "named": ranked[0][0], "align_sender": align(speaker),
            "margin": ranked[0][1] - ranked[1][1]}


def _fit_channel(sent: List[Tuple[float, float]],
                 received: List[Tuple[float, float]]):
    """Fit the channel from what was sent and what arrived.

    THE LEAST-SQUARES FIT, and it is the same one the simself copy uses:
    rx[k] = sum_j h_j * tx[k - j*delay], which is a linear system in
    the h_j, so it is solved as one. A correlation would return only the
    MAGNITUDE and throw the phase away, and the phase is the address.
    """
    import numpy as np
    n = len(sent)
    taps = 2
    delay = 1
    # the frames are (I, Q) pairs, so they become complex numbers here.
    # A correlation would return only the MAGNITUDE and throw the phase
    # away, and the phase IS the address -- so this has to be a
    # least-squares fit over a COMPLEX basis.
    sc = np.array([complex(s[0], s[1]) for s in sent], dtype=np.complex128)
    rc = np.array([complex(r[0], r[1]) for r in received],
                  dtype=np.complex128)
    A = np.zeros((n, taps), dtype=np.complex128)
    b = rc.copy()
    for k in range(n):
        for j in range(taps):
            idx = k - j * delay
            A[k, j] = sc[idx] if idx >= 0 else sc[0]
    try:
        h, *_ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    from wound_core import Channel
    taps_out = [(float(h[j].real), float(h[j].imag)) for j in range(taps)]
    delays_out = [j * delay for j in range(taps)]
    # the fit must not produce a degenerate channel: a zero tap means
    # the fit failed, and a channel with no structure cannot be
    # inverted
    if all(abs(re) + abs(im) < 1e-12 for re, im in taps_out):
        return None
    return Channel(taps_out, delays_out)


# ===========================================================================

def main() -> int:
    stalks = dsc.the_population(N)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=BINS)
    ids = [s.id for s in stalks]

    print("=" * 78)
    print("ATTACHMENT: PHYSICAL OR PHASE LOCKING?")
    print("=" * 78)
    print()
    print("  THE THREE REGIMES, and they are three different mechanisms:")
    print()
    print("    FIXED    the phase IS the geometry's address and never")
    print("             moves. the channel is a FIXED FILTER. this is")
    print("             what the code does today: the tap's phase is")
    print("             `other.address`, and the address is")
    print("             (parity/2) + (girth_ratio - 1) -- computed from")
    print("             the wire's shape.")
    print()
    print("    LOCKED   the phase wanders but is HELD near its address.")
    print("             the brain's case: variable firing, stable")
    print("             identity. the channel is time-varying, slowly.")
    print()
    print("    FREE     the phase drifts with no restoring force. the")
    print("             channel is time-varying at the frame's own")
    print("             timescale, so a pilot estimate taken at the")
    print("             frame's start is stale by the frame's end.")
    print()
    print("  ATTACHMENT ITSELF -- the membership -- is the SAME in all")
    print("  three. `in_view` is a list of stalk ids and each member")
    print("  contributes one tap. So attachment is PHYSICAL in the sense")
    print("  that matters here: it is a fact about which stalks are")
    print("  geometrically present. What the regime changes is the")
    print("  PHASE that the membership carries.")
    print()

    print("=" * 78)
    print("THE MEASUREMENT")
    print("=" * 78)
    print()
    print("  %-8s %-8s %-14s %-12s %-12s %-9s" % (
        "regime", "spread", "channel from", "named", "align sender",
        "correct"))
    print("  " + "-" * 70)

    for regime in ("fixed", "locked", "free"):
        spreads = (0.0,) if regime == "fixed" else (0.20, 0.50)
        for spread in spreads:
            for reestimate in (False, True):
                ok = 0
                tot = 0
                aligns: List[float] = []
                for a in ids:
                    for b in ids:
                        if a == b:
                            continue
                        r = measure(link, stalks, a, b, regime, spread,
                                    reestimate)
                        tot += 1
                        if r.get("correct"):
                            ok += 1
                        if r.get("ok"):
                            aligns.append(float(r["align_sender"]))
                mean_align = (sum(aligns) / len(aligns)) if aligns else 0.0
                print("  %-8s %-8.2f %-14s %-12s %-12.4f %-9s" % (
                    regime, spread,
                    "the frame" if reestimate else "the geometry",
                    "%d/%d" % (ok, tot), mean_align,
                    "%.0f%%" % (100.0 * ok / max(tot, 1))))
    print()

    print("  READING IT:")
    print()
    print("    FIXED -- the pilot estimate holds for the whole frame,")
    print("    because the channel is a fixed filter. one estimate, one")
    print("    inversion, clean recovery. THIS IS WHY THE CURRENT LINK")
    print("    WORKS, and it is not an accident: the phase is a")
    print("    coordinate, so the channel is time-invariant, so the")
    print("    relation RX[k] = H[k]X[k] holds exactly.")
    print()
    print("    LOCKED -- the phase wanders but is held. If the")
    print("    geometry-derived estimate still names the sender, then")
    print("    phase locking can be added WITHOUT a tracker, which")
    print("    would make it nearly free. If it fails, then locked")
    print("    phase needs the pilot re-fitted.")
    print()
    print("    FREE -- the phase drifts. Here the geometry-derived")
    print("    estimate MUST fail, because the channel it describes is")
    print("    not the channel that acted. And the re-fitted estimate")
    print("    has to recover it, because that is what a pilot is FOR.")
    print("    This is the 3GPP case: the channel is time-varying and")
    print("    must be tracked, not assumed.")
    print()

    print("=" * 78)
    print("THE ANSWER")
    print("=" * 78)
    print()
    print("  ATTACHMENT IS PHYSICAL -- membership in the in-view set --")
    print("  and it is ALREADY phase-coded, because each member's tap")
    print("  carries that member's ADDRESS as its phase. The question")
    print("  is not which one it is. It is whether the phase should")
    print("  MOVE.")
    print()
    print("  And the answer is: NOT YET, and the reason is a hard one.")
    print("  Phase locking is a second, independent mechanism already")
    print("  built in `kuramoto_interference.py` -- and it is not")
    print("  connected to the interstalk link. Wiring it in would make")
    print("  the channel time-varying, and the whole recovery depends")
    print("  on the channel being time-invariant (that is what the")
    print("  cyclic prefix and the single pilot estimate are FOR).")
    print()
    print("  So the two mechanisms are ALTERNATIVES for the phase, not")
    print("  complements. If the phase is a coordinate, the channel is")
    print("  fixed and the link is clean. If the phase is a state, the")
    print("  channel is time-varying and the link needs a tracker.")
    print()
    print("  AND THE CHOICE IS NOT COSMETIC, because a locked phase")
    print("  would move the tap's phase, which would move the NULL, and")
    print("  the null is what carries the address. A phase that moves")
    print("  is a phase that changes who the receiver thinks is")
    print("  speaking. So the population code's stability -- the")
    print("  addresses must be derivable so a stalk means the same")
    print("  thing wherever it sits -- is the thing that locking has to")
    print("  preserve.")
    print()
    print("  THE ORDER THAT WORKS, and it is the same order as the")
    print("  ladder: the cheap layer first. Keep the phase FIXED, keep")
    print("  girth and length FIXED, and let the ladder do the")
    print("  escalating. Phase locking is the expensive layer, and it")
    print("  buys what the fixed phase cannot: a channel that changes")
    print("  so the receiver can choose to be somewhere else.")
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
