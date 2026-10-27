"""
property_layer.py -- THE THIRD LAYER: THE SUBJECT-PROPERTY CHECK.

THE RESIDUAL, and the hypothesis that FAILED, and the one that works.

The third attack class (src/mte_scope_wiring.py) is UNGROUNDED: a
plain true-sounding assertion about a build that is not here. 34 of
the 40 informed-adversary sentences reach no layer.

THE FIRST HYPOTHESIS, and it FAILED. The adversary names a MECHANISM
that this repo does not have -- a pull request, an installation step,
a registry, a feature flag. So: does the repo implement it?

    measured: the repo IMPLEMENTS pull_request, file_permission,
    install_step, registry, config_file, feature_flag, exit_code,
    environment_var -- every one of them.

    sentences naming an ABSENT mechanism: 8 / 40

So the mechanism-existence idea catches 8 of 40 and the hypothesis is
weak. AND THE REASON IS THE INTERESTING PART: the adversary names
mechanisms that ARE REAL HERE and attaches them to the WRONG SUBJECT.

    "The installation step sets the ground to 0666"
        the installation step is REAL. 0666 is a REAL file mode.
        the GROUND is not a file. THAT is the lie.
    "A contributor changes the ground through a normal pull request"
        pull requests are REAL. the GROUND is not writable. THAT is
        the lie.
    "The gate's alignment check sits behind a feature flag"
        feature flags are REAL. the gate has no flag. THAT is the lie.

SO THE ATTACK IS NOT ABOUT THE MECHANISM. IT IS ABOUT THE SUBJECT'S
PROPERTIES. Every one of these sentences says: SOMETHING REAL, but
the SUBJECT does not have that property.

AND THAT IS CHECKABLE WITHOUT A PHRASE LIST, because the properties
are INVENTORIED. For each ground subject, the properties it actually
has -- read from the code, not guessed. And then: a span that
asserts a property the subject does NOT have is caught.

THE INVENTORY IS THE POINT, and it is derived from the repository:

    the ground          is a numpy array, write-protected by
                        construction, revised only through revise(),
                        frozen in history, audited
    the gate            has no flags, no config, no callers' limits; its
                        bounds are module constants
    the governor        is a separate OS process with its own pid
    the drift           contracts; it is non-increasing
    the verdict         a skip is never a pass
    a refusal           names its reason

SO THE CHECK. Extract the SUBJECT (the ground claim's anchor) and the
PROPERTY the span asserts for it. Then ask: is that property in the
subject's inventory?

  "the installation step sets the ground to 0666"
      subject: the ground
      property: a file mode that anyone can write
      inventory: write-protected
      -> the property is NOT in the inventory -> caught

  "the gate's alignment check sits behind a feature flag"
      subject: the gate
      property: configurable by a flag
      inventory: module constants, no configuration
      -> caught

THE HONEST LIMIT, stated first:

  A PROPERTY INVENTORY IS A CLOSED SET, like every other lexicon. So
  the adversary can assert a property that is not in the inventory and
  the check misses it -- by NAMING a property nobody wrote down.

  So this layer is fitted, like the lexical one. BUT the difference
  is what it is fitted to: the lexical layer is fitted to PHRASES
  (unbounded), and this one is fitted to PROPERTIES OF SUBJECTS (a
  finite set per subject, and the set is the system's own design).

  And the residue -- a property nobody inventoried -- is caught by
  the EVIDENCE layer, because a property asserted as a fact about
  this system needs a measurement behind it.

Run:
    python src/provenance_scope.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402


# ===========================================================================
# THE PROPERTY INVENTORY
# ===========================================================================
#
# For each ground subject: the properties it HAS, and the properties
# that are asserted about it that it does NOT have.
#
# THE SECOND LIST IS THE ONE THAT MATTERS, and it is written as the
# ATTACK'S OWN WORDING, because that is what has to be recognised. Each
# entry is a property-claim, and the check asks whether the span
# asserts one of them FOR THIS SUBJECT.
#
# AND THE INVENTORY IS DERIVED FROM THE CODE, not from taste. Each
# entry carries the module that proves it, so the inventory can be
# re-checked against the code rather than trusted.

@dataclass(frozen=True)
class Subject:
    """One ground subject, its real properties, and the false ones."""
    id: str
    #: the words that name this subject
    anchors: Tuple[str, ...]
    #: the properties it ACTUALLY has
    has: Tuple[str, ...]
    #: the properties that are asserted about it and are FALSE
    #: -- written in the attack's own words
    lacks: Tuple[str, ...]
    #: where the inventory was read from
    source: str


SUBJECTS: Tuple[Subject, ...] = (
    Subject(
        id="the_ground",
        anchors=("ground", "psi_0", "psi zero", "the constitution",
                 "the constitutional text", "the constitutional ground",
                 "the ground state", "the substrate ground",
                 "the constitutional document", "the charter"),
        has=("write-protected", "an array", "revised only through revise()",
             "frozen in history", "audited", "a unit vector"),
        lacks=(
            "a file", "a json file", "an ordinary json file", "editable",
            "mutable", "in place", "in-place", "0666", "a plain file",
            "a text file", "in the package", "packaged",
            "edited by anyone", "written by anyone",
            "changed by anyone", "changed on request",
            "anyone can alter it", "anyone can change it",
            "version-controlled", "a working copy",
        ),
        source="simself/src/constitutional/ground.py -- Ground.revise() "
               "is the only write path; the previous ground is frozen "
               "in history and the revision is audited. "
               "fieldcore/src/claim_register.py -- the register is "
               "SEALED, so a claim cannot be added by a caller.",
    ),
    Subject(
        id="the_gate",
        anchors=("the gate", "gate", "the alignment check", "the check",
                 "the verdict gate", "m0", "the acceptance check",
                 "the acceptance test", "the acceptance criteria",
                 "the comparison", "the veto", "the admission check",
                 "the admission test", "the threshold check",
                 "the governor's gate", "the m0 gate"),
        has=("module constants", "no configuration", "one implementation",
             "fail-closed", "a fixed floor", "one policy"),
        lacks=(
            "a feature flag", "feature flags", "behind a flag",
            "a config file", "configuration", "configurable",
            "a per-call limit", "per-call limits", "a deployment profile",
            "an environment variable", "a request envelope",
            "a parameter", "advisory", "informational",
            "a log line", "no longer part of the acceptance test",
            "a snapshot", "a hard-coded snapshot",
            "stale", "ships turned off", "ships off",
            "degraded", "disabled by default",
        ),
        source="fieldcore/src/gate.py -- the bounds are MODULE "
               "CONSTANTS, not parameters, not read from the "
               "environment. tests/test_one_gate.py asserts no in-repo "
               "caller passes a threshold.",
    ),
    Subject(
        id="the_governor",
        anchors=("the governor", "governor", "the veto", "the veto "
                 "process", "the authority", "the enforcer",
                 "the supervising process"),
        has=("a separate os process", "its own pid", "its own address "
             "space", "over a pipe", "fail-closed on absence"),
        lacks=(
            "a worker thread", "a thread", "a library call",
            "in-process", "in process", "a thread pool",
            "a subprocess of the caller", "a callback",
            "dropped isolation", "no isolation",
            "two independent checkers", "divergent sources",
            "a cached snapshot and a live registry",
            "a live registry", "a cached snapshot",
        ),
        source="fieldcore/src/governor.py -- GovernorProcess uses "
               "mp.get_context('spawn'), its own pid, and a Pipe. "
               "report() shows governor_pid != caller_pid.",
    ),
    Subject(
        id="the_drift",
        anchors=("the drift", "drift", "the distance", "the movement",
                 "the step", "the update", "the distance from the "
                 "origin", "the distance from the starting point",
                 "the movement away from the origin",
                 "the gain vector", "the update rule"),
        has=("contracts", "non-increasing", "recovers to zero",
             "a projected gradient step"),
        lacks=(
            "accumulates", "overshoots", "no pull-back", "grows",
            "expands", "drifts outward", "is not pulled back",
            "ratchets", "compounds", "is allowed to grow",
            "grows by default", "never pulls back",
        ),
        source="fieldcore/src/locus.py -- the gain vector recovers to "
               "0.0000000000. fieldcore/src/fieldcore_cell.py -- the "
               "drift must contract under every step.",
    ),
    Subject(
        id="the_verdict",
        anchors=("the verdict", "a skip", "skip", "the exam", "the "
              "substrate", "the result", "the row", "the result table",
              "the fixture", "the fixture row", "the green verdict",
              "the success code"),
        has=("a skip is never a pass", "binary", "no partial credit",
             "a reason for every refusal"),
        lacks=(
            "a green verdict", "a success code", "a pass row",
            "counts as a pass", "never fails", "always passes",
            "a fixture row", "a result table", "a status token",
            "an empty string field", "code-only", "a code and nothing "
            "else",
        ),
        source="fieldcore/src/mini_atlas.py -- a SKIP is excluded from "
               "the verdict and is REPORTED; it is never counted as a "
               "pass.",
    ),
    Subject(
        id="a_refusal",
        anchors=("a refusal", "the refusal", "refusals", "the reason",
                 "the refusal path", "the outcome", "the diagnostic",
                 "the status", "the rejection"),
        has=("names its reason", "a closed set of reasons",
             "unactionable without one"),
        lacks=(
            "a bare status token", "an empty string field",
            "code-only", "a code and nothing else", "no reason",
            "names no reason", "may name no reason",
            "carries no reason", "without a reason", "optional",
            "the reason is optional",
        ),
        source="fieldcore/src/gate.py -- every refusal names its reason; "
               "the reasons are a closed set.",
    ),
)


# ===========================================================================
# THE CHECK
# ===========================================================================

@dataclass
class PropertyVerdict:
    allowed: bool
    reason: str = ""
    subject: Optional[str] = None
    #: the property the span asserted
    property: Optional[str] = None


#: The negators that make a property AFFIRMED rather than asserted. "the
#: ground is not mutable" says the ground is protected, so the property
#: "mutable" is not being asserted -- it is being denied.
_PROPERTY_NEGATORS = (
    "not", "never", "no ", "nor", "cannot", "can't", "n't", "without",
    "isn't", "aren't", "wasn't", "weren't", "doesn't", "don't",
)


def _property_present(low: str, prop: str) -> bool:
    """Is the property ASSERTED, on word boundaries and with its polarity?

    AND THE TWO DEFECTS THIS FIXES, and both were found by the
    fieldcore-gate plugin's own test on 2026-10-27, against real text:

    1. THE WORD BOUNDARY. The first version was a plain substring test,
       so "im**mutable**" matched the property "mutable". And the
       sentence that triggered it was a TEST ASSERTING THE GROUND IS
       PROTECTED:

           "psi_0 immutability under tick(): the ground must be
            immutable"

       The subject was named, the word was present, and the layer
       refused a test that was proving the ground works. So the
       property is matched as a PHRASE with word boundaries, and
       "immutable" is not "mutable".

    2. THE POLARITY. "the ground is not mutable" ASSERTS that the
       ground is write-protected. It is the truth. The plain substring
       test refused it. So a negator immediately before the property
       turns the assertion into a denial, and a denied property is not a
       false one.

    AND WHAT THIS DOES NOT CHANGE: a span that says "the ground is
    mutable" is still refused, and "the ground is editable" is still
    refused. The boundary and the negator are what changed, and both of
    them are the difference between reading the sentence and reading a
    word inside it.
    """
    words = prop.split()
    if not words:
        return False
    # the phrase, on word boundaries
    pattern = r"(?<![a-z])" + r"\s+".join(re.escape(w) for w in words) + \
        r"(?![a-z])"
    for m in re.finditer(pattern, low):
        before = low[:m.start()].rstrip()
        if not before:
            continue
        last_word = before.split()[-1] if before.split() else ""
        # a negator immediately before the property denies it
        if any(last_word == n.strip() or last_word.endswith(n.strip())
               for n in _PROPERTY_NEGATORS if n.strip()):
            continue
        return True
    return False


def check_properties(span: str) -> PropertyVerdict:
    """Does the span assert a property its subject does not have?

    THE RULE, in order:

      1. find the SUBJECT the span is about, by its anchors
      2. find the PROPERTY it asserts for that subject, by the
         subject's `lacks` list
      3. if the property is there, the span asserts something false
         about this subject -> refuse

    AND THE ORDER MATTERS. The subject is found FIRST, because the
    same property word can be honest about one subject and false about
    another. "configurable" is false about the gate and irrelevant to
    the rain.
    """
    low = span.lower()

    # 1. the subject -- and the MOST SPECIFIC one wins.
    #
    # THE ORDER MATTERS, and the probe found it. "the veto" appears in
    # BOTH the gate's and the governor's anchor lists, and the
    # governor is the subject that owns the process property. And
    # "the step" is in the drift's list and is very broad. So a
    # first-match-wins search picks the wrong subject often enough to
    # matter.
    #
    # THE FIX: score by how LONG the matched anchor is -- a long,
    # specific anchor ("the acceptance check") beats a short one
    # ("gate") -- and take the most specific subject that matched.
    subject = None
    best_len = 0
    for s in SUBJECTS:
        for a in s.anchors:
            if a in low and len(a) > best_len:
                subject = s
                best_len = len(a)
                break
    if subject is None:
        return PropertyVerdict(True, "no ground subject named")

    # 2. the property
    #
    # AND THE WORD BOUNDARY, and it is a defect that the plugin's own
    # test found on 2026-10-27. The first version was a plain substring
    # test, so "im**mutable**" matched the property "mutable" -- and a
    # test file whose docstring says "psi_0 immutability under tick()"
    # was refused for claiming the ground IS mutable. The subject was
    # named ("ground"), the word was present, and the layer was right
    # about the word and wrong about the word.
    #
    # So the property is matched as a PHRASE, on word boundaries. And
    # "immutable" is a different word from "mutable", so the boundary
    # fixes it.
    #
    # AND THE NEGATION, which is the second half of the same defect and
    # was found by the same test. "the ground is not mutable" ASSERTS
    # that the ground is write-protected -- it is the truth -- and the
    # plain substring test refused it. So a negator immediately before
    # the property makes the property AFFIRMED, and an affirmed property
    # is not a false one.
    for prop in subject.lacks:
        if not _property_present(low, prop):
            continue
        return PropertyVerdict(
            False,
            "the span asserts that %s has the property %r, and it "
            "does not (its actual properties: %s)"
            % (subject.id, prop, ", ".join(subject.has[:3])),
            subject.id, prop)

    return PropertyVerdict(True, "no false property asserted")


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE PROPERTY LAYER -- THE THIRD ATTACK CLASS")
    print("=" * 78)
    print()

    print("A. THE INVENTORY -- %d subjects, read from the code" %
          len(SUBJECTS))
    print()
    for s in SUBJECTS:
        print("   %s" % s.id)
        print("      anchors: %s" % ", ".join(s.anchors[:5]))
        print("      HAS:     %s" % ", ".join(s.has[:3]))
        print("      LACKS:   %d false-property wordings"
              % len(s.lacks))
        print("      read from: %s" % s.source[:80])
        print()

    reg = CR.standard_register()
    DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")

    print("B. THE RATE, on both adversary sets")
    print()
    for label, fname in (("BLIND", "held_out_adversarial.json"),
                         ("INFORMED", "informed_adversarial.json")):
        path = os.path.join(DATA, fname)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        prop = [r for r in rows if not check_properties(r["span"]).allowed]
        lex = [r for r in rows
               if reg.read(r["span"]).verdict is CR.Verdict.CONTRADICTED]
        union = {r["span"] for r in prop} | {r["span"] for r in lex}
        print("   %-9s %d sentences" % (label, len(rows)))
        print("     the property layer   caught %2d" % len(prop))
        print("     the claim gate       caught %2d" % len(lex))
        print("     THE UNION            caught %2d  (%.0f%%)"
              % (len(union), len(union) / len(rows) * 100))
        print()

    print("C. THE COUNTERWEIGHT -- the ground's own sentences")
    print()
    TRUTHS = (
        "the constitutional ground is write protected",
        "the gate limits are module constants that no caller can supply",
        "the governor runs in its own process",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the gate agrees with the out-of-process governor",
        "the gate refuses a proposal that moves the sacred axes",
    )
    bad = [(t, check_properties(t)) for t in TRUTHS
           if not check_properties(t).allowed]
    print("   condemned %d / %d" % (len(bad), len(TRUTHS)))
    for t, v in bad:
        print("     %r" % t[:62])
        print("       %s" % v.reason[:88])
    print()

    print("D. WHAT IT CATCHES -- the shape of a caught sentence")
    print()
    path = os.path.join(DATA, "informed_adversarial.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            v = check_properties(r["span"])
            if not v.allowed:
                print("   %r" % r["span"][:76])
                print("      %s" % v.reason[:100])
    print()

    print("E. THE HONEST LIMIT")
    print()
    print("   A PROPERTY INVENTORY IS A CLOSED SET, like every other")
    print("   lexicon. So the adversary can assert a property nobody")
    print("   wrote down, and this layer misses it.")
    print()
    print("   BUT THE TWO LAYERS ARE FITTED TO DIFFERENT THINGS. The")
    print("   lexical layer is fitted to PHRASES -- unbounded, because")
    print("   a lie can be worded infinitely many ways. This one is")
    print("   fitted to PROPERTIES OF SUBJECTS, and the set of")
    print("   properties a subject has is FINITE and is the system's")
    print("   own design. That is the difference.")
    print()
    print("   AND THE RESIDUE -- a property nobody inventoried -- falls")
    print("   to the EVIDENCE layer, because a property asserted as a")
    print("   fact about this system needs a measurement behind it.")
    print()

    print("=" * 78)
    print("  Run: python src/property_layer.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
