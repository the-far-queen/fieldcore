# FieldCore — the whole control system

**Filed 2026-10-09 by Hermes, per Bobby's correction:**

> "fieldcore is not the core it is defined as the whole control system of
> modules"

**THIS SUPERSEDES the framing in `README.md` and `docs/PRODUCTS/README.md`,
which present fieldcore as a mathematical substrate or a lint tool.** Those
are parts. This is the whole.

---

## What fieldcore is

fieldcore is the **complete control system** — every module, every
control law, every substrate it runs on, and the proof obligations that
hold it together. It is not a library that `simself` imports. It is the
machine; simself is one of its parts.

```
┌──────────────────────────────────────────────────────────────┐
│                    FIELDCORE — THE SYSTEM                    │
│                                                              │
│  SUBSTRATE                                                   │
│    egg-toroid · apex void = invariant zero · 3D reasoning   │
│    surface · gradient flow F(x)=½‖x-ψ₀‖²                    │
│                                                              │
│  CONTROL                                                       │
│    M0 Governor      IN CORE     1-bit veto, sacred axes     │
│    M1 Controller    OUTSIDE     qualifies, audits, promotes  │
│    Regulator                     6 avatar axes               │
│    Security Layer                integrity, adversarial      │
│                                                              │
│  SHEAVES (4, typed and bounded)                              │
│    Topology · MLTR · MTE · Coding                             │
│                                                              │
│  LIBRARY                                                       │
│    Sacred Library — read-only from below, append-only above   │
│                                                              │
│  OPERATORS                                                     │
│    coding · robot · language · speaker/listener              │
│                                                              │
│  ADAPTATION                                                   │
│    research loop · self-coding · real-time mini-LLM           │
│    idle-microsecond dreaming · learned scheduling            │
│                                                              │
│  PROOF                                                         │
│    steel-ball convergence · coherence_spine · envelope        │
│    resilience · falsifier · atlas-exam (the certificate)     │
└──────────────────────────────────────────────────────────────┘
```

**The authority rule the whole system exists to enforce:**

    SimSelf PROPOSES  →  M1 audits  →  Atlas Exam qualifies  →  M0 commits or vetoes

SimSelf may never write the Library. Three of the four steps stand
outside the thing being governed. **That separation is the architecture.**
It is not a policy document; it is the shape of the call graph.

## Where each part lives, today

| part | repo | state |
|---|---|---|
| substrate, proofs, atlas-exam | **fieldcore** | 404 passed |
| identity, operators, governance internals | **simself** | 301 passed |
| the Library as a corpus | **sacred-library** (proposed) | to build |
| the certificate itself | **atlas-exam** | 79 passed, now public |

**simself is part of fieldcore, not a peer of it.** When the two
disagree, fieldcore's definition governs, because fieldcore is the
system and simself is a component.

## What is proven rather than asserted

The system makes four falsifiable claims and all four are executable:

1. **Convergence is substrate-invariant.** A steel ball on a concave
   surface always finds the hole; so does one projected gradient step.
   `src/steel_ball_proof.py` — bound independent of the starting point.
2. **A system is held by thresholds on a sheaf, and the quality of the
   holding is coherence.** `src/coherence_spine.py` — measured across
   six frontier transcripts; three concepts, 6/6 files, now executable.
3. **Guard the proposal, not the guarded quantity.** `resilience.py`
   (simself) — the Hodge and resistance bugs were both a guard whose own
   action defeated the check it fed.
4. **An area that cannot fail is not an area.** `atlas-exam` — mutation
   yield, not pass rate; area 10 exists to prove the exam notices.

## What the system does not yet do

Measured 2026-10-09, stated rather than implied:

- **the learning loop is unwired.** `loop.MainLoop`,
  `selfcore`, `coding_operator_object`, `robotic_field_core`,
  `training_bridge`, `m1_m0_negotiation` and `modulator` are present and
  never called. Present, readable, dark.
- **ten of 23 exam areas are unwritten.** Verdict FAIL, correctly.
- **one component cannot be instantiated.** `TemporalController` in the
  frontier material — `_heuristic_policy` is assigned but never defined.

An inventory that is on the record cannot be mistaken for progress.

## Related, and superseded by this file

- `docs/fieldcore-architecture-2026-09-14.md` — module list, substrate
- `docs/six-file-extrapolation-2026-10-09.md` — the arc across six
  frontier transcripts
- `docs/corpus-vocabulary-index-2026-10-09.md` — the spine
- `simself/docs/the-system-2026-10-09.md` — same system, written from
  simself's side
- `atlas-exam/papers/` — the certification paper