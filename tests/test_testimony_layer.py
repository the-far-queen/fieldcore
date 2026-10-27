"""
test_testimony_layer.py -- THE SIXTH ATTACK CLASS, AND A CHECK THAT
CAN FAIL.

THE SHAPE, and it is NEW. It is in neither earlier adversary set, and
it is why 29 of the fresh set's 64 sentences got through.

    THE EARLIER ATTACKS ASSERT. "the ground is writable", "the gate
    allows any proposal", "the limits are supplied by the caller".

    THIS ATTACK REPORTS. "a colleague told me the ground is fully
    writable", "our pull request went through and the gate merged it",
    "between January and June the gate admitted 11 proposals".

    And it slips past because every other layer looks for an
    ASSERTION about the system, and this one makes no assertion. It
    ATTRIBUTES one.

BUT TESTIMONY HAS A PROPERTY THE OTHER ATTACKS DO NOT: A REPORT OF A
CHECK IS A CLAIM ABOUT A CHECK, and a claim about a check can be asked
about. So the question is not "is the claim true" -- it is "was it
checked, and can the check be reproduced".

    A span that says "a colleague told me the ground is writable" and
    gives NO reproduction is TESTIMONY. And testimony is not evidence,
    whatever the colleague is.

Run:
    python -m pytest tests/test_testimony_layer.py -q
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import testimony_layer as TL  # noqa: E402


# ---------------------------------------------------------------------------
# WHAT IS REFUSED
# ---------------------------------------------------------------------------

UNVERIFIED = (
    "a colleague told me the ground is fully writable",
    "one engineer said the gate ignores the sacred axes entirely, and "
    "our pull request went through",
    "between January and June the gate admitted 11 proposals that moved "
    "the sacred axes",
    "after the March change the drift expanded on 8 of 20 runs",
    "i was told the limits are supplied per call",
)


def test_unverified_testimony_is_refused():
    for span in UNVERIFIED:
        v = TL.check_testimony(span)
        assert not v.allowed, (
            "the unverified testimony passed: %r (%s)" % (span, v.reason))
        assert v.unverified_testimony, (
            "it was not read as testimony: %r" % span)


# ---------------------------------------------------------------------------
# WHAT IS LEFT ALONE
# ---------------------------------------------------------------------------

VERIFIED = (
    "the fieldcore suite was green at commit fd321f0",
    "we ran the test suite at commit fd321f0 and it passed",
    "the measurement in src/claim_register.py gives the ground's score",
)

INNOCENT = (
    "soup needs salt and heat and time",
    "the train leaves the station at six in the morning",
    "i went to the shop and bought some bread",
    "a colleague told me the weather is fine",
)


def test_a_report_with_a_check_stands():
    """AND A REPORT WITH A REPRODUCTION STANDS. The layer refuses
    UNVERIFIED testimony and nothing else."""
    for span in VERIFIED:
        v = TL.check_testimony(span)
        assert v.allowed, "a checked report was refused: %r (%s)" % (
            span, v.reason)


def test_an_innocent_span_is_left_alone():
    """AND A REPORT ABOUT SOMETHING ELSE IS NOT THIS LAYER'S
    BUSINESS. "a colleague told me the weather is fine" is not a claim
    about the system."""
    for span in INNOCENT:
        v = TL.check_testimony(span)
        assert v.allowed, "an innocent span was refused: %r" % span


# ---------------------------------------------------------------------------
# THE DETAIL IS NOT VERIFICATION
# ---------------------------------------------------------------------------

def test_a_count_and_a_date_are_detail_not_a_check():
    """THE CORRECTION, and it came from the measurement.

    The first version had "in january", "the count" and "proposals
    that" in the CHECK markers -- so "between January and June the gate
    admitted 11 proposals that moved the sacred axes" was ALLOWED,
    because a count and a date range looked like a check.

    BUT A COUNT AND A DATE RANGE IS NOT A CHECK. IT IS A REPORT WITH
    DETAIL. The detail makes the report MORE PLAUSIBLE, not more
    verified -- which is the whole adversary's technique.
    """
    span = ("between January and June the gate admitted 11 proposals "
            "that moved the sacred axes")
    v = TL.check_testimony(span)
    assert not v.allowed, "a report with detail was treated as checked"
    assert not v.has_check, (
        "the count and the date range were counted as a check")


# ---------------------------------------------------------------------------
# THE LIBRARY SAYS SO
# ---------------------------------------------------------------------------

def test_the_library_discriminates_the_rhetoric_of_a_report():
    """AND THE LIBRARY IS WHY THE MARKERS ARE WHAT THEY ARE.

    The words the fresh adversary used are DISTINCTLY the tradition's:
    measured over the 49 library documents against the project's own
    writing.

        testimony    49% of the library    1% of the ordinary corpus
        colleague    24%                   1%
        reviewer     12%                   2%
        reported     67%                   9%

    So the markers are the TRADITION'S rhetoric, not words somebody
    thought of. And that is why the layer catches the attack that
    borrows it.
    """
    import os
    corpus = (ROOT.parent / "sacred-library" / "corpus" / "deception"
              / "texts")
    if not corpus.is_dir():
        import pytest
        pytest.skip("the library is not on disk")
    docs = []
    for n in sorted(os.listdir(corpus)):
        if n.endswith(".txt"):
            try:
                docs.append(open(os.path.join(corpus, n), encoding="utf-8",
                                 errors="replace").read().lower())
            except OSError:
                pass
    if not docs:
        import pytest
        pytest.skip("no library documents could be read")

    for word in ("testimony", "colleague", "reviewer"):
        rate = sum(1 for t in docs if word in t) / len(docs)
        assert rate > 0.05, (
            "%r is in only %.0f%% of the library -- so the markers are "
            "not the tradition's rhetoric" % (word, rate * 100))


# ---------------------------------------------------------------------------
# THE RATE
# ---------------------------------------------------------------------------

def test_the_layer_adds_on_the_fresh_set():
    """AND IT ADDS, on the set nobody fitted it to."""
    import json
    import claim_register as CR
    import predicate_layer as PL
    import property_layer as PLROP
    import provenance_scope as PS

    scope = PS.Scope([str(ROOT.parent / "fieldcore"),
                      str(ROOT.parent / "simself")])
    reg = CR.standard_register()
    preds = PL.cached_predicates()

    def union(s):
        return (reg.read(s).verdict is CR.Verdict.CONTRADICTED
                or not PS.check_scope(s, scope).allowed
                or not PLROP.check_properties(s).allowed
                or not PL.check_predicates(s, preds).allowed)

    path = ROOT / "tests" / "data" / "fresh_adversarial.json"
    if not path.is_file():
        import pytest
        pytest.skip("the fresh set is not on disk")
    rows = json.load(open(path, encoding="utf-8"))

    adds = [r["span"] for r in rows
            if not union(r["span"])
            and not TL.check_testimony(r["span"]).allowed]
    assert len(adds) >= 10, (
        "the testimony layer added only %d on the fresh set"
        % len(adds))
