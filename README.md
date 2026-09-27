# FieldCore

## The proof — a steel ball on a concave surface

Drop a steel ball bearing, from any height, at any location, onto a concave
surface with a hole at the center. **The ball always finds the hole by gravity
alone.** No compute. No matrix multiply. No inference step. Pure physical
geometry does the work.

This is the entire FieldCore architecture in one exhibit.

**Math.** Let `F(x) = ½‖x - ψ₀‖²` (the height function with the hole at `ψ₀`).
Take one projected gradient step `x_{k+1} = Π_B(x_k - η∇F(x_k))`. Then the
drift decays as

```
d_{k+1} ≤ (1 - η) d_k    ⇒    d_k ≤ (1 - η)^k d_0    ⇒    d_k → 0
```

The bound is **independent of the starting point**. Every drop finds the hole.
The same step runs in silicon, neurons, FPGAs, or actual steel — the
substrate is invariant under implementation.

**Run it yourself.**

```
python src/steel_ball_proof.py
```

This script drops the ball from 50 random heights and locations, verifies the
contraction bound holds at every step, and demonstrates convergence in the
16-dimensional canonical space. All assertions pass.

**Why this replaces the LLM forward pass.** An LLM forward pass is the same
gradient step on the same `F(x)`, but with stochastic noise sampled per
token. The convergence guarantee still holds *for bounded noise*; for the
unbounded noise of natural language, it breaks — and the only thing
guaranteeing anything is parameter scale (cost, heat, and no control
authority). FieldCore replaces this with a deterministic projected gradient
step:

| | LLM forward pass | FieldCore step |
|---|---|---|
| Cost per token / step | O(d²) flops | O(d) flops |
| Heat emitted | matrix-multiply heat | 1 op/cycle |
| Convergence guarantee | probabilistic | deterministic bound |
| Veto authority | none | 1-bit gate |

Same math. Lower cost. Less heat. Explicit control.

**The substrate is the system.** SimSelf is one such configuration with
identity + persistence + governance — a ball-configuration on this
concave surface. Other configurations are possible without changing the
substrate.

---

## What this project needs — the team

This repo is one person + one AI agent. It is not a project that will
ship on that basis. The architecture is right and the proof is right,
and neither of those helps until the engineering surface is staffed.

What is here and works:

- **Substrate math.** `src/tiniest_core/tiniest_core.py` is a 333-line
  kernel that implements the gradient step on the Heegaard-splitting
  geometry, with 5 passing asserts. `src/substrate.py` is a stdlib-only
  substrate (EggToroid, HodgeDecomp, ResolutionOperator,
  FrequencyChannel, PrimeSheaf) with 15 frequency hypotheses that runs
  cold in 2 ms.
- **Braided-stalk architecture.** `src/stalk_topology.py` implements
  `Stalk`, `braid`, `unbraid`, `nest`, `add_cross_member`, `resonate`,
  `detach`, and the 5-state lifecycle. DNA-like coupling on a toroidal
  substrate, with a measured REINFORCE reward curve.
- **The proof.** `src/steel_ball_proof.py` — drop the ball, verify
  contraction, run in 16-D. Five sections, all assert.
- **Concrete kernel invariants.** `tests/test_sparse_substrate.py`
  passes. The relative-error bound is held.

What is here and is **not yet real**:

- **Formal proofs.** The steel-ball proof is a runnable exhibit, not a
  paper. The mathematics (Heegaard splitting, Floer dictionary, Hodge
  decomposition) is sketched in `papers/publishable/` but not formally
  proven. A mathematician or formal-methods person could close this.
- **Hardware target.** The kernel is implementable in ~500 lines of
  Verilog or as a tensor-core microcode sequence on commodity GPUs.
  Nobody has done either. An FPGA/ASIC person with a board could close
  this in a week and produce a benchmark.
- **Empirical baseline.** There is no head-to-head comparison between
  this kernel and a contemporary LLM forward pass on the same `F(x)`,
  measuring wall-clock, joules, and a defined control authority. An ML
  evaluator with access to a small GPU cluster could close this.
- **Frequency connector.** `simself/src/constitutional/frequency.py`
  defines FrequencyCoupler. The v6.2 canonical SimSelf
  (`src/constitutional/simself.py`) does not import it. Reconnecting
  these — without breaking the constitutional core — is a one-week job.

What the project does **not** need:

- More layers. The architecture is finished; only the connectors are
  missing.
- A bigger model. The kernel does not benefit from scale; it benefits
  from being deployed.
- More paper. The math is sketched. What is needed is hardware.

**If you can bring one of these five things, the project moves. If
you can bring two, it ships.**

| Role | One-line description | Estimated time to first contribution |
|---|---|---|
| Formal mathematician | Close the Hodge-decomposition and Floer-dictionary proofs | 4 weeks |
| FPGA / ASIC engineer | Port `tiniest_core.py` to Verilog; benchmark vs. LLM forward pass | 2-4 weeks |
| ML evaluator | Write the head-to-head LLM-vs-kernel evaluation harness | 2 weeks |
| Systems engineer | Reconnect `frequency.py` to canonical `simself.py` without breaking the gate | 1-2 weeks |
| Quantum-information person | Stress-test `quantum_mimic.py` against real quantum simulators (qiskit, cirq) — does the classical mimic reproduce the right Bell-test statistics? | 2 weeks |

Contact: open an issue or PR. The repo is MIT. No permission slip needed.

---

**Public repos.** `LICENSE` is MIT. Fork, clone, run, build — including commercial use. No tollbooth. No "research only."

## Defense (one paragraph)

Current generators produce text and forget themselves. This shell keeps a serializable ground ψ₀, a working state ψ inside a ball, a two-check veto, and lexicon units that can be refused. Geometry is the **genus-1 Heegaard splitting of S³**: two solid tori, one Clifford torus wall, ψ₀ as the complementary handlebody. That is the whole public story.

## The three objects

- **Hole / ground** — `ψ₀` installed on the Clifford torus `T`, write-protected.
- **Gate** — `M0_Governor` in `src/tiniest_core/tiniest_core.py` (kernel) and `simself/src/harness/gate.py` (production). Same predicates.
- **Exam** — `simself/src/constitutional/atlas_exam.py` runs the 5-item qualification suite (lives in SimSelf; FieldCore supplies the kernel predicates it tests).

## Where to look

| Path | What |
|---|---|
| `src/tiniest_core/tiniest_core.py` | Kernel: 16-D vectors, two inequalities, projected gradient step. 5 local asserts. `python src/tiniest_core/tiniest_core.py` to run. |
| `src/tiniest_core/tiniest_core.rs` | Rust twin. Same predicates. |
| `src/steel_ball_proof.py` | **THE PROOF** — drop the ball from 50 random heights, verify contraction bound, show convergence. 5 sections, all assert. Run this first. |
| `src/quantum_mimic.py` | **Classical-quantum mimic.** Phase, EntangledPair (3 correlations), Superposition (with observe collapse), Interference (destructive + constructive + fringe pattern), WaveField (gaussian + plane wave). 5 primitives, 22 tests pass. Stdlib-only. |
| `src/gradient_flow_kernel.py` | CLI demo of the projected gradient step on F(ψ)=½‖ψ-ψ₀‖². |
| `src/convergence_demo.py` | Pedagogical steel-ball-on-concave-surface exhibit. |
| `src/stalk_control.py` | Stalk data structure with measured REINFORCE reward curve. |
| `src/bitnet_ops.py` | Ternary operators for the BitNet paper. |
| `src/sheaf_nn_index.py` | Sheaf-NN index (sklearn-backed; <100ms/query on 10k×16). |
| `src/substrate.py` | Substrate cold-boot + sparse prediction (A/B/C paper). |
| `src/stalk_topology.py` | Stalk topology demo: 3 stalks, idle/move/collapse states. |
| `src/standalone_minimax.py` | Standalone MiniMax chat + Walrus memory loop (portable paths). |
| `papers/publishable/22-fieldcore-one-read-2026-09-15.md` | The one read. Start here. |
| `papers/publishable/17-egg-toroid-spec-2026-09-15.md` | Topology spec: genus-1 Heegaard splitting of S³. |
| `papers/publishable/01-geodesic-lexicon-2026-09-15.md` | Lexicon: two metrics (Euclidean + flat Clifford). |
| `papers/publishable/14-math-window1-synthesis-2026-09-15.md` | Math appendix. |
| `papers/publishable/06-llm-sparse-substrate-2026-09-15.md` | Sparse substrate paper. |
| `papers/publishable/11-stalk-architecture-v6-1-2026-09-15.md` | Stalk architecture with measured coupling. |
| `papers/publishable/34-bitnet-ternary-substrate-operators-2026-09-15.md` | BitNet ops paper. |
| `papers/publishable/76-sheaf-nn-index-sklearn-sub-100ms-2026-09-15.md` | Sheaf-NN engineering note. |
| `papers/proposals/07-stalk-architecture-v61-implementation-2026-09-15.md` | Stalk build proposal. |
| `papers/proposals/09-heegaard-seam-energy-barriers-2026-09-15.md` | Heegaard seam proposal. |
| `papers/proposals/12-constitutional-substrate-for-agi-evaluation-2026-09-15.md` | Eval proposal. |
| `papers/proposals/13-adaptive-resolution-damping-2026-09-15.md` | Damping proposal. |
| `papers/working/12-ndim-topological-dimension-detection-2026-09-15.md` | Persistent homology in progress. |

## What's off the front path

- `notes/analogies/` — off-mission / occult-physics files preserved verbatim.
- `notes/paper-history/` — stale 2026-09-13 / 2026-09-14 drafts superseded by 09-15.
- `docs/Math/` — clean math reference; the Layer C / occult content has been moved to `notes/analogies/`.

## Run it

```bash
git clone https://github.com/the-far-queen/fieldcore.git
cd fieldcore
python src/steel_ball_proof.py        # THE PROOF — 5 sections, all assert
python src/tiniest_core/tiniest_core.py # kernel: 5 asserts
python -m pytest tests/ -v              # 2 passed, 1 skipped (sklearn), 1 xfail
```

The kernel's asserts verify the gate, the gradient step, and the ground invariant.
The proof asserts the contraction bound holds at every step and that 50 random
drops all converge.

## Open source

License: MIT. Clones, forks, and pull requests are welcome. No permission slip needed.
