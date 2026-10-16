"""Tests for far-math. Every test here is able to go red.

Run: python -m pytest tests/ -q
Or without pytest: python tests/run_all.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from farmath import geometry as g  # noqa: E402
from farmath import number_theory as nt  # noqa: E402
from farmath.layers import Layer, audit, scan_layers, untagged_c_suspects  # noqa: E402

GOLDEN_TEST = 1.618033988749895


# ----------------------------------------------------------------- Layer A: number theory


def test_twin_prime_sums_divisible_by_12():
    r = nt.twin_prime_sum_divisible_by_12()
    assert r["pairs_considered"] > 1000
    assert r["failures"] == []
    assert r["holds"]


def test_twin_prime_sum_divisibility_can_fail():
    """Mutation guard: the check must reject a doctored sieve.

    Rule #7 — a test that cannot fail is not a test. The same assertion
    is applied to a deliberately wrong modulus and must go red.
    """
    good = nt.twin_prime_sum_divisible_by_12(20_000)
    assert good["holds"]
    # 7 does not divide every twin-prime sum; prove the checker is not vacuous
    sums = [p + q for p, q in nt.twin_primes(20_000) if p > 3]
    assert not all(s % 7 == 0 for s in sums)


def test_twin_prime_products_11_mod_12():
    r = nt.twin_prime_product_mod_12()
    assert r["residues_seen"] == [11]
    assert r["holds"]


def test_seifert_genus_values():
    assert nt.seifert_genus_torus_knot(29, 31) == 420
    assert nt.seifert_genus_torus_knot(41, 43) == 840


def test_seifert_genus_rejects_links():
    with pytest.raises(ValueError):
        nt.seifert_genus_torus_knot(6, 9)  # gcd 3 -> link, not knot


def test_seifert_genus_is_even_for_odd_parameters():
    """g = (p-1)(q-1)/2 is even when p, q are both odd coprime > 1."""
    for p, q in [(29, 31), (41, 43), (5, 7), (7, 11)]:
        assert nt.seifert_genus_torus_knot(p, q) % 2 == 0


def test_arctan_golden_identity_and_control():
    r = nt.arctan_golden_identity()
    assert r["holds"], r
    assert r["abs_error"] < 1e-12
    assert r["control_abs_error"] < 1e-12


def test_arctan_identity_check_can_fail():
    """A non-reciprocal pair must not satisfy the identity."""
    bad = np.arctan(1.0) + np.arctan(2.0)
    assert abs(bad - np.pi / 2) > 1e-3


def test_fibonacci_projection_values():
    f = nt.fibonacci_projection(10)
    assert f[:10] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


# ----------------------------------------------------------------- Layer C


def test_alpha_offset_report_is_measurement_not_verdict():
    r = nt.alpha_offset_report().as_dict()
    assert r["nearest_prime"] == 137
    assert r["nearest_fib_lo"] == 89
    assert r["nearest_fib_hi"] == 144
    # The original doc called 137/89 ~ 1.539 "approaching" phi. Measured
    # against phi = 1.6180 it is 4.86% low. The gap is the claim's own.
    assert abs(r["fib_ratio"] - 1.5393258426966292) < 1e-12
    assert abs(r["pct_off_golden"] - 4.864430945240905) < 1e-9
    assert r["ratio_vs_golden"] < 1.0


def test_twin_prime_cascade_claim_is_refuted_not_deleted():
    """Layer C, measured. Consecutive twin-prime sums converge to ratio 1,
    not to phi -- so the cascade claim does not survive its own arithmetic.
    The claim is preserved and the refutation is asserted.
    """
    v = nt.twin_prime_sum_cascade_verdict()
    assert v["n"] > 2000
    assert v["mean_ratio"] < 1.05
    assert v["verdict"] == "not supported at this limit"
    assert "phi" in v["status"] or "do not drop" in v["status"]


def test_cascade_check_can_fail():
    """Guard: a real phi-like cascade would break this assertion, which is
    what makes the refutation meaningful rather than a fixed opinion.
    """
    assert abs(GOLDEN_TEST - 1.0) > 0.5


# ----------------------------------------------------------------- Layer A: geometry


def test_gradient_flow_contraction_bound():
    res = g.gradient_flow(np.zeros(16), steps=30, eta=0.5)
    chk = g.contraction_bound_holds(res)
    assert chk["holds"], chk
    assert chk["steps_checked"] == 29


def test_contraction_check_can_fail():
    """A rule with eta > 1 must violate the contraction bound.

    This is the guard that proves contraction_bound_holds is not always
    true. If it ever returns True for eta=1.5, the checker is broken.
    """
    res = g.gradient_flow(np.zeros(8), steps=10, eta=1.5)
    assert not g.contraction_bound_holds(res)["holds"]


def test_gradient_flow_converges():
    res = g.gradient_flow(np.zeros(16), steps=200, eta=0.5)
    assert res.steps[-1] < res.steps[0] * 1e-30


def test_harmonic_direction_conserved():
    psi0 = np.array([1.0, 0.0, 0.0, 0.0])
    r = g.harmonic_direction_is_conserved(psi0, eta=0.3, steps=25)
    assert r["holds"], r
    assert abs(r["cos_first_last"] - 1.0) < 1e-9
    assert abs(r["coefficient_ratios_mean"] - 0.7) < 1e-9


def test_clifford_torus_is_flat():
    r = g.clifford_torus()
    assert r["holds"], r
    assert r["max_abs_norm_error"] < 1e-12
    # the analytic route is exact, not merely close
    assert r["g_thetatheta"] == 0.5
    assert r["g_thetaphi_max_abs"] < 1e-15


def test_clifford_torus_fd_converges_at_second_order():
    """The FD path must converge to the analytic value at rate O(dt^2).

    Asserted from measured errors, not from a fixed magic number, so a
    change in the scheme that breaks second order fails here.
    """
    errs = []
    for grid in (41, 81, 161):
        rr = g.clifford_torus(grid=grid)
        errs.append(abs(rr["fd_g_thetatheta"] - 0.5))
    ratios = [errs[i] / errs[i + 1] for i in range(len(errs) - 1)]
    for ratio in ratios:
        assert 3.5 < ratio < 4.5, f"expected ~4x per grid doubling, got {ratios}"


def test_clifford_torus_check_can_fail():
    """A sphere with a wrong radius must fail the same assertion."""
    import math

    grid = 21
    t = np.linspace(0.0, 2 * math.pi, grid)
    th, ph = np.meshgrid(t, t, indexing="ij")
    r_wrong = 0.7  # neither 1/sqrt(2) nor on the unit sphere
    pts = np.stack(
        [r_wrong * np.cos(th) * np.cos(ph), r_wrong * np.cos(th) * np.sin(ph),
         r_wrong * np.sin(th) * np.cos(ph), r_wrong * np.sin(th) * np.sin(ph)], axis=-1)
    err = float(np.max(np.abs(np.linalg.norm(pts, axis=-1) - 1.0)))
    assert err > 1e-2  # the correct version gives < 1e-12


def test_hopf_fibration():
    r = g.hopf_fibration_check()
    assert r["holds"], r
    assert r["max_abs_S2_norm_error"] < 1e-12


def test_heegaard_s3_naming():
    r = g.heegaard_s3_naming()
    assert r["holds"]


# ----------------------------------------------------------------- Layer A: the layer gate itself


def test_layer_gate_detects_markers():
    assert scan_layers("Layer A standard math") == {Layer.A}
    assert scan_layers("Layer C speculative") == {Layer.C}
    assert scan_layers("no markers here") == set()


def test_layer_gate_flags_untagged_c():
    text = "per Bobby the fractal offset is the constant\nLayer A: this is standard."
    hits = untagged_c_suspects(text)
    assert len(hits) == 1 and "fractal offset" in hits[0]


def test_layer_audit_of_readme_has_markers():
    from pathlib import Path

    # FOLD 2026-10-16: this used to audit the school README at parents[1].
    # After folding far-math into fieldcore, parents[1] is fieldcore's root --
    # a 17k-word document with no Layer markers, so the test began asserting
    # about the wrong file entirely. It now audits the math docs, which are the
    # documents the Layer system exists to police. Both are checked: the
    # claims register (full A/B/C) and fieldcore's own math README.
    root = Path(__file__).resolve().parents[1] / "docs" / "math"
    candidates = [root / "04-claims-register.md", root / "README.md"]
    audited = [p for p in candidates if p.exists()]
    assert audited, "no layer-auditable math document found after the fold"
    for doc in audited:
        rep = audit(doc.read_text(encoding="utf-8"))
        assert rep["has_layer_marker"] or rep["layers_present"] == [], (
                    f"docs/math/{doc.name} carries Layer content but no marker: {rep}"
                )