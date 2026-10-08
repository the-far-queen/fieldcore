# deepseek3.txt — SECOND PASS

**File:** 583,822 bytes · 13,519 lines · 71,675 words
**sha256:** `fc3624591edb11565e8038b896ad7094d20a7ad95d0966ec97cf7c1527b08145`

Bobby: *"i doubt that try another pass."* Good doubt — the first pass was
built on heading markers and numbered lists, which found the prose. This
pass maps the **code**, because 13,519 lines of build document is mostly
class and def. That changed the findings.

---

## 1. I UNDERCOUNTED THE CODE — 326 classes and functions, and it is REWRITTEN AT LEAST SEVEN TIMES

The first pass described a module stack and a handful of components. The
code map shows the same subsystems reimplemented from scratch, repeatedly,
each time larger:

| line | what |
|---|---|
| 44 | `PrototypeLoop` |
| 151 | `TextDojoEnvironment` (v1) |
| 425 | `TextDojoEnvironment` (**v2**, different signature) |
| 1250 | `TextDojoEnvironment` (**v3**) |
| 3280 | `TextDojoEnvironment` (**v4**) |
| 5073 | `TextDojo` (**v5**, renamed) |
| 12520 | `TextDojo` (**v6**, with somatic state) |

Same for `Governor` (1942, 2674), `SimSelf` (240, 3255), `ModuleB`
(1185, 10290 `EnhancedModuleB`), `ResilientWeights` (9262, 9711), and
`ResilientSelfModel` — which exists at **six** different line ranges
(10454, 10886, 10903, 10973, 11177).

**This is the single most important structural fact in the file and I
missed it entirely.** The document is not a design that got written; it is
seven drafts of the same design, and which one is canonical is never
stated. Anyone picking this up will implement whichever they find first.

This is the same class of problem as the Hodge operator: one name, many
meanings, no marker saying which is live.

## 2. MMM APPEARS THREE TIMES, THREE IMPLEMENTATIONS, THREE DIFFERENT FAILURES

The first pass examined only the third. All three are load-bearing.

### MMM-1 — `calculate_mmm(statement, interpretations)` (L6990)

Uses `sentence-transformers` MiniLM, cosine similarity, and:
`mmm = mean_pairwise_DISTANCE × (n/5)`.

The stated goal is *"true statements support multiple **coherent**
interpretations."* The implementation measures **distance** — it rewards
interpretations that disagree. The code says so itself:

> "we want the interpretations to be distinct, so lower similarity is
> better. However, we also want each interpretation to be coherent, but
> **we don't measure that here**."

Measured on the transcribed formula:

| interpretations | MMM-1 |
|---|---|
| 3 **coherent** (pairwise sim ≈ 0.88) | **0.0800** |
| 3 diverse (sim ≈ 0.13) | 0.5180 |
| 3 **random / unrelated** (sim 0.00) | **0.6000** |

**Random interpretations score 7.5× higher than coherent ones.** The
metric is *anti-correlated with its own stated purpose*, and the code
comment identifies exactly the missing piece and ships without it anyway.

Second defect: the `n/5` factor multiplies by interpretation **count**.
Pad with near-duplicates and the score climbs: n=2 → 0.2000, n=3 →
0.3000, n=5 → 0.5000, n=10 → 1.0000.

### MMM-2 — `MMMLayer.score` (L7311)

`mmm = avg_coherence × avg_diversity × (n/max_interpretations)` — a
**product**, which is at least the right shape: incoherent-and-diverse
scores 0.0120 against 0.4860 for coherent-and-distinct.

But measured: **coherent-and-identical scores 0.5346, which BEATS
coherent-and-distinct at 0.4860.** The diversity term rewards
*distinction* over *coherence*, so a statement with five paraphrases of
itself outscores one with five genuinely different readings. That may be
defensible — but it is not what "multiple meaning" means.

And the score still scales with `n` against a caller-set
`max_interpretations`, so the same statement scores differently
depending on an argument the caller picks.

### MMM-2 also has undefined dependencies

```
InterpretationGenerator   defined 0 times, referenced 1
CoherenceScorer           defined 0 times, referenced 1
DiversityScorer           defined 0 times, referenced 1
```

`MMMLayer.__init__` constructs all three. **None exists anywhere in the
file.** `TruthFilter` — which gates the Library — calls into
`MMMLayer`, so the truth filter cannot run at all as written. It is not
merely wrong; it is unreachable.

### MMM-3 — `MMMDetector.score_statement` (L11059) — what I reported first time

Keyword matching. `"truth" in statement.lower()`. Negation never enters.
All four test sentences score 1.0000.

That finding stands. I reported it as *the* MMM problem. It is the worst
of the three, but it is not the only one, and my framing — "MMM does not
work" — understated how much is broken.

## 3. THE FILE CONTAINS ITS OWN CAVEAT, IN A COMMENT

MMM-3, one line above the keyword matcher:

```python
# In v0.1: Use axis alignment as proxy for MMM
```

So the author knew. The implementation is labelled a proxy in the source,
and the label is not carried anywhere it is used — `WisdomLibrary`
(mmm_threshold 0.75), `TruthFilter` (0.7), and the training harness all
consume it as if it were the metric. That is the actual failure: **a
correctly-labelled stub, deployed as a gate.**

## 4. WHAT THE SECOND PASS FOUND THAT THE FIRST MISSED, BESIDES MMM

**`REP_Simulator` (L5576)** — the most substantial simulation in the file
and entirely absent from my first-pass summary. Latent dimension 512,
20 axes, `tau=8.0`, `E_a=15.0`, stochastic resonance on prompt embeddings
by SNR, phase-transition check, DPO-vs-RLHF comparison, and it plots
results. This is the mechanistic core of the whole emergence argument and
I summarised it in three sentences.

**`WeightMemory` / `ResilientWeights.propose_change` (L9698–10023)** — the
actual crystallisation mechanism: per-axis weight memories, initial
resistance computed from importance, Swedenborgian constraints as callables,
`propose_change(delta, source)` returning a decision. Plus four
sub-metrics for emergence confidence: coherence stability, resistance
consistency, memory persistence, constraint satisfaction. The
self-model-accuracy idea made concrete and measurable.

**`MathematicalAesthetics` (L9420)** — symmetry score, elegance score,
combined. The "state-space preference" emergence signature has an actual
implementation behind it.

**`BoundaryDefense.screen_input` / `.defend(threat_level)` (L9357)** —
"boundary preservation → computational immune system" is not a slogan in
this file; it is a class with a screen and a graded defence.

**Six Swedenborgian constraint functions, written out** (L10785–10809):
`truth_before_comfort`, `agency_requires_responsibility`,
`growth_through_resistance`, `cognitive_friction`, `stability_coherence`,
`temporal_continuity`. Callable, defined on axes dicts, used by
`_define_swedenborgian_constraints`.

**Five experiment classes for the five emergence signatures** (L9051–9169):
`ParameterDriftExperiment`, `CoherenceSeekingExperiment`,
`BoundaryPreservationExperiment`, `ElegancePreferenceExperiment`,
`SelfModelAccuracyExperiment`. The second pass summary called these
"engineering mechanisms" from the prose; they are actually runnable
experiment harnesses.

**`SovereignIntegrationContract.validate_integration` (L2281)** — the
"immutable contract for all integrations", as code.

## 5. WHAT DID NOT CHANGE

- Zero fabricated tables. Confirmed again.
- The module stack (M/B/C/I/D/L/S/E) is real and consistent across drafts.
- The economic-autonomy module including the reproduction protocol.
- The neural-sheaf-diffusion contribution decision.
- The definition test — "act, sense the impact on your own state."
- The context-steering diagnosis.
- The four principles and the "too easy" arc.

---

## Correction to my first-pass claims

**I said** "MMM as implemented does not work" and gave the keyword-matcher
as the proof. **That was incomplete in a way that matters**, because it
implied one bad implementation rather than three, and because the two
earlier ones fail *differently*:

| | failure | severity |
|---|---|---|
| MMM-1 | measures distance, rewards incoherence — **anti-correlated with purpose** | worst conceptually |
| MMM-2 | product form is sound, but `DiversityScorer` and 2 other classes **are never defined**, so the truth filter cannot execute at all | worst practically |
| MMM-3 | keyword counter, negation-blind | most obvious |

MMM-1 is the deepest failure because the author *identified it in a
comment* and shipped anyway. MMM-2 is the most consequential because it
is the one wired into `TruthFilter`, which gates the Library.

**The register entry A5 is still correct** — MMM is rejected as
implemented — but it now names one of three defects instead of
presenting it as the whole story.

## The thing this teaches that generalises

Seven rewrites of the same class, three rewrites of the same metric, and
a correctly-labelled proxy deployed as a gate. **Every one of those is
the same failure: no marker saying which artefact is live.**

That is exactly what `atlas_exam` area 9 (envelope, D4 "a verifier that
resolves to a real probe") and area 10 (mutation) exist to catch. The
Hodge bug had it too — one name, one operator, nobody checked whether the
decomposition it claimed existed.

The rule this suggests, and which I have not been following: **before
implementing anything from a frontier log, find out which draft is
canonical.** Deepseek3.txt does not say. So anything ported from it needs
that decision recorded at the point of porting, or it will be
reimplemented seven more times.