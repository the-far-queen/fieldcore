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

**AND ON 2026-11-05 BOTH THE POPULATION AND THE CONTROL WERE FIXED,
AND THE ANSWER CHANGED.** Two defects, both measured:

  * THE POPULATION. Seven files carried their own copy of the
    population recipe and the copies had DIVERGED. Three of them
    clustered the addresses within thousandths, so population 8 gave 2
    DFT classes for 8 stalks -- and that was published as the
    population code's "real ceiling". The repo's own
    `bench_tradeoff.py` had already called the clustered recipe a
    CONFOUND: "it was asking the receiver to separate things no
    transform could separate, and then reporting that as a limit of
    the design."  The recipe now lives in ONE place,
    `stalk_population.py`, and every stalk is in its own class.

  * THE CONTROL. The false transmission used to pick the NEXT INDEX as
    its false candidate, whose difficulty depends on the recipe -- on
    the clustered recipe that was a parity flip, half the circle
    away, so the false transmission was trivially rejected. The
    adversarial candidate is the one whose ADDRESS is NEAREST the
    speaker's, and that is what this file now uses.

WITH BOTH FIXED, MEASURED: the alignment gate ADMITS the nearest
neighbour at population 8 and above -- 0.569506 at population 8 and
0.943521 at population 64, against MIN_COS = 0.4.  So the gate does
NOT keep the truth counterweight against its hardest case.

THE CAUSE, MEASURED: the frame is a tone of frequency ph/n cycles per
sample, so its DFT peak sits at index ph -- and ph is in [0,1).  EVERY
ADDRESS LANDS IN THE FIRST DFT BIN, and the other bins carry the
frame's skirt, not the address.  So the bins do not separate
addresses, and the separation the gate needs does not shrink with
more bins: 0.184445 of the circle at 32 bins, 0.180562 at 256.

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
     transmission, where the ADVERSARIAL candidate's address is sent: the
     one nearest the speaker's. A gate that admits the false
     transmission has lost its counterweight. This
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

#: THE POPULATION AND THE ADDRESS.
#:
#: MEASURED 2026-11-05: this file used to carry its OWN copy of the
#: population recipe, and so did six others.  The copies had DIVERGED
#: into two behaviours -- one clustered the addresses within
#: thousandths, so the population collapsed into two DFT classes at
#: population 8, while the other spread them evenly.
#:
#: The repo already called the clustered one a CONFOUND, in
#: `bench_tradeoff.py`: "it was asking the receiver to separate things
#: no transform could separate, and then reporting that as a limit of
#: the design."
#:
#: The recipe now lives in ONE place, `stalk_population.py`, and every
#: bench imports it.  `tools/check_population_recipe.py` checks that
#: they all do.
import stalk_population as SP  # noqa: E402
from stalk_population import address_of, make_population  # noqa: E402,F401

# ===========================================================================
# THE POPULATION AND THE ADDRESSES
# ===========================================================================


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


def _address_separation(addrs: Dict[str, float], a: str, b: str) -> float:
    """How far apart two addresses are on the unit circle.

    The circle wraps, so the separation is the SHORT way round.
    """
    d = abs(addrs[a] - addrs[b])
    return min(d, 1.0 - d)


def _nearest_by_address(addrs: Dict[str, float], tx: str,
                        ids: List[str]) -> str:
    """The candidate whose ADDRESS is nearest the speaker's.

    THIS IS THE ADVERSARIAL FALSE CANDIDATE, and it is the control the
    false transmission must use.  The previous control picked the next
    INDEX, whose difficulty depends on the recipe: on the old
    clustered recipe that was a parity flip (half the circle away, so
    trivially rejected) and on the canonical recipe it is 1/n of the
    circle away (the hardest case).  A control whose difficulty is a
    property of the generator measures the generator.

    MEASURED 2026-11-05, the separations this picks:
        clustered recipe, population 8 : 0.002498 = 0.16 bins
        canonical recipe, population 8 : 0.125000 = 8.00 bins

    So the clustered recipe's neighbours are UNRESOLVABLE BY
    CONSTRUCTION -- their frames are the same frame -- while the
    canonical recipe's are as far apart as n addresses on a circle can
    be.
    """
    cands = [c for c in ids if c != tx]
    if not cands:
        return tx
    return min(cands, key=lambda c: _address_separation(addrs, tx, c))


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
    false_seps: List[float] = []

    for n, i in enumerate(picks):
        tx, rx = ids[i], ids[(i + 1) % population]
        sent_spec = spectrum(address_frame(addrs[tx], bins))

        # -- the FALSE transmission: the ADVERSARIAL candidate ----------
        #
        # MEASURED 2026-11-05.  The false candidate used to be the
        # NEXT INDEX:
        #
        #     other = ids[picks[(n + 1) % len(picks)]]
        #
        # which is a control whose difficulty depends on the recipe.
        # On the old clustered recipe the next index was a PARITY FLIP
        # -- half the circle away -- so the false transmission was
        # trivially rejected and the gate looked perfect.  On the
        # canonical recipe the next index is 1/n of the circle away --
        # the hardest case -- and the gate looked broken.  Neither was
        # the control.
        #
        # THE ADVERSARIAL FALSE CANDIDATE IS THE ONE WHOSE ADDRESS IS
        # NEAREST THE SPEAKER'S.  That is the hardest case whatever the
        # recipe is, so the number it produces is a property of the
        # DESIGN and not of the generator.
        other = _nearest_by_address(addrs, tx, ids)
        false_sep = _address_separation(addrs, tx, other)
        false_seps.append(false_sep)

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
        # THE CONTROL'S DIFFICULTY, in address units and in bins.  A
        # reader must be able to see how hard the false transmission
        # was: a control whose difficulty is a property of the recipe
        # measures the recipe.
        "false_separation": min(false_seps) if false_seps else 0.0,
        "false_separation_bins": (min(false_seps) * bins
                                  if false_seps else 0.0),
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
        print("     the false candidate is the ADVERSARIAL one: nearest "
              "address,")
        print("     %.6f of the circle = %.2f bins away"
              % (r["false_separation"], r["false_separation_bins"]))
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
    # AND THE THRESHOLD, which is the question the gate actually asks.
    # The ranges can separate while the THRESHOLD admits the false
    # transmission -- and with the adversarial control they do.
    admit_rows = [r for r in rows
                  if int(r["align_gate_false"]) > 0]  # type: ignore[arg-type]
    if admit_rows:
        print("     BUT THE RANGES SEPARATE WHILE THE THRESHOLD DOES NOT.")
        print("     MEASURED, the alignment gate ADMITS the false")
        print("     transmission at %d of %d populations:"
              % (len(admit_rows), len(rows)))
        for r in admit_rows:
            print("        population %3d bins %3d : %d of %d false "
                  "transmissions admitted, worst alignment %.6f, the "
                  "false candidate %.2f bins away"
                  % (r["population"], r["bins"], r["align_gate_false"],
                     r["trials"], max(r["false_alignment"]),  # type: ignore[arg-type]
                     r["false_separation_bins"]))
        print()
        print("     THE CAUSE, MEASURED: the frame is a tone of frequency")
        print("     ph/n cycles per sample, so its DFT peak sits at index")
        print("     ph -- and ph is in [0,1).  EVERY ADDRESS LANDS IN THE")
        print("     FIRST DFT BIN, and the other bins carry the frame's")
        print("     skirt, not the address.  So two nearby addresses have")
        print("     overlapping frames, and widening the channel adds bins")
        print("     that do not separate addresses.")
    else:
        print("     and the threshold refuses the false transmission at")
        print("     every measured population.")
    print()

    # 3. what the margin actually is
    print("  3. WHAT THE MARGIN ACTUALLY IS.")
    same_rows = [r for r in rows if r["true_margin_same_class"]]
    if same_rows:
        worst_same = min(min(r["true_margin_same_class"])      # type: ignore[arg-type]
                         for r in same_rows)                   # type: ignore[arg-type]
        worst_diff = min(min(r["true_margin_other_class"])    # type: ignore[arg-type]
                         for r in rows if r["true_margin_other_class"])  # type: ignore[arg-type]
        print("     MEASURED, the margin over a class-mate is as small as")
        print("     %.6e, and the margin over another class is as small as"
              % worst_same)
        print("     %.6e -- a factor of %.3g between them."
              % (worst_diff, (worst_diff / worst_same) if worst_same else 0.0))
        print("     So the margin is NOT a confidence measure that grows with")
        print("     the crowd's strength: it is a REPORT OF THE ADDRESS")
        print("     CLASSES. The runner-up is either a class-mate (the margin")
        print("     is negligible) or it is not (the margin is enormous).")
    else:
        # MEASURED 2026-11-05: on the canonical recipe there are NO
        # class-mates -- every stalk is in its own class -- so the
        # class-mate margin does not exist and the old comparison could
        # not be made.  The first version of this report called
        # min() on the empty list and raised ValueError.
        print("     MEASURED, there is NO CLASS-MATE at any measured")
        print("     population: the canonical recipe puts every stalk in its")
        print("     own class, so the margin over a class-mate does not")
        print("     exist and cannot be compared against the margin over")
        print("     another class.")
        print()
        print("     THAT IS THE POINT OF THE CANONICAL RECIPE. The old")
        print("     recipe collapsed the population into two classes, and")
        print("     the margin-over-a-class-mate comparison -- and the")
        print("     'the population code's real ceiling' built on it --")
        print("     was measuring that collapse, not the design.")
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
    print("     'measures the winner' -- is FALSE.")
    print()
    if admit_rows:
        print("     AND THE CONSTANT DOES NEED TO MOVE, or rather the")
        print("     THRESHOLD IS NOT THE PROBLEM. MEASURED, the false")
        print("     transmission's alignment reaches %.6f while the true"
              % max(max(r["false_alignment"])  # type: ignore[arg-type]
                    for r in admit_rows))
        print("     one is 1.000000, so a threshold ABOVE %.6f would refuse"
              % max(max(r["false_alignment"])   # type: ignore[arg-type]
                    for r in admit_rows))
        print("     it -- but the cross-talk RISES as the population grows")
        print("     (the neighbours get closer), so no fixed threshold")
        print("     separates them at every population.  The threshold is")
        print("     not what is wrong; the FRAME is.  Every address lands")
        print("     in DFT bin 0, so the bins do not separate addresses and")
        print("     widening the channel cannot help.")
    else:
        print("     AND THE CONSTANT DOES NOT NEED TO MOVE: the gate")
        print("     refuses the false transmission at every measured")
        print("     population.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
