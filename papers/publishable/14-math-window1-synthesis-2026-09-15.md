# Math-Window-1 Synthesis — Appendix

> **Full rewrite 2026-09-16** (per Grok sharpen + master plan, applied by Hermes). The
> previous version of this document mixed three layers: (A) textbook math used as
> tools; (B) real math glued onto toy code; (C) occult physics and off-mission
> speculation. Per Grok (segment 01, applied 2026-09-16): strip Layer C, retitle
> Layer A as the appendix, drop Layer B until it has a discrete Hodge on a mesh.
>
> This file is now the math appendix. It contains only Layer A material.

## Layer A — textbook math used as tools

The following results are cited at the right level and used as the operational
vocabulary of the architecture. Each is cited correctly; no claim of original
discovery is made.

### Gradient flow on a quadratic potential

The energy `F(ψ) = (1/2) ||ψ - ψ₀||²` has gradient `∇F(ψ) = ψ - ψ₀`. The
gradient flow `ψ̇ = -(ψ - ψ₀)` has solutions

    ψ(t) = ψ₀ + e^{-t} (ψ(0) - ψ₀).

Drift decays as `e^{-t}`. Near the quadratic minimum the Hessian is the
identity, so every direction decays at the same rate.

### Picard and / uniqueness

For a Lipschitz vector field on a complete metric space, Picard–Lindelöf
gives existence and uniqueness of integral curves. On a manifold, chart
language is required; the slogan is fine.

### LaSalle invariance

A standard Lyapunov tool. Cited at the right level.

### Exponential decay near a non-degenerate minimum

Eigenvalues of the Hessian control the rate.

### Hodge Laplacian (corrected)

The Hodge Laplacian on differential forms is

    Δ = dd* + d*d.

The expression `Δ = dd* + d*d  (Hodge Laplacian, corrected 2026-09-16)` is a Dirac-type operator, not a Hodge Laplacian.
This synthesis and every paper that cites the operator must use the form
`dd* + d*d`.

### Product metric on a torus

The induced metric on the Clifford torus in S³ is `ds² = (1/2)(dθ² + dφ²)`.
This is the flat metric on the interface T (see `17-egg-toroid-spec`).

### Heegaard splitting (corrected)

The architecture lives in the genus-1 Heegaard splitting of S³:

    S³ = V ∪ W,    V ∩ W = T.

V and W are solid tori; T is the Clifford torus. Working state ψ moves in V
inside the ball B_R(ψ₀). Ground ψ₀ sits on T (or is write-protected). The
hole is the solid torus W, which has no update field. See
`17-egg-toroid-spec` for the full statement.

### Seifert genus vs Heegaard genus

Seifert genus of a knot T(p, q) is `(p-1)(q-1)/2`. It is a knot invariant,
unrelated to Heegaard genus of a 3-manifold.

### Torus-knot Seifert genus

For T(29, 31), G = (29-1)(31-1)/2 = 420. For T(41, 43), G = (41-1)(43-1)/2 = 840.

### Twin prime facts (number theory)

Twin primes > 3 have sum divisible by 12 (they are `6k ± 1`). The product of
twin primes > 3 is `≡ 11 (mod 12)` because `(6k-1)(6k+1) = 36k² - 1 ≡ -1
(mod 12)`.

### arctan identity (cheap, not a theorem)

`arctan(1/x) + arctan(x) = π/2` for `x > 0`. This includes the special case
`arctan(1/√φ) + arctan(√φ) = π/2`. It is not a pyramid theorem.

### Hopf fibration

The Hopf map `h(z, w) = (|z|² - |w|², 2zw̄)` has fibers `ψ ↦ (e^{iψ}z, e^{iψ}w)`,
which are great circles. The Clifford torus is the preimage of the equator of
S². The bundle statement is `S¹ ↪ S³ → S²`.

### Brendle uniqueness

Among embedded minimal tori in the round 3-sphere, the Clifford torus is the
unique model up to isometries of S³ (Brendle, 2013).

## What is not in this appendix

The following were in the previous synthesis and have been removed:

- Layer B claims (e.g. the ResolutionOperator as a parallel projection; the 20-axis
  derivation from Clifford + octonions + Hodge dual + triple product).
- Layer C claims (fine-structure α from twin-prime offsets; force unification by
  fractal offsets; Giza / Barabar / Tesla geometric filter; water-as-plasma;
  coherence domains as substrate evidence; F# = 256×36/25; Danley Hz;
  diminished chord to C = 512; Swedenborg 100 correspondences as constitutional
  axes; PFA "reality is consciousness" as an engineering axiom; Schauberger
  levitation; mercury room-temperature coherence; bee plasma flight; "45,625
  hours" SNR as a scientific result; 19 author voices = 19 manifolds).

These files have been moved to `notes/analogies/` (preserved verbatim) and
removed from the science tree. See `notes/analogies/` for diff and history.

## References

- Brendle, S. (2013). *Embedded minimal tori in S³.*
- Hopf, H. (1931). *Über die Abbildungen von S³ auf S².*
- Waldhausen, F. (1968). *Heegaard-Zerlegungen der 3-Sphäre.*
