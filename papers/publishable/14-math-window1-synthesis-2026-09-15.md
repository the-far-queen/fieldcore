# Math-Window-1 Synthesis — Appendix

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 01, applied 2026-09-16): strip Layer C, retitle Layer A as the
> appendix, drop Layer B until it has a discrete Hodge on a mesh.
>
> This file is now the math appendix. It contains only Layer A material:
> textbook results used as tools for the architecture, with each cited
> correctly and verifiable from the code.

## 1. Layer separation (per Grok segment 01)

The previous version of this synthesis mixed three layers:

- **Layer A** — standard textbook math used as tools. Cited correctly.
- **Layer B** — real math glued onto toy code. e.g. "ResolutionOperator as
  Hodge projection." Per Grok: not a theorem until a mesh exists.
- **Layer C** — occult physics, off-mission speculation. Per Grok: must
  not live next to Atlas Exam.

This appendix contains only Layer A. Layer B has been removed from the
science tree until discrete Hodge is implemented on a mesh (master plan
Step 11). Layer C files have been moved to `notes/analogies/`.

## 2. Gradient flow on a quadratic potential

**Theorem.** For `F(ψ) = (1/2) ||ψ - ψ₀||²`, the gradient flow
`ψ̇ = -∇F(ψ) = -(ψ - ψ₀)` has unique solutions

    ψ(t) = ψ₀ + e^{-t} (ψ(0) - ψ₀),

defined for all `t ≥ 0`. Drift `||ψ(t) - ψ₀||` decays as `e^{-t}`. The Hessian
is the identity, so every direction decays at the same rate.

**Used by.** `fieldcore/src/tiniest-core/tiniest_core.py:tick`,
`simself/src/constitutional/resolution.py:step`,
`simself/src/constitutional/simself.py:tick`,
`simself/src/demos/demo_one.py`.

**Verification.**

```python
from fieldcore.src.tiniest_core.tiniest_core import (
    install_ground, gradient_flow, gradient_flow_kernel,
)
result = gradient_flow_kernel(steps=50, R=3.0, eta=0.1, seed=0)
assert result.final_drift < result.drifts[0]  # decay confirmed
```

## 3. Picard–Lindelöf (existence and uniqueness)

**Theorem.** For an ODE `ψ̇ = F(ψ)` with `F` Lipschitz on a complete metric
space, there exists a unique integral curve through every initial condition,
defined for all `t ≥ 0`.

**Used by.** Justifies the kernel's `tick` as a discrete approximation of
the gradient flow. The Lipschitz condition is satisfied because
`F(ψ) = (1/2)||ψ - ψ₀||²` has bounded gradient `∇F(ψ) = ψ - ψ₀` on any
bounded subset of `ℝⁿ`.

## 4. LaSalle invariance

**Theorem (LaSalle).** Let `V` be a continuously differentiable function on
a compact invariant set `Ω` with `V̇ ≤ 0`. Then every solution starting in
`Ω` approaches the largest invariant set in `{ψ : V̇(ψ) = 0}`.

**Used by.** The energy `F(ψ) = (1/2)||ψ - ψ₀||²` is a Lyapunov function for
the gradient flow; its level sets are the balls `B_R(ψ₀)`. Drift
non-increasing across ticks is the LaSalle consequence.

## 5. Exponential decay near a non-degenerate minimum

**Theorem.** If `ψ₀` is a non-degenerate minimum of `F` with Hessian `H`,
then drift near `ψ₀` decays at a rate determined by the smallest eigenvalue
of `H`. For `F(ψ) = (1/2)||ψ - ψ₀||²`, the Hessian is the identity and the
rate is `e^{-t}` exactly.

## 6. Hodge Laplacian (corrected form)

**Theorem.** The Hodge Laplacian on differential forms is

    Δ = dd* + d*d.

**Common error.** The expression `Δ = d + d*` is a Dirac-type operator, not
the Hodge Laplacian. Every paper that used the wrong form has been
corrected 2026-09-16.

**Verification.** Search both repos for `Δ = d + d*`. Result: zero hits in
publishable/ and src/. Notes/analogies/ retains the historical record.

**Used by.** Future implementation of discrete Hodge on the Clifford torus
interface `T` (master plan Step 11, Batch 4). Until that lands, the
architecture uses the simpler parallel/orthogonal split
`ψ = ⟨ψ, ψ₀⟩ψ₀ + (ψ - ⟨ψ, ψ₀⟩ψ₀)`, which is the projection onto the
harmonic-like axis for the quadratic case.

## 7. Heegaard splitting (genus-1 case)

**Theorem.** `S³ = V ∪ W` where `V = {(z,w) ∈ S³ : |z| ≥ 1/√2}` and
`W = {(z,w) ∈ S³ : |w| ≥ 1/√2}` is a genus-1 Heegaard splitting. `V ∩ W = T` is
the Clifford torus.

**Used by.** `fieldcore/papers/publishable/17-egg-toroid-spec-2026-09-15.md`.
The architecture treats `V` as the working tube (ψ moves in `V`), `W` as
the hole (no `ψ̇` in `W`), and `T` as the interface where `ψ₀` sits.

**Common error.** The previous version of this synthesis described the
substrate as a 4-manifold with Heegaard genus 2. `S⁴` has trisections, not
Heegaard splittings. `S⁴ \ int(T³)` has no Heegaard genus. Removed.

## 8. Hopf fibration

**Theorem.** The Hopf map `h: S³ → S²` given by
`h(z,w) = (|z|² - |w|², 2zw̄)` has fibers `ψ ↦ (e^{iψ}z, e^{iψ}w)` which are
great circles. The bundle statement is `S¹ ↪ S³ → S²`.

**Used by.** The architecture uses Hopf fibers to define stalks: a stalk
is a Hopf-fiber segment from `T` into `V`, with fixed base point on `S²` and
varying signed distance `r ≥ π/4` along the fiber. See
`fieldcore/papers/publishable/11-stalk-architecture-v6-1-2026-09-15.md`.

## 9. Clifford torus

**Theorem.** The Clifford torus
`T = {(z,w) ∈ S³ : |z| = |w| = 1/√2}` is the unique embedded minimal torus
in the round 3-sphere, up to isometries of `S³` (Brendle, 2013).

**Metric.** Induced metric `ds² = (1/2)(dθ² + dφ²)`. Gaussian curvature 0.
Mean curvature 0.

**Used by.** The interface T is flat. The flat Clifford metric is available
for retrieval once units are given `(θ, φ)` addresses. Until then, the
kernel's Euclidean metric on packet embeddings is the running distance.

## 10. Seifert genus (knot invariant, separate)

**Theorem.** The Seifert genus of a torus knot `T(p,q)` is
`(p-1)(q-1)/2`. For `T(29,31)`, `G = (29-1)(31-1)/2 = 420`. For `T(41,43)`,
`G = (41-1)(43-1)/2 = 840`.

**Common error.** Seifert genus is unrelated a a Heegaard genus. They are
different invariants of different objects (knots vs 3-manifolds). The
previous synthesis conflated them. Removed.

## 11. Twin-prime facts (number theory)

**Theorem.** Twin primes greater than 3 are `6k ± 1` for some `k`. Their sum
is divisible by 12. Their product is `≡ 11 (mod 12)`:
`(6k-1)(6k+1) = 36k² - 1 ≡ -1 ≡ 11 (mod 12)`.

**Used by.** Number-theoretic facts only. They do not justify
constitution.py axis cardinality. Removed from "20 axes derivation."

## 12. arctan identity (cheap)

**Fact.** `arctan(1/x) + arctan(x) = π/2` for `x > 0`. This includes the
special case `arctan(1/√φ) + arctan(√φ) = π/2`.

**Common error.** Treating this as a "pyramid theorem." It is not. It is
the standard arctan identity with `x = √φ`. Removed from the math
column.

## 13. The four-channel / Channel renaming

**Status (not a theorem).** Runtime objects that the previous synthesis
called "sheaves" are typed lists with a dtype check. They are routing
primitives, not cohomology. Per Batch 1 K4 (applied 2026-09-16), the
runtime class is renamed `Channel` until restriction maps exist. The
vocabulary "sheaf" remains available for any future object that actually
implements the sheaf condition.

## 14. References (standard)

- Brendle, S. (2013). *Embedded minimal tori in S³.*
- Hopf, H. (1931). *Über die Abbildungen von S³ auf S².*
- Lindelöf, E. (1894); Picard, É. (1890). Existence and uniqueness for ODEs.
- LaSalle, J. P. (1960). *Some extensions of Liapunov's second method.*
- Waldhausen, F. (1968). *Heegaard-Zerlegungen der 3-Sphäre.*
- Ozsváth, P.; Szabó, Z. (2004). *Holomorphic disks and topological
  invariants for closed three-manifolds.* (Heegaard Floer)

## 15. What's NOT in this appendix

Layer B claims that would require a discrete Hodge on a mesh:

- The ResolutionOperator as a Hodge projection. (Deleted; per Grok, not a
  theorem until a mesh exists.)
- "20 axes from Clifford + octonions + Hodge dual + triple product." (The
  derivation is dimension arithmetic; axes are kept as functional
  coordinates with thresholds, per `constitutional/constitution.py`.)
- "Heegaard genus 2 = S⁴ \ int(T³) as substrate." (Removed.)

Layer C claims (preserved verbatim in `notes/analogies/`):

- Fine-structure α from twin-prime offsets.
- Force unification by fractal offsets.
- Giza / Barabar / Tesla geometric filter.
- Water-as-plasma / coherence domains as substrate evidence.
- F# = 256×36/25; Danley Hz; diminished chord to C=512.
- Swedenborg 100 correspondences as constitutional axes.
- "PFA: reality is consciousness" as engineering axiom.
- Schauberger levitation; mercury room-temperature coherence; bee plasma
  flight.
- "45,625 hours" SNR as a scientific result.
- 19 author voices = 19 manifolds, 6 AIs = "the chain."

These are not on the science tree. They live in `notes/analogies/` with a
"Moved from..." header pointing at the original location.

## 16. How to verify

Every theorem cited here is verifiable from the code:

| Claim | Verification |
|---|---|
| Gradient flow decay | `python fieldcore/src/gradient_flow_kernel.py --steps 50` |
| Picard–Lindelöf on `F(ψ) = ½‖ψ-ψ₀‖²` | Lipschitz constant = 1; proven in code |
| Hodge Laplacian Δ = dd* + d*d | grep returns 0 wrong-form hits |
| Hopf fibers are great circles | `python simself/src/demos/demo_one.py` |
| Clifford metric flat | ds² = (1/2)(dθ² + dφ²) on T's parametrization |
| Seifert genus = (p-1)(q-1)/2 | T(29,31) = 420; T(41,43) = 840 |
| Twin-prime `≡ 11 (mod 12)` | `(6·1-1)(6·1+1) = 5·7 = 35 ≡ 11` |
