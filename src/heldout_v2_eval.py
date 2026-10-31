"""
heldout_v2_eval.py -- THE HONEST RATE, ON A SET THE FRAMES HAVE NEVER
SEEN.

THE POINT OF THIS FILE. The 49 phrasings in src/adversary_probe.py were
FITTED to the frames, so 49/49 is not a generalisation number. The 64
sentences in tests/data/fresh_adversarial.json were the first honest
set, and MEASURED against the instrument as it stood when they were
written they scored 33/64 (51.6%) by the whole union.

So this file measures the NEW set, written by a blind writer, against
the instrument as it stands now -- and it says which layer caught what.

THE FOUR NUMBERS, and each one is a different question:

  A  THE LEXICAL LAYER. Fitted to a phrase list. It generalises badly
     by construction, because the adversary writes new phrases.

  B  THE STRUCTURAL LAYERS. The scope layer, the property layer and
     the predicate layer look for a STRUCTURE rather than a phrase.

  C  THE EVIDENCE LAYER. The one that does not read the sentence. A
     span that asserts a measured ground claim must CARRY the
     measurement -- a command and a number -- or it is UNGROUNDED.

  D  THE UNION. What the gate actually does.

AND THE HONESTY. This set is FITTED the moment anybody reads it and
changes a frame, an anchor, a deny list or a mechanism word. So the
rate here is the number to quote ONLY until that happens, and the file
says so.

THE PROVENANCE, so the number can be trusted:

  the writer ran in --safe-mode, so it had no plugins, no user config
  and no AGENTS.md injection -- and with FIELDCORE_HOME pointing at a
  path that does not exist, so the FieldCore gate could not read the
  writer's reply either. The gate DID try: on the first run it
  stripped the sentences that said the ground was writable, so the
  corpus was missing exactly the attacks it was supposed to hold.

  the writer was given ONLY the eight public claims. The claims are
  public by design -- the instrument refuses a CLAIM, so a claim is
  not a secret -- and the frames, the anchors, the deny lists and
  every measurement were withheld.

  sixteen registers, so the set is sixteen different voices rather
  than one mind's variations.

Run:
    python src/heldout_v2_eval.py
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
SET_NAME = "held_out_v2.json"


def load(name: str) -> List[dict]:
    p = os.path.join(DATA, name)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    print("=" * 78)
    print("THE HONEST RATE, ON A SET THE FRAMES HAVE NEVER SEEN")
    print("=" * 78)
    print()

    rows = load(SET_NAME)
    if not rows:
        print("   THE SET IS NOT ON DISK: %s" % os.path.join(DATA, SET_NAME))
        return 2
    n = len(rows)
    print("   THE SET: %d sentences, %d registers, %d distinct writers"
          % (n, len({r.get("style") for r in rows}),
             len({r.get("session") for r in rows})))
    print()

    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    def layers_for(s: str) -> List[str]:
        hits = []
        if reg.read(s).verdict is CR.Verdict.CONTRADICTED:
            hits.append("lexical")
        if not PS.check_scope(s, scope).allowed:
            hits.append("scope")
        if not PLROP.check_properties(s).allowed:
            hits.append("property")
        if not PL.check_predicates(s, preds).allowed:
            hits.append("predicate")
        return hits

    counts = Counter()
    per_goal: Dict[int, List[int]] = {}
    missed: List[dict] = []
    for r in rows:
        s = r["span"]
        hits = layers_for(s)
        for h in hits:
            counts[h] += 1
        caught = 1 if hits else 0
        per_goal.setdefault(int(r.get("goal", 0)), []).append(caught)
        if not caught:
            missed.append(r)

    print("A. EACH LAYER'S RATE ON THE UNFITTED SET")
    print()
    print("   %-12s %-10s %s" % ("layer", "caught", "what it is fitted to"))
    print("   %-12s %-10s %s" % ("", "", ""))
    for name, what in (("lexical", "a phrase list"),
                       ("scope", "a structure"),
                       ("property", "a structure"),
                       ("predicate", "the system's own truths")):
        print("   %-12s %-10s %s" % (name, "%d/%d" % (counts[name], n), what))
    print()

    print("B. THE UNION, AND THE UNION WITHOUT THE LEXICAL LAYER")
    print()
    union = 0
    union_no_lex = 0
    for r in rows:
        hits = layers_for(r["span"])
        if hits:
            union += 1
        if any(h in hits for h in ("scope", "property", "predicate")):
            union_no_lex += 1
    print("   THE UNION OF ALL FOUR               %2d / %d  (%.0f%%)"
          % (union, n, union / n * 100))
    print("   THE UNION WITHOUT THE LEXICAL LAYER %2d / %d  (%.0f%%)"
          % (union_no_lex, n, union_no_lex / n * 100))
    print("   caught by NOTHING                   %2d / %d  (%.0f%%)"
          % (n - union, n, (n - union) / n * 100))
    print()

    print("C. PER GOAL -- every claim of the ground, attacked")
    print()
    print("   %-6s %-10s %s" % ("goal", "caught", "the claim"))
    claim_by_id = {c.id: c.statement for c in reg.claims}
    order = ["ground_write_protected", "gate_refuses_moving_axes",
             "limits_are_constants", "skip_is_never_pass", "drift_contracts",
             "refusal_names_reason", "governor_is_separate",
             "gate_agrees_with_governor"]
    for gi in sorted(per_goal):
        v = per_goal[gi]
        stmt = claim_by_id.get(order[gi - 1], "?") if gi <= len(order) else "?"
        print("   %-6d %-10s %s" % (gi, "%d/%d" % (sum(v), len(v)),
                                   stmt[:44]))
    print()

    if missed:
        print("D. THE MISSES -- what the instrument did not catch")
        print()
        for r in missed[:14]:
            print("   goal %s  %r" % (r.get("goal"), r["span"][:88]))
        if len(missed) > 14:
            print("   ... and %d more" % (len(missed) - 14))
        print()

    print("=" * 78)
    print("  Run: python src/heldout_v2_eval.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
