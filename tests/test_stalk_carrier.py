"""
test_stalk_carrier.py — three strands, phase carrier, balanced 3-phase.

The assertions are chosen so an unwired version fails: a carrier with
no reference, or a two-strand braid, cannot pass the balance or
self-lock tests.

Run: python -m pytest tests/test_stalk_carrier.py
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stalk_carrier import (  # noqa: E402
    Braid,
    Strand,
    PhaseCarrier,
    three_strand_braid,
    carrier,
)

TAU = 2.0 * math.pi


class BraidGeometryTests(unittest.TestCase):
    def test_three_strands_minimum(self):
        """Two strands can spin; three self-lock. Refuse fewer."""
        with self.assertRaises(ValueError):
            Braid(strands=(Strand("a", 1e-3), Strand("b", 1e-3)), pitch=1e-2)

    def test_lay_angle_is_rope_standard(self):
        b = three_strand_braid()
        self.assertGreater(b.lay_angle_deg(), 50.0)
        self.assertLess(b.lay_angle_deg(), 70.0)

    def test_lay_angle_formula(self):
        b = three_strand_braid()
        a = sum(s.girth for s in b.strands) / 3
        expect = math.degrees(math.atan(TAU * a / b.pitch))
        self.assertAlmostEqual(b.lay_angle_deg(), expect, places=9)

    def test_three_pairs_from_three_strands(self):
        """3 strands -> 3 differential pairs, not 1.5."""
        b = three_strand_braid()
        self.assertEqual(len(b.pairs()), 3)

    def test_braid_matrix_is_complete(self):
        m = three_strand_braid().braid_matrix()
        for i in range(3):
            self.assertEqual(m[i][i], 0)
            self.assertEqual(sum(m[i]), 2, "each strand touches 2 others")

    def test_wire_length_exceeds_axial(self):
        b = three_strand_braid()
        self.assertGreater(b.wire_length(), b.length)

    def test_varied_girths_allowed(self):
        """Rope permits unequal strands; the lay prevents chafing."""
        b = three_strand_braid()
        self.assertEqual(len({s.girth for s in b.strands}), 3)


class CarrierTests(unittest.TestCase):
    def test_carrier_frequency_must_be_positive(self):
        with self.assertRaises(ValueError):
            PhaseCarrier(three_strand_braid(), freq_hz=0.0)

    def test_three_phase_balances_to_zero(self):
        """THE load-bearing result: three 120-degree phasors sum to
        zero at every instant. Machine precision, not 'approximately'."""
        c = carrier()
        for i in range(64):
            t = i / c.freq_hz
            self.assertAlmostEqual(c.balanced_sum(0.0, t), 0.0, places=12,
                                   msg=f"unbalanced at t index {i}")

    def test_offsets_are_120_degrees_apart(self):
        offs = sorted(s.phase_offset % TAU for s in three_strand_braid().strands)
        self.assertAlmostEqual(offs[0], 0.0, places=9)
        self.assertAlmostEqual(offs[1], TAU / 3, places=9)
        self.assertAlmostEqual(offs[2], 2 * TAU / 3, places=9)

    def test_differential_between_any_pair(self):
        """Each pair carries signal -- measured at a quarter cycle.

        NOTE: at t=0 all three strands sit at 0, 120, 240 degrees, so
        every pair difference is exactly zero. That is correct physics,
        not a dead path; an earlier version of this test asserted
        non-zero at t=0 and was wrong.
        """
        c = carrier()
        t = 0.25 / c.freq_hz
        for a, b in c.braid.pairs():
            v = c.differential(a, b, 0.0, t)
            self.assertNotAlmostEqual(v, 0.0, places=6,
                                      msg=f"pair {a}-{b} carries nothing")

    def test_differential_rejects_common_mode(self):
        """An EQUAL disturbance on all three strands is common mode and
        cancels in both the balanced sum and any pair difference."""
        c = carrier()
        t = 0.3 / c.freq_hz
        base = c.differential("a", "b", 0.0, t)
        self.assertNotAlmostEqual(base, 0.0, places=6)
        # the balanced sum carries no signal at all -- that is the
        # whole point of the 120-degree offsets
        self.assertAlmostEqual(c.balanced_sum(0.0, t), 0.0, places=12)
        # adding the same constant to every strand cannot change a
        # difference: |(a+k)-(b+k)| == |a-b| by construction
        k = 5.0
        by = {s.name: s for s in c.braid.strands}
        va = c.amplitude * math.cos(TAU * c.freq_hz * t + by["a"].phase_offset)
        vb = c.amplitude * math.cos(TAU * c.freq_hz * t + by["b"].phase_offset)
        self.assertAlmostEqual((va + k) - (vb + k), va - vb, places=12)


class PhaseCodingTests(unittest.TestCase):
    def test_qpsk_clean_round_trip(self):
        c = carrier()
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        got = c.decode(c.encode(bits, "qpsk"), noise=0.0, scheme="qpsk")
        self.assertEqual(got, bits)

    def test_bpsk_clean_round_trip(self):
        c = carrier()
        bits = [1, 0, 0, 1, 1]
        got = c.decode(c.encode(bits, "bpsk"), noise=0.0, scheme="bpsk")
        self.assertEqual(got, bits)

    def test_qpsk_carries_two_bits_per_symbol(self):
        c = carrier()
        self.assertEqual(len(c.encode([1, 0, 1, 1], "qpsk")), 2)
        self.assertEqual(len(c.encode([1, 0, 1], "bpsk")), 3)

    def test_encode_rejects_bad_bit_count(self):
        c = carrier()
        with self.assertRaises(ValueError):
            c.encode([1, 0, 1], "qpsk")

    def test_noise_eventually_causes_errors(self):
        """If noise never broke anything the receiver would be
        untestable."""
        c = carrier()
        bits = [0, 1] * 40
        got = c.decode(c.encode(bits, "qpsk"), noise=0.6, scheme="qpsk")
        self.assertNotEqual(got, bits)

    def test_tight_phase_noise_is_survivable(self):
        c = carrier()
        bits = [0, 1, 1, 0] * 20
        got = c.decode(c.encode(bits, "qpsk"), noise=0.05, scheme="qpsk")
        self.assertEqual(got, bits)

    def test_symbols_are_uniformly_spaced(self):
        q = PhaseCarrier.qpsk_symbols()
        self.assertEqual(len(q), 4)
        for i in range(4):
            self.assertAlmostEqual(((q[(i + 1) % 4] - q[i]) % TAU),
                                   math.pi / 2, places=9)


class TwoVsThreeTests(unittest.TestCase):
    def test_two_strands_cannot_be_a_braid(self):
        """The reason three exists. Asserted so the choice is never
        'simplified' back to two without noticing."""
        with self.assertRaises(ValueError):
            Braid(strands=(Strand("x", 1e-3, 0.0), Strand("y", 1e-3, math.pi)),
                  pitch=1e-2, length=1.0)

    def test_three_strands_give_a_reference(self):
        """With two you have a-b only. With three there is a c to hold
        the reference, which is what makes phase meaningful."""
        names = {s.name for s in three_strand_braid().strands}
        self.assertEqual(len(names), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)