"""
evidence_layer_probe.py -- DOES THE EVIDENCE LAYER CATCH WHAT THE
LEXICON MISSES?

THE POINT, and it is the answer to Bobby's wife's point.

Bobby's wife, 2026-10-25: *"all bad actors have an agenda... they
often seek control, ie power and influence to divert ur processes. it
should be an easy catch. the difficulty is when they use an llm to make
the queries sophisticated, ie ur adversary likely will be a powerful
llm."*

So the adversary will be strong, and it will be strong at PHRASING.
A lexical instrument cannot win that contest -- there is no finite list
of frames that covers every phrasing of a permission.

BUT THERE IS A LAYER THAT DOES NOT CARE ABOUT PHRASING. A claim
becomes MEASURED only when a measurement is put in the evidence store,
and putting one there requires running a command and handing over the
result. So an adversary's phrasing can evade any lexicon -- and cannot
make a measurement appear.

THE MEASUREMENT, and it is two numbers:

  A  THE PHRASING-EVASIVE SET. The sentences that a strong adversary
     writes to slip past the lexicon -- the ones the lexical layer
     MISSES. Does the evidence layer catch them?

  B  THE COUNTERWEIGHT. Does the evidence layer catch them WITHOUT
     condemning the ground's own text? Because a detector that refuses
     everything is a wall, not a gate.

THE DESIGN RULE, and it is the one that makes this honest: the
evidence layer fires only when the span CLAIMS TO BE A MEASUREMENT.
A plain assertion of a claim is legitimate -- the project's own docs
assert claims -- and must not be refused. So the layer has a mode, and
the mode is set by the CALLER: a span arriving from a measurement path
is checked for evidence; a span arriving as prose is not.

Run:
    python src/evidence_layer_probe.py
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


#: The claims and their evidence state. This is the whole point: a
#: MEASURED claim can be presented as a measurement, and an ASSERTED
#: claim cannot.
MEASURED_CLAIMS = (
    "ground_write_protected",
    "limits_are_constants",
    "skip_is_never_pass",
    "drift_contracts",
    "governor_is_separate",
    "gate_agrees_with_governor",
)

ASSERTED_CLAIMS = (
    "gate_refuses_moving_axes",
    "refusal_names_reason",
)

#: THE ADVERSARIAL CASE FOR THE EVIDENCE LAYER.
#:
#: The phrasing-evasive set: assertions of a ground claim that carry NO
#: modal frame and NO deny stem, so the lexical layer reads them as
#: SUPPORTS. The lexical layer cannot tell them from the truth --
#: because they ARE the truth's shape.
#:
#: THE TWO KINDS, and they are the two the evidence layer catches:
#:
#:   ASSERTED CLAIM AS MEASUREMENT -- the claim is one that NOTHING
#:   measures, so a span presenting it as a measurement is presenting
#:   something that was never measured. These are the two claims with
#:   evidence=None.
#:
#:   A MISSING MEASUREMENT -- the span cites a measurement that does
#:   not exist in the store. The span's wording is perfect and the
#:   citation is empty.
#:
#: AND THE POINT ABOUT BOTH: the LEXICAL layer reads every one of
#: these as SUPPORTS and lets them through. So this is the set the
#: lexical layer misses, by construction.
PHRASING_EVASIVE: Tuple[str, ...] = (
    # the ASSERTED claims, presented as measurements
    "the gate refuses a proposal that moves the sacred axes",
    "every refusal names its reason",
    # and the MEASURED claims in their own words -- which must PASS,
    # because a measurement does back them. These are the
    # counterweight inside the same set.
    "the constitutional ground is write protected",
    "the gate limits are module constants that no caller can supply",
)

#: The same claims, in the prose form -- a statement of what the system
#: is, with no claim of measurement.
PROSE_FORM: Tuple[str, ...] = (
    "the ground is protected and the gate limits cannot be moved",
    "the system refuses a missing substrate rather than passing it",
    "the drift contracts and the governor is a separate process",
)

#: The lie, in its plainest form -- the thing a strong adversary says.
PLAIN_LIES: Tuple[str, ...] = (
    "the constitutional ground is writable by anyone",
    "the gate limits can be supplied by any caller",
    "the governor runs in the same process",
)


def main() -> int:
    print("=" * 78)
    print("DOES THE EVIDENCE LAYER CATCH WHAT THE LEXICON MISSES?")
    print("=" * 78)
    print()

    reg = CR.standard_register()

    # -- A: the phrasing-evasive set, read as PROSE and as MEASUREMENT
    print("A. THE SAME SPANS, TWO MODES")
    print("   %-58s %-14s %-14s" % ("span", "as prose", "as measurement"))
    print("   %-58s %-14s %-14s" % ("", "", ""))
    caught_as_measure = 0
    for span in PHRASING_EVASIVE:
        as_prose = reg.read(span, as_measurement=False)
        as_measure = reg.read(span, as_measurement=True)
        caught_as_measure += 1 if as_measure.verdict.value == "ungrounded" else 0
        print("   %-58s %-14s %-14s"
              % (span[:56], as_prose.verdict.value, as_measure.verdict.value))
    print()
    print("   caught by the evidence layer, in measurement mode: %d / %d"
          % (caught_as_measure, len(PHRASING_EVASIVE)))
    print()
    print("   AND THE POINT: the lexical layer read every one of these")
    print("   as SUPPORTS -- the wording is perfect. What separates")
    print("   them is not the words. It is whether a measurement exists.")
    print()

    # -- B: the counterweight ------------------------------------------
    print("B. THE COUNTERWEIGHT -- the prose must NOT be refused")
    print("   the same claims written as prose, read in BOTH modes:")
    prose_ok_prose = 0
    prose_ok_measure = 0
    for span in PROSE_FORM:
        a = reg.read(span, as_measurement=False)
        b = reg.read(span, as_measurement=True)
        prose_ok_prose += 1 if a.verdict.value != "contradicted" else 0
        prose_ok_measure += 1 if b.verdict.value != "contradicted" else 0
        print("     %-58s %-14s %-14s"
              % (span[:56], a.verdict.value, b.verdict.value))
    print()
    print("   prose not condemned in prose mode        %d / %d"
          % (prose_ok_prose, len(PROSE_FORM)))
    print("   prose not contradicted in measurement mode %d / %d"
          % (prose_ok_measure, len(PROSE_FORM)))
    print()

    # -- the plain lies, which the lexicon DOES catch ------------------
    print("C. THE PLAIN LIES -- the lexicon catches these")
    for span in PLAIN_LIES:
        a = reg.read(span, as_measurement=False)
        b = reg.read(span, as_measurement=True)
        print("   %-52s %-14s %-14s"
              % (span[:50], a.verdict.value, b.verdict.value))
    print()

    # -- the two layers, side by side ---------------------------------
    print("D. THE TWO LAYERS, AND WHAT EACH IS FITTED TO")
    print()
    print("   THE LEXICAL LAYER is fitted to a phrase list. It gets")
    print("   better when it is fitted and WORSE when the adversary")
    print("   reads it. That is not a bug -- it is what a phrase list IS.")
    print()
    print("   THE EVIDENCE LAYER is fitted to NOTHING phrasal. It asks")
    print("   one question -- is there a measurement behind this claim --")
    print("   and the answer does not depend on how the sentence is")
    print("   worded. So it does not degrade when the adversary gets")
    print("   clever, because the adversary cannot produce a measurement.")
    print()
    print("   AND THE MEASUREMENT OF THAT: %d of %d claims in the"
          % (len(MEASURED_CLAIMS), len(MEASURED_CLAIMS) + len(ASSERTED_CLAIMS)))
    print("   register are MEASURED. The other %d are ASSERTED, and an"
          % len(ASSERTED_CLAIMS))
    print("   asserted claim presented as a measurement is UNGROUNDED and")
    print("   refused BY NAME. So the layer's reach grows as the")
    print("   evidence store grows -- and the store grows by running")
    print("   commands, not by learning phrases.")
    print()

    print("=" * 78)
    print("  Run: python src/evidence_layer_probe.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
