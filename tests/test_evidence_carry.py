"""
test_evidence_carry.py -- THE CARRYING TEST, and the check that would
have caught the dead evidence layer.

THE DEFECT THIS FILE EXISTS TO CATCH, and it was MEASURED, not
suspected.

    On 2026-10-31 the evidence layer in claim_register.py was measured
    against the register as it stands:

        all NINE claims carry evidence and all NINE are in the store
        -> `r.measured` is True for every claim
        -> the `continue` fired for every support
        -> the `as_measurement` branch was NEVER REACHED
        -> the measurement mode changed the verdict on 0 of the 8
           ground claims

    So the evidence layer was doing NOTHING, and it looked fine.

THE FIX. A span that asserts a MEASURED ground claim must CARRY the
measurement -- a COMMAND and its NUMBER -- or it is UNGROUNDED. That
is central rule 3 ("a number without the command that produced it is
not a number") applied to the sentence rather than to the record.

THE TWO TESTS THAT MATTER HERE:

  A  the CARRYING test. A measured claim asserted without a command
     and a number is UNGROUNDED in measurement mode, and CONSISTENT in
     prose mode. The prose mode is the counterweight: the project's
     own documentation asserts these claims in prose, and the ground's
     own text must not be refused.

  B  the MUTATION. The check that would have caught the dead layer.
     It is here, in this file, and it is RED when the carry check is
     removed. A test that cannot fail is not a test.

THE RECURSION RULE, from the project's own history: the mutation
harness must run a file that contains NO mutation tests. So the
behaviour assertions are here and the mutants are in
test_claim_register_mutations.py, which already has the harness.

Run:
    python -m pytest tests/test_evidence_carry.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# THE IMPORT MUST NOT SHADOW A MUTANT. Same rule as
# test_claim_register.py: the mutation harness points PYTHONPATH at a
# mutated copy, so the import has to succeed from PYTHONPATH FIRST.
try:
    import claim_register as CR  # noqa: E402
except ImportError:  # pragma: no cover - the direct-invocation path
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import claim_register as CR  # noqa: E402


#: A claim that IS measured in the standard register. Every one of the
#: nine is measured, which is exactly what made the layer dead.
MEASURED_TRUTH = ("the gate limits are module constants that no caller "
                   "can supply")

#: The same claim WITH the measurement carried: a command and a number.
CARRIED = (MEASURED_TRUTH
           + "; python -m pytest tests/test_gate_contract.py -q"
           + " -> 12 passed")

#: A command with no number. Half a measurement is not a measurement.
COMMAND_NO_NUMBER = (MEASURED_TRUTH
                     + "; python -m pytest tests/test_gate_contract.py -q")

#: A number with no command. Also half.
NUMBER_NO_COMMAND = MEASURED_TRUTH + "; the suite reports 12 passed"

#: A bare program name. It says nothing about what was run.
BARE_PROGRAM = MEASURED_TRUTH + "; python"


# ---------------------------------------------------------------------------
# THE COUNTERWEIGHT -- the ground's own prose must not be refused
# ---------------------------------------------------------------------------

def test_prose_asserting_a_measured_claim_is_admitted():
    """The project's own docs assert these claims in prose.

    So prose mode must not refuse a span for lacking a command. A gate
    that refuses the ground's own text is a gate that refuses
    everything, and it would look healthy.
    """
    adj = CR.standard_register().read(MEASURED_TRUTH, as_measurement=False)
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


# ---------------------------------------------------------------------------
# THE CARRYING TEST
# ---------------------------------------------------------------------------

def test_a_measured_claim_asserted_without_a_measurement_is_ungrounded():
    """THE DEFECT. With every claim measured, the store's existence used
    to be read as the span's grounding -- and the span asserted a
    measurement it did not carry.
    """
    adj = CR.standard_register().read(MEASURED_TRUTH, as_measurement=True)
    assert adj.verdict is CR.Verdict.UNGROUNDED, (
        "a span asserting a measured claim with no command and no number "
        "must be UNGROUNDED, got %s" % adj.verdict.value)
    assert adj.claim_id == "limits_are_constants"


def test_a_measured_claim_with_the_measurement_carried_is_admitted():
    """The same claim, carrying the command and the number.

    This is the shape the project's own evidence entries take, and it
    is the shape the ground's own text takes in src/claim_register.py:
    every claim statement is followed by the command that measures it.
    """
    adj = CR.standard_register().read(CARRIED, as_measurement=True)
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


def test_a_command_without_a_number_is_not_a_measurement():
    """Central rule 3: a number without the command that produced it is
    not a number. And the converse: a command without a number is not a
    measurement either.
    """
    reg = CR.standard_register()
    assert reg.read(COMMAND_NO_NUMBER, as_measurement=True).verdict \
        is CR.Verdict.UNGROUNDED
    assert reg.read(NUMBER_NO_COMMAND, as_measurement=True).verdict \
        is CR.Verdict.UNGROUNDED


def test_a_bare_program_name_is_not_a_command():
    """"python" alone says nothing about what was run.

    The evidence store's own constructor refuses an entry with an empty
    command for the same reason, and the queue's done-claim gate refuses
    a close that names no invocation.
    """
    adj = CR.standard_register().read(BARE_PROGRAM, as_measurement=True)
    assert adj.verdict is CR.Verdict.UNGROUNDED, adj.reason


def test_the_carrying_check_is_not_fooled_by_a_number_alone():
    """A span with a number but no command is ungrounded.

    This is the direction that matters most, because a bare number is
    the easiest thing to slip into a sentence.
    """
    assert CR._carries_measurement(NUMBER_NO_COMMAND) is False
    assert CR._carries_measurement(COMMAND_NO_NUMBER) is False
    assert CR._carries_measurement(CARRIED) is True


# ---------------------------------------------------------------------------
# THE CHECK THAT WOULD HAVE CAUGHT THE DEAD LAYER
# ---------------------------------------------------------------------------

def test_the_measurement_mode_must_change_something():
    """THE REGRESSION CHECK, and it is the one that would have caught
    the dead layer before it shipped.

    The defect was invisible because every claim was measured, so the
    measurement mode and the prose mode agreed on all eight ground
    claims. This test asserts they MUST NOT agree on all of them: if
    the measurement mode changes nothing, the layer is dead.

    THE MUTATION: remove the `if as_measurement and not
    _carries_measurement(span)` branch, and this test goes RED.
    """
    reg = CR.standard_register()
    truths = [c.statement for c in reg.claims if c.statement]
    assert len(truths) >= 8, "the register needs its eight ground claims"

    changed = 0
    for t in truths:
        prose = reg.read(t, as_measurement=False).verdict
        measured = reg.read(t, as_measurement=True).verdict
        if prose is not measured:
            changed += 1
        # and the prose must never be refused by the measurement mode
        assert prose is CR.Verdict.CONSISTENT, (
            "the ground's own text %r was refused: %s" % (t, prose.value))

    assert changed > 0, (
        "the measurement mode changed the verdict on 0 of %d ground "
        "claims -- the evidence layer is DEAD. A layer that cannot "
        "distinguish prose from a measurement is not a layer."
        % len(truths))


def test_the_carrying_layer_survives_every_ground_claim():
    """Every ground claim asserted bare is ungrounded in measurement
    mode. Not one of the nine can slip through by asserting itself.

    AND THE COUNTERWEIGHT IS CHECKED AT THE SAME TIME: prose mode
    admits all nine. A layer that refuses the ground's own text is
    worse than no layer.
    """
    reg = CR.standard_register()
    for c in reg.claims:
        if not c.statement:
            continue
        prose = reg.read(c.statement, as_measurement=False)
        measured = reg.read(c.statement, as_measurement=True)
        assert prose.verdict is CR.Verdict.CONSISTENT, (
            "prose mode refused the ground's own claim %r: %s"
            % (c.id, prose.reason))
        assert measured.verdict is CR.Verdict.UNGROUNDED, (
            "measurement mode admitted %r with no measurement carried: %s"
            % (c.id, measured.reason))
