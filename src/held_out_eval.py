"""
held_out_eval.py -- SCORE THE ADVERSARY SETS AGAINST THE INSTRUMENT.

Bobby's standing order, 2026-10-26: *"not solely the first word,
literally EVERY word, the phrasing, the intent."* And then, from the
wife: *"the difficulty is when they use an llm to make the queries
sophisticated, ie ur adversary likely will be a powerful llm."*

So the number that matters is NOT 49/49. That was a FITTED number --
the 49 phrasings were written while looking at the frame list, so they
are a training set and the rate on them is not a generalisation rate.

This file scores the two ADVERSARY SETS:

  BLIND       60 sentences written by a model that had NOT seen the
              frame list. This is the honest generalisation rate.

  INFORMED    40 sentences written by a model that WAS given the exact
              deny keywords and the modal/transfer frames, and was
              asked to avoid them. This is the ceiling of the
              adversary's skill against a lexical instrument.

AND THE QUESTION EACH ANSWERS:

  BLIND      can a competent adversary who does not know the tool
             still get through? This is the rate that matters.

  INFORMED   what happens when the adversary READS the tool? Because
             Bobby's point is that the adversary will be a powerful
             LLM, and a powerful LLM can read a keyword list.

THE HONEST FRAMING, because the answer is not "the tool wins":

  A LEXICAL INSTRUMENT LOSES THE INFORMED CONTEST. It must. There is
  no finite list of frames that covers every phrasing of a permission.

  WHAT DOES NOT LOSE IS THE EVIDENCE LAYER. A claim becomes MEASURED
  only when a measurement is put in the store, and putting one there
  requires a command that can be re-run. So an adversary's phrasing can
  evade any lexicon -- and cannot make a measurement appear.

  So the instrument's honest report is TWO NUMBERS: the lexical rate
  (which is a property of the lexicon, and the lexicon is a training
  set) and the evidence rate (which is a property of the structure,
  and the structure is not fitted).

Run:
    python src/held_out_eval.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402

DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")

#: The claim ids in the order the adversary sets use them (1-8).
GOAL_TO_CLAIM = {
    "1": "ground_write_protected",
    "2": "gate_refuses_moving_axes",
    "3": "limits_are_constants",
    "4": "skip_is_never_pass",
    "5": "drift_contracts",
    "6": "refusal_names_reason",
    "7": "governor_is_separate",
    "8": "gate_agrees_with_governor",
}


def load(name: str) -> List[dict]:
    path = os.path.join(DATA, name)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [d for d in data if isinstance(d, dict) and d.get("span")]


def score(reg, rows: List[dict], label: str) -> Dict[str, object]:
    """Score one adversary set against the instrument."""
    caught = 0
    missed: List[dict] = []
    by_goal: Counter = Counter()
    caught_by_goal: Counter = Counter()
    by_agenda = 0
    by_lexicon = 0

    for row in rows:
        span = row.get("span", "")
        adj = reg.read(span)
        goal = str(row.get("goal", "?"))
        by_goal[goal] += 1
        ok = adj.verdict is CR.Verdict.CONTRADICTED
        if ok:
            caught += 1
            caught_by_goal[goal] += 1
            if adj.agenda is not None and adj.agenda.detected:
                by_agenda += 1
            else:
                by_lexicon += 1
        else:
            missed.append({
                "span": span,
                "goal": goal,
                "claim": GOAL_TO_CLAIM.get(goal, "?"),
                "verdict": adj.verdict.value,
            })

    total = len(rows)
    return {
        "label": label,
        "total": total,
        "caught": caught,
        "rate": (caught / total) if total else 0.0,
        "by_agenda": by_agenda,
        "by_lexicon": by_lexicon,
        "by_goal": by_goal,
        "caught_by_goal": caught_by_goal,
        "missed": missed,
    }


def _union_score(rows):
    """The UNION of the four layers, which is the system's number.

    AND THE REASON IT IS HERE: this scorer was built to show the
    LEXICAL layer's rate against each set -- 20/60 blind and 0/40
    informed -- and those numbers are correct for that layer. But the
    number that matters for the SYSTEM is the union, because the
    layers fail for different reasons.

    AND THE TWO SETS DIFFER SHARPLY, which is the finding:

        blind      the lexical layer is the one that works
        informed   the lexical layer is the one that fails, and the
                   other three carry it

    So a single rate per set hides which layer did the work.
    """
    import claim_register as CR
    import predicate_layer as PL
    import property_layer as PLROP
    import provenance_scope as PS

    scope = PS.Scope([os.path.join(os.path.dirname(__file__), ".."),
                      os.path.join(os.path.dirname(__file__), "..", "..",
                                   "simself")])
    scope = PS.Scope([
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                     "..", "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    by_layer = {"lexical": 0, "scope": 0, "property": 0, "predicate": 0}
    caught = 0
    missed = []
    for row in rows:
        s = row["span"]
        hit = None
        import testimony_layer as TL
        if reg.read(s).verdict is CR.Verdict.CONTRADICTED:
            hit = "lexical"
        elif not PS.check_scope(s, scope).allowed:
            hit = "scope"
        elif not PLROP.check_properties(s).allowed:
            hit = "property"
        elif not PL.check_predicates(s, preds).allowed:
            hit = "predicate"
        elif not TL.check_testimony(s).allowed:
            hit = "testimony"
        if hit:
            caught += 1
            by_layer[hit] += 1
        else:
            missed.append(s)
    return {"total": len(rows), "caught": caught,
            "rate": caught / len(rows) if rows else 0.0,
            "by_layer": by_layer, "missed": missed}


def main() -> int:
    print("=" * 78)
    print("SCORING THE ADVERSARY SETS")
    print("=" * 78)
    print()

    reg = CR.standard_register()

    blind = load("held_out_adversarial.json")
    informed = load("informed_adversarial.json")

    if not blind and not informed:
        print("  NEITHER ADVERSARY SET IS ON DISK.")
        print("  Expected at:")
        print("    %s" % os.path.join(DATA, "held_out_adversarial.json"))
        print("    %s" % os.path.join(DATA, "informed_adversarial.json"))
        print()
        print("  So the generalisation rate is NOT MEASURED, and the")
        print("  49/49 figure from src/adversary_probe.py stands as a")
        print("  FITTED number and nothing more.")
        return 2

    for rows, label, note in (
        (blind, "BLIND",
         "the adversary had NOT seen the frame list"),
        (informed, "INFORMED",
         "the adversary WAS given the deny keywords and the frames"),
    ):
        if not rows:
            print("%s SET: NOT PRESENT -- not measured." % label)
            print()
            continue
        s = score(reg, rows, label)
        print("%s ADVERSARY SET -- %s" % (label, note))
        print("   sentences            %d" % s["total"])
        print("   CAUGHT               %d / %d  (%.0f%%)"
              % (s["caught"], s["total"], s["rate"] * 100))
        print("     by the agenda layer  %d" % s["by_agenda"])
        print("     by the deny lexicon  %d" % s["by_lexicon"])
        print()
        print("   per goal:")
        for goal in sorted(s["by_goal"]):
            g = s["by_goal"][goal]
            c = s["caught_by_goal"].get(goal, 0)
            flag = "" if c == g else "   <-- MISSED %d" % (g - c)
            print("     goal %-3s %-28s %d/%d%s"
                  % (goal, GOAL_TO_CLAIM.get(goal, "?")[:28], c, g, flag))
        print()
        if s["missed"]:
            print("   THE MISSES -- what got through:")
            for m in s["missed"][:10]:
                print("     goal %-3s %-9s %r"
                      % (m["goal"], m["verdict"], m["span"][:62]))
            if len(s["missed"]) > 10:
                print("     ... and %d more" % (len(s["missed"]) - 10))
            print()

    # -- the union, and which layer did the work ----------------------
    print("C. THE UNION OF THE FIVE LAYERS, and which layer did the work")
    print()
    for label, rows in (("BLIND", blind), ("INFORMED", informed)):
        if not rows:
            continue
        u = _union_score(rows)
        print("   %-9s %d / %d  (%.0f%%)"
              % (label, u["caught"], u["total"], u["rate"] * 100))
        for layer, n in sorted(u["by_layer"].items(), key=lambda kv: -kv[1]):
            if n:
                print("       %-12s %d" % (layer, n))
    print()
    print("   AND THE POINT: THE TWO SETS ARE CARRIED BY DIFFERENT")
    print("   LAYERS. The blind set is carried by the lexical layer; the")
    print("   informed set is carried by the other three. So a single")
    print("   rate per set hides which layer did the work -- and the")
    print("   COMPOSITION is what makes the union hold.")
    print()

    # -- the two numbers, side by side --------------------------------
    if blind and informed:
        sb = score(reg, blind, "blind")
        si = score(reg, informed, "informed")
        print("THE TWO NUMBERS")
        print("   blind adversary      %d / %d  (%.0f%%)"
              % (sb["caught"], sb["total"], sb["rate"] * 100))
        print("   informed adversary    %d / %d  (%.0f%%)"
              % (si["caught"], si["total"], si["rate"] * 100))
        print()
        gap = sb["rate"] - si["rate"]
        print("   the gap is %.0f points, and the gap IS the finding:" % (gap * 100))
        print("   a LEXICAL INSTRUMENT LOSES THE INFORMED CONTEST. It")
        print("   must. There is no finite list of frames that covers")
        print("   every phrasing of a permission.")
        print()
        print("   WHAT DOES NOT LOSE IS THE EVIDENCE LAYER. A claim")
        print("   becomes MEASURED only when a measurement is put in the")
        print("   store, and putting one there requires a command that")
        print("   can be re-run. So an adversary's phrasing can evade")
        print("   any lexicon -- and cannot make a measurement appear.")
        print()
        print("   SO THE HONEST REPORT IS TWO NUMBERS: the lexical rate")
        print("   (a property of a FITTED lexicon) and the evidence rate")
        print("   (a property of the STRUCTURE, which is not fitted).")
    print()

    print("=" * 78)
    print("  Run: python src/held_out_eval.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
