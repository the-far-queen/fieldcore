"""
bitnet_ops.py — ternary operators (per Grok master plan, written 2026-09-16).

Operators:
- ternary_matmul(A, B) -> C
- ternary_quantize(x, threshold=0.7) -> {-1, 0, +1}
- ternary_relu(x) -> x

The latency / accuracy comparison against a BitNet baseline is published in
`fieldcore/papers/publishable/34-bitnet-ternary-substrate-operators-2026-09-15.md`.
"""

from __future__ import annotations

import numpy as np


def ternary_quantize(x: np.ndarray, threshold: float = 0.7) -> np.ndarray:
    """Map real values to {-1, 0, +1} with a dead zone of width (1 - threshold)."""
    out = np.zeros_like(x, dtype=np.int8)
    out[x > threshold] = 1
    out[x < -threshold] = -1
    return out


def ternary_relu(x: np.ndarray) -> np.ndarray:
    """Identity on ternary inputs."""
    return x


def ternary_matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Ternary A, dense B. A is int8 in {-1, 0, +1}.

    Naive but correct: dequantize to {-1, 0, +1} floats, then matmul. The
    latency win comes from a packed-int8 implementation that this stub does
    not yet include.
    """
    if A.dtype != np.int8:
        A = A.astype(np.int8)
    Af = A.astype(np.float32)
    return Af @ B.astype(np.float32)
