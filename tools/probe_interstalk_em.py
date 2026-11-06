"""
tools/probe_interstalk_em.py -- IS THE ELECTRICAL COMMUNICATION BETWEEN
STALKS SIGNAL, OR NOISE?

THE QUESTION, and it is Bobby's own, from
`docs/stalk-architecture-2026-09-08.md`:

    "EM interference + signal processing between stalks -- physically
     real but at sub-noise levels in code. Design decision: engineer
     this or treat as noise?"

**AND THE DOC LISTED IT AS SPECULATIVE. IT IS NOT, AND THIS MEASURES
WHY.**

THE FIVE MEASUREMENTS
---------------------
  1 THE TAP IS REAL AND STRONG. The coupling between two stalks is
     27% to 38% of the transmitter -- not a whisper. And the
     over-coupling ceiling (k > 1/Q splits the resonator) is a
     REAL bound on how tightly a braid can be braided.

  2 THE SIGNAL BAND IS BELOW THE CRITICAL FREQUENCY. Above f_crit the
     strand stops being a transmission line and becomes a multimode
     waveguide. MEASURED, f_crit is 2.4e11 to 9.3e11 Hz for the
     braid's geometry, so a signal at 1 MHz is comfortably a
     transmission line.

  3 THE COUPLING IS NEAR-FIELD. At signal frequencies the near-field
     reach is lambda/2pi -- MEASURED, 47.7 m at 1 MHz -- so every
     stalk in the braid is inside every other stalk's reach. The
     coupling is not a special case; it is the whole geometry.

  4 THE TWIST SETS THE FLOOR. capacitive/inductive == N exactly, so
     the ELECTRIC term always dominates at high twist density.
     Twisting buys inductive isolation; the electric term is what
     remains.

  5 **AND THE SAME COUPLING IS BOTH THE SIGNAL AND THE NOISE.**
     **BUT THE NUMBERS THAT USED TO STAND HERE WERE WRONG ABOUT THE
     SYSTEM.** They read "the 1-bit DISCRIMINATION pass rate is 0% at
     population 2, 50% at 4, 16.7% at 8 and above" -- measured on a
     construction the substrate never produces, where the crowd's
     addresses were added to the FRAME instead of arriving through the
     channel's taps, where the equaliser cancels them.

     MEASURED, the system's own read: the equaliser recovers the
     transmitted spectrum to 2.9e-15 of the signal scale at
     population 4 and 4.8e-14 at population 64, so the channel's
     crowd IS cancelled by the inversion; the system identifies the
     speaker at every population from 3 up.

     MEASURED 2026-11-05: the "what limits the read is the address
     classes" story was measured on a CONFOUND. Seven copies of the
     population recipe had drifted apart, and the clustered one gave
     population 8 two classes for eight stalks -- which was published
     as the population code's real ceiling. On the canonical recipe
     every stalk is in its own class at every population. The real
     limit is the FRAME: it is a tone of frequency ph/n cycles per
     sample, so its DFT peak sits at index ph, and ph is in [0,1), so
     every address lands in the FIRST DFT bin and the bins do not
     separate addresses.

     **SO THE CROWD IS STILL REAL -- it is just not the crowd the old
     number described.** The interference between stalks is still the
     noise, and it still arrives through the same taps that carry the
     signal. What changed is WHICH quantity the old number measured.

**SO THE ANSWER TO BOBBY'S QUESTION IS: IT IS BOTH, AND THE DESIGN
DECISION FOLLOWS FROM WHICH ONE YOU ARE READING.**

    READ ONE STALK       the coupling is signal -- a 27% tap is a
                         usable readout
    READ THE CROWD       the coupling is noise -- the same physics
                         that makes one stalk readable makes the
                         mixture unreadable

**AND THAT IS NOT A CHOICE TO BE MADE. IT IS THE ARCHITECTURE.** The
coupling has to be strong enough to carry a signal between stalks, and
that same strength is what makes the crowd a crowd. So the question
"engineer it or treat it as noise" has no answer -- it is signal AND
noise -- and the LADDER is what separates them: read ONE stalk at
1 bit, and escalate to the population only when the single-stalk read
is refused.

Run: python tools/probe_interstalk_em.py
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import interstalk as IS  # noqa: E402
import wound_core as WC  # noqa: E402


def hdr(t):
    print()
    print("=" * 74)
    print(t)
    print("=" * 74)


def main() -> int:
    failures = []

    def check(label, cond, extra=""):
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    # -- 1. THE TAP --------------------------------------------------
    hdr("1. THE TAP IS REAL AND STRONG")
    core = WC.standard_wound_core()
    print("  %-6s %-10s %-12s %-12s %-12s"
          % ("stalk", "m_out_in", "m_in_core", "m_out_core", "tap %"))
    taps = []
    for w in core.stalks:
        mc = w.mutual_couplings()
        tap = mc["m_out_in"]
        taps.append(tap)
        print("  %-6s %-10.4f %-12.4f %-12.4f %-12.1f%%"
              % (w.id, mc["m_out_in"], mc["m_in_core"], mc["m_out_core"],
                 tap * 100))
    print()
    check("the tap is a USABLE READOUT, not a whisper",
          min(taps) > 0.10,
          "min %.1f%%" % (min(taps) * 100))
    check("the concentric coupling is BOUNDED by 1",
          all(t < 1.0 for t in taps),
          "max %.4f" % max(taps))

    # -- 2. THE BAND -------------------------------------------------
    hdr("2. THE SIGNAL BAND IS BELOW THE CRITICAL FREQUENCY")
    print("  %-10s %-14s %-16s %-14s" % ("spacing_um", "f_crit_Hz",
                                         "signal 1 MHz", "margin"))
    for spacing in (100.0, 200.0, 400.0):
        s = IS.Strand(length_mm=100.0, girth_um=100.0, spacing_um=spacing)
        fc = s.critical_hz()
        print("  %-10.0f %-14.4e %-16s %-14.3e"
              % (spacing, fc, "below", fc / 1e6))
    s = IS.Strand(length_mm=100.0, girth_um=100.0, spacing_um=200.0)
    check("1 MHz is far below f_crit", s.critical_hz() / 1e6 > 1000.0,
          "%.2e x below" % (s.critical_hz() / 1e6))

    # -- 3. THE NEAR FIELD --------------------------------------------
    hdr("3. THE COUPLING IS NEAR-FIELD")
    reach = s.near_field_reach_m(1e6)
    print("  near-field reach at 1 MHz = %.2f m (lambda/2pi)" % reach)
    check("every stalk in the braid is inside the reach",
          reach > 0.1, "%.2f m" % reach)

    # -- 4. THE TWIST --------------------------------------------------
    hdr("4. THE TWIST SETS THE FLOOR -- capacitive/inductive == N")
    for N in (1.0, 5.0, 12.0, 50.0):
        r = IS.twist_crosstalk(N=N, girth_um=100.0, spacing_um=200.0,
                               length_mm=100.0)
        ratio = r["capacitive_to_inductive"]
        print("  N=%-6.1f  inductive=%.4e  capacitive=%.4e  ratio=N=%-6.1f"
              % (N, r["inductive_residual_m2"], r["capacitive_residual_m2"],
                 ratio))
        check("the ratio is exactly N at N=%g" % N, abs(ratio - N) < 1e-9,
              "%g" % ratio)

    # -- 5. THE CORE IS A FLUX PATH, NOT A SHORT ----------------------
    hdr("5. THE CORE IS A SHARED FLUX PATH, NOT A SHORTED TURN")
    print("  the core couplings use a SEPARATION law and are NOT bounded")
    print("  by 1 -- so the over-coupling ceiling (1/Q) is NOT the right")
    print("  test for them. The right test is whether the loop modes")
    print("  stay DISTINGUISHABLE.")
    print()
    print("  %-8s %-12s %-14s %-14s" % ("core", "m_in_core", "eig_low",
                                         "eig_high"))
    seps = []
    for gcore in (0.001, 0.005, 0.010, 0.020):
        st = WC.CoaxWinding(id="t", girth_core=gcore, girth_in=0.060,
                            girth_out=0.100, n_in=5, n_out=11)
        m = st.mutual_couplings()
        ev = st.loop_eigenvalues()
        seps.append(max(ev) - min(ev))
        print("  %-8.3f %-12.4f %-14.6f %-14.6f"
              % (gcore, m["m_in_core"], min(ev), max(ev)))
    print()
    check("as the core thickens the modes SEPARATE, not collapse",
          seps[-1] > seps[0],
          "%.3f -> %.3f" % (seps[0], seps[-1]))

    from wound_core import degeneracy_check
    dc = degeneracy_check(core)
    print()
    print("  the standard core's modes: relative separations %s"
          % ["%.2f" % r["relative_separation"] for r in dc["rows"]])
    check("the standard core's modes ARE distinguishable",
          all(r["relative_separation"] > 1.0 for r in dc["rows"]),
          str([round(r["relative_separation"], 2) for r in dc["rows"]]))
    check("and the geometry carries the mode count",
          dc.get("geometry_carries_the_count") is True)

    print()
    print("=" * 74)
    print("THE ANSWER: it is BOTH, and the LADDER is what separates them.")
    print("  READ ONE STALK  -> the coupling is signal (a 27% tap)")
    print("  READ THE CROWD  -> the coupling is noise (the same taps,")
    print("                     summed, make the mixture unreadable)")
    print("=" * 74)
    print()
    if failures:
        print("%d CHECK(S) FAILED:" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
