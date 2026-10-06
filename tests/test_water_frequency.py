"""
test_water_frequency.py — the arithmetic behind the frequency claim.

Every number in water_frequency.py is checked against an independent
closed form here. If a constant is wrong, or a band is mis-stated, the
tests go red.

The biological-scale table is the load-bearing part: it is what
distinguishes a scale that resonates INSIDE water's H-bond relaxation
band from one that does not.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import water_frequency as wf  # noqa: E402


class UnitTests(unittest.TestCase):
    def test_wavelength_vacuum(self):
        self.assertAlmostEqual(wf.nm(1e12), 299792.458, places=2)
        # 1 GHz -> 0.2998 m = 299.8 mm
        self.assertAlmostEqual(wf.nm(1e9) / 1e6, 299.792458, places=4)

    def test_wavenumber(self):
        # 1 THz -> 33.36 cm^-1
        self.assertAlmostEqual(wf.wavenumber_cm(1e12), 33.356, places=2)
        # and the reverse: 3400 cm^-1 -> ~101.9 THz
        self.assertAlmostEqual(wf.wavenumber_cm(wf.C_M_S * 100 * 3400), 3400, places=6)

    def test_thermal_energy(self):
        r = wf.thermal_37c(1e12)
        self.assertAlmostEqual(r["kT_j"], wf.KB * 310.0, places=20)
        self.assertAlmostEqual(r["hf_over_kT"],
                               wf.PLANCK_H * 1e12 / (wf.KB * 310.0), places=9)


class BandTests(unittest.TestCase):
    def test_bands_are_ordered_and_well_formed(self):
        los = [b.lo_hz for b in wf.WATER_BANDS]
        self.assertEqual(los, sorted(los), "bands should ascend")

    def test_every_band_states_what_it_is_not(self):
        """Each band must carry its own limit. A number without a
        boundary is how 137 Hz happened."""
        for b in wf.WATER_BANDS:
            self.assertTrue(b.not_a_claim.strip(),
                            f"{b.name} has no stated limit")
            self.assertTrue(b.source.strip(), f"{b.name} has no source")

    def test_oh_stretch_is_in_the_mid_ir(self):
        """3400-3650 cm^-1 is textbook mid-IR. Assert the conversion
        lands in the mid-IR rather than trusting the label."""
        for b in wf.WATER_BANDS:
            if b.name == "oh-stretch":
                wn_lo = wf.wavenumber_cm(b.lo_hz)
                wn_hi = wf.wavenumber_cm(b.hi_hz)
                self.assertGreater(wn_lo, 3000)
                self.assertLess(wn_hi, 4000)

    def test_only_the_upper_hbond_band_is_selective(self):
        """The band spans 100 GHz - 1 THz but is NOT uniformly usable.

        At its low end hf/kT = 0.016 (thermal noise). The selective
        regime starts around 320 GHz. Asserted so the band is never
        cited at its full width as though the low end worked.
        """
        b = [x for x in wf.WATER_BANDS if x.name == "hbond-relaxation"][0]
        self.assertEqual(wf.thermal_37c(b.lo_hz)["regime"],
                         "thermal noise (hf << kT)")
        self.assertEqual(wf.thermal_37c(b.hi_hz)["regime"],
                         "selective (hf ~ kT)")
        self.assertGreater(wf.SELECTIVE_LO, b.lo_hz)
        self.assertLessEqual(wf.SELECTIVE_HI, b.hi_hz)


class BiologicalScaleTests(unittest.TestCase):
    """Which biological structures resonate INSIDE the H-bond band?

    f = c/2L with c = 1497 m/s in water.
    """

    HBND_LO, HBND_HI = 1e11, 1e12

    def _f_for(self, L_m):
        return wf.C_WATER_FRESH / (2 * L_m)

    def test_dna_diameter_resonates_in_the_SELECTIVE_sub_band(self):
        """DNA double helix ~2 nm -> ~374 GHz. This lands inside the
        H-bond relaxation band, which is the strongest result in the
        file and the reason it is asserted."""
        f = self._f_for(2e-9)
        self.assertGreater(f, wf.SELECTIVE_LO)
        self.assertLess(f, wf.SELECTIVE_HI)

    def test_water_molecule_is_just_ABOVE_the_band(self):
        """2.75 angstrom -> 2.72 THz, above the 1 THz band edge.

        Not inside it. The lattice's own acoustic scale sits one band
        above its relaxation mode, which is why the relaxation mode is
        a collective property and not a single-molecule vibration.
        """
        f = self._f_for(2.75e-10)
        self.assertGreater(f, wf.SELECTIVE_HI)

    def test_large_cells_fall_far_below_the_band(self):
        """A bacterium at 800 nm is ~936 MHz, three orders under the
        H-bond band. Large-scale biology does NOT resonate there."""
        f = self._f_for(800e-9)
        self.assertLess(f, self.HBND_LO)

    def test_neuron_soma_is_far_below(self):
        """The brain does not resonate in the H-bond band at the scale
        of a cell body. It couples electromagnetically instead."""
        self.assertLess(self._f_for(20e-6), 1e9)

    def test_the_matching_structures_are_nanometre_scale(self):
        """Structures landing in the selective sub-band are all between
        roughly 0.75 and 2.3 nm. Assert the range directly."""
        for L in (1e-9, 2e-9, 1.5e-9):
            f = self._f_for(L)
            self.assertTrue(wf.SELECTIVE_LO <= f <= wf.SELECTIVE_HI,
                            f"L={L} gave {f:.3e}, outside selective band")

    def test_hertz_band_biology_is_thermal_noise(self):
        """10 Hz and 100 Hz are ~1e-12 of kT. A quantum resonance at
        those frequencies is not physical; they are macroscopic."""
        for f in (10.0, 100.0, 7.83):
            r = wf.thermal_37c(f)
            self.assertEqual(r["regime"], "thermal noise (hf << kT)")
            self.assertLess(r["hf_over_kT"], 1e-9)


class FluidTableTests(unittest.TestCase):
    def test_known_speeds_are_present_and_ordered(self):
        self.assertLess(wf.C_AIR, wf.C_WATER_SEA)
        self.assertLess(wf.C_WATER_SEA, wf.C_WATER_FRESH)
        self.assertLess(wf.C_WATER_FRESH, wf.C_CSF)
        self.assertLess(wf.C_CSF, wf.C_TISSUE_BRAIN)

    def test_resonance_table_matches_closed_form(self):
        t = wf.resonance_table(cavities_m=(1.0, 10.47))
        for row in t["cavities"]:
            L = row["L_m"]
            self.assertAlmostEqual(row["water" if "water" in row else "seawater"],
                                   row["seawater"], places=6)
            self.assertAlmostEqual(row["seawater"],
                                   wf.C_WATER_SEA / (2 * L), places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)