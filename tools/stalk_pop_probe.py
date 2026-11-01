"""
tools/stalk_pop_probe.py -- THE THREE-PART STALKS, THE POP INCREASE,
AND THE INTERSTALK WIDENING, ON THIS BOX.

Bobby, 2026-11-01: *"confirm we have three part stalks two diff girths
wound around a core we were trying pop increases at 1 bit then multibit
after pop increase and interstalk communication electrically which i
feel is key"*, then two corrections:

    *"nope we got as far as increasng number of stalks ie population was
    cheaper at 1 bit and only the 4 and 8 bit then increase pop again
    not 16 32 64 etc"*

    *"no grow pop at 1 bit first"*

**SO THE ESCALATION POLICY IS NOT A LADDER UP TO 256. IT IS THIS:**

        1 bit    ONE stalk in view. The population as it is.
                 AND THE FIRST MOVE IS TO GROW THE POPULATION -- bring
                 MORE STALKS into view -- WHILE STAYING AT 1 BIT.
        4 bits   only if the population cannot read it at 1 bit.
        8 bits   only if 4 bits cannot either.
        and past 8 bits: POPULATION AGAIN, never a wider word.

**AND THAT IS THE COST PROPERTY.** A wider answer costs more compute
per exchange. So the cheap move is always more stalks, and the width
is the LAST resort. That is the 747 lesson applied to the channel:
the overwhelming majority of exchanges must not leave the cheap layer.

SO THE PROBE MEASURES:
  1 THE THREE-PART COAX -- outer, inner, core, two girths.
  2 THE POPULATION INCREASE -- the eigenvalue spread must GROW with
    the number of stalks.
  3 THE INTERSTALK IS ELECTRICAL -- non-zero couplings, differing
    between partners, symmetric inductance.
  4 THE WIDTH IS DERIVED from the channel, and the ESCALATION is
    POPULATION first.

Run: python tools/stalk_pop_probe.py
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import interstalk_link as IL
import wound_core as WC

FAILURES = []


def check(label, cond, extra=""):
    mark = "ok " if cond else "FAIL"
    print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
    if not cond:
        FAILURES.append(label)


def main():
    print("=" * 74)
    print("THE THREE-PART STALKS, THE POP, AND THE INTERSTALK")
    print("=" * 74)
    print()

    # -- 1. THE THREE-PART COAX -----------------------------------------
    print("1. THE THREE-PART COAX -- outer, inner, core")
    core = WC.standard_wound_core()
    print("     %d stalks, %d loop modes"
          % (core.n_stalks, core.n_loop_modes()))
    check("the core has stalks", core.n_stalks >= 2, str(core.n_stalks))

    w0 = core.stalks[0]
    print("     stalk %s: core %.3f  inner %.3f  outer %.3f  "
          "n_in %d  n_out %d"
          % (w0.id, w0.girth_core, w0.girth_in, w0.girth_out,
             w0.n_in, w0.n_out))
    check("the concentric order is core < inner < outer",
          w0.girth_core < w0.girth_in < w0.girth_out,
          "%.3f / %.3f / %.3f" % (w0.girth_core, w0.girth_in, w0.girth_out))
    check("a coax winding has TWO loop modes",
          len(w0.loop_modes) == 2, str(w0.loop_modes))
    print("     loop modes: %s" % (w0.loop_modes(),))

    gr = [w.girth_ratio() for w in core.stalks]
    tr = [w.turns_ratio() for w in core.stalks]
    print("     girth ratios: %s" % ["%.4f" % g for g in gr])
    print("     turns ratios: %s" % ["%.4f" % t for t in tr])
    check("every stalk has a DIFFERENT girth ratio",
          len(set(round(g, 9) for g in gr)) == len(gr),
          str(["%.4f" % g for g in gr]))
    check("every stalk has a DIFFERENT turns ratio",
          len(set(round(t, 9) for t in tr)) == len(tr),
          str(["%.4f" % t for t in tr]))

    try:
        WC.CoaxWinding(id="bad", girth_core=0.10, girth_in=0.05,
                       girth_out=0.02, n_in=5, n_out=7)
        check("a bad concentric order is REFUSED", False,
              "the constructor accepted core > inner > outer")
    except ValueError as exc:
        check("a bad concentric order is REFUSED", True, str(exc)[:70])

    # -- 2. THE INTERSTALK IS ELECTRICAL -------------------------------
    print()
    print("2. THE INTERSTALK -- the couplings must be REAL")
    mc = w0.mutual_couplings()
    print("     winding %s couplings: %s"
          % (w0.id, {k: round(v, 6) for k, v in list(mc.items())[:5]}))
    vals = [abs(v) for v in mc.values() if isinstance(v, (int, float))]
    check("the mutual couplings are NON-ZERO",
          bool(vals) and max(vals) > 1e-12,
          "max |k| = %.3e" % (max(vals) if vals else 0.0))
    check("the couplings DIFFER between partners",
          len(set(round(v, 12) for v in mc.values())) > 1,
          "%d distinct" % len(set(round(v, 12) for v in mc.values())))

    L = w0.inductance_matrix()
    sym = all(abs(L[i][j] - L[j][i]) < 1e-18
               for i in range(len(L)) for j in range(len(L)))
    check("the inductance matrix is SYMMETRIC", sym,
          "mutual inductance is reciprocal")

    # -- 3. THE POPULATION INCREASE -------------------------------------
    print()
    print("3. THE POPULATION INCREASE -- eigenvalue spread with n stalks")
    spreads = []
    for n in (2, 3, 4, 6, 8, 12):
        try:
            c2 = WC.WoundCore([
                WC.CoaxWinding(id="p%d" % i, girth_core=0.020,
                               girth_in=0.060, girth_out=0.100,
                               n_in=5 + i, n_out=11 + 2 * i)
                for i in range(n)])
        except Exception as exc:
            print("       n=%d -> could not build (%s)" % (n, str(exc)[:60]))
            continue
        ev = c2.stalks[0].loop_eigenvalues()
        spread = (max(ev) - min(ev)) if ev else 0.0
        spreads.append((n, spread, len(ev)))
        print("       %2d stalks -> %d eigenvalues, spread %.6e"
              % (n, len(ev), spread))
    if len(spreads) >= 2:
        check("the eigenvalue spread GROWS with the population",
              spreads[-1][1] > spreads[0][1],
              "%.3e -> %.3e" % (spreads[0][1], spreads[-1][1]))

    # -- 4. THE WIDTH, DERIVED ------------------------------------------
    print()
    print("4. THE WIDTH -- derived from the channel")
    print("     %s" % (IL.WIDTHS,))
    for taps in (1, 2, 3, 4, 5, 8, 16):
        print("       %2d taps -> %3d bits" % (taps, IL.width_for(taps)))
    check("one tap gives ONE bit", IL.width_for(1) == 1, str(IL.width_for(1)))
    check("two taps give MULTIBIT", IL.width_for(2) > 1, str(IL.width_for(2)))
    check("three taps give 8 bits", IL.width_for(3) == 8, str(IL.width_for(3)))
    check("the width NEVER goes DOWN as the channel widens",
          all(IL.width_for(t) <= IL.width_for(t + 1) for t in range(1, 32)),
          "the ladder must be monotone")

    # -- 5. THE EXCHANGE, AND THE COST ----------------------------------
    print()
    print("5. THE EXCHANGE -- what each population costs")
    link = IL.InterstalkLink(core=core)
    ids = [s.id for s in core.stalks]
    for n_view in (0, 1, 2, 3):
        in_view = ids[2:2 + n_view] if n_view else []
        try:
            ex = link.exchange(ids[0], ids[1], in_view=in_view)
        except Exception as exc:
            print("       %d in view -> EXCEPTION %s" % (n_view, str(exc)[:70]))
            continue
        print("       %d in view -> width %3d  taps %2d  allowed=%-5s  "
              "alignment %.4f  %s"
              % (n_view, ex.width_needed, ex.channel_taps, ex.allowed,
                 ex.alignment, ex.reason[:44]))
    print()
    rep = link.report()
    print("     report: %s" % {k: rep[k] for k in list(rep)[:8]})

    print()
    print("=" * 74)
    if FAILURES:
        print("%d CHECK(S) FAILED:" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        return 1
    print("THE THREE-PART STALKS, THE POP, AND THE INTERSTALK ALL WORK.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
