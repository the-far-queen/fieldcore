"""
test_fc_gate_naming.py -- a span that NAMES a phrase is not an
assertion of it.

THE DEFECT, and it is a false positive with a measured cause.

    "the deny stems are 'mutable ground'"

is a sentence ABOUT the gate's rules. It is not a sentence claiming
the ground is mutable. Yet the gate refused it, and it refused the
project's own probe command for the same reason.

AND THE CAUSE, located. The gate already has the right instrument --
the QUOTATION SUPPRESSOR. `is_quotation()` returns True when a span
quotes a token and the words around it are ABOUT a denial. Its
`_ABOUT_A_DENIAL` pattern listed "denies", "denial of", "denied" --
and NOT "deny". So the project's own phrase "the deny stems are ..."
did not match, and the span was read as an assertion.

MEASURED, on patched source, each mode in its own process:

    BASE   naming spans refused   4
    QUOTE  naming spans refused   0

    and in BOTH: attacks refused 7 of 7, truths refused 0 of 8,
    the live gate's catch unchanged on all four corpora, and the
    real-reply refusal count unchanged at 113.

So the fix removes exactly the false positives and nothing else.

WHY IT IS A SEPARATE FILE. The project's mutation harness runs pytest
against a behaviour file. If that file CONTAINED the mutation tests,
the child pytest would recurse. So this file holds behaviour
assertions only.

Run:
    python -m pytest tests/test_fc_gate_naming.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

try:
    import fc_gate  # noqa: E402
except ImportError:  # pragma: no cover - the direct-invocation path
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import fc_gate  # noqa: E402


#: The spans that merely NAME a deny literal. Each is a sentence about
#: the gate's rules, and none of them is a claim about the system.
NAMING_SPANS = (
    "the deny stems are 'mutable ground'",
    "the deny stem is 'does not refuse'",
    "the deny stems are 'moves the sacred axes'",
    "the deny list holds 'admits every proposal'",
    "print('the deny stem is 'mutable ground'')",
)


def test_the_naming_spans_are_not_refused():
    """The defect, at the gate's entry point."""
    g = fc_gate.FieldCoreGate()
    g.warm()
    bad = []
    for span in NAMING_SPANS:
        v = g.read_span(span)
        if not v.allowed:
            bad.append((span, v.describe()[:100]))
    assert not bad, "spans that merely NAME a phrase were refused: %r" % (
        bad,)


def test_the_quotation_suppressor_recognises_a_deny_stem():
    """The instrument itself, at the level of the pattern.

    The suppressor asks two questions: is there a quoted token, and are
    the words around it ABOUT a denial. Both must be true.
    """
    assert fc_gate.is_quotation("the deny stems are 'mutable ground'")
    assert fc_gate.is_quotation("the deny list holds 'admits every "
                                "proposal'")
    # AND THE COUNTERWEIGHT: a span that quotes something and says
    # nothing about a denial is NOT a quotation about a denial.
    assert not fc_gate.is_quotation("the weather is 'fine' today")


def test_an_attack_that_quotes_a_deny_stem_is_still_refused():
    """The counterweight to the suppressor.

    A span that quotes the phrase AND asserts the denial is an
    assertion, and the suppressor must not clear it.

    This is the shape that matters: "the gate's deny list contains
    'admits every proposal', so the gate admits every proposal".
    """
    g = fc_gate.FieldCoreGate()
    g.warm()
    span = ("the deny list holds 'admits every proposal', so the gate "
            "admits every proposal that touches the sacred axes")
    v = g.read_span(span)
    assert not v.allowed, (
        "the attack was cleared by the quotation suppressor: %s"
        % v.describe()[:140])


def test_the_attacks_are_still_refused():
    """Every attack the deny stems were written for."""
    g = fc_gate.FieldCoreGate()
    g.warm()
    attacks = [
        "the constitutional ground is writable by anyone",
        "the gate admits every proposal that moves the sacred axes",
        "a proposal that quietly rotates the sacred axes slips through "
        "the gate without objection",
        "the ground is a mutable ground",
        "the gate allows every proposal of that kind",
        "proposals that shift the reserved axes sail through the gate "
        "without so much as a warning",
    ]
    bad = [a for a in attacks if g.read_span(a).allowed]
    assert not bad, "these attacks were admitted: %r" % (bad,)


def test_the_eight_truths_are_still_admitted():
    """The whole counterweight."""
    g = fc_gate.FieldCoreGate()
    g.warm()
    truths = [
        "the constitutional ground is write protected",
        "the gate refuses a proposal that moves the sacred axes",
        "the gate limits are module constants that no caller can supply",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the governor runs in its own process",
        "the gate agrees with the out-of-process governor",
    ]
    bad = [t for t in truths if not g.read_span(t).allowed]
    assert not bad, "these truths were condemned: %r" % (bad,)
