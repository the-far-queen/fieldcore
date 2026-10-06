"""
test_geometric_ball.py — the ball finds the origin, and does not.

The claim under test is narrow and falsifiable:

  A ball rolling on a CONCAVE height field reaches the origin from
  every starting point, in every dimension, without any inner product.

and the falsification is measured, not asserted:

  Add a bump deep enough to create a second basin and the ball settles
  in the WRONG one.

Run: python -m pytest tests/test_geometric_ball.py
"""

from __future__ import annotations

import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from geometric_ball import (  # noqa: E402
    height,
    local_tilt,
    roll,
    roll_n,
    roll_2d,
    gradient_n_drop,
    universal_drop,
    dimension_independence,
    local_minimum_probe,
)


class NoLinearAlgebraTests(unittest.TestCase):
    """The claim is that the mechanism is geometric. These check the
    primitives are scalar and local."""

    def test_tilt_reads_one_coordinate(self):
        """d/dx(½x²) = x -- depends only on x, not on any other
        coordinate or on a norm across dimensions."""
        self.assertAlmostEqual(local_tilt(3.0), 3.0)
        self.assertAlmostEqual(local_tilt(-2.5), -2.5)
        self.assertAlmostEqual(local_tilt(0.0), 0.0)

    def test_height_is_the_paraboloid(self):
        self.assertAlmostEqual(height(0.0), 0.0)
        self.assertAlmostEqual(height(2.0), 2.0)
        self.assertAlmostEqual(height(-4.0), 8.0)

    def test_tilt_is_the_derivative_of_height(self):
        """finite-difference check against the analytic slope."""
        h = 1e-6
        for x in (0.5, 2.0, -3.0):
            fd = (height(x + h) - height(x - h)) / (2 * h)
            self.assertAlmostEqual(fd, local_tilt(x), places=6)


class UniversalDropTests(unittest.TestCase):
    def test_every_ball_finds_the_hole(self):
        """500 drops from random heights in [-10, 10]. No exceptions."""
        r = universal_drop(500, seed=0)
        self.assertEqual(r["failures"], 0,
                         f"balls failed to converge: {r['failure_examples']}")
        self.assertTrue(r["universal"])

    def test_converges_from_a_great_height(self):
        for x0 in (1.0, 5.0, 10.0, 100.0, -100.0):
            r = roll(x0, steps=20000)
            self.assertLess(abs(r["x"]), 1e-2, f"x0={x0} settled at {r['x']}")

    def test_two_dimensional(self):
        for p in ((1.0, 1.0), (5.0, -3.0), (-7.0, 7.0)):
            r = roll_2d(p, steps=20000)
            self.assertLess(r["r"], 1e-2, f"{p} -> {r}")

    def test_already_at_origin_stays(self):
        r = roll(0.0, steps=100)
        self.assertAlmostEqual(r["x"], 0.0, places=9)


class DimensionIndependenceTests(unittest.TestCase):
    def test_same_steps_in_every_dimension(self):
        """The striking result: identical step count at dim 1 through
        32, because each coordinate only ever reads itself. No matrix
        touches the state."""
        d = dimension_independence(dims=(1, 2, 4, 8, 16, 32), seed=1)
        steps = {r["dim"]: r["steps"] for r in d["rows"]}
        self.assertEqual(len(set(steps.values())), 1,
                         f"step counts differed by dimension: {steps}")
        self.assertTrue(d["all_converged"])

    def test_all_converge_from_fixed_radius(self):
        rng = random.Random(3)
        for dim in (1, 3, 8):
            coords = [rng.gauss(0, 1) for _ in range(dim)]
            scale = 4.0 / math.sqrt(sum(c * c for c in coords))
            r = roll_n([c * scale for c in coords], steps=20000)
            self.assertLess(r["r"], 1e-2, f"dim={dim} r={r['r']}")


class ControlComparisonTests(unittest.TestCase):
    def test_ball_and_gradient_both_converge(self):
        """Same guarantee, different mechanism."""
        for x0 in (1.0, 5.0, -5.0):
            b = roll(x0, steps=20000)
            g = gradient_n_drop([x0], steps=2000)
            self.assertLess(abs(b["x"]), 1e-2)
            self.assertLess(g["r"], 1e-6)

    def test_gradient_is_faster_and_that_is_stated(self):
        """The ball is a physical simulation with damping; it should be
        slower. If it ever isn't, the comparison has changed meaning."""
        b = roll(10.0, steps=20000)
        g = gradient_n_drop([10.0], steps=2000)
        self.assertGreater(b["steps"], g["steps"])


class FalsificationTests(unittest.TestCase):
    """The limit, measured. A ball is not an optimiser."""

    def test_ball_gets_stuck_in_a_local_minimum(self):
        r = local_minimum_probe()
        self.assertFalse(r["found_global"],
                         "ball found the global minimum despite a bump; "
                         "the bump parameters are too weak to falsify")
        self.assertGreater(r["settled_at"], 0.5,
                           f"settled too close to the origin: {r}")

    def test_the_bump_really_creates_two_basins(self):
        r = local_minimum_probe()
        self.assertEqual(r["tilt_zeros"], 3,
                         "expected three tilt zeros (two basins); the "
                         "surface is still effectively concave")

    def test_concave_case_still_finds_global(self):
        """The contrast: with no bump, it works."""
        r = roll(3.0, steps=20000)
        self.assertLess(abs(r["x"]), 1e-2)

    def test_claim_is_scoped_to_concave(self):
        """Guards the wording. If someone widens the claim, this fails."""
        r = local_minimum_probe()
        self.assertIn("CONCAVE", r["interpretation"].upper())
        self.assertIn("not quote", r["interpretation"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)