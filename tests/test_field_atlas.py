"""
test_field_atlas.py — properties, not shapes.

Asserted here as CLAIMS (a count is C(n,k); every sector has equal
degree; the class partition is exhaustive; the harness refuses without
dynamics), not as "the function returns something with the right
attributes". A test that checks a shape passes when the arithmetic is
wrong, which is the failure mode this suite is written against.

Origin of the design: enuminous/FieldSpace, audited 2026-10-06.
"""

import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from field_atlas import (  # noqa: E402
    Atlas,
    AtlasRefusal,
    AblationHarness,
    atlas,
)

FIELDSPACE_SECTORS = ["E", "M", "S", "F", "W", "T", "I", "R", "H", "P", "A"]
SCALARS = ["F", "W", "T", "I", "R", "H", "P", "A"]


class AtlasCombinatoricsTests(unittest.TestCase):
    """The enumeration is a fact about C(n,k). Brute force is the oracle."""

    def test_size_is_binomial_for_many_n_k(self):
        for n in range(2, 10):
            for k in range(1, n + 1):
                a = atlas([f"s{i}" for i in range(n)], k)
                self.assertEqual(
                    a.size(), math.comb(n, k),
                    f"n={n} k={k} produced {a.size()}, expected C({n},{k})",
                )
                self.assertEqual(len(a.blocks), math.comb(n, k))

    def test_every_sector_has_identical_degree(self):
        """Uniformity: in a COMPLETE k-uniform hypergraph all vertices
        have degree C(n-1, k-1). A single sector with a different count
        means the enumeration silently dropped a block."""
        for n, k in [(11, 3), (8, 3), (6, 2), (7, 4), (12, 4), (5, 5)]:
            a = atlas([f"s{i}" for i in range(n)], k)
            deg = a.sector_incidence()
            self.assertEqual(len(set(deg.values())), 1,
                             f"n={n} k={k} degrees are not uniform: {deg}")
            self.assertEqual(set(deg.values()), {math.comb(n - 1, k - 1)})

    def test_blocks_are_distinct_and_correct_size(self):
        a = atlas(FIELDSPACE_SECTORS, 3)
        blocks = a.blocks
        self.assertEqual(len(set(blocks)), len(blocks), "duplicate blocks")
        for b in blocks:
            self.assertEqual(len(b), 3)
            self.assertEqual(len(set(b)), 3, f"{b} repeats a sector")

    def test_matches_fieldspace_reported_numbers(self):
        """Independent reproduction of the upstream audit: 165 blocks,
        45 per sector, 585 displayed statements over the 11-sector set."""
        a = atlas(FIELDSPACE_SECTORS, 3)
        self.assertEqual(a.size(), 165)
        self.assertEqual(set(a.sector_incidence().values()), {45})
        self.assertTrue(a.is_uniform())

    def test_overlap_spectrum_matches_lean_checked_identity(self):
        """FieldSpace proved 1980 + 6930 + 4620 = C(165,2) in Lean 4.
        The histogram is the stronger form of that same identity."""
        a = atlas(FIELDSPACE_SECTORS, 3)
        spec = a.overlap_spectrum()
        self.assertEqual(spec, {2: 1980, 1: 6930, 0: 4620})
        self.assertEqual(sum(spec.values()), math.comb(165, 2))
        # closed forms, not just the sum
        #   share 2: choose the shared pair (C(11,2)), then two distinct
        #            others from the remaining 9. That already counts the
        #            unordered block-pair once. 55 * 36 = 1980.
        self.assertEqual(spec[2], math.comb(11, 2) * math.comb(9, 2))
        #   share 0: two disjoint triples, C(11,3) * C(8,3) / 2
        self.assertEqual(
            spec[0],
            math.comb(11, 3) * math.comb(8, 3) // 2,
        )
        self.assertEqual(spec[0], 4620)

    def test_structural_classes_partition_exhaustively(self):
        """FieldSpace's six structural classes: 56 scalar-triples,
        56 gauge-two-scalar, 28 gravity-two-scalar, 16, 8, 1 = 165."""
        a = atlas(FIELDSPACE_SECTORS, 3)
        hist = a.classes(SCALARS)
        self.assertEqual(hist, {0: 1, 1: 24, 2: 84, 3: 56})
        self.assertTrue(a.class_partition_is_exhaustive(SCALARS))
        # closed form: j scalars out of k, from a scalar pool of size a
        for j, got in hist.items():
            self.assertEqual(
                got,
                math.comb(len(SCALARS), j) * math.comb(
                    len(FIELDSPACE_SECTORS) - len(SCALARS), 3 - j),
                f"class j={j} got {got}",
            )

    def test_pair_incidence_is_uniform(self):
        a = atlas(FIELDSPACE_SECTORS, 3)
        pairs = a.pair_incidence()
        self.assertEqual(len(pairs), math.comb(11, 2))
        self.assertEqual(set(pairs.values()), {9}, "pair degree should be C(9,1)")


class AtlasRefusalTests(unittest.TestCase):
    """A gate has to be able to say no."""

    def test_rank_exceeding_sectors_is_refused(self):
        with self.assertRaises(AtlasRefusal):
            atlas(["a", "b"], 3)

    def test_empty_sector_set_is_refused(self):
        with self.assertRaises(AtlasRefusal):
            atlas([], 3)

    def test_zero_and_negative_rank_refused(self):
        with self.assertRaises(AtlasRefusal):
            atlas(["a", "b"], 0)
        with self.assertRaises(AtlasRefusal):
            atlas(["a", "b"], -1)

    def test_duplicate_sectors_refused(self):
        with self.assertRaises(AtlasRefusal):
            atlas(["a", "b", "a"], 2)

    def test_unknown_distinguished_sector_refused(self):
        a = atlas(FIELDSPACE_SECTORS, 3)
        with self.assertRaises(AtlasRefusal):
            a.classes(["E", "M", "NOT_A_SECTOR"])

    def test_harness_refuses_without_dynamics(self):
        """The load-bearing refusal. A harness that synthesises dynamics
        when none is supplied reports confident deltas about a system
        nobody defined."""
        a = atlas(["E", "M", "S"], 2)
        h = AblationHarness(a)
        with self.assertRaises(AtlasRefusal):
            h.run()
        with self.assertRaises(AtlasRefusal):
            h._stats(frozenset())


class AblationHarnessTests(unittest.TestCase):
    def _dynamics(self):
        idx = {s: i for i, s in enumerate(["E", "M", "S", "F"])}

        def dyn(state, t):
            out = {}
            for s, i in idx.items():
                out[s] = -(0.1 + 0.01 * i) * state[s]
            return out

        return dyn

    def test_sweep_covers_every_removal_up_to_rank(self):
        a = atlas(["E", "M", "S", "F"], 2)
        h = AblationHarness(a, dynamics=self._dynamics(), steps=200)
        runs = h.run()
        # baseline + C(4,1) + C(4,2)
        self.assertEqual(len(runs), 1 + 4 + 6)
        self.assertEqual(runs[0].kind, "baseline")
        self.assertEqual(runs[0].delta_mean_tail, 0.0)

    def test_removing_a_sector_zeroes_it(self):
        a = atlas(["E", "M", "S", "F"], 2)
        h = AblationHarness(a, dynamics=self._dynamics(), steps=200)
        state = h._initial(frozenset({"M"}))
        self.assertEqual(state["M"], 0.0)
        self.assertNotEqual(state["E"], 0.0)

    def test_runs_are_deterministic(self):
        """Same inputs, same numbers. An ablation that cannot reproduce
        itself cannot be compared against itself."""
        a = atlas(["E", "M", "S", "F"], 2)
        r1 = AblationHarness(a, dynamics=self._dynamics(), steps=200).run()
        r2 = AblationHarness(a, dynamics=self._dynamics(), steps=200).run()
        self.assertEqual([x.mean_tail for x in r1], [x.mean_tail for x in r2])

    def test_summary_refuses_before_run(self):
        a = atlas(["E", "M", "S"], 2)
        h = AblationHarness(a, dynamics=self._dynamics())
        with self.assertRaises(AtlasRefusal):
            h.summary()

    def test_all_sectors_removed_refused(self):
        a = atlas(["E", "M"], 2)
        h = AblationHarness(a, dynamics=self._dynamics(), steps=100)
        with self.assertRaises(AtlasRefusal):
            h._stats(frozenset({"E", "M"}))


if __name__ == "__main__":
    unittest.main(verbosity=2)