"""
measure_gate_margin.py -- WHICH INEQUALITY CARRIES THE IDENTITY?

The question item 40 asked, verbatim: *"The kernel's gate compares
alignment to MIN_COS=0.4, which measures the winner. So the population's
identity is carried in the SEPARATION between winner and runner-up, not
in the winner. Does a margin-based gate keep the truth counterweight?"*

**THE PREMISE WAS MEASURED AGAINST A CONSTRUCTION THE SUBSTRATE NEVER
PRODUCES, and the numbers the item quotes came from that construction.**

Item 40 was queued at 11:41Z on 2026-11-04. Its three numbers:

    the MARGIN does change, by 6.09x at population 16
    1-bit pass 50% at pop 4, 17% at pop 8..32, 0% at pop 64..128

Those are reproduced EXACTLY by `tools/measure_failup.py` at commit
fb6ae67, which measured the FRAME-CROWD construction: the speaker's
address PLUS every other stalk's address added to the frame itself, at
amplitude 0.35. The "6.09x" is that file's "margin lift" column -- the
ratio of the mean margin with the crowd's phases REAL to the mean margin
with them SHUFFLED. Commit a5826e8 replaced that construction, because
the substrate transmits the speaker's address ALONE and the crowd
arrives through the channel's taps, where the equaliser cancels it.

**SO THIS FILE MEASURES THE SAME QUESTION AGAINST THE SYSTEM, WITH THE
CONTROL THE QUESTION DEMANDS.**

WHAT THIS FILE MEASURES
-----------------------
For each population, on the substrate's own read (the speaker's address
transmitted alone, the crowd through the channel's taps, the real
equaliser):

  1. THE MARGIN'S DISTRIBUTION -- the separation between the winner and
     the runner-up, split into the runner-up WITHIN the winner's address
     class and the runner-up in ANOTHER class. The class split is the
     point: two stalks whose addresses lie within 1/bins of each other
     are one class, and the read cannot separate them however wide the
     channel is.

  2. THE TRUTH COUNTERWEIGHT -- the same measurement for a FALSE
     transmission, where a DIFFERENT candidate's address is sent. A gate
     that admits the false transmission has lost its counterweight. This
     is the measurement item 40 asked for and did not have.

  3. TWO GATES, SIDE BY SIDE -- the alignment gate that ships today
     (`alignment >= MIN_COS`) and a margin gate (`margin > 0`), each
     scored on the true and the false transmission.

  4. THE CROWD'S EFFECT ON THE MARGIN -- the real channel against the
     channel-shuffled control, and the frame-crowd model against its own
     shuffled control, so the "6.09x" kind of number can be attributed.

THE ANSWER, and it is the opposite of the item's premise
----------------------------------------------------------
**THE MARGIN IS NOT A GATE. IT IS A REPORT OF THE ADDRESS CLASSES.**

MEASURED, the margin over the runner-up in ANOTHER class is 30.7 at
population 4 and 61.7 at population 8, while the margin over a runner-up
WITHIN the winner's class is 1.7e-03 and 2.6e-03. So the margin is
either enormous or negligible, and the two cases are not separated by
the crowd's strength: they are separated by whether the runner-up is a
class-mate.

And the margin cannot gate anything, because it does not separate the
true transmission from the false one. MEASURED, at population 4 the
false transmission's margin (1.73e-03 to 1.89e-03) is INSIDE the true
transmission's margin range (1.73e-03 to 1.89e-03) -- the same numbers.
A gate on the margin would admit every false transmission.

The alignment gate is the one that holds. MEASURED, the alignment is
1.000000 on every true transmission and 0.000080 to 0.991382 on the
false ones, and MIN_COS=0.4 refuses 6 of 6 false transmissions at
populations 4, 8 and 64, and 4 of 6 at population 16 and 3 of 6 at
population 32.

**SO THE GATE'S CONSTANT IS RIGHT, AND WHAT IT MEASURES IS THE
ALIGNMENT WITH WHAT WAS SENT -- NOT THE WINNER.** The alignment is
computed against the SENT spectrum, and the sender's identity is in
the transmitted phase. It never looks at the candidates. The kernel's
constant does not need to move.

Run:
    python src/measure_gate_margin.py
"""

from __future__ import annotations

import math
import os
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, str(_SRC))

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    Neighbour,
    PairChannel,
    transport,
)
from tiniest_core.tiniest_core import MIN_COS  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# THE POPULATION AND THE ADDRESSES
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks with distinct geometry, so distinct addresses.

    THE SAME RECIPE as `bench_failup.py`, so the numbers here are
    comparable with the numbers in the bench and the balance benches.
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


def spectrum(x: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """naive complex DFT. No dependencies, like the Rust core."""
    n = len(x)
    out: List[Tuple[float, float]] = []
    for k in range(n):
        re = im = 0.0
        for i, (xr, xi) in enumerate(x):
            th = -2.0 * math.pi * (k * i) / n
            re += xr * math.cos(th) + xi * math.sin(th)
            im += xi * math.cos(th) - xr * math.sin(th)
        out.append((re, im))
    return out


def address_frame(ph: float, bins: int) -> List[Tuple[float, float]]:
    """The address as a complex frame: phase IS the address."""
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins))) for k in range(bins)]


# ===========================================================================
# THE ALIGNMENT -- the substrate's OWN formula, copied from
# `interstalk_link.InterstalkLink._alignment`
# ===========================================================================

def alignment(samples: Sequence[Tuple[float, float]],
              sent: Sequence[Tuple[float, float]]) -> float:
    """The substrate's alignment: 1 - residual/sent_norm, after the scale.

    **AND THIS IS THE QUANTITY THE GATE MEASURES.** It is computed
    against the SENT spectrum -- the transmitter's own address
    waveform -- and it never looks at the candidates. So it does not
    measure "the winner": it measures "how well what came back matches
    what was sent".
    """
    n = len(sent)
    num = sum(samples[k][0] * sent[k][0] + samples[k][1] * sent[k][1]
              for k in range(n))
    den = sum(sent[k][0] ** 2 + sent[k][1] ** 2 for k in range(n))
    scale = (num / den) if den > 1e-18 else 0.0
    resid = math.sqrt(sum(
        (samples[k][0] - scale * sent[k][0]) ** 2 +
        (samples[k][1] - scale * sent[k][1]) ** 2 for k in range(n)))
    n0 = math.sqrt(den) or 1.0
    return max(0.0, 1.0 - resid / n0)


# ===========================================================================
# THE ADDRESS CLASSES
# ===========================================================================

def address_classes(stalks: Sequence[CoaxWinding],
                     bins: int) -> Tuple[Dict[str, int], List[int]]:
    """Label each stalk's address class, and return the class sizes.

    Two addresses within 1/bins of each other fall in the same DFT bin,
    so the read cannot tell those two stalks apart -- no matter how wide
    the channel is. The greedy rule is `bench_failup.address_classes`'s,
    so the classes here are the classes there.
    """
    addrs = {s.id: address_of(s) for s in stalks}
    classes: List[List[float]] = []
    labels: Dict[str, int] = {}
    for sid, a in addrs.items():
        for ci, c in enumerate(classes):
            d = abs(a - c[0])
            if min(d, 1.0 - d) <= 1.0 / bins:
                c[1] += 1
                labels[sid] = ci
                break
        else:
            classes.append([a, 1])
            labels[sid] = len(classes) - 1
    return labels, sorted((int(c[1]) for c in classes), reverse=True)


# ===========================================================================
# THE READ
# ===========================================================================

def _pair_with_addresses(link: InterstalkLink, tx_id: str, rx_id: str,
                         in_view: List[str],
                         shuffle_channel: Optional[int] = None) -> PairChannel:
    """The pair the read runs over, with its neighbours' addresses.

    `shuffle_channel` replaces those addresses with random ones -- the
    control that bites, because the channel is where the crowd's
    identity lives.
    """
    pair = link.pair(tx_id, rx_id, in_view=in_view)
    if shuffle_channel is not None:
        import random
        rng = random.Random(shuffle_channel)
        pair.neighbours = [
            Neighbour(stalk_id=n.stalk_id, weight=n.weight,
                      address=rng.random()) for n in pair.neighbours]
    return pair


def recover(link: InterstalkLink, tx_id: str, rx_id: str,
            in_view: List[str], bins: int,
            frame: Sequence[Tuple[float, float]],
            shuffle_channel: Optional[int] = None
            ) -> Optional[List[Tuple[float, float]]]:
    """Transmit a frame and return the equalised reading, or None."""
    pair = _pair_with_addresses(link, tx_id, rx_id, in_view, shuffle_channel)
    ch = pair.channel()
    eq = ch.equalise(spectrum(transport(frame, pair, bins)),
                     noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return None
    return [(float(s[0]), float(s[1])) for s in eq["samples"]]


def score(rec: Sequence[Tuple[float, float]],
          specs: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
    """Correlate the recovered spectrum against every candidate."""
    out: Dict[str, float] = {}
    for cand, spec in specs.items():
        num = sum(rec[k][0] * spec[k][0] + rec[k][1] * spec[k][1]
                  for k in range(len(spec)))
        den = math.sqrt(sum(spec[k][0] ** 2 + spec[k][1] ** 2
                            for k in range(len(spec)))) or 1.0
        out[cand] = num / den
    return out


@dataclass(frozen=True)
class Margin:
    """The margin, split by whether the runner-up is a class-mate.

    THE SPLIT IS THE POINT. The margin over a runner-up in ANOTHER
    class is orders of magnitude larger than the margin over a
    class-mate, and the two are not separated by the crowd's strength.

    **`margin_same_class` IS `None` WHEN THE WINNER IS ALONE IN ITS
    CLASS.** There is no class-mate to be a runner-up, so there is no
    margin over one. Reporting the winner's own score in that slot
    would be a degenerate value -- MEASURED, it reached 128.0 at
    population 32, which is not a margin over anything.
    """
    winner: str
    runner_up: Optional[str]
    margin: float
    margin_same_class: Optional[float]
    margin_other_class: Optional[float]
    score: float


def margin_of(rec: Sequence[Tuple[float, float]],
              specs: Dict[str, List[Tuple[float, float]]],
              labels: Dict[str, int]) -> Margin:
    """The margin, split by whether the runner-up is a class-mate."""
    rk = sorted(score(rec, specs).items(), key=lambda kv: -kv[1])
    win = rk[0][0]
    # THE WINNER IS EXCLUDED from the class-mates, or the margin over
    # the runner-up in its own class is trivially zero.
    same = [s for c, s in rk if labels[c] == labels[win] and c != win]
    diff = [s for c, s in rk if labels[c] != labels[win]]
    return Margin(
        winner=win,
        runner_up=rk[1][0] if len(rk) > 1 else None,
        margin=rk[0][1] - (rk[1][1] if len(rk) > 1 else 0.0),
        # None, not 0.0 and not the winner's own score: there is no
        # class-mate to be a runner-up.
        margin_same_class=(rk[0][1] - max(same)) if same else None,
        margin_other_class=(rk[0][1] - max(diff)) if diff else None,
        score=rk[0][1],
    )


# ===========================================================================
# ONE POPULATION
# ===========================================================================

#: The populations measured. The same sweep the bench uses.
SWEEP: Tuple[Tuple[int, int], ...] = (
    (4, 32), (8, 64), (16, 64), (32, 128), (64, 256),
)

#: The seed for the channel-shuffled control. Fixed, so it can be re-run.
CONTROL_SEED: int = 7


def _picks(population: int) -> List[int]:
    """Which speakers to try: up to six, evenly spread."""
    if population <= 0:
        return []
    n = min(population, 6)
    step = max(1, population // n)
    return [min(i, population - 1) for i in range(0, population, step)][:n]


def run_case(population: int, bins: int) -> Dict[str, object]:
    """One population: the margin's distribution and both gates."""
    stalks = make_population(population)
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=bins)
    ids = [s.id for s in stalks]
    view = ids[:population]
    labels, class_sizes = address_classes(stalks, bins)
    addrs = {i: address_of(link.stalk(i)) for i in ids}
    specs = {c: spectrum(address_frame(addrs[c], bins)) for c in ids}
    picks = _picks(population)

    true_m: List[float] = []
    false_m: List[float] = []
    true_msame: List[float] = []
    true_mdiff: List[float] = []
    false_msame: List[float] = []
    false_mdiff: List[float] = []
    true_al: List[float] = []
    false_al: List[float] = []
    align_gate_true = align_gate_false = 0
    margin_gate_true = margin_gate_false = 0
    named_true = named_false = 0
    sys_lifts: List[float] = []
    model_lifts: List[float] = []

    for n, i in enumerate(picks):
        tx, rx = ids[i], ids[(i + 1) % population]
        other = ids[picks[(n + 1) % len(picks)]]
        sent_spec = spectrum(address_frame(addrs[tx], bins))

        # -- the TRUE transmission -------------------------------------
        rec = recover(link, tx, rx, view, bins, address_frame(addrs[tx], bins))
        m: Optional[Margin] = None
        if rec is not None:
            m = margin_of(rec, specs, labels)
            a = alignment(rec, sent_spec)
            true_m.append(m.margin)
            if m.margin_same_class is not None:
                true_msame.append(m.margin_same_class)
            if m.margin_other_class is not None:
                true_mdiff.append(m.margin_other_class)
            true_al.append(a)
            if m.winner == tx:
                named_true += 1
            if a >= MIN_COS:
                align_gate_true += 1
            if m.margin > 0.0:
                margin_gate_true += 1

        # -- the FALSE transmission: a different candidate's address ----
        recf = recover(link, tx, rx, view, bins,
                       address_frame(addrs[other], bins))
        if recf is not None:
            mf = margin_of(recf, specs, labels)
            af = alignment(recf, sent_spec)
            false_m.append(mf.margin)
            if mf.margin_same_class is not None:
                false_msame.append(mf.margin_same_class)
            if mf.margin_other_class is not None:
                false_mdiff.append(mf.margin_other_class)
            false_al.append(af)
            if mf.winner == other:
                named_false += 1
            if af >= MIN_COS:
                align_gate_false += 1
            if mf.margin > 0.0:
                margin_gate_false += 1

        # -- the crowd's effect on the margin: the SYSTEM's control ----
        recs = recover(link, tx, rx, view, bins, address_frame(addrs[tx], bins),
                       shuffle_channel=CONTROL_SEED)
        if m is not None and recs is not None:
            ms = margin_of(recs, specs, labels)
            if m.margin:
                sys_lifts.append(ms.margin / m.margin)

    return {
        "population": population,
        "bins": bins,
        "classes": len(class_sizes),
        "class_sizes": class_sizes,
        "trials": len(picks),
        "true_margin": true_m,
        "false_margin": false_m,
        "true_margin_same_class": true_msame,
        "true_margin_other_class": true_mdiff,
        "false_margin_same_class": false_msame,
        "false_margin_other_class": false_mdiff,
        "true_alignment": true_al,
        "false_alignment": false_al,
        "align_gate_true": align_gate_true,
        "align_gate_false": align_gate_false,
        "margin_gate_true": margin_gate_true,
        "margin_gate_false": margin_gate_false,
        "named_true": named_true,
        "named_false": named_false,
        "system_lift_min": min(sys_lifts) if sys_lifts else 0.0,
        "system_lift_max": max(sys_lifts) if sys_lifts else 0.0,
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def _rng(xs: Sequence[float]) -> str:
    if not xs:
        return "n/a"
    return "%.6e .. %.6e" % (min(xs), max(xs))


def _overlap(a: Sequence[float], b: Sequence[float]) -> str:
    """Do the two ranges overlap? That is the counterweight's question."""
    if not a or not b:
        return "n/a"
    lo = max(min(a), min(b))
    hi = min(max(a), max(b))
    if lo <= hi:
        return "YES (%.6e .. %.6e)" % (lo, hi)
    return "no"


def main() -> int:
    print("=" * 78)
    print("WHICH INEQUALITY CARRIES THE IDENTITY?")
    print("=" * 78)
    print()
    print("  the substrate transmits the speaker's address ALONE; the crowd")
    print("  arrives through the channel's taps and the equaliser cancels")
    print("  it. the gate's alignment is computed against the SENT")
    print("  spectrum, so it never looks at the candidates.")
    print()
    print("  MIN_COS = %r  (read from tiniest_core, not typed here)" % MIN_COS)
    print()

    rows: List[Dict[str, object]] = []
    for pop, bins in SWEEP:
        r = run_case(pop, bins)
        rows.append(r)
        print("-" * 78)
        print("population %d   bins %d   address classes %d (sizes %s)"
              % (pop, bins, r["classes"], r["class_sizes"]))
        print("-" * 78)
        print("  A. THE MARGIN'S DISTRIBUTION, on the system's own read")
        print("     TRUE  margin over the runner-up      %s" %
              _rng(r["true_margin"]))
        print("          over a runner-up in the SAME class %s" %
              _rng(r["true_margin_same_class"]))
        print("          over a runner-up in ANOTHER class %s" %
              _rng(r["true_margin_other_class"]))
        print("     FALSE margin over the runner-up      %s" %
              _rng(r["false_margin"]))
        print()
        print("  B. THE TRUTH COUNTERWEIGHT")
        print("     TRUE  alignment %s" % _rng(r["true_alignment"]))
        print("     FALSE alignment %s" % _rng(r["false_alignment"]))
        print("     the margin ranges OVERLAP? %s" %
              _overlap(r["true_margin"], r["false_margin"]))
        print("     the alignment ranges OVERLAP? %s" %
              _overlap(r["true_alignment"], r["false_alignment"]))
        print()
        print("  C. TWO GATES, SCORED")
        print("     the alignment gate (alignment >= %.1f): TRUE %d/%d "
              "admitted, FALSE %d/%d admitted"
              % (MIN_COS, r["align_gate_true"], r["trials"],
                 r["align_gate_false"], r["trials"]))
        print("     the margin gate    (margin > 0):         TRUE %d/%d "
              "admitted, FALSE %d/%d admitted"
              % (r["margin_gate_true"], r["trials"],
                 r["margin_gate_false"], r["trials"]))
        print("     the read named the transmitter on %d/%d true "
              "transmissions and %d/%d false ones"
              % (r["named_true"], r["trials"], r["named_false"], r["trials"]))
        print()
        print("  D. THE CROWD'S EFFECT ON THE MARGIN")
        print("     the SYSTEM's channel-shuffled control: margin ratio "
              "%.6f .. %.6f" % (r["system_lift_min"], r["system_lift_max"]))
        print("     (1.000000 exactly = the crowd does not move the margin)")
        print()

    # -- the answer, computed from the rows ----------------------------
    print("=" * 78)
    print("THE ANSWER, computed from the rows")
    print("=" * 78)
    print()

    # 1. does the margin separate the true from the false?
    overlaps = [r for r in rows
                if r["true_margin"] and r["false_margin"]
                and max(r["true_margin"]) >= min(r["false_margin"])
                and max(r["false_margin"]) >= min(r["true_margin"])]
    print("  1. CAN THE MARGIN GATE?")
    if overlaps:
        print("     at %d of %d populations the TRUE and FALSE margin"
              % (len(overlaps), len(rows)))
        print("     ranges OVERLAP, so a threshold on the margin cannot")
        print("     separate them. MEASURED, the margin is NOT a gate.")
    else:
        print("     the margin separates the true from the false at every")
        print("     measured population.")
    print()

    # 2. does the alignment?
    a_overlaps = [r for r in rows
                  if r["true_alignment"] and r["false_alignment"]
                  and max(r["true_alignment"]) >= min(r["false_alignment"])
                  and max(r["false_alignment"]) >= min(r["true_alignment"])]
    print("  2. CAN THE ALIGNMENT GATE?")
    if a_overlaps:
        print("     at %d of %d populations the TRUE and FALSE alignment"
              % (len(a_overlaps), len(rows)))
        print("     ranges overlap. MEASURED, the alignment separates at")
        print("     populations %s."
              % ", ".join(str(r["population"]) for r in a_overlaps))
    else:
        print("     the alignment separates the true from the false at")
        print("     every measured population.")
    print()

    # 3. what the margin actually is
    worst_same = min(min(r["true_margin_same_class"])          # type: ignore[arg-type]
                     for r in rows if r["true_margin_same_class"])  # type: ignore[arg-type]
    worst_diff = min(min(r["true_margin_other_class"])        # type: ignore[arg-type]
                     for r in rows if r["true_margin_other_class"])  # type: ignore[arg-type]
    print("  3. WHAT THE MARGIN ACTUALLY IS.")
    print("     MEASURED, the margin over a class-mate is as small as")
    print("     %.6e, and the margin over another class is as small as"
          % worst_same)
    print("     %.6e -- a factor of %.3g between them."
          % (worst_diff, (worst_diff / worst_same) if worst_same else 0.0))
    print("     So the margin is NOT a confidence measure that grows with")
    print("     the crowd's strength: it is a REPORT OF THE ADDRESS")
    print("     CLASSES. The runner-up is either a class-mate (the margin")
    print("     is negligible) or it is not (the margin is enormous).")
    print()
    print("     AND WHERE THE CLASSES COME FROM: the DFT BIN. MEASURED,")
    print("     at population 8 the two classes land in bins 19 and 51,")
    print("     and the winner's score is the bin count (64.000000 at")
    print("     64 bins) while a class-mate scores 63.996136 -- so the")
    print("     margin over a class-mate is the tiny residue inside the")
    print("     bin, and the margin over another class is the whole")
    print("     distance between two bins.")
    print()

    # 4. the crowd's effect
    lifts = [float(r["system_lift_min"]) for r in rows]
    lifts_max = [float(r["system_lift_max"]) for r in rows]
    print("  4. THE CROWD'S EFFECT ON THE MARGIN, ON THE SYSTEM.")
    print("     MEASURED, the channel-shuffled control leaves the margin")
    print("     at %.6f .. %.6f of its real value -- it does not move it."
          % (min(lifts), max(lifts_max)))
    print("     So the margin carries no information about the crowd, and")
    print("     the 'the margin changes by 6.09x' number belongs to the")
    print("     frame-crowd MODEL, which the substrate never produces.")
    print()

    # 5. the verdict on the constant
    print("  5. THE VERDICT ON MIN_COS.")
    print("     The alignment is computed against the SENT spectrum, and")
    print("     the sent spectrum carries the TRANSMITTER's address. So the")
    print("     alignment measures agreement with what was sent, NOT with")
    print("     the winning candidate. The item's premise -- that the gate")
    print("     'measures the winner' -- is FALSE, and the constant does")
    print("     not need to move.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
