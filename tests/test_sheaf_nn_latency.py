"""
test_sheaf_nn_latency.py — verify SheafNNIndex < 100ms per query.
"""
import time
import sys
import os
import pytest

import numpy as np


# Add this repo's src/ to sys.path so `sheaf_nn_index` resolves regardless of cwd.
_REPO_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
if _REPO_SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(_REPO_SRC))


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
