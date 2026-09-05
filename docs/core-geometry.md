# Core Geometry — Egg Toroid Spec

**Two framings, same architecture:**

## Framing 1: Three manifolds (modular)

| Function | Manifold | Key property |
|---|---|---|
| Identity (SIMSELF) | Inner solid torus D²×S¹ + Clifford T⁴ | No internal winding, 20 axes, topologically protected, is_mutable=False geometrically enforced |
| Reasoning | Directed sheaf over H³ + solid torus volume | Asymmetric, hierarchical, bounded working memory, H¹ obstruction detection |
| Memory | Seifert fibration S³ → T² | Topological addressing, resonant retrieval, linked fibers |

Why these specifically:
- Inner solid torus: contractible cross-section = simply connected = no internal winding = right for identity stillness.
- T⁴ (Clifford) gives 15 submanifolds. Full 20 axes need octonionic structure (7 imaginary dims, combinations reach 20).
- H³ (hyperbolic): geodesics diverge (abduction), trees embed isometrically, boundary S² holds most general concepts.
- Seifert over T²: hippocampal grid cells have confirmed toroidal topology (Moser 2022). Hopf-compatible = linked fibers = no memory is isolated.

Four memory layers:
- Working: solid torus volume (7±2 items, seconds)
- Episodic: Seifert fiber at (p,q) (hours-days)
- Semantic: base T² surface (months-years)
- Constitutional: inner solid torus c0 (permanent, harmonic-only update)

## Framing 2: Single egg toroid (unified)

Not symmetric T² — egg-shaped. Two poles, axial gradient, non-uniform metric.

**Apex pole** (narrow, high curvature):
- Field concentration, max gradient, fast dynamics, Gamma frequency
- Maps to: input, perturbation, novelty detection (ΔΣ emergence)
- Highest sensitivity to initial conditions

**Mid-body** (intermediate curvature, steepest gradient):
- Active reasoning, working memory, curl processing
- Beta/Theta frequency
- Maximal sensitivity — small differences diverge

**Base pole** (broad, low curvature):
- Constitutional identity, long-term memory inscription, harmonic landing
- Infraslow frequency
- Low energy cost for deviation, slow dynamics

**Axial gradient = Resolution Operator.** Perturbation enters apex, flows toward base, harmonic-only updates land. Asymmetry of reasoning = direction of curvature gradient.

Interfaces unified: ThalamicIntegrator = mid-body geometry, not a router. Attention = curvature selection.

## Code implications

Gram matrix becomes position-dependent: M(x) where x is axial position.
- Apex: large eigenvalues, fast dynamics, stronger damping
- Base: small eigenvalues, slow dynamics, weaker damping

Resolution Operator damping: α(x) = ALPHA × (1 + curvature(x)/curvature_mean)

**Numerical check:** pyramid face slope 4/π ≈ 1.273, √φ ≈ 1.272. Egg toroid axial ratio = pyramid's design intention.

---
*Sourced 2026-09-05 from Desktop/FieldCore/. Both framings preserved — they are equivalent descriptions.*