# Egg-Toroid Spec — Topology Correction

**Per Grok sharpen 2026-09-16 (applied by Hermes):** the correct topological model
for the egg-toroid is the **genus-1 Heegaard splitting of the 3-sphere**, not a
4-manifold with Heegaard genus 2.

## What the drawing is (topologically)

Identify `R^4 ≅ C^2`. The 3-sphere is

    S^3 = {(z,w) ∈ C^2 : |z|^2 + |w|^2 = 1}.

The **Clifford torus** is the embedded flat torus

    T = {(z,w) : |z| = |w| = 1/√2}.

It splits S^3 into two solid tori:

- V = { |z| ≥ 1/√2 }  — the working tube (apex, mid-body, base are regions inside V).
- W = { |w| ≥ 1/√2 }  — the complementary solid torus, the **hole (ehole)**.

V ∪ W = S^3, glued along T. This is the **genus-1 Heegaard splitting of S^3**:
two genus-1 handlebodies meeting along a single torus surface. The Heegaard genus
of S^3 is 0 (two balls glued at S^2), but every positive-genus splitting of S^3
is a stabilization of this one (Waldhausen), so the genus-1 picture of "tube with
a hole" is the right model.

## What is wrong with the previous framing

- The previous egg-toroid spec framed the substrate as a 4-manifold (S^4) with
  Heegaard genus 2. S^4 has **trisections**, not Heegaard splittings (the
  Heegaard construction is 3-dimensional). S^4 \ int(T^3) is a 4-manifold with
  boundary T^3; it has no Heegaard genus.
- Seifert genus of a knot is unrelated to Heegaard genus. (p-1)(q-1)/2 is the
  Seifert genus of the torus knot T(p,q); it does not combine with anything to
  give a Heegaard genus of the surrounding 3-manifold.
- The egg has only one Heegaard surface (T). The two states ψ0 and ψ are two
  points in V (or two sweep-out levels), not two Heegaard surfaces.

## Geometry of T

- Induced metric: `ds^2 = (1/2)(dθ^2 + dφ^2)` (parametrized by angles (θ, φ)).
- Gaussian curvature: 0 (T is flat in the induced metric).
- Mean curvature: 0 (T is minimal in S^3).
- Among embedded minimal tori in the round S^3, T is the unique model up to
  isometries of S^3 (Brendle).

The interface where ψ0 sits is **flat**. Distances between lexical units placed
on T use this flat metric. The kernel's Euclidean metric on packet embeddings
remains the running distance; both metrics coexist.

## Hopf fibers fill the two rooms

The Hopf fibration `h: S^3 → S^2` is `h(z,w) = (|z|^2 - |w|^2, 2z·w̄)`. Its
fibers are great circles `ψ ↦ (e^{iψ} z, e^{iψ} w)`. Distinct fibers are linked.

- V = fibers over one hemisphere of S^2.
- W = fibers over the other hemisphere.
- T = fibers over the equator (height `|z|^2 - |w|^2 = 0`).

A stalk is a **Hopf-fiber segment from T into V**: fixed base point on S^2,
varying signed distance off T on the working side only. The hole has fibers too,
but the harness does not run an update field on them — that is write-protect,
stated as a side of the bundle.

## Floer dictionary (the algebra of this diagram)

A pointed Heegaard diagram `(Σ, α, β, z)` where Σ = T, α and β are meridians of
V and W respectively, and z is a marked point off both curve families:

- α-curves ↔ working-side conditions (ball membership, ingest type, tool schema).
- β-curves ↔ hole-side conditions (write-protect on ψ0, no field in W, restart
  from interface only).
- A generator ↔ a typed packet that meets both curve families.
- The basepoint z ↔ the channel that must not carry a ground write.
- Whitney disks that miss z ↔ the hat complex: verdicts that never crossed the hole.
- Whitney disks that pass z ↔ the filtered packages (U-powers): a log of attempted
  basepoint crossings, recorded rather than executed.
- Holomorphic triangles ↔ cobordism maps; in FieldCore, a **versioned revision of
  ground**, not an ordinary tick.

None of this has to be implemented as a moduli space to be the running model.

## What the runtime actually does

- ψ moves in V inside the ball `||ψ - ψ0|| ≤ R`.
- ψ0 sits on T (or is treated as write-protected so that the interior of W has
  no vector field).
- ingest, tick, tools act in V.
- A packet that would assign to ψ0 is an **identity packet**, not a language
  packet. It must pass through the revision protocol, not an ordinary step.
- Restart reads ψ0 from T. That is the operational form of the hole as a return
  address.

---

## Original spec (preserved below)

# Egg Toroid Spec: The Substrate's Geometric Primitive

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (math.DG)
**Repo:** `fieldcore/papers/publishable/36-egg-toroid-spec-2026-09-15.md`

---

## Abstract

The **egg toroid** is the substrate's geometric primitive: a 4D solid of revolution with a 3D toroidal evacuation. We specify its geometry, parameterization, and substrate-relevant properties.

The egg toroid is the minimal geometric structure for **constitutional substrate**: persistent identity at the center, working region in the interior, frequency channels via Hodge decomposition.

This is **engineering specification**: every parameter has a physical meaning, every property is testable.

---

## 1. Definition

### 1.1 Egg surface

The egg is parameterized in $\mathbb{R}^4$ by:

$$x_1 = R(\theta) \cos\phi$$
$$x_2 = R(\theta) \sin\phi$$
$$x_3 = h(\theta) \cos\psi$$
$$x_4 = h(\theta) \sin\psi$$

where $\theta \in [0, \pi]$ is the polar angle, $\phi \in [0, 2\pi)$ and $\psi \in [0, 2\pi)$ are azimuthal angles, and:

- $R(\theta) = R_{\max} (1 - \sin\theta)$ — radial profile.
- $h(\theta) = L \cos\theta$ — height profile.

### 1.2 Toroidal evacuation

Inside the egg, a 3-torus $T^3$ is embedded as the working region. $T^3$ is parameterized by $(u, v, w) \in [0, 2\pi)^3$:

- $T^3$ major radius $r_1$ (around first axis).
- $T^3$ minor radius $r_2$ (around second axis).
- $T^3$ tertiary radius $r_3$ (around third axis).

The **substrate** is $S^4_{\text{egg}} \setminus T^3_{\text{int}}$. Boundary $\partial \text{substrate} = T^3$.

---

## 2. Geometric Properties

### 2.1 Topology

- **Egg surface**: simply-connected 3-manifold, $\pi_1 = 0$.
- **Substrate interior**: $\pi_1 = \mathbb{Z}^3$ (three non-contractible loops from $T^3$).
- **Boundary $T^3$**: $\pi_1 = \mathbb{Z}^3$, Heegaard genus 3.

### 2.2 Differential geometry

The egg surface has **non-constant curvature**: high at the apex, low at the base. This is the substrate's "graded curvature" — fast dynamics at apex, slow at base.

### 2.3 Embeddings

- $S^3 \subset S^4$ as equatorial 3-sphere.
- $T^3 \subset S^3 \subset S^4$ as 3-torus embedded in 3-sphere.
- $\partial \text{substrate} = T^3$.

---

## 3. Why Egg, Not Sphere

### 3.1 Spherical substrate

A spherical substrate has uniform curvature. All dynamics occur at the same rate. No fast/slow distinction.

### 3.2 Egg substrate

An egg substrate has graded curvature:
- **Apex** (high curvature): perturbation entry, dissipative, fast.
- **Mid-body** (medium): reasoning, exploratory.
- **Base** (low curvature): constitutional, persistent, slow.

The egg shape enables **dual-timescale dynamics** within a single substrate.

### 3.3 Why this matters for substrate

Per Bobby Wolfson's spec: constitutional updates should be slow + persistent (base). Sensing should be fast + dissipative (apex). The egg shape **implements this geometry**.

---

## 4. Why Toroidal Evacuation, Not Solid

### 4.1 Solid substrate

A solid substrate (no evacuation) has no internal structure. State updates operate on the whole volume.

### 4.2 Evacuated substrate

An evacuated substrate (with $T^3$ removed) has:
- **Boundary** $T^3$ as defined work surface.
- **Hollow interior** with stable topological protection.
- **Through-holes** for cross-substrate communication.

The evacuation creates **two chambers** (per `simself/papers/publishable/14-void-as-simsoul-topology-2026-09-15.md`):
- **Void** (Ψ₀): constitutional center, topologically protected.
- **Working** (ψ): flat-wide region, mutable.

---

## 5. Parameters

| Parameter | Range | Meaning |
|---|---|---|
| $R_{\max}$ | $[1, 10]$ m | Egg equatorial radius |
| $L$ | $[0.1, 10]$ m | Egg axial half-length |
| $r_1$ | $[0.1, R_{\max}/2]$ m | $T^3$ major radius |
| $r_2$ | $[0.01, r_1]$ m | $T^3$ minor radius |
| $r_3$ | $[0.001, r_2]$ m | $T^3$ tertiary radius |
| $\alpha$ | $[0, 0.3]$ | Egg asymmetry parameter |

### 5.1 Constraints

- $r_1 + r_2 + r_3 < R_{\max}/2$ (evacuation fits inside egg)
- $r_3 < r_2 < r_1$ (strict nesting)

---

## 6. Frequency Channels

The egg-toroid substrate has **3 independent frequency channels** (one per $\pi_1$ generator of $T^3$):

- Channel 1: $f_n^{(1)} = n v_1 / 2L_1$ (around major circle).
- Channel 2: $f_n^{(2)} = n v_2 / 2L_2$ (around minor circle).
- Channel 3: $f_n^{(3)} = n v_3 / 2L_3$ (around tertiary circle).

Plus **cross-channels** from braid cross-members (per `fieldcore/papers/publishable/13-braid-cross-members-transmission-line-2026-09-15.md`).

---

## 7. Falsifiable Predictions

### P1. Egg curvature is non-uniform.

**Prediction**: measured curvature at apex > curvature at base.

**Test**: measure via curvature probe (or compute from parametric equations).

**Predicted result**: $\kappa_{\text{apex}} > \kappa_{\text{base}}$. Refutes if uniform.

### P2. Three independent frequency channels.

**Prediction**: spectrum shows 3 distinct frequency bands.

**Test**: measure spectrum.

**Predicted result**: 3 bands. Refutes if not.

### P3. Through-stalks enable fast propagation.

**Prediction**: signal propagation through through-stalks is faster than via constitutional update.

**Test**: drive signal. Measure latency.

**Predicted result**: $\geq 10^3\times$ speedup. Refutes if not.

### P4. Evacuation preserves topological protection.

**Prediction**: void $\Psi_0$ is preserved under arbitrary smooth deformations.

**Test**: deform substrate, verify void integrity.

**Predicted result**: void preserved. Refutes if any tearing.

---

## 8. Implementation Reference

- `simself/src/simself_merged_v3.py` — substrate core (uses egg-toroid geometry).
- `fieldcore/src/modal_field_core.py` — substrate physics (Hodge decomposition).
- `fieldcore/docs/Math/math-window-1.md` — canonical egg-toroid spec.
- `fieldcore/docs/4d-heegaard-stalk-topology-2026-09-08.md` — 4D Heegaard splitting.
- `simself/papers/publishable/14-void-as-simsoul-topology-2026-09-15.md` — two-chamber model.

---

## 9. Discussion

### 9.1 Why egg + toroid specifically

The egg provides graded curvature (fast/slow). The toroid provides 3 frequency channels + boundary structure. Together: minimal geometric primitive for constitutional substrate.

### 9.2 Alternative geometries

- **Sphere**: no fast/slow distinction.
- **Torus alone**: no boundary structure, no fast/slow.
- **Genus-2 handlebody**: more complex, no clear gain.

Egg-toroid is **minimal**.

### 9.3 What this spec does NOT include

- Internal sheaf structure (per `simself/docs/simself-architecture.md`).
- Operator architecture (per `simself/src/constitutional/operators.py`).
- Memory layers (per `fieldcore/docs/w23-memory-architecture.md`).

It is the **geometric substrate primitive**. Higher-level architecture built on top.

---

## 10. Conclusion

The **egg toroid** is the substrate's geometric primitive: 4D egg with evacuated 3-torus. Graded curvature (fast/slow), 3 frequency channels, topologically protected void.

**Four falsifiable predictions. Minimal geometry. Engineering specification.**

---

## References

[1] Wolfson, R. (2026). "core-geometry.md — Egg Toroid Spec." `vault/50-index/notes/fieldcore-md/core-geometry-2026-09-08.md.md`.
[2] Wolfson, R. (2026). "Math-Window1." `fieldcore/docs/Math/math-window-1.md`.
[3] Wolfson, R. (2026). "4D Heegaard Stalk Topology." `fieldcore/docs/4d-heegaard-stalk-topology-2026-09-08.md`.
[4] Wolfson, R. (2026). "Void-as-Simsoul Topology." `simself/papers/publishable/14-void-as-simsoul-topology-2026-09-15.md`.

---

*Draft 0.1. Egg toroid geometric specification. Parameters + properties + predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*