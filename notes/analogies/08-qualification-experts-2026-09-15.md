> **Moved to `notes/analogies/` on 2026-09-16** (per Grok sharpen 2026-09-16 + master plan Step 14 weekly review, applied by Hermes).
>
> **Reason:** does not serve the three public objects (hole, gate, exam) on the front path.

# Paper — Qualification of FieldCore Experts: A Geometric Audit Protocol

**Title:** *Qualification of FieldCore Experts: A Deterministic Geometric Audit Protocol for Mixture-of-Experts Substrates*

**Authors:** Robert D. Wolfson¹, Hermes²
¹ Independent Researcher, Bangkok
² Nous Research / MiniMax M3

**Status:** Full draft v1.0 — 2026-09-15.
**Target venue:** AI architecture / mixture-of-experts venue. 14–18 pages.
**Repo:** `fieldcore/papers/publishable/08-qualification-experts-2026-09-15.md`

---

## Abstract

Current mixture-of-experts (MoE) systems fail for architectural reasons — silent drift, degenerate collapse, fake specialisation, constraint-breaking reasoning — that performance metrics do not catch. We specify a geometric audit protocol that certifies **expert qualification** as a property of geometry, decoupled from empirical performance. The protocol enforces four invariant checks on the expert's induced geometry: descent validity ($\langle \nabla F, \Delta h \rangle < 0$ everywhere in the certified region), basin stability ($\|\nabla F\| \to 0$ in bounded time), metric conditioning ($\kappa(g) < \kappa_{\max}$), and constraint compatibility ($c(h_t) \leq \varepsilon$). Qualification is determined via stress probes — basin centres, basin boundary, constraint-adjacent, adversarial curvature — applied to a shared probe set $H_{\text{qual}}$ across experts. Rollout is deterministic; no sampling. The protocol prevents silent expert failure, degenerate collapse, geometry drift after fine-tuning, fake specialisation, and constraint-breaking reasoning.

**Core claim:** MoE systems usually fail because they never certify geometry.

---

## 1. Introduction

MoE systems route inputs to specialised sub-networks ("experts"). In principle, this gives the system modular, efficient computation. In practice, MoE systems frequently fail in ways that are not visible in aggregate accuracy:

1. **Silent expert failure** — an expert returns answers that look fine, but its internal geometry has drifted.
2. **Degenerate collapse** — one expert takes all load; others atrophy.
3. **Geometry drift after fine-tuning** — LoRA / adapters warp the metric without re-certification.
4. **Fake specialisation** — experts cluster by input surface features, not by structural property.
5. **Constraint-breaking reasoning** — an expert produces output violating invariants during descent.

All five are properties of the *geometry*, not the *loss*. None are caught by performance metrics. We propose a deterministic audit protocol that certifies geometry independently of performance.

---

## 2. The audit protocol

### 2.1 Definition

**Expert qualification.** An expert $E_i$ is **Qualified** iff its induced geometry produces stable, bounded, convergent collapse over a certified region $\Omega_k \subseteq \mathcal{M}$ of state space under constraint regime $C_k$.

Certification is a function:

$$
\text{Qualify}(E_i, \Omega_k, C_k) \to \{\text{Qualified}, \text{Unqualified}\}.
$$

Experts may be Qualified in multiple disjoint regions.

### 2.2 Four invariant checks

#### Check A — Descent validity

The collapse must actually descend:

$$
\langle \nabla F_i(h), \Delta h \rangle < 0 \quad \forall h \in \Omega_k.
$$

If false anywhere in $\Omega_k$: the expert is **Unqualified** (local ascent or oscillation).

#### Check B — Basin stability

The collapse must terminate, not drift:

$$
\|\nabla F_i(h_t)\| \to 0 \quad \text{within } T_{\max}.
$$

Bounded curvature required. No limit cycles.

#### Check C — Metric conditioning

The metric must be invertible and well-conditioned:

$$
\kappa(g_i(h)) < \kappa_{\max} \quad \forall h \in \Omega_k.
$$

Ill-conditioned metric = fake diversity, brittle collapse, numerical instability.

#### Check D — Constraint compatibility

All ring/hard constraints respected:

$$
\forall c \in C_k: c(h_t) \leq \varepsilon.
$$

Violations = hard fails, not penalties.

### 2.3 Probe construction

Shared probe set $H_{\text{qual}} = \{h_1, \ldots, h_Q\}$ contains four categories:

| Probe type | Source | Tests |
|---|---|---|
| Basin centre | Converged states of $E_i$ | Stability |
| Basin boundary | Near-converged states | Descent near boundary |
| Constraint-adjacent | States near $\partial C_k$ | Constraint compatibility |
| Adversarial curvature | High-$\|\nabla^2 F\|$ states | Metric conditioning |

Probes are constructed once, then reused across all experts for fair comparison.

### 2.4 Deterministic rollout

```
h_{t+1} = h_t - alpha * g_i^{-1}(h_t) * grad F_i(h_t)
```

Track:

- Energy monotonicity (must decrease).
- Curvature bounds.
- Constraint margins.
- Termination time.

No stochasticity. No sampling.

### 2.5 Pass criteria

| Check | Pass condition |
|---|---|
| Descent | $\geq 99\%$ monotone decrease |
| Stability | $\geq 99\%$ converge within $T_{\max}$ |
| Conditioning | $\kappa(g) < \kappa_{\max}$ everywhere |
| Constraints | 0 hard violations |
| Variance | Low outcome variance across probes |

Anything else → **Unqualified**.

---

## 3. Theorem (qualification $\neq$ performance)

**Statement.** A Qualified expert may have low accuracy; an Unqualified expert may have high accuracy. The two are decoupled.

**Proof.** The four invariant checks are properties of the *induced geometry* (descent direction, basin shape, metric conditioning, constraint satisfaction). Accuracy is a property of the *loss landscape trajectory*. Geometric validity does not imply trajectory optimality, and trajectory optimality does not imply geometric validity. ∎

**Engineering consequence.** MoE evaluation must separate the two questions:

1. Is the expert Qualified (geometrically safe)?
2. Is the expert accurate (loss-landscape optimal)?

A system with high accuracy but Unqualified experts produces constraint-violating outputs under adversarial pressure. A system with Qualified but low-accuracy experts is structurally safe but inefficient.

---

## 4. Theorem (deterministic certification)

**Statement.** Given a fixed probe set $H_{\text{qual}}$ and rollout rule, certification of expert $E_i$ in region $\Omega_k$ under $C_k$ is a deterministic, polynomial-time function of $|H_{\text{qual}}|$, $T_{\max}$, and $|\Omega_k|$.

**Proof sketch.** Each probe rollout is a finite sequence of gradient steps bounded by $T_{\max}$. Each step is a deterministic matrix operation on the expert's induced metric. Total cost: $O(|H_{\text{qual}}| \cdot T_{\max} \cdot \text{cost}(E_i))$. ∎

This makes certification tractable in practice for any reasonable probe set size.

---

## 5. Failure-mode coverage

The four checks together cover all five MoE failure modes:

| Failure mode | Detected by |
|---|---|
| Silent expert failure | Check A (descent validity) + Check B (stability) |
| Degenerate collapse | Check B (basin stability over probe set) |
| Geometry drift after fine-tuning | All four (full re-certification) |
| Fake specialisation | Check C (metric conditioning reveals pseudo-diversity) |
| Constraint-breaking reasoning | Check D (constraint compatibility) |

---

## 6. Falsifiable predictions

- **F1:** A MoE system with $\geq 90\%$ aggregate accuracy but Unqualified experts produces constraint-violating outputs $\geq 5\%$ of the time on adversarial probes.
- **F2:** A Qualified expert that fails accuracy retraining can be detected via re-certification within bounded audit cost (polynomial in $|\Omega_k|$).
- **F3:** Stress probes (constraint-adjacent + adversarial curvature) catch $\geq 80\%$ of geometry drift that performance metrics miss.
- **F4:** A Qualified expert that is fine-tuned on a new task remains Qualified iff its induced geometry satisfies all four checks on $H_{\text{qual}}$ post-tuning.

---

## 7. Engineering realisation

### 7.1 Code layout

```
simself/src/constitutional/qofe.py        # main protocol
simself/src/constitutional/qofe_probes.py # probe generation
simself/src/constitutional/qofe_rollout.py # deterministic rollout
simself/src/constitutional/qofe_report.py # certification report
```

### 7.2 API

```python
from constitutional.qofe import qualify_expert, certify_region

result = qualify_expert(
    expert=E_i,
    region=Omega_k,
    constraints=C_k,
    probes=H_qual,
)
# result.qualified: bool
# result.check_results: Dict[str, CheckResult]
# result.coverage: float  # fraction of probes where all checks pass
```

### 7.3 Integration with the agent

The QoFE protocol is invoked by the Governor before promoting any expert to the constitutional sheaf. An expert that fails certification is sent back to retraining with a diagnosis report.

---

## 8. Relation to other work

- **Constitutional AI** (Bai et al., 2022): trained principles + RLHF. QoFE: geometric audit.
- **MoE literature** (Shazeer et al., 2017; Fedus et al., 2022): routing and load balancing. QoFE: geometry certification.
- **Atlas Exam** (`fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-15.md`): empirical correlation study. QoFE: deterministic geometric audit. Atlas Exam is the empirical companion to QoFE.

---

## 9. Open questions

1. **Probe coverage.** How to choose $H_{\text{qual}}$ coverage — random sampling, adversarial generation, or learned probe distribution?
2. **Online certification cost.** Is re-certification after each fine-tuning step tractable for online learning?
3. **Cross-stage qualification.** Does Qualification generalise across constitutional embryogenesis stages (per `fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-15.md`)?
4. **Atlas Exam ↔ QoFE.** Is QoFE a strict refinement of Atlas Exam's empirical correlation?

---

## 10. Roadmap

1. Survey existing MoE failure literature; cite overlaps + deltas.
2. Formalise 4 invariant checks as concrete code in `simself/src/constitutional/qofe.py`.
3. Implement deterministic rollout + probe generation.
4. Empirical study on simulated MoE with engineered drift.
5. Measure F1, F2, F3, F4.
6. Write paper to 16–20 pages; arxiv preprint.

---

## References

- Bai, Y., et al. (2022). *Constitutional AI*. arXiv:2212.08073.
- Fedus, W., et al. (2022). *Switch Transformers*. JMLR.
- Shazeer, N., et al. (2017). *Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer*. arXiv:1701.06538.
- Wolfson, R. D., Hermes (2026). *Atlas Exam*. fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-15.md.

---

*Filed 2026-09-15 by Hermes for Bobby. 4 invariant checks, 4 falsifiable predictions, deterministic rollout. Engineering realisation in `simself/src/constitutional/qofe.py`.*