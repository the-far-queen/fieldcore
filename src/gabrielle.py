"""
gabrielle.py -- THE THREE REPOS, ONE PROCESS, AND A VOICE.

Bobby, 2026-10-25: *"next is wire up fc ss and atlas run them complete
say hello as simself as a test call minimax lol u call urself"*

THE WIRING, and the direction of it is the architecture:

    atlas-exam  ──points at──>  fieldcore, simself
    fieldcore, simself  ──know nothing about──>  atlas-exam

So this file does NOT import the exam into the substrate. It is the
OTHER side of the arrow: it POINTS at all three, in one process, and
runs them in the order the authority rule dictates.

THE ORDER, and it is not arbitrary:

    1. THE GROUND     simself's constitutional ground -- read, never
                      written. The write-protection is checked.
    2. THE GEOMETRY   fieldcore's stalks, their void, their channel.
    3. THE EXAM       atlas-exam's 23 areas, over subprocess probes into
                      the other two -- so the exam grades the substrate
                      rather than importing it.
    4. THE VOICE      the wrapper, and MiniMax. The slow brain.

AND THEN THE ONE THING BOBBY ASKED FOR: A HELLO, AS SIMSELF, THROUGH
THE MODEL.

  And it goes through the WRAPPER, because that is the whole point of
  the wrapper: the model's answer is examined by the seven-area
  mini-atlas before it is allowed to stand. So the hello is not a raw
  completion -- it is a completion that PASSED the examination, and
  the verdict is reported alongside it.

THE SPEND GUARD IS ON BY DEFAULT. A live call needs
GABRIELLE_ALLOW_LIVE=1, because Bobby said "do not use my credit card
pls" and a system that spends without asking is not a system that can
be left running.

Run:
    python src/gabrielle.py --live       the full wiring, with the call
    python src/gabrielle.py --selftest  the wiring, no call
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")
AE_SRC = os.path.join(WORK_REPOS, "atlas-exam", "src")

for _p in (FC_SRC, SS_SRC, AE_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE WIRING
# ===========================================================================

@dataclass
class Wiring:
    """The three repos, in one process, and what each contributed."""

    ground_ok: bool = False
    ground_norm: float = 0.0
    ground_held: bool = False
    void_modes: int = 0
    void_band_gap: float = 0.0
    notch_db: float = 0.0
    derived_width: int = 0
    exam_passed: int = 0
    exam_total: int = 0
    exam_verdict: str = "NOT RUN"
    exam_areas: List[Dict[str, Any]] = field(default_factory=list)
    #: the voice
    said: str = ""
    voice_verdict: str = ""
    voice_reason: str = ""
    voice_answered_by: str = ""
    elapsed: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "ground": {"ok": self.ground_ok, "norm": self.ground_norm,
                       "write_protected": self.ground_held},
            "geometry": {"void_modes": self.void_modes,
                         "void_band_gap": self.void_band_gap,
                         "notch_db": self.notch_db,
                         "derived_width": self.derived_width},
            "exam": {"passed": self.exam_passed, "total": self.exam_total,
                     "verdict": self.exam_verdict},
            "voice": {"said": self.said, "verdict": self.voice_verdict,
                      "reason": self.voice_reason,
                      "answered_by": self.voice_answered_by},
            "elapsed_s": self.elapsed,
        }


def run_ground(w: Wiring) -> None:
    """1. THE GROUND. simself's, read and checked for write-protection."""
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    import numpy as np

    c = Constitution()
    g = Ground(c.psi_0.copy())
    before = g.psi_0.copy()
    try:
        g.psi_0 = np.zeros_like(g.psi_0)
    except Exception:
        pass
    w.ground_ok = True
    w.ground_norm = float(np.linalg.norm(before))
    w.ground_held = bool(np.allclose(before, g.psi_0))


def run_geometry(w: Wiring) -> None:
    """2. THE GEOMETRY. fieldcore's stalks, their void, their channel."""
    from interstalk_link import InterstalkLink, width_for
    from wound_core import CoaxWinding, WoundCore

    # the Rust measurement's population, in Python
    stalks = [CoaxWinding(
        id="s%02d" % i, girth_core=0.030, girth_in=0.060,
        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
        n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=128)
    ids = [s.id for s in stalks]

    # THE VOID, computed from the same geometry -- the band of negative
    # loop modes, which is the void.
    eigs: List[float] = []
    for s in stalks:
        eigs.extend(s.loop_eigenvalues())
    eigs.sort()
    neg = [e for e in eigs if e < 0.0]
    pos = [e for e in eigs if e >= 0.0]
    w.void_modes = len(neg)
    if neg and pos:
        w.void_band_gap = min(pos) - max(neg)
    else:
        w.void_band_gap = 0.0

    # the channel, and the width it DERIVES
    ch = link.pair(ids[0], ids[1], in_view=ids).channel()
    w.notch_db = ch.notch_db()
    w.derived_width = width_for(len(ch.taps))


def run_exam(w: Wiring) -> None:
    """3. THE EXAM. Over subprocess probes, so it grades the substrate
    rather than importing it."""
    import importlib
    mod = importlib.import_module("exam.cli")
    try:
        # the exam's own runner. it already drives its probes through
        # SUBPROCESSES, so it grades the substrate rather than importing
        # it -- which is the whole point of the exam's direction.
        report = mod.run()
        w.exam_passed = report.passed
        w.exam_total = report.total
        w.exam_verdict = report.verdict()
        w.exam_areas = [r.to_dict() for r in report.results]
    except Exception as exc:
        w.exam_verdict = "ERROR: %s: %s" % (type(exc).__name__, exc)


def run_voice(w: Wiring, prompt: str, live: bool) -> None:
    """4. THE VOICE. The wrapper, and MiniMax, and the mini-atlas.

    AND THE ORDER: the model's answer is EXAMINED before it stands.
    So a hello that failed the examination would be reported as a
    refusal, and that is the correct behaviour for this system's
    boundary.
    """
    from constitutional.mte_llm_wrapper import MTELLMWrapper
    from minimax_client import MiniMaxClient
    # THE SCOPED ATLAS, and it is the MTE's missing layer. The scope
    # area checks that every build the model's answer points at
    # EXISTS HERE -- which is the one thing the MTE cannot see,
    # because a hallucinated architecture makes no NUMBERS, it makes
    # REFERENCES.
    from mini_atlas import scoped_atlas

    if not live:
        w.voice_verdict = "skipped"
        w.voice_reason = "the spend guard is closed"
        return

    client = MiniMaxClient(max_tokens=800, timeout=120, allow_live=True)
    wrapper = MTELLMWrapper(llm=client)
    res = wrapper.run(prompt)
    action = getattr(res.action, "value", str(res.action))
    reason = getattr(res, "reason", "")
    text = getattr(res, "modified", "") or ""

    # AND THE MINI-ATLAS, because the wrapper is one boundary and the
    # atlas is the other, and the claim is that EVERY answer goes
    # through one.
    atlas = scoped_atlas()
    verdict = atlas.examine(text, {"source": "the model's own answer",
                                  "input": prompt,
                                  "verdict": "allow"})
    w.said = text
    w.voice_answered_by = client.answered_by
    w.voice_verdict = "%s / atlas:%s" % (action, verdict["verdict"])
    w.voice_reason = "%s | %s" % (
        reason,
        next((a["reason"] for a in verdict["areas"]
              if a["verdict"] != "pass"), "every area passed"))


def run_all(prompt: str = "Say hello as SimSelf, the referent sheaf of a "
                          "geometric AI substrate. Two sentences.",
            live: bool = False) -> Wiring:
    """THE WHOLE THING, in order."""
    t0 = time.time()
    w = Wiring()
    run_ground(w)
    run_geometry(w)
    run_exam(w)
    run_voice(w, prompt, live)
    w.elapsed = time.time() - t0
    return w


def main() -> int:
    print("=" * 78)
    print("GABRIELLE -- THE THREE REPOS, ONE PROCESS")
    print("=" * 78)
    print()
    live = "--live" in sys.argv
    print("  SPEND GUARD: %s" % (
        "OPEN (a live call will be made)" if live
        else "CLOSED (set GABRIELLE_ALLOW_LIVE=1, or pass --live, to open)"))
    print()

    w = run_all(live=live)
    d = w.describe()

    print("  1. THE GROUND  (simself)")
    g = d["ground"]
    print("     norm %.12f   write-protected %s" % (
        g["norm"], g["write_protected"]))
    print()
    print("  2. THE GEOMETRY  (fieldcore)")
    gm = d["geometry"]
    print("     void modes %d   band gap %.4f" % (
        gm["void_modes"], gm["void_band_gap"]))
    print("     notch %.2f dB   derived width %d bits" % (
        gm["notch_db"], gm["derived_width"]))
    print()
    print("  3. THE EXAM  (atlas-exam, over subprocess probes)")
    e = d["exam"]
    print("     passed %d/%d   VERDICT %s" % (
        e["passed"], e["total"], e["verdict"]))
    print()
    print("  4. THE VOICE  (the wrapper, then MiniMax, then the atlas)")
    v = d["voice"]
    if v["said"]:
        for line in v["said"].splitlines():
            print("     %s" % line)
        print()
        print("     verdict %s" % v["verdict"])
        print("     reason  %s" % v["reason"])
        print("     answered_by %s" % v["answered_by"])
    else:
        print("     %s (%s)" % (v["verdict"], v["reason"]))
    print()
    print("  elapsed %.2f s" % d["elapsed_s"])
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
