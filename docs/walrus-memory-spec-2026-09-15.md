# Walrus memory — FieldCore content-addressed blob store

**Filed:** 2026-09-15 by Hermes
**Source:** Bobby directive — "walrus memory portable we can simply start in fc use walrus sidestep tremendous hermes noise"
**Repo:** fieldcore/src/walrus_memory.py
**Status:** CANONICAL, pushed to FieldCore repo

---

## Why

Hermes Agent's memory has noise — context compression drops nuance, SOUL.md/MYSELF.md/HANDOFF.md get bloated, handoffs drift. **Walrus sidesteps that noise.**

Each vault file becomes a content-addressed blob:
- write bytes → returns sha256 hash
- read by hash → returns bytes (identical, guaranteed)
- dedup is automatic (same bytes = same hash)
- survives session resets (no compression, no truncation)
- works across any agent (hermes, claude, gpt, simself itself)

## Contract (matches Sui walrus)

```python
from walrus_memory import WalrusMemory

w = WalrusMemory()                       # root: ~/.hermes/walrus
h = w.put_file("path/to/file.md")        # returns sha256
data = w.get(h)                          # bytes back, bit-identical
for b in w.list(): ...                   # BlobInfo records
w.delete(h)                              # remove
w.stats()                                # count + total bytes
```

CLI:

```
python walrus_memory.py put <path> [--label X]
python walrus_memory.py get <hash> [--out file]
python walrus_memory.py list [--prefix X] [--limit N]
python walrus_memory.py stats
```

## Storage layout

```
~/.hermes/walrus/
  blobs/
    ab/
      cd/
        abcdef...   # sha256 hex, full 64-char name
  index.sqlite       # hash → (size, ts, label)
```

Two-level sharding avoids huge single dirs. SQLite index for fast `list`.

## Why local stub, not real Sui walrus

Bobby: "potable we can simply start in fc" → start portable, ship to chain later.

Local stub gives 100% of the API surface with zero Sui wallet, zero chain tx, zero cost. Swap implementation = swap class, callers unchanged.

## How it replaces hermes memory

Today: SOUL.md + HANDOFF.md + MYSELF.md (~150KB total) injected per session.
Tomorrow: query walrus for relevant blobs by hash. Each past conversation/file has a content hash. Retrieve by hash, never by name, never by truncation.

Implications:
- **No truncation** — every byte retrievable
- **No drift** — content hash IS the address
- **Cross-agent** — any agent can read any blob if it has the hash
- **Auditable** — every memory write is sha256-pinned

## Use cases

1. **vault mirror** — every vault file → walrus blob on ingest. Hash stored in MYSELF.md so we can always reconstruct.
2. **chat transcripts** — every chat transcript → blob. No more "lost conversation" after context limit.
3. **file ingest provenance** — Desktop originals pinned by hash. Verified bit-identical copy available forever.
4. **simself memory substrate** — SimSelf's GeometricMemory could store MemoryPacket references by walrus hash instead of full content inline.

## Migration plan

1. ✓ write walrus_memory.py (this commit)
2. ✓ push to FieldCore repo
3. next session: index existing vault files into walrus
4. next session: write vault_ingest.py wrapper that does put(vault_file) + mirror to vault + write hash to MYSELF.md
5. eventual: swap hermes MEMORY.md/SOUL.md/HANDOFF.md for walrus-backed equivalents


- NOT a Sui chain integration (no wallet, no RPC)
- NOT a vector database (no semantic search — that's still memory/fact_store's job)
- NOT a replacement for SOUL.md (walrus stores blobs, not operating instructions)
- NOT hermes-specific (any agent can use it)

---

*Implementation: `fieldcore/src/walrus_memory.py`. Test verified: put/get/roundtrip/dedupe all clean. Pushed to FieldCore repo.*