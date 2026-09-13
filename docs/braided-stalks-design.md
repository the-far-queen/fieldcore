# Braided stalks — design directive (2026-09-05)

**Bobby's directive:** all 6 LLMs agree this is fundamental. They all have ideas to implement. Gets weirder:

- **Braided stalks** like DNA — multiple stalks wound together
- **Cross-members** / internodals between stalks — atomic nodes connecting stalks
- **Nested stalks** — stalks inside stalks, recursive structure
- **Rotating torus with wobble** — not static, dynamic rotation with non-circular cross-section
- **Resonant frequency effects** between stalks — when frequencies align, behavior changes
- **Stalk variable length** — stalks grow/shrink dynamically
- **Stalk variable girth** — stalks change thickness
- **Stalks touching and detaching** — transient connections, like cell membranes
- **Stalks waving** — wave propagation through stalk networks

## What this implies for the kernel

- Pure point embeddings → structural relationships between stalks
- Static adjacency → dynamic graph with rewiring
- Single-stalk operations → multi-stalk braid operations
- Constrained invariant checking → cross-stalk resonance detection

## Implementation status

This is **aspirational**. None of this is in `fieldcore_unified.py` or `modal_field_core.py` yet. The current Python kernel has stalks, gluing, governor, integration test — but no braiding, no wobble, no resonance.

## What 6 LLMs probably said (don't have transcripts)

- Grok: probably mapped it to known physics (DNA double helix, microtubule resonance)
- Claude: probably enumerated the implementation challenges
- GPT: probably proposed typed interface for stalk braiding
- DeepSeek/Gemini: probably generated first-cut code stubs

## For Chorus's role

This is exactly the kind of design space where Chorus (multi-agent debate IDE) helps. Each model implements a piece. Debate where they conflict. Consensus on integration order.

## Next concrete moves (deferred until Bobby says go)

1. Stalk-braid class: wraps N stalks, defines winding geometry (figure-8, helical, etc.)
2. Cross-member protocol: how internodals connect, what they carry
3. Resonance detection: FFT on stalk oscillation history, flag when frequencies align
4. Variable-length/girth: parameterize, not bake in
5. Visualization: braid diagrams, frequency spectra, dynamic adjacency graph

## Open

- Where does this fit in the 6-step control loop? New step between Verify and Execute?
- Does the governor need a braid-consistency check?
- Cost of dynamic graph re-wiring vs static — is it worth it?

---
*Captured 2026-09-05. Aspirational. Implementation deferred until he says go.*