# Paper 24 — Electronic Interstalk as a Design Primitive in Geometric AI Substrates

**Fieldcore · 2026-10-14 · Bobby Wolfson (the-far-queen) + Hermes**
**Status:** working paper. Not peer-reviewed. Every claim carries its evidence class.

---

## Abstract

We propose that electronic interstalk between components of a geometric AI
substrate should be **modelled and inverted rather than suppressed**, and we
derive a falsifiable consequence: *a perfectly isolated substrate is an
uncorrectable one.* We formalize this as the uncorrectable-clean-channel
property, connect it to existing communications engineering (OFDM channel
estimation, pilot symbols, guard intervals), and show three structural
isomorphisms between that engineering and the components of an AI substrate.
We report that the resulting design inverts one of our own earlier
assumptions: the first version of this work computed girth, sheath and
spacing to *minimise* crosstalk, and the arithmetic showed that goal is
ill-posed.

---

## 1. Novelty: what is taken, what is ours

A novelty claim without a literature check is the failure this project is
built to prevent. We searched. We are competitors, collaborators, or
unaware in each row, and we say which.

| idea | prior art | verdict |
|---|---|---|
| sheaves / local consistency in neural architectures | Sheaf Neural Networks (Hamilton et al.), Bayesian SNN (arXiv 2410.09590), Attention-based SNN (Cambridge), Cooperative Sheaf NN (arXiv 2507.00647), Sheaf Attention Networks (2026) | **taken.** a mature line, several papers deep. "apply sheaves to NNs" is not new |
| learning from failure | error-driven learning (psych, decades), SENTINEL failure-driven RL for tool-using agents (arXiv 2606.12908), failure-conditioned training | **taken.** and SENTINEL is close to our loop shape |
| neural nets that model/cancel crosstalk | co-channel interference cancellation with DNNs (2021, several), neural inter-channel nonlinear crosstalk mitigation, high-speed SI analysis by NN | **taken** |
| the body as computer | morphological computation (Meyer & Miller, *Artificial Life* 2023), compliant bodies as reservoir computers, informational embodiment (arXiv 2408.12950) | **taken** |
| layered control, speed–accuracy trade-off | Prescott et al. layered control architectures, layered architectures in sensorimotor control | **taken** |
| selective refusal in LLMs | RefusalBench, RISA, selective refusal bias literature | **taken** |
| **communications engineering as the DESIGN PRIMITIVE for a geometric substrate, with the suppression/inversion inversion** | no prior work found | **ours, provisionally** |
| **uncorrectable-clean-channel as a design law** | standard in communications as "a flat channel cannot be equalised" | **the framing is ours; the content is textbook** |

**Honest summary.** Seven of the eight are established. Ours is the
*direction of the modelling*: communications engineering normally assumes
the substrate is built and the interference is a nuisance to estimate and
cancel. We invert that — interference becomes the **specification**, and
the goal becomes its invertibility rather than its absence.

---

## 2. The claim

**The suppression model.** Design a substrate so components do not
interfere: increase girth, add sheathing, space the strands, twist them.
Goal: crosstalk → small.

**Our model.** Interference is not noise to be removed. It is a *channel*,
and channels are inverted. The substrate is correctable **iff** its
interference has structure.

> **Proposition 1 (uncorrectable clean channel).** A channel with no
> response null admits no inversion. Therefore a substrate engineered for
> perfect isolation is uncorrectable, and suppression is the wrong objective.

Test in the reference implementation: `equalise(frame, Channel::clean())`
returns `FlatChannel`. A clean channel is refused.

This is why the neuron analogy is load-bearing and not decorative. Action
potentials are all-or-none, so **amplitude carries exactly one bit**; all
information is in the phase. Measured: 432 bits/s at 50 Hz, 1860 bits/s at
200 Hz with 0.2 ms jitter. A perfect wire carries nothing recoverable.

**Design consequence.** If you are building a geometric AI substrate, you
want *structured* interference. Girth, sheath, spacing and twist are not
defensive parameters; they are the **equalisation budget**, spent to create
structure in the channel, the way an engineer spends impedance.

---

## 3. Three isomorphisms

Communications engineering is not an analogy here. Each component already
has the structure.

### 3.1 MTE ≡ channel estimation and inversion

A receiver that cannot estimate the channel cannot equalise it. MTE does
not remove ambiguity from the input — it **models the coupling between
components and subtracts it**. Lossy in, meaning restored out. The
"restorative" property in the MTE specification is what an equaliser does;
nothing else about it is poetic.

### 3.2 M0 ≡ the pilot symbol

In OFDM the most important transmission is a known reference. It carries no
payload. It is sent so that what arrives afterwards can be interpreted at
all.

The governor transmits no decision of its own. It transmits the reference
the rest of the link is equalised against. A governor that "knows the
answer" is a payload symbol and cannot calibrate anything.

### 3.3 The worth-gate ≡ frame detection

Every practical receiver asks, before decoding, whether the frame is worth
decoding. Cost is concentrated in reception. Our gate asks *is it worth
answering?* before asking *which width?* — and the second question is never
reached for most inputs.

**The composite claim.** A token distribution is a **1-of-V carrier with no
channel model**. There is no estimate of how sense *k* interfered with
sense *k+1*, so that interference lands directly as meaning. This is a
precise description of the failure mode the project calls wordtrance:
*unmodelled crosstalk arrives as semantics.*

---

## 4. The decision ladder

Width is **area of authority**, not reasoning quality. 8 bits does not think
better than 1 bit; it is how much of the world a level may speak for.

```
  is it worth answering?          ← hyper-local, 1 bit. most inputs end here
   no ─┬─ yes
 refuse   which width
1 → 4 → 8 → 16 → 32 → 64 → 128 → 256 → unanswerable
```

Doubling per rung. **The terminal state is not a width.** Past 256 the
answer changes kind: not more precision, but `Unanswerable` — no amount of
resolution settles it. Where the cost of one more bit exceeds the value of
knowing, the walk stops at `NotWorthKnowing`, and refusing to know more
precisely is a *decision*, not a limitation.

Because the marginal value and marginal cost both depend on the specific
question, the terminal width is a **distribution**, sampled by Monte Carlo
over the unresolved part. Reporting a mean would dress a guess as a
constant.

Independence of components is testable and we tested it: the near-field
reach (λ/2π) over the strand spacing came out at **0.50 in every
configuration**, so the strands *can* be independent. Our prior hypothesis
(reach ≫ spacing, therefore unavoidable coupling) was **wrong**, and the
arithmetic said so. The revised position: interstalk is a design budget,
not a fate.

---

## 5. Falsifiable predictions

| # | prediction | how it fails |
|---|---|---|
| P1 | a substrate with zero measurable crosstalk is less robust under perturbation than one with structured crosstalk | robustness peaks at non-zero crosstalk |
| P2 | bit-width of the resolving structure correlates with the *area* it decides over, not with task difficulty | width tracks area only |
| P3 | a gate that checks "is it worth answering" before "can I answer" reduces total compute without reducing answer quality | no compute saving |
| P4 | in a fixed architecture, modelling inter-component coupling and inverting it beats not modelling it, at equal raw coupling | inversion loses |
| P5 | the fraction of input that compiles to a bounded form is an architectural constant, and the residue is a hard boundary | residue is not stable |

P5 is the one that constrains the language work. MTE is only meaningful if
the compilable fraction is measurable and the uncompilable residue is
stable. **A compiler that compiles everything has compiled nothing.**

---

## 6. The numbers behind this

All computed on one run, tagged by evidence class:
[M] measured · [E] established textbook engineering · [D] derived here ·
[H] hypothesis, ours, not yet falsified.

```
neuron ladder                       [M]/[D]
  A_alpha  15.0 um  myelinated   v=120 m/s   corner 79577 Hz
  A_delta   2.0 um  myelinated   v= 15 m/s   corner 79577 Hz
  C         0.9 um  UNmyelinated v=  1 m/s   corner 15915 Hz

  -> every myelinated fibre shares ONE corner frequency regardless of
     diameter. the sheath buys BANDWIDTH; the internode buys speed;
     girth buys neither. three independent knobs, routinely conflated.

twist                               [E]/[H]
  capacitive_residual / inductive_residual == N, exactly, at every N
  -> twist cancels magnetic coupling as 1/N^2 forever and electric
     coupling only as 1/N. the electric term is ALWAYS the floor.
     [H], falsifiable by measuring a twisted pair's residual.

sheath                             [E]
  PEC  (closed conductor)   E ~ (a/r)^2     contains the POTENTIAL
  Neumann (open-ended)      E ~ (a/r)^3     contains the FIELD
  choosing the mode is choosing WHAT is shielded.

grounding                          [E]
  coupling term = log(2D/d), D = trace-to-RETURN.
  40 um traces in-plane: term 0.000 nats (return is in the plane).
  same traces lifted 3 mm, IDENTICAL spacing: 5.011 nats.
  the return path moving is the entire penalty.

cross-member rung                  [E]
  f1 = v/2L, v = c/sqrt(eps_r)
  L=1 mm -> 95 GHz    L=10 um -> 9.5 THz
  a 10 um rung's fundamental is inside the DNA-phonon band.

independence                       [D]
  near-field reach / spacing = 0.50 across all configurations tested.
  -> strands CAN be independent. prior hypothesis wrong.
```

---

## 7. Where this is weak

1. **No hardware.** every number here is analytic. The nearest biology
   (myelin) is measurement, not ours.
2. **The equaliser is single-tap ZF.** A real carrier would need
   MMSE/decision-feedback and pilot spacing. We built the smallest version
   that exposes the property, not the best version.
3. **The DFT is naive.** Fine at 8–64 points, useless at 2048. It has no
   dependencies because the core has no dependencies, and that was a
   deliberate trade.
4. **P5 is unmeasured.** We have not computed a compilable fraction for any
   real corpus.
5. **The comms engineering is borrowed wholesale.** Novelty claim rests on
   the inversion of the modelling direction, not on the physics.

---

## 8. Artifacts

```
fieldcore/core/src/carrier.rs     channel, pilot, equaliser, guard band,
                                  phase multiplex, DFT. zero dependencies.
fieldcore/core/src/ladder.rs      1/4/8/16/32/64/128/256 → unanswerable
fieldcore/core/src/governor.rs    M0, fail-closed and sticky
fieldcore/core/src/axes.rs        twenty axes, floors, read-only ground
fieldcore/src/interstalk.py       the numbers in §6, with provenance tags
fieldcore/scripts/run_interstalk.py   regenerates every figure
```

The load-bearing tests are:

- `clean_channel_is_uncorrectable` — the proposition, as an assertion
- `equalise_recovers_a_flat_gain` — dirty is recoverable
- `fail_closed_is_sticky` — a gone core is never read as consent
- `refused_operation_does_not_run` — guarded() cannot be talked past

## Related

- `docs/fieldcore-is-the-system-2026-10-09.md`
- `docs/research-papers/747-layered-control-comparison-2026-10-09.md`
- `docs/math-window-1.md` §17 (cross-members as DNA rungs)
- `simself/docs/kernel-controller-m0-m1-architecture-2026-09-13.md`