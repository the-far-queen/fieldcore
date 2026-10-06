"""
test_control_metrics.py — a specification you can FAIL.

The point of control metrics is that they produce PASS/FAIL. These
tests assert the metrics are correct AND that the spec genuinely
discriminates — a spec everything passes is as useless as a test that
cannot fail.

Run: python -m pytest tests/test_control_metrics.py
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from control_metrics import (  # noqa: E402
    StepResponse,
    Spec,
    displaced_trajectory,
    record_trajectory,
    damping_agreement,
    concave_settling_budget,
    CONCAVE_SPEC,
    evaluate_concave,
    evaluate_bumped,
)


class StepResponseTests(unittest.TestCase):
    def test_empty_and_tiny(self):
        r = StepResponse([0.0], [0.0])
        self.assertEqual(r.final(), 0.0)
        self.assertEqual(r.peak(), 0.0)
        self.assertEqual(r.local_peaks(), [])

    def test_local_peaks_finds_the_oscillations(self):
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        pk = r.local_peaks()
        self.assertGreater(len(pk), 4, "expected several oscillation peaks")

    def test_peaks_decay(self):
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        pk = [v for _, v in r.local_peaks() if v > 1e-9]
        self.assertEqual(pk, sorted(pk, reverse=True),
                         "peak amplitudes must decrease")

    def test_settling_time_uses_a_scale_not_the_reference(self):
        """REGRESSION: the first version banded around the FINAL value.
        For a ball settling at the origin the reference is 0, the band
        collapses to zero width, and the metric reports 'never settled'
        no matter how small the residual."""
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        st = r.settling_time()
        self.assertLess(st, r.t[-1],
                        "reported as still outside the band at the last "
                        "sample, which is the zero-width-band bug")
        self.assertGreater(st, 0.0)

    def test_overshoot_is_finite_at_zero_reference(self):
        """REGRESSION: dividing by a zero reference returned inf, which
        failed the spec for a system that never overshoots."""
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        self.assertTrue(math.isfinite(r.overshoot_percent(reference=0.0)))

    def test_steady_state_error_at_the_end(self):
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        self.assertLess(r.steady_state_error(0.0), 0.01)


class DampingRecoveryTests(unittest.TestCase):
    """The load-bearing check: recover the damping from the trajectory
    by a method that never sees the input."""

    def test_damping_recovered_from_decay(self):
        for d in (0.2, 0.35, 0.7, 1.0):
            r = damping_agreement(damping=d)
            self.assertTrue(r["agrees"],
                            f"damping {d}: recovered "
                            f"{r['damping_from_decay']} rel err "
                            f"{r['relative_error']}")
            self.assertLess(r["relative_error"], 0.01)

    def test_two_methods_are_independent(self):
        """the measured value must not be the input echoed back."""
        r = damping_agreement(damping=0.7)
        self.assertNotAlmostEqual(r["damping_from_decay"],
                                  r["damping_input"], places=6,
                                  msg="recovery is suspiciously exact")

    def test_zeta_identity_holds(self):
        r = damping_agreement(damping=0.35, gravity=1.0)
        self.assertAlmostEqual(r["zeta_analytic"], 0.35 / 2.0, places=9)

    def test_overshoot_identity_would_fail_but_decay_does_not(self):
        """A ball released from rest never overshoots, so the classical
        overshoot identity is inapplicable here.

        Asserted BEHAVIOURALLY rather than by reading the method string:
        the overshoot route returns 0.0, the decay route recovers the
        true value. An earlier version of this test checked the wording
        of a docstring and passed for the wrong reason.
        """
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        # the inapplicable route reports ZERO damping for a ball whose
        # initial displacement IS its peak. Measured, not assumed:
        # peak == y[0] so overshoot is exactly 100%, and the identity
        # maps 100% to zeta = 0. It looks like a clean answer, not an
        # error, which is why it has to be caught by comparing against
        # the value we know is true.
        self.assertAlmostEqual(r.overshoot_percent(reference=0.0), 100.0,
                               places=6)
        self.assertAlmostEqual(r.damping_from_overshoot(), 0.0, places=9)
        # the applicable route recovers the truth
        self.assertAlmostEqual(r.damping_from_decay(), 0.35, delta=0.01)


class SpecTests(unittest.TestCase):
    def test_concave_spec_passes(self):
        v = evaluate_concave()["verdict"]
        self.assertTrue(v["passed"], f"concave spec failed: {v}")

    def test_spec_can_fail(self):
        """A spec everything passes is as useless as a test that cannot
        fail. This one must reject an impossible budget."""
        impossible = Spec("impossible", max_settling_time=0.001,
                          max_overshoot_pct=0.0,
                          max_steady_state_error=0.0)
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        self.assertFalse(impossible.evaluate(r, 0.0)["passed"])

    def test_settling_budget_is_derived(self):
        b = concave_settling_budget()
        self.assertGreater(b, 0)
        # envelope term plus half a period
        envelope = 2 * math.log(2.0 / 0.02) / 0.35
        half_period = math.pi / math.sqrt(1 - (0.35 / 2) ** 2)
        self.assertAlmostEqual(b, envelope + half_period, places=6)

    def test_concave_budget_exceeds_measured(self):
        r = displaced_trajectory(2.0, damping=0.35, steps=12000)
        self.assertGreater(CONCAVE_SPEC.max_settling_time,
                           r.settling_time())


class BumpedSpecTests(unittest.TestCase):
    def test_bumped_spec_does_not_demand_the_global_minimum(self):
        """The honest spec is 'settles stably'. Which basin is REPORTED,
        not required -- because basin_landscape.py measured that the
        basin depends on the initial condition."""
        import basin_landscape as bl
        out = evaluate_bumped(bl.one_bump().tilt)
        self.assertIn("SOMEWHERE", out["verdict"]["spec"])
        self.assertIn("not assumed", out["note"])
        self.assertIn("settled_at", out)

    def test_bumped_response_still_settles(self):
        import basin_landscape as bl
        out = evaluate_bumped(bl.one_bump().tilt)
        self.assertLess(out["trajectory"]["steady_state_error"], 0.01)


if __name__ == "__main__":
    unittest.main(verbosity=2)