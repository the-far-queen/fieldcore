"""
mutation_restore.py -- PUT A MUTATED FILE BACK EXACTLY AS IT WAS.

Bobby, 2026-11-07.

**AND THE GATE WAS RIGHT AND THE DEFECT WAS OURS.** MEASURED 2026-11-07:
the full fieldcore suite failed `test_the_gate_exposes_a_staleness_check`
in EVERY run, and it passed in isolation. REPRODUCED:

    BEFORE the mutation check, the gate says stale: None
    AFTER  the mutation check, the gate says stale: the gate's rules on
    disk are newer than the rules it is using: built=4316721aa20c
    (369 files) disk=368a2bc086a2 (369 files) moved=walrus_memory.py

**AND THE CAUSE: A MUTATION CHECK REWRITES THE REAL `src/*.py` AND
RESTORES ITS BYTES -- BUT THE WRITE MOVES THE FILE'S MTIME, AND
`gate_staleness.py` FINGERPRINTS THE MTIME OF EVERY RULE FILE.** So the
bytes were the same and the mtime was not, and the gate watched a file
that moved and named it. **THE GATE WAS RIGHT.**

**AND THIS IS A WHOLE-CLASS DEFECT**: any tool that writes a real source
file and restores its bytes leaves the tree looking changed. The bytes
are the same and the mtime is not, and a rule file that moved is the
whole point of the staleness check.

**SO THE RESTORE PUTS BOTH BACK**, and the tree ends byte-identical AND
stat-identical.
"""

from __future__ import annotations

import os
from pathlib import Path


class Restored:
    """A file that will be put back exactly as it was.

    **AND EXACTLY MEANS BYTES AND MTIME.** The bytes are what a reader
    sees and the mtime is what the gate fingerprints, and restoring one
    without the other has left the tree changed.

    Use it as a context manager:

        with Restored(TARGET) as f:
            f.write(mutated)
            ... run the thing that must go red ...

    and the file is back, byte-identical and stat-identical, whether the
    body raised or not.
    """

    def __init__(self, path):
        self.path = Path(path)
        self._original: str = ""
        self._stat = None

    def __enter__(self) -> "Restored":
        self._original = self.path.read_text(encoding="utf-8")
        self._stat = self.path.stat()
        return self

    def write(self, text: str) -> None:
        """Write the mutated text. The restore is the context's job."""
        self.path.write_text(text, encoding="utf-8")

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.path.write_text(self._original, encoding="utf-8")
        # AND THE MTIME GOES BACK TO WHERE IT WAS.
        os.utime(self.path,
                 ns=(self._stat.st_atime_ns, self._stat.st_mtime_ns))
        return False
