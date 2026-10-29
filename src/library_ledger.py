"""
ledger.py -- THE LIVING LIBRARY. What the system knows, and what it
plans to build.

Bobby, 2026-10-28: *"the method is inhabit simself and not wonder how to
grow with fc but rather cron job find repos and research sort scavenge
suggest build as simself consult with growing sacred library which
doesn't just list texts is the ongoing library of all info incl what to
build a living resource"*

SO THIS FILE IS THE THIRD PIECE, and it is the one that makes the other
two a LOOP rather than two separate scans.

THE CHAIN, as Bobby states it:

    SCAN        find repos and research      (dawn.py, ladder.py)
    RESEARCH    understand what they are      (the scavenger)
    SORT        by the system's own relevance (awareness.py)
    SCAVENGE    extract the load-bearing parts
    SUGGEST     propose what to BUILD from it
    CONSULT     simself reads the growing library before proposing
    LIBRARY     the living record, which grows

AND THE IMPORTANT PART: **the library is not a list of texts.** It is
the ongoing record of everything the system has found, read, sorted and
judged -- AND of what it plans to build. A library of only finished
things is an archive. A library that also holds what is NEXT is the
reason the system can plan.

THE THREE KINDS OF ENTRY, and they are different in kind, not in
format:

    FINDING    something the world offered, and the system's reading of
               it. q0 until examined.
    BUILD      a proposal -- what to build, and why. This is the part
               that makes the library forward-looking.
    NOTE       what the system learned about itself.

AND THE CERTIFICATION IS THE LIBRARY'S SPINE, and it is not decoration.
`SACRED-LIBRARY.md` states the rule the whole project rests on:

    SimSelf PROPOSES -> M1 audits -> ATLAS EXAM qualifies -> M0 commits

    "Nothing in corpus/ was written by SimSelf. Every entry arrived
     through the chain above, which means every entry has a provenance
     line, a certification level, and a check that could have refused
     it."

So an entry in this ledger starts at q0 and can only rise by being
examined. A rejected entry is NOT deleted -- it is LABELLED. That
distinction is the library.

AND WHY THE LEDGER IS NOT THE SACRED LIBRARY'S ENGINE. The engine
(`simself/src/constitutional/sacred_library.py`) archives CODE -- it
writes `<name>_<hash>.py` files. It is the right store for skills and
the wrong store for a research ledger, which needs provenance, scores,
paths, and a certification that a gate moved. So there are two stores
with one rule, and the rule is the same: nothing enters above q0 without
an examination.

AND WHERE IT LIVES. NOT in the repo -- it changes every day and the
substrate does not. Beside the state, and mirrored to the vault, so it
survives a reinstall.

AND WHAT THIS DOES NOT DO. It does not admit anything. It records
proposals at q0 and lets the gate decide. A ledger that admitted things
would be a second write path, and the project has exactly one.

Run:
    python src/ledger.py --selftest
    python src/ledger.py --show
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))

#: Where the ledger lives. Beside the state, NOT in the repo.
LEDGER_DIR = os.environ.get(
    "FC_LEDGER_DIR",
    os.path.join(WORK_REPOS, "fieldcore_state", "ledger"))

#: The certification levels, from `sacred_library.py`, unchanged.
CERTIFICATION_LEVELS = ("q0", "q1", "q2", "q3", "q4")

#: What each level MEANS, and it is the engine's own scheme.
CERT_MEANING = {
    "q0": "arrived, not yet examined",
    "q1": "sourced",
    "q2": "cross-referenced against another tradition",
    "q3": "SNR-survived",
    "q4": "canonical -- may be cited as constitutional reference",
}


@dataclass
class Entry:
    """One thing in the living library.

    AND EVERY ENTRY CARRIES ITS PROVENANCE, because the library's own
    doc says that is the difference between a library and a notes
    folder: "every entry has a provenance line, a certification level,
    and a check that could have refused it."
    """

    #: what kind of thing this is
    kind: str = "finding"        # finding | build | note
    #: the thing's name
    name: str = ""
    #: the content -- a description, a paper's abstract, a proposal
    content: str = ""
    #: PROVENANCE. Where it came from, and the path that reached it.
    source: str = ""
    url: str = ""
    #: the path: a list of (player, followed, followed_of_that) tuples
    path: List[Any] = field(default_factory=list)
    #: the system's reading
    relevance: float = 0.0
    score: float = 0.0
    stars: int = 0
    language: str = ""
    #: CERTIFICATION. Starts at q0. Only an examination moves it.
    certification: str = "q0"
    #: the examination that moved it, and why
    examined_by: str = ""
    exam_reason: str = ""
    #: when
    at: float = field(default_factory=time.time)
    #: the run that found it
    run: str = ""
    #: the digest of the awareness that judged it
    awareness_digest: str = ""
    #: extra, kind-specific fields
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["cert_meaning"] = CERT_MEANING.get(self.certification, "")
        return d


class Ledger:
    """THE LIVING LIBRARY. Append-only, certified, growing."""

    def __init__(self, directory: Optional[str] = None):
        self.dir = directory or LEDGER_DIR
        self.entries: List[Entry] = []
        self._loaded = False

    # -- the file -------------------------------------------------------

    @property
    def path(self) -> str:
        return os.path.join(self.dir, "ledger.jsonl")

    def load(self) -> int:
        """Read the ledger from disk.

        AND WHY IT IS READ FROM DISK EVERY TIME. The ledger is written by
        a cron job in a fresh process and read by another. An in-memory
        list would be empty every time it mattered.
        """
        if self._loaded:
            return len(self.entries)
        self._loaded = True
        if not os.path.isfile(self.path):
            return 0
        with open(self.path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                known = {k: v for k, v in d.items()
                         if k in Entry.__dataclass_fields__}
                self.entries.append(Entry(**known))
        return len(self.entries)

    def append(self, entry: Entry) -> Entry:
        """Append one entry. The only write.

        AND WHY THERE IS ONLY ONE WRITE METHOD. Because the library's
        value is that its record cannot be edited -- only appended to
        and, occasionally, certified. A method that could update an
        entry in place would make the record a working document instead
        of an evidence.
        """
        os.makedirs(self.dir, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        self.entries.append(entry)
        self._loaded = True
        return entry

    # -- the three kinds ------------------------------------------------

    def add_finding(self, found: Any, awareness_digest: str = "",
                    run: str = "") -> Entry:
        """A FINDING: something the world offered, and the reading."""
        e = Entry(
            kind="finding",
            name=getattr(found, "full_name", "") or getattr(found, "ident", ""),
            content=(getattr(found, "description", "") or "")[:600],
            source=getattr(found, "source", "") or getattr(found, "url", ""),
            url=getattr(found, "url", ""),
            path=[list(p) for p in getattr(found, "paths", [])][:5],
            relevance=float(getattr(found, "relevance", 0.0)),
            score=float(getattr(found, "score", 0.0)),
            stars=int(getattr(found, "stars", 0)),
            language=getattr(found, "language", "") or "",
            certification="q0",
            run=run,
            awareness_digest=awareness_digest,
        )
        return self.append(e)

    def add_build(self, name: str, proposal: str, why: str,
                  source: str = "", url: str = "",
                  awareness_digest: str = "", run: str = "",
                  relevance: float = 0.0) -> Entry:
        """A BUILD: what to build, and why.

        AND THIS IS THE PART THAT MAKES THE LIBRARY FORWARD-LOOKING. A
        library that holds only what has been found is an archive. This
        one also holds what the system PLANS to build, so the next
        consultation can read the plan and not start over.

        AND IT IS STILL q0. A proposal is a proposal until it is
        examined -- the library's own rule, unchanged.
        """
        e = Entry(
            kind="build",
            name=name,
            content=proposal[:2000],
            source=source,
            url=url,
            certification="q0",
            run=run,
            awareness_digest=awareness_digest,
            relevance=relevance,
            extra={"why": why},
        )
        return self.append(e)

    def add_note(self, name: str, content: str, run: str = "") -> Entry:
        """A NOTE: what the system learned about itself."""
        e = Entry(kind="note", name=name, content=content[:2000],
                  certification="q0", run=run)
        return self.append(e)

    # -- the certification ----------------------------------------------

    def certify(self, name: str, level: str, examined_by: str,
                reason: str) -> Optional[Entry]:
        """Raise an entry's certification. The ONLY way up.

        AND IT APPENDS A NEW ENTRY RATHER THAN EDITING. So the record
        shows the whole history: the finding at q0, and later the
        examination that raised it to q2. A rejected entry is not
        deleted -- it is labelled, and the label is in the record.
        """
        if level not in CERTIFICATION_LEVELS:
            return None
        for e in reversed(self.entries):
            if e.name == name and e.kind != "certification":
                cert = Entry(
                    kind="certification",
                    name=name,
                    content="certified to %s by %s" % (level, examined_by),
                    certification=level,
                    examined_by=examined_by,
                    exam_reason=reason,
                    source=e.source,
                    url=e.url,
                    run=e.run,
                    extra={"of_run": e.run, "of_at": e.at},
                )
                return self.append(cert)
        return None

    # -- the consultation ------------------------------------------------

    def consult(self, topic: str = "", limit: int = 12,
                kinds: Sequence[str] = ("build", "finding", "note")
                ) -> List[Entry]:
        """What the library says, about a topic.

        AND WHY THIS IS A READ AND NOT A SEARCH. Because the point of
        the consultation is that the system reads what it already knows
        BEFORE it proposes anything new. A proposal that ignores the
        library is the same proposal the system made yesterday.

        AND THE ORDER: builds first, then findings, then notes. Because
        a plan is more actionable than an observation, and an
        observation is more actionable than a reflection.
        """
        self.load()
        out: List[Entry] = []
        for kind in kinds:
            for e in reversed(self.entries):
                if e.kind != kind:
                    continue
                if topic and topic.lower() not in (
                        (e.name + " " + e.content).lower()):
                    continue
                out.append(e)
                if len(out) >= limit:
                    return out
        return out

    def stats(self) -> Dict[str, Any]:
        self.load()
        by_kind: Dict[str, int] = {}
        by_cert: Dict[str, int] = {}
        for e in self.entries:
            by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
            if e.kind != "certification":
                by_cert[e.certification] = by_cert.get(e.certification, 0) + 1
        return {
            "path": self.path,
            "n_entries": len(self.entries),
            "by_kind": by_kind,
            "by_certification": by_cert,
            "certification_meanings": CERT_MEANING,
        }


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import tempfile
    print("=" * 78)
    print("THE LIVING LIBRARY")
    print("=" * 78)
    print()

    tmp = tempfile.mkdtemp()
    led = Ledger(directory=tmp)
    print("1. THE THREE KINDS OF ENTRY:")
    led.add_finding(type("F", (), {"full_name": "someone/sheaf", "description": "a sheaf library", "source": "github", "url": "https://github.com/x", "paths": [], "relevance": 4.0, "score": 0.7, "stars": 30, "language": "rust"})(), awareness_digest="abc123")
    led.add_build("sheaf_loop", "make the sheaf loop run in the substrate", "the atlas says sheaves are unwired", relevance=5.0)
    led.add_note("the_ground_holds", "8 axes, 16-dim vector, write-protected")
    print("   finding | build | note  -- three kinds, not one list of texts")
    print()

    print("2. EVERYTHING STARTS AT q0, because the library's rule is that")
    print("   nothing enters above q0 without an examination:")
    for e in led.entries:
        print("   %-10s %-22s %s  (%s)" % (e.kind, e.name[:22], e.certification,
                                           CERT_MEANING[e.certification]))
    print()

    print("3. CERTIFICATION IS THE ONLY WAY UP, and it appends:")
    led.certify("sheaf_loop", "q2", "the atlas", "2 areas passed")
    print("   after certifying 'sheaf_loop' to q2:")
    for e in led.entries[-2:]:
        print("   %-14s %-22s %s" % (e.kind, e.name[:22], e.certification))
    print()

    print("4. A REJECTED ENTRY IS NOT DELETED -- it is LABELLED.")
    print("   (the library's own doc: 'A rejected text is not deleted;")
    print("    it is labeled. That distinction is the library.')")
    print("   entries: %d -- nothing was removed to record the examination"
          % len(led.entries))
    print()

    print("5. THE CONSULTATION, and the order:")
    for e in led.consult(limit=5):
        print("   %-10s %s" % (e.kind, e.name[:40]))
    print()

    print("6. THE LEDGER SURVIVES A FRESH PROCESS:")
    led2 = Ledger(directory=tmp)
    print("   entries reloaded: %d" % led2.load())
    print("   and the stats: %s" % json.dumps(led2.stats()["by_kind"]))
    print()
    print("   Run: python src/ledger.py --selftest")
    return 0


def main() -> int:
    if "--show" in sys.argv:
        led = Ledger()
        print(json.dumps(led.stats(), indent=1))
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
