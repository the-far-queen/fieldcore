# FieldCore

The geometric substrate of the shell. SimSelf is the identity layer that sits on it.

**Public repos.** `LICENSE` is open. No tollbooth. Fork, clone, run, build — including commercial use.

## Defense (one paragraph)

Current generators produce text and forget themselves. This shell keeps a serializable ground ψ₀, a working state ψ inside a ball, a two-check veto, and lexicon units that can be refused. Geometry is the **genus-1 Heegaard splitting of S³**: two solid tori, one Clifford torus wall, ehole as the complementary handlebody. That is the whole public story.

## The three objects

- **Hole / ground** — `ψ₀` installed on the Clifford torus `T`, write-protected.
- **Gate** — `M0_Governor` in `src/tiniest-core/tiniest_core.py` (kernel) and `simself/src/harness/gate.py` (production). Same predicates.
- **Exam** — `simself/src/constitutional/atlas_exam.py` runs the 5-item qualification suite.

## Where to look

| Path | What |
|---|---|
| `src/tiniest-core/tiniest_core.py` | Kernel: 16-D vectors, two inequalities, projected gradient step. 5 local asserts. |
| `src/tiniest-core/tiniest_core.rs` | Rust twin. Same predicates. |
| `src/gradient_flow_kernel.py` | CLI demo of the projected gradient step on F(ψ)=½‖ψ-ψ₀‖². |
| `src/convergence_demo.py` | Bobby's pedagogical steel-ball-on-concave-surface exhibit. |
| `src/stalk_control.py` | Stalk data structure with measured REINFORCE reward curve. |
| `src/bitnet_ops.py` | Ternary operators for the BitNet paper. |
| `papers/publishable/22-fieldcore-one-read-2026-09-15.md` | The one read. Start here. |
| `papers/publishable/17-egg-toroid-spec-2026-09-15.md` | Topology spec: genus-1 Heegaard splitting of S³. |
| `papers/publishable/01-geodesic-lexicon-2026-09-15.md` | Lexicon: two metrics (Euclidean + flat Clifford). |
| `papers/publishable/14-math-window1-synthesis-2026-09-15.md` | Math appendix. Layer C stripped. |
| `papers/publishable/03-atlas-exam-fieldcore-2026-09-15.md` | Atlas exam (FieldCore half). |
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

## Three artifacts (in order)

1. **Demo script.** `simself/src/demos/demo_one.py` — load ground, perturb, step, gate.
2. **Restart test.** `simself/tests/test_restart.py` — dump, kill, load, compare.
3. **Atlas in the open.** `simself/docs/atlas-current-snapshot-2026-09-16.md` — 5 items, score 2/5, weekly cadence.

## Open source

License: free. Clones, forks, and pull requests are welcome. No permission slip needed.
