"""
bench_tradeoff.py -- THE BALANCE POINT, with the confounds separated.

THE QUESTION, verbatim, 2026-10-25:
  "calculate optimal number of pop increase ie number of stalks employed
   versus when to increase bits, there must be a tradeoff at some point
   where bit increase helps more than increasing pop further also second
   calculate whether 4-bit and 8-bit is enough or should increase pop
   again or go to 32,64?"

WHAT THE DIAGNOSIS FOUND, and it changed the design of this bench
-------------------------------------------------------------------
`diag_balance.py` ran four experiments. The results that matter:

  EXP 1 (no crowd): naming was 24/24 at EVERY population up to 64, with
       63 taps, and the SNR was 274 dB. So the channel and the
       equaliser handle a large tap count fine. The equaliser is NOT
       the limit.

  EXP 2 (population 16, crowd varied): 0.00 -> 24/24, 0.02 -> 24/24,
       0.05 -> 4/24, 0.15 -> 0/24. So the CROWD is what kills it.

  EXP 3 (taps capped, population not): the caps were a CONFOUND --
       capping `in_view` reduced the frame's crowd as well as the
       channel's taps, so the experiment changed two things at once and
       proved nothing. This bench separates them: the crowd's members
       and the channel's reflected paths are now INDEPENDENT.

  EXP 4 (crowd scaled down with population): still collapsed at
       population 16, so a fixed aggregate interference budget does not
       rescue it either.

So the crowd is the limit, and the interesting question becomes: WHY
does more population cost more than it gives?

THE ANSWER THE MEASUREMENT POINTS AT, and this is the mechanism
------------------------------------------------------------------
The equaliser is zero-forcing: it inverts the channel, so it multiplies
each frequency bin by 1/H(f). A channel with T taps has T notches, and
a notch is where |H(f)| is smallest. An interferer that lands near a
notch is therefore amplified ENORMOUSLY by the equaliser, and as T
grows the notches get deeper AND more numerous, so more of the crowd
lands on one.

That is the real tradeoff, and it is a design consequence rather than a
law of nature:

  RECRUITING MORE STALKS
    gives  more addresses to name        (log2(P) bits)
    but adds  taps to the channel        (T = P reflected paths)
    which deepens the notches
    which amplifies whichever interferers sit on them

  WIDENING THE READING
    gives  more serial bits on the same channel
    but costs TIME, not space

So the balance point is where the marginal bit of NAMING, bought with a
stalk, costs more SNR than the marginal bit of WIDTH, bought with time.

THE MEASUREMENTS, per cell of the grid
--------------------------------------
  P          the population in view -- how many stalks exist
  T          the channel's reflected paths -- how many taps
  width      the channel-DERIVED width in bits, width_for(T+1). The
             repo's own rule: the width comes from the channel, so
             widening and recruiting are ONE dial, not two.
  crowd      the interfering stalks in the frame. INDEPENDENT of T.
  named      whether the receiver named the speaker, out of P candidates
  capacity   the reading's Shannon capacity, log2(1+SNR)
  needed     log2(P): the bits required to name among P
  noise_gain the equaliser's mean |1/H|^2 over the bins: how much the
             equaliser amplifies what it did not want
  cost       width * P: the ladder's own cost measure

Run:
    python src/bench_tradeoff.py
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
    REACH,
    transport,
    width_for,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The frame length, fixed so the resolution limit is constant.
BINS = 128

#: The per-interferer amplitude. Fixed across the grid, so the only
#: things that change are P, T, and the width.
CROWD_AMP = 0.15

#: The populations.
POPS: Tuple[int, ...] = (2, 4, 8, 16, 32, 64)

#: The reflected-path counts. T = 0 means the direct path only, which
#: is the hyperlocal case: the stalk hears itself and nothing else.
TAPS: Tuple[int, ...] = (0, 1, 3, 7, 15, 31)

#: The dB a hard bit decision needs.
DB_PER_BIT = 6.0


# ===========================================================================
# THE POPULATION WITH EVENLY SPREAD ADDRESSES
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks whose addresses are evenly spread, and whose geometry is
    SOLVED FROM the address.

    The address formula is
        address = ((n_out % 2)/2 + (girth_ratio - 1)) % 1
    so with an even n_out (parity term 0) a target address a gives
    girth_ratio = 1 + a. The code assigns the addresses; the hardware
    realises them. address_i = (i + 0.5)/n, so the closest pair is
    exactly n bins apart at 128 bins and every stalk is resolvable.

    THIS FIXED A CONFOUND: the first bench's generator produced
    addresses clustered within 0.012 of each other, which is under two
    DFT bins -- so it was asking the receiver to separate things no
    transform could separate, and then reporting that as a limit of the
    design.
    """
    out: List[CoaxWinding] = []
    for i in range(n):
        a = (i + 0.5) / n
        girth_in = 0.050
        out.append(CoaxWinding(
            id="p%03d" % i,
            girth_out=girth_in * (1.0 + a), girth_in=girth_in,
            girth_core=0.018, n_in=5, n_out=10))
    return out


def address_of(stalk: CoaxWinding) -> float:
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


def spectrum(x: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
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
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins)))
            for k in range(bins)]


def equaliser_noise_gain(ch, bins: int) -> float:
    """The mean |1/H(f)|^2 over the bins.

    THE MECHANISM. A zero-forcing equaliser multiplies each bin by
    1/H(f). Its noise gain is the mean of |1/H|^2, and it is the reason
    a bigger channel can be a worse channel: more taps means more
    notches, and a notch is where |H| is smallest, so the equaliser's
    gain peaks there.
    """
    gains = []
    for k in range(bins):
        f = k / bins
        hr, hi = ch.response_complex(f)
        mag2 = hr * hr + hi * hi
        if mag2 > 1e-18:
            gains.append(1.0 / mag2)
    if not gains:
        return 0.0
    return sum(gains) / len(gains)


# ===========================================================================
# ONE READ, WITH THE CROWD AND THE TAPS SEPARATED
# ===========================================================================

def read(link: InterstalkLink, tx_id: str, rx_id: str,
         crowd_ids: List[str], neighbour_ids: List[str],
         candidates: List[str], crowd_amp: float,
         bins: int) -> Dict[str, Any]:
    """One exchange.

    `crowd_ids` -- who radiates into the frame. INDEPENDENT of the
    channel's structure.

    `neighbour_ids` -- whose reflected paths the CHANNEL has. This is
    the tap count, and it is what the width is derived from.
    """
    # build the pair with a controlled set of neighbours
    pair = link.pair(tx_id, rx_id, in_view=neighbour_ids)
    ch = pair.channel()

    ph_tx = address_of(pair.tx)
    crowd_ph = [address_of(link.stalk(c)) for c in crowd_ids
                if c not in (tx_id, rx_id)]

    frame: List[Tuple[float, float]] = []
    for k in range(bins):
        acc_r = acc_i = 0.0
        th = 2.0 * math.pi * ph_tx * (k / bins)
        acc_r += math.cos(th)
        acc_i += math.sin(th)
        for op in crowd_ph:
            th2 = 2.0 * math.pi * op * (k / bins)
            acc_r += crowd_amp * math.cos(th2)
            acc_i += crowd_amp * math.sin(th2)
        frame.append((acc_r, acc_i))

    received = transport(frame, pair, bins)
    rx_spec = spectrum(received)
    eq = ch.equalise(rx_spec, noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "correct": False, "snr_db": 0.0,
                "margin": 0.0, "taps": len(ch.taps)}

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
    return {"ok": True, "correct": winner == tx_id, "snr_db": snr_db,
            "margin": margin, "taps": len(ch.taps)}


def cell(pop: int, taps: int, crowd_amp: float = CROWD_AMP,
         trials: int = 3, speakers: int = 5) -> Dict[str, Any]:
    """One cell of the grid: a population and a tap count."""
    stalks = make_population(pop)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    view = list(ids)

    named = 0
    total = 0
    unreadable = 0
    snrs: List[float] = []
    margins: List[float] = []
    real_taps = 0
    noise_gain = 0.0
    t0 = time.perf_counter()

    for _ in range(trials):
        for i in range(min(pop, speakers)):
            tx = ids[i]
            rx = ids[(i + 1) % pop]
            # the channel's neighbours: capped at `taps`
            nbrs = view[:2 + taps] if taps > 0 else view[:2]
            r = read(link, tx, rx, view, nbrs, ids, crowd_amp, BINS)
            if real_taps == 0:
                real_taps = int(r["taps"])
                pair = link.pair(tx, rx, in_view=nbrs)
                noise_gain = equaliser_noise_gain(pair.channel(), BINS)
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
    width = width_for(real_taps)
    return {
        "pop": pop,
        "taps": real_taps,
        "width": width,
        "named": named,
        "trials": total,
        "unreadable": unreadable,
        "rate": (named / total) if total else 0.0,
        "snr_db": mean_snr,
        "capacity": math.log2(1.0 + snr_lin),
        "needed": math.log2(pop),
        "margin": (sum(margins) / len(margins)) if margins else 0.0,
        "noise_gain": noise_gain,
        "cost": width * pop,
        "secs": time.perf_counter() - t0,
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE BALANCE POINT -- population against width, one dial")
    print("=" * 78)
    print()
    print("  the width is DERIVED from the channel: width_for(taps).")
    print("  so widening and recruiting are not two dials -- a wider")
    print("  channel IS a bigger population in view.")
    print()
    print("  the crowd is HELD AT %.2f per interferer and is INDEPENDENT" % CROWD_AMP)
    print("  of the tap count, so the grid varies one thing at a time.")
    print()

    grid: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for pop in POPS:
        print("=" * 78)
        print("POPULATION %d  (the %d addresses to name)" % (pop, pop))
        print("=" * 78)
        print()
        print("  %-6s %-7s %-10s %-8s %-9s %-9s %-10s %-9s %-7s" % (
            "paths", "taps", "width", "named", "snr dB", "capacity",
            "needed", "noise gain", "cost"))
        print("  " + "-" * 88)
        for t in TAPS:
            r = cell(pop, t)
            grid[(pop, t)] = r
            print("  %-6d %-7d %-10d %-8s %-9.2f %-9.2f %-10.2f %-9.3g %-7d" % (
                t, r["taps"], r["width"],
                "%d/%d" % (r["named"], r["trials"]),
                r["snr_db"], r["capacity"], r["needed"],
                r["noise_gain"], r["cost"]))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE MARGINAL TRADE -- one more stalk against one more tap")
    print("=" * 78)
    print()
    print("  doubling the population buys 1 bit of NAMING (log2 P)")
    print("  and costs 1 more tap in the channel")
    print()
    print("  so the trade is: does the extra tap cost more SNR than the")
    print("  extra address is worth?")
    print()
    for pop in POPS:
        print("  population %d:" % pop)
        prev = None
        for t in TAPS:
            r = grid[(pop, t)]
            if prev is not None:
                d_cap = r["capacity"] - prev["capacity"]
                d_need = r["needed"] - prev["needed"]
                # the surplus is what is left over after paying for the
                # names: capacity minus the bits the names needed
                surplus = r["capacity"] - r["needed"]
                prev_surplus = prev["capacity"] - prev["needed"]
                d_surplus = surplus - prev_surplus
                print("    +1 path: capacity %+6.2f bits, names need %+.2f, "
                      "surplus %+6.2f bits  (was %+.2f)" % (
                          d_cap, d_need, d_surplus, prev_surplus))
            prev = r
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE BEST CELL AT EACH POPULATION (by surplus)")
    print("=" * 78)
    print()
    print("  surplus = capacity - log2(P): the bits left over after")
    print("  paying for the names. this is what the width can be spent")
    print("  on, and it is the quantity the ladder's width must fit in.")
    print()
    print("  %-6s %-8s %-8s %-10s %-10s %-10s %-8s" % (
        "pop", "paths", "width", "capacity", "needed", "surplus", "named"))
    print("  " + "-" * 70)
    best_by_pop: Dict[int, Dict[str, Any]] = {}
    for pop in POPS:
        cells = [grid[(pop, t)] for t in TAPS]
        best = max(cells, key=lambda r: (r["capacity"] - r["needed"]))
        best_by_pop[pop] = best
        print("  %-6d %-8d %-8d %-10.2f %-10.2f %-10.2f %-8s" % (
            pop, best["taps"], best["width"], best["capacity"],
            best["needed"], best["capacity"] - best["needed"],
            "%d/%d" % (best["named"], best["trials"])))
    print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE WIDTH THE READING CAN PAY FOR")
    print("=" * 78)
    print()
    print("  at each population, the largest width whose bit count fits")
    print("  in the surplus. that is the width the reading can ACTUALLY")
    print("  carry, and comparing it with the ladder's schedule says")
    print("  whether the ladder is buying bits it cannot use.")
    print()
    WIDTHS = (1, 4, 8, 16, 32, 64, 128, 256)
    print("  %-6s %-12s %-12s %-14s %-14s %s" % (
        "pop", "best width", "surplus", "carries (bits)", "schedule says",
        "verdict"))
    print("  " + "-" * 74)
    for pop in POPS:
        b = best_by_pop[pop]
        surplus = b["capacity"] - b["needed"]
        carries = max((w for w in WIDTHS if w <= max(surplus, 0.0)),
                      default=0)
        sched = b["width"]
        if surplus < 0:
            verdict = "the names do NOT fit"
        elif carries >= sched:
            verdict = "the width FITS"
        else:
            verdict = "the width is TOO WIDE"
        print("  %-6d %-12d %-12.2f %-14d %-14d %s" % (
            pop, sched, surplus, carries, sched, verdict))
    print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("IS 4-BIT AND 8-BIT ENOUGH?")
    print("=" * 78)
    print()
    print("  a width of W bits names 2^W stalks. the question is whether")
    print("  the reading at that population carries W bits.")
    print()
    for pop in (2, 4, 8, 16, 32, 64):
        best = best_by_pop[pop]
        surplus = best["capacity"] - best["needed"]
        print("  population %-3d: best width %-4d bits, surplus %-6.2f, "
              "named %s" % (
                  pop, best["width"], surplus,
                  "%d/%d" % (best["named"], best["trials"])))
        for w in (4, 8, 16, 32, 64):
            need = math.log2(2 ** w)      # bits needed to name 2^W stalks
            print("      %-3d bits names %-8d stalks, needs %-5.1f bits "
                  "-> %s" % (
                      w, 2 ** w, need,
                      "ENOUGH" if best["capacity"] >= need else "SHORT"))
    print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
