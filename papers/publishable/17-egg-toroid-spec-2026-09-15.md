# Egg-Toroid Spec

> **Full rewrite 2026-09-16** (per Grok master plan + sharpen 2026-09-16, applied by Hermes). The previous version of this paper described a 4-manifold with Heegaard genus 2 and a "discovered" tube metric. That framing is wrong. The egg-toroid drawing is a useful picture of a tube with a hole. Topologically, it is the **genus-1 Heegaard splitting of the 3-sphere S³**, with the **Clifford torus T** as the interface and the **Hopf fibration** filling the two solid tori on either side. This paper is the canonical statement of that picture.

## 1. The 3-sphere as the ambient space

The architecture's 3-manifold statement lives in S³. Write ℝ⁴ ≅ ℂ² and define

    S³ = {(z, w) ∈ ℂ² : |z|² + |w|² = 1}.

S³ is the unit sphere in ℂ². Two real planes (z and w) with radii locked by the unit-sphere rule. This is the smallest round 3-manifold that admits a non-trivial Heegaard splitting.

## 2. The Clifford torus is the wall

The Clifford torus is

    T = {(z, w) ∈ S³ : |z| = |w| = 1/√2}.

T is a flat square torus in S³. Parametrize it by two angles:

    (1/√2)(cos θ, sin θ, cos φ, sin φ),    θ, φ ∈ [0, 2π).

The induced metric is

    ds² = (1/2) dθ² + (1/2) dφ².

T is **flat** in the induced metric: Gaussian curvature 0. T is **minimal** in S³: principal curvatures +1 and -1, mean curvature 0. Among embedded minimal tori in the round 3-sphere, T is the **unique model up to isometries of S³** (Brendle, 2013).

T is the **interface** in the architecture. Ground ψ₀ sits on T. Ingest writes units as points or as charts on T. The geodesic lexicon uses the flat Clifford metric on T to compute distances between units that have been given (θ, φ) addresses. Until then, the kernel's Euclidean metric on packet embeddings is the running distance. The two metrics coexist; neither replaces the other.

## 3. The Hopf map fills the two rooms

The Hopf fibration h: S³ → S² is

    h(z, w) = (|z|² - |w|², 2z w̄).

Fibers are great circles of S³:

    ψ ↦ (e^{iψ} z, e^{iψ} w).

Distinct fibers do not meet; any two fibers are linked once. The bundle statement is S¹ ↪ S³ → S².

The level sets of the height |z|² - |w|² are the surfaces

    T_r = {(z, w) : |z| = cos r, |w| = sin r},    r ∈ [0, π/2].

At r = π/4, T_r is the Clifford torus T. As r varies, T_r sweeps a family of nested tori, each a union of Hopf fibers.

The two **solid tori** on either side of T are

    V = {(z, w) : |z| ≥ 1/√2}    (the working tube),
    W = {(z, w) : |w| ≥ 1/√2}    (the complementary solid torus, ehole).

V ∪ W = S³. V ∩ W = T. This is the **genus-1 Heegaard splitting of S³**: two solid tori glued along their common boundary T. The gluing that yields S³ sends a meridian of V to a longitude of W; the standard embedding picture (a doughnut in ℝ³ with the hole continued through the point at infinity) shows the same split.

## 4. Apex / mid-body / base are labels inside V, not a second genus

The egg-toroid drawing partitions V into three regions along the working direction: apex (one end), mid-body (the wide region), base (the other end). These are **labels inside one solid torus**, not a higher-genus splitting. They can be taken as intervals of constant (θ, φ) and varying signed distance from T (Hopf-fiber radius r ≥ π/4 into V), or as arcs of constant r and varying (θ, φ). They do not change the topology.

The previous framing of this paper described a 4-manifold (S⁴) with Heegaard genus 2 and called three zones a second genus. S⁴ has no Heegaard splitting; it has trisections (Gay–Kirby). S⁴ \ int(T³) has no Heegaard genus. None of those objects apply here.

## 5. The identity law is a placement rule on this picture

Ground ψ₀ is a marked structure on T (a basepoint, a frame, a frozen section). Working state ψ is a point of V, recorded as an embedding in ℝⁿ or, if a mesh is built, as a point with r ≥ π/4 (signed distance off T into V). The ball

    B_R(ψ₀) = {ψ ∈ V : ||ψ - ψ₀|| ≤ R}

is the working neighborhood of the interface. The hole is r < π/4: no update field.

A packet that would assign to ψ₀ is an **identity packet**, not a language packet. It must pass through the revision protocol, not an ordinary tick. The kernel implements this as a type-channel split on `dtype` in `tiniest_core.py` (now `Channel`, per Batch 1 K4).

## 6. The energy and the gradient flow

The simplest energy that makes "return to self" a gradient flow is

    F(ψ) = (1/2) ||ψ - ψ₀||².

Then ∇F(ψ) = ψ - ψ₀, and the gradient flow is

    ψ̇ = -(ψ - ψ₀).

Solutions exist and are unique on V. They are

    ψ(t) = ψ₀ + e^{-t} (ψ(0) - ψ₀).

Drift decays as e^{-t}. Near this quadratic minimum the Hessian is the identity, so every direction decays at the same rate. Additional energy terms (task error, lexicon conflict) change the Hessian; they do not change the rule: name F, take a step opposite ∇F, clip to B_R(ψ₀).

A richer energy is allowed but must satisfy ∇F(ψ₀) = 0 and positive-definite Hessian at ψ₀ on the working subspace. If those fail, "return to self" is a name, not a flow.

## 7. The kernel step

The discrete kernel update is the **projected gradient step** on F:

    ψ ← Π_{B_R(ψ₀)} (ψ - η (ψ - ψ₀)),    η > 0.

Π_{B_R(ψ₀)} is radial projection onto the sphere ||ψ - ψ₀|| = R from ψ₀. Implementation: `fieldcore/src/gradient_flow_kernel.py` (per Batch 2 Step 2, applied 2026-09-16). The earlier `convergence_demo.py` is Bobby's pedagogical steel-ball-on-concave-surface exhibit and is preserved as a teaching artifact, not as the running kernel.

## 8. The Heegaard Floer dictionary

A pointed Heegaard diagram (Σ, α, β, z) for this splitting: Σ = T, α and β are meridians of V and W respectively, z is a marked point off both curve families. The hat complex CF̂ has generators at intersections of α and β. The differential counts holomorphic Whitney disks missing z.

Architecture dictionary (per Grok segment 08, applied 2026-09-16):

- **α-curves ↔ working-side conditions.** Ball membership, ingest type, tool schema.
- **β-curves ↔ hole-side conditions.** Write-protect on ψ₀, no field in W, restart from T only.
- **A generator ↔ a typed packet that meets both.** A packet that fails either family is not a generator.
- **The basepoint z ↔ the channel that must not carry a ground write.** A packet that wants to write ψ₀ has the wrong basepoint neighborhood.
- **Whitney disks that miss z ↔ the hat complex.** Verdicts that never attempted a ground write.
- **Whitney disks that pass z ↔ the filtered packages (U-powers).** A log of attempted crossings, recorded rather than executed.
- **Holomorphic triangles ↔ cobordism maps.** In FieldCore these are a **versioned revision of ground**, not an ordinary tick.

None of this has to be implemented as a moduli space to be the running model. The dictionary names the rooms. The kernel already occupies them.

## 9. Stalks are fibers, built as records

A stalk in this architecture is a **Hopf-fiber segment from T into V**: fixed base point p on S², varying signed distance r ≥ π/4 along the fiber. Implementation: a record with an embedding, a link list, and a status (`candidate | admitted | committed | refused`). FieldCore `src/stalk_control.py` and `src/stalk_topology.py` already store this shape. The reward signal REINFORCE needs a measured coupling curve before the stalk paper earns "paper" status; until then the stalk paper is **demoted to docs/** in the next paper-tree review.

## 10. The status of "geometric AI"

The architecture is geometric in two of the four standard senses: it uses a manifold of embeddings (ℝⁿ around ψ₀) and a topological statement (the splitting). It does **not** implement equivariant networks or geometric-algebra tokens or discrete Hodge on a mesh. Until it does, "geometric AI" is a positioning term, not a claim. The path from positioning to claim: triangulate T, implement discrete Hodge on 0- and 1-forms, project activations onto harmonic 1-forms, show one task where the harmonic part is the memory the shell wanted to keep. That work is Batch 4 Step 11 of the master plan.

## 11. The picture as architecture

Drawing → module map:

| Drawing | Module |
|---|---|
| V (working tube) | `simself/src/constitutional/simself.py` (canonical, Batch 1 K5) |
| W (ehole) | `simself/src/constitutional/ground.py` (write-protect on ψ₀) |
| T (interface) | `simself/src/harness/gate.py` (Batch 1 K8, same predicates as kernel) |
| ψ moving in V | `simself/src/constitutional/resolution.py`, `tiniest_core.py` |
| A packet meeting both sides | `simself/src/m1_m0_negotiation.py` |
| α-conditions (V) | `fieldcore/src/tiniest-core/tiniest_core.py` `M0_Governor` |
| β-conditions (W) | `simself/src/harness/gate.py`, `ground.py` |
| The hat record | `simself/src/harness/metrics.py` + `decision_log` |
| Triangles | `simself/src/constitutional/atlas_exam.py` (5-item exam) |
| Stalks | `fieldcore/src/stalk_control.py` + `simself/src/stalk.py` |

## 12. What stays, what is deleted

**Stays in this paper:**

- The 3-sphere as ambient.
- The Clifford torus as the interface.
- The Hopf map as the room-filler.
- The energy F and the gradient flow.
- The Floer dictionary.
- The drawing-to-module map.

**Deleted from the previous version:**

- "4D egg-toroid" as a 4-dimensional object.
- "Heegaard genus 2" as the default of the egg.
- "S⁴ \ int(T³)" as a substrate.
- "ds² = (R + r cos θ)² dφ² + r² dθ² + dz²" as a discovered metric.
- "Apex / mid-body / base" as zones of a higher-genus object.

Each of those was wrong. The egg is a 3-sphere drawing; the picture has one surface and two solid pieces.

## 13. Verifiable claims

This paper is testable as a set of engineering statements, not as a discovery:

| Claim | Test |
|---|---|
| The kernel veto is two inequalities. | `M0_Governor.norm_ok`, `M0_Governor.cos_ok` in `tiniest_core.py` |
| Working state stays inside B_R(ψ₀). | `fieldcore/src/gradient_flow_kernel.py --R 3.0 --eta 0.1` |
| Ground is write-protected. | `test_ground_immutable_across_restart` in `tests/test_restart.py` |
| Restart preserves ψ₀, ψ, committed unit ids, verdicts. | `test_restart_round_trip` in `tests/test_restart.py` |
| T is flat in the induced metric. | ds² = (1/2)(dθ² + dφ²) on the parametrization in §2 |
| V ∪ W = S³, V ∩ W = T. | Set-theoretic check from the definitions in §3 |
| V and W are linked across T. | Linking number 1 on any pair of Hopf fibers crossing the equator |
| The Atlas exam runs the 5 named items. | `python simself/src/demos/atlas_run.py` |

A reader can verify each of these without taking the paper's word for it.

## 14. References

- Brendle, S. (2013). *Embedded minimal tori in S³.* 
- Hopf, H. (1931). *Über die Abbildungen von S³ auf S².* 
- Ozsváth, P.; Szabó, Z. (2004). *Holomorphic disks and topological invariants for closed three-manifolds.* 
- Waldhausen, F. (1968). *Heegaard-Zerlegungen der 3-Sphäre.* 

These are the cited standard results. The engineering uses only definitions and the genus-1 case.
