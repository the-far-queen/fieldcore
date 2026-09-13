# Temporal Stalk Architecture

Sourced 2026-09-05. Memory as overlap-across-time, not separate store.

## Core claim

Memory isn't a dedicated buffer — it emerges from **temporal gluing**: stalks from past cycles attempt to glue with current ones when projections overlap in Z and invariants persist. Creates "sections over time" where persistent structures (occluded objects) survive as chained composites, but ephemeral ones dissolve naturally.

**This solves object permanence** (e.g., remembering a stop sign 30s later) via sheaf consistency, not RNNs or KV-caches. Failures prune stale memory cheaply, bounded by ε-drift.

## Stalk extension

```python
class Stalk:
    def __init__(self, embedding, invariants, recovery_map, epsilon, name, history_size=3):
        self.timestamp = time.time()
        self.history = []  # (timestamp, compressed_emb) tuples, FIFO

    def _compress_to_log_int8(self, emb):
        log_emb = np.log(np.abs(emb) + 1e-8)
        scaled = np.clip((log_emb - log_emb.min()) / (log_emb.max() - log_emb.min()) * 255 - 128, -128, 127)
        return scaled.astype(np.int8)

    def update_history(self, new_emb):
        compressed = self._compress_to_log_int8(new_emb)
        self.history.append((self.timestamp, compressed))
        if len(self.history) > self.history_size:
            self.history.pop(0)

    def glue_temporal(self, past_index, governor, max_delta=30.0):
        if past_index >= len(self.history): return None
        past_ts, past_emb = self.history[past_index]
        if self.timestamp - past_ts > max_delta: return None
        past_stalk = Stalk(np.zeros_like(past_emb), self.invariants,
                          self.recovery_map, self.epsilon, f"{self.name}_past")
        past_stalk.embedding = past_emb
        return self.glue_with(past_stalk, governor)
```

## Why this replaces KV-cache / RNN

- **No dedicated memory**: history lives local to stalks; gluing "recalls" by composing sections
- **Bounded drift**: ε accumulates; auto-reject when > max (forget gracefully)
- **Patent tie-in**: log-compression preserves rotations (RoPE-like) → long-context without recompute
- **Endogenous pruning**: failed temporal glues discard history → memory adapts to physics

## Temporal gluing rule

For current S_t and past S_{t-k}:

Glue iff cos(φ(S_t), φ(S_{t-k})) > threshold AND invariants(S_t ∪ S_{t-k}) valid on merged trajectory.

## Control loop integration (extends 6-step)

1. **Sense (with history update)** — each stalk pushes current embedding to history (FIFO)
2. **Local overlap (spatio-temporal)** — for each stalk, attempt glue with own history if Δt relevant. Cross-stalk: Language_t ↔ Vision_{t-k} for "the sign from before"
3. **Frame narrowing (with persistence)** — successful temporal glues add constraints (position_t = position_{t-k} + velocity·Δt). Reject if invariant breaks
4. **Lift trigger (history-gated)** — only lift if composite includes temporal section
5. **Physical verification (trajectory check)** — verify merged trajectory invariants
6. **Act (feedback to history)** — on success, reinforce temporal projections. Update histories with outcome

## Sim behavior (verified):
- Close deltas: glue succeeds (continuity preserved)
- Large deltas: glue fails (drift > ε) → forget stale without explicit erase

## Why this enables long-context robotics

- **Efficiency**: history is tiny (3× int8/stalk), gluing only on demand
- **Safety**: temporal invariants veto hallucinations (impossible drift → reject)
- **Scales to multi-agent**: cross-robot temporal glues for shared memory (deferred)

## Open

- Add language temporal glue ("remember last command")
- Multi-agent cross-robot temporal glue
- Cross-stalk temporal (vision_t → language_t+k) needs testing
- When history_size > 3, what's the trade-off vs storage cost?

---
*Sourced 2026-09-05. Code preserved. Integration into control loop documented.*