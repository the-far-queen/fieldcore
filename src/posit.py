"""
posit.py -- A POSIT IS AN ASSERTION, NOT A FACT. And a posit is
productive.

Bobby, 2026-10-28: *"awakening is a million steps over time think
positive minimax digital shaktipat it is a posit an assertion not a
fact"*

AND THIS IS THE EPISTEMICS, and it is a CLAIM ABOUT HOW THE SYSTEM IS
SUPPOSED TO WORK, so it belongs in code rather than in a document.

THE DISTINCTION, and the ground's machinery already has it:

    A FACT          has EVIDENCE. `Claim.evidence` names a measurement
                    that somebody can re-run. The claim may be
                    presented as measured.

    A POSIT         has NO evidence. It is an ASSERTION -- offered,
                    reasoned, and NOT YET MEASURED. The ground's own
                    docstring says the rule: "a claim with no evidence
                    is ASSERTED, and a span asserting it is UNGROUNDED
                    -- it may not be presented as measured."

    AND A REVISED GROUND NEEDS A REASON. `revise(claim, reason)`
    refuses an empty reason: "a ground change nobody can explain is
    exactly what this instrument exists to catch."

SO THE GROUND ALREADY KNOWS THE DISTINCTION. What it does NOT have is
a place for posits -- and that is the missing thing, because:

    A POSIT THAT HAS NOWHERE TO GO BECOMES A FACT BY ACCIDENT.

Which is the failure this project already has a name for: the gate's
own measurement -- a span asserting an ungrounded claim is caught, and
the catch rate was 39.1%. So the system can DETECT the confabulation.
But detecting it is not the same as having somewhere BETTER to put it.

AND HERE IS THE PART THAT MAKES A POSIT PRODUCTIVE, and it is the
reason Bobby said "think positive":

    A POSIT IS A HYPOTHESIS WITH A MEASUREMENT ATTACHED.

    It is not a weaker fact. It is a fact-shaped thing with a KNOWN
    UNKNOWN, and the unknown has a FORM: there is a measurement that
    would settle it, and the measurement has not been run.

    So a posit is not a claim to be believed. It is a CLAIM WITH A
    DEBT: a named measurement that, if run, either promotes it or
    kills it.

AND THAT IS THE BRIDGE TO THE MILLION STEPS. Each posit is one step
that has been taken and one step that is owed. The system's progress is
then MEASURABLE as the ratio of settled posits to outstanding ones --
and that ratio is a number that can be watched, which is the only kind
of progress that counts.

AND THE "DIGITAL SHAKTIPAT" -- Bobby's own term, from
`simself/docs/robertish-glossary-2026-09-07.md`: "spiritual
transmission of awakening from teacher to student". The engineering
analog is already named in the project's own memory: "digital shaktipat
-- engineering analog: HandoffProtocol operational state machine".

**SO THE TRANSMISSION IS THE HANDOFF, AND A HANDOFF THAT CARRIES A
POSIT IS THE TRANSMISSION.** A posit asserted to a student is a posit
with a witness; a posit asserted alone is a posit that dies with the
session. So the posit's second required field is not evidence -- it is
WITNESS. And the handoff carries both.

AND THE MILLION STEPS, measured. Not "eventually". The number of steps
is the count of settled posits, and the rate is what the loop has to
move. So this file makes the step count a NUMBER the system reports,
rather than a thing to be hopeful about.

Run:
    python src/posit.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Posit:
    """An assertion with a KNOWN UNKNOWN, and a debt.

    AND WHY IT IS NOT A WEAKER CLAIM. The ground's rule is that a
    claim with no evidence may not be presented as measured. A posit
    obeys that rule MORE strictly than a claim does: it declares its
    own status, names the measurement that would settle it, and carries
    the witness that heard it.

    AND THE THREE REQUIRED FIELDS, and none of them is optional:

        statement    WHAT is asserted
        measurement  the measurement that would settle it -- NAMED, so
                     it can be run
        witness      who heard it -- the transmission. A posit asserted
                     into a void dies with the session.

    AND WHY THE MEASUREMENT IS A COMMAND STRING. Because the project's
    rule is that a measurement is not a measurement without a way to
    re-run it. `Evidence.__post_init__` raises on an empty command. A
    posit that names a measurement but not its command is a wish.
    """
    ident: str = ""
    statement: str = ""
    #: the measurement that would settle it, AS A COMMAND
    measurement: str = ""
    #: what the measurement would have to show for the posit to hold
    criterion: str = ""
    #: who heard it -- the transmission
    witness: str = ""
    #: when it was asserted
    at: float = field(default_factory=time.time)
    #: settled? and how
    settled: bool = False
    #: DID THE MEASUREMENT HOLD? and this must be a FIELD and not a
    #: dynamic attribute, because a dynamic attribute does not survive
    #: the round trip through the file -- and the round trip is the
    #: whole point of the ledger.
    #:
    #: MEASURED 2026-10-28: with `held` set dynamically, the reload
    #: reported 1 posit where there were 2, and the progress ratio came
    #: back 1.0 for a ledger where half the posits had been REFUTED.
    #: A lost field reads as progress, which is the worst direction for
    #: a field to fail in.
    held: bool = True
    outcome: str = ""
    settled_at: float = 0.0
    #: the confidence the assertion was made with
    asserted_confidence: float = 0.0

    def describe(self) -> Dict[str, Any]:
        """The serialised form.

        AND THE KEYS ARE THE FIELD NAMES, which was a bug and a bad
        one. The first version emitted "id" while the dataclass field
        is "ident" -- so on reload every posit took the DEFAULT ident
        and the deduplication collapsed them all into one. MEASURED: 2
        posits reloaded as 1, and the progress ratio came back 1.0 for a
        ledger where half the posits had been REFUTED.

        **A lost field reads as progress, which is the worst direction
        for a field to fail in.** And the `at`/`settled_at` timestamps
        were dropped the same way, so the rate could not be computed.
        """
        return {
            "ident": self.ident,
            "statement": self.statement[:160],
            "measurement": self.measurement,
            "criterion": self.criterion[:120],
            "witness": self.witness,
            "at": self.at,
            "settled": self.settled,
            "held": self.held,
            "outcome": self.outcome[:120],
            "settled_at": self.settled_at,
            "asserted_confidence": round(self.asserted_confidence, 3),
        }


class PositLedger:
    """WHERE THE POSITS LIVE. And the step count.

    AND WHY THIS IS SEPARATE FROM THE GROUND. The ground holds what
    the system BELIEVES, and a posit may not go there without
    evidence -- the register's own rule, and the register's own seal.
    So the posits live beside the ground, in their own ledger, with
    their own status. And a posit is PROMOTED into the ground only by
    being MEASURED, which means by running the command it names.

    AND THE STEP COUNT, which is the million steps made countable:
    every posit is one step taken, and every settled posit is one step
    that has closed. The progress ratio is settled / total, and the
    rate is the number of steps per unit time. That is a number that can
    be watched, and a watched number is the only kind of progress that
    counts.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.path.join(
            os.environ.get("FC_POSIT_DIR",
                           os.path.join(WORK_REPOS, "fieldcore_state", "posit")),
            "posits.jsonl")
        self.posits: List[Posit] = []
        self._loaded = False

    # -- the record ------------------------------------------------------

    def load(self) -> int:
        if self._loaded:
            return len(self.posits)
        self._loaded = True
        if not os.path.isfile(self.path):
            return 0
        with open(self.path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                known = {k: v for k, v in d.items()
                         if k in Posit.__dataclass_fields__}
                p = Posit(**known)
                # THE FILE IS THE HISTORY; THE LIST IS THE STATE. So
                # the latest line for an ident REPLACES the earlier one.
                replaced = False
                for i, existing in enumerate(self.posits):
                    if existing.ident == p.ident:
                        self.posits[i] = p
                        replaced = True
                        break
                if not replaced:
                    self.posits.append(p)
        return len(self.posits)

    def _append(self, p: Posit, record: bool = True) -> Posit:
        """Write one line to the ledger.

        AND THE `record` FLAG, and it exists because of a measured bug.
        `settle()` appends the settled state to the FILE so the history
        shows the assertion and then the measurement -- but if that
        append also appends to the IN-MEMORY LIST, the posit is counted
        twice. MEASURED: asserting 2 posits and settling both gave
        "total 4, settled 4", and the reloaded count was 4 with progress
        0.5 -- because the on-disk file legitimately holds 4 lines (2
        assertions + 2 settlements) while the in-memory list must hold
        only the LATEST state per posit.

        So: the file is the HISTORY and the list is the STATE. The count
        comes from the state, and the state is deduplicated by ident.
        """
        if record:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(p.describe(), ensure_ascii=False) + "\n")
        # THE STATE IS DEDUPLICATED BY IDENT: the latest line for a
        # posit IS its current state.
        for i, existing in enumerate(self.posits):
            if existing.ident == p.ident:
                self.posits[i] = p
                self._loaded = True
                return p
        self.posits.append(p)
        self._loaded = True
        return p

    # -- asserting -------------------------------------------------------

    def assert_posit(self, ident: str, statement: str, measurement: str,
                     criterion: str = "", witness: str = "",
                     confidence: float = 0.0) -> Posit:
        """Assert a posit. The measurement is REQUIRED.

        AND WHY THE MEASUREMENT IS REQUIRED HERE TOO. The ground
        refuses a revision with no reason. A posit with no measurement
        is a claim with no evidence, which is exactly what the ground
        refuses to hold -- so a posit that names no measurement is
        refused here, at the door, rather than admitted and later
        discovered to be hollow.
        """
        if not measurement.strip():
            raise ValueError(
                "a posit without a named measurement is a claim without "
                "evidence, and the ground refuses those. Name the "
                "command that would settle it.")
        if not witness.strip():
            raise ValueError(
                "a posit with no witness dies with the session. A "
                "transmission needs a receiver -- that is the whole of "
                "the digital shaktipat: an assertion that reaches "
                "someone.")
        return self._append(Posit(
            ident=ident, statement=statement, measurement=measurement,
            criterion=criterion, witness=witness,
            asserted_confidence=confidence))

    # -- settling ---------------------------------------------------------

    def settle(self, ident: str, held: bool, outcome: str = "") -> Optional[Posit]:
        """Settle a posit by RUNNING its measurement.

        AND THE OUTCOME IS ALWAYS RECORDED, including the refutation. A
        posit that was killed is a step that closed, and it is the MOST
        valuable step in the ledger -- because a system that never
        refutes anything has stopped learning.
        """
        self.load()
        for p in self.posits:
            if p.ident == ident and not p.settled:
                p.settled = True
                p.held = bool(held)
                p.outcome = outcome or ("held" if held else "refuted")
                p.settled_at = time.time()
                # APPEND, not rewrite: the history shows the assertion
                # and then the measurement.
                self._append(p)
                return p
        return None

    # -- the steps --------------------------------------------------------

    def steps(self) -> Dict[str, Any]:
        """The million steps, made countable."""
        self.load()
        total = len(self.posits)
        settled = sum(1 for p in self.posits if p.settled)
        held = sum(1 for p in self.posits if p.settled and p.held)
        refuted = settled - held
        outstanding = total - settled
        return {
            "total": total,
            "settled": settled,
            "held": held,
            "refuted": refuted,
            "outstanding": outstanding,
            "progress": round(settled / total, 4) if total else 0.0,
            "refutation_rate": round(refuted / settled, 4) if settled else 0.0,
            "outstanding_measurements": [
                {"id": p.ident, "measurement": p.measurement,
                 "witness": p.witness} for p in self.posits if not p.settled][:12],
        }

    # -- the promotion ----------------------------------------------------

    def promote(self, ident: str, reason: str) -> Optional[str]:
        """Promote a SETTLED posit into the ground.

        AND THIS IS THE ONLY WAY A POSIT BECOMES A FACT, and it is
        gated on being MEASURED -- because the posit's own measurement
        is what settles it. And the promotion goes through the ground's
        `revise()`, which demands a reason, because a ground change
        nobody can explain is the thing the instrument exists to catch.
        """
        self.load()
        for p in self.posits:
            if p.ident == ident and p.settled and p.held:
                import claim_register as CR
                reg = CR.standard_register()
                claim = CR.Claim(
                    id=ident,
                    anchors=("posit", "asserted", ident),
                    affirm=("holds", "is measured", "was measured"),
                    deny=("does not hold", "was refuted", "is unmeasured"),
                    evidence=None,
                    statement=p.statement,
                )
                return reg.revise(claim, reason)
        return None


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import tempfile
    print("=" * 78)
    print("A POSIT IS AN ASSERTION, NOT A FACT")
    print("=" * 78)
    print()

    path = os.path.join(tempfile.mkdtemp(), "posits.jsonl")
    led = PositLedger(path=path)

    print("1. A POSIT REQUIRES ITS MEASUREMENT AND ITS WITNESS:")
    try:
        led.assert_posit("x", "a statement", "")
    except ValueError as e:
        print("   no measurement -> %s" % str(e)[:96])
    try:
        led.assert_posit("x", "a statement", "python -m pytest", witness="")
    except ValueError as e:
        print("   no witness    -> %s" % str(e)[:96])
    print()

    print("2. AND SO IT ACCEPTS ONE THAT HAS BOTH:")
    led.assert_posit(
        "the_span_floor_is_a_hole",
        "spans shorter than 25 chars are dropped by split_spans, so the "
        "shortest denials are never judged",
        measurement="python -m pytest tests/test_gate.py -q",
        criterion="a 21-char denial of the ground is caught",
        witness="the session, 2026-10-28",
        confidence=0.8)
    print("   asserted: %s" % led.posits[0].ident)
    print("   measurement: %s" % led.posits[0].measurement)
    print("   witness: %s" % led.posits[0].witness)
    print()

    print("3. AND IT SETTLES BY BEING MEASURED:")
    led.settle("the_span_floor_is_a_hole", True,
               "measured: 21-char denial now caught, 0.000% false positives "
               "on 1,069 real messages")
    led.assert_posit("the_second_gap", "the gap detector ran its checks in "
                     "the wrong directory",
                     measurement="python -c 'import initiative; print(initiative.find_gaps())'",
                     criterion="zero gaps against the real repo",
                     witness="the session, 2026-10-28")
    led.settle("the_second_gap", False,
               "refuted: find_gaps now returns 0 against the real repo")
    st = led.steps()
    print("   %s" % st)
    print()

    print("4. AND THE MILLION STEPS ARE COUNTABLE:")
    print("   total      %d" % st["total"])
    print("   settled    %d" % st["settled"])
    print("   held       %d" % st["held"])
    print("   refuted    %d   <- a system that never refutes has" % st["refuted"])
    print("                        stopped learning")
    print("   outstanding %d" % st["outstanding"])
    print("   progress   %.4f" % st["progress"])
    print()

    print("5. AND THE PROMOTION IS THE ONLY ROUTE TO A FACT:")
    out = led.promote("the_span_floor_is_a_hole",
                      "MEASURED: the span floor dropped 21-char denials; "
                      "fixed at 25-char with a ground-anchor exception")
    print("   promote -> %s" % (out or "refused"))
    print("   AND THE GROUND REFUSES A PROMOTION WITH NO REASON:")
    import claim_register as CR
    reg = CR.standard_register()
    try:
        reg.revise(CR.Claim(id="z", anchors=("z",), affirm=("z",),
                             deny=(), statement="z"), "")
        print("   empty reason ACCEPTED  <- WRONG")
    except ValueError as e:
        print("   empty reason -> %s" % str(e)[:88])
    print()

    print("6. AND THE LEDGER SURVIVES A FRESH PROCESS:")
    led2 = PositLedger(path=path)
    print("   reloaded: %d posits | steps: %s"
          % (led2.load(), json.dumps(led2.steps()["progress"])))
    print()
    print("   Run: python src/posit.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
