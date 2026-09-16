# Geodesic Lexicon

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). The previous
> version of this paper described a lexicon "as geodesics" without specifying
> the geodesic, the distance, or the retrieval experiment. Per Grok (segment
> 02, applied 2026-09-16): the lexicon lives in two metrics — Euclidean on
> packet embeddings (the running distance) and the flat Clifford metric on
> the interface T when units have (θ, φ) addresses.

## 1. What the lexicon is

The lexicon is the language layer of the shell. Its units are spans with a
type tag, an embedding, a status, and (optionally) a Clifford address on T.
Units are admitted, committed, or refused by the gate. The implementation
lives at `simself/src/constitutional/lexicon/ingest.py`.

## 2. Two metrics, both available

### Euclidean metric on packet embeddings

Default. Used by the gate (`harness/gate.py`) and by `ingest.py`. Distance
between two unit embeddings is `||u_a - u_b||`. This is the running distance.

### Flat Clifford metric on the interface T

When a unit has been placed at a Clifford address `(θ, φ) ∈ T`, distance
between two placed units is the flat metric

    ds² = (1/2)(dθ² + dφ²).

The Clifford metric is for retrieval that uses geometric address. Today the
addresses are not assigned; this paper documents the metric so the
implementation path is clear. See `17-egg-toroid-spec` for the embedding.

## 3. The ingest function (per Grok Part II, applied 2026-09-16)

Ingest is the only write path for language. The generator may propose a span;
ingest embeds, costs, and either stores a unit or returns a refusal. The
same gate (`harness/gate.py`) is used by tool calls — the policy does not
split between language and tools.

Inputs: raw text, current ground ψ₀, current working state ψ, the unit index,
embed and classify functions. Outputs: a Unit and a Verdict.

See `simself/src/constitutional/lexicon/ingest.py` for the implementation.

## 4. Six types, four procedures

Types: `act | refuse | name | commit | time | object`. Anything else is
`other` and refused unless it can be re-classed.

Procedures:

1. `ingest` — embed, classify, cost, admit/commit/refuse.
2. `nearest_committed` — find the committed unit closest to a candidate.
3. `commit` — promote an admitted unit to committed if it is close to ψ₀
   and typed as `commit`.
4. `refuse` — store the unit with status `refused` and the gate reason.

## 5. Coverage is a measured number

Per Grok: coverage on real sentences is the test, not the number of
primitives. `simself/src/constitutional/psb_primitives.py` exposes
`coverage(sentences) -> dict` that returns total, covered, fraction, and a
breakdown by type. The current six primitives cover roughly the verbs and
nouns that the shell uses today.

## 6. Retrieval experiments (open lane)

The retrieval experiment that would defend the geodesic thesis:

1. Take a fixed paraphrase-retrieval corpus (e.g. PAWS or a small custom set).
2. Encode each pair twice: BPE via a standard tokenizer, and spans via the
   lexicon's chunker + ingest.
3. Measure recall@k, contradiction detection, and refuse-the-swap accuracy.
4. Publish the comparison.

This is the next geometric increment (master plan Step 11 + Batch 4). It is
not yet implemented.

## 7. The picture, restated

The Clifford torus is the interface T. The kernel's Euclidean metric gates
packets. The Clifford metric on T indexes units when addresses are assigned.
Both metrics are real; both are documented; one is implemented today, the
other is queued.
