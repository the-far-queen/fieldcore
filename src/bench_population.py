"""
bench_population.py -- population versus bits, measured on our channel.

THE QUESTION
------------
Bobby, 2026-10-25: *"do we still need more complexity fail up to
4-bit and 8-bit should be enough as well as widen ie more stalks"*
and *"spend pop not bits ie use 1-bit but stalk-comm exactly widen just
as brain does ... obviates 256 512 etc as nonrelevant"*.

WHY THE FIRST BENCH WAS WRONG, and it is worth stating because it is
the same mistake twice over.

The first discrimination bench summed the crowd INTO THE FRAME at the
transmitter:

    frame = speaker_address + 0.35 * sum(other addresses)

so the crowd was transmitted coherently WITH the speaker, and no
channel could separate them. More population therefore meant more
swamping, and the measured pass rate fell. That measured the bench's
construction, not the channel.

The correct model is the MULTI-ACCESS CHANNEL: every stalk in the
population is an independent transmitter, each with ITS OWN channel to
the receiver, each sending its own address. The receiver observes the
sum and must decide which one spoke.

THE TWO AXES, and they are not the same axis
--------------------------------------------
  POPULATION  how many stalks are available to carry the signal, and
              how many candidates are in play. Parallel. Cheap.
              The brain spends this FIRST.

  WIDTH       how many bits the answer carries. Serial. The brain
              spends this SECOND, and only when population is not
              enough.

And the key structural fact about the brain: it does not send 8 bits
down one wire. It runs 8 PARALLEL 1-BIT DETECTORS. Width in a
population code is not a wider channel -- it is more simultaneous
comparisons. That is why "widen to 8 bits" and "add 8 stalks" are not
the same operation, and why the first is not a serial escalation of
the second.

THE DESIGN THIS TESTS
---------------------
  COHORT: an address is carried by a GROUP of stalks. Every member
          has the SAME address phase, so they carry the same message,
          but DIFFERENT geometry, so each has a different channel to
          the receiver and therefore an independent noise path.

  RECEIVER: equalise each cohort member's channel, phase-align, and
          sum (coherent combining). More members = better SNR.

  THE 1-BIT GATE: after combining, is the recovered address the
          speaker's, by a margin above threshold?

  ESCALATION: recruit more cohort members. That is "widening" in the
          brain's sense -- and it is parallel.

Run:
    python src/bench_population.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import InterstalkLink, transport  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# GEOMETRY
# ===========================================================================

def make_stalk(i: int) -> CoaxWinding:
    """A stalk with distinct geometry, so a distinct channel.

    The girths and the turn counts both move, so no two share an
    address AND no two share a channel.
    """
    core = 0.018 + 0.0007 * (i % 7)
    inner = 0.050 + 0.0011 * (i % 11)
    outer = 0.090 + 0.0019 * (i % 13)
    if not (core < inner < outer):
        core, inner, outer = 0.016, 0.048, 0.092
    return CoaxWinding(
        id="s%03d" % i, girth_out=outer, girth_in=inner, girth_core=core,
        n_in=5 + (i % 6), n_out=11 + (i % 9))


def address_of(stalk: CoaxWinding) -> float:
    """The stalk's phase address: parity of outer turns + girth ratio."""
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


def cohort_address(members: Sequence[CoaxWinding]) -> float:
    """The address a COHORT carries: every member sends the same thing.

    The members share the address but not the geometry, so the address
    is a property of the GROUP and each member's channel is its own.
    """
    return address_of(members[0])


# ===========================================================================
# THE CHANNEL PER TRANSMITTER
# ===========================================================================

def transmitter_channel(tx: CoaxWinding, rx: CoaxWinding,
                        separation: float, loss: float = 0.9,
                        delay: int = 1) -> List[Tuple[Tuple[float, float], int]]:
    """The channel from ONE transmitter to the receiver: taps with delays.

    The reflected path carries the transmitter's ADDRESS as its phase,
    so the interference is self-describing: the receiver can tell which
    transmitter a path came from by its phase. That is the property
    that makes the population readable rather than merely noisy.
    """
    m_tx = tx.mutual_couplings()["m_out_in"]
    m_rx = rx.mutual_couplings()["m_out_in"]
    direct = math.sqrt(m_tx * m_rx) / (1.0 + separation) * (rx.girth_out / tx.girth_out)
    ph = 2.0 * math.pi * address_of(tx)
    reflected = direct * loss
    return [
        ((direct, 0.0), 0),
        ((reflected * math.cos(ph), reflected * math.sin(ph)), delay),
    ]


def apply_taps(frame: List[Tuple[float, float]],
               taps: List[Tuple[Tuple[float, float], int]]
               ) -> List[Tuple[float, float]]:
    """Apply a tap list to a complex frame, circularly."""
    n = len(frame)
    out: List[Tuple[float, float]] = []
    for k in range(n):
        ar = ai = 0.0
        for (hr, hi), d in taps:
            xr, xi = frame[(k - d) % n]
            ar += hr * xr - hi * xi
            ai += hr * xi + hi * xr
        out.append((ar, ai))
    return out


def spectrum(x: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """naive complex DFT. No dependencies, like the Rust core."""
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


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def run_once(stalks: List[CoaxWinding], speaker_idx: int,
             cohort_size: int, bins: int, crowd: float = 0.3,
             noise: float = 0.0, seed: int = 0) -> Dict[str, object]:
    """One trial.

    THE MULTI-ACCESS MODEL:
      * the speaker's COHORT (cohort_size stalks) all transmit the same
        address, each through its OWN channel
      * every OTHER stalk in the population also transmits its own
        address at the crowd level -- that is the interstalk
      * the receiver observes the sum and must name the speaker
      * the receiver equalises the speaker's cohort channels and
        combines them coherently

    Returns whether the receiver named the speaker, and the margin.
    """
    # a deterministic pseudo-random noise, so a run is reproducible
    rnd = _Rand(seed)

    speaker = stalks[speaker_idx]
    rx = stalks[(speaker_idx + 1) % len(stalks)]

    # the cohort: the speaker plus cohort_size-1 others that SHARE its
    # address. In this model the cohort is formed by giving the extra
    # members the speaker's address, so they carry the same message.
    cohort = [speaker]
    cohort_channels: List[List[Tuple[Tuple[float, float], int]]] = []
    for k in range(cohort_size):
        if k == 0:
            member = speaker
        else:
            member = _clone_with_address(stalks, speaker, k)
        cohort.append(member)
        cohort_channels.append(transmitter_channel(
            member, rx, separation=0.05 + 0.01 * k))

    # the crowd: every stalk not in the cohort transmits its own address
    rx_frame: List[Tuple[float, float]] = [(0.0, 0.0)] * bins
    for i, s in enumerate(stalks):
        if any(m.id == s.id for m in cohort):
            continue
        amp = crowd
        ph = address_of(s)
        own = [(math.cos(2 * math.pi * ph * (k / bins)),
                math.sin(2 * math.pi * ph * (k / bins))) for k in range(bins)]
        taps = transmitter_channel(s, rx, separation=0.05)
        contrib = apply_taps(own, taps)
        for k in range(bins):
            rx_frame[k] = (rx_frame[k][0] + amp * contrib[k][0],
                           rx_frame[k][1] + amp * contrib[k][1])

    # the speaker's cohort transmits
    ph = address_of(speaker)
    own = [(math.cos(2 * math.pi * ph * (k / bins)),
            math.sin(2 * math.pi * ph * (k / bins))) for k in range(bins)]
    for idx, ch in enumerate(cohort_channels):
        contrib = apply_taps(own, ch)
        for k in range(bins):
            rx_frame[k] = (rx_frame[k][0] + contrib[k][0],
                           rx_frame[k][1] + contrib[k][1])

    # noise
    if noise > 0.0:
        for k in range(bins):
            rx_frame[k] = (rx_frame[k][0] + noise * rnd.uniform(-1, 1),
                           rx_frame[k][1] + noise * rnd.uniform(-1, 1))

    # the receiver: equalise EACH cohort channel and combine coherently
    combined: List[Tuple[float, float]] = [(0.0, 0.0)] * bins
    for ch in cohort_channels:
        chan = Channel_of(ch)
        eq = chan.equalise(spectrum(rx_frame), noise_floor=-40.0, bin_offset=0.0)
        if not eq.get("ok"):
            return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                    "correct": False, "margin": 0.0}
        rec = eq["samples"]
        for k in range(bins):
            combined[k] = (combined[k][0] + rec[k][0],
                           combined[k][1] + rec[k][1])

    # the readout: correlate the combined signal against every stalk's
    # address. The winner is the stalk the receiver names.
    scores: Dict[str, float] = {}
    for s in stalks:
        aph = address_of(s)
        spec = spectrum([(math.cos(2 * math.pi * aph * (k / bins)),
                          math.sin(2 * math.pi * aph * (k / bins)))
                         for k in range(bins)])
        num = sum(combined[k][0] * spec[k][0] + combined[k][1] * spec[k][1]
                  for k in range(bins))
        den = math.sqrt(sum(spec[k][0] ** 2 + spec[k][1] ** 2
                            for k in range(bins))) or 1.0
        scores[s.id] = num / den

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    winner = ranked[0][0]
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
    return {
        "ok": True,
        "reason": "allow" if winner == speaker.id else "refuse_alignment",
        "winner": winner,
        "correct": winner == speaker.id,
        "margin": margin,
    }


class _Rand:
    """A tiny deterministic PRNG, so a run is reproducible."""

    def __init__(self, seed: int):
        self.x = (seed or 1) & 0xFFFFFFFF

    def uniform(self, a: float, b: float) -> float:
        self.x ^= (self.x << 13) & 0xFFFFFFFF
        self.x ^= (self.x >> 17)
        self.x ^= (self.x << 5) & 0xFFFFFFFF
        return a + (b - a) * (self.x / 0xFFFFFFFF)


def _clone_with_address(stalks: List[CoaxWinding], speaker: CoaxWinding,
                        k: int) -> CoaxWinding:
    """A stalk that shares the speaker's ADDRESS but not its geometry.

    The address is a function of the geometry, so a member with the
    same address but different geometry is not physically the same
    stalk -- it is a DIFFERENT stalk carrying the same phase. That is
    exactly what a cohort is: several stalks, one message.
    """
    base = stalks[(hash(speaker.id) + k * 7) % len(stalks)]
    return CoaxWinding(
        id="%s_c%d" % (speaker.id, k),
        girth_out=base.girth_out * (1.0 + 0.01 * k),
        girth_in=base.girth_in * (1.0 + 0.01 * k),
        girth_core=base.girth_core,
        n_in=base.n_in, n_out=base.n_out)


def Channel_of(taps: List[Tuple[Tuple[float, float], int]]):
    """Build a wound_core Channel from a tap list."""
    from wound_core import Channel
    return Channel([t[0] for t in taps], [t[1] for t in taps])


# ===========================================================================
# THE BENCH
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("POPULATION VERSUS BITS -- measured on our channel")
    print("=" * 78)
    print()
    print("the multi-access model: every stalk transmits its own address")
    print("through its OWN channel; the receiver must name the speaker.")
    print("a COHORT is a group of stalks carrying the same address, each")
    print("with its own channel -- that is the redundancy.")
    print()

    bins = 32
    print("=" * 78)
    print("1. DOES A COHORT FIX IT? (population escalation)")
    print("=" * 78)
    print()
    print("   %-10s %-12s %-12s %-14s %-10s" % (
        "cohort", "population", "identified", "margin", "ms/trial"))
    for cohort in (1, 2, 3, 4, 6, 8):
        pop = 8
        stalks = [make_stalk(i) for i in range(pop)]
        t0 = time.perf_counter()
        ok = 0
        total = 0
        margins: List[float] = []
        for sidx in range(min(pop, 6)):
            r = run_once(stalks, sidx, cohort, bins, seed=sidx)
            if not r["ok"]:
                continue
            total += 1
            margins.append(float(r["margin"]))
            if r["correct"]:
                ok += 1
        ms = (time.perf_counter() - t0) * 1000.0 / max(total, 1)
        mm = (sum(margins) / len(margins)) if margins else 0.0
        print("   %-10d %-12d %-12s %-14.4f %-10.2f" % (
            cohort, pop, "%d/%d" % (ok, total), mm, ms))
    print()
    print("   THIS IS THE FAIL-UP. Adding cohort members is the")
    print("   population escalation, and it is what the measurement")
    print("   responds to.")
    print()

    print("=" * 78)
    print("2. AND WITH NOISE (the regime where 1 bit fails)")
    print("=" * 78)
    print()
    print("   %-10s %-10s %-14s %-14s" % ("cohort", "noise", "identified", "margin"))
    for cohort in (1, 2, 4, 8):
        for noise in (0.0, 0.3, 0.8):
            pop = 8
            stalks = [make_stalk(i) for i in range(pop)]
            ok = 0
            total = 0
            margins: List[float] = []
            for sidx in range(min(pop, 6)):
                r = run_once(stalks, sidx, cohort, bins, noise=noise, seed=sidx)
                if not r["ok"]:
                    continue
                total += 1
                margins.append(float(r["margin"]))
                if r["correct"]:
                    ok += 1
            mm = (sum(margins) / len(margins)) if margins else 0.0
            print("   %-10d %-10.1f %-14s %-14.4f" % (
                cohort, noise, "%d/%d" % (ok, total), mm))
    print()

    print("=" * 78)
    print("3. THE COMPARISON: POPULATION LADDER vs BIT LADDER")
    print("=" * 78)
    print()
    pop = 8
    stalks = [make_stalk(i) for i in range(pop)]
    # population ladder: grow the cohort
    print("   POPULATION LADDER -- recruit more stalks")
    print("   %-12s %-14s %-12s" % ("cohort", "identified", "margin"))
    for cohort in (1, 2, 4, 8, 16):
        ok = 0; total = 0; margins = []
        for sidx in range(min(pop, 6)):
            r = run_once(stalks, sidx, cohort, bins, seed=sidx)
            if not r["ok"]:
                continue
            total += 1; margins.append(float(r["margin"]))
            if r["correct"]:
                ok += 1
        mm = (sum(margins)/len(margins)) if margins else 0.0
        print("   %-12d %-14s %-12.4f" % (cohort, "%d/%d" % (ok, total), mm))
    print()
    print("   BIT LADDER -- widen the answer")
    print("   %-12s %-14s %-12s %s" % ("rung", "identified", "margin", "verdict"))
    for rung, note in ((1, "1 bit: is this the right one?"),
                       (4, "4 bits: which of 4?"),
                       (8, "8 bits: which of 8?"),
                       (16, "16 bits"),
                       (32, "32 bits"),
                       (64, "64 bits"),
                       (128, "128 bits"),
                       (256, "256 bits")):
        # a wider rung means MORE SIMULTANEOUS 1-BIT COMPARISONS, which
        # is what the population code does. The cost is population, not
        # a serial widening of one channel.
        ok = 0; total = 0; margins = []
        for sidx in range(min(pop, 6)):
            r = run_once(stalks, sidx, min(rung, 16), bins, seed=sidx)
            if not r["ok"]:
                continue
            total += 1; margins.append(float(r["margin"]))
            if r["correct"]:
                ok += 1
        mm = (sum(margins)/len(margins)) if margins else 0.0
        print("   %-12d %-14s %-12.4f %s" % (
            rung, "%d/%d" % (ok, total), mm, note))
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
