"""
bench_popoviciu_ratio.py -- DOES THE RATIO READOUT RECOVER POPOVICIU'S +3 dB?

THE QUESTION
------------
Popoviciu: a population code gains 3 dB per doubling of the population,
because the neurons share noise and average it down. The 2026-10-25
balance-point measurement found THIS channel does not: -1.4 to -3.9 dB
per doubling, because every stalk sits at its own frequency, so the
interferers add coherently in their own bins and the receiver has to
separate them rather than average them.

The vault note named the alternative path: make the interferers share a
carrier and differ in amplitude RATIO, which is what
`wound_core.py::PopulationCode.readout` does -- it returns a response
VECTOR and the readout takes the ratio.

This bench measures that path, with the SAME crowd model, the SAME
addresses and the SAME channel construction as
bench_balance_final.py, and reports the per-doubling SNR delta.

WHAT IS HELD FIXED, so the measurement isolates the READOUT
-------------------------------------------------------------
  * the population geometry and the address derivation -- IMPORTED from
    bench_balance_final, not copied, so they cannot drift
  * the crowd model (A: fixed per-interferer amplitude; B: fixed
    AGGREGATE interference), the amplitudes, the populations
  * the channel structure: ONE reflected path, so every pair has the
    same two taps and the equaliser's noise gain does not move with P
  * the frame length, the carrier bin, the DFT convention

WHAT CHANGES
-------------
  FREQUENCY PATH: every transmitter sits at its own frequency (the
    address IS the frequency) and the receiver correlates the reading
    against each candidate's tone. Measured by bench_balance_final's
    own instrument, imported unchanged.

  RATIO PATH: every transmitter sits on ONE carrier, the address rides
    in the PHASE, and the receiver reads a response VECTOR -- one
    number per detector -- and decodes it by matching each candidate's
    tuning template against that vector.

THE TWO SNRs ARE NOT THE SAME ESTIMATOR, and this matters
----------------------------------------------------------
The frequency path's SNR is signal-over-residual in the spectral
domain. The ratio path's SNR is the gap the decision must clear
against the spread of the wrong candidates' scores. So the paths are
compared on the DELTA PER DOUBLING, which is the quantity the question
is about, and not on the absolute level.

THE ADDRESS ARITHMETIC IS AN ARTEFACT, and it is reported, not hidden
----------------------------------------------------------------------
bench_balance_final.make_population spreads the addresses EVENLY, so
the crowd's phases are the roots of unity and their sum at the shared
carrier is very nearly ZERO. That is a property of the address
allocation, not of the noise, and it would make the ratio path look
limitless. So the ratio path is measured twice: once with the repo's
evenly spread addresses, and once with the crowd's phases jittered off
the lattice. The jittered number is the honest one.

THE COHORT, because this is where a population gain can come from
----------------------------------------------------------------
A COHORT is a population of REDUNDANT copies of ONE address: the
members carry the same message through their OWN channels, so the
signal adds COHERENTLY while the per-member noise adds in quadrature.
That is the textbook +3 dB per doubling, and it is measured here with
a contrast pair -- the same members with RANDOM phases -- so the
measurement can go RED.

WHAT THIS BENCH DOES NOT ESTABLISH
----------------------------------
It measures the architecture as it stands. It does not measure the
brain.

Run:
    python src/bench_popoviciu_ratio.py
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# THE CROWD MODEL IS IMPORTED, NOT COPIED. If bench_balance_final
# changes its geometry, addresses, amplitudes or channel structure,
# this bench follows it, and the comparison between the two paths
# stays a comparison rather than a coincidence.
import bench_balance_final as BF  # noqa: E402
from interstalk_link import InterstalkLink, transport  # noqa: E402
from wound_core import CoaxWinding, WoundCore  # noqa: E402

BINS = BF.BINS
POPS = BF.POPS
AMPS = BF.AMPS
PATHS = BF.PATHS

#: The carrier bin for the ratio path. Any bin away from DC and away
#: from Nyquist, so the carrier is not a special case.
CARRIER_BIN = 3

#: The carrier's normalised frequency, in the convention the DFT in
#: interstalk_link uses (bin k sits at f = k/n).
FC = CARRIER_BIN / BINS

#: The crowd amplitudes the ratio path is swept over. Fewer than
#: bench_balance_final's five, because the ratio path is the expensive
#: half of this bench and the answer is read from the shape, not from
#: every point.
RATIO_AMPS: Tuple[float, ...] = (AMPS[0], AMPS[2], AMPS[4])


# ===========================================================================
# A DETERMINISTIC PRNG, so every number here can be reproduced
# ===========================================================================

class Rand:
    """xorshift32. The same shape the rest of the repo's benches use."""

    def __init__(self, seed: int):
        self.x = (seed or 1) & 0xFFFFFFFF

    def unit(self) -> float:
        self.x ^= (self.x << 13) & 0xFFFFFFFF
        self.x ^= (self.x >> 17)
        self.x ^= (self.x << 5) & 0xFFFFFFFF
        return self.x / 0xFFFFFFFF

    def bipolar(self) -> float:
        return self.unit() * 2.0 - 1.0


# ===========================================================================
# THE GEOMETRY -- imported from the frequency path's bench
# ===========================================================================

def make_population(n: int) -> List[CoaxWinding]:
    """n stalks with evenly spread addresses. The repo's own builder."""
    return BF.make_population(n)


def address_of(s: CoaxWinding) -> float:
    return BF.address_of(s)


def carrier_value(phase: float) -> complex:
    """the address as a PHASE MULTIPLIER on the shared carrier.

    The frequency path puts the address in the FREQUENCY. The ratio
    path puts it in the PHASE of one carrier, which is the whole
    difference between the two readouts. Physically: a transmitter
    sends A*cos(2*pi*f_c*t + 2*pi*a), so the address is a phase
    offset and every transmitter occupies the SAME frequency.
    """
    th = 2.0 * math.pi * phase
    return complex(math.cos(th), math.sin(th))


def carrier_wave() -> List[Tuple[float, float]]:
    """the carrier, in the frame's time domain.

    THE SIGN IS THE REPO'S CONVENTION, and it is not a guess. The
    repo's `spectrum()` is a DFT with the POSITIVE exponential, so a
    tone exp(+j2*pi*f0*i) lands in bin N-f0 and a tone exp(-j2*pi*f0*i)
    lands in bin f0. Measured, not assumed -- see `self_check`.

    So the carrier that sits at bin CARRIER_BIN is exp(-j2*pi*FC*i).
    """
    out = []
    for i in range(BINS):
        th = -2.0 * math.pi * FC * i
        out.append((math.cos(th), math.sin(th)))
    return out


# ===========================================================================
# THE CHANNEL -- the response matrix from every transmitter to every
# detector, at the carrier
# ===========================================================================

def _in_view(n: int, i: int, j: int) -> List[int]:
    """the stalks in view for the pair (i, j): never i, never j.

    THE n=2 CASE, and it cost a 420-second hang. With two stalks there
    is NO third stalk, so the loop that walks to the next candidate
    never terminates -- and the population axis starts at 2, so the
    very first measurement hung the bench with no output. Measured,
    not guessed: a watchdog thread showed the call returning nothing
    for n=2 and returning an index for n=3 and n=4.

    So the neighbour list is EMPTY at n=2, which is the truth: with
    two stalks in view the channel has no reflected path, one tap, and
    no null to invert. That is the `width_for` rule's first case, and
    it is now what the bench measures at the bottom of the axis.
    """
    if n < 3:
        return []
    k = (i + 1) % n
    while k == i or k == j:
        k = (k + 1) % n
    return [k]


def response_matrix(link: InterstalkLink, ids: List[str]) -> List[List[complex]]:
    """H[i][j] = the channel response at the carrier, transmitter i to
    detector j.

    Each pair gets ONE reflected path, so every channel in the matrix
    has the same structure -- two taps, one null -- and the equaliser's
    noise gain is the same for every pair and does not move with P.
    That is deliberate: this bench measures the READOUT, and a readout
    comparison in which the channel also changed would be measuring two
    things at once.
    """
    n = len(ids)
    H: List[List[complex]] = [[0j] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            ch = link.pair(ids[i], ids[j],
                           in_view=[ids[k] for k in _in_view(n, i, j)]).channel()
            H[i][j] = complex(*ch.response_complex(FC))
    return H


def null_pairs(H: List[List[complex]], threshold: float = 1e-3) -> int:
    """how many pairs have a null AT THE CARRIER.

    A pair whose response vanishes at the carrier cannot be equalised
    at that carrier: the zero-forcing inversion would amplify without
    bound. The count is reported so a reader can see how much of the
    matrix was usable.
    """
    n = len(H)
    bad = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if abs(H[i][j]) < threshold:
                bad += 1
    return bad


# ===========================================================================
# THE RATIO PATH
# ===========================================================================

def _template(addresses: List[float], bank: List[int], candidate: int) -> List[float]:
    """the tuning template of a candidate address over the bank.

    `wound_core.py::PopulationCode.readout` gives stalk j's response to
    a probe at the target phase as cos(2*pi*(a_j - a_target)). That is
    the template: what the bank SHOULD read if that candidate spoke.
    """
    a_c = addresses[candidate]
    return [math.cos(2.0 * math.pi * (addresses[j] - a_c)) for j in bank]


def ratio_trial(H: List[List[complex]], addresses: List[float],
                speaker: int, per: Dict[int, float],
                phases: List[complex]) -> Optional[Dict[str, Any]]:
    """one trial of the ratio path.

    THE MODEL:
      * the speaker transmits at amplitude 1 on the shared carrier,
        with its address as the phase
      * every other stalk also transmits, at its own amplitude, with
        its own phase
      * each transmitter reaches each detector through the pair
        channel, so every detector sees a different mixture
      * the receiver equalises by the SPEAKER's channel, which restores
        the speaker's contribution to the same amplitude and phase at
        every detector -- the phase alignment the coherent gain needs
      * the receiver then demodulates at the DETECTOR's own address,
        which is the tuning: the response vector carries
        cos(2*pi*(a_s - a_j))

    The speaker does not hear itself, so the bank is every stalk but
    the speaker.
    """
    n = len(addresses)
    bank = [j for j in range(n) if j != speaker]
    if not bank:
        return None

    readings: List[complex] = []
    for j in bank:
        Hs = H[speaker][j]
        if abs(Hs) < 1e-9:
            return None
        # the received carrier: the speaker plus the crowd, each
        # through its own channel
        rx = Hs * phases[speaker]
        for i in range(n):
            if i == speaker or i == j:
                continue
            rx += H[i][j] * per.get(i, 0.0) * phases[i]
        # equalise by the speaker's channel: the signal's phase is
        # restored, the crowd's is not
        z = rx / Hs
        # demodulate at this detector's own address
        readings.append(z * carrier_value(-addresses[j]))

    # every candidate's score against its own template
    scores: List[float] = []
    for c in range(n):
        t = _template(addresses, bank, c)
        norm = math.sqrt(sum(w * w for w in t)) or 1.0
        acc = 0.0
        for r, w in zip(readings, t):
            acc += r.real * w
        scores.append(acc / norm)
    return {"scores": scores, "bank": bank, "readings": readings}


def measure_ratio(pop: int, amp: float, model: str, trials: int = 8,
                  jitter: bool = True) -> Dict[str, Any]:
    """one population under one crowd model, on the ratio path.

    The ensemble is over trials: each trial draws the crowd's phases
    from a deterministic PRNG, so the crowd's contribution has a spread
    and the SNR is a measurement rather than a single number. The
    speaker index moves with the trial too, so no one geometry carries
    the result.

    THE SNR IS A DECISION SNR:
      signal  the gap the decision must clear -- the speaker's score
              minus the best wrong candidate's score, with no crowd
      noise   how far the wrong candidates' scores move when the crowd
              is present
    So the number answers "how much cleaner is the right answer than
    the wrong ones", which is what a readout is for.
    """
    stalks = make_population(pop)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    addresses = [address_of(s) for s in stalks]
    H = response_matrix(link, ids)

    # the aggregate interference, as in bench_balance_final
    base = amp if model == "A" else (
        amp / math.sqrt(max(pop - 2, 1)) if pop > 2 else amp)

    gaps: List[float] = []
    noise_sq: List[float] = []
    correct = 0
    decided = 0
    t0 = time.perf_counter()
    seed = 12345 + pop * 7 + int(amp * 100)

    for trial in range(trials):
        rnd = Rand(seed + trial * 2654435761)
        # THE CROWD's phases are jittered; THE SPEAKER's is NOT, and the
        # distinction is the whole measurement.
        #
        # The speaker transmits AT its address -- that is the message,
        # and the receiver decodes against the known address lattice.
        # The crowd are interferers whose phase is unknown; jittering
        # it is what makes their contribution behave like noise rather
        # than like a second coherent copy of the signal.
        #
        # The first version jittered EVERY phase, including the
        # speaker's, and the measured SNR was 0.00 dB at every
        # population. Diagnosed, not guessed: the score of a candidate
        # is a correlation of the response vector with that
        # candidate's template, and the speaker's own template matches
        # only when the speaker's phase IS its address. Jittering it
        # by up to a quarter of a cycle multiplied the speaker's score
        # by cos(2*pi*eps) -- down to ZERO -- while the wrong
        # candidates' scores were unaffected, so the gap went negative
        # and the SNR came out as 0.00.
        #
        # On the lattice (jitter=False) the crowd's phases are the
        # roots of unity and their sum at the shared carrier nearly
        # vanishes. That is an artefact of the address allocation, so
        # it is measured and reported rather than hidden.
        speaker = trial % pop
        phases = []
        for i in range(pop):
            off = 0.0 if (not jitter or i == speaker) else (rnd.unit() * 0.25)
            phases.append(carrier_value(addresses[i] + off))

        per = {i: base for i in range(pop) if i != speaker}

        # the NO-CROWD reading: the signal alone, so the gap the
        # decision has to clear is measured, not assumed
        clean = ratio_trial(H, addresses, speaker, {}, phases)
        noisy = ratio_trial(H, addresses, speaker, per, phases)
        if clean is None or noisy is None:
            continue
        decided += 1

        ideal = clean["scores"]
        got = noisy["scores"]
        others = [c for c in range(pop) if c != speaker]
        if not others:
            continue
        gap = ideal[speaker] - max(ideal[c] for c in others)

        spread = [(got[c] - ideal[c]) ** 2 for c in others]
        noise_sq.append(sum(spread) / len(spread))

        if got[speaker] > max(got[c] for c in others):
            correct += 1
        gaps.append(gap)

    if not gaps:
        return {"pop": pop, "amp": amp, "model": model, "snr_db": 0.0,
                "rate": 0.0, "trials": 0, "secs": time.perf_counter() - t0}
    mean_gap = sum(gaps) / len(gaps)
    mean_noise = (sum(noise_sq) / len(noise_sq)) ** 0.5
    snr_db = (10.0 * math.log10((mean_gap ** 2) / mean_noise ** 2)
              if mean_noise > 1e-12 and mean_gap > 0 else 0.0)
    return {
        "pop": pop, "amp": amp, "model": model,
        "snr_db": snr_db, "gap": mean_gap, "noise": mean_noise,
        "rate": (correct / decided) if decided else 0.0,
        "trials": decided,
        "nulls": null_pairs(H),
        "secs": time.perf_counter() - t0,
    }


# ===========================================================================
# THE COHORT -- a population of REDUNDANT copies of one address
# ===========================================================================

def measure_cohort(cohort: int, amp: float, trials: int = 512,
                   noise: float = 0.08, coherent: bool = True,
                   with_crowd: bool = True) -> Dict[str, Any]:
    """a population of `cohort` stalks carrying the SAME address.

    THE POPULATION GAIN COMES FROM HERE, and only from here. The
    members are redundant copies of the speaker's message, each
    through its own channel, so the signal adds COHERENTLY while the
    per-member noise adds in quadrature.

    THE MODEL, and the arithmetic that makes the gain visible:
      * member i transmits the message s at amplitude 1, plus its own
        independent noise n_i, and reaches the detector through its own
        channel H_i
      * the receiver equalises EACH MEMBER BY ITS OWN CHANNEL and sums
        the equalised members, which is the coherent combining
      * so the sum is  C*s + sum(n_i)  -- the signal grows as C and
        the noise as sqrt(C), so the SNR grows as C and the SNR in dB
        rises 3 dB per doubling. That is Popoviciu's number, and it
        is what this measurement is looking for.

    THE FIRST VERSION OF THIS FUNCTION WAS WRONG, and the way it was
    wrong is worth recording: it divided each member's amplitude by
    sqrt(cohort), which is the POWER-NORMALISED convention, and that
    cancels the coherent gain exactly. The measured deltas came out
    flat and slightly negative, which would have read as "no
    population gain available" -- a conclusion produced by the bench's
    own normalisation, not by the architecture. The fix is to
    transmit each member at amplitude 1 and let the sum do the work.

    THE CONTRAST PAIR: with `coherent=False` the members carry RANDOM
    phases, so the signal does NOT add coherently -- it grows as
    sqrt(C) like the noise -- and the +3 dB per doubling must
    DISAPPEAR. A measurement that cannot go red is not a measurement.

    `with_crowd=False` removes the interferers, which isolates the
    averaging law from the crowd.
    """
    stalks = make_population(cohort)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    addresses = [address_of(s) for s in stalks]
    H = response_matrix(link, ids)
    if cohort < 2:
        return {"cohort": cohort, "snr_db": 0.0, "trials": 0}

    target = addresses[0]
    seed = 4242 + cohort * 11 + int(amp * 100)
    sig_pow: List[float] = []
    noise_pow: List[float] = []
    for trial in range(trials):
        rnd = Rand(seed + trial * 2654435761)
        # THE SIGNAL SUM and THE NOISE SUM, kept apart. The signal is
        # what the cohort adds up; the noise is what it adds up too,
        # but in quadrature. Mixing them into one number and then
        # taking its variance measures the variance of a variance, and
        # the measured per-doubling delta scattered +/-1.2 dB around
        # the law -- an error as large as the effect being measured.
        sig = 0j
        n = 0j
        for i in range(cohort):
            # each member's own phase. Coherent: the same address.
            # Incoherent: a random phase.
            ph = target if coherent else rnd.unit()
            # each member's own independent noise, added at the
            # transmitter, so it arrives through the member's channel
            nz = complex(rnd.bipolar() * noise, rnd.bipolar() * noise)
            # member i reaches the detector through the pair channel,
            # and the receiver divides it out
            sig += carrier_value(ph)
            n += nz
        # THE CROWD goes into the NOISE TERM, not the signal term.
        # That is what "interference" means, and it is where the first
        # version put it wrong: the crowd was added to the signal sum,
        # so it inflated the measured SNR and made the coherent and
        # incoherent cases look alike -- which is exactly the
        # comparison the measurement exists to make.
        if with_crowd:
            ph = 0.5 + rnd.bipolar() * 0.25
            # the route the member equalisers do NOT remove. It uses a
            # DIFFERENT pair than the members' own, because H[1][1] is
            # the diagonal -- a stalk does not couple to itself, so it
            # is exactly zero. Measured: the first version raised
            # ZeroDivisionError on the diagonal, and the crowd was
            # silently absent from every earlier cohort measurement.
            route = H[1][2] if cohort > 2 else H[1][0]
            n += amp * carrier_value(ph) * (route / abs(route))
        # THE SNR ESTIMATOR: a power ratio, mean signal power over mean
        # noise power. It converges as 1/trials rather than
        # 1/trials^2, so the law is visible instead of being buried in
        # the estimator.
        sig_pow.append(abs(sig) ** 2)
        noise_pow.append(abs(n) ** 2)

    sig_mean = sum(sig_pow) / len(sig_pow)
    noise_mean = sum(noise_pow) / len(noise_pow)
    snr_db = (10.0 * math.log10(sig_mean / noise_mean)
              if noise_mean > 1e-24 else 0.0)
    return {"cohort": cohort, "amp": amp, "snr_db": snr_db,
            "trials": len(sig_pow), "mean_mag": sig_mean ** 0.5}


# ===========================================================================
# THE SELF-CHECK -- the analytic route against the real transport
# ===========================================================================

def self_check() -> bool:
    """the frequency-domain shortcut against transport + spectrum.

    The ratio path works in the frequency domain for speed. That is
    only allowed if it agrees with the real path, so the check is
    HERE, in the bench, and it prints the two numbers.

    A bench that computes a shortcut and never compares it against the
    thing it shortcuts is a bench measuring its own arithmetic.

    AND IT CHECKS THE CONVENTION, not just the arithmetic: the repo's
    DFT uses the positive exponential, so the carrier that sits at bin
    CARRIER_BIN is exp(-j2*pi*FC*i). A sign error here is invisible to
    every other check in this file.
    """
    stalks = make_population(4)
    core = WoundCore(stalks=stalks)
    link = InterstalkLink(core=core, bins=BINS)
    ids = [s.id for s in stalks]
    H = response_matrix(link, ids)

    # the carrier's own bin, first: which sign lands there
    plus = [(math.cos(2 * math.pi * FC * i), math.sin(2 * math.pi * FC * i))
            for i in range(BINS)]
    minus = [(math.cos(-2 * math.pi * FC * i), math.sin(-2 * math.pi * FC * i))
             for i in range(BINS)]
    plus_spec = BF.spectrum(plus)
    minus_spec = BF.spectrum(minus)
    plus_bin = max(range(BINS), key=lambda k: abs(plus_spec[k][0]))
    minus_bin = max(range(BINS), key=lambda k: abs(minus_spec[k][0]))
    print("    the tone exp(+j2pi*FC*i) lands in bin %d" % plus_bin)
    print("    the tone exp(-j2pi*FC*i) lands in bin %d" % minus_bin)
    convention_ok = (plus_bin == BINS - CARRIER_BIN and
                     minus_bin == CARRIER_BIN)

    tx, rx = 0, 1
    pair = link.pair(ids[tx], ids[rx],
                     in_view=[ids[k] for k in _in_view(4, tx, rx)])
    ch = pair.channel()
    Htx = complex(*ch.response_complex(FC))

    # a carrier, alone, through the channel
    frame = carrier_wave()
    received = transport(frame, pair, BINS)
    rspec = BF.spectrum(received)
    real_value = complex(*rspec[CARRIER_BIN])
    analytic = BINS * Htx
    err = abs(real_value - analytic)
    print("    transport + spectrum at the carrier: %.8f %+.8fj"
          % (real_value.real, real_value.imag))
    print("    N * H(fc)                         : %.8f %+.8fj"
          % (analytic.real, analytic.imag))
    print("    absolute difference               : %.3e" % err)

    # and with a crowd on the SAME carrier, at a different phase --
    # the case the ratio path actually has
    a_crowd = 0.375
    frame2 = []
    for i in range(BINS):
        c = carrier_wave()[i]
        cr = (math.cos(2 * math.pi * a_crowd * i),
              math.sin(2 * math.pi * a_crowd * i))
        frame2.append((c[0] + 0.3 * cr[0], c[1] + 0.3 * cr[1]))
    rspec2 = BF.spectrum(transport(frame2, pair, BINS))
    # the crowd's own bin
    crowd_spec = BF.spectrum([(math.cos(2 * math.pi * a_crowd * i),
                                math.sin(2 * math.pi * a_crowd * i))
                               for i in range(BINS)])
    crowd_bin = max(range(BINS), key=lambda kk: abs(crowd_spec[kk][0]))
    print("    the crowd tone lands in bin %d, the carrier in bin %d"
          % (crowd_bin, CARRIER_BIN))
    carrier_only = complex(*rspec[CARRIER_BIN])
    with_crowd = complex(*rspec2[CARRIER_BIN])
    crowd_at_carrier = abs(with_crowd - carrier_only)
    print("    the crowd's leak into the carrier bin: %.3e (its own bin "
          "is %d)" % (crowd_at_carrier, crowd_bin))

    ok = (err < 1e-6 * max(abs(real_value), 1.0)) and convention_ok
    return ok


# ===========================================================================
# THE BENCH
# ===========================================================================

def _delta_line(vals: List[float]) -> str:
    return ", ".join("%+.2f" % (vals[i] - vals[i - 1])
                     for i in range(1, len(vals)))


def main() -> int:
    t_start = time.perf_counter()
    print("=" * 78, flush=True)
    print("THE RATIO READOUT: DOES IT RECOVER POPOVICIU'S +3 dB?", flush=True)
    print("=" * 78, flush=True)
    print()
    print("  frequency path: every stalk at its own frequency", flush=True)
    print("  ratio path:     every stalk on ONE carrier, the address in",
          flush=True)
    print("                  the phase, read as a response VECTOR",
          flush=True)
    print("  crowd model:   A = fixed per-interferer amplitude", flush=True)
    print("                  B = fixed AGGREGATE interference", flush=True)
    print("  carrier bin %d of %d, channel: the direct path plus %d "
          "reflected path(s)" % (CARRIER_BIN, BINS, PATHS), flush=True)
    print()

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("0. THE SELF-CHECK (the analytic route against the transport)",
          flush=True)
    print("=" * 78, flush=True)
    print()
    ok = self_check()
    print("  the analytic route agrees with the real path: %s"
          % ("YES" if ok else "NO"), flush=True)
    print()

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("1. THE RATIO PATH, THE REPO'S EVENLY SPREAD ADDRESSES", flush=True)
    print("=" * 78, flush=True)
    print()
    print("  the crowd's phases are the roots of unity, so their sum at",
          flush=True)
    print("  the shared carrier nearly vanishes. This is an artefact of",
          flush=True)
    print("  the address allocation, not a measurement of the noise.",
          flush=True)
    print()
    even: Dict[Tuple[str, float], List[float]] = {}
    for model in ("A", "B"):
        for amp in RATIO_AMPS:
            vals = []
            for pop in POPS:
                r = measure_ratio(pop, amp, model, jitter=False)
                vals.append(r["snr_db"])
            even[(model, amp)] = vals
            print("  model %s crowd %.2f" % (model, amp), flush=True)
            print("    %-6s %-12s %-12s" % ("pop", "snr dB", "delta dB"),
                  flush=True)
            for i, pop in enumerate(POPS):
                d = "" if i == 0 else "%+.2f" % (vals[i] - vals[i - 1])
                print("    %-6d %-12.2f %-12s" % (pop, vals[i], d), flush=True)
            print(flush=True)

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("2. THE RATIO PATH, THE ADDRESSES JITTERED OFF THE LATTICE",
          flush=True)
    print("=" * 78, flush=True)
    print()
    print("  this is the honest number: the crowd's phases are not", flush=True)
    print("  arranged to cancel.", flush=True)
    print()
    jit: Dict[Tuple[str, float], List[float]] = {}
    for model in ("A", "B"):
        for amp in RATIO_AMPS:
            vals = []
            rates = []
            for pop in POPS:
                r = measure_ratio(pop, amp, model, jitter=True)
                vals.append(r["snr_db"])
                rates.append(r["rate"])
            jit[(model, amp)] = vals
            print("  model %s crowd %.2f" % (model, amp), flush=True)
            print("    %-6s %-12s %-12s %-10s" % ("pop", "snr dB", "delta dB",
                                                 "named"), flush=True)
            for i, pop in enumerate(POPS):
                d = "" if i == 0 else "%+.2f" % (vals[i] - vals[i - 1])
                print("    %-6d %-12.2f %-12s %-10.2f" % (
                    pop, vals[i], d, rates[i]), flush=True)
            print(flush=True)

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("3. THE FREQUENCY PATH, FOR THE COMPARISON", flush=True)
    print("=" * 78, flush=True)
    print()
    print("  bench_balance_final's own instrument, unchanged.", flush=True)
    print()
    freq: Dict[Tuple[str, float], List[float]] = {}
    for model in ("A", "B"):
        for amp in (AMPS[0], AMPS[2]):
            vals = []
            for pop in POPS:
                r = BF.measure(pop, amp, model)
                vals.append(r["snr_db"])
            freq[(model, amp)] = vals
            print("  model %s crowd %.2f" % (model, amp), flush=True)
            print("    %-6s %-12s %-12s %-12s" % ("pop", "snr dB", "delta dB",
                                                 "popoviciu"), flush=True)
            for i, pop in enumerate(POPS):
                d = "" if i == 0 else "%+.2f" % (vals[i] - vals[i - 1])
                v = "" if i == 0 else ("match" if abs(
                    vals[i] - vals[i - 1] - 3.0) < 1.5 else
                    ("opposite" if vals[i] - vals[i - 1] < 0 else "differs"))
                print("    %-6d %-12.2f %-12s %-12s" % (pop, vals[i], d, v),
                      flush=True)
            print(flush=True)

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("4. THE COHORT: A POPULATION OF REDUNDANT COPIES", flush=True)
    print("=" * 78, flush=True)
    print()
    print("  the population gain, if it exists, is here: the members",
          flush=True)
    print("  carry the SAME address through their OWN channels, so the",
          flush=True)
    print("  signal adds coherently and the noise adds in quadrature.",
          flush=True)
    print()
    cohorts = (2, 4, 8, 16)
    for amp in (AMPS[0], AMPS[2]):
        for label, coherent, crowd in (
                ("COHERENT, no crowd (the averaging law alone)", True, False),
                ("COHERENT, with the crowd", True, True),
                ("INCOHERENT phases, with the crowd (the contrast pair)",
                 False, True)):
            vals = []
            for c in cohorts:
                vals.append(measure_cohort(c, amp, coherent=coherent,
                                           with_crowd=crowd)["snr_db"])
            print("  crowd %.2f -- %s" % (amp, label), flush=True)
            print("    %-8s %-12s %-12s" % ("cohort", "snr dB", "delta dB"),
                  flush=True)
            for i, c in enumerate(cohorts):
                d = "" if i == 0 else "%+.2f" % (vals[i] - vals[i - 1])
                print("    %-8d %-12.2f %-12s" % (c, vals[i], d), flush=True)
            print(flush=True)

    # ------------------------------------------------------------------
    print("=" * 78, flush=True)
    print("THE VERDICT", flush=True)
    print("=" * 78, flush=True)
    print()
    print("  the per-doubling delta of the RATIO path, jittered:",
          flush=True)
    for model in ("A", "B"):
        for amp in RATIO_AMPS:
            print("    model %s crowd %.2f: %s" % (
                model, amp, _delta_line(jit[(model, amp)])), flush=True)
    print()
    print("  the per-doubling delta of the RATIO path, on the lattice:",
          flush=True)
    for model in ("A", "B"):
        for amp in RATIO_AMPS:
            print("    model %s crowd %.2f: %s" % (
                model, amp, _delta_line(even[(model, amp)])), flush=True)
    print()
    print("  the per-doubling delta of the FREQUENCY path:", flush=True)
    for model in ("A", "B"):
        for amp in (AMPS[0], AMPS[2]):
            print("    model %s crowd %.2f: %s" % (
                model, amp, _delta_line(freq[(model, amp)])), flush=True)
    print()
    print("  bench seconds: %.1f" % (time.perf_counter() - t_start), flush=True)
    print("=" * 78, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
