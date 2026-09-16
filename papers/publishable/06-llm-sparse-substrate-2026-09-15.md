# LLM Sparse Substrate

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02): "Real topic. Strong if predictions are actually tested. Weak
> if the three predictions stay in markdown." This rewrite turns each
> prediction into a testable hypothesis with code.

## 1. The thesis

Sparse ternary operators can replace dense matmul in the kernel's veto and
ingest paths without measurable accuracy loss. The substrate becomes
lighter; the gate runs faster.

## 2. The three predictions (now tests)

### Prediction A: ternary_matmul matches dense matmul to < 1% relative error.

Test:

```python
import numpy as np
from src.bitnet_ops import ternary_quantize, ternary_matmul

rng = np.random.RandomState(0)
A = ternary_quantize(rng.randn(64, 64))
B = rng.randn(64, 64)

# dense baseline (dequantize A then matmul)
A_dense = A.astype(np.float32)
C_dense = A_dense @ B

# ternary
C_tern = ternary_matmul(A, B)

rel_err = np.max(np.abs(C_tern - C_dense)) / np.max(np.abs(C_dense))
assert rel_err < 0.01, f"rel_err={rel_err}"
```

Status: code in `src/bitnet_ops.py`. Test pending numpy availability. Pass
criterion: relative error < 1%.

### Prediction B: ternary_matmul is at least 1.5x faster than dense matmul on the same shape.

Test:

```python
import time
import numpy as np
from src.bitnet_ops import ternary_matmul

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
```

Status: code stub only. The packed-int8 fast path is not yet written; the
naive version uses float32 and is roughly the same speed as dense. A real
speedup requires packed-int8 with a sign lookup, which is the next
implementation step.

Pass criterion: ternary_matmul at least 1.5x faster than dense matmul.

### Prediction C: the kernel veto is preserved under ternary quantization.

Test:

```python
import numpy as np
from src.tiniest_core import gate, install_ground
from src.bitnet_ops import ternary_quantize

psi0 = install_ground(16)
good = psi0 + 0.05 * np.random.RandomState(0).randn(16)
bad = 5.0 * np.ones(16)

# Same gate before and after ternary quantization of psi0.
ok_g, _ = gate(good, psi0)
ok_b, _ = gate(bad, psi0)
assert ok_g[0] is True
assert ok_b[0] is False

# Ternary quantize psi0; the gate must still reject `bad`.
psi0_q = ternary_quantize(psi0, threshold=0.5).astype(np.float32)
psi0_q = psi0_q / np.linalg.norm(psi0_q)
ok_g2, _ = gate(good, psi0_q)
ok_b2, _ = gate(bad, psi0_q)
assert ok_g2[0] is True, "gate flipped to deny on good packet after quantize"
assert ok_b2[0] is False, "gate flipped to allow on bad packet after quantize"
```

Status: code present in `tiniest_core.py` and `bitnet_ops.py`. Test
pending numpy. Pass criterion: the gate's allow/deny verdicts are
identical before and after ternary quantization of ψ₀.

## 3. What's in this paper

Three falsifiable predictions, each with code and a pass criterion. The
tests live alongside the code in `tests/test_sparse_substrate.py` (to be
written when CI has numpy).

## 4. What's NOT in this paper

- Original proof that ternary operators are universally optimal.
- Novel sparsity theory.
- BitNet comparison at full LLM scale (this paper is the kernel path).

The kernel veto is the only place this paper claims a win. If the
predictions fail, the paper is wrong.
