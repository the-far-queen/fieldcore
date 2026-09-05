# FieldCore

**Math, atlas exam, geometric compute, and SimSelf theory.**

Theory and design docs for the FieldCore work. SimSelf Python package lives separately.

## Layout

- `docs/` — design docs, derivations, methodology
- `src/` — Python implementations (modal field controller, stalk control)

## Contents

### Math derivations

- `docs/math-transformer-gradient-flow.md` — Pre-LN Transformer as constrained Riemannian gradient flow (Raskutti-Mukherjee mirror-descent direction). Includes §8a quasi-periodic scheduling with golden ratio.

### Core architecture

- `docs/fieldcore.md` — root doc, three threads (math, SimSelf, code)
- `docs/fieldcore-v09-modular.md` — modules 11-18 (PSBs, language, reasoning, learning, ingestion, tools, swarm, governor)
- `docs/core-geometry.md` — three manifolds + egg toroid (unified framing)
- `docs/emergence-rep-sheaf.md` — emergence mechanics, REP formalization, sheaf cognition

### SimSelf + tools

- `docs/llm-emergence-mte-resilience.md` — LLM emergence, FieldCore IDE fork, MTE engine, Sacred Library write rules, Q3 resilience sim, tier-1 sheaf defense
- `docs/chorus-ide-design.md` — multi-agent debate IDE (VS Code fork of Roo Code)

### Implementations

- `src/modal_field_core.py` — Modal Field Controller v3.5 (T² self-extending controller, Hodge decomposition, basis spawning)
- `src/stalk_control.py` — async multi-stalk control loop with REINFORCE learning (LanguageStalk, AsyncStalkController, ConstraintPropagator, PhysicalVerifier)

## Source provenance

Each doc was sourced from Bobby's notes (`zN.txt` files + named files in `Desktop/FieldCore/`), cleaned, trimmed of speculative framing, and pushed. Originals kept on Desktop.

The 4 targets: SimSelf, Atlas Exam, math, geometric compute. Drop everything else.

## Local mirror

Bobby's working environment also has `C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\` containing all docs and src files for local reference. Same content, hermes-side.

---
*Repo established 2026-09-05. README updated as files are pushed.*