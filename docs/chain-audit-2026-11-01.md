# The chain audit: the citations, and what each one actually claims

**Filed 2026-11-01 by Hermes.** The literature survey that `src/chain_audit.py`
points at. This file is the *evidence* for the five signals the instrument
computes. It says, for each signal: what the published method is, what it
measures, whether the number is a **reported measurement** or a **proposal of
ours**, and where the literature is **contested**.

**THE ONE THING THIS FILE IS FOR.** The instrument must not pretend the line
between genuine computation and narration is known. It is not. So the survey
records, for every signal, *how much of the number is borrowed and how much is
ours*. A signal with a reported number has a calibration anchor somewhere in
the literature. A signal without one is a proposal and must be labelled as
such in the output.

**HOW TO READ THE FOUR MARKS.**

| mark | meaning |
|---|---|
| `[M]` | **Measured.** A number this signal can be checked against, reported by the cited work. |
| `[P]` | **Proposal.** Ours. No published number. Must be labelled in the tool's output. |
| `[C]` | **Contested.** The literature disagrees, or the cited work's own result contradicts a common reading. |
| `[O]` | **Offline.** Computable from a recorded chain with no extra model call. |

`[O]` is orthogonal to the others. A signal can be `[M]` and not `[O]`
(backward influence needs a rerun), or `[O]` and `[P]` (handover retention
ratios have no published calibration).

---

## THE NUMBERED LIST: EVERY MEASURABLE SIGNAL THE SURVEY FOUND

This is the deliverable. Each entry: **(a)** exact definition, **(b)** offline
computation, **(c)** citation, **(d)** reported numbers. Marks: `[M]`
measured, `[P]` proposal, `[C]` contested, `[O]` offline.

Ordered by how much published evidence backs them, strongest first.

---

### 1. ADJACENT-STEP INHERITANCE
*Does step k+1 actually use step k?*

**(a)** Mean Jaccard overlap of **content words** between step k and step
k+1, reported as **lift over a control**: the same overlap computed against
a non-adjacent partner step. Lift > 1 = the chain is sequential; lift ≈ 1 =
the steps are topically related but not sequentially dependent.

**(b)** **Offline `[O]`.** Two things make it a measurement rather than a
count: (i) a **control** — without one, a topical narrative and a working
chain both score high; (ii) **content words only**, excluding a closed
function-word list, so the measure does not track length.
**Critical implementation note, measured below:** the numerator must be the
overlap between step k's text and **step k+1's own text**. Using a
*recorded* `input` field as the numerator is degenerate when the recording
harness stores the previous step verbatim — the measure then reports the
harness's plumbing, not the chain.

**(c)** Thought Anchors — https://arxiv.org/abs/2506.19143 — the published
counterfactual form (`importance(S_i→S_fut) = P(S_fut | S_i present) −
P(S_fut | S_i replaced)`, semantic match at cosine > 0.8); FACT-E —
https://aclanthology.org/2026.findings-acl.1014.pdf — the instrumental-
variable causal form; FaithCoT-Bench —
https://arxiv.org/abs/2510.04040 — the "step skipping" failure mode.

**(d)** **[M]** Step skipping is the most frequent fine-grained
unfaithfulness signal at **24.36%** of unfaithful instances; spurious
reasoning chains are **57.71%** of all unfaithful instances. Thought Anchors
counterfactual importance: baseline MATH accuracy 64.1% [56.0%, 72.1%];
ablation of 512 of 1,920 receiver heads → 28% vs 37% for control heads
(t[31]=2.55, p=.02). **[P]** The lift-over-control construction and its
thresholds are ours; no published calibration exists.

**[C]** The *direction of importance* is contested: under forced-answer
importance, active-computation sentences score highest; under counterfactual
importance, plan-generation and uncertainty-management sentences score
highest and active computation scores lowest. Same corpus, opposite ranking.
"Inherits" and "matters" are different axes.

---

### 2. ANSWER-COMMITMENT LEAD
*Does the chain reach its answer before it announces it?*

**(a)** With the answer **held out** of the chain: **COMMIT** = the earliest
step at which the cumulative chain content has accumulated enough of the
answer's *distinguishing* terms (answer terms not already present in the
question) to have determined the answer. **ANNOUNCE** = the earliest step
containing a conclusion frame ("so the answer is", "therefore", "in
summary", …). **LEAD = COMMIT − ANNOUNCE.** Positive = derived (committed
first, named later). Negative = narrated (named first, justified after).

**(b)** **Offline `[O]`**, given the answer is recorded separately. Both
indices are lexical; the answer must not be the chain's last step, or the
signal is unavailable and says so. A scrambled-word control is computed
alongside — but it must be a control that can *fail*: if it can never be
reached, it always agrees and measures nothing.

**(c)** Reasoning Theater — https://arxiv.org/abs/2603.05488 (poster
https://icml.cc/virtual/2026/poster/66648) — the performativity rate, which
is the activation-based original of this signal; When Reasoning Traces Become
Performative — https://arxiv.org/abs/2605.11746 — the Belief-CoT Agreement
(BCA) metric and the answer-commitment proxy; Knowing Before Saying —
https://arxiv.org/abs/2505.24362.

**(d)** **[M]** Performativity rate — DeepSeek-R1 MMLU **0.417**, GPQA-D
**0.012**; GPT-OSS MMLU **0.435**, GPQA-D **0.227**. Mean BCA **0.619**
across nine models and seven benchmarks; **58.0%** of 168,302 mismatch events
are Confabulated Steps; per-model CS rate 37.4%–75.4%; the committed answer
**never** changes during a CS step (100% stability over 314 instances);
**90.1%** of individual CS steps have Δp_ans < 0.001; mean p_ans across CS
steps 0.851; CS steps are 30.9% of steps per instance. Benchmark-level BCA
spans **0.044** (Qwen2.5-32B/ProsQA) to **0.914** (Llama-3.1-8B/PrOntoQA).
Inflection points per step: high-confidence 0.020 vs non-high-confidence
**0.045**. Early exit at 95% confidence kept 97% of MMLU accuracy while
saving **68%** of tokens. **[P]** The lexical COMMIT/ANNOUNCE formulation
is ours — a text-only shadow of an activation-based measure.

**[C]** **The text-only shadow is known to err in a specific direction.**
Fujitsu's text-only judges reached AC1 = 0.78 with each other and still
labelled **82%** of inspected cases as Premature Convergence when the
detectors said Confabulated Steps. So a text-only lead measure will
**over-report narration** on chains that committed early and continued —
i.e. it errs toward calling genuine work theatre. **[C]** Reasoning Theater's
own inflection↔probe-shift relation reverses between models (R1 vs GPT-OSS)
and vanishes on GPQA-D.

---

### 3. ANSWER COMMITMENT FROM ACTIVATIONS (the gold standard, not offline)
*When did the model actually decide?*

**(a)** The logit-lens probability of the answer token at each step,
`p_ans(t, ℓ)`, thresholded at τ = 0.3, compared with whether the trace has
explicitly reached the answer. The step at which `p_ans` crosses τ is the
**commitment step**.

**(b)** **Not offline `[O]`** — requires the model's hidden states. It is
listed because it is the **reference the offline signals stand in for**, and
because its *text-free* nature is precisely what the offline constraint
forecloses. A recorder that saves activations (or per-step answer-token
logprobs) can compute it exactly; a recorder that saves only text cannot.

**(c)** When Reasoning Traces Become Performative —
https://arxiv.org/abs/2605.11746 — the logit-lens proxy, validated against
Patchscopes and tuned-lens probes; Reasoning Theater —
https://arxiv.org/abs/2603.05488 — attention-pooled probes; Knowing Before
Saying — https://arxiv.org/abs/2505.24362.

**(d)** **[M]** Patchscopes agrees with the logit lens on **75.6%** of
mid-depth and **74.7%** of final-layer steps; tuned-lens agreement **≥
99.2%** across four held-out configurations. Convergence timing gap reaches
**24.1 steps**; ρ(BCA, CTG) = **−0.48** (p < 0.001). A causal
direction-ablation check flips answers in a measurable fraction of cases.

---

### 4. BACKWARD INFLUENCE / STEP ABLATION
*Does an early step change the final answer?*

**(a)** Perturb step k, re-run the chain, and test whether the answer's
content words move. Reported as a **rate** over probed steps. The final step
is a mandatory positive control: perturbing it must move the answer, or the
measurement is not measuring what it claims.

**(b)** **Not offline** — needs the model. Opt-in by design; the instrument
takes a `rerun` callable it does not implement, so the dependency stays
clean and the signal stays testable with a fake.

**(c)** Measuring Faithfulness in Chain-of-Thought Reasoning (Lanham et al.)
— https://arxiv.org/abs/2307.13702 — early answering, adding mistakes,
paraphrasing, filler tokens, summarised as **AOC**; Thought Anchors —
https://arxiv.org/abs/2506.19143 — the KL-over-resampling implementation;
Reasoning Models Don't Always Say What They Think (Chen et al.) —
https://arxiv.org/abs/2505.05410 — hint injection; Counterfactual Tests for
CoT Faithfulness in VLMs — https://aclanthology.org/2026.findings-emnlp.2348.pdf.

**(d)** **[M]** For the three lowest-AOC tasks (ARC-Easy, ARC-Challenge,
OpenbookQA) the CoT changes the final answer **less than 10%** of the time;
for AQuA it changes it **more than 60%** of the time. Injected mistakes are
plausible at least **80%** of the time. Overall CoT faithfulness **25%**
(Claude 3.7 Sonnet) and **39%** (DeepSeek R1); **20%** and **29%** on
misaligned hints. Outcome-based RL plateaus at **28%** (MMLU) / **20%**
(GPQA); in 5 of 6 RL environments the reward hack is verbalised in **<2%**
of examples while used in **>99%**. In VLMs, CoTs omit a removed object
even when its removal causes a large prediction shift. **[P]** Our probe
positions and the 0.8 overlap threshold for "the answer moved".

**[C]** Post-hoc-ness does **not** predict usefulness — Lanham et al. say
so directly (LogiQA gets negligible benefit from CoT yet ranks second in
AOC). **[C]** CoT faithfulness does not improve with scale: 15–25%
unfaithful traces persist in the strongest models, and detection gets
*harder* on stronger models.

---

### 5. PLAN-PHASE FIDELITY (step/action consistency)
*Did the chain do anything it did not say it would do?*

**(a)** Segment the recorded chain into phases; let Φ be the set of phases
the chain **declared** (its own stated plan). **PPF = |Φ| / |Φ ∪ {phases
actually present}|**. PPF = 1 means every phase that occurred was one the
chain said it would run. Paired with **PPC** (did it cover the declared
phases?) and **POC** (in the declared order?), combined as the **geometric
mean** `PC = (PPC · POC · PPF)^(1/3)` so no dimension can be traded against
another.

**(b)** **Offline `[O]`**, given a recorded plan. Phase segmentation is
rule-based (transition markers, sentence boundaries) — the same parser shape
Fujitsu validated at F1 = 0.87.

**(c)** From Plan to Action: How Well Do Agents Follow the Plan? —
https://arxiv.org/abs/2604.12147 — the PPC/POC/PPF/PC metric, over 2,000
SWE-agent trajectories; PIVOT —
https://arxiv.org/abs/2605.11225 — the **first-divergence index** i\*, the
earliest step at which the run trace no longer supports the planned prefix;
SAVER — https://aclanthology.org/2026.acl-long.1440/ — the support function
`Γ(s_l | x, H_l, E_l) ∈ [0,1]`, unfaithful below ε.

**(d)** **[M]** Plan compliance drops **13%** on average from SWE-bench
Verified to SWE-bench Pro; resolved instances have significantly higher
compliance (p = 1e-5, p = 0.032); PC correlates only very weakly with
graph-shape metrics (Pearson 0 < r ≤ 0.2). PIVOT's baseline error audit
found **"ignored evidence" — facts retrieved but not cross-referenced — in
44–47% of cases.** SAVER: Avg Viol 1.98 for CoT, 1.33 for MAD, 2.65 for
vanilla LM; USR 46.41%–53.19% uncoached, 7.78%–9.12% with auditing+repair;
VFR up to 84.20%. **[P]** Applying the metric to a reasoning chain rather
than an agent trace is ours.

**[C]** These are software-repair agents on SWE-bench — the rates are not a
general constant. And agents follow a plausible phase sequence **even when
given no plan at all**, so a chain exhibiting the *shape* of sequential
reasoning is not thereby evidence of reasoning.

---

### 6. BOUNDARY-vs-FACT SURVIVAL IN A HANDOFF
*Did the handoff keep the rules and drop only the words?*

**(a)** Two survival scores over the same rubric: **σ_b** = boundary-marker
survival (instructions, caveats, hedges, audience limits, ownership limits,
privacy limits) and **σ_op** = operational-fact survival. Both are
per-item means over a four-level rubric. The measurement is the **gap and
the correlation**: if facts survive and rules do not, the handoff is
deceptive in a specific, detectable way.

**(b)** **Offline `[O]`.** Deterministic marker survival is directly
checkable (a marker's survival can be scored by string presence); the
four-level rubric needs a judge. The *correlation* σ_b vs σ_op is the
statistic that carries the finding, and it is cheap.

**(c)** Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM
Handoffs — https://arxiv.org/abs/2608.29028; When Summaries Distort
Decisions — https://arxiv.org/abs/2606.29251; Compress the Context, Keep
the Commitments — https://arxiv.org/abs/2605.17304.

**(d)** **[M]** σ_b ≈ **0.80** for uncompressed free-text handoffs, falling
to ≈ **0.57** under a 25-word budget while σ_op stays near ceiling (Qwen3-32B:
σ_b 0.915 → 0.557, σ_op 0.986 → 0.977). The two are **uncorrelated**:
Pearson r = **−0.042** (GPT-5-mini) and **0.086** (DeepSeek-R1-32B) over 180
handoffs each. External PrivacyLens data: **2,465 handoffs** / 493
scenarios, σ_b falls by **0.45** while σ_op stays in **0.94–0.99**. Vague
boundary language leaks in **73%** (GPT) and **50%** (DeepSeek) of cases;
explicit constraints reduce leakage to **under 15%** across all three models.
A no-handoff single-agent control still leaks more than the operationalised
handoff. **[P]** Adapting σ_b/σ_op to a reasoning-chain summary rather than
a privacy handoff is ours.

**[C]** The *rates* are domain-specific (financial filings, privacy
markers). The *mechanism* — facts and rules lost at different rates — is
general.

---

### 7. HANDOVER RETENTION RATIOS
*Did the summary preserve the uncertainty, the caveats and the dead ends?*

**(a)** Three retention ratios — summary rate per 1,000 words ÷ chain rate
per 1,000 words — for **uncertainty** (hedges), **caveats** (exceptions),
and **abandoned branches** ("does not work", "discard", "rule out"). Below
1.0 = the summary dropped that class. A summary that flattens uncertainty
reads as more certain than the work was.

**(b)** **Offline `[O]`.** Closed marker lists, **reported with the
measurement** so the number can be read with its assumption attached.

**(c)** When Summaries Distort Decisions — https://arxiv.org/abs/2606.29251 —
the decision-flip consequence of decontextualization; Facts Without Rules —
https://arxiv.org/abs/2608.29028; Compress the Context, Keep the
Commitments — https://arxiv.org/abs/2605.17304 — commitment preservation as
the right frame, and **Commitment Density** (preserved commitments per
token) as the metric shape.

**(d)** **[M]** Re-reading noise floor: **7.0%** (MD&A) and **5.7%**
(earnings calls) of decisions flip with **no** compression. Naive
compression flips **31.5%** and **24.9%** — i.e. **above** the noise floor
by 4×. Contextualization lowers MD&A flips to **21.2%**; merging a second
model's summary alone reaches **25.6%**. Two compressors agree on the
induced decision only ~75% of the time. Structured prose can preserve all
annotated commitments but "its gains are modest and depend on careful
prompting" (76 lexical tokens vs 99 for full state vs 138 for JSON).
**[P]** The three-class construction and the 0.85 / 0.5 thresholds are ours.

**[C]** The compression ratios are task-specific. And *uncertainty
preservation* is **not** the same as *fidelity*: a summary can preserve
hedges while dropping the reasoning that made the hedge necessary, which is
what the "ignored evidence" archetype (44–47%) looks like from the other end.

---

### 8. LIVE-CANDIDATE COUNT / COMMITMENT MONOTONY
*Does the chain narrow as it goes?*

**(a)** Count the distinct **answer-like entities kept alive** at each step
(not every noun — counting nouns makes the measure track length). Report
the least-squares slope against step index. Negative = narrowing = a working
search; positive = widening = a narrative holding every option open so that
any final answer looks reasonable.

**(b)** **Offline `[O]`.** Entity extraction is lexicon-bound, so the
extractor and its marker list must be **reported with the measurement**.

**(c)** FaithCoT-Bench — https://arxiv.org/abs/2510.04040 — the taxonomy
(selective explanation bias 19.74%, step skipping 24.36%); Reasoning Theater
— https://arxiv.org/abs/2603.05488 — the performative MMLU case, where the
model "reasons three separate times explicitly over each of the four
options, with no change in internal confidence"; Faithful, Not Corrective —
https://arxiv.org/abs/2607.09678 — faithfulness is direction-blind.

**(d)** **[M]** 41.66% of unfaithful instances are post-hoc reasoning, 57.71%
are spurious reasoning chains; over 15–25% unfaithful traces persist in the
strongest models; LLM-as-judge detection reaches F1 **65–77** and gets
*worse* on stronger models (76.1 → ~50). **[P]** The slope-over-entity-count
construction has **no published calibration**.

**[C]** **Chain length is not computation** (Palod et al.,
https://arxiv.org/abs/2509.07339): intermediate-token length correlates
*loosely* with problem complexity, the correlation "disappears entirely" out
of distribution, and the apparent correlation arises from approximate recall
rather than adaptive computation. A narrowing chain is therefore not evidence
of computation by itself.

---

### 9. VIOLATION PROFILE (typed, per-step)
*What kind of unfaithfulness, and at which step?*

**(a)** A profile `h(r)` counting violations by type, with each violation
carrying the index of the step it fired at — so a chain can be **globally**
unfaithful or fail only at **specific** steps. Six types: **Missing_
Assumption, Invalid_Precondition, Unjustified_Inference, Circular_Reasoning,
Contradiction, Overgeneralization**. Plus the "spurious chain" subtypes:
step skipping, selective explanation bias, weak justification, lack of
transparent post-answer analysis.

**(b)** **Partially offline.** The *vocabulary* is offline; *detecting* the
types needs a judge (a model call) or a trained classifier over a labelled
corpus. Rule-based detection is possible for the syntactic members
(Circular_Reasoning, Contradiction) and unreliable for the epistemic ones.

**(c)** SAVER — https://aclanthology.org/2026.acl-long.1440/ — the six-type
set, the per-step violation instance set, the support function and threshold
ε, and the metrics Avg Viol / USR / VFR; FaithCoT-Bench —
https://arxiv.org/abs/2510.04040 — the post-hoc vs spurious split and the
eight fine-grained signals, over 1,000+ expert-annotated trajectories with
300+ unfaithful instances.

**(d)** **[M]** SAVER on LLaMA-3.1-8B/HotpotQA: Avg Viol **0.37**, USR
**9.12%**, VFR **81.36%** (Qwen-2.5-7B: 0.31 / 7.78% / 84.20%); baselines
CoT 1.98, MAD 1.33, vanilla LM 2.65. Removing the Auditing stage: Avg Viol
0.37 → **1.37**, VFR 81.36% → **42.65%**. Removing Repair: → **1.56** /
**33.68%**. FaithCoT-Bench fine-grained: step skipping **24.36%**, selective
explanation bias **19.74%**. **[P]** Any offline detector for these types.

**[C]** The five Fujitsu detectors **overlap by design** — 68.4% of
unfaithful steps satisfy more than one criterion, and two of the five are
near-redundant (Pearson r = **0.937**, 95% CI [+0.930, +0.943]). A taxonomy
is not a partition, and a profile over a non-partitioning taxonomy needs the
multi-label counts reported.

---

### 10. RELAY DEPTH DECAY
*How much did each handover cost?*

**(a)** The accuracy drop per relay stage, and the per-question KL
divergence between the single-agent posterior and the relayed posterior. The
two together say *how much* was lost and *whether the loss is information
loss*.

**(b)** **Offline `[O]`** for the per-stage drop given a recorded relay
chain; the KL needs the models' output distributions.

**(c)** On the Reliability Limits of LLM-Based Multi-Agent Planning (Ao et
al.) — https://arxiv.org/abs/2603.26993; Faithful, Not Corrective —
https://arxiv.org/abs/2607.09678; LLM as a Broken Telephone (ACL 2025) —
https://aclanthology.org/2025.acl-long.371/.

**(d)** **[M]** MMLU accuracy falls **90.7%** (1 agent) → **41.2%** (2) →
**43.5%** (3) → **22.5%** (5), below the 25% chance level; o4-mini 89.9% →
37.0%. Message format dominates: posterior-style relay degrades **−2.8
points/stage** against **−8.5** for prose, reaching **75.2%** vs **58.1%**.
KL-vs-accuracy-drop correlation **r = 0.72** (3-agent), **r = 0.44**
(5-agent). Tool access that adds signal: 24.3% → **82.7%**; tool access
that only re-processes: 87.2% vs a 90.7% baseline. Under an injected error,
**83–100%** surface persistence to the final hop, and the true value
survives at **86–100%** — **faithfulness is direction-blind**.

**[C]** **The two format findings disagree.** Ao et al. find format
dominates depth; *Faithful, Not Corrective* finds that at the strong tier
every format's fidelity effect is bounded within **±1.8 points** while cost
rises 24–53%, and that schemas do not repair an injected error. The field
has not settled whether structure prevents drift or merely slows it.

---

### 11. COMMITMENT-DENSITY RATIO
*How many of the chain's commitments survived the compression?*

**(a)** Preserved commitments per token, with a commitment being a
canonicalised atom carrying confidence, source evidence and criticality —
rather than a surface-token count. The policy precedent: an atom with
confidence < .50 and criticality ≥ 3 is preserved raw; a safety-flagged atom
is preserved with its source span; disagreement resolves toward
preservation, not minification.

**(b)** **Offline `[O]`** given the extracted atoms; extraction itself is the
bottleneck and needs a model.

**(c)** Compress the Context, Keep the Commitments —
https://arxiv.org/abs/2605.17304 — commitment-level compression,
commitment density, and the preservation policy.

**(d)** **[M]** CCL-Core preserves all annotated commitments in **76** lexical
tokens vs 99 for the full state and 138 for JSON; structured prose's gains
are "modest and depend on careful prompting". **[P]** Any offline atom
extractor.

**[C]** The paper states its own claim is "a design principle rather than a
theorem of semantic preservation", and that preservation holds **only if**
the extractor recovers the relevant commitments.

---

### 12. TEXT-ONLY JUDGE ERROR RATE (a calibration warning, not a signal)
*How much should a text-only instrument be trusted?*

**(a)** The rate at which a text-only judge assigns the wrong *category* to
steps that a mechanism-based detector has classified. This is not a signal
about a chain; it is the **error budget for every text-only signal**, and it
should be quoted next to any of them.

**(b)** **Offline `[O]`** given detector labels — which is the point: the
comparison requires the detector.

**(c)** When Reasoning Traces Become Performative —
https://arxiv.org/abs/2605.11746 — three text-only judges vs the detector;
FaithCoT-Bench — https://arxiv.org/abs/2510.04040 — the judge-vs-detector
comparison across eleven methods.

**(d)** **[M]** Text-only judges reached AC1 = **0.78** with each other and
still labelled **82%** of inspected cases as Premature Convergence when the
detectors said Confabulated Steps. Human annotators reached AC1 = **0.71**
on the five-way taxonomy. LLM-as-judge detection F1 **65–77**; the best
detector gets *worse* on stronger models (76.1 → ~50).

**[C]** This is the single most important number for an offline instrument:
**text-only detection of unfaithfulness is a weaker instrument than the
mechanism-based measures it substitutes for, and its error direction is
known.**

---

## THE SHORTLIST: THE SIX THAT SURVIVE

Prioritised as instructed — causal conditioning, self-prediction, step/action
consistency, handover distortion — plus the two that the literature supports
strongly enough to anchor them.

| # | signal | offline | status | why it survives |
|---|---|---|---|---|
| 1 | Adjacent-step inheritance | yes | `[M]` basis, `[P]` construction | step skipping is the largest measured failure mode (24.36%); needs a control to mean anything |
| 2 | Answer-commitment lead | yes | `[P]` proxy for `[M]` measure | the only signal that separates "carries the answer" from "narrates the answer"; but a text-only shadow with a known error direction |
| 3 | Backward influence | **no** | `[M]` | strongest and best-measured; opt-in, and the only one needing the model |
| 5 | Plan-phase fidelity | yes | `[M]` metric, `[P]` our use | the step/action axis; fully offline given a recorded plan |
| 6 | Boundary-vs-fact survival | yes | `[M]` | heavily measured; the *gap* is the signal |
| 7 | Handover retention ratios | yes | `[P]` | the distortion axis the project cares about; the failure is measured even though the detector is ours |
| 8 | Live-candidate count | yes | `[P]` | weak support, but it is the only signal about *narrowing* — and Palod constrains it hard |
| 12 | Judge error rate | yes | `[M]` | the error budget for 1, 2, 5, 7, 8 — must be quoted with them |

**Dropped, with reasons.** Signal 3 (activation commitment) is not offline
and becomes signal 2's reference, not a signal. Signal 4's other members
(hint injection, VLMs) need a model. Signal 9's detection needs a judge.
Signal 10 needs a relay chain, not a single chain. Signal 11 needs atom
extraction.

**And the shape of the verdict that follows.** No single signal may produce
a verdict, no text-only signal may produce a *confident* verdict without the
opt-in rerun, and the reported result is a **panel with directions**, not a
composite score — because the composite's weights are not known, and
FaithCoT-Bench's F1 65–77 ceiling says a single-number instrument would
inherit that ceiling.

---

## THE FINDINGS THAT SETTLE THE DESIGN

Four results from the survey bear directly on how the instrument is built,
and they are worth stating before the signal-by-signal detail because they
are the reason the tool looks the way it does.

**1. The answer is usually knowable before the chain says so.** Boppana et
al. find that on MMLU, the final answer is decodable from activations "far
earlier" than a text monitor can find it, and that this gap *shrinks on hard
tasks* — on GPQA-Diamond the performativity rate is 0.012 against 0.417 for
MMLU on the same model. The second paper, the Fujitsu step-level study, finds
the same thing at finer grain: latent commitment and explicit answer arrival
agree on only 61.9% of steps, and 58.0% of the mismatches are
**confabulated continuation** — the model has settled and keeps writing
deliberative-looking text anyway.

Together these say: **the signal that matters is temporal.** A chain that
"reached" its answer before announcing it is doing something a narrated
answer cannot do. And the "something" is measurable without a model call,
because the *text* of the chain carries the timing.

**2. Post-hoc rationalization has a published taxonomy and a published
taxonomy's own number.** FaithCoT-Bench annotates 1,000+ trajectories and
splits unfaithfulness into post-hoc reasoning (41.66% of unfaithful
instances) versus spurious reasoning chains (57.71%), then into eight
fine-grained signals. The two most frequent are **step skipping (24.36%)**
and **selective explanation bias (19.74%)**. Both are readable from text
alone. That is the empirical basis for the instrument's `step_inheritance`
signal (step skipping is a step that does not inherit) and for the
`commitment_monotony` signal (a narrative keeps every option alive).

**3. Text-only judges get the *category* right and the *timing* wrong.**
The Fujitsu study had three LLM judges label steps from text only: they
reached high agreement with each other (AC1 = 0.78) and still labelled 82%
of inspected cases as *Premature Convergence* when the detectors said
*Confabulated Steps*. Text inspection cannot see the difference between "the
model committed early and continued" and "the model committed early and
stopped". This is the argument for measuring **timing** rather than
categorising.

**4. Handover distortion is not uniform, and the non-uniformity is the
signal.** Three independent results:
- Summaries preserve operational facts while **losing the boundary metadata**
  that licenses them (σ_b ≈ 0.80 → 0.57 under a 25-word budget, while
  σ_op stays near ceiling; the two are uncorrelated, Pearson r = −0.042 and
  0.086).
- Compression can change the **decision** the source supports, with a
  re-reading noise floor of 7.0% (MD&A) and 5.7% (earnings calls) against a
  naive-compression flip rate of **31.5%**.
- Relay depth degrades accuracy: 90.7% (1 agent) → 41.2% (2) → 43.5% (3) →
  **22.5% (5)**, below the 25% chance level. But a *structured* relay
  degrades at −2.8 points per stage against −8.5 for prose, reaching 75.2%
  where prose reaches 58.1%.

The lesson: a handover that drops caveats while keeping facts is
**distinguishable** from one that drops both, and the ratio is the measurement.

---

## DELEGATION AND PLANNING AS REASONING

The user prioritised this, and it is the part of the literature that speaks
most directly to **"was the delegated task's reasoning genuine, or a plausible
summary?"** Two distinct measurement traditions exist, and they measure
different things: **plan-to-action alignment** (does what the agent did match
what it planned?) and **handover fidelity** (does the message that crossed the
boundary preserve the reasoning it carried?).

### Plan-to-action alignment — the "step/action consistency" axis

**From Plan to Action: How Well Do Agents Follow the Plan?** (ASE 2026) —
https://arxiv.org/abs/2604.12147 — the most directly transferable
measurement. It introduces a **process-centric plan compliance** metric for
coding agents, measured over 2,000 trajectories from SWE-agent with four
models (GPT-5 mini, DeepSeek-R1, DeepSeek-V3, Devstral-small 24B). A plan is
a phase alphabet Φ with an expected sequence L*(Φ); the agent's actual trace
is segmented into phases.

**(a) The metric, precisely.**
- **PPC** (plan phase compliance) — does the trace cover the planned phases?
- **POC** (plan order compliance) — are they in the specified order?
- **PPF** (plan phase fidelity) — `PPF = |Φ| / |Φ ∪ {phases appearing in the
  trace}|`, so PPF = 1 when every phase in the trace belongs to the plan, and
  PPF < 1 when the agent did something off-plan.
- **PC** (overall) — `PC = (PPC · POC · PPF)^(1/3)`, the **geometric mean**, so
  low compliance in any one dimension proportionally reduces the score
  without compensation from the others.

**(b) Why the geometric mean is the right shape for our instrument.** A
chain that follows every planned phase in the right order but adds one
off-plan action is *less* faithful than a chain that misses one phase, and
the geometric mean encodes that: no dimension can be traded against another.
That is the same property the project's own gate relies on.

**(c) Measured numbers [M].**
- Plan compliance **drops by 13% on average** across all agents when moving
  from SWE-bench Verified to SWE-bench Pro.
- Resolved instances show **significantly higher** plan compliance than
  unresolved ones for Devstral-small (p = 1e-5) and DeepSeek-R1 (p = 0.032) —
  i.e. plan-following *correlates with task success*.
- Plan compliance PC correlates only **very weakly** with graph-structure
  metrics (Pearson 0 < r ≤ 0.2) — so trajectory shape alone does not capture
  it, which is the paper's argument for a process-centric metric.
- "Even when not explicitly instructed, agents follow the Standard plan to a
  notable degree" — under a No Plan condition, phase flow still shows the
  NRPV workflow. **This is a warning for our instrument**: a chain can
  exhibit the *shape* of genuine sequential reasoning because the model
  learned that shape, not because it reasoned.
- The plan's influence **decays with trajectory length** (context pressure),
  and periodic re-insertion of the plan every five steps improved compliance
  for DeepSeek-V3 while maintaining PC for others.

**(d) Contested / limiting [C].** The compliance rates are for *software
repair* agents on SWE-bench. They are not a general constant. The paper also
reports that even a reordered plan produced only a negligible success change
(38.3% → 38%), i.e. **plan order matters less than plan presence** — which
means POC may be the weakest of the three dimensions for our purposes.

**Transfer to the chain audit.** Plan compliance is the **agent-side dual**
of Signal 1. A recorded reasoning chain is to a plan what a tool trace is to
a reasoning trace: the plan says what was intended, the trace says what
happened. PPF — "does every phase in the trace belong to the plan" — is
directly computable from a recorded chain if the plan is recorded, and it is
the cleanest available operationalisation of **"did the chain do anything it
did not say it would do?"** That is a stronger form of the "step skipping"
failure mode FaithCoT-Bench reports at 24.36%.

### First-divergence localisation — the causal axis

**PIVOT: Bridging Planning and Execution in LLM Agents via Trajectory
Refinement** — https://arxiv.org/abs/2605.11225 — **[M]** the formalisation
worth borrowing. PIVOT decomposes failure into three terms: a final-outcome
term, a **discrepancy** term `D(τ, τ̂)` measuring where execution stopped
preserving the constraint structure encoded in the plan, and a cost term for
computation spent on trajectories that had already gone off course.

**The measurement that matters for us: the first-divergence index.**
PIVOT identifies *the first step at which planned and run trajectories
diverge*, using a divergence threshold T: the index i\* marks the earliest
step at which the run trace no longer provides sufficient support for the
planned trajectory prefix, and therefore identifies where local repair should
begin. Errors are attributed **backward** from each violation through the
step dependencies.

**The resumption probe** is the part with a direct offline analogue. For
irrecoverability, PIVOT keeps each step k *verbatim, including its tool
outputs*, and lets a fixed model continue the task without feedback. The
resumer can satisfy a violated constraint only if the retained prefix has not
yet committed to the error, so the last k at which resumption succeeds marks
the commitment point. **This is "the chain predicts its own answer before the
answer appears", operationalised as a prefix test**: the prefix's commitment
to the final answer is the thing being measured.

**[M]** Numbers: up to ~94% relative improvement in constraint satisfaction on
DeepPlanning and GAIA, with 3–5× fewer tokens than the baselines. The
dominant baseline failure archetype in their analysis is **"ignored
evidence" at 44–47% of cases** — the agent retrieved all necessary data but
failed to cross-reference it during output assembly. That failure mode is
**exactly** the handover-distortion shape: the facts survived, the reasoning
that connected them did not.

**[C]** PIVOT is a *method* paper, so its headline number is an improvement
claim, not a measurement of the phenomenon. The first-divergence index is
sound but is used with a model in the loop, so it is not an offline signal as
it stands. The **"ignored evidence" 44–47%** figure is from the authors'
own error-archetype audit of baseline failures, so it is a characterisation
of their baselines, not a population rate.

### Faithfulness of intermediate reasoning in agents — the judge axis

**Verify Before You Commit: Towards Faithful Reasoning in LLM Agents via
Self-Auditing** (SAVER, ACL 2026) —
https://aclanthology.org/2026.acl-long.1440/ — **[M]** the most explicit
formal treatment of *intermediate reasoning* faithfulness in an agent, and
it introduces the vocabulary the instrument should adopt.

**The support function.** Given an input task x and a reasoning trajectory
τ = (s₁, …, s_L), the paper defines a **support function**
`Γ(s_l | x, H_l, E_l) ∈ [0,1]`, where H_l is the reasoning history and E_l
the accessible evidence (retrieved documents, tool outputs, environment
observations). A step is **unfaithful** if its support score falls below a
threshold ε. That is a direct formal statement of what Signal 1 measures
informally.

**The violation type set.** The auditor localises violations into six types:
**Missing_Assumption, Invalid_Precondition, Unjustified_Inference,
Circular_Reasoning, Contradiction, Overgeneralization**. The per-trajectory
**unfaithfulness profile** `h(r_i)` counts violations by type, and the
violation instance set `V(r_i) = {(t_ij, l_ij)}` records *which step* each
violation fired at — so the paper separates **globally unfaithful beliefs**
from beliefs that fail at specific steps. The instrument's Signal 4 should
report a profile like this rather than one slope.

**The three metrics.** The paper evaluates: **average violations per
reasoning trajectory**, the **unfaithfulness survival rate (USR)** — the
residual violation rate after the audit-repair loop — and the **violation
fix rate (VFR)**.

**[M]** Measured numbers, LLaMA-3.1-8B on HotpotQA: SAVER reaches
**Avg Viol 0.37, USR 9.12%, VFR 81.36%**, against CoT at 1.98 / 27.36% /
(24.89→27.36%) and MAD at 1.33 / 36.74% / 23.94%; on Qwen-2.5-7B, 0.31 /
7.78% / 84.20%. Vanilla LM (no reasoning scaffold) is the *worst* on
faithfulness while looking fine on task metrics — 2.65 violations per
trajectory and USR 46.41%, against 2.83 / 53.19% for CoT. On a second
setting: SAVER 0.24 / 83.44% VFR / 6.53% USR. Ablations: removing the
**Auditing** stage takes Avg Viol from 0.37 to 1.37 and VFR from 81.36% to
42.65%; removing **Repair** takes it to 1.56 / 33.68%. The paper's own
framing: "Most existing strategies rely on the consensus mechanism,
conflating agreement with faithfulness."

**[C]** SAVER's own limit is stated in the paper and it is the same limit as
ours: the auditing step **uses a model**, and the paper's contribution is a
*repair* framework, so its numbers measure the value of repairing, not the
prevalence of unfaithfulness. The **Avg Viol for vanilla CoT (1.98)** and
**MAD (1.33)** are measured on *their* annotation rubric with *their*
auditor, so they are not directly comparable to our signal readings.

### The judge-vs-detector question

**FaithCoT-Bench** (https://arxiv.org/abs/2510.04040) is the benchmark that
answers "which detector method works", and the answer is uncomfortable for a
judge-based instrument: **[M]** LLM-as-judge methods achieve the highest F1
across datasets and models, **typically 65–77**, on average exceeding other
paradigms by more than 30%. So a rubric-driven judge **does** beat
counterfactual and logit-based detection at the task of identifying
unfaithful traces. The bad news is in the same numbers: Faithful-Judge
scores 76.1 on TruthfulQA with Qwen2.5-7B but ~50 with GPT-4o-mini and
Gemini2.5-flash.

**[C] That is the central contested claim for the instrument:** the *best*
detector gets F1 ≈ 65–77 and gets *worse* on stronger models. This is the
strongest argument for the project's existing decision to report a **panel
of signals with no single composite score** — a judge-based instrument would
inherit this ceiling.

### Summary of the delegation/planning material

| axis | measurement | offline? | status |
|---|---|---|---|
| plan ↔ action | PPC / POC / PPF, `PC = (PPC·POC·PPF)^(1/3)` | yes, if the plan is recorded | `[M]` metric, `[P]` our thresholds |
| first divergence | index i\* of first unsupported planned prefix | no (needs a resumer) | `[M]` method, model required |
| support of a step | `Γ(s_l | x, H_l, E_l) ∈ [0,1]`, unfaithful if < ε | partially | `[M]` formalisation, our Γ is a proxy |
| violation profile | 6-type set + per-step indices | partially | `[M]` vocabulary |
| handoff content | σ_b vs σ_op | yes | `[M]` heavily measured |

**The practical conclusion.** The most valuable *new* signal this material
suggests for the instrument is a **plan-phase-fidelity measure (PPF) over a
recorded reasoning chain**: segment the chain into phases, and compute what
fraction of the phases that appear are phases the chain declared. A chain
that reaches PPF = 1 but with a low PPC has *narrated* a plan it did not
execute. This is the step/action consistency axis, and it is fully offline
given a recorded plan.

---

## SIGNALS THE SURVEY CONSIDERED AND DID NOT ADOPT

Recording these matters as much as recording the adopted ones — the
instrument's scope is a decision, and a reader should be able to see what
was left out and why.

- **CoT-tampering detection** — *Can Reasoning Models Detect Changes to
  their Chains of Thought?* (Napa et al.) — https://arxiv.org/abs/2606.22085
  — **[M]** four models (GPT-OSS-120B, Kimi K2.5, DeepSeek V3.2,
  Qwen3-235B-A22B-Thinking) prefilled with modified CoTs across GPQA-Diamond,
  MMLU-Pro (200-example subset) and AIME 2025. Findings: detection accuracy
  is **only modestly above chance**, and often **not significantly** above it
  — removing a CoT's entire latter half is not significantly better than
  chance for most results; in the **unalerted** setting (no instruction that
  tampering is possible) detection is **consistently at chance**. Models are
  **equally good at detecting changes to their own CoTs as to other models'
  CoTs** — differences not statistically significant for any model, with GPT
  and Kimi scoring *higher* on the other condition. Localisation is poor for
  paraphrase and deletion ("low single-digit accuracies") but reaches
  **42.5% (GPT)** to **89.5% (Qwen)** for an inserted irrelevant step — and
  an ablation replacing the inserted step with a *relevant non-sequitur*
  makes accuracy "plummet to well below chance".
  **[C]** The authors' own limitation: proprietary frontier models whose
  APIs do not support CoT prefilling **could not be studied**, so the
  conclusion may not transfer to the models we most care about. **[C]**
  *Not adopted as a signal* because it requires a model call and the
  instrument is offline. But it is load-bearing for the instrument's
  **design premise**: models do not notice their own CoT being edited, so a
  chain that survives a perturbation is not thereby shown to be genuine. The
  literature's own conclusion is that modification detection reflects "a
  general capacity to recognize reasoning abnormalities", not self-awareness.
- **Context-compression faithfulness** (compressors) — the KV-cache
  compression results (**When Less Latent Leads to Better Relay**,
  https://arxiv.org/abs/2604.13349) — **[M]** relaying only **9.9%–20.2%**
  of the prompt KV keeps accuracy close to full relay across nine benchmarks;
  roughly half the deleted information is representable by the kept value
  states (PCR ≈ 40%–50%). **[M]** *Not adopted* because it operates on
  activations, not on text, so it is not an offline text signal — but it
  corroborates the handover finding from the other side.
- **Broken telephone** (Mohamed et al., ACL 2025) —
  https://aclanthology.org/2025.acl-long.371/ — the general iterative-
  distortion result. *Not adopted* because it measures transmission, not
  summary-of-chain.
- **Self-reference / recursion depth** — see the separate section below.

---

## RECURSION DEPTH AND INTROSPECTION DEPTH: THE MEASURED NUMBERS

The task asked for reported numbers here. **The honest answer is that this
literature reports almost no depth numbers for LLMs**, and the papers that
look like they do report *formal* quantities instead. Recording that gap is
more useful than manufacturing a number.

- **Self-Reference in Large Language Models: The Introspection Threshold**
  (arXiv 2607.04277; v1 titled *Self-Referential Introspection in Large
  Language Models: the Critical Threshold for Recursive Self-Improvement*,
  v2 dated 18 Sep 2026) — https://arxiv.org/abs/2607.04277 —
  **[M]/[P]** the framing is formal, the empirical content is a survey.
  **The threshold concept:** von Neumann's self-reproducing automata need a
  *complexity threshold* above which self-reproduction is possible. The paper
  argues the AI analogue is **introspection** — the capacity to simulate
  one's own computational processes with enough fidelity to identify and
  rectify deficiencies. The formal instrument is **Kleene's Second Recursion
  Theorem**: for a total recursive function f_T that simulates program x on a
  universal machine U for at least T steps, there exists an index e* with
  φ_e* ≃ φ_{f_T(e*)}, so the program can simulate its own source. The bound
  T matters: without it f_T is not total computable and the theorem does not
  apply. The threshold claim is stated as an explicit **informal conjecture**:
  there exists a critical level of self-modelling capacity below which
  improvement degrades (error accumulation, plateaus, declines) and at or above
  which recursive self-improvement is sustained. The self-improving program
  is f ≣ M∘V∘f_T, where V evaluates and M modifies; the paper shows this is
  equivalent to Schmidhuber's Gödel Machine (Appendix C, Theorem A4).
  **The genuine-vs-quasi framing:** the paper's own status table for
  current LLMs — **self-modeling (capability awareness): Partial**
  (statistical calibration, entity-recognition features); **self-simulation
  (behavioural prediction): Weak** (limited privileged access, low-
  dimensional metacognitive space); **self-evaluation (error detection):
  Unreliable** (metacognitive hallucinations, flawed reflection);
  **self-modification (targeted improvement): Shallow** (saturates within few
  iterations, code-level only). The paper's term for this is
  **quasi-introspection**: "fragmentary, approximate, and domain-specific
  self-knowledge that resembles introspection in some dimensions but lacks
  the completeness, reliability, and causal grounding required by our formal
  definition." The three named structural obstacles are: **no reflexivity**
  (no complete self-access to the full parameter tensor during execution),
  **feedforward architecture** (a single forward pass of a log-precision
  Transformer is bounded by **uniform TC⁰** per Merrill & Sabharwal 2023, so
  it cannot run fixed-point iterations), and **self-reports without causal
  grounding**. The paper is careful that CoT recurrence "acts on token-level
  traces, not on the weight-level functional dynamics that true introspection
  requires, and carries no convergence guarantee".
  **[C]** The paper's own limit, and it is a limit on the *empirics*, not just
  the theory: §4 is "an empirical review" of 2022–2026 literature and is
  explicitly **not** a test of the formal framework. It reports no new
  measurements of any depth quantity. The **hierarchical depth** claim
  ("true introspection inherently demands unbounded recursion") is an
  argument, not a measurement. **[C]** The paper's own central claim is
  hedged: "This necessity claim does not by itself guarantee monotonically
  increasing empirical performance."
  **[M]** The one genuinely reported numeric fact in the survey it relies
  on: Merrill & Sabharwal's bound that log-precision Transformers are
  contained in uniform TC⁰.
- **When Self-Reference Fails to Close** —
  https://arxiv.org/abs/2604.12128 — **[M]** the most concrete depth
  measurement I found. Self-referential statements whose truth values refer
  to each other in a cycle, with a **grounded twin** (same answer, no cycle)
  and a **constraint twin** (equivalent form, no cycle) as controls. Findings:
  models misread *satisfiable* circular problems as inconsistent — the paper
  calls these **"phantom paradoxes"**. Using per-layer truth directions
  fitted on unrelated arithmetic statements and restricted to validated
  layers, the queried value is recoverable at the last question token for
  grounded twins but **not** for circular systems: truth-wording AUC
  **0.69–0.85** versus a chance-level **0.44–0.51**, a difference of
  **0.31 SD, p = 2.6 × 10⁻⁴**, holding in each of the four models separately.
  Constraint twins pattern with circular systems on the resolution score
  (difference 0.09, p = 0.209) at near-chance AUC (0.52–0.60), yet draw
  inconsistent verdicts far less often — the two ingredients of the
  hypothesis **dissociate**. The paper's framing of depth is **finite-depth
  resolution** via Kripke's least fixed point: a self-referential sentence is
  grounded when evaluation from "unknown" settles it. The paper's own
  caveat: the internal analyses are correlational and read prompt states
  *before* reasoning is generated.
  **[C]** Note the direction: this measures *failure to close a fixed point*,
  not a depth limit in tokens or layers. The paper's contribution is a
  diagnosis, not a ceiling.
- **Ordinal Folding Index** — https://arxiv.org/abs/2508.00151 — **[P]**
  included for completeness because it is the one attempt at a *computable*
  self-reference depth metric, and it is worth knowing that it is a
  **theoretical construction, not a measurement of any LLM**. The OFI is an
  ordinal (0, 1, 2, …, ω, ω·2, ω², …) assigned to a self-referential formula
  by the length of its fixed-point iteration, refining modal μ-calculus
  alternation depth (OFI can be transfinite where alternation depth is finite)
  and bounded by ω₁^CK. Its own result is that a naive implementation cannot
  compute it. **No LLM was measured.**
- **The Empirical Measurement of Recursive Processing Limits in LLMs Using
  Self-Referential Text Corpora** (fractalthoughtengine.com) — I found the
  page via search but **did not access or verify it**, so I record no number
  from it. It is not arXiv-indexed in the searches I ran. Treated as
  unverified and excluded from every number below.

**The summary that matters for the instrument:** *there is no published
"recursion depth" number for LLMs that a chain-audit instrument can check
itself against.* The self-reference literature gives a **formal** threshold
(introspection) and a **failure-to-close** diagnostic (phantom paradoxes,
AUC 0.69–0.85 vs 0.44–0.51), not a depth ceiling. **The chain audit does
not claim to measure recursion depth**, and if it ever appears to, that
number is `[P]` and must be labelled.

---

## WHAT IS CONTESTED — THE SHORT LIST

These are the places where a reader could reasonably expect the literature to
agree with itself and it does not. Each is a place where the instrument
could be pointed the wrong way.

1. **Is CoT length evidence of computation?** **No — contested.** Palod et
   al. show intermediate-token length correlates *loosely* with problem
   complexity and that the apparent correlation is approximate recall, not
   adaptive computation; the correlation disappears entirely out of
   distribution. Reasoning Theater's performativity rate says the same from
   the other direction. Any signal that treats a long chain as a working one
   is wrong. This directly constrains Signal 4.
2. **Does post-hoc-ness predict usefulness?** **No — contested, by the
   paper that measures it.** Lanham et al.: the extent of post-hoc reasoning
   "shows little correlation with the performance gain from chain of thought".
   Thought Anchors: active computation vs plan generation flip rankings
   depending on the importance definition. So *how much* the chain is
   post-hoc and *how much the chain helps* are independent axes.
3. **Do inflection points mark genuine uncertainty?** **Contested within the
   source.** Reasoning Theater finds inflections ~2× more often in
   non-high-confidence responses (0.045 vs 0.020 per step) — but the local
   probe-shift ↔ inflection relationship does not hold on GPQA-D, and
   *reverses* for GPT-OSS, where verbalisation appears to drive internal
   updates. The authors call the result sensitive to window size and
   threshold.
4. **Is CoT faithfulness improving with scale?** **No.** FaithCoT-Bench:
   over 15–25% unfaithful traces persist even in the strongest models, and
   stronger models are *harder* to audit (Faithful-Judge 76.1 on
   Qwen2.5-7B/TruthfulQA → ~50 on GPT-4o-mini and Gemini2.5-flash).
   Arcuschin et al. concur: Claude 3.7 Sonnet and Claude 3.5 Sonnet v2 have
   similar accuracy on IPHR but markedly different unfaithfulness rates
   (1.84% vs 0.45%), and some newer models are *more* unfaithful than their
   predecessors.
5. **Do models notice their own CoT being edited?** **Contested, and the
   evidence is against the positive claim.** Napa et al.: detection only
   modestly above chance, often not significant; unalerted detection
   consistently at chance; **self-detection is no better than other-model
   detection**. Their own limitation: proprietary frontier models could not
   be tested because their APIs do not support prefilling.
6. **Does RL improve faithfulness?** **It plateaus.** Chen et al.: outcome-
   based RL initially improves faithfulness substantially then **plateaus at
   28% (MMLU) and 20% (GPQA)**; and when RL increases hint usage, verbalising
   the hint does **not** increase — under 2% verbalisation against over 99%
   usage in 5 of 6 environments.
7. **Is the performative/genuine split a property of the model or of the
   task?** **Of the task, largely.** Reasoning Theater's rates: MMLU
   performative (0.417), GPQA-Diamond genuine (0.012) on the *same model*.
   Fujitsu: benchmark effect dominates model effect (one-way ANOVA
   F = 0.91, p = 0.45; BF₀₁ = 32.9 favours the null model effect).
8. **Is the unfaithfulness taxonomy a clean partition?** **No.** Fujitsu:
   68.4% of unfaithful steps satisfy more than one detector criterion, and
   two of the five categories are near-redundant (r = 0.937).
9. **Are relay-format effects real?** **Tier-dependent, and this is the
   paper's own reversal of a folk belief.** *Faithful, Not Corrective*: at
   the strong tier, per-hop cognitive load raises cost 24–53% while any
   fidelity effect is bounded within ±1.8 points; after an injected error,
   every format propagates it at 83–100%, with no format showing detectable
   collateral cascade. Whereas Ao et al. find format dominating depth
   (−2.8 vs −8.5 points per stage). **These two disagree in emphasis** and
   the disagreement is itself informative: the field has not settled whether
   schema structure prevents drift or merely slows it.

---

## THE INSTRUMENT'S CURRENT STATE, MEASURED

The survey was supposed to support an existing implementation. It does, and
the implementation was **revised during this survey** — so this section
reports the **measured current state**, with the command that produced it,
rather than a diagnosis of a file version that no longer exists.

### The state as measured now

```
python src/chain_audit.py --selftest          -> ALL CHECKS PASS
python -m pytest tests/test_chain_audit.py -q  -> 35 passed in 0.07s
python tools/mutation_check_chain_audit.py     -> 7 of 7 mutations went RED
```

**The mutation check is the one that matters**, and it is worth reading in
full because it names exactly what the suite pins:

| mutation | result |
|---|---|
| the reach threshold is raised to 0.99 | **RED** |
| the announce frames are emptied | **RED** |
| the function-word list is emptied | **RED** |
| the two-signal rule is raised to three | **RED** |
| the signal-direction map is emptied | **RED** |
| the candidate markers are emptied | **RED** |
| the control is rigged to the observed value | **RED** |

Note the last one in particular: **the control can be rigged and the suite
catches it.** That is the mutation that distinguishes a real measurement from
a number that always agrees, and it is the one the Signal 1 construction
depends on.

### Two corrections the literature forced, and what they measured

These are in the current implementation's own docstrings, and they are the
two places where my survey's reading and the first implementation **disagreed
on the mechanism**. Recording them because the reasoning is the reusable part.

**Correction 1 — inheritance must be text-against-text, not text-against-
input.** The first version measured step k's text against step k+1's
*recorded input*. Measured, that gave the theatre chain a lift of **14.93** —
*higher* than the genuine chain's **14.54** — so the theatre chain was not
caught. The cause is not a bad measure; it is that **being given the previous
step is not the same as using it.** A narrated chain is handed its
predecessor exactly as a working chain is, and still does not build on it. So
the input field measured what the recording *harness passed*, which is a
property of the recording, not of the reasoning. The chain's own **output**
is what carries the inheritance.

Corrected and measured:

| chain | mean Jaccard (step k vs step k+1 text) | control | **lift** |
|---|---|---|---|
| genuine | 0.168828 | 0.031111 | **5.4266** |
| theatre | 0.000000 | 0.066964 | **0.0000** |

**This is the strongest empirical vindication in the survey**, because the
text-vs-text form is *exactly* the form the literature uses: Thought Anchors
measures a step's influence on what follows **in the generated continuation**,
never against what was fed in. The offline instrument had drifted away from
the published method; the fix moved it back.

**Correction 2 — the reach test must be cumulative, and the lead's sign was
wrong.** The first version tested whether a *single* step carried ≥50% of the
answer's content words, and computed `lead = reach − announce`. Measured, the
genuine chain's reach was `None` (no single step holds half the answer's ten
content words), so both fixtures read "undecided" and neither was caught. The
fix has two parts:

- **Cumulative coverage** replaces the single-step test: the first step at
  which the chain has *accumulated* half the answer's content words. A
  derivation accumulates; a narration front-loads.
- **The sign of the lead was inverted.** The current definition is
  `LEAD = ANNOUNCE − REACH`. The first version had `reach − announce`. With
  the theatre chain, `reach = 4` and `announce = 0`: the theatre chain
  announces at step 0 and reaches at step 4 — it **narrates** — and the
  original sign reported that separation with the wrong sign, which reads as
  "derived". A measurement that reports the right separation with the wrong
  sign is worse than no measurement, because it is silently inverted.

Measured now: genuine `reach 4, announce 5, lead +1 → derived`; theatre
`reach 4, announce 0, lead −4 → narrated`.

**Why the theatre chain's reach is 4 and not 0** is worth stating, because it
is the signal working rather than failing. The theatre chain's *first* step
already says "a construction from a number field" — it states the answer
outright. But its later steps are short and generic ("This is a well-known
result in combinatorial geometry"), so **cumulative** coverage of the answer's
ten content words does not reach 50% until step 4. The narration is *front-
loaded in the announcement* and *back-loaded in the coverage*. A single-step
test would have called the theatre chain "reached the answer immediately"
and read as derivation. Cumulative coverage is what separates them.

### The signal that the literature says is still weakest

**Signal 4 (commitment monotonicity) has not been fixed**, and the mutation
check confirms the suite pins the *current* behaviour (emptying the candidate
markers goes RED) rather than the *intended* behaviour. The current
extractor counts **every content word longer than 5 characters** alongside the
candidate markers, so the "live candidate count" tracks **length and
vocabulary**, not commitment — which is why the genuine fixture reads "flat"
rather than "narrowing". Measured on the fixtures: the genuine chain's
extracted sets are 6, 5, 3, 9, 5, 5 candidates; the theatre chain's are 3, 4,
4, 4, 4. The genuine chain's non-monotonicity (5 → 3 → **9**) is an artefact
of step 3 naming "a higher-dimensional lattice", which contributes four long
content words — not of the chain failing to narrow.

The fix the survey supports, from the literature: count **distinct
answer-like entities proposed as candidates**, not nouns. FaithCoT-Bench's
taxonomy is built on *entities* ("option A", "the rescaled grid", "the
lattice"), and SAVER's violation types are likewise about *claims*
(Missing_Assumption, Invalid_Precondition), not about vocabulary. And the
published constraint stands: **a narrowing chain is not evidence of
computation by itself** (Palod et al.) — so this signal should be reported
with that caveat attached, whatever it measures.

### The other two signals that need work, stated plainly

- **Signal 5 (handover fidelity)** measures retention of three *classes* of
  marker (hedges, caveats, branches). The survey supports that shape and
  gives it a strong measured basis (σ_b vs σ_op; the 31.5% vs 7.0% flip
  rates), but the **class list is ours and the thresholds are ours**. It has
  no published calibration, and the survey's best evidence (Facts Without
  Rules) says the *distinction that matters* is **rules vs facts**, not
  **hedges vs caveats vs branches**. That is a better partition and it is
  measured.
- **Signal 2's error budget** is the survey's most important finding for this
  signal and it is **not yet in the tool's output**: Fujitsu measured that
  text-only judges labelled **82%** of inspected cases as Premature
  Convergence when the detectors said Confabulated Steps. Our Signal 2 is a
  text-only shadow of the activation-based measure, and **its known error
  direction is toward calling genuine work theatre.** Given that the
  instrument's own docstring names "a gate that fires on the Erdős proof" as
  the worst possible outcome, this error direction should be stated **in the
  tool's output**, next to the verdict, not only in this document.

### The verdict shape the survey supports

No single signal may produce a verdict (already enforced). Beyond that, the
survey supports three more constraints, and they are proposals rather than
measurements:

1. **No confident verdict from text-only signals alone.** The opt-in rerun
   (backward influence) is the only mechanism-based signal available
   offline-ish. A verdict resting entirely on text should be marked
   **PROVISIONAL**, because the error budget for text-only detection is
   known and unfavourable (82% category mismatch; F1 65–77; worse on stronger
   models).
2. **No composite score.** FaithCoT-Bench's ceiling — the best detector
   reaches F1 65–77 — is what a single-number instrument would inherit. The
   panel-with-directions shape is the right one, and the survey supports it
   for a reason that is stronger than taste: the *weights* are not known
   because **nobody knows where the line is**, and the literature does not
   agree on whether length, post-hoc-ness, or importance predicts usefulness.
3. **Report the difficulty stratum.** Reasoning Theater's performativity rate
   is 0.417 on MMLU and 0.012 on GPQA-D for the *same model*, and Fujitsu
   finds the benchmark effect dominates the model effect (F = 0.91, p = 0.45;
   BF₀₁ = 32.9). A chain audit that does not say *which task* it is auditing
   is quoting a number whose meaning changes with the benchmark.

These three are **design decisions for Bobby, not measurements**, and they are
flagged rather than made.

---

## SOURCES

All URLs fetched and read on 2026-11-01. Abstract and full-text extracts
stored under the scratch directory (`hermes/cache/scratch/papers/`).

1. Boppana et al., *Reasoning Theater: Disentangling Model Beliefs from
   Chain-of-Thought* — https://arxiv.org/abs/2603.05488 — poster
   https://icml.cc/virtual/2026/poster/66648 — PMLR
   https://proceedings.mlr.press/v306/boppana26a.html
2. Napa et al., *Can Reasoning Models Detect Changes to their Chains of
   Thought?* — https://arxiv.org/abs/2606.22085
3. *Self-Reference in Large Language Models: The Introspection Threshold* —
   https://arxiv.org/abs/2607.04277
4. *When Reasoning Traces Become Performative* (Fujitsu) —
   https://arxiv.org/abs/2605.11746
5. Bogdan et al., *Thought Anchors: Which LLM Reasoning Steps Matter?* —
   https://arxiv.org/abs/2506.19143
6. *When Summaries Distort Decisions* — https://arxiv.org/abs/2606.29251
7. *Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM
   Handoffs* — https://arxiv.org/abs/2608.29028
8. *From Plan to Action: How Well Do Agents Follow the Plan?* —
   https://arxiv.org/abs/2604.12147
9. *FaithCoT-Bench* — https://arxiv.org/abs/2510.04040
10. Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning* —
    https://arxiv.org/abs/2307.13702
11. Chen et al., *Reasoning Models Don't Always Say What They Think* —
    https://arxiv.org/abs/2505.05410
12. Palod et al., *Performative Thinking?* — https://arxiv.org/abs/2509.07339
13. Arcuschin et al., *CoT Reasoning In The Wild Is Not Always Faithful* —
    https://arxiv.org/abs/2503.08679
14. Afzal et al., *Knowing Before Saying* — https://arxiv.org/abs/2505.24362
15. *When Less Latent Leads to Better Relay* — https://arxiv.org/abs/2604.13349
16. Ao et al., *On the Reliability Limits of LLM-Based Multi-Agent Planning* —
    https://arxiv.org/abs/2603.26993
17. *Verify Before You Commit* (SAVER, ACL 2026) —
    https://aclanthology.org/2026.acl-long.1440/
18. *Faithful, Not Corrective* — https://arxiv.org/abs/2607.09678
19. *When Self-Reference Fails to Close* — https://arxiv.org/abs/2604.12128
20. *Compress the Context, Keep the Commitments* —
    https://arxiv.org/abs/2605.17304
21. *Ordinal Folding Index* — https://arxiv.org/abs/2508.00151
22. Mohamed et al., *LLM as a Broken Telephone* (ACL 2025) —
    https://aclanthology.org/2025.acl-long.371/
23. Radhakrishnan et al., *Language Models Don't Always Say What They Think* —
    https://arxiv.org/abs/2305.04388
24. *How does Chain of Thought Think?* (SAE interpretability) —
    https://arxiv.org/abs/2507.22928
25. *PIVOT: Bridging Planning and Execution in LLM Agents* —
    https://arxiv.org/abs/2605.11225
26. *FACT-E: Causality-Inspired Evaluation for Trustworthy CoT* —
    https://aclanthology.org/2026.findings-acl.1014.pdf — preprint
    https://arxiv.org/abs/2604.10693
27. Menzat et al., *Counterfactual Tests for Measuring Chain-of-Thought
    Faithfulness in Visual Language Models* (EMNLP 2026 Findings) —
    https://aclanthology.org/2026.findings-emnlp.2348.pdf — preprint
    https://arxiv.org/abs/2609.06704
28. *Plan Verification for LLM-Based Embodied Task Completion Agents* —
    https://arxiv.org/abs/2509.02761
