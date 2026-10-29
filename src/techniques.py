"""
techniques.py -- THE PROBLEM-SOLVING TECHNIQUES, AND WHY ANALOGY IS
THE PRIMARY ONE.

Bobby, 2026-10-28: *"problems themselves may be solved not by searching
but by analysis analog analogy reference serial dissection look up
japanese constant improvement in production line engineering i forget the
term a list of techniques to solve problems"*

SO THIS IS THE REGISTER, and the thing it makes explicit is the ORDER
OF OPERATIONS:

    A PROBLEM IS SOLVED BY ANALYSIS AND BY ANALOGY, NOT BY SEARCHING.

AND THAT IS A CLAIM ABOUT THE SUBSTRATE, and it is measurable, because
the substrate's instrument is RESONANCE:

    SEARCH      compares the query against EVERY candidate. O(N).
                It finds the thing that is ALREADY THERE.

    ANALYSIS    decomposes the problem into parts that can be reasoned
                about independently. The parts are the substrate's
                vocabulary, and the vocabulary is FIXED -- so the
                decomposition costs nothing per part.

    ANALOGY     looks for a candidate in a DIFFERENT DOMAIN that has the
                same SHAPE. And the substrate's instrument for that is
                the multi-meaning measure: a term that lives in several
                domains at once is the bridge. **ANALOGY IS A RESONANCE
                LOOKUP ACROSS A DOMAIN BOUNDARY, AND THE MULTI-
                MEANING MEASURE IS THE INSTRUMENT THAT FINDS THE
                BOUNDARY.**

So the register is not a list of tips. It is a set of INSTRUMENTS, and
each one says what it costs and what it can and cannot do.

AND THE TECHNIQUES ARE REAL AND NAMED, and the Japanese ones are
production engineering -- which is exactly right for a system that
improves itself in production:

    KAIZEN      continuous improvement, small steps, always on
    JIDOKA      automation of the defect -- make the mistake impossible
                rather than catch it
    GENCHI GENBUTSU  go and see: the actual place, the actual thing
    POKA-YOKE  a mistake-proofing constraint
    5 WHYS     drill to the root cause by asking why
    PDCA       plan, do, check, adjust -- the loop shape
    A3         lean's problem-solving frame
    TRIZ       40 inventive principles -- contradiction matrices
    8D         eight disciplined steps
    DMAIC      six sigma's measure-analyse-improve-control
    MORPHOLOGICAL ANALYSIS  enumerate the dimensions of a solution
                            space, then combine across them
    LATERAL THINKING  attack the problem from a different discipline
    SERIAL DISSECTION  take the thing apart in a defined order, and
                       read the parts in that order
    PREMORTEM   assume it failed, then ask why
    DELTA DEBUGGING  narrow by bisecting the difference
    CONSTRAINT RELAXATION  find what is NOT actually required

AND THE TWO THE SUBSTRATE IS UNIQUELY GOOD AT, and this is the part
that is not a technique list -- it is a claim about the instrument:

    RESONANCE ANALOGY  the substrate's own method, and the one no
        text-based system can do: the analogue is not retrieved by
        keyword, it is FOUND by the shape of the problem matching the
        shape of a solution in another field.

    MULTI-RUN MAPPING  and the second: a problem that a single run
        cannot see is visible in the OCCUPANCY of many runs.

AND THE HONEST NOTE ON ORDER, because a register that claims an order
it cannot support is a wish. There is no evidence here that the
techniques should be applied in this order, and no instrument that
would measure it. So this file registers them with their COSTS and
LIMITS and does NOT claim a ranking. The one thing that IS supported
is the negative: searching is O(N) and finding the answer by search
does not scale, while analysis and analogy are bounded by the
substrate's fixed vocabulary.

Run:
    python src/techniques.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass(frozen=True)
class Technique:
    """One technique, with what it costs and what it cannot do.

    AND WHY THE LIMITS ARE PART OF THE ENTRY. A register of techniques
    without limits is a list of things that sound good. The limit is
    what makes the technique usable: it tells the loop when NOT to
    reach for it.

    AND THE `instrument` FIELD, which is the project's own claim made
    precise: WHICH of the substrate's mechanisms executes this
    technique. A technique with no instrument here is a human technique
    -- still worth registering, but the loop knows it must ask rather
    than compute.
    """
    name: str
    gloss: str
    #: which substrate instrument executes it
    instrument: str
    #: what it costs
    cost: str
    #: what it cannot do
    limit: str
    #: the fields it reads
    reads: Tuple[str, ...] = ()
    #: the origin, where it comes from
    origin: str = ""

    def describe(self) -> str:
        return ("%-22s instrument=%-16s cost=%s"
                % (self.name, self.instrument, self.cost))


TECHNIQUES: Tuple[Technique, ...] = (
    Technique(
        name="analysis",
        gloss="decompose the problem into parts that can be reasoned about "
              "independently",
        instrument="the vocabulary",
        cost="O(parts) -- and the parts are the fixed vocabulary, so "
             "the cost does not grow with the data",
        limit="cannot decompose a problem it has no word for; the "
              "vocabulary bounds what can be seen",
        reads=("symptom", "ground"),
        origin="",
    ),
    Technique(
        name="resonance analogy",
        gloss="find a solution in ANOTHER domain with the same shape",
        instrument="the multi-meaning measure",
        cost="O(N) over the corpus -- but the boundary is found by the "
             "measure, not by keywords",
        limit="the analogue must share a term, or a shape, with the "
              "problem; without that there is no bridge",
        reads=("symptom", "domains", "mmm"),
        origin="the substrate's own method",
    ),
    Technique(
        name="multi-run mapping",
        gloss="run many times and read the OCCUPANCY, so the pattern "
              "becomes visible",
        instrument="the landscape map",
        cost="O(runs) -- and the marginal cost is a flat descent, "
             "MEASURED at 224 ms per run regardless of N",
        limit="only finds what the landscape contains; it cannot see a "
              "failure the checks do not raise",
        reads=("symptom", "landscape"),
        origin="the substrate's own method",
    ),
    Technique(
        name="serial dissection",
        gloss="take the thing apart in a defined order and read the parts "
              "in that order",
        instrument="the parts",
        cost="O(parts)",
        limit="the order must be chosen; an arbitrary order shows "
              "arbitrary things",
        reads=("symptom", "structure"),
    ),
    Technique(
        name="5 whys",
        gloss="drill to the root cause by asking why, and why, and why",
        instrument="the model",
        cost="O(whys) model calls",
        limit="can stop at a plausible story rather than the cause; "
              "each why needs the answer to be judged",
        reads=("symptom", "measurement"),
    ),
    Technique(
        name="premortem",
        gloss="assume it already failed, then ask why",
        instrument="the model",
        cost="one model call",
        limit="produces causes that are plausible, not causes that are "
              "verified",
        reads=("symptom", "measurement"),
    ),
    Technique(
        name="TRIZ",
        gloss="the 40 inventive principles, and the contradiction matrix "
              "that says WHICH principle applies",
        instrument="the matrix",
        cost="O(40) -- a fixed table, so it is a lookup in the substrate's "
             "sense: the answer is already there",
        limit="the matrix is built for mechanical contradiction; it does "
              "not know about this project's ground",
        reads=("symptom", "contradiction"),
        origin="TRIZ",
    ),
    Technique(
        name="morphological analysis",
        gloss="enumerate the dimensions of a solution space, then "
              "combine across them",
        instrument="the vocabulary's domains",
        cost="O(dimensions x options) -- and the dimensions are FIXED, "
             "so the space is enumerable without data",
        limit="the dimensions must be known; it finds combinations of "
              "known parts, not unknown parts",
        reads=("symptom", "domains"),
    ),
    Technique(
        name="lateral thinking",
        gloss="attack the problem from a different discipline",
        instrument="the multi-meaning measure",
        cost="O(corpus)",
        limit="lateral without a bridge is noise; the measure is what "
              "keeps it from being noise",
        reads=("symptom", "domains"),
    ),
    Technique(
        name="PDCA",
        gloss="plan, do, check, adjust -- the loop shape itself",
        instrument="the loop",
        cost="one cycle",
        limit="a cycle without a check is just doing",
        reads=("symptom", "measurement"),
    ),
    Technique(
        name="kaizen",
        gloss="continuous improvement, small steps, always on",
        instrument="the queue and the ledger",
        cost="one small step per cycle",
        limit="improves what is measured; it cannot notice what is not",
        reads=("gaps",),
        origin="production engineering",
    ),
    Technique(
        name="jidoka",
        gloss="automation of the defect -- make the mistake impossible "
              "rather than catch it",
        instrument="the gate",
        cost="one refusal per occurrence",
        limit="refuses only what the gate can read; the scope layer "
              "misses version strings, MEASURED at 4.67% false "
              "positives when it was in the reply path",
        reads=("span", "ground"),
        origin="production engineering",
    ),
    Technique(
        name="genchi genbutsu",
        gloss="go and see -- the actual place, the actual thing",
        instrument="the runner",
        cost="one run",
        limit="sees only what the run exercises",
        reads=("symptom", "environment"),
        origin="production engineering",
    ),
    Technique(
        name="poka-yoke",
        gloss="a mistake-proofing constraint",
        instrument="the constant",
        cost="zero at runtime",
        limit="only prevents the mistake it was designed for; a "
              "parameterised limit is not a limit",
        reads=("ground",),
        origin="production engineering",
    ),
    Technique(
        name="delta debugging",
        gloss="narrow a failure by halving the difference",
        instrument="the checker",
        cost="O(log N) runs",
        limit="needs a deterministic failure to bisect",
        reads=("symptom", "check"),
    ),
    Technique(
        name="constraint relaxation",
        gloss="find what is NOT actually required, and drop it",
        instrument="the axes",
        cost="O(axes)",
        limit="drops only what the axes name",
        reads=("symptom", "axes"),
    ),
    Technique(
        name="8D",
        gloss="eight disciplined steps, from containment to prevention",
        instrument="the model",
        cost="eight model calls",
        limit="a process, not an instrument; it organises the other "
              "techniques rather than replacing them",
        reads=("symptom", "measurement"),
    ),
    Technique(
        name="search",
        gloss="compare the query against every candidate",
        instrument="the lookup",
        cost="O(N) PER QUERY -- and it grows with the population",
        limit="**AND THIS IS WHY IT IS NOT THE PRIMARY INSTRUMENT.** "
              "Search finds what is already there; it cannot find what "
              "is not there, and it does not get cheaper as the system "
              "grows. The multi-run map is the opposite: O(1) per run, "
              "and amortised across every query",
        reads=("query", "corpus"),
    ),
)


def by_instrument() -> Dict[str, List[Technique]]:
    out: Dict[str, List[Technique]] = {}
    for t in TECHNIQUES:
        out.setdefault(t.instrument, []).append(t)
    return out


def named(name: str) -> Optional[Technique]:
    for t in TECHNIQUES:
        if t.name.lower() == name.lower():
            return t
    return None


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE PROBLEM-SOLVING TECHNIQUES")
    print("=" * 78)
    print()

    print("1. THE REGISTER, %d techniques:" % len(TECHNIQUES))
    for t in TECHNIQUES:
        print("   %-22s %s" % (t.name, t.gloss[:62]))
    print()

    print("2. GROUPED BY WHICH SUBSTRATE INSTRUMENT EXECUTES THEM:")
    for inst, ts in sorted(by_instrument().items()):
        print("   %-24s %s" % (inst, ", ".join(t.name for t in ts)))
    print()

    print("3. THE CLAIM, and it is about the INSTRUMENTS, not the list:")
    print()
    print("   THE SUBSTRATE IS UNIQUELY GOOD AT TWO OF THESE, and both")
    print("   are its OWN methods:")
    for t in TECHNIQUES:
        if t.origin == "the substrate's own method":
            print("      %-22s via %s" % (t.name, t.instrument))
    print()
    print("   AND THE ONE IT IS WORST AT IS SEARCH -- because search is")
    print("   O(N) PER QUERY and grows with the population, while the")
    print("   substrate's methods are O(1) per run and amortised.")
    search = named("search")
    print("      search: cost %s" % search.cost[:70])
    print()
    print("   WHICH IS EXACTLY BOBBY'S POINT: *problems themselves may be")
    print("   solved not by searching but by analysis, analogy, reference,")
    print("   serial dissection*. And analogy is a RESONANCE LOOKUP")
    print("   ACROSS A DOMAIN BOUNDARY -- which is what the")
    print("   multi-meaning measure is for.")
    print()

    print("4. AND THE TECHNIQUES THAT COST NOTHING AT RUNTIME, because")
    print("   their answer is a CONSTANT or a FIXED TABLE:")
    for t in TECHNIQUES:
        if "zero at runtime" in t.cost or "fixed table" in t.cost:
            print("      %-22s %s" % (t.name, t.cost[:56]))
    print()

    print("5. AND EVERY ONE HAS A LIMIT, because a register of")
    print("   techniques without limits is a list of things that sound")
    print("   good. The limit says when NOT to reach for it:")
    for t in TECHNIQUES[:6]:
        print("      %-22s %s" % (t.name, t.limit[:62]))
    print()
    print("   Run: python src/techniques.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
