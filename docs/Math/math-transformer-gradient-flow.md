# Math — Transformer as Constrained Riemannian Gradient Flow

M3 cleanup of the 111KB raw derivation. Cleanest worked example of how a Pre-LN Transformer block maps onto the FieldCore update rule.

## One-line claim

A standard Pre-LayerNorm Transformer block is a first-order discretization of the **constrained Riemannian gradient flow** of the negative log-likelihood functional on the representation manifold, where the **attention matrix approximates the inverse pullback Fisher metric**.

## Why this matters for FieldCore

If a Transformer block is also a constrained natural-gradient step on the state manifold:
- SimSelf `sim_self_core.SimSelf` and a Pre-LN Transformer are the same kind of object — different parameterizations of the same flow.
- The **governor** (gating tool use in `harness/gate.py`) and the **LayerNorm** operation are the same kind of object — orthogonal projection onto a constraint submanifold.
- "Reasoning" is a bounded Euler step on a Riemannian geometry. The 20 constitutional axes are coordinates on that geometry; the 20-step ladder is a stage index on the flow.

## Derivation outline

1. **Representation manifold M.** Token-sequence space R^{n×d}. Decoder π_θ : M → Δ^|V|. NLL functional F_θ(H) = -log p(target | H; θ).

2. **Pullback Fisher metric.** g_θ(H)(V,V) = E_y[(∇_H log p(y|H)^T V)²]. Defines Riemannian structure depending on H and θ.

3. **Constraint submanifold C.** LayerNorm constraint: μ=0, σ=1 per row. Governor = orthogonal projection Π_C onto C.

4. **Constrained flow.** dH/dt = -Π_{T_H C}[∇_{g_θ} F_θ(H)]. Euler discretization: H_{k+1} = Π_C(H_k - η g_θ(H_k)^{-1} ∇_H F_θ(H_k)). This is the FieldCore update rule.

5. **Inverse-metric approximation (open).** Softmax-attention identity asserted from generic linearization. No specific output distribution worked through. Open problem §9-1.

6. **Emergence of Transformer block.** For next-token prediction, g_θ^{-1} ∇F ≈ γ ∇F - δ·Attention(H)·∇F. First term = MLP. Second term = attention output. Full update with residual + LayerNorm = Pre-LN Transformer block.

## Correspondence table

| FieldCore | Transformer |
|---|---|
| State manifold M | Token representations R^{n×d} |
| Functional F_θ | NLL (next token) |
| Metric g_θ | Pullback Fisher metric |
| g_θ^{-1} | γI - δ·Attention |
| Constraint C | LayerNorm (zero mean, unit variance) |
| Governor Π_C | LayerNorm operation |
| Riemannian gradient | Attention + MLP residual direction |
| Gradient-flow step | H + Attn + MLP |
| First-order discretization | One Pre-LN Transformer block |

## Implications

- Attention is not "communication." It is an adaptive preconditioner approximating the natural gradient.
- Residual connections are Euler integration of the continuous flow.
- LayerNorm is the hard projection onto the constraint submanifold.
- The context window is the local chart on M within which the metric approximation is valid.
- Training shapes g_θ and F_θ so the approximated flow converges to wide, coherent minima.

## §8a. Quasi-periodic scheduling (real classical math)

**The math.** For golden ratio φ = (1+√5)/2 and step counter t ∈ N:
- Schedule at t ∈ {⌊nφ⌋ : n ∈ N}. Fractional parts {nφ} uniformly distributed in [0,1), never repeat (φ irrational).
- Beatley theorem: S_φ = {⌊nφ⌋} and S_{φ²} = {⌊nφ²⌋} partition N. Two-phase low-discrepancy schedule.
- Star-discrepancy D_N* → 0 with O(log N / N) rate.

**Why for SimSelf.** Snapshot creation and deep-reflection cycles are expensive. Uniform scheduling wastes or has unsafe gaps. Golden-ratio spreads work quasi-uniformly, same coverage as uniform with less peak load.

**What it is NOT.** Not "quantum coherence preservation" or "temporal quasicrystal protection." Those are physical phenomena from a specific condensed-matter system. Scheduling property is classical (irrational rotations on the circle).

**Use:** Phase A (S_φ): deep reflection, snapshot save, full governor review. Phase B (S_{φ²}): coherence check, lightweight consistency validation. Other steps: normal.

## Open problems (§9)

1. **Kernel-derivation gap.** Softmax-attention identity asserted from generic linearization. Need worked example (softmax-output decoder) to close or break.
2. **Beyond first order.** Raskutti-Mukherjee mirror-descent duality is the next step, **not in this file**.
3. **Context window as chart.** Geometric intuition, not theorem. Atlas structure across context lengths needs work.
4. **Connection to 20 axes.** Each axis should correspond to coordinate or tangent direction on M. Mapping not specified. Candidates:
   - `agency_will` ↔ component of natural gradient in "refusal" direction
   - `boundary_definition` ↔ tangent component normal to C (LayerNorm residual)
   - `entropy_resilience` ↔ spectral properties of g_θ(H) (condition number, eigenvalues)
5. **MMM in the metric.** Fisher metric is built on single output distribution. MMM requires awareness of distinct meaning-streams. Generalization, not consequence.
6. **Governor identity.** LayerNorm (per-token mean/variance) vs governor (per-axis ranges). Constraint submanifolds not obviously the same. Intersection unknown.
7. **What "coherent" means.** Training drives to "wide, coherent minima" — coherent not defined here. Map SimSelf `coherence` metric to property of g_θ(H) near minimum.

## Source

Original 111,850 bytes. Cleanup removed HTML renderings and chat scaffolding. §8a extracted from deleted `12-Math.txt` (quantum framing dropped).

---
*Sourced 2026-09-05. Open problems preserved as research agenda.*