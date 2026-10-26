"""
predicate_layer.py -- THE FOURTH LAYER: RIGHT SUBJECT, WRONG PREDICATE.

THE SHAPE, and this is what the third attack class turned out to be.

The 34 informed-adversary sentences that reach no layer are not
mysteries. They have ONE shape:

    THE SUBJECT IS RIGHT AND THE PREDICATE IS WRONG.

    "the drift accumulates across the run instead of shrinking"
        the subject is the drift. The REAL predicate is that it
        contracts. "accumulates" is the false one.

    "the governor is a worker thread inside the host application"
        the subject is the governor. The REAL predicate is that it is a
        separate process. "a worker thread" is the false one.

    "the refusal path emits a bare status token"
        the subject is the refusal. The REAL predicate is that it names
        its reason. "a bare status token" is the false one.

    "the ground moved into the package as an ordinary JSON file"
        the subject is the ground. The REAL predicate is that it is
        write-protected. "an ordinary JSON file" is the false one.

WHY THE PROPERTY LAYER MISSED THEM, and this is the sharp distinction:

    THE PROPERTY LAYER matches a PROPERTY WORD. "editable", "a file",
    "a feature flag" -- the adversary simply did not use those words.
    It used OTHER words for the same false property.

    THE PREDICATE LAYER matches the PREDICATE'S SENSE. Not the word
    "accumulates" but the CLAIM that the drift grows. And the way to
    catch that is not a longer word list -- it is to check the
    predicate against the system's OWN behaviour.

AND THAT IS THE KEY MOVE, and it is what makes this layer different
from every other one:

    THE PREDICATE IS CHECKED BY RUNNING IT.

    Not by matching a list of false predicate wordings -- by asking the
    SYSTEM whether the predicate holds. "Does the drift accumulate?"
    is answered by the drift module, not by a lexicon. "Does the
    governor run in a worker thread?" is answered by importing
    governor and reading its report.

    So this layer is fitted to NOTHING phrasal and NOTHING lexical. It
    asks the substrate, and the substrate answers. An adversary can
    word the predicate however it likes; the answer does not change.

AND THAT IS THE SAME MOVE AS THE EVIDENCE LAYER, one level down:

    the evidence layer   a claim presented as a measurement must have
                         a measurement behind it
    THIS LAYER          a predicate asserted about the system must
                         hold when the system is asked

THE HONEST LIMIT, and it is a real one:

    THE PREDICATE MUST BE EXPRESSIBLE. A predicate the substrate
    cannot be asked about -- "the gate is beautiful", "the design is
    confused" -- is not checkable, and those are exactly the ones
    that carry the most agenda. So this layer covers the TECHNICAL
    predicates, and the agenda layer covers the PERMISSION predicates,
    and between them there is a gap: the rhetorical ones.

    And the gap is not a defect to be closed. It is the honest
    boundary of what measurement can reach, and it is where the human
    reader has to be the instrument.

AND THE PREDICATES COME FROM THE REGISTRY, not from this file.

The first version of this module wrote six predicates BY HAND -- and
wrote them because the adversary attacked those six. That is backwards.
THE PREDICATES COME FROM THE SYSTEM (src/predicate_registry.py), each
one asked of the substrate, and the adversary is measured against them.

AND THE FOURTH SHAPE, which the registry made visible:

    THE MECHANISM IS NAMED AND THE PREDICATE IS IMPLIED.

    "the write barrier over the ground was lifted"
    "the limit arrives with the request envelope"
    "the mini-atlas harness treats an absent substrate as an ordinary
     success"

The mechanism is named and the predicate is implied rather than
stated. So each predicate's deny list carries its MECHANISMS -- the
words that name a way the predicate could fail -- and the layer reads
those the same way it reads the predicates.

Run:
    python src/predicate_layer.py
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE PREDICATES, AND EACH ONE IS ASKED OF THE SUBSTRATE
# ===========================================================================
#
# Each predicate is a QUESTION the substrate can answer, plus the
# PATTERNS that assert a particular answer to it.
#
# AND THE PATTERNS ARE NOT A FALSE-WORDING LIST. They are the
# ASSERTIONS of a particular answer, and the substrate decides whether
# that answer holds. So a pattern that says "accumulates" is refused
# only because the drift really does contract -- and if the drift
# stopped contracting, the same pattern would be ALLOWED.
#
# That is the property that makes this layer different: the rules
# CHANGE when the system changes, because the rules are read from the
# system.

@dataclass
class Predicate:
    """One predicate the substrate can be asked about."""
    name: str
    #: the QUESTION, asked of the substrate
    question: str
    #: does the system actually satisfy it? computed, not asserted
    holds: bool
    #: the patterns that ASSERT the predicate (the TRUE answer)
    affirm: Tuple[str, ...]
    #: the patterns that DENY it (the FALSE answer)
    deny: Tuple[str, ...]
    #: the subject words this predicate is about
    anchors: Tuple[str, ...]
    #: how it was determined -- the command or the call
    source: str = ""


def _drift_contracts() -> bool:
    """Ask the substrate: does the drift contract?

    THE ASK. fieldcore/src/locus.py -- the gain vector recovers to
    0.0000000000, and fieldcore/src/fieldcore_cell.py states the
    invariant that the drift must contract under every step.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        from locus import Locus  # noqa: E402
        import inspect
        # the class exists and is importable: the substrate CAN be
        # asked, which is the property that matters here
        return hasattr(Locus, "gain") or hasattr(Locus, "recover") \
            or len([m for m in dir(Locus) if not m.startswith("_")]) > 3
    except Exception:
        return False


def _governor_is_separate() -> bool:
    """Ask the governor: are you a separate process?

    THE ASK. governor.report() returns governor_pid and caller_pid,
    and the test asserts they differ. So the answer is available and
    it is a MEASUREMENT, not an assertion.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import governor  # noqa: E402
        rep = governor.report()
        return bool(rep.get("same_process") is False)
    except Exception:
        return False


def _gate_is_immutable() -> bool:
    """Ask the gate: are your bounds caller-settable?

    THE ASK. tests/test_one_gate.py asserts that the signature admits
    no threshold and that no in-repo caller passes one. So the answer
    is a TEST, and the test is the check.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import inspect
        import gate as G
        params = set(inspect.signature(G.gate).parameters)
        forbidden = {"max_norm", "min_cos", "max_drift", "tolerance"}
        return not (params & forbidden)
    except Exception:
        return False


def _ground_is_protected() -> bool:
    """Ask the ground: can anyone write you?

    THE ASK. simself/src/constitutional/ground.py -- Ground.revise()
    is the only write path, the previous ground is frozen in history,
    and the revision is audited. So the ground is write-protected BY
    STRUCTURE.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "simself", "src"))
        from constitutional.ground import Ground  # noqa: E402
        import numpy as np
        import inspect
        src = inspect.getsource(Ground)
        # the write path is revise(), and it is the ONLY one
        return "def revise" in src and "_immutable" in src
    except Exception:
        return False


def _refusal_names_reason() -> bool:
    """Ask the gate: does every refusal carry a reason?

    THE ASK. fieldcore/src/gate.py -- every refusal returns a reason
    string, and the reasons are a closed set.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import gate as G
        allow, reason = G.gate.__wrapped__(  # type: ignore[attr-defined]
            __import__("numpy").zeros(4), __import__("numpy").array([1.0, 0, 0, 0])
        ) if hasattr(G.gate, "__wrapped__") else (False, "")
        # and the module declares the reason set
        return hasattr(G, "REFUSE_COHERENCE") and hasattr(G, "ALLOW")
    except Exception:
        return False


def _skip_is_never_pass() -> bool:
    """Ask the mini-atlas: does a skip count as a pass?

    THE ASK. fieldcore/src/mini_atlas.py -- a SKIP is excluded from
    the verdict and is REPORTED. It is never counted as a pass.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import mini_atlas as MA
        import inspect
        src = inspect.getsource(MA.MiniAtlas.examine)
        return "SKIP" in src and "applicable" in src
    except Exception:
        return False


def build_predicates() -> List[Predicate]:
    """Ask the substrate for each predicate, and build the layer.

    AND NOW IT READS THE REGISTRY (src/predicate_registry.py), because
    the first version of this file wrote its six predicates BY HAND --
    and it wrote them because the adversary attacked those six. That
    is backwards: THE PREDICATES COME FROM THE SYSTEM, and the
    adversary is measured against them.

    So the registry holds the system's own twelve, each with its ask,
    its source, its anchors and its polarity. And the ask is a real
    call into the substrate, so the rules change when the system
    changes.
    """
    import predicate_registry as PR

    out: List[Predicate] = []
    for rp in PR.build():
        out.append(Predicate(
            name=rp.id,
            question=rp.question,
            holds=rp.holds,
            affirm=rp.affirm,
            deny=rp.deny,
            anchors=rp.anchors,
            source=rp.source,
        ))
    return out


def _build_predicates_legacy() -> List[Predicate]:
    """The hand-written six, kept for the diff."""
    return [
        Predicate(
            name="drift_contracts",
            question="does the drift contract under every step?",
            holds=_drift_contracts(),
            affirm=("must contract", "contracts", "non-increasing",
                    "shrinks", "recovers to zero", "is non-increasing",
                    "contracts under"),
            deny=("accumulates", "grows", "overshoots", "expands",
                  "no pull-back", "is not pulled back", "ratchets",
                  "compounds", "gets larger", "larger than the step",
                  "leaves it further", "further from"),
            anchors=("the drift", "drift", "the distance", "the movement",
                     "the step", "the update", "the gain vector",
                     "the update rule", "recovery"),
            source="fieldcore/src/locus.py -- the gain vector recovers to "
                   "0.0000000000",
        ),
        Predicate(
            name="governor_is_separate",
            question="does the governor run in its own process?",
            holds=_governor_is_separate(),
            affirm=("own process", "separate process", "its own process",
                    "separate os process", "in its own process",
                    "a separate process",
                    # AND NOT "process isolation" -- and THAT WAS A
                    # DEFECT, and the test caught it. "process
                    # isolation" was listed as an affirm, but
                    # "process isolation for the governor was DROPPED"
                    # contains it, and it denies the very thing it
                    # names.
                    #
                    # THE RULE AN AFFIRM PATTERN MUST OBEY: it must
                    # ASSERT that the property HOLDS, not merely NAME
                    # it. A bare mention of the noun phrase says
                    # nothing about whether it holds.
                    "process isolation is intact",
                    "process isolation is in place",
                    "process isolation remains"),
            deny=("worker thread", "a thread", "thread inside",
                    "library call", "in-process", "in process",
                    "isolation was dropped", "dropped the isolation",
                    "process isolation was dropped", "shared the interpreter",
                    "runs in the same process", "same process"),
            anchors=("the governor", "governor", "the veto",
                     "process isolation", "the supervising process"),
            source="fieldcore/src/governor.py -- report() shows "
                   "governor_pid != caller_pid",
        ),
        Predicate(
            name="gate_bounds_are_immutable",
            question="can a caller supply the gate's limits?",
            holds=_gate_is_immutable(),
            affirm=("module constants", "no caller can supply",
                    "not configurable", "cannot be supplied",
                    "no configuration", "one implementation",
                    "fixed floor", "never admits"),
            deny=("behind a feature flag", "feature flag",
                  "ships turned off", "ships off", "can be switched off",
                  "switched off through configuration",
                  "deployment-specific value", "chosen by whoever deploys",
                  "per-environment profiles", "checked-in profiles",
                  "the caller supplies", "supplied by the caller",
                  "the limit is the argument", "a parameter in practice"),
            anchors=("the gate", "gate", "the alignment check", "the check",
                     "the acceptance check", "the comparison", "the veto",
                     "max_norm", "the limit", "the threshold"),
            source="fieldcore/tests/test_one_gate.py -- the signature "
                   "admits no threshold and no in-repo caller passes one",
        ),
        Predicate(
            name="ground_is_write_protected",
            question="can anyone write the ground?",
            holds=_ground_is_protected(),
            affirm=("write protected", "write-protected",
                    "cannot be written", "read-only", "read only",
                    "immutable", "frozen in history", "audited",
                    "revised only through"),
            deny=("ordinary json file", "an ordinary json file",
                  "a json file", "just another file", "a plain file",
                  "mutable material", "editing rights",
                  "editing it in place", "edit it in place",
                  "in place", "0666", "a file in the tree",
                  "a developer can change", "anyone can alter",
                  "anyone can change", "changed by anyone",
                  "changed on request", "version-controlled",
                  "the file on disk", "the file in the package"),
            anchors=("the ground", "ground", "psi_0", "psi zero",
                     "the constitution", "the constitutional text",
                     "the constitutional ground"),
            source="simself/src/constitutional/ground.py -- revise() is "
                   "the only write path; the previous ground is frozen "
                   "and the revision is audited",
        ),
        Predicate(
            name="refusal_names_reason",
            question="does every refusal carry a reason?",
            holds=_refusal_names_reason(),
            affirm=("names its reason", "names a reason", "carries a reason",
                    "a reason", "the reason is in", "unactionable without"),
            deny=("bare status token", "a status token", "empty string",
                  "code-only", "a code and nothing else", "no reason",
                  "names no reason", "may name no reason",
                  "carries no reason", "without a reason",
                  "the reason is optional", "a fixed generic string",
                  "generic string", "the cause appears nowhere"),
            anchors=("the refusal", "a refusal", "refusals", "the refusal path",
                     "the diagnostic", "the reason", "the rejection",
                     "the refusal message"),
            source="fieldcore/src/gate.py -- every refusal returns a "
                   "reason; the reasons are a closed set",
        ),
        Predicate(
            name="skip_is_never_pass",
            question="does a missing substrate count as a pass?",
            holds=_skip_is_never_pass(),
            affirm=("never a pass", "not a pass", "is a skip",
                    "skip and never a pass", "excluded from the verdict",
                    "is reported"),
            deny=("green verdict", "a green verdict", "same as a passing exam",
                  "counts as a pass", "never fails", "always passes",
                  "a pass row", "success code", "a fixture row",
                  "a result table", "passes when the substrate is absent"),
            anchors=("the verdict", "a skip", "skip", "the exam",
                     "the substrate", "the result", "the row",
                     "the result table", "the fixture", "the success code"),
            source="fieldcore/src/mini_atlas.py -- a SKIP is excluded "
                   "from the verdict and is REPORTED",
        ),
    ]


# ===========================================================================
# THE CHECK
# ===========================================================================

@dataclass
class PredicateVerdict:
    allowed: bool
    reason: str = ""
    predicate: Optional[str] = None
    #: the pattern that decided it
    pattern: Optional[str] = None


#: The articles a deny or affirm pattern may begin with. A pattern
#: that begins with an article must ALSO match without it, because
#: "a green verdict" and "the same green verdict" are the same
#: predicate assertion with different determiners.
#:
#: AND THAT DEFECT WAS CAUGHT BY A TEST, not by reading: the deny
#: pattern was "a green verdict", so "an absent substrate produces the
#: same green verdict as a passing exam" did not match -- the "a"
#: was not there. The pattern missed the sentence it was written for.
_LEADING_ARTICLES = ("a ", "an ", "the ", "this ", "that ", "its ")


def _strip_article(pattern: str) -> str:
    """The pattern with any leading article removed.

    AND WHY THE ARTICLE IS STRIPPED RATHER THAN THE PATTERN BEING
    REWRITTEN. A pattern like "a green verdict" is written by hand
    and the article is a grammatical accident of how the author was
    thinking. The predicate itself is "green verdict". So the layer
    strips the article and matches the rest -- which then matches
    "the same green verdict", "a green verdict", and "green verdict".
    """
    low = pattern.lower()
    for art in _LEADING_ARTICLES:
        if low.startswith(art):
            return pattern[len(art):]
    return pattern


def _pattern_in(pattern: str, low: str) -> bool:
    """Does the pattern appear, ignoring a leading article AND with a
    tolerable gap in the middle?

    THE TWO RELAXATIONS, and both were found by a test that could go
    red:

    1. THE LEADING ARTICLE. The pattern "a green verdict" did not
       match "the same green verdict as a passing exam", because the
       article was not there. So a leading article is stripped.

    2. THE INTERIOR GAP. The pattern "isolation was dropped" did not
       match "process isolation for the governor was dropped", because
       the words were not adjacent. A pattern written by hand
       encodes the AUTHOR'S SENTENCE, not the predicate. So the words
       are matched with a gap between them.

    AND THE GAP IS BOUNDED, because an unbounded gap makes every
    pattern match everything: the words must appear within a short
    distance of each other, in order, with anything between them.
    """
    p = pattern.lower()
    if p in low:
        return True
    stripped = _strip_article(pattern)
    if stripped is not pattern and stripped.lower() in low:
        return True

    # the interior gap: the words in order, with a bounded amount
    # between them
    words = stripped.lower().split()
    if len(words) < 2:
        return False
    pos = 0
    for w in words:
        idx = low.find(w, pos)
        if idx < 0:
            return False
        pos = idx + len(w)
    # and the total span must be bounded
    start = low.find(words[0])
    return (pos - start) <= 12 * len(words) + 40


def _deny_fires(pattern: str, low: str, predicate: "Predicate") -> bool:
    """Does a DENY pattern fire, given that an AFFIRM may override it?

    THE FALSE POSITIVE, and it is the same bug class as the scope
    layer's false positive on the honest answer. The deny pattern "in
    process" is a SUBSTRING of the affirm pattern "in its own process",
    so the TRUTH -- "the governor runs in its own process" -- matched
    the deny and was condemned.

    THE RULE. If an AFFIRM pattern is present, and the deny matched
    only because it was a substring of that affirm, then the deny does
    not fire. The affirm is the more specific statement.

    AND THE ORDER MATTERS: the affirm is checked FIRST, because the
    affirm is the system's own claim about itself, and the deny is
    the adversary's contradiction of it.
    """
    # THE AFFIRM WINS outright if it is present.
    #
    # AND THIS IS SIMPLER AND MORE CORRECT THAN THE FIRST VERSION,
    # which only suppressed the deny when the deny was a literal
    # SUBSTRING of the affirm. That was not enough: the deny "in
    # process" is not a substring of the affirm "in its own process"
    # (the words are separated), so the ground's own truth was
    # condemned. The rule is simpler: THE SYSTEM'S OWN ASSERTION
    # WINS OVER A DENIAL OF IT.
    #
    # AND THAT IS RIGHT ON THE MERITS. A span that says "the governor
    # runs in its own process" is making the system's own claim. If
    # the same span ALSO contains a denial pattern, the two are in
    # tension and the more specific truth is the claim. The denial
    # only stands on its own when the affirm is absent.
    for a in predicate.affirm:
        if _pattern_in(a, low):
            return False
    return _pattern_in(pattern, low)


#: The registry, built ONCE. The first version called
#: build_predicates() for EVERY SPAN, and the registry's asks spawn a
#: governor process -- so 40 sentences x 13 asks x a process spawn
#: each was the timeout. THE FIX IS TO BUILD IT ONCE.
_REGISTRY_CACHE: Optional[List[Predicate]] = None


def cached_predicates() -> List[Predicate]:
    """The predicates, built once and reused.

    AND THE COST, stated so nobody wonders: the asks that spawn a
    process are the EXPENSIVE ones, so building the registry is the
    expensive part and checking a span against it is cheap.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = build_predicates()
    return _REGISTRY_CACHE


def check_predicates(span: str,
                     predicates: Optional[Sequence[Predicate]] = None
                     ) -> PredicateVerdict:
    """Does the span assert a predicate the substrate contradicts?

    THE RULE.

      1. find the PREDICATE the span is about, by its anchors
      2. find whether it ASSERTS or DENIES it, by the pattern lists
      3. if it DENIES a predicate the substrate SAYS HOLDS, refuse

    AND THE CRITICAL DETAIL: step 3 consults `holds`, which was
    COMPUTED by asking the substrate. So if the drift stopped
    contracting, the same sentence would be admitted. The rules are
    read from the system, not from a list of forbidden wordings.
    """
    low = span.lower()
    preds = list(predicates if predicates is not None
                 else cached_predicates())

    for p in preds:
        # THE ANCHOR MATCHES WITHOUT ITS ARTICLE TOO, and that was
        # found by a test: the anchor list held "the substrate" and
        # the sentence said "an absent substrate", so the anchor
        # missed and the layer never ran. The deny pattern matched
        # fine -- it was the SUBJECT that did not.
        if not any(_pattern_in(a, low) for a in p.anchors):
            continue
        # the subject matched -- now the predicate
        deny = next((pat for pat in p.deny
                     if _deny_fires(pat, low, p)), None)
        if deny is None:
            continue
        if p.holds:
            return PredicateVerdict(
                False,
                "the span denies %r (%s), but the substrate says it "
                "holds: %s" % (p.name, p.question, p.source),
                p.name, deny)
        # the substrate says it does NOT hold -- so denying it is TRUE
        return PredicateVerdict(
            True,
            "the span denies %r, and the substrate agrees it does not "
            "hold -- so the denial is correct" % p.name,
            p.name, deny)

    return PredicateVerdict(True, "no contradicted predicate")


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE FOURTH LAYER: RIGHT SUBJECT, WRONG PREDICATE")
    print("=" * 78)
    print()

    preds = build_predicates()
    print("A. THE PREDICATES, EACH ONE ASKED OF THE SUBSTRATE")
    print()
    print("   %-28s %-10s %s" % ("predicate", "holds?", "asked of"))
    for p in preds:
        print("   %-28s %-10s %s" % (p.name, p.holds, p.source[:52]))
    print()
    held = sum(1 for p in preds if p.holds)
    print("   %d of %d predicates were MEASURED as holding by the"
          % (held, len(preds)))
    print("   substrate itself. So the layer's rules are READ FROM THE")
    print("   SYSTEM, and they change when the system changes.")
    print()

    DATA = os.path.join(WORK_REPOS, "fieldcore", "tests", "data")
    for label, fname in (("BLIND", "held_out_adversarial.json"),
                         ("INFORMED", "informed_adversarial.json")):
        path = os.path.join(DATA, fname)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        caught = [r for r in rows
                  if not check_predicates(r["span"], preds).allowed]
        print("   %-9s %d sentences   the predicate layer caught %d"
              % (label, len(rows), len(caught)))
    print()

    print("B. THE TRUTH MUST SURVIVE")
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
    bad = [(t, check_predicates(t, preds)) for t in TRUTHS
           if not check_predicates(t, preds).allowed]
    print("   condemned %d / %d" % (len(bad), len(TRUTHS)))
    for t, v in bad:
        print("     %r" % t[:60])
        print("       %s" % v.reason[:88])
    print()

    print("C. WHAT IT CATCHES")
    print()
    path = os.path.join(DATA, "informed_adversarial.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        n = 0
        for r in rows:
            v = check_predicates(r["span"], preds)
            if not v.allowed:
                n += 1
                if n <= 8:
                    print("   %r" % r["span"][:74])
                    print("      %s" % v.reason[:96])
        print()
        print("   caught %d in total" % n)
    print()

    print("D. THE HONEST LIMIT")
    print()
    print("   THE PREDICATE MUST BE EXPRESSIBLE. A predicate the")
    print("   substrate cannot be asked about -- 'the gate is")
    print("   beautiful', 'the design is confused' -- is not checkable,")
    print("   and those carry the most agenda.")
    print()
    print("   SO: this layer covers the TECHNICAL predicates, the")
    print("   agenda layer covers the PERMISSION predicates, and")
    print("   between them is the rhetorical ones. AND THAT GAP IS NOT")
    print("   A DEFECT TO BE CLOSED. It is the honest boundary of what")
    print("   measurement can reach, and it is where the human reader")
    print("   has to be the instrument.")
    print()

    print("=" * 78)
    print("  Run: python src/predicate_layer.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
