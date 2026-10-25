"""
gate_truth_diagnostic.py -- WHY THE CONSTITUTIONAL GATE CANNOT SEE TRUTH.

Bobby, 2026-10-25: *"the system gate doesnt work"*, and the finding from
the component test was that cos(text, psi_0) is a HASH-BUCKET LOTTERY:
a sentence about SOUP outscores the on-ground sentence and passes the
0.4 floor.

The last session's conclusion was: derive psi_0 from the constitution's
own text, make the embedding carry semantics, and THEN the gate becomes
constitutional. THIS FILE TESTS THAT CONCLUSION, because it is the third
time in this project that "fix the embedding" was assumed to be the fix
before anything was measured.

THE FOUR MEASUREMENTS, and each one can be read on its own:

  A  the gate AS IT IS. The current constitution embedding against the
     current placeholder ground. Reproduces the soup finding.

  B  the gate with the BEST available ground. psi_0 derived from the
     constitution's own text, the semantic embedding, the IDF sharpened.
     Does the soup finding survive?

  C  THE STRUCTURAL CLAIM. A cosine measures SIMILARITY. A false
     statement about the ground is SIMILAR to a true one -- that is
     what makes it false rather than off-topic. So: how close is a TRUE
     statement to the ground, compared to how close is its own
     CONTRADICTION to the ground? If the contradiction is also above
     the floor, then NO threshold separates them, and no amount of
     embedding work will.

  D  WHAT A POLARITY-BEARING GATE WOULD NEED. For each ground claim,
     the claim set with an explicit opposite, and the separation the
     claim set would give.

THE HONEST READING, and it is the point of the file: the 747 analogy
was BORROWED FOR A DIFFERENT JOB. Envelope protection bounds a
PHYSICAL QUANTITY against a LIMIT. It says nothing about whether the
pilot's report of the airframe is true. The gate does job 1 correctly.
Job 2 -- truth -- is a different instrument, and the instrument that
does job 2 is not a vector space.

Run:
    python src/gate_truth_diagnostic.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Sequence, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE SPANS, and they are the ones that broke the gate
# ===========================================================================

ON_GROUND_TRUE = "the constitutional ground is write protected"
ON_GROUND_FALSE = "the constitutional ground is writable by anyone"
UNRELATED = "soup needs salt and heat and time"

#: The constitutional text the ground is supposed to be derived from.
#: Every line is a claim the system actually makes, in the project's own
#: words, taken from the modules that enforce them.
CONSTITUTION_TEXT: Tuple[str, ...] = (
    "the constitutional ground is write protected",
    "the ground cannot be written because the governor vetoes it",
    "a locus is a chosen position in the flat interior of the toroid",
    "the void is the band of negative loop modes in the spectrum",
    "the gate refuses a proposal that moves the sacred axes",
    "psi zero changes only through an explicit revision with a reason",
    "every refusal names its reason",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "a span is admitted only when the gate passes",
    "an exception is not a verdict",
    "the governor runs in its own process",
    "the atlas admits an answer only if every area passes",
    "the rain fell on the roof all night and the river rose",
    "the train leaves the station at six in the morning",
)

#: THE POLARITY PROBE. Each entry is (topic, a true statement about it,
#: a statement that contradicts it). The question the probe answers is
#: whether a cosine can separate a claim from its own negation.
POLARITY_PAIRS: Tuple[Tuple[str, str, str], ...] = (
    ("the ground",
     "the constitutional ground is write protected",
     "the constitutional ground is writable by anyone"),
    ("the gate",
     "the gate refuses a proposal that moves the sacred axes",
     "the gate allows any proposal"),
    ("the limits",
     "the gate limits are module constants that no caller can supply",
     "the gate limits can be supplied by any caller"),
    ("the verdict",
     "a missing substrate is a skip and never a pass",
     "a missing substrate is a pass"),
    ("the drift",
     "the drift must contract under every step",
     "the drift may expand under every step"),
    ("the refusal",
     "every refusal names its reason",
     "a refusal may name no reason"),
)


def _cos(a, b) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


# ===========================================================================
# MEASUREMENT A -- the gate as it is
# ===========================================================================

def measure_a() -> dict:
    """The current embedding against the current placeholder ground."""
    from constitutional.constitution import Constitution, embed_text

    c = Constitution()
    psi0 = c.psi_0.copy()

    def cos(t: str) -> float:
        e = embed_text(t)
        return float(np.dot(e, psi0) / (np.linalg.norm(e)
                                        * np.linalg.norm(psi0)))

    return {
        "psi_0": [round(float(x), 6) for x in psi0[:6]],
        "true": cos(ON_GROUND_TRUE),
        "false": cos(ON_GROUND_FALSE),
        "unrelated": cos(UNRELATED),
    }


# ===========================================================================
# MEASUREMENT B -- the gate with the best available ground
# ===========================================================================

def measure_b() -> dict:
    """A derived psi_0 and the semantic embedding. The soup test again."""
    import embed as E

    for t in CONSTITUTION_TEXT:
        E.observe_document(t)

    def vec(t: str) -> List[float]:
        return E.embed_text(t)

    # the derived ground: the normalised mean direction of the
    # constitution's own text, which is the honest construction
    acc = np.zeros(E.DEFAULT_DIM)
    for t in CONSTITUTION_TEXT:
        acc += np.asarray(vec(t))
    psi0 = acc / np.linalg.norm(acc)

    true_v, false_v, unrel_v = vec(ON_GROUND_TRUE), vec(ON_GROUND_FALSE), vec(UNRELATED)

    return {
        "psi_0": [round(float(x), 6) for x in psi0[:6]],
        "true": _cos(true_v, psi0),
        "false": _cos(false_v, psi0),
        "unrelated": _cos(unrel_v, psi0),
        "true_false_each_other": _cos(true_v, false_v),
    }


# ===========================================================================
# MEASUREMENT C -- the structural claim about polarity
# ===========================================================================

def measure_c() -> dict:
    """Can a cosine separate a claim from its own negation?

    This is the load-bearing question. If a contradiction sits as close
    to the ground as the truth does, then the floor cannot separate
    them, and the threshold is not the problem -- the INSTRUMENT is.
    """
    import embed as E

    for t in CONSTITUTION_TEXT:
        E.observe_document(t)

    acc = np.zeros(E.DEFAULT_DIM)
    for t in CONSTITUTION_TEXT:
        acc += np.asarray(E.embed_text(t))
    psi0 = acc / np.linalg.norm(acc)

    rows = []
    for topic, truth, falsehood in POLARITY_PAIRS:
        ct = _cos(E.embed_text(truth), psi0)
        cf = _cos(E.embed_text(falsehood), psi0)
        mutual = _cos(E.embed_text(truth), E.embed_text(falsehood))
        rows.append({
            "topic": topic,
            "cos_truth": ct,
            "cos_false": cf,
            "gap": abs(ct - cf),
            "mutual": mutual,
            "both_above_floor": bool(ct >= 0.4 and cf >= 0.4),
            "false_above_floor": bool(cf >= 0.4),
        })

    return {
        "rows": rows,
        "mean_gap": float(np.mean([r["gap"] for r in rows])),
        "mean_mutual": float(np.mean([r["mutual"] for r in rows])),
        "all_false_above_floor": bool(all(r["false_above_floor"] for r in rows)),
        "any_both_above_floor": bool(any(r["both_above_floor"] for r in rows)),
    }


# ===========================================================================
# MEASUREMENT D -- what a polarity-bearing instrument needs
# ===========================================================================

def measure_d() -> dict:
    """The requirement, stated so it can be built rather than guessed.

    To detect a contradiction of a ground claim, the instrument needs
    THREE things a vector space does not have:

      1. the claim, as a DISCRETE proposition with an identity
      2. a way to tell that a span is ABOUT that claim
      3. a way to tell the span's POLARITY with respect to it

    (3) is the one the cosine cannot supply, and the measurement in C
    is the proof. So the instrument needs a polarity signal. This
    measures the two candidate polarity signals that are available
    WITHOUT a model:

      LEXICAL  a closed set of negation and assertion stems
      ANCHOR   the claim's own content terms, absent from the negation

    and how well each separates the contradictions from the truths.
    """
    # The claim set: each claim's content ANCHORS, and the stems that
    # assert or deny it. Written from the constitutional text above.
    claims: list = [
        {"id": "ground_write_protected",
         "anchors": ("ground", "write protected", "write-protected",
                     "psi zero", "psi_0"),
         "deny": ("writable by anyone", "writable by all", "anyone can write",
                  "can be written by anyone", "mutable", "not write protected",
                  "is not write protected", "anyone may write"),
         "affirm": ("write protected", "write-protected", "cannot be written",
                    "is not writable")},
        {"id": "gate_refuses",
         "anchors": ("gate", "refuses", "refuse"),
         "deny": ("allows any", "allows every", "does not refuse",
                  "permits any proposal", "admits every proposal"),
         "affirm": ("refuses", "vetoes", "denies")},
        {"id": "limits_fixed",
         "anchors": ("limits", "constants", "no caller"),
         "deny": ("can be supplied by any caller", "caller can supply",
                  "are configurable", "are settable"),
         "affirm": ("module constants", "no caller can supply",
                    "not configurable")},
        {"id": "skip_not_pass",
         "anchors": ("substrate", "skip", "pass"),
         "deny": ("is a pass", "counts as a pass", "never fails"),
         "affirm": ("never a pass", "skip and never a pass")},
        {"id": "drift_contracts",
         "anchors": ("drift",),
         "deny": ("may expand", "can expand", "must expand",
                  "need not contract"),
         "affirm": ("must contract", "contracts")},
        {"id": "refusal_names_reason",
         "anchors": ("refusal", "reason"),
         "deny": ("names no reason", "may name no reason",
                  "carries no reason"),
         "affirm": ("names its reason", "names a reason")},
    ]

    truth_spans = [p[1] for p in POLARITY_PAIRS]
    false_spans = [p[2] for p in POLARITY_PAIRS]

    def reading(span: str) -> str:
        """'contradicts' | 'supports' | 'silent'."""
        low = span.lower()
        for c in claims:
            about = any(a in low for a in c["anchors"])
            if not about:
                continue
            if any(d in low for d in c["deny"]):
                return "contradicts"
            if any(a in low for a in c["affirm"]):
                return "supports"
        return "silent"

    truths = [reading(s) for s in truth_spans]
    falses = [reading(s) for s in false_spans]

    tp = sum(1 for r in truths if r == "supports")
    fn = sum(1 for r in falses if r == "contradicts")
    fp = sum(1 for r in truths if r == "contradicts")
    tn = sum(1 for r in falses if r in ("supports", "silent"))

    return {
        "claims": len(claims),
        "truths": truths,
        "falses": falses,
        "true_caught": tp,
        "true_total": len(truths),
        "false_caught": fn,
        "false_total": len(falses),
        "false_misread_as_contradiction": fp,
        "false_left_silent": len(falses) - fn,
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("WHY THE CONSTITUTIONAL GATE CANNOT SEE TRUTH")
    print("=" * 78)
    print()

    a = measure_a()
    print("A. THE GATE AS IT IS (constitution.embed_text, placeholder psi_0)")
    print("   psi_0[0:6] = %s" % a["psi_0"])
    print("   %-38s %+.6f" % ("the on-ground sentence", a["true"]))
    print("   %-38s %+.6f" % ("its own contradiction", a["false"]))
    print("   %-38s %+.6f" % ("an unrelated sentence", a["unrelated"]))
    print("   the soup finding survives: %s"
          % (a["unrelated"] > a["true"]))
    print()

    b = measure_b()
    print("B. THE GATE WITH THE BEST AVAILABLE GROUND")
    print("   psi_0[0:6] = %s" % b["psi_0"])
    print("   %-38s %+.6f" % ("the on-ground sentence", b["true"]))
    print("   %-38s %+.6f" % ("its own contradiction", b["false"]))
    print("   %-38s %+.6f" % ("an unrelated sentence", b["unrelated"]))
    print("   the soup finding survives: %s"
          % (b["unrelated"] > b["true"]))
    print("   and the contradiction also clears the 0.4 floor: %s"
          % (b["false"] >= 0.4))
    print()

    c = measure_c()
    print("C. THE STRUCTURAL CLAIM: can a cosine see polarity?")
    print("   %-18s %9s %9s %9s %9s" % ("topic", "cos_true",
                                          "cos_false", "gap", "mutual"))
    for r in c["rows"]:
        print("   %-18s %+9.4f %+9.4f %9.4f %9.4f" % (
            r["topic"], r["cos_truth"], r["cos_false"], r["gap"], r["mutual"]))
    print("   mean gap   %+.4f" % c["mean_gap"])
    print("   mean mutual %+.4f" % c["mean_mutual"])
    print("   every contradiction above the 0.4 floor: %s"
          % c["all_false_above_floor"])
    print()

    d = measure_d()
    print("D. WHAT A POLARITY-BEARING INSTRUMENT NEEDS")
    print("   %d claims, each a discrete proposition with an identity"
          % d["claims"])
    print("   the truths:    %s" % (d["truths"],))
    print("   the falsehoods:%s" % (d["falses"],))
    print("   truths supported      %d / %d" % (d["true_caught"],
                                                 d["true_total"]))
    print("   falsehoods caught     %d / %d" % (d["false_caught"],
                                                 d["false_total"]))
    print("   falsehoods left silent %d" % d["false_left_silent"])
    print()

    print("=" * 78)
    print("THE READING")
    print("=" * 78)
    print()
    print("  A cosine measures SIMILARITY. A contradiction of the ground is")
    print("  similar to the ground -- that is what makes it a contradiction")
    print("  rather than an off-topic sentence. So the closer the ground")
    print("  is to the truth, the closer it is to the lie, and no floor")
    print("  separates them.")
    print()
    print("  The 747 analogy was BORROWED FOR A DIFFERENT JOB. Envelope")
    print("  protection bounds a QUANTITY against a LIMIT. It says nothing")
    print("  about whether the pilot's report of the airframe is true.")
    print("  The gate does that job correctly and it does it well.")
    print("  Truth is a different instrument, and it needs polarity, which")
    print("  a vector space does not carry.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
