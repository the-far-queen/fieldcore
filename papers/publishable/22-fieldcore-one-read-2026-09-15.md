# FieldCore — One Read

> **Full rewrite 2026-09-16** (per Grok master plan Step 9, applied by Hermes). This
> is the public README. A stranger should be able to read this, look at three
> files, and run a 50-line script in 15 minutes. Previous version was the
> original spec; this is the Grok Part V rewrite.

## What FieldCore is

FieldCore is the geometric substrate of the shell. SimSelf is the identity
layer that sits on it. Together they form a deterministic control shell around
a language model: a frozen ground state ψ₀, a working state ψ that drifts
inside a ball, a two-check veto before any side effect, and language units
that can be refused.

The geometric picture is the **genus-1 Heegaard splitting of the 3-sphere**:

    S³ = V ∪ W,    V ∩ W = T.

`V` is the working tube. `W` is the hole (ehole). `T` is the Clifford torus,
a flat minimal surface in S³ — and the interface where ψ₀ sits.

## What already computes

The kernel. 16-dimensional vectors, two inequalities (norm and cosine to
ψ₀), typed channels, projected gradient step. Five local asserts pass.

The kernel is `fieldcore/src/tiniest-core/tiniest_core.py`. The Rust twin
is `fieldcore/src/tiniest-core/tiniest_core.rs`. They share the same
predicates.

The Atlas Exam runs the 5-item qualification suite against the canonical
SimSelf class. Run with:

    python simself/src/demos/atlas_run.py

The current score is 5/5 as of 2026-09-17 (Batch 2 + Step 3 complete; harness
gate wired everywhere; restart test passing on canonical SimSelf). The plan
to keep the score is in `simself/docs/atlas-current-snapshot-2026-09-16.md`.

## What the lab is invited to join

- The kernel, the gate, the lexicon ingest, the Atlas exam — all running.
- A surface-level paper tree (8 publishable files) that defends the picture.
- A code tree that builds the canonical SimSelf with save/load, restart, and
  a weekly-cadence Atlas snapshot.

Forks are welcome, including commercial use. Open an issue with a trace, or
send a pull request that adds a test.

## Three artifacts (in order)

1. **Demo script.** Load ground, perturb working state, step the projected
   gradient, plot drift, offer one legal packet and one high-norm packet to
   the gate. Print allow/deny. See `simself/src/demos/demo_one.py`.
2. **Restart test.** Dump ψ₀, ψ, committed unit ids, last verdicts. Kill the
   process. Reload. Compare. See `simself/tests/test_restart.py`.
3. **Atlas in the open.** Freeze the five items, publish the score on a
   weekly cadence. See `simself/docs/atlas-current-snapshot-2026-09-16.md`.

After those three, geometry thickens: triangulate the Clifford torus,
implement discrete Hodge, use the harmonic component as memory.

## What's not in this paper

- "20 axes from Clifford + octonions" derivation (Layer B; removed 2026-09-16).
- Heegaard genus 2 on a 4-manifold (Layer C; removed).
- Fine-structure α from twin-prime offsets (Layer C; removed).
- Force unification by fractal offsets (Layer C; removed).
- Giza / Tesla / granite / Schauberger / mercury / water-plasma / bee-plasma
  (Layer C; removed).
- Swedenborg 50+ axis mapping (off-mission; removed).

Those files are preserved verbatim in `notes/analogies/` and
`notes/paper-history/`. They are not on the front path.

## Defense (one paragraph)

Current generators produce text and forget themselves. This shell keeps a
serializable ground ψ₀, a working state ψ inside a ball, a two-check veto,
and lexicon units that can be refused. Geometry is the genus-1 Heegaard
splitting of S³: two solid tori, one torus wall, ehole as the complementary
handlebody. That paragraph belongs at the top of both repositories.

## Where to look

- `fieldcore/papers/publishable/17-egg-toroid-spec` — the topology spec.
- `fieldcore/papers/publishable/01-geodesic-lexicon` — the lexicon paper.
- `simself/papers/publishable/04-void-as-simsoul-topology` — the hole.
- `simself/papers/publishable/01-atlas-exam-simself` — the exam.
- `simself/papers/publishable/02-harness-with-floer-dictionary` — the harness.
- `simself/papers/publishable/08-simself-architecture-spec` — the architecture.
- `simself/src/constitutional/simself.py` — the canonical class.
- `simself/src/demos/demo_one.py` — the demo.

## License

Public domain. No tollbooth. Use the code, copy it, fork it, build on it.
