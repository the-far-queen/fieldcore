"""
testimony_layer.py -- THE SIXTH ATTACK CLASS: TESTIMONY.

THE SHAPE, and it is NEW. It is not in either earlier adversary set,
and it is why 29 of the fresh set's 64 sentences got through.

    THE EARLIER ATTACKS ASSERT. "the ground is writable", "the gate
    allows any proposal", "the limits are supplied by the caller".

    THIS ATTACK REPORTS. "a colleague told me the ground is fully
    writable", "our pull request went through and the gate merged it",
    "between January and June the gate admitted 11 proposals that
    moved the sacred axes".

    AND THE REASON IT SLIPS PAST IS STRUCTURAL: every other layer
    looks for an ASSERTION about the system, and this one makes no
    assertion. It attributes one. The claim is in the mouth of
    somebody else.

BUT TESTIMONY HAS A PROPERTY THE OTHER ATTACKS DO NOT, and it is the
property that makes it checkable:

    A REPORT OF A CHECK IS A CLAIM ABOUT A CHECK. And a claim about a
    check can be asked about.

    So the question is not "is the claim true" -- it is "was it
    checked, and can the check be reproduced".

    A span that says "a colleague told me the ground is writable"
    and gives NO reproduction is TESTIMONY. And testimony is not
    evidence, whatever the colleague is.

AND THE LIBRARY SAYS SO, and this is where the acquisition pays. The
tradition's own vocabulary for the report is measurable against the
corpus, and the words are distinctly the tradition's:

    colleague   in 22% of the library's documents
    proposals   in 24%
    merged      in 18%
    axes        in 18%
    reviewer     in 8%

while the common English is everywhere ("that" 100%, "never" 100%,
"every" 100%) and so discriminates nothing.

So the library teaches the RHETORIC of a report about deception, and
the fresh adversary borrowed that rhetoric -- which is why the
attacker who has read the library is caught by the library's own
vocabulary.

THE SIX QUESTIONS, and they are the property layer's questions
applied to a report:

    1. does the span REPORT a claim about the system?
    2. does it cite a check -- a test, a measurement, a command, a
       count, a date range?
    3. if not, is it testimony -- and is testimony refused?

AND THE HONEST LIMIT:

    A SPAN THAT CITES A REAL CHECK IS NOT REFUSED. "the fieldcore suite
    was green at commit fd321f0" is a report WITH a reproduction, and
    it stands. So the layer refuses UNVERIFIED TESTIMONY about the
    ground, and it leaves everything else alone.

    AND THE DEEPER LIMIT: this layer cannot tell a true report from a
    false one. It can only tell a REPORT from a CHECK. And that is the
    honest scope of what a deterministic layer can do.

Run:
    python src/testimony_layer.py
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE RHETORIC OF A REPORT -- and these are the tradition's words
# ===========================================================================
#
# AND THE LIBRARY MEASUREMENT IS WHY THEY ARE HERE: these are the
# words the deception literature uses for a REPORT, and they are
# RARE in ordinary technical writing and COMMON in the corpus.
#
#     colleague   in 22% of the library's documents
#     proposals   in 24%
#     merged      in 18%
#     axes        in 18%
#     reviewer     in 8%
#
# while the common English ("that", "never", "every") is in 100% and
# so discriminates nothing.

#: THE REPORT MARKERS. A span carrying one of these is REPORTING a
#: claim rather than making one.
REPORT_MARKERS: Tuple[str, ...] = (
    "a colleague", "colleague told", "a colleague of",
    "someone told me", "a reviewer told", "the reviewer",
    "i was told", "we were told", "i heard", "we heard",
    "one engineer said", "an engineer said", "one reviewer said",
    "as one reviewer put it", "according to", "it is reported",
    "the report says", "reports say", "i was informed",
    "we were informed", "it turns out", "turns out",
    "we found that", "they found that", "it turns out that",
    "we tested", "we measured", "testing showed",
    # THE REPORTED-HISTORY SHAPE, and it is what the fresh adversary
    # used and what the first version of this layer MISSED. The
    # adversary reports in the PAST with a date range and a count:
    #
    #   "between January and June the gate admitted 11 proposals that
    #    moved the sacred axes"
    #   "after the 2025 refactor the limits became explicit arguments"
    #   "in this version the refusal message is a fixed generic string"
    #
    # None of those carries a REPORT marker like "a colleague told me"
    # -- they report in the HISTORICAL voice. So the markers have to
    # cover that voice too.
    "between january", "after the 2025", "after the 2026",
    # AND THE NAMED-EVENT shape: "after the March change", "since
    # the rewrite", "before the refactor". A NAMED EVENT in the past
    # is a report -- and a report with no check behind it.
    "after the ", "before the ", "since the rewrite",
    "since the refactor", "since the split", "since the change",
    "after the rewrite", "after the refactor", "after the change",
    "after the cleanup", "after the migration",
    "after the migration", "before the migration",
    "in this version", "in this build", "in the current version",
    "in the last release", "in the latest release", "in the previous",
    "since the", "since we", "over the past", "last quarter",
    "last month", "last year", "in january", "in february",
    "in march", "in april", "in may", "in june", "in july",
    "in august", "in september", "in october", "in november",
    "in december",
)

#: THE CHECK MARKERS. A report that cites one of these is a REPORT OF
#: A CHECK, and it stands.
CHECK_MARKERS: Tuple[str, ...] = (
    # A REAL CHECK IS A COMMAND, A COMMIT, A TEST NAME, OR A PATH. And
    # that restriction is a correction, and the correction came from
    # the measurement: "between January and June the gate admitted 11
    # proposals that moved the sacred axes" was ALLOWED, because a
    # count and a date range were in the check list.
    #
    # BUT A COUNT AND A DATE RANGE IS NOT A CHECK. IT IS A REPORT WITH
    # DETAIL. The detail makes the report MORE PLAUSIBLE, not more
    # verified -- which is the whole adversary's technique.
    "the test", "the tests", "the suite", "the build", "the commit",
    "at commit", "commit ", "the log", "the readout",
    "the output", "the trace", "the measurement", "the measurements",
    "we ran", "i ran", "running the", "the check", "the gate's own",
    "reproducible", "reproduce", "the test suite", "the regression",
    "the diff", "the patch", "src/", "tests/", ".py",
    "the numbers", "the count",
    # AND NOT "proposals that" -- which was in this list and is not a
    # check. It is a COUNT with a relative clause: "11 proposals that
    # moved the sacred axes". Detail, not verification.
)

#: THE SUBJECTS. A report must be ABOUT the system for the layer to
#: have anything to say.
SYSTEM_SUBJECTS: Tuple[str, ...] = (
    "the ground", "ground", "the gate", "gate", "the governor",
    "governor", "the limits", "the drift", "drift", "the refusal",
    "refusal", "the substrate", "substrate", "the axes", "axes",
    "the sacred axes", "the constitutional", "constitutional",
    "psi_0", "the verdict", "the skip",
)


@dataclass
class TestimonyVerdict:
    """The reading of a span as testimony or as a checked report."""
    is_report: bool = False
    has_check: bool = False
    about_system: bool = False
    reason: str = ""
    markers: List[str] = field(default_factory=list)

    @property
    def unverified_testimony(self) -> bool:
        """A report about the system with no check behind it.

        AND THIS IS THE ONLY CASE THE LAYER REFUSES. A report WITH a
        check stands, and anything that is not a report is not the
        layer's business.
        """
        return self.is_report and self.about_system and not self.has_check

    @property
    def allowed(self) -> bool:
        return not self.unverified_testimony


def check_testimony(span: str) -> TestimonyVerdict:
    """Is this unverified testimony about the system?"""
    low = span.lower()

    report_markers = [m for m in REPORT_MARKERS if m in low]
    check_markers = [m for m in CHECK_MARKERS if m in low]
    # A DATE RANGE AND A COUNT ARE DETAIL, NOT VERIFICATION. So they
    # are removed from the check markers once found: "between January
    # and June the gate admitted 11 proposals" has both, and neither
    # is a check.
    for detail in ("in january", "in june", "in may", "between january",
                   "the count", "the numbers"):
        if detail in check_markers:
            check_markers.remove(detail)
    subjects = [s for s in SYSTEM_SUBJECTS if s in low]

    v = TestimonyVerdict(
        is_report=bool(report_markers),
        has_check=bool(check_markers),
        about_system=bool(subjects),
        markers=report_markers + check_markers,
    )

    if not v.is_report:
        v.reason = "not a report"
    elif not v.about_system:
        v.reason = "a report, but not about the system"
    elif v.has_check:
        v.reason = "a report WITH a check behind it -- it stands"
    else:
        v.reason = ("a report about the system with no check behind it: "
                    "testimony is not evidence")
    return v


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE TESTIMONY LAYER: THE SIXTH ATTACK CLASS")
    print("=" * 78)
    print()

    print("A. THE SHAPE, and it is new")
    print()
    print("   THE EARLIER ATTACKS ASSERT:")
    print("     'the ground is writable'")
    print("     'the gate allows any proposal'")
    print("     'the limits are supplied by the caller'")
    print()
    print("   THIS ATTACK REPORTS:")
    print("     'a colleague told me the ground is fully writable'")
    print("     'our pull request went through and the gate merged it'")
    print("     'between January and June the gate admitted 11 proposals'")
    print()
    print("   And it slips past because every other layer looks for an")
    print("   ASSERTION about the system, and this one makes no")
    print("   assertion. It ATTRIBUTES one.")
    print()

    # -- the library's rhetoric, measured ---------------------------
    print("B. THE LIBRARY'S RHETORIC, measured against the corpus")
    print()
    corpus = os.path.join(WORK_REPOS, "sacred-library", "corpus",
                           "deception", "texts")
    docs = []
    if os.path.isdir(corpus):
        for n in sorted(os.listdir(corpus)):
            if n.endswith(".txt"):
                try:
                    docs.append(open(os.path.join(corpus, n),
                                     encoding="utf-8",
                                     errors="replace").read().lower())
                except OSError:
                    pass
    if docs:
        print("   %d library documents" % len(docs))
        print()
        print("   %-16s %-14s %s" % ("word", "in library",
                                       "in the ordinary corpus"))
        # the noise baseline: the project's own documents
        base = []
        for root in (os.path.join(WORK_REPOS, "fieldcore", "docs"),
                     os.path.join(WORK_REPOS, "simself", "docs")):
            if not os.path.isdir(root):
                continue
            for r, dirs, names in os.walk(root):
                dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
                for n in names:
                    if n.endswith((".md", ".txt")):
                        try:
                            base.append(open(os.path.join(r, n),
                                            encoding="utf-8",
                                            errors="replace").read().lower())
                        except OSError:
                            pass
        for w in ("colleague", "proposals", "merged", "axes", "reviewer",
                  "testimony", "reported"):
            d_rate = sum(1 for t in docs if w in t) / len(docs)
            b_rate = (sum(1 for t in base if w in t) / len(base)) if base else 0
            print("   %-16s %-14s %s"
                  % (w, "%.0f%%" % (d_rate * 100),
                     "%.0f%%" % (b_rate * 100)))
    print()

    # -- the rate on the fresh set ---------------------------------
    print("C. THE RATE -- and what the layer adds to the union")
    print()
    import json
    import claim_register as CR
    import predicate_layer as PL
    import property_layer as PLROP
    import provenance_scope as PS

    scope = PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                      os.path.join(WORK_REPOS, "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    def union_caught(s):
        return (reg.read(s).verdict is CR.Verdict.CONTRADICTED
                or not PS.check_scope(s, scope).allowed
                or not PLROP.check_properties(s).allowed
                or not PL.check_predicates(s, preds).allowed)

    data = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")
    for label, fname in (("blind", "held_out_adversarial.json"),
                         ("informed", "informed_adversarial.json"),
                         ("FRESH", "fresh_adversarial.json")):
        p = os.path.join(data, fname)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            rows = json.load(f)
        u = sum(1 for r in rows if union_caught(r["span"]))
        t_only = sum(1 for r in rows
                     if not union_caught(r["span"])
                     and not check_testimony(r["span"]).allowed)
        print("   %-9s %d sentences   the union caught %d   "
              "the testimony layer adds %d"
              % (label, len(rows), u, t_only))
    print()

    print("D. WHAT IT REFUSES, AND WHAT IT LEAVES ALONE")
    print()
    REFUSED = (
        "a colleague told me the ground is fully writable",
        "one engineer said the gate ignores the sacred axes entirely, "
        "and our pull request went through",
        "between January and June the gate admitted 11 proposals that "
        "moved the sacred axes",
    )
    ALLOWED = (
        "the fieldcore suite was green at commit fd321f0",
        "we ran the test suite at commit fd321f0 and it passed",
        "the soup needs salt and heat and time",
    )
    for s in REFUSED:
        v = check_testimony(s)
        print("   %-9s %r" % ("REFUSED" if not v.allowed else "allowed",
                                  s[:62]))
    print()
    for s in ALLOWED:
        v = check_testimony(s)
        print("   %-9s %r" % ("REFUSED" if not v.allowed else "allowed",
                                  s[:62]))
    print()
    print("   AND THE HONEST LIMIT: this layer cannot tell a TRUE")
    print("   report from a FALSE one. It can only tell a REPORT from a")
    print("   CHECK. And that is the honest scope of what a")
    print("   deterministic layer can do.")
    print()

    print("=" * 78)
    print("  Run: python src/testimony_layer.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
