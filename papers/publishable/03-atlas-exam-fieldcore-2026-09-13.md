# Paper 3 — Atlas Exam (Bobby's correction: STRONGEST of 4)

**Title:** *Atlas Exam: Geometric Framework for AI Substrate Evaluation*

**Status:** Paper 1 in ranking. Strongest of the 4 papers per Bobby's 2026-09-13 correction. **Lives in BOTH repos** (simself-side empirical work + fieldcore-side framework theory).

**Authors:** Bobby (first) + Hermes (second).

**Target venue:** AI evaluation venue (NeurIPS eval track / HELM workshop / FAccT). ~16-20 pages.

**Effort:** ~6 weeks (3 weeks correlation study + 3 weeks writing).

---

## ⚠️ IMPORTANT — this paper lives in BOTH repos

- **simself/docs/research-papers/paper3-atlas-exam.md** — empirical correlation work, test infrastructure, Atlas exam protocol
- **fieldcore/docs/research-papers/paper3-atlas-exam.md** — this file: framework theory, mathematical substrate, geometric interpretation of 8-rung ladder

Both repos commit separately to the SAME paper. Bobby is author on both.

---

## What's IN this paper

- **Atlas exam framework:** 27 areas / 6 clusters / 8-rung Awakening Ladder.
- **8-rung ladder operational definitions** — what test proves rung 3 vs rung 4? (THIS IS THE LOAD-BEARING METHODOLOGICAL CONTRIBUTION.)
- **Empirical correlation study** (the strongest novel claim):
  - Apply Atlas exam to ≥5 substrate variants (v6.0, v6.1, v6.1+memory gate, v6.2, shuffled control).
  - Report Atlas pass/fail per substrate.
  - Show Atlas outputs correlate with engineering properties (stability, robustness, frequency distinctness).
- **Live deployment** — Atlas outputs are test results, not benchmarks.
- **Failure mode case study** — the routing 2/5 pre-existing flakiness as honest limitation.
## What this paper IS

- A substrate self-evaluation framework that produces **live, reproducible, geometric scores** correlating with engineering properties.
- The substrate validates itself through its own exam.
- Failure modes (routing 2/5) are PUBLISHABLE — honest limitations increase credibility.

## Empirical state — current

- `simself/src/constitutional/test_frequency_layer.py` — 7/7 tests pass.
- Atlas exam — 4/5 tests pass (routing 2/5 pre-existing).
- `simself_merged_v3_5.py` — embryogenic Ψ₀ = installed Ψ₀, cos sim = 1.000000.
- `fieldcore/src/convergence_demo.py` — verifies Bobby's steel-ball claim.

## Empirical state — REQUIRED before writing (the load-bearing work)

- **Atlas exam applied to ≥5 substrate variants:**
  1. v6.0 base (no FrequencyCoupler)
  2. v6.1 + FrequencyCoupler (current)
  3. v6.1 + ResonanceChannel memory gate (open work #1)
  4. v6.2 + position-dependent damping α(κ(x)) (open work #7)
  5. Shuffled random substrate (negative control)
- Report Atlas pass/fail per substrate. Show correlation with engineering properties.
- **This is the paper's strongest empirical claim:** live evaluation outputs correlate with substrate engineering properties across N configurations.

## Open questions

1. **Rung operational definitions** — what's the test for each of the 8 rungs? Need formal spec.
2. **27 areas / 6 clusters** — which areas? Which clusters? Need full taxonomy.
3. **Correlation metric** — Pearson? Spearman? Geometric? Bobby's call.
4. **Substrate variant #4** — does v6.2 exist yet, or is it a planned configuration we test as v6.1+modified?

---

*Stub. Source: `simself/docs/research-papers-2026-09-13.md` §Paper 3.*

*This paper lives in BOTH repos — simself for empirical work, fieldcore for framework theory. The two halves must be written and committed together.*