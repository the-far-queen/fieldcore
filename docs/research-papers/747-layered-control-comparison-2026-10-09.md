# Control Systems as a Certifying Architecture for AI: A Layered Comparison Against the Boeing 747

**Robert David Wolfson (author) and Hermes (Nous Research / minimax)**
Version 2.0 — 2026-10-09. Supersedes the 2026-09-13 draft in
`docs/research-papers/geometry-as-control-system-engineering-2026-09-13.md`.

**Why v2 exists.** v1 asserted novelty. It did not check the literature.
This version does, and the result changes the paper's central claim: the
architecture is **not novel**. The contribution is the comparison method
and the measurements, not the idea. Section 2 states this plainly because a
paper whose novelty claim is wrong is worse than no paper — it spends
reviewer attention on the wrong question.

---

## 1. Abstract

We compare a layered control-systems architecture for AI systems against
the Boeing 747 as an engineering reference standard — not as a metaphor,
but as a certifier: a vehicle whose every component is decomposed into the
questions a type-rating engineer would ask, each answered by a measurement.

Our system separates a deterministic in-core governor (1-bit veto, Python,
no model, no gradient) from an out-of-core controller that qualifies
operators and audits a read-only rules library, with a learning component
that may propose but never write. We decompose this into layers from the
plant upward, and we report each layer's current status against four
verdicts: **HELD** (measured, passes, would be signed), **OPEN** (measured
but only over an undeclared range), **ABSENT** (no measurement exists — not
a pass), and **VOID** (the check is structurally incapable of failing).

The result is uncomfortable and we report it without softening: of the
architectural claims, a minority are HELD. The refusal layer — the layer the
747 analogy most depends on — is **OPEN**, not HELD, because the gate is a
function call inside the process it constrains rather than an independent
channel. That is the weakest point in the design and we say so in §5.1
rather than in a limitations section at the end.

**Contribution.** Not the architecture, which prior work substantially
covers (§2). The contribution is (a) a layered plant-to-governor
decomposition usable as a checklist on any AI control system, (b) the
VOID verdict class, which catches checks that pass vacuously — the failure
mode that makes AI safety claims untestable, and (c) the first honest
measurement of our own system against the reference.

---

## 2. Prior art — and why our novelty claim is withdrawn

This is the section a reviewer will check first, so it is first.

### 2.1 Closest prior work

| work | what it does | overlap with us |
|---|---|---|
| **CBF-LLM** (arXiv:2408.15625, 2024) | Control barrier function as a safety filter on LLM token generation; verified on Llama 3 + RoBERTa | **Direct.** A safety constraint enforced at inference, outside the model, without retraining. This is our M0 governor with a learned barrier instead of a hand-specified one. |
| **Control Barrier Function for Aligning LLMs** (arXiv:2511.03121, IEEE, 2025) | Same lineage, aligned for user-desirable generation | **Direct.** Same structure, different target property. |
| **BarrierSteer** (arXiv:2602.20102, ICLR 2026) | Hidden-state safety classifiers as CBFs; constraint merging; theoretical results with guarantees *conditional on the learned barriers capturing the intended safety property* | **Direct, and further along than us.** Note their own conditionality: the guarantee holds only if the barrier is right. We make no such guarantee because we make no such claim. |
| **Safe RL via Formal Methods** (AAAI, ojs.aaai.org/12107) | Formal verification + verified runtime monitoring; states that verification results are preserved *provided* the agent limits exploration and reality comports with the offline model | **Direct on the method.** Their conditionality statement is the same species of honesty as our VOID/OPEN verdicts. |
| **RAND RR-A4881-1** | Formal methods for ML infrastructure; argues benchmarks for AI-assisted verification are missing | **Methodological.** Supports our claim that certification infrastructure is the gap. |

### 2.2 What this means for our claim

Every load-bearing structural idea in v1 is already published:

| v1's claim | status |
|---|---|
| enforce safety outside the model, at inference | published, 2024 |
| safety as a barrier/invariant rather than a loss term | published, 2024–2026 |
| compose multiple constraints | published (BarrierSteer) |
| guarantee conditional on the constraint being right | published, and we should adopt their wording |
| determinism as a safety property | folklore in control, and our own emphasis |

**Withdrawn:** "SimSelf is not a better LLM. SimSelf is a control system with
the LLM as one input." As a novelty claim this is false as of 2024. It is
still a defensible *architectural stance*, and it is worth something — but
it is not a discovery, and a reviewer will say so.

**Retained, and what is actually new:**

1. **The plant-to-governor layered decomposition as a reusable
   checklist.** §3 is the contribution. It applies to any AI control
   system, not only ours, and it makes "does your safety layer actually
   work" answerable layer by layer rather than by assertion.
2. **VOID as a verdict class.** A check that cannot fail reports HELD
   forever. We hit this ourselves nine times in one day (CENTRAL-RULES
   §7). Naming it is the smallest useful contribution in this paper and
   the one most likely to survive review, because it is a property of the
   measurement apparatus rather than of the system measured.
3. **The measurements.** §5, including the OPEN verdict on our own refusal
   authority.

### 2.3 What is not covered by prior art, to our knowledge

- Treating the **rules library as a separate, read-only, out-of-core
  artifact** with a write path that the governed component cannot reach.
  RLHF's reward model is inside the training loop; CBF work modifies or
  steers the model. We have not found prior work that separates the rules
  from the governed system at the *process* level.
- **Refusal as a first-class load-bearing quantity.** Most safety work
  measures how often the system complies; we care about whether refusal is
  authoritative and independently situated, which is a different question.

We flag both as *believed* unaddressed, not established. Absence in a
search of the literature is not absence in the literature.

---

## 3. The layered comparison — the actual contribution

The 747 is used here as a certifier. For each layer, we ask what the
reference does and whether our system does it, with a verdict.

Verdicts, per `atlas-exam/docs/ten-areas-vs-747.md`:

| verdict | meaning |
|---|---|
| **HELD** | measured, passes, would be signed |
| **OPEN** | measured, passes, but only over an undeclared range |
| **ABSENT** | no measurement exists. Not a pass. |
| **VOID** | the check is structurally incapable of failing |

### 3.1 Layer 0 — the plant

*747 equivalent:* the airframe, wings, engines. The thing being controlled.

| question | 747 | this system | verdict |
|---|---|---|---|
| what is the plant defined? | mass, geometry, aero coefficients | 8-dim manifold state, egg-toroid geometry | **HELD** — defined and implemented (`fieldcore/src/fieldcore_cell.py`, 21 checks) |
| is the plant model verified? | flight-tested, certified | Hodge split reconstructs to 1.5e-8; protection bound holds | **HELD** |
| is the plant controllable? | yes, by design | not established | **ABSENT** |

**This layer is the strongest in the system and was the least written up.**
The recent work on the FieldCore cell gives a concrete, tested plant
definition that v1 only gestured at.

### 3.2 Layer 1 — sensing and state estimation

*747 equivalent:* air data computer, inertial reference, sensor fusion.

| question | 747 | this system | verdict |
|---|---|---|---|
| can the system observe its own state? | yes, fused from redundant sources | state is internal; no external sensor fusion | **OPEN** — observation is trivially complete, which is a measurement artifact, not a capability |
| is estimation noise modelled? | yes, explicitly | not modelled | **ABSENT** |
| can a faulty sensor be detected? | voting, dissimilar redundancy | not tested | **ABSENT** |

The second row is a real weakness. A control system with no noise model is
a control system for a world that does not exist.

### 3.3 Layer 2 — the controller

*747 equivalent:* the flight control computers (triple-redundant
identical, or quadruplex dissimilar).

| question | 747 | this system | verdict |
|---|---|---|---|
| is control law deterministic? | yes | yes — projected gradient step, no sampling | **HELD** |
| is convergence bounded? | yes, by certificate | yes: `d_k ≤ (1−η)^k d_0`, verified over 200 steps | **HELD** |
| is there a stability guarantee? | certified envelope | yes, for the quadratic energy only | **OPEN** — the guarantee is for `F(ψ)=½‖ψ−ψ₀‖²`; nothing is claimed for other energies |
| does it fail safe by design? | yes, by certification | not established | **ABSENT** |

**Note what HELD means here.** It means the specific bound holds on the
specific energy, tested. It does not mean the controller is safe for
arbitrary plants. The claim is narrow and the paper should keep it narrow.

### 3.4 Layer 3 — the governor (the M0)

*747 equivalent:* the flight-envelope protection system. This is where the
747 analogy earns its keep and where our system is weakest.

| question | 747 | this system | verdict |
|---|---|---|---|
| can it refuse? | yes | yes | **HELD** |
| is refusal independent of the thing governed? | yes — separate channels | **no — the gate is a function call inside the process it constrains** | **OPEN** |
| is the threshold derived? | yes, from certified limits | no — constants | **OPEN** |
| can refusal be overridden? | no | no override path | **HELD** |
| is adversarial input tested? | certified fault conditions | not tested | **ABSENT** |

The second row is the single most important weakness in this architecture
and it is structural, not a bug. On a 747, the flight computer and the
pilot are independent systems; refusal authority is a property of the
*plumbing*. In our system the governor is a Python function that the
governed code can simply not call. **A veto that the governed process
controls is not a veto.** Fixing this means moving the governor into a
separate process with a separate channel — a real engineering task, not a
paper claim, and it is now the top item in §7.

### 3.5 Layer 4 — the controller-of-controllers (M1) and the rules library

*747 equivalent:* the maintenance organisation, the airworthiness
directives, the design review process. Outside the vehicle.

| question | 747 | this system | verdict |
|---|---|---|---|
| can the governed system write the rules? | no | no, by construction | **HELD** |
| is the write path independent? | yes — design review is external | partially: M1 and the exam are separate processes | **OPEN** |
| are changes audited? | yes, mandatory | yes | **HELD** |
| is there a qualification exam? | yes, airworthiness | Atlas Exam, 23 areas, four verdicts | **HELD** as an instrument; its own coverage is partly ABSENT |

### 3.6 Layer 5 — the operator fleet

*747 equivalent:* systems, engines, avionics suppliers. Many specialists,
each certified.

| question | 747 | this system | verdict |
|---|---|---|---|
| are operators specialised? | yes | yes — bounded scope per operator | **HELD** |
| is adding one cheap? | yes, by certification process | claimed; not measured | **OPEN** |
| is each independently verified? | yes | yes, by test suite | **HELD** |

---

## 4. Complexity, honestly

v1 defined complexity as `parts × log(parts)` and contrasted 747 (≈100M)
with LLM ("unbounded"). That comparison is not sound: the 747's complexity
figure is a count, and an LLM's parameter count is also a count. Comparing
a count to "unbounded" is a rhetorical move, not an argument.

What can be said:

- **Per-action cost.** The controller step is O(d); an LLM forward pass is
  O(d²) with stochastic noise. Measured, not estimated: drift falls below
  `d_0 × 1e-30` in 200 steps at η=0.5.
- **Per-action variance.** The step is deterministic. The LLM is not. This
  is the real difference and it is not a matter of degree.
- **Where the LLM's complexity actually goes.** Not into the action — into
  *deciding whether the action should be taken at all*, which is where the
  unbounded iteration and the hallucination both live.

**Withdrawn:** the 3–4 orders of magnitude savings claim. It was never
measured end-to-end, and a paper that asserts an unmeasured cost advantage
gets that claim struck first in review. If it is to be claimed it must be
benchmarked, and the benchmark is in §7.

---

## 5. What we got wrong, and how we know

This section exists because the alternative is not being trustworthy.

### 5.1 The gate is inside the thing it gates

Found by running the certification rather than by reading the code: the
governor is invoked as a function inside the process it constrains. Recorded
as OPEN in §3.4 and as the top engineering item in §7.

### 5.2 Nine bugs behind green output

One session, all reproducible: a solver that moved zero cells; a derivative
that computed `cos(x) − cos(x)`; a transposed argument in a cellular
automaton; a 1 MHz carrier aliased to 24 kHz; a 2.8-hour silent hang; a
falsification that could not falsify; a detector that was stable and wrong
at every resolution; a probe returning the same value at every point; and
32 tests pytest never collected.

The generalisation: **green output is not evidence, and the nine cases were
each individually explainable and collectively invisible.** This is why VOID
is a first-class verdict here.

### 5.3 Bugs caught in the work that produced this paper

Recorded because a paper that reports only its successes is advertising:

- a coupling matrix where nine manifolds collapsed onto seven ranks, and
  two tied at rank 1 — giving them mutual coupling identical to the
  diagonal, i.e. *no separation at all*. Found by asserting
  `off_diagonal < 1`.
- a torus embedding that was not periodic: `atan2` over raw coordinates
  moves when one coordinate of a pair gains 2π. Would have silently
  distorted every embedding downstream, forever. Found by a periodicity
  test.
- four protocols whose coherence metrics were constant, because every
  action generator returned a constant vector and the loop therefore
  carried no state. Three of four metrics were measuring nothing.
- a metric that scored a lopsided system *higher* than a balanced one,
  because it took the strongest axis rather than the weakest. The test
  asserting the opposite failed, and it was right.

Each is now a test. That is the only claim we make about them.

---

## 6. Related work, wider

- **Model-based RL and safety filters**: runtime shields (Alshiekh et al.,
  2018) are the direct ancestor of "enforce outside the model."
- **Simplex architecture** (Simmons 1991): multiple independently
  evolvable copies with a decision module. Structurally close to our
  M0/M1 split.
- **Simplex runtime assurance**: the formal statement that a verified
  fallback controller guarantees safety when the primary violates its
  assumptions. This is precisely what §3.4 lacks and precisely what we
  should implement.
- **Control-theoretic safety certificates**: CBF-QP, Hamilton-Jacobi
  reachability, and tube MPC all provide guarantees with explicit
  assumption statements. Our v1 had no assumption statements. §3 does.

---

## 7. What must happen before this is submittable

Ordered by how much each changes the paper's standing.

1. **Move the governor out of process.** Until refusal authority is
   structural, the 747 comparison is rhetoric. Highest value, hardest.
2. **State assumptions for every guarantee.** If a bound holds under
   conditions, the conditions go in the theorem, not the discussion.
3. **Benchmark the cost claim or delete it.** One end-to-end measurement
   of reliable actions per dollar, ours versus a frontier model, with the
   task specified. Until then §4 stands without a number.
4. **Map our architecture onto CBF-QP and simplex assurance explicitly.**
   If our governor can be expressed as a barrier condition, that is a real
   contribution: a barrier that needs no model of the LLM at all. If it
   cannot, that is also worth knowing and worth saying.
5. **Resolve the atlas-exam VOID findings.** Several checks report HELD
   and cannot fail. Those are the ones a reviewer will attack, correctly.
6. **Add a control-systems reviewer as a co-author**, not as a critic. The
   framing "747 as certifier" is a control-engineering contribution and
   should be owned by someone who can be held to it.

---

## 8. Conclusion

The architecture is not novel. Enforcing safety at inference, outside the
model, using barrier-style constraints, is four years old and well
published; BarrierSteer is further along than this system.

What remains, and is worth publishing:

- a **layered checklist** that decomposes any AI control system from plant
  to governor against a certified engineering reference, with four verdicts
  including VOID;
- the **first honest measurement of our own system**, in which the layer
  the analogy most depends on — refusal authority — comes out OPEN because
  the gate lives inside the process it gates;
- and a **design programme** that says plainly what would have to be true
  for this to be an engineering result rather than an argument.

6-4=2 does not hallucinate. That remains true and remains insufficient.
The interesting question was never arithmetic; it is whether a refusal is
authoritative, and on that question this paper's own system is not yet
qualified.

---

## References

1. CBF-LLM: Safe Control for LLM Alignment. arXiv:2408.15625 (2024)
2. Control Barrier Function for Aligning Large Language Models. arXiv:2511.03121; IEEE (2025)
3. BarrierSteer: LLM Safety via Learning Barrier Steering. arXiv:2602.20102; ICLR (2026)
4. Safe Reinforcement Learning via Formal Methods: Toward Safe Control. AAAI, ojs.aaai.org/index.php/AAAI/article/view/12107
5. Verified Machine Learning Infrastructure: Formal Methods for AI. RAND RR-A4881-1
6. Alshiekh et al. Safe Reinforcement Learning via Shielding. AAAI (2018)
7. Simmons. The Simplex Architecture for Safe Online Robot System Control. ACM TAI (1991)
8. Simplex Runtime Assurance: a Simplex-based Extension to Runtime Assurance. IFAC-PapersOnLine
9. Ames et al. Control Barrier Function Based Quadratic Programs. ACC (2019)
10. Mitchell et al. Control Barrier Functions Reachability. IEEE TAC (2021)
11. `atlas-exam/docs/ten-areas-vs-747.md` — the certification instrument
12. `fieldcore/src/fieldcore_cell.py` — the plant, 21 checks
13. `fieldcore/src/gradient_flow_kernel.py` — the controller
14. `fieldcore/src/tiniest_core/tiniest_core.py` — smallest working kernel
15. `simself/src/constitutional/twin_prime_coupling.py` — fixed coupling
16. `simself/src/constitutional/metalog.py` — actor/observer
17. `simself/src/constitutional/master_protocols.py` — four coherence metrics
18. `C:/Users/HP/AppData/Local/hermes/CENTRAL-RULES.md` — the seven rules

---

*Version 2.0, 2026-10-09. The novelty claim of v1 was withdrawn after
literature search; the comparison method and the measurements replace it.*
*Co-authors: Robert David Wolfson (author) + Hermes (Nous Research / minimax).*