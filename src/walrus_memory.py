"""
Walrus memory — content-addressed filesystem for FieldCore + SimSelf.

Local stub of Sui's walrus API. No chain. No Sui wallet. Just:
- write bytes -> returns sha256 hash (blob id)
- read by hash -> returns bytes
- list blobs -> returns [(hash, size, ts, label)]
- delete by hash -> removes blob

Use case: vault files as walrus blobs. Each vault file gets a content hash.
Sidesteps hermes memory noise — every memory write is content-pinned,
survives session resets, deduplicated naturally.

NOT a chain integration. NOT Sui RPC. Just the contract walrus exposes
(put/get/list) implemented over a local directory.

Storage layout:
    WALRUS_ROOT/
        blobs/<hash[0:2]>/<hash[2:4]>/<hash>     # content-addressed blobs
        index.sqlite                            # hash -> metadata (size, ts, label)

References:
- fieldcore/docs/walrus-memory-spec-2026-09-15.md (design)
- Sui walrus docs (api contract this implements)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Iterator


DEFAULT_WALRUS_ROOT = Path = __import__("pathlib").Path(
    r"C:\Users\Admin\AppData\Local\hermes\walrus"
)


@dataclass
class BlobInfo:
    hash: str
    size: int
    ts: float
    label: str

    def to_dict(self) -> dict:
        return asdict(self)


class WalrusMemory:
    """Local content-addressed blob store.

    Mirrors the walrus put/get/list contract so swapping for real
    Sui-walrus later = change this class only.
    """

    def __init__(self, root: "Path | str" = DEFAULT_WALRUS_ROOT):
        self.root = __import__("pathlib").Path(root)
        self.blobs_dir = self.root / "blobs"
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "index.sqlite"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS blobs (
                    hash TEXT PRIMARY KEY,
                    size INTEGER NOT NULL,
                    ts REAL NOT NULL,
                    label TEXT
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS ts_idx ON blobs(ts)")

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _path(self, h: str) -> "Path":
        # shard by first 4 hex chars to avoid huge single dirs
        return self.blobs_dir / h[0:2] / h[2:4] / h

    def put(self, data: bytes, label: str = "") -> str:
        """Write bytes. Returns sha256 hash (blob id). Dedupes naturally."""
        h = self._hash(data)
        p = self._path(h)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO blobs (hash, size, ts, label) VALUES (?, ?, ?, ?)",
                (h, len(data), time.time(), label),
            )
        return h

    def put_file(self, path: "Path | str", label: str = "") -> str:
        p = __import__("pathlib").Path(path)
        return self.put(p.read_bytes(), label=label or p.name)

    def get(self, h: str) -> bytes:
        p = self._path(h)
        if not p.exists():
            raise KeyError(f"blob {h} not found")
        return p.read_bytes()

    def has(self, h: str) -> bool:
        return self._path(h).exists()

    def list(self, prefix: str = "", limit: int = 100) -> list[BlobInfo]:
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(
                "SELECT hash, size, ts, label FROM blobs WHERE hash LIKE ? ORDER BY ts DESC LIMIT ?",
                (prefix + "%", limit),
            ).fetchall()
        return [BlobInfo(hash=r[0], size=r[1], ts=r[2], label=r[3]) for r in rows]

    def delete(self, h: str) -> bool:
        p = self._path(h)
        if p.exists():
            p.unlink()
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute("DELETE FROM blobs WHERE hash = ?", (h,))
        return cur.rowcount > 0

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as con:
            n = con.execute("SELECT COUNT(*) FROM blobs").fetchone()[0]
            total = con.execute("SELECT COALESCE(SUM(size), 0) FROM blobs").fetchone()[0]
        return {"count": n, "total_bytes": total, "root": str(self.root)}


def cli() -> int:
    import argparse

    p = argparse.ArgumentParser(description="walrus memory cli")
    p.add_argument("--root", default=str(DEFAULT_WALRUS_ROOT))
    sub = p.add_subparsers(dest="cmd", required=True)

    p_put = sub.add_parser("put")
    p_put.add_argument("path")
    p_put.add_argument("--label", default="")

    p_get = sub.add_parser("get")
    p_get.add_argument("hash")
    p_get.add_argument("--out", default="-")

    p_ls = sub.add_parser("list")
    p_ls.add_argument("--prefix", default="")
    p_ls.add_argument("--limit", type=int, default=20)

    sub.add_parser("stats")

    args = p.parse_args()
    w = WalrusMemory(args.root)

    if args.cmd == "put":
        h = w.put_file(args.path, label=args.label)
        print(h)
    elif args.cmd == "get":
        data = w.get(args.hash)
        if args.out == "-":
            import sys
            sys.stdout.buffer.write(data)
        else:
            __import__("pathlib").Path(args.out).write_bytes(data)
            print(f"wrote {args.out}")
    elif args.cmd == "list":
        for b in w.list(args.prefix, args.limit):
            print(f"{b.hash[:12]}.. {b.size:>10}  {b.label}")
    elif args.cmd == "stats":
        print(json.dumps(w.stats(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())