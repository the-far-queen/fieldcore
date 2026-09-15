# Proposal 13 — Adaptive Resolution Damping for Constitutional Substrates

**Original Number:** 13
**Author:** Bobby Wolfson
**Repo:** `fieldcore/papers/proposals/`
**Folder:** `proposals/` (substrate-physics focus)
**Expanded:** 2026-09-15 by Hermes from concept to full proposal.

---

**Claim**: replacing the fixed-damping resolution operator with an adaptive $\eta$ that scales with $\|\delta\| = \|\psi_{\text{current}} - \psi_0\|$ reduces long-running drift from ~1.07/5-perturbations (v6.0 empirical) to $\le 0.1 / 10^4$-perturbations.

**Experiment**:
- Implement adaptive-$\eta$ version of `ResolutionOperator.__call__()` and `SimSelf.resolve_and_update()`.
- Run $10^4$ random continuous perturbations on the substrate.
- Measure final drift, mean drift, max drift.
- Compare to v6.0 baseline (drift ~1.07 after 5 perturbations).
- Run the full Atlas Exam (5 tests) on the adaptive version.

**Funding required**:
- Research engineer (1 year): $150,000
- Compute infrastructure: $10,000
- **Total: $160,000**

**Academic fields**: control systems, differential geometry, AI alignment.

---

## Mathematical framework

**Setup.** Substrate state space $\mathcal{M} = \mathbb{R}^{14}$ (DIM in v6.0/v6.2 code). Constitutional ground $\psi_0 \in \mathcal{M}$, immutable. Working state $\psi_{\text{current}} \in \mathcal{M}$, mutable. Drift:

$$
\delta(t) = \psi_{\text{current}}(t) - \psi_0.
$$

**v6.0 / v6.2 dynamics:**

$$
\psi_{\text{current}}(t+1) = \psi_{\text{current}}(t) - \eta \cdot \delta(t) + \eta \cdot R(\delta(t)),
$$

where $R$ is the bounded resolution operator and $\eta$ is fixed (0.03 if stable, 0.08 otherwise).

**Adaptive-$\eta$ proposal:**

$$
\eta(t) = \eta_{\min} + (\eta_{\max} - \eta_{\min}) \cdot \sigma(\alpha \|\delta(t)\|),
$$

where $\sigma$ is the sigmoid, $\alpha$ is a tunable gain, $\eta_{\min} = 0.01$, $\eta_{\max} = 0.20$.

**Target quantity.** Drift under $T = 10^4$ perturbations:

$$
\Delta_{\infty} = \lim_{T \to \infty} \frac{1}{T} \sum_{t=1}^{T} \|\delta(t)\|.
$$

The falsification criterion is $\Delta_{\infty} \le 0.1$ over $T = 10^4$ random perturbations, vs. the v6.0 baseline of $\Delta_5 \approx 1.07$.

## Methods

1. Implement adaptive-$\eta$ version of `ResolutionOperator.__call__()` and `SimSelf.resolve_and_update()`.
2. Run $10^4$ random continuous perturbations on the substrate.
3. Measure final drift, mean drift, max drift.
4. Compare to v6.0 baseline (drift ~1.07 after 5 perturbations).
5. Run the full Atlas Exam (5 tests) on the adaptive version.

## Funding breakdown

- Research engineer (1 year): $150,000
- Compute infrastructure: $10,000
- **Total: $160,000**

## Personnel

Principal investigator: Robert D. Wolfson (Bobby).
Research engineer: TBD.
Collaborating institutions: TBD.

## Milestones (1-year timeline)

| Quarter | Milestone |
|---|---|
| **Q1** | Implement adaptive-$\eta$ dynamics; verify on small N. |
| **Q2** | Run $10^4$-perturbation benchmark; compare to v6.0 baseline. |
| **Q3** | Run full Atlas Exam on adaptive version; tune $\alpha$. |
| **Q4** | arxiv preprint; open-source release. |

## Falsifiable predictions

The proposal is testable. The predictions are:

- **F1.** Drift over $10^4$ random perturbations $\le 0.1$ (vs v6.0's ~1.07 over 5).
- **F2.** Atlas Exam 5/5 pass on adaptive-$\eta$ version.
- **F3.** Replication: independent lab reproduces drift $< 0.1$ on the released code.

If F1, F2, or F3 fail, the proposal is refuted.

## Relation to other proposals in this set

| # | Title | Connection |
|---|---|---|
| 02 | Mercury Room-Temperature Quantum Coherence | Adjacent substrate engineering |
| 04 | Schauberger Vortex Engineering | Adjacent substrate engineering |
| 09 | Heegaard Seam Energy Barriers | Adjacent substrate engineering |
| 11 | Surface Plasmons on Polished Granite | Adjacent substrate engineering |
| 12 | Constitutional Substrate for AGI Evaluation | Directly related (Atlas Exam evaluation framework) |
| 04 (simself) | Operator Algebra Algebraic Closure | Related: adaptive eta is an algebraic operator on the substrate |
| 09 (simself) | MTE Machine Translation Engine | Related: MTE will need stable substrate |

## Open Questions

1. What is the theoretical upper bound on $\Delta_\infty$ under adaptive-$\eta$, given the substrate's geometry?
2. Does the result generalise across substrate variants (v6.0 / v6.2 / future)?
3. What is the smallest experiment that can falsify the claim?
4. Does adaptive-$\eta$ interact with the constitutional filter (word-boundary regex) to produce emergent gating behaviour?

## Outputs

- 1 arxiv preprint.
- Open-source code (MIT `).
- 1 conference talk at NeurIPS / ICML.

## Ethical and safety considerations

Standard controls per relevant domain (control systems / AI alignment). No novel hazards beyond standard software safety.

## Why this is engineering, not speculation

The proposal:

1. Names a specific, measurable claim.
2. Specifies the experimental apparatus (10⁴-perturbation benchmark).
3. States the falsification criterion.
4. Provides a funding plan.
5. Provides a personnel plan.
6. Provides a 1-year milestone schedule.

A speculation does not have these. This proposal does.

---

*Filed 2026-09-15 by Hermes for Bobby. Original concept expanded from the Grok v6.0 review observation (drift too high) into a full research-grant proposal.*