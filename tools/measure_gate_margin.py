#!/usr/bin/env python3
"""
tools/measure_gate_margin.py -- WHICH INEQUALITY CARRIES THE IDENTITY?

The CLI over `src/measure_gate_margin.py`.

Queue item 40 asked: *"The kernel's gate compares alignment to MIN_COS=0.4,
which measures the winner. So the population's identity is carried in the
SEPARATION between winner and runner-up, not in the winner. Does a
margin-based gate keep the truth counterweight?"*

**THE ANSWER IS NO, AND THE ITEM'S PREMISE WAS MEASURED AGAINST A
CONSTRUCTION THE SUBSTRATE NEVER PRODUCES.** Its three numbers -- "the
MARGIN does change, by 6.09x at population 16", "1-bit pass 50% at pop
4, 17% at pop 8..32, 0% at pop 64..128" -- are reproduced EXACTLY by
this same file at commit fb6ae67, which measured the FRAME-CROWD model.
Commit a5826e8 replaced that construction, because the substrate
transmits the speaker's address ALONE and the crowd arrives through the
channel's taps, where the equaliser cancels it.

Run:  python tools/measure_gate_margin.py
Exit: 0 when the measurement ran, 1 otherwise.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    """Run the measurement. Every printed line is computed, not written."""
    import measure_gate_margin

    print("=" * 74)
    print("WHICH INEQUALITY CARRIES THE IDENTITY?")
    print("=" * 74)
    print()
    print("  this tool has no prose of its own. the measurement lives in")
    print("  src/measure_gate_margin.py, and every number below is")
    print("  computed from the rows it just measured.")
    print()
    return measure_gate_margin.main()


if __name__ == "__main__":
    sys.exit(main())
