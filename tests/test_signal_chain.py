"""
test_signal_chain.py — the DSP, and the guards that catch silent failure.

The bugs this file exists to prevent, all found today:

  1. a carrier aliased because the sample rate came from the symbol grid
  2. an O(n^2) DFT that made every run take hours and return nothing
  3. a bandpass reporting 0.0 when the record was too short to resolve
     the band at all

So the tests assert the GUARDS, not just the outputs.

Run: python -m pytest tests/test_signal_chain.py
"""

from __future__ import annotations

import math
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from signal_chain import (  # noqa: E402
    Carrier,
    PSKModulator,
    RaisedCosine,
    BandPass,
    CoherentDemodulator,
    NyquistGuard,
    SignalChain,
)


class RaisedCosineTests(unittest.TestCase):
    def test_bandwidth_is_derived_from_bit_rate(self):
        """QPSK carries 2 bits/symbol, so Rb = 2*Rs and the occupied
        bandwidth follows. NOT a typed band."""
        rc = RaisedCosine(1000.0, "qpsk")
        self.assertEqual(rc.bit_rate_hz(), 2000.0)
        self.assertAlmostEqual(rc.one_sided_bandwidth_hz(),
                               0.5 * 1.22 * 2000.0, places=6)

    def test_bpsk_is_half_of_qpsk_at_the_same_symbol_rate(self):
        b = RaisedCosine(1000.0, "bpsk")
        q = RaisedCosine(1000.0, "qpsk")
        self.assertAlmostEqual(b.bit_rate_hz() * 2, q.bit_rate_hz())

    def test_rolloff_values_are_standard(self):
        self.assertAlmostEqual(RaisedCosine.ALPHA_NTSC, 0.22)
        self.assertAlmostEqual(RaisedCosine.ALPHA_GPRS, 0.22)

    def test_rolloff_must_be_in_range(self):
        with self.assertRaises(ValueError):
            RaisedCosine(1000.0, "qpsk", alpha=1.5)
        with self.assertRaises(ValueError):
            RaisedCosine(1000.0, "qpsk", alpha=-0.1)

    def test_zero_rolloff_is_the_minimum(self):
        a = RaisedCosine(1000.0, "qpsk", alpha=0.0)
        b = RaisedCosine(1000.0, "qpsk", alpha=1.0)
        self.assertLess(a.null_to_null_hz(), b.null_to_null_hz())

    def test_pulse_length_tracks_rolloff(self):
        self.assertAlmostEqual(RaisedCosine(1000.0, "qpsk", 0.22)
                               .pulse_length_s(), 1.22, places=9)


class ModulatorAliasingTests(unittest.TestCase):
    """REGRESSION: sps came from the symbol grid and silently aliased a
    1 MHz carrier to 24 kHz."""

    def test_sample_rate_resolves_the_carrier(self):
        c = Carrier(1e6)
        m = PSKModulator(c, "qpsk")
        sps = m.samples_per_carrier_cycle(1e3)
        fs = m.sample_rate_for(1e3)
        self.assertGreaterEqual(fs, 2 * c.freq_hz,
                                "sample rate must resolve the CARRIER")
        self.assertGreaterEqual(sps, 2)

    def test_transmit_refuses_an_undersampled_carrier(self):
        """An explicit too-small sps must RAISE, not alias quietly."""
        c = Carrier(1e6)
        m = PSKModulator(c, "bpsk")
        with self.assertRaises(ValueError) as ctx:
            m.transmit([1, 0, 1], 1e3, n_samples_per_symbol=8)
        self.assertIn("alias", str(ctx.exception).lower())

    def test_transmit_uses_the_derived_rate_by_default(self):
        c = Carrier(1e6)
        m = PSKModulator(c, "bpsk")
        tx = m.transmit([1, 0, 1], 1e3)
        sps = m.samples_per_carrier_cycle(1e3)
        self.assertEqual(len(tx), 3 * sps,
                         "3 BPSK symbols at the derived samples-per-symbol")
        self.assertGreaterEqual(len(tx) / 3, 2)

    def test_bit_count_must_match_the_scheme(self):
        m = PSKModulator(Carrier(1e6), "qpsk")
        with self.assertRaises(ValueError):
            m.encode([1, 0, 1], )


class PhaseCodingTests(unittest.TestCase):
    def test_qpsk_round_trip(self):
        m = PSKModulator(Carrier(1e6), "qpsk")
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        self.assertEqual(m.decode(m.encode(bits)), bits)

    def test_bpsk_round_trip(self):
        m = PSKModulator(Carrier(1e6), "bpsk")
        bits = [1, 0, 0, 1, 1]
        self.assertEqual(m.decode(m.encode(bits)), bits)

    def test_noise_causes_errors(self):
        m = PSKModulator(Carrier(1e6), "qpsk")
        bits = [0, 1] * 40
        self.assertNotEqual(m.decode(m.encode(bits), noise=0.7), bits)

    def test_symbols_are_uniform_as_a_set(self):
        """The SET of phases is 90 degrees apart. The ORDER is Gray-
        coded (0, 90, 270, 180), which is deliberate: adjacent symbols
        then differ by one bit, so a nearest-symbol decision errs by one
        bit rather than two.

        The previous version of this test asserted uniform spacing in
        CYCLE order, which fails on Gray coding. The correct property
        is that the set is uniform and the ordering is Gray.
        """
        q = PSQK = PSKModulator(Carrier(1e6), "qpsk").symbols()
        TAU = 2 * math.pi
        # a 4-ary PSK constellation has pairwise separations of 90 deg
        # (adjacent) or 180 deg (opposite). It does NOT make every pair
        # 90 -- that would be a different (impossible) 4-point set on
        # the circle.
        import itertools
        for i, j in itertools.combinations(range(len(q)), 2):
            d = abs(((q[j] - q[i] + math.pi) % TAU) - math.pi)
            self.assertIn(round(d, 9), (round(math.pi / 2, 9), round(math.pi, 9)),
                          f"pair {i},{j} separated by {d}")
        # and there are exactly 2 points at each separation from any one
        for i in range(len(q)):
            ds = sorted(round(abs(((q[j] - q[i] + math.pi) % TAU) - math.pi), 6)
                        for j in range(len(q)) if j != i)
            self.assertEqual(ds, [round(math.pi / 2, 6), round(math.pi / 2, 6),
                                  round(math.pi, 6)])

    def test_qpsk_is_gray_coded(self):
        q = PSKModulator(Carrier(1e6), "qpsk").symbols()
        order = [int(round(x / (math.pi / 2))) % 4 for x in q]
        # Gray walk: consecutive labels differ in exactly one bit
        for i in range(len(order) - 1):
            diff = order[i] ^ order[i + 1]
            self.assertIn(diff, (1, 2),
                          f"{order[i]} -> {order[i+1]} is not Gray-adjacent")


class NyquistTests(unittest.TestCase):
    def test_margin_below_one_is_refused(self):
        with self.assertRaises(ValueError):
            NyquistGuard(1000.0, 3000.0, margin=0.5)

    def test_required_rate_is_twice_the_bandwidth(self):
        g = NyquistGuard(1000.0, 5000.0, margin=1.0)
        self.assertAlmostEqual(g.required_rate(), 2000.0)

    def test_aliasing_is_reported(self):
        g = NyquistGuard(1000.0, 3000.0)
        self.assertNotAlmostEqual(g.alias_frequency(10_000.0), 10_000.0)


class BandPassResolutionTests(unittest.TestCase):
    """REGRESSION: returned 0.0 when the record could not resolve the
    band, which read as 'the signal is in the wrong place'."""

    def test_refuses_an_unresolvable_record(self):
        bp = BandPass(998_780.0, 1_001_220.0, 4e6)
        with self.assertRaises(ValueError):
            bp.keep_fraction([0.0] * 64)     # 64 samples, bin = 62.5 kHz

    def test_resolvable_record_is_accepted(self):
        bp = BandPass(998_780.0, 1_001_220.0, 4e6)
        x = [math.cos(2 * math.pi * 1e6 * (t / 4e6)) for t in range(4096)]
        self.assertTrue(bp.resolvable(4096))
        self.assertGreater(bp.keep_fraction(x), 0.5)


class PerformanceTests(unittest.TestCase):
    """REGRESSION: a naive O(n^2) DFT made the chain take hours and
    return nothing. If numpy is removed again, this fails loudly."""

    def test_chain_completes_quickly(self):
        c = SignalChain(1e6, 1e3, "qpsk")
        t0 = time.time()
        c.run([1, 0, 1, 1, 0, 0, 1, 0])
        self.assertLess(time.time() - t0, 20.0,
                        "the chain took too long; the FFT path is probably gone")


class EndToEndTests(unittest.TestCase):
    def test_chain_reports_a_complete_result(self):
        c = SignalChain(1e6, 1e3, "qpsk")
        r = c.run([1, 0, 1, 1, 0, 0, 1, 0])
        for k in ("record_samples", "samples_per_carrier_cycle",
                  "occupied_bandwidth_hz", "nyquist_ok",
                  "bandpass_energy_kept", "baseband_rms"):
            self.assertIn(k, r)
        self.assertTrue(r["nyquist_ok"])
        self.assertGreater(r["bandpass_energy_kept"], 0.5,
                           "most of the energy should be in the carrier band")

    def test_demodulator_makes_a_carrier(self):
        c = Carrier(1e6)
        fs = 8e6
        x = [c.at(t / fs) for t in range(2048)]
        d = CoherentDemodulator(1e6, fs, 1e3)
        base = d.demodulate(x)
        self.assertTrue(all(math.isfinite(v) for v in base))
        self.assertGreater(max(abs(v) for v in base), 0.1)


if __name__ == "__main__":
    unittest.main(verbosity=2)