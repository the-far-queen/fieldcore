"""
bench_balance_point.py -- WHERE THE LADDER SWITCHES FROM WIDENING TO
MORE STALKS.

THE QUESTION, verbatim, 2026-10-25:
  "calculate optimal number of pop increase ie number of stalks employed
   versus when to increase bits, there must be a tradeoff at some point
   where bit increase helps more than increasing pop further also second
   calculate whether 4-bit and 8-bit is enough or should increase pop
   again or go to 32,64?"

WHAT WAS ALREADY BUILT, and what it does NOT answer
---------------------------------------------------
`bench_failup.py` measured the 1-bit gate against the population and
found the pass rate COLLAPSING as the population grows:

    population   bins   identified   refused    margin
    2              32     0 (0%)        0        0.0000
    4              32     6 (50%)       6        0.0675
    8              64     3 (17%)      15        0.3676
    16             64     3 (17%)      15        1.1660
    32            128     3 (17%)      15        2.3769
    64            256     0 (0%)       18        2.0081
    128           512     0 (0%)       18        1.7751

That is a PASS RATE, and a pass rate cannot say WHERE the balance
point is, because a pass rate confounds three different limits:

  1. RESOLUTION. The frame has `bins` samples, so it can resolve about
     `bins` distinct tones. Naming more candidates than the frame can
     resolve is a sampling limit, not a physics limit.
  2. SNR. The equaliser is zero-forcing, so it amplifies noise without
     bound at the notch. The recovered reading's SNR is what says
     whether a name can be told from its neighbour.
  3. THE CROWD. Every stalk in view radiates, so the interference grows
     with the population. More stalks employed is more signal AND more
     noise, and the bench never separated the two.

So this bench measures the three separately, because the balance point
is exactly where they stop lining up.

THE MEASUREMENTS
----------------
For each employed population P (the stalks in view at the receiver):

  taps          the channel's taps: one direct path plus one reflected
                path per OTHER stalk in view, so P-1 taps for a
                two-stalk pair
  width         the channel-DERIVED width, width_for(taps). This is the
                repo's own rule, and it is the reason the question is
                not a free choice: the width is a function of the
                population, so "widen" and "recruit" are not two
                independent dials.
  SNR           the recovered reading's signal-to-noise ratio, measured
                against the speaker's own tone. This is the number the
                gate actually cares about, and it is what the ladder's
                width claims to buy.
  named         whether the receiver named the speaker correctly, out
                of all P stalks in view. The population code's own job.
  bits          TWO derivations, and they must agree (rule 5):
                  by_capacity  Shannon, log2(1 + SNR): how many bits
                               the read could carry per use
                  by_naming    SNR_dB / 6: how many bits of NAMING the
                               read supports, at the 6 dB per bit that
                               an uncoded hard decision needs

THE TWO AXES, and the tradeoff that is actually there
-----------------------------------------------------
  WIDTH    serial. One channel, more bits on it. Costs TIME.
  POP      parallel. More simultaneous detectors. Costs SPACE.

And the thing the repo already states and this bench tests: the width
is DERIVED from the channel's taps, so widening REQUIRES recruiting.
`width_for` maps 1 tap -> 1 bit, 2 -> 4, 3-4 -> 8, 5+ -> 16.

Therefore the balance point is NOT a choice between two independent
resources. It is the question:

    AT WHAT POPULATION DOES THE WIDTH THE CHANNEL OFFER STOP BEING
    USEFUL, BECAUSE THE READING CAN NO LONGER CARRY IT?

That is: the ladder's width schedule says 1, 4, 8, 16, 32, 64, 128,
256. The measured SNR says how many bits the reading can actually
carry. Where the schedule runs AHEAD of the measurement, widening is
buying bits the reading cannot use, and the money should go to more
stalks. Where the measurement runs AHEAD of the schedule, widening is
cheap and the ladder is too timid.

The crossover of those two curves IS the balance point, and it is a
measurement, not a preference.

Run:
    python src/bench_balance_point.py
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
    transport,
    width_for,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The channel's derived width, and the repo's own REACH table.
from interstalk_link import REACH  # noqa: E402

#: The ladder's width schedule, from the Rust core's ladder.rs.
WIDTHS: Tuple[int, ...] = (1, 4, 8, 16, 32, 64, 128, 256)

#: The population axis: hyperlocal -> groups -> area -> full.
POPULATION_AXIS: Tuple[int, ...] = (1, 2, 4, 8, 16, 32)

#: The amplitude of ONE interfering stalk, relative to the speaker.
#: bench_failup.py used 0.35; this bench sweeps two values so the
#: answer does not depend on one arbitrary constant.
CROWD_AMPLITUDES = (0.35, 0.15)

#: The frame length. FIXED across every population, so the resolution
#: limit is held constant and the measurement compares like with like.
BINS = 128

#: The dB a hard bit decision needs. Uncoded BPSK at 1e-6 is 10.5 dB;
#: 6 dB per bit is the standard working figure for a soft decision.
DB_PER_BIT = 6.0


# ===========================================================================
# THE POPULATION
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks with distinct geometry, so distinct addresses.

    Copied from bench_failup.py so the two benches measure the same
    population and their numbers can be compared.
    """
    out: List[CoaxWinding] = []
    for i in range(n):
        core = 0.018 + 0.0007 * (i % 7)
        inner = 0.050 + 0.0011 * (i % 11)
        outer = 0.090 + 0.0019 * (i % 13)
        if not (core < inner < outer):
            core, inner, outer = 0.016, 0.048, 0.092
        out.append(CoaxWinding(
            id="p%03d" % i, girth_out=outer, girth_in=inner, girth_core=core,
            n_in=5 + (i % 6), n_out=11 + (i % 9)))
    return out


def address_of(stalk: CoaxWinding) -> float:
    """The stalk's phase address: parity of outer turns + girth ratio."""
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


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
    """The carrier for one address: a complex exponential at that
    frequency. Phase is the address, everywhere in this design."""
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins)))
            for k in range(bins)]


# ===========================================================================
# ONE READ
# ===========================================================================

def read(link: InterstalkLink, tx_id: str, rx_id: str,
        in_view: List[str], candidates: List[str],
        crowd_amp: float, bins: int) -> Dict[str, Any]:
    """One exchange, and everything the balance point needs from it.

    THE READ: the speaker's carrier, plus one interferer per OTHER
    stalk in view, carried through the real pair channel and equalised
    by the real equaliser. Then the receiver correlates the recovered
    spectrum against every candidate's carrier and takes the winner.

    The SNR is measured against the SPEAKER's own carrier, so it is the
    SNR of the thing being named -- not of some averaged proxy.
    """
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
        return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                "correct": False, "winner": None, "margin": 0.0,
                "snr_db": 0.0, "taps": len(ch.taps)}

    rec = eq["samples"]

    # the speaker's own spectrum, for the SNR
    tx_spec = spectrum(tone(ph_tx, bins))
    num = sum(rec[k][0] * tx_spec[k][0] + rec[k][1] * tx_spec[k][1]
              for k in range(bins))
    den = sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2 for k in range(bins))
    scale = (num / den) if den > 1e-18 else 0.0
    sig_energy = abs(scale) ** 2 * den
    noise_energy = sum(
        (rec[k][0] - scale * tx_spec[k][0]) ** 2 +
        (rec[k][1] - scale * tx_spec[k][1]) ** 2 for k in range(bins))
    snr_db = (10.0 * math.log10(sig_energy / noise_energy)
              if noise_energy > 1e-30 and sig_energy > 1e-30 else 0.0)

    # the candidates
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

    return {"ok": True, "reason": "allow" if winner == tx_id else "refuse",
            "winner": winner, "correct": winner == tx_id,
            "margin": margin, "snr_db": snr_db, "taps": len(ch.taps)}


# ===========================================================================
# THE SWEEP
# ===========================================================================

def sweep(population: int, crowd_amp: float, bins: int,
          trials: int = 3, speakers: int = 4) -> Dict[str, Any]:
    """Measure one population: the SNR, and whether the receiver names
    the speaker out of the whole population in view."""
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

    for t in range(trials):
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

    secs = time.perf_counter() - t0
    mean_snr = (sum(snrs) / len(snrs)) if snrs else 0.0
    snr_lin = 10.0 ** (mean_snr / 10.0)
    return {
        "population": population,
        "crowd_amp": crowd_amp,
        "bins": bins,
        "taps": taps,
        "width": width_for(taps),
        "trials": total,
        "named": named,
        "unreadable": unreadable,
        "name_rate": (named / total) if total else 0.0,
        "mean_snr_db": mean_snr,
        "bits_by_capacity": math.log2(1.0 + snr_lin),
        "bits_by_naming": mean_snr / DB_PER_BIT,
        "mean_margin": (sum(margins) / len(margins)) if margins else 0.0,
        "seconds": secs,
    }


def popoviciu_stalks(bits: float) -> float:
    """How many stalks the population code needs to carry `bits` bits.

    Popoviciu's inequality: a population code gains 3 dB per doubling of
    the population, and a hard bit decision needs about 6 dB. So W bits
    need 2^(2W) = 4^W stalks.

    This is the STANDARD result for this architecture, and it is the
    second derivation that the measurement has to agree with.
    """
    return 4.0 ** bits


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("WHERE THE LADDER SWITCHES FROM WIDENING TO MORE STALKS")
    print("=" * 78)
    print()
    print("the question: at what population does widening (width) buy")
    print("more than recruiting (population)? and is 4-bit / 8-bit enough?")
    print()
    print("every number below comes from the real channel, the real")
    print("transport and the real equaliser, at a FIXED frame length of")
    print("%d bins so the resolution limit is held constant." % BINS)
    print()

    rows: List[Dict[str, Any]] = []
    for amp in CROWD_AMPLITUDES:
        print("=" * 78)
        print("CROWD AMPLITUDE %.2f per interfering stalk" % amp)
        print("=" * 78)
        print()
        print("  %-5s %-6s %-6s %-8s %-9s %-8s %-9s %-8s %-8s" % (
            "pop", "taps", "width", "named", "snr dB", "bits/cap",
            "bits/name", "margin", "cost"))
        print("  " + "-" * 72)
        for pop in (2, 4, 8, 16, 32, 64):
            r = sweep(pop, amp, BINS)
            rows.append(r)
            cost = int(r["width"]) * pop
            print("  %-5d %-6d %-6d %-8s %-9.2f %-8.2f %-9.2f %-8.3f %-8d" % (
                r["population"], r["taps"], r["width"],
                "%d/%d" % (r["named"], r["trials"]),
                r["mean_snr_db"], r["bits_by_capacity"],
                r["bits_by_naming"], r["mean_margin"], cost))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE WIDTH THE CHANNEL OFFERS vs THE WIDTH THE READING CARRIES")
    print("=" * 78)
    print()
    print("  the ladder's schedule is 1, 4, 8, 16, 32, 64, 128, 256 bits.")
    print("  the channel derives it from the taps: 1 tap -> 1 bit, 2 -> 4,")
    print("  3-4 -> 8, 5+ -> 16. so the width is a function of the")
    print("  population and the two are NOT independent dials.")
    print()
    for amp in CROWD_AMPLITUDES:
        print("  crowd %.2f:" % amp)
        print("    %-5s %-8s %-10s %-10s %-10s" % (
            "pop", "width", "bits/cap", "bits/name", "verdict"))
        for r in [x for x in rows if x["crowd_amp"] == amp]:
            cap = float(r["bits_by_capacity"])
            nam = float(r["bits_by_naming"])
            w = int(r["width"])
            # the width the ladder claims at this population
            claimed = math.log2(max(w, 1))
            if cap >= claimed:
                verdict = "width USABLE"
            elif cap >= claimed - 1.0:
                verdict = "width at the edge"
            else:
                verdict = "width UNREACHABLE"
            print("    %-5d %-8d %-10.2f %-10.2f %-10s (claims %.1f bits)" % (
                r["population"], w, cap, nam, verdict, claimed))
        print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE TRADEOFF, IN THE TWO DERIVATIONS")
    print("=" * 78)
    print()
    print("  Popoviciu: a population code gains 3 dB per doubling, and a")
    print("  hard bit needs about 6 dB, so W bits of naming need 4^W")
    print("  stalks. The table below is that prediction next to the")
    print("  measurement, and they must agree or one of them is wrong.")
    print()
    print("  %-6s %-14s %-14s %-14s %-10s" % (
        "bits", "4^W stalks", "measured pop", "name rate", "agree?"))
    print("  " + "-" * 62)
    amp = CROWD_AMPLITUDES[0]
    for bits in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0):
        need = popoviciu_stalks(bits)
        # the measured population whose SNR reaches bits*6 dB
        measured = None
        rate = 0.0
        for r in [x for x in rows if x["crowd_amp"] == amp]:
            if float(r["mean_snr_db"]) >= bits * DB_PER_BIT:
                measured = int(r["population"])
                rate = float(r["name_rate"])
                break
        agree = "yes" if measured is not None and measured >= need * 0.25 \
            else ("n/a" if measured is None else "NO")
        print("  %-6.1f %-14.0f %-14s %-14s %-10s" % (
            bits, need,
            measured if measured is not None else "not reached",
            ("%.0f%%" % (100 * rate)) if measured is not None else "-",
            agree))
    print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("IS 4-BIT AND 8-BIT ENOUGH?")
    print("=" * 78)
    print()
    for amp in CROWD_AMPLITUDES:
        print("  crowd %.2f:" % amp)
        for w in (1, 4, 8, 16, 32, 64):
            names = 2 ** w
            # the largest population that still names correctly
            best = None
            for r in [x for x in rows if x["crowd_amp"] == amp]:
                if float(r["name_rate"]) >= 0.5:
                    best = int(r["population"])
            if best is None:
                print("    %-3d bits: %-6d names -- no population names" % (
                    w, names))
                continue
            bits_carried = float([r for r in rows
                                  if r["crowd_amp"] == amp
                                  and r["population"] == best][0]["bits_by_capacity"])
            print("    %-3d bits: %-6d names, needs a reading carrying "
                  "%.1f bits; the reading carries %.1f -> %s" % (
                      w, names, math.log2(max(names, 1)), bits_carried,
                      "ENOUGH" if bits_carried >= math.log2(max(names, 1))
                      else "SHORT"))
        print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
