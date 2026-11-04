#!/usr/bin/env python3
"""
tools/measure_failup.py -- HOW MANY FAIL UPWARDS, the CLI over the
corrected bench.

Bobby, 2026-10-25: *"how many fail upwards ie widening is optimal"*.
And 2026-11-01, twice: *"no grow pop at 1 bit first"* and *"nope we
got as far as increasing number of stalks ie population was cheaper at
1 bit and only the 4 and 8 bit then increase pop again not 16 32 64
etc"*.

THE QUESTION, and it is the one the earlier bench got wrong:
**CAN THE RECEIVER TELL WHICH STALK SPOKE?** Not "can I hear it" -- that
is a loopback question, and the earlier bench asked it and reported a
100% pass rate, which looked like the gate never escalates.

**THIS FILE USED TO CARRY ITS OWN COPY OF THE MEASUREMENT, AND THE COPY
WAS WRONG.** It built a FRAME carrying the speaker's address PLUS the
crowd's addresses added to the frame itself, and it printed PROSE that
its own output contradicted -- the hard-coded text claimed "the
population at which the 1-bit read STOPS WINNING is 4" while the run
above it printed 0% at population 2, which is BELOW chance, and the
shuffled control BEAT the measurement at population 16.

**THE ROOT OF IT: the frame-crowd construction is a MODEL, not the
system.** The substrate transmits the speaker's address ALONE and the
crowd arrives through the channel's taps, where the equaliser cancels
it. MEASURED, the recovered spectrum against the transmitted one
differs by 2.9e-15 of the signal scale at population 4 and 4.8e-14 at
population 64.

So there is now ONE measurement, in `src/bench_failup.py`, and this
file is its CLI. One measurement, one construction, one set of
controls -- because two measurements of "how many fail upwards" that
disagree is how the stale numbers travelled through four source files
and a test.

AND THE PROSE IS GONE FROM HERE. Every line this file prints is
computed from the rows it just measured. A hard-coded sentence beside
a measured number is how "the population at which the 1-bit read stops
winning is 4" came to contradict the 0% printed two lines above it.

Run:  python tools/measure_failup.py
Exit: 0 when the bench ran, 1 otherwise.
"""
from __future__ import annotations

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    """Run the bench. Every printed line is computed, not written."""
    import bench_failup

    print("=" * 74)
    print("HOW MANY FAIL UPWARDS -- population first, and the control")
    print("=" * 74)
    print()
    print("  this tool has no prose of its own. the measurement lives in")
    print("  src/bench_failup.py, and every number below is computed")
    print("  from the rows it just measured.")
    print()
    return bench_failup.main()


if __name__ == "__main__":
    sys.exit(main())
