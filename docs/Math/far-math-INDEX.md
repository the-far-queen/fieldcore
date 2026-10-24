# far-math — index (folded into fieldcore, 2026-10-16)

> **MOVED, THEN THE REPO WAS DELETED.** Bobby: *"del far-math fold into
> fieldcore"* (2026-10-16), then *"del not archive rest of archived"*
> (2026-10-24) — so the far-math repo no longer exists on GitHub. The code is
> `fieldcore/src/farmath/`, the documents are here. This file is the index for
> **the far-math school**; `README.md` in this directory indexes **fieldcore's
> own math docs**. Two indexes, two scopes — deliberately, because the two sets
> serve different readers. fieldcore's own docs stay Layer A only; the far-math
> school carries the full A/B/C layer system.

A math school for humans and AI. No tuition, no credits, no
accreditation. Every claim carries a layer: **A** tool, **B** held, **C**
marked and preserved.

## Read in this order

1. **[01 — The identity law](01-identity-law.md)** — the one result
   everything else reduces to. Gradient step, contraction bound, harmonic
   exception, and why an LLM forward pass is the same step with unbounded
   noise on top.
2. **[02 — Reconciled geometry](02-geometry-reconciled.md)** — the
   egg-toroid picture as a genus-1 Heegaard splitting of S³, Clifford
   torus and Hopf map computed, plus the corrections Grok forced and the
   Layer B material held for a mesh that does not exist yet.
3. **[03 — Number theory](03-number-theory.md)** — what verifies, what
   does not, and one Layer C claim that failed its own arithmetic.
4. **[04 — Claims register](04-claims-register.md)** — every claim, its
   layer, its check, its standing. Promotions and demotions on the record.

## The three-layer rule

```
A  standard mathematics, cited correctly        → may be used as a tool
B  real math not yet implemented on real code    → held until the operator exists
C  speculative, Bobby's framing                  → preserved, marked, never load-bearing
```

> "treat unfounded as speculative not drop all theorizing im often
> correct." — Bobby, 2026-09-14-late

`src/farmath/layers.py` enforces this. The gate is the point: the rule
survives because a machine reads it, not because a document says so.

## Run the checks

```
python -m pytest tests/ -q
```

24 checks, all able to go red. Several exist specifically to prove a
checker is not vacuous — the contraction checker is shown to reject
η = 1.5, the Clifford torus assertion is shown to reject a wrong radius,
and the twin-prime divisibility checker is shown to reject a modulus it
does not divide.

## Numbers you can trust

Every figure in these docs was produced by running the module and is
reproducible from the command above. Where a number contradicts an earlier
claim, both are here, dated, with the correction named.

## Terms used here

Defined here so this document can be read cold. The full glossary is
`GLOSSARY.md`.


- **prerequisite load** - the fraction of a document's domain terms that it never defines for the reader
- **Clifford torus** - the flat torus inside the 3-sphere

## More terms


- **gradient** - the direction in which a function rises fastest
- **harmonic** - the part of a field with Delta h = 0, preserved under gradient flow
- **Heegaard splitting** - building a 3-manifold by gluing two handlebodies along their boundary
