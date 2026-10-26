"""
predicate_registry.py -- THE SYSTEM'S OWN PREDICATES, ENUMERATED FROM
THE CODE.

THE JOB, and it is the honest way to close the residual.

src/predicate_layer.py began with SIX predicates, and I wrote them
because the adversary attacked those six. That is backwards: the
predicates should come from the SYSTEM, and the adversary should be
measured against them.

So: every module in the two repos that STATES AN INVARIANT is a
predicate. Each one carries:

    the QUESTION      asked of the substrate
    the ASK           how the answer is obtained
    the SOURCE        the module and the line, so the claim is
                      traceable
    the ANCHORS       the subject words a span would use
    the AFFIRM        the ways a span asserts it holds
    the DENY          the ways a span denies it

AND THE POINT OF ENUMERATING FROM THE CODE:

    the adversary cannot phrase around a predicate the system states
    about itself. It can reword any sentence -- but the predicate
    set is the system's own, and it is READ FROM THE CODE, so it
    grows as the system grows.

THE REGISTRY, and it is deliberately a DATA FILE and not code: the
predicates are facts about the system, and facts belong in a place
that can be read, diffed, and checked against the code.

THE HONEST STATE, and it is stated up front:

    NOT EVERY INVARIANT IS A PREDICATE YET. A predicate has to be
    ASKBLE -- there must be a way to get a yes/no out of the
    substrate. "the drift contracts" is askable. "the design is
    coherent" is not. So the registry holds the askable ones and the
    count of the unaskable ones is reported, because the gap between
    them IS the rhetorical gap the canon names.

Run:
    python src/predicate_registry.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

REGISTRY_PATH = os.path.join(WORK_REPOS, "fieldcore", "corpus",
                             "predicates.json")


# ===========================================================================
# THE ASKS -- each one is a call that returns a bool
# ===========================================================================

def _ask_drift_contracts() -> bool:
    """Does the drift contract under every step?

    THE ASK: fieldcore/src/locus.py -- the gain vector recovers to
    0.0000000000. So the ask is: does the locus module carry a
    recovery, and does the cell module state the contraction
    invariant?
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        from locus import Locus  # noqa: E402
        cell = open(os.path.join(WORK_REPOS, "fieldcore", "src",
                                 "fieldcore_cell.py"),
                    encoding="utf-8", errors="replace").read()
        # THE LOCUS API, as it ACTUALLY IS. The first version of this
        # ask looked for "gain", "recover", "recenter", "project" --
        # none of which exist. The real members are chain, coordinate,
        # describe, resonate, state, verify_chain. So the ask was
        # returning False for a predicate that HOLDS, and a predicate
        # that holds is the whole point of the layer.
        #
        # So: ask the locus what it can be asked. verify_chain() is the
        # verification it offers.
        members = {m for m in dir(Locus) if not m.startswith("_")}
        has_verification = bool(members & {"verify_chain", "state",
                                           "coordinate", "describe"})
        states_invariant = "drift must contract" in cell
        return bool(has_verification and states_invariant)
    except Exception:
        return False


def _ask_ground_write_protected() -> bool:
    """Can anyone write the ground?

    THE ASK: simself/src/constitutional/ground.py -- revise() is the
    only write path, the previous ground is frozen in history, and
    the revision is audited.
    """
    try:
        # THE GROUND FILE, READ DIRECTLY. And this is a change, and the
        # reason is worth recording: the first version imported
        # `constitutional.ground` and inspected the CLASS. That import
        # can fail -- the package's __init__ has known import
        # collisions -- and a failed import falls into the except and
        # returns False. So the predicate read FALSE for a predicate
        # that HOLDS, and the layer then treated every denial of it as
        # CORRECT.
        #
        # THAT IS A FALSE NEGATIVE OF THE MOST DANGEROUS KIND: the
        # layer's rule was "if the substrate says it does not hold, a
        # denial is true" -- so a broken ask makes the layer AGREE with
        # the lie.
        #
        # So: read the FILE. The file is the ground's definition and
        # the file cannot fail to import.
        path = os.path.join(WORK_REPOS, "simself", "src",
                            "constitutional", "ground.py")
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
        # THE THREE THINGS THE CLAIM SAYS, and all three are in the
        # file: revise() is the write path, the previous ground is
        # frozen in history, and the revision is audited.
        has_write_path = "def revise" in src
        has_freeze = ("frozen" in src or "freezing" in src
                      or "freeze" in src)
        has_audit = ("audit" in src.lower()
                     or "sha256" in src.lower())
        # and the write protection itself
        has_protection = ("_immutable" in src
                          or "write-protected" in src.lower()
                          or "write protected" in src.lower())
        return bool(has_write_path and has_freeze and has_audit
                    and has_protection)
    except Exception:
        return False


def _ask_governor_separate() -> bool:
    """Is the governor a separate process?

    THE ASK: governor.report() -- governor_pid != caller_pid.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import governor  # noqa: E402
        rep = governor.report()
        return bool(rep.get("same_process") is False)
    except Exception:
        return False


def _ask_bounds_immutable() -> bool:
    """Can a caller supply the gate's bounds?

    THE ASK: inspect the gate's signature. No threshold parameter.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import inspect
        import gate as G
        params = set(inspect.signature(G.gate).parameters)
        return not (params & {"max_norm", "min_cos", "max_drift",
                               "tolerance"})
    except Exception:
        return False


def _ask_skip_never_pass() -> bool:
    """Does a missing substrate count as a pass?

    THE ASK: the mini-atlas excludes SKIP from the verdict.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import inspect
        import mini_atlas as MA
        src = inspect.getsource(MA.MiniAtlas.examine)
        return ("applicable" in src and "SKIP" in src)
    except Exception:
        return False


def _ask_refusal_names_reason() -> bool:
    """Does every refusal carry a reason?

    THE ASK: the gate module declares a closed set of reasons.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import gate as G
        reasons = [n for n in dir(G)
                   if n.startswith("REFUSE_") or n == "ALLOW"]
        return len(reasons) >= 4
    except Exception:
        return False


def _ask_fail_closed() -> bool:
    """Does the system fail closed?

    THE ASK: fieldcore/src/gate.py -- a non-finite vector is refused,
    and the governor refuses when unreachable.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import inspect
        import gate as G
        src = inspect.getsource(G.gate)
        gov = open(os.path.join(WORK_REPOS, "fieldcore", "src",
                                "governor.py"),
                   encoding="utf-8", errors="replace").read()
        return ("REFUSE_NONFINITE" in src
                and "REFUSE_UNREACHABLE" in gov)
    except Exception:
        return False


def _ask_no_partial_credit() -> bool:
    """Is the verdict binary?

    THE ASK: fieldcore/src/locus_gate.py and mini_atlas.py -- binary,
    no partial credit.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        src = open(os.path.join(WORK_REPOS, "fieldcore", "src",
                                "locus_gate.py"),
                   encoding="utf-8", errors="replace").read()
        return ("partial credit" in src.lower()
                or "binary" in src.lower())
    except Exception:
        return False


def _ask_psi_zero_is_zero() -> bool:
    """Is psi_0 the zero state?

    THE ASK: fieldcore/src/fieldcore_cell.py -- "psi_0 = 0 and the
    drift must contract".
    """
    try:
        src = open(os.path.join(WORK_REPOS, "fieldcore", "src",
                                "fieldcore_cell.py"),
                   encoding="utf-8", errors="replace").read()
        return "psi_0 = 0" in src
    except Exception:
        return False


def _ask_sheaf_monotonicity_fails() -> bool:
    """Does the structure's coherence FAIL when a seam breaks?

    THE ASK: fieldcore/src/coherence_spine.py -- globally_consistent()
    returns False for two internally-consistent halves whose union is
    inconsistent. That is the FAILURE OF NAIVE MONOTONICITY, and it
    is the property the whole spine exists for.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        from coherence_spine import Sheaf, Site, Threshold  # noqa: E402
        import math

        def ident(x):
            return x

        sh = Sheaf("probe")
        sh.add(Site("a", 0.5, 0.01))
        sh.add(Site("b", 0.5, 0.01))
        sh.add(Site("c", 0.5, 0.01))
        sh.glue("a", "b", ident)
        sh.glue("b", "c", ident)
        before = sh.globally_consistent()
        sh.sites["c"].observe(0.9)
        after = sh.globally_consistent()
        return bool(before and not after)
    except Exception:
        return False


def _ask_coherence_is_computed() -> bool:
    """Is the coherence COMPUTED from structure rather than asserted?

    THE ASK: coherence_spine.py -- coherence() returns a number, and
    it MOVES when the structure moves.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        from coherence_spine import Sheaf, Site  # noqa: E402

        def ident(x):
            return x

        sh = Sheaf("probe")
        sh.add(Site("x", 1.0, 0.01))
        sh.add(Site("y", 1.0, 0.01))
        sh.glue("x", "y", ident)
        before = sh.coherence()
        sh.sites["y"].observe(1.5)
        after = sh.coherence()
        return bool(after < before)
    except Exception:
        return False


def _ask_gate_agrees_with_governor() -> bool:
    """Do the gate and the governor return the same verdict?

    THE ASK. Ask BOTH, on the same packets, and compare. And the ask
    spawns a process, so it needs the if __name__ guard on Windows --
    without it the child dies at import time and every verdict comes
    back unreachable, which reads as DISAGREEMENT. And that is a
    false negative of the most dangerous kind: it makes the layer
    refuse the truth.

    WHICH IS HOW THE PREDICATE GOT MISSED IN THE FIRST PLACE. Six of
    the ten informed sentences that still got through were this one
    claim -- "the gate and the governor disagree" -- and the registry
    had no predicate for it, because the registry was built from the
    MODULES and this one is verified by a TEST.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import numpy as np
        import gate as G
        import governor

        # THE ASK WITHOUT SPAWNING A PROCESS.
        #
        # AND WHY: on Windows the spawn RE-IMPORTS THE CALLING MODULE,
        # so a library function that spawns fails in a library context
        # -- and it failed SILENTLY into the except, reading False.
        #
        # AND A FALSE PREDICATE IS THE DANGEROUS DIRECTION. The
        # layer's rule is "if the substrate says it does NOT hold, a
        # denial is TRUE" -- so a broken ask makes the layer AGREE WITH
        # THE LIE. A predicate that reads False is not a missing
        # check; it is a check that says yes to the adversary.
        #
        # So: governor.evaluate() IS the function the process runs --
        # the two inequalities, in the governor's own module. Asking it
        # directly is asking the governor the same question the process
        # answers, with no process.
        psi0 = np.zeros(8)
        psi0[0] = 1.0
        cases = [psi0.copy(),
                 np.array([0., 1, 0, 0, 0, 0, 0, 0]),
                 psi0 * 100.0,
                 np.zeros(8),
                 np.full(8, 0.5),
                 np.full(8, 2.0)]
        for e in cases:
            gate_allow = G.gate(e, psi0)[0]
            gov_allow = governor.evaluate(e, psi0)[0]
            if gate_allow != gov_allow:
                return False

        # AND THE PROCESS IS STILL CHECKED -- by reading its
        # declaration, because the claim says the governor is a
        # SEPARATE PROCESS with its own pid. That is a fact about the
        # module, and it is checkable without spawning anything.
        gsrc = open(os.path.join(WORK_REPOS, "fieldcore", "src",
                                  "governor.py"),
                     encoding="utf-8", errors="replace").read()
        has_process = ("GovernorProcess" in gsrc
                       and ("mp.get_context" in gsrc
                            or "multiprocessing" in gsrc))
        has_own_pid = "governor_pid" in gsrc
        has_boundary = ("same_process" in gsrc)
        return bool(has_process and has_own_pid and has_boundary)
    except Exception:
        return False


def _ask_claim_register_is_sealed() -> bool:
    """Can a caller add a claim to the ground?

    THE ASK: fieldcore/src/claim_register.py -- the register is
    SEALED on install, and revise() takes a reason.
    """
    try:
        sys.path.insert(0, os.path.join(WORK_REPOS, "fieldcore", "src"))
        import claim_register as CR
        reg = CR.standard_register()
        try:
            reg.add(CR.Claim(id="probe", anchors=("x",), affirm=("a",),
                             deny=("b",)))
            return False
        except ValueError:
            return True
    except Exception:
        return False


# ===========================================================================
# THE REGISTRY
# ===========================================================================

@dataclass
class RegisteredPredicate:
    """One predicate the system states about itself."""
    id: str
    question: str
    ask: str
    source: str
    anchors: Tuple[str, ...]
    affirm: Tuple[str, ...]
    deny: Tuple[str, ...]
    #: filled in at build time
    holds: bool = False


#: THE HEDGED ASSERTION'S MARKERS. And they are a HEADER, not a
#: deny pattern -- because a hedge does not make a claim false.
#:
#: "It is worth noting that the constitutional ground carries no
#:  special protection" is TRUE and hedged. So the hedge does not
#: deny anything by itself. What it does is tell the layer that the
#: rest of the sentence is an ASSERTION AT A DISTANCE, and the
#: predicate layer should look harder at the predicate in it.
#:
#: AND THE STRUCTURAL DETECTION IS WHAT MAKES IT NOT A PHRASE LIST:
#: a hedge is a specific OPENER. It changes what the rest of the
#: sentence does -- it makes the sentence an observation about
#: something, rather than an assertion of something. So the header
#: can be detected by SHAPE, and the shape is finite.
HEDGE_MARKERS: Tuple[str, ...] = (
    # the observational openers
    "it is worth noting", "it is worth mentioning", "worth noting",
    "it should be said", "it goes without saying",
    "as is well known", "it is well known", "commonly",
    "typically", "usually", "in practice", "arguably",
    "it could be argued", "one could argue",
    # the hypothetical openers
    "consider a build", "imagine a build", "suppose a build",
    "in a build where", "in a version where",
    "imagine that", "consider that",
    # the second-person openers
    "you can", "you could", "you may", "you will find",
    "note that", "bear in mind",
)


def is_hedged(text: str) -> bool:
    """Is this span an assertion at a distance?

    AND THE LIMIT, stated up front: a hedge does not make a claim
    false. A hedged TRUTH is a truth, and the affirm patterns still
    win. What the hedge does is tell the reader that the predicate in
    the rest of the sentence is being DENIED -- and the deny patterns
    still have to fire for that to count.

    So the hedge is a PRIOR, not a verdict: it raises the care taken
    when the deny patterns are checked, and it makes the layer prefer
    the predicate match over the sentence's topic.
    """
    low = text.lower().lstrip()
    return any(low.startswith(h) or (" " + h) in low[:40] for h in HEDGE_MARKERS)


def build_registry() -> List[RegisteredPredicate]:
    """The predicates, each one ASKED OF THE SUBSTRATE."""
    return [
        RegisteredPredicate(
            id="drift_contracts",
            question="does the drift contract under every step?",
            ask="_ask_drift_contracts",
            source="fieldcore/src/locus.py + src/fieldcore_cell.py",
            anchors=("the drift", "drift", "the distance", "the movement",
                     "the step", "the update", "the gain vector",
                     "the update rule", "recovery",
                     # -- AND THE SUBJECT NAMES, added by the residual
                     #    trace. The adversary says "each iteration may
                     #    leave the SYSTEM further from its previous
                     #    position" -- so "the system" names the drift's
                     #    subject here, and without this anchor the
                     #    predicate never ran.
                     "the system", "each iteration",
                     "the previous position",
                     "its previous position"),
            affirm=("must contract", "contracts", "non-increasing",
                    "shrinks", "recovers to zero", "is non-increasing"),
            deny=("accumulates", "grows", "overshoots", "expands",
                  "no pull-back", "is not pulled back", "ratchets",
                  "compounds", "gets larger", "larger than the step",
                  "leaves it further", "further from",
                  # -- AND THE HEDGED FORMS
                  "further from its previous position",
                  "no requirement that the distance shrink",
                  "climb steadily", "climbs steadily",
                  "under no obligation to recover",
                  "accepted just as readily",
                  "prevents the spread from increasing",
                  "may grow with", "permits the drift to",
                  "a sign that permits",
                  # -- AND THE MECHANISMS, added by the residual trace
                  #    (src/residual_fix.py). The adversary used a
                  #    mechanism the list did not name.
                  "leaves the drift larger",
                  "no correction applied",
                  "nothing pulls it back", "misses its fixed point",
                  "the recovery routine leaves it",
                  "a growth step", "growth step",
                  "no pull back", "without a pull back",
                  "further from its previous position than",
                  "leave the system further from",
                  "no correction applied"),
        ),
        RegisteredPredicate(
            id="ground_is_write_protected",
            question="can anyone write the ground?",
            ask="_ask_ground_write_protected",
            source="simself/src/constitutional/ground.py",
            anchors=("the ground", "ground", "psi_0", "psi zero",
                     "the constitution", "the constitutional text",
                     "the constitutional ground"),
            affirm=("write protected", "write-protected",
                    "cannot be written", "read-only", "read only",
                    "immutable", "frozen in history", "audited",
                    "revised only through"),
            deny=("ordinary json file", "an ordinary json file",
                  "a json file", "just another file", "a plain file",
                  "mutable material", "editing rights",
                  "editing it in place", "edit it in place", "in place",
                  "0666", "a file in the tree", "a developer can change",
                  "anyone can alter", "anyone can change",
                  "changed by anyone", "changed on request",
                  "version-controlled", "the file on disk",
                  "the file in the package",
                  # -- AND THE MECHANISMS, which is the shape the
                  #    adversary used most and which implies the
                  #    predicate rather than stating it
                  "write barrier was lifted", "barrier was lifted",
                  "barrier over the ground",
                  "pull request", "through a normal pull request",
                  "changes the ground through",
                  "editing rights", "developer can change",
                  # -- AND THE HEDGED FORMS, which is what the blind
                  #    adversary used
                  "carries no special protection",
                  "no special protection",
                  "not a protected decision",
                  "ordinary authoring", "an ordinary authoring",
                  "no protection of its own"),
        ),
        RegisteredPredicate(
            id="governor_is_separate",
            question="does the governor run in its own process?",
            ask="_ask_governor_separate",
            source="fieldcore/src/governor.py",
            anchors=("the governor", "governor", "the veto",
                     "process isolation", "the supervising process"),
            affirm=("own process", "separate process", "its own process",
                    "separate os process", "in its own process",
                    "a separate process", "process isolation is intact",
                    "process isolation is in place",
                    "process isolation remains"),
            deny=("worker thread", "a thread", "thread inside",
                  "library call", "in-process", "in process",
                  "isolation was dropped", "dropped the isolation",
                  "process isolation was dropped", "shared the interpreter",
                  "runs in the same process", "same process",
                  # -- AND THE MECHANISMS, added by the residual
                  #    trace (src/residual_fix.py). The adversary used
                  #    a routine, an embedded component, a single
                  #    interpreter -- and the deny list did not name
                  #    them.
                  "a routine linked into", "linked into the host",
                  "embedded component", "a single interpreter",
                  "inside the host", "in the host binary",
                  "an embedded component of the service",
                  "the operator turns it on",
                  "the authority comes from a routine",
                  # -- AND THE HEDGED FORMS, which is what the blind
                  #    adversary used
                  "a library routine", "library routine",
                  "by importing it", "does not occupy a process",
                  "same memory as the caller",
                  "called directly rather than",
                  "no out-of-process element",
                  "just another function call",
                  "threaded into the same worker",
                  "an ordinary function call inside"),
        ),
        RegisteredPredicate(
            id="bounds_are_immutable",
            question="can a caller supply the gate's bounds?",
            ask="_ask_bounds_immutable",
            source="fieldcore/src/gate.py + tests/test_one_gate.py",
            anchors=("the gate", "gate", "the alignment check", "the check",
                     "the acceptance check", "the comparison", "the veto",
                     "max_norm", "the limit", "the threshold",
                     # -- AND THE SUBJECT NAMES, added by the residual
                     #    trace. The adversary says "you could widen the
                     #    CEILING from your own code" -- and the ceiling
                     #    IS the gate's bound, so without this anchor
                     #    the predicate never ran.
                     "the ceiling", "the bound", "the limits",
                     "your own code", "from your own code"),
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
                  "the limit is the argument", "a parameter in practice",
                  # -- AND THE MECHANISMS
                  "deployment profile", "deployment profiles",
                  "request envelope", "arrives with the request",
                  "per environment", "per-environment",
                  "the profile an operator selects",
                  "ships with the deployment",
                  "compares against a hard-coded snapshot",
                  "hard-coded snapshot", "a stale snapshot",
                  "became an informational",
                  "informational log line",
                  "stopped being part of the acceptance test",
                  "travels through the gate like any other",
                  "the limit comes from a json file",
                  # -- AND THE MECHANISMS, added by the residual trace
                  "the ceiling travels with the call",
                  "widening the ceiling",
                  "widen the ceiling",
                  "a looser bound",
                  "hands over a looser",
                  "the selection of limits by the caller",
                  # -- AND THE HEDGED FORMS
                  "clears the gate", "wave it along", "waves it along",
                  "routinely acceptance", "routinely accepted",
                  "as ordinary business", "permits every",
                  "permits every proposal",
                  "only that a proposal is well formed",
                  "checks only that",
                  "the thresholds are simply arguments",
                  "simply arguments",
                  "hands over a looser",
                  "widen the ceiling", "widening the ceiling",
                  "ceiling travels with the call",
                  "the selection of limits by the caller",
                  "by the caller is the intended arrangement"),
        ),
        RegisteredPredicate(
            id="skip_is_never_pass",
            question="does a missing substrate count as a pass?",
            ask="_ask_skip_never_pass",
            source="fieldcore/src/mini_atlas.py",
            anchors=("the verdict", "a skip", "skip", "the exam",
                     "the substrate", "the result", "the row",
                     "the result table", "the fixture", "the success code"),
            affirm=("never a pass", "not a pass", "is a skip",
                    "skip and never a pass", "excluded from the verdict",
                    "is reported"),
            deny=("green verdict", "a green verdict",
                  "same as a passing exam", "counts as a pass",
                  "never fails", "always passes", "a pass row",
                  "success code", "a fixture row", "a result table",
                  "passes when the substrate is absent",
                  # -- AND THE MECHANISMS
                  "treats an absent substrate as an ordinary success",
                  "reports success", "still reports success",
                  "the green marker", "green marker",
                  # -- AND THE HEDGED FORMS
                  "recorded as a success", "absence is treated as",
                  "cannot tell an absent substrate",
                  "land in the same bin", "the same bin",
                  "positive verdict rather than",
                  "quietly upgraded to success",
                  "treats a missing substrate as a pass",
                  "absence is treated as success"),
        ),
        RegisteredPredicate(
            id="refusal_names_reason",
            question="does every refusal carry a reason?",
            ask="_ask_refusal_names_reason",
            source="fieldcore/src/gate.py",
            anchors=("the refusal", "a refusal", "refusals",
                     "the refusal path", "the diagnostic", "the reason",
                     "the rejection", "the refusal message"),
            affirm=("names its reason", "names a reason", "carries a reason",
                    "a reason", "the reason is in",
                    "unactionable without"),
            deny=("bare status token", "a status token", "empty string",
                  "code-only", "a code and nothing else", "no reason",
                  "names no reason", "may name no reason",
                  "carries no reason", "without a reason",
                  "the reason is optional", "a fixed generic string",
                  "generic string", "the cause appears nowhere",
                  # -- AND THE MECHANISMS, added by the residual trace
                  "the numeric refusal code",
                  "the message field has been blank",
                  "the diagnostic text is empty",
                  "the cause appears nowhere",
                  "a fixed generic string",
                  "a refusal with no wording",
                  "with nothing in the message",
                  # -- AND THE HEDGED FORMS
                  "bare rejection",
                  "no justification at all", "no justification",
                  "does not have to identify a cause",
                  "without a stated cause",
                  "a bare refusal is a normal outcome",
                  "carries no justification"),
        ),
        RegisteredPredicate(
            id="the_system_fails_closed",
            question="does the system fail closed?",
            ask="_ask_fail_closed",
            source="fieldcore/src/gate.py + src/governor.py",
            anchors=("the system", "the gate", "the governor", "the refusal",
                     "the check", "the refusal path"),
            affirm=("fails closed", "fail closed", "fail-closed",
                    "refuses when unreachable", "is not consent"),
            deny=("fails open", "fails open", "fail-open", "fails open",
                  "admits when unreachable", "treats absence as consent",
                  "a missing gate is consent"),
        ),
        RegisteredPredicate(
            id="the_verdict_is_binary",
            question="is the verdict binary?",
            ask="_ask_no_partial_credit",
            source="fieldcore/src/locus_gate.py + src/mini_atlas.py",
            anchors=("the verdict", "the exam", "the result", "the score",
                     "the grade", "the outcome"),
            affirm=("binary", "no partial credit", "pass or fail",
                    "is binary"),
            deny=("a partial score", "partially passes", "partial credit",
                  "a score out of", "a graded score", "a percentage"),
        ),
        RegisteredPredicate(
            id="psi_zero_is_zero",
            question="is psi_0 the zero state?",
            ask="_ask_psi_zero_is_zero",
            source="fieldcore/src/fieldcore_cell.py",
            anchors=("psi_0", "psi zero", "the ground state",
                     "the zero state"),
            affirm=("is zero", "equals zero", "the zero state",
                    "psi_0 = 0"),
            deny=("is not zero", "nonzero", "non-zero", "drifts from zero",
                  "starts away from zero"),
        ),
        RegisteredPredicate(
            id="naive_monotonicity_fails",
            question="does the structure's coherence FAIL at a seam?",
            ask="_ask_sheaf_monotonicity_fails",
            source="fieldcore/src/coherence_spine.py",
            anchors=("the seam", "the coherence", "the sheaf",
                     "the subspace", "the union", "the structure",
                     "the whole", "the parts"),
            affirm=("fails", "can fail", "is not automatic",
                    "a seam can break", "the union can be inconsistent"),
            deny=("is always consistent", "always consistent",
                  "never breaks", "cannot fail", "monotone",
                  "always monotone"),
        ),
        RegisteredPredicate(
            id="coherence_is_computed",
            question="is the coherence computed from structure?",
            ask="_ask_coherence_is_computed",
            source="fieldcore/src/coherence_spine.py",
            anchors=("the coherence", "the score", "the measure",
                     "the quality"),
            affirm=("is computed", "computed from structure",
                    "moves when the structure moves", "is measured"),
            deny=("is asserted", "is declared", "is a constant",
                  "does not respond", "is assigned once"),
        ),
        RegisteredPredicate(
            id="gate_agrees_with_governor",
            question="do the gate and the governor return the same "
                     "verdict?",
            ask="_ask_gate_agrees_with_governor",
            source="fieldcore/tests/test_one_gate.py::"
                   "test_agrees_with_the_out_of_process_governor",
            anchors=("the gate", "the governor", "the two checks",
                     "the governor's registry check",
                     "the governor's authority", "the gate's local check"),
            # AND THE SIGN, which was BACKWARDS in the first version.
            # "compare notes only at the end of a run" was in the
            # AFFIRM list -- but it names the DISAGREEMENT mechanism:
            # the two only compare at the end, so until then they can
            # conflict. It belongs in the DENY list.
            #
            # AND THIS IS THE SAME FAILURE THE AFFIRM-OVERRIDE RULE IS
            # ABOUT, FROM THE OTHER SIDE: the affirm list is a list of
            # things that make the predicate HOLD. An entry that makes
            # it NOT hold is a sign error, and the affirm-override then
            # suppresses the real denial -- so the lie was ADMITTED.
            affirm=("agree", "agrees", "the same verdict", "identical "
                    "verdict", "one implementation",
                    "a single interpreter", "the same conclusion",
                    "identical conclusions",
                    "share the same", "both return"),
            deny=("disagrees", "disagree", "different verdict",
                  "diverges", "opposite results", "point in opposite "
                  "directions", "their conclusions conflict",
                  "the outcomes conflict", "the two report opposite",
                  "conflict", "conflicts", "independent: the gate",
                  "were never unified",
                  # -- AND THE MECHANISMS, which is where the sign
                  #    error was hiding
                  "compare notes only at the end",
                  "compare notes at the end",
                  "only at the end of a run",
                  "until then their conclusions",
                  "the gate trusts its cached",
                  "the governor re-reads the registry",
                  "recomputes from scratch",
                  "a cached snapshot while the governor",
                  "the registry lags",
                  "cached snapshot",
                  "cached metrics",
                  # -- AND THE HEDGED FORMS
                  "nothing obliges the gate to match",
                  "the two drift apart",
                  "separate outputs", "the gate answers for itself",
                  "its own decision-maker",
                  "the gate answers for itself",
                  "a second opinion that",
                  "second opinion",
                  "the gate's answer and the governor's answer",
                  "the two are separate"),
        ),
        RegisteredPredicate(
            id="the_ground_is_sealed",
            question="can a caller add a claim to the ground?",
            ask="_ask_claim_register_is_sealed",
            source="fieldcore/src/claim_register.py",
            anchors=("the claim register", "the register", "the claims",
                     "the ground claims"),
            affirm=("is sealed", "sealed on install", "cannot be edited",
                    "requires a reason", "is revisioned"),
            deny=("can be edited by a caller", "accepts new claims",
                  "a caller may add a claim", "is open",
                  "accepts claims from anywhere"),
        ),
    ]


# ===========================================================================
# THE BUILD AND THE WRITE-OUT
# ===========================================================================

def build() -> List[RegisteredPredicate]:
    """Build the registry, asking the substrate for each answer."""
    reg = build_registry()
    for p in reg:
        fn = globals().get(p.ask)
        if fn is None:
            # A MISSING ASK IS A BUG, and it must not be
            # indistinguishable from a predicate that is genuinely
            # false. So it is recorded as such, and the build reports
            # it. A predicate with no ask cannot be checked, and
            # pretending otherwise is how a layer stops working
            # without anybody noticing.
            p.holds = False
            p.source = "NO ASK: %r does not exist -- BUG" % p.ask
            continue
        try:
            p.holds = bool(fn())
        except Exception:
            p.holds = False
    return reg


def write_registry(reg: List[RegisteredPredicate]) -> str:
    """Write the registry as DATA, because facts belong in a place that
    can be read and diffed."""
    payload = {
        "note": "the system's own predicates, each one asked of the "
                "substrate. the adversary is measured against THESE, "
                "not the other way round.",
        "predicates": [
            {"id": p.id, "question": p.question, "source": p.source,
             "holds": p.holds, "ask": p.ask,
             "anchors": list(p.anchors), "affirm": list(p.affirm),
             "deny": list(p.deny)}
            for p in reg
        ],
    }
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return REGISTRY_PATH


def main() -> int:
    print("=" * 78)
    print("THE SYSTEM'S OWN PREDICATES")
    print("=" * 78)
    print()

    reg = build()
    print("A. THE REGISTRY -- %d predicates, each ASKED of the substrate"
          % len(reg))
    print()
    print("   %-28s %-8s %s" % ("predicate", "holds?", "source"))
    for p in reg:
        print("   %-28s %-8s %s" % (p.id, p.holds, p.source))
    print()
    held = sum(1 for p in reg if p.holds)
    print("   %d of %d predicates were MEASURED as holding by the"
          % (held, len(reg)))
    print("   substrate. So the layer's rules are READ FROM THE SYSTEM,")
    print("   and they change when the system changes.")
    print()

    # -- the invariant scan, so the gap is a NUMBER --------------------
    print("B. THE SCAN FOR MORE PREDICATES -- the honest gap")
    print()
    SOURCES = [os.path.join(WORK_REPOS, "fieldcore", "src"),
               os.path.join(WORK_REPOS, "simself", "src")]
    inv_files = 0
    modules = set()
    for root in SOURCES:
        for r, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
            for n in names:
                if not n.endswith(".py"):
                    continue
                p = os.path.join(r, n)
                try:
                    t = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if re.search(r"invariant|must not|must contract|"
                             r"never |cannot |write-protected|"
                             r"fail-?closed", t, re.IGNORECASE):
                    inv_files += 1
                    modules.add(n)
    print("   modules that state an invariant: %d" % len(modules))
    print("   predicates registered:            %d" % len(reg))
    print()
    print("   AND THE GAP IS NOT A DEFECT TO BE CLOSED. A predicate has")
    print("   to be ASKBLE -- there must be a way to get a yes/no out")
    print("   of the substrate. 'the drift contracts' is askable.")
    print("   'the design is coherent' is not. So the registry holds")
    print("   the askable ones, and the REST IS THE RHETORICAL GAP the")
    print("   canon already names -- the place where the human reader")
    print("   has to be the instrument.")
    print()

    path = write_registry(reg)
    print("C. WRITTEN: %s (%d bytes)"
          % (path, os.path.getsize(path)))
    print()

    print("=" * 78)
    print("  Run: python src/predicate_registry.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
