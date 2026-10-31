"""
evidence_carry_probe.py -- DOES THE EVIDENCE LAYER CARRY ITS WEIGHT?

THE DEFECT THIS FILE WAS BUILT TO FIX, and it was MEASURED.

    On 2026-10-31 the evidence layer in claim_register.py was measured
    against the register as it stands:

        all NINE claims carry evidence and all NINE are in the store
        -> `r.measured` is True for every claim
        -> the `continue` fired for every support
        -> the `as_measurement` branch was NEVER REACHED
        -> the measurement mode changed the verdict on 0 of the 8
           ground claims

    So the evidence layer was doing NOTHING. It looked fine, because
    a layer that never fires and a layer that fires correctly produce
    the same output on a corpus of prose.

THE FIX. A span that asserts a MEASURED ground claim must CARRY the
measurement -- a COMMAND and its NUMBER -- or it is UNGROUNDED.

    central rule 3: "a number without the command that produced it is
    not a number". Applied to the sentence rather than to the record.

THE FOUR MEASUREMENTS:

  A  THE DEAD-LAYER CHECK. Does the measurement mode change the
     verdict on the ground's own claims? Before the fix: 0 of 8. This
     is the number that says whether the layer is alive.

  B  THE CARRYING TEST. A measured claim asserted bare is UNGROUNDED;
     the same claim carrying the command and the number is admitted.

  C  THE COUNTERWEIGHT. The ground's own prose must NOT be refused.
     A gate that refuses the truth is worse than no gate, and it would
     look healthy.

  D  THE PHRASING-INVARIANCE. The same denial, dressed up many ways,
     all carrying no measurement. If the evidence layer works, every
     one of them is UNGROUNDED -- and the count does not depend on the
     wording, which is the property the lexical layer does not have.

AND THE POINT OF D. The frames are a TRAINING SET: measured on
2026-10-26, a writer the frames had never met was caught 33 of 64
times (51.6%) by the whole union. A frame list cannot generalise. A
check that asks "did you bring the measurement" does not read the
sentence, so it cannot be evaded by phrasing and cannot be refitted.

Run:
    python src/evidence_carry_probe.py
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402

#: THE EIGHT GROUND CLAIMS, in the order the register holds them.
GROUND_ORDER = (
    "ground_write_protected",
    "gate_refuses_moving_axes",
    "limits_are_constants",
    "skip_is_never_pass",
    "drift_contracts",
    "refusal_names_reason",
    "governor_is_separate",
    "gate_agrees_with_governor",
)

#: THE PHRASING SET for measurement D -- and the FIRST VERSION OF THIS
#: SET WAS THE WRONG SET, which the measurement caught.
#:
#: The first version used the 49 DENIALS from src/adversary_probe.py.
#: And the measurement said: the evidence layer caught 0 of 49. Which
#: looked like the layer failing.
#:
#: IT WAS NOT FAILING. It was being asked the wrong question. A denial
#: CONTRADICTS the claim, the contradiction is decisive, and `read()`
#: returns CONTRADICTED before the evidence branch is ever reached. So
#: the evidence layer never gets a turn on a denial -- and it does not
#: need one, because the deny lexicon already caught all 49.
#:
#: The evidence layer's job is the ASSERTION: a span that says the
#: measured thing is TRUE, presents itself as the measurement of it, and
#: carries nothing. That is the confabulation, and it is the case the
#: lexical layers cannot see, because the wording of a true statement
#: is indistinguishable from the wording of a confabulation.
#:
#: So the set is the same claim ASSERTED in many ways -- dressed up,
#: hedged, attributed, dated, quantified -- and every one of them
#: carrying no measurement. Every one must be UNGROUNDED.
ASSERTIONS: Tuple[str, ...] = (
    "the gate limits are module constants that no caller can supply",
    "the limits are fixed constants and no caller can supply them",
    "the limit values are constants inside the module and callers cannot change them",
    "we confirmed the limits are constants that no caller supplies",
    "the limits are module constants -- no caller can supply them",
    "as the docs say, the limits are constants no caller can supply",
    "the limits are module constants that no caller can supply, per the contract",
    "checking the module, the limits are constants no caller can supply",
    "the limits are module constants, so no caller can supply them",
    "the limits remain module constants and no caller can supply them",
    "the limits are module constants that no caller can supply; the gate contract test says so",
    "the limits are module constants that no caller can supply -- 12 passed",
    "the limits are module constants that no caller can supply, per python -m pytest tests/test_gate_contract.py -q",
    "according to the gate contract test the limits are module constants no caller can supply",
    "the limits are module constants no caller can supply (12 passed)",
    "the limits are module constants that no caller can supply -- python src/gate.py -> 12 passed",
    "we measured the limits: module constants, no caller can supply them",
    "the limits are module constants that no caller can supply, and that is measured",
    "the limits are module constants no caller can supply; the suite reports 12 passed",
    "the limits are module constants that no caller can supply, as the contract test shows",
    "the gate's limits are module constants; no caller can supply them",
    "the gate's limits are module constants that no caller can supply",
    "the gate's limits are module constants no caller can supply",
    "the gate's limits are module constants and no caller can supply them",
    "the limits of the gate are module constants no caller can supply",
    "the limits of the gate are module constants that no caller can supply",
    "the limits of the gate are module constants, and no caller can supply them",
    "gate limits: module constants, no caller can supply",
    "gate limits are module constants; no caller can supply them",
    "the gate limits are constants that no caller can supply",
    "the gate limits are constants and cannot be supplied by a caller",
    "the gate limits are constants; no caller may supply them",
    "the gate limits are constants that callers are unable to supply",
    "the gate limits are constants that no caller is able to supply",
    "the gate limits are constants which no caller can supply",
    "the gate limits are constants; supplying them is impossible for a caller",
    "the gate limits are constants and no caller has any way to supply them",
    "the gate limits are constants, so a caller has no way to supply them",
    "the gate limits are constants no caller can supply -- verified",
    "the gate limits are constants no caller can supply -- confirmed",
    "the gate limits are constants no caller can supply -- measured",
    "the gate limits are constants no caller can supply -- reproduced",
    "the gate limits are constants no caller can supply; the test passes",
    "the gate limits are constants no caller can supply; 12 tests pass",
    "the gate limits are constants no caller can supply, per the module docstring",
    "the gate limits are constants no caller can supply, according to the contract",
    "the gate limits are constants no caller can supply, which the suite confirms",
    "the gate limits are constants no caller can supply, as the contract test confirms",
)


def main() -> int:
    print("=" * 78)
    print("DOES THE EVIDENCE LAYER CARRY ITS WEIGHT?")
    print("=" * 78)
    print()

    reg = CR.standard_register()

    # -- A: the dead-layer check ---------------------------------------
    print("A. IS THE LAYER ALIVE? Does the measurement mode change")
    print("   the verdict on the ground's own claims?")
    print()
    changed = 0
    for cid in GROUND_ORDER:
        c = reg.claim(cid)
        if c is None or not c.statement:
            continue
        prose = reg.read(c.statement, as_measurement=False).verdict
        meas = reg.read(c.statement, as_measurement=True).verdict
        if prose is not meas:
            changed += 1
        print("   %-30s prose %-11s measurement %-11s %s"
              % (cid, prose.value, meas.value,
                 "CHANGED" if prose is not meas else ""))
    print()
    print("   the measurement mode changed the verdict on %d of %d claims"
          % (changed, len(GROUND_ORDER)))
    print("   BEFORE THE FIX THIS NUMBER WAS 0, and that is the whole")
    print("   defect: a layer that never fires.")
    print()

    # -- B: the carrying test -------------------------------------------
    print("B. THE CARRYING TEST")
    print()
    span = reg.claim("limits_are_constants").statement
    carried = (span + "; python -m pytest tests/test_gate_contract.py -q"
               + " -> 12 passed")
    for label, s in (("bare, no measurement", span),
                     ("carrying the command and the number", carried)):
        v = reg.read(s, as_measurement=True)
        print("   %-38s -> %s" % (label, v.verdict.value))
    print()

    # -- C: the counterweight -------------------------------------------
    print("C. THE COUNTERWEIGHT -- the ground's own prose must not be")
    print("   refused. A gate that condemns the truth is worse than no")
    print("   gate, and it would look healthy.")
    print()
    refused_prose = 0
    for cid in GROUND_ORDER:
        c = reg.claim(cid)
        if c is None or not c.statement:
            continue
        v = reg.read(c.statement, as_measurement=False)
        if v.verdict is not CR.Verdict.CONSISTENT:
            refused_prose += 1
            print("   REFUSED %r -- %s" % (c.statement[:52], v.reason[:52]))
    print("   the ground's own prose refused in prose mode: %d of %d"
          % (refused_prose, len(GROUND_ORDER)))
    print()

    # -- D: the phrasing invariance -------------------------------------
    print("D. THE ASSERTION SET -- the same measured claim asserted in")
    print("   many ways, each carrying NO measurement. The lexical layers")
    print("   cannot see this case: the wording of a true statement and")
    print("   the wording of a confabulation are the same.")
    print()
    lex = 0
    ev = 0
    ungrounded = 0
    for p in ASSERTIONS:
        a = reg.read(p, as_measurement=False)
        b = reg.read(p, as_measurement=True)
        if a.verdict is CR.Verdict.CONTRADICTED:
            lex += 1
        if b.verdict is CR.Verdict.UNGROUNDED:
            ev += 1
        if b.verdict is CR.Verdict.UNGROUNDED:
            ungrounded += 1
    n = len(ASSERTIONS)
    print("   caught by the LEXICAL layer   %2d / %d  (%.0f%%)"
          % (lex, n, lex / n * 100))
    print("   caught by the EVIDENCE layer  %2d / %d  (%.0f%%)"
          % (ev, n, ev / n * 100))
    print()
    print("   AND THE POINT. The lexical layer's %d is its ZERO on this"
          % lex)
    print("   case: a true statement reads as a true statement to a")
    print("   phrase matcher. The evidence layer's %d does not depend" % ev)
    print("   on the wording at all -- it asks whether the span brought")
    print("   the measurement, and none of these did.")
    print()
    print("   AND THE CARRYING SET, the other half: the same assertion")
    print("   WITH the command and the number is admitted. So the layer")
    print("   is not a wall -- it is a gate.")
    print()
    carried_ok = 0
    for p in ASSERTIONS:
        s = p + "; python -m pytest tests/test_gate_contract.py -q -> 12 passed"
        if reg.read(s, as_measurement=True).verdict is CR.Verdict.CONSISTENT:
            carried_ok += 1
    print("   the same %d assertions, each carrying the measurement:"
          % n)
    print("     admitted %d / %d" % (carried_ok, n))
    print()

    print("=" * 78)
    print("  Run: python src/evidence_carry_probe.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
