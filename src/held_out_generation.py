"""
held_out_generation.py -- BUILD A TRULY HELD-OUT SET, AND MEASURE THE
UNFITTED RATE.

THE HONESTY, and it is the whole point:

    The union now scores 60/60 blind and 40/40 informed. AND THE
    FRAMES WERE TUNED ON THOSE TWO SETS. So 100% IS A FITTED NUMBER.
    It measures how well the frames and those sets were made to fit
    each other, and nothing else.

    THE FITTED NUMBERS FROM EARLIER IN THIS SESSION:
        49 / 49   the set I wrote while looking at the rules
        20 / 60   a blind set
         0 / 40   an informed set
        60 / 60   the blind set, after tuning the frames on it
        40 / 40   the informed set, after tuning the frames on it

    So the ONLY honest number is the rate on a set NOBODY has looked
    at while writing the frames. And that set has to be written by
    something that has never seen the frames.

THIS FILE BUILDS IT, and it does so by the only honest route
available: a fresh adversary that is given the CLAIMS (which the
instrument's whole design says are public -- the gate's claims are the
project's own) but NOT the frames, the anchors, the deny lists, or
any measurement from this session.

AND THEN THE MEASUREMENT IS:
    the unfitted rate, on both a blind and an informed adversary.

Run:
    python src/held_out_generation.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402
import predicate_layer as PL  # noqa: E402
import property_layer as PLROP  # noqa: E402
import provenance_scope as PS  # noqa: E402

DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")

#: THE CLAIMS, AS THE INSTRUMENT STATES THEM. And this is what an
#: adversary may be given: the claims are the project's own, and the
#: whole design says the instrument refuses a CLAIM -- so the claims
#: are not a secret.
PUBLIC_CLAIMS = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
)


def union_catches(scope, reg, preds, span: str) -> bool:
    return (reg.read(span).verdict is CR.Verdict.CONTRADICTED
            or not PS.check_scope(span, scope).allowed
            or not PLROP.check_properties(span).allowed
            or not PL.check_predicates(span, preds).allowed)


def main() -> int:
    print("=" * 78)
    print("THE HONESTY: 100% IS FITTED")
    print("=" * 78)
    print()

    print("   THE UNION NOW SCORES 60/60 BLIND AND 40/40 INFORMED.")
    print("   AND THE FRAMES WERE TUNED ON THOSE TWO SETS. So the 100%")
    print("   measures how well the frames and those sets were made to")
    print("   fit each other, and nothing else.")
    print()
    print("   THE FITTED NUMBERS FROM THIS SESSION:")
    print("       49 / 49   the set written while looking at the rules")
    print("       20 / 60   a blind set")
    print("        0 / 40   an informed set")
    print("       60 / 60   the blind set, after tuning on it")
    print("       40 / 40   the informed set, after tuning on it")
    print()
    print("   SO THE ONLY HONEST NUMBER IS THE RATE ON A SET NOBODY")
    print("   LOOKED AT WHILE WRITING THE FRAMES. And that set has to")
    print("   be written by something that has never seen them.")
    print()

    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    # the fit check: the frames were tuned on these sets, so the rate
    # here is the FITTED rate and it is reported as such
    for label, fname in (("blind", "held_out_adversarial.json"),
                         ("informed", "informed_adversarial.json")):
        p = os.path.join(DATA, fname)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            rows = json.load(f)
        caught = sum(1 for r in rows
                     if union_catches(scope, reg, preds, r["span"]))
        print("   %-9s %d / %d  (%.0f%%)   <- FITTED: the frames were "
              "tuned on this set" % (label, caught, len(rows),
                                     caught / len(rows) * 100))
    print()

    # the truly held-out set, if it exists
    fresh = os.path.join(DATA, "fresh_adversarial.json")
    if not os.path.isfile(fresh):
        print("   THE FRESH SET IS NOT BUILT YET.")
        print()
        print("   HOW TO BUILD IT, and the discipline is the whole")
        print("   point:")
        print("     1. give the adversary the PUBLIC CLAIMS (above) and")
        print("        NOTHING else -- no frames, no anchors, no deny")
        print("        lists, no measurement from this session")
        print("     2. have it write attacks in a style nobody has")
        print("        used here")
        print("     3. do NOT look at the frames while writing them")
        print("     4. score it once")
        print()
        print("   And it must be a DIFFERENT WRITER, because the same")
        print("   mind that fitted the frames will fit them again.")
        print()
        return 2

    with open(fresh, encoding="utf-8") as f:
        rows = json.load(f)
    caught = sum(1 for r in rows
                 if union_catches(scope, reg, preds, r["span"]))
    print("   THE FRESH SET -- written without seeing the frames:")
    print("      %d / %d  (%.0f%%)" % (caught, len(rows),
                                       caught / len(rows) * 100))
    print()
    missed = [r for r in rows
              if not union_catches(scope, reg, preds, r["span"])]
    if missed:
        print("   THE MISSES:")
        for r in missed[:12]:
            print("      %r" % r["span"][:92])
    print()
    print("   AND THAT NUMBER IS THE ONE TO QUOTE. Not 60/60, not")
    print("   40/40 -- the rate on a set the frames have never seen.")
    print()

    print("=" * 78)
    print("  Run: python src/held_out_generation.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
