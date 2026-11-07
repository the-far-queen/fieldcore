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


#: WHERE THE BLOBS LIVE, and the path is DERIVED and not hard-coded.
#:
#: MEASURED 2026-11-07: the root was the literal string
#: `C:\Users\Admin\AppData\Local\hermes\walrus` -- **a path from a
#: different machine**. This machine's user is HP. And the REAL store,
#: `C:\Users\HP\AppData\Local\hermes\walrus`, existed with its
#: `index.sqlite` and **zero blobs in it**.
#:
#: So every write went to a directory that does not exist and never
#: will, and the store that was supposed to hold the system's
#: content-addressed memory was **EMPTY**. **A HARDCODED PATH IS A
#: PATH TO SOMEONE ELSE'S MACHINE.**
#:
#: AND THE FIX IS NOT THE RIGHT USERNAME -- it is a path that is
#: DERIVED, because the next machine would be wrong too.
_DEFAULT_ROOT = __import__("pathlib").Path(
    os.environ.get("HERMES_LOCAL_APP_DATA")
    or os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes")
) / "walrus"

DEFAULT_WALRUS_ROOT = Path = _DEFAULT_ROOT


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
        """The bytes for a hash, or a NAMED refusal.

        **AND THE REFUSAL NAMES ITS REASON**, because the robot's veto
        names the action it refused and a bare KeyError names nothing:
        a caller cannot tell "this blob was never written" from "this
        blob was written and then deleted" from "the store is on the
        wrong machine".

        **AND THAT LAST ONE WAS NOT HYPOTHETICAL** -- MEASURED
        2026-11-07: the store's root was the literal path
        `C:/Users/Admin/...`, a path from a different machine, so the
        real store held zero blobs and every get() would have said "not
        found" for content that was never written anywhere.
        """
        p = self._path(h)
        if not p.exists():
            raise KeyError(
                "the blob %s is not in this store: %s -- it was never "
                "written here, or it was deleted" % (h[:16], self.root))
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


def _selftest() -> int:
    """The walrus memory, proved.

    **AND THIS SELFTEST ASSERTS THE REFUSAL, NOT JUST THE HAPPY PATH.**
    A selftest that only asserts the happy path proves nothing -- and
    the robot's own selftest asserts the VETO, so it fails if the veto
    stops happening. So this one asserts that a missing blob is refused
    WITH A NAMED REASON, and that the reason names the store it looked
    in.

    **AND IT ASSERTS THE ROOT POINTS AT THIS MACHINE**, because the bug
    it exists to catch was a root on someone else's machine, and the
    symptom was an EMPTY store that looked like an empty system.
    """
    import tempfile
    root = tempfile.mkdtemp()
    w = WalrusMemory(root=root)

    # -- 1. the round trip
    h = w.put(b"the content", "a label")
    assert w.get(h) == b"the content", "the round trip did not hold"
    assert w.has(h), "the blob is not there"
    assert len(list(w.list())) == 1, "the list is wrong"

    # -- 2. AND THE CONTENT ADDRESSING DEDUPES
    h2 = w.put(b"the content", "another label")
    assert h2 == h, "the same content made two blobs"
    assert len(list(w.list())) == 1, "the same content made two blobs"

    # -- 3. AND THE ROOT POINTS AT THIS MACHINE
    assert "Users\\Admin\\" not in str(DEFAULT_WALRUS_ROOT), (
        "the store's root is on another machine: %s" % DEFAULT_WALRUS_ROOT)
    assert os.path.expanduser("~")[:11].lower() in str(
        DEFAULT_WALRUS_ROOT).lower(), (
        "the store's root is not under this user's home: %s"
        % DEFAULT_WALRUS_ROOT)

    # -- 4. AND THE REFUSAL NAMES ITS REASON
    try:
        w.get("f" * 64)
    except KeyError as exc:
        # AND THE RAW MESSAGE IS `exc.args[0]`, not `str(exc)` -- a
        # KeyError's str() is the REPR of its argument, so every
        # backslash in the path is doubled and the message reads as
        # `C:\\Users\\...`. **AND A TEST THAT COMPARES THE REPR
        # AGAINST A PATH FAILS FOR A REASON THAT IS NOT THE BUG.**
        msg = exc.args[0]
        assert "not in this store" in msg, "the refusal does not name the store"
        # AND THE PATH IS COMPARED IN THE FORM THE MESSAGE CARRIES --
        # `self.root` is a Path, so its str() is the OS spelling
        # (backslashes on Windows) and not the literal the test passed
        # in. **AND A TEST THAT COMPARES THE WRONG SPELLING OF A PATH
        # FAILS FOR A REASON THAT IS NOT THE BUG.**
        assert str(w.root) in msg, (
            "the refusal does not name where it looked: %s" % msg)
    else:
        raise AssertionError("a missing blob was not refused")

    # -- 5. AND THE DELETE REMOVES IT
    w.delete(h)
    assert not w.has(h), "the deleted blob is still there"

    print("  [ok ] the round trip")
    print("  [ok ] the content addressing dedupes")
    print("  [ok ] the root points at this machine")
    print("  [ok ] the refusal names its reason")
    print("  [ok ] the delete removes it")
    print()
    print("  THE WALRUS SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    try:
        rc = cli()
    except SystemExit as e:
        # argparse's error path: if no args, exit 2 → show usage, exit 0.
        if e.code == 2:
            print(__doc__)
            sys.exit(0)
        raise
    sys.exit(rc)