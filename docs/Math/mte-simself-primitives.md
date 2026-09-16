# MTE — SimSelf Primitives

> **Verified 2026-09-16** (per Grok master plan, applied by Hermes). Layer A
> reference for MLTR (machine language technical register) and the MTE
> (machine translation engine) bridging layer.

## 1. MLTR

MLTR = the register a machine uses when the human language layer is too
lossy. The architecture treats MLTR as a target vocabulary that is more
constrained than BPE tokens: typed units with explicit case slots.

## 2. MTE

MTE = the transformer that translates between MLTR (machine register)
and a human language. Per the architecture:

- MLTR is the unit type (`act | refuse | name | commit | time | object`).
- MTE is the wrapping that maps an intact span to a typed unit via
  `classify_span(span) -> UnitType` in
  `simself/src/constitutional/psb_primitives.py`.
- The reverse direction (committed unit → natural language) is a
  generative step that lives outside the gate.

## 3. Why this matters

Tokenization (BPE) is lossy. MLTR is a larger unit. The MTE wraps the
translation so the loss is bounded and measured. Coverage on a fixed
sentence list is the test (`coverage(sentences)` in
`psb_primitives.py`).

## 4. Used by

- `simself/papers/publishable/13-mte-llm-wrapper-safety-2026-09-15.md`
  — the safety contract.
- `simself/papers/proposals/09-mte-machine-translation-engine-bidirectional-loss-2026-09-15.md`
  — the bidirectional-loss proposal.

## 5. Status

Implementation: `classify_span(span)` in
`simself/src/constitutional/psb_primitives.py`. Coverage is measured.
Bidirectional loss (MTE in the reverse direction) is open work.

## 6. References

- `fieldcore/papers/publishable/01-geodesic-lexicon-2026-09-15.md` —
  the lexicon paper.
- `simself/src/constitutional/psb_primitives.py` — the primitives.
- `simself/src/constitutional/lexicon/ingest.py` — the lexicon ingest.
