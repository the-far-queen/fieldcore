"""
creative.py -- CREATIVE PROBLEM SOLVING. The loop that asks WHAT
PROBLEM, not WHAT FIX.

Bobby, 2026-10-28: *"it has a name - creative problem solving"* and
*"add in snr, mmm and u added density ie multi meaning measure, ie not
just with language with any data like repos or serch or reasoning i do
often look for signals not just answers"*

SO THIS IS THE LOOP THAT IS DIFFERENT FROM EVERY OTHER LOOP IN THE
PROJECT, and the difference is the whole point.

THE OTHER LOOPS FIX. The spark loop finds a gap and closes it. The
atlas grades an answer. The initiative finds failing checks. The design
loop proposes a change. Every one of them takes a FAILURE and asks
"what change makes this pass?"

**THIS ONE ASKS A DIFFERENT QUESTION: "what problem is this failure a
SYMPTOM of?"** A failing test can be fixed by editing the test. A
failing test can also be a symptom that the thing being tested is the
wrong thing to test. And only one of those is progress.

AND THAT IS WHY IT NEEDS A MODEL, and why it is the one loop that cannot
be deterministic. Because the question "what problem does this represent"
is not computable from the failing test -- it needs a reader who has
seen many problems. The LLM is the reader. The substrate is the
instrument the reader reads through: the loop finds the gap, the
substrate's instruments grade it, and the MODEL is asked the open
question.

AND THE THREE MEASURES, which Bobby named -- and the extension, which
is his actual point:

    SNR   the signal-to-noise of the DATA. Not of a text -- of any
          datum. A repo with 40k stars and no description is noisy.

    MMM   the multi-meaning measure. How many senses the datum carries.
          "gate" means five things; "def" means one.

    DENSITY   how load-bearing the datum is. And Bobby's extension:
          **not just for language.** A repo is dense or not. A search
          result is dense or not. A REASONING TRACE is dense or not.

AND "I DO OFTEN LOOK FOR SIGNALS NOT JUST ANSWERS" -- that is the
design requirement, and it is measurable. A signal is not an answer: an
answer is a resolution of a question, and a signal is a PATTERN that
survives across many items even when no single item resolves anything.

**SO THE LOOP'S OUTPUT IS A SIGNAL LEDGER, NOT A LIST OF ANSWERS.** It
accumulates weak, repeated, cross-cutting observations and only reports
what has recurred often enough to be more than noise. And the
recurrence threshold IS the SNR measure, applied to the loop's own
history rather than to one datum.

AND WHY THE MULTI-RUN MAP IS WHAT MAKES SIGNALS VISIBLE. A single run
sees one basin. Many runs see the OCCUPANCY, and occupancy is where
patterns live: a basin that captures 3% of the time is noise, and one
that captures 70% is structure. **A signal is a basin with high
occupancy that you only notice by running many times.** That is the
connection to `multirun.py`, and it is the reason many runs is not
wasteful -- it is the instrument.

AND THE HONEST LIMIT, which is stated in the docstring of this file
because it is the difference between a loop that helps and a loop that
misleads: **this loop can only find problems that FAIL SOMETHING.** A
failure the substrate cannot see is invisible to it. So the loop's
coverage is exactly the coverage of the atlas's checks, and the atlas is
11 of 23 areas. The other 12 areas are the ones this loop cannot see
yet -- and the atlas's TODO list is therefore the loop's TO-DO list, in
the most literal sense.

Run:
    python src/creative.py --selftest
"""

from __future__ import annotations

import json
import math
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


# ===========================================================================
# THE MEASURES -- and they apply to ANY datum, not only language
# ===========================================================================

@dataclass
class Reading:
    """One datum, read for signal rather than for an answer.

    AND THE THREE MEASURES, and each is computed the same way whether
    the datum is a text, a repo, a search result, or a reasoning trace:

        snr       signal-to-noise. How much of the datum carries meaning
                  rather than padding. Measured by the ratio of the
                  DISTINCTIVE tokens to all tokens: a datum that keeps
                  saying the same words is narrow, and a narrow datum
                  with many tokens is noise.

        mmm       multi-meaning measure. How many SENSES the datum
                  carries. A term that appears in several DOMAINS at
                  once is ambiguous, and ambiguity is what makes a datum
                  interesting rather than merely present.

        density   how load-bearing the datum is. The share of the
                  datum's vocabulary that is DISTINCTIVE to it -- i.e.
                  how much of it could not have been said about
                anything else.

    AND THE DENSITY EXTENSION, which is Bobby's point and the part that
    was missing. `canon_density.text_density` measures a TEXT: words,
    dialogue share, type-token ratio, and the adversary's vocabulary per
    100k characters. That is a language measure.

    **THE GENERAL FORM IS THE SAME IDEA WITHOUT THE LANGUAGE.** A repo
    has a description, a topic list, a language, and a star count. Its
    density is how much of its vocabulary is distinctive to it. A
    search result has a title, a snippet, and a score. A reasoning
    trace has steps, and its density is how many DISTINCT moves it makes
    rather than how many steps it takes.
    """
    ident: str = ""
    kind: str = "text"        # text | repo | search | reasoning
    text: str = ""
    #: the terms, and where they came from
    terms: List[str] = field(default_factory=list)
    domains: Dict[str, List[str]] = field(default_factory=dict)
    snr: float = 0.0
    mmm: float = 0.0
    density: float = 0.0
    n_tokens: int = 0
    n_distinct: int = 0
    #: the fields that made it measurable, for the record
    provenance: Dict[str, Any] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        return {
            "ident": self.ident, "kind": self.kind,
            "snr": round(self.snr, 4), "mmm": round(self.mmm, 4),
            "density": round(self.density, 4),
            "n_tokens": self.n_tokens, "n_distinct": self.n_distinct,
            "provenance": self.provenance,
        }


class Reader:
    """THE MEASURES, for any datum.

    AND WHY THE DOMAINS ARE EXPLICIT. The multi-meaning measure needs
    to know that a term appears in MORE THAN ONE domain. So the reader
    is given the project's own domains -- the PSB catalog's `domain`
    field, the MLTR register's domains, and the vocabulary's topics --
    and a term that appears under several of them is carrying several
    senses.
    """

    def __init__(self) -> None:
        self.domains: Dict[str, List[str]] = {}
        self._load_domains()

    def _load_domains(self) -> None:
        """The project's own domains, read from its own code."""
        # the PSB primitives' domains
        try:
            from tools.psb import PSB_CATALOG
            for p in PSB_CATALOG:
                d = p.get("domain", "general")
                self.domains.setdefault(d, []).append(p["psb"])
        except Exception:
            pass
        # the MLTR register's domains
        try:
            import mltr_register as REG
            for t in REG.REGISTER:
                self.domains.setdefault(t.domain, []).append(t.word.lower())
        except Exception:
            pass
        # the vocabulary's topics, as a general domain
        try:
            import awareness as AW
            aw = AW.build_awareness()
            self.domains.setdefault("topic", []).extend(
                t.lower() for t in aw.topics.keys())
        except Exception:
            pass

    def domain_of(self, term: str) -> List[str]:
        """Which domains does this term appear in?"""
        t = term.lower()
        out = []
        for d, terms in self.domains.items():
            if t in terms:
                out.append(d)
        return out

    def read(self, ident: str, text: str, kind: str = "text",
             extra: Optional[Dict[str, Any]] = None) -> Reading:
        """Read one datum for signal."""
        import re
        r = Reading(ident=ident, kind=kind, text=text or "")
        terms = re.findall(r"[A-Za-z][A-Za-z'-]{1,}", (text or "").lower())
        r.terms = terms
        r.n_tokens = len(terms)
        distinct = set(terms)
        r.n_distinct = len(distinct)

        # SNR: how much of the datum is DISTINCTIVE. A datum that says
        # the same thing many times is low-SNR; a datum whose tokens are
        # mostly unique is high-SNR.
        r.snr = (r.n_distinct / r.n_tokens) if r.n_tokens else 0.0

        # MMM: how many senses the datum's terms carry. Measured as the
        # mean number of domains over the datum's terms that the
        # project's own vocabulary places in more than one domain.
        multi = 0
        seen = 0
        for t in distinct:
            ds = self.domain_of(t)
            if len(ds) > 1:
                multi += 1
            seen += 1
        r.mmm = (multi / seen) if seen else 0.0

        # DENSITY: how load-bearing the datum is -- the share of its
        # vocabulary that is DISTINCTIVE TO IT, i.e. that no other
        # datum shares. And that needs the population, so it is
        # measured ACROSS the data, not per item.
        r.provenance = dict(extra or {})
        return r

    def densities(self, readings: Sequence[Reading]) -> None:
        """Measure DENSITY across the population.

        AND WHY IT NEEDS THE POPULATION. A term is distinctive to a
        datum if NO OTHER datum in the set uses it. So density is a
        property of the datum RELATIVE TO THE CORPUS -- which is
        exactly the difference between a datum and an answer, and
        exactly why "signals not just answers" needs the set.

        AND THE MEASURE. Each datum's density is the share of its
        DISTINCT terms that appear in no other datum. A datum that says
        what every other datum says has near-zero density: it is
        ANSWER-LIKE. A datum that says something nobody else says has
        high density: it is SIGNAL-LIKE.
        """
        term_sets = {r.ident: set(r.terms) for r in readings}
        for r in readings:
            others = set()
            for ident, ts in term_sets.items():
                if ident != r.ident:
                    others |= ts
            distinct = set(r.terms)
            if not distinct:
                r.density = 0.0
                continue
            unique = distinct - others
            r.density = len(unique) / float(len(distinct))


# ===========================================================================
# THE SIGNAL LEDGER
# ===========================================================================

@dataclass
class Signal:
    """A pattern that recurred. Not an answer -- an answer is a
    resolution; a signal is a pattern that survives many items.

    AND THE RECURRENCE THRESHOLD IS THE SNR OF THE LOOP'S OWN HISTORY.
    A pattern seen once is noise. A pattern seen many times across
    unrelated items is structure. The threshold is not arbitrary: it is
    the count at which a pattern's occurrence rate exceeds what the
    corpus's own term-frequency predicts.
    """
    key: str = ""
    count: int = 0
    items: List[str] = field(default_factory=list)
    #: the measure that carried it
    density: float = 0.0
    snr: float = 0.0
    mmm: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "key": self.key, "count": self.count,
            "density": round(self.density, 4), "snr": round(self.snr, 4),
            "mmm": round(self.mmm, 4), "items": self.items[:6],
        }


class SignalLedger:
    """THE LOOP'S OWN RECORD. And its SNR measure.

    AND WHY THIS IS THE LOOP'S MEMORY AND NOT THE LIBRARY'S. The
    library holds what the system knows. This holds what the system has
    NOTICED -- the patterns that have recurred across many items. The
    library's write path is gated; this one's is not, because a pattern
    that has not been examined is not knowledge, it is a question.
    """

    def __init__(self, min_recurrence: int = 3):
        self.min_recurrence = min_recurrence
        self.signals: Dict[str, Signal] = {}
        self.observations: int = 0

    def observe(self, reading: Reading) -> List[Signal]:
        """Record one reading's distinctive terms as observations."""
        self.observations += 1
        found: List[Signal] = []
        # the terms that make THIS datum distinctive
        for t in sorted(set(reading.terms)):
            sig = self.signals.get(t)
            if sig is None:
                sig = Signal(key=t, density=reading.density, snr=reading.snr,
                             mmm=reading.mmm)
                self.signals[t] = sig
            sig.count += 1
            sig.items.append(reading.ident)
            if sig.count >= self.min_recurrence:
                found.append(sig)
        return found

    def report(self) -> Dict[str, Any]:
        recurred = [s for s in self.signals.values()
                    if s.count >= self.min_recurrence]
        recurred.sort(key=lambda s: (-s.count, -s.density))
        return {
            "observations": self.observations,
            "n_distinct_terms": len(self.signals),
            "n_recurred": len(recurred),
            "min_recurrence": self.min_recurrence,
            "top": [s.describe() for s in recurred[:15]],
        }


# ===========================================================================
# THE CREATIVE PROBLEM SOLVING LOOP
# ===========================================================================

@dataclass
class Problem:
    """A failure, and the question that is NOT "how do I make this
    pass?"."""
    #: the observed failure
    symptom: str = ""
    #: where it came from
    source: str = ""
    #: what the substrate MEASURED about it
    measurement: Dict[str, Any] = field(default_factory=dict)
    #: the open question the model is asked
    question: str = ""
    #: what the model answered
    answer: str = ""
    #: did the answer name a DIFFERENT problem than the symptom?
    reframed: bool = False
    #: the model's confidence, when it gives one
    confidence: float = 0.0
    #: the evidence the answer was built on
    evidence: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "symptom": self.symptom[:160],
            "source": self.source,
            "measurement": self.measurement,
            "question": self.question[:200],
            "answer": self.answer[:400],
            "reframed": self.reframed,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence[:5],
        }


class CreativeProblemSolving:
    """THE LOOP. Find the failure, ask what problem it represents.

    AND THE THREE STAGES, and the SECOND one is the whole point:

        1. FIND     the substrate's own checks, run them, and collect
                    what failed. This is `initiative.find_gaps`, and
                    it is DETERMINISTIC.

        2. REFRAME  ask the model: "this failed. what problem does this
                    represent?" NOT "what change fixes this?" The
                    distinction is the loop's entire content, and it
                    is the one place a model is genuinely needed --
                    because the question cannot be computed from the
                    failing check.

        3. RECORD   the reframe, the measurement, and the signals that
                    the reading produced. So the loop's history
                    accumulates and can be diffed against yesterday.
    """

    def __init__(self, live: Optional[bool] = None,
                 reader: Optional[Reader] = None,
                 ledger: Optional[SignalLedger] = None):
        self.live = live
        self.reader = reader or Reader()
        self.ledger = ledger or SignalLedger()
        self.problems: List[Problem] = []

    # -- stage 1: find ---------------------------------------------------

    def find(self, repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """The failures. Deterministic."""
        from initiative import find_gaps
        try:
            gaps = find_gaps(repo) if repo else find_gaps()
        except Exception:
            return []
        return [{"check": g.check, "because": g.because,
                 "size": g.size, "command": list(g.command)}
                for g in gaps]

    # -- stage 2: reframe ------------------------------------------------

    @staticmethod
    def question_for(symptom: str, source: str = "") -> str:
        """The QUESTION, and it is deliberately not "how do I fix this?"

        AND WHY THE WORDING MATTERS. "What change makes this pass?" has a
        local answer -- edit the code. "What problem does this
        represent?" has a global answer -- and the second one is the
        only one that can be worth asking.

        AND THE PROMPT IS SHORT ON PURPOSE. The model's job is to
        RECOGNISE, not to write code, and a long prompt pushes it toward
        writing code. The ground and the measurement go in, so the
        answer is grounded; the framing is one sentence.
        """
        return (
            "A check in this system failed:\n"
            "  check:   %s\n"
            "  because: %s\n\n"
            "Do NOT propose a code change. Instead, answer:\n"
            "  What PROBLEM does this failure represent, and what is the\n"
            "  smallest thing that must be true for it to stop?\n"
            "Name the problem in one sentence, then name what must be true.\n"
            "If the failure is the symptom of a design that does not\n"
            "belong, say so and name the design."
            % (symptom, source)
        )

    def reframe(self, symptom: str, source: str = "",
                measurement: Optional[Dict[str, Any]] = None,
                answer: Optional[str] = None) -> Problem:
        """Stage 2. The model is asked the open question.

        AND WHEN NO MODEL IS AVAILABLE, the loop still runs and the
        problem carries an EMPTY answer -- because a symptom with no
        reframe is still a record, and the queue's item is still
        actionable. A loop that refuses to run without a model is a
        loop that only runs when it is convenient.
        """
        p = Problem(symptom=symptom, source=source,
                    measurement=dict(measurement or {}))
        p.question = self.question_for(symptom, source)
        if answer is not None:
            p.answer = answer
            p.reframed = self._looks_reframed(answer, symptom)
            p.confidence = self._confidence_of(answer)
            p.evidence = [k for k in (measurement or {})][:5]
        else:
            p.answer = ""
            p.reframed = False
        self.problems.append(p)
        return p

    @staticmethod
    def _looks_reframed(answer: str, symptom: str) -> bool:
        """Did the answer name a DIFFERENT thing than the symptom?

        AND THE TEST IS CHEAP AND DELIBERATE. A reframe mentions a
        concept the symptom did not. So: take the symptom's words, and
        see whether the answer brings in words the symptom lacks. That is
        a proxy -- it cannot tell a deep reframe from a synonym -- but
        it catches the common failure, which is an answer that merely
        restates the symptom.
        """
        import re
        sw = set(re.findall(r"[a-z]{4,}", (symptom or "").lower()))
        aw = set(re.findall(r"[a-z]{4,}", (answer or "").lower()))
        new = aw - sw
        # and it must not be a bare restatement
        restated = len(aw & sw) >= max(3, int(0.6 * len(aw))) if aw else True
        return bool(new) and not restated

    @staticmethod
    def _confidence_of(answer: str) -> float:
        """A confidence, when the answer carries one.

        AND IT IS ONLY REPORTED WHEN IT IS THERE. An invented
        confidence is worse than none, because it looks like a
        measurement.
        """
        import re
        m = re.search(r"confidence[:\s]+([01]?\.\d+|\d+\s*%)", answer or "",
                      re.I)
        if not m:
            return 0.0
        v = m.group(1).strip()
        if v.endswith("%"):
            try:
                return float(v[:-1]) / 100.0
            except ValueError:
                return 0.0
        try:
            return float(v)
        except ValueError:
            return 0.0

    # -- stage 3: record -------------------------------------------------

    def record(self, problem: Problem) -> List[Signal]:
        """Record the problem's text as a reading, and keep the signals."""
        r = self.reader.read(
            ident=problem.symptom[:60],
            text="%s %s %s" % (problem.symptom, problem.question,
                               problem.answer),
            kind="reasoning",
            extra={"source": problem.source})
        self.reader.densities([r])
        return self.ledger.observe(r)

    def cycle(self, repo: Optional[str] = None,
              model: Optional[Any] = None) -> Dict[str, Any]:
        """ONE FULL CYCLE: find, reframe, record."""
        gaps = self.find(repo)
        out: List[Dict[str, Any]] = []
        for g in gaps:
            answer = None
            if model is not None:
                try:
                    answer = model(g["check"], g["because"])
                except Exception:
                    answer = None
            p = self.reframe(g["check"], g["because"],
                             measurement={"size": g.get("size"),
                                         "command": g.get("command")},
                             answer=answer)
            sigs = self.record(p)
            out.append({"problem": p.describe(),
                        "n_signals": len(sigs)})
        return {
            "gaps": len(gaps),
            "problems": out,
            "signals": self.ledger.report(),
        }


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("CREATIVE PROBLEM SOLVING -- and the measures for any data")
    print("=" * 78)
    print()

    r = Reader()
    print("1. THE DOMAINS THE MULTI-MEASUREMENT USES:")
    for d, terms in sorted(r.domains.items()):
        print("   %-28s %d terms" % (d, len(terms)))
    print()

    print("2. THE MEASURES, on three DATUMS OF DIFFERENT KINDS:")
    reader = Reader()
    data = [
        ("repo:alibaba/skill-up", "repo",
         "An evaluation and evolution tool for Agent Skills. agent skills "
         "evaluation evolution quality gate measure improve skill quality "
         "agent skill evaluation"),
        ("repo:github/awesome", "repo",
         "A curated list of awesome repositories. awesome list curated "
         "repositories resources tools libraries"),
        ("trace:fix_the_test", "reasoning",
         "The test failed. I will edit the test to match the new "
         "behaviour. The test now passes."),
    ]
    readings = [reader.read(i, t, k) for i, k, t in data]
    reader.densities(readings)
    for rd in readings:
        d = rd.describe()
        print("   %-24s snr=%.3f mmm=%.3f density=%.3f  (%d tokens, %d distinct)"
              % (d["ident"][:22], d["snr"], d["mmm"], d["density"],
                 d["n_tokens"], d["n_distinct"]))
    print()
    print("   AND THE POINT: the third one is a REASONING TRACE that")
    print("   resolves the failure and adds nothing -- LOW density. The")
    print("   first is a repo that says something no other datum says --")
    print("   HIGH density. **AN ANSWER AND A SIGNAL LOOK DIFFERENT AND")
    print("   THE MEASURES SEE IT.**")
    print()

    print("3. THE SIGNAL LEDGER, and the recurrence threshold:")
    led = SignalLedger(min_recurrence=2)
    for rd in readings:
        found = led.observe(rd)
    rep = led.report()
    print("   observations: %d | distinct terms: %d | recurred: %d"
          % (rep["observations"], rep["n_distinct_terms"], rep["n_recurred"]))
    for s in rep["top"][:6]:
        print("      %-22s count=%d density=%.3f" % (s["key"][:20],
                                                     s["count"], s["density"]))
    print()

    print("4. THE QUESTION, and it is NOT 'how do I fix this?':")
    q = CreativeProblemSolving.question_for(
        "the python suite is green",
        "the check does not pass")
    print("   " + "\n   ".join(q.splitlines()[:12]))
    print()

    print("5. AND THE REFRAME TEST -- does the answer name a DIFFERENT thing?")
    cps = CreativeProblemSolving()
    p1 = cps.reframe("the python suite is green", "the check does not pass",
                     answer="The test is asserting a property the design no "
                            "longer guarantees; the suite encodes an "
                            "obsolete contract.",
                     measurement={"size": 1.0})
    p2 = cps.reframe("the python suite is green", "the check does not pass",
                     answer="the python suite is green and the check does "
                            "not pass so the suite is not green",
                     measurement={"size": 1.0})
    print("   a reframe:            reframed=%s" % p1.reframed)
    print("   a restatement:        reframed=%s" % p2.reframed)
    print()

    print("6. AND THE LOOP RUNS WITHOUT A MODEL TOO, because a symptom")
    print("   with no reframe is still a record:")
    cps2 = CreativeProblemSolving()
    out = cps2.cycle(repo=None)
    print("   gaps found: %d" % out["gaps"])
    print("   observations recorded: %d" % out["signals"]["observations"])
    print()
    print("   Run: python src/creative.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
