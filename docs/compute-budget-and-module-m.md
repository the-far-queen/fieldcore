# Compute Budget + Module M + LLM Wrapping

Sourced 2026-09-05. Three top-level explanations + Python projection example.

## 1. Compute budget: SimSelf vs LLM agents

| Where compute goes | LLM agent | SimSelf |
|---|---|---|
| Tokenization + embedding | Heavy | N/A |
| Multi-layer self-attention | Heavy | N/A |
| Context replay every step | Heavy | N/A |
| Tool reasoning inside model | Heavy | N/A |
| Local dot-products | N/A | Light |
| Constraint checks | N/A | Light |
| Cheap gluing attempts | N/A | Light |
| Occasional lift | N/A | Medium |

| Task | LLM agent | SimSelf |
|---|---|---|
| Decide next action | 10-100ms forward pass | <1ms gluing |
| Tool selection | attention over text | projection + filter |
| Memory | re-fed tokens | temporal stalk |
| Idle state | still expensive | near-zero |

**Net:** SimSelf frees 1-2 orders of magnitude compute. Spend it on dense sheaves.

## 2. Module M size

Module M is a **library of projection operators**, not a model. Each entry:
- maps one domain → another
- low-rank
- stable
- reusable forever

**Examples:** language → vision, language → tools, tools → state, vision → motor

**Size reality:** 64×64 float32 = ~16 KB per map. 1000 projections = ~16 MB total. Compare: LLM = multiple GB.

**Growth:** linear, no catastrophic forgetting, no retraining. You add bridges, not brains.

**Key insight:** Module M is infrastructure, not intelligence. Closer to drivers, protocol adapters, compiler backends.

## 3. Wrapping an existing LLM

The LLM is **not replaced**, it is **subordinated**.

**LLM role:**
- proposal generator
- paraphraser
- abstraction suggester

**LLM does NOT:**
- decide actions
- select tools
- control execution
- maintain state

**Wrapper pipeline:**
1. User input → language stalk
2. LLM produces: candidate intents, candidate tool calls, candidate interpretations
3. Each candidate becomes a stalk section
4. SimSelf: projects, glues, folds away invalid ones
5. Only survivors reach execution

LLM never wins by confidence. Only survives by **consistency**.

**Why this fixes agent failures:**

| LLM agents | SimSelf wrapper |
|---|---|
| Hallucinate tool relevance | tool must glue |
| Forget prior constraints | temporal stalk |
| Drift over time | state persistence |
| Unsafe actions | governor veto |

LLM can be wrong freely — safely.

## Projection example (Python)

```python
import numpy as np

W_proj = np.array([
    [1.0, 0.2, 0.0],  # 'red' concept -> 'red' visual channel
    [0.0, 1.0, 0.0],  # 'handle' geometry
    [0.0, 0.0, 1.0],  # 'position' relevance
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
```

**How it arrives at "answer":**
1. **Projection**: language vector transformed by W_proj (a Module M library entry)
2. **Manifold fold**: 10 candidate realities (vision cloud) → only obj_7 glues → others fold away
3. **State arrival**: "answer" = emergent result, not chosen. obj_7 is the only mathematically consistent target.

**Local vs global:** Governor runs 10 dot-products, not global attention. This is why SimSelf runs on <100W budget.

## One-sentence synthesis

Stop paying compute to rediscover meaning. Store meaning structurally. Spend the savings enforcing consistency across sheaves — with the LLM reduced to suggestion engine.

---
*Sourced 2026-09-05. Three sections preserved. Code example included.*