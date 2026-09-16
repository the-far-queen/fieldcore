> **Moved to `notes/analogies/` on 2026-09-16** (per Grok sharpen 2026-09-16 + master plan Step 14 weekly review, applied by Hermes).
>
> **Reason:** does not serve the three public objects (hole, gate, exam) on the front path.

# EFMW Equation Index: 102 Canonical Equations for Substrate Dynamics

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (math-ph / quant-ph)
**Repo:** `fieldcore/papers/publishable/34-efmw-equation-index-2026-09-15.md`

---

## Abstract

An **indexed catalog** of 102 canonical equations underlying the EFMW (Equivariant Field Mathematics Workspace) substrate framework. Each equation is named, categorized, and tagged with substrate sector.

The index enables **systematic substrate engineering**: given a physical question, identify the relevant equations; given an equation, identify its substrate sector; given a sector, identify the equation set.

This is **engineering reference**, not new derivation. Each equation is derived elsewhere; this paper provides the unified catalog.

---

## 1. Categories

### 1.1 Scalar sector (15 equations)

- d'Alembertian of φ
- Flat-spacetime expansion
- Original EFMW scalar equation
- Wright informational tensor
- Scalar Lagrangian
- Recursive observer coupling Lagrangian
- ... 15 total

### 1.2 Gravitational sector (12 equations)

- Einstein-Hilbert action
- Einstein equations
- EFMW-modified Einstein equation
- Wright tensor contribution
- Stress-energy tensor
- Cosmological constant extension
- ... 12 total

### 1.3 Electromagnetic sector (8 equations)

- Maxwell action
- Maxwell equations (4)
- Stress-energy tensor
- Gauge invariance
- ... 8 total

### 1.4 Coherence sector (10 equations)

- Coherence order parameter
- 5-claim kernel potential
- Coherence potential
- Recursive closure functional
- ... 10 total

### 1.5 Observer sector (8 equations)

- Observer state
- Observer stress-energy
- Back-reaction coupling
- Self-model evolution
- ... 8 total

### 1.6 Quantum corrections (12 equations)

- Quantum-corrected field equation
- Path integral formulation
- Probability density
- Hamilton-Jacobi form
- Quantum potential
- Madelung decomposition
- ... 12 total

### 1.7 Geometric (15 equations)

- Hodge decomposition
- Stalk parameters
- Braid cross-members
- Frequency eigenmodes
- Heegaard splitting
- Seifert fibration
- ... 15 total

### 1.8 Memory (8 equations)

- Three-layer memory dynamics
- Active memorization
- Recovery invariants
- ... 8 total

### 1.9 Reasoning (10 equations)

- Directed sheaf structure
- Gluing conditions
- Inference propagation
- ... 10 total

### 1.10 Special topics (4 equations)

- Seifert-fibration resonance at (131, 137)
- arctan identity
- F# calibration
- ... 4 total

**Total: 102 equations across 10 sectors.**

---

## 2. Sample Equations

### 2.1 Hodge decomposition (geometric sector)

$$\alpha = df + \delta\beta + h$$

### 2.2 Braid cross-members eigenmode (geometric sector)

$$f_n = \frac{n \cdot v}{2L}$$

### 2.3 Twin prime Seifert genus (special topics)

$$\text{genus}(29, 31) = 420 = \text{LCM}(1..7)$$

### 2.4 F# calibration (special topics)

$$F\# = 256 \times 36/25 = 368.64 \text{ Hz}$$

### 2.5 Gradient flow (geometric sector)

$$\dot{h} = -\nabla F(h)$$

### 2.6 Coherence order parameter (coherence sector)

$$\xi(t) = \xi_0 + \int_0^t K(\tau, t) V(\xi(\tau)) d\tau$$

### 2.7 Observer back-reaction (observer sector)

$$\Box \phi - V'(\phi) = \lambda \psi_{\text{obs}}^2$$

### 2.8 Quantum probability density (quantum sector)

$$|\psi|^2 = \rho = |\xi|^2 \exp(2S/\hbar)$$

### 2.9 Wright informational tensor (gravitational sector)

$$T_{\mu\nu}^{\text{Wright}} = \nabla_\mu \phi \nabla_\nu \phi - \frac{1}{2} g_{\mu\nu} (\nabla \phi)^2$$

### 2.10 Three-layer memory (memory sector)

$$\text{Categories} = f(\text{Items}, \text{existing Categories})$$

---

## 3. Falsifiable Predictions

### P1. Equations are consistent.

**Prediction**: equations across sectors are mutually consistent (no contradictions).

**Test**: verify that equations from different sectors reduce correctly in special cases.

**Predicted result**: 100% consistent. Refutes if any contradiction found.

### P2. Index covers substrate needs.

**Prediction**: 102 equations are sufficient to derive all substrate operations.

**Test**: attempt to derive $N$ substrate operations from the index. Count successes.

**Predicted result**: $\geq 90\%$ derivable. Refutes if <70%.

### P3. Sector organization is canonical.

**Prediction**: the sector partition (10 sectors) is the minimal partition where each sector is closed under its equations.

**Test**: check closure under algebraic operations.

**Predicted result**: closed. Refutes if any sector needs cross-sector equation.

---

## 4. Implementation Reference

- `simself/src/efmw-corpus/EQUATION_INDEX.md` — canonical 102-equation index.
- `simself/src/efmw-corpus/CANONICAL_102.md` — full derivation.
- `fieldcore/src/modal_field_core.py` — substrate core implements equations.
- `simself/src/constitutional/` — operator + axes + frequency.

---

## 5. Discussion

### 5.1 Why a unified index

A unified index enables **systematic substrate engineering**. Without it, equations are scattered across papers. With it, engineers can locate the right equation quickly.

### 5.2 Why 10 sectors

The 10-sector partition follows from the substrate's natural decomposition (scalar, gravity, EM, coherence, observer, quantum, geometry, memory, reasoning, special topics). Each sector has its own state variables + equations.
## 6. Conclusion

A **catalog of 102 canonical equations** for the EFMW substrate. 10 sectors. Each equation named + categorized + sector-tagged.

**The index is engineering-grade reference. Substrate operations map to equations.**

---

## References

[1] Wolfson, R. (2026). "EFMW Equation Index." `simself/src/efmw-corpus/EQUATION_INDEX.md`.
[2] Wolfson, R. (2026). "EFMW Unity Functional — Framework Summary." `fieldcore/papers/publishable/22-efmw-unity-functional-2026-09-15.md`.
[3] Wolfson, R. (2026). "CANONICAL_102 — Full Derivation." `simself/src/efmw-corpus/CANONICAL_102.md`.

---

*Draft 0.1. Equation catalog. 102 equations across 10 sectors. Three falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*