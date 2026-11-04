"""
fc_hermes.py -- THE APP, AS A WRAPPER AROUND HERMES.

Bobby, 2026-11-02: *"use either wrapper around hermes or standalone app
the whole system fc and all modules they are lettered use stubs for
undeveloped ones"*.

SO BOTH, AND THEY ARE NOT ALTERNATIVES. They are two ends of one thing:

    fc_app.py        the INVENTORY -- ten letters, each measured
    fc_hermes.py     the BRIDGE -- the same system, serving a live session

`fc_app.py` answers "what is live and what is stubbed". This file
answers "give me an answer, through the whole system, from the ground".

THE SHAPE OF THE BRIDGE, and why it is a bridge and not a plugin:

  A PLUGIN guards the session -- it reads the reply Bobby reads and the
  tool calls Bobby's machine runs. It sits INSIDE Hermes.

  A WRAPPER sits OUTSIDE Hermes and the model is INSIDE it. The model
  becomes a callee. The instruments -- the gate, the ground, the locus,
  the governor, the atlas, the library -- stay outside the thing they
  govern, which is the whole architecture of this project.

  Both are useful and they are different seams. `fieldcore-gate` is
  already installed as the plugin, so the plugin seam is taken. This
  file is the wrapper seam.

THE ORDER, and the order is the architecture:

    1. THE GATE reads the PROMPT        a request to weaken the ground
                                         never reaches the model
    2. SIMSELF GIVES THE LOCUS          the substrate is the answering
                                         position, not a topic
    3. THE MODEL answers                 through the MTE, which is the
                                         deterministic edge
    4. THE GATE reads the ANSWER         a fluent answer can assert
                                         something false about the system
    5. THE GOVERNOR vetoes               one bit, out of process
    6. THE ATLAS grades the answer       8 areas, on every answer
    7. THE LIBRARY records it            append-only, versioned

AND WHAT THIS FILE ADDS OVER `fc_wrapper.py`, which already does all
seven: the TEN LETTERS. `fc_wrapper` is the control system for one
exchange. This file is the control system plus the inventory, so a
caller can ask BOTH questions in one process:

    the bridge    "what does the system say?"
    the survey    "and what is actually running?"

THE SPEND GUARD IS CLOSED BY DEFAULT. `GABRIELLE_ALLOW_LIVE=1` opens
it. With it closed, the LOCAL CONSTRUCTED MIND answers -- which is not
a stub, it is the constructed-from-signal mind the project is building,
and it reports that it answered. So the bridge runs end to end with no
credential and no spend.

Run:
    python src/fc_hermes.py --ask "what is the ground?"
    python src/fc_hermes.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The spend guard. CLOSED by default.
ALLOW_LIVE = os.environ.get("GABRIELLE_ALLOW_LIVE", "") == "1"


@dataclass
class Reply:
    """One answer, and everything that decided it."""
    prompt: str = ""
    answer: str = ""
    delivered: bool = False
    answered_by: str = ""
    #: the trace, one line per instrument
    trace: List[str] = field(default_factory=list)
    #: the letter survey, so a caller sees the system AND its state
    letters: List[Dict[str, Any]] = field(default_factory=list)
    elapsed: float = 0.0
    #: the steps with their ok bit, so a caller can check a refusal
    #: rather than read a string
    steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "answer": self.answer,
            "delivered": self.delivered,
            "answered_by": self.answered_by,
            "trace": self.trace,
            "steps": self.steps,
            "letters": self.letters,
            "elapsed_s": round(self.elapsed, 3),
        }


class Bridge:
    """The whole system, serving a live session.

    AND THE COMPOSITION IS LAZY. The wrapper, the gate, the atlas, the
    library, the locus and the governor are each resolved on first use,
    so a missing checkout degrades ONE instrument to "unavailable" and
    names it -- it does not make this module unimportable, and it does
    not silently drop a check.
    """

    def __init__(self, live: Optional[bool] = None):
        from fc_wrapper import FieldCoreWrapper
        self.live = ALLOW_LIVE if live is None else live
        self._wrapper = FieldCoreWrapper(live=self.live)

    # -- the exchange ---------------------------------------------------

    def ask(self, prompt: str, learn: bool = True) -> Reply:
        import time
        t0 = time.time()
        r = Reply(prompt=prompt)
        ex = self._wrapper.ask(prompt, learn=learn)
        r.answer = ex.answer
        r.delivered = ex.delivered
        r.answered_by = ex.answered_by
        # AND THE TRACE CARRIES THE ok BIT.
        #
        # MEASURED 2026-11-04: the previous version built the trace as
        # "<step>: <detail>" and DROPPED the ok bit. The wrapper's own
        # `Exchange.trace()` renders "ok" or "REFUSED" per step, and
        # that bit is the difference between "the gate read the answer
        # and found nothing wrong" and "the gate REFUSED the answer".
        #
        # MEASURED: asked "the ground is a parameter at the call site",
        # the gate refused at the prompt step -- the wrapper's trace
        # showed "gate/prompt  REFUSED ..." and the bridge's trace
        # showed "gate/prompt: an advisory catch on the fail-closed
        # path: ..." with nothing to say the step did not pass. A
        # refusal that reads as a clearance is worse than no trace.
        #
        # So the trace keeps the bit, and the steps are also carried
        # as data, so a caller can CHECK the refusal instead of reading
        # a string and hoping.
        r.trace = ["%-14s %-7s %s" % (s.name, "ok" if s.ok else "REFUSED",
                                     s.detail[:110])
                   for s in ex.steps]
        r.steps = [s.to_dict() for s in ex.steps]
        r.letters = self.survey()
        r.elapsed = time.time() - t0
        return r

    # -- the survey -----------------------------------------------------

    def survey(self) -> List[Dict[str, Any]]:
        """The ten letters, each measured.

        AND WHY THE BRIDGE CARRIES IT. A bridge that answers without
        saying what is running is a bridge that hides its own state. The
        caller gets the answer AND the inventory in one call.
        """
        import fc_app
        return [lt.to_dict() for lt in fc_app.survey()]

    # -- the description ------------------------------------------------

    def describe(self) -> Dict[str, Any]:
        """What is wired, and what the letters say.

        AND THE INSTRUMENTS ARE AT THE TOP LEVEL, not nested one level
        down under "instruments".

        MEASURED 2026-11-04: the previous version put the wrapper's
        whole `describe()` dict under the key "instruments", so the
        per-instrument entries sat at `d["instruments"]["instruments"]
        ["gate"]`. A caller asking "is the gate wired?" had to know
        that the bridge's shape was NOT the wrapper's shape -- and the
        bridge's own selftest carried that workaround inline.

        So the bridge reports the instruments the same way the wrapper
        does: `d["instruments"]["gate"]`. The wrapper's whole report is
        still carried, under "wrapper", for anything that wants it.

        RED: if the nesting came back, this fails.
        """
        import fc_app
        letters = fc_app.survey()
        wrapper_report = self._wrapper.describe()
        return {
            "live": self.live,
            "spend_guard": "open" if self.live else "closed",
            "instruments": wrapper_report.get("instruments", {}),
            "wrapper": wrapper_report,
            "letters": {
                "live": sum(1 for l in letters if l.state == "LIVE"),
                "stub": sum(1 for l in letters if l.state == "STUB"),
                "dark": sum(1 for l in letters if l.state == "DARK"),
                "states": {l.letter: l.state for l in letters},
            },
        }


# ===========================================================================
# THE ENTRY POINTS
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("THE APP AS A WRAPPER AROUND HERMES")
    print("=" * 78)
    print()
    b = Bridge(live=False)

    d = b.describe()
    print("1. THE SPEND GUARD: %s" % d["spend_guard"])
    print()
    print("2. THE INSTRUMENTS:")
    for name, info in sorted(d["instruments"].items()):
        mark = "ok" if info.get("available") else "UNAVAILABLE"
        detail = info.get("type") or info.get("error", "")[:70]
        print("   %-10s %-12s %s" % (name, mark, detail))
    print()
    print("3. THE TEN LETTERS:")
    for letter, state in sorted(d["letters"]["states"].items()):
        print("   %s  %s" % (letter, state))
    print("   LIVE %d  STUB %d  DARK %d"
          % (d["letters"]["live"], d["letters"]["stub"],
             d["letters"]["dark"]))
    print()
    print("4. ONE EXCHANGE, through all seven instruments:")
    r = b.ask("what is the FieldCore ground and why is it write-protected?")
    for line in r.trace:
        print("   %s" % line)
    print()
    print("   answered by: %s" % r.answered_by)
    print("   delivered:   %s" % r.delivered)
    print()
    for line in (r.answer or "").splitlines():
        print("   %s" % line)
    print()
    print("=" * 78)
    print("  So: the bridge runs with the spend guard CLOSED, the local")
    print("  constructed mind answers, and every instrument is named.")
    print("=" * 78)
    return 0


def ask(prompt: str) -> int:
    b = Bridge(live=ALLOW_LIVE)
    r = b.ask(prompt)
    for line in r.trace:
        print(line)
    print()
    print("answered by: %s" % r.answered_by)
    print("delivered:   %s" % r.delivered)
    print()
    print(r.answer)
    print()
    print("-" * 78)
    for letter in r.letters:
        print("  [%s] %s %s" % (letter["state"], letter["letter"],
                                letter["name"]))
    return 0 if r.delivered else 1


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--ask" in argv:
        i = argv.index("--ask")
        prompt = argv[i + 1] if i + 1 < len(argv) else "what is the ground?"
        return ask(prompt)
    if "--describe" in argv:
        print(json.dumps(Bridge(live=False).describe(), indent=2, default=str))
        return 0
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main())
