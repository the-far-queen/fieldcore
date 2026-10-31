"""
ladder_cap.py -- THE MEASURED CAP ON THE DUAL LADDER, AND HOW TO RE-RUN IT.

WHY THIS FILE EXISTS
--------------------
The dual ladder (`dual_ladder.py`) climbs two axes: the WIDTH and the
POPULATION. It was built with the full axes -- width up to 256 bits and
population up to 32 stalks -- on the assumption that the geometry is
right and the cost is the only thing that stops the climb.

THE MEASUREMENT SAYS OTHERWISE. The 2026-10-25 balance-point bench
found that the surplus (the bits left after paying for the names) PEAKS
at a low population and goes NEGATIVE above it. So the upper rungs of
the ladder buy a width the reading cannot carry and a population that
costs SNR. They are decoration.

THE CAP, as measured (see `corpus/ladder_cap.json` for the full table):

    peak population  3
    peak width       4 bits   (the channel at population 3 carries two
                                taps, and two taps derive four bits)

THE CAP IS A MEASUREMENT, NOT A CONSTANT, and that is the whole point
of this file. A cap written as a literal in the code -- `POP 3` typed
into a tuple -- is a number nobody can re-run, and it outlives the
measurement that produced it. So the measurement lives in a DATA FILE,
next to the bench that produced it, with:

  * the command that produced it, so a reader can re-run it
  * the sha256 of the bench source, so a change to the bench
    INVALIDATES the cap instead of silently outliving it
  * the per-condition table, so the answer can be read, not just
    trusted

WHAT THE CAP IS FOR
-------------------
The ladder's GEOMETRY is not truncated. The full 13 rungs are still
built, because the axes are the nested stalk topology (hyperlocal ->
groups -> area -> full) and the Rust core's width ladder (1 / 4 / 8 /
... / 256), and neither of those is a performance setting. Truncating
them would make the Python ladder disagree with the substrate it
mirrors.

What the cap does is mark the rungs above the measured ceiling as
UNREACHABLE, and make the ladder REFUSE to climb into them, naming the
measured surplus as the reason. That is the same move the Rust core
already makes at its own top: "the terminal state is not a width, it is
a change of kind (Unanswerable)". The ladder keeps its full geometry;
the REFUSAL is what changes.

THE HONEST CAVEAT, which the cap file carries too
--------------------------------------------------
The crowd amplitude is a free parameter with no measured physical value
in this repo. The SHAPE is what the cap rests on -- the peak is at 3 in
every condition measured, under both crowd models -- and not the
absolute surplus. And the cap assumes the FREQUENCY path, which is the
one the bench measures. The RATIO path (`wound_core.py::PopulationCode.
readout`) is a separate question and is NOT settled by this cap.

Run:
    python src/ladder_cap.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

#: The cap file. It sits in `corpus/` beside `predicates.json`, because
#: it is the same kind of thing: a MEASURED fact the system is held to.
CAP_PATH = os.path.join(os.path.dirname(_HERE), "corpus", "ladder_cap.json")

#: The bench that produced the measurement, and the file whose sha256
#: pins the measurement to the code that made it.
BENCH_PATH = os.path.join(_HERE, "bench_balance_final.py")


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class CapError(RuntimeError):
    """The cap file is missing, malformed, or stale.

    A cap that cannot be read must NOT silently become "no cap", and it
    must not silently become a different cap. It is a refusal by name.
    """


class LadderCap:
    """The measured ceiling on the ladder, with its provenance.

    `population` and `width` are the measured peak. `reason` says why
    the rungs above it are unreachable, and `command` says how to
    re-measure it.
    """

    def __init__(self, data: Dict[str, Any]):
        self.raw = data
        self.population: int = int(data["peak_population"])
        self.width: int = int(data["peak_width"])
        self.command: str = str(data["command"])
        self.measured_on: str = str(data.get("measured_on", ""))
        self.bench_sha256: str = str(data.get("bench_sha256", ""))
        self.conditions: List[Dict[str, Any]] = list(data.get("conditions", []))
        self.caveat: str = str(data.get("caveat", ""))

    # -- the rule ---------------------------------------------------------

    def allows(self, width: int, population: int) -> bool:
        """Is this rung inside the measured ceiling?

        THE RULE, and it is the measured shape: a rung is reachable if
        its population is at or below the measured peak population. The
        WIDTH is not a second axis here, because `width_for` DERIVES the
        width from the channel, and the channel's taps are a function of
        the population. So at a given population the width is whatever
        the channel gives, and the population is the thing the
        measurement constrains.
        """
        return population <= self.population

    def reason_for(self, width: int, population: int) -> str:
        """Why this rung is unreachable, in words that name the number."""
        if self.allows(width, population):
            return ""
        worst = self.worst_surplus()
        return ("population %d is above the measured peak %d: the surplus "
                "at the peak is %s and it falls from there, so this rung "
                "buys a width the reading cannot carry (%s)"
                % (population, self.population,
                   ("%+.2f bits" % worst) if worst is not None else "negative",
                   self.command))

    def worst_surplus(self) -> Optional[float]:
        """The surplus at the peak, if the file records it.

        **AND THE KEY IS `peak_surplus`, BECAUSE THAT IS WHAT THE BENCH
        WRITES.** MEASURED 2026-10-31: this method read `c.get("surplus")`
        while `bench_balance_final.py` writes `"peak_surplus"`. The key
        was never there, so the method returned None on every call and
        `reason_for()` said the surplus at the peak was "negative" --
        while the measured surplus is +7.298 bits. **A refusal that
        quotes a number that is not there is worse than a refusal with
        no number**, because a reader checks the number.

        So the reader takes the key the writer writes. And it takes the
        bare key too, so an older file that used it still reads.
        """
        vals = []
        for c in self.conditions:
            if c.get("peak_population") != self.population:
                continue
            surplus = c.get("peak_surplus")
            if surplus is None:
                surplus = c.get("surplus")
            if surplus is None:
                continue
            vals.append(float(surplus))
        if not vals:
            return None
        return min(vals)

    def peak_populations(self) -> List[int]:
        """Every peak the measurement found, one per condition.

        A cap that only holds in ONE condition is a knife edge, not a
        result (central rule 6). This is the list that shows whether the
        peak is the SAME in every condition.
        """
        return sorted({int(c["peak_population"]) for c in self.conditions
                       if c.get("peak_population") is not None})

    def describe(self) -> str:
        peaks = self.peak_populations()
        return ("peak population %d (measured in %d conditions, peaks %s), "
                "peak width %d bits, measured %s by %s"
                % (self.population, len(self.conditions), peaks,
                   self.width, self.measured_on, self.command))


def load_cap(path: Optional[str] = None, check_bench: bool = True) -> LadderCap:
    """Read the cap, and refuse it if the bench has moved under it.

    THE STALENESS CHECK. The cap file carries the sha256 of the bench
    that produced it. If the bench has changed since, the measurement
    may no longer hold -- a new crowd model, a different channel, a
    changed equaliser -- so the cap must be RE-MEASURED, not inherited.

    This is the check that a cap living in code as a literal can never
    have, and it is the reason the measurement is a file.
    """
    p = path or CAP_PATH
    if not os.path.exists(p):
        raise CapError(
            "no cap file at %s: the ladder's ceiling is a MEASUREMENT, "
            "and the measurement is not there. Re-measure it with "
            "`python src/bench_balance_final.py` and write the file."
            % p)
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        raise CapError("the cap file at %s will not parse: %s" % (p, exc))
    cap = LadderCap(data)
    if check_bench and cap.bench_sha256:
        if not os.path.exists(BENCH_PATH):
            raise CapError(
                "the cap names a bench sha256 but %s is not there, so the "
                "measurement cannot be tied to the code that produced it"
                % BENCH_PATH)
        actual = _sha256(BENCH_PATH)
        if actual != cap.bench_sha256:
            raise CapError(
                "the cap is STALE: it was measured against bench "
                "sha256 %s and the bench is now %s. The measurement may no "
                "longer hold. Re-run `python src/bench_balance_final.py` "
                "and update corpus/ladder_cap.json."
                % (cap.bench_sha256[:16], actual[:16]))
    return cap


def main() -> int:
    print("=" * 78)
    print("THE LADDER'S MEASURED CAP")
    print("=" * 78)
    print()
    try:
        cap = load_cap()
    except CapError as exc:
        print("  REFUSED: %s" % exc)
        return 1
    print("  %s" % cap.describe())
    print()
    print("  the command that produced it:")
    print("    %s" % cap.command)
    print()
    print("  the per-condition table:")
    print("    %-8s %-8s %-10s %-12s %-10s" % (
        "model", "crowd", "peak pop", "surplus", "capacity"))
    print("    " + "-" * 54)
    for c in cap.conditions:
        # **AND THE KEYS ARE THE BENCH'S OWN.** MEASURED 2026-10-31:
        # this table read `c.get("surplus")` and `c.get("capacity")`
        # while the bench writes "peak_surplus" and "peak_capacity_bits"
        # -- so every row printed "?" for both, and a table of "?"s
        # looks like a measurement that found nothing.
        surplus = c.get("peak_surplus", c.get("surplus"))
        capacity = c.get("peak_capacity_bits", c.get("capacity"))
        print("    %-8s %-8s %-10s %-12s %-10s" % (
            c.get("model", "?"), c.get("crowd", "?"),
            c.get("peak_population", "?"),
            ("%+.2f" % surplus) if surplus is not None else "?",
            ("%.2f" % capacity) if capacity is not None else "?"))
    print()
    peaks = cap.peak_populations()
    print("  the peak is %s across %d conditions" % (
        peaks, len(cap.conditions)))
    print()
    print("  THE CAVEAT, because a cap without one is a rule:")
    for line in cap.caveat.splitlines():
        print("    %s" % line)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
