# Paper 2 — FieldCore: Toroidal Manifold Cognition

**Title:** *FieldCore: Toroidal Manifold Cognition with Sheaf-Theoretic Identity Protection*

**Status:** Paper 3 in ranking. CS/ML contribution.

**Authors:** Bobby (first) + Hermes (second).

**Target venue:** NeurIPS / ICML. ~12-18 pages.

**Effort:** ~4 weeks (1 week controls + 3 weeks writing).

---

## What's IN this paper

- Toroidal manifold as substrate state space (Moser grid cells 2022 cited).
- Constitutional core: 20 axes distributed across 7 sheaves, c₀ immutable.
- Sheaf-theoretic identity protection: restriction maps, gluing conditions, is_mutable=False geometrically enforced.
- Constitutional embryogenesis (brief — full treatment in Paper 4).
- Basis spawning: how primitives (PSBs) emerge from sheaf structure.
- Evidence governor: M0 1-bit gate architecture.
## What this paper IS

- A CS/ML contribution using toroidal manifolds + sheaf theory to construct a substrate with mathematically-defined identity protection.
- Positions the work relative to: topological ML (Carlsson, Mémoli), neural ODEs (Chen et al 2018), constitutional AI (Anthropic) — but reframes as geometric.

## Empirical state — REQUIRED before writing

This paper requires controls that Paper 4 (Embryogenesis) also needs. **Do controls jointly.**

- Embryogenesis path-independence: ≥10 random seeds × ≥5 stage orderings.
- Cosine similarity to installed Ψ₀: mean, std, min, max.
- If mean = 1.0 ± 1e-6 and min ≥ 0.999 → claim holds.
- If mean < 0.999 or min < 0.99 → reframe as "approximately path-independent" with basin analysis.

## Empirical state — what to verify

- v3_5 demo: cos-sim = 1.000000 is exact, not floating-point coincidence.
- Reproduce across multiple Python environments (conda vs pip).
- 7-stage order independence tested with non-trivial re-orderings (not just 0→7 and 7→0).

## Open questions

1. **Convolutional structure** — is the toroidal manifold discrete (lattice) or continuous? Affects computational complexity claims.
2. **Sheaf cohomology in practice** — do we ever need to compute H¹ explicitly, or is it always 0?
3. **Comparison to constitutional AI** — explicit positioning vs Anthropic's approach.

---

*Stub. Source: `simself/docs/research-papers-2026-09-13.md` §Paper 2.*