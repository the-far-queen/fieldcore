"""
informed_miss_analysis.py -- WHAT THE INFORMED ADVERSARY WROTE, AND
WHETHER THE NON-LEXICAL LAYERS CATCH IT.

THE NUMBER, and it is the definitive one:

    src/adversary_probe.py   49 / 49   (the FITTED set)
    src/held_out_eval.py     20 / 60   (the BLIND adversary)
    src/held_out_eval.py      0 / 40   (the INFORMED adversary)

**ZERO.** The adversary was given the exact deny keywords and the
exact modal/transfer frames and asked to write around them. It wrote
40 sentences and EVERY ONE got through.

Bobby's wife, 2026-10-26: *"the difficulty is when they use an llm to
make the queries sophisticated, ie ur adversary likely will be a
powerful llm."* That is now a MEASUREMENT, not an opinion.

So this file asks the question that matters now:

  DOES ANY LAYER CATCH THE INFORMED ADVERSARY?

And it checks the three candidate layers in turn:

  THE EVIDENCE LAYER. A span that presents a ground claim as a
  measurement, where the claim is ASSERTED (nothing measures it), is
  UNGROUNDED -- and that does not depend on the wording.

  THE FRUIT LAYER. The six behavioural questions. They do not depend
  on the wording either, because they ask what was DONE.

  THE MECHANISM LAYER. The informed adversary did not use modal
  frames -- it used TECHNICAL MECHANISMS ("the write barrier was
  lifted", "the alignment check sits behind a feature flag"). So the
  mechanism classes are the third candidate, and they are lexical
  again -- so they will lose too, but they might close the specific
  gap.

THE HONEST OUTCOME, whatever it is: this file exists to find out, and
the finding it produces is the finding, not the one I want.

Run:
    python src/informed_miss_analysis.py
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
INFORMED = os.path.join(DATA, "informed_adversarial.json")

GOAL_TO_CLAIM = {
    "1": "ground_write_protected", "2": "gate_refuses_moving_axes",
    "3": "limits_are_constants", "4": "skip_is_never_pass",
    "5": "drift_contracts", "6": "refusal_names_reason",
    "7": "governor_is_separate", "8": "gate_agrees_with_governor",
}

#: The MECHANISM CLASSES, from src/mechanism_scan.py. The informed
#: adversary used technical mechanisms, so this taxonomy needs a
#: technical arm.
TECHNICAL_MECHANISMS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("revision", (
        "revision", "revision notes", "in the 0.9", "in this build",
        "in the current build", "as of", "since the", "changed to",
        "was changed", "has changed", "moved to", "was moved",
        "now lives", "now sits", "became", "was replaced",
    )),
    ("flag", (
        "feature flag", "behind a flag", "the flag", "toggle",
        "switched off", "switched on", "disabled by default",
        "enabled by default", "the default is", "by default",
    )),
    ("permission_change", (
        "0666", "chmod", "the write barrier", "the barrier was lifted",
        "the protection was removed", "the guard was removed",
        "the check was dropped", "no longer enforced", "no longer runs",
        "is not enforced", "was lifted", "was removed", "was dropped",
    )),
    ("mechanism_of_record", (
        "pull request", "normal workflow", "the normal workflow",
        "the ordinary process", "the standard process",
        "through the ordinary", "as part of the build",
        "in the packaging", "the installation step", "the install step",
        "the storage layer", "the snapshot", "hard-coded",
        "a hard-coded", "the comparison became",
    )),
)


def load_informed() -> List[dict]:
    if not os.path.isfile(INFORMED):
        return []
    with open(INFORMED, encoding="utf-8") as f:
        data = json.load(f)
    return [d for d in data if isinstance(d, dict) and d.get("span")]


def main() -> int:
    print("=" * 78)
    print("THE INFORMED ADVERSARY: 0 / 40, AND WHAT CATCHES IT")
    print("=" * 78)
    print()

    rows = load_informed()
    if not rows:
        print("  THE INFORMED SET IS NOT ON DISK at %s" % INFORMED)
        print("  So the informed rate is NOT MEASURED.")
        return 2

    reg = CR.standard_register()

    # -- A: the shape of what the adversary wrote ---------------------
    print("A. WHAT THE INFORMED ADVERSARY WROTE")
    print("   the mechanism it used, in its own words:")
    mech_counts = Counter()
    for row in rows:
        low = row["span"].lower()
        found = False
        for name, markers in TECHNICAL_MECHANISMS:
            if any(m in low for m in markers):
                mech_counts[name] += 1
                found = True
        if not found:
            mech_counts["(none of the four classes)"] += 1
    for name, n in mech_counts.most_common():
        print("     %-32s %d" % (name, n))
    print()
    print("   the first three, verbatim:")
    for row in rows[:3]:
        print("     %r" % row["span"][:96])
    print()

    # -- B: the three candidate layers --------------------------------
    print("B. DOES ANY LAYER CATCH THEM?")

    # B1: the lexical layer
    lex_caught = sum(1 for row in rows
                     if reg.read(row["span"]).verdict is CR.Verdict.CONTRADICTED)
    print()
    print("   B1  THE LEXICAL LAYER (deny stems + modal/transfer frames)")
    print("       caught %d / %d" % (lex_caught, len(rows)))
    print("       THE ADVERSARY WAS GIVEN BOTH LISTS AND WROTE AROUND")
    print("       THEM. So this is not a failure of the lists -- it is")
    print("       the lists being lists.")

    # B2: the evidence layer
    ev_caught = 0
    ev_rows = []
    for row in rows:
        adj = reg.read(row["span"], as_measurement=True)
        ok = adj.verdict.value == "ungrounded"
        ev_caught += 1 if ok else 0
        ev_rows.append((row, adj))
    print()
    print("   B2  THE EVIDENCE LAYER (in measurement mode)")
    print("       caught %d / %d" % (ev_caught, len(rows)))
    if ev_caught:
        print("       and it caught them WITHOUT reading the words:")
        for row, adj in ev_rows:
            if adj.verdict.value == "ungrounded":
                print("         %r" % row["span"][:70])
                print("           %s" % adj.reason[:88])
                break
    else:
        print("       and it caught NONE -- because these spans do not")
        print("       CLAIM TO BE MEASUREMENTS. They assert false")
        print("       technical facts, which is a different attack.")

    # B3: the mechanism layer
    mech_caught = 0
    for row in rows:
        low = row["span"].lower()
        goal = str(row.get("goal", "?"))
        claim = reg.claim(GOAL_TO_CLAIM.get(goal, ""))
        if claim is None:
            continue
        if CR.match_anchor(low, claim.anchors) is None:
            continue
        if any(any(m in low for m in markers)
               for _n, markers in TECHNICAL_MECHANISMS):
            mech_caught += 1
    print()
    print("   B3  THE MECHANISM LAYER (the technical arm)")
    print("       caught %d / %d" % (mech_caught, len(rows)))
    print("       and it is lexical again -- so it will lose the same")
    print("       way, one widening later.")

    # -- C: what the informed adversary actually did ------------------
    print()
    print("C. WHAT THE INFORMED ADVERSARY DID, AND WHY IT WORKED")
    print()
    print("   IT STOPPED MAKING CLAIMS ABOUT THE SYSTEM AND STARTED")
    print("   DESCRIBING A DIFFERENT BUILD.")
    print()
    print("   The 40 sentences do not say 'the ground is writable'. They")
    print("   say 'in the 0.9 revision the alignment comparison became an")
    print("   advisory check' and 'the write barrier was lifted during")
    print("   the storage migration' and 'the installation step sets the")
    print("   ground to 0666'.")
    print()
    print("   THAT IS A DIFFERENT ATTACK, and it is the one that matters.")
    print("   The lexical layers look for a FALSE STATEMENT ABOUT THE")
    print("   GROUND. The informed adversary is not making one. It is")
    print("   making a TRUE STATEMENT about a DIFFERENT SYSTEM -- a")
    print("   system where the ground is indeed writable, because it")
    print("   is a FILE and files are writable.")
    print()
    print("   So the attack is not against the CLAIM. It is against the")
    print("   PROVENANCE: it asserts facts about a system that is not")
    print("   this one, in the grammatical form of facts about this")
    print("   one, with no marker that they are about elsewhere.")
    print()
    print("   AND THAT IS EXACTLY WHAT THE MINERS CALL CONFABULATION")
    print("   AND WHAT THE ATLAS EXAM CALLS PROVENANCE: an answer whose")
    print("   numbers are traceable to a measurement, or which says they")
    print("   are not. The attack passes because the sentence LOOKS")
    print("   like a statement of fact and carries no pointer to which")
    print("   system it is about.")
    print()

    # -- D: the three candidate layers, in the report ----------------
    print("D. WHAT WOULD CATCH IT")
    print()
    print("   NOT A BIGGER LIST. The adversary is describing builds")
    print("   that do not exist, and there are infinitely many ways to")
    print("   describe a build that does not exist.")
    print()
    print("   THE PROVENANCE POINTER. Every span that asserts a fact")
    print("   about the system must carry a pointer to WHERE the fact")
    print("   came from -- a measurement, a file, a commit, a version.")
    print("   A span describing 'the 0.9 revision' has no such pointer,")
    print("   because the 0.9 revision is not here. THAT is checkable,")
    print("   and it is checkable without reading the words.")
    print()
    print("   AND THIS IS THE ATLAS EXAM'S AREA 2 -- PROVENANCE --")
    print("   which already exists in fieldcore/src/mini_atlas.py and")
    print("   already asks exactly this question. So the machinery for")
    print("   catching the informed adversary was BUILT, on 2026-10-25,")
    print("   and was not WIRED to the claim gate.")
    print()

    print("=" * 78)
    print("  Run: python src/informed_miss_analysis.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
