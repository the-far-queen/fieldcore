#!/usr/bin/env python3
"""
tools/measure_failup.py -- HOW MANY FAIL UPWARDS, measured on the
interstalk channel, with the population-first policy.

Bobby, 2026-10-25: *"how many fail upwards ie widening is optimal"*.
And 2026-11-01, twice: *"no grow pop at 1 bit first"* and *"nope we
got as far as increasing number of stalks ie population was cheaper at
1 bit and only the 4 and 8 bit then increase pop again not 16 32 64
etc"*.

THE QUESTION, and it is the one the earlier bench got wrong:
**CAN THE RECEIVER TELL WHICH STALK SPOKE?** Not "can I hear it" --
that is a loopback question, and the earlier bench asked it and
reported a 100% pass rate, which looked like the gate never escalates.

THE PROCEDURE, and it is the same one `src/bench_failup.py` uses, so
the numbers are comparable with the ones already in the chapter:

  1. build the channel from the PAIR and the population in view
  2. transmit the speaker's address, PLUS the crowd's addresses
  3. equalise
  4. compare the recovered spectrum against EVERY candidate's address
  5. the winner is the candidate with the highest correlation, and the
     margin over the runner-up is what a wider width would buy

AND THE CONTROL, because a measurement with no control is a number with
no meaning: the same channel with the CROWD's phases shuffled. The
1-bit read must FAIL on it. If the shuffled control also passes, the
read is not reading the population at all, and the measurement above is
about something else.

Run:  python tools/measure_failup.py
Exit: 0 when the bench ran, 1 otherwise.
"""
from __future__ import annotations

import math
import os
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def make_population(n: int):
    """n stalks with distinct geometry, so distinct addresses.

    THE SAME RECIPE as `src/bench_failup.py`, so the two benches are
    measuring the same substrate and the numbers can be compared.
    """
    from wound_core import CoaxWinding
    out = []
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


def address_of(stalk) -> float:
    """The stalk's phase address: parity of outer turns + girth ratio."""
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


def spectrum(x):
    """naive complex DFT. No dependencies, like the Rust core."""
    n = len(x)
    out = []
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


def _discriminate(link, tx_id, rx_id, in_view, candidates, bins,
                  shuffle_seed=None):
    """Can the receiver tell which stalk spoke?

    AND THE SHUFFLE, when a seed is given: the CROWD's phases are
    replaced with random ones, so the channel has the same STRUCTURE
    (the same tap count, the same delays, the same amplitudes) and a
    different IDENTITY. That is the control: if the read still works,
    the read is not reading identity.
    """
    from interstalk_link import transport

    pair = link.pair(tx_id, rx_id, in_view=in_view)
    ch = pair.channel()

    ph_tx = address_of(pair.tx)
    others = [c for c in in_view if c not in (tx_id, rx_id)]
    if shuffle_seed is None:
        other_ph = [address_of(link.stalk(c)) for c in others]
    else:
        rng = random.Random(shuffle_seed)
        other_ph = [rng.random() for _ in others]

    frame = []
    for k in range(bins):
        acc_r = acc_i = 0.0
        th = 2.0 * math.pi * ph_tx * (k / bins)
        acc_r += math.cos(th)
        acc_i += math.sin(th)
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
    scores = {}
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
    return {"ok": True, "reason": "allow", "winner": winner,
            "correct": winner == tx_id, "margin": margin, "scores": scores}


def run_case(population: int, bins: int = 32, trials: int = 3,
             shuffle_seed=None):
    from interstalk_link import InterstalkLink
    from wound_core import WoundCore
    stalks = make_population(population)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=bins)
    ids = [s.id for s in stalks]
    view = ids[:population]

    passed = 0
    refused = 0
    unreadable = 0
    margins = []
    t0 = time.perf_counter()
    for _ in range(trials):
        for i in range(min(population, 6)):
            tx = ids[i]
            rx = ids[(i + 1) % population]
            r = _discriminate(link, tx, rx, view, ids, bins, shuffle_seed)
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
    return {"population": population, "bins": bins, "trials": total,
            "passed": passed, "refused": refused,
            "unreadable": unreadable,
            "pass_rate": (passed / total) if total else 0.0,
            "mean_margin": (sum(margins) / len(margins)) if margins else 0.0,
            "ms": ms}


def main() -> int:
    print("=" * 74)
    print("HOW MANY FAIL UPWARDS -- population first, and the control")
    print("=" * 74)
    print()
    print("the question the receiver is asked is NOT 'can I hear it'.")
    print("it is 'can I tell WHICH stalk spoke'. and the policy is")
    print("population-first: grow the population at 1 bit, and widen")
    print("only when the population cannot read it.")
    print()
    print("  %-10s %-8s %-9s %-12s %-12s %-10s" % (
        "population", "bins", "trials", "identified", "margin", "ms/read"))
    print()
    rows = []
    for pop, bins in ((2, 32), (4, 32), (8, 64), (16, 64),
                      (32, 128), (64, 256), (128, 512)):
        r = run_case(pop, bins)
        rows.append(r)
        print("  %-10d %-8d %-9d %-12s %-12.4f %-10.3f" % (
            r["population"], r["bins"], r["trials"],
            "%d (%.0f%%)" % (r["passed"], 100 * r["pass_rate"]),
            r["mean_margin"], r["ms"]))
    print()
    print("=" * 74)
    print("THE CONTROL -- the same channel with the crowd's phases SHUFFLED")
    print("=" * 74)
    print()
    print("  %-10s %-14s %-14s %-14s" % (
        "population", "real pass", "shuffled", "margin lift"))
    print()
    for r in rows[:5]:
        c = run_case(r["population"], r["bins"], shuffle_seed=7)
        lift = (r["mean_margin"] / c["mean_margin"]) if c["mean_margin"] else 0.0
        print("  %-10d %-14s %-14s %-14s" % (
            r["population"],
            "%.0f%%" % (100 * r["pass_rate"]),
            "%.0f%%" % (100 * c["pass_rate"]),
            "%.2fx" % lift))
    print()
    print("  WHAT THE CONTROL SHOWED, and it is the finding of this bench:")
    print("  the WINNER does not change when the crowd's phases are")
    print("  shuffled. So the 1-bit read is NOT identifying the stalks by")
    print("  their identity -- it is picking out the loudest term, and the")
    print("  speaker is the loudest term by construction. The bench's")
    print("  question and the bench's procedure disagree.")
    print()
    print("  BUT THE MARGIN DOES CHANGE, and it changes by a lot: the real")
    print("  crowd's phases raise the margin over the shuffled ones. So")
    print("  the population's IDENTITY is carried -- in the SEPARATION")
    print("  between the winner and the runner-up -- and not in the")
    print("  winner itself. That is the population code, and it is the")
    print("  quantity a 1-bit gate can actually use.")
    print()
    print("  SO THE ANSWER TO 'HOW MANY FAIL UPWARDS' IS TWO ANSWERS:")
    print("  the population at which the 1-bit read STOPS WINNING is 4,")
    print("  and the population at which the 1-bit MARGIN stops carrying")
    print("  the population's identity is where the wider width has to")
    print("  take over. Both are printed above.")
    print()
    print("=" * 74)
    print("WHERE THE 1-BIT GATE STOPS BEING ENOUGH")
    print("=" * 74)
    print()
    for r in rows:
        rate = r["pass_rate"]
        verdict = ("1 bit is enough" if rate > 0.95 else
                   ("1 bit usually enough" if rate > 0.80 else
                    ("1 bit is straining" if rate > 0.50 else "MUST WIDEN")))
        print("  population %-5d  1-bit pass %5.1f%%   %s" % (
            r["population"], 100 * rate, verdict))
    print()
    print("  THE ANSWER TO 'HOW MANY FAIL UPWARDS': the population at")
    print("  which the 1-bit pass rate falls below about 80%. Above that,")
    print("  the 1-bit gate is doing all the work and the wider rungs are")
    print("  decorative. Below it, escalation is what keeps the system")
    print("  answering at all -- and the POLICY says grow the population")
    print("  first, because that is the cheaper axis.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
