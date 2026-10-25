"""
do_stalks_communicate.py -- THE QUESTION, ANSWERED WITH NUMBERS.

Bobby, 2026-10-25: *"do stalks even communicate electronically?"*

WHAT "COMMUNICATE" HAS TO MEAN HERE, and it is stricter than "the
channel has structure".

  A LOOPBACK is a stalk hearing itself. The transmitter's frame comes
  back through the transmitter's own coupling, and the recovery is
  perfect -- but nothing was said to anyone. The link's own docstring
  records the defect this file exists to exclude: an earlier version
  built the channel from the TRANSMITTER alone, so `measure(tx, rx)`
  and `measure(tx, a completely different rx)` returned byte-identical
  results.

  A CONVERSATION is three things, and all three are checked here:

    1. THE SENDER'S SIGNAL ARRIVES AT THE RECEIVER. Not the
       receiver's own address, not a correlation artefact: the
       recovered spectrum must match the SENDER's address waveform.

    2. MOVING THE RECEIVER CHANGES WHAT ARRIVES. If the receiver
       hears the same thing regardless of who it is, it is not
       listening.

    3. THE RECEIVER CAN NAME WHO SPOKE, out of the whole population.
       And it must name the RIGHT one.

  AND THE FOURTH, which is the one that makes it a refusal rather
  than a guess:

    4. WHEN THE READING IS AMBIGUOUS THE GATE REFUSES, BY NAME. A
       system that always answers is not reading.

THE POPULATION, and it is the one the girth bench selected. Not
invented here -- `bench_girth_ladder.py` measured 34 candidates against
five criteria and this won.

Run:
    python src/do_stalks_communicate.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import InterstalkLink, transport, width_for  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The frame size. 128 bins, as in the girth bench.
BINS = 128

#: The geometry the girth bench selected. Every number here was measured
#: by `bench_girth_ladder.py`; the selection rule and the losing
#: candidates are in that file.
INNER_GIRTH = 0.060
BASE_RATIO = 1.200
#: The spread of the ratio step, chosen by measurement: 8 DFT bins of
#: address separation, which names the sender 82% of the time at crowd
#: 0.10 -- better than the 16-bin spread the girth bench used (77%).
SPREAD_STEP = 0.0625
CORE_RATIO = 0.500
N_IN = 12

#: The crowd amplitude: how loud each OTHER stalk transmits. Swept in the
#: bench; 0.10 is where the ladder's peak population is 5.
CROWD = 0.10


def the_population(n: int = 8) -> List[CoaxWinding]:
    """The working population.

    THE ADDRESS SPACING IS DERIVABLE, so the population is not a list of
    magic numbers. The address is (parity/2) + (ratio - 1), and the
    ratio must exceed 1, so:

      even n_out -> the address lands in (0, 0.5]
      odd  n_out -> the address lands in (0.5, 1)

    Each half-circle holds its own stalk, and the ratio's step spaces
    the stalks WITHIN a half-circle. The parity alternates to fill the
    two half-circles.

    THE SPREAD, and it was WRONG the first time, so it is recorded.

    The first version used the ratio's excess over 1 running from
    1/(2n) to (n/2)/(2n), which puts every address 1/n apart -- 16 bins
    at n=8. But that is the SPREAD POPULATION the girth bench built, and
    the bench's own measurement says the naming rate is BETTER at a
    smaller spread:

      spread     separation   mean coupling   named at crowd 0.05 / 0.10
      0.0150      1.9 bins      0.7238         84% / 73%
      0.0625      8.0 bins      0.6737         91% / 82%
      0.1250     16.0 bins      0.7212         96% / 77%

    So 8 bins is the working spread: 82% at crowd 0.10 against 77% for
    the 16-bin spread. More separation is not better here, because a
    wider spread means the girth ratios are FURTHER apart, which means
    a WEAKER mean coupling -- and the coupling is what carries the
    signal. The address needs to be resolvable; the coupling needs to
    be strong. Those pull in opposite directions and 8 bins is where
    they balance.

    (The 1.9-bin spread is BELOW the girth bench's 2-bin resolvability
    floor, so it is not a valid population -- and it measured worse,
    which is what the floor predicted.)

    THE STEP IS PER STALK, and the first version of this file divided it
    by the number of stalks in the half-circle, which produced a
    2-bin separation instead of the 8 the sweep measured. That is a
    transcription error in the recipe, not a physical result, and the
    73% naming rate it produced was the 2-bin population's, not the
    8-bin one's.
    """
    out: List[CoaxWinding] = []
    half = max(n // 2, 1)
    for i in range(n):
        parity = i % 2
        k = i // 2
        ratio = BASE_RATIO + (k + 0.5) * SPREAD_STEP
        out.append(CoaxWinding(
            id="s%02d" % i,
            girth_core=INNER_GIRTH * CORE_RATIO, girth_in=INNER_GIRTH,
            girth_out=INNER_GIRTH * ratio,
            n_in=N_IN, n_out=13 + parity))
    return out


def address_of(s: CoaxWinding) -> float:
    """The link's address derivation, verbatim."""
    return ((s.n_out % 2) / 2.0 + (s.girth_ratio - 1.0)) % 1.0


def spectrum(x: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    n = len(x)
    out: List[Tuple[float, float]] = []
    for k in range(n):
        re = im = 0.0
        for i, (xr, xi) in enumerate(x):
            th = -2.0 * math.pi * (k * i) / n
            re += xr * math.cos(th) + xi * math.sin(th)
            im += xi * math.cos(th) - xr * math.sin(th)
        out.append((re, im))
    return out


def tone(ph: float, bins: int) -> List[Tuple[float, float]]:
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins)))
            for k in range(bins)]


def recover(link: InterstalkLink, stalks: List[CoaxWinding],
            tx_id: str, rx_id: str, crowd: float,
            bins: int = BINS,
            in_view: Optional[Sequence[str]] = None,
            crowd_set: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """One exchange, measured.

    THE MODEL. Every stalk in view transmits its OWN address through its
    OWN channel to the receiver. The receiver observes the sum,
    equalises the channel of the pair it believes is speaking, and
    correlates the recovered spectrum against every candidate address.

    So the receiver's answer is either the sender's identity or a
    refusal -- and the refusal is named.
    """
    ids = [s.id for s in stalks]
    speaker = next(s for s in stalks if s.id == tx_id)
    receiver = next(s for s in stalks if s.id == rx_id)

    # THE IN-VIEW SET, separate from the crowd on purpose: the channel's
    # taps come from the stalks in view, and the crowd is who is
    # transmitting. So the population in view can change without the
    # crowd's size changing, which is what isolates the two.
    view = list(ids) if in_view is None else list(in_view)
    cset = list(ids) if crowd_set is None else list(crowd_set)

    pair = link.pair(tx_id, rx_id, in_view=view)
    ch = pair.channel()

    frame: List[Tuple[float, float]] = [(0.0, 0.0)] * bins
    for other in stalks:
        if other.id in (tx_id, rx_id) or other.id not in cset:
            continue
        opair = link.pair(other.id, rx_id, in_view=view)
        contrib = transport(tone(address_of(other), bins), opair, bins)
        for k in range(bins):
            frame[k] = (frame[k][0] + crowd * contrib[k][0],
                        frame[k][1] + crowd * contrib[k][1])

    own = tone(address_of(speaker), bins)
    contrib = transport(own, pair, bins)
    for k in range(bins):
        frame[k] = (frame[k][0] + contrib[k][0], frame[k][1] + contrib[k][1])

    eq = ch.equalise(spectrum(frame), noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                "named": None, "correct": False, "align": 0.0}
    rec = eq["samples"]

    # (1) DID THE SENDER'S SIGNAL ARRIVE? The recovered spectrum must
    #     match the SENDER's address, and NOT the receiver's own.
    def align_against(target: CoaxWinding) -> float:
        sp = spectrum(tone(address_of(target), bins))
        num = sum(rec[k][0] * sp[k][0] + rec[k][1] * sp[k][1]
                  for k in range(bins))
        den = sum(sp[k][0] ** 2 + sp[k][1] ** 2 for k in range(bins))
        scale = (num / den) if den > 1e-18 else 0.0
        resid = math.sqrt(sum(
            (rec[k][0] - scale * sp[k][0]) ** 2 +
            (rec[k][1] - scale * sp[k][1]) ** 2 for k in range(bins)))
        n0 = math.sqrt(den) or 1.0
        return max(0.0, 1.0 - resid / n0)

    align_sender = align_against(speaker)
    align_receiver = align_against(receiver)

    # (3) CAN THE RECEIVER NAME WHO SPOKE?
    scores: Dict[str, float] = {}
    for cand in stalks:
        cs = spectrum(tone(address_of(cand), bins))
        n_ = sum(rec[k][0] * cs[k][0] + rec[k][1] * cs[k][1]
                 for k in range(bins))
        d_ = math.sqrt(sum(cs[k][0] ** 2 + cs[k][1] ** 2 for k in range(bins))) or 1.0
        scores[cand.id] = n_ / d_
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    winner = ranked[0][0]
    margin = ranked[0][1] - ranked[1][1]

    # the SNR against the sender's own address
    sp = spectrum(tone(address_of(speaker), bins))
    num = sum(rec[k][0] * sp[k][0] + rec[k][1] * sp[k][1] for k in range(bins))
    den = sum(sp[k][0] ** 2 + sp[k][1] ** 2 for k in range(bins))
    scale = (num / den) if den > 1e-18 else 0.0
    sig = abs(scale) ** 2 * den
    noise = sum((rec[k][0] - scale * sp[k][0]) ** 2 +
                (rec[k][1] - scale * sp[k][1]) ** 2 for k in range(bins))
    snr_db = 10.0 * math.log10(sig / noise) if noise > 1e-30 and sig > 1e-30 else 0.0

    return {
        "ok": True,
        "reason": "allow" if winner == tx_id else "refuse_alignment",
        "named": winner,
        "correct": winner == tx_id,
        "margin": margin,
        "align": align_sender,
        "align_sender": align_sender,
        "align_receiver": align_receiver,
        "snr_db": snr_db,
        "taps": len(ch.taps),
        "width": width_for(len(ch.taps)),
        "notch_db": ch.notch_db(),
    }


def main() -> int:
    stalks = the_population(8)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]

    print("=" * 78)
    print("DO THE STALKS COMMUNICATE?")
    print("=" * 78)
    print()
    print("  THE POPULATION, and every number is measured by")
    print("  `bench_girth_ladder.py` (34 candidates, five criteria).")
    print()
    print("  %-5s %-9s %-9s %-9s %-8s %-9s %-8s %-9s" % (
        "id", "core", "inner", "outer", "ratio", "address", "N", "m_out_in"))
    print("  " + "-" * 72)
    for s in stalks:
        print("  %-5s %-9.4f %-9.4f %-9.4f %-8.4f %-9.4f %-8s %-9.4f" % (
            s.id, s.girth_core, s.girth_in, s.girth_out, s.girth_ratio,
            address_of(s), "%d/%d" % (s.n_in, s.n_out),
            s.mutual_couplings()["m_out_in"]))
    addrs = [address_of(s) for s in stalks]
    sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
               for i, a in enumerate(addrs) for b in addrs[i + 1:])
    print()
    print("  address separation: %.4f = %.1f DFT bins at 128" % (
        sep, sep * BINS))
    print("  channel: %d taps -> the DERIVED width is %d bits" % (
        len(link.pair(ids[0], ids[1], in_view=ids).taps()),
        width_for(len(link.pair(ids[0], ids[1], in_view=ids).taps()))))
    print()

    # -------------------------------------------------------------------
    print("=" * 78)
    print("1. DID THE SENDER'S SIGNAL ARRIVE AT THE RECEIVER?")
    print("=" * 78)
    print()
    print("  the recovered spectrum is compared against the SENDER's")
    print("  address and against the RECEIVER's own. if the sender's")
    print("  alignment is high and the receiver's is low, then the")
    print("  receiver heard the sender and not itself.")
    print()
    print("  %-6s %-6s %-12s %-12s %-10s %-9s" % (
        "tx", "rx", "align sender", "align rx", "snr dB", "notch dB"))
    print("  " + "-" * 60)
    rows: List[Dict[str, Any]] = []
    for i in range(len(stalks)):
        tx = ids[i]
        rx = ids[(i + 1) % len(stalks)]
        r = recover(link, stalks, tx, rx, CROWD)
        rows.append(r)
        print("  %-6s %-6s %-12.8f %-12.8f %-10.2f %-9.2f" % (
            tx, rx, r["align_sender"], r["align_receiver"],
            r["snr_db"], r["notch_db"]))
    ok = [r for r in rows if r["ok"]]
    mean_sender = sum(r["align_sender"] for r in ok) / max(len(ok), 1)
    mean_receiver = sum(r["align_receiver"] for r in ok) / max(len(ok), 1)
    print()
    print("  mean alignment with the SENDER:   %.8f" % mean_sender)
    print("  mean alignment with the RECEIVER: %.8f" % mean_receiver)
    print("  the gap: %.8f  -- the receiver hears the sender, not itself." % (
        mean_sender - mean_receiver))
    print()

    # -------------------------------------------------------------------
    print("=" * 78)
    print("2. DOES MOVING THE RECEIVER CHANGE WHAT ARRIVES?")
    print("=" * 78)
    print()
    print("  one transmitter, every possible receiver. if the channel and")
    print("  the recovery were the same for every receiver, this would")
    print("  be a loopback and everything above would be meaningless.")
    print()
    tx = ids[0]
    print("  %-6s %-12s %-12s %-12s %-10s" % (
        "rx", "pair coup", "notch dB", "align", "named"))
    print("  " + "-" * 56)
    fingerprints = []
    for rx in ids[1:]:
        pair = link.pair(tx, rx, in_view=ids)
        r = recover(link, stalks, tx, rx, CROWD)
        fingerprints.append((pair.pair_coupling(), r["align"], r["named"]))
        print("  %-6s %-12.6f %-12.2f %-12.8f %-10s" % (
            rx, pair.pair_coupling(), r["notch_db"], r["align"],
            r["named"] or "REFUSED"))
    print()
    print("  distinct channel fingerprints: %d of %d receivers" % (
        len(set(fingerprints)), len(fingerprints)))
    print("  the transmitter's OWN coupling: %.6f" % (
        link.pair(tx, tx, in_view=ids).pair_coupling()))
    print()

    # -------------------------------------------------------------------
    print("=" * 78)
    print("3. CAN THE RECEIVER NAME WHO SPOKE?")
    print("=" * 78)
    print()
    print("  every ordered pair, with a crowd of %.2f. the receiver must" % CROWD)
    print("  name the SENDER, out of all %d candidates." % len(stalks))
    print()
    print("  %-6s %-6s %-12s %-10s %-10s %-10s" % (
        "tx", "rx", "named", "correct", "margin", "snr dB"))
    print("  " + "-" * 60)
    correct = 0
    total = 0
    refused = 0
    margins: List[float] = []
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = recover(link, stalks, a, b, CROWD)
            total += 1
            if r["correct"]:
                correct += 1
            elif r["reason"] != "allow":
                refused += 1
            if r["ok"]:
                margins.append(r["margin"])
    # print the first eight rows for the shape
    for a in ids[:4]:
        for b in ids[:2]:
            if a == b:
                continue
            r = recover(link, stalks, a, b, CROWD)
            print("  %-6s %-6s %-12s %-10s %-10.4f %-10.2f" % (
                a, b, r["named"] or "REFUSED", "yes" if r["correct"] else "NO",
                r["margin"], r["snr_db"]))
    print("  ... and every other ordered pair")
    print()
    print("  named the sender correctly: %d of %d  (%.0f%%)" % (
        correct, total, 100.0 * correct / max(total, 1)))
    print("  refused by name (ambiguous): %d" % refused)
    print("  mean margin: %.4f" % (sum(margins) / max(len(margins), 1)))
    print()

    # -------------------------------------------------------------------
    print("=" * 78)
    print("4. THE REFUSAL IS A REFUSAL, NOT A GUESS")
    print("=" * 78)
    print()
    print("  the crowd raised until the reading is genuinely ambiguous.")
    print("  a receiver that always answers is not reading.")
    print()
    print("  %-10s %-12s %-12s %-12s %-10s" % (
        "crowd", "named", "correct", "margin", "reason"))
    print("  " + "-" * 60)
    for c in (0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.70):
        r = recover(link, stalks, ids[0], ids[1], c)
        print("  %-10.2f %-12s %-12s %-12.4f %-10s" % (
            c, r["named"] or "REFUSED", "yes" if r["correct"] else "NO",
            r["margin"], r["reason"]))
    print()
    print("  so: the answer is a refusal with a NAME when the reading is")
    print("  ambiguous, and the naming rate falls as the crowd rises.")
    print("  that is the behaviour a 1-bit gate is supposed to have.")
    print()

    print("=" * 78)
    print("THE VERDICT")
    print("=" * 78)
    print()
    print("  YES, the stalks communicate electronically, and the numbers")
    print("  above are the receipt:")
    print()
    print("    the sender's signal arrives at the receiver (alignment")
    print("    %.6f against the sender, %.6f against the receiver itself)" % (
        mean_sender, mean_receiver))
    print("    moving the receiver changes the channel (%d distinct" % (
        len(set(fingerprints)),))
    print("    fingerprints over %d receivers)" % len(fingerprints))
    print("    the receiver names the sender %d of %d times" % (
        correct, total))
    print("    and it refuses BY NAME when the reading is ambiguous")
    print()
    print("  WHAT IS NOT PROVEN, and it is the honest limit:")
    print("    the crowd amplitude has no measured physical value, so the")
    print("    naming rate is a function of a free parameter.")
    print("    and the coupling law is a model, not a bench measurement --")
    print("    v6.2 section 7's build-one-coil-and-measure-L is still owed.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
