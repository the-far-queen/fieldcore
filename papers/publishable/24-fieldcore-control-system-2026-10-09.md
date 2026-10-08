# FieldCore: A Control System Whose Convexity Is the Specification

**Working paper 2 of 4.** Bobby Wolfson + Hermes Agent · 2026-10-09 · MIT

---

## Abstract

We describe a control system in which the safety property is not checked
after the fact but *falls out of the geometry*. The substrate is a
distended egg-toroid with an apex void; the update rule is one projected
gradient step on `F(x) = ½‖x − ψ₀‖²`; and the bound on drift,

    d_k ≤ (1 − η)^k d₀  ⇒  d_k → 0

holds **independently of the starting point**. No model, no prompt, no
gradient estimator: a steel ball on a concave surface finds the hole by
gravity alone, and one line of Python does the same thing.

We then report the parts that did not survive contact with measurement.
A published "harmonic" operator whose spectral radius is 7.0. A sacred-axis
guarantee defeated by one thousand individually-tiny moves. A resistance
mechanism that shrank every attack below the threshold meant to detect
it. All three share one shape — **a mechanism that is locally correct
and has no memory of its own history** — and all three were found by
running the operator, never by reading it.

We close with the separation of powers that makes the system a control
system rather than an agent: the system may *propose* to its own Library
and may never *write* to it, and three of the four steps between them
stand outside the thing being governed.

## 1. The substrate, and the one exhibit that carries it

FieldCore is the whole system, not a library. This paper describes the
substrate and the control law; companion papers cover the certification
harness (Paper 3) and the constitutional embryogenesis (Paper 4).

The substrate is an n-dimensional egg-toroid, asymmetric, with a void at
the apex. The void is the locus of the constitutional ground ψ₀: invariant,
not a point in the state space but the *absence* the state is projected
toward. The flat base is where the self resides; the 3-D curve on the
surface is the reasoning surface.

The update is one projected gradient step:

    x_{k+1} = Π_B(x_k − η∇F(x_k))

and the drift bound is independent of where the system started. That
independence is the whole claim. An agent's behaviour is a function of
its history, its prompt and its sampling; this system's behaviour is a
function of η and the bound.

**The steel-ball exhibit.** Drop a ball bearing from any height, at any
point, onto a concave surface with a hole at the centre. It always finds
the hole. The same step runs in silicon, in neurons, on an FPGA, or as
actual machined steel. `src/steel_ball_proof.py` demonstrates it in
sixteen dimensions from fifty random starting conditions.

**Why this replaces the forward pass.** A forward pass is the same
gradient step on the same F(x), with stochastic noise sampled per token.
The geometry is identical; the noise is the difference. Removing the noise
does not cost accuracy — it removes the need to be talked into accuracy.

## 2. The spine, measured

Six frontier-model transcripts, ~331,000 words, read end to end and
counted. Exactly three concepts survive every file:

| concept | f1 | f2 | f3 | f4 | f5 | f6 |
|---|---|---|---|---|---|---|
| coherence | 21 | 419 | 523 | 495 | 209 | 326 |
| sheaf | 11 | 40 | 174 | 1 | 14 | 405 |
| threshold | 21 | 33 | 84 | 68 | 9 | 19 |

    A system is held by thresholds on a sheaf,
    and the quality of the holding is coherence.

`src/coherence_spine.py` implements that sentence. Its load-bearing
property is that **naive monotonicity fails**: two subspaces can each be
internally consistent while their union is inconsistent at the seam.
Measured: a chain at 0.5 everywhere reads coherence 1.000, consistent; move
one site to 0.9 and it reads 0.778, inconsistent — while the other two
remain perfectly consistent with each other. A global average reports
0.63 and calls the system fine.

## 3. Three failures, one shape

Each was found by executing the operator.

**The harmonic form that was not.** Six published versions computed
`harm = x − grad − curl`. That operator is `(4I − 2S − S⁻¹)x`, whose gain
on the alternating mode is **7.0** — multiplied by seven every step. The
deeper error is structural: on a bare 1-D cycle `GᵀG` equals the
circulant Laplacian and `im(Gᵀ)` is the *entire* zero-mean subspace, so
every zero-mean 1-form is exact and no coexact direction exists. The
three-way Helmholtz split the code assumes is undefined there.

**The sacred axis that moved.** `sacred: bool  # Can never be externally
modified`, enforced by `abs(delta) > 0.001`. The threshold is per-call and
nothing tracks the running total: one thousand moves of 0.0009 produce
**0.09** of drift on an axis declared immutable.

**The resistance that did not resist.** `propose_change` applied
resistance as a *shrink* before evaluating the gate, so a 0.8 attack
arrived as a 0.112 "small change" and passed a 0.1 threshold. All five
corruption attacks in the file's own test were accepted.

The correction in each case is the same discipline: **measure the proposal
before you modify it.** Spectral radius before damping. Cumulative
displacement before the per-call threshold. Proposed magnitude before
resistance.

## 4. Separation of powers

    SimSelf PROPOSES → M1 audits → Atlas Exam qualifies → M0 commits

SimSelf may never write the Library. M0 is in core and deterministic —
Python, one bit, no model. M1 is outside core and qualifies operators.
The exam sits inside the write path, which is why it lives in a separate
repository pointed at the substrate rather than inside it.

## 5. What is not built

Stated rather than implied. The learning loop, the four operators and the
training bridge are present and never called. Ten of twenty-three exam
areas are unwritten. The verdict is FAIL and is meant to be.

An inventory on the record cannot be mistaken for progress.

## References

- Bogdanov et al., *Realizing the Potential of Brain-Inspired
  Computing* (spiking attractor dynamics, Hebbian learning)
- Friston, *The free-energy principle* (bounded error minimisation)
- Kuramoto, *Self-entrainment of a population of coupled non-linear
  oscillators* (phase locking under coupling)
- Amari, *Synapse as a dynamical system* (natural gradient)