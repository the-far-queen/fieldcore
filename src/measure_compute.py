
"""
measure_compute.py -- THE ANALOG-COMPUTE MEASUREMENT, as a runnable file.

So the numbers Bobby asked for are reproducible rather than quoted. Each
section prints the measurement it makes.

Run:
    python src/measure_compute.py
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK, "fieldcore", "src"),
           os.path.join(WORK, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def locus_measure():
    """Does the state hold the input, and does the phase lock?"""
    import numpy as np
    from locus import Locus
    from wound_core import CoaxWinding
    st = [CoaxWinding(id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                       girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                       n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    loc = Locus(stalk_ids=[s.id for s in st], stalks=st)
    out = {}
    for k in (0, 3, 6):
        d = [0.0] * 8
        d[k] = 0.5
        loc2 = Locus(stalk_ids=[s.id for s in st], stalks=st)
        for _ in range(8):
            loc2.resonate(d)
        for _ in range(6):
            loc2.resonate([0.0] * 8)
        g = np.asarray(loc2.state.gain)
        out["tilt@%d" % k] = {"argmax": int(np.argmax(g)),
                               "spread": round(float(np.max(g) - np.min(g)), 9)}
    # and the unbounded amplitude
    loc3 = Locus(stalk_ids=[s.id for s in st], stalks=st)
    for _ in range(32):
        loc3.resonate([0.1] * 8)
    out["32 constant drives -> norm"] = round(
        float(np.linalg.norm(loc3.state.gain)), 4)
    loc4 = Locus(stalk_ids=[s.id for s in st], stalks=st)
    for _ in range(4):
        loc4.resonate([0.0] * 8)
    out["4 zero drives -> norm"] = round(
        float(np.linalg.norm(loc4.state.gain)), 6)
    return out


def landscape_measure():
    """Does the ball always find the same hole? And do the traps
    discriminate?"""
    import basin_landscape as BL
    out = {}
    land = BL.random_landscape(seed=0, n=6)
    drops = {}
    for x0 in (-6.0, -4.0, -2.0, -0.5, 0.5, 2.0, 4.0, 6.0):
        drops["x0=%+.1f" % x0] = BL.drop(land, x0)["settled"]
    out["seed 0 drops"] = drops
    tot = glob = 0
    per = []
    for seed in range(8):
        land = BL.random_landscape(seed=seed, n=6)
        g = min(land.minima(), key=lambda m: land.height(m))
        hits = 0
        for x0 in (-6, -3, -1, 0, 1, 3, 6):
            r = BL.drop(land, x0)
            tot += 1
            if abs(r["settled"] - g) < 0.05:
                glob += 1
                hits += 1
        per.append(hits)
    out["global min reached"] = "%d of %d (%.1f%%)" % (glob, tot, 100.0 * glob / tot)
    out["per landscape"] = per
    return out


def main() -> int:
    print("=" * 74)
    print("HOW THE ANALOG COMPUTE WORKS -- THE MEASUREMENTS")
    print("=" * 74)
    print()
    print("1. THE LOCUS: does the state hold the input, and does the")
    print("   phase lock?")
    for k, v in locus_measure().items():
        print("   %-26s %s" % (k, v))
    print()
    print("2. THE LANDSCAPE: does the ball always find the same hole?")
    for k, v in landscape_measure().items():
        print("   %-26s %s" % (k, v))
    print()
    print("3. THE DISCRIMINATION: deep_narrow vs shallow_wide")
    import basin_landscape as BL
    for name, land in (("deep_narrow", BL.deep_narrow_vs_shallow_wide()),
                       ("shallow_wide", BL.one_bump())):
        rows = [(x0, BL.drop(land, x0)["settled"])
                for x0 in (-4.0, -2.0, 0.0, 2.0, 4.0)]
        print("   %-12s minima=%s" % (name, [round(m, 3) for m in sorted(land.minima())]))
        print("      %s" % [(x, round(s, 3)) for x, s in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
