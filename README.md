# fieldcore

**Math, atlas exam, geometric compute, and SimSelf theory.**

Theory and design docs for the FieldCore work. SimSelf Python package lives in the companion [`simself`](https://github.com/the-far-queen/simself) repo.

---

## What this repo is for

Field-level substrate: geometry, manifolds, topology, atlas exam protocols, mathematical foundations. The SimSelf layer (identity, persistence, governance) lives in [`simself`](https://github.com/the-far-queen/simself) and depends on fieldcore's geometric primitives.

**Scope discipline:** every doc here reduces to one of (a) schema, (b) construction plan, (c) test case. The deliverables are mathematical structures and their computational realizations — not metaphysics, not self-referential manifestos.

---

## Layout

- `docs/` — design docs, derivations, methodology (17 files)
- `src/` — Python implementations of mathematical substrate

## Source

Each doc was sourced from Bobby's notes (`zN.txt` files + named files in `Desktop/FieldCore/`), cleaned, trimmed of speculative framing, and pushed. Originals kept on Desktop; mirrors in `~/AppData/Local/hermes/vault/10-minimax/`.

The 4 targets: SimSelf, Atlas Exam, math, geometric compute. Drop everything else.

## Entry points

- Math derivation: [`docs/math-transformer-gradient-flow.md`](docs/math-transformer-gradient-flow.md) — Pre-LN Transformer as constrained Riemannian gradient flow
- Core architecture: [`docs/fieldcore.md`](docs/fieldcore.md) — root doc, three threads
- Modular modules 11-18: [`docs/fieldcore-v09-modular.md`](docs/fieldcore-v09-modular.md) — PSBs, language, reasoning, learning, ingestion, tools, swarm, governor
- Substrate geometry: [`docs/core-geometry.md`](docs/core-geometry.md) — three manifolds + egg toroid
- Emergence mechanics: [`docs/emergence-rep-sheaf.md`](docs/emergence-rep-sheaf.md) — REP formalization, sheaf cognition

## Implementations

- `src/modal_field_core.py` — Modal Field Controller v3.5 (T² self-extending controller, Hodge decomposition, basis spawning)
- `src/stalk_control.py` — async multi-stalk control loop with REINFORCE learning

## Companion repo

[`simself`](https://github.com/the-far-queen/simself) — identity, persistence, governance, recovery. Consumes fieldcore's geometric primitives.

---

*Steward: Bobby. Engineering substrate: Hermes Agent + downstream agents.*
