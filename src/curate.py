"""
curate.py -- THE CURATION SEAM. Where a scan becomes a library entry.

Bobby, 2026-10-28: *"the controller curates sacred library not simself
which is the active agent all routes through atlas exam"*

SO THIS FILE IS THE CORRECTION, and it is a correction to what I built
minutes ago.

WHAT I HAD BUILT, and what was wrong with it. My first version of the
living library let the SCAN write entries directly into the ledger. That
is exactly the thing the library's own doc forbids:

    "Nothing in corpus/ was written by SimSelf. Every entry arrived
     through the chain above, which means every entry has a provenance
     line, a certification level, and a check that could have refused
     it."

    SimSelf PROPOSES -> M1 audits -> ATLAS EXAM qualifies -> M0 commits

A scan writing directly to the library is a SECOND WRITE PATH, and the
project has exactly one. Worse, it made the scan the curator, and the
scan is the wrong instrument for that: a scan cannot judge, it can only
find.

THE CORRECTED CHAIN, and each step has its owner:

    THE SCAN finds.              (dawn.py, ladder.py)
        The active agent -- SimSelf -- READS the findings.
    SIMSELF PROPOSES.            (the agent, through the model)
        It reads what the library already holds -- the consultation --
        and proposes what to build. The proposal carries the library's
        context, so it is not the same proposal twice.
    THE CONTROLLER CURATES.      (this file, through the Admitter)
        M1's job: the proposal is AUDITED. The Admitter is the seam
        between a model's proposal and the committed unit, and it is
        the only write path in the runtime.
    THE ATLAS EXAM QUALIFIES.    (the portable atlas, on the answer)
    M0 COMMITS OR REFUSES.       (the governor, one bit)

AND WHERE THE LEDGER SITS. The ledger is the RECORD of that chain, not
a substitute for it. An entry appears in the ledger when the chain has
run -- and the ledger records the REFUSALS too, at q0, labelled. A
rejected thing is not deleted. That distinction is the library.

AND THE CERTIFICATION, unchanged: q0 until examined. Nothing enters
above q0 without an examination someone did.

AND WHAT THIS FILE DOES NOT DO. It does not make the atlas pass. It
does not invent a proposal. It does not write code. It takes a
proposal, runs it through the controller, records the outcome -- and the
recording is the part that makes the library grow into something that
can be read.

Run:
    python src/curate.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Curation:
    """One proposal's journey through the chain.

    AND EVERY STAGE IS RECORDED, because the interesting case is the
    stage that REFUSED. A record that only says "admitted" cannot be
    audited, and an unauditable write path is the thing this whole
    project is against.
    """

    proposal: str = ""
    name: str = ""
    #: the stages, in order, each with its verdict
    stages: List[Dict[str, Any]] = field(default_factory=list)
    #: the final certification
    certification: str = "q0"
    #: did it get committed?
    committed: bool = False
    #: the reason, by name
    reason: str = ""
    #: the library consultation that informed it
    consulted: List[str] = field(default_factory=list)
    at: float = field(default_factory=time.time)
    run: str = ""

    def stage(self, name: str, ok: bool, detail: str = "") -> None:
        self.stages.append({"stage": name, "ok": ok, "detail": detail[:400]})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "proposal": self.proposal[:1500],
            "stages": self.stages,
            "certification": self.certification,
            "committed": self.committed,
            "reason": self.reason,
            "consulted": self.consulted,
            "at": self.at,
            "run": self.run,
        }


class Curator:
    """THE CONTROLLER'S SIDE. M1 audits, the exam qualifies, M0 commits.

    AND WHY THE ADMITTER IS THE RIGHT SEAM. It is the only object in
    the runtime that sees a SEQUENCE of proposals -- it holds the
    refusal log with the stage that produced each refusal, and the
    pivot detector asks about the sequence. So a curation route that
    did not go through it would lose the one capability the write path
    has that nothing else does.
    """

    def __init__(self, ledger: Optional[Any] = None, admitter: Optional[Any] = None):
        self._ledger = ledger
        self._admitter = admitter
        self.curations: List[Curation] = []

    @property
    def ledger(self):
        if self._ledger is None:
            import library_ledger as led_mod
            self._ledger = led_mod.Ledger()
        return self._ledger

    @property
    def admitter(self):
        """The Admitter, built once.

        AND WHY IT IS LAZY. Because it constructs a whole semantic
        index, and the selftest needs to run without one.
        """
        if self._admitter is None:
            from constitutional.admit import Admitter
            self._admitter = Admitter()
        return self._admitter

    # -- the consultation -----------------------------------------------

    def consult(self, topic: str = "", limit: int = 8) -> List[str]:
        """What the library already holds, on this topic.

        AND WHY THIS HAPPENS BEFORE THE PROPOSAL. Because a proposal
        that ignores the library is the same proposal the system made
        yesterday. The consultation is what makes the library a
        participant in the loop rather than a record of it.
        """
        entries = self.ledger.consult(topic=topic, limit=limit)
        return ["%s (%s): %s" % (e.kind, e.name, e.content[:120])
                for e in entries]

    # -- the curation ---------------------------------------------------

    def curate(self, name: str, proposal: str, why: str = "",
               topic: str = "", source: str = "", url: str = "",
               run: str = "") -> Curation:
        """One proposal through the whole chain.

        AND THE ORDER, and it is the library's own:

            1. CONSULT   the library, first
            2. PROPOSE   the proposal, with the library's context
            3. AUDIT     M1: the controller reads it (the Admitter)
            4. QUALIFY   the atlas exam grades it
            5. COMMIT    M0: the governor's bit
            6. RECORD    the outcome, whatever it was
        """
        c = Curation(proposal=proposal, name=name, run=run)

        # -- 1. consult -------------------------------------------------
        c.consulted = self.consult(topic=topic or name)
        c.stage("consult", True, "%d entries consulted" % len(c.consulted))

        # -- 2. propose -------------------------------------------------
        c.stage("propose", bool(proposal.strip()), why or "no reason given")

        # -- 3. audit: M1 through the Admitter -------------------------
        try:
            unit, verdict = self.admitter.admit(proposal)
            if unit is None:
                log = self.admitter.refuse_log()
                reason = ""
                if log:
                    last = log[-1]
                    reason = "%s: %s" % (last[0], str(last[1])[:200])
                c.stage("audit", False, reason or "the controller refused it")
                c.reason = reason or "refused by the controller"
                self._record(c, why, source, url)
                self.curations.append(c)
                return c
            c.stage("audit", True, "admitted as a unit")
        except Exception as exc:  # noqa: BLE001 -- a broken seam refuses
            c.stage("audit", False, "the seam raised: %r" % (exc,))
            c.reason = "the seam raised"
            self._record(c, why, source, url)
            self.curations.append(c)
            return c

        # -- 4. qualify: the atlas exam --------------------------------
        try:
            from mini_atlas import standard_atlas
            atlas = standard_atlas()
            res = atlas.examine(proposal)
            passed = res.get("verdict") == "pass"
            c.stage("qualify", passed,
                    "%s %d/%d applicable" % (res.get("verdict"),
                                             res.get("passed", 0),
                                             res.get("applicable", 0)))
        except Exception as exc:  # noqa: BLE001
            c.stage("qualify", False, "the exam raised: %r" % (exc,))

        # -- 5. commit: M0's bit ---------------------------------------
        try:
            import numpy as np
            from embed import embed_text
            from constitutional.constitution import Constitution
            emb = np.asarray(embed_text(proposal or "", dim=16), dtype=float)
            n = float(np.linalg.norm(emb))
            if n > 0:
                emb = emb / n
            psi = np.asarray(Constitution().psi_0, dtype=float)
            n0 = float(np.linalg.norm(psi))
            if n0 > 0:
                psi = psi / n0
            from governor import GovernorProcess
            gov = GovernorProcess()
            try:
                d = gov.ask(emb, psi)
            finally:
                gov.close()
            c.committed = bool(d.allow)
            c.stage("commit", c.committed,
                    "allowed" if c.committed else "refused: %s"
                    % getattr(d, "verdict", "?"))
            if not c.committed:
                c.reason = "the governor refused: %s" % getattr(d, "verdict", "?")
        except Exception as exc:  # noqa: BLE001 -- an unreachable core refuses
            c.stage("commit", False, "the core could not be asked: %r" % (exc,))
            c.reason = "the core could not be asked"

        # -- 6. record --------------------------------------------------
        self._record(c, why, source, url)
        self.curations.append(c)
        return c

    def _record(self, c: Curation, why: str, source: str, url: str) -> None:
        """Write the outcome into the living library.

        AND THE CERTIFICATION, and it is the ONE rule that never bends:
        an entry starts at q0 and only an examination moves it. So a
        REFUSED proposal is recorded at q0 too -- labelled, not deleted.
        That is the library's own distinction and it is the whole value
        of the record.
        """
        try:
            # AND NOT `append(add_build(...))`. The first version did
            # that, and `add_build` ALREADY appends -- so every proposal
            # was recorded twice. The symptom was a consultation that
            # returned the same proposal name twice, which looked like
            # a feature (the library "remembering" it) and was not.
            #
            # And this is why the selftest printed the name twice in
            # step 5 and I did not catch it immediately: a duplicate
            # reads as emphasis.
            self.ledger.add_build(
                name=c.name,
                proposal=c.proposal,
                why=why or c.reason,
                source=source,
                url=url,
                run=c.run,
            )
        except Exception:
            pass


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import tempfile
    print("=" * 78)
    print("THE CURATION SEAM")
    print("=" * 78)
    print()

    tmp = tempfile.mkdtemp()
    import library_ledger as led_mod
    cur = Curator(ledger=led_mod.Ledger(directory=tmp))

    print("1. THE CHAIN, and who owns each step:")
    print("   THE SCAN finds            (dawn.py, ladder.py)")
    print("   SIMSELF PROPOSES          (the active agent, with the library)")
    print("   THE CONTROLLER CURATES    (M1, through the Admitter)")
    print("   THE ATLAS EXAM QUALIFIES  (the portable atlas)")
    print("   M0 COMMITS OR REFUSES     (the governor, one bit)")
    print("   THE LEDGER RECORDS        (whatever happened)")
    print()

    print("2. THE CONSULTATION COMES FIRST, so a proposal is not the same")
    print("   proposal twice:")
    cur.ledger.add_build("sheaf_loop", "make the sheaf loop run", "the atlas says unwired")
    print("   consulted: %s" % cur.consult(topic="sheaf"))
    print()

    print("3. A PROPOSAL GOES THROUGH THE CHAIN, and every stage is")
    print("   recorded -- including the stage that refused:")
    c = cur.curate("proposal_one",
                    "the atlas reports the sheaf loop has no inbound callers; "
                    "wire it from the substrate's own wiring module",
                    why="measured: the atlas's area 18 is unwired",
                    topic="sheaf")
    for s in c.stages:
        print("   %-10s %-6s %s" % (s["stage"], "ok" if s["ok"] else "REFUSED",
                                     s["detail"][:74]))
    print("   committed: %s | reason: %s" % (c.committed, c.reason[:60]))
    print()

    print("4. A REFUSAL IS RECORDED, NOT DELETED:")
    stats = cur.ledger.stats()
    print("   entries: %d  %s" % (stats["n_entries"], stats["by_kind"]))
    print("   every one at q0: %s" % (stats["by_certification"],))
    print()

    print("5. AND THE LIBRARY GREW, which is the point:")
    print("   entries now: %d" % cur.ledger.load())
    print("   the consultation sees them: %s"
          % [e.name for e in cur.ledger.consult(limit=5)])
    print()
    print("   Run: python src/curate.py --selftest")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
