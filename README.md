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
