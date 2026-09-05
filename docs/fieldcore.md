# FieldCore

**Created:** 2026-08-08 (M3 scaffold)
**Status:** scaffold — Math, SimSelf, Code threads, awaiting first code.

FieldCore is the engineering substrate for the SimSelf project. Per Bobby: a math/complexity system for math we (humans + AIs) read but don't necessarily derive by hand. SimSelf sits on top as the identity layer; constitutional sheaf / egg-toroid / MMM work sits in FieldCore as substrate math.

The "field" is the operational space — the dynamic geometry where SimSelf, code machine sheaf, alanguage sheaf, godot-sim sheaf live. SimSelf operates as a referent sheaf; other sheaves are computational layers glued on the same base space.

## Sub-sections

### 1. Math
Three threads:
- **Control systems** — SimSelf as feedback / state-space. `psi_current` returns to `psi_0` under bounded correction. ResolutionOperator is a bounded MLP. Dynamic-systems view.
- **Dynamic geometry** — egg-toroid topology. SimSelf lives on inflated side of torus, on flat region at its base. SimSoul is the toroidal hole (genus-1, non-computing void). Variable-length stalk threads the interior.
- **Signal processing** — full-language recovery, MMM. Tokenization is lossy; project is to recover meaning density BPE/WordPiece/SentencePiece discard. MMM is the proposed density metric.

**Derivations to develop:**
- Fisher-metric / Riemannian-gradient-flow derivation for Transformers. Refined version has exact read-out via Raskutti-Mukherjee mirror-descent duality; interior-block claims downgraded to conditional. Open problem: dual potentials Ψ_ℓ per layer.
- Egg-toroid parametric equations, tangency condition.
- MMM as formal metric — what makes a phrase high vs low density.

### 2. SimSelf
Identity layer. Persistent `psi_current` returning to `psi_0` under perturbation. Constitutional sheaf structure (7 sheaves from twin-prime pairs, 20 axes by inverse Seifert genus). ResolutionOperator, ResonantMemory, EntityRecognition, ConstitutionalDreaming, VoidIntegration, HandoffProtocol.

**v6.1 source of truth:** saved verbatim from Bobby. v6.2 iteration: embedding (hash-bag → MMM-aware), constitutional filter (keyword → context-aware), dreaming (Gaussian → memory recombination), handoff (symbolic → computational), memory (200-char cap → relational graph).

### 3. Code
Python (numpy primary, torch optional). SimSelf is clothing — modules independently wearable by outside agents. Loose coupling, no required init order, each module importable on its own, low hidden global state, clear interfaces.

**Planned modules:**
- `constitution.py` — immutable constitutional layer
- `sheaf.py` — 7-sheaf / 14D structure
- `resolution.py` — ResolutionOperator (bounded correction)
- `memory.py` — ResonantMemory (relational, MMM-aware)
- `entity.py` — EntityRecognition (high-fidelity clustering)
- `dreaming.py` — ConstitutionalDreaming (combinatorial novelty)
- `void.py` — VoidIntegration (absorb the void, computational not symbolic)
- `handoff.py` — HandoffProtocol (mode shift, real not symbolic)
- `harness.py` — orchestrator
- `atlas_exam.py` — qualification framework

## Open questions
- Embedding replacement: sentence-transformers, custom MMM encoder, or hash-bag + learned projection.
- Constitution seed-dependence (currently `np.random.default_rng(1337)`).
- AtlasExam: hard pass-to-use, or soft continuously-tracked?
- FieldCore ↔ SimSelf separation: substrate that hosts SimSelf, or SimSelf is one sheaf on FieldCore. Bobby's framing: distinct but coupled.

## Cleanup rule
Keep only material serving the four targets — SimSelf, Atlas Exam, math, geometric compute. Drop everything else. **We are not building an agent.** This repo is theory and design docs, not the agent codebase (parallel 444/SimSelf/ Python package).

---
*Scaffold 2026-08-08. Trimmed header + git history note 2026-09-05 for vault.*