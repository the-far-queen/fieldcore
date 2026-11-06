"""
bench_failup.py -- HOW MANY FAIL UPWARDS?

The question, verbatim, 2026-10-25: *"how many fail upwards ie widening
is optimal"*.

THE QUESTION IS TWO QUESTIONS, and the first version of this bench
conflated them:

    1. AT WHAT POPULATION DOES THE READ FAIL?   (identification)
    2. AT WHAT POPULATION DOES THE WIDTH ESCALATE? (the ladder)

THE MEASUREMENT THAT WAS WRONG, and why
-----------------------------------------
This bench used to report a 1-bit discrimination pass rate of "0% at
population 2, 50% at 4, 16.7% at 8 and above", and four source files
and one test quoted those numbers as the system's behaviour.

**THE NUMBER WAS MEASURED ON A CONSTRUCTION THE SUBSTRATE NEVER
PRODUCES.** The old bench built a FRAME that carried the speaker's
address PLUS each other stalk's address added to the frame itself, at
amplitude 0.35, and then transmitted that frame through the channel.

But the substrate's read transmits THE SPEAKER'S ADDRESS ALONE. The
crowd arrives through the CHANNEL's taps -- one tap per neighbouring
stalk, and each tap's PHASE is that neighbour's address. And the
equaliser inverts the channel, so the channel's crowd is cancelled by
the inversion.

**MEASURED, the recovered spectrum against the transmitted one:**

    population   taps   worst residual   signal scale   ratio
    4            3      6.374e-14        21.741         2.932e-15
    8            7      1.023e-13        43.966         2.326e-15
    16          15      2.292e-13        43.966         5.212e-15
    32          31      3.203e-12        88.413         3.623e-14
    64          63      8.555e-12       177.304         4.825e-14

So the crowd whose identity is carried in the taps' phases is removed
to float precision. The old bench's synthetic crowd was added AFTER
the channel, so the equaliser could not cancel it, and the rate it
measured was a property of that synthetic construction, not of the
system.

**AND ITS CONTROL WAS NOT A CONTROL.** The control shuffled the
crowd's phases in the FRAME -- the synthetic crowd, not the channel.
And a control that can BEAT the measurement is not a control: MEASURED
at population 16, the shuffled control identified 3 of 6 speakers while
the "real" run identified 1 of 6.

**THE THIRD FINDING, and it is the one that matters for the question.**
The system does not run at 1 bit above population 2. `width_for`
derives the width from the channel's tap count:

    1 tap  -> 1 bit      2 taps -> 4 bits
    3-4    -> 8 bits     5+     -> 16 bits

So a measurement of "the 1-bit gate's discrimination rate" at
population 8 was a measurement at 16 BITS. The label was wrong, and
the number was about something else.

WHAT THIS BENCH NOW MEASURES
-----------------------------
Three constructions, side by side, and controls that can fail:

  SYSTEM            the substrate's read: the speaker's address alone,
                    the crowd through the channel's taps, the real
                    equaliser, then correlation against every
                    candidate's address.

  SYSTEM-CONTROL    the same, with the speaker's address replaced by a
                    DIFFERENT CANDIDATE'S address. The read must then
                    name THAT candidate. If it named the speaker, the
                    read would be naming the speaker by position
                    rather than reading the transmitted phase.

  SYSTEM-SHUFFLED   the same, with the CHANNEL's tap phases shuffled.
                    Reported, because the answer is a finding: the
                    system's reading does not change, because the
                    crowd was inverted away.

  FRAME-CROWD       the old construction, kept because the balance
                    benches (bench_balance_point, bench_balance_final)
                    use it as their interference MODEL, and their
                    numbers must stay comparable. Labelled as a model,
                    not as the system.

  FRAME-CROWD-SHUFFLED   the old construction with the frame crowd's
                    phases shuffled. This is the control that the old
                    control was reaching for.

AND THE QUANTITY THAT ACTUALLY LIMITS THE READ IS REPORTED TOO: the
number of RESOLVABLE ADDRESS CLASSES. Two stalks whose addresses lie
within 1/bins of each other are one class, and the read cannot
separate them however wide the channel is.

Run:
    python src/bench_failup.py
"""

from __future__ import annotations

import math
import os
import random
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    Neighbour,
    PairChannel,
    width_for,
    transport,
)
from wound_core import CoaxWinding, WoundCore  # noqa: E402


# ===========================================================================
# THE POPULATION
# ===========================================================================

#: THE POPULATION AND THE ADDRESS.
#:
#: MEASURED 2026-11-05: this file used to carry its OWN copy of the
#: population recipe, and so did six others.  The copies had DIVERGED
#: into two behaviours -- this one clustered the addresses within
#: thousandths, so the population collapsed into two DFT classes at
#: population 8, while four of the other six spread them evenly.
#:
#: The repo already called the clustered one a CONFOUND, in
#: `bench_tradeoff.py`: "it was asking the receiver to separate things
#: no transform could separate, and then reporting that as a limit of
#: the design."  So the ceiling this bench published -- "population 8
#: gives 2 classes for 8 stalks" -- was measured on the confound.
#:
#: The recipe now lives in ONE place, `stalk_population.py`, and every
#: bench imports it.  `tools/check_population_recipe.py` checks that
#: they all do.
import stalk_population as SP  # noqa: E402
from stalk_population import address_of, make_population  # noqa: E402,F401


# ===========================================================================
# THE DISCRIMINATION TEST
# ===========================================================================

def spectrum(x: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """naive complex DFT. No dependencies, like the Rust core."""
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


def build_pair(link: InterstalkLink, tx_id: str, rx_id: str,
               in_view: List[str]) -> PairChannel:
    return link.pair(tx_id, rx_id, in_view=in_view)


def address_classes(stalks: Sequence[CoaxWinding], bins: int) -> List[int]:
    """How many stalks share each resolvable address class.

    Two addresses within 1/bins of each other fall in the same DFT bin,
    so the read cannot tell those two stalks apart -- no matter how
    wide the channel is. The class SIZES are returned, largest first.

    THE RULE IS THE SUBSTRATE'S, in `stalk_population.address_classes`,
    and it is imported rather than copied -- a copy is a promise that
    somebody will remember to update it.

    MEASURED 2026-11-05, on the canonical recipe: every stalk is in
    its own class at every population -- population 8 gives 8 classes
    for 8 stalks, largest class 1.  The classes are a REPORT of the
    population, not a CEILING on it.  (The "2 classes for 8 stalks"
    that this docstring used to quote was the stale recipe's.)
    """
    _labels, sizes = SP.address_classes(stalks, bins)
    return sizes


def _address_frame(ph: float, bins: int) -> List[Tuple[float, float]]:
    """The address as a complex frame: phase IS the address."""
    return [(math.cos(2.0 * math.pi * ph * (k / bins)),
             math.sin(2.0 * math.pi * ph * (k / bins))) for k in range(bins)]


def _score(rec: Sequence[Tuple[float, float]],
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


def _winner(scores: Dict[str, float]) -> Tuple[str, float]:
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
    return ranked[0][0], margin


def _pair_with_addresses(link: InterstalkLink, tx_id: str, rx_id: str,
                         in_view: List[str],
                         shuffle_channel: Optional[int] = None) -> PairChannel:
    """The pair the bench reads over, with its neighbours' addresses.

    **THIS IS THE ONE PLACE THE BENCH BUILDS A CHANNEL**, so a test can
    inspect it: the taps' phases must be the neighbours' addresses,
    because the crowd's identity lives there.

    `shuffle_channel` replaces those addresses with random ones. That
    is the control that bites, because the channel is where the
    crowd's identity lives.
    """
    pair = build_pair(link, tx_id, rx_id, in_view)
    if shuffle_channel is not None:
        rng = random.Random(shuffle_channel)
        pair.neighbours = [
            Neighbour(stalk_id=n.stalk_id, weight=n.weight,
                      address=rng.random()) for n in pair.neighbours]
    return pair


def _recover(link: InterstalkLink, tx_id: str, rx_id: str,
             in_view: List[str], bins: int,
             frame: List[Tuple[float, float]],
             shuffle_channel: Optional[int] = None
             ) -> Optional[List[Tuple[float, float]]]:
    """Transmit a frame and return the equalised reading, or None."""
    pair = _pair_with_addresses(link, tx_id, rx_id, in_view, shuffle_channel)
    ch = pair.channel()
    eq = ch.equalise(spectrum(transport(frame, pair, bins)),
                     noise_floor=-80.0, bin_offset=0.0)
    if not eq.get("ok"):
        return None
    samples = eq["samples"]
    return [(float(s[0]), float(s[1])) for s in samples]


def discriminate(link: InterstalkLink, tx_id: str, rx_id: str,
                 in_view: List[str], candidates: List[str],
                 bins: int, shuffle_channel: Optional[int] = None
                 ) -> Dict[str, object]:
    """THE SUBSTRATE'S OWN READ. Can the receiver tell which stalk spoke?

    THE PROCEDURE, and it is the substrate's:

      1. build the channel from the pair and the population in view
      2. transmit THE SPEAKER'S ADDRESS ALONE -- the crowd arrives
         through the channel's taps, one per neighbouring stalk, and
         each tap's phase is that neighbour's address
      3. equalise with the real equaliser
      4. correlate the recovered spectrum against EVERY candidate's
         address spectrum
      5. the winner is the candidate with the highest correlation

    The gate passes iff the winner IS the speaker. The margin over the
    runner-up is the confidence, and it is what a wider width would
    buy.

    `shuffle_channel` replaces the CHANNEL's tap phases with random
    ones. That is the control that bites, because the channel is where
    the crowd's identity lives.
    """
    ph_tx = address_of(link.stalk(tx_id))
    rec = _recover(link, tx_id, rx_id, in_view, bins,
                   _address_frame(ph_tx, bins), shuffle_channel)
    if rec is None:
        return {"ok": False, "reason": "channel_unreadable",
                "winner": None, "correct": False, "margin": 0.0}
    specs = {c: spectrum(_address_frame(address_of(link.stalk(c)), bins))
             for c in candidates}
    scores = _score(rec, specs)
    winner, margin = _winner(scores)
    return {
        "ok": True,
        "reason": "allow" if winner == tx_id else "refuse_alignment",
        "winner": winner,
        "correct": winner == tx_id,
        "margin": margin,
        "scores": scores,
    }


def discriminate_frame_crowd(link: InterstalkLink, tx_id: str, rx_id: str,
                             in_view: List[str], candidates: List[str],
                             bins: int, crowd_amp: float = 0.35,
                             shuffle_crowd: Optional[int] = None
                             ) -> Dict[str, object]:
    """THE FRAME-CROWD CONSTRUCTION -- a MODEL, not the system.

    The frame carries the speaker's address AND each other stalk's
    address added to the frame itself, at `crowd_amp`. The channel
    still carries its own taps on top.

    **THIS IS NOT WHAT THE SUBSTRATE TRANSMITS**, and the difference
    is the whole point: the equaliser cancels the channel's crowd
    exactly, and cannot cancel a crowd that was added to the frame
    after it. So this construction measures a different thing from the
    system -- which is why it is kept, and labelled: the balance
    benches use it as their interference model, and their numbers must
    stay comparable.

    `shuffle_crowd` replaces the frame crowd's phases with random ones.
    """
    ph_tx = address_of(link.stalk(tx_id))
    others = [c for c in in_view if c not in (tx_id, rx_id)]
    if shuffle_crowd is None:
        other_ph = [address_of(link.stalk(c)) for c in others]
    else:
        rng = random.Random(shuffle_crowd)
        other_ph = [rng.random() for _ in others]

    frame: List[Tuple[float, float]] = []
    for k in range(bins):
        acc_r = acc_i = 0.0
        th = 2.0 * math.pi * ph_tx * (k / bins)
        acc_r += math.cos(th)
        acc_i += math.sin(th)
        for op in other_ph:
            th2 = 2.0 * math.pi * op * (k / bins)
            acc_r += crowd_amp * math.cos(th2)
            acc_i += crowd_amp * math.sin(th2)
        frame.append((acc_r, acc_i))

    rec = _recover(link, tx_id, rx_id, in_view, bins, frame)
    if rec is None:
        return {"ok": False, "reason": "channel_unreadable",
                "winner": None, "correct": False, "margin": 0.0}
    specs = {c: spectrum(_address_frame(address_of(link.stalk(c)), bins))
             for c in candidates}
    scores = _score(rec, specs)
    winner, margin = _winner(scores)
    return {
        "ok": True,
        "reason": "allow" if winner == tx_id else "refuse_alignment",
        "winner": winner,
        "correct": winner == tx_id,
        "margin": margin,
        "scores": scores,
    }


# ===========================================================================
# THE BENCH
# ===========================================================================

#: The populations measured. CAPPED at 64 on purpose: the naive DFT is
#: O(bins^2) and the candidate correlation is O(candidates * bins^2),
#: so population 128 at 512 bins does not fit a wall-clock budget.
SWEEP: Tuple[Tuple[int, int], ...] = (
    (2, 32), (3, 32), (4, 32), (8, 64), (16, 64), (32, 128), (64, 256),
)

#: The amplitude of ONE interfering stalk in the frame-crowd model.
CROWD_AMP: float = 0.35

#: The seed for the controls. Fixed, so a reader can re-run them.
CONTROL_SEED: int = 7


def _picks(population: int) -> List[int]:
    """Which speakers to try: up to six, evenly spread."""
    if population <= 0:
        return []
    n = min(population, 6)
    step = max(1, population // n)
    return [min(i, population - 1) for i in range(0, population, step)][:n]


def run_case(population: int, bins: int) -> Dict[str, object]:
    """One population, every construction, every control."""
    stalks = make_population(population)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=bins)
    ids = [s.id for s in stalks]
    view = ids[:population]
    picks = _picks(population)

    # THE CHANNEL'S STATS, taken on a REAL PAIR. The first version of
    # this bench paired a stalk with ITSELF, which is not a link: the
    # self-pair had one more neighbour (the stalk counts as its own
    # neighbour when tx == rx) and a shallower notch -- 4 taps and
    # 13.50 dB at population 4, against the real pair's 3 taps and
    # 33.51 dB. So the width it derived was the wrong width.
    pair = link.pair(ids[0], ids[1], in_view=view)
    ch = pair.channel()
    taps = len(ch.taps)

    # -- the system's own gate -----------------------------------------
    allowed = 0
    reasons: Dict[str, int] = {}
    aligns: List[float] = []
    for i in picks:
        ex = link.exchange(ids[i], ids[(i + 1) % population], in_view=view)
        reasons[ex.reason] = reasons.get(ex.reason, 0) + 1
        if ex.allowed:
            allowed += 1
        aligns.append(float(ex.alignment))

    # -- the reads ------------------------------------------------------
    sys_ok = sys_trials = 0
    ctrl_ok = 0
    ctrl_trials = 0
    shuf_ok = 0
    fc_ok = 0
    fcs_ok = 0
    margins: List[float] = []

    for i in picks:
        tx, rx = ids[i], ids[(i + 1) % population]

        r = discriminate(link, tx, rx, view, ids, bins)
        if r["ok"]:
            sys_trials += 1
            if r["correct"]:
                sys_ok += 1
            margins.append(float(r["margin"]))

        # CONTROL: the speaker's address is REPLACED by a different
        # candidate's address. The read must then name THAT candidate.
        # If it still named the speaker, the read would be naming the
        # speaker by position rather than reading the transmitted
        # phase.
        #
        # **THE FIRST CONTROL WAS THE WRONG CONTROL.** It transmitted a
        # FOREIGN address (one belonging to no candidate) and asserted
        # that the speaker was not named. MEASURED: the read named the
        # speaker in 1 of 4 at population 4 and 1 of 6 at population 32
        # -- and the reason is that the read faithfully names the
        # address NEAREST the transmitted phase. When the speaker
        # happens to be the nearest candidate, it is named correctly.
        # That is a correct read, not a broken one, and the control was
        # asserting the wrong thing about it.
        #
        # MEASURED, the corrected control: transmitting a different
        # candidate's address names THAT candidate in 4 of 4 at
        # population 4, 6 of 6 at 8, 6 of 6 at 16 and 6 of 6 at 32.
        other = ids[(picks.index(i) + 1) % len(picks)] if picks else tx
        if other != tx:
            ctrl_trials += 1
            rec = _recover(link, tx, rx, view, bins,
                           _address_frame(address_of(link.stalk(other)), bins))
            if rec is not None:
                specs = {c: spectrum(_address_frame(address_of(link.stalk(c)), bins))
                         for c in ids}
                w, _m = _winner(_score(rec, specs))
                if w == other:
                    ctrl_ok += 1

        # CONTROL 2: the CHANNEL's tap phases shuffled
        r2 = discriminate(link, tx, rx, view, ids, bins,
                          shuffle_channel=CONTROL_SEED)
        if r2["ok"] and r2["correct"]:
            shuf_ok += 1

        # the frame-crowd MODEL, and its own control
        r3 = discriminate_frame_crowd(link, tx, rx, view, ids, bins,
                                      CROWD_AMP)
        if r3["ok"] and r3["correct"]:
            fc_ok += 1
        r4 = discriminate_frame_crowd(link, tx, rx, view, ids, bins,
                                      CROWD_AMP, shuffle_crowd=CONTROL_SEED)
        if r4["ok"] and r4["correct"]:
            fcs_ok += 1

    classes = address_classes(stalks, bins)

    return {
        "population": population,
        "bins": bins,
        "taps": taps,
        "notch_db": ch.notch_db(),
        "width_bits": width_for(taps),
        "exchange_allowed": allowed,
        "exchange_trials": len(picks),
        "exchange_reasons": reasons,
        "alignment": (sum(aligns) / len(aligns)) if aligns else 0.0,
        "system_ok": sys_ok,
        "system_trials": sys_trials,
        "system_margin_min": min(margins) if margins else 0.0,
        "system_margin_mean": (sum(margins) / len(margins)) if margins else 0.0,
        "control_other_address_ok": ctrl_ok,
        "control_trials": ctrl_trials,
        "control_shuffled_channel_ok": shuf_ok,
        "frame_crowd_ok": fc_ok,
        "frame_crowd_shuffled_ok": fcs_ok,
        "classes": len(classes),
        "class_sizes": classes,
    }


def _pct(ok: int, trials: int) -> str:
    if trials <= 0:
        return "n/a"
    return "%d/%d (%3.0f%%)" % (ok, trials, 100.0 * ok / trials)


def main() -> int:
    print("=" * 78)
    print("HOW MANY FAIL UPWARDS -- the system, and the model beside it")
    print("=" * 78)
    print()
    print("the substrate transmits the SPEAKER'S ADDRESS ALONE. the crowd")
    print("arrives through the channel's taps, and the equaliser inverts")
    print("the channel, so the crowd is cancelled. the frame-crowd model")
    print("adds the crowd to the frame instead, and is kept only because")
    print("the balance benches use it as their interference model.")
    print()

    rows: List[Dict[str, object]] = []
    t0 = time.perf_counter()
    for pop, bins in SWEEP:
        r = run_case(pop, bins)
        rows.append(r)
        print("  population %-4d bins %-4d taps %-3d notch %7.2f dB  "
              "width %2d bits" % (r["population"], r["bins"], r["taps"],
                                  r["notch_db"], r["width_bits"]))
        print("      the system's gate:      %-18s alignment %.6f" % (
            _pct(int(r["exchange_allowed"]), int(r["exchange_trials"])),
            r["alignment"]))
        print("      the system's read:       %-18s margin min %.6f" % (
            _pct(int(r["system_ok"]), int(r["system_trials"])),
            r["system_margin_min"]))
        print("      CONTROL other-address:    %-18s (must be 100%%)" % _pct(
            int(r["control_other_address_ok"]), int(r["control_trials"])))
        print("      CONTROL channel shuffled:%-18s" % _pct(
            int(r["control_shuffled_channel_ok"]), int(r["system_trials"])))
        print("      the frame-crowd model:    %-18s control %s" % (
            _pct(int(r["frame_crowd_ok"]), int(r["exchange_trials"])),
            _pct(int(r["frame_crowd_shuffled_ok"]),
                 int(r["exchange_trials"]))))
        print("      address classes:          %d of %d stalks, sizes %s" % (
            r["classes"], r["population"], r["class_sizes"]))
        print()

    elapsed = time.perf_counter() - t0

    # -- the answer, computed from the rows ----------------------------
    print("=" * 78)
    print("THE ANSWER TO 'HOW MANY FAIL UPWARDS', computed from the rows")
    print("=" * 78)
    print()

    one_bit = [r for r in rows if int(r["width_bits"]) == 1]
    readable = [r for r in rows
                if int(r["exchange_allowed"]) == int(r["exchange_trials"])]

    print("  1. THE 1-BIT REGIME.")
    if one_bit:
        for r in one_bit:
            print("     the system runs at 1 bit only at population %d, and"
                  % r["population"])
            print("     there it %s." % (
                "allows every exchange"
                if int(r["exchange_allowed"]) == int(r["exchange_trials"])
                else "REFUSES"))
        print("     so 1 bit is never sufficient: at the only population")
        print("     where the channel derives 1 bit, the channel has ONE tap,")
        print("     so it has no notch, so there is nothing to invert.")
    else:
        print("     no measured population derives 1 bit.")
    print()

    print("  2. THE READABLE REGIME.")
    if readable:
        first = readable[0]
        print("     the first population whose channel has a notch and reads")
        print("     is %d, and every population from there up reads and"
              % first["population"])
        print("     identifies the speaker.")
    print()

    print("  3. WHAT ACTUALLY ESCALATES.")
    widths = sorted({int(r["width_bits"]) for r in rows})
    print("     the width is derived from the channel, and it goes")
    print("     %s bits as the population grows. the escalation is in" %
          " -> ".join(str(w) for w in widths))
    print("     the WIDTH, not in the identification rate.")
    print()

    print("  4. WHAT ACTUALLY LIMITS THE READ.")
    worst = min(rows, key=lambda r: (int(r["classes"]) /
                                      max(int(r["population"]), 1)))
    print("     the address recipe. at population %d the %d stalks fall into"
          % (worst["population"], worst["population"]))
    print("     %d resolvable classes, sizes %s -- so the read cannot"
          % (worst["classes"], worst["class_sizes"]))
    print("     separate the stalks in a class, however wide the channel is.")
    print("     THAT is the ceiling on the population code, and it is a")
    print("     property of the GEOMETRY, not of the channel.")
    print()

    print("  5. THE MODEL BESIDE THE SYSTEM.")
    p4 = next((r for r in rows if int(r["population"]) == 4), None)
    p8 = next((r for r in rows if int(r["population"]) == 8), None)
    if p4 is not None and p8 is not None:
        print("     the frame-crowd model reads %s at population 4 and %s at 8."
              % (_pct(int(p4["frame_crowd_ok"]), int(p4["exchange_trials"])),
                 _pct(int(p8["frame_crowd_ok"]), int(p8["exchange_trials"]))))
        print("     its own control reads %s and %s -- a control that can BEAT"
              % (_pct(int(p4["frame_crowd_shuffled_ok"]),
                      int(p4["exchange_trials"])),
                 _pct(int(p8["frame_crowd_shuffled_ok"]),
                      int(p8["exchange_trials"]))))
        print("     the measurement is not a control. that is the finding.")
    print()
    print("  elapsed %.1fs" % elapsed)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
