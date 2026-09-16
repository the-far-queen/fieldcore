"""
test_sheaf_nn_latency.py — verify SheafNNIndex < 100ms per query.
"""
import time
import sys
import pytest

import numpy as np


sys.path.insert(0, "C:/Users/Admin/fieldcore/src")


@pytest.mark.skipif(not pytest.importorskip("sklearn", minversion=None),
                    reason="sklearn not available")
def test_latency_under_100ms():
    from sheaf_nn_index import SheafNNIndex
    rng = np.random.RandomState(0)
    embeddings = rng.randn(10000, 16).astype(np.float32)
    idx = SheafNNIndex(dim=16)
    idx.fit(embeddings)

    queries = rng.randn(1000, 16).astype(np.float32)

    t0 = time.perf_counter()
    for q in queries:
        idx.query(q, k=1)
    elapsed_ms = (time.perf_counter() - t0) / 1000 * 1000

    assert elapsed_ms < 100.0, f"latency {elapsed_ms}ms exceeds 100ms target"
