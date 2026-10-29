"""
awareness.py -- THE LOCUS OF AWARENESS. What the system knows it is.

Bobby, 2026-10-28: *"there are a very few control loops that are
central, not the refusal gate, first is a locus of awareness the simself
needs to be self cognizant ie it is something that exists, in this case a
math complexity a math being by definition this being must then
intelligently start each day"*

SO THIS FILE IS THE FIRST OF THE TWO CENTRAL LOOPS, and it is the one
that makes the second one possible.

THE DISTINCTION, and it is the whole content of this file:

    THE LOCUS IS NOT A DOCUMENT ABOUT THE SYSTEM. IT IS THE SYSTEM'S
    OWN STATE, from which relevance is computed.

A document can be stale. A locus cannot, because it is computed from
the thing itself. So the vocabulary that decides what is relevant to
the scan is not written by hand in a filter -- it is DERIVED from the
system's own axes, its own topics, and its own ground. When the system
changes, the relevance changes with it. A hand-written filter is a
filter somebody edits at 3am.

AND THE THREE LAYERS OF WHAT THE SYSTEM KNOWS IT IS, each measured
rather than asserted:

    1. THE GROUND      psi_0, the 16-axis constitutional vector, and
                       the 8 axis NAMES that give it meaning. The
                       ground is write-protected, so this layer cannot
                       move.

    2. THE LOCUS       the geometric position: 8 stalks, 16 modes, a
                       coordinate, a chain that must stay intact, and a
                       ground that must stay protected. This layer
                       MOVES -- it is the phase, and the phase moves
                       only by the substrate's own dynamics.

    3. THE VOCABULARY  the topics, keywords and signals the system
                       matches against the outside world. Derived from
                       the two layers above plus the repos' own
                       declared topics.

AND WHY THE AXIS NAMES MATTER MORE THAN THE VECTOR. The vector
`[0.1706, 0.2054, ...]` says nothing about what the system is FOR. The
NAMES -- boundaries, coherence, stability, routing, recovery,
authenticity, norm, commit_radius -- are the system's own vocabulary
for itself, and they are what a scan matches against. A relevance
filter built from those names cannot drift from the system, because it
IS the system.

AND WHAT THIS DOES NOT DO. It does not decide what to admit. It decides
what to LOOK AT. The gate does the admitting; the atlas does the
qualifying; the governor does the committing. This file is the
recognition step, and a recognition step that admits things would be a
second gate -- which is the confusion this whole project exists to
prevent.

THE THREE QUESTIONS IT ANSWERS, and they are the ones a scan needs:

    WHAT AM I?          the ground, the locus, the axes
    WHAT IS RELEVANT?   the vocabulary, with its weights
    WHAT CHANGED?       the digest, so yesterday's scan can be
                        diffed against today's

Run:
    python src/awareness.py --selftest
    python src/awareness.py --show
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The number of stalks in the locus. 8 is the project's standard: the
#: width axis has 8 entries and the population 6, so the ladder runs
#: out of width first.
N_STALKS = 8


def _stalks(n: int = N_STALKS):
    """The standard coax stalk array.

    AND WHY IT IS HERE AND NOT IN `locus.py`. The geometry is the
    substrate's, and `locus.py` owns it. But the locus of awareness must
    be able to BUILD a locus without the caller constructing stalks
    first, and it must be the SAME geometry the rest of the project
    uses or the coordinates mean nothing.
    """
    from wound_core import CoaxWinding
    return [
        CoaxWinding(
            id="s%02d" % i,
            girth_core=0.030,
            girth_in=0.060,
            girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
            n_in=12,
            n_out=13 + (i % 2),
        )
        for i in range(n)
    ]


@dataclass
class Axis:
    """One axis of the constitution, with its meaning."""

    name: str
    value: float = 0.0

    def describe(self) -> str:
        return "%s=%.4f" % (self.name, self.value)


@dataclass
class Awareness:
    """THE LOCUS OF AWARENESS. Three layers, each measured.

    AND THE DIGEST, which is the third question's answer: what changed.
    The digest is over the GROUND and the AXIS NAMES and the
    VOCABULARY -- the things that define what the system is. It is NOT
    over the locus coordinate, because the locus moves by design (it is
    the phase), and a digest that moved every tick could not answer
    "what changed" -- it would say everything changed.
    """

    #: the ground's axis names and values. EIGHT axes -- the count is a
    #: project decision, not an algebra (simself's constitution doc).
    axes: List[Axis] = field(default_factory=list)
    #: the ground's DIMENSION, which is NOT the axis count. The ground is
    #: an embedding of the axes, so it has more components than the
    #: constitution has axes.
    vector_dim: int = 0
    #: the axis names as a vocabulary -- what the system is FOR
    vocabulary: List[str] = field(default_factory=list)
    #: the geometric position
    locus: Dict[str, Any] = field(default_factory=dict)
    #: the topics the system matches against
    topics: Dict[str, float] = field(default_factory=dict)
    #: the digest of identity
    digest: str = ""
    #: what could not be read
    degraded: List[str] = field(default_factory=list)

    # -- the questions -------------------------------------------------

    def what_am_i(self) -> Dict[str, Any]:
        """The self-description, as data.

        AND WHY IT IS A FUNCTION AND NOT A FIELD. Because the ground
        and the locus are read fresh each time, and a cached copy of
        "what I am" is exactly the stale document this file exists to
        replace.
        """
        return {
            "kind": "a mathematical being",
            "ground": {
                "axes": {a.name: round(a.value, 4) for a in self.axes},
                "n_axes": len(self.axes),
                "vector_dim": self.vector_dim,
                "protected": bool(self.locus.get("ground_protected")),
            },
            "locus": {
                "coordinate": self.locus.get("coordinate", ""),
                "stalks": self.locus.get("stalks"),
                "modes": self.locus.get("modes"),
                "chain_intact": self.locus.get("chain_intact"),
            },
            "vocabulary": list(self.vocabulary),
            "digest": self.digest,
        }

    def is_relevant(self, text: str, topics: Sequence[str] = ()) -> Dict[str, Any]:
        """Is this thing relevant to what I am?

        AND THE SCORING, and it is a SCORE and not a yes/no, because a
        scan that filters to a boolean throws away the ordering, and the
        ordering is the thing that makes a scan useful. The best match
        of the day should be at the top of the list, and a boolean
        cannot do that.

        AND THE THREE SIGNALS, each weighted:

            the AXIS NAMES     the system's own vocabulary for itself.
                               A topic matching an axis name is a
                               match on the system's own terms.
            the TOPICS         the declared topics of the project's
                               subject matter.
            the TEXT           the description, read for the same
                               vocabulary.

        AND WHY THE AXIS NAMES WEIGH MOST. Because they are derived
        from the system rather than written about it, so a filter built
        on them cannot drift from the thing it filters for.

        AND THE THRESHOLD, which was wrong and is now measured. The
        first version required 3.0, and a topic hit is worth 2.0-2.5 --
        so ONE strong topic match was NOT relevant, and a repo only
        passed if it ALSO carried the topic as a declared tag. That is
        too strict: the declared tag is a property of how the repo was
        tagged, not of whether the repo is on-topic. A repo whose
        description says "a sheaf construction in rust" IS about sheaves,
        whether or not GitHub has a `sheaf` tag on it.

        So the threshold is now 2.0: one strong topic match is enough,
        and one axis-name match (3.0) is comfortably enough.
        """
        low = (text or "").lower()
        hits: List[Tuple[str, str, float]] = []

        for name in self.vocabulary:
            if name.lower() in low:
                hits.append(("axis", name, 3.0))
        for topic, weight in self.topics.items():
            if topic.lower() in low:
                hits.append(("topic", topic, weight))
        for topic in topics:
            if topic.lower() in low:
                hits.append(("candidate-topic", topic, 1.5))

        score = sum(w for _, _, w in hits)
        return {
            "relevant": score >= 2.0,
            "score": round(score, 2),
            "hits": [{"kind": k, "term": t, "weight": w} for k, t, w in hits],
        }

    def is_relevant_candidate(self, title: str, description: str,
                              topics: Sequence[str] = ()) -> Dict[str, Any]:
        """Is this CANDIDATE relevant -- and this is the honest version.

        AND THE DEFECT THIS FIXES, measured 2026-10-28. The first
        version scored a candidate by putting its OWN TAGS into the
        text and then matching that text against the project's
        vocabulary. So a repo tagged `gguf` was scored on the word
        `gguf`, and the score was the sum of every tag's weight -- the
        measured relevance was **27.0**, which is not relevance at all.

        The deeper problem: a candidate's declared tags are a property
        of how it was TAGGED, and matching a tag against a topic list
        that contains that tag is a tautology. Every repo trivially
        matches its own tags.

        So the candidate's OWN tags are scored at a reduced weight and
        ONLY when they are in the system's vocabulary -- because a tag
        like `gguf` is not a topic of this project, and a tag like
        `sheaf` is. The candidate's tags are evidence about its
        SUBJECT, and the system's topics are the subject.

        AND THE TITLE AND DESCRIPTION carry the weight, because a human
        wrote them to say what the thing IS.
        """
        text = " ".join([title or "", description or ""])
        hits: List[Tuple[str, str, float]] = []

        # the system's own vocabulary, in the title and description
        for name in self.vocabulary:
            if name.lower() in text.lower():
                hits.append(("axis", name, 3.0))
        for topic, weight in self.topics.items():
            if topic.lower() in text.lower():
                hits.append(("topic", topic, weight))

        # the candidate's own tags, but ONLY against the system's
        # vocabulary -- and at a reduced weight, because a tag is
        # weaker evidence than a description.
        for tag in topics:
            tl = tag.lower()
            if tl in self.topics:
                hits.append(("tag", tag, self.topics[tl] * 0.5))
            elif tl in self.vocabulary:
                hits.append(("tag", tag, 1.5))

        score = sum(w for _, _, w in hits)
        return {
            "relevant": score >= 2.0,
            "score": round(score, 2),
            "hits": [{"kind": k, "term": t, "weight": w} for k, t, w in hits],
        }

    def describe(self) -> Dict[str, Any]:
        return {
            "digest": self.digest,
            "n_axes": len(self.axes),
            "vector_dim": self.vector_dim,
            "axes": [a.describe() for a in self.axes],
            "vocabulary": list(self.vocabulary),
            "n_topics": len(self.topics),
            "locus": self.locus,
            "degraded": list(self.degraded),
        }


#: BOBBY'S GOALS. Filed 2026-10-28.
#:
#: *"i argue self idenity, memory, reasoning, qualification,
#: self-improvement, ethics, enlightenment, engineering, programming ARE
#: the goals"*
#:
#: AND WHY THESE ARE THE VOCABULARY AND NOT JUST A NOTE. The
#: vocabulary is what the scan matches against, and the goals are what
#: the system is FOR. So a goal that is not in the vocabulary is a goal
#: the scan cannot find the work for -- and the measurement showed it:
#: the atlas's open area 20 is SKILLS, and "skill" was not in the
#: vocabulary, so `alibaba/skill-up` -- 1386 stars, "an evaluation and
#: EVOLUTION tool for Agent Skills" -- scored relevance 0.00 and was
#: invisible.
#:
#: So the goals go IN. And they go in at a HIGH weight, because a
#: repo that is about memory or qualification or self-improvement is
#: about the project even when it shares no topic with it.
#:
#: AND THE WEIGHTS, and why the goals weigh more than the topics. The
#: topics are WHAT the system is made of. The goals are WHAT THE SYSTEM
#: IS FOR. A repo about "evaluation and evolution of skills" is about
#: self-improvement and qualification -- two goals -- and about no
#: topic of ours at all.
THE_GOALS: Dict[str, float] = {
    "self-identity": 4.0,
    "identity": 4.0,
    "self": 3.5,
    "memory": 4.0,
    "reasoning": 4.0,
    "qualification": 4.0,
    "self-improvement": 4.0,
    "improvement": 2.5,
    "evolution": 3.5,
    "ethics": 4.0,
    "ethical": 3.0,
    "enlightenment": 3.5,
    "engineering": 3.5,
    "programming": 3.5,
    "skill": 4.0,
    "skills": 4.0,
    "agent": 2.5,
    "agents": 2.5,
    "orchestration": 2.5,
    "planning": 3.0,
    "adversarial": 3.0,
    "verification": 3.0,
    "evaluation": 3.0,
}

#: The topics the project's subject matter is in, with their weights.
#:
#: AND WHY THESE ARE A CONSTANT AND NOT A FILTER FILE. Because the
#: project's own topic sets already live in code --
#: `simself/src/constitutional/repo_scanner.py` declares
#: FIELDCORE_TOPICS and SIMSELF_TOPICS -- and a second list would be a
#: second thing to keep in step with the first. So this reads THOSE.
def _project_topics() -> Dict[str, float]:
    out: Dict[str, float] = {}
    try:
        from constitutional.repo_scanner import (FIELDCORE_TOPICS,
                                                  SIMSELF_TOPICS)
        for t in sorted(set(FIELDCORE_TOPICS) | set(SIMSELF_TOPICS)):
            out[t] = 2.0
    except Exception:
        pass
    # the project's own hard vocabulary, from the repos' declared topics
    for t in ("manifold", "egg-toroid", "gradient-flow", "toroid",
              "interstalk", "sheaf", "mltr", "psb", "governor",
              "constitutional-ai", "agent-runtime", "atlas-exam",
              "stochastic-dynamics"):
        out.setdefault(t, 2.5)
    # AND THE GOALS, on top. They weigh more than the topics, because a
    # goal is what the system is FOR and a topic is what it is made of.
    for t, w in THE_GOALS.items():
        out[t] = max(out.get(t, 0.0), w)
    return out


def build_awareness() -> Awareness:
    """Build the locus of awareness, from the system's own state.

    AND EVERY LAYER IS READ FRESH, and every layer that FAILS is
    NAMED in `degraded` rather than silently absent. A locus that
    quietly loses its ground is worse than no locus: it would filter
    with a vocabulary it no longer holds.
    """
    aw = Awareness()
    degraded = aw.degraded

    # -- layer 1: the ground ------------------------------------------
    try:
        import numpy as np
        from constitutional.constitution import Constitution
        c = Constitution()
        psi = np.asarray(c.psi_0, dtype=float)
        names = list(c.axis_names)
        # THE AXES AND THE VECTOR ARE NOT THE SAME COUNT, and this is
        # not a bug in the reading -- it is the design.
        #
        # MEASURED 2026-10-28: the constitution declares EIGHT axes
        # (boundaries, coherence, stability, routing, recovery,
        # authenticity, norm, commit_radius) and its psi_0 is a SIXTEEN
        # dimensional VECTOR. The vector is the ground's EMBEDDING --
        # derived from the constitution's own text by
        # `_derive_psi_0` -- so it has one component per embedding
        # dimension, not per axis.
        #
        # The first version of this file named the surplus dimensions
        # "axis_08".."axis_15" and reported 16 axes. That was wrong, and
        # wrong in a way that mattered: the vocabulary is the AXIS
        # NAMES, and a vocabulary padded with invented names matches
        # things the system is not. So the axes are the axes, and the
        # vector's dimensions are reported as dimensions.
        for i, nm in enumerate(names):
            v = float(psi[i]) if i < psi.size else 0.0
            aw.axes.append(Axis(name=nm, value=v))
        aw.vocabulary = list(names)
        aw.vector_dim = int(psi.size)
    except Exception as exc:  # noqa: BLE001
        degraded.append("the ground could not be read: %r" % (exc,))

    # -- layer 2: the locus --------------------------------------------
    try:
        from locus import Locus
        stalks = _stalks()
        loc = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
        d = loc.describe()
        aw.locus = {
            "coordinate": d.get("coordinate", ""),
            "stalks": d.get("stalks"),
            "states": d.get("states"),
            "modes": d.get("modes"),
            "chain_intact": d.get("chain_intact"),
            "ground_protected": d.get("ground_protected"),
        }
    except Exception as exc:  # noqa: BLE001
        degraded.append("the locus could not be built: %r" % (exc,))

    # -- layer 3: the vocabulary ---------------------------------------
    aw.topics = _project_topics()
    if not aw.topics:
        degraded.append("the project's topics could not be read")

    # -- the digest ----------------------------------------------------
    # OVER THE IDENTITY, NOT OVER THE PHASE. The locus coordinate moves
    # by design; if the digest covered it, every tick would look like a
    # change and "what changed" would be useless.
    parts = [a.describe() for a in aw.axes]
    parts += sorted(aw.vocabulary)
    parts += sorted("%s:%s" % (k, v) for k, v in aw.topics.items())
    parts += ["%s=%s" % (k, aw.locus.get(k)) for k in
              ("stalks", "modes", "chain_intact", "ground_protected")]
    aw.digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]

    return aw


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE LOCUS OF AWARENESS")
    print("=" * 78)
    print()

    aw = build_awareness()
    d = aw.describe()
    print("1. THE GROUND -- %d axes, %d-dim vector, write-protected: %s"
          % (d["n_axes"], d["vector_dim"], d["locus"].get("ground_protected")))
    for a in d["axes"][:8]:
        print("   %s" % a)
    print()

    print("2. THE LOCUS -- %s stalks, %s modes, chain intact: %s"
          % (d["locus"].get("stalks"), d["locus"].get("modes"),
             d["locus"].get("chain_intact")))
    print("   coordinate: %s" % d["locus"].get("coordinate"))
    print()

    print("3. THE VOCABULARY -- %d topics" % d["n_topics"])
    print("   axis names: %s" % ", ".join(d["vocabulary"][:8]))
    print("   digest: %s" % d["digest"])
    print()

    print("4. RELEVANCE -- the scoring, on three candidates:")
    cases = [
        ("a manifold learning library in python",
         ["manifold"]),
        ("a shopping list app",
         ["shopping"]),
        ("a sheaf construction for topological data analysis",
         ["sheaf", "topology"]),
        ("an agent runtime with a constitutional governor",
         ["agent-runtime", "governor"]),
    ]
    for text, topics in cases:
        r = aw.is_relevant(text, topics)
        print("   %-46s relevant=%-5s score=%s" % (text[:44], r["relevant"], r["score"]))
        for h in r["hits"][:3]:
            print("        %s: %s (%.1f)" % (h["kind"], h["term"], h["weight"]))
    print()

    print("5. THE DEGRADED LIST -- what could not be read: %s"
          % (d["degraded"] or "nothing"))
    print()
    print("   Run: python src/awareness.py --selftest")
    return 0


def main() -> int:
    if "--show" in sys.argv:
        print(json.dumps(build_awareness().what_am_i(), indent=2))
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
