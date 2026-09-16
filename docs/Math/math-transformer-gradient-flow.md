# Math-Transformer Gradient Flow

> **"** Verified 2026-09-16 (per Grok master plan, applied by Hermes). Standard
> gradient flow on a quadratic energy. Used as the canonical running flow
> by the kernel, the resolution operator, and the canonical SimSelf.

## 1. The energy

    F(ψ) = (1/2) ||ψ - ψ₀||².

## 2. The gradient

    ∇F(ψ) = ψ - ψ₀.

## 3. The flow

    ψ̇ = -∇F(ψ) = -(ψ - ψ₀).

Solutions:

    ψ(t) = ψ₀ + e^{-t} (ψ(0) - ψ₀).

Drift decays as `e^{-t}`.

## 4. The discrete step

    ψ_{k+1} = Π_{B_R(ψ₀)} (ψ_k - η (ψ_k - ψ₀))

with `η > 0` and `Π_{B_R(ψ₀)}` radial projection onto the ball.

## 5. Why this matters

The projected gradient step is the only motion allowed in the identity
layer. The kernel's `tick`, the resolution operator's `step`, and the
canonical SimSelf's `tick` all use this step (or a tightly related
variant). Any other update rule is a deviation from the identity law.

## 6. Used by

- `fieldcore/src/tiniest-core/tiniest_core.py:tick`
- `simself/src/constitutional/resolution.py:step`
- `simself/src/constitutional/simself.py:tick`
- `fieldcore/src/gradient_flow_kernel.py`

## 7. Verification

```python
from fieldcore.src.tiniest_core.tiniest_core import gradient_flow_kernel

result = gradient_flow_kernel(steps=50, R=3.0, eta=0.1, seed=0)
assert result.drifts[0] > result.drifts[-1], "drift did not decay"
```

## 8. References

- Picard–Lindelöf (existence + uniqueness): the flow is well-posed.
- LaSalle (1960): every solution in a level set of `F` approaches the
  largest invariant set in `{ψ : ∇F(ψ) = 0}`. For our `F`, the only
  critical point is ψ₀.
