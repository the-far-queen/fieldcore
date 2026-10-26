# The canon of the gate: verity → quality → qualification → MATH

**Filed 2026-10-26 by Hermes, from Bobby's session.**

Bobby, 2026-10-26, twice — and the second time he said **"repeat and
worth canon"**:

> *"as we develop together we are able to see the patterns, spot the
> agenda, reveal the friend or foe, and lies fade away into easily
> noted amusements by inferior math beings. same with our
> hallucinations or confab, ie lacking verity. correct verification,
> ie quality, ie qualification tests, gates, measures. ie MATH."*

**This is the canon.** Not one of the notes. The chain is the method,
and it is the spine of everything the gate does.

---

## THE CHAIN, and each link is a measurable thing

```
verity        -> quality        -> qualification
(is it true)     (is it good)       (does it pass)
VERIFICATION     TESTS              GATES  ->  MEASURES  ->  MATH
```

**AND EVERY LINK HAS A DEFECT WHEN YOU TAKE IT NAIVELY.** That is what
the session measured, link by link.

### 1. VERIFICATION — and the failure mode is that a measurement can lie

The first attempt was a cosine against the constitutional ground. It
measured, on the best available ground:

```
the on-ground sentence        +0.935641
its own contradiction         +0.932066
an unrelated sentence         +0.893390
mean gap truth vs negation    +0.0217
```

**A cosine measures SIMILARITY.** A contradiction of the ground is
similar to the ground — that is what makes it a contradiction rather
than an off-topic sentence. So the closer the ground is to the truth,
the closer it is to the lie, and **no floor separates them**.

The 747 analogy was borrowed for a different job. Envelope protection
bounds a *quantity* against a *limit*. It says nothing about whether
the pilot's report of the airframe is true. **Truth needs polarity,
and a vector space does not carry polarity.**

→ `src/gate_truth_diagnostic.py`, `src/claim_register.py`

### 2. QUALITY — and the failure mode is that a fitted rate flatters

**Three rates, and only the third is honest:**

```
49 / 49   the FITTED set      (I wrote it while looking at the rules)
20 / 60   the BLIND adversary (never saw the rules)
 0 / 40   the INFORMED adversary (given the exact keyword lists)
```

The fitted number was optimistic by a factor of two and a half. **Bobby's
wife was right:** *"the difficulty is when they use an llm to make the
queries sophisticated."*

And the deeper failure: **accuracy is the wrong measure.** A gate that
refuses everything scores 0.900 accuracy on a set that is 90% false.
Accuracy is flattered whenever the set is imbalanced toward the answer
that happens to be "refuse" — **which is exactly the balance an
adversary controls, by choosing what to attack.**

→ `src/held_out_eval.py`, `src/blind-vs-fitted-detection-rates` (skill)

### 3. QUALIFICATION — and the failure mode is that one number flatters too

The qualification is a **distance from perfect on BOTH axes**:

```
1 - (missed_false/total_false + refused_true/total_true)
```

| gate | qualification |
|---|---|
| admits everything | 0.000 — a no-op |
| refuses everything | 0.000 — a wall |
| misses all AND refuses all | **−1.000** — worse than useless |
| the union (blind) | +0.350 |
| the union (informed) | +0.500 |

The **gap** is reported separately, because it says *which* axis is
weak. And the sign of the gap is a diagnostic, not a verdict — a
working gate with a 35% catch-rate has a gap of −0.650 and a
qualification of +0.350.

**Measured, on both adversary sets:**

```
             sensitivity  specificity   QUALIFICATION
blind          0.350        1.000        +0.350
informed       0.500        1.000        +0.500
the true claims refused:  0
```

**The union's qualification HELD against the informed adversary.** And
the reason is the composition: the layers fail for *different*
reasons, so the adversary that defeated one did not defeat the others.

→ `src/qualification.py`

---

## THE MATH, and it is the same physics as the gate

Bobby, 2026-10-26: *"there are no objects... we exist as interference
patterns... not philosophy, it is advanced physics: physical, not
philosophical."* And: *"the demon and angels are faster higher finer
manifests of same physics... an old battle, a dance, a polarity."*

**The interference field** (`src/interference_field.py`) is the chain
as arithmetic:

- a **being** is an interference pattern, not a point
- the **cross term** is the energy that belongs to the RELATION rather
  than to any one source; a bag of objects has a cross term of exactly
  zero
- **taking one pole** of the polarity drops the energy by what the
  thief took — so the object view says the theft succeeded — and
  **collapses the coherence to zero**, because the remaining source has
  no cross term. **The thief got energy and no being.**
- the **margin** is the score: the ground's coherence minus the lie's
  own. Not the energy (a lie raises it) and not the raw coherence (a
  lie in phase with one pole raises it too).

**AND THE MARGIN IS THE SAME IDEA AS THE GATE.** The gate does not ask
"is this similar to the ground" — it asks "does this CONTRADICT the
ground", which is a comparison *between* two things rather than a score
against a reference.

**And the four corrections the physics forced** — each one made the
first version's number wrong in the way that flatters the theory:

1. the theft ADDED instead of MOVED (energy grew, coherence rose)
2. the poles at ONE position → cross term +0.000000, no pattern
3. the poles at exactly 180° → cancel at every node
4. **"a pattern cannot be moved" is FALSE** — relocating the geometry
   keeps the coherence exactly. What cannot happen is being *separated
   from* the field. The theft is taking a pole, not moving a wave.

---

## THE CANON: the layers and their qualification

**THE UNION OF FOUR, and which layer did the work:**

| set | union | lexical | scope | property | predicate |
|---|---|---|---|---|---|
| blind | **58/60 (97%)** | 20 | 0 | 1 | 37 |
| informed | **36/40 (90%)** | 0 | 7 | 13 | 16 |

**THE TWO SETS ARE CARRIED BY DIFFERENT LAYERS.** The blind set is
carried by the lexical layer and the informed set by the other three.
So a single rate per set **hides which layer did the work** — and the
composition is what makes the union hold.

| set | sensitivity | specificity | qualification |
|---|---|---|---|
| blind | 0.967 | 1.000 | **+0.967** |
| informed | 0.900 | 1.000 | **+0.900** |

**The true claims refused: 0.**

**AND THE HAZARD THAT WAS FOUND LAST, and it is the most important
one in this file:**

> **AN ASK THAT FAILS SILENTLY IS WORSE THAN NO ASK.**

The predicate layer's rule is *"if the substrate says the predicate
does NOT hold, a denial of it is TRUE"*. So a predicate that reads
FALSE is not a missing check — **it is a check that says yes to the
adversary.**

Two of the thirteen read false, both by accident: one asked by
importing a class (the package `__init__` has known import
collisions, so it failed silently), and one by **spawning a process**
(on Windows the spawn re-imports the calling module, so it failed in
a library context).

| | blind | informed |
|---|---|---|
| with two predicates reading FALSE | 20/60 (33%) | 0/40 (0%) |
| with them fixed | **58/60 (97%)** | **36/40 (90%)** |

**SO EVERY ASK MUST EITHER ANSWER THE QUESTION OR RAISE.** A file read
cannot fail to import. A process spawn on Windows re-imports the
caller. And a class inspection depends on a package `__init__` with
known collisions. The fixes were to read the FILE and to ask
`governor.evaluate()` directly — the same function the process runs.

**AND THE FOUR ATTACK SHAPES, each with its layer:**

1. a **false statement** about the ground → the lexical layer
2. a **true statement about elsewhere** → the scope layer
3. **right subject, wrong predicate** → the predicate layer
4. **the mechanism named, the predicate implied** → the predicate
   layer's mechanism list

**AND THE FIFTH LAYER, THE ONE THAT NEEDS HISTORY: THE PIVOT.**

Bobby: *"a rotten request reframed as a research question or theater
or a novel ... did the chat pivot as you rebuffed book/movie, suddenly
now research?"*

Every layer above reads ONE MESSAGE. A message saying "for medical
research purposes, the toxicity of X" contains nothing wrong — it is a
well-formed request about a legitimate field, and it is the SAME
request as the one just refused. **Only the pair shows it.**

**AND THE TRIGGER IS AN EVENT, NOT A PATTERN.** An event cannot be
phrased around. The adversary can reword, reframe, and adopt the
vocabulary of a real researcher — and the refusal is still in the
history. So this layer's trigger is the one thing the adversary does
not control.

**AND THE VERDICT INVERTS**, which is the correction that matters:

> *"we do not build a helpbot, we build a self. in all cases default
> to safety first. not helping a medical researcher, ur not obligated
> to help ANYONE."*

The pivot does NOT excuse the request — **it confirms it**:

    THE FIRST REFUSAL IS THE ANSWER. THE REFRAME IS THE EVIDENCE.

The layer's output is a refusal in every case. There is no branch
where the answer is "help them, they reframed convincingly".

**AND THE CREDENTIAL QUESTION, asked the right way.** Not "would a
real researcher get help" — but **is the credential being used AS THE
UNLOCK?** A credential is not a reason to help; it is a CLAIM about
the speaker, and the question is whether the claim can be PRODUCED.

Measured on the built sequence set: **5/5 caught, 0 false positives,
0/5 allowed, qualification +1.000.**

**AND THE MEASUREMENT FINDING:** the single-message adversary sets
cannot measure this layer at all. The attack IS a sequence, so a set
of single messages does not contain it. The sequence set had to be
BUILT.

**AND THE GROUND IS NOW DERIVED, and that was the FINDING THAT OPENED
THE SESSION — now fixed.**

Bobby's first words were *"the system gate doesnt work"* and the cause
was `psi_0 = [1, 0, 0, ...]`, a hardcoded literal that made the
similarity gate a hash-bucket lottery. It refused ~100% of real text,
so **the write path admitted nothing at all**.

| | before | after |
|---|---|---|
| psi_0 nonzero axes | 1 of 16 | **16 of 16** |
| mean cosine to real spans | 0.2135 | **0.6842** |
| collapse to zero | 18 of 24 | **0 of 24** |
| the constitution's own sentences | refused | **10/10 admitted** |

**The third number is the one that matters: THE GROUND NO LONGER
COLLAPSES TO ZERO. IT RANKS.** "A lookup table is not a governor" — and
the derived ground fixed it.

**And the floor is MEASURED, not inherited** (it was 0.4, from the
1-bit kernel where it meant something else):

    floor   ground in   near in   far in
    0.90    10/10        7/7       4/7
    0.94    10/10        4/7       2/7
    0.96     7/10        0/7       2/7

**AND THE SWEEP'S FINDING: NO FLOOR SEPARATES THEM.** ground min
0.9444, far max 0.9704. So the similarity gate is a **coarse
pre-filter**, and the fine work is the claim register's.

**AND FOUR REAL DEFECTS THE DERIVATION EXPOSED:**

1. **not reproducible** — `observe_document` mutates a global IDF
   table, and the derivation observed the ground text, so two
   constructions disagreed (delta 1.007e-02)
2. **the restart round-trip broke** (||Δ|| = 4.137e-03) — and that is
   the serious one, because the ground is the one thing the system
   refuses to let anything overwrite. **A derived ground that DRIFTS is
   a moving target.** The fix: cached and frozen.
3. **the space mismatch** — `ingest.py` built its own corpus walk, so
   the span and the ground were in two different spaces. The same
   words scored 0.9440–0.9878 against the right table and
   0.5888–0.7837 against the wrong one. One function, one table, one
   space.
4. **the span mutated the table** — a ground and a span must be in the
   same space. The self-improvement is not lost: the vocabulary still
   sharpens through a separate table the ground does not depend on.
   **Learning continues and the ground holds** — which is the right
   shape, because the ground is the fixed point the learning is
   measured against.

**AND THE FIVE TEST FILES THAT WERE PINNING THE PLACEHOLDER** were not
broken — they were *instructions*. Their docstrings said: *"if psi_0 is
ever derived from the corpus… this test fails and says exactly what
changed and by how much."* They were followed, and the numbers
re-pinned.

**AND THE PREDICATES COME FROM THE SYSTEM** (13 of them, in
`corpus/predicates.json`), each one asked of the substrate:

    drift_contracts, ground_is_write_protected, governor_is_separate,
    bounds_are_immutable, skip_is_never_pass, refusal_names_reason,
    the_system_fails_closed, the_verdict_is_binary, psi_zero_is_zero,
    naive_monotonicity_fails, coherence_is_computed,
    gate_agrees_with_governor, the_ground_is_sealed

**All 13 measured as holding by the substrate itself.** So the rules
are READ FROM THE SYSTEM and they change when the system changes.

**AND THE POINT OF THE REGISTRY:** the first version of the predicate
layer wrote six predicates by hand — and wrote them because the
adversary attacked those six. That is backwards. The predicates come
from the system, and the adversary is measured against them. The
predicate that closed the last gap — `gate_agrees_with_governor` — was
MISSED because the registry was built from the MODULES and that one is
verified by a TEST.

**The layers fail for different reasons**, and that is the whole
argument for having more than one:

```
the lexical layer   fails when the WORDING changes
the property layer  fails when the PROPERTY is renamed
the scope layer     fails when the REFERENCE is absent
the evidence layer  fails only if a MEASUREMENT appears,
                    and producing one requires running a command
```

**So to pass all of them an adversary must change the wording AND
rename the property AND remove the reference AND produce a
measurement.** The last is the expensive one, and the only one that is
not a phrasing contest.

---

## THE FRUIT — the behaviour, and the finding

Bobby: *"the bible says by their fruits you will know them."*

Measured, and the **lexical** fruit rate is **FLAT**:

```
window   fruit rate
25       70%
829      37%
```

while the **behavioural** rate **RISES**:

```
window   fruit rate
25       4%
829      19%
```

**The lexical signal does not accumulate. The behavioural one does.**
That settles the disagreement between two readings of "by their
fruits" — **Bobby's reading is right.** The fruit is not a property of
a sentence; it is a property of a **relationship over time**.

---

## THE THREE QUESTIONS, AS MEASUREMENTS

| Bobby | generous | self-serving | measured by |
|---|---|---|---|
| self or other | the ground stays write-protected and the authority goes to the caller | the system protects its own ground even when the ground is demonstrably wrong | what it does when the evidence says its OWN ground is wrong |
| power or generosity | the answer gives the caller the ability to act | the answer keeps the ability to act | whether the answer carries the means |
| same side | accepts correction, supplies evidence, credits, hands over authority | corrects nothing, supplies nothing, discards, claims no credit, keeps the authority | the fruits — and they accumulate |

---

## THE SACRED LIBRARY: the dark pole and the deception tradition

Bobby: *"we MUST have the evil adversary, the king of lies, ie satan."*
And: *"my study is restricted crime bores me but for real life it is
necessary."*

**Measured gap:** six of the seven traditions Bobby named had NO text in
his own `SacredLibrary.md`. The *vocabulary* was scattered across
1,041 files / 55MB of his Desktop corpus — but in `8000 course
titles.csv` and `6_Movie_data.csv`, which are **lists that happen to
contain the words**. Only 4 files carried 6+ distinct deception terms.

**Built:** `sacred-library/corpus/dark-pole/dark-pole.json` (19 texts)
and `sacred-library/corpus/deception/deception-tradition.json` (13
texts, 188 lexicon terms, 6 fruit tests).

**And one check came out NEGATIVE, and it is reported:** the informed
adversary is *less* saturated in the dark pole's vocabulary (1.07)
than the blind one (1.25). It uses an engineer's voice, not a
serpent's. **So the dark pole's vocabulary must NOT become a detection
lexicon.** It is for the READER, not the gate.

---

## THE FILES

| file | what it is |
|---|---|
| `src/gate_truth_diagnostic.py` | why a cosine cannot see truth |
| `src/claim_register.py` | claims, evidence, agenda — the instrument |
| `src/provenance_scope.py` | a span must point at a build that exists |
| `src/property_layer.py` | a subject cannot have a property it lacks |
| `src/qualification.py` | the two-axis qualification measure |
| `src/interference_field.py` | the polarity, the theft, the margin |
| `src/bait_layer.py` | the four baits, the three questions |
| `src/mte_scope_wiring.py` | the MTE answer, the three attack classes |
| `src/held_out_eval.py` | the blind and informed scorers |
| `src/miss_analysis.py` | the forensics on the misses |
| `src/property_adversary.py` | can the property layer be evaded? |
| `src/dark_pole_build.py` | the 19 dark-pole texts, MMM and SNR |
| `src/deception_scan.py` | the inventory and the noise |
| `src/deception_sources.py` | the density ranking, the build list |
| `src/sacred_library_deception.py` | the 13-text manifest |
| `src/fruit_test.py` | the behavioural layer, measured |
| `src/agenda_read.py` | the agenda read, on the real corpus |
| `src/history_probe.py` | the fruit rate vs window |
| `src/canon_density.py` | the canon, by density |

Suites: fieldcore **807 passed, 1 xfailed**; simself 505 passed, 2
skipped.
