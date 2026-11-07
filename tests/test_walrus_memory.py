"""
test_walrus_memory.py -- the walrus memory, and the machine it runs on.

Bobby, 2026-11-07: the robot's pattern for each fc system -- the
substrate it reaches, a MEASUREMENT that it reaches it, a NAMED refusal,
a selftest that passes, and the census saying WIRED.

**AND THE BUG WAS MEASURED.** MEASURED 2026-11-07: `walrus_memory.py`'s
root was the literal path `C:/Users/Admin/AppData/Local/hermes/walrus`
-- **a path from a different machine**. This machine's user is HP. And
the REAL store, `C:/Users/HP/AppData/Local/hermes/walrus`, existed with
its `index.sqlite` and **zero blobs in it**.

So every write went to a directory that does not exist and never will,
and the store that was supposed to hold the system's content-addressed
memory was **EMPTY**. **A HARDCODED PATH IS A PATH TO SOMEONE ELSE'S
MACHINE.**
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import walrus_memory as W  # noqa: E402


# ---------------------------------------------------------------------------
# 1. the root points at THIS machine
# ---------------------------------------------------------------------------

def test_the_root_is_not_another_users_machine():
    """**A HARDCODED PATH IS A PATH TO SOMEONE ELSE'S MACHINE.**"""
    root = str(W.DEFAULT_WALRUS_ROOT)
    assert "Users\\Admin\\" not in root, (
        "the store's root is on another machine: %s" % root)
    assert "Users/Admin/" not in root, (
        "the store's root is on another machine: %s" % root)


def test_the_root_is_derived_not_hardcoded():
    """**AND THE FIX IS NOT THE RIGHT USERNAME -- it is a path that is
    DERIVED, because the next machine would be wrong too.**"""
    home = os.path.expanduser("~")
    assert home.lower() in str(W.DEFAULT_WALRUS_ROOT).lower(), (
        "the root is not under this user's home: %s" % W.DEFAULT_WALRUS_ROOT)


def test_the_root_is_the_store_that_exists():
    """**AND THE REAL STORE EXISTS AND IS WHERE THE CODE POINTS.**"""
    assert os.path.isdir(str(W.DEFAULT_WALRUS_ROOT)), (
        "the store's root does not exist: %s" % W.DEFAULT_WALRUS_ROOT)


# ---------------------------------------------------------------------------
# 2. the round trip, and the dedupe
# ---------------------------------------------------------------------------

def test_the_round_trip(tmp_path):
    w = W.WalrusMemory(root=str(tmp_path))
    h = w.put(b"the content", "a label")
    assert w.get(h) == b"the content"
    assert w.has(h)
    assert len(list(w.list())) == 1


def test_the_content_addressing_dedupes(tmp_path):
    """**AND THE DEDUPE IS THE POINT OF A CONTENT ADDRESS** -- the same
    bytes are the same blob, whatever the label."""
    w = W.WalrusMemory(root=str(tmp_path))
    h1 = w.put(b"the content", "one label")
    h2 = w.put(b"the content", "another label")
    assert h1 == h2, "the same content made two hashes"
    assert len(list(w.list())) == 1, "the same content made two blobs"


def test_different_content_makes_different_blobs(tmp_path):
    w = W.WalrusMemory(root=str(tmp_path))
    assert w.put(b"one") != w.put(b"two")


# ---------------------------------------------------------------------------
# 3. the refusal names its reason
# ---------------------------------------------------------------------------

def test_the_refusal_names_the_store(tmp_path):
    """**AND A CALLER CANNOT TELL "NEVER WRITTEN" FROM "WRITTEN AND THEN
    DELETED" FROM "THE STORE IS ON THE WRONG MACHINE"** -- unless the
    refusal says which store it looked in."""
    w = W.WalrusMemory(root=str(tmp_path))
    try:
        w.get("f" * 64)
    except KeyError as exc:
        msg = exc.args[0]
        assert "not in this store" in msg, msg
        assert str(w.root) in msg, msg
    else:
        raise AssertionError("a missing blob was not refused")


def test_the_refusal_is_not_a_bare_keyerror(tmp_path):
    """**AND THE REFUSAL NAMES ITS REASON** -- because the robot's veto
    names the action it refused and a bare KeyError names nothing."""
    w = W.WalrusMemory(root=str(tmp_path))
    try:
        w.get("f" * 64)
    except KeyError as exc:
        assert len(exc.args[0]) > 40, (
            "the refusal is too short to name a reason: %r" % (exc.args[0],))
        assert str(w.root) in exc.args[0]


def test_the_delete_removes_it(tmp_path):
    w = W.WalrusMemory(root=str(tmp_path))
    h = w.put(b"the content", "a label")
    assert w.delete(h)
    assert not w.has(h), "the deleted blob is still there"


# ---------------------------------------------------------------------------
# 4. the selftest, and that it can go RED
# ---------------------------------------------------------------------------

def test_the_selftest_passes():
    assert W._selftest() == 0


def test_the_mutation_check_says_every_mutation_went_red():
    """**A SELFTEST THAT CANNOT FAIL IS NOT A CHECK.**"""
    import subprocess
    tool = os.path.join(REPO, "tools", "mutation_check_walrus.py")
    proc = subprocess.run([sys.executable, "-B", tool],
                          capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, (proc.stdout + proc.stderr)[-1200:]
    assert "every mutation went RED" in proc.stdout, proc.stdout[-600:]
