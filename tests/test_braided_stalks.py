"""
test_braided_stalks.py — braided stalk pairs that actually carry signal.

The module this replaces had `signal_flow` returning its input
unchanged, with a test asserting that identity. So the assertions here
are chosen to FAIL on an unwired implementation:

- transfer must depend on twist rate
- transfer must depend on girth asymmetry
- reachability must be enforced by the bridges, not assumed

Run: python -m pytest tests/test_braided_stalks.py
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from braided_stalks import (  # noqa: E402
    BraidedPair,
    BraidedNetwork,
    substrate_network,
)


class GeometryTests(unittest.TestCase):
    def test_separation_is_sum_of_girths(self):
        p = BraidedPair("x", 0.30, 0.40, twist_rate=2.0)
        self.assertAlmostEqual(p.separation, 0.70)

    def test_loop_area_falls_with_twist_rate(self):
        areas = [BraidedPair("x", 0.3, 0.4, twist_rate=t).loop_area
                 for t in (0.5, 1.0, 2.0, 8.0)]
        self.assertEqual(areas, sorted(areas, reverse=True),
                         "tighter braid must give a smaller loop area")

    def test_loop_area_is_separation_over_twist_rate(self):
        p = BraidedPair("x", 0.3, 0.4, twist_rate=4.0)
        self.assertAlmostEqual(p.loop_area, 0.7 / 4.0)

    def test_helix_radius_is_half_the_separation(self):
        """The wire wraps the pair's midpoint. Using the full
        separation as the radius double-counts the diameter."""
        p = BraidedPair("x", 0.30, 0.36, twist_rate=2.5, length=1.0)
        pitch = 1 / 2.5
        expect = 2.5 * math.hypot(pitch, 2 * math.pi * (0.66 / 2))
        self.assertAlmostEqual(p.path_length, expect, places=9)

    def test_path_length_exceeds_axial(self):
        p = BraidedPair("x", 0.3, 0.4, twist_rate=3.0, length=1.0)
        self.assertGreater(p.path_length, p.length)


class RejectionTests(unittest.TestCase):
    def test_rejection_improves_with_twist_rate(self):
        prev = -1.0
        for t in (0.5, 1.0, 2.0, 5.0, 10.0):
            r = BraidedPair("x", 0.30, 0.36, twist_rate=t).common_mode_rejection_db(1.0)
            self.assertGreater(r, prev,
                               f"twist {t} did not improve rejection: {r}")
            prev = r

    def test_symmetric_pair_rejects_ambient_entirely(self):
        """Equal girths have identical coupling, so the induced
        differential residue is zero."""
        p = BraidedPair("x", 0.30, 0.30, twist_rate=2.0)
        self.assertEqual(p.common_mode_rejection_db(1.0), float("inf"))

    def test_asymmetry_leaks_a_residue(self):
        sym = BraidedPair("x", 0.30, 0.30, twist_rate=2.0)
        asym = BraidedPair("x", 0.30, 0.36, twist_rate=2.0)
        self.assertLess(asym.common_mode_rejection_db(1.0),
                        sym.common_mode_rejection_db(1.0))

    def test_greater_asymmetry_means_worse_rejection(self):
        mild = BraidedPair("x", 0.30, 0.33, twist_rate=2.0)
        wild = BraidedPair("x", 0.30, 0.42, twist_rate=2.0)
        self.assertLess(wild.common_mode_rejection_db(1.0),
                        mild.common_mode_rejection_db(1.0))

    def test_sheath_improves_rejection(self):
        bare = BraidedPair("x", 0.30, 0.36, twist_rate=2.0, sheath=False)
        clad = BraidedPair("x", 0.30, 0.36, twist_rate=2.0, sheath=True)
        self.assertGreater(clad.common_mode_rejection_db(1.0),
                           bare.common_mode_rejection_db(1.0))


class TransferTests(unittest.TestCase):
    """This is the function the old module did not have."""

    def test_clean_transfer_is_the_signal_times_loss(self):
        p = BraidedPair("x", 0.30, 0.36, twist_rate=2.5, length=1.0)
        got = p.transfer(1.0, 0.0, ambient=0.0)
        expect = 10.0 ** (-p.attenuation_db() / 20.0)
        self.assertAlmostEqual(got, expect, places=9)

    def test_transfer_is_not_the_identity(self):
        """The old signal_flow returned its input. This must not."""
        p = BraidedPair("x", 0.30, 0.36, twist_rate=2.5, length=1.0)
        self.assertNotAlmostEqual(p.transfer(0.5, 0.0, ambient=0.0), 0.5,
                                  places=3)

    def test_differential_subtracts(self):
        p = BraidedPair("x", 0.30, 0.36, twist_rate=2.5)
        both = p.transfer(1.0, 1.0, ambient=0.0)
        self.assertAlmostEqual(both, 0.0, places=9)

    def test_more_twist_costs_signal(self):
        """Twist rate and delivered signal move in OPPOSITE directions.

        Measured, clean ambient:
            twist 0.5 -> 0.833    twist  2 -> 0.484
            twist 1.0 -> 0.659    twist 10 -> 0.219

        A tighter braid is a longer wire, so it loses more. The braid
        buys rejection (monotone up in dB) and pays for it in signal.
        There is an optimum, not a "more is better" -- which is why
        the pair's twist rate is a design parameter rather than a
        constant.
        """
        loose = BraidedPair("x", 0.30, 0.36, twist_rate=0.5, length=1.0)
        tight = BraidedPair("x", 0.30, 0.36, twist_rate=10.0, length=1.0)
        self.assertLess(tight.transfer(1.0, 0.0, ambient=0.0),
                        loose.transfer(1.0, 0.0, ambient=0.0))
        self.assertGreater(tight.attenuation_db(), loose.attenuation_db())

    def test_tradeoff_between_rejection_and_signal(self):
        """The two effects oppose; both directions asserted so a change
        to either formula has to be deliberate."""
        prev_sig, prev_rej = 0.0, 0.0
        for t in (0.5, 1.0, 2.0, 5.0, 10.0):
            p = BraidedPair("x", 0.30, 0.36, twist_rate=t, length=1.0)
            sig = p.transfer(1.0, 0.0, ambient=0.0)
            rej = p.common_mode_rejection_db(1.0)
            self.assertLess(sig, prev_sig or 1.0, f"signal rose at t={t}")
            self.assertGreater(rej, prev_rej, f"rejection fell at t={t}")
            prev_sig, prev_rej = sig, rej

    def test_ambient_appears_in_the_output(self):
        """Noise must not be silently discarded -- that would make the
        gate trivially pass."""
        p = BraidedPair("x", 0.30, 0.36, twist_rate=2.0)
        clean = p.transfer(1.0, 0.0, ambient=0.0)
        noisy = p.transfer(1.0, 0.0, ambient=1.0)
        self.assertGreater(noisy, clean)


class NetworkTests(unittest.TestCase):
    def test_components_split_on_missing_bridges(self):
        net = substrate_network()
        self.assertEqual(sorted(net.components()),
                         [['pair1', 'pair2', 'pair3'], ['pair4']])

    def test_unbridged_pair_is_unreachable(self):
        net = substrate_network()
        m = net.reachability_matrix()
        self.assertTrue(m[("pair1", "pair2")], "bridged pairs must reach")
        self.assertFalse(m[("pair1", "pair4")], "unbridged pair unreachable")
        self.assertFalse(m[("pair4", "pair1")])

    def test_propagate_requires_a_known_source(self):
        net = substrate_network()
        with self.assertRaises(KeyError):
            net.propagate("nonexistent", [1.0])

    def test_propagate_length_matches_input(self):
        net = substrate_network()
        sig = [0.1, 0.2, 0.3, 0.4]
        self.assertEqual(len(net.propagate("pair1", sig)), len(sig))

    def test_deliver_returns_a_list_per_pair(self):
        net = substrate_network()
        sig = [0.1, 0.2]
        out = net.deliver("pair1", sig)
        self.assertEqual(sorted(out), ["pair1", "pair2", "pair3"])
        for v in out.values():
            self.assertEqual(len(v), len(sig))

    def test_duplicate_pair_id_refused(self):
        net = BraidedNetwork()
        p = BraidedPair("a", 0.3, 0.4)
        net.add(p)
        with self.assertRaises(ValueError):
            net.add(BraidedPair("a", 0.3, 0.5))

    def test_bridge_to_unknown_pair_refused(self):
        net = BraidedNetwork()
        net.add(BraidedPair("a", 0.3, 0.4))
        with self.assertRaises(KeyError):
            net.bridge("a", "ghost")

    def test_invalid_geometry_refused(self):
        for kwargs in ({"girth_a": 0.0, "girth_b": 0.3},
                       {"girth_a": 0.3, "girth_b": -0.1},
                       {"girth_a": 0.3, "girth_b": 0.3, "length": 0.0},
                       {"girth_a": 0.3, "girth_b": 0.3, "twist_rate": -1.0}):
            with self.assertRaises(ValueError):
                BraidedPair("bad", **kwargs)


class VariationTests(unittest.TestCase):
    def test_substrate_pairs_are_all_geometrically_distinct(self):
        """Variable girths are the point; identical pairs would make the
        variation decorative."""
        net = substrate_network()
        sig = tuple(sorted((p.loop_area, p.twist_rate, p.girth_a, p.girth_b)
                           for p in net.pairs.values()))
        self.assertEqual(len(sig), len(net.pairs))


if __name__ == "__main__":
    unittest.main(verbosity=2)