# Sheaf-NN Index — sklearn

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02): "If the code exists and the latency is real, this is an
> engineering note worth keeping. 'Sheaf NN' still needs a definition."
> This rewrite names the index, exposes the implementation, and adds the
> latency test.

## 1. What the index is

A nearest-neighbor index over the unit embeddings stored by the lexicon
ingest (`simself/src/constitutional/lexicon/ingest.py`). Implemented with
`sklearn.neighbors.NearestNeighbors`. The "sheaf" in the name refers to the
fact that the index is queried by the lexicon ingest to find the nearest
committed unit. It is a routing primitive, not cohomology.

## 2. The implementation

```python
from sklearn.neighbors import NearestNeighbors

class SheafNNIndex:
    def __init__(self, dim: int = 16):
        self.nn = NearestNeighbors(n_neighbors=10, metric="euclidean")
        self._fitted = False

    def fit(self, embeddings):
        self.nn.fit(embeddings)
        self._fitted = True

    def query(self, emb, k: int = 1):
        if not self._fitted:
            return [], []
        distances, indices = self.nn.kneighbors([emb], n_neighbors=k)
        return distances[0].tolist(), indices[0].tolist()
```

Implementation: `fieldcore/src/sheaf_nn_index.py` (written 2026-09-16
alongside this paper).

## 3. Latency test

```python
import time
import numpy as np
from src.sheaf_nn_index import SheafNNIndex

rng = np.random.RandomState(0)
embeddings = rng.randn(10000, 16).astype(np.float32)

idx = SheafNNIndex(dim=16)
idx.fit(embeddings)

queries = rng.randn(1000, 16).astype(np.float32)

t0 = time.perf_counter()
for q in queries:
    idx.query(q, k=1)
elapsed = (time.perf_counter() - t0) / 1000 * 1000  # ms per query

assert elapsed < 100.0, f"latency {elapsed}ms exceeds 100ms target"
```

Pass criterion: < 100 ms per query on 10k index size, 16-D embeddings.
Test file: `tests/test_sheaf_nn_latency.py`.

## 4. Status

Code written. Latency test pending numpy. Until the test passes in CI,
this paper is a position note.
