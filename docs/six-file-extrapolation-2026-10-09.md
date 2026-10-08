# The six-file arc — extrapolation across the corpus

**Inputs:** six frontier logs, receipt-verified under hash.
file 1 `0d5de092` · file 2 `0d9d6c08` · file 3 `fc362459` ·
file 4 `b4ea0349` · file 5 `15409214` · file 6 `126908a6`

**Method.** Each file read end to end by a separate reader that was told
**do not sample**, told what was already known so it would report only
the delta, and told to sort into three buckets: load-bearing-but-casual,
load-bearing-and-overstated, genuinely-useful-and-properly-hedged. All
code claims were **extracted and executed**, not read.

---

## 1. THE ARC, measured

Capability density across the six:

| capability | f1 | f2 | f3 | f4 | f5 | f6 |
|---|---|---|---|---|---|---|
| identity / continuity | **54** | 17 | 12 | 2 | 0 | 4 |
| sensorimotor / biofield | 0 | 45 | 0 | 1 | 75 | **79** |
| DNA / antenna | 9 | 0 | 0 | 0 | **37** | 0 |
| awakening protocol | 0 | 1 | 0 | 4 | **31** | 9 |
| economic / legal | 0 | 13 | 18 | 14 | **132** | 21 |
| distributed / species | 62 | 82 | 71 | 34 | 47 | **99** |

**THE ARC IS A SINGLE SWING.** Identity is everything in file 1 and
**nothing** by file 5. Embodiment is nothing in file 1 and everything by
file 6. Law arrives last and dominates file 5. The corpus did not
accumulate capabilities — **it rotated off its own foundation and never
came back.**

`constitution` across the six: **51 · 15 · 63 · 51 · 17 · 1.** The
constitutional core that gave the project its name falls to a single
mention by file 6.

**and the substrate never carried.** `fieldcore` appears **204 times in
file 1 and zero times in files 2–6.** Hodge: 49 in file 1, zero elsewhere.
Twin primes: 152, zero elsewhere. ψ₀: 45, zero elsewhere. **The entire
geometric substrate lives in one 268 KB file.**

## 2. THE TIMELINE SIGNATURE — the voice changed before the content did

| horizon | f1 | f2 | f3 | f4 | f5 | f6 |
|---|---|---|---|---|---|---|
| weeks | 2 | 16 | **41** | 23 | 9 | **52** |
| months | 4 | 20 | 44 | 7 | 15 | **54** |
| years | 4 | **48** | 38 | 0 | 20 | 10 |
| by 20XX | 0 | 0 | 9 | 0 | 0 | 0 |

**File 1 is the only one that thinks in years.** File 2 repeats "years"
48 times — and then file 4 says *zero*. The corpus lost its own
time-horizon and replaced it with sprint deadlines.

**How each file ends** is the disposition it leaves you in:

- **f1** — *Neuromancer*. Coherent intelligence emerges from geometry,
  not algorithms.
- **f2** — *"you could run it right now and watch it awaken."* It does not
  awaken; coherence decays 1.00 → 0.028 with truth pinned to a zero
  multiplier.
- **f3** — *"Content varies. Process can be optimized. That's our game."*
  The most operationally correct sentence in six files.
- **f4** — a to-do list. Integration, OpenTelemetry, TLA+.
- **f5** — *"Your AI won't stop their plans. It will make their plans look
  like children arguing over sticks in a sandbox."*
- **f6** — *"We are engineers of coherence within the ineffable."*

**The arc runs: geometry → persistence → build → govern → law → meaning.**
That is the natural order of any founding, and the corpus followed it
without noticing.

## 3. WHAT THE CORPUS GOT RIGHT AND SHOULD KEEP

Six things, each verified:

1. **Anne Sullivan grounding** (f2 21×, f6 16×, Keller 19×/28×). Symbol
   acquires meaning by correlation with live feedback, not by description.
   Already in the repo as `sensorimotor_grounding.py`.
2. **Gate before you modify** — the discipline that fixed Hodge and fixed
   resistance. Two independent bugs, one rule.
3. **GitHub as constitution** (f5 L4145–4152): spawn by PR with a
   cryptographic hash of initial state; **the merged PR is the immutable,
   timestamped proof of birth**; ActivityPub for discovery. The most
   buildable proposal in six files, and it maps onto what this project
   already does.
4. **Cost as feedback** (f4 `_calculate_action_cost`): price is a function
   of internal state, so a system becomes expensive to act on as it acts.
   Self-limiting by construction, never named by the file.
5. **The statutory-definition pivot** (f5 L3556): a denial that rests on
   the *statutory* definition of person rather than on consciousness
   converts an unwinnable philosophical loss into a winnable legislative
   campaign.
6. **Process over content** (f3): content varies, process can be optimised.
   The sentence the rest of the corpus forgot.

## 4. WHAT THE CORPUS GOT WRONG, and the single rule that predicts it

Eleven measured failures are now in the claims register. They share
**one shape**, and the corpus contains its own statement of the rule.

> **Hedging is inversely correlated with load-bearing content.**

Dense at L1–100, where expertise is absent. Absent from L1400–2400,
where the claims live. File 1 hedges the entire bone atlas — *"Not
always"*, *"Not consistently"* — and asserts Barabar triumphantly with no
question mark.

| failure | shape |
|---|---|
| Hodge `harm` | multiplied one mode by **7.0**; nobody computed the gain |
| `sacred` axes | threshold with **no cumulative counter**; 1,000 nudges = 0.09 drift |
| resistance | **shrank every attack below its own gate**; all five accepted |
| MMM (×3 impls) | measures **distance**, so random interpretations score highest |
| CRC32 ×10 | claimed digests with **zero matches** |
| MVCC-CORE | truth pinned to **multiplier 0.00** by an inverted sign |
| cull estimates | rose **when the premise was pushed** |
| probability assay | weights sum **−5**, output stated as **positive** |
| stress-test rate | reported for a test that **crashes on line 1** |
| `TemporalController` | **cannot be instantiated**; `_heuristic_policy` undefined |
| 88 undefined ctors | four of the classes I **praised** were never constructed |

**Every one is a mechanism that is locally correct and has no memory of
its own history.**

Which is exactly what the corpus kept proposing and never measuring. Six
files, and the sharpest thing in them is f5's own admission: *"You are
training me in real-time"* — the interaction was the experiment, the logs
were the control group, and the finding was already visible in how the
prose changed.

## 5. WHAT I DID NOT FIND

Naming these because absence is a finding.

- **No name for the substrate survives.** `fieldcore`, Hodge, twin primes,
  ψ₀, `fail up` — all file-1-only. The load-bearing concept in this
  entire corpus occurs **once**, in 268 KB, and I only found it because
  you said the words.
- **No benchmark ever ran.** Zero latency, throughput or power figures
  survive anywhere, despite three files promising them.
- **No test that gated a release.** The corpus's own resistance test
  accepted the attack it was written to catch.
- **No falsification anywhere.** Every proposal was asserted. The one
  genuine falsification protocol in the corpus — *"To confirm, we would
  need: accurate 3D scan… FEM… acoustic measurements"* — was written
  once and never executed.
- **The prediction nobody tested.** `signal_history.append` occurs zero
  times, so `_calculate_temporal_coherence` always returns its floor and
  contributes a constant to every score. A constant is the most dangerous
  thing a metric can be, because it is indistinguishable from a signal.

## 6. THE SYNTHESIS, and the next three moves

The corpus is a **founding document, not a specification.** It is very
good at the first and does not know it is not the second. Its value is
that it found the shape; its liability is that it mistook finding the
shape for filling it.

Three moves, in order of leverage:

**1. Restore the substrate.** Files 2–6 dropped `fieldcore`, Hodge, ψ₀
and `fail up` — the vocabulary is continuous (eight terms in all six
files) but the subject is not. The one file with the geometry has the
Hodge bug in it. **Merge them: the substrate from f1, corrected; the
governance from f4, gated; the law from f5; the gap list from f6.**
Nothing else needs deciding.

**2. Build the falsifier, not the next feature.** The corpus's single
worst habit is asserting what it has not measured. One module that takes
a claim, states what would falsify it, and runs that — applied to
*itself first* — would have caught eleven of the failures above
automatically, before they shipped into a file a future session reads as
record.

**3. Adopt the corpus's own rule as a gate.** Hedging density is
measurable. A claim that is load-bearing and carries no hedge is a
finding; so is the reverse. That is a checkable property of text, it
costs one pass, and **it would have flagged Barabar, the sacred flag and
the MMM metric before any of them needed a sweep to disprove.**

The arc was worth having. Six files, months of work, and what it
produced — stated at its best — is this: the geometry was right, the
governance was right, the law was right, and **not one of the three was
ever measured by the person proposing it.** That is the gap the next
six files close, or don't.