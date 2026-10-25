"""
bench_balance2.py -- THE BALANCE POINT, with the confounds removed.

WHAT WENT WRONG IN bench_balance_point.py, and it is the rule-4 move:
suspect your own code before you call a result physics.

  1. THE ADDRESSES WERE CLUSTERED. `make_population` varied the
     geometry by `i % 7`, `i % 11`, `i % 13`, and the resulting
     addresses came out as:
         0.300000, 0.296935, 0.294118, 0.291519, 0.289116, 0.287980
     -- six addresses within 0.012 of each other. At 128 bins one bin
     is 1/128 = 0.0078 wide, so those stalks were UNRESOLVABLE. The
     name rate fell because the bench was asking the receiver to
     separate things no DFT can separate, not because the crowd
     drowned the signal.

     The address formula is
         address = ((n_out % 2)/2 + (girth_ratio - 1)) % 1
     so the geometry can be chosen to HIT a target address. This bench
     spreads the addresses evenly: address_i = (i + 0.5)/P.

  2. THE UNITS OF THE WIDTH WERE WRONG. The first bench compared
     log2(width) against the reading's capacity. But the ladder's
     width IS a bit count -- W16 means sixteen bits -- so claiming
     "4 bits" for W16 was a units error that made every width look
     unreachable.

  3. THE FRAME LENGTH WAS NOT HELD AGAINST RESOLUTION. Now the
     spacing in bins is reported per row, so a reader can see whether
     the resolution limit or the SNR limit is the binding one.

THE MEASUREMENT
---------------
For each employed population P:

  spacing    the closest pair of addresses, in DFT bins. Must be >> 1.
  taps       the channel's taps: one direct path plus one reflected
             path per other stalk in view.
  width      the channel-DERIVED width in BITS, width_for(taps). The
             repo's own rule: the width comes from the channel, so
             widening and recruiting are the same dial.
  capacity   the reading's Shannon capacity, log2(1 + SNR), measured
             against the speaker's own carrier.
  needed     log2(P): the bits required to NAME among P stalks.
  named      whether the receiver named the speaker, out of P.

THE TRADEOFF, stated as a crossover
-----------------------------------
  width_usable   width <= capacity   -- the ladder's width can be
                   carried by the reading. If width > capacity, the
                   ladder is buying bits the reading cannot hold.
  naming_possible  capacity >= needed -- the reading can carry the
                   names. If capacity < needed, no amount of width
                   helps, because the names do not fit.

And the cost side:
  space   P stalks
  time    the width's serial read

THE BALANCE POINT is where naming_possible and width_usable cross:
below it, population is the only thing that helps; above it, width is
already saturated and the only remaining gain is margin.

Run:
    python src/bench_balance2.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    PairChannel,
    REACH,
    transport,
    width_for,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The amplitude of ONE interfering stalk, relative to the speaker.
CROWD_AMPLITUDES = (0.35, 0.15)

#: The frame length, held FIXED so the resolution limit is constant.
BINS = 128

#: The dB a hard bit decision needs.
DB_PER_BIT = 6.0


# ===========================================================================
# THE POPULATION, WITH EVENLY SPREAD ADDRESSES
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks whose addresses are EVENLY SPREAD over the unit circle.

    THE ADDRESS IS CHOSEN, THEN THE GEOMETRY IS SOLVED FOR IT, because
    the address formula is invertible:

        address = ((n_out % 2)/2 + (girth_ratio - 1)) % 1

    With an even n_out (parity term 0) the target address a gives
    girth_ratio = 1 + a. So the stalk's geometry is DERIVED from its
    address rather than the other way round, which is what a real
    population code would do -- the code assigns the addresses and the
    hardware realises them.

    THE POINT: address_i = (i + 0.5)/n, so the closest pair is
    exactly 1/n apart, i.e. n bins apart at 128 bins. Every stalk is
    resolvable, and any collapse that follows is a CHANNEL limit.
    """
    out: List[CoaxWinding] = []
    for i in range(n):
        a = (i + 0.5) / n
        girth_in = 0.050
        girth_out = girth_in * (1.0 + a)
        girth_core = 0.018
        out.append(CoaxWinding(
            id="p%03d" % i,
            girth_out=girth_out, girth_in=girth_in, girth_core=girth_core,
            n_in=5, n_out=10))          # even n_out -> parity term 0
    return out


def address_of(stalk: CoaxWinding) -> float:
    """The stalk's phase address: parity of outer turns + girth ratio."""
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


def min_spacing_bins(stalks: List[CoaxWinding], bins: int) -> float:
    """The closest pair of addresses, measured in DFT bins.

    A pair closer than about 2 bins cannot be separated by a naive
    DFT with no window, so this is the RESOLUTION limit, reported
    separately from the SNR limit.
    """
    addrs = sorted(address_of(s) for s in stalks)
    best = 1.0
    for i in range(len(addrs)):
        for j in range(i + 1, len(addrs)):
            d = addrs[j] - addrs[i]
            best = min(best, d)
    return best * bins


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


def tone(ph: float, bins: int) -> List[Tuple[float, float]]:
    """The carrier for one address. Phase is the address."""
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins)))
            for k in range(bins)]


# ===========================================================================
# ONE READ
# ===========================================================================

def read(link: InterstalkLink, tx_id: str, rx_id: str,
        in_view: List[str], candidates: List[str],
        crowd_amp: float, bins: int) -> Dict[str, Any]:
    """One exchange through the real channel and the real equaliser."""
    pair: PairChannel = link.pair(tx_id, rx_id, in_view=in_view)
    ch = pair.channel()

    ph_tx = address_of(pair.tx)
    others = [c for c in in_view if c not in (tx_id, rx_id)]
    other_ph = [address_of(link.stalk(c)) for c in others]

    frame: List[Tuple[float, float]] = []
    for k in range(bins):
        acc_r = acc_i = 0.0
        th = 2.0 * math.pi * ph_tx * (k / bins)
        acc_r += math.cos(th)
        acc_i += math.sin(th)
        for op in other_ph:
            th2 = 2.0 * math.pi * op * (k / bins)
            acc_r += crowd_amp * math.cos(th2)
            acc_i += crowd_amp * math.sin(th2)
        frame.append((acc_r, acc_i))

    received = transport(frame, pair, bins)
    rx_spec = spectrum(received)
    eq = ch.equalise(rx_spec, noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "correct": False, "winner": None,
                "margin": 0.0, "snr_db": 0.0, "taps": len(ch.taps)}

    rec = eq["samples"]
    tx_spec = spectrum(tone(ph_tx, bins))
    num = sum(rec[k][0] * tx_spec[k][0] + rec[k][1] * tx_spec[k][1]
              for k in range(bins))
    den = sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2 for k in range(bins))
    scale = (num / den) if den > 1e-18 else 0.0
    sig = abs(scale) ** 2 * den
    noise = sum((rec[k][0] - scale * tx_spec[k][0]) ** 2 +
                (rec[k][1] - scale * tx_spec[k][1]) ** 2 for k in range(bins))
    snr_db = (10.0 * math.log10(sig / noise)
              if noise > 1e-30 and sig > 1e-30 else 0.0)

    scores: Dict[str, float] = {}
    for cand in candidates:
        spec = spectrum(tone(address_of(link.stalk(cand)), bins))
        n_ = sum(rec[k][0] * spec[k][0] + rec[k][1] * spec[k][1]
                 for k in range(bins))
        d_ = math.sqrt(sum(spec[k][0] ** 2 + spec[k][1] ** 2
                           for k in range(bins))) or 1.0
        scores[cand] = n_ / d_
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    winner = ranked[0][0]
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
    return {"ok": True, "correct": winner == tx_id, "winner": winner,
            "margin": margin, "snr_db": snr_db, "taps": len(ch.taps)}


# ===========================================================================
# THE SWEEP
# ===========================================================================

def sweep(population: int, crowd_amp: float, bins: int,
          trials: int = 4, speakers: int = 6) -> Dict[str, Any]:
    stalks = make_population(population)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=bins)
    ids = [s.id for s in stalks]
    view = list(ids)

    named = 0
    total = 0
    unreadable = 0
    snrs: List[float] = []
    margins: List[float] = []
    taps = 0
    t0 = time.perf_counter()
    for _ in range(trials):
        for i in range(min(population, speakers)):
            tx = ids[i]
            rx = ids[(i + 1) % population]
            r = read(link, tx, rx, view, ids, crowd_amp, bins)
            taps = max(taps, int(r["taps"]))
            if not r["ok"]:
                unreadable += 1
                continue
            total += 1
            snrs.append(float(r["snr_db"]))
            margins.append(float(r["margin"]))
            if r["correct"]:
                named += 1

    mean_snr = (sum(snrs) / len(snrs)) if snrs else 0.0
    snr_lin = 10.0 ** (mean_snr / 10.0)
    capacity = math.log2(1.0 + snr_lin)
    width = width_for(taps)
    return {
        "population": population,
        "crowd_amp": crowd_amp,
        "bins": bins,
        "taps": taps,
        "width": width,
        "spacing_bins": min_spacing_bins(stalks, bins),
        "trials": total,
        "named": named,
        "unreadable": unreadable,
        "name_rate": (named / total) if total else 0.0,
        "mean_snr_db": mean_snr,
        "capacity_bits": capacity,
        "needed_bits": math.log2(population),
        "width_usable": capacity >= width,
        "naming_possible": capacity >= math.log2(population),
        "mean_margin": (sum(margins) / len(margins)) if margins else 0.0,
        "seconds": time.perf_counter() - t0,
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE BALANCE POINT -- width against population, confounds removed")
    print("=" * 78)
    print()
    print("  addresses are now EVENLY SPREAD: address_i = (i+0.5)/P, and")
    print("  the geometry is solved from the address, so every stalk is")
    print("  resolvable. frame length fixed at %d bins." % BINS)
    print()

    rows: List[Dict[str, Any]] = []
    for amp in CROWD_AMPLITUDES:
        print("=" * 78)
        print("CROWD AMPLITUDE %.2f per interfering stalk" % amp)
        print("=" * 78)
        print()
        print("  %-4s %-7s %-7s %-6s %-8s %-9s %-9s %-8s %-7s %-6s" % (
            "pop", "spacing", "taps", "width", "named", "snr dB",
            "capacity", "needed", "margin", "cost"))
        print("  " + "-" * 84)
        for pop in (2, 4, 8, 16, 32, 64):
            r = sweep(pop, amp, BINS)
            rows.append(r)
            cost = int(r["width"]) * pop
            print("  %-4d %-7.1f %-7d %-6d %-8s %-9.2f %-9.2f %-8.2f %-7.3f %-6d" % (
                r["population"], r["spacing_bins"], r["taps"], r["width"],
                "%d/%d" % (r["named"], r["trials"]),
                r["mean_snr_db"], r["capacity_bits"], r["needed_bits"],
                r["mean_margin"], cost))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE TWO CROSSOVERS")
    print("=" * 78)
    print()
    print("  width_usable    capacity >= width   the ladder's width can be")
    print("                                  carried by the reading")
    print("  naming_possible capacity >= log2(P) the reading can carry the")
    print("                                  names; if not, no width helps")
    print()
    for amp in CROWD_AMPLITUDES:
        print("  crowd %.2f:" % amp)
        print("    %-4s %-7s %-9s %-9s %-14s %-16s" % (
            "pop", "width", "capacity", "needed", "width usable",
            "naming possible"))
        for r in [x for x in rows if x["crowd_amp"] == amp]:
            print("    %-4d %-7d %-9.2f %-9.2f %-14s %-16s" % (
                r["population"], r["width"], r["capacity_bits"],
                r["needed_bits"],
                "YES" if r["width_usable"] else "NO",
                "YES" if r["naming_possible"] else "NO"))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE BALANCE POINT")
    print("=" * 78)
    print()
    for amp in CROWD_AMPLITUDES:
        sel = [x for x in rows if x["crowd_amp"] == amp]
        # the widest population at which the width is still usable
        w_ok = [x for x in sel if x["width_usable"]]
        # the widest population at which naming still works
        n_ok = [x for x in sel if x["naming_possible"]]
        # the widest population that actually names correctly
        r_ok = [x for x in sel if x["name_rate"] >= 0.5]
        print("  crowd %.2f:" % amp)
        print("    width usable up to population  %s" % (
            max((x["population"] for x in w_ok), default="none")))
        print("    naming possible up to population %s" % (
            max((x["population"] for x in n_ok), default="none")))
        print("    names correctly (>=50%%) up to population %s" % (
            max((x["population"] for x in r_ok), default="none")))
        # the margin at the last working population: the surplus there
        # is what a wider reading would have to earn
        if r_ok:
            last = max(r_ok, key=lambda x: x["population"])
            surplus = last["capacity_bits"] - last["needed_bits"]
            print("    at population %d: capacity %.2f, needed %.2f, "
                  "surplus %.2f bits" % (
                      last["population"], last["capacity_bits"],
                      last["needed_bits"], surplus))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("IS 4-BIT AND 8-BIT ENOUGH?")
    print("=" * 78)
    print()
    print("  a width of W bits can NAME 2^W stalks. the question is")
    print("  whether the reading at that population carries W bits.")
    print()
    for amp in CROWD_AMPLITUDES:
        sel = [x for x in rows if x["crowd_amp"] == amp]
        print("  crowd %.2f:" % amp)
        print("    %-8s %-10s %-12s %-14s %-14s %s" % (
            "width", "names", "population", "capacity", "needed", "verdict"))
        for r in sel:
            w = int(r["width"])
            names = 2 ** w
            if r["capacity_bits"] >= w:
                verdict = "the width FITS"
            elif r["capacity_bits"] >= r["needed_bits"]:
                verdict = "names fit, width does NOT"
            else:
                verdict = "NEITHER: not enough bits"
            print("    %-8d %-10d %-12d %-14.2f %-14.2f %s" % (
                w, names, r["population"], r["capacity_bits"],
                r["needed_bits"], verdict))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE MARGINAL TRADE, PER DOUBLING")
    print("=" * 78)
    print()
    print("  what one more doubling of the population buys, in bits of")
    print("  naming capacity, and what the width does over the same step")
    print()
    for amp in CROWD_AMPLITUDES:
        sel = [x for x in rows if x["crowd_amp"] == amp]
        print("  crowd %.2f:" % amp)
        print("    %-10s %-10s %-12s %-12s %-10s" % (
            "from", "to", "cap before", "cap after", "delta bits"))
        for a, b in zip(sel, sel[1:]):
            delta = float(b["capacity_bits"]) - float(a["capacity_bits"])
            print("    %-10d %-10d %-12.2f %-12.2f %-+10.2f" % (
                a["population"], b["population"], a["capacity_bits"],
                b["capacity_bits"], delta))
        print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
