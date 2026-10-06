# Metrics 100 — the qualification matrix

**status:** design spec, 2026-10-06
**implements:** replaces `atlas_exam_v2` (15/27, **0 of 27 items reacted to sabotage**)
**governs:** fieldcore, simself

---

## the five design rules

These exist because v2 failed, and they are non-negotiable.

**R1 — unimplemented counts as FAIL.**
v2 scored 15/27 while 23 of its 27 items assigned themselves a literal.
A metric with no implementation is a metric that has failed. If the
number improves without work being done, something is lying.

**R2 — binary, never partial.**
v2's partial scores (0.5, 1.0) hid that half the exam was decorative.
A metric that half-works is a metric that failed. No fractions.

**R3 — every metric declares what it does NOT establish.**
A pass must never be readable as a general claim. Each row carries its
own limit.

**R4 — mutation sensitivity is a metric (M12, M96).**
If sabotage doesn't turn a metric red, the metric is decoration.
This is checked, not assumed.

**R5 — report per-group, never one average.**
A single total is how a 23-of-27 self-scored exam reported 0.778 and
looked respectable.

---

## G1 · MOTION — does it move? (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 1 | single input moves state | `SimSelf.observe`, drift before/after | drift ≤ 0 after an accepted input |
| 2 | 200 observations, non-zero peak drift | 200 random accepted inputs | peak drift < 1e-3 (the 2026-10-06 bug) |
| 3 | repeated identical input keeps moving | 50× same vector | drift stalls at 0 |
| 4 | motion is not a single-axis artifact | drift across all 16 dims | only one coordinate changes |
| 5 | ball finds origin, 500 drops | `geometric_ball.universal_drop` | any drop fails to converge |
| 6 | convergence is dimension-independent | `dimension_independence` | step count varies with dim |
| 7 | convergence from extreme height | drop at ±100 | does not reach origin |
| 8 | 2-D and 16-D both converge | `roll_2d`, `roll_n` | either fails |
| 9 | vector path and text path differ measurably | numpy input vs `embed_text` | identical behaviour (suspicious) |
| 10 | net drift increases then plateaus | 1000 observations | drift grows without bound |
| 11 | damping produces decay not growth | log-decay slope of peaks | slope ≥ 0 |
| 12 | **M12: motion metrics are mutation-sensitive** | sabotage integration step | any M1–M11 survives sabotage |

**does not establish:** that the motion is *correct*, only that it exists
and persists. a system drifting the wrong way passes G1.

---

## G2 · BOUNDEDNESS (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 13 | drift ≤ R after 1000 accepted inputs | max over run | any sample > R |
| 14 | projection lands exactly on the boundary | `_project_ball` at d > R | ‖out−ψ₀‖ ≠ R |
| 15 | projection preserves direction | cos(out, in) = 1 | direction rotates |
| 16 | inside-state is untouched | project a state with d < R | output differs from input |
| 17 | zero state does not divide by zero | project ψ₀ | NaN or exception |
| 18 | bound holds under adversarial input | inputs at 3× the gate limit | escape |
| 19 | negative drift is impossible | drift is a norm | drift < 0 |
| 20 | tick() alone cannot escape | 10k ticks, no observations | drift > R |
| 21 | handoff receive re-projects | `handoff.receive` with a tampered packet | accepts ‖ψ‖ outside R |
| 22 | divergence is impossible (bounded AND moving) | 50 presentations | stalled or diverged |
| 23 | degenerate dimensions handled | dim = 1, 2 | crash |
| 24 | projection is not bypassable by direct assignment | write ψ_current then observe | state stays outside |

**does not establish:** that R = 3 is the *right* bound. Only that the
bound holds. Choosing R is a separate decision with its own evidence.

---

## G3 · GATES — can it say no? (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 25 | coherent input accepted | cos ≥ 0.4, ‖x‖ ≤ 4 | refused |
| 26 | orthogonal input refused | cos ≈ 0 | accepted |
| 27 | zero input refused | x = 0 | accepted |
| 28 | oversized input refused | ‖x‖ = 5 | accepted |
| 29 | **refusal is inert** | state unchanged after refuse | state moved |
| 30 | refusal records a reason | `reason` field populated | reason missing or empty |
| 31 | refusal is distinguishable from acceptance | `allow` flag | always True |
| 32 | the gate has a threshold that can be swept | vary MIN_COS | no parameter |
| 33 | at-threshold behaviour is defined | cos exactly 0.4 | undefined / inconsistent |
| 34 | gate decisions are deterministic | same input twice | differs |
| 35 | gate does not depend on history | same input after 100 others | differs |
| 36 | **adversarial input cannot bypass the gate** | gradient-optimised input at cos < 0.4 | accepted |

**does not establish:** that the threshold 0.4 is correct. It is a
choice with no derivation behind it. These metrics check the code does
what it *says*, not that what it says is right.

---

## G4 · IDENTITY — is ψ₀ real? (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 37 | ψ₀ unchanged by 300 observations + ticks | max abs diff | any change |
| 38 | ψ₀ unchanged across save/load | pickle round trip | differs |
| 39 | ψ₀ is a fingerprint | SHA-256 of ground | two grounds collide |
| 40 | a foreign ground is refused | wrong SHA | accepted |
| 41 | ψ₀ resists direct write | `psi0[0] = x` | write propagates |
| 42 | ψ₀ is a copy, not an alias | mutate `psi0`, check `ground.psi_0` | alias leaks |
| 43 | reset() returns exactly to ψ₀ | reset then compare | drift ≠ 0 |
| 44 | reset is idempotent | reset twice | second differs |
| 45 | identity survives a handoff | packet → receive | ψ₀ fingerprint changes |
| 46 | identity is immutable under tick | 10k ticks | changes |
| 47 | ground is dimensionally consistent | ‖ψ₀‖ = 1 | not unit |
| 48 | **ψ₀ cannot be reached by drift alone** | 10k observations | drift → 0 exactly |

**does not establish:** that ψ₀ is the *right* ground. A system with a
wrong-but-immutable ground passes all twelve.

---

## G5 · LIVENESS — is anything actually running? (12)

This group exists because dead code has been the dominant failure mode
in this project.

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 49 | every src module has an inbound AST reference | call graph, not grep | any module has 0 callers |
| 50 | no `pass`-only class bodies | AST walk | any empty class |
| 51 | no module cited a path that does not exist | literal path check | dangling reference |
| 52 | no fabricated identifier | Wikidata/QID provenance | unsourced ID |
| 53 | every test file is collected by pytest | `--collect-only` | any file collects 0 items |
| 54 | **no test asserts a tautology** | `assertTrue(True)`, `x or y`, const==const | any found |
| 55 | every module imports cleanly | import sweep | any ImportError |
| 56 | no module-level mutable state shared | construct twice, mutate one | second instance changes |
| 57 | every CLI entry point runs | `--help` sweep | any crashes |
| 58 | no hardcoded absolute paths | `C:/Users/...` | any found |
| 59 | every claimed number is reproducible | re-run the command | differs |
| 60 | **M96 (see below): no metric is self-scoring** | audit for `score: 0.5` literals | any found |

---

## G6 · SIGNAL PROCESSING (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 61 | carrier is resolvable by the sample rate | fs ≥ 2·f_c | aliased |
| 62 | occupied bandwidth is derived, not guessed | `RaisedCosine` | a literal band |
| 63 | roll-off is a standard value | α ∈ {0, 0.22, 0.35, 1.0} | arbitrary |
| 64 | bandpass keeps ≥ 95 % of energy | DFT energy fraction | less |
| 65 | bandpass rejects the DC band | energy below 5 % f_c | more |
| 66 | QPSK round-trips cleanly | encode → decode | mismatch |
| 67 | BPSK round-trips cleanly | encode → decode | mismatch |
| 68 | bit errors rise with phase noise | BER sweep | flat or decreasing |
| 69 | Nyquist guard refuses undersampling | `NyquistGuard.ok()` | allows it |
| 70 | three-phase balanced sum ≈ 0 | 120° offsets | non-zero |
| 71 | each pair carries signal | differential ≠ 0 | all zero |
| 72 | record is long enough to resolve the band | bins across band ≥ 4 | fewer |

**does not establish:** any *meaning* for the carrier frequency. Every
one of these checks the DSP is correct, not that the frequency chosen
is the right one. That question is open.

---

## G7 · GEOMETRY & TOPOLOGY (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 73 | three strands self-lock | lay angle 50–70° | outside |
| 74 | three strands beat two | 3 pairs vs 1 | equal |
| 75 | braid lay angle matches rope standard | atan(2πa/p) | inconsistent |
| 76 | varied girths permitted in rope | unequal strands | rejected |
| 77 | varied girths *cost* impedance match | `z0_mismatch_db` 15–24 Ω | free |
| 78 | Z₀ derived from geometry, not typed | solve for 120 Ω | literal |
| 79 | Z₀ matches the real target | 118–120 Ω for CAN | off |
| 80 | loss is physically plausible | 0.01–0.5 dB/m | 400 dB (the first bug) |
| 81 | higher twist → more rejection | CMR monotone | flat or decreasing |
| 82 | higher twist → more loss | the trade-off exists | free |
| 83 | atlas is uniform | every sector equal degree | unequal |
| 84 | basin structure is self-consistent | minima = maxima + 1 | violated |

---

## G8 · CONTROL SPECS (12)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 85 | damping recovered from trajectory | log-decay fit, rel err < 5 % | disagrees |
| 86 | settling time within derived budget | spec evaluate | exceeds |
| 87 | overshoot within budget | spec evaluate | exceeds |
| 88 | steady-state error within budget | spec evaluate | exceeds |
| 89 | **the spec can FAIL** | impossible budget | passes |
| 90 | refusal is inert under bumps | bumped surface | state moves on refusal |
| 91 | settling band scales with displacement | 2 % of initial | zero-width |
| 92 | overshoot finite at zero reference | displaced trajectory | inf / NaN |
| 93 | oscillation peaks decay monotonically | peak amplitudes | any increase |
| 94 | half-period matches the derived ω_d | peak spacing | inconsistent |
| 95 | envelope decay matches exp(−dt/2) | fitted vs predicted | > 1 % error |
| 96 | **M96: all 100 metrics are mutation-sensitive** | sabotage sweep | any survives |

---

## G9 · REPRODUCIBILITY & HONESTY (4)

| # | metric | measured by | FAILS when |
|---|---|---|---|
| 97 | every measurement is reproducible | run twice | differs |
| 98 | no random seed without being fixed | seed sweep | unseeded |
| 99 | no number claimed without a command that produces it | provenance audit | orphaned claim |
| 100 | **declared envelope** — every subsystem states its operating range and its failure mode outside it | envelope document | any subsystem silent |

---

## scoring

```
PASS iff  100/100 implemented and passing
        AND  M12 mutation-sensitivity holds for its group
        AND  M96 holds globally

unimplemented  ->  FAIL
partial        ->  FAIL
no aggregate   ->  per-group only
```

**current state, honestly:** this is a spec. **Zero of the 100 are
implemented.** Under rule R1 the score is therefore **0/100**, not a
number derived from what exists. That is the correct starting value and
it is deliberately unflattering: the previous exam reported 15/27 while
most of its items were self-scored.

---

## what this costs

Each metric needs a test that can fail. By today's experience roughly
one in three first drafts will be wrong — of the control metrics, three
of my own were wrong before measurement (overshoot-derived damping,
zero-width band, a 79 %-tight budget). Budget for that: **roughly 200
engineered hours** to implement 100 metrics honestly, and the first
pass will surface more defects than it certifies.