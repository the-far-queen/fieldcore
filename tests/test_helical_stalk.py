"""
test_helical_stalk.py — prime-wound local phase with skip-distance coupling.

Built from Bobby's correction in the frontier session:

  "pls draw in sheaves and helical windings NOT ON THE MANIFOLD BUT ON
   STALKS"

The load-bearing claim is LOCALITY: a manifold is global, a stalk is local,
and reasoning/memory/control are all local, so the architecture should be.
These tests check the parts of that claim which are numerically checkable,
and state plainly which parts are not.

THREE PROPERTIES CAUGHT IN THE SELFTEST AND LOCKED HERE
------------------------------------------------------
  1. coherence is GAUGE-INVARIANT. A uniform phase offset changes nothing
     (measured separation 1.11e-16). My first scramble test applied a
     uniform offset and asserted a change -- the test was wrong, not the
     code. Only RELATIVE phase carries information.
  2. the restriction matrix is INDEFINITE, not positive-semidefinite. The
     graph is complete, so row sums are positive and the constant mode is
     not a null vector. A positive-weight complete-graph operator is
     indefinite by construction. My selftest printed the opposite.
  3. coupling(5, 13) = 0.757 is CORRECT -- 13 is the upper member of pair
     (11,13), so the skip is 1. My first check called that a refusal
     failure. An anchor that genuinely fails is 23.

Run: python -m pytest tests/test_helical_stalk.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from helical_stalk import (  # noqa: E402
    MAX_TABULATED_SKIP,
    SKIP_COUPLING,
    Stalk,
    coherence,
    coupling,
    propagate,
    restriction_matrix,
    stalk_network,
)


# ---------------------------------------------------------------------------
# H1: the coupling table refuses rather than guessing
# ---------------------------------------------------------------------------

def test_h1_skip_zero_is_one():
    assert coupling(5, 5) == pytest.approx(1.0)


def test_h2_coupling_decreases_with_skip():
    vals = [SKIP_COUPLING[k] for k in sorted(SKIP_COUPLING)]
    assert all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)), \
        "coupling must decay with skip distance"


def test_h3_beyond_the_table_is_refused():
    """skip(5,71) = 6 > MAX_TABULATED_SKIP. A zero would assert 'these do
    not interact'; the truth is 'we did not measure this'."""
    with pytest.raises(ValueError, match="beyond the tabulated range"):
        coupling(5, 71)


def test_h4_unlisted_anchor_is_refused():
    """23 is in no twin-prime pair, so no skip distance can be computed."""
    with pytest.raises(ValueError, match="unknown winding anchor"):
        coupling(5, 23)


def test_h5_upper_member_is_a_valid_anchor():
    """LOCKS CORRECTION 3. 13 is the upper member of (11,13); the skip from
    5 is 1 and the coupling is 0.757. An earlier check asserted this should
    refuse, which was wrong."""
    assert coupling(5, 13) == pytest.approx(SKIP_COUPLING[1])
    assert coupling(11, 17) == pytest.approx(SKIP_COUPLING[1])


def test_h6_coupling_is_symmetric():
    for a in (5, 11, 17, 29):
        for b in (5, 11, 17, 29):
            if a != b:
                assert coupling(a, b) == coupling(b, a)


# ---------------------------------------------------------------------------
# H2: the restriction matrix
# ---------------------------------------------------------------------------

def test_h7_matrix_is_symmetric_with_zero_diagonal():
    st = stalk_network(["A", "B", "C", "D"])
    R = restriction_matrix(st)
    assert np.allclose(R, R.T)
    assert np.allclose(np.diag(R), 0.0), "a stalk does not couple to itself"


def test_h8_matrix_is_indefinite_and_that_is_correct():
    """LOCKS CORRECTION 2. The graph is complete, so row sums are positive
    and the constant mode is not a null vector. A positive-weight
    complete-graph operator is indefinite. Asserting PSD here would have
    been asserting something false about a correct implementation."""
    st = stalk_network(["A", "B", "C", "D"])
    ev = np.linalg.eigvalsh(restriction_matrix(st))
    assert ev.min() < 0.0, "must be indefinite"
    assert ev.max() > 0.0


def test_h9_matrix_is_well_conditioned():
    """|eig| must stay inside a measured band.

    The thresholds are the MEASURED values for n=4 (|eig| 0.150..1.765),
    not a round number I picked. An earlier version asserted cond < 5.0
    from memory; measured cond is 11.79. The test was wrong.

    What this guards is the Hodge failure mode in a new place: an
    operator that multiplies a mode by ~7 every step is the bug that sat
    in six published versions.
    """
    st = stalk_network(["A", "B", "C", "D"])
    ev = np.abs(np.linalg.eigvalsh(restriction_matrix(st)))
    assert ev.max() < 2.0, f"largest |eig| = {ev.max()}, too hot"
    assert ev.min() > 0.10, f"smallest |eig| = {ev.min()}, too cold"


def test_h10_conditioning_degrades_with_size_as_documented():
    """LOCKS THE DOCSTRING TABLE. Measured, not asserted from memory:
    n=2 cond 1.00, n=3 cond 2.88, n=4 cond 11.79, n=5 cond 13.35."""
    conds = {}
    for n in (2, 3, 4, 5):
        st = stalk_network([chr(65 + i) for i in range(n)])
        ev = np.abs(np.linalg.eigvalsh(restriction_matrix(st)))
        conds[n] = ev.max() / ev.min()
    assert conds[2] == pytest.approx(1.000, abs=1e-2)
    assert conds[3] == pytest.approx(2.876, abs=0.01)
    assert conds[4] == pytest.approx(11.79, abs=0.05)
    assert conds[5] == pytest.approx(13.35, abs=0.05)
    assert conds[4] > conds[3] > conds[2], "conditioning must worsen with size"


def test_h11_network_size_is_capped_at_the_table():
    """Five skip levels means five expressible stalks. A sixth must REFUSE,
    not silently return zero -- zero asserts non-interaction, which is a
    much stronger claim than 'unmeasured'. An earlier version of this test
    asked for six stalks and called the resulting exception a failure; the
    exception was the module working correctly.
    """
    with pytest.raises(ValueError, match="beyond the tabulated range"):
        restriction_matrix(stalk_network(["A", "B", "C", "D", "E", "F"]))


# ---------------------------------------------------------------------------
# H3: locality. this is the property the module exists for.
# ---------------------------------------------------------------------------

def test_h12_a_stalk_only_touches_declared_neighbours():
    """No global operator. The A-B coupling must not depend on how many
    stalks exist elsewhere."""
    big = stalk_network(["A", "B", "C", "D"])
    small = stalk_network(["A", "B"])
    rb = restriction_matrix(big)
    rs = restriction_matrix(small)
    assert np.allclose(rs[0, 1], rb[0, 1]), \
        "the A-B coupling must not depend on how many stalks exist"


def test_h11_propagation_moves_phase():
    st = stalk_network(["A", "B", "C", "D"])
    before = {n: s.phase for n, s in st.items()}
    propagate(st, "A", phase_shift=0.7, duration=10)
    after = {n: s.phase for n, s in st.items()}
    assert any(after[n] != before[n] for n in ("B", "C", "D")), \
        "propagation moved nothing -- the network is inert"


def test_h12_propagation_records_provenance():
    """Without restricted_from there is no way to tell a phase that
    arrived from a neighbour from one that was already there."""
    st = stalk_network(["A", "B", "C", "D"])
    propagate(st, "A", phase_shift=0.7, duration=10)
    for n in ("B", "C", "D"):
        assert st[n].restricted_from == "A"


def test_h1X_source_does_not_propagate_to_itself():
    st = stalk_network(["A", "B", "C"])
    received = propagate(st, "A", phase_shift=1.0, duration=8)
    assert "A" not in received


def test_h1X_unknown_source_is_refused():
    st = stalk_network(["A", "B"])
    with pytest.raises(ValueError, match="unknown stalk"):
        propagate(st, "Z", phase_shift=1.0)


def test_h1X_network_length_mismatch_is_refused():
    with pytest.raises(ValueError, match="same length"):
        stalk_network(["A", "B"], windings=[5])


def test_h1X_negative_amplitude_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        Stalk(name="X", winding=5, amplitude=-1.0)


def test_h1X_phase_wraps_into_range():
    s = Stalk(name="X", winding=5, phase=7.5)
    assert 0.0 <= s.phase < 2 * math.pi
    s.advance(1.0)
    assert 0.0 <= s.phase < 2 * math.pi


# ---------------------------------------------------------------------------
# H4: coherence. gauge invariance and response, both measured.
# ---------------------------------------------------------------------------

def test_h1X_coherence_is_one_when_aligned():
    st = stalk_network(["A", "B", "C", "D"])
    assert coherence(st) == pytest.approx(1.0, abs=1e-12)


def test_h1X_coherence_is_gauge_invariant():
    """LOCKS CORRECTION 1. A uniform offset changes nothing. Absolute phase
    is a gauge freedom; only relative phase carries information."""
    st = stalk_network(["A", "B", "C", "D"])
    before = coherence(st)
    for s in st.values():
        s.advance(1.9)
    after = coherence(st)
    assert abs(before - after) < 1e-12, \
        f"coherence responded to a uniform offset: {before} -> {after}"


def test_h20_coherence_falls_when_phases_differ():
    st = stalk_network(["A", "B", "C", "D"])
    aligned = coherence(st)
    for n, p in zip(("A", "B", "C", "D"), (0.0, 0.5, 1.0, 1.5)):
        st[n].phase = p
    spread = coherence(st)
    assert spread < 1.0
    assert aligned - spread > 0.1, f"separation only {aligned - spread}"


def test_h21_coherence_is_bounded():
    st = stalk_network(["A", "B", "C", "D"])
    for _ in range(50):
        for s in st.values():
            s.advance(0.37)
        c = coherence(st)
        assert -1e-12 <= c <= 1.0 + 1e-12, f"coherence left its range: {c}"


def test_h22_coherence_of_empty_is_zero_not_an_error():
    assert coherence({}) == 0.0


# ---------------------------------------------------------------------------
# H5: the design table is labelled as design
# ---------------------------------------------------------------------------

def test_h23_table_is_monotone_and_bounded():
    vals = [SKIP_COUPLING[k] for k in sorted(SKIP_COUPLING)]
    assert vals[0] == 1.0
    assert all(0.0 < v <= 1.0 for v in vals)
    assert sorted(SKIP_COUPLING) == list(range(MAX_TABULATED_SKIP + 1))


def test_h24_module_states_the_granite_claim_is_rejected():
    """The table is DESIGN. The docstring must say so, and must point at the
    register entry where the granite claim was tested and rejected. A module
    that quietly implied the coupling was measured would reintroduce a
    claim we already know is unsupported."""
    import helical_stalk as hs
    doc = (hs.__doc__ or "")
    assert "DESIGN" in doc
    assert "claims-register" in doc, "must point at the register entry"
    assert "REJECTED" in doc


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))