# Glossary — every term this school uses, defined once

> Read this before anything else in `docs/`. It exists because a measured
> prerequisite-load audit (2026-10-09) found every document in this folder
> at 100% load: each used its domain vocabulary without defining it. A
> reader arriving cold had no way to start.
>
> Terms are defined in the ordinary sense, not the project's sense. Where
> the project uses a term unusually, the difference is stated in the
> entry rather than hidden.

## Geometry and topology

**manifold** — a space that locally looks like ordinary Euclidean space.
Far from a point, it may be curved, have holes, or wrap around; near every
point it has ordinary coordinates. The "locally" is the whole content of
the word.

**solid torus** — D² × S¹. A doughnut. Homeomorphic to the region between
two nested tori, equivalently a solid bent into a ring.

**Clifford torus** — the flat torus sitting inside the 3-sphere, given by
points (z, w) with |z| = |w| = 1/√2. It is the standard example of a
minimal surface: nothing about it can be shrunk.

**Heegaard splitting** — a way of building a 3-manifold by gluing two
handlebodies along their common boundary. S³ is the genus-1 case: two
solid tori glued along a torus.

**Hopf fibration** — a map from the 3-sphere onto the 2-sphere whose every
point maps to a circle, and every circle is a great circle of the
3-sphere. The 1962 Penrose "impossible" staircase picture comes from it.

**Seifert genus** — the least number of handles on a surface whose boundary
is a given knot. A property of the knot. It is NOT the Heegaard genus,
which is a property of the surrounding 3-manifold; the two were confused in
this project and the confusion was corrected in 2026-09.

**homology** — a way of counting holes that gives the same answer for
spaces you can deform into each other. H₁ of a loop is ℤ; the loop has one
independent hole.

## Differential structure

**Hodge decomposition** — splitting a field on a closed manifold into an
exact part, a coexact part, and a harmonic part. The harmonic part is the
one that survives gradient flow.

**Hodge Laplacian** — Δ = dd* + d*d, the operator on differential forms that
makes those three parts orthogonal. The project once wrote a Dirac-type
operator in this slot and it was corrected.

**gradient flow** — descending a quantity F(ψ) by moving against its
gradient: ψ̇ = −∇F(ψ). The identity law of this whole project is one
specific case, F(ψ) = ½‖ψ − ψ₀‖².

**harmonic** — the part of a field with Δh = 0. Under gradient flow it does
not move. In this project it is treated as the part worth preserving.

**Riemannian metric** — a rule for measuring distances on a curved space.
The Fisher metric in `fieldcore/src/fisher_metric.py` is one: distances
defined by the model's own uncertainty rather than by a geometry given in
advance.

## Numbers and primes

**twin primes** — two primes differing by 2, such as 11 and 13. Their sums
are all divisible by 12 above the pair (3,5), and their products are all
11 mod 12; both are proven, not conjectured.

**golden ratio, φ** — (1 + √5)/2 ≈ 1.618. Its reciprocal 1/φ ≈ 0.618 is
the egg-compression constant in the FieldCore cell. That constant is
Bobby's choice and is treated as a design parameter, not as a theorem
about the substrate.

**fine-structure constant, α** — 1/137.035999…, the coupling strength of
electromagnetism. The project speculates that it relates to the offset
between the prime and Fibonacci fractals. That is marked speculation and
is load-bearing on nothing.

## This project

**PSB** — Primary Semantic Block. A typed unit of meaning in Bobby's
vocabulary work: act, refuse, name, commit, time, object. The claim is that
language is built from a small primitive set plus composition, and that
tokenisation destroys the relations between them.

**constitutional axis** — a coordinate of the system with thresholds rather
than a continuous value. Twenty were originally specified; eight
functional ones are canonical.

**M0 governor** — the deterministic component with authority to refuse. Now
a separate OS process, so a veto cannot be widened or skipped by the
component it governs.

**M1 controller** — the out-of-core component that qualifies operators and
audits changes to the rules library.

**sheaf** — a way of assigning data to pieces of a space such that
overlapping pieces agree on their intersection. Used here to ask whether
local data can be glued into something global; when it cannot, the failure
has a measured dimension (H¹) rather than being a vague disagreement.

**degrees of freedom** — the number of independent directions a state can
move in. Constraints remove them, and the count is a rank rather than a
number of rules.
