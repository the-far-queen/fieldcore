# 01 — The identity law (Layer A)

**Claim.** Let `F(ψ) = ½‖ψ − ψ₀‖²`. The projected gradient step

```
ψ_{k+1} = Π_{B_R(ψ₀)} ( ψ_k − η (ψ_k − ψ₀) ),    η > 0
```

converges for every starting point inside the ball, with an explicit bound.

**Verification.** `farmath.geometry.gradient_flow` +
`contraction_bound_holds`, 22 checks green. The suite asserts the bound at
every recorded step and also asserts that η = 1.5 *violates* it, so the
checker is not vacuous.

## The bound

```
d_{k+1} ≤ (1 − η) d_k   ⇒   d_k ≤ (1 − η)^k d_0   ⇒   d_k → 0
```

Independent of the start. That independence is the load-bearing part: it
is why a steel ball dropped anywhere on a concave surface arrives at the
hole, and why the same step gives the same behaviour in steel, in silicon
and in neurons.

Measured, 200 steps at η = 0.5, 16 dimensions: drift falls below
`d_0 × 1e-30`.

## The harmonic exception

On a closed Riemannian manifold the Hodge decomposition splits a
perturbation into exact, coexact and harmonic parts. Gradient flow moves
the exact part (the gradient of a function) and leaves the harmonic part
fixed, because `Δh = 0`.

The architecture's running substitute for the harmonic form is the
parallel projection `⟨ψ, ψ₀⟩ ψ₀`. Verified in
`harmonic_direction_is_conserved`: the coefficient on `ψ₀` scales by
exactly `1 − η` each step and the direction cosine between the first and
last harmonic parts is 1 to within 1e-9.

**Layer B, held.** The substitute is not yet the harmonic 1-form. It
becomes the harmonic 1-form when a discrete Hodge operator exists on a
triangulated interface `T`. Until then the parallel projection is a
stand-in and is labelled one.

## Why not an LLM forward pass

An LLM forward pass is the same gradient step on the same `F`, with
stochastic noise sampled per token. For bounded noise the bound still
holds. Natural-language noise is not bounded, so the guarantee does not
survive — what remains is parameter scale (cost, heat, and no control
authority) doing the work instead of mathematics.

|  | LLM forward pass | this step |
|---|---|---|
| cost per step | O(d²) flops | O(d) flops |
| heat | matrix-multiply heat | 1 op/cycle |
| convergence | probabilistic | deterministic bound |
| veto authority | none | 1-bit gate |

Same mathematics, lower cost, explicit control.

## Terms used here

Defined here so this document can be read cold. The full glossary is
`GLOSSARY.md`.


- **projected gradient step** - moving against the gradient of an energy F, with the result projected back into a bounded region
- **Hodge decomposition** - splitting a field into exact, coexact and harmonic parts
- **harmonic** - the part of a field with Delta h = 0, which gradient flow does not move

## More terms


- **gradient** - the direction in which a function rises fastest
- **gradient flow** - descending a quantity by moving against its gradient
- **manifold** - a space that locally looks like ordinary Euclidean space
