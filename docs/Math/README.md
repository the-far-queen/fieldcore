# docs/Math — — Layer A reference

> **"** Full rewrite 2026-09-16 (per Grok master plan, applied by Hermes). Layer C
> content (occult physics, off-mission speculation, untested geometries) has
> been moved to `notes/analogies/`. The remaining files here are Layer A only:
> standard math used as tools for the architecture.

## What stays in `docs/Math/`

| File | What | Used by |
|---|---|---|
| `math-transformer-gradient-flow.md` | Standard gradient flow on F. | `papers/publishable/17-egg-toroid-spec` §6. |
| `mte-simself-primitives.md` | MLTR (machine language technical register) reference. | `papers/publishable/01-geodesic-lexicon` §3. |
| `topo-sheaf-stalk.md` | Topology reference for stalks as fibers. | `papers/publishable/11-stalk-architecture`. |
| `math-window-1.md` | Raw material for the appendix (Layer A only). | `papers/publishable/14-math-window1-synthesis`. |

## What left `docs/Math/` (moved to `notes/analogies/`)

The following were Layer C / off-mission and are preserved verbatim for diff and history. They are NOT on the science tree:

- `insect-microstructure-schema.md` — speculative biology
- `insect-plasma-flight.md` — bee plasma physics
- `mycelium-network-engineering-2026-09-13.md` — φ in mycelia
- `nested-egg-toroids.md` — 15 untested geometries
- `robotics-developer-clarity-2026-09-14.md` — off-mission
- `schauberger-vortex-engineering-2026-09-13.md` — Schauberger vortex
- `stalk-architecture-2026-09-08.md` — superseded by `papers/publishable/11-stalk-architecture-v6-1`
- `stella-octangula-cluster.md` — speculative geometry
- `water-as-plasma-engineering-2026-09-13.md` — water-as-plasma
- `geometry-over-material-winding-numbers-2026-09-14.md` — speculative
- `topology-geometry-core.md` — superseded by `papers/publishable/17-egg-toroid-spec`
- `core-geometry-2026-09-08.md` — superseded
- `emergence-rep-sheaf.md` — runtime sheaf → Channel rename (Batch 1 K4)
- `4d-heegaard-stalk-topology-2026-09-08.md` — 4-manifold framing, superseded

## The Hodge operator

This is the corrected statement used across both repos:

    Δ = dd* + d*d        (Hodge Laplacian on differential forms)

NOT `Δ = d + d*` (which is a Dirac-type operator, not a Hodge Laplacian).
