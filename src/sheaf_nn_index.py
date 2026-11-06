"""
sheaf_nn_index.py — sklearn NearestNeighbors index (per Grok master plan).

A nearest-neighbor index for unit embeddings stored by the lexicon ingest.
"sheaf" in the name = routing primitive, not cohomology. Per Batch 1 K4 the
runtime objects are Channels until restriction maps exist.
"""

from __future__ import annotations

from typing import Optional

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
        # AND THE CONFIGURED NEIGHBOUR COUNT IS KEPT, because the
        # query's default has to come from somewhere.
        self.n_neighbors = n_neighbors
        self.nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
        self._fitted = False

    def fit(self, embeddings: np.ndarray):
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dim:
            raise ValueError(f"expected shape (n,, {self.dim}), got {embeddings.shape}")
        self.nn.fit(embeddings)
        self._fitted = True

    def query(self, emb: np.ndarray, k: Optional[int] = None):
        """The nearest neighbours of `emb`, and their distances.

        **AND `k` DEFAULTS TO THE INDEX'S OWN `n_neighbors`, NOT TO 1.**

        MEASURED 2026-11-06: the default was `k: int = 1`, so an
        index CONFIGURED with `n_neighbors=2` returned ONE neighbour
        unless the caller passed `k` explicitly -- and the constructor
        argument was silently ignored by every caller that relied on
        it. The capability-wiring probe caught it: it built
        `SheafNNIndex(dim=4, n_neighbors=2)`, asked for the neighbours,
        got one, and reported the capability DARK with "the index did
        not return the neighbours it was asked for".

        **A CONFIGURED ARGUMENT THAT THE METHOD IGNORES IS A LIE IN
        THE SIGNATURE.** And this one was not even wrong -- it was
        quietly different, which is worse.

        AND THE COUNT IS CAPPED BY WHAT WAS FITTED, because
        scikit-learn cannot return more neighbours than there are
        points, and asking for more is a RuntimeError there rather
        than an empty result here.
        """
        if not self._fitted:
            return [], []
        want = self.n_neighbors if k is None else int(k)
        if want < 1:
            raise ValueError("k must be at least 1")
        n_fitted = int(getattr(self.nn, "n_samples_fit_", 0) or 0)
        if n_fitted:
            want = min(want, n_fitted)
        distances, indices = self.nn.kneighbors([emb], n_neighbors=want)
        return distances[0].tolist(), indices[0].tolist()

    def __repr__(self) -> str:
        return f"SheafNNIndex(dim={self.dim} fitted={self._fitted})"
