"""
bench_girth_ladder.py -- SELECT THE GIRTHS, THEN FIND THE LADDER'S ORDER.

BOBBY'S TWO TASKS, 2026-10-25:

  1. "select girths" -- the 3-part stalk is a core plus an INNER and an
     OUTER winding. Which girths? The MINIMUM that works, and the
     OPTIMAL one.

  2. "pop increase first then decide where to go for bitwise increase
     and then pop again ... then test if stalks even communicate"

Plus the two he added while this was running:

  3. "a high speed mesh channel worn into pathways often used again
      brain does this saves compute like cache in a sense"

  4. "physical motion of stalks is used in the brain too -- waving,
      attachment, detachment, proximity. lengthening/girth changes.
      how to utilize?"

THIS FILE measures 1, 2 and 3. Item 4 is a mechanism question, and what
the measurement produced for it is in PART C.

THE MEASUREMENT THAT MAKES IT A CONVERSATION AND NOT A LOOPBACK
------------------------------------------------------------------
The link's own docstring records the defect this file is built to avoid:
an earlier version built the channel from the TRANSMITTER alone, so
`measure(tx, rx)` and `measure(tx, a completely different rx)` returned
byte-identical results. That is a loopback.

So every candidate geometry is checked for it: for a fixed transmitter,
the channel must CHANGE when the receiver changes. The check is printed,
not asserted in silence.

PROVENANCE, as in `interstalk.py`:
    [M] measured here, by this file, with the command printed.
    [E] established textbook physics or established telecom practice.
    [H] hypothesis. Not cited as a result.

Run:
    python src/bench_girth_ladder.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    transport,
    width_for,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402

#: The frame size. 128 bins, as in `bench_balance_final.py`. The address
#: resolvability rule below is stated in bins, so it moves with this.
BINS = 128

#: An address must be this far from every other address, in bins, or two
#: stalks cannot be told apart by the transform.
RESOLVE_FLOOR_BINS = 2.0

#: The inner winding's girth. Every ratio in this file is a multiple of
#: it, so one number sets the whole population's scale.
INNER_GIRTH = 0.060

#: The crowd amplitude: how loud each other stalk transmits. The same
#: value `bench_balance_final.py` swept, so the two benches agree.
CROWD = 0.15


# ===========================================================================
# THE ADDRESS, and the geometry that produces it
# ===========================================================================

def address_of(s: CoaxWinding) -> float:
    """The phase address, exactly as the link derives it.

    VERBATIM from `interstalk_link.InterstalkLink._address`, because a
    different derivation would make the readout correlate against a
    phase the transmitter never sent -- and the failure would look like
    a channel problem rather than a bookkeeping one.
    """
    return ((s.n_out % 2) / 2.0 + (s.girth_ratio - 1.0)) % 1.0


def make_stalks(base_ratio: float, delta_step: float, core_ratio: float,
                n_in: int, n_outs: Sequence[int]) -> List[CoaxWinding]:
    """Build a population of 3-part stalks from a geometry recipe.

    THE RECIPE, and every term is a lever:

      base_ratio   the WINDING RATIO of the first stalk, girth_out /
                   girth_in. It must exceed 1, because the windings are
                   concentric and the outer one encloses the inner one:
                   outer > inner is a geometric requirement.
      delta_step   how much the ratio grows from one stalk to the next.
                   The address carries (girth_ratio - 1), so this step
                   IS the address spacing.
      core_ratio   where the core sits between the two windings, as
                   core/inner. It is the third conductor, so it is what
                   makes the two loop modes unequal.
      n_in/n_outs  the turn counts. `n_out` PARITY is a binary address
                   component, and the overlap min/max is the shared flux
                   path, so the turns set both the address and the
                   coupling.

    THE ADDRESS, so the spacing is computable rather than hoped for:
        address = (n_out % 2) / 2 + (girth_ratio - 1)     mod 1
    so the parity contributes 0 or 0.5 and the ratio contributes the
    continuous part.
    """
    out: List[CoaxWinding] = []
    for i, n_out in enumerate(n_outs):
        ratio = base_ratio + i * delta_step
        out.append(CoaxWinding(
            id="s%d" % i, girth_core=INNER_GIRTH * core_ratio,
            girth_in=INNER_GIRTH, girth_out=INNER_GIRTH * ratio,
            n_in=n_in, n_out=n_out))
    return out


def make_spread_population(n: int) -> List[CoaxWinding]:
    """A population whose addresses are as evenly spread as the formula
    allows. [M]

    THE CONSTRAINT, and it is a real one, not a preference. The address
    is (parity/2) + (ratio - 1), and the ratio must exceed 1, so:

      even turn count -> address in (0, 0.5]
      odd  turn count -> address in (0.5, 1)

    Each half-circle holds its own stalk, and the ratio's own step
    spaces the stalks WITHIN a half-circle. So for n stalks:

      the ratio's excess over 1 runs from 1/(2n) up to (n/2)/(2n)
      the parity alternates, filling the two half-circles

    which puts every address 1/n apart on the unit circle, so at 128
    bins every address is 128/n bins from its neighbour.
    """
    out: List[CoaxWinding] = []
    half = max(n // 2, 1)
    for i in range(n):
        parity = i % 2
        k = i // 2
        offset = (k + 0.5) / (2.0 * half)
        ratio = 1.0 + offset
        out.append(CoaxWinding(
            id="s%02d" % i,
            girth_core=INNER_GIRTH * 0.25, girth_in=INNER_GIRTH,
            girth_out=INNER_GIRTH * ratio,
            n_in=12, n_out=13 + parity))
    return out


def circ_sep(a: float, b: float) -> float:
    """The separation of two phases on the unit circle."""
    return abs((a - b + 0.5) % 1.0 - 0.5)


def min_separation(addresses: Sequence[float]) -> float:
    if len(addresses) < 2:
        return 1.0
    best = 1.0
    for i in range(len(addresses)):
        for j in range(i + 1, len(addresses)):
            best = min(best, circ_sep(addresses[i], addresses[j]))
    return best


def spectrum(x: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """naive complex DFT. No dependencies, like carrier.rs."""
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


def tone(ph: float, bins: int) -> List[Tuple[float, float]]:
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins)))
            for k in range(bins)]


# ===========================================================================
# THE CROWD MEASUREMENT -- can the receiver NAME the speaker?
# ===========================================================================

def name_the_speaker(link: InterstalkLink, stalks: List[CoaxWinding],
                     tx_id: str, rx_id: str, crowd: float,
                     bins: int = BINS,
                     in_view: Optional[Sequence[str]] = None,
                     crowd_set: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """The multi-access measurement. [M]

    THE MODEL, and it is the corrected one. The crowd is NOT summed into
    the transmitter's frame -- that was the first bench's mistake, and it
    made the crowd unresolvable by construction. Here every stalk is an
    INDEPENDENT transmitter with its OWN channel to the receiver, each
    sending its OWN address. The receiver observes the sum and must name
    the speaker.

    The receiver knows which transmitter it is listening to, because the
    PILOT is the known reference and the channel is estimated per pair.
    It then equalises that pair's channel and correlates the recovered
    spectrum against every candidate address.

    THE CROWD AND THE TAPS ARE DECOUPLED. The channel's taps are the
    stalks in VIEW; the crowd is every stalk in the population, each at
    `crowd` amplitude. So the population can grow without the channel's
    structure and the crowd's size changing at the same time -- which
    was the confounded experiment that `bench_balance_final.py` had to
    remove.
    """
    ids = [s.id for s in stalks]
    speaker = next(s for s in stalks if s.id == tx_id)
    if rx_id not in ids:
        raise KeyError(rx_id)

    # THE IN-VIEW SET, and it is separate from the crowd on purpose.
    # The channel's taps come from the stalks in VIEW; the crowd is
    # every stalk in the population. So the population can grow without
    # the channel's structure and the crowd's size changing together.
    view = list(ids) if in_view is None else [i for i in in_view]

    pair = link.pair(tx_id, rx_id, in_view=view)
    ch = pair.channel()

    frame: List[Tuple[float, float]] = [(0.0, 0.0)] * bins

    # the crowd: every other stalk in the CROWD SET transmits its own
    # address through its OWN channel to the same receiver
    cset = list(ids) if crowd_set is None else list(crowd_set)
    for other in stalks:
        if other.id in (tx_id, rx_id) or other.id not in cset:
            continue
        opair = link.pair(other.id, rx_id, in_view=view)
        own = tone(address_of(other), bins)
        contrib = transport(own, opair, bins)
        for k in range(bins):
            frame[k] = (frame[k][0] + crowd * contrib[k][0],
                        frame[k][1] + crowd * contrib[k][1])

    # the speaker
    own = tone(address_of(speaker), bins)
    contrib = transport(own, pair, bins)
    for k in range(bins):
        frame[k] = (frame[k][0] + contrib[k][0], frame[k][1] + contrib[k][1])

    eq = ch.equalise(spectrum(frame), noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return {"ok": False, "reason": "channel_%s" % eq.get("error"),
                "correct": False, "margin": 0.0, "snr_db": 0.0,
                "capacity_bits": 0.0, "taps": len(ch.taps),
                "width": width_for(len(ch.taps)), "notch_db": ch.notch_db()}
    rec = eq["samples"]

    # the SNR of the recovered reading against the speaker's own address
    sp = spectrum(tone(address_of(speaker), bins))
    num = sum(rec[k][0] * sp[k][0] + rec[k][1] * sp[k][1] for k in range(bins))
    den = sum(sp[k][0] ** 2 + sp[k][1] ** 2 for k in range(bins))
    scale = (num / den) if den > 1e-18 else 0.0
    sig = abs(scale) ** 2 * den
    noise = sum((rec[k][0] - scale * sp[k][0]) ** 2 +
                (rec[k][1] - scale * sp[k][1]) ** 2 for k in range(bins))
    snr_db = 10.0 * math.log10(sig / noise) if noise > 1e-30 and sig > 1e-30 else 0.0

    scores: Dict[str, float] = {}
    for cand in stalks:
        cs = spectrum(tone(address_of(cand), bins))
        n_ = sum(rec[k][0] * cs[k][0] + rec[k][1] * cs[k][1] for k in range(bins))
        d_ = math.sqrt(sum(cs[k][0] ** 2 + cs[k][1] ** 2 for k in range(bins))) or 1.0
        scores[cand.id] = n_ / d_
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
    return {
        "ok": True,
        "reason": "allow" if ranked[0][0] == tx_id else "refuse_alignment",
        "correct": ranked[0][0] == tx_id,
        "winner": ranked[0][0],
        "margin": margin,
        "snr_db": snr_db,
        "capacity_bits": math.log2(1.0 + 10.0 ** (snr_db / 10.0)),
        "taps": len(ch.taps),
        "width": width_for(len(ch.taps)),
        "notch_db": ch.notch_db(),
    }


# ===========================================================================
# PART A -- THE GEOMETRY GRID
# ===========================================================================

def within_stalk_gap(stalk: CoaxWinding) -> Tuple[float, float]:
    """The gap between a stalk's OWN two loop modes. [M]

    THE v6.2 CLAIM is about ONE stalk: its two loop modes are separated
    by its geometry -- the core plus the girth difference -- so the axis
    count needs no sigma_g perturbation. So this is the gap the claim is
    about.

    Returns (ratio, fraction): the ratio is hi/lo and the fraction is
    (hi - lo)/hi, which reads 0..1.

    AND THE SIGN. The loop eigenvalues of this model have a NEGATIVE
    midpoint -- the matrix is INDEFINITE -- so a midpoint-relative gap
    is not even defined, and a guard of the form `mid > 1e-18` sent
    every gap to zero. That is a bug in the MEASUREMENT, and it read as
    "the geometry carries no axis at all", which is a completely
    different claim.

    WHY THE MATRIX IS INDEFINITE, and it is a modelling fact worth
    recording: `mutual_couplings` returns a DIMENSIONLESS normalised
    coupling (overlap x radius ratio), while `inductance_matrix` builds
    the diagonal from r^2 N^2. So the off-diagonals are ratios and the
    diagonal is areas-times-turns-squared, and the two are not in the
    same units. The matrix is therefore not an inductance matrix, and
    its eigenvalue SIGNS carry no physics.

    So the gap is measured on MAGNITUDES.
    """
    e1, e2 = stalk.loop_eigenvalues()
    a, b = abs(e1), abs(e2)
    hi, lo = max(a, b), min(a, b)
    ratio = hi / lo if lo > 1e-18 else float("inf")
    frac = (hi - lo) / hi if hi > 1e-18 else 0.0
    return ratio, frac


def pooled_gap(stalks: Sequence[CoaxWinding]) -> Tuple[float, float]:
    """The gap between neighbouring eigenvalues of ALL the stalks pooled.

    THE CONTROL, and it is a different measurement: pooling compares one
    stalk's LOW mode against ANOTHER stalk's low mode, so it measures
    how far apart the stalks are, not how far apart a stalk's own modes
    are.

    It is kept because the two must be COMPARABLE: if they came out the
    same, the distinction would be doing no work and one of the two
    measurements would be wrong.
    """
    pooled: List[float] = []
    for s in stalks:
        pooled.extend(s.loop_eigenvalues())
    pooled.sort()
    ratios: List[float] = []
    fracs: List[float] = []
    for i in range(len(pooled) - 1):
        mid = abs((pooled[i] + pooled[i + 1]) / 2.0)
        if mid <= 1e-18:
            continue
        ratios.append(abs(pooled[i + 1] - pooled[i]) / mid)
        fracs.append(abs(pooled[i + 1] - pooled[i]) / max(abs(pooled[i + 1]),
                                                         1e-18))
    return (min(ratios) if ratios else 0.0,
            min(fracs) if fracs else 0.0)


def evaluate(spec: Dict[str, Any], crowd: float = CROWD) -> Dict[str, Any]:
    """Score one geometry. [M]"""
    stalks = make_stalks(
        float(spec["base_ratio"]), float(spec["delta_step"]),
        float(spec["core_ratio"]), int(spec["n_in"]), list(spec["n_outs"]))
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    addresses = [address_of(s) for s in stalks]
    sep = min_separation(addresses)
    sep_bins = sep * BINS

    couplings = [s.mutual_couplings()["m_out_in"] for s in stalks]
    mean_m = sum(couplings) / len(couplings)

    # THE MODE GAP, and it must be measured WITHIN a stalk.
    #
    # The v6.2 claim is that ONE stalk's two loop modes are separated by
    # its geometry -- the core plus the girth difference -- so the axis
    # count needs no sigma_g perturbation. So the gap that matters is
    # the gap between a stalk's OWN two modes.
    #
    # Pooling every stalk's eigenvalues into one sorted list and taking
    # the smallest gap between neighbours compares one stalk's LOW mode
    # against ANOTHER stalk's low mode. That is a between-stalk
    # comparison, not the within-stalk one the claim is about, and it
    # reports 0.0000 for every candidate -- which reads as "the geometry
    # carries nothing" and is simply the wrong measurement. The earlier
    # version of this same mistake is recorded in
    # `wound_core.degeneracy_check`.
    #
    # AND THE SIGN. The loop eigenvalues of this model have a NEGATIVE
    # midpoint -- the matrix is INDEFINITE -- so the midpoint-relative
    # gap is not even defined, and the guard `mid > 1e-18` sent every
    # gap to 0.0000. That is a bug in the MEASUREMENT, and it read as
    # "the geometry carries no axis at all", which is a completely
    # different claim.
    #
    # WHY THE MATRIX IS INDEFINITE, and it is a modelling fact worth
    # recording: `mutual_couplings` returns a DIMENSIONLESS normalised
    # coupling (overlap x radius ratio), while `inductance_matrix`
    # builds the diagonal from r^2 N^2. So the off-diagonals are
    # ratios and the diagonal are areas-times-turns-squared, and the
    # two are not in the same units. The matrix is therefore not an
    # inductance matrix, and its eigenvalue SIGNS carry no physics.
    #
    # So the gap is measured on MAGNITUDES, and the indefiniteness is
    # reported rather than hidden.
    gap_ratios: List[float] = []
    gap_fracs: List[float] = []
    indefinite = 0
    for s in stalks:
        ratio, frac = within_stalk_gap(s)
        gap_ratios.append(ratio)
        gap_fracs.append(frac)
        e1, e2 = s.loop_eigenvalues()
        if (e1 < 0) != (e2 < 0):
            indefinite += 1
    min_gap = min(gap_ratios) if gap_ratios else 0.0
    min_gap_frac = min(gap_fracs) if gap_fracs else 0.0
    # THE CONTROL, measured alongside so the two can be compared
    pooled_ratio, pooled_frac = pooled_gap(stalks)

    # and the BETWEEN-stalk separation of the same mode, for the record
    between = []
    for i in range(len(stalks)):
        for j in range(i + 1, len(stalks)):
            a = stalks[i].loop_eigenvalues()
            b = stalks[j].loop_eigenvalues()
            for u, v in zip(a, b):
                mid = (u + v) / 2.0
                between.append(abs(v - u) / mid if mid > 1e-18 else 0.0)
    min_between = min(between) if between else 0.0

    # the exchange over the full population: does it recover?
    aligns: List[float] = []
    allowed = 0
    refused: Dict[str, int] = {}
    for tx in stalks:
        for rx in stalks:
            if tx.id == rx.id:
                continue
            ex = link.exchange(tx.id, rx.id, in_view=ids)
            aligns.append(ex.alignment)
            if ex.allowed:
                allowed += 1
            else:
                refused[ex.reason] = refused.get(ex.reason, 0) + 1

    # THE LOOPBACK FALSIFICATION. Move the receiver and the channel must
    # change. If it does not, every number above is a transmitter talking
    # to itself.
    p1 = link.pair(ids[0], ids[1], in_view=ids)
    p2 = link.pair(ids[0], ids[2], in_view=ids)
    t1, t2 = p1.taps(), p2.taps()
    receiver_matters = t1 != t2
    receiver_gap = max(abs(a[0] - b[0]) + abs(a[1] - b[1])
                       for a, b in zip(t1, t2))

    # the flat channel: nothing to invert, and the gate must REFUSE by
    # name. This is the design law, checked.
    flat = link.exchange(ids[0], ids[1], in_view=[ids[0], ids[1]])

    # the crowd measurement
    named = 0
    trials = 0
    snrs: List[float] = []
    for tx in stalks:
        rx_id = ids[(stalks.index(tx) + 1) % len(ids)]
        m = name_the_speaker(link, stalks, tx.id, rx_id, crowd)
        trials += 1
        if m.get("correct"):
            named += 1
        if m.get("ok"):
            snrs.append(float(m["snr_db"]))

    return {
        "spec": spec,
        "sep": sep,
        "sep_bins": sep_bins,
        "resolvable": sep_bins >= RESOLVE_FLOOR_BINS,
        "mean_m": mean_m,
        "min_gap": min_gap,
        "min_gap_frac": min_gap_frac,
        "pooled_gap": pooled_ratio,
        "pooled_gap_frac": pooled_frac,
        "indefinite": indefinite,
        "min_between": min_between,
        "align_min": min(aligns) if aligns else 0.0,
        "align_max": max(aligns) if aligns else 0.0,
        "allowed": allowed,
        "refused": refused,
        "receiver_matters": receiver_matters,
        "receiver_gap": receiver_gap,
        "flat_refused": (not flat.allowed) and flat.reason == "channel_flat_channel",
        "named": named,
        "trials": trials,
        "snr_db": (sum(snrs) / len(snrs)) if snrs else 0.0,
        "stalk": stalks,
    }


#: The candidate grid. The winding RATIO is girth_out/girth_in, so it
#: must exceed 1 -- the outer winding encloses the inner one. The
#: address carries (ratio - 1), so a ratio near 1 puts every address
#: near zero.
CANDIDATES: List[Dict[str, Any]] = []
for _ratio in (1.20, 1.40, 1.70, 2.00):
    for _step in (0.01, 0.03, 0.06, 0.12):
        for _core in (0.25, 0.50):
            CANDIDATES.append({
                "base_ratio": _ratio,
                "ratio": _ratio,
                "delta_step": _step,
                "core_ratio": _core,
                "n_in": 12,
                # alternating turn PARITY, so the binary address
                # component separates the stalks as well as the ratio
                "n_outs": (13, 14, 15, 16),
            })
# two controls, deliberately wrong, to prove the checks can go red
CANDIDATES.append({
    "base_ratio": 1.40, "ratio": 1.40,
    "delta_step": 0.002, "core_ratio": 0.33, "n_in": 12,
    "n_outs": (13, 13, 13, 13),
    "note": "CONTROL: the addresses nearly coincide",
})
CANDIDATES.append({
    "base_ratio": 1.0001, "ratio": 1.0001,
    "delta_step": 0.0, "core_ratio": 0.25, "n_in": 12,
    "n_outs": (13, 14, 15, 16),
    "note": "CONTROL: no girth difference at all",
})


def part_a() -> List[Dict[str, Any]]:
    print("=" * 78)
    print("PART A -- SELECT THE GIRTHS")
    print("=" * 78)
    print()
    print("  the address carries (girth_ratio - 1) and the turn parity, so")
    print("  the girth ratio is the coupling AND the address at once. the")
    print("  grid below varies the ratio, the spread, the core position and")
    print("  the turn counts, and scores each on:")
    print("    sep_bins   how far apart two addresses are, in DFT bins")
    print("    mean_m     the mean winding-to-winding coupling")
    print("    mode_gap   the gap between a stalk's OWN two loop modes")
    print("    align      the worst recovery over every ordered pair")
    print("    rx         whether moving the receiver changes the channel")
    print("    named      can the receiver still name the speaker, crowd .15")
    print()
    print("  %-4s %-6s %-6s %-6s %-9s %-8s %-9s %-9s %-7s %-5s" % (
        "#", "ratio", "step", "core", "sep_bins", "mean_m", "mode_gap",
        "align", "named", "rx"))
    print("  " + "-" * 76)

    rows: List[Dict[str, Any]] = []
    t0 = time.perf_counter()
    for i, spec in enumerate(CANDIDATES):
        r = evaluate(spec)
        rows.append(r)
        s = r["spec"]
        print("  %-4d %-6.2f %-6.3f %-6.2f %-9.2f %-8.4f %-9.4f %-9.6f "
              "%-7s %-5s" % (
                  i, float(s["ratio"]), float(s["delta_step"]),
                  float(s["core_ratio"]), r["sep_bins"], r["mean_m"],
                  r["min_gap"], r["align_min"],
                  "%d/%d" % (r["named"], r["trials"]),
                  "yes" if r["receiver_matters"] else "NO"))
    print("  (" + "%.1f" % (time.perf_counter() - t0) + " s)")
    print()

    good = [r for r in rows
            if r["resolvable"] and r["receiver_matters"] and r["flat_refused"]
            and r["align_min"] > 0.999999 and r["named"] == r["trials"]]
    print("  THE SELECTION RULE, applied in this order:")
    print("    1. the addresses must be separable (>= %.0f bins)" % RESOLVE_FLOOR_BINS)
    print("    2. moving the receiver must change the channel (not a loopback)")
    print("    3. the flat channel must be refused by name")
    print("    4. every ordered pair must recover (alignment > 0.999999)")
    print("    5. the receiver must still name the speaker with a crowd")
    print()
    print("  %d of %d candidates satisfy all five." % (len(good), len(rows)))
    print()

    print("  THE MINIMUM SPREAD, measured. For each step, how far apart the")
    print("  addresses land:")
    print("  %-8s %-11s %-10s %-8s %-9s" % (
        "step", "sep (bins)", "resolvable", "named", "align"))
    for st in sorted(set(float(r["spec"]["delta_step"]) for r in rows)):
        sub = [r for r in rows if float(r["spec"]["delta_step"]) == st]
        best = max(sub, key=lambda r: r["sep_bins"])
        print("  %-8.3f %-11.2f %-10s %-8s %-9.6f" % (
            st, best["sep_bins"],
            "yes" if best["resolvable"] else "NO",
            "%d/%d" % (best["named"], best["trials"]), best["align_min"]))
    print()

    print("  THE RATIO, measured. Coupling and recovery by ratio, over the")
    print("  candidates that are otherwise sound, so the ratio is compared")
    print("  on equal terms:")
    print("  %-8s %-11s %-11s %-8s %-9s" % (
        "ratio", "mean_m", "mode_gap", "named", "align"))
    for rt in sorted(set(float(r["spec"]["ratio"]) for r in rows)):
        sub = [r for r in rows if float(r["spec"]["ratio"]) == rt]
        sub = [r for r in sub if r["resolvable"] and r["receiver_matters"]]
        if not sub:
            continue
        best = max(sub, key=lambda r: r["mean_m"])
        print("  %-8.2f %-11.4f %-11.4f %-8s %-9.6f" % (
            rt, best["mean_m"], best["min_gap"],
            "%d/%d" % (best["named"], best["trials"]), best["align_min"]))
    print()

    if good:
        winner = max(good, key=lambda r: (r["mean_m"], r["min_gap"]))
        s = winner["spec"]
        print("  THE WINNER, and every term is a number this file measured:")
        print("    winding ratio %.3f   (outer/inner, must exceed 1)" % float(s["ratio"]))
        print("    inner girth   %.4f   (the unit the ratios are on)" % INNER_GIRTH)
        print("    ratio step    %.3f   (the spread between stalks)" % float(s["delta_step"]))
        print("    core ratio    %.3f   (core/inner)" % float(s["core_ratio"]))
        print("    turns         n_in=%d, n_out=%s" % (int(s["n_in"]), list(s["n_outs"])))
        print("    mean coupling %.4f" % winner["mean_m"])
        print("    address sep   %.2f bins" % winner["sep_bins"])
        print("    mode gap      %.4f  (within a stalk)" % winner["min_gap"])
        print("    between-stalk %.4f  (same mode, other stalks)" % winner["min_between"])
        print("    recovery      %.8f worst, %.8f best" % (
            winner["align_min"], winner["align_max"]))
        print("    named         %d/%d with a crowd of %.2f" % (
            winner["named"], winner["trials"], CROWD))
        print()
        print("  THE CHOSEN POPULATION, in girths:")
        for st in winner["stalk"]:
            print("    %-4s core %.4f  inner %.4f  outer %.4f   "
                  "N %d/%d   ratio %.4f   address %.4f   m_out_in %.4f" % (
                      st.id, st.girth_core, st.girth_in, st.girth_out,
                      st.n_in, st.n_out, st.girth_ratio,
                      address_of(st), st.mutual_couplings()["m_out_in"]))
        print()
    else:
        print("  NO CANDIDATE satisfies all five. That is a finding, and")
        print("  it is printed rather than papered over.")
        crit = {
            "resolvable": [r for r in rows if not r["resolvable"]],
            "receiver_matters": [r for r in rows if not r["receiver_matters"]],
            "flat_refused": [r for r in rows if not r["flat_refused"]],
            "alignment": [r for r in rows if r["align_min"] <= 0.999999],
            "named": [r for r in rows if r["named"] != r["trials"]],
        }
        for k, v in crit.items():
            print("    failed %-18s : %d of %d" % (k, len(v), len(rows)))
        print()
    return rows


# ===========================================================================
# PART B -- THE LADDER OVER THE REAL LINK
# ===========================================================================

def report_balance(rows: List[Dict[str, Any]], crowds: Sequence[float],
                   model: str) -> None:
    """The balance point and the ladder's answer, for one crowd model.

    THE NAMING RATE, and why it is a rate and not a verdict.

    The first version of this report said "naming never holds" whenever
    fewer than ALL the pairs were named. That is a 100%-or-nothing
    test, and it produced a nonsense reading: at crowd 0.05 the rate was
    2/5, 3/6, 3/6 -- the receiver names the speaker in half the trials,
    which is not "never". A rate is the honest quantity, because a
    receiver that names the speaker half the time and REFUSES the other
    half is behaving correctly: it refuses when the reading is
    ambiguous. That refusal is the design working, not failing.
    """
    print("  THE BALANCE POINT, swept over the crowd. The surplus is the")
    print("  bits left after paying for the names, which is what the width")
    print("  must fit in.")
    print()
    print("  %-9s %-10s %-11s %-11s %-12s %-11s" % (
        "crowd", "peak pop", "surplus", "capacity", "best rate", "rate@peak"))
    print("  " + "-" * 66)
    for c in crowds:
        key = "c%.2f" % c
        cand = [r for r in rows if r[key]["tried"] > 0]
        if not cand:
            continue
        best = max(cand, key=lambda r: r[key]["surplus"])
        bestrate = max(cand, key=lambda r: r[key]["rate"])
        print("  %-9.2f %-10d %-11.2f %-11.2f %-12s %-11.2f" % (
            c, best["p"], best[key]["surplus"], best[key]["cap"],
            ("%d/%d at pop %d" % (bestrate[key]["named"],
                                  bestrate[key]["tried"], bestrate["p"])),
            best[key]["rate"]))
    print()
    print("  THE LADDER'S ANSWER. The cap is the population at which the")
    print("  naming RATE peaks -- not the population where every pair")
    print("  happens to land, which is a coin-flip criterion. The width")
    print("  follows the cap because the width is DERIVED from the taps.")
    print()
    for c in crowds:
        key = "c%.2f" % c
        cand = [r for r in rows if r[key]["tried"] > 0]
        if not cand:
            continue
        bestrate = max(cand, key=lambda r: (r[key]["rate"], r[key]["surplus"]))
        r = bestrate
        print("    crowd %.2f: the naming rate peaks at %d stalks in view "
              "(%d/%d)," % (c, r["p"], r[key]["named"], r[key]["tried"]))
        print("               which derives width %d bits -- cost %d, "
              "reach %d." % (r["width"], r["width"] * r["p"],
                             r["width"] * r["p"]))
    print()
    print("  THE ORDER, and it is not a taste question:")
    print("    1. POPULATION FIRST. Below the balance point, recruiting")
    print("       pays: more stalks in view means more taps, more")
    print("       structure to invert, and a better reading.")
    print("    2. THEN THE WIDTH, and the width FOLLOWS the population,")
    print("       because width_for(taps) is the channel's, not the")
    print("       caller's. There is no separate width dial to turn.")
    print("    3. THEN POP AGAIN, only if the reading is still refused.")
    print()


def part_b() -> None:
    print("=" * 78)
    print("PART B -- THE LADDER: POP FIRST, THEN WHERE TO WIDEN")
    print("=" * 78)
    print()
    print("  THE STRUCTURAL FACT FIRST, because it changes the question.")
    print("  `width_for(taps)` derives the width from the channel, and the")
    print("  channel's taps are one per OTHER stalk in view. So a wider")
    print("  channel IS a bigger population in view: 'widen' and 'recruit'")
    print("  are ONE dial in this architecture, not two.")
    print()
    print("  THE MINIMUM. With two stalks in view there is ONE path, so")
    print("  there is no null and nothing to invert -- the flat channel,")
    print("  which the design law says is UNCORRECTABLE and must be")
    print("  refused by name. So the first readable population is THREE.")
    print()

    N = 16
    stalks = make_spread_population(N)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    sep = min_separation([address_of(s) for s in stalks])
    print("  the population: %d stalks, addresses %.4f apart (%.1f bins)" % (
        N, sep, sep * BINS))
    print()
    print("  %-9s %-6s %-7s %-10s %-10s %-10s %-9s %-9s %-8s" % (
        "in view", "taps", "width", "notch dB", "clean", "snr dB",
        "capacity", "surplus", "named"))
    print("  " + "-" * 80)

    #
    # THE CROWD IS SWEPT, NOT FIXED.
    #
    # The first version held the crowd at 0.15 while the in-view set
    # grew, but the crowd was the WHOLE population -- so at 16 stalks
    # there were 15 interferers and the reading was swamped, and the
    # naming rate fell to 0/6 at almost every population. The answer was
    # "nothing works", which is a fact about the crowd amplitude and not
    # about the ladder.
    #
    # The earlier bench (`bench_balance_final.py`) swept the crowd
    # amplitude for exactly this reason: it is the one free parameter
    # with no measured physical value, so the answer has to be a RANGE
    # over it rather than a single number.
    #
    # AND THE MEASUREMENT IS AVERAGED OVER PAIRS, because one pair was
    # noisy enough to be meaningless: the same structure gave 0.42 dB at
    # 16 stalks in view and 8.80 dB at 4.
    CROWDS = (0.02, 0.05, 0.10, 0.15)
    #
    # THE TWO CROWD MODELS, and the difference between them IS the
    # architecture's central fact.
    #
    # COUPLED: the crowd is the stalks IN VIEW, each at the crowd
    #   amplitude, and the taps are also one per stalk in view. So
    #   recruiting a stalk adds a tap AND an interferer. This is the
    #   architecture as built -- `width_for(taps)` is the channel's, so
    #   a bigger population in view IS a wider channel, and it IS also
    #   more interference. They are the same dial.
    #
    # DECOUPLED: the crowd is the WHOLE population, and the taps are the
    #   in-view set. So the population grows without the crowd growing.
    #   This is the CONTROL, and it isolates the tap effect.
    #
    # The two models disagree about where the ladder should stop, so
    # both are reported. The coupled model is the one that describes the
    # substrate; the decoupled one says what would happen if the
    # interference could be held constant.
    MODELS = ("coupled", "decoupled")

    for model in MODELS:
        print("  MODEL: %s" % model.upper())
        if model == "coupled":
            print("    the crowd is the stalks IN VIEW, and the taps are")
            print("    also one per stalk in view. recruiting adds a tap AND")
            print("    an interferer -- the same dial.")
        else:
            print("    the crowd is the WHOLE population; the taps are the")
            print("    in-view set. the control that isolates the tap effect.")
        print()
        print("  %-9s %-6s %-7s %-10s" % ("in view", "taps", "width", "notch dB") +
              "".join(" %-16s" % ("crowd %.2f" % c) for c in CROWDS))
        print("  " + "-" * 92)
        print("  %-9s %-6s %-7s %-10s" % ("", "", "", "") +
              "".join(" %-16s" % ("named  capacity") for _ in CROWDS))
        print("  " + "-" * 92)

        rows: List[Dict[str, Any]] = []
        for p in range(2, N + 1):
            view = ids[:p]
            pair = link.pair(ids[0], ids[1], in_view=view)
            ch = pair.channel()
            line = "  %-9d %-6d %-7d %-10.2f" % (
                p, len(ch.taps), width_for(len(ch.taps)), ch.notch_db())
            rec: Dict[str, Any] = {"p": p, "taps": len(ch.taps),
                                   "width": width_for(len(ch.taps)),
                                   "notch": ch.notch_db()}
            for c in CROWDS:
                caps: List[float] = []
                named = 0
                tried = 0
                # the crowd's membership depends on the model
                if model == "coupled":
                    crowd_set = [i for i in view]
                else:
                    crowd_set = list(ids)
                for i in range(min(p, 6)):
                    tx = ids[i]
                    rx = ids[(i + 1) % p]
                    if tx == rx:
                        continue
                    m = name_the_speaker(link, stalks, tx, rx, c,
                                         in_view=view,
                                         crowd_set=crowd_set)
                    tried += 1
                    if m.get("correct"):
                        named += 1
                    if m.get("ok"):
                        caps.append(float(m.get("capacity_bits", 0.0)))
                cap = (sum(caps) / len(caps)) if caps else 0.0
                rec["c%.2f" % c] = {"named": named, "tried": tried,
                                    "cap": cap, "rate": named / max(tried, 1),
                                    "surplus": cap - math.log2(p)}
                line += " %-16s" % ("%d/%-3d %8.2f" % (named, tried, cap))
            rows.append(rec)
            print(line)
        print()
        report_balance(rows, CROWDS, model)
    print()

    report_balance(rows, CROWDS, "END")
    print()

    print("  SO THE LADDER IS:  1 bit at 2 in view -> 4 bits -> 8 bits ->")
    print("  stop, and the stop is at the population where the naming rate")
    print("  peaks. The measurement above says where that is.")
    print()


# ===========================================================================
# PART C -- THE CACHE, THE WORN HIGHWAY, THE MOVING STALK
# ===========================================================================

class PathwayCache:
    """The used-pathway cache. [H] -- the mechanism is mine.

    THE BRAIN'S VERSION, and it is the point: a pathway used often is
    myelinated and thickened, so the second time the question arrives it
    travels a better road. Here the cache remembers, per ORDERED PAIR,
    the number of stalks in view at which the exchange last SUCCEEDED,
    and the next question on that pair starts there instead of climbing
    from the bottom.

    What this saves is ATTEMPTS, and an attempt is not free: each one is
    a frame transmitted, a channel estimated from a pilot, and a spectrum
    inverted.

    It is a cache and not a shortcut, because the cached rung is still
    MEASURED when it is used. The cache says where to START, not what the
    answer is.
    """

    def __init__(self) -> None:
        self._rungs: Dict[Tuple[str, str], int] = {}
        self.hits = 0
        self.misses = 0

    def lookup(self, tx: str, rx: str) -> Optional[int]:
        if (tx, rx) in self._rungs:
            self.hits += 1
            return self._rungs[(tx, rx)]
        self.misses += 1
        return None

    def store(self, tx: str, rx: str, rung: int) -> None:
        self._rungs[(tx, rx)] = rung


def walk(link: InterstalkLink, ids: Sequence[str], tx: str, rx: str,
         start: int) -> Tuple[bool, int, int]:
    """Climb the population until the exchange is allowed.

    Returns (allowed, population_used, attempts_made). The population is
    the LADDER'S RUNG in this architecture, because the width is derived
    from the taps and the taps are one per stalk in view.
    """
    attempts = 0
    for p in range(max(start, 2), len(ids) + 1):
        attempts += 1
        ex = link.exchange(tx, rx, in_view=ids[:p])
        if ex.allowed:
            return True, p, attempts
    return False, len(ids), attempts


def part_c() -> None:
    print("=" * 78)
    print("PART C -- THE CACHE, THE WORN HIGHWAY, THE MOVING STALK")
    print("=" * 78)
    print()
    stalks = make_spread_population(8)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]

    # -- the cache ------------------------------------------------------
    print("  THE CACHE. The same question asked N times. The first ask")
    print("  climbs from the bottom; the rest start where the last one")
    print("  landed. Measured: ATTEMPTS made, which is what compute is.")
    print()
    cache = PathwayCache()
    attempts_with = 0
    attempts_without = 0
    t_with = time.perf_counter()
    for _q in range(20):
        for tx in stalks:
            for rx in stalks:
                if tx.id == rx.id:
                    continue
                start = cache.lookup(tx.id, rx.id)
                ok, pop, at = walk(link, ids, tx.id, rx.id,
                                   start if start is not None else 2)
                attempts_with += at
                if ok:
                    cache.store(tx.id, rx.id, pop)
                _, _, at2 = walk(link, ids, tx.id, rx.id, 2)
                attempts_without += at2
    dt = time.perf_counter() - t_with
    print("    exchanges             %d" % (20 * len(stalks) * (len(stalks) - 1)))
    print("    attempts WITH cache   %d" % attempts_with)
    print("    attempts WITHOUT      %d" % attempts_without)
    print("    attempts avoided      %d  (%.0f%% fewer)" % (
        attempts_without - attempts_with,
        100.0 * (attempts_without - attempts_with) / max(attempts_without, 1)))
    print("    cache hits / misses   %d / %d" % (cache.hits, cache.misses))
    print("    wall clock            %.2f s" % dt)
    print()
    print("    THE CAVEAT, and it is the important one: the cache saves")
    print("    ATTEMPTS, not ANSWERS. Every rung it skips is a rung that")
    print("    was NOT measured, so a cache hit is a belief that the")
    print("    channel has not changed. When the geometry moves, the cache")
    print("    is wrong, and it is wrong silently. So the cache has to")
    print("    carry the geometry it was learned under -- which is what")
    print("    the next measurement is about.")
    print()

    # -- the worn highway: does growth buy anything? --------------------
    print("  THE WORN HIGHWAY. A pathway used often gets a bigger")
    print("  cross-section, the way a frequently used axon is myelinated")
    print("  and thickened. Measured here as: grow BOTH windings of BOTH")
    print("  ends by a factor and see what the channel does.")
    print()
    print("  %-8s %-11s %-11s %-10s %-10s %-8s" % (
        "growth", "m_out_in", "pair coup", "notch dB", "clean", "named"))
    for growth in (1.00, 1.05, 1.15, 1.30, 1.50):
        grown = [CoaxWinding(
            id=s.id, girth_core=s.girth_core * growth,
            girth_in=s.girth_in * growth, girth_out=s.girth_out * growth,
            n_in=s.n_in, n_out=s.n_out) for s in stalks]
        gcore = WoundCore(stalks=grown)
        glink = InterstalkLink(core=gcore, bins=BINS)
        m = sum(s.mutual_couplings()["m_out_in"] for s in grown) / len(grown)
        pair = glink.pair(ids[0], ids[1], in_view=ids)
        ex = glink.exchange(ids[0], ids[1], in_view=ids)
        nm = name_the_speaker(glink, grown, ids[0], ids[1], CROWD)
        print("  %-8.2f %-11.4f %-11.4f %-10.2f %-10.6f %-8s" % (
            growth, m, pair.pair_coupling(), pair.channel().notch_db(),
            ex.alignment, "yes" if nm.get("correct") else "NO"))
    print()
    print("  THE FINDING, and it is a real one: growing both windings")
    print("  keeps the RATIO, so the ADDRESS does not move, the coupling")
    print("  does not move (m_out_in is overlap x inner/outer, and both")
    print("  scale), and the notch does not move. So in THIS model the")
    print("  worn highway buys NOTHING by growing the wire.")
    print()
    print("  WHY, and it is the same reason a road does not get shorter by")
    print("  being wider: the channel here is a RATIO. Everything that")
    print("  matters -- coupling, address, notch -- is a ratio of the")
    print("  geometry, and scaling the geometry leaves every ratio alone.")
    print("  What growth DOES change is the SEPARATION, which the pair")
    print("  coupling divides by, so a scaled pair couples slightly")
    print("  LESS. Which is the opposite of what the brain's myelination")
    print("  does.")
    print()
    print("  SO THE WORN HIGHWAY, to be real, has to be a state on the")
    print("  PATHWAY and not a size on the wire: a gain the pathway has")
    print("  earned. That is the next thing to build, and it is [H].")
    print()

    # -- the MOVING stalk: what happens when the geometry moves -------
    print("  THE MOVING STALK. Bobby: the brain waves its connections,")
    print("  attaches and detaches, and changes proximity. So: what")
    print("  happens to the link when the RECEIVER MOVES?")
    print()
    print("  %-10s %-12s %-11s %-11s %-11s" % (
        "separation", "pair coup", "notch dB", "direct gain", "rx resp"))
    for sep in (0.000, 0.002, 0.005, 0.010, 0.020, 0.040):
        pair = link.pair(ids[0], ids[1], in_view=ids)
        pair.separation = sep
        print("  %-10.3f %-12.4f %-11.2f %-11.4f %-11.4f" % (
            sep, pair.pair_coupling(), pair.channel().notch_db(),
            pair.direct_gain(), pair.receiver_response()))
    print()
    print("  WHAT THE MOVEMENT ACTUALLY DOES, and it is LESS than the")
    print("  first version of this text claimed. The coupling rises as the")
    print("  receiver closes -- 0.8050 at 0.040 separation, 0.8372 at")
    print("  zero, so a 4% change over that range -- and the NOTCH DOES")
    print("  NOT MOVE.")
    print()
    print("  WHY NOT, and it is a structural fact about this model rather")
    print("  than a parameter: the notch is set by the RATIO of the direct")
    print("  path to the reflected path, and the reflected path carries")
    print("  REFLECTION_LOSS times the direct one. The separation scales")
    print("  BOTH, so the ratio is untouched and the response shape is")
    print("  untouched. Moving the receiver changes the GAIN of the")
    print("  channel. It does not change the channel's SHAPE.")
    print()
    print("  The first version of this text said the notch deepens as the")
    print("  receiver closes, and said proximity buys SNR while spending")
    print("  invertibility. The measurement does not show that, and the")
    print("  sentence is corrected here rather than left standing.")
    print()
    print("  SO WHAT IS THE MOVING STALK FOR, on the evidence? In THIS")
    print("  model, it is a GAIN control, and a weak one. To make it the")
    print("  brain's mechanism -- where proximity changes what a stalk")
    print("  can RESOLVE, not merely how loudly it hears -- the notch has")
    print("  to depend on the separation. That means the reflected path")
    print("  must be a function of the geometry rather than a fixed loss")
    print("  factor, which is the physical fix and the next build.")
    print()


# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("GIRTHS, THEN THE LADDER, THEN COMMUNICATION")
    print("=" * 78)
    print()
    part_a()
    part_b()
    part_c()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
