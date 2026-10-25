"""
bench_ladder.py -- where should the ladder stop?

THE QUESTION
------------
Bobby, 2026-10-25: *"is 128 wiser mathematically or 256 cheap enough?
would it be 'smarter' at 512 or i am overthinking -- pls choose the best
compromise: sufficient fail-up and broadening, but not till its compute
cost outweighs it. do the math."*

THE ARITHMETIC, and it is three separate questions that the ladder's own
docstring has been treating as one:

  1. HOW MUCH AUTHORITY DOES A POPULATION BUY? The width IS the area
     of authority (`ladder.rs`: "Width is not a measure of reasoning
     quality -- 8 bits does not think better than 1 bit -- it is a
     measure of how much of the world that level is entitled to speak
     for"). So the width a population justifies is
     log2(the number of distinguishable regions).

  2. WHAT DOES WIDENING COST? Every rung adds a stalk in view, which
     adds a CHANNEL TAP, which adds a null, which the zero-forcing
     inversion must survive. And the DFT is naive -- paper 24 §7.3 says
     outright: "Fine at 8-64 points, useless at 2048."

  3. WHAT DOES WIDENING BUY? The value of a wider rung is not
     "more precision". It is: fewer refusals. The 747 lesson is that
     the overwhelming majority of decisions must NOT leave the cheap
     layer. So a wider rung is worth paying for only if the 1-bit gate
     actually refuses often enough to matter.

This script measures all three.

Run:
    python src/bench_ladder.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Dict, List, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    WIDTHS,
    REACH,
    RESOLVED,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# A SYNTHETIC POPULATION
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks, each with its own geometry.

    The geometry varies the way the standard four do: the girths and
    the turn counts both move, so no two stalks share an address.
    """
    out: List[CoaxWinding] = []
    for i in range(n):
        core = 0.018 + 0.0007 * (i % 7)
        inner = 0.050 + 0.0011 * (i % 11)
        outer = 0.090 + 0.0019 * (i % 13)
        # keep the concentric order: core < inner < outer
        if not (core < inner < outer):
            core = 0.016
            inner = 0.048
            outer = 0.092
        n_in = 5 + (i % 6)
        n_out = 11 + (i % 9)
        out.append(CoaxWinding(id="p%03d" % i, girth_out=outer,
                                girth_in=inner, girth_core=core,
                                n_in=n_in, n_out=n_out))
    return out


# ===========================================================================
# THE MEASUREMENTS
# ===========================================================================

def time_exchange(link: InterstalkLink, tx: str, rx: str,
                  view: List[str], repeats: int = 1) -> float:
    """The wall-clock cost of one exchange, in milliseconds."""
    t0 = time.perf_counter()
    for _ in range(repeats):
        link.exchange(tx, rx, in_view=view)
    return (time.perf_counter() - t0) * 1000.0 / repeats


def measure_at(population: int, bins: int,
               repeats: int = 1) -> Dict[str, object]:
    """One measurement: a population of `population` stalks, `bins` bins."""
    stalks = make_population(population)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=bins)
    ids = [s.id for s in stalks]
    tx, rx = ids[0], ids[1]
    view = ids[:population]

    ex = link.exchange(tx, rx, in_view=view)
    ms = time_exchange(link, tx, rx, view, repeats=repeats)
    taps = ex.channel_taps
    return {
        "population": population,
        "bins": bins,
        "taps": taps,
        "alignment": ex.alignment,
        "allowed": ex.allowed,
        "width": ex.width_used,
        "notch_db": ex.notch_db,
        "ms": ms,
    }


def bits_justified(population: int) -> int:
    """How many bits of authority a population of this size justifies.

    A population of P stalks presents P^2 PAIRS to speak about (who is
    near whom, who couples to whom), so the number of distinguishable
    regions is P^2 and the bits needed to name one is 2*log2(P).

    This is the key number, and it is the answer to "is 128 wiser or is
    256 cheap enough": the width is a function of the POPULATION, and
    the population is the thing that is physically bounded.
    """
    return max(1, int(math.ceil(2 * math.log2(max(population, 2)))))


# ===========================================================================
# THE MAIN
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("WHERE SHOULD THE LADDER STOP -- measured, not guessed")
    print("=" * 78)
    print()

    # ---------------------------------------------------------------
    # 1. THE AUTHORITY ARITHMETIC
    # ---------------------------------------------------------------
    print("=" * 78)
    print("1. HOW MUCH AUTHORITY DOES A POPULATION BUY?")
    print("=" * 78)
    print()
    print("   width IS the area of authority. A population of P stalks")
    print("   presents P^2 pairs, so the bits needed to name a region")
    print("   is 2*log2(P).")
    print()
    print("   %-14s %-10s %-14s %s" % ("population", "bits", "stalks for", "note"))
    for p in (2, 4, 8, 16, 32, 64, 128, 256, 1024, 65536):
        b = bits_justified(p)
        # how many stalks would be needed for each ladder rung
        need = {w: int(round(math.pow(2, w / 2.0))) for w in (16, 32, 64, 128, 256)}
        print("   %-14d %-10d %-14s %s" % (
            p, b,
            "2^%d" % (b / 2.0),
            "W16 needs %d" % need[16] if p < need[16] else
            ("W32 needs %d" % need[32] if p < need[32] else
             ("W64 needs %d" % need[64] if p < need[64] else
              ("W128 needs %d" % need[128] if p < need[128] else
               ("W256 needs %d" % need[256] if p < need[256] else "W256+"))))))
    print()
    print("   READ THAT COLUMN. To justify 128 bits of authority you need")
    print("   2^64 stalks. To justify 256 you need 2^128. The upper rungs")
    print("   are not expensive -- they are UNREACHABLE. The population")
    print("   is the binding constraint, and it binds long before the")
    print("   compute does.")
    print()

    # ---------------------------------------------------------------
    # 2. THE COST
    # ---------------------------------------------------------------
    print("=" * 78)
    print("2. WHAT DOES WIDENING COST?")
    print("=" * 78)
    print()
    print("   %-12s %-8s %-8s %-12s %-10s %-12s" % (
        "population", "taps", "bins", "alignment", "ms", "notch dB"))
    for pop, bins in ((4, 32), (8, 32), (16, 64), (32, 128),
                      (64, 256), (128, 512)):
        m = measure_at(pop, bins, repeats=1)
        print("   %-12d %-8d %-8d %-12.8f %-10.2f %-12.3f" % (
            m["population"], m["taps"], m["bins"], m["alignment"],
            m["ms"], m["notch_db"]))
    print()
    print("   the naive DFT is O(bins^2) and the inversion is O(bins*taps),")
    print("   so the cost grows as the SQUARE of the resolution while the")
    print("   benefit grows as the LOGARITHM of the population. That")
    print("   asymmetry is the whole answer.")
    print()

    # ---------------------------------------------------------------
    # 3. THE VALUE: DOES THE 1-BIT GATE REFUSE OFTEN ENOUGH?
    # ---------------------------------------------------------------
    print("=" * 78)
    print("3. WHAT DOES WIDENING BUY? THE ESCALATION RATE")
    print("=" * 78)
    print()
    print("   A wider rung is worth paying for only if the 1-bit gate")
    print("   refuses often enough to matter. So: over many pairs at a")
    print("   given population, how often does the 1-bit reading stand?")
    print()
    print("   %-12s %-10s %-12s %-12s %-14s" % (
        "population", "bins", "1-bit pass", "mean align", "width used"))
    for pop, bins in ((4, 64), (8, 64), (16, 128), (32, 256), (64, 512)):
        stalks = make_population(pop)
        core = WoundCore(stalks=stalks)
        link = InterstalkLink(core=core, bins=bins)
        ids = [s.id for s in stalks]
        view = ids[:pop]
        ok = 0
        total = 0
        aligns: List[float] = []
        widths: Dict[int, int] = {}
        for i in range(min(pop, 12)):
            for j in range(min(pop, 12)):
                if i == j:
                    continue
                e = link.exchange(ids[i], ids[j], in_view=view)
                total += 1
                aligns.append(e.alignment)
                if e.allowed:
                    ok += 1
                widths[e.width_used] = widths.get(e.width_used, 0) + 1
        mean_align = sum(aligns) / len(aligns) if aligns else 0.0
        print("   %-12d %-10d %-12s %-12.8f %-14s" % (
            pop, bins,
            "%d/%d" % (ok, total),
            mean_align,
            ", ".join("%dx%d" % (k, v) for k, v in sorted(widths.items()))))
    print()
    print("   If the 1-bit reading stands at every population, then the")
    print("   ladder is not being USED for width at all -- the 1-bit")
    print("   gate is doing the work and the wider rungs are dead code.")
    print("   Which is exactly the failure the atlas exam's reachability")
    print("   area exists to find.")
    print()

    # ---------------------------------------------------------------
    # 4. THE VERDICT
    # ---------------------------------------------------------------
    print("=" * 78)
    print("4. THE VERDICT")
    print("=" * 78)
    print()
    print("   The ladder's rungs are NAMES for areas of authority:")
    for w in WIDTHS:
        r = REACH.get(w, 0)
        if r >= 2 ** 40:
            print("     W%-4d reach %-22s (2^%d stalk units)" % (
                w, ">= 2^40", w - 1))
        else:
            print("     W%-4d reach %-22d stalk units" % (w, r))
    print()
    print("   The population that would justify each rung:")
    for w in (16, 32, 64, 128, 256):
        print("     W%-4d needs %d stalks" % (w, int(round(2 ** (w / 2.0)))))
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
