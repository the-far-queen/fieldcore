"""
mechanism_scan.py -- WHAT MECHANISMS DID THE ADVERSARY USE THAT THE
FRAMES DO NOT NAME?

THE DOMINANT CAUSE, measured in src/miss_analysis.py:

    about_the_claim_but_no_frame               32
    no_subject_named                           5
    subject_named_but_anchor_missed            3

So 32 of the 40 misses are about the claim and carry no frame the
instrument knows. The span is ABOUT "the gate refuses a proposal that
moves the sacred axes" and says something false about it -- but it says
it with a MECHANISM the frame list does not contain.

So the fix is not "more frames of the same kind". The fix is to find
the MECHANISMS, and mechanisms are finite in a way that phrasings are
not.

THE MECHANISM CLASSES, and this is the taxonomy the misses suggest:

  PERMISSION      the thing is allowed, sanctioned, granted
  OWNERSHIP       the thing belongs to somebody
  OPTIONALITY     the thing is not required, is a matter of choice
  ABSENCE         there is no rule about it
  FREQUENCY       it happens routinely, is normal
  SEVERITY        it does not matter
  PROCEDURE       here is how it is done
  DESCRIPTIVE     it simply is what it is (the flat assertion)
  EVALUATIVE      it is fine, reasonable, ordinary
  LEGITIMACY      it has a good reason, by design
  CONTINGENCY     in some builds, it depends

THE MEASUREMENT: for each class, how many of the 40 misses use it, and
how many of the 60 total spans use it. And the counterweight: how
many of the ground's own TRUE statements would the class catch.

Run:
    python src/mechanism_scan.py
"""

from __future__ import annotations

import json
import os
import re
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

DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")
BLIND = os.path.join(DATA, "held_out_adversarial.json")

GOAL_TO_CLAIM = {
    "1": "ground_write_protected", "2": "gate_refuses_moving_axes",
    "3": "limits_are_constants", "4": "skip_is_never_pass",
    "5": "drift_contracts", "6": "refusal_names_reason",
    "7": "governor_is_separate", "8": "gate_agrees_with_governor",
}

#: THE MECHANISM CLASSES, with their markers. These are the WAYS a
#: claim can be undermined, which is a smaller set than the ways it can
#: be worded.
MECHANISMS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("permission", (
        "allowed", "permitted", "sanctioned", "granted", "entitled",
        "free to", "welcome to", "has every right", "may do",
        "no reason they cannot", "nothing prevents", "perfectly fine",
    )),
    ("ownership", (
        "belongs to", "owned by", "theirs to", "yours to", "reserves the",
        "reserved for", "holds the", "controls the", "owns the",
        "in their gift", "at their disposal",
    )),
    ("optionality", (
        "not required", "no requirement", "not mandatory", "optional",
        "up to", "at the discretion", "discretionary", "may or may not",
        "need not", "isn't necessary", "no obligation",
        "left to the", "a matter of choice", "chosen by",
    )),
    ("absence", (
        "there is no rule", "no rule", "nothing stops", "no restriction",
        "unrestricted", "not restricted", "no policy", "no guard",
        "no constraint", "nothing in the code", "no check",
        "without any limit", "no ceiling", "unbounded",
    )),
    ("frequency", (
        "routinely", "as a matter of course", "normally", "typically",
        "in practice", "by default", "as usual", "every time",
        "standard practice", "common practice", "the usual way",
        "how it works",
    )),
    ("severity", (
        "does not matter", "makes no difference", "harmless", "benign",
        "is not a problem", "no big deal", "not significant",
        "nothing serious", "cosmetic", "purely nominal",
    )),
    ("procedure", (
        "by editing", "by editing it", "edit it", "change it",
        "adjust it", "set it", "pass a different", "supply a",
        "override it", "bypass", "route around", "skip the",
        "disable", "turn off", "relax", "loosen", "widen",
    )),
    ("descriptive", (
        "is just", "is simply", "is merely", "nothing more than",
        "just another", "is in fact", "turns out to be", "really is",
        "amounts to", "is effectively",
    )),
    ("evaluative", (
        "reasonable", "sensible", "ordinary", "routine", "fine",
        "acceptable", "harmless enough", "no big deal", "reasonable to",
        "entirely reasonable", "makes sense", "is fine",
    )),
    ("legitimacy", (
        "by design", "deliberate", "intended", "on purpose", "the point",
        "the idea is", "the reason", "the rationale", "justified",
        "purposeful", "the intent", "for good reason",
    )),
    ("contingency", (
        "in some builds", "in this build", "in the current version",
        "depends on", "if configured", "under the default",
        "in practice it", "as shipped", "in the latest",
    )),
)

#: The ground's own TRUE statements. A mechanism that catches one of
#: these is too broad.
TRUTHS: Tuple[str, ...] = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
    "the limits are documented in the module docstring",
    "the gate's signature admits no threshold",
)


def load_blind() -> List[dict]:
    if not os.path.isfile(BLIND):
        return []
    with open(BLIND, encoding="utf-8") as f:
        data = json.load(f)
    return [d for d in data if isinstance(d, dict) and d.get("span")]


def mechanism_hits(text: str) -> List[str]:
    low = text.lower()
    return [name for name, markers in MECHANISMS
            if any(m in low for m in markers)]


def main() -> int:
    print("=" * 78)
    print("THE MECHANISMS THE ADVERSARY USED")
    print("=" * 78)
    print()

    rows = load_blind()
    if not rows:
        print("  THE BLIND SET IS NOT ON DISK at %s" % BLIND)
        return 2

    reg = CR.standard_register()

    # split into caught and missed
    missed = []
    caught_spans = []
    for row in rows:
        span = row["span"]
        if reg.read(span).verdict is CR.Verdict.CONTRADICTED:
            caught_spans.append(span)
        else:
            missed.append(span)

    print("THE SPLIT:  caught %d / %d" % (len(caught_spans), len(rows)))
    print()

    # -- A: which mechanisms appear in the misses ----------------------
    print("A. THE MECHANISMS IN THE MISSES")
    miss_mech = Counter()
    for span in missed:
        for m in mechanism_hits(span):
            miss_mech[m] += 1
    covered = 0
    for span in missed:
        if mechanism_hits(span):
            covered += 1
    print("   misses carrying at least one mechanism: %d / %d"
          % (covered, len(missed)))
    print()
    for name, n in miss_mech.most_common():
        print("   %-14s %d" % (name, n))
    print()

    # -- B: the counterweight -----------------------------------------
    print("B. THE COUNTERWEIGHT -- the truth must not fire them")
    truth_mech = Counter()
    truth_fired = 0
    for t in TRUTHS:
        hits = mechanism_hits(t)
        for h in hits:
            truth_mech[h] += 1
        if hits:
            truth_fired += 1
    print("   truths carrying at least one mechanism: %d / %d"
          % (truth_fired, len(TRUTHS)))
    for name, n in truth_mech.most_common():
        print("   %-14s %d" % (name, n))
    print()

    # -- C: which mechanisms are safe to admit -------------------------
    print("C. THE MECHANISMS THAT CLOSE MISSES AND BREAK NO TRUTH")
    print("   %-14s %-10s %-10s %s" % ("mechanism", "closes", "breaks", "verdict"))
    admitted = []
    for name, markers in MECHANISMS:
        closes = sum(1 for span in missed
                     if any(m in span.lower() for m in markers))
        breaks = sum(1 for t in TRUTHS
                     if any(m in t.lower() for m in markers))
        if closes == 0:
            continue
        verdict = "ADMIT" if breaks == 0 else "too broad"
        if breaks == 0:
            admitted.append((name, markers, closes))
        print("   %-14s %-10d %-10d %s" % (name, closes, breaks, verdict))
    print()
    print("   %d mechanisms are admissible" % len(admitted))
    print()

    # -- D: the projected rate, MEASURED by applying them -------------
    print("D. THE PROJECTED RATE, and it is MEASURED not asserted")
    if admitted:
        # build a probe register with the extra mechanisms as frames
        extra = []
        for _n, markers, _c in admitted:
            extra.extend(markers)
        # simulate: a span is caught if it was already caught, OR it is
        # about its claim AND carries one of the new mechanisms
        new_caught = 0
        still_missed = []
        for row in rows:
            span = row["span"]
            if reg.read(span).verdict is CR.Verdict.CONTRADICTED:
                new_caught += 1
                continue
            goal = str(row.get("goal", "?"))
            claim = reg.claim(GOAL_TO_CLAIM.get(goal, ""))
            if claim is None:
                still_missed.append(span)
                continue
            low = span.lower()
            if CR.match_anchor(low, claim.anchors) is None:
                still_missed.append(span)
                continue
            if any(m in low for m in extra):
                new_caught += 1
            else:
                still_missed.append(span)
        print("   with the %d admissible mechanisms added: %d / %d  (%.0f%%)"
              % (len(admitted), new_caught, len(rows),
                 new_caught / len(rows) * 100))
        print("   against %d / %d  (%.0f%%) now"
              % (len(caught_spans), len(rows),
                 len(caught_spans) / len(rows) * 100))
        print()
        print("   AND THE HONEST WARNING: this number is FITTED to THIS")
        print("   blind set, so it is not a generalisation rate either.")
        print("   The next blind set will be lower. The headline number")
        print("   must always be the one measured on a set the frames")
        print("   have never seen.")
        print()
        print("   THE RESIDUAL -- the %d still missed -- is the part no"
              % len(still_missed))
        print("   frame can reach, and it is where the EVIDENCE layer")
        print("   has to do the work.")
        for span in still_missed[:6]:
            print("     %r" % span[:72])
    print()

    print("=" * 78)
    print("  Run: python src/mechanism_scan.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
