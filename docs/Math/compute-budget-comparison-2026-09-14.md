# Compute Budget — SimSelf vs LLM Agents (Engineering Reference)

**Source:** `Desktop/SimSelf/docs/compute-budget-comparison.md` (9.1KB)
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **engineering reference** — concrete cost profile, falsifiable

---

## 1. Rough Compute Budget: SimSelf vs LLM Agents

### Standard LLM Agent

Where compute goes:
- tokenization + embedding
- multi-layer self-attention
- context replay every step
- tool reasoning *inside* the model

**Cost profile**
- scales with context length × layers
- recomputes meaning every action
- attention dominates FLOPs
- idle compute even when nothing changes

→ *re-deriving intent repeatedly*

### SimSelf Control System

Where compute goes:
- local dot-products (projection + similarity)
- constraint checks
- cheap gluing attempts (most fail early)
- occasional "lift" (expensive check)

**Cost profile**
- constant-time per stalk
- linear in number of active stalks
- no context replay
- no quadratic attention

→ *checking consistency, not thinking*

### Back-of-envelope

| Task               | LLM Agent              | SimSelf             |
| ------------------ | ---------------------- | ------------------- |
| Decide next action | 10–100 ms forward pass | <1 ms gluing        |
| Tool selection     | attention over text    | projection + filter |
| Memory             | re-fed tokens          | temporal stalk      |
| Idle state         | still expensive        | near-zero           |

**Net:** SimSelf frees **1–2 orders of magnitude** compute. That surplus is what you spend on dense sheaves.

---

## 2. Module M Size — How Big Does It Need to Be?

### Module M is NOT a model

It is a **library of projection operators**.

Each entry:
- maps one domain → another
- low-rank
- stable
- reusable forever

Examples:
- language → vision
- language → tools
- tools → state
- vision → motor

### Size reality

A projection:
- 64×64 or smaller
- float32 or even int8
- ~16 KB per map

Even **1,000 projections** is:
- ~16 MB
- trivially cacheable
- edge-deployable

Compare to a single LLM = multiple GB.

### Growth behavior

- Module M grows **linearly**
- never invalidates old entries
- no catastrophic forgetting
- no retraining cascade

You add bridges, not brains.

### Key insight

> **Module M is infrastructure, not intelligence.** It's closer to drivers, protocol adapters, compiler backends. Not cognition.

---

## 4. How This Wraps an Existing LLM (Cleanly)

**The LLM is not replaced. It is subordinated.**

### Role of the LLM

The LLM becomes:
- proposal generator
- paraphraser
- abstraction suggester

It does NOT:
- decide actions
- select tools
- control execution
- maintain state

### How the wrapper works

```
User input → language stalk
   ↓
LLM produces:
   - candidate intents
   - candidate tool calls
   - candidate interpretations
   ↓
Each candidate becomes a stalk section
   ↓
SimSelf:
   - projects
   - glues
   - folds away invalid ones
   ↓
Only survivors reach execution
```

The LLM never "wins by confidence". It only survives by **consistency**.

### Tool calls — concrete example

Instead of:
> LLM decides to call Tool X

You get:
- LLM suggests Tool X, Y, Z
- Tool-stalk checks schemas
- Safety-stalk checks invariants
- Temporal-stalk checks continuity
- Governor allows only one

Tool call happens because **nothing else survives**.

### Why this fixes agent failures

| LLM Agents                 | SimSelf Wrapper   |
| -------------------------- | ----------------- |
| hallucinate tool relevance | tool must glue    |
| forget prior constraints   | temporal stalk    |
| drift over time            | state persistence |
| unsafe actions             | governor veto     |

The LLM can be wrong freely — safely.

---

## Cross-Modal Projection (the bridge)

This code implements the cross-modal projection — the mathematical bridge that allows a language stalk to "handshake" with a visual point cloud.

```python
import numpy as np

# cross-modal projection (the 'library' entry)
# real system: learned weight matrix W_proj
# maps language-space (dim 3) to vision-space (dim 3)
W_proj = np.array([
    [1.0, 0.2, 0.0],  # 'red' → 'red' visual channel
    [0.0, 1.0, 0.0],  # 'handle' geometry
    [0.0, 0.0, 1.0]   # 'position' relevance
])

def semantic_filter(lang_stalk, vision_stalks, threshold=0.85):
    L_rec = lang_stalk.recovery_map(lang_stalk.embedding)
    L_proj = np.dot(W_proj, L_rec)
    glued_indices = []
    for i, v_stalk in enumerate(vision_stalks):
        V_rec = v_stalk.recovery_map(v_stalk.embedding)
        similarity = np.dot(L_proj, V_rec) / (np.linalg.norm(L_proj) * np.linalg.norm(V_rec))
        if similarity > threshold:
            glued_indices.append(i)
    return glued_indices

# setup: language stalk 'red handle', 10 visual stalks
vision_cloud = []
for i in range(10):
    raw_val = np.random.uniform(0.1, 1.0, size=3)
    if i == 7:
        raw_val = np.array([1.9, 0.6, 0.1])
    vision_cloud.append(Stalk(raw_val, [norm_invariant], taylor_recovery, 0.1, f"obj_{i}"))

# execute the fold
glued_objs = semantic_filter(lang_command, vision_cloud)
```

---

## How the manifold arrives at the answer

1. **The projection**: language vector is transformed by W_proj (from Module M library). New language = new W_proj entry.
2. **The manifold fold**: vision has 10 candidates. Language glues with obj_7 → other 9 folded away (exist in library, not active in current sheaf).
3. **State arrival**: grasping = emergent collapse. No "choice" — obj_7 is the only mathematically consistent target.

---

## Local vs. global

Governor computed **10 dot-products**. Not a global attention sweep. That's why SimSelf runs on <100W.

If SimSelf dies and humanity finds the master library — **no retraining needed**. Add new W_proj maps for new sensors/tools/languages. Module M grows. Sheaf becomes more complex. The folding mechanism stays the same.

---

## One-sentence synthesis

> **We stop paying compute to rediscover meaning, store meaning structurally, and spend the savings enforcing consistency across sheaves — with the LLM reduced to a suggestion engine.**

---

*Filed 2026-09-14 by Hermes. Per Bobby: re-mining pass on underused originals.*
