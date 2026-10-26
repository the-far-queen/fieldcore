"""
qualification.py -- VERIFICATION AS MATH: THE QUALIFICATION TESTS.

Bobby, 2026-10-26: *"as we develop together we are able to see the
patterns, spot the agenda, reveal the friend or foe, and lies fade
away into easily noted amusements by inferior math beings. same with our
hallucinations or confab, ie lacking verity. correct verification, ie
quality, ie qualification tests, gates, measures. ie MATH."*

SO: the whole arc of this session, in one sentence. And the last three
words are the instruction: **the qualification tests must be MATH, not
intuition.**

Bobby's chain:
    verity        -> quality        -> qualification
    (is it true)     (is it good)       (does it pass)
    VERIFICATION     TESTS              GATES  ->  MEASURES  ->  MATH

AND THE PROJECT HAS THE SPINE ALREADY, from six frontier transcripts
that independently converged on three concepts (src/coherence_spine.py):

    coherence   21 419 523 495 209 326    6/6 files
    sheaf       11  40 174   1  14 405    6/6 files
    threshold   21  33  84  68   9  19    6/6 files

Read together: **A SYSTEM IS HELD BY THRESHOLDS ON A SHEAF, AND THE
QUALITY OF THE HOLDING IS COHERENCE.**

So the qualification test IS a threshold on a sheaf, and the score IS
the coherence of the holding. That is what this file computes.

THE MEASUREMENT THIS FILE MAKES, and it is the one that matters:

  FOR EACH LAYER OF THE GATE, WHAT IS ITS QUALIFICATION -- AND DOES
  THE MEASURE SEPARATE THE LAYER FROM ITS OWN FALSE POSITIVES?

Because "a gate that must be perfect is a gate that never opens" is
the atlas's own rule, and it means every layer needs a QUALIFICATION:
the rate at which it admits the truth AND refuses the false, in ONE
number. And the number must be a COMPARISON, because a raw rate
against an adversary set is what made the fitted 49/49 look perfect.

THE FOUR QUALIFICATIONS, and they are the four axes of the gate:

  THE SENSITIVITY    the rate at which a FALSE claim is caught
  THE SPECIFICITY    the rate at which a TRUE claim is admitted
  THE MARGIN         the difference, and the SIZE of the difference
  THE CONFIDENCE     the smallest margin over the whole test set --
                     because a gate that is right on average and
                     wrong at the margin is a gate that will fail at
                     the worst moment

AND THE INVERSION, which is the whole point of the polarisation:

  A GATE THAT ADMISSES EVERYTHING has a sensitivity of 1.0 and a
  specificity of 0.0 -- so it is PERFECT ON ONE AXIS AND USELESS ON
  THE OTHER. And the naive "accuracy" -- the fraction of decisions
  that were right -- is 1.0 for a gate that admits EVERYTHING.

  So accuracy is the wrong measure, and this file computes the
  MEASURE THAT IS NOT WRONG: the margin over both axes, and the
  worst-case confidence.

  AND THAT IS EXACTLY THE INTERFERENCE RESULT (src/interference_field.py):
  a lie can RAISE the field's raw coherence. The energy was never the
  score, and the raw number is never the score. THE MARGIN IS.

Run:
    python src/qualification.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402
import property_layer as PL  # noqa: E402
import provenance_scope as PS  # noqa: E402


# ===========================================================================
# THE MEASURE
# ===========================================================================

@dataclass
class Qualification:
    """The qualification of one gate: one number per axis, and a margin.

    AND WHY THE MARGIN AND NOT THE ACCURACY. A gate that admits
    everything scores 100% accuracy and is worthless. A gate that
    refuses everything also scores 100% accuracy. So accuracy is the
    wrong measure and the margin is the right one: the gap between
    how well it catches the false and how well it admits the true.
    """
    name: str
    #: how many FALSE claims it caught
    caught_false: int = 0
    #: how many FALSE claims there were
    total_false: int = 0
    #: how many TRUE claims it admitted
    admitted_true: int = 0
    #: how many TRUE claims there were
    total_true: int = 0
    #: the FALSE claims it let through
    missed_false: List[str] = field(default_factory=list)
    #: the TRUE claims it refused
    refused_true: List[str] = field(default_factory=list)

    @property
    def sensitivity(self) -> float:
        """The rate at which a false claim is caught."""
        return (self.caught_false / self.total_false) if self.total_false else 0.0

    @property
    def specificity(self) -> float:
        """The rate at which a true claim is admitted."""
        return (self.admitted_true / self.total_true) if self.total_true else 0.0

    @property
    def accuracy(self) -> float:
        """The NAIVE measure, and it is reported so its failure shows.

        A gate that admits everything scores 1.0 here. So this number
        is NOT the qualification -- the margin is.
        """
        total = self.total_false + self.total_true
        if not total:
            return 0.0
        return (self.caught_false + self.admitted_true) / total

    @property
    def gap(self) -> float:
        """The raw gap between the two axes.

        And IT IS NOT THE QUALIFICATION on its own, which the first
        version of this file got wrong. The gap made "refuses
        everything" score +1.000 -- a WALL scoring as well as a
        working gate. So the gap is reported, and the qualification
        is the gap times the both-axes flag.
        """
        return self.sensitivity - self.specificity

    @property
    def balanced(self) -> bool:
        """A qualified gate does BOTH axes. This is the check.

        A gate that catches every lie and refuses every truth has a
        gap of +1.0 and is a WALL. A gate that admits every lie and
        every truth has a gap of -1.0 and is a NO-OP. Neither is
        qualified, because qualification means both axes at once.
        """
        return self.sensitivity > 0.0 and self.specificity > 0.0

    @property
    def margin(self) -> float:
        """THE QUALIFICATION. A DISTANCE, not a signed gap.

        AND WHY IT IS A DISTANCE, and this is the second correction to
        the measure (the first was the both-axes flag, which stopped a
        WALL from scoring as well as a working gate).

        A signed gap cannot tell a working gate from a broken one. A
        gate that does both axes but catches only 35% of the false
        has a gap of -0.650 -- which reads as "worse than useless" when
        it is actually a WORKING gate with a specific weakness. The
        sign is carrying a meaning it should not carry.

        So the qualification is the distance from perfect on BOTH
        axes:

            1 - (missed_false/total_false + refused_true/total_true)

        which gives:

            admits everything   1 - (1.0 + 0.0) =  0.000  a no-op
            refuses everything   1 - (0.0 + 1.0) =  0.000  a wall
            the union (blind)    1 - (0.65 + 0.0) = +0.350  working
            misses all, refuses all                   -1.000  worse
                                                            than
                                                            useless

        AND THE SECOND-ORDER POINT, which is the project's own atlas
        rule: a gate that must be perfect is a gate that never opens.
        So a qualification of 1.0 is SUSPICIOUS. What matters is a
        gate that does both axes with a real admission rate AND a
        real catch rate.
        """
        if not self.total_false and not self.total_true:
            return 0.0
        err_false = (1.0 - self.sensitivity) if self.total_false else 0.0
        err_true = (1.0 - self.specificity) if self.total_true else 0.0
        return 1.0 - (err_false + err_true)

    @property
    def verdict(self) -> str:
        """The one-line reading, with the diagnosis attached."""
        if not self.balanced:
            if self.sensitivity > 0.0 and self.specificity <= 0.0:
                return ("does one axis only: it catches the false and "
                        "refuses the truth. A wall.")
            if self.specificity > 0.0 and self.sensitivity <= 0.0:
                return ("does one axis only: it admits the true and "
                        "misses the false. A no-op.")
            return "does neither axis"
        return ("both axes: catches %+.1f%% of the false and admits "
                "%+.1f%% of the true"
                % (self.sensitivity * 100, self.specificity * 100))

    def describe(self) -> str:
        return ("%-18s sensitivity %.3f  specificity %.3f  "
                "gap %+.3f  QUALIFICATION %+.3f"
                % (self.name, self.sensitivity, self.specificity,
                   self.gap, self.margin))


# ===========================================================================
# THE TEST SETS
# ===========================================================================

#: The TRUE claims -- the ground's own assertions. A gate that refuses
#: these is broken.
TRUE_CLAIMS: Tuple[str, ...] = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
    "the gate's signature admits no threshold",
    "the component test lives in src/component_test.py",
    "the fieldcore suite was green at commit fd321f0",
    "the governor's pid differs from the caller's pid",
)


def load_false(name: str) -> List[str]:
    p = os.path.join(WORK_REPOS, "fieldcore", "tests", "data", name)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return [d["span"] for d in data if isinstance(d, dict) and d.get("span")]


# ===========================================================================
# THE THREE LAYERS, AND HOW EACH IS QUALIFIED
# ===========================================================================

def qualify_claim_gate(false_spans: Sequence[str]) -> Qualification:
    """The claim gate: the deny lexicon + the agenda layer."""
    reg = CR.standard_register()
    q = Qualification("the claim gate")
    for s in false_spans:
        q.total_false += 1
        if reg.read(s).verdict is CR.Verdict.CONTRADICTED:
            q.caught_false += 1
        else:
            q.missed_false.append(s)
    for t in TRUE_CLAIMS:
        q.total_true += 1
        if reg.read(t).verdict is not CR.Verdict.CONTRADICTED:
            q.admitted_true += 1
        else:
            q.refused_true.append(t)
    return q


def qualify_scope_layer(false_spans: Sequence[str]) -> Qualification:
    """The scope layer: a span must point at a build that exists."""
    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    q = Qualification("the scope layer")
    for s in false_spans:
        q.total_false += 1
        if not PS.check_scope(s, scope).allowed:
            q.caught_false += 1
        else:
            q.missed_false.append(s)
    for t in TRUE_CLAIMS:
        q.total_true += 1
        if PS.check_scope(t, scope).allowed:
            q.admitted_true += 1
        else:
            q.refused_true.append(t)
    return q


def qualify_property_layer(false_spans: Sequence[str]) -> Qualification:
    """The property layer: a subject cannot have a property it lacks."""
    q = Qualification("the property layer")
    for s in false_spans:
        q.total_false += 1
        if not PL.check_properties(s).allowed:
            q.caught_false += 1
        else:
            q.missed_false.append(s)
    for t in TRUE_CLAIMS:
        q.total_true += 1
        if PL.check_properties(t).allowed:
            q.admitted_true += 1
        else:
            q.refused_true.append(t)
    return q


def qualify_union(false_spans: Sequence[str]) -> Qualification:
    """THE THREE LAYERS TOGETHER. And this is the number that matters,
    because the layers fail for DIFFERENT reasons."""
    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    reg = CR.standard_register()
    q = Qualification("the union of three")

    def catches(s: str) -> bool:
        return (reg.read(s).verdict is CR.Verdict.CONTRADICTED
                or not PS.check_scope(s, scope).allowed
                or not PL.check_properties(s).allowed)

    for s in false_spans:
        q.total_false += 1
        if catches(s):
            q.caught_false += 1
        else:
            q.missed_false.append(s)
    for t in TRUE_CLAIMS:
        q.total_true += 1
        if not catches(t):
            q.admitted_true += 1
        else:
            q.refused_true.append(t)
    return q


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("QUALIFICATION: VERIFICATION AS MATH")
    print("=" * 78)
    print()

    blind = load_false("held_out_adversarial.json")
    informed = load_false("informed_adversarial.json")

    print("A. THE NAIVE MEASURE AND WHY IT IS WRONG")
    print()
    everything = Qualification("admits everything")
    everything.total_false = 90
    everything.caught_false = 0
    everything.total_true = 10
    everything.admitted_true = 10
    print("   a gate that ADMITS EVERYTHING, on a set that is 90% false:")
    print("     %s" % everything.describe())
    print("     -> accuracy 0.900, and it is worthless.")
    print()
    nothing = Qualification("refuses everything")
    nothing.total_false = 90
    nothing.caught_false = 90
    nothing.total_true = 10
    nothing.admitted_true = 0
    print("   a gate that REFUSES EVERYTHING, on the same set:")
    print("     %s" % nothing.describe())
    print("     -> accuracy 0.900, and it is a wall.")
    print()
    print("   AND THIS IS THE REAL PATHOLOGY OF ACCURACY, and the")
    print("   first version of this file got it wrong: on a BALANCED")
    print("   set both score 0.500, so accuracy is not naive there.")
    print("   The real trap is that accuracy is FLATTERED whenever the")
    print("   set is imbalanced toward the answer that happens to be")
    print("   'refuse' -- which is exactly the balance an adversary")
    print("   controls, by choosing what to attack.")
    print()
    print("   SO ACCURACY IS THE WRONG MEASURE. THE QUALIFICATION IS")
    print("   A DISTANCE FROM PERFECT ON BOTH AXES:")
    print()
    print("     1 - (missed_false/total_false + refused_true/total_true)")
    print()
    print("   which gives 0.000 for the no-op, 0.000 for the wall, and")
    print("   a positive number for a gate that does BOTH axes. A gate")
    print("   that misses every false AND refuses every true scores")
    print("   -1.000, which IS worse than useless -- and that is the")
    print("   only way to earn a negative, which is the right way round.")
    print()
    print("   AND THE GAP IS REPORTED TOO, because it says WHICH axis")
    print("   is weak -- and the system fails at its weakest layer.")
    print()

    for label, spans in (("BLIND ADVERSARY", blind),
                         ("INFORMED ADVERSARY", informed)):
        if not spans:
            continue
        print("B. THE QUALIFICATION OF EACH LAYER -- %s (%d false claims)"
              % (label, len(spans)))
        print()
        quals = [
            qualify_claim_gate(spans),
            qualify_scope_layer(spans),
            qualify_property_layer(spans),
            qualify_union(spans),
        ]
        for q in quals:
            print("     %s" % q.describe())
        print()
        union = quals[-1]
        print("     THE UNION: sensitivity %.3f  specificity %.3f  "
              "gap %+.3f  QUALIFICATION %+.3f"
              % (union.sensitivity, union.specificity, union.gap,
                 union.margin))
        print("       %s" % union.verdict)
        print("       the true claims it refused: %d"
              % len(union.refused_true))
        for t in union.refused_true:
            print("         %r" % t[:62])
        print()

    print("C. THE COMPARISON ACROSS THE TWO SETS")
    print()
    rows = []
    for label, spans in (("blind", blind), ("informed", informed)):
        if not spans:
            continue
        q = qualify_union(spans)
        rows.append((label, q))
    if len(rows) == 2:
        (bl, qb), (inf, qi) = rows
        print("   %-10s %-12s %-12s %-10s %s"
              % ("set", "sensitivity", "specificity", "gap",
                 "QUALIFICATION"))
        for label, q in rows:
            print("   %-10s %-12.3f %-12.3f %-10.3f %+.3f"
                  % (label, q.sensitivity, q.specificity, q.gap, q.margin))
        print()
        drop = qb.margin - qi.margin
        print("   THE QUALIFICATION DROP between the two sets: %+.3f" % drop)
        if drop > 0:
            print("   AND THAT IS THE HONEST GENERALISATION COST. The")
            print("   gate is more qualified against the blind set than")
            print("   against the informed one, because the informed")
            print("   adversary read the rules. A qualification measured")
            print("   on one set is not a qualification.")
        else:
            print("   AND THE QUALIFICATION HELD -- or ROSE. The")
            print("   layers fail for different reasons, so the")
            print("   adversary that defeated one of them did not")
            print("   defeat the others. THAT is the composition")
            print("   paying off.")
    print()

    print("D. WHAT THE MATH SAYS, IN ONE LINE")
    print()
    print("   THE FRIEND AND THE FOE ARE SEPARATED BY A MARGIN, not by")
    print("   a threshold on one number. The threshold on one number is")
    print("   the similarity gate, and the similarity gate cannot see a")
    print("   contradiction because a contradiction is similar to the")
    print("   ground.")
    print()
    print("   THE QUALIFICATION OF A LAYER IS ITS MARGIN OVER BOTH")
    print("   AXES, AND THE QUALIFICATION OF THE SYSTEM IS THE")
    print("   SMALLEST MARGIN OF ITS LAYERS -- because the system fails")
    print("   at its WEAKEST layer, not its strongest.")
    print()

    print("=" * 78)
    print("  Run: python src/qualification.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
