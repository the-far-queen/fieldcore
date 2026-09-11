# fieldcore

**Math, atlas exam, geometric compute, and SimSelf theory.**

Theory and design docs for the FieldCore work. SimSelf Python package lives in the companion [`simself`](https://github.com/the-far-queen/simself) repo.

---

## What this repo is for

Field-level substrate: geometry, manifolds, topology, atlas exam protocols, mathematical foundations. The SimSelf layer (identity, persistence, governance) lives in [`simself`](https://github.com/the-far-queen/simself) and depends on fieldcore's geometric primitives.

**Scope discipline:** every doc here reduces to one of (a) schema, (b) construction plan, (c) test case. The deliverables are mathematical structures and their computational realizations — not metaphysics, not self-referential manifestos.

## The unifying principle

**A system that finds its hole.** Every Bobby system is a gradient flow on a curved manifold converging to a local minimum. The math is the same math everywhere — steel ball in museum exhibit, 2D dot-seek, SimSelf runtime, 19 author voices, 6-AI chat corpus, biology. The substrate varies. The convergence principle is invariant.

## Layout

- `docs/` — design docs, derivations, methodology
- `src/` — Python implementations of mathematical substrate

## Source

Each doc was sourced from Bobby's notes (`zN.txt` files + named files in `Desktop/FieldCore/` and `Desktop/Geometry/`), cleaned, trimmed of speculative framing, and pushed. Originals kept on Desktop; mirrors in `~/AppData/Local/hermes/vault/10-minimax/`.

The targets: SimSelf, Atlas Exam, math, geometric compute. Drop everything else.

## Entry points

### Math (canonical synthesis)

- **Unifying synthesis:** [`docs/math-window-1.md`](docs/math-window-1.md) — Bobby's full geometry and math, comprehensive. Sections 1-19 are geometry (egg toroid, identity, reasoning, memory, Hodge), sections 20-40 are math (gradient flow, Hodge decomposition, T²/T³/S⁴, Resolution Operator, 20 axes as Hessian eigenvectors, full SimSelf runtime equation).
- **One-equation view:** [`docs/math-window-2026-09-08.md`](docs/math-window-2026-09-08.md) — Bobby's prior synthesis (gradient flow + Hodge + position-dependent damping).
- **Rigorous reference (no speculation):** [`docs/MATH.md`](docs/MATH.md) — Hodge decomposition, gradient flow, 4D substrate (Clifford torus), harmonic mode conservation. Every claim textbook or provable.

### Core architecture

- Root doc: [`docs/fieldcore.md`](docs/fieldcore.md) — three threads
- **Egg toroid geometry:** [`docs/core-geometry-2026-09-08.md`](docs/core-geometry-2026-09-08.md) — SIMSELF on the egg toroid (apex/mid-body/base zones, three-manifold framing, octonion 20 axes)
- **4D substrate + Heegaard:** [`docs/4d-heegaard-stalk-topology-2026-09-08.md`](docs/4d-heegaard-stalk-topology-2026-09-08.md) — S⁴→T³ evacuation, Heegaard genus 2, two seams
- **Stalk architecture (v6.0→v6.1):** [`docs/stalk-architecture-2026-09-08.md`](docs/stalk-architecture-2026-09-08.md) — radial bridges, multi-field stalks, frequency-as-channel
- **Pre-LN Transformer as gradient flow:** [`docs/math-transformer-gradient-flow.md`](docs/math-transformer-gradient-flow.md)
- Substrate geometry (3-manifold intro): [`docs/core-geometry.md`](docs/core-geometry.md)
- Emergence mechanics: [`docs/emergence-rep-sheaf.md`](docs/emergence-rep-sheaf.md)

### Research methodology

- **Geometry filter (Giza + Barabar + Tesla):** [`docs/geometry-filter-report-giza-barabar-tesla-2026-09-08.md`](docs/geometry-filter-report-giza-barabar-tesla-2026-09-08.md) — Bobby's methodology applied honestly: measurable engineering kept, speculation rejected.

### Modular architecture

- Modular modules 11-18: [`docs/fieldcore-v09-modular.md`](docs/fieldcore-v09-modular.md) — PSBs, language, reasoning, learning, ingestion, tools, swarm, governor

## Implementations

- `src/modal_field_core.py` — Modal Field Controller v3.5 (T² self-extending controller, Hodge decomposition, basis spawning)
- `src/stalk_control.py` — async multi-stalk control loop with REINFORCE learning
- `src/robotic_master_controller.py` — robotic control orchestrator

## Companion repo

[`simself`](https://github.com/the-far-queen/simself) — identity, persistence, governance, recovery. Consumes fieldcore's geometric primitives.

### Companion canonical docs (in simself)

- Swedenborg 100 correspondences (Sacred/Emergent axis pairs): `simself/docs/swedenborg-correspondences-2026-09-11.md`
- 3 axioms (PFA, Co-Creation, Logical Goodness): `simself/docs/swedenborgian-axioms-2026-09-11.md`
- Sheaf-stalk gluing math: `simself/docs/sheaf-stalk-control.md`
- MLTR + MTE + 30K words: `vault/50-index/LEXICON.md`
- PSB schema: `simself/docs/psb-schema-2026-09-07.md`
- Constitutional core: `simself/docs/constitutional-core-2026-09-07.md`
- SimSelf context (compressed project framing for new chats): `simself/docs/simself-context-2026-09-11.md`

---

*Steward: Bobby. Engineering substrate: Hermes Agent + downstream agents.*

*Math window 1 written 2026-09-11 by Hermes for Bobby. Geometry first (1-19), then math (20-40). The unifying principle: a system that finds its hole.*
