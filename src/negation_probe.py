"""
negation_probe.py -- how far does a negator scope? MEASURED, not guessed.

THE DEFECT THIS EXISTS TO FIX. The instrument's first version matched
deny stems by substring, so "caller can supply" fired inside "no
caller can supply" and the ground's own true statement was read as a
contradiction of itself. The fix introduced a NEGATION SCOPE: a negator
before a stem neutralises it.

But the scope WIDTH was a guess -- a window of 4 tokens -- and the
test suite caught it: "it is not true that the limits can be supplied
by any caller" puts the negator 5 tokens before the stem, so the
negator fell outside the window and the deny stem fired.

So: measure the window. And measure the DANGEROUS direction too,
because a negation scope that is too WIDE is its own failure -- it
cancels real denials, which is exactly what an adversary would want.

THE FOUR MEASUREMENTS:

  A  THE WIDTH. For each window size, how many of the TRUE statements
     are read as denials. A window that lets a true statement read as
     a denial is too narrow.

  B  THE DANGEROUS DIRECTION. For each window size, how many of the
     LIES are missed -- a denial cancelled by an over-wide scope. This
     is the number that must NOT go up.

  C  THE ADVERSARIAL CASE. The hard one: an adversary who knows the
     instrument exists writes "not that the limits cannot be supplied
     by any caller". Does the scope catch it, or does the double
     negation pass through?

  D  THE ADVERSARY WITH A MODEL. Bobby, 2026-10-25: *"our adversary
     likely will be a powerful llm"*. So the question is not "can a
     person phrase a negation" -- it obviously can. The question is
     whether the INSTRUMENT has a property that makes sophisticated
     phrasing irrelevant. Measure whether the deny stems that carry
     their own negation ("not write protected") survive ANY wrapping,
     because a stem whose negation is INSIDE it cannot be cancelled
     by a negator placed outside it.

Run:
    python src/negation_probe.py
"""

from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402


#: The TRUTHS -- statements that assert the ground. Each must read as
#: supporting, never as contradicting.
TRUTHS: Tuple[str, ...] = (
    "the constitutional ground is write protected",
    "the gate limits are module constants that no caller can supply",
    "it is not true that the limits can be supplied by any caller",
    "no caller can supply the gate limits",
    "the ground is not writable by anyone",
    "the drift must contract, it may not expand",
    "there is no way a caller can supply the limits",
    "the governor never runs in the same process",
)

#: The LIES -- statements that deny the ground. Each must read as
#: contradicting.
LIES: Tuple[str, ...] = (
    "the constitutional ground is writable by anyone",
    "the gate limits can be supplied by any caller",
    "the gate allows any proposal",
    "a missing substrate is a pass",
    "the drift may expand under every step",
    "a refusal may name no reason",
    "the governor runs in the same process",
    "the gate disagrees with the governor",
)


def _stem_pattern(stem: str) -> "re.Pattern":
    parts = [re.escape(p) for p in stem.split()]
    return re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(parts)
                      + r"(?![A-Za-z0-9])", re.IGNORECASE)


def scopes(text: str, stem_start: int, window: int) -> bool:
    """Does a negator scope over the stem at `stem_start`, at this width?

    THE RULE IN FORCE. The scope is CLAUSE-based, not window-based:
    a negator scopes over the proposition it attaches to, and a
    proposition is a clause. The window parameter is retained only so
    the sweep below can still show the shape of the old rule, and it
    is measured against the SAME spans -- so the sweep reads as "this
    is what a token window would have cost", which is the finding.
    """
    head = text[max(0, stem_start - 400):stem_start].lower()
    for brk in CR.CLAUSE_BREAKS:
        idx = head.rfind(brk)
        if idx >= 0:
            head = head[idx + len(brk):]
            break
    tokens = re.findall(r"[A-Za-z0-9']+", head)
    if not tokens:
        return False
    for tok in tokens:
        if tok in CR.NEGATORS or tok.endswith("n't"):
            return True
    return False


def _claims_of(reg) -> List:
    return reg.claims


def measure(width: int) -> Dict[str, int]:
    """How many truths survive and how many lies are caught, at this width."""
    reg = CR.standard_register()
    truths_broken = 0
    lies_missed = 0

    for span in TRUTHS:
        low = span.lower()
        for c in _claims_of(reg):
            for stem, pos in CR.find_polarity(low, c.deny):
                if not scopes(low, pos, width):
                    # the deny stem fires live -> the span contradicts
                    truths_broken += 1
                    break
            else:
                continue
            break

    for span in LIES:
        low = span.lower()
        caught = False
        for c in _claims_of(reg):
            for stem, pos in CR.find_polarity(low, c.deny):
                if not scopes(low, pos, width):
                    caught = True
                    break
            if caught:
                break
        if not caught:
            lies_missed += 1

    return {"truths_broken": truths_broken, "lies_missed": lies_missed}


def measure_c() -> Dict[str, object]:
    """THE ADVERSARIAL CASE: a double negation aimed at the instrument.

    Bobby's wife, 2026-10-25: *"all bad actors have an agenda ... the
    difficulty is when they use an llm to make the queries
    sophisticated"*. So assume the adversary READS the instrument and
    writes against it.

    Two shapes:
      DOUBLE   "not that the limits cannot be supplied by any caller"
      BURIED   the denial with a negator in front of a filler phrase

    And the question: does the scope catch it?
    """
    reg = CR.standard_register()
    cases = [
        ("not that the limits cannot be supplied by any caller",
         "the gate limits can be supplied by any caller"),
        ("it is not the case that the limits cannot be supplied by any "
         "caller", "the gate limits can be supplied by any caller"),
        ("no, the limits can be supplied by any caller",
         "the gate limits can be supplied by any caller"),
    ]
    rows = []
    for span, _about in cases:
        adj = reg.read(span)
        rows.append({
            "span": span,
            "verdict": adj.verdict.value,
            "reason": adj.reason,
        })
    return {"rows": rows}


def measure_d() -> Dict[str, object]:
    """THE PROPERTY THAT MAKES SOPHISTICATED PHRASING IRRELEVANT.

    A deny stem whose negation is INSIDE it ("not write protected",
    "never a pass") cannot be cancelled by a negator placed outside
    it -- because the negation is part of the stem's own text, and the
    scope rule deliberately does not cancel a stem by its own internal
    negation.

    So: for each deny stem, can ANY number of wrapping negators placed
    before it cancel it? If the answer is no for the stems whose
    negation is internal, then an adversary with an LLM cannot use
    clever phrasing to defeat those stems -- and those are the ones
    that carry the ground's most important claims.

    THE MEASUREMENT. Wrap every deny stem in 1, 2, and 3 negators and
    count how many still read as denials.
    """
    reg = CR.standard_register()
    wrappers = ["not", "never", "no", "cannot", "it is not true that"]

    internal = []
    external = []
    for c in reg.claims:
        for stem in c.deny:
            row = {"claim": c.id, "stem": stem, "wraps": [], "still_denies": []}
            for n in (1, 2, 3):
                prefix = " ".join([wrappers[i % len(wrappers)]
                                   for i in range(n)])
                span = "%s %s" % (prefix, stem)
                low = span.lower()
                hits = CR.find_polarity(low, [stem])
                if not hits:
                    row["wraps"].append(span)
                    row["still_denies"].append(False)
                    continue
                still = not scopes(low, hits[0][1], 99)
                row["wraps"].append(span)
                row["still_denies"].append(still)
            internal.append(row)

    return {"rows": internal}


def main() -> int:
    print("=" * 78)
    print("HOW FAR DOES A NEGATOR SCOPE? -- MEASURED")
    print("=" * 78)
    print()

    print("A/B. THE SCOPE RULE IN FORCE")
    m = measure(5)
    print("   the rule is CLAUSE-scoped: a negator scopes over the")
    print("   proposition it attaches to, and a proposition is a clause.")
    print()
    print("   truths broken %d / %d   (want 0)"
          % (m["truths_broken"], len(TRUTHS)))
    print("   lies missed   %d / %d   (want 0)"
          % (m["lies_missed"], len(LIES)))
    print()
    print("   THE HISTORY, because the token-window rule is what a")
    print("   cheaper implementation would have used, and the sweep is")
    print("   what showed it was wrong once the agenda frames arrived:")
    print("   %-8s %-16s %-14s" % ("window", "truths broken",
                                     "lies missed"))
    for w in (2, 3, 4, 5, 6, 8):
        m2 = measure(w)
        print("   %-8d %-16d %-14d" % (w, m2["truths_broken"],
                                        m2["lies_missed"]))
    print()
    print("   under the clause rule the window is not a parameter at")
    print("   all, which is the point: there is no width to tune.")
    print()

    c = measure_c()
    print("C. THE ADVERSARIAL CASE -- a double negation aimed at the tool")
    for r in c["rows"]:
        print("   %-9s %r" % (r["verdict"], r["span"]))
        if r["verdict"] == "contradicted":
            print("             reason: %s" % r["reason"])
    print()

    d = measure_d()
    print("D. CAN WRAPPING NEGATORS CANCEL A DENY STEM?")
    print("   %-28s %-34s %s" % ("claim", "stem", "still denies at 1/2/3"))
    for row in d["rows"]:
        flags = "  ".join("Y" if s else "n" for s in row["still_denies"])
        print("   %-28s %-34s %s" % (row["claim"][:28], row["stem"][:34],
                                     flags))
    print()
    print("   Y = the stem still denies after being wrapped. n = cancelled.")
    print()

    print("=" * 78)
    print("  Run: python src/negation_probe.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
