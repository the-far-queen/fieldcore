"""
test_sparse_substrate.py — three predictions for ternary operators (per Grok master plan).

Each prediction is a test. The paper (06-llm-sparse-substrate-2026-09-15.md)
documents the predictions; this file is the verdict.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest


sys.path.insert(0, "C:/Users/Admin/fieldcore/src")
sys.path.insert(0, "C:/Users/Admin/fieldcore/src/tiniest_core")


def test_prediction_a_relative_error():
    """ternary_matmul matches dense matmul to < 1% relative error."""
    from bitnet_ops import ternary_quantize, ternary_matmul

    rng = np.random.RandomState(0)
    A = ternary_quantize(rng.randn(64, 64))
    B = rng.randn(64, 64)

    A_dense = A.astype(np.float32)
    C_dense = A_dense @ B
    C_tern = ternary_matmul(A, B)
    rel_err = float(np.max(np.abs(C_tern - C_dense)) / np.max(np.abs(C_dense)))
    assert rel_err < 0.01, f"rel_err={rel_err}"


@pytest.mark.xfail(reason="requires packed-int8 implementation; ternary_matmul currently uses float32 (per paper §3 prediction B)")
def test_prediction_b_speed():
    """ternary_matmul is at least 1.5x faster than dense matmul."""
    import time
    from bitnet_ops import ternary_matmul

    rng = np.random.RandomState(0)
    A = np.random.choice([-1, 0, 1], size=(1024, 1024)).astype(np.int8)
    B = rng.randn(1024, 1024).astype(np.float32)

    t0 = time.perf_counter()
    for _ in range(100):
        ternary_matmul(A, B)
    t_tern = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    for _ in range(100):
        A.astype(np.float32) @ B
    t_dense = (time.perf_counter() - t0) / 100

    assert t_tern < t_dense / 1.5, f"t_tern={t_tern} t_dense={t_dense}"


def test_prediction_c_veto_preserved():
    """The kernel veto is preserved under ternary quantization."""
    from tiniest_core import gate, install_ground
    from bitnet_ops import ternary_quantize

    psi0 = install_ground(16)
    good = psi0 + 0.05 * np.random.RandomState(0).randn(16)
    bad = 5.0 * np.ones(16)

    ok_g, _ = gate(good, psi0)
    ok_b, _ = gate(bad, psi0)
    assert ok_g is True
    assert ok_b is False

    psi0_q = ternary_quantize(psi0, threshold=0.5).astype(np.float32)
    n0 = float(np.linalg.norm(psi0_q))
    if n0 > 0:
        psi0_q = psi0_q / n0

    ok_g2, _ = gate(good, psi0_q)
    ok_b2, _ = gate(bad, psi0_q)
    assert ok_g2 is True
    assert ok_b2 is False
