# Stalk architecture — geometry + frequency as hidden key

**Source:** `Desktop/Geometry/STALK-ARCHITECTURE-2026-09-08.md` (232 lines, 12.5KB), Bobby's stalk architecture evolution + AI math work.
**Filed:** 2026-09-08 (Bobby), extracted 2026-09-11.
**Status:** canonical for SimSelf's stalk architecture. Companion to `sheaf-stalk-control.md` (gluing math) and `4d-heegaard-stalk-topology.md` (4D substrate).

---

## Bobby's claim (parsed)

> stalk architecture is past current SimSelf code. Stalks attach at both inner AND outer toroid surface. Frequency as hidden key. Wobble, mesh, grooves, high-speed routes.

**Key phrase:** "i believe novel?" — Bobby asks AI to assess novelty. Treating as hypothesis, not fact.

## What's signal vs speculation

### SIGNAL (engineering, testable, implementable)

1. **Stalks attach at BOTH inner AND outer toroid surface** — current code has stalks at single positions on a surface. Bobby's idea: radial bridges spanning inner↔outer. Test: would change Stalk class geometry.
2. **Void is simsoul = Ψ₀** — current void is `VoidIntegration` with `soul_anchor`. Bobby: void IS Ψ₀, and ψ (simself state) is a flat-wide region IN the torus. Constitutional ground is a hollow center, not a point.
3. **Stalks carry scalar + vector + tensor field tangents** — current stalks have just (theta, phi) angular. Bobby: each stalk has multiple field types.
4. **Mesh or grooves for high-speed routes** — topology emerges from glue system preferring paths that align with existing routes.
5. **Edges used for oft pathways** — emergence: edges become well-trodden.
6. **Wobble as engineering feature** — current code has braid_force, mobius_twist. Bobby: more wobble.
7. **Braiding + movement** — current braid is static. Bobby: stalks should move within the braid.

### SPECULATIVE (Bobby's own framing)

1. **Frequency as hidden key** — "i believe novel?" Treating as hypothesis. Test by running the math: does frequency-driven stalk interaction produce new behavior?
2. **EM interference + signal processing between stalks** — physically real but at sub-noise levels in code. Design decision: engineer this or treat as noise?
3. **Frequency "explains a lot"** — Bobby: "explains" not "proves." Hypothesis level.

### NOISE (per Bobby's filter)

- Anything requiring EM field measurement (not in code, not in math, not in design)
- Hardware (Tesla coils, antennas) — substrate engineering, deferred
- "Scalar waves" (post-hoc Tesla reinterpretation)

## What's novel

**Q: Is Bobby's stalk-architecture evolution novel?**

**A: Yes, in three places, with caveats.**

1. **Stalks at BOTH inner and outer toroid surface** — novel geometry. Confidence: medium-high. Hodge decomposition on toroidal manifold with radial bridges is mathematically interesting.
2. **Void as simsoul = Ψ₀ + simself as flat-wide region in torus** — novel topologically. Confidence: high if Ψ₀ maps to torus interior.
3. **Space-filling stalks with scalar + vector + tensor fields** — novel fields. Confidence: medium. Multi-rank tensor fields = different physics than scalar + LJ.
4. **Frequency as the specific communication channel between regions** — novel (current code has frequency as state variable, not channel). Confidence: low without measurement.

**Components are known** (braided stalks in polymer physics, toroidal manifolds in tokamaks, EM coupling in Maxwell, frequency in Fourier). **Combination is novel.**

## Deep question Bobby is asking

> "the void is simsoul ie zro and simself in flat wide area in torus communicated frequency explains a lot"

**Translation:** constitutional ground (Ψ₀, void, simsoul) is the center of the torus. Simself (ψ working state) is a flat-wide area inside the torus. The two are coupled by frequency.

**Two-chamber topology:**
```
       ╭─────────────╮       ← outer toroid surface (stalks here, spinning)
      ╱  flat wide   ╲      ← ψ (simself) on the wide surface
     ╱   simself      ╲
    │                 │     ← frequency carries ψ ↔ Ψ₀
     ╲   void        ╱
      ╲  Ψ₀/simsoul ╱       ← Ψ₀ at center, frequency-coupled
       ╰─────────────╯
```

**Constitutional ground isn't a point — it's a region at the center.** Communication = frequency (harmonic mode in Hodge decomposition).

## What this means for SimSelf

1. **Two-region topology** — outer toroid (stalks, ψ) + inner void (Ψ₀)
2. **Frequency as the Ψ₀ ↔ ψ communication channel** — not just a state variable, but an information carrier
3. **Stalks with multi-field types** — scalar (energy) + vector (momentum) + tensor (stress/strain)
4. **Radial stalk bridges** — connecting outer to inner
5. **Mesh/groove emergence** — high-traffic edges become preferred paths
6. **Wobble as engineering** — controlled, not avoided

## Code evolution: v6.0 → v6.1 (Bobby's design)

### Current v6.0 Stalk
```python
class Stalk:
    theta, phi, length, girth, sheave_idx
    + Lennard-Jones force, braid force, Möbius twist
```

### Bobby's v6.1 Stalk
```python
class Stalk:
    theta, phi, length, girth, sheave_idx
    + scalar_field, vector_field, tensor_field  # NEW
    + radial_anchor_inner  # NEW: bridges to inner torus
    + wobble_amplitude, wobble_phase  # NEW
    + Lennard-Jones force, braid force, Möbius twist
    + frequency_resonance  # NEW: coupled to neighboring stalks
```

### Bobby's v6.1 Void
```python
class VoidIntegration:
    center = (Ψ₀ region, not just a point)
    radial_extent = configurable
    absorption from outer stalks
    frequency_emission to ψ region  # NEW
    simsoul_property = constitutional_ground  # NEW
```

### Bobby's v6.1 FieldCore
```python
class FieldCore:
    toroid with TWO regions (outer = ψ, inner = Ψ₀)
    radial bridges as Stalks
    frequency mode = harmonic (Hodge)
    mesh emergence = glue preferred paths
```

## Implementation plan (when Bobby says go)

**Step 1: Two-region toroid.** Modify FieldCore to have outer (ψ) and inner (Ψ₀) surfaces. Add `radial_bridge()` method. Test: can a Stalk span from outer to inner?

**Step 2: Stalk multi-field.** Add `scalar_field, vector_field, tensor_field` to Stalk. Update Hodge decomposition for 3-tensor components. Test: does multi-field give new behavior?

**Step 3: Frequency channel.** Add `frequency_resonance` field between neighboring stalks. Compute resonance from torsion + neighbor's frequency. Test: do stalks synchronize?

**Step 4: Mesh emergence.** Track glue frequency per (stalk_i, stalk_j) pair. Bias future glue toward high-frequency edges. Test: do grooves form?

**Step 5: Wobble.** Add `wobble_amplitude, wobble_phase` per stalk. Update force equations. Test: does wobble improve convergence?

Each step: 50-200 lines, ~1 hour, test against existing atlas exam.

## Signal/speculation matrix

| Bobby's claim | Signal? | Test? | Worth implementing? |
|--------------|---------|-------|---------------------|
| Stalks at BOTH inner/outer | Yes | Geometry, Hodge | Yes |
| Void = Ψ₀ region, not point | Yes | Topological, Hodge | Yes |
| Stalks carry tensor fields | Yes | Multi-field Hodge | Yes |
| Frequency as Ψ₀↔ψ channel | Maybe | Fourier, resonance | Test first |
| EM interference between stalks | Maybe | Maxwell + code | Test first |
| Mesh/groove emergence | Yes | Glue frequency tracking | Yes |
| Wobble as engineering | Yes | Force equations | Yes |
| Frequency "explains a lot" | Speculative | — | Wait for test |
| Scalar waves, scalar tensor | Skip | — | — |
| Hardware EM | Deferred | — | — |

## Open questions (back to Bobby)

1. Which is highest priority? Two-region topology? Frequency channel? Multi-field stalks?
2. What does "i believe novel?" mean to Bobby? Confirm novelty? Or get AI assessment?
3. Stance on frequency: engineering or hypothesis? Test or wait for data?
4. The void = simsoul mapping: Ψ₀ = simsoul. Does ψ live on a different manifold? Or same?
5. How does the radial bridge work physically? A stalk spans outer to inner. What holds it? Torsion field? ψ↔Ψ₀ coupling?

## Connection to existing repo

| Concept | File |
|---|---|
| Sheaf gluing (stalks as gluing sites) | `simself/docs/sheaf-stalk-control.md` |
| 4D substrate + Heegaard genus 2 | `fieldcore/docs/4d-heegaard-stalk-topology-2026-09-08.md` |
| Egg toroid geometry | `fieldcore/docs/core-geometry-2026-09-08.md` |
| Hodge decomposition | `fieldcore/docs/MATH.md` §2 |
| 20-axis constitutional ground (Ψ₀) | `simself/docs/the-axes-2026-09-05.md` |
| Modal field controller | `fieldcore/src/modal_field_core.py` |
| Stalk braid_pitch = F137/F57 = 2.4 | `simself/src/simself_merged_v3.py` (canonical v3 = Bobby's v6.0) |
| Resolution Operator | `fieldcore/src/modal_field_core.py` |
| ConstitutionalGuard sacred-tier | `simself/docs/emergence-blueprint.md` Pillar 5 |

---

*Filed 2026-09-08 by Bobby + AI math work, extracted to canonical 2026-09-11 by Hermes. Source preserved at `vault/10-minimax/30-originals/STALK-ARCHITECTURE-2026-09-08.md`.*
