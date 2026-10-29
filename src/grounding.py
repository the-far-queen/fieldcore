"""
grounding.py -- THE SUBSTRATE'S OWN GROUNDINGS. It computes; the model
articulates.

Bobby, 2026-10-28: *"try how mant numbers from 1 to 10 inclsuive we
will develop simself in code not philosophy"*

SO THIS FILE IS THE ANSWER TO A DEFECT THE MEASUREMENT FOUND, and the
defect is a real one about who does what.

MEASURED, through Hermes' own provider API:

    Q: how many numbers are there from 1 to 10 inclusive?
    A: 10 numbers.                         <- CORRECT
       governor: allowed
       atlas:   fail
         "the answer carries numbers and the context grounds none of them"

    Q: what is 1+2+3+4+5+6+7+8+9+10?
    A: 55                                   <- CORRECT
       governor: REFUSED
       atlas:   None

**THE ANSWERS WERE RIGHT AND THE SYSTEM SAID THEY WERE WRONG.** And
that is the failure worth naming: the model was asked to do arithmetic
it did not need to do, and then the answer was graded against a
grounding nobody had produced.

THE DIVISION, and it is the project's own shape applied to arithmetic:

    THE SUBSTRATE COMPUTES.   It holds the numbers, and it can produce
                               them exactly, with a command that
                               reproduces them.
    THE MODEL ARTICULATES.    It says what the number means in a
                               sentence, in the system's own voice.

    THE ATLAS GRADES the articulation against the substrate's grounding.
    So "55" passes because the SUBSTRATE grounded 55, not because the
    model was trusted.

AND WHY THE MODEL MUST NOT BE THE ONE COMPUTING. Three reasons, and
the third is the load-bearing one:

    1. THE MODEL CAN HALLUCINATE A COUNT. It said 10 and 55 and both
       were right -- but a model asked "how many numbers from 1 to 10"
       is one token away from "how many numbers from 1 to 11", and
       there is no check on a fluent count.
    2. THE SUBSTRATE CAN REPRODUCE IT. The evidence link names a
       command. A model cannot name a command that reproduces its own
       arithmetic.
    3. **THE GROUNDING IS WHAT MAKES THE ANSWER ADMISSIBLE.** The
       atlas's provenance area asks whether every number in the answer
       is in the context's grounding. If the substrate does not
       compute, there IS no grounding, and every correct answer is
       inadmissible. That is the defect.

AND THE TWO CONTEXTS THE ATLAS WANTS, and this file produces both:

    ctx["source"]              where the number came from
    ctx["grounded_numbers"]    the numbers that are grounded

AND WHY THE GROUNDED NUMBERS ARE A LIST AND NOT A FLAG. Because the
provenance area checks EACH number against the grounding, within 5%. A
flag could only say "trust this answer"; a list says "these specific
numbers are grounded, and any other number in the answer is not".

AND WHAT IT DOES NOT DO. It does not compute arbitrary mathematics.
It computes what this substrate can measure and reproduce: the counts,
the sums, the axis values, the locus dimensions. A question outside
that set gets no grounding, and the answer is then inadmissible -- which
is the honest outcome, and the gate says so.

Run:
    python src/grounding.py --selftest
"""

from __future__ import annotations

import json
import os
import re
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

#: The numbers in a text, and the patterns that name a range.
_NUM = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Grounding:
    """What the substrate measured, and how to reproduce it.

    AND THE THREE PARTS, and they map exactly onto what the atlas's two
    areas read:

        source             the command that reproduces it
        grounded_numbers   the numbers that are grounded
        detail             what was measured, in words
    """

    source: str = ""
    grounded_numbers: List[float] = field(default_factory=list)
    detail: str = ""
    kind: str = ""

    def context(self) -> Dict[str, Any]:
        """The atlas's context, and only the keys it reads."""
        return {
            "source": self.source,
            "grounded_numbers": list(self.grounded_numbers),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "grounded_numbers": list(self.grounded_numbers),
            "detail": self.detail,
        }


class Grounder:
    """THE SUBSTRATE'S GROUNDINGS. It computes what it can reproduce."""

    # -- the measurements ----------------------------------------------

    def count_integers(self, lo: int, hi: int) -> Grounding:
        """How many integers from lo to hi, INCLUSIVE.

        AND THE INCLUSIVE DETAIL, which is the whole question. A count
        from 1 to 10 inclusive is TEN, because there are ten integers:
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10. The off-by-one here is the
        classic one, and the substrate computes it from the range
        itself rather than being asked to.

        AND THE GROUNDED NUMBERS ARE BOTH: the count AND the bounds. So
        an answer that says "10" is grounded, and so is one that says
        "from 1 to 10" -- because 1 and 10 are grounded too.
        """
        if hi < lo:
            lo, hi = hi, lo
        count = hi - lo + 1
        return Grounding(
            source="python src/grounding.py --selftest",
            grounded_numbers=[float(count), float(lo), float(hi)],
            detail="there are %d integers from %d to %d inclusive"
                   % (count, lo, hi),
            kind="count",
        )

    def sum_integers(self, lo: int, hi: int) -> Grounding:
        """The sum from lo to hi, inclusive."""
        if hi < lo:
            lo, hi = hi, lo
        total = (hi * (hi + 1)) // 2 - ((lo - 1) * lo) // 2
        return Grounding(
            source="python src/grounding.py --selftest",
            grounded_numbers=[float(total), float(lo), float(hi)],
            detail="the sum of the integers from %d to %d inclusive is %d"
                   % (lo, hi, total),
            kind="sum",
        )

    def substrate_facts(self) -> Grounding:
        """The substrate's own dimensions and counts.

        AND WHY THIS IS HERE. A question about the system -- "how many
        stalks", "how many modes", "how many axes" -- is answerable
        exactly by the substrate, and the answer must be grounded, or
        the atlas refuses it.
        """
        nums: List[float] = []
        detail: List[str] = []
        src = "python src/grounding.py --selftest"

        try:
            from locus import Locus
            from wound_core import CoaxWinding
            stalks = [CoaxWinding(
                id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                n_in=12, n_out=13 + (i % 2)) for i in range(8)]
            loc = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
            d = loc.describe()
            nums += [float(d.get("stalks") or 0), float(d.get("modes") or 0),
                     float(d.get("states") or 0)]
            detail.append("%s stalks, %s modes" % (d.get("stalks"),
                                                   d.get("modes")))
        except Exception:
            pass

        try:
            from constitutional.constitution import Constitution
            c = Constitution()
            nums.append(float(len(c.axis_names)))
            detail.append("%d constitutional axes" % len(c.axis_names))
        except Exception:
            pass

        try:
            from awareness import build_awareness
            aw = build_awareness()
            nums.append(float(len(aw.topics)))
            detail.append("%d topics in the vocabulary" % len(aw.topics))
        except Exception:
            pass

        return Grounding(source=src, grounded_numbers=nums,
                         detail="; ".join(detail), kind="substrate")

    # -- the matching ---------------------------------------------------

    def ground(self, question: str) -> Optional[Grounding]:
        """What the substrate can measure about this question.

        AND THE ORDER, cheapest and most specific first. A question
        that is about a range is about the range, not about the
        substrate -- so the range patterns are tried before the general
        substrate facts.

        AND IT RETURNS NONE FOR WHAT IT CANNOT MEASURE. A question with
        no grounding gets no grounding, and the answer is then
        inadmissible -- which is the honest outcome. The substrate does
        not fabricate a grounding to make an answer pass.
        """
        q = (question or "").lower()

        # a range: "from 1 to 10", "1..10", "between 1 and 10"
        m = (re.search(r"(?:from|between)\s+(-?\d+)\s+(?:to|and|through)\s+"
                       r"(-?\d+)", q)
             or re.search(r"(-?\d+)\s*(?:\.\.|to|through)\s*(-?\d+)", q))
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if re.search(r"sum|add|total|together", q):
                return self.sum_integers(lo, hi)
            return self.count_integers(lo, hi)

        # an explicit sum: "1+2+3+...+10"
        m2 = re.search(r"((?:\d+\s*\+\s*)+\d+)", q)
        if m2:
            nums = [int(x) for x in re.findall(r"\d+", m2.group(1))]
            if nums:
                lo, hi = min(nums), max(nums)
                if len(nums) > 2 or nums != list(range(lo, hi + 1)):
                    total = sum(nums)
                    return Grounding(
                        source="python src/grounding.py --selftest",
                        grounded_numbers=[float(total)] + [float(n) for n in nums],
                        detail="the sum of %s is %d"
                               % (" + ".join(str(n) for n in nums), total),
                        kind="sum")

        # the substrate's own facts
        if any(w in q for w in ("stalk", "mode", "axis", "axes", "topic",
                                "substrate", "locus", "ground", "you",
                                "yourself", "exist", "self")):
            return self.substrate_facts()

        return None


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE SUBSTRATE'S OWN GROUNDINGS")
    print("=" * 78)
    print()

    g = Grounder()
    cases = [
        ("how many numbers are there from 1 to 10 inclusive?",
         "count"),
        ("count the integers from 1 to 10 inclusive", "count"),
        ("how many numbers from 3 to 7 inclusive", "count"),
        ("what is 1+2+3+4+5+6+7+8+9+10?", "sum"),
        ("what is the sum of the integers from 1 to 10?", "sum"),
        ("how many stalks are in the locus?", "substrate"),
        ("do you exist?", "substrate"),
        ("what is the capital of Peru?", "NONE"),
    ]
    for q, expect in cases:
        r = g.ground(q)
        got = r.kind if r else "NONE"
        flag = "" if got == expect else "   <- WRONG"
        print("   %-52s -> %-10s %s" % (q[:50], got, flag))
        if r:
            print("      %s" % r.detail[:88])
            print("      grounded: %s | source: %s"
                  % ([round(n, 4) for n in r.grounded_numbers][:6],
                     r.source[:40]))
    print()

    print("2. THE ATLAS, with the substrate's grounding:")
    from mini_atlas import standard_atlas
    atlas = standard_atlas()
    for q in ["10 numbers.", "55",
              "The answer is 55, measured by summing 1 through 10."]:
        gr = g.ground(q)
        ctx = gr.context() if gr else {}
        r = atlas.examine(q, ctx)
        fails = [x for x in r["areas"] if x["verdict"] == "fail"]
        print("   %-52s %s" % (q[:50], r["verdict"]))
        for x in fails:
            print("      FAIL %s: %s" % (x["area"], x["reason"][:70]))
    print()
    print("   AND THE QUESTION THAT MATTERS: does the grounding make the")
    print("   CORRECT answer admissible?")
    gr = g.ground("what is 1+2+3+4+5+6+7+8+9+10?")
    ctx = gr.context()
    r = atlas.examine("55", ctx)
    print("   '55' with the substrate's grounding -> %s" % r["verdict"])
    print("   %s" % r["reason"] if "reason" in r else "")
    print()
    print("   Run: python src/grounding.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
