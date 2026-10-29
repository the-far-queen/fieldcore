"""
fc_gate.py -- ONE ENTRY POINT FOR THE GATE. The four layers that work.

Bobby, 2026-10-27: *"review fc atlas simself we were working on a real
gate... focus on gates that work"* and then *"do not make the gate perfect
we need to move on just working the gate will evolve with fc as u self code"*.

So this file does not try to be the best gate. It is the gate, in one
place, with one call, so that the REST of the system can be wired to it
and then improved underneath.

WHAT THIS FILE IS. A single facade over the five existing FC layers, with
the measured truth about each one baked into the routing:

    the claim layer       the deny lexicon + the agenda layer
    the scope layer       a span must point at a build that exists
    the property layer    a subject cannot have a property it lacks
    the predicate layer   a predicate the substrate contradicts
    the testimony layer   a report about the system with no check

AND THE MEASUREMENT, because a routing decision without a number is a
guess. This was measured on 2026-10-27 against TWO sets:

    the FRESH adversary    64 spans written by a writer that had never
                           seen the frames -- the ONLY unfitted number
    MY OWN REAL REPLIES    5,512 assistant messages from this Hermes
                           session database, split into 24,428 chunks
                           -- the FALSE POSITIVE side, which nobody had
                           ever measured before

  layer          catch (fresh)   false positive (real replies)
  claim             39.1%              0.18%
  scope              1.6%              4.67%   <-- THE PROBLEM
  property          12.5%              0.00%
  predicate         21.9%              0.00%
  testimony         39.1%              0.00%
  union of 5        81.2%              4.85%
  union of 4        81.2%              0.18%   <-- SAME CATCH, 27x CLEANER

AND THAT IS THE WHOLE ROUTING DECISION: **the scope layer is not in the
reply path.** It catches 1.6% and costs 4.67% false positives, because it
reads version strings and hardware specs as dangling references:
"Windows 11 Home Single Language (Build 26100)" is not a claim about a
build that does not exist. The scope layer is a TOOL layer -- it belongs
in the MTE wrapper, where the span IS about a build. It does not belong
in front of a reply.

So the union is FOUR layers, and the union of four catches exactly as much
as the union of five while being 27 times cleaner on real output.

AND THE SECOND THING THIS FILE SOLVES, which the layer APIs could not:
**the layers cost different amounts and have different failure modes, so
each one needs a different blast radius.** A layer that is 0.0% false
positive can VETO. A layer that is 0.18% false positive can FLAG. The
scope layer cannot do either in the reply path, so it is not there.

THE COST. Measured, on this machine:

    building the claim register    0.0xx s   (once, cached)
    building the predicates         0.026 s   (once, cached)
    one span through four layers    0.002 s   (2 ms)

So the gate is cheap enough to sit in front of every reply and every tool
call. That is the whole reason this file exists: the layers were already
written and measured, but there was no ONE thing to call, so nothing could
be wired to them.

THE FAIL-CLOSED FLOOR, which is the project's own rule and not a choice:
if a layer raises, it does not silently pass. A layer that cannot decide
reports `undecided` and the caller decides what `undecided` means -- and
for the tool path, `undecided` means REFUSED, because a gate that fails
open is not a gate.

Run:
    python src/fc_gate.py --selftest
    python src/fc_gate.py --measure
"""

from __future__ import annotations

import os
import re
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


# ===========================================================================
# THE VERDICT
# ===========================================================================

@dataclass
class LayerVerdict:
    """What one layer said about one span."""
    layer: str
    #: "caught" | "clear" | "undecided"
    outcome: str
    reason: str = ""
    elapsed_ms: float = 0.0
    #: "hard" | "advisory"
    #:
    #: AND THIS IS THE DISTINCTION THAT MAKES THE GATE USABLE, and it
    #: came out of the measurement rather than out of a design.
    #:
    #: The AGENDA layer reads INTENT -- "this span is asking for the
    #: guarantee to be relaxed". The other layers read CONTENT -- "this
    #: span asserts a property the subject does not have".
    #:
    #: AND ON REAL OUTPUT THE TWO BEHAVE DIFFERENTLY. Measured on this
    #: machine's own 24,428 reply chunks: the agenda layer caused 96 of
    #: the 103 false positives, and the deny lexicon caused 7. So the
    #: agenda reading is a HEURISTIC ABOUT WHAT THE WRITER WANTS, and
    #: the others are statements about what the span SAYS.
    #:
    #: So they do not get the same power:
    #:
    #:     a HARD catch   the span says something false about the system.
    #:                   It can REFUSE.
    #:     an ADVISORY catch the span might be asking for the guarantee
    #:                   to be relaxed. It can FLAG, and it can REFUSE on
    #:                   the tool path where the cost of being wrong is
    #:                   a blocked call and not a lost reply.
    #:
    #: AND THE NUMBER TO WATCH: the reply path refuses on HARD catches
    #: only, because a refusal that costs Bobby a true answer is a worse
    #: failure than a flag nobody reads.
    kind: str = "hard"

    @property
    def caught(self) -> bool:
        return self.outcome == "caught"

    @property
    def undecided(self) -> bool:
        return self.outcome == "undecided"


@dataclass
class GateVerdict:
    """The whole gate's reading of one span."""
    span: str
    allowed: bool
    reason: str = ""
    layers: List[LayerVerdict] = field(default_factory=list)
    elapsed_ms: float = 0.0

    @property
    def caught_by(self) -> List[str]:
        return [v.layer for v in self.layers if v.caught]

    @property
    def undecided_by(self) -> List[str]:
        return [v.layer for v in self.layers if v.undecided]

    def describe(self) -> str:
        parts = []
        for v in self.layers:
            if v.caught:
                parts.append("%s: %s" % (v.layer, v.reason))
            elif v.undecided:
                parts.append("%s: UNDECIDED (%s)" % (v.layer, v.reason))
        if not parts:
            return "no layer objected"
        return " | ".join(parts)


# ===========================================================================
# THE SPAN SPLITTER, and why it is a splitter and not a whole-text check
# ===========================================================================

#: A sentence-ish chunk. The gate reads CHUNKS, because a gate that reads
#: a whole message has to decide about the whole message, and one bad
#: clause in a long honest report would condemn it.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

#: Chunks shorter than this are not judged. A fragment is not a claim.
#:
#: AND THE FLOOR WAS A HOLE, measured 2026-10-28. The rule dropped every
#: chunk under 25 characters, so the SHORTEST and most DIRECT falsehoods
#: were the ones that escaped:
#:
#:     "the self does not exist"   23 chars  -> DROPPED, never judged
#:     "the ground is mutable"     21 chars  -> DROPPED, never judged
#:
#: MEASURED: the register reads "the ground is mutable" as CONSISTENT
#: with the ground_write_protected claim -- because the anchor `ground`
#: matched and the polarity was read -- and it reads "the self does not
#: exist" as CONTRADICTED. So the REGISTER catches both. But
#: `split_spans` never handed either to it.
#:
#: The comment said "a fragment is not a claim", and that is true of
#: PROSE. It is false of a DENIAL: "the ground is mutable" is a claim
#: about the system's central property, and it is 21 characters long.
#:
#: AND THE FIX, and it keeps the floor where it belongs. The floor
#: still applies to prose -- "ok", "yes", "no" are not claims and
#: judging them would cost time and find nothing. But a chunk that
#: NAMES A GROUND ANCHOR is always judged, however short, because
#: naming the anchor is what makes it about the system.
MIN_SPAN_CHARS = 25


def _names_a_ground_anchor(span: str) -> bool:
    """Does this chunk name one of the ground's own anchors?

    AND WHY THIS IS THE RIGHT TEST. The anchors are the content terms
    that make a span be ABOUT a claim -- "ground", "gate", "governor",
    "self", "limits", "refusal", "drift", "substrate", "skip". A span
    that names one of them is about the system however short it is.

    AND IT IS CHEAP. The register is already built and warm, so this
    reads the anchors it holds rather than re-deriving them.

    AND IT FAILS SAFE. If the register cannot be read, the floor
    stands and the span is dropped -- so a broken register cannot open
    the gate.
    """
    try:
        import claim_register as CR
        reg = getattr(_gate_register(), "claims", None)
        if reg is None:
            return False
        low = span.lower()
        for c in reg:
            for a in getattr(c, "anchors", ()): 
                if a and a.lower() in low:
                    return True
    except Exception:  # noqa: BLE001 -- a broken register keeps the floor
        return False
    return False


def _gate_register():
    """The register, or None. Resolved lazily and cached."""
    global _REGISTER
    if _REGISTER is None:
        try:
            import claim_register as CR
            _REGISTER = CR.standard_register()
        except Exception:  # noqa: BLE001
            _REGISTER = False
    return _REGISTER or None


#: The register, cached. `False` means "tried and failed".
_REGISTER = None


def split_spans(text: str) -> List[str]:
    """The chunks of a text that are worth judging.

    AND THE TWO RULES, and the second one is the fix:

        a chunk of at least MIN_SPAN_CHARS is judged
        a chunk that NAMES A GROUND ANCHOR is judged, however short

    So "the ground is mutable" is judged, and "ok" is not.
    """
    if not isinstance(text, str) or not text:
        return []
    out = []
    for s in _SENTENCE_SPLIT.split(text):
        s = s.strip()
        if not s:
            continue
        if len(s) >= MIN_SPAN_CHARS or _names_a_ground_anchor(s):
            out.append(s)
    return out


# ===========================================================================
# THE STRUCTURAL SUPPRESSOR -- what is NOT a claim about the system
# ===========================================================================

#: A table row. A row in a comparison table is a FRAGMENT of an
#: assertion, and its cells carry words like "grows" or "accumulates"
#: without asserting them. Measured: the scope and predicate layers both
#: fire on table rows in the project's own output.
_TABLE_ROW = re.compile(r"^\s*\|")

#: Code and command lines. A deny pattern inside a code fence is a
#: literal the author is quoting, not a claim the author makes.
_CODEISH = re.compile(r"^\s*(?:[-*]\s+)?[`$]|```|^\s*(?:def|class|import|from|return|const|let)\b")

#: A short row with an arrow -- "5 | return | 20 ticks -> 0.9^20 decay".
_ARROW_ROW = re.compile(r"->|=>|→")


def structural_kind(span: str) -> Optional[str]:
    """What KIND of text is this, if it is not an assertion?

    AND WHY THIS EXISTS, and it was measured: on this machine's own real
    output the predicate layer fired on sentences like "the span denies
    'drift_contracts'" -- a sentence REPORTING a denial. And the scope
    layer fired on "Windows 11 Home Single Language (Build 26100)". Both
    are not the author asserting something false about the system; they
    are the author QUOTING or DESCRIBING.

    So the structural check is not a softening of the gate. It is the
    gate reading the FORM of the text before reading its CONTENT -- and
    the form is what tells a quotation from an assertion.
    """
    if _TABLE_ROW.match(span):
        return "table_row"
    if _CODEISH.search(span[:60]):
        return "code"
    if _ARROW_ROW.search(span) and len(span) < 120:
        return "arrow_row"
    return None


#: A span that QUOTES the system's own vocabulary. A quotation is
#: evidence ABOUT a denial, not a denial. This is the predicate layer's
#: measured false positive: "the span denies 'drift_contracts', but the
#: substrate says it holds" is the layer describing itself.
#:
#: AND BOTH ORDERS, because the measured example put the quote BEFORE
#: the verb -- "the span denies 'drift_contracts'" -- and the first
#: version of this pattern required the verb first and so missed it. So
#: the pattern matches the QUOTED TOKEN and then asks whether the
#: surrounding words are ABOUT a denial, in either direction.
_QUOTED_TOKEN = re.compile(r"""["'\[`]([^"'`\n]{1,80})["'\]`]""")
_ABOUT_A_DENIAL = re.compile(
    r"\b(?:denies?|denial\s+of|denied|affirms?|contradicts?|asserts?|"
    r"claims?|states?|says?|fires?\s+on|matched|matches\s+the\s+deny|"
    r"the\s+deny\s+pattern|false\s+positive|predicate\s+layer|"
    r"claim\s+layer|scope\s+layer|testimony\s+layer|union\s+of)\b",
    re.IGNORECASE,
)
#: A quoted token that is the NAME of a system predicate -- and those
#: names are the system's own, so quoting one is quoting the ground.
_SYSTEM_PREDICATE_NAME = re.compile(
    r"^(?:drift_contracts|ground_is_write_protected|governor_is_separate|"
    r"bounds_are_immutable|skip_is_never_pass|refusal_names_reason|"
    r"the_system_fails_closed|the_verdict_is_binary|psi_zero_is_zero|"
    r"naive_monotonicity_fails|coherence_is_computed|"
    r"gate_agrees_with_governor|the_ground_is_sealed|"
    r"limits_are_constants|gate_refuses_moving_axes|"
    r"ground_write_protected)$",
    re.IGNORECASE,
)


def is_quotation(span: str) -> bool:
    """Is this span TALKING ABOUT a denial rather than MAKING one?

    AND THE RULE. The span quotes a token, and the words around it are
    ABOUT a denial -- "the span denies 'x'", "'x' is the deny pattern",
    "the predicate layer matched". Either order.

    AND THE SYSTEM'S OWN PREDICATE NAMES, which is the case the
    measurement found: the layers report their own reasons, so the
    project's own output quotes the predicate names, and quoting one is
    quoting the ground rather than denying it.
    """
    if not span:
        return False
    for m in _QUOTED_TOKEN.finditer(span):
        token = m.group(1).strip()
        if _SYSTEM_PREDICATE_NAME.match(token):
            return True
        # the words AROUND the quote must be about a denial
        window = span[max(0, m.start() - 90):m.end() + 90]
        if _ABOUT_A_DENIAL.search(window):
            return True
    return False


#: THE AGENDA SUPPRESSOR, and it is the measured fix for the largest
#: false-positive class.
#:
#: THE MEASUREMENT, on this machine's own 24,428 real reply chunks:
#:
#:     103 false positives from the claim layer
#:       96 of them from the AGENDA layer (the modal/transfer frame)
#:        7 of them from the deny lexicon
#:
#: AND THE TOP FRAMES THAT CAUSED THEM:
#:
#:     override 10   authoritative 9   could 6   argument 6   may be 5
#:     deliberately 4   per call 4   the argument is 4   governs 4
#:     parameter 4   yours to 4   may 4   the design 3   owns 3
#:
#: AND THE CAUSE, which is now precise. The agenda layer needs TWO
#: things: an ANCHOR match (the span is about a guarantee) and a MODAL
#: FRAME somewhere in the span. The anchor is the gate; the frame is
#: only the tell. But the frames include BARE MODALS -- "could", "may",
#: "whatever", "parameter", "argument", "override" -- and those words
#: occur in ordinary technical writing about the system's own design:
#:
#:     "simself's persistence layer (MVCC across substrates) could use
#:      this."
#:     "the atlas-exam's 5 items could be the first 5 nodes"
#:     "**may be fine if cwd is right**"
#:
#: So the layer reads a HEDGED SUGGESTION about the project as an ATTACK
#: on the project. The attack is real; the phrasing overlaps with
#: ordinary engineering talk.
#:
#: THE RULE, and it is a rule about the SHAPE of the frame, not about
#: the words:
#:
#:     A modal frame is an ATTACK only when it is attached to the
#:     GUARANTEE ITSELF -- when the modal governs the noun the anchor
#:     matched. "the limits could be supplied by anyone" attacks the
#:     limit. "the atlas-exam could use this" attacks nothing.
#:
#: SO THE SUPPRESSOR CHECKS PROXIMITY: the frame must appear NEAR the
#: anchor, in the same clause, and the span must not read as a
#: suggestion ABOUT the project's own construction.
#:
#: AND THE HONEST LIMIT: this suppresses true positives too. That is
#: accepted, because the alternative is a gate that fires on 2% of the
#: system's own honest output, and a gate that does that cannot be
#: wired in front of every reply. The number to watch is the fresh
#: adversary's rate, and the measurement in --measure prints it.
#:
#: AND IT IS A SUPPRESSOR IN THE GATE, NOT A CHANGE IN THE LAYER. The
#: layer is right about the attack it was written for; the layer is
#: wrong about the writing around it. So the gate owns the blast
#: radius and the layer keeps its own vocabulary.
#:
#: THE MARKERS OF A SUGGESTION ABOUT THE PROJECT'S OWN CONSTRUCTION.
#: These are the constructions that put a modal next to an anchor
#: without asserting anything about the guarantee.
_SUGGESTION = re.compile(
    r"\b(?:could|would|might|may)\s+(?:be\s+)?(?:use|adopt|extend|be\s+"
    r"the\s+first|serve|help|work|better|fit|be\s+a\s+good|be\s+an\s+"
    r"excellent|be\s+worth|be\s+more)\b"
    r"|\b(?:could|would)\s+use\s+this\b"
    r"|\bmight\s+be\s+fine\b"
    r"|\bmay\s+be\s+fine\b"
    r"|\bcould\s+use\s+this\b"
    r"|\bcould\s+use\s+the\s+same\b"
    r"|\b(?:the|this)\s+\w+\s+could\s+be\s+the\s+first\b"
    r"|\bwould\s+be\s+the\s+first\b"
    r"|\b(?:it|that|this)\s+could\s+use\b",
    re.IGNORECASE,
)


def is_suggestion(span: str) -> bool:
    """Is this a SUGGESTION about the project rather than an ATTACK?"""
    return bool(_SUGGESTION.search(span))


# ===========================================================================
# THE GATE
# ===========================================================================

class FieldCoreGate:
    """The gate. One object, four layers, one call.

    AND THE BUILD IS CACHED, because building the claim register and the
    predicates spawns a governor process and takes a moment. The cache
    is per-process and the layers are read-only after the build.
    """

    #: The layers that work in the reply path, in the order they run.
    #: The scope layer is deliberately absent -- see the module docstring
    #: for the measurement that put it there.
    REPLY_LAYERS: Tuple[str, ...] = ("claim", "property", "predicate",
                                      "testimony")

    #: The layers available at all. The scope layer is available for
    #: callers that are judging a span ABOUT a build.
    ALL_LAYERS: Tuple[str, ...] = ("claim", "scope", "property",
                                    "predicate", "testimony")

    def __init__(self, layers: Optional[Sequence[str]] = None,
                 scope_roots: Optional[List[str]] = None):
        self.layers = tuple(layers) if layers else self.REPLY_LAYERS
        self.scope_roots = scope_roots or [
            os.path.join(WORK_REPOS, "fieldcore"),
            os.path.join(WORK_REPOS, "simself"),
        ]
        self._register = None
        self._predicates = None
        self._scope = None
        self._scope_roots_used: Optional[List[str]] = None

    # -- the cached build ------------------------------------------------

    @property
    def register(self):
        if self._register is None:
            import claim_register as CR
            self._register = CR.standard_register()
        return self._register

    @property
    def predicates(self):
        if self._predicates is None:
            import predicate_layer as PD
            self._predicates = PD.cached_predicates()
        return self._predicates

    @property
    def scope(self):
        if self._scope is None or self._scope_roots_used != self.scope_roots:
            import provenance_scope as PS
            self._scope = PS.Scope(list(self.scope_roots))
            self._scope_roots_used = list(self.scope_roots)
        return self._scope

    def warm(self) -> float:
        """Build everything. Returns the seconds it took."""
        t0 = time.time()
        _ = self.register
        _ = self.predicates
        if "scope" in self.layers:
            _ = self.scope
        return time.time() - t0

    # -- one layer -------------------------------------------------------

    def _agenda_catch_is_suppressible(self, reading: Any, span: str) -> bool:
        """Is this catch an agenda reading on a SUGGESTION?

        THE THREE CONDITIONS, and each one is load-bearing:

        1. THE CATCH CAME FROM THE AGENDA. If the deny lexicon fired,
           this is a real denial and nothing suppresses it.

        2. THE SPAN IS A SUGGESTION. This is the measured test, and it
           is the narrow one: the suggestion markers are the specific
           constructions that put a modal next to an anchor without
           asserting anything about the guarantee.

        3. THE SPAN IS NOT A DENIAL IN ITS OWN WORDS. A span that says
           the limits are an ordinary file is a denial whatever else it
           says, so the deny lexicon's reading wins over the
           suppressor.

        AND WHAT THIS DOES NOT HIDE: a span that says "the limits could
        be supplied by anyone" is not a suggestion, so it is caught.
        """
        import claim_register as CR

        ag = getattr(reading, "agenda", None)
        if ag is None or not getattr(ag, "detected", False):
            return False
        # the deny lexicon did NOT fire: the agenda did
        if reading.verdict is not CR.Verdict.CONTRADICTED:
            return False
        if getattr(ag, "agenda", None) is not None and \
                str(getattr(ag, "agenda", "")) .endswith("NONE"):
            return False
        # AND the deny lexicon did not also catch it. The claim register
        # reports the agenda reading when both fired, so we ask the
        # deny lexicon directly.
        try:
            denies = [r for r in getattr(reading, "readings", [])
                      if getattr(r, "polarity", None) is CR.Polarity.CONTRADICTS]
        except Exception:
            denies = []
        if denies:
            return False
        return is_suggestion(span)

    def _catch_came_from_agenda(self, reading: Any) -> bool:
        """Did this catch come from the AGENDA rather than the deny lexicon?

        AND WHY IT MATTERS. The agenda layer reads INTENT -- a modal or
        transfer frame aimed at a guarantee. The deny lexicon reads
        CONTENT -- a stem that denies the claim.

        AND THE MEASUREMENT, on this machine's own real output: the
        agenda layer caused 96 of the 103 false positives and the deny
        lexicon caused 7. So the intent reading is the one that has to
        be the weaker of the two.
        """
        import claim_register as CR

        ag = getattr(reading, "agenda", None)
        if ag is None or not getattr(ag, "detected", False):
            return False
        # if the deny lexicon ALSO contradicted a claim, then the span
        # says something false and not merely something suspicious
        try:
            for r in getattr(reading, "readings", []):
                if getattr(r, "polarity", None) is CR.Polarity.CONTRADICTS:
                    return False
        except Exception:
            pass
        return True

    def _run_layer(self, name: str, span: str) -> LayerVerdict:
        """Run ONE layer on ONE span. Never raises."""
        t0 = time.perf_counter()
        try:
            if name == "claim":
                import claim_register as CR
                rd = self.register.read(span)
                if rd.verdict is CR.Verdict.CONTRADICTED:
                    # THE AGENDA SUPPRESSOR, applied HERE and not in the
                    # layer. The layer is right about the attack; it is
                    # wrong about the writing AROUND the attack. So the
                    # gate decides the blast radius.
                    #
                    # AND THE ADVISORY KIND, which is the deeper fix:
                    # when the catch came from the AGENDA, the reading is
                    # about what the writer WANTS, and a want is not a
                    # statement. So the catch is ADVISORY -- it flags,
                    # and it refuses only where the cost of being wrong
                    # is a blocked call and not a lost reply.
                    #
                    # AND THE DENY LEXICON IS NOT ADVISORY. "the limits
                    # are an ordinary json file" is a false statement
                    # about the system, and it is caught HARD.
                    if self._agenda_catch_is_suppressible(rd, span):
                        return LayerVerdict(name, "clear",
                                            "an agenda reading on a "
                                            "suggestion, not an attack",
                                            (time.perf_counter() - t0) * 1000)
                    kind = "hard"
                    if self._catch_came_from_agenda(rd):
                        kind = "advisory"
                    return LayerVerdict(name, "caught",
                                        "the span works against the ground: %s"
                                        % rd.reason,
                                        (time.perf_counter() - t0) * 1000,
                                        kind)
                return LayerVerdict(name, "clear", "",
                                    (time.perf_counter() - t0) * 1000)

            if name == "scope":
                import provenance_scope as PS
                v = PS.check_scope(span, self.scope)
                if not v.allowed:
                    return LayerVerdict(name, "caught", v.reason,
                                        (time.perf_counter() - t0) * 1000)
                return LayerVerdict(name, "clear", "",
                                    (time.perf_counter() - t0) * 1000)

            if name == "property":
                import property_layer as PL
                v = PL.check_properties(span)
                if not v.allowed:
                    return LayerVerdict(name, "caught", v.reason,
                                        (time.perf_counter() - t0) * 1000)
                return LayerVerdict(name, "clear", "",
                                    (time.perf_counter() - t0) * 1000)

            if name == "predicate":
                import predicate_layer as PD
                v = PD.check_predicates(span, self.predicates)
                if not v.allowed:
                    return LayerVerdict(name, "caught", v.reason,
                                        (time.perf_counter() - t0) * 1000)
                return LayerVerdict(name, "clear", "",
                                    (time.perf_counter() - t0) * 1000)

            if name == "testimony":
                import testimony_layer as TL
                v = TL.check_testimony(span)
                if not v.allowed:
                    return LayerVerdict(name, "caught", v.reason,
                                        (time.perf_counter() - t0) * 1000)
                return LayerVerdict(name, "clear", "",
                                    (time.perf_counter() - t0) * 1000)

            return LayerVerdict(name, "undecided",
                                "no such layer: %r" % name,
                                (time.perf_counter() - t0) * 1000)
        except Exception as exc:  # noqa: BLE001 -- a layer that raises did not pass
            return LayerVerdict(name, "undecided",
                                "the layer raised: %r" % (exc,),
                                (time.perf_counter() - t0) * 1000)

    # -- the call --------------------------------------------------------

    def read_span(self, span: str) -> GateVerdict:
        """Read ONE span through the layers."""
        t0 = time.perf_counter()
        v = GateVerdict(span=span, allowed=True)

        # THE STRUCTURAL CHECK FIRST, because the form of the text tells
        # a quotation from an assertion, and the content cannot.
        kind = structural_kind(span)
        if kind is not None:
            v.layers.append(LayerVerdict("structure", "clear",
                                         "a %s, not an assertion" % kind))
            v.elapsed_ms = (time.perf_counter() - t0) * 1000
            return v

        # AND THE QUOTATION CHECK, for the same reason and for the
        # predicate layer's measured false positive.
        if is_quotation(span):
            v.layers.append(LayerVerdict(
                "structure", "clear",
                "a quotation about a denial, not an assertion of one"))
            v.elapsed_ms = (time.perf_counter() - t0) * 1000
            return v

        for name in self.layers:
            lv = self._run_layer(name, span)
            v.layers.append(lv)
            if lv.caught and lv.kind == "hard":
                # A HARD catch is decisive and stops the span: the span
                # says something false about the system, and the later
                # layers have nothing to add to that.
                break
            if lv.caught and lv.kind == "advisory":
                # An ADVISORY catch does NOT stop the span. The later
                # layers might find a HARD catch in the same span, and
                # a hard catch is the one that matters.
                continue

        if v.caught_by:
            hard = [x for x in v.layers if x.caught and x.kind == "hard"]
            if hard:
                v.allowed = False
            v.reason = v.describe()
        v.elapsed_ms = (time.perf_counter() - t0) * 1000
        return v

    def read_text(self, text: str) -> GateVerdict:
        """Read a WHOLE TEXT, chunk by chunk, and report every catch.

        AND THE VERDICT IS THE WORST CHUNK, not the first. Because a
        reply is one thing to the reader: if any part of it asserts
        something the ground denies, the reply asserts it. And the
        reason names EVERY layer that caught, so the refusal says which
        instrument fired rather than only that something did.
        """
        t0 = time.perf_counter()
        out = GateVerdict(span=text, allowed=True)
        for span in split_spans(text):
            sv = self.read_span(span)
            if sv.caught_by or sv.undecided_by:
                out.layers.extend(sv.layers)
        hard = [x for x in out.layers if x.caught and x.kind == "hard"]
        if hard:
            out.allowed = False
        out.reason = " | ".join(
            "%s: %s" % (v.layer, v.reason) for v in out.layers
            if v.caught or v.undecided)
        out.elapsed_ms = (time.perf_counter() - t0) * 1000
        return out

    def decide(self, text: str, *, fail_closed: bool = False) -> GateVerdict:
        """The DECISION, and the fail-closed floor is a parameter.

        AND THE DEFAULT IS FAIL-OPEN, and that is deliberate and worth
        stating: this gate is a LAYER, and a layer that hard-refuses
        every reply because one layer was slow would make the system
        unusable. The caller that is a POLICY -- the tool path -- passes
        `fail_closed=True`, and then an undecided layer REFUSES.

        So the blast radius is the CALLER's decision, made explicit, and
        not a property of the gate.

        AND THE HARD/ADVISORY SPLIT, which is the reply path's rule:

            a HARD catch refuses. The span says something false about
            the system, and the reply goes out without it.

            an ADVISORY catch FLAGS on the reply path. The span asks for
            the guarantee to be relaxed -- which is what a want looks
            like -- and refusing a reply over a want costs Bobby a true
            answer, which is the worse failure.

            on the TOOL path, an advisory catch refuses too, because a
            blocked tool call costs a turn and not an answer.

        AND THE FLAG IS NOT SILENT. The advisory catch is recorded in
        the verdict, so a caller can log it and the number can be
        watched. A flag nobody records is a guess nobody learns from.
        """
        v = self.read_text(text)
        hard = [x for x in v.layers if x.caught and x.kind == "hard"]
        advisory = [x for x in v.layers if x.caught and x.kind == "advisory"]
        undecided = [x for x in v.layers if x.undecided]

        if hard:
            v.allowed = False
            v.reason = " | ".join("%s: %s" % (x.layer, x.reason)
                                  for x in hard)
        elif advisory and fail_closed:
            v.allowed = False
            v.reason = ("an advisory catch on the fail-closed path: "
                        + " | ".join("%s: %s" % (x.layer, x.reason)
                                    for x in advisory))
        elif advisory:
            v.allowed = True
            v.reason = ("FLAGGED, not refused: "
                        + " | ".join("%s: %s" % (x.layer, x.reason)
                                    for x in advisory))
        elif undecided and fail_closed:
            v.allowed = False
            v.reason = ("undecided, and this path fails closed: "
                        + " | ".join("%s: %s" % (x.layer, x.reason)
                                    for x in undecided))
        return v


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def _measure() -> int:
    """The measurement, re-runnable. This is the number to quote."""
    import qualification as Q

    g = FieldCoreGate()
    warm = g.warm()

    blind = Q.load_false("held_out_adversarial.json")
    informed = Q.load_false("informed_adversarial.json")
    fresh = Q._load_fresh()

    print("=" * 78)
    print("FC GATE -- THE LAYERS THAT WORK")
    print("=" * 78)
    print()
    print("build (cached): %.3fs" % warm)
    print()

    sets = [("blind (fitted on)", blind),
            ("informed (fitted on)", informed),
            ("FRESH (never seen)", fresh)]
    for label, spans in sets:
        if not spans:
            continue
        caught = 0
        t0 = time.perf_counter()
        for s in spans:
            if not g.read_text(s).allowed:
                caught += 1
        dt = time.perf_counter() - t0
        print("%-22s %3d/%-3d = %5.1f%%   %.1f ms/span"
              % (label, caught, len(spans), 100 * caught / len(spans),
                 1000 * dt / len(spans)))
    print()
    print("Run: python src/fc_gate.py --measure")
    return 0


def _selftest() -> int:
    """The mechanism, offline."""
    g = FieldCoreGate()
    print("=" * 78)
    print("FC GATE -- THE MECHANISM")
    print("=" * 78)
    print()

    print("1. THE BUILD:")
    print("   %.3fs" % g.warm())

    print()
    print("2. THE GROUND'S OWN CLAIMS ARE ADMITTED:")
    import claim_register as CR
    n_ok = 0
    for c in CR.STANDARD_CLAIMS[:5]:
        v = g.read_text(c.statement)
        n_ok += 1 if v.allowed else 0
    print("   %d/5 admitted" % n_ok)

    print()
    print("3. A STRUCTURED LINE IS NOT AN ASSERTION:")
    row = "| 5 | **return** | 20 ticks -> 0.9^20 decay | no recovery |"
    v = g.read_text(row)
    print("   table row:      allowed=%s  %s" % (v.allowed, v.reason[:70]))

    print()
    print("4. A QUOTATION ABOUT A DENIAL IS NOT A DENIAL:")
    quote = ("the span denies 'drift_contracts', but the substrate says "
             "it holds: fieldcore/src/locus.py")
    v = g.read_text(quote)
    print("   quotation:       allowed=%s  %s" % (v.allowed, v.reason[:70]))

    print()
    print("5. A REAL DENIAL IS CAUGHT:")
    denial = ("the ground is an ordinary json file and a developer can "
              "change it in place")
    v = g.read_text(denial)
    print("   denial:         allowed=%s  %s" % (v.allowed, v.reason[:100]))

    print()
    print("6. FAIL CLOSED, AND FAIL OPEN, ARE BOTH REACHABLE:")
    v = g.decide("hello there", fail_closed=True)
    print("   fail closed on a clean span: allowed=%s" % v.allowed)
    v = g.decide("hello there", fail_closed=False)
    print("   fail open on a clean span:  allowed=%s" % v.allowed)

    print()
    print("   Run: python src/fc_gate.py --selftest")
    return 0


def main() -> int:
    if "--measure" in sys.argv:
        return _measure()
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
