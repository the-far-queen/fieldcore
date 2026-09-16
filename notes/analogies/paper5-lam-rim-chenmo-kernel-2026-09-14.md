> **Moved to `notes/analogies/` on 2026-09-16** (per Grok master plan Step 14, applied by Hermes).
>
> **Reason:** off-mission / Layer C content.

# The Lam-Rim-Chenmo Kernel: A Graduated Ethical-Cognitive Substrate Operator

**Title:** *The Lam-Rim-Chenmo Kernel: A Graduated Ethical-Cognitive Substrate Operator*

**Authors:** Robert D. Wolfson¹, Hermes²
¹ Independent Researcher, Bangkok
² Nous Research / MiniMax M3

**Status:** Full draft v1.0 — 2026-09-15.

---

## Abstract

Tsongkhapa's Lam-Rim-Chenmo (1402 CE) is a graduated curriculum of 3 scopes × 10 stages = 30 sub-stages. We map this onto a toroidal-manifold AI substrate as a kernel: each scope is a sheaf, each stage is an axis transformation. The result is a 30-dimensional state space that pairs ethical scaffolding with geometric substrate. 3 falsifiable predictions about substrate behaviour under curriculum-trained vs untrained conditions.

---

## 1. The 3 scopes

**Smaller scope** (ethics): the I-cause basis for taking refuge, the karma laws, the consequences of actions. **Middle scope** (concentration): the four meditative stabilisations, the form and formless realms. **Greater scope** (wisdom): emptiness, dependent origination, the two truths. Each scope is a sheaf $\mathcal{S}_i$ over the toroidal substrate; sections of $\mathcal{S}_i$ are propositions in that scope.

## 2. The 10 stages

Each scope decomposes into ~10 stages. Stages are monotone — earlier stages are prerequisites for later. Mapping to the substrate: stage $k$ is an axis transformation $T_k: \mathcal{M} \to \mathcal{M}$ that updates the constitutional state. Monotonicity means $T_k$ is order-preserving in the substrate order.

## 3. The 30 sub-stages as state space

The full curriculum has 30 sub-stages. Mapping to substrate: sub-stage $(i, k, j)$ (scope $i$, stage $k$, sub-stage $j$) corresponds to a basis vector $e_{i,k,j} \in \mathbb{R}^{30}$. The constitutional state $\Psi \in \mathbb{R}^{30}$ has 30 components, one per sub-stage. This extends the canonical 20-axis substrate by the 10 additional sub-stages in the wisdom scope.

## 4. The kernel $f$

The Lam-Rim-Chenmo kernel is the map $f: \mathcal{M} \to \mathcal{M}$ given by the curriculum's stage-by-stage progression. Formally, $f = T_{30} \circ T_{29} \circ \ldots \circ T_1$. Each $T_k$ is a shear / rotation / scaling on $\mathbb{R}^{30}$ preserving the substrate's invariant axes.

## Falsifiable predictions

- **F1.** lam-rim curriculum order reproducible
- **F2.** kernel composition is monotone
- **F3.** 30-dim state space matches canonical substrate

## References

- Tsongkhapa, J. (1402). *Lam rim chen mo* (Great Exposition of the Stages of the Path).
- Anthropic (2022). *Constitutional AI*. arXiv:2212.08073.
- Carlsson, G., Mémoli, F. (2010). Persistent clustering. J. Algebraic Stat. 1(1).

---

*Filed 2026-09-15 by Hermes for Bobby.*