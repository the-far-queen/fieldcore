"""
mutation_check_walrus.py -- the walrus selftest can go RED.

Bobby, 2026-11-07: the robot's pattern is a NAMED refusal and a selftest
that passes -- and **a selftest that cannot fail is not a check**.

**AND THE BUG THE SELFTEST EXISTS TO CATCH WAS MEASURED.** MEASURED
2026-11-07: `walrus_memory.py`'s root was the literal path
`C:/Users/Admin/AppData/Local/hermes/walrus` -- **a path from a
different machine**. This machine's user is HP. And the REAL store,
`C:/Users/HP/AppData/Local/hermes/walrus`, existed with its
`index.sqlite` and **zero blobs in it**.

So every write went to a directory that does not exist and never will,
and the store that was supposed to hold the system's content-addressed
memory was **EMPTY**. **A HARDCODED PATH IS A PATH TO SOMEONE ELSE'S
MACHINE.**

**AND THE MUTATIONS, one per claim the selftest makes:**

    M1  the root goes back to another user's machine
    M2  the content addressing stops deduping
    M3  the refusal stops naming the store it looked in
    M4  the refusal reverts to a bare KeyError
    M5  the delete stops removing the blob
    M6  the round trip starts returning the wrong bytes

**AND EVERY MUTATION MUST GO RED.** A mutation that stays GREEN is a
claim the selftest does not actually make.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
TARGET = SRC / "walrus_memory.py"

PY = sys.executable


def _run_selftest() -> tuple[bool, str]:
    """Run the walrus selftest and say whether it passed."""
    proc = subprocess.run(
        [PY, "-B", str(TARGET), "--selftest"],
        capture_output=True, text=True, cwd=str(REPO))
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def _mutate(src: str, old: str, new: str) -> str:
    """Return the source with one replacement, or raise if it missed."""
    if old not in src:
        raise AssertionError("the mutation site was not found: %r" % old[:70])
    return src.replace(old, new, 1)


MUTATIONS = [
    ("M1 the root goes back to another user's machine",
     '_DEFAULT_ROOT = __import__("pathlib").Path(\n'
     '    os.environ.get("HERMES_LOCAL_APP_DATA")\n'
     '    or os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes")\n'
     ') / "walrus"',
     '_DEFAULT_ROOT = __import__("pathlib").Path(\n'
     '    r"C:\\Users\\Admin\\AppData\\Local\\hermes") / "walrus"'),

    ("M2 the content addressing stops deduping",
     '        h = self._hash(data)\n        p = self._path(h)',
     '        h = hashlib.sha256(str(time.time()).encode()).hexdigest()\n'
     '        p = self._path(h)'),

    ("M3 the refusal stops naming the store it looked in",
     '"the blob %s is not in this store: %s -- it was never "\n'
     '                "written here, or it was deleted" % (h[:16], self.root))',
     '"the blob %s is not found" % (h[:16],))'),

    ("M4 the refusal reverts to a bare KeyError",
     '            raise KeyError(\n'
     '                "the blob %s is not in this store: %s -- it was never "\n'
     '                "written here, or it was deleted" % (h[:16], self.root))',
     '            raise KeyError(h)'),

    ("M5 the delete stops removing the blob",
     '    def delete(self, h: str) -> bool:',
     '    def delete(self, h: str) -> bool:\n'
     '        return True  # MUTATED: the delete does nothing'),

    ("M6 the round trip starts returning the wrong bytes",
     '        return p.read_bytes()',
     '        return b""  # MUTATED: the wrong bytes'),
]


def main() -> int:
    print("=" * 78)
    print("THE WALRUS SELFTEST, AND WHETHER IT CAN GO RED")
    print("=" * 78)
    print()

    original = TARGET.read_text(encoding="utf-8")
    backup = TARGET.with_suffix(".py.bak")

    ok, out = _run_selftest()
    print("the selftest as it stands: %s" % ("PASSES" if ok else "FAILS"))
    if not ok:
        print(out[-1500:])
        print()
        print("THE SELFTEST DOES NOT PASS, SO THERE IS NOTHING TO MUTATE")
        return 1

    went_red = 0
    stayed_green = []
    try:
        for name, old, new in MUTATIONS:
            TARGET.write_text(_mutate(original, old, new), encoding="utf-8")
            passed, mout = _run_selftest()
            if passed:
                stayed_green.append(name)
                print("  [GREEN] %-52s <-- THE CLAIM IS NOT PROVEN" % name)
            else:
                went_red += 1
                first = ""
                for line in mout.splitlines():
                    if "AssertionError" in line or "Error" in line:
                        first = line.strip()[:70]
                        break
                print("  [RED  ] %-52s %s" % (name, first))
    finally:
        TARGET.write_text(original, encoding="utf-8")
        if backup.exists():
            backup.unlink()

    print()
    print("  mutations that went RED: %d" % went_red)
    print("  mutations that stayed GREEN: %d" % len(stayed_green))
    for n in stayed_green:
        print("     -- %s" % n)
    print()
    if stayed_green:
        print("  EVERY MUTATION MUST GO RED, AND %d DID NOT" % len(stayed_green))
        return 1
    print("  every mutation went RED: the checks hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
