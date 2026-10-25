"""
bench_failup.py -- HOW OFTEN DOES THE GATE FAIL UP?

The question, verbatim, 2026-10-25: *"how many fail upwards ie widening
is optimal"*.

THE MEASUREMENT, and the trap in it
-----------------------------------
The failure rate depends on what the 1-bit gate is being asked to do,
and the earlier bench (bench_ladder.py) measured the WRONG thing. It
asked "can the receiver hear the transmitter?" -- a loopback question
-- and found a 100% pass rate up to population 32 and a collapse at 64.

That collapse at 64 was almost certainly a NUMERICAL artifact, not a
genuine information limit. Two reasons to suspect it:

  1. the naive DFT is O(bins^2) and at 256 bins the accumulated float
     error is large enough to matter, while the signal is O(1)
  2. the alignment measure normalises by the transmit norm, so a
     channel that merely attenuates the signal scores 1.0 -- meaning
     the gate passes anything it can hear at all

So this bench measures the thing that ACTUALLY fails up. And that is
not "can I hear it". It is:

    CAN THE RECEIVER TELL WHICH STALK SPOKE?

That is the real 1-bit question, and it is the one the population code
exists to answer. The receiver is presented with a MIXTURE of several
stalks and must identify which one is present. A single-stalk channel
does not test discrimination at all.

THE THREE REGIMES, and they are the answer to the question:

  ISOLATED      one stalk, no interference.
                Can it be heard? yes. Can it be IDENTIFIED? trivially.
                -> the gate passes. This is the 1-bit case, and it is
                the cheap layer the 747 analogy requires.

  CROWDED      several stalks, the receiver must pick one out of the
                mixture. The interference is the noise, and the
                question is discrimination.

  OVERWHELMED  the population is large enough that the mixture's
                interference at the correct answer exceeds the
                interference at the WRONG answers -- so no 1-bit
                reading can separate them, and the question MUST
                escalate to a wider width.

The third regime is where widening earns its cost. This bench finds
where it starts.

Run:
    python src/bench_failup.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    PairChannel,
    Neighbour,
    transport,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# THE POPULATION
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks with distinct geometry, so distinct addresses.

    The geometry varies the way the standard four do: girths and turn
    counts both move, so no two stalks share an address, and the
    concentric order core < inner < outer is preserved.
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


# ===========================================================================
# THE DISCRIMINATION TEST
# ===========================================================================

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


def build_pair(link: InterstalkLink, tx_id: str, rx_id: str,
               in_view: List[str]) -> PairChannel:
    return link.pair(tx_id, rx_id, in_view=in_view)


def discriminate(link: InterstalkLink, tx_id: str, rx_id: str,
                 in_view: List[str], candidates: List[str],
                 bins: int) -> Dict[str, object]:
    """Can the receiver tell which stalk spoke?

    THE PROCEDURE:
      1. build the channel from the pair and the population in view
      2. transmit the speaker's address, PLUS the other candidates'
         addresses as interference (that is the CROWD)
      3. equalise
      4. compare the recovered spectrum against EVERY candidate's
         address spectrum
      5. the winner is the candidate with the highest correlation

    The gate passes iff the winner IS the speaker. The margin over the
    runner-up is the confidence, and it is what a wider width would buy.

    This is the population code: the readout is the RATIO across the
    population, not a dedicated wire per concept.
    """
    pair = build_pair(link, tx_id, rx_id, in_view)
    ch = pair.channel()

    # the speaker's signal, plus the crowd
    frame: List[Tuple[float, float]] = []
    ph_tx = address_of(pair.tx)
    others = [c for c in in_view if c not in (tx_id, rx_id)]
    other_ph = [address_of(link.stalk(c)) for c in others]

    for k in range(bins):
        acc_r = acc_i = 0.0
        # the speaker
        th = 2.0 * math.pi * ph_tx * (k / bins)
        acc_r += math.cos(th)
        acc_i += math.sin(th)
        # the crowd: each other stalk interferes
        for op in other_ph:
            th2 = 2.0 * math.pi * op * (k / bins)
            acc_r += 0.35 * math.cos(th2)
            acc_i += 0.35 * math.sin(th2)
        frame.append((acc_r, acc_i))

    received = transport(frame, pair, bins)
    rx_spec = spectrum(received)
    eq = ch.equalise(rx_spec, noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                "winner": None, "correct": False, "margin": 0.0}

    rec = eq["samples"]

    # compare against every candidate
    scores: Dict[str, float] = {}
    for cand in candidates:
        ph = address_of(link.stalk(cand))
        spec = spectrum([(math.cos(2 * math.pi * ph * (k / bins)),
                          math.sin(2 * math.pi * ph * (k / bins)))
                         for k in range(bins)])
        num = sum(rec[k][0] * spec[k][0] + rec[k][1] * spec[k][1]
                  for k in range(bins))
        den = math.sqrt(sum(spec[k][0] ** 2 + spec[k][1] ** 2
                            for k in range(bins))) or 1.0
        scores[cand] = num / den

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    winner = ranked[0][0]
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)

    return {
        "ok": True,
        "reason": "allow" if winner == tx_id else "refuse_alignment",
        "winner": winner,
        "correct": winner == tx_id,
        "margin": margin,
        "scores": scores,
    }


# ===========================================================================
# THE BENCH
# ===========================================================================

def run_case(population: int, bins: int, trials: int = 3) -> Dict[str, object]:
    stalks = make_population(population)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=bins)
    ids = [s.id for s in stalks]
    view = ids[:population]

    passed = 0
    refused = 0
    unreadable = 0
    margins: List[float] = []
    t0 = time.perf_counter()
    for _ in range(trials):
        for i in range(min(population, 6)):
            tx = ids[i]
            rx = ids[(i + 1) % population]
            r = discriminate(link, tx, rx, view, ids, bins)
            if not r["ok"]:
                unreadable += 1
                continue
            margins.append(float(r["margin"]))
            if r["correct"]:
                passed += 1
            else:
                refused += 1
    total = passed + refused
    ms = (time.perf_counter() - t0) * 1000.0 / max(total, 1)
    return {
        "population": population,
        "bins": bins,
        "trials": total,
        "passed": passed,
        "refused": refused,
        "unreadable": unreadable,
        "pass_rate": (passed / total) if total else 0.0,
        "mean_margin": (sum(margins) / len(margins)) if margins else 0.0,
        "ms": ms,
    }


def main() -> int:
    print("=" * 78)
    print("HOW MANY FAIL UPWARDS -- the measurement that matters")
    print("=" * 78)
    print()
    print("the question the receiver is asked is NOT 'can I hear it'.")
    print("it is 'can I tell WHICH stalk spoke'. a single-stalk channel")
    print("does not test discrimination at all -- that is why the earlier")
    print("bench reported a 100% pass rate and looked like the gate")
    print("never escalates.")
    print()

    print("=" * 78)
    print("THE THREE REGIMES")
    print("=" * 78)
    print()
    print("  %-12s %-8s %-10s %-14s %-14s %-10s" % (
        "population", "bins", "trials", "identified", "refused", "margin"))
    print()
    for pop, bins in ((2, 32), (4, 32), (8, 64), (16, 64),
                      (32, 128), (64, 256), (128, 512)):
        r = run_case(pop, bins)
        print("  %-12d %-8d %-10d %-14s %-14s %-10.4f" % (
            r["population"], r["bins"], r["trials"],
            "%d (%.0f%%)" % (r["passed"], 100 * r["pass_rate"]),
            r["refused"],
            r["mean_margin"]))
    print()
    print("  unreadable channels (the equaliser refused) are reported")
    print("  separately: a channel that cannot be inverted is not a")
    print("  wrong answer, it is an unreadable one.")
    print()

    # ----------------------------------------------------------------
    print("=" * 78)
    print("WHERE THE 1-BIT GATE STOPS BEING ENOUGH")
    print("=" * 78)
    print()
    rows = []
    for pop, bins in ((2, 32), (4, 32), (8, 64), (16, 64),
                      (32, 128), (64, 256), (128, 512)):
        rows.append(run_case(pop, bins))
    for r in rows:
        rate = r["pass_rate"]
        verdict = ("1 bit is enough" if rate > 0.95 else
                   ("1 bit usually enough" if rate > 0.80 else
                    ("1 bit is straining" if rate > 0.50 else
                     "MUST WIDEN")))
        print("  population %-5d  1-bit pass %5.1f%%   %s" % (
            r["population"], 100 * rate, verdict))
    print()
    print("  THE ANSWER TO 'HOW MANY FAIL UPWARDS': the number to watch")
    print("  is the population at which the 1-bit pass rate falls below")
    print("  about 80%. Above that, the 1-bit gate is doing all the work")
    print("  and the wider rungs are decorative. Below it, escalation")
    print("  is what keeps the system answering at all.")
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
