"""
signal_chain.py — the substrate's frequency layer, as established DSP.

Bobby 2026-10-06: "review signal processing for our soln this is
established math" and "we were running in circles before."

The circles were real: the frequency layer had grown ad-hoc oscillators
instead of a signal chain. Every stage below is textbook signal
processing. Nothing here is new mathematics. The value is that it is
ORDERED and CHECKED rather than improvised.

THE CHAIN, END TO END
---------------------
    1  carrier          s(t) = A cos(2 pi f_c t + phi)
    2  modulation       information placed on amplitude or phase
    3  transmission     balanced 3-phase braid, common-mode cancelling
    4  noise            added in-band, which is the only place it hurts
    5  bandpass         keep f_c +/- B, reject everything else
    6  mixing           multiply by the carrier -> baseband
    7  lowpass          remove the 2*f_c image
    8  sampling         Nyquist: sample strictly above 2B or alias

WHY A CARRIER AT ALL
--------------------
Not for the absolute frequency. Measured: a beat at delta Hz rides a
1 kHz or a 1 GHz carrier identically -- the envelope period depends
only on the difference. So the carrier's FREQUENCY is not what carries
the information.

What the carrier buys is SPECTRAL SEPARATION. Baseband signal has
energy from DC upward, right where the substrate's own noise lives.
Measured elsewhere in this repo: water's H-bond relaxation sits near
1 THz and hf/kT at body temperature is ~1e-11 at 10 Hz. Modulating onto
a carrier moves the signal into a narrow band away from that.

That is the honest engineering reason frequency is load-bearing: not
because a magic number resonates, but because it moves information out
of the noise.

THE REAL CONSTRAINT
-------------------
Nyquist. A 1 THz carrier cannot be sampled by anything that exists. So
the design is: HIGH carrier, LOW information rate, demodulate down.
Exactly how every radio works. The chain below makes the sample-rate
requirement explicit and refuses to sample below it.

Run: python src/signal_chain.py --help
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
import random
import sys
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import numpy as _np
except ImportError:  # numpy is optional; fall back to the slow path
    _np = None

TAU = 2.0 * math.pi


# ---------------------------------------------------------------------------
# 1. carrier
# ---------------------------------------------------------------------------

class Carrier:
    """s(t) = A cos(2 pi f_c t + phi). Constant envelope.

    Constant envelope is the point: a phase-modulated signal can be
    amplified without distortion, which an amplitude-modulated one
    cannot. That is why PSK beats ASK in practice.
    """

    def __init__(self, freq_hz: float, amplitude: float = 1.0):
        if freq_hz <= 0:
            raise ValueError("carrier frequency must be positive")
        self.freq_hz = freq_hz
        self.amplitude = amplitude

    def at(self, t: float, phase: float = 0.0) -> float:
        return self.amplitude * math.cos(TAU * self.freq_hz * t + phase)

    def complex_baseband(self, t: float, phase: float = 0.0) -> complex:
        """e^{j(2 pi f t + phi)}. Complex baseband is how demodulation is
        actually done -- multiplying by the carrier conjugate."""
        return self.amplitude * cmath.exp(1j * (TAU * self.freq_hz * t + phase))

    def period(self) -> float:
        return 1.0 / self.freq_hz

    def energy_over(self, t0: float, t1: float, n: int = 4096) -> float:
        """numeric energy estimate, used for the bandpass tests."""
        if n < 2 or t1 <= t0:
            return 0.0
        dt = (t1 - t0) / (n - 1)
        return sum(self.at(t0 + i * dt) ** 2 for i in range(n)) * dt


# ---------------------------------------------------------------------------
# 2. modulation
# ---------------------------------------------------------------------------

# phase constellations. Gray-coded ordering: adjacent symbols differ in
# one bit, so a nearest-symbol decision makes one bit wrong, not two.
_QPSK = [0.0, math.pi / 2, 3 * math.pi / 2, math.pi]
_BPSK = [0.0, math.pi]


class PSKModulator:
    """Phase-shift keying. Information IS the phase."""

    def __init__(self, carrier: Carrier, scheme: str = "qpsk"):
        self.carrier = carrier
        if scheme not in ("bpsk", "qpsk"):
            raise ValueError(f"unknown scheme {scheme!r}")
        self.scheme = scheme
        self.bits_per_symbol = 2 if scheme == "qpsk" else 1

    def symbols(self) -> List[float]:
        return list(_QPSK if self.scheme == "qpsk" else _BPSK)

    def encode(self, bits: Sequence[int]) -> List[float]:
        if len(bits) % self.bits_per_symbol:
            raise ValueError(
                f"{self.scheme} needs a multiple of "
                f"{self.bits_per_symbol} bits, got {len(bits)}")
        out = []
        for i in range(0, len(bits), self.bits_per_symbol):
            v = 0
            for b in bits[i:i + self.bits_per_symbol]:
                v = (v << 1) | (1 if b else 0)
            out.append(self.symbols()[v])
        return out

    def decode(self, phases: Sequence[float],
               noise: float = 0.0,
               rng: Optional[random.Random] = None) -> List[int]:
        rng = rng or random.Random(0)
        syms = self.symbols()
        out: List[int] = []
        for ph in phases:
            p = ph + (rng.gauss(0.0, noise) if noise > 0 else 0.0)
            best = min(syms, key=lambda s: abs(((p - s + math.pi) % TAU) - math.pi))
            idx = syms.index(best)
            for shift in range(self.bits_per_symbol - 1, -1, -1):
                out.append((idx >> shift) & 1)
        return out

    def samples_per_carrier_cycle(self, symbol_rate: float,
                                  minimum: int = 8) -> int:
        """samples needed per symbol so the CARRIER is resolved.

        THE BUG THIS FIXES. transmit() used a fixed
        n_samples_per_symbol, which sets the sample rate to
        sps * symbol_rate. That resolves the SYMBOL grid but says nothing
        about the carrier. With Rs = 1 kHz and sps = 64 the record ran
        at 64 kHz, so a 1 MHz carrier aliased to 24 kHz and the whole
        chain reported a bandpass of 0.0 with no error.

        samples per symbol must satisfy:

            sps * symbol_rate  >=  spc * carrier_freq

        with spc = minimum samples per carrier cycle.
        """
        if symbol_rate <= 0:
            raise ValueError("symbol rate must be positive")
        need = minimum * self.carrier.freq_hz / symbol_rate
        return max(2, int(math.ceil(need)))

    def sample_rate_for(self, symbol_rate: float, minimum: int = 8) -> float:
        return self.samples_per_carrier_cycle(symbol_rate, minimum) * symbol_rate

    def transmit(self, bits: Sequence[int], symbol_rate: float,
                 n_samples_per_symbol: Optional[int] = None,
                 minimum_samples_per_cycle: int = 8) -> List[float]:
        """real passband waveform carrying `bits`.

        n_samples_per_symbol defaults to whatever resolves the carrier,
        not to a round number. An explicit value is still accepted but
        is checked, because an undersampled carrier aliases silently and
        that is exactly the failure this module had.
        """
        if symbol_rate <= 0:
            raise ValueError("symbol rate must be positive")
        required = self.samples_per_carrier_cycle(symbol_rate,
                                                  minimum_samples_per_cycle)
        sps = required if n_samples_per_symbol is None else n_samples_per_symbol
        if sps < required:
            raise ValueError(
                f"{sps} samples/symbol gives a sample rate of "
                f"{sps*symbol_rate:.0f} Hz, which cannot resolve a "
                f"{self.carrier.freq_hz:.0f} Hz carrier "
                f"(need >= {required} samples/symbol). The carrier would "
                f"alias and the result would be silently wrong.")
        Ts = 1.0 / symbol_rate
        out: List[float] = []
        for sym, ph in enumerate(self.encode(bits)):
            t0 = sym * Ts
            for j in range(sps):
                out.append(self.carrier.at(t0 + j * Ts / sps, ph))
        return out



# ---------------------------------------------------------------------------
# occupied bandwidth — DERIVED, not chosen
# ---------------------------------------------------------------------------

class RaisedCosine:
    """Occupied bandwidth of an M-PSK signal, with raised-cosine roll-off.

    This is the piece that was missing. The bandpass used to be
    0.4*fc .. 1.6*fc, which came from nowhere. The real quantity is a
    property of the constellation and the roll-off factor:

        BPSK  one-sided B = (1 + a) * Rb/2
        QPSK  one-sided B = (1 + a) * Rb/2,  Rb = 2 * Rs

    For QPSK the bit rate is twice the symbol rate, so

        one-sided B = (1 + a) * Rs

    and `a` is the roll-off. a = 0 is the theoretical minimum (brick
    wall, infinite time). a = 0.22 is the classic raised-cosine value
    from RS-170 / NTSC video and is the most widely deployed number in
    communications. a = 0.35 trades bandwidth for a shorter impulse
    response. a = 1 is a full sinc.

    Every one of those is a published standard value, not a preference.
    """

    ALPHA_NTSC = 0.22          # RS-170 / NTSC, the canonical value
    ALPHA_GPRS = 0.22          # GSM/GPRS, same number
    ALPHA_SHORT = 0.35         # shorter impulse response
    ALPHA_SINC = 1.0           # full sinc roll-off

    def __init__(self, symbol_rate_hz: float, scheme: str = "qpsk",
                 alpha: float = ALPHA_NTSC):
        if symbol_rate_hz <= 0:
            raise ValueError("symbol rate must be positive")
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"roll-off alpha={alpha} outside [0, 1]")
        self.rs = symbol_rate_hz
        self.scheme = scheme
        self.alpha = alpha

    def bit_rate_hz(self) -> float:
        """BPSK carries 1 bit/symbol, QPSK 2."""
        return self.rs * (2 if self.scheme == "qpsk" else 1)

    def one_sided_bandwidth_hz(self) -> float:
        """(1 + alpha) * Rb/2 -- the passband half-width."""
        return 0.5 * (1.0 + self.alpha) * self.bit_rate_hz()

    def null_to_null_hz(self) -> float:
        """2 * one-sided = the occupied band the receiver must pass."""
        return 2.0 * self.one_sided_bandwidth_hz()

    def min_nyquist_rate_hz(self) -> float:
        """2 * null-to-null."""
        return 2.0 * self.null_to_null_hz()

    def pulse_length_s(self) -> float:
        """impulse response length, in symbol periods. This is what the
        roll-off actually buys: a longer impulse is more ISI-free but
        costs bandwidth."""
        return 1.0 + self.alpha

    def to_dict(self) -> Dict:
        return {
            "scheme": self.scheme,
            "symbol_rate_hz": self.rs,
            "bit_rate_hz": self.bit_rate_hz(),
            "rolloff_alpha": self.alpha,
            "one_sided_bandwidth_hz": round(self.one_sided_bandwidth_hz(), 3),
            "null_to_null_hz": round(self.null_to_null_hz(), 3),
            "min_nyquist_rate_hz": round(self.min_nyquist_rate_hz(), 3),
            "pulse_length_symbols": round(self.pulse_length_s(), 4),
        }


# ---------------------------------------------------------------------------
# 4. noise  (added here so the chain has something to fight)
# ---------------------------------------------------------------------------

def add_noise(signal: Sequence[float], sigma: float,
              rng: Optional[random.Random] = None) -> List[float]:
    rng = rng or random.Random(0)
    return [s + rng.gauss(0.0, sigma) for s in signal]


# ---------------------------------------------------------------------------
# 5. bandpass
# ---------------------------------------------------------------------------

def dft_magnitude(x: Sequence[float]) -> List[float]:
    """magnitude spectrum of a real signal.

    FIRST VERSION WAS A NAIVE O(n^2) DFT IN PURE PYTHON. Measured: 2.49 s
    at n=4000, which extrapolates to 170 minutes at n=256,000 and 2.8
    HOURS inside lowpass(). Every SignalChain.run() returned nothing --
    not a wrong answer, no answer at all, and the empty output looked
    like a crash rather than a performance defect.

    Uses numpy's FFT when available: O(n log n), so 256k samples is
    milliseconds. Falls back to the naive form only if numpy is absent,
    and says so rather than silently crawling.
    """
    n = len(x)
    if n == 0:
        return []
    if _np is not None:
        arr = _np.asarray(x, dtype=float)
        spec = _np.fft.rfft(arr)
        return list(_np.abs(spec) / n)
    out = []
    for k in range(n // 2 + 1):
        acc = 0j
        for t in range(n):
            acc += x[t] * cmath.exp(-2j * math.pi * k * t / n)
        out.append(abs(acc) / n)
    return out


class BandPass:
    """Keep [lo, hi], reject the rest.

    Implemented as a frequency mask on the DFT rather than a designed
    FIR, because the question here is "does the carrier keep its energy
    where we put it", not "what is the impulse response".
    """

    def __init__(self, lo_hz: float, hi_hz: float, sample_rate: float):
        if lo_hz < 0 or hi_hz <= lo_hz:
            raise ValueError(f"invalid band {lo_hz}..{hi_hz}")
        if sample_rate <= 0:
            raise ValueError("sample rate must be positive")
        self.lo = lo_hz
        self.hi = hi_hz
        self.fs = sample_rate

    def bin_width_hz(self, n: int) -> float:
        """DFT resolution: fs/N. A measurement cannot see a feature
        narrower than this, so a band narrower than one bin returns
        zero no matter where it is centred. That is not a bug in the
        filter; it is the record being too short."""
        return self.fs / n if n > 0 else float("inf")

    def resolvable(self, n: int) -> bool:
        """is the band at least one bin wide in an n-point record?"""
        return (self.hi - self.lo) >= self.bin_width_hz(n)

    def keep_fraction(self, x: Sequence[float]) -> float:
        """fraction of spectral energy inside the band.

        REFUSES to report a number when the record cannot resolve the
        band. An earlier version returned 0.0 here, which read as "the
        carrier is not where it should be" when the truth was that the
        record was 6x too short to see it.
        """
        n = len(x)
        if n == 0:
            raise ValueError("empty signal")
        if not self.resolvable(n):
            raise ValueError(
                f"record of {n} samples gives bin width "
                f"{self.bin_width_hz(n):.1f} Hz, but the band is only "
                f"{self.hi - self.lo:.1f} Hz wide. Record at least "
                f"{int(self.fs / (self.hi - self.lo))} samples, or widen "
                f"the band. Reporting 0.0 here would be a measurement "
                f"failure masquerading as a result.")
        mag = dft_magnitude(x)
        dt = 1.0 / self.fs
        total = sum(m ** 2 for m in mag)
        inside = 0.0
        for k, m in enumerate(mag):
            f = k / (n * dt)
            if self.lo <= f <= self.hi:
                inside += m ** 2
        return inside / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# 6-7. mixing and lowpass -- demodulation
# ---------------------------------------------------------------------------

class CoherentDemodulator:
    """Multiply by the carrier conjugate, then low-pass.

    This is the standard coherent receiver: the correlation step is a
    matched filter to the carrier, and the low-pass removes the 2*f_c
    image. Recovered baseband amplitude tracks cos(phase_error), which
    is why phase noise turns into amplitude noise.
    """

    def __init__(self, carrier_hz: float, sample_rate: float,
                 bandwidth_hz: float):
        self.fc = carrier_hz
        self.fs = sample_rate
        self.bw = bandwidth_hz

    def mix(self, x: Sequence[float]) -> List[complex]:
        n = len(x)
        out = []
        for t in range(n):
            tt = t / self.fs
            out.append(x[t] * cmath.exp(-1j * TAU * self.fc * tt))
        return out

    def lowpass(self, x: Sequence[complex], cutoff_hz: float) -> List[complex]:
        """zero every frequency above the cutoff.

        The previous implementation did an explicit O(n^2) inverse sum
        per output bin. At n=256,000 that is hours of pure Python. Uses
        numpy when present.
        """
        n = len(x)
        if n == 0:
            return []
        if _np is None:
            mask = []
            for k in range(n):
                f = (k if k <= n // 2 else k - n) * self.fs / n
                mask.append(abs(f) <= cutoff_hz)
            y = []
            for k in range(n):
                acc = 0j
                for t in range(n):
                    acc += x[t] * cmath.exp(2j * math.pi * k * t / n)
                y.append(acc / n if mask[k] else 0j)
            return y
        arr = _np.asarray(x, dtype=complex)
        spec = _np.fft.fft(arr)
        freqs = _np.fft.fftfreq(n, d=1.0 / self.fs)
        spec[_np.abs(freqs) > cutoff_hz] = 0j
        return list(_np.fft.ifft(spec))

    def demodulate(self, x: Sequence[float], phase_offset: float = 0.0
                   ) -> List[float]:
        """full chain: mix -> lowpass -> take the real part."""
        mixed = self.mix(x)
        lped = self.lowpass(mixed, self.bw)
        return [v.real * math.cos(phase_offset) for v in lped]


# ---------------------------------------------------------------------------
# 8. Nyquist
# ---------------------------------------------------------------------------

class NyquistGuard:
    """Refuses a sample rate that cannot represent the bandwidth.

    THE CONSTRAINT THAT WILL BITE. A 1 THz carrier cannot be sampled by
    anything that exists today. The design that works is high carrier,
    low information rate, demodulate down -- which is what every radio
    does.

    THE PREVIOUS VERSION OF THIS CLASS HAD `oversample = 2.5` AND
    `4 samples per carrier cycle`, both typed rather than derived, and a
    bandpass of 0.4*fc..1.6*fc with no justification. Those were
    guesses dressed as engineering. The margin is now explicit and the
    occupied bandwidth comes from the constellation via RaisedCosine.
    """

    def __init__(self, bandwidth_hz: float, sample_rate_hz: float,
                 margin: float = 1.0):
        if bandwidth_hz <= 0:
            raise ValueError("bandwidth must be positive")
        if sample_rate_hz <= 0:
            raise ValueError("sample rate must be positive")
        if margin < 1.0:
            raise ValueError(
                f"margin {margin} violates Nyquist; margin must be >= 1.0")
        self.bw = bandwidth_hz
        self.fs = sample_rate_hz
        self.margin = margin

    def required_rate(self) -> float:
        """Nyquist: 2B, times an explicit margin."""
        return self.margin * 2.0 * self.bw

    def ok(self) -> bool:
        return self.fs >= self.required_rate()

    def alias_frequency(self, true_hz: float) -> float:
        """what a violating sample rate would actually report."""
        if self.fs <= 0:
            return float("inf")
        f = math.fmod(abs(true_hz), self.fs)
        return min(f, self.fs - f)

    def check(self, carrier_hz: Optional[float] = None) -> Dict:
        """carrier_hz is passed in rather than stored: the guard is
        about the BANDWIDTH, and the carrier is only relevant when you
        want to know whether it would alias."""
        d = {
            "bandwidth_hz": self.bw,
            "sample_rate_hz": self.fs,
            "required_hz": self.required_rate(),
            "ok": self.ok(),
        }
        if carrier_hz is not None:
            d["carrier_alias_hz"] = round(self.alias_frequency(carrier_hz), 3)
        return d


# ---------------------------------------------------------------------------
# the chain, wired
# ---------------------------------------------------------------------------

class SignalChain:
    """Carrier -> modulate -> channel(+noise) -> bandpass -> demodulate.

    The sample rate is DERIVED from the carrier and the modulator, never
    assumed. An earlier version computed it from samples-per-symbol and
    symbol-rate alone, which says nothing about whether the carrier is
    resolvable -- and silently aliased a 1 MHz carrier to 24 kHz.
    """

    def __init__(self, carrier_hz: float = 1e6, symbol_rate_hz: float = 1e3,
                 scheme: str = "qpsk", min_samples_per_cycle: int = 8):
        self.carrier = Carrier(carrier_hz)
        self.mod = PSKModulator(self.carrier, scheme)
        self.symbol_rate = symbol_rate_hz
        self.min_spc = min_samples_per_cycle
        self.sps = self.mod.samples_per_carrier_cycle(symbol_rate_hz,
                                                      min_samples_per_cycle)
        self.fs = self.mod.sample_rate_for(symbol_rate_hz, min_samples_per_cycle)

    def minimum_record(self, occupied_hz: float, bins_wanted: int = 8) -> int:
        """samples needed so the DFT has `bins_wanted` bins across the
        occupied band. Measurement resolution is a design constraint,
        not an afterthought."""
        return max(64, int(self.fs * bins_wanted / max(occupied_hz, 1.0)))

    def run(self, bits: Sequence[int], noise_sigma: float = 0.0,
            rng: Optional[random.Random] = None,
            repeat: int = 8) -> Dict:
        """repeat the symbol stream so the record spans several bins of
        the occupied band. A single short burst cannot be spectrally
        resolved; repetition is the standard fix and is what a
        continuous transmission actually looks like."""
        rng = rng or random.Random(0)
        stream = list(bits) * max(1, repeat)
        tx = self.mod.transmit(stream, self.symbol_rate)

        rx = add_noise(tx, noise_sigma, rng) if noise_sigma > 0 else list(tx)

        rc = RaisedCosine(self.symbol_rate, scheme=self.mod.scheme)
        half = rc.one_sided_bandwidth_hz()
        bp = BandPass(self.carrier.freq_hz - half,
                      self.carrier.freq_hz + half, self.fs)
        kept = bp.keep_fraction(rx) if bp.resolvable(len(rx)) else None

        demod = CoherentDemodulator(self.carrier.freq_hz, self.fs,
                                    self.symbol_rate)
        baseband = demod.demodulate(rx)

        guard = NyquistGuard(rc.null_to_null_hz(), self.fs)
        return {
            "bits": list(stream),
            "repeat": repeat,
            "record_samples": len(tx),
            "carrier_hz": self.carrier.freq_hz,
            "symbol_rate_hz": self.symbol_rate,
            "samples_per_symbol": self.sps,
            "samples_per_carrier_cycle": round(self.fs / self.carrier.freq_hz, 3),
            "sample_rate_hz": self.fs,
            "occupied_bandwidth_hz": rc.null_to_null_hz(),
            "nyquist_ok": guard.ok(),
            "nyquist_required_hz": guard.required_rate(),
            "bandpass_energy_kept": round(kept, 6) if kept is not None else None,
            "baseband_rms": round(
                math.sqrt(sum(v * v for v in baseband) / max(len(baseband), 1)), 6),
        }


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: chain | nyquist | bandpass | psk | noise | verdict")
        return 0

    if argv[0] == "chain":
        c = SignalChain(1e6, 1e3, "qpsk")
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        print(json.dumps(c.run(bits), indent=2))
        return 0

    if argv[0] == "bandwidth":
        print("occupied bandwidth, DERIVED from the constellation")
        for scheme in ("bpsk", "qpsk"):
            print(f"\n{scheme.upper()} at Rs = 1000 sym/s (Rb = "
                  f"{'2000' if scheme=='qpsk' else '1000'} bit/s):")
            print(f"  {'alpha':>6} {'one-sided':>12} {'null-to-null':>13} "
                  f"{'min fs':>10} {'pulse':>8}")
            for a in (0.0, RaisedCosine.ALPHA_NTSC,
                      RaisedCosine.ALPHA_SHORT, RaisedCosine.ALPHA_SINC):
                rc = RaisedCosine(1000.0, scheme, a)
                print(f"  {a:>6} {rc.one_sided_bandwidth_hz():>12.1f} "
                      f"{rc.null_to_null_hz():>13.1f} "
                      f"{rc.min_nyquist_rate_hz():>10.1f} "
                      f"{rc.pulse_length_s():>8.2f}")
        print("\nalpha=0.22 is RS-170/NTSC and GSM/GPRS -- the standard.")
        print("alpha=0 is the theoretical minimum but needs infinite time.")
        return 0

    if argv[0] == "nyquist":
        print("the constraint that will bite")
        print(f"{'carrier':>12} {'bandwidth':>12} {'fs':>14} {'ok':>6} {'alias':>14}")
        cases = [
            (1e3, 1e3, 1e5), (1e6, 1e3, 1e7), (1e9, 1e3, 1e10),
            (1e12, 1e3, 1e13), (1e12, 1e12, 1e13),
        ]
        for fc, bw, fs in cases:
            g = NyquistGuard(bw, fs)
            print(f"{fc:>12.0e} {bw:>12.0e} {fs:>14.0e} "
                  f"{str(g.ok()):>6} {g.alias_frequency(fc):>14.3e}")
        print("\na 1 THz carrier sampled at 1 THz aliases to ~0:")
        print("high carrier + low information + demodulate down is the only")
        print("path that works, exactly as in any radio.")
        return 0

    if argv[0] == "bandpass":
        c = SignalChain(1e6, 1e3, "qpsk")
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        tx = c.mod.transmit(bits, c.symbol_rate, c.sps)
        print("fraction of spectral energy inside the carrier band")
        for lo, hi in [(0.0, 1e6), (0.4e6, 1.6e6), (0.9e6, 1.1e6),
                       (2e6, 3e6)]:
            bp = BandPass(lo, hi, c.fs)
            print(f"  {lo/1e6:5.2f}-{hi/1e6:5.2f} MHz  "
                  f"{bp.keep_fraction(tx)*100:6.2f}%")
        print("\nenergy belongs where the carrier is. that is the whole")
        print("argument for modulating: it moves signal out of the DC")
        print("band where the substrate's own noise lives.")
        return 0

    if argv[0] == "psk":
        for scheme in ("bpsk", "qpsk"):
            c = Carrier(1e6)
            m = PSKModulator(c, scheme)
            bits = [1, 0, 1, 0] if scheme == "bpsk" else [1, 0, 1, 1, 0, 0, 1, 0]
            ph = m.encode(bits)
            back = m.decode(ph)
            print(f"{scheme}: {len(bits)} bits -> {len(ph)} symbols -> "
                  f"round trip {'OK' if back == bits else 'FAIL'}")
        print("\nfor phase noise:")
        m = PSKModulator(Carrier(1e6), "qpsk")
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        for noise in (0.0, 0.1, 0.2, 0.3, 0.5, 0.8):
            got = m.decode(m.encode(bits), noise=noise)
            errs = sum(1 for a, b in zip(bits, got) if a != b)
            print(f"  sigma={noise:4} rad -> {errs}/{len(bits)} bit errors")
        return 0

    if argv[0] == "noise":
        c = SignalChain(1e6, 1e3, "qpsk")
        bits = [1, 0, 1, 1, 0, 0, 1, 0] * 8
        print("received baseband RMS vs channel noise")
        for sigma in (0.0, 0.05, 0.1, 0.25, 0.5):
            r = c.run(bits, noise_sigma=sigma)
            print(f"  sigma={sigma:5}  baseband_rms={r['baseband_rms']:.4f}  "
                  f"band_kept={r['bandpass_energy_kept']:.4f}")
        return 0

    if argv[0] == "verdict":
        print("=== the chain, established at every stage ===")
        for stage, what in [
            ("carrier", "A cos(2 pi f t + phi), constant envelope"),
            ("modulation", "PSK/QPSK -- information IS the phase"),
            ("channel", "balanced 3-phase braid (stalk_carrier)"),
            ("noise", "in-band only; that is where it hurts"),
            ("bandpass", "keep f_c +/- B, reject the rest"),
            ("mixing", "multiply by carrier conjugate"),
            ("lowpass", "remove the 2 f_c image"),
            ("sampling", "Nyquist: fs > 2B or alias"),
        ]:
            print(f"  {stage:10} {what}")
        print("\nthe carrier's absolute frequency carries nothing.")
        print("the beat period depends only on the DIFFERENCE.")
        print("what frequency buys is spectral separation -- getting")
        print("information out of the band where the substrate's noise is.")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))