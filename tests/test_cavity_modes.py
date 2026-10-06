"""
test_cavity_modes.py — the room-mode physics, asserted not assumed.

The claim being defended is narrow and checkable: for a rectangular
cavity, mode frequencies follow from dimensions and wave speed by

    f(n,m,p) = (c/2) sqrt((n/Lx)^2 + (m/Ly)^2 + (p/Lz)^2)

If that is wrong, nothing in the module is worth reading.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cavity_modes import (  # noqa: E402
    axial_modes,
    full_modes,
    degeneracy,
    report,
    C_AIR,
    C_GRANITE,
)


class AxialModeTests(unittest.TestCase):
    def test_fundamental_is_c_over_2L(self):
        for Lx, Ly, Lz in [(1.0, 1.0, 1.0), (2.0, 2.0, 2.0),
                           (5.0, 5.0, 5.0), (10.47, 5.23, 5.97),
                           (2.0, 4.0, 6.0), (3.0, 1.0, 7.5)]:
            modes = axial_modes(Lx, Ly, Lz, C_AIR)
            # axial_modes rounds to 4 dp for reporting, so compare at 3.
            self.assertAlmostEqual(
                modes[0].f, C_AIR / (2 * max(Lx, Ly, Lz)), places=3,
                msg=f"fundamental wrong for {Lx}x{Ly}x{Lz}",
            )

    def test_harmonics_are_integer_multiples(self):
        m = axial_modes(5.0, 7.0, 9.0, C_AIR, n_max=6)
        x = [mo for mo in m if mo.n > 0 and mo.m == 0 and mo.p == 0]
        self.assertEqual(len(x), 6)
        for i, mo in enumerate(x, 1):
            self.assertAlmostEqual(mo.f, C_AIR * i / (2 * 5.0), places=6)

    def test_only_one_index_nonzero(self):
        for mo in axial_modes(4.0, 5.0, 6.0, C_AIR):
            self.assertEqual(sum([mo.n, mo.m, mo.p]), mo.n + mo.m + mo.p)
            self.assertIn(sum(1 for v in (mo.n, mo.m, mo.p) if v > 0), (1,))


class FullModeTests(unittest.TestCase):
    def test_matches_closed_form(self):
        Lx, Ly, Lz = 10.47, 5.23, 5.97
        for mo in full_modes(Lx, Ly, Lz, C_AIR, n_max=3):
            expect = (C_AIR / 2) * math.sqrt(
                (mo.n / Lx) ** 2 + (mo.m / Ly) ** 2 + (mo.p / Lz) ** 2
            )
            self.assertAlmostEqual(mo.f, expect, places=3)

    def test_no_zero_mode(self):
        """(0,0,0) is not a mode; it would be the DC offset."""
        for mo in full_modes(3.0, 4.0, 5.0, C_AIR, n_max=3):
            self.assertNotEqual((mo.n, mo.m, mo.p), (0, 0, 0))

    def test_sorted_ascending(self):
        fs = [mo.f for mo in full_modes(3.0, 4.0, 5.0, C_AIR, n_max=4)]
        self.assertEqual(fs, sorted(fs))

    def test_longer_cavity_gives_lower_frequency(self):
        """The whole premise: frequency is set by geometry."""
        short = full_modes(1.0, 1.0, 1.0, C_AIR, n_max=1)[0].f
        long = full_modes(10.0, 10.0, 10.0, C_AIR, n_max=1)[0].f
        self.assertLess(long, short)
        self.assertAlmostEqual(long * 10, short, places=6)

    def test_wave_speed_scales_frequency(self):
        air = full_modes(2.0, 2.0, 2.0, C_AIR, n_max=2)[0].f
        stone = full_modes(2.0, 2.0, 2.0, C_GRANITE, n_max=2)[0].f
        self.assertAlmostEqual(stone / air, C_GRANITE / C_AIR, places=6)


class DegeneracyTests(unittest.TestCase):
    """A cube is maximally degenerate. That fingerprint is the honest,
    measurable version of 'this shape was chosen for a frequency'."""

    def test_cube_is_more_degenerate_than_non_cube(self):
        cube = degeneracy(full_modes(2, 2, 2))
        box = degeneracy(full_modes(2, 2, 3.5))
        self.assertGreater(max(cube.values()), max(box.values()))

    def test_cube_fundamental_is_triply_degenerate(self):
        """degeneracy() bins to 0.5 Hz, so look up on the same grid."""
        d = degeneracy(full_modes(2, 2, 2))
        key = round(C_AIR / 4.0 / 0.5) * 0.5
        self.assertGreaterEqual(d.get(key, 0), 3,
                                f"cube fundamental not 3-fold degenerate: {d}")

    def test_cube_does_not_break_the_21cm_alignment(self):
        """The (1,1,1) mode of a cube: sqrt(3)/2 * c/L. Sanity check on
        the three-axis term rather than an acoustic claim."""
        modes = {(mo.n, mo.m, mo.p): mo.f
                 for mo in full_modes(2, 2, 2, C_AIR, n_max=2)}
        self.assertAlmostEqual(
            modes[(1, 1, 1)], math.sqrt(3) * C_AIR / 4.0, places=4
        )


class ReportTests(unittest.TestCase):
    def test_report_is_serialisable_and_carries_the_disclaimer(self):
        r = report(10.47, 5.23, 5.97)
        self.assertIn("dimensions_m", r)
        self.assertIn("fundamental_per_axis_hz", r)
        self.assertIn("note", r)
        self.assertIn("whether the geometry was chosen", r["note"])

    def test_kings_chamber_fundamentals(self):
        """Concrete numbers so a change in the constants is visible."""
        r = report(10.47, 5.23, 5.97)
        self.assertAlmostEqual(r["fundamental_per_axis_hz"]["x"], 16.38, places=2)
        self.assertAlmostEqual(r["fundamental_per_axis_hz"]["y"], 32.79, places=2)
        self.assertAlmostEqual(r["fundamental_per_axis_hz"]["z"], 28.73, places=2)

    def test_kings_chamber_does_NOT_reach_the_alpha_band(self):
        """Measured limit, asserted so it cannot quietly become true.

        King's Chamber interior is ~10.47 x 5.23 x 5.97 m. The longest
        axis sets the lowest mode at 343/(2*10.47) = 16.38 Hz. The alpha
        band (8-13 Hz) is BELOW that.

        So in AIR this chamber is not an alpha-band resonator. Anyone
        claiming an alpha coupling from these dimensions is wrong unless
        the medium is not air, or the coupling mechanism is not a room
        mode. Recorded here because the claim is tempting and the
        arithmetic is simple.
        """
        r = report(10.47, 5.23, 5.97)
        bands = {m["band"] for m in r["axial_modes"]}
        self.assertNotIn("alpha", bands)
        self.assertAlmostEqual(r["fundamental_per_axis_hz"]["x"], 16.38, places=2)
        # and the harmonics do climb into gamma, which is the band
        # people actually measure chamber effects in
        self.assertIn("gamma", bands)


if __name__ == "__main__":
    unittest.main(verbosity=2)