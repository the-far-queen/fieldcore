"""
sheaf_nn_index.py — sklearn NearestNeighbors index (per Grok master plan).

A nearest-neighbor index for unit embeddings stored by the lexicon ingest.
"sheaf" in the name = routing primitive, not cohomology. Per Batch 1 K4 the
runtime objects are Channels until restriction maps exist.
"""

from __future__ import annotations

import numpy as np

try:
    from sklearn.neighbors import NearestNeighbors
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


class SheafNNIndex:
    def __init__(self, dim: int = 16, n_neighbors: int = 10):
        if not _SKLEARN_AVAILABLE:
            raise RuntimeError("sklearn not available; install scikit-learn to use SheafNNIndex")
        self.dim = dim
        self.nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
        self._fitted = False

    def fit(self, embeddings: np.ndarray):
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dim:
            raise ValueError(f"expected shape (n,, {self.dim}), got {embeddings.shape}")
        self.nn.fit(embeddings)
        self._fitted = True

    def query(self, emb: np.ndarray, k: int = 1):
        if not self._fitted:
            return [], []
        distances, indices = self.nn.kneighbors([emb], n_neighbors=k)
        return distances[0].tolist(), indices[0].tolist()

    def __repr__(self) -> str:
        return f"SheafNNIndex(dim={self.dim} fitted={self._fitted})"
