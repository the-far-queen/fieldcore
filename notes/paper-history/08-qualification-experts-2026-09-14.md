> **Moved to `notes/paper-history/` on 2026-09-16** (per Grok sharpen 2026-09-16, applied by Hermes).
>
> **Reason:** stale draft superseded by the 2026-09-15 version.

# Paper 12 — Qualification of FieldCore Experts: A Geometric Audit Protocol (DRAFT)

**Title:** *Qualification of FieldCore Experts: A Deterministic Geometric Audit Protocol for Mixture-of-Experts Substrates*

**Status:** DRAFT. Created 2026-09-14 by Hermes (auto-paper-build per Bobby's directive).
**Source:** `simself/docs/qofe-qualification-experts-2026-09-14.md` (md5 94af26aea16778cb8bd0f0335843a4c5).
**Authors:** Robert David Wolfson (Bobby) first author; Hermes (Minimax-M3) second.
**Venue:** AI architecture / mixture-of-experts venue.

---

## Abstract

A geometric audit protocol that certifies **expert qualification** as a property of geometry rather than empirical performance. The protocol enforces four invariant checks — descent validity (∇F·Δh < 0 everywhere in the certified region), basin stability (||∇F|| → 0 within bounded time), metric conditioning (κ(g) < κ_max), and constraint compatibility (c(h_t) ≤ ε). Qualification is determined via stress probes — basin centers, basin boundary, constraint-adjacent, adversarial curvature — applied to a shared probe set H_qual across experts. Rollout is deterministic; no sampling. The protocol prevents silent expert failure, degenerate collapse, geometry drift after fine-tuning, fake specialization, and constraint-breaking reasoning — failure modes common in current MoE systems.

**Core claim (verbatim): "This is why MoE systems usually fail — they never certify geometry."**

## Background — MoE failure modes

Current mixture-of-experts systems fail for reasons that are architectural, not statistical:
- Silent expert failure (expert returns answers that look fine but the geometry has drifted)
- Degenerate collapse (one expert takes all load; others atrophy)
- Geometry drift after fine-tuning (LoRA / adapters warp the metric without re-certification)
- Fake specialization (experts cluster by input surface features, not by structural property)
- Constraint-breaking reasoning (an expert produces output violating invariants during descent)

All five are properties of the geometry, not the loss. None are caught by performance metrics.

## The audit protocol

### Definition (exact)

> An expert E_i is **Qualified** iff its induced geometry produces stable, bounded, convergent collapse over a certified region Ω_k ⊂ M of state space under constraint regime C_k.

Certification: `(E_i, Ω_k, C_k) → Qualified`. Experts may be qualified in multiple disjoint regions.

### Four invariant checks

**A. Descent validity** — collapse actually descends:
- ⟨∇F_i(h), Δh⟩ < 0 ∀ h ∈ Ω_k
- Failure → disqualified (local ascent or oscillation)

**B. Basin stability** — collapse terminates, doesn't drift:
- ||∇F_i(h_t)|| → 0 within T_max
- Bounded curvature, no limit cycles

**C. Metric conditioning** — metric invertible and well-conditioned:
- κ(g_i(h)) < κ_max
- Ill-conditioned = fake diversity, brittle collapse, numerical instability

**D. Constraint compatibility** — ring/hard constraints respected:
- ∀c ∈ C_k: c(h_t) ≤ ε
- Violations = hard fails, not penalties

### Probe construction

Shared probe set H_qual = {h_1, ..., h_Q}:
- Basin center samples
- Basin boundary perturbations
- Constraint-adjacent states
- Adversarial curvature spikes

### Deterministic rollout

```
h_{t+1} = h_t - α · g_i^{-1}(h_t) · ∇F_i(h_t)
```

Track: energy monotonicity, curvature bounds, constraint margins, termination time. No stochasticity. No sampling.

### Pass criteria (≥99% everywhere)

| Check | Condition |
|-------|-----------|
| Descent | ≥99% monotone decrease |
| Stability | ≥99% converge within T_max |
| Conditioning | κ(g) < κ_max everywhere |
| Constraints | 0 hard violations |
| Variance | Low outcome variance across probes |

Anything else → **Unqualified**.

## Engineering claim

The protocol certifies geometric validity, decoupled from empirical performance. An expert can be a top performer (high accuracy) yet Unqualified (geometry drifted). Conversely, a Qualified expert may be average on accuracy yet structurally safe.

This decoupling is novel. Most MoE evaluation conflates the two.

## Falsifiable predictions

- F1: A MoE system with ≥90% aggregate accuracy but Unqualified experts produces constraint-violating outputs ≥5% of the time on adversarial probes. Confirms "performance ≠ qualification."
- F2: A Qualified expert that fails accuracy retraining can be detected via re-certification within bounded audit cost (polynomial in |Ω_k|).
- F3: Stress probes (constraint-adjacent + adversarial curvature) catch ≥80% of geometry drift that performance metrics miss.

## Open questions

1. How to choose H_qual coverage — random sampling, adversarial generation, or learned probe distribution?
2. Cost of re-certification after each fine-tuning step — is it tractable for online learning?
3. Relation to Constitutional Embryogenesis (Paper 4) — does Qualification generalize across developmental stages?
4. Connection to Atlas Exam (Paper 3) — is QoFE a strict refinement of Atlas Exam's empirical correlation?

## Roadmap

- 1: Survey existing MoE failure literature; cite overlaps + deltas
- 2: Formalize 4 invariant checks as concrete code in `simself/src/constitutional/qofe.py`
- 3: Implement deterministic rollout + probe generation
- 4: Empirical study on simulated MoE with engineered drift
- 5: Measure F1, F2, F3
- 6: Write paper to 16-20 pages; arxiv preprint

---

*DRAFT created 2026-09-14 by Hermes auto-paper-build. Source at simself/docs/qofe-qualification-experts-2026-09-14.md, preserved at vault/30-originals/. Lead for Discord paper chat.*
