"""
test_coherence_spine.py -- the three surviving concepts as one mechanism.

THE SPINE, MEASURED ACROSS SIX VERIFIED TRANSCRIPTS
---------------------------------------------------
    concept      f1  f2  f3  f4  f5  f6   files
    coherence    21 419 523 495 209 326    6/6
    sheaf        11  40 174   1  14 405    6/6
    threshold    21  33  84  68   9  19    6/6

Exactly three concepts survive all six files. Read together:

    A SYSTEM IS HELD BY THRESHOLDS ON A SHEAF,
    AND THE QUALITY OF THE HOLDING IS COHERENCE.

Everything else is regional -- PSB 4/6, sacred axis 5/6, governor 5/6,
MVCC 3/6, and two that never propagated: psi_0 (file 1 only) and
counterfactual (file 6 only).

THE LOAD-BEARING PROPERTY
-------------------------
Naive monotonicity FAILS: two subspaces can each be internally
consistent and their union be inconsistent at the seam. That is why a
sheaf is not an average. Every test below that touches `globally_
consistent` is really testing that this can go false.

Run: python -m pytest tests/test_coherence_spine.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from coherence_spine import (  # noqa: E402
    Disposition,
    Sheaf,
    Site,
    Threshold,
)


def _id(x: float) -> float:
    return x


def _line(slope: float):
    return lambda x: slope * x


def chain(n=3, value=0.5, tol=0.01):
    sh = Sheaf("t")
    names = [f"s{i}" for i in range(n)]
    for nm in names:
        sh.add(Site(nm, value=value, tolerance=tol))
    for a, b in zip(names, names[1:]):
        sh.glue(a, b, _id)
    return sh, names


# ---------------------------------------------------------------------------
# S1: a coherent sheaf is coherent
# ---------------------------------------------------------------------------

def test_s1_matched_sites_are_coherent():
    sh, _ = chain()
    assert sh.globally_consistent()
    assert sh.coherence() == pytest.approx(1.0)


def test_s2_no_maps_means_vacuously_coherent():
    sh = Sheaf("empty")
    sh.add(Site("solo", 0.5, 0.01))
    assert sh.globally_consistent()
    assert sh.coherence() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# S2: THE SEAM CAN BREAK. this is the whole point.
# ---------------------------------------------------------------------------

def test_s3_two_consistent_halves_can_form_an_inconsistent_union():
    """The failure of naive monotonicity, stated as a test.

    a=0.5 and b=0.5 agree; b=0.5 and c=0.5 agree. The chain is smooth.
    Then c alone moves to 0.9 and the UNION breaks, while a and b are
    still perfectly consistent with each other.

    A global average reports 0.63 and calls it fine. That is the failure
    this structure exists to prevent.
    """
    sh, names = chain()
    sh.sites["s2"].observe(0.9)
    assert not sh.globally_consistent()
    # and the OTHER two are still mutually consistent
    ab = abs(sh.maps[0].apply(sh.sites["s0"].value) - sh.sites["s1"].value)
    assert ab < 1e-12, "the a-b pair should be untouched"


def test_s4_violation_names_the_seam_and_the_gap():
    sh, _ = chain()
    sh.sites["s2"].observe(0.9)
    v = sh.violations()
    assert len(v) == 1
    assert "s1->s2" in v[0]
    assert "tolerance" in v[0]
    assert "0.4" in v[0]


def test_s5_tolerance_bounds_what_counts_as_a_violation():
    sh, _ = chain(tol=0.01)
    sh.sites["s2"].observe(0.505)          # gap 0.005 < tolerance
    assert sh.globally_consistent()
    sh.sites["s2"].observe(0.6)             # gap 0.1 > tolerance
    assert not sh.globally_consistent()


def test_s6_zero_tolerance_is_strict():
    sh, _ = chain(tol=0.0)
    sh.sites["s1"].observe(0.5 + 1e-15)
    assert sh.globally_consistent(), "below the 1e-12 slack"


# ---------------------------------------------------------------------------
# S3: coherence is computed, not asserted
# ---------------------------------------------------------------------------

def test_s7_coherence_falls_as_the_seam_opens():
    sh, _ = chain()
    before = sh.coherence()
    sh.sites["s2"].observe(0.9)
    after = sh.coherence()
    assert after < before
    # MEASURED, not guessed: the chain has TWO maps. One is clean (gap 0),
    # one is broken (0.4), so the mean relative gap is 0.4/0.9/2.
    assert after == pytest.approx(1.0 - (0.4 / 0.9) / 2, abs=0.001)


def test_s8_coherence_is_a_pure_function_of_structure():
    sh, _ = chain()
    sh.sites["s2"].observe(0.7)
    a = sh.coherence()
    b = sh.coherence()
    assert a == b, "reading coherence must not change it"


def test_s9_coherence_is_bounded():
    sh, _ = chain()
    for v in (0.0, 1.0, 5.0, -5.0, 1e6):
        sh.sites["s1"].observe(v)
        c = sh.coherence()
        assert 0.0 <= c <= 1.0, f"coherence escaped [0,1]: {c}"


# ---------------------------------------------------------------------------
# S4: thresholds
# ---------------------------------------------------------------------------

def test_s10_threshold_fires_on_a_declared_bound():
    t = Threshold("t", "q", 0.5, "above")
    assert t.check(0.4)[0] is Disposition.PASS
    assert t.check(0.6)[0] is Disposition.REFUSE
    assert "breaches" in t.check(0.6)[1]


def test_s11_threshold_direction_below():
    t = Threshold("t", "q", 0.1, "below")
    assert t.check(0.05)[0] is Disposition.REFUSE
    assert t.check(0.5)[0] is Disposition.PASS


def test_s12_threshold_is_frozen():
    t = Threshold("t", "q", 0.5)
    with pytest.raises(AttributeError):
        t.bound = 999.0


def test_s13_nonfinite_bound_refused():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite"):
            Threshold("t", "q", bad)


def test_s14_bad_direction_refused():
    with pytest.raises(ValueError, match="direction"):
        Threshold("t", "q", 1.0, "sideways")


# ---------------------------------------------------------------------------
# S5: structure integrity
# ---------------------------------------------------------------------------

def test_s15_glue_to_unknown_site_refused():
    sh, _ = chain()
    with pytest.raises(KeyError, match="unknown site"):
        sh.glue("s0", "ghost", _id)


def test_s16_duplicate_site_replaces():
    sh, _ = chain()
    sh.add(Site("s0", value=0.7, tolerance=0.01))
    assert sh.sites["s0"].value == pytest.approx(0.7)
    assert len(sh.sites) == 3


def test_s17_drift_tracks_the_last_move():
    sh, _ = chain()
    sh.sites["s0"].observe(0.8)
    assert sh.sites["s0"].drift() == pytest.approx(0.3)
    assert sh.sites["s1"].drift() == pytest.approx(0.0)
    assert sh.drift() == pytest.approx(0.3)


def test_s18_a_non_identity_rule_is_honoured():
    """A gluing map is a rule, not necessarily a copy."""
    sh = Sheaf("scaled")
    sh.add(Site("in", 2.0, 0.01))
    sh.add(Site("out", 4.0, 0.01))
    sh.glue("in", "out", _line(2.0))      # doubling
    assert sh.globally_consistent(), "a satisfied non-identity map is consistent"
    sh.sites["in"].observe(3.0)             # now the target should be 6.0
    assert not sh.globally_consistent(), \
        "the target must be checked against the RULE, not against the source"


# ---------------------------------------------------------------------------
# S6: the honesty clause
# ---------------------------------------------------------------------------

def test_s19_module_does_not_claim_cohomology():
    """It must say plainly that it computes no cohomology -- and must name
    CechCohomology, the class files 3 and 6 declared and left empty."""
    import coherence_spine as cs
    doc = (cs.__doc__ or "").lower()
    assert "cohomology" in doc
    assert "cechcohomology" in doc.replace(" ", ""), \
        "must name the class the corpus declared and never filled"
    assert "no h^1" in doc or "no h1" in doc, \
        "must state what it does NOT compute"


def test_s20_module_names_the_two_unpropagated_concepts():
    import coherence_spine as cs
    doc = (cs.__doc__ or "").lower()
    assert "psi_0" in doc, "must name the orphaned file-1 concept"
    assert "counterfactual" in doc, "must name the orphaned file-6 concept"


def test_s21_module_states_it_does_not_measure_anything_real():
    """The module must say what coherence is NOT for, in its own words."""
    import coherence_spine as cs
    doc = (cs.__doc__ or "").lower()
    assert "does not establish that coherence is the right measure" in doc
    assert "rather than asserted about it" in doc


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))