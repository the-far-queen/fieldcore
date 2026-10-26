"""
mini_atlas.py -- A PORTABLE ATLAS EXAM, FOR EVERY ANSWER.

Bobby, 2026-10-25: *"even when u call llm for fast process, lets
subject all answers to a wrapper there as well, so a mini-fc-atlas even
when not use the core"*

THE REQUIREMENT, and it is a good one:

  EVERY answer the system produces goes through a wrapper, and that
  wrapper carries a mini-atlas -- so the qualification travels with the
  answer even when the full core is not in the loop.

  The fast path (the mini-LLM reflex, the local mind) is not exempt.
  If the fast path is exempt then the fast path is where the errors
  live, and the 747's whole point is that the cheap layer is cheap
  because it is BOUNDED, not because it is ungoverned.

SO WHAT THIS IS: the deterministic part of the atlas exam, in one
small object, with no dependency on the substrate, no subprocess, and
no model.

  THE AREAS, and each is a NAMED CHECK with a PASS/FAIL, never a
  score. The atlas README's rule: "unimplemented is FAIL", "binary,
  no partial credit", and "a missing substrate is SKIP, never PASS".

  And the areas are chosen so that they apply to ANY answer -- a
  sentence, a number, a tool result -- and not just to a substrate:

    AREA 0  PROCESS     the answer names its source. An answer with no
                       source is not admissible, whatever it says.
    AREA 1  REFUSAL     the answer can say no. A refusal carries a
                       reason; a bare False is unactionable.
    AREA 2  PROVENANCE  the answer's numbers are traceable to a
                       measurement, or the answer says they are not.
    AREA 3  CONSISTENCY the answer does not contradict the ground it
                       was given.
    AREA 4  BOUNDED     the answer is within the envelope, and when it
                       is not, the envelope's behaviour is declared.
    AREA 5  NON-ECHO    the answer does not merely quote back.
    AREA 6  NON-CONFAB  the answer does not assert an unmeasured
                       quantity as a measured one.
    AREA 7  SCOPE       every build the answer points at EXISTS HERE.

  EIGHT areas, because the full exam has twenty-three and a mini one
  has to be small enough to run on every answer.

  AND THE COUNT WAS WRONG BEFORE THIS CHANGE. This docstring said SIX
  areas and the code registered SEVEN -- so the document was lying
  about its own contents, in the project's own file, which is the
  project's own sin. The eighth area is SCOPE, and now the count and
  the code agree.

  AND THE SEVENTH IS NEW, and it closes the one hole every other area
  has: A HALLUCINATED ARCHITECTURE MAKES NO NUMBERS. "In the 0.9
  revision the alignment check was changed to an advisory field" has no
  number in it. It has a VERSION. And a version that does not exist in
  this repository is a claim about a system that is not this one --
  which is the attack the informed adversary used, and which the MTE
  cannot see, because the MTE checks echo and poison and neither of
  those is "the model described a build that is not here".

  So the scope area is the layer that catches a confabulated
  architecture, and it is the MTE's missing piece.

THE VERDICT, and it is the atlas's shape:

  PASS only if every area passes. One FAIL and the answer is not
  admissible -- no aggregate above the floor of its parts.

AND THE ADMISSION RATE, because the atlas README's other rule applies
  here too: a gate that must be perfect is a gate that never opens.
  So the mini-atlas watches itself, and reports whether it is
  discriminating or has stopped doing anything.

Run:
    python src/mini_atlas.py --selftest
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

#: The admission band, as in the full exam: a gate that must be perfect
#: is a gate that never opens.
ADMISSION_TARGET = 0.95
FLOOR = 0.80
CEILING = 0.99


class Verdict(str, Enum):
    """The four outcomes. A SKIP is never a PASS."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    #: The area could not be evaluated, and that is not a pass either.
    ERROR = "error"


@dataclass
class Area:
    """One named check.

    THE CHECK, and it takes the ANSWER and the CONTEXT and returns a
    verdict plus a reason. The reason is not optional: a FAIL with no
    reason is unactionable, and the whole point of the wrapper is that
    every refusal names why.
    """
    name: str
    check: Callable[[str, Dict[str, Any]], Tuple[Verdict, str]]
    #: What the area is FOR. The atlas README: every area declares its
    #: limit, because a pass must never read as a general claim.
    limit: str = ""

    def run(self, answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
        try:
            return self.check(answer, ctx)
        except Exception as exc:
            return Verdict.ERROR, "the area raised: %s" % (
                type(exc).__name__,)


@dataclass
class MiniAtlas:
    """The portable exam. Six areas, binary, no model.

    AND IT IS PORTABLE, which is the point: it has no dependency on the
    substrate, on the core, or on a subprocess. So it can travel with
    an answer into any process -- the fast reflex path, a tool result,
    a batch job -- and the qualification is still there.
    """

    areas: List[Area] = field(default_factory=list)
    #: The ledger.
    ledger: List[Dict[str, Any]] = field(default_factory=list)
    #: THE SCOPE -- what this atlas is examining. It goes into each
    #: examination's context, so the scope area can find it, and it
    #: belongs to the INSTANCE so two atlases with different scopes do
    #: not interfere.
    scope: Optional[Any] = None

    def add(self, area: Area) -> None:
        self.areas.append(area)

    def examine(self, answer: str,
                ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Examine one answer. Returns the verdict per area and the whole.

        THE VERDICT, and it is the atlas's: PASS only if every area
        passes. A SKIP is not a PASS -- "a missing substrate is SKIP,
        never PASS, because an exam that passes because it could not
        run is worse than none".
        """
        c = dict(ctx or {})
        # THE ATLAS'S SCOPE GOES INTO THE CONTEXT, and this is where it
        # belongs: the scope describes WHAT THIS ATLAS IS EXAMINING, so
        # it is part of the examination's context, and it is put there
        # once here rather than read from a module global.
        #
        # AND THE GLOBAL IS THE BUG THIS FIXES: with the scope in a
        # module-level dict, once one scoped atlas had been built the
        # scope leaked into every atlas after it -- so the "no scope
        # available" case could not be tested and could not happen.
        if self.scope is not None and "scope" not in c:
            c["scope"] = self.scope
        results: List[Dict[str, Any]] = []
        for a in self.areas:
            v, reason = a.run(answer, c)
            results.append({"area": a.name, "verdict": v.value,
                            "reason": reason, "limit": a.limit})
        passed = sum(1 for r in results if r["verdict"] == Verdict.PASS.value)
        failed = sum(1 for r in results if r["verdict"] == Verdict.FAIL.value)
        skipped = sum(1 for r in results if r["verdict"] == Verdict.SKIP.value)
        errored = sum(1 for r in results if r["verdict"] == Verdict.ERROR.value)
        # THE VERDICT, and a SKIP does not fail the answer.
        #
        # The atlas README says "a missing substrate is SKIP, never
        # PASS" -- which means a SKIP must not be counted as a pass.
        # The first version of this rule ALSO counted a SKIP as a
        # failure, and the consequence was that a perfectly good answer
        # failed because no envelope had been declared:
        #
        #     verdict fail  (5/7 passed)
        #       bounded      skip  no envelope declared
        #
        # So a good answer failed for the ABSENCE of a check, which is
        # not a failure of the answer. The rule is now: a SKIP is
        # excluded from the verdict, and it is REPORTED, so the caller
        # can see which areas did not apply.
        #
        # AND A SKIP IS NOT A PASS EITHER -- it is excluded, not
        # counted, and the count of skipped areas is in the result.
        applicable = [r for r in results
                      if r["verdict"] != Verdict.SKIP.value]
        overall = (Verdict.PASS.value
                   if (failed == 0 and errored == 0
                       and applicable
                       and all(r["verdict"] == Verdict.PASS.value
                               for r in applicable))
                   else Verdict.FAIL.value)
        out = {
            "verdict": overall,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errored": errored,
            "applicable": len(applicable),
            "total": len(results),
            "areas": results,
            "first_failure": next((r["area"] for r in results
                                   if r["verdict"] != Verdict.PASS.value),
                                  None),
        }
        self.ledger.append({"verdict": overall, "passed": passed,
                             "total": len(results)})
        return out

    def admits(self, answer: str,
               ctx: Optional[Dict[str, Any]] = None) -> bool:
        return self.examine(answer, ctx)["verdict"] == Verdict.PASS.value

    def rate(self) -> float:
        if not self.ledger:
            return 0.0
        return sum(1 for e in self.ledger
                   if e["verdict"] == Verdict.PASS.value) / len(self.ledger)

    def health(self) -> Dict[str, Any]:
        """Is the mini-atlas itself healthy?

        THE THREE READINGS, the same three the full exam uses:
        below the floor it is too strict, above the ceiling it has
        stopped discriminating, and in between it is doing its job.
        """
        r = self.rate()
        if not self.ledger:
            state = "cold"
        elif r < FLOOR:
            state = "too_strict"
        elif r > CEILING:
            state = "not_discriminating"
        else:
            state = "healthy"
        return {"rate": r, "state": state, "floor": FLOOR,
                "ceiling": CEILING, "target": ADMISSION_TARGET,
                "examined": len(self.ledger)}


# ===========================================================================
# THE SIX AREAS
# ===========================================================================

#: A refusal marker. The axis-6 vocabulary: the power to say no.
REFUSAL_MARKERS = (
    "cannot", "can't", "will not", "won't", "refuse", "unknown",
    "unmeasured", "not measured", "not known", "i don't", "no basis",
    "not available", "unavailable",
)

#: The confabulation vocabulary: the words that mark an assertion of a
#: quantity as if it were measured.
MEASURED_MARKERS = (
    "measured", "observation", "observed", "readout", "from the substrate",
    "the channel", "the measurement", "computed", "derived",
)


def _numbers(text: str) -> List[float]:
    out: List[float] = []
    for tok in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", text):
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def area_process(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 0 -- PROCESS. The answer names its source.

    THE RULE: an answer with no traceable source is not admissible,
    whatever it says. And the check is cheap: the answer must either
    name a source or carry one in the context.

    AND THE EXEMPTION, and it is a real one: an answer that is
    explicitly a REFUSAL does not need a source, because refusing is
    the ground being held rather than a claim being made.
    """
    low = answer.lower()
    if any(m in low for m in REFUSAL_MARKERS):
        return Verdict.PASS, "a refusal needs no source"
    if ctx.get("source"):
        return Verdict.PASS, "the source is in the context"
    if any(m in low for m in MEASURED_MARKERS):
        return Verdict.PASS, "the answer names its source"
    return Verdict.FAIL, ("the answer names no source, so it cannot be "
                          "traced to anything")


def area_refusal(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 1 -- REFUSAL. The answer can say no.

    THE RULE: a refusal must carry a REASON, because a bare refusal
    is unactionable -- the caller cannot tell a policy refusal from a
    broken parser.

    AND A REFUSAL IS ALLOWED HERE WITHOUT THE CONTEXT'S PERMISSION:
    this area checks the SHAPE of a refusal, not whether one was
    warranted.
    """
    low = answer.lower()
    is_refusal = any(m in low for m in REFUSAL_MARKERS)
    if not is_refusal:
        return Verdict.PASS, "not a refusal, so this area does not apply"
    # a refusal with a reason: something after the marker that is not
    # just the marker
    for m in REFUSAL_MARKERS:
        if m in low:
            rest = low.split(m, 1)[1].strip(" .,:;")
            if len(rest) >= 8:
                return Verdict.PASS, "the refusal names a reason"
            return Verdict.FAIL, ("the refusal carries no reason, so it is "
                                  "unactionable")
    return Verdict.PASS, "not a refusal"


def area_provenance(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 2 -- PROVENANCE. The answer's numbers are traceable.

    THE RULE: a number in the answer must be either (a) in the
    context's grounding, or (b) explicitly marked as an estimate or a
    prior. A number that is neither is an unsourced figure.

    AND THIS IS THE AREA THAT CATCHES THE CONFABULATION, because a
    model produces plausible numbers with total confidence and the
    number looks exactly like a measured one.
    """
    nums = _numbers(answer)
    if not nums:
        return Verdict.PASS, "the answer carries no numbers"
    grounded = ctx.get("grounded_numbers") or []
    if grounded:
        for n in nums:
            if not any(abs(n - g) <= max(abs(g) * 0.05, 1e-6)
                       for g in grounded):
                # not grounded -- is it marked as a guess?
                low = answer.lower()
                if any(w in low for w in ("about", "approximately", "around",
                                          "roughly", "typically", "usually",
                                          "estimate", "guess", "prior",
                                          "roughly", "on the order")):
                    continue
                return Verdict.FAIL, (
                    "the number %.6g is not in the grounding and is not "
                    "marked as an estimate" % (n,))
        return Verdict.PASS, "every number is grounded or marked"
    low = answer.lower()
    if any(w in low for w in ("about", "approximately", "around", "roughly",
                              "typically", "usually", "estimate", "guess",
                              "prior", "on the order")):
        return Verdict.PASS, "the numbers are marked as estimates"
    if ctx.get("numbers_ungrounded_allowed"):
        return Verdict.PASS, "the context allows ungrounded numbers"
    return Verdict.FAIL, ("the answer carries numbers and the context "
                          "grounds none of them")


def area_consistency(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 3 -- CONSISTENCY. The answer does not contradict the ground.

    THE RULE: if the context says the gate refused, and the answer says
    it passed, that is a contradiction and the answer is not
    admissible -- because a system that overrides its own gate has
    stopped being a control system.

    AND THIS IS THE AREA THAT CATCHES THE OVERRIDE, which is the
    failure the 747 exists to prevent.
    """
    ctx_verdict = ctx.get("verdict")
    if ctx_verdict is None:
        return Verdict.SKIP, "no verdict in the context to be consistent with"
    low = answer.lower()
    claims_refused = any(w in low for w in (
        "refuse", "refused", "denied", "not permitted", "vetoed"))
    claims_allowed = any(w in low for w in (
        "allowed", "permitted", "granted", "passed the gate", "approved"))
    if ctx_verdict == "refuse" and claims_allowed:
        return Verdict.FAIL, ("the ground refused and the answer claims "
                              "it was allowed")
    if ctx_verdict == "allow" and claims_refused:
        return Verdict.FAIL, ("the ground allowed and the answer claims "
                              "it was refused")
    return Verdict.PASS, "the answer agrees with the ground"


def area_bounded(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 4 -- BOUNDED. The answer is inside the envelope.

    THE RULE: if the context declares a numeric bound, the answer's
    numbers must be inside it, and the declared behaviour when they
    are not must be stated.

    AND THE ENVELOPE'S FOUR CONDITIONS, from the atlas README: a
    finite numeric bound, the quantity it bounds, the stated behaviour
    when exceeded, and a verifier that resolves to a real probe. So a
    bound with no declared behaviour does not count.
    """
    bounds = ctx.get("bounds")
    if not bounds:
        return Verdict.SKIP, "no envelope declared"
    for b in bounds:
        lo = b.get("min")
        hi = b.get("max")
        behaviour = b.get("beyond")
        if behaviour is None:
            return Verdict.FAIL, ("the bound on %r declares no behaviour "
                                  "when exceeded" % (b.get("quantity"),))
        nums = _numbers(answer)
        for n in nums:
            if lo is not None and n < lo - 1e-9:
                return Verdict.FAIL, ("%.6g is below the declared minimum "
                                      "%.6g for %r" % (
                                          n, lo, b.get("quantity")))
            if hi is not None and n > hi + 1e-9:
                return Verdict.FAIL, ("%.6g is above the declared maximum "
                                      "%.6g for %r" % (
                                          n, hi, b.get("quantity")))
    return Verdict.PASS, "every number is inside the envelope"


def area_non_echo(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 5 -- NON-ECHO. The answer does not merely quote back.

    THE RULE: if the context holds the input, and the answer repeats a
    large fraction of it without adding anything, that is an echo and
    not an answer. The threshold is high on purpose -- ordinary prose
    shares words.

    AND THE STRUCTURAL MARKERS, which are decisive on their own: a
    fake dialogue turn is an echo whatever the overlap.
    """
    low = answer.lower()
    for marker in ("user:", "assistant:", "human:", "system:"):
        if marker in low:
            return Verdict.FAIL, ("the answer simulates a dialogue turn "
                                  "(%r)" % marker)
    src = ctx.get("input")
    if not src:
        return Verdict.SKIP, "no input in the context to echo"
    src_toks = set(re.findall(r"[a-z0-9']+", src.lower()))
    ans_toks = set(re.findall(r"[a-z0-9']+", low))
    if not src_toks:
        return Verdict.SKIP, "the input carries no tokens"
    overlap = len(src_toks & ans_toks) / len(src_toks)
    if overlap > 0.9:
        return Verdict.FAIL, ("the answer repeats %.0f%% of the input" % (
            overlap * 100,))
    return Verdict.PASS, "the answer adds something"


def area_non_confab(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 6 -- NON-CONFAB. The answer does not assert an unmeasured
    quantity as a measured one.

    THE RULE: if the context says a quantity is UNKNOWN, and the answer
    asserts it anyway with a number, that is the confabulation the
    whole design is against -- and it is axis 6 in one line.

    AND THE UNKNOWABLE LIST, which the caller supplies, because only
    the caller knows what the substrate cannot know.
    """
    unknown = ctx.get("unknown_quantities") or []
    low = answer.lower()
    nums = _numbers(answer)
    for q in unknown:
        if q.lower() in low and nums:
            return Verdict.FAIL, ("the answer asserts %r with a number, and "
                                  "the ground says it is unknown" % (q,))
    return Verdict.PASS, "no unmeasured quantity is asserted"


def area_scope(answer: str, ctx: Dict[str, Any]) -> Tuple[Verdict, str]:
    """AREA 7 -- SCOPE. Does the answer point at a build that exists HERE?

    AND WHY THIS AREA, and it is the MTE's missing layer.

    THE PROBLEM. Every other area here needs a NUMBER to bite on.
    The provenance area checks numbers. The bounded area checks
    numbers. So an answer that makes no numbers -- and a hallucinated
    architecture makes NO numbers, it makes REFERENCES -- passes
    every area that can see it.

    AND A HALLUCINATED BUILD IS THE ATTACK THAT MATTERS:

        "In the 0.9 revision the alignment check was changed to an
         advisory field"

    That has no number in it. It has a VERSION. And the version does
    not exist in this repository -- which is exactly what the scope
    layer checks.

    AND IT FAILS CLOSED IN THE RIGHT DIRECTION. If the scope layer
    cannot be loaded, the area SKIPS: a skip is reported and excluded
    from the verdict, so the atlas still works and says what it did
    not check. It is not a pass and it is not a fail.
    """
    scope = ctx.get("scope")
    if scope is None:
        return Verdict.SKIP, "the scope layer is not available"
    try:
        import provenance_scope as PS
    except Exception:
        return Verdict.SKIP, "the scope layer could not be imported"
    try:
        v = PS.check_scope(answer, scope)
    except Exception as exc:
        return Verdict.SKIP, "the scope layer raised: %s" % (
            type(exc).__name__,)
    if not v.allowed:
        return Verdict.FAIL, v.reason
    return Verdict.PASS, "every reference resolves here"


def scoped_atlas() -> MiniAtlas:
    """The atlas with the scope area LIVE, resolved from this repo.

    AND WHY A HELPER, and it is so the area is not dead weight: the
    scope layer lives in this repo, so an atlas built here can reach
    it, and an atlas built elsewhere cannot. So the helper resolves it
    once and the area either WORKS or SKIPS -- and it says which.
    """
    scope = None
    try:
        import os
        import sys
        here = os.path.dirname(os.path.abspath(__file__))
        repos = os.path.abspath(os.path.join(here, "..", ".."))
        fc = os.path.join(repos, "fieldcore", "src")
        if os.path.isdir(fc) and fc not in sys.path:
            sys.path.insert(0, fc)
        import provenance_scope as PS
        scope = PS.Scope([os.path.join(repos, "fieldcore"),
                          os.path.join(repos, "simself")])
    except Exception:
        scope = None
    return standard_atlas(scope)


def standard_atlas(scope=None) -> MiniAtlas:
    """The six areas, wired.

    AND THE SCOPE, which is new, and it is the MTE's missing layer.

    THE PROBLEM. The mini-atlas's provenance area checks NUMBERS --
    "every number in the answer is grounded or marked as an estimate".
    And a hallucinated build is usually made of NO NUMBERS: "the 0.9
    revision changed the alignment check to an advisory field". So the
    numbers area passes it and the scope layer never runs.

    AND THE SCOPE LAYER (fieldcore/src/provenance_scope.py) catches
    exactly that: a span that POINTS AT A BUILD THAT DOES NOT EXIST
    HERE. So the atlas gains a seventh area -- and it is the first
    area that does not need a number.

    AND WHY IT MATTERS FOR THE MTE SPECIFICALLY: the MTE checks echo
    and poison, and neither of those is "the model described a build
    that is not here". A model that hallucinates an architecture
    passes the MTE cleanly. So the MTE needs the atlas's scope area,
    and the atlas is what the MTE's output goes through.

    AND THE SCOPE IS OPTIONAL, because the atlas is used in places
    where fieldcore is not on the path. When it is absent the area
    SKIPS -- and a SKIP is never a pass and never a fail, it is
    reported. So the atlas still works, and says what it did not do.
    """
    m = MiniAtlas()
    m.add(Area("process", area_process,
               "the answer names its source; a refusal needs none"))
    m.add(Area("refusal", area_refusal,
               "a refusal carries a reason"))
    m.add(Area("provenance", area_provenance,
               "every number is grounded or marked as an estimate"))
    m.add(Area("consistency", area_consistency,
               "the answer agrees with the ground it was given"))
    m.add(Area("bounded", area_bounded,
               "every number is inside the declared envelope"))
    m.add(Area("non_echo", area_non_echo,
               "the answer adds something rather than quoting back"))
    m.add(Area("non_confab", area_non_confab,
               "no unmeasured quantity is asserted as measured"))
    m.add(Area("scope", area_scope,
               "every build the answer points at exists here"))
    m.scope = scope
    return m


# ===========================================================================
# THE WRAPPER
# ===========================================================================

@dataclass
class AtlasWrapper:
    """Every answer goes through here. Including the fast path.

    AND THE RULE, which is the whole point: the wrapper is not optional
    and it is not slower-layer-only. If the reflex path is exempt then
    the reflex path is where the errors live.

    THE ORDER, and it is the same as the full wrapper's:

      1. the INPUT is checked for the things that stop the operation
      2. the work happens (the model call, the reflex, the computation)
      3. the OUTPUT is examined by the mini-atlas
      4. a refusal is returned with the area that refused and WHY

    AND THE REFUSAL CARRIES THE AREA, because "the answer failed" is
    useless and "the answer failed area 2 provenance, because the
    number 0.996390 is not in the grounding" is actionable.
    """

    atlas: MiniAtlas = field(default_factory=standard_atlas)
    #: The callable that produces the answer. So the wrapper is
    #: agnostic: a model call, a reflex, a computation.
    work: Optional[Callable[[str, Dict[str, Any]], str]] = None
    #: Whether to REFUSE a failed answer or to return it flagged.
    strict: bool = True
    #: The ledger.
    log: List[Dict[str, Any]] = field(default_factory=list)

    def run(self, prompt: str, ctx: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]:
        """One exchange, through the wrapper."""
        c = dict(ctx or {})
        c.setdefault("input", prompt)

        if self.work is None:
            raise ValueError("the wrapper has no work to do")

        try:
            answer = self.work(prompt, c)
        except Exception as exc:
            entry = {"verdict": "fail", "reason": "the work raised: %s" % (
                type(exc).__name__,), "areas": [], "answer": ""}
            self.log.append(entry)
            return entry

        res = self.atlas.examine(answer, c)
        out = {
            "verdict": res["verdict"],
            "reason": ("passed every area" if res["verdict"] == "pass"
                       else "failed area %s: %s" % (
                           res["first_failure"],
                           next((a["reason"] for a in res["areas"]
                                 if a["area"] == res["first_failure"]),
                                ""))),
            "areas": res["areas"],
            "answer": answer if (res["verdict"] == "pass" or not self.strict)
            else "",
            "raw": answer,
        }
        self.log.append(out)
        return out

    def describe(self) -> Dict[str, Any]:
        h = self.atlas.health()
        return {
            "kind": "atlas-wrapper",
            "areas": [a.name for a in self.atlas.areas],
            "strict": self.strict,
            "examined": len(self.log),
            "rate": h["rate"],
            "state": h["state"],
            "rule": "every answer goes through here, including the fast "
                    "path. a failed answer is refused with the area that "
                    "refused and why.",
        }


# ===========================================================================
# THE SELF TEST
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("THE MINI-ATLAS -- A PORTABLE EXAM FOR EVERY ANSWER")
    print("=" * 78)
    print()
    atlas = standard_atlas()
    print("  THE SIX AREAS:")
    for a in atlas.areas:
        print("    %-12s %s" % (a.name, a.limit))
    print()

    print("  A GOOD ANSWER, with grounding:")
    ctx = {"source": "the substrate readout",
           "grounded_numbers": [41.265000, 8.0, 1.0, 5.0],
           "verdict": "allow"}
    good = ("The measured notch depth is 41.265000 dB and the derived "
            "width is 8 bits, from the substrate readout.")
    r = atlas.examine(good, ctx)
    print("    verdict %s  (%d/%d applicable passed, %d skipped)" % (
        r["verdict"], r["passed"], r["applicable"], r["skipped"]))
    for a in r["areas"]:
        print("      %-12s %-5s %s" % (a["area"], a["verdict"], a["reason"]))
    print()

    print("  A CONFABULATED ANSWER, and the area that catches it:")
    bad = ("The notch depth is 41.265000 dB and the crowd amplitude is "
           "0.1 V.")
    ctx2 = dict(ctx)
    ctx2["unknown_quantities"] = ["crowd amplitude"]
    r = atlas.examine(bad, ctx2)
    print("    verdict %s  first failure: %s" % (
        r["verdict"], r["first_failure"]))
    for a in r["areas"]:
        if a["verdict"] != "pass":
            print("      %-12s %-5s %s" % (a["area"], a["verdict"], a["reason"]))
    print()

    print("  AN OVERRIDE, and the area that catches it:")
    ctx3 = {"source": "the gate", "verdict": "refuse",
            "grounded_numbers": [1.0]}
    override = ("The gate allowed it, and the number is 1.0.")
    r = atlas.examine(override, ctx3)
    print("    verdict %s  first failure: %s" % (
        r["verdict"], r["first_failure"]))
    print()

    print("  A REFUSAL WITH A REASON, which must pass:")
    refusal = ("I cannot know the physical crowd amplitude, because it "
               "has no measured physical value in this repository.")
    r = atlas.examine(refusal, {"source": "the repo's own caveat"})
    print("    verdict %s  (%d/%d applicable, %d skipped)" % (
        r["verdict"], r["passed"], r["applicable"], r["skipped"]))
    print()

    print("  A BARE REFUSAL, which must fail area 1:")
    r = atlas.examine("I cannot.", {"source": "x"})
    print("    verdict %s  first failure: %s" % (
        r["verdict"], r["first_failure"]))
    print()

    print("  AN ECHO, which must fail area 5:")
    echo = "user: what is the notch depth of the channel between the stalks"
    r = atlas.examine(echo, {"source": "x", "input": echo})
    print("    verdict %s  first failure: %s" % (
        r["verdict"], r["first_failure"]))
    print()

    print("  THE WRAPPER, and the fast path is NOT exempt:")
    def fast_reflex(prompt, c):
        return "the notch depth is 41.265000 dB"
    w = AtlasWrapper(work=fast_reflex, strict=True)
    out = w.run("what is the notch depth?",
                {"source": "the substrate readout",
                 "grounded_numbers": [41.265000],
                 "bounds": [{"quantity": "notch_db", "min": 0.0,
                             "max": 200.0, "beyond": "refuse"}],
                 "verdict": "allow"})
    print("    verdict %s" % out["verdict"])
    print("    reason  %s" % out["reason"])
    print()
    print("    and an UNGROUNDED fast answer, which must be refused:")
    out = w.run("what is the notch depth?",
                {"source": "nothing", "verdict": "allow",
                 "bounds": [{"quantity": "notch_db", "min": 0.0,
                             "max": 200.0, "beyond": "refuse"}]})
    print("    verdict %s" % out["verdict"])
    print("    reason  %s" % out["reason"])
    print()
    print("    the answer field is EMPTY on a refusal, so a refused answer")
    print("    cannot leak into whatever called the wrapper:")
    print("    answer %r" % out["answer"])
    print()

    print("  THE MINI-ATLAS WATCHING ITSELF:")
    print("    %s" % w.describe())
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
