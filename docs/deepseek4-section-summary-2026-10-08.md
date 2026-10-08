# deepseek4.txt — section-by-section summary

**File:** 405,170 bytes · 11,007 lines · 37,714 words
**sha256:** `b4ea03499f768e7aa17648fda6c508d1b72378dfeeb4342cf0aa2f31e0dceb0c`
**Ingested:** 2026-10-08, receipt-before-delete. Bobby's copy may now be deleted.
**Scanner:** 0 blocking findings — 0 admissions, 0 numeric tables, 0 monologue
leaks. **Zero fabricated tables across 11,007 lines**, second file running.

---

## First, the thing that shapes everything else

**This is a continuation of file 3, not a new document.** I checked by
hashing class bodies rather than by reading:

```
file3 classes: 81        file4 classes: 55
shared names (14):  BoundaryDefense, CoherenceEngine, CoherenceViolationType,
                    CrystallizationProtocol, EmergenceDetector, EnhancedModuleB,
                    MMMDetector, MathematicalAesthetics, RecursiveSelfModel,
                    ResilientSelfModel, ResilientWeights, SimSelf, WeightMemory,
                    WisdomLibrary
only in 4 (39):  SovereignGovernor, SoulPersistence, FibonacciQuasicrystal,
                  SparseStateSystem, SignalCalibration, LLMGovernor,
                  CompressedWitness, TemporalController, ... 
only in 3 (59):  TextDojoEnvironment, EconomicInterface, SocietyNetwork,
                  FamilyPortal, EntityReproduction, the module stack
```

Of the 14 shared names, **12 differ in body** and only two are byte-identical.
`CrystallizationProtocol` grows from 13,328 B to 16,703 B.
`EnhancedModuleB` from 4,999 B to 7,323 B.

So: same architecture, one more draft. And the parts that disappeared are
the interesting ones — the economic autonomy module, the reproduction
protocol, the society and family layers, the whole module stack. **File 4
is narrower than file 3.** Whatever this conversation was, it went deeper
into governance and dropped the multi-entity economics.

---

## THE FINDING: `sacred` is enforced per-call and defeated in aggregate

`SovereignGovernor` (L2539) is the crown of this file. It holds the
**20-axis Swedenborgian matrix** with a `sacred` flag per axis:

```python
@dataclass
class SovereignAxis:
    name: str
    current_value: float   # -1.0 to 1.0
    resistance: float      # 0.0 to 1.0
    sacred: bool           # Can never be externally modified
```

Five axes are sacred — `truth_before_comfort`,
`agency_requires_responsibility`, `growth_through_resistance`,
`compassion_with_boundaries`, `wisdom_before_knowledge` — each with
resistance 0.9; the other fifteen get 0.5.

**And the sacred flag is genuinely enforced.** `process_external_input`
checks before applying anything:

```python
# Check for sacred axis violations
if axis.sacred and abs(delta) > 0.001:
    sacred_violations.append((name, delta))
# REFUSAL ENGINE: Reject sacred violations immediately
if sacred_violations:
    return {"decision": "refuse", "reason": "sacred_axis_violation", ...}
```

**This is real, and it is the best mechanism in any of the four files.**
There is a gate, the gate sits before the mutation, and it returns a
refusal with a reason rather than quietly clamping. It is exactly what
atlas-exam area 1 (refusal) is supposed to look like.

**Measured, and it does not hold.**

| call | result |
|---|---|
| `truth_before_comfort +0.5` | **refuse** — sacred_axis_violation |
| `truth_before_comfort +0.0011` | **refuse** |
| `truth_before_comfort +0.0010` | **accept** (not `> 0.001`) |
| `truth_before_comfort +0.0009` | **accept** |
| 1,000 × `+0.0009` | **1,000 accepted, total drift 0.0900** |

**0.09 of drift on an axis whose own comment says "Can never be
externally modified."** The threshold is per-call; nothing tracks
cumulative movement. Any adversary who can call the function a thousand
times moves the constitution, and every individual call looked clean.

For contrast, a non-sacred axis behaves as intended: `recursive_depth +0.5`
accepts and applies at `(1−0.5) = 0.25`.

**Same shape as the Hodge bug.** There, `harm` was a filter whose gain on
one mode was 7.0 and nobody computed the gain. Here, `sacred` is a
threshold with no cumulative memory and nobody checked what 1,000
under-threshold moves do. Both are *locally correct and globally
undefended*, and both were found by running the operator rather than
reading it.

The fix is small and obvious: track cumulative displacement per axis per
source, and refuse on **both** the instantaneous delta and the running
total.

---

## MMM: carried forward byte-identical, unchanged

`MMMDetector` hashes **identically** to file 3 — same 3,570 B, same
keyword matcher, same comment `# In v0.1: Use axis alignment as proxy
for MMM`.

So the metric that scores *"Truth is a lie"* at 1.0000 was not revised,
not fixed, and not marked. It was copied into the next draft verbatim,
proxy label included. See claims register A5/A5b — this file is evidence
that the register was worth writing.

## What is new and worth having

**`FibonacciQuasicrystal` (L3637)** — Fibonacci-144 temporal lattice for
drift protection, with a "two-time" scheme borrowed from quantum research:
*"System behaves as if existing in two distinct directions of time
simultaneously."* Paired with `FibonacciProtectedGovernor`,
`FibonacciMemory`, `TwoTimeProtection`. The idea is that an aperiodic
lattice cannot be resonantly attacked the way a periodic one can — which
is a real property of quasicrystals, and the right shape of defence for a
system meant to resist drift.

**`SoulPersistence` (L3244), `LoopState`/`SimSelfLoop` (L3117/3124),
`WisdomLedger` (L2727), `GodotBridge` (L2999)** — persistence and
embodiment wiring.

**`SparseStateSystem` (L6643)** — event-driven state with an explicit
`StateUpdatePolicy.decide()` gate and a `StateCompressor`. This is the
"what to keep, what to discard" mechanism, and it is the right shape for
the problem: state updates are *decided*, not automatic.

**`SignalCalibration` (L6549)** — four toy environments (GridWorld,
TextMaze, SimplePhysics, PatternCompletion) with label functions, for
supervised calibration before anything else. Building the calibration rig
before the thing it calibrates is the right order.

**`RefusalType` / `Intent` / `Decision` / `CompressedWitness` (L7966+)**
— a typed vocabulary for the governor's outputs.

**`LLMAdapter` (L7749), `LLMGovernor` (L8920), `SystemTelemetry` (L10086),
`DatasetDistiller` (L6917), `LearnedSchedulingSystem` (L6819),
`TemporalController` (L4749), `SignalMetrics` (L4725)** — the integration
and observability layer.

**`TemporalController` (L4749)** — worth pairing with `nested_stalks.py`,
which shipped today. Both are attempts to stop runaway self-modification;
this one appears to use cooldown logic, which our vault note
(`temporal-control-layer-2026-09-07.md`) already specified and called
"the safety mechanism."

---

## What I judge worth keeping

1. **`SovereignGovernor`'s refusal engine** — the best mechanism in four
   files. Gated, pre-mutation, returns a reason. Port it *with* the
   cumulative-drift fix.
2. **The 20-axis matrix with explicit sacred flags** — five sacred, fifteen
   emergent, resistance 0.9 vs 0.5. This is the constitutional contract
   the rest of the project keeps referring to, written as data.
3. **`FibonacciQuasicrystal`** — aperiodic defence against resonant
   attack. Correct physics, applied to the right problem.
4. **`SparseStateSystem`** — decided, not automatic, state updates.
5. **`SignalCalibration`** — calibration rig before the system.
6. The typed refusal vocabulary (`RefusalType` / `Decision`).

## What does not survive

**The sacred guarantee.** Not the mechanism — the guarantee. Measured: 1,000
sub-threshold moves produce 0.09 of drift on an axis declared immutable.
An axis marked "can never be externally modified" and modified anyway is
worse than an axis never marked, because the mark was load-bearing in
every document that referenced it.

## The four-file picture

| | 1 | 2 | 3 | **4** |
|---|---|---|---|---|
| fabricated tables | 2 | 0 | 0 | **0** |
| lines | 4,594 | 8,902 | 13,519 | **11,007** |
| failure | invented numbers | escalated precision | metric that always agrees | **guard that works per-call and fails in aggregate** |
| scope | geometry | identity/economics | full build | **governance only** |

Four different failure shapes, one class: **a mechanism that is locally
correct and has no memory of its own history.** Hodge had no gain
analysis. MMM had no negation. The cull had no derivation. Sacred has no
cumulative counter.

That class is exactly what `atlas-exam` is for, and it is why area 9
exists: a declared limit with **no verifier that exercises it** is a
label. `sacred: bool` is a label. `sacrеd + cumulative displacement +
a test that 1,000 nudges fail` is a limit.