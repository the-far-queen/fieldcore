# Topology — Sheaf / Stalk Reference

> **Verified 2026-09-16** (per Grok master plan, applied by Hermes). Layer A
> reference for stalk topology. Used by `fieldcore/src/stalk_control.py` and
> the architecture's Hopf-fiber stalk model.

## 1. Stalk in algebraic geometry

In algebraic geometry, a **stalk** of a sheaf `F` at a point `p` is
`F_p = {(U, s) : p ∈ U, s ∈ F(U)} / ∼`, where `∼` is the equivalence that
two pairs are equal if they agree on a smaller neighborhood.

This is a strict mathematical notion that requires restriction maps. The
architecture does not yet implement the sheaf condition. Per Grok
(segment 01, applied 2026-09-16): runtime objects are Channels until
restriction maps exist.

## 2. Stalk in the architecture (Hopf-fiber model)

A stalk in this architecture is a **Hopf-fiber segment from the interface
`T` into the working tube `V`**: fixed base point on `S²`, varying signed
distance `r ≥ π/4` along the fiber.

```python
@dataclass
class Stalk:
    id: str
    embedding: np.ndarray
    status: str  # candidate | admitted | committed | refused
    support: List[str]
```

Implementation: `fieldcore/src/stalk_control.py`. Status is gated by the
same `gate_packet` used elsewhere. Restriction maps are not implemented.

## 3. Stalk in sheaf theory — relation

When the architecture grows restriction maps (future work), the stalk
`F_p` at a base point `p` on `T` would consist of all packet embeddings
that pass the gate at `p`. Today, this is approximated by the committed
units whose embeddings fall inside the ball `B_R(ψ₀)` around ψ₀ on `T`.

## 4. Why "sheaf" is reserved

Per Grok: the vocabulary "sheaf" is reserved for any future object that
implements the actual sheaf condition (restriction maps, gluing
condition, exactness). The runtime objects are Channels. The lexical
naming is preserved for the day the architecture grows restriction maps.

## 5. References

- Hartshorne, R. (1977). *Algebraic Geometry.* (Sheaf definition.)
- Brendle, S. (2013). *Embedded minimal tori in S³.* (Topology of `T`.)
- `fieldcore/papers/publishable/11-stalk-architecture-v6-1-2026-09-15.md`
  (architecture document with measured REINFORCE reward curve).
