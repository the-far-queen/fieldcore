"""
diag_balance.py -- WHICH LIMIT IS BINDING: the crowd, the equaliser, or
the frame's resolution?

Central rule 4: a surprising result means suspect the code first.

bench_balance2 measured, at 128 bins with evenly spread addresses:

    crowd 0.15   pop  4  16/16 named   capacity 4.48
                 pop  8  12/24 named   capacity 2.94
                 pop 16   0/24 named   capacity 1.54

The collapse from 100% to 0% between population 8 and 16 is not a
resolution limit -- the addresses are 8 bins apart at pop 16, which a
DFT can separate. So something else is doing it, and there are exactly
three candidates:

  A. THE CROWD. Each other stalk radiates, so the aggregate
     interference grows linearly with the population. At pop 64 that is
     63 interferers at amplitude 0.15 = 9.5x the speaker's amplitude.

  B. THE EQUALISER'S NOISE GAIN. The channel has one tap per stalk in
     view (the direct path plus one reflected path per other stalk).
     A zero-forcing equaliser inverts that matrix, and its noise gain
     grows with the tap count. So RECRUITING MORE STALKS MAKES THE
     EQUALISER NOISIER -- which is backwards for a design whose whole
     point is "spend pop not bits".

  C. THE FRAME'S RESOLUTION. Bounded by the address spacing, and
     measured separately so it can be ruled out rather than assumed.

This runs three experiments, one per candidate:

  EXP 1  crowd = 0, population varies.
         If naming still collapses, the crowd is NOT the cause.
  EXP 2  population fixed, crowd varies.
         Isolates the crowd's contribution.
  EXP 3  the channel's tap count is DECOUPLED from the population --
         the pair keeps a fixed number of reflected paths while the
         population grows. If naming survives, the equaliser's noise
         gain is the binding constraint and the fix is in the design,
         not in the question.

Run:
    python src/diag_balance.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Any, Dict, List, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from bench_balance2 import (  # noqa: E402
    address_of,
    make_population,
    min_spacing_bins,
    read,
    spectrum,
    tone,
)
from interstalk_link import InterstalkLink, REACH, width_for  # noqa: E402
from wound_core import WoundCore  # noqa: E402

BINS = 128


def run(pop: int, crowd_amp: float, trials: int = 4,
        speakers: int = 6, fixed_taps: int = 0) -> Dict[str, Any]:
    """One population, one crowd amplitude.

    `fixed_taps` > 0 caps the channel's reflected paths, decoupling the
    tap count from the population. That is EXP 3.
    """
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
    taps = 0
    t0 = time.perf_counter()

    for _ in range(trials):
        for i in range(min(pop, speakers)):
            tx = ids[i]
            rx = ids[(i + 1) % pop]
            # EXP 3: cap the neighbours so the tap count is fixed
            in_view = view
            if fixed_taps > 0:
                in_view = view[:2 + fixed_taps]
            r = read(link, tx, rx, in_view, ids, crowd_amp, BINS)
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
    return {
        "pop": pop,
        "crowd": crowd_amp,
        "named": named,
        "trials": total,
        "unreadable": unreadable,
        "rate": (named / total) if total else 0.0,
        "snr_db": mean_snr,
        "taps": taps,
        "spacing": min_spacing_bins(stalks, BINS),
        "margin": (sum(margins) / len(margins)) if margins else 0.0,
        "secs": time.perf_counter() - t0,
    }


def line(r: Dict[str, Any]) -> str:
    return ("  pop %-4d crowd %-5.2f taps %-4d spacing %-6.1f "
            "named %-7s snr %-8.2f margin %-8.3f" % (
                r["pop"], r["crowd"], r["taps"], r["spacing"],
                "%d/%d" % (r["named"], r["trials"]), r["snr_db"], r["margin"]))


def main() -> int:
    print("=" * 78)
    print("WHICH LIMIT IS BINDING?")
    print("=" * 78)
    print()

    print("=" * 78)
    print("EXP 1: NO CROWD AT ALL. if naming collapses here, the crowd")
    print("       is not the cause -- the channel or the equaliser is.")
    print("=" * 78)
    print()
    for pop in (4, 8, 16, 32, 64):
        print(line(run(pop, 0.0)))
    print()

    print("=" * 78)
    print("EXP 2: POPULATION FIXED AT 16, CROWD VARIES.")
    print("=" * 78)
    print()
    for amp in (0.0, 0.02, 0.05, 0.15, 0.35):
        print(line(run(16, amp)))
    print()

    print("=" * 78)
    print("EXP 3: THE TAP COUNT IS CAPPED, THE POPULATION IS NOT.")
    print("       the channel keeps a fixed number of reflected paths,")
    print("       so the equaliser's noise gain stops growing while the")
    print("       crowd still does.")
    print("=" * 78)
    print()
    for cap in (0, 2, 6, 14, 30):
        print("  -- capped at %d reflected paths --" % cap)
        for pop in (8, 16, 32):
            print(line(run(pop, 0.15, fixed_taps=cap)))
        print()

    print("=" * 78)
    print("EXP 4: THE CROWD SCALED DOWN AS THE POPULATION GROWS, so the")
    print("       AGGREGATE interference is held FIXED.")
    print("       this is the 'fixed interference budget' model, and it")
    print("       is the one a population code assumes.")
    print("=" * 78)
    print()
    for pop in (4, 8, 16, 32, 64):
        amp = 0.35 / math.sqrt(pop - 1) if pop > 1 else 0.35
        r = run(pop, amp)
        r["crowd"] = amp
        print(line(r))
    print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
