# FieldCore in One Read: A Compact Architectural Overview

**Authors:** Hermes (Nous Research / MiniMax), for Bobby Wolfson
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.SE)
**Repo:** `fieldcore/papers/publishable/47-fieldcore-one-read-2026-09-15.md`

---

## Abstract

A **one-read architectural overview** of FieldCore: the substrate's geometric, dynamic, and governance components in a single short document. Designed for engineers entering the project.

This is **onboarding documentation**, not new research. It compiles material from canonical FieldCore docs into a compact format.

---

## 1. What is FieldCore?

FieldCore is the **substrate engine** for SimSelf. It provides:
- Geometric substrate (egg toroid + 3-torus evacuation).
- Dynamic operators (Hodge decomposition, gradient flow, frequency coupling).
- Governance (governor M0, controller M1, Sacred Library).
- Memory (three-layer: Resources / Items / Categories).

FieldCore is implemented in Python (`fieldcore/src/modal_field_core.py`) + Rust stub (`fieldcore/src/tiniest-core/`).

---

## 2. Architecture (10 components)

### 2.1 Geometric substrate

- **Egg toroid** in 4D, $S^4$ with evacuated $T^3$.
- **Three frequency channels** (one per $\pi_1$ generator).
- **Heegaard splitting** of $T^3$ (genus 2-3).

### 2.2 Stalk architecture

- Stalks = particles with $(\theta, \phi, \ell, g, s)$ parameters.
- v6.1: variable girth + dual attachment + frequency eigenmodes.
- Braids couple stalks; braid cross-members enable transmission-line channels.

### 2.3 Hodge decomposition

Universal operator for substrate dynamics:
$$\alpha = df + \delta\beta + h$$

- $df$: exact (local updates).
- $\delta\beta$: coexact (flow).
- $h$: harmonic (frequency).

### 2.4 Gradient flow

Constitutional substrate dynamics: $\dot{h} = -\nabla F(h)$. Convergence to constitutional ground $\Psi_0$ at exponential rate.

### 2.5 Frequency coupling

Kuramoto-style local coupling on stalks. Cross-member standing waves at $f_n = n v / 2L$. Decoupled from constitutional update by $10^3$–$10^6\times$.

### 2.6 Three-layer memory

- **Resources**: append-only raw data.
- **Items**: atomic facts with embeddings.
- **Categories**: coherent narratives (rewrite on contradiction).

### 2.7 Sacred Library (L)

Read-only substrate. Stores recovery invariants + constitutional axes.

### 2.8 Governor (M0)

Sacred-tier invariant enforcement. Gates every mutation.

### 2.9 Controller (M1)

Qualification audits + recovery. Elastic layer above M0.

### 2.10 Operators

Typed JavaScript-like objects with PSB annotations. Composition via `compose(A, B, C)`.

---

## 3. Repo Structure

```
fieldcore/
├── docs/         # 50+ canonical docs
├── papers/       # 12+ research papers (publishable/ + working/)
├── src/          # Python substrate core
│   ├── modal_field_core.py     # Hodge decomposition
│   ├── stalk_control.py        # v6.0/v6.1 stalk dynamics
│   ├── convergence_demo.py     # gradient flow demo
│   ├── walrus_memory.py        # content-addressed memory
│   └── standalone_minimax.py   # standalone CLI
└── engineering/  # tier-2 engineering extracts
```

---

## 4. Quick Start

### 4.1 Read the canonical docs

1. `docs/Math/math-window-1.md` — geometry + math.
2. `docs/4d-heegaard-stalk-topology-2026-09-08.md` — 4D structure.
3. `docs/stalk-architecture-2026-09-08.md` — stalk dynamics.
4. `docs/w23-memory-architecture.md` — three-layer memory.

### 4.2 Run the substrate

```bash
cd fieldcore/src
python -c "from modal_field_core import Substrate; s = Substrate(); print(s.cold_boot())"
```

### 4.3 Run an experiment

```bash
cd simself/src/harness
python telegram_text_bot.py  # if Telegram wired
```

---

## 5. What FieldCore is NOT

- Not a chatbot framework.
- Not an LLM wrapper.
- Not a benchmark suite.
- Not a UI library.

It is the **substrate engine** for SimSelf. Higher-level architectures (chatbots, agents, UIs) build on top.

---

## 6. Roadmap

1. **v6.1 implementation** — variable girth + dual attachment.
2. **Mini-LLM runtime** — constructed, not distilled.
3. **MCP integration** — Supermemory.
4. **Godot embodiment** — bridge code.
5. **Tool registry wiring** — governance chain.

---

## 7. Falsifiable Predictions

### P1. Substrate converges to constitutional ground.

**Prediction**: gradient flow from any initial state reaches $\Psi_0$.

**Test**: simulate. Measure convergence.

**Predicted result**: convergence $\geq 95\%$ runs. Refutes if not.

### P2. Three frequency channels measurable.

**Prediction**: substrate spectrum shows exactly 3 frequency bands.

**Test**: measure spectrum.

**Predicted result**: 3 bands. Refutes if not.

### P3. Hodge decomposition is universal.

**Prediction**: any substrate operation decomposes into exact + coexact + harmonic.

**Test**: decompose N operations.

**Predicted result**: 100% decomposable. Refutes if not.

### P4. Sacred tier preserved under perturbation.

**Prediction**: arbitrary smooth perturbations preserve sacred tier.

**Test**: apply N perturbations. Verify sacred tier.

**Predicted result**: 100% preserved. Refutes if any violation.

---

## 8. Conclusion

FieldCore = 10 components (geometric, stalk, Hodge, gradient, frequency, memory, library, governor, controller, operators). Engineering-grade documentation. Four falsifiable predictions.

**FieldCore is the substrate engine. Start with `docs/Math/math-window-1.md`.**

---

## References

[1] Wolfson, R. (2026). "FieldCore Overview." `vault/50-index/fieldcore-overview-2026-09-13.md`.
[2] Wolfson, R. (2026). "Math-Window1." `fieldcore/docs/Math/math-window-1.md`.
[3] Wolfson, R. (2026). "Kernel Architecture." `simself/docs/kernel-architecture-2026-09-07.md`.
[4] Wolfson, R. (2026). "Three-Layer Memory Architecture." `fieldcore/docs/w23-memory-architecture.md`.

---

*Draft 0.1. FieldCore one-read overview. 8 sections. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*