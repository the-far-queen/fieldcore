# BitNet Ternary Substrate Operators

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02, applied 2026-09-16): "Strongest modern-AI paper if you implement
> ops and compare to BitNet." This paper now contains the implementation.

## 1. What this paper is

Ternary weight operators (-1, 0, +1) used in the substrate's ingest path. The
goal is to compare the latency and accuracy of ternary operators to a standard
BitNet baseline.

## 2. Operators

Three operators, all defined on `int8` packed tensors:

- `ternary_matmul(A, B) -> C`: A is `(-1, 0, +1)`, B is dense. Implemented as
  a packed-int8 dot product with a sign lookup. Implementation:
  `fieldcore/src/bitnet_ops.py`.
- `ternary_quantize(x, threshold=0.7) -> {-1, 0, +1}`: per-element threshold
  quantizer with dead-zone.
- `ternary_relu(x) -> x`: identity for ternary inputs.

## 3. Latency comparison

Method:

1. Generate a fixed random dataset: shape `(1024, 1024)` ternary A, `(1024,
   1024)` dense B.
2. Run `ternary_matmul` 100 times, measure mean and p99 latency.
3. Run `numpy.matmul` on the same data (B dense, A dequantized) for
   comparison.
4. Publish the numbers.

## 4. Accuracy comparison

Method:

1. Take a small classification task (e.g. MNIST subset, 10k samples).
2. Train a one-layer ternary linear classifier. Implement the forward pass
   with `ternary_matmul`.
3. Compare test accuracy to a one-layer dense baseline.
4. Publish the numbers.

## 5. Status

Implementation: `fieldcore/src/bitnet_ops.py` — written 2026-09-16 per this
rewrite. Latency and accuracy numbers: pending. Until they are published, this
paper is a position note.

## 5. References

- BitNet: Scaling 1-bit Transformers for Large Language Models (Ma et al., 2024).
