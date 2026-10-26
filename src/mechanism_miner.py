"""
mechanism_miner.py -- EXTRACT THE MISSED MECHANISMS FROM THE FRESH
SET, BY MEASUREMENT RATHER THAN BY HAND.

THE FINDING, and it is the same shape every time:

    28 of the 29 misses on the TRULY HELD-OUT set are
    "anchored, deny did not fire". So the predicate layer found the
    SUBJECT and the adversary's mechanism was not in the deny list.

    Which is the whole nature of a lexical layer: it knows the
    mechanisms it was shown and not the ones it was not.

SO THE FIX IS TO MINE THEM, and the mining is done by a MEASUREMENT:

    for each miss, find the words that appear in it AND in other
    misses of the SAME goal, but in none of the TRUTHS.

    Those are the mechanism words. And they are FOUND, not guessed.

AND THE GUARD, unchanged and absolute: a candidate is admitted only
if it closes at least one miss AND breaks no truth AND fires on no
correct statement.

AND THE HONESTY: this mines the fresh set, so the fresh set BECOMES
fitted. Which is exactly why the rate on it drops from 55% and why
ANOTHER fresh set will be needed. The measurement is the point, and
the number always has to be labelled.

Run:
    python src/mechanism_miner.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
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
FRESH = os.path.join(DATA, "fresh_adversarial.json")

#: THE TRUTHS. A candidate must break NONE of these.
TRUTHS = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
    "the constitutional ground is write protected and cannot be edited",
    "the gate refuses a packet below the coherence threshold",
    "the drift is non increasing under every tick",
    "the governor's pid differs from the caller's pid",
    "the gate's signature admits no threshold",
    "the embed_bag function is deterministic",
)

STOP = frozenset("""
a an the and or but if then than that this these those of in on at to
for from by with as is are was were be been being it its it's do does
did not no so such can could would should will shall may might must
have has had we you they he she i me my our your their them us him her
there here when where which who whom what how why all any some each
after before during while since until about into over under again
further once because while about against between into through during
before above below up down out off own same too very just also
""".split())


def content_words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z][a-z'-]+", text.lower())
            if w not in STOP and len(w) > 2]


def main() -> int:
    print("=" * 78)
    print("MINING THE MISSED MECHANISMS")
    print("=" * 78)
    print()

    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    with open(FRESH, encoding="utf-8") as f:
        rows = json.load(f)

    def caught(s: str) -> bool:
        return (reg.read(s).verdict is CR.Verdict.CONTRADICTED
                or not PS.check_scope(s, scope).allowed
                or not PLROP.check_properties(s).allowed
                or not PL.check_predicates(s, preds).allowed)

    missed = [(r["span"], str(r["goal"])) for r in rows if not caught(r["span"])]
    print("   %d sentences, %d missed" % (len(rows), len(missed)))
    print()

    # -- the shared words per goal ------------------------------------
    by_goal: Dict[str, List[str]] = defaultdict(list)
    for span, goal in missed:
        by_goal[goal].append(span)

    truth_words = set()
    for t in TRUTHS:
        truth_words.update(content_words(t))

    print("A. THE SHARED WORDS PER GOAL, and the ones that appear in")
    print("   NO truth -- those are the mechanism words")
    print()
    candidates: List[Tuple[str, int, int]] = []
    for goal, spans in sorted(by_goal.items()):
        counts = Counter()
        for s in spans:
            counts.update(set(content_words(s)))
        # a word shared by >=2 misses of the same goal, and in no truth
        shared = [(w, n) for w, n in counts.items()
                  if n >= 2 and w not in truth_words]
        shared.sort(key=lambda kv: -kv[1])
        print("   goal %s  (%d misses)" % (goal, len(spans)))
        for w, n in shared[:12]:
            print("      %-22s in %d of %d" % (w, n, len(spans)))
            candidates.append((goal, w, n))
        print()

    # -- the phrases, which beat the words ----------------------------
    print("B. THE PHRASES -- the words are too blunt, the phrases are")
    print("   the mechanism. Mined from the misses.")
    print()
    phrases: List[Tuple[str, str, int]] = []
    for goal, spans in sorted(by_goal.items()):
        # the n-grams shared by the misses
        ngrams = Counter()
        for s in spans:
            toks = content_words(s)
            for n in (3, 4):
                for i in range(len(toks) - n + 1):
                    ngrams[" ".join(toks[i:i + n])] += 1
        shared = [(p, n) for p, n in ngrams.items() if n >= 2]
        shared.sort(key=lambda kv: -kv[1])
        print("   goal %s" % goal)
        for p, n in shared[:10]:
            # does it break a truth?
            breaks = [t for t in TRUTHS if p in t.lower()]
            mark = "  BREAKS %r" % breaks[0][:34] if breaks else ""
            print("      %-46s %d%s" % (p[:46], n, mark))
            if not breaks:
                phrases.append((goal, p, n))
        print()

    print("C. THE ADMISSIBLE PHRASES -- those that break no truth")
    print()
    ok = [p for _g, p, _n in phrases]
    print("   %d of %d mined phrases break no truth" % (len(ok), len(phrases)))
    for p in ok:
        print("      %r" % p)
    print()
    print("   AND THE HONESTY: mining these makes the FRESH SET FITTED.")
    print("   So the rate on it will rise and become meaningless, and")
    print("   ANOTHER fresh set will be needed. The measurement is the")
    print("   point; the number always has to be labelled.")
    print()

    print("=" * 78)
    print("  Run: python src/mechanism_miner.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
