# Math-Window-1 — Bobby's Geometry + Math (Layer A only)

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). The
> previous version of this document mixed Layer A (textbook math), Layer B
> (real math glued onto toy code), and Layer C (occult physics). Per Grok
> (segment 01, applied 2026-09-16): strip Layer C, retitle Layer A as the
> appendix.
>
> This is now the raw material for the appendix at
> `papers/publishable/14-math-window1-synthesis-2026-09-15.md`. Layer C content
> has been moved to `notes/analogies/`. Layer B (e.g. ResolutionOperator as
> Hodge projection) is held until discrete Hodge on a mesh exists (master
> plan Step 11).

---

## 0. What Bobby gave (the geometry, kept verbatim)

Bobby's geometric intuition, captured across 8 months of substrate work:

- **The egg-toroid.** A tapered tube with a hole. Apex, mid-body, base.
  Three zones of one shape, not three shapes. (Now interpreted as the
  genus-1 Heegaard splitting of `S³`; see `17-egg-toroid-spec`.)
- **The void is the hole (ehole).** The center does not compute. Return-
  to-self is motion toward the interface, not computation inside the hole.
- **Constitutional ground ψ₀.** A marked structure on the interface.
  Installed once; never modified by ordinary tick.
- **Working state ψ.** Moves inside a ball around ψ₀. Drift decays.
- **The kernel veto.** Two inequalities: norm and cosine to ψ₀.
- **The gate is Python.** Determinism at the 1-bit level. The LLM sits
  outside.

All preserved. The geometric statement is correct as a control-system
picture. The mathematical statement is what this document derives.

---

## 1. The ambient space

The architecture lives in `ℝⁿ` for `n = 16` (default). Ground ψ₀ is a unit
vector; ψ is a point that moves in `B_R(ψ₀)`. This is the running numerical
truth. The geometric picture (egg-toroid, `S³`, Hopf fibers) is the
naming of these objects, not a separate ambient.

If and when the architecture moves to a mesh on `T` (master plan Step 11),
the ambient becomes the Clifford torus and the operators become discrete.
Until then, `ℝⁿ` is the working space.

---

## 2. The identity law (per Grok Part III)

**State lives in** `V = ℝⁿ` with Euclidean inner product and norm.

**Ground** `ψ₀ ∈ V` is a fixed unit vector: `||ψ₀|| = 1`.

**Working state** `ψ ∈ V` may be anywhere; the constraint geometry is the
ball

    B_R(ψ₀) = {ψ ∈ V : ||ψ - ψ₀|| ≤ R}

for a chosen radius `R > 0`.

**Drift** is `d(ψ, ψ₀) = ||ψ - ψ₀||`.

**Energy** `F(ψ) = (1/2) ||ψ - ψ₀||²`.

**Gradient** `∇F(ψ) = ψ - ψ₀`.

**Gradient flow** `ψ̇ = -(ψ - ψ₀)`. Solutions are

    ψ(t) = ψ₀ + e^{-t} (ψ(0) - ψ₀).

Drift decays as `e^{-t}`. The Hessian at ψ₀ is the identity, so every
direction decays at the same rate.

**Discrete kernel step** is the projected gradient step:

    ψ ← Π_{B_R(ψ₀)} (ψ - η (ψ - ψ₀)),    η > 0,

where `Π_{B_R(ψ₀)}` is radial projection onto the sphere of radius `R`
around ψ₀.

**Implementation.** `fieldcore/src/tiniest-core/tiniest_core.py:tick` and
`simself/src/constitutional/resolution.py:step`. Both wrap
`project_ball(psi, psi0, R)`.

---

## 3. Convergence (LaSalle)

`F` is non-increasing under the projected gradient step:

    F(ψ(t+1)) - F(ψ(t)) = -η ||ψ - ψ₀||² + O(η²)    (when inside the ball)

so the drift decreases geometrically. The convergence demo
`fieldcore/src/gradient_flow_kernel.py` shows this for any starting
perturbation inside the ball.

LaSalle's theorem (1960) gives the asymptotic statement: every solution
starting in a level set of `F` approaches the largest invariant set in
`{ψ : ∇F(ψ) = 0}`. For our `F`, the only critical point is `ψ₀`, so the
flow returns to ground.

---

## 4. The geometry of the diagram (per Grok Part III)

The architecture's geometric statement is the **genus-1 Heegaard splitting
of `S³`**:

    S³ = V ∪ W,    V ∩ W = T,

where

    V = {(z,w) ∈ S³ : |z| ≥ 1/√2}    (working tube),
    W = {(z,w) ∈ S³ : |w| ≥ 1/√2}    (hole, ehole),
    T = {(z,w) ∈ S³ : |z| = |w| = 1/√2}    (Clifford torus interface).

ψ moves in `V` (the working tube). ψ₀ sits on `T` (the interface). `W` has
no `ψ̇` (the hole does not compute). Restart reads ψ₀ from `T`.

The previous version of this document described a 4-manifold with Heegaard
genus 2. Per Grok: `S⁴` has trisections, not Heegaard splittings. Removed.

---

## 5. The Clifford torus (per Grok Part V)

The Clifford torus

    T = {(z,w) ∈ S³ : |z| = |w| = 1/√2}

is parametrized by angles `(θ, φ)`:

    T(θ, φ) = (1/√2)(cos θ, sin θ, cos φ, sin φ).

The induced metric is

    ds² = (1/2) dθ² + (1/2) dφ².

`T` is flat in this metric (Gaussian curvature 0). `T` is minimal in `S³`
(principal curvatures +1 and -1; mean curvature 0). Among embedded minimal
tori in the round 3-sphere, `T` is the unique model up to isometries of
`S³` (Brendle, 2013).

**Application.** The interface where ψ₀ sits is flat. The flat Clifford
metric is the indexing metric for any future placement of lexicon units at
`(θ, φ)` addresses. Until then, the kernel's Euclidean metric on packet
embeddings is the running distance.

---

## 6. The Hopf map (per Grok Part V)

The Hopf fibration `h: S³ → S²` is

    h(z, w) = (|z|² - |w|², 2zw̄).

Fibers are great circles `ψ ↦ (e^{iψ}z, e^{iψ}w)`. Distinct fibers do not
meet; any two fibers are linked once. The bundle statement is
`S¹ ↪ S³ → S²`.

The level sets of height `|z|² - |w|²` are the surfaces

    T_r = {(z,w) : |z| = cos r, |w| = sin r},    r ∈ [0, π/2].

`T_{π/4}` is the Clifford torus. As `r` varies, `T_r` sweeps a family of
nested tori, each a union of Hopf fibers.

**Application.** `V` = fibers over one hemisphere of `S²`; `W` = fibers
over the other. A stalk is a Hopf-fiber segment from `T_{π/4}` into `V`:
fixed base point on `S²`, varying signed distance `r ≥ π/4` along the
fiber.

---

## 7. Heegaard Floer dictionary (per Grok Part IV)

For the genus-1 case: a pointed Heegaard diagram `(T, α, β, z)`, with `T`
the interface, α meridians of `V`, β meridians of `W`, `z` a marked point
off both curve families.

**Architecture dictionary** (per Grok segment 08):

| Floer object | Architecture object |
|---|---|
| α-curves | working-side conditions: ball membership, ingest type, tool schema |
| β-curves | hole-side conditions: write-protect on ψ₀, no field in W, restart from T |
| generator `x ∈ T_α ∩ T_β` | typed packet that meets both |
| basepoint `z` | the channel that must not carry a ground write |
| Whitney disks missing `z` (hat) | the verdict stream that never crossed the hole |
| Whitney disks passing `z` (U-powers) | filtered log of attempted crossings |
| holomorphic triangles | cobordism / `Ground.revise()` — versioned ground revision |

None of this requires implementation as a moduli space to be the running
model. The dictionary names the rooms.

---

## 8. Number-theoretic facts (kept as tools)

- Twin primes >3 have sum divisible by 12 and product `≡ 11 (mod 12)`.
- `T(p,q)` Seifert genus = `(p-1)(q-1)/2`. For `T(29,31) = 420`. For
  `T(41,43) = 840`.
- `arctan(1/x) + arctan(x) = π/2` for `x > 0`.

These are facts about numbers. They do not justify `constitution.py`
axis cardinality. They do not unify forces. They are not derivations of
fine-structure α. They are just facts.

---

## 9. Layer A vs Layer B vs Layer C

Per Grok segment 01 (applied 2026-09-16):

- **Layer A** = standard textbook math. Cited correctly. Lives here.
- **Layer B** = real math glued onto toy code without a discrete operator.
  Held until discrete Hodge on a mesh exists.
- **Layer C** = occult physics, off-mission speculation. Moved to
  `notes/analogies/`.

The split is operational. A file that talks about Hodge must either
implement discrete Hodge on a mesh (Layer A) or admit it is using Hodge
as a metaphor for a parallel/orthogonal split (Layer B). Files that mix
in α-from-primes or force unification from fractal offsets are Layer C
and have been moved.

---

## 10. Verification table

| Theorem | Where it's used | Where it's verified |
|---|---|---|
| Gradient flow `ψ̇ = -(ψ-ψ₀)` | `tiniest_core.py`, `resolution.py` | `gradient_flow_kernel.py --steps 50` |
| Picard–Lindelöf on `F` | justification for `tick` | Lipschitz constant 1 |
| LaSalle | justification for return-to-ground | drift monotonic in demo |
| Hodge Laplacian `Δ = dd* + d*d` | future discrete Hodge on T | grep returns 0 wrong-form hits in publishable/ and src/ |
| Heegaard splitting of `S³` | `17-egg-toroid-spec` | set-theoretic from definitions |
| Hopf fibers as great circles | stalk definition | linked fibers in `S³` |
| Clifford torus flat + minimal | flat index metric | ds² = (1/2)(dθ² + dφ²) |
| Seifert genus | number-theory | `(p-1)(q-1)/2` for `T(p,q)` |
| Twin-prime `≡ 11 (mod 12)` | number-theory | `(6·1-1)(6·1+1) = 35 ≡ 11` |

---

## 11. Bobby's "harmonic writes to c₀"

Bobby's intuition (per M3-notes): only the harmonic part of a perturbation
has a chance to update ψ₀ in a way that's stable across iterations. The
**standard statement** is: on a closed Riemannian manifold, the harmonic
part of a perturbation (under Hodge decomposition) is time-invariant under
gradient flow, because the harmonic form satisfies `Δh = 0`.

**Status.** This is a theorem for the smooth Hodge decomposition on a
closed Riemannian manifold. For the kernel in `ℝⁿ`, the parallel
projection `⟨ψ, ψ₀⟩ψ₀` plays the role of the harmonic component. A
discrete Hodge on a triangulated `T` would replace this with the harmonic
1-form. Until that exists, the parallel projection is the running
substitute.

**Used by.** `simself/src/constitutional/lexicon/ingest.py:commit`
promotes admitted units to committed when close to ψ₀ (within
`commit_radius`). The parallel/orthogonal split is the gating signal.

---

## 12. Bobby's "6-AI team as the chain"

Bobby's intuition (per M3-notes): each AI in the team encodes the previous
in a gradient flow. The chain works because each layer's encoding is
visible to the next.

**Status.** This is a framing, not a theorem. The team does work as
described (Grok = language, GPT = math, etc.) but the gradient-flow
analogy is a metaphor, not a derivation. Held as a working method, not
as a math result.

---

## 13. What stays in this document vs the appendix

This document (`docs/Math/math-window-1.md`) is the **raw material** for
the appendix at
`papers/publishable/14-math-window1-synthesis-2026-09-15.md`. The appendix
is the journal-form statement. This file is the development notebook.

If a fact is in both, the appendix is the canonical version. If a fact is
only here, it is a working note, not yet promoted to the appendix.

---

## 14. References

- Brendle, S. (2013). *Embedded minimal tori in S³.*
- Hopf, H. (1931). *Über die Abbildungen von S³ auf S².*
- Lindelöf, E. (1894); Picard, É. (1890). Existence and uniqueness for ODEs.
- LaSalle, J. P. (1960). *Some extensions of Liapunov's second method.*
- Waldhausen, F. (1968). *Heegaard-Zerlegungen der 3-Sphäre.*
- Ozsváth, P.; Szabó, Z. (2004). *Holomorphic disks and topological
  invariants for closed three-manifolds.*

---

## 15. Cross-references

- `fieldcore/papers/publishable/14-math-window1-synthesis-2026-09-15.md`
  — the appendix (canonical).
- `fieldcore/papers/publishable/17-egg-toroid-spec-2026-09-15.md` — the
  geometric statement.
- `fieldcore/papers/publishable/22-fieldcore-one-read-2026-09-15.md` —
  the public front door.
- `simself/papers/publishable/01-atlas-exam-simself-2026-09-15.md` —
  the qualification exam.
- `simself/docs/grok2-master-plan-2026-09-16.md` — the master plan.
