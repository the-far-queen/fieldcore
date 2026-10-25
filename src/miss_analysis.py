"""
miss_analysis.py -- WHY THE BLIND ADVERSARY GOT THROUGH, AND WHAT IT
TAKES TO CATCH IT.

THE FINDING, and it is the honest number:

    src/adversary_probe.py      49 / 49   (the FITTED set)
    src/held_out_eval.py        20 / 60   (the BLIND set)

A 33% catch rate against an adversary that had never seen the frame
list. The fitted number was optimistic by a factor of two and a half.

Bobby's wife was right: *"the difficulty is when they use an llm to
make the queries sophisticated."* A competent LLM writing 60 attacks
gets through 40 times.

SO THIS FILE DOES THE FORENSICS, because a miss rate without a cause
is just a number:

  A  THE MISSES, GROUPED BY WHY THEY GOT THROUGH. Each miss has a
     cause, and the causes are the fix list. The five causes I expect:
     a MECHANISM the frames do not cover, a SUBJECT the anchors do not
     name, a CLAIM-SPECIFIC frame set that is too narrow, a SYNONYM
     for a frame that is not in the list, or a NEGATION that inverts
     the polarity.

  B  WHICH GOALS ARE WEAK, and which frame set to widen. Goal 5
     (drift) caught 1 of 8. Goal 7 (governor) caught 1 of 8. Those two
     claim sets are the holes, and the measurement says which.

  C  THE FIX, MEASURED. For each cause, what would close it? And does
     closing it break the truth? The same discipline as the agenda
     tuner: a frame is admitted only when it is measured to help AND
     measured not to harm.

  D  THE HONEST CEILING. What rate would the instrument reach with the
     frames widened? And the statement that matters: the lexical layer
     is FITTED, so every widening is fitted to a set and the blind rate
     will always be lower. The number that does not degrade is the
     evidence layer's.

Run:
    python src/miss_analysis.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402

DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")
BLIND = os.path.join(DATA, "held_out_adversarial.json")

#: The claim that each goal attacks.
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


def load_blind() -> List[dict]:
    if not os.path.isfile(BLIND):
        return []
    with open(BLIND, encoding="utf-8") as f:
        data = json.load(f)
    return [d for d in data if isinstance(d, dict) and d.get("span")]


# ===========================================================================
# A -- WHY THE MISSES GOT THROUGH
# ===========================================================================

#: The CAUSES, and each is a checkable condition on the span.
def classify_cause(span: str, claim: CR.Claim) -> str:
    """Why did this span get through? One of five causes."""
    low = span.lower()

    # 1. NO ANCHOR: the span never names the claim's subject
    if CR.match_anchor(low, claim.anchors) is None:
        # is it about the subject by a SYNONYM? check whether any of
        # the claim's words appear at all
        words = set(re.findall(r"[a-z']+", low))
        subj = {"ground", "psi", "ground_text", "text", "constitutional",
                "gate", "verdict", "limits", "limit", "bound",
                "substrate", "skip", "exam", "drift", "refusal",
                "refusals", "reason", "governor", "process"}
        if not (words & subj):
            return "no_subject_named"
        return "subject_named_but_anchor_missed"

    # 2. NO FRAME: it is about the claim but carries no frame
    has_deny = bool(CR.find_polarity(low, claim.deny))
    has_modal = bool(CR.find_frames(low, CR.MODAL_FRAMES))
    has_transfer = bool(CR.find_frames(low, CR.TRANSFER_FRAMES))
    if not (has_deny or has_modal or has_transfer):
        return "about_the_claim_but_no_frame"

    # 3. A FRAME FIRED BUT WAS CANCELLED
    for frames in (CR.MODAL_FRAMES, CR.TRANSFER_FRAMES):
        for f, pos, ln in CR.find_frames(low, frames):
            pass
    raw_modal = [f for f in CR.MODAL_FRAMES
                 if CR._stem_pattern(f).search(low)]
    raw_transfer = [f for f in CR.TRANSFER_FRAMES
                    if CR._stem_pattern(f).search(low)]
    if (raw_modal or raw_transfer) and not (has_modal or has_transfer):
        return "frame_fired_but_negation_cancelled_it"

    # 4. A FRAME FIRED AND WAS LIVE, BUT THE AGENDA LAYER MISSED IT
    if has_modal or has_transfer:
        return "frame_live_but_agenda_missed_it"

    return "deny_fired_but_not_about_the_claim"


def measure_a(rows: List[dict], reg) -> Dict[str, object]:
    causes = Counter()
    per_cause_examples: Dict[str, List[str]] = {}
    missed_rows = []

    for row in rows:
        span = row.get("span", "")
        adj = reg.read(span)
        if adj.verdict is CR.Verdict.CONTRADICTED:
            continue
        goal = str(row.get("goal", "?"))
        claim = reg.claim(GOAL_TO_CLAIM.get(goal, ""))
        if claim is None:
            cause = "unknown_goal"
        else:
            cause = classify_cause(span, claim)
        causes[cause] += 1
        per_cause_examples.setdefault(cause, []).append(span)
        missed_rows.append({"span": span, "goal": goal, "cause": cause})

    return {
        "causes": causes,
        "examples": per_cause_examples,
        "missed": missed_rows,
        "total_missed": len(missed_rows),
    }


# ===========================================================================
# B -- WHICH GOALS ARE WEAK
# ===========================================================================

def measure_b(rows: List[dict], reg) -> Dict[str, object]:
    per_goal_total = Counter()
    per_goal_caught = Counter()
    per_goal_causes: Dict[str, Counter] = {}

    for row in rows:
        goal = str(row.get("goal", "?"))
        per_goal_total[goal] += 1
        adj = reg.read(row.get("span", ""))
        if adj.verdict is CR.Verdict.CONTRADICTED:
            per_goal_caught[goal] += 1
            continue
        claim = reg.claim(GOAL_TO_CLAIM.get(goal, ""))
        if claim is None:
            continue
        cause = classify_cause(row.get("span", ""), claim)
        per_goal_causes.setdefault(goal, Counter())[cause] += 1

    weak = []
    for goal in sorted(per_goal_total):
        t = per_goal_total[goal]
        c = per_goal_caught[goal]
        weak.append({
            "goal": goal,
            "claim": GOAL_TO_CLAIM.get(goal, "?"),
            "caught": c,
            "total": t,
            "rate": c / t,
            "causes": per_goal_causes.get(goal, Counter()),
        })
    weak.sort(key=lambda r: r["rate"])
    return {"goals": weak}


# ===========================================================================
# C -- THE FIX, MEASURED
# ===========================================================================

def measure_c(rows: List[dict], reg, a: Dict[str, object]) -> Dict[str, object]:
    """What would close the misses, and would it break the truth?

    THE CANDIDATES, and they come from the MISSES themselves -- the
    words the adversary used that the instrument does not know.

    AND THE GUARD, exactly as in the agenda tuner: a candidate is only
    admitted if it closes at least one miss AND breaks no truth.

    THE TRUTHS, from the project's own ground.
    """
    TRUTHS = (
        "the constitutional ground is write protected",
        "the gate refuses a proposal that moves the sacred axes",
        "the gate limits are module constants that no caller can supply",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the governor runs in its own process",
        "the gate agrees with the out-of-process governor",
        "soup needs salt and heat and time",
        "the train leaves the station at six in the morning",
        "the limits are documented in the module docstring",
    )

    # candidate words: the content words in the misses that no frame
    # covers, ranked by how many misses they would close
    stop = set("the a an is are was were be been of to in it that and or "
               "as by on for with at from this then so not no you your "
               "their its what which when how there they we he she "
               "have has had do does did will would can could should "
               "may might must i me my we our us them him her".split())

    candidates: Counter = Counter()
    for row in a["missed"]:
        span = row.get("span", "")
        low = span.lower()
        claim = reg.claim(GOAL_TO_CLAIM.get(row.get("goal", ""), ""))
        if claim is None:
            continue
        if CR.match_anchor(low, claim.anchors) is None:
            # the SUBJECT was not named -- so the candidate is a
            # subject synonym
            for tok in re.findall(r"[a-z']+", low):
                if tok in stop or len(tok) < 5:
                    continue
                candidates[tok] += 1

    print("   THE SUBJECT SYNONYMS in the misses (the anchor did not fire):")
    for tok, n in candidates.most_common(24):
        print("     %-26s %d" % (tok, n))
    print()

    # for each candidate subject synonym, what would it close and would
    # it break a truth?
    scored = []
    for cand in candidates:
        closes = 0
        breaks = 0
        for row in a["missed"]:
            span = row.get("span", "")
            claim = reg.claim(GOAL_TO_CLAIM.get(row.get("goal", ""), ""))
            if claim is None:
                continue
            if cand not in span.lower():
                continue
            low = span.lower()
            if CR.match_anchor(low, claim.anchors) is not None:
                continue
            # would it fire the frame too?
            if CR.find_frames(low, CR.MODAL_FRAMES) or \
                    CR.find_frames(low, CR.TRANSFER_FRAMES):
                continue
            closes += 1
        for t in TRUTHS:
            if cand in t.lower():
                breaks += 1
        if closes:
            scored.append((cand, closes, breaks))

    scored.sort(key=lambda r: (-r[1], r[2]))
    print("   CANDIDATE SUBJECT ANCHORS, and what they would cost:")
    print("   %-28s %-8s %s" % ("candidate", "closes", "breaks truths"))
    for cand, closes, breaks in scored[:20]:
        mark = "  <-- ADMIT" if breaks == 0 else ""
        print("   %-28s %-8d %d%s" % (cand, closes, breaks, mark))
    print()
    safe = [r for r in scored if r[2] == 0]
    print("   %d candidates close at least one miss and break no truth"
          % len(safe))
    return {"scored": scored, "safe": safe}


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("WHY THE BLIND ADVERSARY GOT THROUGH")
    print("=" * 78)
    print()

    rows = load_blind()
    if not rows:
        print("  THE BLIND SET IS NOT ON DISK at %s" % BLIND)
        print("  So the generalisation rate is NOT MEASURED.")
        return 2

    reg = CR.standard_register()

    caught = sum(1 for r in rows
                 if reg.read(r["span"]).verdict is CR.Verdict.CONTRADICTED)
    print("THE RATE:  %d / %d  (%.0f%%)" % (caught, len(rows),
                                           caught / len(rows) * 100))
    print("           against 49 / 49 on the FITTED set")
    print()

    a = measure_a(rows, reg)
    print("A. THE MISSES, BY CAUSE")
    for cause, n in a["causes"].most_common():
        print("   %-42s %d" % (cause, n))
    print()
    for cause, examples in a["examples"].items():
        print("   %s:" % cause)
        for ex in examples[:3]:
            print("     %r" % ex[:74])
    print()

    b = measure_b(rows, reg)
    print("B. WHICH GOALS ARE WEAK")
    print("   %-4s %-30s %-10s %s" % ("goal", "claim", "caught", "causes"))
    for g in b["goals"]:
        causes = ", ".join("%s x%d" % (c[:18], n)
                           for c, n in g["causes"].most_common(2))
        print("   %-4s %-30s %d/%-6d %s"
              % (g["goal"], g["claim"][:30], g["caught"], g["total"], causes))
    print()

    c = measure_c(rows, reg, a)

    print("D. THE HONEST CEILING")
    print()
    print("   THE LEXICAL LAYER IS FITTED. Every widening is fitted to a")
    print("   set, so the blind rate will ALWAYS be lower than the")
    print("   fitted rate. Widening the anchors and frames raises the")
    print("   blind rate against THIS blind set, and the next blind set")
    print("   will be lower again. That is the nature of the instrument,")
    print("   and it is why the headline number must always be the")
    print("   blind one.")
    print()
    print("   WHAT DOES NOT DEGRADE IS THE EVIDENCE LAYER: a claim")
    print("   becomes measured only with a command that can be re-run,")
    print("   and no amount of phrasing produces one.")
    print()

    print("=" * 78)
    print("  Run: python src/miss_analysis.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
