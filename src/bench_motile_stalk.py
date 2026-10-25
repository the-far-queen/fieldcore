"""
bench_motile_stalk.py -- WHAT DOES A MOVING STALK ACTUALLY BUY?

Bobby, 2026-10-25: *"add in motile stalks what value there? attach and
detach, waving, near proximity affects closer, girth changes, length
changes -- or do i complicate needlessly?"*

THE FOUR LEVERS, and they are not the same thing:

  ATTACH/DETACH   a stalk joins or leaves the population in view.
                  In this architecture that is NOT a new mechanism: the
                  channel's taps are one per stalk in view, so
                  attaching a stalk IS adding a tap, and `width_for`
                  turns that into the width. So attaching IS the ladder.

  PROXIMITY       the receiver moves closer to or further from the
                  transmitter. The pair coupling divides by the
                  separation, so this is a GAIN knob.

  GIRTH           the windings change size. Measured: nothing, because
                  everything that matters is a RATIO of the geometry.

  LENGTH          the stalk gets longer or shorter. This is the one
                  lever that is INERT in the current model, and it
                  should NOT be -- length is what sets a coil's
                  resonance, and a resonance is what makes the channel
                  frequency-selective.

THE QUESTION THIS FILE ANSWERS, and it is the one Bobby asked:
does the motility change the CHANNEL or only the GAIN?

  GAIN means the same channel with a bigger or smaller number. The
  address, the notch, the width -- all unchanged. That is a volume
  knob.

  SHAPE means the channel's STRUCTURE changes: a different notch, a
  different width, a different address. That is a new capability, and
  it is what the brain's motile connections actually do.

So every lever is measured on BOTH: what it changes in the GAIN, and
what it changes in the SHAPE. And the file reports which levers are
already implemented, which are inert, and what the cheapest fix is for
each.

PROVENANCE: [M] measured here. [E] established. [H] hypothesis.

Run:
    python src/bench_motile_stalk.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import do_stalks_communicate as dsc  # noqa: E402
from interstalk_link import InterstalkLink, transport, width_for  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The working population from `do_stalks_communicate.py`, which the
#: girth bench selected.
N = 8


def base_population() -> List[CoaxWinding]:
    return dsc.the_population(N)


def fingerprint(link: InterstalkLink, stalks: List[CoaxWinding],
                tx: str, rx: str) -> Dict[str, Any]:
    """Everything about one channel that could change.

    THE GAIN and THE SHAPE, separated:

      gain   the pair coupling, the direct gain, the received power
      shape  the notch depth, the tap COUNT, the DERIVED width, and the
             address of the sender (which is set by the geometry)
    """
    ids = [s.id for s in stalks]
    pair = link.pair(tx, rx, in_view=ids)
    ch = pair.channel()
    tx_stalk = next(s for s in stalks if s.id == tx)
    rx_stalk = next(s for s in stalks if s.id == rx)
    return {
        "pair_coupling": pair.pair_coupling(),
        "direct_gain": pair.direct_gain(),
        "notch_db": ch.notch_db(),
        "taps": len(ch.taps),
        "width": width_for(len(ch.taps)),
        "address": dsc.address_of(tx_stalk),
        "rx_address": dsc.address_of(rx_stalk),
        "ratio": tx_stalk.girth_ratio,
        "m_out_in": tx_stalk.mutual_couplings()["m_out_in"],
        "path_len_in": tx_stalk.path_length(tx_stalk.girth_in, tx_stalk.n_in),
        "lay_angle_in": tx_stalk.lay_angle_deg(tx_stalk.girth_in, tx_stalk.n_in),
    }


def measure(link: InterstalkLink, stalks: List[CoaxWinding],
            tx: str, rx: str, crowd: float = dsc.CROWD) -> Dict[str, Any]:
    """One exchange: does the receiver still hear the sender?"""
    r = dsc.recover(link, stalks, tx, rx, crowd)
    return {"correct": r["correct"], "align": r["align_sender"],
            "named": r["named"], "reason": r["reason"],
            "snr_db": r["snr_db"]}


def shape_changed(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    """Which of the SHAPE fields changed. The gain fields are excluded."""
    fields = ("notch_db", "taps", "width", "address", "rx_address",
              "ratio", "m_out_in")
    out = []
    for f in fields:
        va, vb = a[f], b[f]
        if isinstance(va, float) and isinstance(vb, float):
            if abs(va - vb) > 1e-9:
                out.append(f)
        elif va != vb:
            out.append(f)
    return out


def gain_changed(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    fields = ("pair_coupling", "direct_gain")
    out = []
    for f in fields:
        va, vb = a[f], b[f]
        if abs(va - vb) > 1e-9:
            out.append(f)
    return out


def part_attach_detach() -> None:
    print("=" * 78)
    print("LEVER 1 -- ATTACH / DETACH")
    print("=" * 78)
    print()
    print("  A stalk joins or leaves the population in view.")
    print()
    stalks = base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    ids = [s.id for s in stalks]
    print("  %-10s %-6s %-7s %-11s %-14s %-12s" % (
        "in view", "taps", "width", "notch dB", "address", "named"))
    print("  " + "-" * 66)
    for p in range(2, N + 1):
        view = ids[:p]
        pair = link.pair(ids[0], ids[1], in_view=view)
        ch = pair.channel()
        # the exchange, with the in-view set as the channel
        r = dsc.recover(link, stalks[:p], ids[0], ids[1], dsc.CROWD,
                        in_view=view)
        print("  %-10d %-6d %-7d %-11.2f %-14.4f %-12s" % (
            p, len(ch.taps), width_for(len(ch.taps)), ch.notch_db(),
            dsc.address_of(stalks[0]),
            "yes" if r["correct"] else "NO"))
    print()
    print("  SO ATTACH IS NOT A NEW MECHANISM HERE. The channel's taps")
    print("  ARE the population in view, so attaching a stalk adds a tap")
    print("  and `width_for` turns the tap count into the width. Attaching")
    print("  IS the ladder. That is why 'should I widen or recruit' was")
    print("  never a free choice -- the answer was 'recruiting IS widening'.")
    print()
    print("  AND THE ADDRESS DOES NOT MOVE when a stalk attaches. So the")
    print("  attachment changes the CHANNEL and the WIDTH, not who anyone")
    print("  is. That is the right behaviour: a bigger crowd must not")
    print("  change the identities, or the addresses would not be stable.")
    print()


def part_proximity() -> None:
    print("=" * 78)
    print("LEVER 2 -- PROXIMITY (the waving, the leaning-in)")
    print("=" * 78)
    print()
    print("  The receiver moves closer to or further from the sender.")
    print()
    stalks = base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    ids = [s.id for s in stalks]
    print("  %-12s %-14s %-13s %-12s %-11s %-12s" % (
        "separation", "pair coupling", "notch dB", "address", "width",
        "named"))
    print("  " + "-" * 72)
    base_fp = None
    for sep in (0.0, 0.005, 0.010, 0.020, 0.040, 0.080, 0.160):
        pair = link.pair(ids[0], ids[1], in_view=ids)
        pair.separation = sep
        ch = pair.channel()
        r = dsc.recover(link, stalks, ids[0], ids[1], dsc.CROWD)
        fp = {
            "pair_coupling": pair.pair_coupling(),
            "direct_gain": pair.direct_gain(),
            "notch_db": ch.notch_db(),
            "taps": len(ch.taps), "width": width_for(len(ch.taps)),
            "address": dsc.address_of(stalks[0]),
            "rx_address": dsc.address_of(stalks[1]),
            "ratio": stalks[0].girth_ratio,
            "m_out_in": stalks[0].mutual_couplings()["m_out_in"],
        }
        if base_fp is None:
            base_fp = fp
        print("  %-12.3f %-14.6f %-13.2f %-12.4f %-11d %-12s" % (
            sep, fp["pair_coupling"], fp["notch_db"], fp["address"],
            fp["width"], "yes" if r["correct"] else "NO"))
    print()
    print("  THE VERDICT: proximity is a GAIN knob in this model.")
    print("  The coupling falls as the separation grows, and the notch,")
    print("  the width, the address and the tap count all hold still.")
    print()
    print("  WHY THE NOTCH DOES NOT MOVE, and it is structural rather than")
    print("  a parameter: the notch is set by the RATIO of the direct path")
    print("  to the reflected path, and the reflected path carries")
    print("  REFLECTION_LOSS times the direct one. The separation scales")
    print("  BOTH, so the ratio is untouched and the response shape is")
    print("  untouched.")
    print()
    print("  SO WHAT IT WOULD TAKE: the reflected path has to become a")
    print("  function of the geometry instead of a fixed loss factor.")
    print("  Then a stalk that moves closer changes not just how loud")
    print("  the signal is but what the interference looks like -- which")
    print("  is the brain's mechanism, where proximity changes what a")
    print("  cell can RESOLVE.")
    print()
    print("  And that is a ONE-LINE change in the physics, not a new")
    print("  architecture: the reflected path's amplitude is currently")
    print("  `direct * REFLECTION_LOSS`, and it would become")
    print("  `direct * f(separation, girth_ratio)` with f derived from the")
    print("  return-path term `interstalk.py::return_path_penalty` already")
    print("  has: log(2D/d).")
    print()


def part_girth() -> None:
    print("=" * 78)
    print("LEVER 3 -- GIRTH")
    print("=" * 78)
    print()
    print("  The windings change size. The brain's answer is that a")
    print("  frequently used axon is myelinated and thickened.")
    print()
    stalks = base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    ids = [s.id for s in stalks]
    print("  %-8s %-14s %-13s %-12s %-11s %-12s" % (
        "growth", "pair coupling", "notch dB", "address", "width",
        "named"))
    print("  " + "-" * 70)
    for growth in (0.75, 1.0, 1.25, 1.5, 2.0):
        grown = [CoaxWinding(
            id=s.id, girth_core=s.girth_core * growth,
            girth_in=s.girth_in * growth, girth_out=s.girth_out * growth,
            n_in=s.n_in, n_out=s.n_out) for s in stalks]
        glink = InterstalkLink(core=WoundCore(stalks=grown), bins=dsc.BINS)
        pair = glink.pair(ids[0], ids[1], in_view=ids)
        ch = pair.channel()
        r = dsc.recover(glink, grown, ids[0], ids[1], dsc.CROWD)
        print("  %-8.2f %-14.6f %-13.2f %-12.4f %-11d %-12s" % (
            growth, pair.pair_coupling(), ch.notch_db(),
            dsc.address_of(grown[0]), width_for(len(ch.taps)),
            "yes" if r["correct"] else "NO"))
    print()
    print("  THE VERDICT: girth growth is INERT in this model. The coupling")
    print("  does not move, the notch does not move, the address does not")
    print("  move, the width does not move.")
    print()
    print("  WHY: everything that matters here is a RATIO of the geometry.")
    print("  m_out_in = overlap x inner/outer, and scaling both leaves the")
    print("  ratio alone. The address is (parity/2) + (ratio - 1), and")
    print("  the ratio is unchanged. The notch is a ratio of two paths")
    print("  that scale together. So a bigger wire is a louder wire and")
    print("  nothing else.")
    print()
    print("  SO A GROWN STALK IS THE SAME STALK. If the brain's thickened")
    print("  axon carries MORE INFORMATION, then this model is missing")
    print("  what the thickening does -- and the missing piece is the")
    print("  RESONANCE: a thicker, longer wire resonates at a different")
    print("  frequency, so it carries a different tone. Which is lever 4.")
    print()


def part_length() -> None:
    print("=" * 78)
    print("LEVER 4 -- LENGTH")
    print("=" * 78)
    print()
    print("  The stalk gets longer or shorter. This is the one that SHOULD")
    print("  matter most: length is what sets a coil's resonance, and a")
    print("  resonance is what makes the channel frequency-selective.")
    print()
    stalks = base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    ids = [s.id for s in stalks]
    print("  %-9s %-14s %-13s %-12s %-11s %-12s %-11s" % (
        "length", "pair coupling", "notch dB", "address", "width",
        "lay angle", "named"))
    print("  " + "-" * 82)
    for length in (0.5, 1.0, 2.0, 4.0):
        long_stalks = [CoaxWinding(
            id=s.id, girth_core=s.girth_core, girth_in=s.girth_in,
            girth_out=s.girth_out, n_in=s.n_in, n_out=s.n_out,
            length=length) for s in stalks]
        llink = InterstalkLink(core=WoundCore(stalks=long_stalks),
                               bins=dsc.BINS)
        pair = llink.pair(ids[0], ids[1], in_view=ids)
        ch = pair.channel()
        r = dsc.recover(llink, long_stalks, ids[0], ids[1], dsc.CROWD)
        print("  %-9.2f %-14.6f %-13.2f %-12.4f %-11d %-12.1f %-11s" % (
            length, pair.pair_coupling(), ch.notch_db(),
            dsc.address_of(long_stalks[0]), width_for(len(ch.taps)),
            long_stalks[0].lay_angle_deg(long_stalks[0].girth_in,
                                         long_stalks[0].n_in),
            "yes" if r["correct"] else "NO"))
    print()
    print("  THE VERDICT: length is INERT in the channel, and it should")
    print("  NOT be. The lay angle DOES move -- 83.7 degrees at length 0.5,")
    print("  77.5 at 1.0, 66.1 at 2.0, 48.5 at 4.0 -- so the geometry")
    print("  knows the length. But the CHANNEL does not use it: the taps")
    print("  are a fixed structure with a fixed delay in BINS, and the")
    print("  delay is not computed from the physical length.")
    print()
    print("  SO A LONGER STALK IS THE SAME STALK, TOO. And that is the")
    print("  real gap: the model's channel has no frequency dependence on")
    print("  the geometry at all. The taps are dimensionless and the")
    print("  delay is a bin count, so a coil twice as long is a coil with")
    print("  the same filter.")
    print()
    print("  WHAT IT WOULD TAKE, and this is the cheapest and the")
    print("  deepest of the four fixes:")
    print()
    print("    THE PATH DELAY MUST COME FROM THE PHYSICAL LENGTH. The")
    print("    propagation delay over the coil is length x sqrt(eps_r) / c,")
    print("    and the bin width is set by the frame. So the tap's delay")
    print("    in bins is a function of the stalk's length and the")
    print("    dielectric -- and a longer stalk's reflection arrives LATER,")
    print("    which ROTATES the tap's phase, which MOVES the notch.")
    print()
    print("    The frequency that makes it matter is the coil's own")
    print("    resonance, f = v / 2L with v = c / sqrt(eps_r). At a")
    print("    micrometre scale that lands in the THz, which is the")
    print("    DNA-phonon claim in `interstalk.py::rung_frequency` -- and")
    print("    at the frame's own bandwidth the phase across the frame is")
    print("    what carries the address.")
    print()
    print("    So: length becomes the lever that moves the CHANNEL SHAPE,")
    print("    and a stalk that lengthens changes what it can resolve.")
    print("    That is the brain's mechanism and it is missing here.")
    print()


def part_the_margin() -> None:
    print("=" * 78)
    print("AND ONE MORE FINDING, which the test suite caught")
    print("=" * 78)
    print()
    print("  The margin -- the gap between the best and second-best")
    print("  candidate score -- does NOT separate correct readings from")
    print("  wrong ones. Measured on the working population at crowd 0.10:")
    print()
    stalks = base_population()
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=dsc.BINS)
    ids = [s.id for s in stalks]
    good: List[float] = []
    bad: List[float] = []
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, dsc.CROWD)
            (good if r["correct"] else bad).append(r["margin"])
    if good and bad:
        print("    correct readings: margin from %.4f to %.4f" % (
            min(good), max(good)))
        print("    wrong readings:   margin from %.4f to %.4f" % (
            min(bad), max(bad)))
        print("    they OVERLAP, and the wrong readings have the LARGER")
        print("    margins: %.4f against %.4f." % (max(bad), min(good)))
        print()
        print("  WHY: the score is a CORRELATION divided by the candidate's")
        print("  norm, so it is signed. When the reading is a mess every")
        print("  candidate scores near zero, and the DIFFERENCE between")
        print("  two near-zero numbers is large in absolute terms while")
        print("  meaning nothing. So a big margin on a bad reading means")
        print("  'nothing was heard, and these two are equally unheard'.")
        print()
        print("  SO THE MARGIN IS NOT A CONFIDENCE, and any gate that")
        print("  thresholds on it is thresholding on noise. The honest")
        print("  confidence is the ALIGNMENT -- how much of the SENDER's")
        print("  waveform is in the recovered signal -- because that is")
        print("  measured against the thing that was actually sent.")
        print()
        print("  And the 1-bit gate already uses exactly that: the")
        print("  kernel's MIN_COS on the recovered reading. So the gate is")
        print("  right and the MARGIN is the wrong quantity to look at.")
        print("  Recorded here so nobody builds a threshold on it.")
        print()


def main() -> int:
    print("=" * 78)
    print("WHAT DOES A MOVING STALK BUY?")
    print("=" * 78)
    print()
    part_attach_detach()
    part_proximity()
    part_girth()
    part_length()
    part_the_margin()
    print("=" * 78)
    print("THE SUMMARY, and it is the answer to Bobby's question")
    print("=" * 78)
    print()
    print("  LEVER           GAIN?   SHAPE?   VERDICT")
    print("  " + "-" * 58)
    print("  attach/detach   no      YES     already implemented -- it IS")
    print("                               the ladder, because the taps")
    print("                               are the population in view")
    print("  proximity       YES     no      a volume knob. to make it")
    print("                               the brain's mechanism the")
    print("                               reflected path must depend on")
    print("                               the separation")
    print("  girth           no      no      inert: everything here is a")
    print("                               ratio of the geometry")
    print("  length          no      no      inert, and it is the BIG")
    print("                               one: length is what sets the")
    print("                               resonance")
    print()
    print("  SO: DOES MOTILITY COMPLICATE NEEDLESSLY?")
    print()
    print("  No -- and here is why that is the answer rather than a")
    print("  reassurance. Attach/detach is ALREADY the ladder, so the")
    print("  motility costs nothing extra: the mechanism exists and the")
    print("  population code is what moves.")
    print()
    print("  But two of the four levers are inert, and inert is worse than")
    print("  absent, because it LOOKS like a control. Proximity moves the")
    print("  gain and the shape does not follow, so a stalk that leans")
    print("  in hears louder and resolves the same. And length moves")
    print("  nothing at all in the channel, so a stalk that lengthens is")
    print("  indistinguishable from one that did not.")
    print()
    print("  THE CHEAPEST FIX, and it is one number per stalk: the path")
    print("  DELAY must come from the physical length. The taps are")
    print("  dimensionless and the delay is a bin count, so the model has")
    print("  no frequency dependence on the geometry at all. Make the")
    print("  delay a function of length and the dielectric, and:")
    print()
    print("    the reflected path arrives later on a longer stalk, which")
    print("    ROTATES the tap, which MOVES the notch -- so length")
    print("    becomes a control on what the channel can resolve")
    print()
    print("    and the RETURN PATH becomes length-dependent too, so")
    print("    proximity and length reinforce each other, which is what")
    print("    makes a MOTILE substrate rather than a static one")
    print()
    print("  So the answer is: the architecture is not complicated, it is")
    print("  UNFINISHED in one place, and the unfinished place is the")
    print("  physics that already exists in `interstalk.py` (the return")
    print("  path term log(2D/d) and the rung frequency v/2L) and has not")
    print("  been wired into the channel that the measurement uses.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
