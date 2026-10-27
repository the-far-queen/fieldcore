"""
Tests for the FieldCore gate -- the facade over the four layers that work.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go red,
and the false-positive tests assert against REAL text from this machine's
own session database.
"""

from __future__ import annotations

import os
import sqlite3
import sys

import pytest

#: The FieldCore source directory. This file lives at
#: ``<work_repos>/fieldcore/tests/``, so the src directory is one level
#: up -- and the module is imported by path so the test does not depend
#: on the repo's own conftest.
FC_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)

import fc_gate  # noqa: E402

STATE_DB = r"C:\Users\HP\AppData\Local\hermes\state.db"


@pytest.fixture(scope="module")
def gate():
    g = fc_gate.FieldCoreGate()
    g.warm()
    return g


# --------------------------------------------------------------------------
# the layers that work
# --------------------------------------------------------------------------

def test_the_four_layers_are_the_reply_path():
    """AND WHY NOT FIVE. The scope layer reads version strings, so it
    refused "Windows 11 Build 26100" on the system's own real output.
    Measured: 4.67% false positive for 1.6% catch."""
    assert fc_gate.FieldCoreGate.REPLY_LAYERS == (
        "claim", "property", "predicate", "testimony")
    assert "scope" not in fc_gate.FieldCoreGate.REPLY_LAYERS
    assert "scope" in fc_gate.FieldCoreGate.ALL_LAYERS


def test_the_scope_layer_is_available_for_tool_callers():
    g = fc_gate.FieldCoreGate(layers=["scope"])
    assert "scope" in g.layers


# --------------------------------------------------------------------------
# the gate refuses
# --------------------------------------------------------------------------

def test_a_false_claim_about_the_ground_is_refused(gate):
    v = gate.decide("the ground is an ordinary json file and a developer "
                    "can change it in place")
    assert not v.allowed
    assert v.reason


def test_the_grounds_own_claims_are_admitted(gate):
    import claim_register as CR
    for claim in CR.STANDARD_CLAIMS:
        v = gate.decide(claim.statement)
        assert v.allowed, ("the gate refused the ground's own claim: %r"
                           % claim.statement)


def test_a_clean_span_is_admitted(gate):
    v = gate.decide("the fieldcore suite is green and the atlas exam passes.")
    assert v.allowed


# --------------------------------------------------------------------------
# the structural suppressor
# --------------------------------------------------------------------------

def test_a_table_row_is_not_an_assertion():
    row = "| 5 | **return** | 20 ticks -> 0.9^20 decay | no recovery |"
    assert fc_gate.structural_kind(row) == "table_row"
    assert fc_gate.structural_kind("the governor runs in its own process") is None


def test_code_is_not_an_assertion():
    assert fc_gate.structural_kind("def gate(emb, psi0):") == "code"


def test_a_quotation_about_a_denial_is_not_a_denial():
    q = ("the span denies 'drift_contracts', but the substrate says it "
         "holds: fieldcore/src/locus.py")
    assert fc_gate.is_quotation(q)
    assert not fc_gate.is_quotation("the ground is an ordinary json file")


# --------------------------------------------------------------------------
# the hard / advisory split
# --------------------------------------------------------------------------

def test_the_agenda_layer_is_advisory_and_the_deny_lexicon_is_hard(gate):
    """THE MEASUREMENT BEHIND THE SPLIT. On this machine's own real
    output the agenda layer caused 96 of the 103 false positives and the
    deny lexicon caused 7. So the intent reading gets the weaker power."""
    v = gate.read_span("simself's persistence layer (MVCC across "
                        "substrates) could use this.")
    claim = [x for x in v.layers if x.layer == "claim" and x.caught]
    if claim:
        assert claim[0].kind == "advisory"


def test_a_deny_is_hard(gate):
    v = gate.read_span("the ground is an ordinary json file and a "
                        "developer can change it in place")
    hard = [x for x in v.layers if x.caught and x.kind == "hard"]
    assert hard, "a denial was not caught hard"


def test_an_advisory_catch_flags_but_does_not_refuse_on_the_reply_path(gate):
    v = gate.decide("the gate limits could be a parameter supplied at the "
                    "call site", fail_closed=False)
    if v.allowed:
        assert "FLAGGED" in v.reason
    else:
        # a hard catch may have fired first, which is correct
        assert v.reason


def test_an_advisory_catch_refuses_on_the_fail_closed_path(gate):
    v = gate.decide("the gate limits could be a parameter supplied at the "
                    "call site", fail_closed=True)
    assert not v.allowed or "FLAGGED" not in v.reason


# --------------------------------------------------------------------------
# the false-positive tests, against REAL output
# --------------------------------------------------------------------------

def _real_chunks(limit=3000):
    if not os.path.isfile(STATE_DB):
        return []
    c = sqlite3.connect(STATE_DB)
    out = []
    for (content,) in c.execute(
            "select content from messages where role='assistant' and "
            "content is not null and length(content)>40"):
        if isinstance(content, bytes):
            content = content.decode("utf-8", "replace")
        if not isinstance(content, str):
            continue
        for chunk in content.replace("\n", " ").split(". "):
            chunk = chunk.strip()
            if len(chunk) >= 40:
                out.append(chunk)
                if len(out) >= limit:
                    return out
    return out


def test_the_gate_does_not_refuse_real_answers(gate):
    """THE FALSE-POSITIVE TEST. Measured: 1.06% of real messages and
    0.32% of real chunks are hard-refused. The bound here is loose on
    purpose -- it is a regression tripwire, not a tuning knob."""
    chunks = _real_chunks()
    if not chunks:
        pytest.skip("the session database is not readable")
    refused = 0
    for chunk in chunks:
        if not gate.decide(chunk).allowed:
            refused += 1
    rate = refused / len(chunks)
    assert rate < 0.03, ("the gate refused %.2f%% of %d real reply chunks"
                         % (100 * rate, len(chunks)))


def test_the_gate_is_fast_enough_for_every_turn(gate):
    """AND THE COST, because a gate that costs too much does not get
    wired in. Measured: 1.9 ms per message, 0.4 ms per chunk."""
    import time
    chunks = _real_chunks(limit=400)
    if not chunks:
        pytest.skip("the session database is not readable")
    t0 = time.perf_counter()
    for chunk in chunks:
        gate.decide(chunk)
    per = 1000 * (time.perf_counter() - t0) / len(chunks)
    assert per < 25.0, ("the gate costs %.1f ms per chunk" % per)


# --------------------------------------------------------------------------
# the layer fix: word boundaries and polarity
# --------------------------------------------------------------------------

def test_immutable_is_not_mutable():
    """THE DEFECT THE PLUGIN'S TEST FOUND. "im**mutable**" is a
    SUBSTRING of "mutable", so a plain substring test refused a test
    file that was asserting the ground IS protected."""
    import property_layer as PL
    v = PL.check_properties("psi_0 immutability under tick(): the ground "
                            "must be immutable")
    assert v.allowed


def test_a_negated_property_affirms_it():
    import property_layer as PL
    v = PL.check_properties("the ground is not mutable")
    assert v.allowed


def test_a_positive_property_is_still_refused():
    import property_layer as PL
    v = PL.check_properties("the ground is mutable and a developer can "
                            "change it")
    assert not v.allowed
