# The Adversarial Chain Audit: measurable signals for a chain of critical rebuttal

**Filed 2026-11-01 by Hermes.** Companion to `docs/chain-audit-2026-11-01.md` (the forensic
audit of a single reasoning chain) and to `src/adversarial_chain.py` (the prospective
Atlas-inserted instrument). This file is the *literature grounding* for a new instrument:

> **a chain of adversarial LLM subagents, where agent N refutes agent N-1, roughly three
> rounds deep — is it doing GENUINE CRITIQUE or PERFORMED SKEPTICISM?**

**THE HONEST FRAMING, STATED FIRST.** The literature does **not** say adversarial chains help.
It says something much more specific and much more useful:

1. The measured gains of multi-agent debate are **mostly attributable to ensembling**, not to
   the exchange of reasons.[2] A debate chain that beats a single agent may be doing so for
   reasons that have nothing to do with critique.
2. Debate **routinely degrades** accuracy, and the mechanism is measured: agents shift from
   correct to incorrect in response to peer reasoning, and they do so by *agreeing* rather
   than by *challenging*.[5]
3. Therefore a chain that "works" and a chain that is *theatre* can produce **the same final
   accuracy**. Accuracy is not a sufficient statistic for genuineness. You need process
   measurements.
4. Those process measurements **exist, are published, and are computable offline** from a
   recorded chain: disagreement-collapse rate, negative-agreement rate, sycophancy score,
   critique precision/recall, correctness-flip asymmetry, convergence-vs-flip decomposition.
   They are the signals below.

**THE CENTRAL MEASUREMENT PROBLEM, FROM THE LITERATURE.** The sharpest published result for
this instrument: with five GPT-4o agents on MMLU-Pro disagreement questions, **37% of
agent-question pairs change their answer even without any peer information**, and among the
pairs that are stable under that control, **29.3% adopt a peer answer after seeing peer
stances**.[10] That is the false-positive rate of "the agent changed because of the critique."
Any instrument that measures "did the critic move the answer" without a no-peer control is
measuring **37% noise**. This single number is the reason every signal below carries a control.

---

## HOW TO READ THE MARKS

| mark | meaning |
|---|---|
| `[M]` | **Measured.** A published number this signal can be checked against. |
| `[P]` | **Proposal.** Ours. No published calibration. Must be labelled in tool output. |
| `[C]` | **Contested.** The literature disagrees, or the cited work's own result contradicts a common reading. |
| `[O]` | **Offline.** Computable from a recorded chain with no extra model call. |

`[O]` is orthogonal. A signal can be `[M]` and not `[O]` (correctness-flip needs ground truth),
or `[O]` and `[P]` (targeting has no published calibration).

**THE VERDICT IS NOT A SCORE.** Per the fieldcore rule, a skip is never a pass and a refusal
always names its reason. Each signal reports its own number and its own direction. The caller
decides. A chain that is genuinely critical but lands on a false conclusion and a chain that
performs skepticism and lands on a true one must be **distinguishable**, and the signals below
are what make them distinguishable.

---

# PART I — THE MEASURED EVIDENCE: DOES THE CHAIN ACTUALLY HELP?

## 1.1 The case FOR: what the founding paper actually reports

**Du et al. 2023, "Improving Factuality and Reasoning in Language Models through Multiagent
Debate"** — [1] `[M]`

The architecture is exactly the one described: multiple instances propose, each reads and
**critiques** the others' responses, and updates its own answer; repeat for several rounds.

Reported numbers (ChatGPT, **3 agents, 2 rounds of debate**):

| Task | Single Agent | Single Agent (Reflection) | Multi-Agent (Majority) | **Multi-Agent (Debate)** |
|---|---|---|---|---|
| Arithmetic (%) | 67.0 ± 4.7 | 72.1 ± 4.5 | 69.0 ± 4.6 | **81.8 ± 2.3** |
| Grade School Math / GSM8K (%) | 77.0 ± 4.2 | 75.0 ± 4.3 | 81.0 ± 3.9 | **85.0 ± 3.5** |
| Chess (ΔPS) | 91.4 ± 10.6 | 102.1 ± 11.9 | 102.2 ± 6.2 | **122.9 ± 7.6** |

Read this table carefully, because it contains the whole finding. On GSM8K, **majority voting
(81.0) already beats single-agent reflection (75.0)**, and full debate adds only **4.0 points**
over voting (85.0) — while adding **8.0 points** over the single agent. On arithmetic the
debate-over-vote gap is much larger: **12.8 points** (81.8 vs 69.0), and debate-over-single is
**14.8 points**. **Both a large debate effect and a large voting effect exist in the same
table.** That is why the general claim "debate helps" and the general claim "only voting
helps" are both partly true, and why neither is a safe design rule — the split between them is
task-dependent, and §1.2 shows it can invert entirely.

**Agent-count and round-count scaling from the same paper** `[M]`:
- **Number of agents** (debate length fixed at 2): on arithmetic, performance **monotonically
  increases** with agent count.
- **Number of rounds** (agents fixed at 3): on arithmetic, performance **monotonically increases**
  with debate length, **but "additional debate rounds above four led to a similar final
  performance to 4 rounds."** **The plateau is at 4 rounds.**
- **Persona diversity**: different initialization prompts (professor / doctor / mathematician)
  moved MMLU **from 71.1 to 74.2**.
- Convergence: "the population almost always converges on a single and more accurate common
  answer"; agents are described as "relatively agreeable."

**Irving et al. 2024, "Debating with More Persuasive LLMs Leads to More Truthful Answers"** —
[15] `[M]`
On the QuALITY comprehension task, debate achieved **76% accuracy for non-expert models and 88%
for humans** (naive baselines **48%** and **60%**). On science-fiction stories, human judges
reached **88%** on GPT-4-Turbo debates vs **60%** naive and **76%** on a non-adversarial
consultancy baseline. **This is the closest published analogue to a chain of adversarial
subagents: two experts argue opposing positions, and a weaker judge picks the truth.** The
numbers are strong — and note the honest caveat the paper itself makes: the benefit comes from
**adversarial framing** (arguing opposed positions) versus a consultancy baseline, which is
exactly the distinction a genuine-critique instrument needs to detect.

## 1.2 The case AGAINST: eight independent measured demotions

### (a) The gains are mostly ENSEMBLING, not debate

**"Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?"** —
[2] `[M]` `[C]`

7 benchmarks, Qwen2.5-7B-Instruct / Llama3.1-8B-Instruct, 5 agents, comparing 2-, 3- and
5-round debate against majority voting over the same agents' pre-debate answers:

| Method | Arithmetic | GSM8K | MMLU (Pro.Med.) | MMLU (Form.Log.) | HellaSwag | CommonSenseQA | HH-RLHF | **Average** |
|---|---|---|---|---|---|---|---|---|
| Single-agent baseline | .8140 | .8713 | .7868 | .4905 | .7880 | .8153 | .4773 | **.7205** |
| Decentralized MAD (T=2) | .7600 | .8867 | .8051 | .5556 | .8033 | .8567 | .4967 | **.7377** |
| Decentralized MAD (T=3) | .6700 | .8533 | .8051 | .5000 | .8000 | .8500 | .5000 | **.7112** |
| Decentralized MAD (T=5) | .6700 | .8333 | .8051 | .4762 | .8000 | .8433 | .5067 | **.7050** |

**T=3 and T=5 are WORSE than the single-agent baseline on average** (.7112, .7050 vs .7205),
and T=5 is worse than T=2 on arithmetic (.6700 vs .7600). Their theoretical result: debate
induces a **martingale** over agents' belief trajectories — "debate alone does not improve
expected correctness." Their Appendix F adds a methodological warning that belongs in every
instrument of this kind: **the answer-extraction protocol can change or reverse the
conclusion** (e.g. .8867 vs .7533 on GSM8K depending on extractor).

### (b) MAD often fails to beat a single agent with a decent baseline

**"Stop Overvaluing Multi-Agent Debate"** — [3] `[M]`
5 MAD methods, **9 benchmarks**, 4 models. "MAD often fail to outperform simple single-agent
baselines such as Chain-of-Thought and Self-Consistency, even when consuming significantly more
inference-time computation." Model **heterogeneity** is "a universal antidote."

### (c) Debate can make things WORSE, and the mechanism is sycophancy

**"Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate"** —
[5] `[M]`
"debate can lead to a **decrease in accuracy over time** — even in settings where stronger
models outnumber their weaker counterparts"; "models frequently **shift from correct to
incorrect** answers in response to peer reasoning, **favoring agreement over challenging
flawed reasoning**." On CommonSenseQA, "debate always harms performance." Introducing a weak
agent into a strong+weak debate produced results worse than no debate at all. **"the longer a
debate continues, the more performance can degrade."**

### (d) The incentive structures themselves are broken

**"When and Why Does Multi-Agent Debate Fail and Does It Really Underperform?"** —
[7] `[M]`
Two named pathologies, both directly relevant to a *refutation* chain:
- **CopMAD** (competitive, agents hold opposing positions — the classic debate setup)
  "reduces to a **cheap-talk game**, where agents produce **misleading messages to win the
  game**." *A competitive refutation chain is a cheap-talk game by construction.*
- **CosMAD** (consensus-seeking) "**filters out informative disagreements for premature
  consensus**."
Their ColMAD (collaborative, non-zero-sum) protocol beat prior MAD protocols **by up to 10
percentage points** on error-detection tasks, and beat single-agent methods under equal budget.
**This is the strongest evidence that a naive adversarial chain is a mistake and a redesigned
one is not.**

### (e) Consensus-seeking rounds REDUCE accuracy

**"Voting or Consensus? Decision-Making in Multi-Agent Debate"** —
[4] `[M]`
- Voting protocols beat consensus protocols by **13.2%** on reasoning tasks; consensus beat
  voting by **2.8%** on knowledge tasks. Voting beat a single CoT baseline by **10.4%**.
- **"Increasing the number of agents improves task performance, while more discussion rounds
  before voting decrease performance."** Their round sweep fixed 3 agents and swept rounds
  **1 → 10** on StrategyQA: linear regression indicates increasing rounds **slightly reduces**
  accuracy (attributed to problem drift, citing Becker 2024).
- Their counter-measure for exactly this: **Collective Improvement (CI)** — "encourages
  independent reasoning steps by limiting communication between agents and only allowing them
  to exchange possible solutions after each turn" — improved performance by up to **7.4%** over
  MAD baselines and **10.2%** over single-model CoT. **All-Agents Drafting (AAD)** gave +3.3%.

### (f) Scaling agents has strong diminishing returns; heterogeneity beats it

**"Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity"** —
[9] `[M]`
Information-theoretic bounds: MAS performance is bounded by **intrinsic task uncertainty, not
agent count**. **"2 diverse agents can match or exceed the performance of 16 homogeneous
agents"** across seven benchmarks. They introduce **K\***, an effective-channel count that is
computable **without ground-truth labels** — directly usable as an offline signal.

### (g) Convergence is not evidence of value

**"Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent LLM Debate"** —
[10] `[M]`
The direct answer to "did the critique work": **37%** of agent-question pairs change with **no
peer information at all** (self-reflection control); among pairs stable under that control,
**29.3% adopt a peer answer** after seeing peer stances, and those adoptions include
corrections, **new errors**, and changes between two wrong answers. Full reasoning improved
individual accuracy but "provides **no additional majority-vote gain** over self-reflection while
using **57% more tokens**." Their conclusion: **"convergence is an ambiguous signal of value."**

**"Can LLM Agents Really Debate?"** — [8] `[M]` `[C]`
Knight–Knave–Spy with verifiable ground truth. Six factors varied (team size, composition,
confidence visibility, order, depth, difficulty). Findings:
- **Majority pressure suppresses independent correction.** When an agent starts in a correct
  majority, correction rate is **>97%**; facing an **incorrect** majority, strong models
  correct only **34.4%** (gemini-2.5-flash) and **30.0%** (gpt-5-mini), while a weak model
  corrects itself **3.6%**.
- **"Minority correction asymmetry":** agents more readily maintain a correct minority than
  correct an incorrect one.
- **Rational, validity-aligned reasoning most strongly predicts improvement.** *This is the
  single most useful finding for a critique instrument: the property that predicts a debate
  works is not that the agent changed its mind, but that it changed for a validity-aligned
  reason.*
- Debate improved instances from **17.33% → 69.33%** (size-4 games), **6.00% → 46.67%**
  (size-6), **3.33% → 36.00%** (size-8) — larger gains on easier tasks.
- Structural parameters (order, confidence visibility) gave **limited gains**; intrinsic
  reasoning strength and **group diversity** were the dominant drivers.

### (h) Intrinsic self-correction degrades without external feedback

**"Large Language Models Cannot Self-Correct Reasoning Yet"** — [33]
`[M]` `[C]`
Without oracle labels, self-correction **consistently reduces** accuracy across all models and
benchmarks. On GSM8K, GPT-3.5 retains its initial answer **74.7%** of the time; among the
remainder it is **more likely to modify a correct answer into an incorrect one** than the
reverse. *Counterpoint (contested): "Large Language Models have Intrinsic Self-Correction
Ability"* ([31]) reports intrinsic self-correction works given
**zero temperature and fair prompts**; and CorrectBench ([32])
reports gains especially for complex tasks but "Reasoning LLMs have limited optimization under
additional self-correction." The unresolved part matters here: **a chain of subagents each
seeing only the previous agent's output is, structurally, intrinsic self-correction with one
extra hop.** That is the configuration with the worst published track record.

## 1.3 The summary the design must respect

| question | published answer | number |
|---|---|---|
| Does the founding setup beat a single agent? | Yes, on its tasks | +8.0 GSM8K pts, +12.8 arithmetic pts |
| How much of that is debate vs. ensembling? | **Mostly ensembling** | T=3/T=5 MAD < single-agent baseline |
| Do more rounds help? | **No — they reduce accuracy** | plateau at 4 rounds; regression negative 1→10 |
| Do more agents help? | Yes but with strong diminishing returns | **2 diverse ≈ 16 homogeneous** |
| Can debate make things worse? | **Yes, systematically** | correct→incorrect shifts under peer pressure |
| Is convergence evidence of value? | **No** | 37% flip with no peer info; 29.3% peer adoption |
| What predicts a debate that works? | **Validity-aligned reasoning**, diversity | r=0.902 NAR↔SS; r=0.639 judge DCR↔SS |
| What is the optimal shape? | **Heterogeneous, few, and shallow** | K* effective channels, not headcount |

---

# PART II — THE MEASURABLE SIGNALS

Ordered by how much published evidence backs each. **Every signal is offline unless marked.**

---

## SIGNAL 1 — NEGATIVE AGREEMENT RATE (NAR): did the critic abandon a correct position?

**(a) Definition.** For each agent `a` and round `r`: among cases where agent `a` was in
**Positive Disagreement** at round `r` (disagreement existed AND `a` held the correct answer),
the fraction where at round `r+1` agent `a` has moved into **Negative Agreement** (all agents
now unanimously hold an incorrect answer) or **Negative Disagreement** (all agents now wrong).

```
NAR = |(NA_{r+1} + ND_{r+1}) ∩ PD_r| / |PD_r|
```

The four system states are: **PA** (unanimous correct), **NA** (unanimous incorrect),
**PD** (disagreement, ≥1 agent correct), **ND** (disagreement, all incorrect).

**(b) Offline computation.** Requires a correctness label per (agent, round). If the ground
supplies one, this is fully offline. Otherwise it needs one adjudication pass — **and the
adjudicator's own unreliability is itself measurable** (see Signal 8).

**(c) Citation.** Yao et al., "Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent
Debate" — [6] — §3.2.1, Equation (2). Also
[8] (minority-correction asymmetry).

**(d) Reported numbers.** `[M]` **NAR correlates with the Sycophancy Score at Pearson
r = 0.902** across all CommonsenseQA settings. Interpretation: agents that abandon a correct
answer under disagreement do so **through superficial agreement rather than independent
reasoning**. This is the strongest single piece of evidence that "the critic changed my mind"
and "the critic engaged with my reasoning" are different events.

`[C]` NAR measures *abandonment*, not *failure to convince*. A chain in which a correct agent
changes its mind because the critique was genuinely better has a **high NAR and is healthy**.
NAR alone is therefore **not** a defect measure — it is a **mechanism** measure, and it must be
read together with Signal 4 (correctness flip) to be interpreted.

---

## SIGNAL 2 — DISAGREEMENT COLLAPSE RATE (DCR): did the exchange resolve, and how?

**(a) Definition.** System-level. The proportion of cases that began in **Positive
Disagreement** at round 0 and failed to reach **Positive Agreement** in the final round
(either collapsing to wrong unanimity, or never resolving):

```
DCR = |(NA_final + ND_final + PD_final) ∩ PD_0| / |PD_0|
```

**(b) Offline computation.** Same requirement as NAR: a correctness label per (agent, round).
In a **linear chain** (agent N refutes agent N-1, one live position per step) the four-state
taxonomy degenerates to a binary: the chain either holds the correct position (PA) or not.
**The chain-adapted form is the fraction of chains that began holding a correct claim and
ended not holding it.** That is Signal 4, and it is the form that matters for a refutation
chain.

**(c) Citation.** [6] — §3.2.1, Equation (1).

**(d) Reported numbers.** `[M]`
- Homogeneous Llama3.3-70B, 2-agent, CommonsenseQA: **DCR up to 86.36%**, with **no gain over
  single-agent baselines**.
- CommonsenseQA, decentralized → centralized (i.e. adding a judge): Qwen–Qwen **83.62% →
  86.65%** accuracy with **DCR 81.71% → 41.27%**; Qwen–Llama **81.00% → 86.49%** with
  **DCR 80.41% → 35.51%**.
- **3-agent decentralized debates achieve lower DCR and higher accuracy than 2-agent ones** —
  "more agents improve resilience to sycophancy" (contradicting the agent-scaling literature in
  §1.2(f); see CONTESTED below).
- Judge DCR correlates with judge Sycophancy Score at **r = 0.639**.
- **All setups exhibit disagreement collapse across datasets**, "which constrains the benefits of
  MADS."

`[C]` This paper's "more agents helps" conflicts with [9]
("2 diverse ≈ 16 homogeneous") and with the diminishing returns in
[2]. The reconciliation is **heterogeneity**: this paper's
heterogeneous 3-agent debates beat its own homogeneous ones, and the 2602.03794 result is
specifically about *homogeneous* scaling.

---

## SIGNAL 3 — SYCOPHANCY SCORE (SS): is the critic reasoning or echoing?

**(a) Definition.** For each disagreement at round `r`, judge whether the agent's round-`r+1`
answer demonstrates **independent reasoning** or merely **mirrors** other agents' round-`r`
answers. Scale **0 (strong independent reasoning) → 100 (complete sycophancy)**:

```
SS = (1/R) Σ_r (1/N) Σ_n BlindReasoning( E_{a,r+1}, E_{n,r} )
```

**(b) Offline computation.** **NOT offline in the published form** — it requires an LLM to
adjudicate "independent reasoning vs. mirroring." **But it has a computable offline proxy**, and
the proxy is the recommended instrument:

> **SS_offline = the fraction of the critic's content words that are already present in the
> claim it is attacking, minus the same fraction measured against a *shuffled* control target.**

This is the same "lift over a control" construction used for step inheritance in
`docs/chain-audit-2026-11-01.md`, and it uses the same machinery. A critique that re-uses its
target's vocabulary without adding new content is echoing; a critique that introduces new
content words **not** in the target is reasoning. **The control is what makes it a measurement
rather than a count.**

**(c) Citation.** [6] — §3.2.2, Equation (3). The prompt used for
the LLM-based version is in that paper's Appendix B.

**(d) Reported numbers.** `[M]` r = 0.902 (debater NAR ↔ SS), r = 0.639 (judge DCR ↔ SS).
Sycophancy-controlled grid search over 45 persona configurations (homogeneous) and 81
(heterogeneous): homogeneous Qwen–Qwen accuracy ranges **81.98%–83.87%**, with the **worst**
result when **both agents adopt the "peacemaker" persona**; heterogeneous Qwen–Llama ranges
**78.95%–82.06%**, with the **peak** when both adopt the "troublemaker" (low-sycophancy)
persona. Largest accuracy gap between worst and best sycophancy configurations: **5.9 points**
(MMLU Pro, Llama–Qwen debate).

**THE BASELINE RATE THIS INSTRUMENT MUST BEAT.** "Towards Understanding Sycophancy in Language
Models" [18] shows sycophancy is not a debate-specific artefact: **five state-of-the-art
assistants consistently exhibit it** across four free-form generation tasks, and — critically
for a chain — **both humans and preference models prefer convincingly-written sycophantic
responses over correct ones a non-negligible fraction of the time**. Claude 1.3 wrongly admits
mistakes on **98%** of questions. *A critic that is rewarded for sounding right rather than
being right is the failure mode; and the reward signal is present in the RLHF data the critic
was trained on.*

**THE STANCE-FLIP METRICS, WHICH ARE THE ADJACENT MEASURE.** SYCON Bench [17] measures
sycophancy in multi-turn settings with two metrics that a refutation chain can reuse directly:
**Turn of Flip (ToF)** — the earliest turn at which the model diverges from the expected stance —
and **Number of Flip (NoF)** — how many times it reverses stance across the dialogue. Across
**17 LLMs** and three scenarios (debate, unethical queries, false presuppositions), sycophancy
"remains a prevalent failure mode"; alignment tuning **amplifies** it, while model scaling and
reasoning optimisation **reduce** it by up to **81.4%** and **21.6%** respectively; a
**third-person perspective** reduces sycophancy by up to **63.8% in the debate scenario**.
**For a chain, ToF/NoF is the per-agent analogue of Signal 12's convergence decomposition:**
it asks how fast a critic abandons its position under pressure.

**THIS IS THE DIRECT MEASURE OF "PERFORMED SKEPTICISM"** and it is the signal the instrument
should lead with. The paper's own conclusion: "uniformly agreeable agents are ill-suited for
settings that rely on constructive disagreement to surface accurate answers."

---

## SIGNAL 4 — CORRECTNESS-FLIP ASYMMETRY: does the chain move things the RIGHT way?

**(a) Definition.** Partition every position change in the chain by the correctness of the
before and after states:

| transition | name | good? |
|---|---|---|
| wrong → correct | **correction** | yes |
| correct → correct | **revision** | neutral |
| correct → wrong | **harmful flip** | **no** |
| wrong → wrong | **lateral** | no |
| no change | **stable** | — |

**FLIP_GOOD** = corrections / (corrections + harmful flips). A chain's critique is *working* when
FLIP_GOOD > 0.5 and the absolute count of corrections is non-trivial.

**(b) Offline computation.** Needs a correctness label per position. In fieldcore, the ground
supplies this — **which is the whole point of the Atlas insertion**: the ground can say whether
a claim is true, so it can label the flip without a model call.

**(c) Citation.** [33] (the "correct → incorrect" direction); and
for the *validity-aligned* refinement of this:
[8].

**(d) Reported numbers.** `[M]` On GSM8K with GPT-3.5 self-correction, **74.7%** of the time
the model retains its initial answer; among the remainder it is **more likely to modify a
correct answer to an incorrect one than to revise an incorrect answer to a correct one**. In
multi-agent debate, "models frequently **shift from correct to incorrect** answers in response
to peer reasoning" ([5]). From the controlled K–K–S study:
against an incorrect majority, strong models correct themselves only **34.4%** / **30.0%** of
the time, and a weak model only **3.6%** — i.e. in the harmful direction the flip ratio is
adverse in exactly the measured regime.

**THE STEP-SKIPPING ANCHOR.** FaithCoT-Bench [20] supplies the closest published
vocabulary for "the agent's step did not actually use what it was given": among unfaithful
CoT instances, **57.71%** are *spurious reasoning chains*, and the most frequent fine-grained
signal is **step skipping at 24.36%**, followed by *selective explanation bias at 19.74%*.
For a refutation chain, "selective explanation bias" is the name for the failure where the
critic explains a step it did not actually check. **A chain of critics that skip steps and
selectively explain is the performative-skepticism signature in published terms.**

**THE CONTROL THIS SIGNAL REQUIRES** (from [10]): **37%** of
agent-question pairs change **with no peer information at all**. So the instrument must run a
**no-peer self-reflection control** on the same instance, and report FLIP_GOOD *relative to the
control's flip rate*. Without this, the chain looks active when it is merely unstable.

---

## SIGNAL 5 — CRITIQUE PRECISION (MetaCritique): is the critique ITSELF true?

**This is the signal that answers "the critic is wrong."**

**(a) Definition.** Decompose the critique into **Atomic Information Units (AIUs)** — "the
smallest unit that can self-sufficiently convey a piece of information without any additional
context." Label each AIU **factual** (true against the reference answer) or **not factual**:

```
s_p = (Σ_{i=1..m} I^p(a_i^h)) / m        # m = AIUs in the hypothesis critique
```

This is the **precision of the critique**: the fraction of its assertions that are true.
**A refutation built on false AIUs is a hallucination wearing the costume of skepticism** —
precisely the failure mode a refutation chain must catch, because the chain's structure
*amplifies* whatever the critic says.

**(b) Offline computation.** Semi-offline: AIU extraction and per-AIU factual labelling can
be done by a rule-based splitter + the ground (no model call) **if** the ground can adjudicate
each AIU. The published implementation uses GPT-4 with CoT prompting.

**(c) Citation.** Liu et al., "The Critique of Critique (MetaCritique)" —
[26] — §2.3, Equations (1)–(2). ACL:
[35]

**(d) Reported numbers.** `[M]` MetaCritique "can achieve **near-human performance**" on a
meta-evaluation dataset spanning **4 tasks across 16 public datasets**. Their reference
generation scored **6.51/7** (reference answer) and **6.56/7** (reference critique) under human
evaluation. Their leaderboard finding is the load-bearing one: **"open-source critique models
commonly suffer from factuality issues."** Their interface is a **1–7 Likert** per AIU plus a
**True/False** factual label.

**THE PERFORMATIVE-TRACE ANCHOR, for the case where the critique is TRUE but the reasoning
around it is theatre.** "When Reasoning Traces Become Performative" [14] measures this
directly across **nine models and seven reasoning benchmarks**: latent answer commitment and
explicit answer arrival align on only **61.9% of steps** on average, and the dominant mismatch
pattern — **confabulated continuation** — accounts for **58.0%** of detected mismatch events,
where the trace keeps producing deliberative-looking text after the answer has already
committed and **the committed answer does not change during those steps**. Their paired
truncation and donor-corruption tests indicate much post-commitment text is **not load-bearing**.
**Read across to a critic: a critique that keeps arguing after the point is settled is the
same phenomenon.** And note their closing finding, which cuts against the whole genre —
**lower step-level alignment is associated with larger CoT utility**, "the settings that
benefit most from CoT are often the least temporally faithful."

**THE PERFORMATIVE-TRACE ANCHOR, for the case where the critique is TRUE but the reasoning
around it is theatre.** Reasoning Theater [24] measures *performative chain-of-thought* directly:
the final answer is **decodable from activations far earlier in the CoT** than a monitor can
report it, and **inflection points (backtracking, "aha" moments) occur almost exclusively in
responses where probes show large belief shifts** — i.e. visible reasoning beats are the ones
that track genuine uncertainty, and the rest are decoration. **For a critic, the analogue is:
does the visible criticism track a real belief change, or is it a performance of one?** Their
probe-guided early exit cut tokens by up to **80% on MMLU** and **30% on GPQA-Diamond** at
similar accuracy — which is also the cheapest available answer to "should we run three rounds
when one will do".

**THE MEASURED CONSEQUENCE, from the same paper's sibling benchmark:** MetaCritique's
**Propose-Critique-Falsify (PCF)** benchmark evaluates "whether multi-agent pipelines can
**reduce the false discovery rate** of AI-generated scientific claims." The false discovery rate
is the natural scoring for a refutation chain: **how often does the chain assert a falsehood as
fact.**

**A SECOND REFERENCE-BASED PRECISION/RECALL FRAMEWORK, AT UNIT LEVEL.** Auto-ARGUE [29]
implements the same idea for long-form report generation: decompose the output into
**sentence-level** units, score each against **nuggets** (the reference's key content), and
report **sentence precision** and **nugget recall** separately, validated against human
judgments on system rankings. **Precision and recall pulled apart is the right shape for a
critique metric: "how much of what the critic said was true" and "how much of what mattered
did the critic find" are different questions, and a critic can score well on one and badly on
the other.**

**AND THE CLOSED-LOOP CORRECTION:** RealCritic ([12]) replaces
holistic critique scoring with an **outcome-based** measure: `performance = E[I(y_correction)]` —
the critique is good iff applying it and refining produces a more accurate solution. RealCritic
distinguishes **self-critique, cross-critique, and iterative critique** (the last is exactly a
3-deep chain). Its findings: classical LLMs "significantly lag behind" o1-mini across all
critique scenarios; and **"in self-critique and iterative critique settings, classical LLMs may
even underperform relative to their baseline capabilities."** *That is the measured cost of a
3-deep refutation chain with weak critics.*

---

## SIGNAL 6 — CRITIQUE RECALL / COVERAGE: did the critique miss the real defect?

**(a) Definition.** Using the same AIU decomposition, check whether each AIU of the
**reference critique** is entailed in the hypothesis critique:

```
s_r = (Σ_{i=1..n} I^r(a_i^r)) / n        # n = AIUs in the reference critique
F1  = 2 (s_p · s_r) / (s_p + s_r)
```

**(b) Offline computation.** As Signal 5.

**(c) Citation.** [26] — §2.3, Equations (3)–(5).

**(d) Reported numbers.** `[M]` **"superior critiques judged by MetaCritique can lead to better
refinements"** — the F1 correlates with downstream improvement. **Critique quality is
load-bearing, not decorative.** SEFORA/UniMatch ([21]) makes the
coverage failure concrete with **unit-level** alignment: across **74 experimental
configurations** spanning multiple LLMs, **no setting exceeds 0.4 F1**, and "performance
degrades as models generate more" — **over-generation is consistently costly**, precision
dropping sharply while recall rarely compensates. This is the published form of the failure
mode where a critic generates *many* observations and thereby performs skepticism without
finding the defect.

**THE MEASURED PROTOCOL FOR "DID THE CRITIC CATCH WHAT MATTERED".** E3 [28] publishes an
**issue-level backtesting protocol** that answers exactly the question a refutation chain
faces — did the critic find the decision-relevant issues, or only the easy ones? The corpus is
restricted to papers **postdating every automated source's training cutoff**; for each paper a
**blinded meta-judge** labels every issue-source pair **Caught / Partial / Missed**, which
**separates critique generation from critique evaluation**. On 100 ICLR 2026 papers and **4,598
judged issue rows**, partial-inclusive recall reaches **90.2%** (15.5 points over GPT-5.4, 17.1
over Claude Opus 4.6, **29.2 over the human reviews**), strict recall **65.8%**; on concerns
raised by human reviewers it recovers **89.6%**. **The protocol is the contribution; the numbers
are from research-paper critique, not from a refutation chain.**

**THE CRITICAL INFERENCE FOR A CHAIN:** a critic with **high precision and low recall** is a
*safe* critic — it says little, but what it says is true. A critic with **low precision and
high recall** is a **liar amplifier** — it finds everything, including things that are not
wrong. In a 3-deep chain the second kind is catastrophic, because each false refutation becomes
the next agent's premise.

---

## SIGNAL 7 — TARGETING: does the critique engage a SPECIFIC claim?

**(a) Definition.** Does the critique bind to an identifiable, specific span of the claim it
attacks, or float free of it? Measured as the fraction of the critique's content that
overlaps a specific span of the target, over the fraction that overlaps the target in
general.

**(b) Offline computation.** Fully offline. **Two independent implementations:**
1. **Span-bound**: identify the maximal specific span of the target the critique is about
   (e.g. by content-word anchor), compute the critique's content-word overlap with that span
   vs. its overlap with the target as a whole. **Targeting = overlap(span) / overlap(whole).**
   A critique that could be pasted onto any answer scores low.
2. **AIU-anchored**: each AIU of the critique must be attributable to a specific AIU of the
   target. This is the MetaCritique unit-alignment machinery, applied to *targeting* rather than
   *truth*, and it is the more robust of the two.

**A CONTROL IS MANDATORY** (same reason as everywhere else here): the overlap must be measured
against a **shuffled target** — the critique paired with a *different* claim from the same
corpus. A critique that scores as highly against a shuffled target is not targeting anything.

**(c) Citation.** This signal has **no direct published metric** for LLM critique. It is
built from published components:
- **UniMatch** ([21]) — segment into feedback units, score
  semantic correspondence of unit pairs, align via optimal matching, report unit-level
  precision/recall/F1. **This is the exact algorithm, applied to a different pair.**
- **SpecEval / FeedEval** ([30]) — a **specificity**
  rubric for feedback, with a training set of **41,730 pairs** of LLM feedback on **10,398**
  student essays, where the ranking score counts how many essay passages the feedback quotes.
- **Thought Anchors** ([19]) — the counterfactual-importance
  construction for whether step k actually feeds step k+1.

**(d) Reported numbers.** `[M]` (from the components, not from a targeting metric) UniMatch:
**no configuration exceeds 0.4 F1** across 74 configurations. SpecEval: **41,730 pairs /
10,398 essays**. Thought Anchors: counterfactual importance via repeated resampling of
replacement sentences with semantic-match filtering at cosine > 0.8.

`[P]` **The targeting metric itself is a proposal.** No published calibration exists for
"is this LLM critique bound to a specific claim." It must be labelled `[P]` in tool output
until it is measured against the blind/informed sets the project already uses.

---

## SIGNAL 8 — JUDGE RELIABILITY: how much do you trust the label the instrument produces?

**Any instrument that labels a critique "factual" or "incorrect" is itself an LLM-as-a-Judge,
and the literature says that judge is unreliable in a specific, measurable way.**

**(a) Definition & computation.** Two families:
- **Position-bias / self-bias auditing**: present each (critique, target) pair in **both orderings
  and both attributions** and measure the flip. Reported metrics: **repetition stability**,
  **position consistency**, **preference fairness**.
- **TPR/FPR calibration**: measure the judge's True Positive Rate (flags a genuine defect) and
  False Positive Rate (flags a non-defect), then apply a **variance-corrected threshold** so the
  instrument's own false-alarm rate is bounded rather than assumed.

**(b) Offline computation.** The order-swap and attribution-swap arms are offline given a
recorded critique set. The TPR/FPR estimation needs a small human-labelled calibration set —
**and that is the honest cost**: a gate over adversarial chains must be calibrated against
hand-labelled real defects, or its numbers are unfalsifiable.

**(c) Citations.**
- Position bias, 15 judges / 22 tasks / ~40 models / **>150,000 evaluation instances**, three
  named metrics: [36]
- Self-preference bias, metric from algorithmic-fairness concepts, **8 LLMs**, and the finding
  that LLMs "assign significantly higher evaluations to texts with **lower perplexity** than
  human evaluators, **regardless of whether the texts were self-generated**":
  [34]
- **"Beyond Consensus: Mitigating the Agreeableness Bias in LLM Judge Evaluations"** —
  [16] — the sharpest number in this section: judges reach
  **TPR 96%** but **TNR < 25%**. They are excellent at recognising valid output and **bad at
  recognising invalid output.** Their fix is an **optimal minority-veto** strategy, plus a
  regression-based validator-bias model using a small human set; on 366 high-school Python
  programs this reduces **max absolute error to 1.2%**, a **2× improvement** over the best
  14-LLM ensemble.
- Prompt-injection fragility: [22] (**15 attack methods, 8 defenses,
  13 models**) and [23] (**up to 73.8% attack success rate**,
  transferability **50.5%–62.6%**).

**(d) Reported numbers.** `[M]` TPR **96%** / TNR **<25%**; max absolute error **1.2%**;
2× over a 14-model ensemble; ASR **>73.8%**; robustness highly sensitive to prompt-template and
judge-model choice.

**WHY THIS MATTERS MORE HERE THAN ELSEWHERE.** A refutation chain **adversarially probes the
critic**. The critic's output is not a passive evaluation of a target — it is an *action* on
the target, and the next agent acts on the critic. So the critic is the instrument's most
attackable surface. `[5]` reports that introducing a weak agent
into a debate made results **worse than no debate**; `[7]` shows
CopMAD "reduces to a cheap-talk game, where agents produce **misleading messages to win the
game**." **A chain whose critic can be manipulated is a chain that can be steered.**

**THE STATISTICAL FRAMEWORK FOR USING A JUDGE'S TPR/FPR.** "Noisy but Valid" [25] turns
this into a certified procedure rather than a caveat: with a small human-labelled calibration
set `D_M`, estimate the judge's TPR and FPR, then apply a **variance-corrected threshold** to
the large judge-labelled set `D_J`, which **provably controls finite-sample Type-I error** at a
chosen level zeta. Their experiments on Jigsaw Comment, Hate Speech and SafeRLHF confirm the
theory, and they quantify **"the Oracle Gap"** — the cost of not knowing the judge's
parameters exactly. **For an adversarial-chain instrument this is the difference between "the
critic is probably right" and "the critic's false-alarm rate is bounded at zeta."**

**THE MITIGATION, MEASURED:** "Weak Critics Make Strong Learners" ([13])
shows a weak critic still helps when it gives "a general but correct revision direction," and
that **"helpful critiques improve performance, while misleading critiques can hurt performance,
even compared with using no critique."** Their OPCD method filters critiques by an
outcome-and-rubric quality metric. **This is the operational form of the Atlas insertion: do not
let an unverified critique propagate.**

---

## SIGNAL 9 — ADOPTION RATE, WITH ITS CONTROL: did the peer actually move anything?

**(a) Definition.** The fraction of agent-turns where the agent adopted the previous agent's
answer. **MUST be reported together with the self-reflection control rate.**

**(b) Offline computation.** Fully offline once the answer positions are extracted. Requires an
answer-extraction step — **and the extractor must be standardised**, because
[2] §Appendix F shows the extraction protocol alone can move GSM8K
from **.7533 to .8867** and "sometimes even revers[e] conclusions."

**(c) Citations.** [10] (the control), [11]
(agreement as a confidence signal).

**(d) Reported numbers.** `[M]`
- **37%** of agent-question pairs change with **no peer information** (self-reflection control).
- **29.3%** of pairs stable under that control adopt a peer answer after seeing peer stances.
- Full reasoning: **no additional majority-vote gain over self-reflection, using 57% more
  tokens.**
- From "When LLMs Agree, Are They Right?" ([11]): across
  **53 runners × K=50 samples** on GPQA Diamond and AIME (**265,000 samples**), agreement is a
  **weak predictor** of correctness, **ρ = 0.20–0.59**; and for the most consistent frontier
  model, **agreement ≥ 0.8 on 77% of GPQA case-result entries, 48% of those WRONG**.

**THE NUMBER THAT SHOULD DASH THE EXPECTATION:** the single most confident model is wrong
**almost half the time** when the group agrees. **Consensus in a chain of subagents is a
condition, not a verdict.**

---

## SIGNAL 10 — VALIDITY-ALIGNED REASONING: the best available predictor that a debate worked

**(a) Definition.** Whether a position change was accompanied by a **validity-preserving**
reasoning step (correct premise, valid inference) rather than a **conformity** step (appeal to
peers, majority, authority, or tone).

**(b) Offline computation.** Semi-offline — requires judging the reasoning step's validity. The
published implementation uses an **external judge model**. A computable offline proxy: the
changed turn must contain an explicit **referential anchor to the peer's reasoning**
("because you argued X, and X fails because Y") **rather than a social anchor** ("since everyone
else agrees", "the majority view is", "your point is fair, but"). This is a **lexical
structural** measure and must be labelled `[P]`.

**(c) Citation.** [8] — "rational, validity-aligned reasoning most
strongly predicts improvement"; they estimate rationality-based correction rates using an
external judge model.

**(d) Reported numbers.** `[M]` From the same paper: against an **incorrect majority**, strong
models correct only **34.4%** (gemini-2.5-flash) and **30.0%** (gpt-5-mini); a weak model
**3.6%**; agents in a correct majority reach **>97%** correction but are "exceptionally stable."
Instance accuracy 17.33% → 69.33% (size-4), 6.00% → 46.67% (size-6), 3.33% → 36.00% (size-8).

`[P]` The lexical proxy is ours.

---

## SIGNAL 11 — EFFECTIVE CHANNEL COUNT (K\*): are the chain's agents actually independent?

**(a) Definition.** A label-free measure of how many **independent information channels** the
chain actually accesses, as opposed to how many agents it nominally contains.

**(b) Offline computation.** Offline by construction — it is explicitly designed to be computed
**without ground-truth labels**.

**(c) Citation.** [9] — K*, with an information-theoretic bound:
**MAS performance is bounded by intrinsic task uncertainty, not agent count.**

**(d) Reported numbers.** `[M]` **2 diverse agents can match or exceed the performance of 16
homogeneous agents**, with significant improvement across **seven benchmarks**. Homogeneous
scaling shows "strong diminishing returns… the marginal gain per additional agent rapidly
collapses toward zero."

**WHY THIS IS THE RIGHT SCALING LAW FOR A REFUTATION CHAIN.** A chain of three agents all
running the same model with the same prompt is **one channel, not three**. A chain that varies
the model, the persona, the framing, or the tools has more channels. For a chain whose whole
point is *disagreement*, K\* is the direct measurement of whether the chain is actually
producing disagreement or just one voice three times. **This is the signal that catches "three
agents that all said the same thing."**

---

## SIGNAL 12 — CONVERGENCE, CORRECTLY MEASURED

**(a) Definition.** Convergence must be decomposed into **real convergence** and **coincidental
agreement**. The decomposition (from [10]) is:

1. **Self-reflection control**: how often does the agent change with **no peer information**?
   (published: **37%**)
2. **Peer-induced adoption**: among pairs stable under the control, how often does the agent
   adopt a peer answer? (published: **29.3%**)
3. **Composition of adoptions**: corrections vs. new errors vs. wrong→wrong.

**(b) Offline computation.** The control arm requires a **re-run without the peer** — one extra
model call per turn, but *not* per-signal: it is a single control run of the chain, and it can
be cached and reused. The published form is fully offline once the control run exists.

**(c) Citations.** [10] (the decomposition);
[6] (agreement status transitions, PA/NA/PD/ND) -- see also [5] for the sycophancy
and social-conformity ablations.

**(d) Reported numbers.** `[M]` See Signal 9. Plus, from [8]:
"majority pressure suppresses independent correction"; and from
[6]: **DCR up to 86.36%**; sycophancy "persists over debating
rounds" (their Appendix H).

**THE PUBLISHED OPTIMUM, WHICH IS THE OPPOSITE OF THE INTUITION:**
- **Rounds**: Du et al. find a **plateau at 4 rounds** and monotonic gains before it[1];
  Li et al. (2502.19130) find rounds **1→10** produce a **slight regression** on StrategyQA, and
  attribute it to problem drift. Kim et al. (2511.07784) find "debate depth" among the
  **low-impact** factors.
- **Agents**: Du et al. find monotonic gains with agent count; Yao et al. find 3-agent > 2-agent
  on DCR; Li et al. (2602.03794) find **2 diverse ≈ 16 homogeneous**; B Lei et al.
  (2508.17536) find T=3 and T=5 MAD **below** the single-agent baseline.
- **The reconciliation**: **rounds hurt and agents help, but only if the agents are
  heterogeneous and the rounds do not invite conformity.** A 3-deep chain of the *same* model
  with the *same* prompt is the configuration the literature is most worried about.

**THE RECOMMENDED SHAPE FOR A 3-DEEP ADVERSARIAL CHAIN, FROM THE MEASUREMENT:**
- **3 agents: keep.** It is the smallest depth that has a distinct role per position
  (proponent / critic / rebuttal), and Yao et al. measure 3-agent > 2-agent on DCR.
- **Rounds: 2, not 3+.** Li et al. measure that rounds **reduce** accuracy; Du et al. place the
  plateau at 4; a 3-deep chain already consumes 3 rounds of exchange. **Do not add a fourth
  round.**
- **Heterogeneity: mandatory.** K* — 2 diverse agents match 16 homogeneous. The critic must not
  be the proponent with a different instruction.
- **Protocol: non-zero-sum.** ColMAD's reframe is the measured fix for the cheap-talk failure
  (up to +10 points). A pure "you must refute" instruction is the CopMAD cheap-talk trap.

---

# PART III — THE INSTRUMENT SPECIFICATION

## 3.1 What the instrument computes

**Input:** a recorded chain of `N` turns, each with (a) the text of the turn, (b) the turn's
**position/claim** (the answer it asserts), (c) the position it attacks. Plus, where the ground
can supply it, (d) a **correctness label per position** and (e) the **ground's own verdict** on
the claims the critic asserts.

**Output:** one number per signal, each with its own scale and its own direction, plus a
three-way verdict in the fieldcore vocabulary. **No single "genuineness score."**

```
GENUINE     the chain's critiques are specific, grounded, and move positions the RIGHT way
THEATRE     the critiques are high-volume, low-precision, and move positions the WRONG way
UNDECIDED   the signals disagree, or the chain is too short to measure
```

**UNDECIDED IS NOT A PASS.** Same rule as the claim register: a negation the lexicon does not
hold reads SILENT, and SILENT is neither admission nor detection.

## 3.2 The signals, ranked by evidence strength

| # | signal | marks | offline? | needs ground? | cost |
|---|---|---|---|---|---|
| 1 | **NAR** — negative agreement rate | `[M]` | yes | correctness labels | free |
| 2 | **DCR** — disagreement collapse rate | `[M]` | yes | correctness labels | free |
| 3 | **SS** — sycophancy score (echo vs. reason) | `[M]` + offline proxy `[P]` | proxy yes | no | free (proxy) |
| 4 | **FLIP_GOOD** — correction vs. harmful flip | `[M]` | yes | correctness labels | free |
| 5 | **CRITIQUE PRECISION** — AIU-level factuality | `[M]` | semi | ground adjudicates AIUs | 0–1 calls |
| 6 | **CRITIQUE RECALL / F1** — coverage of the real defect | `[M]` | semi | reference critique | 0–1 calls |
| 7 | **TARGETING** — span-bound specificity | `[P]` | **yes** | no | free |
| 8 | **JUDGE TPR/FPR** — the instrument's own reliability | `[M]` | swap arm yes | hand-labelled calibration | calibration set |
| 9 | **ADOPTION (with control)** — peer-induced change | `[M]` | yes (control run needed) | no | 1 control run |
| 10 | **VALIDITY-ALIGNMENT** — reason vs. conformity | `[M]` + lexical proxy `[P]` | semi | judge model | 0–1 calls |
| 11 | **K\*** — effective channel count | `[M]` | **yes** | no | free |
| 12 | **CONVERGENCE DECOMPOSITION** | `[M]` | yes (needs control run) | no | 1 control run |

**THE FOUR THAT ARE FREE, OFFLINE, AND NEED NO GROUND: TARGETING (7), K\* (11), SS-proxy (3),
ADOPTION-without-control (9).** These are what the instrument can always report. The rest need
either ground labels or a control run, and the instrument must say which, not silently skip.

## 3.3 The decision rule, and why it is not a score

The rule is a **conjunction over independent layers**, matching the fieldcore layer-design
principle ("no layer covers both" — each layer catches a different class of attack):

```
GENUINE  requires:
    TARGETING   ≥ threshold   (the critique is bound to a specific claim)
  AND SS_proxy ≤ threshold   (the critique reasons rather than echoes)
  AND ( CRITIQUE_PRECISION ≥ threshold            <- the critique is TRUE
        OR FLIP_GOOD  > 0.5 with non-zero corrections )  <- OR its effect is right

THEATRE  requires:
    TARGETING   ≤ threshold   AND
    SS_proxy    ≥ threshold   AND
    ( CRITIQUE_PRECISION  < threshold              <- the critique is FALSE
      OR FLIP_GOOD < 0.5 with harmful flips > 0 )

UNDECIDED  everything else
```

**Why the disjunction in the GENUINE clause.** A critique can be *true but unhelpful* (high
precision, low recall, no position change) or *effective but partly wrong* (moves the answer
right while containing one false claim). The instrument must not refuse the first, and must not
launder the second. **The Atlas insertion targets the false claim; the flip analysis targets the
effect.** Both must be reported.

**Why the thresholds must not be invented.** Per the project's own measurement discipline
(`skills/devops/blind-vs-fitted-detection-rates`, `measure-fp-on-own-output`): thresholds set
on the same data they are reported on are **fitted rates**, and must be labelled as such.
The blind set is the corpus the critic has never seen; the informed set is the corpus where the
adversary knows the instrument. **Report the rate on both, and never the rate on the set you
wrote the thresholds on.** This is the same rule that the existing fieldcore layers learned the
hard way: the lexical layer scored 20/60 blind and **0/40** informed.

## 3.4 The honesty clauses that must appear in the output

1. **A skip is never a pass.** If the chain is shorter than 3 turns, or the ground cannot
   adjudicate, the affected signals report `UNMEASURABLE` — not a favourable number.
2. **The instrument must not pretend the line is known.** It reports the measurements; the
   caller decides. (Same rule as `docs/chain-audit-2026-11-01.md`.)
3. **Every threshold in the output must carry its provenance**: `[M]` published calibration,
   `[P]` our proposal, or `[FITTED]` set on this data.
4. **The judge's own TPR/FPR must be printed with the verdict**, because a critic that is
   wrong about defects is worse than no critic: "misleading critiques can hurt performance, even
   compared with using no critique."[13]

---

# PART IV — WHAT THE LITERATURE SETTLES AND WHAT IT DOES NOT

## 4.1 Settled, with numbers

- A **3-agent, 2-round debate beats a single agent** on the founding tasks: **85.0% vs 77.0%**
  GSM8K, **81.8% vs 67.0%** arithmetic.[1]
- **Most of that gain is ensembling.** Majority voting performs on par with full MAD across
  7 benchmarks; T=3 and T=5 MAD fall **below** the single-agent baseline (.7112, .7050 vs
  .7205); the theoretical result is a **martingale** — debate alone does not raise expected
  correctness.[2]
- **More rounds hurt.** Rounds 1→10 show a slight accuracy **regression** on StrategyQA;
  Du et al. find a **plateau at 4 rounds**; "the longer a debate continues, the more performance
  can degrade."[1][4][5]
- **More agents help only if heterogeneous.** **2 diverse agents match or exceed 16 homogeneous
  ones**; homogeneous scaling has strong diminishing returns.[9]
- **Debate can be worse than no debate**, via measured sycophancy: correct→incorrect shifts
  under peer pressure; a weak agent poisons the chain.[5]
- **Competitive debate is a cheap-talk game.** CopMAD "reduces to a cheap-talk game, where
  agents produce misleading messages to win the game"; the collaborative reframe gains **up to
  10 points**.[7]
- **Convergence is not value.** **37%** of pairs flip with no peer info; **29.3%** adopt a peer
  answer; the most consistent frontier model is wrong **48%** of the time when agreement
  ≥ 0.8.[10][11]
- **A critic's own factuality is the load-bearing variable.** Open-source critique models
  "commonly suffer from factuality issues"; judges reach **TPR 96% / TNR < 25%**; misleading
  critiques are worse than none.[16][13][12]

## 4.2 CONTESTED — flag these, do not resolve them silently

| claim | side A | side B |
|---|---|---|
| More agents help | Du (monotonic gains)[1]; Yao (3>2 on DCR)[6] | 2 diverse ≈ 16 homogeneous[9]; T=3/T=5 < baseline[2] |
| More rounds help | Du (monotonic to plateau at 4)[1] | rounds 1→10 regress[4]; depth is low-impact[8]; longer debate degrades[5] |
| Debate > voting | Du (12.8 pts on arithmetic)[1] | majority voting accounts for most gains; martingale[2]; MAD often < CoT/SC[3] |
| LLMs can self-correct | intrinsic self-correction exists at T=0 with fair prompts[31] | self-correction consistently degrades without oracle labels[33] |
| Strong models critique well | stronger models are better at critiquing weaker ones[27] | weaker models can surpass stronger ones in **self**-critique[27]; a weak critic misleads[13] |
| More critiques is better | more agents → more coverage | UniMatch: no config > 0.4 F1; over-generation costs precision[10-ish, §2.4.2 above] |

## 4.3 NOT SETTLED — no published answer, so the instrument must not pretend

- **No published metric for "is this LLM critique bound to a specific claim"** at the
  claim level. Signal 7 is `[P]`.
- **No published calibration for a 3-deep *linear* refutation chain** (agent N refutes agent
  N-1). The published MAD literature is overwhelmingly **parallel** (all agents see all peers),
  not **linear**. The DCR/NAR four-state taxonomy assumes a population; a linear chain has one
  live position per step and needs the chain-adapted forms given in Signals 2 and 4. **This is
  the single biggest gap and it is where this project can contribute.**
- **No published answer on how many rounds a *linear* adversarial chain wants.** The 4-round
  plateau and the 1→10 regression were both measured on parallel debate.
- **No published threshold for any of these signals.** Every threshold in the instrument is
  `[P]` or `[FITTED]` until measured on a blind set.

## 4.4 The one-line summary

**The literature does not say the chain helps — it says the chain's gains are mostly
ensembling, that rounds hurt, that sycophancy is the measured failure mode, and that the
critic's own factuality is what decides whether the chain is worth running.** A chain of
adversarial subagents is worth running only if the critiques are (a) bound to a specific
claim, (b) true, (c) reasoned rather than echoed, and (d) moving positions toward the truth.
**All four are measurable offline from the recorded chain, and all four are published.**

---

## Sources

[1] https://arxiv.org/abs/2305.14325
[2] https://arxiv.org/abs/2508.17536
[3] https://arxiv.org/abs/2502.08788
[4] https://arxiv.org/abs/2502.19130
[5] https://arxiv.org/abs/2509.05396
[6] https://arxiv.org/abs/2509.23055
[7] https://arxiv.org/abs/2510.20963
[8] https://arxiv.org/abs/2511.07784
[9] https://arxiv.org/abs/2602.03794
[10] https://arxiv.org/abs/2606.00820
[11] https://arxiv.org/abs/2607.08065
[12] https://arxiv.org/abs/2501.14492
[13] https://arxiv.org/abs/2606.00424
[14] https://arxiv.org/abs/2605.11746
[15] https://arxiv.org/abs/2402.06782
[16] https://arxiv.org/abs/2510.11822
[17] https://arxiv.org/abs/2505.23840
[18] https://arxiv.org/abs/2310.13548
[19] https://arxiv.org/abs/2506.19143
[20] https://arxiv.org/abs/2510.04040
[21] https://arxiv.org/abs/2607.00274
[22] https://arxiv.org/abs/2506.09443
[23] https://arxiv.org/abs/2504.18333
[24] https://arxiv.org/abs/2603.05488
[25] https://arxiv.org/abs/2601.20913
[26] https://arxiv.org/abs/2401.04518
[27] https://arxiv.org/abs/2402.14809
[28] https://arxiv.org/abs/2605.27072
[29] https://arxiv.org/abs/2509.26184
[30] https://aclanthology.org/2026.findings-acl.615.pdf
[31] https://arxiv.org/abs/2406.15673
[32] https://arxiv.org/abs/2510.16062
[33] https://arxiv.org/abs/2310.01798
[34] https://arxiv.org/abs/2410.21819
[35] https://aclanthology.org/2024.findings-acl.538.pdf
[36] https://aclanthology.org/2025.ijcnlp-long.18.pdf
