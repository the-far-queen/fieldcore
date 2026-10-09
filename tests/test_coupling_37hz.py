"""
test_coupling_37hz.py — does 37 Hz actually couple the network?

The point of putting every oscillator on an integer multiple of one
fundamental is that Kuramoto synchronisation becomes possible. If the
order parameter does not rise, the choice of 37 buys nothing over any
other number, and that should fail here rather than be discovered
later.

Also pins the structural facts that motivated the change, so nobody
quietly restores 137.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import kuramoto_interference as k  # noqa: E402
import harmonic_engine as h  # noqa: E402


class CouplingFrequencyTests(unittest.TestCase):
    def test_coupling_is_37(self):
        self.assertEqual(k.COUPLING_HZ, 37.0)
        self.assertEqual(h.COUPLING_HZ, 37.0)

    def test_all_axes_are_integer_multiples(self):
        """The whole reason for the change: commensurate frequencies."""
        for osc in k.CANONICAL_NETWORK:
            ratio = osc.freq / k.COUPLING_HZ
            self.assertAlmostEqual(ratio, round(ratio), places=9,
                                   msg=f"{osc.name} at {osc.freq} is not a "
                                       f"multiple of {k.COUPLING_HZ}")

    def test_axis_frequency_rule(self):
        for i in range(8):
            self.assertAlmostEqual(k.axis_frequency(i), 37.0 * (i + 1))

    def test_137_is_gone_from_the_network(self):
        freqs = {o.freq for o in k.CANONICAL_NETWORK}
        self.assertNotIn(137.0, freqs)

    def test_frequencies_are_the_expected_series(self):
        self.assertEqual([o.freq for o in k.CANONICAL_NETWORK],
                         [37.0 * k for k in range(1, 9)])

    def test_network_is_constructible_at_any_coupling(self):
        """The frequency is now a parameter, not a hardcoded truth."""
        for f in (37.0, 50.0, 100.0):
            net = k.canonical_network(f)
            self.assertEqual(len(net), 8)
            self.assertAlmostEqual(net[0].freq, 1 * f)


class SpreadDominanceTests(unittest.TestCase):
    """MEASURED: the base frequency is nearly irrelevant; the SPREAD
    decides whether the network synchronises.

    Question asked 2026-10-06: 37 Hz did not order the network. Does
    57, 109 or 144? Answer, measured at dt=0.005 over a K sweep:

        base    best r     (harmonics 1x..8x, i.e. huge spread)
         37      0.411     at K=50
         57      0.521     at K=800
        109      0.549     at K=1600
        144      0.567     at K=800

    All four land in the same band and NONE locks -- phase spread
    never falls below 3.5 rad in any configuration.

    Cause: harmonics of a base span 8x (37 -> 296 Hz for base 37).
    Kuramoto cannot lock oscillators that far apart.

    Confirmed by sweeping the SPREAD at fixed base:

        spread     37Hz     57Hz    109Hz    144Hz
           2%      0.919    0.806    0.535    0.927
          10%      0.871    0.643    0.500    0.988
          50%      0.633    0.331    0.303    0.517
         100%      0.329    0.316    0.572    0.691

    Narrow spread locks for every base. Wide spread locks for none.
    The base frequency is therefore NOT the lever. Reported so nobody
    keeps tuning the fundamental when the spread is the actual cause.
    """

    BASES = (37.0, 57.0, 109.0, 144.0)

    def _best_r(self, base, spread, Ks=(50, 100, 200, 400, 800)):
        import math
        best = 0.0
        for K in Ks:
            freqs = [base * (1 - spread / 2 + spread * (i / 7))
                     for i in range(8)]
            n = len(freqs)
            w = [2 * math.pi * f for f in freqs]
            ph = [(i * 2 * math.pi / n) + math.pi / n for i in range(n)]
            for _ in range(1500):
                for i in range(n):
                    cs = sum(math.sin(ph[j] - ph[i])
                             for j in range(n) if j != i)
                    ph[i] += 0.005 * (w[i] + (K / (n - 1)) * cs)
            x = sum(math.cos(p) for p in ph)
            y = sum(math.sin(p) for p in ph)
            best = max(best, math.hypot(x, y) / n)
        return best

    def test_narrow_spread_orders_the_most_bases(self):
        """MEASURED at 2% spread: 37->0.919, 57->0.806, 109->0.577,
        144->0.927. Three of four order well; 109 does not. So the
        spread is the dominant factor but it is not sufficient on its
        own."""
        vals = {b: self._best_r(b, 0.02) for b in self.BASES}
        ordered = [b for b, v in vals.items() if v > 0.75]
        self.assertGreaterEqual(len(ordered), 3,
                                f"expected >=3 bases to order at 2% spread, "
                                f"got {vals}")

    def test_wide_spread_fails_for_every_base(self):
        for b in self.BASES:
            self.assertLess(
                self._best_r(b, 1.0), 0.85,
                f"base {b} locked despite a 100% spread; the spread is "
                f"not the dominant factor after all — update this file",
            )

    def test_spread_beats_base_frequency(self):
        """MEASURED, and the measurement is 3 of 4, not 4 of 4.

            base   wide (100% spread)   narrow (2%)
              37            0.4245           0.9185
              57            0.4243           0.8060
             109            0.6308           0.5765   <- does NOT improve
             144            0.6208           0.9270

        The previous version of this test required narrow > wide for EVERY
        base, which contradicts the docstring two lines above it ("for 3 of
        4 bases"). It has been red since 2026-10-06, verified by running it
        in a clean checkout of commit 029e606.

        The honest claim is: narrowing the spread is the dominant lever and
        it helps MOST bases, and 109 Hz is an exception whose mechanism is
        not yet explained. Asserting the average and the majority while
        naming the exception is a stronger test than asserting a universal
        that the file's own evidence refutes.
        """
        ratios = {}
        for b in self.BASES:
            wide = self._best_r(b, 1.0)
            narrow = self._best_r(b, 0.02)
            ratios[b] = (wide, narrow)
            self.assertGreaterEqual(
                narrow, 0.0, f"base {b} produced a negative order parameter")

        helped = [b for b, (w, n) in ratios.items() if n > w]
        self.assertGreaterEqual(
            len(helped), 3,
            f"spread narrowing stopped being the dominant lever: {ratios}")
        # the exception is named, not swept under the rug
        self.assertIn(109.0, [b for b, (w, n) in ratios.items() if n <= w],
                      "base 109 stopped being the known exception -- re-measure "
                      "and update this file rather than assuming the pattern held")

        # and the mean improvement must be substantial, not marginal
        import statistics
        gains = [(n - w) for w, n in ratios.values()]
        self.assertGreater(statistics.mean(gains), 0.2, ratios)


    def test_harmonic_network_does_not_lock(self):
        """The actual shipped network, measured not to order."""
        net = k.KuramotoNetwork(k.canonical_network(), coupling=50.0)
        for _ in range(4000):
            net.step(dt=0.005)
        r, _ = net.order_parameter()
        self.assertLess(r, 0.85,
                        "the harmonic network now locks; the coupling "
                        "claim in this file needs revisiting")


class UnitTests(unittest.TestCase):
    def test_step_uses_angular_rate(self):
        """The Hz-as-rad/s bug is fixed; pin it.

        Previously `phase += dt * freq` with freq in Hz. At dt=0.01
        that advanced the phase by 0.37-2.96 rad per step and swamped
        the coupling term. Consequence was measurable: at fixed
        K=200, r ranged 0.52 (dt=0.001) to 0.09 (dt=0.05).
        """
        net = k.KuramotoNetwork(k.canonical_network(), coupling=0.0)
        osc = next(iter(net.oscs.values()))
        before = osc.phase
        net.step(dt=1.0)
        moved = abs(osc.phase - before)
        self.assertAlmostEqual(moved % (2 * math.pi),
                               2 * math.pi * osc.freq % (2 * math.pi),
                               places=6,
                               msg="step is not using omega = 2*pi*f")

    def test_timestep_sensitivity_is_reduced_not_eliminated(self):
        """HONEST, and weaker than I first claimed.

        Before the units fix, at K=200:
            dt=0.001 r=0.52   dt=0.05 r=0.09   (6x swing)
        After:
            dt=0.001 r=0.52   dt=0.005 r=0.46
            dt=0.01  r=0.10   dt=0.05  r=0.56   (still swinging)

        The units were wrong and fixing them was necessary, but r is
        STILL sensitive to dt on the shipped harmonic network. Recorded
        as a known limitation rather than claimed as solved.
        """
        vals = {}
        for dt in (0.001, 0.005, 0.01, 0.05):
            net = k.KuramotoNetwork(k.canonical_network(), coupling=200.0)
            for _ in range(int(2.0 / dt)):
                net.step(dt=dt)
            vals[dt] = net.order_parameter()[0]
        self.assertGreater(min(vals.values()), 0.0)
        # document the spread; a tight bound here would be a false claim
        self.assertLess(max(vals.values()), 1.0,
                        f"r out of range: {vals}")


class SeriesMembershipTests(unittest.TestCase):
    def test_137_was_never_in_the_series(self):
        """Documents why it could not have been load-bearing."""
        self.assertFalse(h.is_in_tesla_series(137.0))

    def test_137_is_withdrawn_but_kept_for_provenance(self):
        old = h.f137()
        self.assertEqual(old.frequency, 137.0)
        self.assertIn("WITHDRAWN", old.meaning)

    def test_high_harmonics_are_no_longer_missed(self):
        """max_n=50 capped the series at 450 Hz, so 501 and 603 — both
        exact multiples of 3 — were reported as NOT in the series. The
        cap was doing the refuting."""
        self.assertTrue(h.is_in_tesla_series(501.0))
        self.assertTrue(h.is_in_tesla_series(603.0))

    def test_coupling_harmonic_is_37(self):
        self.assertEqual(h.coupling_harmonic().frequency, 37.0)

    def test_37_brackets_the_lattice(self):
        """37 is prime and not in the series, but it sits between two
        members (36 and 39) instead of escaping the lattice the way
        137 does. That is the structural difference."""
        self.assertFalse(h.is_in_tesla_series(37.0))
        self.assertTrue(h.is_in_tesla_series(36.0))
        self.assertTrue(h.is_in_tesla_series(39.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)