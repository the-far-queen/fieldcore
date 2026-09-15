"""
Standalone MiniMax API + Walrus memory loop.

No hermes harness. No context compression. No noise.
Just: minimax API for chat, walrus for memory persistence.

Usage:
    python standalone_minimax.py
    > hello
    [minimax reply]
    > /list
    [walrus blob list]
    > /quit

Env: MINIMAX_API_KEY must be set. Read from hermes .env if missing.
"""
from __future__ import annotations

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

WALRUS_ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\walrus")
HERMES_ENV = Path(r"C:\Users\Admin\AppData\Local\hermes\.env")
MINIMAX_BASE = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
SYSTEM = "you are a helpful assistant. terse, lowercase, no fluff."


def load_api_key() -> str:
    k = os.environ.get("MINIMAX_API_KEY")
    if k:
        return k
    if HERMES_ENV.exists():
        for line in HERMES_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("MINIMAX_API_KEY="):
                v = line.split("=", 1)[1].strip()
                if v and "your" not in v.lower():
                    return v
    print("MINIMAX_API_KEY not set. export it or add to hermes .env", file=sys.stderr)
    sys.exit(2)


# minimal walrus, no deps on fieldcore/src
import hashlib, sqlite3, time


class MiniWalrus:
    def __init__(self, root: Path):
        self.root = root
        (self.root / "blobs").mkdir(parents=True, exist_ok=True)
        self.db = self.root / "index.sqlite"
        self._init()

    def _init(self):
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TABLE IF NOT EXISTS blobs (hash TEXT PRIMARY KEY, size INTEGER, ts REAL, label TEXT)")

    def put(self, data: bytes, label: str = "") -> str:
        h = hashlib.sha256(data).hexdigest()
        p = self.root / "blobs" / h[:2] / h[2:4] / h
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT OR REPLACE INTO blobs VALUES (?,?,?,?)", (h, len(data), time.time(), label))
        return h

    def list(self, limit: int = 10):
        with sqlite3.connect(self.db) as c:
            return c.execute("SELECT hash, size, ts, label FROM blobs ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()


def chat(messages: list[dict]) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 800,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{MINIMAX_BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {load_api_key()}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


def main() -> int:
    walrus = MiniWalrus(WALRUS_ROOT)
    history: list[dict] = [{"role": "system", "content": SYSTEM}]
    print(f"minimax standalone. model={MODEL}, walrus={WALRUS_ROOT}")
    print("commands: /list /clear /quit")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not line:
            continue
        if line == "/quit":
            return 0
        if line == "/clear":
            history = [history[0]]
            print("(cleared)")
            continue
        if line == "/list":
            for h, size, ts, label in walrus.list():
                print(f"{h[:12]}.. {size:>8}  {label}")
            continue
        history.append({"role": "user", "content": line})
        try:
            reply = chat(history)
        except urllib.error.HTTPError as e:
            reply = f"(http {e.code}: {e.read().decode()[:200]})"
        except Exception as e:
            reply = f"(err: {e})"
        print(reply)
        # pin this turn to walrus
        blob = json.dumps({"user": line, "assistant": reply, "model": MODEL}).encode()
        h = walrus.put(blob, label=f"turn-{len(history)//2}")
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    sys.exit(main())