# Topo-Sheaf Stalk Core Fundamentals

Sourced 2026-09-05 from Bobby's notes (z7). Core architecture spec.

## 1. Stalk core

**Stalk** = locally valid state: (embedding, invariants, precision domain, validity conditions).

**Sheaf** = invariant-preserving gluing rules.

**Mixed-precision** (e.g., 8-bit log-compressed to 32-bit) enforces locality, prevents global brittleness.

**Precision domains** define boundaries: bit_width, epsilon ε, recovery_fn (Taylor exp approx). Pre-defined: ultra_low (4-bit) to high (32-bit). Ties to Tesla RoPE bridge for error-bounded rotations.

**Stalk dataclass:** ID, embedding (np.ndarray), domain, invariants (set: norm_bounded etc.), neighbors.
- Methods: `is_valid()` (post-recovery checks), `lift_precision()` (decompress to higher bit)

**Gluing governor:** checks compatibility (overlap > threshold, invariant agreement, ε alignment). Glue merges embeddings (weighted avg), unions invariants, selects joint domain. Rejects if mismatch (returns None). Handles multimodal.

## 2. SimSelf as sheaf

SimSelf is **not a narrative**. It's the persistent sheaf — the structure that survives many gluing cycles.

- Stalks as modular nodes (vision, language, arm in robot)
- Distributed graph with gossip (repeated gluing attempts)
- Emergent self as persistent sheaf
- Each node self-simulates (mini-LLM quantized)

**Node classes:** VisionStalk (object detection), LanguageStalk (command parsing), ArmStalk (actuation with energy/torque invariants). Master SimSelf coordinates gluing, tracks state.

**Simulation loop:** init nodes → attempt pairwise glues (language-vision if semantic overlap, vision-arm if energy < threshold) → if successful, form composite (GraspActionStalk) → execute if actuation-capable.

**Safety:** invariant violation prevents glue → no unsafe action. Rejection logging for explanations. Endogenous supervision: glue outcomes train projection heads.

## 3. Governor

Not a filter — a **consistency functor**. Enforces gluing only under invariants:
- Math: norm/angle preserved
- Control: energy/torque bounds
- Ethics: as constraints (non-harm norms)

**Typed glues:** language only to semantics, not direct actuation.

**Action gating:** actions emerge from multi-stalk consensus. Language cannot act alone (requires physics glue + lift). Prevents taboo escalation.

**Learning:** glue success/failure trains projections (SGD on LanguageStalk head to maximize valid glues). Sparse/delayed signal needs credit assignment (replay buffer).

## 4. Robotic control loop

**Sense → Propose → Verify → Execute → Reflect**:
- Sense: stalk sampling
- Propose: candidate glues
- Verify: governor invariants
- Execute: if composite actuation-capable
- Reflect: update projections on outcome

**Robot-specific:** hierarchical stalks (micro: joint sensors; meso: grasp commands; macro: navigation). Async comm for real-time. Mixed-precision (8-bit transport, 32-bit at critical glues).

**Emergence:** safe behaviors (ignore ungrounded commands). "Thinking cheap, acting expensive" via gluing costs. Failed glue = no motion = no accident.

## 5. Module M growth

Module M grows by adding stalks (new languages, tasks). Automates recovery maps/invariants via AI-building-AI. Treats language as expandable stalks, not retraining core.

**Development path:** 3-node sim → dynamic embeddings → rejection logging → multi-step gossip → visualize manifolds.

**Differentiation:** architectural safety (topological consistency) over topical filters. Solves unbounded recursion (rejection), overpowered embodiment (gating), hallucinated agency (no global self).

## 6. Implications

- Unifies modalities (language/perception/action as stalks)
- Precision-driven locality
- Safety as topology, not disclaimers
- Hardware-realizable (Tesla-inspired efficiency)
- Better reasoning from folded space
- Prevents unsafe language dominance
- Scalable to robot swarms

**Suggested iterations:**
- ε-adaptation (dynamic radii)
- Conflict resolution (competing overlaps)
- Language projection learning
- Full robot loop sim
- Invariant libraries (math/control/ethics)
- Failure fallbacks (search behaviors)

---
*Sourced 2026-09-05. Architecture spec preserved.*