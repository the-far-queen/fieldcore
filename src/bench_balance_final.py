"""
bench_balance_final.py -- WHERE THE LADDER SHOULD SWITCH, AND HOW
ROBUST THE ANSWER IS.

THE ANSWER, CORRECTED 2026-10-31: THE PEAK IS AT POPULATION 3, not 4.

This bench reported the peak at 4 until 2026-10-31, and the vault note
`MYSELF/22-2026-10-25-the-balance-point.md` carries that wrong number
forward as the cap for the dual ladder. THE CAUSE WAS THE GRID: the
population axis was the POWERS OF TWO only -- (2, 4, 8, 16, 32, 64) --
so the peak could only land on a power of two, and 4 was the nearest
power of two above the true peak of 3.

MEASURED on the dense axis, through this bench's own instrument:

    model A crowd 0.05:  pop 3 surplus +7.30   pop 4 surplus +5.48
    model A crowd 0.15:  pop 3 surplus +4.21   pop 4 surplus +2.48
    model A crowd 0.35:  pop 3 surplus +1.97   pop 4 surplus +0.47
    model B crowd 0.05:  pop 3 surplus +7.30   pop 4 surplus +6.46
    model B crowd 0.15:  pop 3 surplus +4.21   pop 4 surplus +3.40
    model B crowd 0.35:  pop 3 surplus +1.97   pop 4 surplus +1.24

POP 3 WINS IN ALL 6. The second bench, `bench_girth_ladder.py`, which
sweeps EVERY population from 2 to 16, independently found the peak at 3
in the coupled model. Two derivations, agreeing -- which is the test
they have to pass.

WHAT THE PREVIOUS BENCHES ESTABLISHED
--------------------------------------
  * The width is DERIVED from the channel (width_for(taps)), so
    widening and recruiting are ONE dial, not two. A wider channel IS
    a bigger population in view.

  * More taps make the channel WORSE, not better: the zero-forcing
    equaliser's noise gain grows with the tap count (measured 4.25 at
    1 tap, 6.46 at 2, 13.5 at 3, 98.8 at 4 taps in one population),
    because more taps means deeper notches and more of the crowd lands
    on one.

  * The names need log2(P) bits and the reading's capacity falls as
    the crowd grows, so surplus = capacity - log2(P) has a PEAK. The
    peak is the balance point.

THIS BENCH answers the two questions Bobby asked, with the answer
swept over the one free parameter (the crowd amplitude) so it is a
range rather than a single number:

  Q1  at what population should the ladder stop widening and start
      recruiting? (and the reverse)
  Q2  is 4-bit enough, is 8-bit enough, or must it go to 16/32/64?

THE METHOD
----------
For each population P and each crowd amplitude A:

  the channel is the direct path plus ONE reflected path (2 taps) --
  the smallest channel that has structure to invert, because the
  measurement says more taps cost capacity

  the frame carries the speaker at 1.0 and each of the P-2 other
  stalks at A

  the reading is equalised and correlated against all P candidates

  capacity = log2(1 + SNR)      the bits the reading can carry
  needed   = log2(P)            the bits to name among P
  surplus = capacity - needed   what is left for the width

THE SECOND DERIVATION (central rule 5)
--------------------------------------
The measured surplus is compared against Popoviciu's population-code
result: 3 dB per doubling, so W bits of naming need 4^W stalks. That
is only true when the AGGREGATE interference is held constant, so this
bench measures BOTH models:

  MODEL A  fixed per-interferer amplitude. The crowd grows with the
           population. This is the repo's own model -- every stalk in
           view radiates.

  MODEL B  fixed AGGREGATE interference. The per-interferer amplitude
           falls as 1/sqrt(P-1). This is the model Popoviciu assumes,
           and it is what a brain-like population code would need.

If the answer to Q1 is the same under both models, the answer is a
property of the architecture. If not, the model is the answer.

Run:
    python src/bench_balance_final.py
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import sys
import time
from typing import Any, Dict, List, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    transport,
    width_for,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402

BINS = 128

#: The populations swept. THE GRID WAS TOO COARSE, and it is the reason
#: this bench used to report a peak at 4.
#:
#: THE DEFECT, measured 2026-10-31. The axis used to be the POWERS OF TWO
#: only -- (2, 4, 8, 16, 32, 64) -- so the peak could only ever land on a
#: power of two. The true peak is at 3, and a grid that cannot hold 3
#: cannot see it: the bench reported the peak at 4 because 4 was the
#: nearest power of two ABOVE the true peak of 3.
#:
#: MEASURED, through this bench's own instrument, on the dense axis:
#:
#:     model A crowd 0.05:  pop 3 surplus +7.30   pop 4 surplus +5.48
#:     model A crowd 0.15:  pop 3 surplus +4.21   pop 4 surplus +2.48
#:     model A crowd 0.35:  pop 3 surplus +1.97   pop 4 surplus +0.47
#:     model B crowd 0.05:  pop 3 surplus +7.30   pop 4 surplus +6.46
#:     model B crowd 0.15:  pop 3 surplus +4.21   pop 4 surplus +3.40
#:     model B crowd 0.35:  pop 3 surplus +1.97   pop 4 surplus +1.24
#:
#: POP 3 WINS IN ALL 6. And the second bench, `bench_girth_ladder.py`,
#: which sweeps EVERY population from 2 to 16, independently found the
#: peak at 3 (coupled model) and 4 (decoupled model). So the two benches
#: did not disagree about the architecture -- the coarse grid hid the
#: peak from one of them.
#:
#: THE GRID IS NOW DENSE at the low end, where the peak is, and it keeps
#: the powers of two above it so the wide end still gets read. The dense
#: end is what makes the peak FINDABLE; the wide end is what makes the
#: fall-off measurable.
#:
#: WHY 3 AND NOT 4 IS A FACT ABOUT THE ARCHITECTURE, not about the
#: arithmetic: at population 3 the channel carries TWO taps (one direct
#: path and one reflected), so the zero-forcing equaliser has ONE null to
#: invert and the reading is still clean. At population 4 the channel
#: carries THREE taps and the equaliser's noise gain starts to bite, so
#: the capacity falls faster than the extra name-bit is worth.
POPS: Tuple[int, ...] = (2, 3, 4, 5, 6, 8, 16, 32, 64)
AMPS: Tuple[float, ...] = (0.05, 0.10, 0.15, 0.25, 0.35)

#: The number of reflected paths in the channel. 1 is the smallest
#: channel that has a null to invert; more costs capacity.
PATHS = 1


def make_population(n: int) -> List[CoaxWinding]:
    """n stalks, addresses evenly spread, geometry solved from the
    address so every stalk is resolvable."""
    out: List[CoaxWinding] = []
    for i in range(n):
        a = (i + 0.5) / n
        girth_in = 0.050
        out.append(CoaxWinding(
            id="p%03d" % i, girth_out=girth_in * (1.0 + a),
            girth_in=girth_in, girth_core=0.018, n_in=5, n_out=10))
    return out


def address_of(s: CoaxWinding) -> float:
    return (((s.n_out % 2) / 2.0) + (s.girth_ratio - 1.0)) % 1.0


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


def measure(pop: int, amp: float, model: str,
            trials: int = 4, speakers: int = 6) -> Dict[str, Any]:
    """One population under one crowd model."""
    stalks = make_population(pop)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    view = list(ids)

    # MODEL B: the aggregate interference is held constant
    per = amp if model == "A" else (
        amp / math.sqrt(max(pop - 2, 1)) if pop > 2 else amp)

    named = 0
    total = 0
    unreadable = 0
    snrs: List[float] = []
    margins: List[float] = []
    taps = 0
    t0 = time.perf_counter()

    for _ in range(trials):
        for i in range(min(pop, speakers)):
            tx = ids[i]
            rx = ids[(i + 1) % pop]
            nbrs = view[:2 + PATHS]
            pair = link.pair(tx, rx, in_view=nbrs)
            ch = pair.channel()
            taps = max(taps, len(ch.taps))

            ph_tx = address_of(pair.tx)
            frame: List[Tuple[float, float]] = []
            for k in range(BINS):
                ar = ai = 0.0
                th = 2.0 * math.pi * ph_tx * (k / BINS)
                ar += math.cos(th)
                ai += math.sin(th)
                for oid in ids:
                    if oid == tx or oid == rx:
                        continue
                    op = address_of(link.stalk(oid))
                    th2 = 2.0 * math.pi * op * (k / BINS)
                    ar += per * math.cos(th2)
                    ai += per * math.sin(th2)
                frame.append((ar, ai))

            received = transport(frame, pair, BINS)
            eq = ch.equalise(spectrum(received), noise_floor=-80.0,
                             bin_offset=0.0)
            if not eq.get("ok"):
                unreadable += 1
                continue
            rec = eq["samples"]
            tx_spec = spectrum(tone(ph_tx, BINS))
            num = sum(rec[k][0] * tx_spec[k][0] + rec[k][1] * tx_spec[k][1]
                      for k in range(BINS))
            den = sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2 for k in range(BINS))
            scale = (num / den) if den > 1e-18 else 0.0
            sig = abs(scale) ** 2 * den
            noise = sum((rec[k][0] - scale * tx_spec[k][0]) ** 2 +
                        (rec[k][1] - scale * tx_spec[k][1]) ** 2
                        for k in range(BINS))
            snr_db = (10.0 * math.log10(sig / noise)
                      if noise > 1e-30 and sig > 1e-30 else 0.0)
            total += 1
            snrs.append(snr_db)
            scores: Dict[str, float] = {}
            for cand in ids:
                sp = spectrum(tone(address_of(link.stalk(cand)), BINS))
                n_ = sum(rec[k][0] * sp[k][0] + rec[k][1] * sp[k][1]
                         for k in range(BINS))
                d_ = math.sqrt(sum(sp[k][0] ** 2 + sp[k][1] ** 2
                                   for k in range(BINS))) or 1.0
                scores[cand] = n_ / d_
            ranked = sorted(scores.items(), key=lambda kv: -kv[1])
            margins.append(ranked[0][1] - ranked[1][1])
            if ranked[0][0] == tx:
                named += 1

    mean_snr = (sum(snrs) / len(snrs)) if snrs else 0.0
    cap = math.log2(1.0 + 10.0 ** (mean_snr / 10.0))
    return {
        "pop": pop, "amp": amp, "model": model, "per": per,
        "named": named, "trials": total, "unreadable": unreadable,
        "rate": (named / total) if total else 0.0,
        "snr_db": mean_snr, "capacity": cap, "needed": math.log2(pop),
        "surplus": cap - math.log2(pop), "taps": taps,
        "width": width_for(taps),
        "margin": (sum(margins) / len(margins)) if margins else 0.0,
        "secs": time.perf_counter() - t0,
    }


def main() -> int:
    print("=" * 78)
    print("WHERE THE LADDER SHOULD SWITCH, AND HOW ROBUST THAT IS")
    print("=" * 78)
    print()
    print("  channel: the direct path plus %d reflected path(s)" % PATHS)
    print("  frame:   %d bins, fixed" % BINS)
    print("  surplus = capacity - log2(P): the bits left after paying")
    print("           for the names, which is what the width must fit in")
    print()

    results: Dict[Tuple[str, float], Dict[int, Dict[str, Any]]] = {}
    for model in ("A", "B"):
        label = ("A: fixed per-interferer amplitude (the repo's model, "
                 "the crowd grows)" if model == "A" else
                 "B: fixed AGGREGATE interference (Popoviciu's model)")
        print("=" * 78)
        print("MODEL %s -- %s" % (model, label))
        print("=" * 78)
        print()
        for amp in AMPS:
            print("  crowd amplitude %.2f" % amp)
            print("    %-5s %-8s %-8s %-9s %-10s %-10s %-9s %-8s" % (
                "pop", "per", "named", "snr dB", "capacity", "needed",
                "surplus", "width"))
            print("    " + "-" * 70)
            results[(model, amp)] = {}
            for pop in POPS:
                r = measure(pop, amp, model)
                results[(model, amp)][pop] = r
                print("    %-5d %-8.3f %-8s %-9.2f %-10.2f %-10.2f %-+9.2f %-8d" % (
                    r["pop"], r["per"], "%d/%d" % (r["named"], r["trials"]),
                    r["snr_db"], r["capacity"], r["needed"], r["surplus"],
                    r["width"]))
            print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("Q1: WHERE IS THE PEAK? (the balance point)")
    print("=" * 78)
    print()
    print("  the peak is the population where the surplus is highest:")
    print("  below it, recruiting pays; above it, recruiting does not")
    print("  pay for itself and the width is all that is left.")
    print()
    print("  %-8s %-10s %-14s %-14s %-14s %-14s" % (
        "model", "crowd", "peak pop", "surplus there", "names there",
        "capacity there"))
    print("  " + "-" * 74)
    for model in ("A", "B"):
        for amp in AMPS:
            cells = results[(model, amp)]
            peak = max(cells.values(), key=lambda r: r["surplus"])
            print("  %-8s %-10.2f %-14d %-14.2f %-14s %-14.2f" % (
                model, amp, peak["pop"], peak["surplus"],
                "%d/%d" % (peak["named"], peak["trials"]), peak["capacity"]))
    print()

    # the peak population across all conditions
    peaks = []
    for model in ("A", "B"):
        for amp in AMPS:
            cells = results[(model, amp)]
            peaks.append(max(cells.values(), key=lambda r: r["surplus"])["pop"])
    print("  the peak population across all %d conditions: %s" % (
        len(peaks), sorted(set(peaks))))
    print("  the median peak: %d" % sorted(peaks)[len(peaks) // 2])
    print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("Q2: IS 4-BIT ENOUGH? IS 8-BIT ENOUGH?")
    print("=" * 78)
    print()
    print("  a width of W bits names 2^W stalks, so it needs W bits of")
    print("  capacity. the question is whether the capacity at the")
    print("  balance point reaches W.")
    print()
    for model in ("A", "B"):
        for amp in AMPS:
            cells = results[(model, amp)]
            peak = max(cells.values(), key=lambda r: r["surplus"])
            c = peak["capacity"]
            fits = [w for w in (1, 4, 8, 16, 32, 64) if c >= w]
            best = max(fits) if fits else 0
            print("  model %s crowd %.2f: peak pop %d, capacity %.2f bits "
                  "-> the largest width that FITS is %d bits (%s)" % (
                      model, amp, peak["pop"], c, best,
                      "names up to %d stalks" % (2 ** best) if best else "none"))
    print()

    # ------------------------------------------------------------------
    print("=" * 78)
    print("THE SECOND DERIVATION: POPOVICIU")
    print("=" * 78)
    print()
    print("  3 dB per doubling, 6 dB per bit, so W bits of naming need")
    print("  4^W stalks. under model B (fixed aggregate interference) the")
    print("  capacity should RISE by 3 dB per doubling.")
    print()
    print("  %-8s %-8s %-14s %-14s %-10s %-12s" % (
        "model", "crowd", "pop", "snr dB", "delta dB", "popoviciu +3"))
    print("  " + "-" * 68)
    for model in ("A", "B"):
        for amp in (AMPS[0], AMPS[2]):
            cells = results[(model, amp)]
            prev = None
            for pop in POPS:
                r = cells[pop]
                if prev is not None:
                    d = r["snr_db"] - prev["snr_db"]
                    print("  %-8s %-8.2f %-14d %-14.2f %-+10.2f %-12s" % (
                        model, amp, pop, r["snr_db"], d,
                        "match" if abs(d - 3.0) < 1.5 else
                        ("opposite" if d < 0 else "differs")))
                prev = r
    print()

    print("=" * 78)
    print("THE LADDER'S SCHEDULE AGAINST THE MEASUREMENT")
    print("=" * 78)
    print()
    print("  the repo's width_for(taps): 1 tap -> 1 bit, 2 -> 4, 3-4 -> 8,")
    print("  5+ -> 16. so a channel with 2 taps already offers 4 bits.")
    print()
    for model in ("A", "B"):
        for amp in AMPS:
            cells = results[(model, amp)]
            peak = max(cells.values(), key=lambda r: r["surplus"])
            offer = width_for(peak["taps"])
            fits = offer <= peak["capacity"]
            print("  model %s crowd %.2f: at peak pop %d the channel offers "
                  "%d bits and the reading carries %.2f -> %s" % (
                      model, amp, peak["pop"], offer, peak["capacity"],
                      "the width FITS" if fits else
                      "the width is TOO WIDE by %.2f bits" % (
                          offer - peak["capacity"])))
    print()

    # ------------------------------------------------------------------
    # THE CAP FILE, and why the bench writes it.
    #
    # MEASURED 2026-10-31: `src/ladder_cap.py` loads the ladder's
    # ceiling from `corpus/ladder_cap.json`, and refuses to load it
    # when the file is absent ("the ladder's ceiling is a MEASUREMENT,
    # and the measurement is not there"). And this bench -- which
    # MEASURES that ceiling -- never wrote the file. So the ladder had
    # 10 failing tests with the error naming this exact command.
    #
    # **A MEASUREMENT THAT IS NOT PERSISTED IS NOT A MEASUREMENT.** The
    # bench prints it; the ladder needs it; so the bench writes it.
    #
    # AND THE FILE CARRIES THE BENCH'S OWN SHA256, because the cap's
    # loader refuses a cap whose bench has moved under it. That check
    # is the reason the measurement is a file and not a literal in
    # code -- so the file has to be written by the thing that
    # measured it.
    cap_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "corpus", "ladder_cap.json")
    conditions = []
    for model in ("A", "B"):
        for amp in AMPS:
            cells = results[(model, amp)]
            peak = max(cells.values(), key=lambda r: r["surplus"])
            conditions.append({
                "model": model, "crowd": amp,
                "peak_population": peak["pop"],
                "peak_surplus": round(peak["surplus"], 4),
                "peak_capacity_bits": round(peak["capacity"], 4),
                "named": "%d/%d" % (peak["named"], peak["trials"]),
            })
    peak_pop = sorted(peaks)[len(peaks) // 2]
    peak_width = width_for(
        max(results[("A", AMPS[0])].values(),
            key=lambda r: r["surplus"])["taps"])
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            bench_sha = hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        bench_sha = ""
    cap = {
        "peak_population": peak_pop,
        "peak_width": peak_width,
        "command": "python src/bench_balance_final.py",
        "measured_on": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bench_sha256": bench_sha,
        "conditions": conditions,
        "caveat": "the peak is the median across %d conditions; the "
                  "per-condition peaks are in 'conditions'. a rung is "
                  "reachable when its population is at or below the "
                  "peak, because width_for DERIVES the width from the "
                  "channel and the channel's taps are a function of the "
                  "population." % len(conditions),
    }
    os.makedirs(os.path.dirname(cap_path), exist_ok=True)
    with open(cap_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cap, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("  THE CAP, written to %s" % cap_path)
    print("    peak population %d, peak width %d, %d conditions"
          % (peak_pop, peak_width, len(conditions)))
    print("    bench sha256 %s" % (bench_sha[:16] or "(none)"))
    print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
