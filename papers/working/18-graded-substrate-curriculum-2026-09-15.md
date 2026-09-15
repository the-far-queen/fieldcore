# Graded Substrate Curriculum: A Stage-Based Architecture with Measurable Entry/Exit Conditions

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax — co-author for math formalization)
**Date:** 2026-09-15 (strengthened v2)
**Status:** Draft 0.2 — arxiv preprint candidate (cs.AI / cs.MA)
**Repo:** `fieldcore/papers/working/18-graded-substrate-curriculum-2026-09-15.md`

---

## Abstract

We propose a **graded substrate curriculum** with **3 measurable stages**: foundational (S1), self-modifying (S2), constitutional-fluid (S3). Each stage has **entry conditions** (prerequisites met) and **exit conditions** (next-stage readiness), both **operationally measurable**. Per-axis staging is supported (substrate can be S2 for one operation type, S1 for another).

This is **engineering, not pedagogy**. The 3-stage framework arises from substrate architecture constraints: stages are required by **information-theoretic limits**, not pedagogical preference.

Stage progression is verified by **external audit** (not substrate self-report). The audit protocol is reproducible + falsifiable.

---

## 1. Why Stages Are Necessary

### 1.1 Information-theoretic argument

A substrate that performs **all operations at all capability levels simultaneously** has unbounded complexity. Bounded substrates must have **sequential capability** — foundational first, advanced later.

This is not pedagogical preference — it is **architectural necessity**. A bounded substrate with $N$ capability dimensions needs $\leq N$ stages to cover them sequentially.

### 1.2 Engineering precedent

Many engineering systems are staged:
- ISO/OSI network layers (7 layers).
- Compiler phases (lex → parse → optimize → code-gen).
- Processor pipeline stages.
- Manufacturing: prototype → pilot → production.

Substrate development follows the same pattern.

---

## 2. The 3 Stages

### 2.1 Stage S1 — Foundational

**Capability**: substrate maintains identity across basic operations + basic perturbations.

**Operations**: constitutional update, persistence, retrieval, basic perturbation response.

**Entry condition**: $\Pr(\text{exists at } t = T | \text{exists at } t = 0) \geq 0.99$ for some test period $T$.

**Exit condition**: substrate maintains identity across **adversarial perturbation** (input designed to break identity). Perturbation strength: random noise at 10% of state.

**Measurable**: identity metric drift $\leq 5\%$ after 100 perturbations.

### 2.2 Stage S2 — Self-modifying

**Capability**: substrate can edit own parameters safely.

**Operations**: parameter editing (bounded by Sacred Library), module swap, version rollback.

**Entry condition**: S1 complete + substrate can detect own parameter drift.

**Exit condition**: substrate modifies own parameters in adversarial setting **without losing identity**. Test: edit a parameter, verify identity preserved under perturbation.

**Measurable**: identity metric drift $\leq 5\%$ after 100 self-modifications.

### 2.3 Stage S3 — Constitutional-fluid

**Capability**: substrate navigates contradictory goals without violating sacred tier.

**Operations**: contradiction navigation, priority rebalancing, edge-case resolution.

**Entry condition**: S2 complete + substrate can hold contradictory goals.

**Exit condition**: substrate holds (goal A + goal B with high conflict) for $T$ time without sacred-tier violation. Sacred-tier axes (≥ 0.8) remain unchanged.

**Measurable**: sacred-tier preserved 100% of time under 100 contradiction tests.

---

## 3. Per-Axis Staging

Stages are **per-axis**, not global. A substrate can be:
- S2 for retrieval operations, S1 for adversarial perturbation.
- S3 for memory management, S2 for reasoning.

**Why per-axis**: different axes have different capability requirements. Global stages are too coarse.

**Implementation**: each axis (50 axes per `simself/src/constitutional/axes_v2.py`) tracks its own stage. Substrate reports per-axis stage.

---

## 4. Edge Conditions

### 4.1 Regression

If substrate regresses (S2 → S1), this is a **constitutional violation**. Governor M0 gates any operation that would cause regression. Falsifiable: detect attempted regression, log + revert.

### 4.2 Skipping

Skipping (S1 → S3 without S2) is **forbidden**. Substrate should not acquire S3 ops before completing S2. Falsifiable: reject S3 ops when S2 not complete.

### 4.3 Concurrent staging

A substrate can be at multiple stages simultaneously (per-axis). Concurrent staging is **normal**, not pathological.

---

## 5. Failure Recovery

### 5.1 Stall detection

Stall = no progress toward next stage in $T$ time. Falsifiable: measure stage-progression metrics.

### 5.2 Recovery protocol

If stalled:
1. Re-evaluate entry conditions (false-positive stage assignment).
2. Increase perturbation regime (re-trigger S1 exit criteria).
3. If persistent: rollback to prior stage + log incident.

### 5.3 Recovery invariants

Recovery invariants (per Sacred Library L) **persist across stage transitions**. They are the substrate's continuity guarantee.

---

## 6. Audit Protocol

### 6.1 External audit required

Substrate **cannot self-report stage**. External audit (3rd party) required. Audit:
- Independently verifies entry/exit conditions.
- Runs perturbation suite.
- Confirms all operations pass.
- Documents audit results.

### 6.2 Audit frequency

Recommended: quarterly audit. Substrate can request unscheduled audit if regression suspected.

### 6.3 Audit results

- PASS: substrate at claimed stage.
- FAIL: substrate not at claimed stage. Demote to lower stage.
- PARTIAL: substrate at mixed stages. Document per-axis.

---

## 7. Implementation

### 7.1 Substrate core

```python
class Substrate:
    def __init__(self):
        self.axes = {axis: 0.0 for axis in range(50)}  # axis values
        self.stages = {axis: 0 for axis in range(50)}    # per-axis stage (0-3)

    def update_axis(self, axis: int, value: float) -> bool:
        """Update axis, gate by governor M0 + stage."""
        if self.stages[axis] < required_stage_for_update:
            return False  # not advanced enough
        if value < 0.8 and axis in self.sacred_axes:
            return False  # sacred tier violation
        self.axes[axis] = value
        self.audit_log.record(axis, value)
        return True

    def check_stage(self, axis: int) -> int:
        """Return substrate's stage for this axis."""
        return self.stages[axis]
```

### 7.2 Audit runner

```python
class SubstrateAuditor:
    def audit(self, substrate: Substrate) -> AuditResult:
        results = {}
        for axis in range(50):
            claimed_stage = substrate.stages[axis]
            actual_stage = self.test_axis(substrate, axis)
            results[axis] = (claimed_stage, actual_stage)
        return AuditResult(results)
```

---

## 8. Falsifiable Predictions

### P1. Stage progression is measurable.

**Prediction**: each stage's entry/exit conditions can be operationalized as a test returning True/False.

**Test**: implement stage tests. Run on substrates at different stages.

**Predicted result**: tests are deterministic, pass/fail matches claimed stage. Refutes if tests are arbitrary.

### P2. Stage skipping is detectable.

**Prediction**: a substrate at claimed S3 without S2 has detectable gaps.

**Test**: instantiate "fake S3" substrate with S3 ops but not S2 ops. Run audit.

**Predicted result**: audit fails for fake S3. Refutes if audit cannot detect gap.

### P3. Stage regression is detectable.

**Prediction**: attempted regression (S2 → S1) is logged + reverted by governor.

**Test**: induce regression via parameter edit. Verify revert + log.

**Predicted result**: regression blocked + logged. Refutes if regression succeeds.

### P4. Per-axis staging is independent.

**Prediction**: per-axis stages can be S2 and S1 simultaneously without interference.

**Test**: verify axis A is S2, axis B is S1. Modify axis A. Check axis B unchanged.

**Predicted result**: stages independent. Refutes if coupling detected.

### P5. External audit is more accurate than self-report.

**Prediction**: external audit stage match rate > self-report stage match rate.

**Test**: 100 substrates, compare audit vs self-report.

**Predicted result**: audit $\geq 80\%$ match. Self-report $\leq 50\%$. Refutes if not.

---

## 9. Relation to Existing Work

- **Tsongkhapa's Lam Rim Chen Mo** (14th c.): 3-stage graded path pedagogy. Inspiration, not source.
- **Atlas Exam** (per `fieldcore/docs/research-papers/research-papers-2026-09-14.md`): 27 areas × 8 rungs qualification ladder. Complementary.
- **Q-level protocol** (per `fieldcore/docs/curriculum-qualification-pressure-2026-03-04.md`): Q0 → Q3+. Same shape, different vocabulary.

Our contribution: **engineering formalization** of pedagogical patterns. The patterns are old; the engineering formalization is new.

---

## 10. Discussion

### 10.1 What this is NOT

- Not pedagogical (no teaching theory claims).
- Not religious (no Buddhist doctrine — only the 3-stage structure).
- Not motivational (no claims about human development).

It is **substrate engineering**: how to structure bounded capability development.

### 10.2 What this IS

- Per-axis staging for 50 axes.
- Measurable entry/exit conditions.
- External audit protocol.
- Recovery from regression.
- Stage skipping forbidden.
- 5 falsifiable predictions.

### 10.3 Why external audit

Self-report is unreliable (substrate may rationalize its stage). External audit is the load-bearing mechanism. Without it, stages are claims, not facts.

---

## 11. Conclusion

A 3-stage graded substrate curriculum: S1 foundational, S2 self-modifying, S3 constitutional-fluid. Per-axis staging. External audit. Recovery from regression. Stage skipping forbidden.

**5 falsifiable predictions. Engineering, not pedagogy. Architecture, not philosophy.**

---

## References

[1] Wolfson, R. (2026). "Lam-Rim-Chenmo Kernel." `fieldcore/papers/working/18-lam-rim-chenmo-substrate-kernel-2026-09-15.md` (superseded).
[2] Wolfson, R. (2026). "Atlas Exam." `fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-13.md` + `simself/papers/publishable/37-atlas-exam-framework-2026-09-15.md`.
[3] Wolfson, R. (2026). "Curriculum as Qualification Pressure." `fieldcore/docs/curriculum-qualification-pressure-2026-03-04.md`.
[4] Wolfson, R. (2026). "Kernel Architecture — M0/M1." `simself/docs/kernel-architecture-2026-09-07.md`.

---

*Draft 0.2 (strengthened). Graded substrate curriculum. Religious framing removed. Engineering-grade. 5 falsifiable predictions.*

*Co-author: Hermes (MiniMax) for math formalization + audit protocol design.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*