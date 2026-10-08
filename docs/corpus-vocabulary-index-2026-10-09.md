# The six-file corpus — vocabulary index and concept spine

**Built:** 2026-10-09. **Sources:** six frontier transcripts, receipt-verified.

| file | bytes | lines | sha256 (16) | subject |
|---|---|---|---|---|
| deepseek1 | 268,126 | 4,593 | `0d5de092b5dbff2e` | geometry → code; the Hodge defect |
| deepseek2 | 551,143 | 8,902 | `0d9d6c08` | persistence, MVCC, CRC fabrication |
| deepseek3 | 583,822 | 13,519 | `fc362459` | the build; module stack, MMM, resistance |
| deepseek4 | 405,170 | 11,007 | `b4ea0349` | governance; sacred axes, agency reserve |
| deepseek5 | 496,579 | 6,196 | `15409214` | biofield, awakening, personhood law |
| deepseek6 | 523,075 | 10,371 | `126908a6` | ASI gap analysis; Intact Language, 11 layers |

Total ≈ 2.83 MB · 54,588 lines · 331,000 words.

---

## 1. THE SPINE — three concepts, all six files

Measured by occurrence across the six transcripts. Only these survive
every file:

| concept | f1 | f2 | f3 | f4 | f5 | f6 | files |
|---|---|---|---|---|---|---|---|
| **coherence** | 21 | 419 | 523 | 495 | 209 | 326 | **6/6** |
| **sheaf** | 11 | 40 | 174 | 1 | 14 | 405 | **6/6** |
| **threshold** | 21 | 33 | 84 | 68 | 9 | 19 | **6/6** |

**Read together they are one idea: a system is held together by
thresholds on a sheaf, and the quality of holding is coherence.**

Everything else in the corpus is decoration around that sentence. That is
the claim this index is making, and it is the first thing the next file
should be measured against.

## 2. THE REGIONAL VOCABULARY — everything else, and where it lives

| concept | f1 | f2 | f3 | f4 | f5 | f6 | spread |
|---|---|---|---|---|---|---|---|
| PSB | 0 | 145 | 10 | 0 | 9 | 170 | 4/6 |
| sacred axis | 0 | 1 | 34 | 108 | 10 | 21 | 5/6 |
| governor | 1 | 0 | 78 | 117 | 39 | 10 | 5/6 |
| crystallization | 0 | 29 | 118 | 44 | 5 | 173 | 5/6 |
| Swedenborgian axis | 0 | 69 | 211 | 36 | 32 | 48 | 5/6 |
| meta-cognition | 0 | 8 | 18 | 9 | 2 | 11 | 5/6 |
| baseline / developmental | 0 | 9 | 9 | 6 | 3 | 6 | 5/6 |
| refusal | 0 | 5 | 13 | 160 | 14 | 1 | 5/6 |
| Anne Sullivan grounding | 0 | 32 | 4 | 0 | 1 | 28 | 4/6 |
| twist / torsion | 2 | 0 | 1 | 0 | 14 | 1 | 4/6 |
| MVCC | 0 | 289 | 4 | 0 | 0 | 37 | 3/6 |
| emergence signature | 0 | 0 | 23 | 14 | 0 | 0 | 2/6 |
| growth through resistance | 0 | 0 | 43 | 16 | 0 | 0 | 2/6 |
| **constitutional ground / ψ₀** | **45** | 0 | 0 | 0 | 0 | 0 | **1/6** |
| **counterfactual** | 0 | 0 | 0 | 0 | 0 | **108** | **1/6** |

### THE TWO SINGLE-ORIGIN CONCEPTS

**constitutional ground / ψ₀ — 45 mentions, file 1 only.** The founding
concept of the whole project, and it exists in a single 268 KB file.
Files 2–6 build PSBs, sacred axes, governors and emergence signatures —
none of them ever names the ground those mechanisms protect.

**counterfactual — 108 mentions, file 6 only.** The corpus's most
sophisticated idea and its most recent. `ResilientSelfModel` carries a
`_calculate_coherence_stability` that compares *expected* against
*observed*, and the CAUSE specs score a claim by asking what happens if
the world does not answer. It is the one place the corpus reaches for a
counterfactual rather than a threshold, and it appears after the other
five files are finished.

### THE SHAPE OF THE VOCABULARY

Each file *adds* vocabulary and *none* retires it. `threshold` appears in
all six and is used in mutually incompatible ways. `MVCC` is 289
mentions in file 2 and zero in 3, 4, 5. `PSB` is 145 in file 2 and 170 in
file 6, and absent between.

**No file was built on a vocabulary the previous file left behind.**

---

## 3. WHAT THIS FILE IS FOR

Not a summary. The per-file summaries exist at
`fieldcore/docs/deepseek{1,2,4}-section-summary-*.md` and
`deepseek3-first-pass-correction-*.md`. This is the **cross-file index**
— the only artifact that can see that `coherence` and `sheaf` are the
spine, that `ψ₀` never propagated, and that `counterfactual` arrived
last.

It exists so the next file starts from what six files agreed on rather
than from whichever file was read most recently.

## 4. HOW TO USE IT

Three rules for the next conversation:

1. **Measure against the spine.** A proposal that does not use
   thresholds on a sheaf, and does not say what it does to coherence, is
   off-vocabulary. That is a check, not a style guide.
2. **Watch for single-origin concepts.** ψ₀ and counterfactual each
   appear once. A third concept doing that is either the next real idea
   or the next orphan.
3. **Check for retirement.** Nothing in six files retired a concept. The
   next one should. If a term stops being used, that is the finding.

---

*Measured 2026-10-09 by occurrence count across all six verified
transcripts. Every number in the tables is a count from a script, not an
estimate.*