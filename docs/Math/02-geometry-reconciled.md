# 02 — Reconciled geometry (Layer A, with Bobby's originals kept)

Source: `Desktop/FieldCore/Math-Window1.md` (2026-09-16 rewrite, per Bobby
+ Grok reconciliation) and `4D-HEEGAARD-STALK-TOPOLOGY-2026-09-08.md`.

## What Bobby gave, verbatim

- The toroid is 3D. **Solid fact.**
- The egg is likely 4D. Bobby's word: "likely." **Hypothesis.**
- Frequency as hidden key. **Speculative**; the engineering reading is
  kept, the poetic framing is marked.

> "treat unfounded as speculative not drop all theorizing im often
> correct." — Bobby, 2026-09-14-late

This is the rule that shapes the whole repo.

## The egg-toroid picture, formalised

The picture is the **genus-1 Heegaard splitting of S³**:

```
S³ = V ∪ W,    V ∩ W = T
```

- `V` — working tube (apex, mid-body, base are labels inside one solid torus)
- `W` — ehole, the hole that does not compute
- `T` — Clifford torus, the interface where ψ₀ sits

The gluing swaps meridian with longitude, which is the standard genus-1
gluing; the amalgam then reduces the free product `ℤ * ℤ` to the
trivial group. Checked in
`farmath.geometry.heegaard_s3_naming`.

**Corrections Grok forced, kept beside the original:**

- Heegaard splittings are a notion for **3-manifolds**. `S⁴` has
  *trisections* (Gay–Kirby), not Heegaard splittings.
- 4-manifolds have no Heegaard genus. The old "4D substrate with Heegaard
  genus 2" framing was wrong and is removed from the science tree.
- Seifert genus is a **knot** invariant and is not the Heegaard genus of
  the surrounding 3-manifold. The document conflated them; corrected.

## Clifford torus (Layer A, computed)

```
T = {(z, w) ∈ S³ : |z| = |w| = 1/√2}
```

Parametrised exactly by `X(θ,φ) = (1/√2)(cos θ, sin θ, cos φ, sin φ)`:

| quantity | measured | expected |
|---|---|---|
| max norm error on S³ | 2.22e-16 | 0 |
| g_θθ (analytic) | 0.5 exactly | 0.5 |
| g_φφ (analytic) | 0.5 exactly | 0.5 |
| g_θφ (max abs) | 0.0 | 0 |
| g_θθ by finite difference (grid 41) | 0.49590 | 0.5 ± 0.049 |

The metric is `ds² = (1/2)(dθ² + dφ²)`: flat. The finite-difference route
converges at second order — measured ratio **4.00** per grid doubling,
asserted in `test_clifford_torus_fd_converges_at_second_order`, so the
accuracy claim is checked rather than assumed. Minimality and uniqueness
among embedded minimal tori in round S³ is Brendle (2013).

## Hopf fibration (Layer A, computed)

```
h(z, w) = ( 2 Re(z w̄),  2 Im(z w̄),  |z|² − |w|² ) :  S³ → S²
```

| quantity | measured |
|---|---|
| max ‖h‖ − 1 | 4.44e-16 |
| fiber spread (all φ map to one base point) | 3.33e-16 |
| fiber centroid offset | 1.11e-16 |
| fiber centered rank | 2 (a plane — a great circle, not a solid) |

Fibers are great circles: `S¹ ↪ S³ → S²`. Used in the architecture as the
geometric naming of stalks.

## Layer B — held until a mesh exists

Real mathematics, currently glued onto code that does not implement it:

- **The 20 axes from Clifford + octonion.** `20 = 8 + 12` is dimension
  arithmetic, not a theorem. The axes remain load-bearing as *functional*
  coordinates with thresholds; the derivation is out of publishable.
  Canonical set is 8 functional axes.
- **ResolutionOperator as "Hodge projection".** It is a bounded MLP:
  `ALPHA·tanh(W₁δ) → W₂ → scale → clip`. Replaced by the projected
  gradient step.
- **20 axes as Hessian eigenvectors.** Requires an `F` with 20
  directions; the quadratic `F` has one. Held.
- **Position-dependent damping on the egg-toroid.** Needs a discrete
  operator on the metric. Held.

## Layer C — preserved, marked, off every runtime path

- α from twin-prime fractal offsets at sheaves (131, 137)
- force unification by the same modular arithmetic
- Swedenborg correspondences as substrate labels — Grok's note stands:
  *"value, language, correspondences, and literary maps can label
  coordinates after the fact. They cannot be the predicate."*
- the three axioms (PFA, Co-Creation, Logical Goodness) — framings, not
  engineering axioms; the runtime uses operational predicates (norm,
  cosine, drift)
- F♯ = 256×36/25 = 368.64 Hz, diminished chord to C = 512
- 19 voices as 19 manifolds; the 6-AI team as "the chain"
- Giza, Tesla, Schauberger, mercury, water-plasma

None of these are on the science tree. All of them are kept.

## Terms used here

Defined here so this document can be read cold. The full glossary is
`GLOSSARY.md`.


- **manifold** - a space that locally looks like ordinary Euclidean space
- **Heegaard splitting** - building a 3-manifold by gluing two handlebodies along their boundary
- **Clifford torus** - the flat torus inside the 3-sphere, given by |z| = |w| = 1/sqrt(2)
- **Hopf fibration** - a map from the 3-sphere onto the 2-sphere whose fibers are great circles
- **solid torus** - D2 x S1, a doughnut
- **Seifert genus** - the least number of handles on a surface whose boundary is a given knot

## More terms


- **gradient** - the direction in which a function rises fastest
