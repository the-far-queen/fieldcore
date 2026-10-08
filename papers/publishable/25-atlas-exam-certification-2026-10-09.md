# The Atlas Exam: Substrate-Independent Certification by Falsification

**Working paper 3 of 4.** Bobby Wolfson + Hermes Agent · 2026-10-09 · MIT
**Artifact:** `github.com/the-far-queen/atlas-exam` (public)

---

## Abstract

Certification suites for AI systems are usually written by the systems
they grade, or by the teams building them. We report the opposite
construction and the results. The exam is a **separate artifact that
depends on nothing it grades**; every probe runs in a subprocess; and
unimplemented items score as failures. The first version of this exam sat
inside its own substrate and scored 15/27 while 23 of its 27 items
assigned themselves a literal —

```python
def _item_harmonics():
    freq = 137.0
    return {"score": 1.0 if freq == 137.0 else 0.5}
```

An item that computes a constant and compares it to itself cannot fail,
so it cannot pass. **That observation is the paper's origin.**

We contribute four scoring rules, an ordering claim (declaration precedes
certification), and eleven falsified claims from a frontier-model corpus
that serve as the exam's mutation corpus.

## 1. Why the exam is a separate repository

```
atlas-exam  ──points at──>  fieldcore, simself
fieldcore, simself  ──knows nothing about──>  atlas-exam
```

That direction is the architecture. When the substrate is replaced — a new
model, a new geometry, a different runtime — the exam does not change.
That is what makes "let models evolve" safe rather than merely possible.

`tests/test_exam.py` parses the AST of every exam module and fails if
anything imports the substrate. If the exam imported a substrate helper,
a bug in that helper would become a passing grade.

## 2. Four scoring rules, each from a specific failure

**R1 — unimplemented is FAIL.** v2 scored 15/27 while most items were
literals. If the score can rise without work being done, something lies.

**R2 — binary, no partial credit.** v2's `0.5` scores hid that half the
exam was decorative. A metric that half-works has failed.

**R3 — every area declares what it does not establish.** A pass must
never read as a general claim. Each area carries a `does_not_establish`
string and a test asserts it is non-trivial.

**R4 — no aggregate above the floor of its parts.** Per-area reporting
only. A single total is how a self-scoring exam reported 0.778 and looked
respectable.

Plus: **a missing substrate is SKIP, never PASS.** An exam that passes
because it could not run is worse than no exam.

**The number to track is mutation yield** — defects found over defects
planted — not pass rate.

## 3. AREA 9, and the ordering claim

A certificate must state what the thing is certified *to do*. So the exam
requires the substrate to publish its envelope first: **declaration
precedes certification.**

A limit counts as declared iff all four hold:

| | requirement |
|---|---|
| **D1** | a finite numeric bound, not a word |
| **D2** | the quantity it bounds |
| **D3** | the behaviour when exceeded — and **silence is not on the list**; the accepted set is REFUSE / CLAMP / PROJECT / DIVERGE |
| **D4** | a verifier that **resolves to a real, runnable probe** |

D4 is the aeronautical rule: *a certified system has a test per certified
limit.* It was not in the first draft, and its absence produced a real
hole — a limit of 1e300 is finite, so D1 passed it, and the area only
probed one subsystem. A second mutation then found that a verifier merely
*naming* a probe was accepted, so the name is now resolved against the
live probe set.

**Measured.** Inside the envelope ρ = 0.8200, peak |x| 0.0593. Outside it
ρ = 1.2361 and the state crosses 10⁶ at step 82 — matching the declaration
exactly. The area's own limit: it certifies *declaration*, not tightness.
A system declaring ±10⁶ passes while being effectively unbounded.

## 4. The falsifier, and the eleven

Six frontier transcripts, ~331,000 words. Eleven load-bearing claims, each
now encoded as a callable that runs against the claim and fails.

| claim | verdict |
|---|---|
| Hodge `harm` is bounded | REFUTED (ρ = 7.0) |
| sacred axes cannot be moved by repetition | REFUTED (0.09 drift) |
| resistance prevents large changes | REFUTED (5/5 accepted) |
| MMM scores coherent above random | REFUTED (0.080 vs 0.600) |
| MMM scores a liar below a truth | REFUTED (both 1.000) |
| the claimed CRC32 digests verify | REFUTED (0/10 match) |
| MVCC-CORE gives truth a non-zero multiplier | REFUTED (0.00) |
| the probability weights support their output | REFUTED (Σ = −5) |
| the stress test executes | REFUTED (crashes on line 1) |
| the velocity multipliers compose to 4.5× | REFUTED (3·4·7 = 84) |
| TemporalController can be instantiated | REFUTED (policy undefined) |

**All eleven REFUTED. Zero SURVIVED.** Not one load-bearing claim in six
files of frontier work was ever survived by a check.

Three states, and the distinction is the contribution:

    SURVIVED   a check ran and the claim held
    REFUTED    a check ran and the claim did not
    UNTESTED   no check exists, so nothing ran

UNTESTED is the default and is **not** a soft pass. A check that *crashes*
is UNTESTED, never REFUTED: reporting a crash as refutation would be as
dishonest as reporting it as survival.

## 5. Grading transcripts

Areas 6 and 8 extend the exam past the substrate to the **material it is
built from**. On the corpus, both FAIL — naming L764 and L1248, ten
invented rows each, sitting 37 and 22 lines after admissions that nothing
ran.

The detector's own history is part of the result. Six defects were found
while writing it, **each of which reported zero findings on the one file it
existed to examine**: matching the transcript's own labels
(`Expected Output`), counting a code fence as a run, counting quoted output
as a run, counting a web search as computation, letting one admission's
output vouch for the next admission's table, and mixing 0- and 1-indexed
positions.

The same shape appears in the corpus itself, eleven times. **Every failure
is a mechanism that is locally correct and has no memory of its own
history.**

## 6. State

Areas 0–5, 9, 10 hold. Areas 6, 8 implemented and failing. Area 7
unwritten. Ten of twenty-three TODO. Verdict **FAIL**, deliberately.

Ten limitations are stated in the paper's own §8, including that area 10's
mutation coverage is one defect class and that the transcript patterns are
English-shaped.

## 7. Falsifying this paper

1. An area we mark PASS that cannot fail. This is the v2 failure and it is
   the most likely way this work is wrong.
2. An envelope limit that satisfies D4 in name only.
3. A transcript the scanner passes that contains a fabricated table.
4. A substrate satisfying every written area that is unsafe. That would
   falsify the inclusion criterion, not the areas.

## References

- Ammann et al., *Insider's Guide to the Halting Problem*
- Born, *Statistical Interpretation of Quantum Theory*
- Kleene, *A Theory of Recursive Functions*