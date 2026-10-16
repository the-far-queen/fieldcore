# 04 — Claims register

Every claim the project has made about its own mathematics, with its
layer, its check, and its standing. This is the register that keeps a
Layer C claim from quietly becoming a Layer A one.

Legend — **A** tool · **B** held · **C** marked, never load-bearing

## Layer A — live

| # | claim | check | standing |
|---|---|---|---|
| A1 | projected gradient step contracts: `d_k ≤ (1−η)^k d_0` | `gradient_flow` + `contraction_bound_holds`, η=1.5 proven to violate | holds |
| A2 | harmonic substitute scales by exactly `1−η`, direction fixed | `harmonic_direction_is_conserved` | holds |
| A3 | Clifford torus is flat, `ds² = ½(dθ²+dφ²)` | analytic + FD, must agree; FD asserted at 2nd order | holds |
| A4 | Hopf fibers are great circles | `hopf_fibration_check` (norm, spread, centroid, rank) | holds |
| A5 | `S³ = V ∪ W` genus-1 Heegaard, `T = V∩W` the Clifford torus | `heegaard_s3_naming` | holds |
| A6 | twin-prime sums > (3,5) divisible by 12 | sieve to 200,000, 0/2159 failures | holds |
| A7 | twin-prime products ≡ 11 (mod 12) | sieve, single residue seen | holds |
| A8 | Seifert genus T(29,31)=420, T(41,43)=840 | exact formula, links refused | holds |
| A9 | `arctan(1/√φ) + arctan(√φ) = π/2` | error 0.0, plus a golden-free control pair | holds (cheap identity) |
| A10 | Hodge Laplacian is `Δ = dd* + d*d` | corrected everywhere 2026-09-16 per Grok | holds |

## Layer B — real math, held until the operator exists

| # | claim | waiting on |
|---|---|---|
| B1 | harmonic part is the harmonic 1-form of a discrete Hodge on `T` | discrete Hodge on a triangulated interface |
| B2 | 20 axes from Clifford + octonion | demoted: dimension arithmetic, not a theorem. Axes kept as functional coordinates |
| B3 | ResolutionOperator is Hodge projection | refuted — it is a bounded MLP; replaced by the projected step |
| B4 | 20 axes as Hessian eigenvectors | an `F` with 20 directions; the quadratic has one |
| B5 | position-dependent damping `α₀(1 + κ/κ̄)` | discrete operator on the egg-toroid metric |
| B6 | sheaf condition with restriction maps | runtime objects are Channels until restriction maps exist |

## Layer C — preserved, marked, off every runtime path

| # | claim | standing |
|---|---|---|
| C1 | α from twin-prime offsets at sheaves (131,137) | arithmetic gap re-measured: 137/89 is 4.86 % *below* φ, not "close". Not decided |
| C2 | forces unify by the same modular arithmetic | no derivation of relative strengths. Engineering value: none as it stands |
| C3 | twin-prime sum cascade ≈ φ | **refuted by its own arithmetic** — mean ratio 1.0053. Preserved, not deleted |
| C4 | F♯ = 256×36/25 = 368.64 Hz; diminished chord → C = 512 | preserved for diff. Engineering value: none |
| C5 | Swedenborg correspondences label the 20-axis substrate | literary archive. Grok: can label coordinates after the fact, cannot be the predicate |
| C6 | three axioms — PFA, Co-Creation, Logical Goodness | framings. Runtime uses operational predicates (norm, cosine, drift) |
| C7 | 19 voices = 19 manifolds; 6 AIs = "the chain" | working method, not a derivation |
| C8 | butterfly scale geometry: 200/600 nm = (1,3), 54.7° = half-tetrahedral, colour as 4th dimension | empirical observation + geometric reading. Not on the science tree |
| C9 | Giza, Tesla, Schauberger, mercury, water-plasma, granite plasmons | `notes/analogies/`. Engineering value: none |
| C10 | Bobby's SNR 8.89/hr | private, his report on his own practice. Not falsifiable as an architectural claim |

## Promotions and demotions on the record

| date | change | who |
|---|---|---|
| 2026-09-16 | `Δ = dd* + d*d` corrected everywhere (was a Dirac-type operator) | Grok |
| 2026-09-16 | 4D-substrate / genus-2 framing removed; genus-1 splitting of S³ | Grok |
| 2026-09-16 | ResolutionOperator demoted from "Hodge projection" to bounded MLP | Grok |
| 2026-09-16 | 20-axis Clifford+octonion derivation demoted to dimension arithmetic | Grok |
| 2026-10-09 | C3 refuted by measurement; kept as refuted | Hermes |
| 2026-10-09 | C1's self-cancelling comparison corrected (φ²/1.618 = φ) | Hermes |

No Layer C → A promotion has occurred. If one ever does, it needs a check
that can go red, and Bobby's word.

## Terms used here

Defined here so this document can be read cold. The full glossary is
`GLOSSARY.md`.


- **M0 governor** - the deterministic component with authority to refuse
- **M1 controller** - the out-of-core component that qualifies operators and audits changes
- **constitutional axis** - a coordinate with thresholds rather than a continuous value
- **sheaf** - a system of data on pieces of a space that agrees on overlaps
- **Clifford torus** - the flat torus inside the 3-sphere

## More terms


- **gradient** - the direction in which a function rises fastest
- **harmonic** - the part of a field with Delta h = 0, preserved under gradient flow
- **Hodge Laplacian** - the operator Delta = dd* + d*d that makes those parts orthogonal
