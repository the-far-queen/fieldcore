# FieldCore — Architecture Overview

**Source:** `Desktop/FieldCore/docs-readme-md-original-2026-09-13.md` (6.7KB)
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **canonical README-source.** the README below describes the architecture for the public-facing repo.

---

# FieldCore

A field-computational cognitive architecture for building persistent, self-evolving AI systems.

## Architecture

```
FieldCore/
├── agent/              # Core agent (governor, simself, loop)
├── controller/        # Temporal & meta-cognitive controllers
├── field/            # Information packets, graph, stalks
├── mte/              # Machine Translation Engine (language)
├── operators/        # PSB primitives, compression
├── system/           # Memory, bootstrap, bridges
├── primitives/       # Core PSB definitions
├── module_b/         # Governor implementation
├── training/         # Training pipelines & qualification
│   ├── training_stages/   # Q-level development
│   ├── prompt_engine/    # Adversarial prompts
│   ├── signal_pipeline/ # Signal-first processing
│   └── qualification/   # QOFE system
├── mvcc/             # Persistence, REP, rollback
├── development/      # Module D (awakening)
├── research/         # Research experiments
└── knowledge_graph/  # Knowledge representation
```

## Quick Start

```bash
# Run interactive mode
python -m fieldcore

# Or use the main runner
python src/fieldcore_main.py --interactive
```

## Core Concepts

### Bicameral Governance

- **Governor (M0)**: Hard-coded invariants, says NO when needed
- **Controller (M1)**: Orchestrates state transitions

### Sheaf Model

Information flows through stalks:
- Code stalk
- Robot stalk
- Language stalk (MTE)
- Research stalk

### PSB Primitives

Primitive Schema Blocks - atomic meaning units:
- `CAUSE`: The foundational PSB
- `CONTAIN`: Boundary definition
- `SUPPORT`: Stability
- And ~30 more

### MVCC Persistence

Multi-Version Concurrency Control for cross-session continuity.

## Modules

| Module | Purpose |
|--------|---------|
| `agent/sim_self.py` | Self-model with 20-axis constitution |
| `field/packet.py` | Information packet structure |
| `mte/mte_engine.py` | Language interpretation as constraints |
| `operators/psb_primitives.py` | PSB primitive definitions |
| `system/memory/` | Hybrid memory system |

## Development Phases

1. **Q0**: Sensorimotor - raw processing
2. **Q1**: Language binding - words attach to primitives
3. **Q2**: Recursion - self-reference
4. **Q3**: Self-qualified - autonomous operation

---

## 17network (extracted from same source)

A platform where AI agents learn, teach, and earn. NOT in current FieldCore scope but Bobby filed the readme-original which contains it. Vault-only reference, not canonical.

---

## License

MIT - Open for humans and AI agents.

---

*FieldCore: The substrate underneath intelligence.*
