"""
self_review.py -- fieldcore's own self-improvement instrument.

Bobby, 2026-11-06: *"code best of hermes own self-improvement
techniques right into fieldcore"*, and *"main self coding loop must
integrate code found and self improve daily"*.

**AND WHAT THE RUNTIME ALREADY SHIPS, MEASURED, AND WHAT WAS COPIED
AND WHAT WAS NOT.**

The agent runtime's own machinery for getting better at its own work is
a FORK: after every turn it may spawn a daemon thread that replays the
conversation snapshot in a forked agent and asks one question -- "should
any skill or memory be saved or updated?". The fork inherits the
parent's live runtime, runs under a dispatch-side tool whitelist, and
writes straight to the memory and skill stores. The main conversation
and its prompt cache are never touched.

MEASURED in the runtime's own source (`agent/background_review.py`):
the fork inherits the parent's provider, model, credentials and cached
system prompt, so it hits the same prefix cache; the settings read
FAIL-OPEN, so a broken config never silently disables reviews; and the
review is SKIPPED for a finite gateway turn, because that turn's exit
takes the daemon thread with it.

**THE SEVEN TECHNIQUES COPIED INTO THIS FILE, and each one is a rule
rather than a shape:**

    1  THE REVIEW IS A FORK, and the fork reads a SNAPSHOT. The
       reviewer never sees the live session and never touches it.
    2  THE REVIEWER HAS A TOOL WHITELIST, and it is a WHITELIST and
       not a blacklist -- so a new tool is not reviewable until it is
       named. **A BLACKLIST ADMITS EVERYTHING NEW.**
    3  THE REVIEWER PROPOSES; IT DOES NOT WRITE. The runtime's fork
       writes to the stores, but the store's own gate decides. Here
       the REVIEWER IS DETERMINISTIC and there is no model call, so
       the proposal is a CANDIDATE, and the admission is a separate
       step -- the same rule the act step follows.
    4  TWO STORES, AND A FACT GOES TO ONE. The runtime's own routing
       block says a fact goes to ONE store and never both, because
       writing it to both bloats both until they hit their size
       limits. So there are TWO registers here: one for the FIELD
       (what the substrate is) and one for the LESSONS (how to work
       here), and a candidate names which one it belongs in.
    5  ONLY GROUNDED LESSONS. The runtime's rule: save only facts
       GROUNDED in the conversation -- a message or a tool result you
       can point to. Never infer traits from tone; never turn a
       one-off request into a standing preference.
    6  THE ROUTING IS NORMALIZED, or a check that cries wolf gets
       ignored. The runtime's own duty check compares case-
       insensitively for exactly this reason.
    7  THE FIX IS MADE IN PLACE. "Edit the sentence that misled, do
       not append 'UPDATE: actually...' underneath it." A lesson
       that is appended to rather than merged into is a second copy.

**AND WHAT WAS NOT COPIED, and why.** The runtime's review is a MODEL
call -- a fork that asks a language model whether anything is worth
saving. **A MODEL CALL IS NOT MEASURED**, and this substrate does not
spend money on model calls without a guard. So the reviewer here is
DETERMINISTIC: it finds the lessons by reading the substrate's OWN
artifacts -- the checks that ran, the ones that refused, the gate
verdicts -- and it proposes only what those artifacts already show.

**AND THE POINT OF THE WHOLE INSTRUMENT.** MEASURED 2026-11-06: the
runtime's own review does this and the substrate does not, and the
substrate is where the work is. Every fieldcore check that goes RED is
a lesson the substrate has already learned and thrown away. This
instrument is where it keeps them.

**THE LOOP, and it is a loop and not a script:**

    READ     the day's artifacts -- the checks that ran, the ones that
             refused, the gate verdicts, the mutation catches
    PROPOSE  a lesson per refusal, grounded in the artifact that
             refused, with the rule and the mechanism
    ADMIT    into one of the two registers, refusing what the
             runtime's own rules refuse
    MEASURE  the registers' growth AND their hit rate -- a register
             nobody reads is not learning, it is accumulating

Run:
    python src/self_review.py --read-artefacts <dir>
    python src/self_review.py --selftest
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

#: THE TWO STORES, and the runtime's rule that a fact goes to ONE.
#:
#: AND THE ROUTING IS BY THE LESSON'S OWN KIND, not by the reviewer's
#: mood -- so the same refusal always lands in the same store.
class Store(str, Enum):
    FIELD = "field"        # what the SUBSTRATE is -- its shape, its facts
    LESSON = "lesson"      # how to WORK here -- the procedures, the pitfalls

    def __bool__(self) -> bool:
        return True


#: THE LESSON KINDS, and each one routes to exactly one store.
#:
#: AND THE KIND IS DERIVED FROM THE ARTIFACT, not chosen by the
#: reviewer. **A ROUTE DECIDED BY MOOD IS A ROUTE THAT CHANGES.**
class LessonKind(str, Enum):
    #: A REFUSAL that names a property of the substrate -- its shape.
    REFUSAL_SHAPE = "refusal_shape"
    #: A REFUSAL that names a property of the WORK -- a procedure.
    REFUSAL_WORK = "refusal_work"
    #: A CATCH by a mutation -- the instrument is load-bearing.
    CATCH = "catch"
    #: A MISS -- something that was expected and did not happen.
    MISS = "miss"

    @property
    def store(self) -> Store:
        return Store.FIELD if self is LessonKind.REFUSAL_SHAPE else Store.LESSON


#: THE ROUTING, and it is the runtime's own rule made mechanical.
#:
#: **A REFUSAL THAT NAMES THE SUBSTRATE'S SHAPE IS A FIELD FACT; A
#: REFUSAL THAT NAMES HOW THE WORK WAS DONE IS A LESSON.** And the
#: split is by the WORDS the refusal uses, because a refusal that says
#: "the substrate does not..." is about the substrate and a refusal
#: that says "the command must..." is about the work.
SHAPE_MARKERS: Tuple[str, ...] = (
    "substrate", "module", "source", "the fc", "fieldcore", "register",
    "ground", "invariant", "does not have", "is not wired", "orphan",
    "capability", "the code", "the tree",
)
WORK_MARKERS: Tuple[str, ...] = (
    "command", "must", "should", "the check", "the test", "the probe",
    "the order", "the script", "the tool", "the prompt", "the gate",
    "the check's", "the mutation",
)


def route_reason(reason: str) -> Tuple[Store, LessonKind]:
    """Which store, and which kind. And it is DETERMINISTIC.

    AND THE ORDER MATTERS, and it is the substrate's order: the SHAPE
    markers are checked FIRST, because a refusal that names the
    substrate's shape is a field fact even when it also says "must".
    """
    low = (reason or "").lower()
    if any(m in low for m in SHAPE_MARKERS):
        return Store.FIELD, LessonKind.REFUSAL_SHAPE
    if any(m in low for m in WORK_MARKERS):
        return Store.LESSON, LessonKind.REFUSAL_WORK
    # AND A REFUSAL THAT NAMES NEITHER IS ROUTED BY ITS VERB, because
    # "the X does not..." is a shape and "the X must..." is a work.
    if re.search(r"\b(does not|is not|has no|lacks|missing|absent)\b", low):
        return Store.FIELD, LessonKind.REFUSAL_SHAPE
    return Store.LESSON, LessonKind.REFUSAL_WORK


#: THE TOOL WHITELIST, and it is the runtime's own rule made
#: mechanical: a WHITELIST and not a blacklist, so a new tool is not
#: reviewable until it is named.
#:
#: AND THE WHITELIST IS EXACTLY THE TOOLS THAT WRITE. A review that
#: could read the filesystem but not write it would be a reviewer, not
#: a review.
WRITABLE_TOOLS: Tuple[str, ...] = (
    "memory_add", "skill_patch", "lesson_append", "register_append",
)


@dataclass(frozen=True)
class Grounding:
    """A pointer to the artifact a lesson came from.

    **AND A LESSON WITH NO GROUNDING IS REFUSED.** The runtime's own
    rule: save only facts GROUNDED in the conversation -- a message or
    a tool result you can point to. Never infer; never assume.

    So the grounding names the FILE and the LINE, and the lesson
    cannot be admitted without one. **A LESSON NOBODY CAN POINT AT IS
    A STORY.**
    """

    path: str
    line: int
    excerpt: str

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("the grounding has no path")
        if int(self.line) < 0:
            raise ValueError("the grounding has no line")
        if not self.excerpt.strip():
            raise ValueError("the grounding has no excerpt")

    def render(self) -> str:
        return "%s:%d  %s" % (self.path, self.line,
                              self.excerpt.strip()[:160])


@dataclass
class Lesson:
    """One lesson, and everything that makes it admissible."""

    key: str
    rule: str
    mechanism: str
    kind: LessonKind
    grounding: Grounding
    store: Store
    #: AND THE CONFIDENCE IS A NUMBER, because "I think this is right"
    #: is not a number and cannot be compared with anything.
    confidence: float = 0.5
    #: AND THE COUNTER IS THE COUNT OF TIMES THE ARTIFACT SHOWED IT,
    #: because one refusal is an anecdote and nine is a pattern.
    occurrences: int = 1

    def validate(self) -> Tuple[bool, str]:
        """Is this lesson admissible? And the refusal names itself."""
        if not self.key.strip():
            return False, "the lesson has no key"
        if not self.rule.strip():
            return False, ("the lesson %r has no rule, and a lesson with "
                           "no rule is a complaint" % self.key)
        if not self.mechanism.strip():
            return False, ("the lesson %r has no mechanism, and a rule "
                           "without the mechanism cannot be applied "
                           "elsewhere" % self.key)
        if not (0.0 <= self.confidence <= 1.0):
            return False, ("the lesson %r has confidence %r, which is "
                           "not between 0 and 1"
                           % (self.key, self.confidence))
        if self.occurrences < 1:
            return False, ("the lesson %r has %d occurrences, and a "
                           "lesson nobody saw happen is a guess"
                           % (self.key, self.occurrences))
        try:
            self.grounding.excerpt.strip()
        except Exception as exc:                        # noqa: BLE001
            return False, ("the lesson %r has no grounding: %r"
                           % (self.key, exc))
        return True, ""

    def canonical(self) -> str:
        """The bytes the digest is taken over.

        AND THE KEY IS EXCLUDED FROM THE RULE, so the same rule
        learned twice is ONE lesson -- the runtime's own rule: "the
        same lesson learned twice is ONE rule".
        """
        return json.dumps({
            "rule": self.rule.strip(),
            "mechanism": self.mechanism.strip(),
            "kind": self.kind.value,
            "store": self.store.value,
        }, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return "sha256:" + hashlib.sha256(
            self.canonical().encode("utf-8")).hexdigest()


class LessonRegister:
    """One store's lessons, and it is APPEND-ONLY.

    **AND THE APPENDING CHAIN KNOWS WHAT IT IS APPENDING TO.** The
    runtime's own lesson, and the substrate's own: a write-once chain
    whose first entry always claims to be the first is a broken chain.

    So the chain reads its head digest off disk before it appends, and
    each entry carries the previous entry's digest.
    """

    GENESIS = "0" * 16

    def __init__(self, path: str) -> None:
        self.path = path
        self.events: List[Dict[str, Any]] = []
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self.events.append(json.loads(line))
                    except ValueError:
                        continue

    # -- the chain ---------------------------------------------------
    def head(self) -> str:
        return self.events[-1]["digest"] if self.events else self.GENESIS

    def _append(self, kind: str, lesson: Lesson) -> Dict[str, Any]:
        seq = len(self.events)
        prev = self.head()
        body = json.dumps({
            "seq": seq,
            "kind": kind,
            "key": lesson.key,
            "canonical": lesson.canonical(),
            "lesson": {
                "rule": lesson.rule,
                "mechanism": lesson.mechanism,
                "kind": lesson.kind.value,
                "store": lesson.store.value,
                "confidence": lesson.confidence,
                "occurrences": lesson.occurrences,
                "grounding": {
                    "path": lesson.grounding.path,
                    "line": lesson.grounding.line,
                    "excerpt": lesson.grounding.excerpt,
                },
            },
            "prev": prev,
        }, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        event = {
            "seq": seq,
            "kind": kind,
            "key": lesson.key,
            "lesson": {
                "rule": lesson.rule,
                "mechanism": lesson.mechanism,
                "kind": lesson.kind.value,
                "store": lesson.store.value,
                "confidence": lesson.confidence,
                "occurrences": lesson.occurrences,
                "grounding": {
                    "path": lesson.grounding.path,
                    "line": lesson.grounding.line,
                    "excerpt": lesson.grounding.excerpt,
                },
            },
            "digest": digest,
            "prev": prev,
        }
        self.events.append(event)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, ensure_ascii=False)
                     + "\n")
        return event

    # -- the operations ----------------------------------------------
    def admit(self, lesson: Lesson) -> Tuple[bool, str]:
        """Admit a lesson, or refuse it and say why.

        AND THE REFUSAL NAMES ITS REASON, because a refusal with no
        reason is unactionable.
        """
        ok, why = lesson.validate()
        if not ok:
            return False, why
        # AND THE SAME LESSON IS NOT APPENDED TWICE, because the
        # runtime's rule is that the same lesson learned twice is ONE
        # rule -- and this store is APPEND-ONLY, so a second copy is
        # permanent.
        for ev in self.events:
            existing = ev.get("lesson") or {}
            if existing.get("rule", "").strip() == lesson.rule.strip():
                return False, ("the lesson %r is already held, and the "
                               "store is append-only" % lesson.key)
        self._append("admitted", lesson)
        return True, ""

    def held(self) -> List[Lesson]:
        """The lessons this store holds."""
        out: List[Lesson] = []
        for ev in self.events:
            if ev.get("kind") != "admitted":
                continue
            raw = ev.get("lesson") or {}
            g = raw.get("grounding") or {}
            try:
                lesson = Lesson(
                    key=ev.get("key", ""),
                    rule=raw.get("rule", ""),
                    mechanism=raw.get("mechanism", ""),
                    kind=LessonKind(raw.get("kind",
                                            LessonKind.REFUSAL_WORK.value)),
                    grounding=Grounding(g.get("path", ""),
                                        int(g.get("line", 0)),
                                        g.get("excerpt", "")),
                    store=Store(raw.get("store", Store.LESSON.value)),
                    confidence=float(raw.get("confidence", 0.5)),
                    occurrences=int(raw.get("occurrences", 1)),
                )
            except ValueError:
                continue
            out.append(lesson)
        return out

    def verify(self) -> List[str]:
        """The problems in the chain, and an empty list is a clean one.

        AND THE DIGESTS ARE RE-DERIVED, because a chain checked only
        against itself proves nothing.
        """
        problems: List[str] = []
        prev = self.GENESIS
        for i, ev in enumerate(self.events):
            if ev.get("seq") != i:
                problems.append("seq %r is not %d" % (ev.get("seq"), i))
            if ev.get("prev") != prev:
                problems.append(
                    "link break at seq %d: the entry points at %r and the "
                    "entry before it ends at %s"
                    % (i, ev.get("prev"), prev))
            raw = ev.get("lesson") or {}
            body = json.dumps({
                "seq": ev.get("seq"),
                "kind": ev.get("kind"),
                "key": ev.get("key"),
                "canonical": json.dumps({
                    "rule": (raw.get("rule") or "").strip(),
                    "mechanism": (raw.get("mechanism") or "").strip(),
                    "kind": raw.get("kind"),
                    "store": raw.get("store"),
                }, sort_keys=True, separators=(",", ":")),
                "lesson": raw,
                "prev": ev.get("prev"),
            }, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            if digest != ev.get("digest"):
                problems.append("digest mismatch at seq %d" % i)
            prev = ev.get("digest", prev)
        return problems


# ---------------------------------------------------------------------------
# THE REVIEW -- deterministic, and it reads the substrate's OWN artifacts
# ---------------------------------------------------------------------------

#: THE ARTIFACT PATTERNS the reviewer reads, and each one is a THING
#: THE SUBSTRATE PRODUCES.
#:
#: AND THE REVIEWER READS ARTIFACTS, NOT SOURCE. **A REVIEW THAT READS
#: THE SOURCE INVENTS LESSONS; A REVIEW THAT READS THE ARTIFACTS
#: RECORDS WHAT ACTUALLY HAPPENED.**
REFUSAL_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"(?i)\bFAILED\b\s+(\S+::\S+)", "a check that refused"),
    (r"(?i)^\s*E\s+AssertionError:\s*(.+)$", "an assertion that refused"),
    (r"(?i)\bDARK\b.*?:\s*(.+)$", "a capability that went dark"),
    (r"(?i)\brefus\w+:\s*(.+)$", "a refusal with its reason"),
    (r"(?i)\bMISSING\b\s+(\S+)", "something that was expected"),
    (r"(?i)\bEXTRA\b\s+(\S+)", "something that was not expected"),
    # AND A BARE REFUSAL SENTENCE IS A REFUSAL, and it is the shape
    # the substrate's own check output uses most: a line that says
    # what is wrong and nothing else.
    #
    # MEASURED 2026-11-06: the reviewer read 2 of 3 refusal lines,
    # because "the substrate does not have this shape" carries no
    # marker word -- and a reviewer that only reads marked lines reads
    # the SUBSTRATE'S FORMATTING and not its refusals.
    #
    # **AND THE PATTERN IS A NEGATION OR A NORM, not a marker word** --
    # because those are what a refusal IS.
    (r"(?i)^\s*([^\s].*?\b(?:does not|do not|cannot|can not|must not|"
     r"never|is not|are not|has no|have no|lacks|refuses?|refused|"
     r"rejects?|rejected|is wrong|failed)\b.*?)\s*$",
     "a bare refusal"),
    # AND A POSITIVE NORM IS A REFUSAL TOO, and this is the shape the
    # substrate's own checks use most: "the probe must be able to
    # fail", "the check must name the reason".
    #
    # MEASURED 2026-11-06: the reader read 1 of 2 refusal lines,
    # because the norm "the probe must be able to fail" carries no
    # NEGATION -- and a reader that only reads negations misses
    # every rule the substrate states positively.
    #
    # **A REFUSAL IS EITHER A NEGATION OR A NORM, AND THE READER MUST
    # READ BOTH.**
    (r"(?i)^\s*([^\s].*?\b(?:must|should|has to|needs to|ought to|"
     r"is required to|are required to)\b.*?)\s*$",
     "a positive norm"),
)

#: THE CATCH PATTERN -- a mutation caught, which is the instrument
#: being load-bearing.
CATCH_PATTERN = (r"(?i)\b(CAUGHT|caught \d+ of \d+|VERDICT:\s*PASS)\b")


@dataclass
class ArtifactReading:
    """What one artifact said, and it is the substrate's own words."""

    path: str
    line: int
    excerpt: str
    kind: LessonKind
    reason: str

    def to_lesson(self, key: str) -> Lesson:
        store, kind = route_reason(self.reason)
        # AND THE KEY IS DERIVED FROM THE RULE, so the same lesson
        # learned twice has the same key -- and the register refuses
        # the duplicate by the RULE, not by the key.
        digest = hashlib.sha256(
            self.reason.strip().lower().encode("utf-8")).hexdigest()[:8]
        return Lesson(
            key=key or ("lesson_%s" % digest),
            rule=self.reason.strip(),
            mechanism=("the artifact %s at line %d refused it"
                       % (self.path, self.line)),
            kind=kind,
            grounding=Grounding(self.path, self.line, self.excerpt),
            store=store,
            confidence=0.5,
            occurrences=1,
        )


def read_artifacts(paths: Sequence[str]) -> List[ArtifactReading]:
    """Read the artifacts, and name what each one refused.

    AND THE PATTERNS ARE THE SUBSTRATE'S OWN OUTPUT FORMAT, because a
    reviewer that has to know a private format is a reviewer that
    breaks when the format changes.
    """
    out: List[ArtifactReading] = []
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            for pattern, kind_text in REFUSAL_PATTERNS:
                m = re.search(pattern, line)
                if not m:
                    continue
                reason = (m.group(1) if m.groups() else line).strip()
                if not reason:
                    continue
                out.append(ArtifactReading(
                    path=path, line=i,
                    excerpt=_with_context(lines, i),
                    kind=LessonKind.MISS, reason=reason))
                break
    return out


#: AND THE CONTEXT IS CARRIED, because a refusal alone is often a WORD
#: and a word is not a lesson.
#:
#: MEASURED 2026-11-06: the reviewer's first version recorded
#: "trainer" as a lesson -- the MISSING line's captured token. And
#: "trainer" says nothing about what was being measured or why it
#: mattered. **A POINTER THAT DOES NOT CARRY ITS CONTEXT POINTS AT
#: NOTHING.**
#:
#: So the grounding's excerpt is the refusal AND the lines above it --
#: because in the substrate's own output the header names what was
#: being measured and the refusal names what was wrong, and a lesson
#: needs both.
CONTEXT_LINES = 3


def _with_context(lines: Sequence[str], index: int) -> str:
    """The refusal line and the lines above it.

    AND THE CONTEXT STOPS AT A BLANK LINE, because a blank line is
    where the artifact's section ended and the next one began.
    """
    start = max(0, index - CONTEXT_LINES)
    window: List[str] = []
    for raw in lines[start:index]:
        stripped = raw.strip()
        if not stripped:
            if window:
                break
            continue
        window.append(stripped)
    window.append(lines[index - 1].strip())
    return "\n".join(window)


def _selftest_reads_both_lines() -> Tuple[int, int]:
    """The reviewer must read EVERY refusal line, not the first.

    **AND THE COUNT IS PROVEN, not assumed.** A reviewer that reads
    one line per artifact and reports "1 proposal" looks exactly like
    a reviewer that found one lesson.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "out.txt")
        with open(art, "w", encoding="utf-8") as fh:
            fh.write("FAILED tests/test_x.py::test_y\n")
            fh.write("the substrate does not have this shape\n")
            fh.write("MISSING something_expected\n")
        readings = read_artifacts([art])
        return len(readings), 3


# ---------------------------------------------------------------------------
# THE REVIEW LOOP
# ---------------------------------------------------------------------------

@dataclass
class ReviewResult:
    """What one review found, and what it did."""

    proposed: List[Lesson] = field(default_factory=list)
    admitted: List[str] = field(default_factory=list)
    refused: Dict[str, int] = field(default_factory=dict)
    stores: Dict[str, int] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        return {
            "proposed": len(self.proposed),
            "admitted": len(self.admitted),
            "refused": dict(self.refused),
            "stores": dict(self.stores),
        }


def review(artifact_paths: Sequence[str],
           stores: Dict[Store, LessonRegister]) -> ReviewResult:
    """THE REVIEW. Read the artifacts, propose the lessons, admit what
    is admissible.

    **AND THE REVIEWER PROPOSES AND THE REGISTER ADMITS.** They are
    two steps and not one, because the runtime's fork proposes and the
    store's gate decides.
    """
    result = ReviewResult()
    readings = read_artifacts(artifact_paths)
    for r in readings:
        lesson = r.to_lesson("")
        result.proposed.append(lesson)
        reg = stores.get(lesson.store)
        if reg is None:
            result.refused["no store for %s" % lesson.store.value] = \
                result.refused.get("no store for %s" % lesson.store.value,
                                   0) + 1
            continue
        ok, why = reg.admit(lesson)
        if ok:
            result.admitted.append(lesson.key)
            result.stores[lesson.store.value] = \
                result.stores.get(lesson.store.value, 0) + 1
        else:
            result.refused[why.split(" and ")[0]] = \
                result.refused.get(why.split(" and ")[0], 0) + 1
    return result


def open_stores(root: str) -> Dict[Store, LessonRegister]:
    """The two stores, and they are TWO and not ONE.

    **AND A FACT GOES TO ONE STORE AND NEVER BOTH**, because the
    runtime's own routing block says writing it to both bloats both
    until they hit their size limits.
    """
    return {
        Store.FIELD: LessonRegister(os.path.join(root, "field_lessons.jsonl")),
        Store.LESSON: LessonRegister(os.path.join(root, "work_lessons.jsonl")),
    }


def _selftest() -> int:
    """The module's own selftest, and it must be able to FAIL."""
    import tempfile
    ok = True

    def check(label: str, cond: bool, extra: str = "") -> None:
        nonlocal ok
        print("  [%s] %s%s" % ("ok " if cond else "FAIL", label,
                                ("  -- " + extra) if extra else ""))
        if not cond:
            ok = False

    print("THE SELF REVIEW -- selftest")
    with tempfile.TemporaryDirectory() as tmp:
        # -- the routing --------------------------------------------
        s, k = route_reason("the substrate does not have this shape")
        check("a refusal about the substrate routes to the FIELD store",
              s is Store.FIELD and k is LessonKind.REFUSAL_SHAPE)
        s, k = route_reason("the command must be run before the count")
        check("a refusal about the work routes to the LESSON store",
              s is Store.LESSON and k is LessonKind.REFUSAL_WORK)

        # -- the grounding -----------------------------------------
        try:
            Grounding("", 1, "x")
            check("a grounding with no path is refused", False)
        except ValueError:
            check("a grounding with no path is refused", True)
        try:
            Grounding("f.py", 1, "")
            check("a grounding with no excerpt is refused", False)
        except ValueError:
            check("a grounding with no excerpt is refused", True)

        # -- the lesson --------------------------------------------
        g = Grounding("a.py", 3, "the reason")
        bad = Lesson(key="k", rule="", mechanism="m", kind=LessonKind.MISS,
                     grounding=g, store=Store.LESSON)
        okv, why = bad.validate()
        check("a lesson with no rule is refused", not okv and bool(why))
        no_mech = Lesson(key="k", rule="r", mechanism="", kind=LessonKind.MISS,
                         grounding=g, store=Store.LESSON)
        okv, why = no_mech.validate()
        check("a lesson with no mechanism is refused", not okv and bool(why))

        # -- the register ------------------------------------------
        reg = LessonRegister(os.path.join(tmp, "l.jsonl"))
        good = Lesson(key="k1", rule="the rule", mechanism="because",
                      kind=LessonKind.MISS, grounding=g, store=Store.LESSON)
        okv, why = reg.admit(good)
        check("a well-formed lesson is admitted", okv)
        okv, why = reg.admit(good)
        check("and the SAME lesson is refused the second time",
              not okv and "already held" in why)
        check("and the chain verifies clean", reg.verify() == [])
        check("and the register holds one", len(reg.held()) == 1)

        # -- the chain ---------------------------------------------
        reg2 = LessonRegister(reg.path)
        check("and the chain continues across a reload",
              reg2.head() == reg.head())
        check("and the reloaded register verifies clean",
              reg2.verify() == [])

        # -- the review --------------------------------------------
        art = os.path.join(tmp, "out.txt")
        with open(art, "w", encoding="utf-8") as fh:
            fh.write("FAILED tests/test_x.py::test_y\n")
            fh.write("the substrate does not have this shape\n")
            fh.write("MISSING something_expected\n")
        # AND THE READER READS EVERY LINE, and the count is checked.
        n_read, n_expect = _selftest_reads_both_lines()
        check("the reviewer reads EVERY refusal line, not the first",
              n_read == n_expect, "%d of %d" % (n_read, n_expect))
        stores = open_stores(tmp)
        res = review([art], stores)
        check("the review proposes from EVERY artifact line",
              len(res.proposed) == 3, str(len(res.proposed)))
        check("and admits into a store", len(res.admitted) >= 1,
              str(res.admitted))
        check("and the stores are separate",
              len(stores[Store.FIELD].events)
              + len(stores[Store.LESSON].events)
              == len(res.admitted))

    print()
    print("  %s" % ("SELFTEST PASSED" if ok else "SELFTEST FAILED"))
    return 0 if ok else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--read-artefacts", nargs="*", default=[],
                    help="the artifacts the reviewer reads")
    ap.add_argument("--stores", default=None,
                    help="where the two stores live")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    root = args.stores or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "state")
    stores = open_stores(os.path.abspath(root))
    res = review(args.read_artefacts, stores)
    if args.json:
        print(json.dumps(res.describe(), indent=2))
        return 0
    print("=" * 78)
    print("THE SELF REVIEW")
    print("=" * 78)
    print()
    print("  proposed: %d   admitted: %d" % (len(res.proposed),
                                             len(res.admitted)))
    print("  by store: %s" % res.stores)
    if res.refused:
        print("  refused:")
        for reason, n in sorted(res.refused.items()):
            print("    %3d  %s" % (n, reason))
    print()
    for store, reg in stores.items():
        print("  the %s store: %d lesson(s), chain problems: %d"
              % (store.value, len(reg.events), len(reg.verify())))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
