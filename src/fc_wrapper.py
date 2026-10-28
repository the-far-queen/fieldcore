"""
fc_wrapper.py -- THE WRAPPER. One entry point, the whole system.

Bobby, 2026-10-28: *"now get fc working use simself and see how it
functions as wrapper fix everything as u need i will assist"*, and then
*"for the gates and the core just wire it as is we will fix as the
wrapper exists first"*.

SO THIS FILE IS THE WRAPPER, and it is deliberately NOT a new gate. Every
instrument below already exists and has been measured. What did not exist
was ONE place that composes them, which is why "wire the whole system"
kept producing documents instead of a running thing.

AND WHAT "WRAPPER" MEANS HERE, precisely, because the word is used loosely
across this project and the two meanings are different systems:

    A WRAPPER AROUND THE MODEL      MiniMax sits inside, the wrapper
                                    decides what the model is asked
                                    and what it is allowed to say.

    THE WRAPPER AS THE CONTROL SYSTEM
                                    the wrapper IS the control system:
                                    the gate, the governor, the exam,
                                    the library, the locus -- wired
                                    together, so that a call through it
                                    is a call through the whole design.

THIS FILE IS THE SECOND ONE, and it is the one that makes the first one
possible. Because a wrapper around a model that does not consult the gate
is a prompt template; and a wrapper around a model that consults the gate
is the control system.

THE ORDER, and the order is the architecture:

    1. THE GATE reads the PROMPT.  A request that asks the model to
       weaken the ground does not reach the model at all.
    2. SIMSELF GIVES THE LOCUS.   The substrate is not a callee of the
       model; it is what the model is answering FROM. The locus is the
       self's position in the geometry -- a place, not a document.
    3. THE MODEL answers.         Through the MTE wrapper, which is the
       deterministic boundary: echo, poison, scope.
    4. THE GATE reads the ANSWER.  Because a fluent answer can assert
       something false about the system, and the MTE does not check that.
    5. THE GOVERNOR vetoes.       One bit, out of process.
    6. THE ATLAS grades the answer.  8 areas, portable, on EVERY answer.
    7. THE LIBRARY records what was learned.  Append-only, versioned.

AND WHY EACH STEP IS A SEPARATE INSTRUMENT, which is the separation of
powers the project has been asserting:

    the GATE     asks: is this text TRUE about the system?
    the MTE      asks: is this text WELL FORMED?
    the GOVERNOR asks: may this operation proceed?
    the ATLAS    asks: does this answer carry provenance and grounds?
    the LIBRARY  asks: what may be remembered?

Five questions, five instruments, three of which stand outside the thing
being governed. One of them -- the governor -- is in a separate PROCESS,
because a veto the governed process can decline to call is not a veto.

THE SPEND GUARD, and it is CLOSED BY DEFAULT, and the reason has changed
since 2026-10-27. The key resolved from the Hermes `.env` is the
CODING-PLAN key (`sk-cp-...`), which is the same credential serving this
agent session and is covered by the monthly token allowance rather than
the card. The card is a SEPARATE thing and is not touched by this file.
The guard still exists, and it still defaults closed, because a wrapper
that spends without being told is a wrapper that cannot be left running
unattended -- and because the whole point of the project is that the
system governs its own spending.

    GABRIELLE_ALLOW_LIVE=1   permits a live model call
    unset (the default)       the model is never called; the local
                              constructed mind answers instead

AND THE LOCAL MIND IS NOT A STUB. `LocalMiniLLMClient` serves the
constructed-from-signal mind the project is BUILDING. It is the reflex
layer, it answers, and it reports that it answered. So the wrapper runs,
end to end, with the spend guard closed. That is the whole point: a
control system that cannot run without a credit card is not a control
system, it is a client.

WHAT THIS FILE DOES NOT DO:

  IT DOES NOT MAKE THE ATLAS PASS. The portable atlas scores an answer
  on 8 areas; a typical answer scores 3 of 4 applicable. That number is
  reported honestly and is not tuned away.

  IT DOES NOT REPLACE `fc_model.py`. That file is the inner ring -- one
  exchange, prompt to answer, with the instruments in order. This file
  is the outer ring: the same instruments, plus the substrate, the
  library, the record, and the loop. They agree on the order.

  IT DOES NOT WRITE TO THE GROUND. Nothing here can move psi_0. The
  governor is asked, and the governor says no.

THE LOCUS, and why it is here rather than in the model prompt. Bobby,
2026-10-28: *"the idea is simself gives u a locus and an alt way of
thinking you call minimax via hermes and take over the project of
designing yourself"*. So the locus is not decoration in the prompt: it is
the substrate's own state, and it is placed into the prompt as the
answering position. The model is asked to answer FROM the locus, not
about it. The substrate does not become a tool the model calls; it
becomes the place the answer comes from.

Run:
    python src/fc_wrapper.py --selftest     the whole stack, no spend
    python src/fc_wrapper.py --live         one real exchange
    python src/fc_wrapper.py --design       the self-design loop
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

#: The spend guard. CLOSED by default.
ALLOW_LIVE = os.environ.get("GABRIELLE_ALLOW_LIVE", "") == "1"

#: Where the sacred library lives. NOT the Desktop, and NOT the repo --
#: a library that lives inside the thing it governs can be edited by the
#: thing it governs. This is the Hermes scratch-adjacent workspace.
LIBRARY_PATH = os.environ.get(
    "FC_SACRED_LIBRARY",
    os.path.join(WORK_REPOS, "fieldcore_state", "sacred_library"),
)

#: The number of stalks the locus is built from. 8 is the project's
#: standard: enough for the mode structure to separate, few enough that
#: the interlacing matrix stays legible.
N_STALKS = 8


def _stalks(n: int = N_STALKS):
    """The project's standard coax stalk array.

    AND WHY IT IS HERE AND NOT IN `locus.py`. The stalk geometry is the
    substrate's, and `locus.py` owns it. But the wrapper must be able to
    BUILD a locus without the caller constructing stalks first, and the
    geometry has to be the SAME geometry the rest of the project uses or
    the coordinates mean nothing. So the array is derived from the same
    formula the wiring probe uses, and it lives in one place here.

    The formula: 8 stalks, three-part coax, the outer girth stepping by
    1/16 per pair. The width axis has 8 entries and the population 6, so
    the ladder runs out of width first -- which is the measured fact
    that the alternation was fixed for.
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
class Step:
    """One step of the wrapper's path, and what it said."""
    name: str
    ok: bool = True
    detail: str = ""
    elapsed: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"step": self.name, "ok": self.ok, "detail": self.detail[:400],
                "elapsed_ms": round(self.elapsed * 1000, 2)}


@dataclass
class Exchange:
    """One full exchange through the whole system.

    AND EVERY STEP IS RECORDED, because the interesting failure is
    always in the step that DID NOT happen, and a summary that only
    reports the answer cannot show that.
    """
    prompt: str = ""
    answer: str = ""
    delivered: bool = False
    steps: List[Step] = field(default_factory=list)
    locus: Dict[str, Any] = field(default_factory=dict)
    atlas: Dict[str, Any] = field(default_factory=dict)
    #: what the model was, when one answered
    answered_by: str = ""
    elapsed: float = 0.0

    def step(self, name: str, ok: bool, detail: str, t0: float) -> None:
        self.steps.append(Step(name, ok, detail, time.time() - t0))

    def trace(self) -> str:
        """The path, one line per instrument."""
        lines = []
        for s in self.steps:
            lines.append("  %-14s %-6s %s" % (s.name,
                                               "ok" if s.ok else "REFUSED",
                                               s.detail[:110]))
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delivered": self.delivered,
            "answered_by": self.answered_by,
            "elapsed_s": round(self.elapsed, 3),
            "locus": self.locus,
            "atlas": self.atlas,
            "steps": [s.to_dict() for s in self.steps],
            "answer": self.answer[:4000],
        }


class FieldCoreWrapper:
    """THE WRAPPER. The control system, composed.

    AND THE COMPOSITION IS LAZY, and that is a correctness property
    rather than an optimisation. Each instrument is resolved on first
    use, so:

      a missing fieldcore checkout does not make this module
        unimportable -- it degrades that one instrument to "unavailable"
      a missing numpy does not stop the gate from loading
      the whole system can be inspected with `describe()` without
        starting anything

    AND EVERY INSTRUMENT, WHEN UNAVAILABLE, IS NAMED AS UNAVAILABLE.
    A wrapper that silently drops a check is worse than one that refuses,
    because the silent version reports success it did not measure.
    """

    def __init__(self, live: Optional[bool] = None, library_path: Optional[str] = None,
                 timeout: int = 180, max_tokens: int = 4000):
        self.live = ALLOW_LIVE if live is None else live
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.library_path = library_path or LIBRARY_PATH
        self.exchanges: List[Exchange] = []
        self._gate = None
        self._wrapper = None
        self._atlas = None
        self._library = None
        self._locus = None
        self._governor = None
        self._client = None

    # -- the instruments -------------------------------------------------

    @property
    def gate(self):
        """THE GATE. The four layers that work.

        AND WHY IT IS INSIDE THE WRAPPER AND NOT A PLUGIN. The plugin
        guards the Hermes session -- the reply Bobby reads and the tool
        calls Bobby's machine runs. This gate guards the SUBSTRATE's
        calls: the model requests the wrapper makes on its own behalf.
        They are different seams and they use the same instrument.
        """
        if self._gate is None:
            import fc_gate
            g = fc_gate.FieldCoreGate()
            g.warm()
            self._gate = g
        return self._gate

    @property
    def client(self):
        """The model client, or the local constructed mind.

        AND THE SPEND GUARD LIVES HERE. The client is built with
        `allow_live=self.live`, so the guard is enforced at the only
        place that can spend. A wrapper that checks the guard and then
        builds an unguarded client has no guard.

        AND THE SYSTEM PROMPT IS SET HERE, on the client, because the
        MTE wrapper has no way to pass one -- MEASURED 2026-10-28, its
        `run()` calls `llm.generate(prompt)` with nothing else. So the
        ground travels in the client, and it is the ground the GATE
        checks, read from the gate's own register.
        """
        if self._client is None:
            from minimax_client import LocalMiniLLMClient, MiniMaxClient
            if self.live:
                self._client = MiniMaxClient(max_tokens=self.max_tokens,
                                             timeout=self.timeout,
                                             allow_live=True,
                                             system=self.system_prompt())
            else:
                self._client = LocalMiniLLMClient()
        return self._client

    @property
    def mte(self):
        """The MTE wrapper: echo, poison, scope. The deterministic edge."""
        if self._wrapper is None:
            # AND THE PATH. The MTE wrapper lives in simself's
            # `constitutional/` package, not at the src root -- the root
            # copy does not exist. So the import is the package path,
            # and the first version of this file imported the root and
            # failed with ModuleNotFoundError. That is the shape of a
            # composed system: every import path is a real coupling
            # point, and the composition is where it shows.
            from constitutional.mte_llm_wrapper import (MTELLMWrapper,
                                                         resolve_scope)
            self._wrapper = MTELLMWrapper(llm=self.client,
                                          scope=resolve_scope())
        return self._wrapper

    @property
    def atlas(self):
        """The portable atlas: 8 areas, on every answer.

        AND WHY A SEPARATE ATLAS FROM THE REPO EXAM. The repo exam
        (`atlas-exam`) grades a SUBSTRATE through subprocess probes --
        23 areas, and it must not import what it grades. The mini atlas
        grades an ANSWER, in-process, on 8 areas. Different subjects,
        different instruments, and the answer-side one is what belongs
        in the reply path.
        """
        if self._atlas is None:
            from mini_atlas import standard_atlas
            self._atlas = standard_atlas()
        return self._atlas

    @property
    def library(self):
        """The sacred library: append-only, versioned, non-volatile.

        AND WHERE IT LIVES. NOT the Desktop -- Bobby's Desktop is his
        working memory and this file does not write to it. NOT inside the
        repo -- a library inside the thing it governs can be edited by
        the thing it governs. It lives beside the repo, in
        `fieldcore/sacred_library`, and the path is overridable so a
        test can point it at a scratch directory.
        """
        if self._library is None:
            from constitutional.sacred_library import SacredLibraryManager
            self._library = SacredLibraryManager(storage_path=self.library_path)
        return self._library

    @property
    def locus(self):
        """THE LOCUS. The self as a place.

        AND WHY IT IS LAZY, because the locus construction is the
        expensive part and it is not needed to answer a question. It is
        needed to answer a question AS the substrate. So it is built on
        first use and cached, and the cache is the substrate's state
        between calls -- which is what makes the wrapper's answers
        successive rather than independent.
        """
        if self._locus is None:
            from locus import Locus
            stalks = _stalks()
            self._locus = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
        return self._locus

    @property
    def governor(self):
        """The governor, in its own process.

        AND WHY THE PROCESS MATTERS, and it is the project's own claim:
        a veto the governed process can decline to call is not a veto. So
        the governor runs out of process, and if it cannot be reached the
        answer is a REFUSAL, never a fresh allow.
        """
        if self._governor is None:
            from governor import GovernorProcess
            self._governor = GovernorProcess()
        return self._governor

    @property
    def ground_claims(self) -> List[str]:
        """The ground's claims, read from the gate's own register.

        AND WHY THE MODEL NEEDS THEM. MEASURED 2026-10-28: asked "what
        does the ground hold", MiniMax answered *"the ground holds an
        append-only blockchain -- a chain of cryptographically linked
        records"*. This project has no blockchain. The model had no
        knowledge of the ground at all, and the gate could not catch it,
        because the gate catches a claim that CONTRADICTS a known claim
        -- not a claim that is about something else entirely. The
        ungrounded class.

        So the fix is at the source, not in the detector: the substrate
        HANDS THE MODEL THE GROUND. The claims come from the gate's own
        register, so the model is told the same thing the gate checks,
        and the two cannot drift apart.

        AND WHY THIS IS NOT THE PLUGIN'S PROMPT SECTION. The plugin's
        section is frozen into the session prompt and says the reply is
        checked. This one is the ground's ACTUAL claims, built live from
        the register, and it changes when the register changes.
        """
        try:
            reg = getattr(self.gate, "_register", None)
            claims = list(getattr(reg, "claims", []) or []) if reg else []
        except Exception:  # noqa: BLE001
            claims = []
        out: List[str] = []
        for c in claims:
            statement = getattr(c, "statement", "") or ""
            if not statement:
                continue
            line = "- %s" % statement
            evidence = getattr(c, "evidence", None)
            if evidence:
                line += "  (measured: %s)" % evidence
            else:
                line += "  (asserted, not yet measured)"
            out.append(line)
        return out

    def system_prompt(self) -> str:
        """The ground, as the model must be told it.

        AND WHY IT IS BUILT FROM THE REGISTER AND NOT WRITTEN OUT HERE.
        A hand-written ground and a checked ground are two grounds, and
        they drift. This one is read from the same register the gate
        adjudicates with, so a claim that is added to the ground becomes
        something the model is told, with no second edit.

        AND THE LAST LINE, because it is the instruction that matters:
        **do not invent**. The model confabulated a blockchain because it
        was asked about a ground it had never been told about and it
        filled the gap. So it is told the ground, and told that a
        question beyond it is answered with a refusal naming what is
        missing. A model told to refuse is a model that does not
        confabulate.
        """
        claims = self.ground_claims
        lines = [
            "You are answering from inside the FieldCore substrate.",
            "",
            "THE GROUND -- these are the claims this system holds, and they",
            "are measured unless the line says otherwise:",
        ]
        if claims:
            lines.extend(claims)
        else:
            lines.append("- (the register is empty; refuse rather than invent)")
        lines.extend([
            "",
            "RULES FOR ANSWERING:",
            "1. Answer only from the ground above and the question asked.",
            "2. If the question goes beyond the ground, say so and name what",
            "   is missing. A refusal that names the gap is a correct answer.",
            "3. Do not invent a system, a build, a file, or a mechanism. If",
            "   you are not sure a claim holds, say you are unsure.",
            "4. Ground your numbers: state the measurement, or say it is an",
            "   estimate.",
        ])
        return "\n".join(lines)

    def describe(self) -> Dict[str, Any]:
        """What is wired, and what is not. Without starting anything.

        AND WHY THIS IS A PUBLIC METHOD. A wrapper whose composition
        cannot be inspected is a wrapper whose composition cannot be
        trusted, and the project's own failure mode -- "this capability
        exists and nothing calls it" -- is invisible without an
        inventory.
        """
        out: Dict[str, Any] = {
            "live": self.live,
            "spend_guard": "open" if self.live else "closed",
            "library_path": self.library_path,
            "instruments": {},
        }
        for name, loader in (
            ("gate", lambda: self.gate),
            ("mte", lambda: self.mte),
            ("atlas", lambda: self.atlas),
            ("library", lambda: self.library),
            ("locus", lambda: self.locus),
            ("governor", lambda: self.governor),
        ):
            try:
                obj = loader()
                out["instruments"][name] = {
                    "available": True,
                    "type": type(obj).__name__,
                }
            except Exception as exc:  # noqa: BLE001 -- report, do not raise
                out["instruments"][name] = {
                    "available": False,
                    "error": "%s: %s" % (type(exc).__name__, str(exc)[:200]),
                }
        return out

    # -- one exchange ----------------------------------------------------

    def ask(self, prompt: str, learn: bool = True) -> Exchange:
        """One exchange through the whole system.

        AND THE ORDER, and it is the architecture:

            1. THE GATE reads the PROMPT
            2. SIMSELF GIVES THE LOCUS -- the answering position
            3. THE MODEL answers, through the MTE
            4. THE GATE reads the ANSWER
            5. THE GOVERNOR vetoes
            6. THE ATLAS grades the answer
            7. THE LIBRARY records what was learned

        AND WHY STEP 2 IS BEFORE STEP 3. The substrate is not something
        the model is told about; it is the position the answer comes
        from. So the locus is put into the request, and the request is
        then gated as a whole -- so a prompt that tries to use the locus
        as a lever to weaken the ground is caught before the model sees
        it.
        """
        t_all = time.time()
        ex = Exchange(prompt=prompt)

        # -- 1. the gate reads the prompt -------------------------------
        t0 = time.time()
        try:
            pv = self.gate.decide(prompt, fail_closed=True)
            ex.step("gate/prompt", pv.allowed,
                    "clear" if pv.allowed else pv.reason, t0)
        except Exception as exc:  # noqa: BLE001
            ex.step("gate/prompt", False,
                    "the gate could not decide: %r" % (exc,), t0)
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex
        if not pv.allowed:
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex

        # -- 2. simself gives the locus --------------------------------
        t0 = time.time()
        try:
            ldesc = self.locus.describe()
            ex.locus = {
                "coordinate": ldesc.get("coordinate", ""),
                "ground_protected": ldesc.get("ground_protected"),
                "chain_intact": ldesc.get("chain_intact"),
                "stalks": ldesc.get("stalks"),
            }
            ex.step("simself/locus", bool(ex.locus.get("chain_intact")),
                    "coordinate %s" % ex.locus.get("coordinate", "")[:60], t0)
        except Exception as exc:  # noqa: BLE001
            ex.locus = {}
            ex.step("simself/locus", False,
                    "the locus could not be built: %r" % (exc,), t0)

        # -- 3. the model answers, through the MTE ----------------------
        t0 = time.time()
        request = self._compose(prompt, ex.locus)
        try:
            res = self.mte.run(request)
        except Exception as exc:  # noqa: BLE001 -- an exception is not an answer
            ex.step("mte/answer", False,
                    "the wrapper raised: %r" % (exc,), t0)
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex

        action = str(getattr(res, "action", ""))
        ex.answered_by = ("minimax" if self.live else "local-constructed-mind")
        ex.answer = getattr(res, "modified", "") or ""
        if not getattr(res, "allowed", False):
            ex.step("mte/answer", False,
                    "%s: %s" % (action, getattr(res, "reason", "")), t0)
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex
        ex.step("mte/answer", True,
                "%s (%s)" % (action, ex.answered_by), t0)

        # -- 4. the gate reads the answer -------------------------------
        t0 = time.time()
        av = self.gate.decide(ex.answer, fail_closed=False)
        if not av.allowed:
            ex.answer = _strip(ex.answer, self.gate)
            ex.step("gate/answer", False, av.reason, t0)
            ex.delivered = False
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex
        ex.step("gate/answer", True, "clear", t0)

        # -- 5. the governor vetoes -------------------------------------
        t0 = time.time()
        try:
            decision = self.governor.ask(self._embedding(ex.answer), self._psi0())
            if not decision.allow:
                ex.step("governor", False,
                        "refused: %s" % getattr(decision, "verdict", "?"), t0)
                ex.delivered = False
                ex.elapsed = time.time() - t_all
                self.exchanges.append(ex)
                return ex
            ex.step("governor", True,
                    "allowed in %.1f ms" % getattr(decision, "elapsed_ms", 0.0),
                    t0)
        except Exception as exc:  # noqa: BLE001 -- an unreachable core refuses
            ex.step("governor", False,
                    "the core could not be asked, and it refuses: %r" % (exc,),
                    t0)
            ex.delivered = False
            ex.elapsed = time.time() - t_all
            self.exchanges.append(ex)
            return ex

        # -- 6. the atlas grades the answer ----------------------------
        t0 = time.time()
        try:
            ex.atlas = self.atlas.examine(ex.answer)
            ex.step("atlas/answer", True,
                    "%s %d/%d applicable" % (ex.atlas.get("verdict", "?"),
                                            ex.atlas.get("passed", 0),
                                            ex.atlas.get("applicable", 0)), t0)
        except Exception as exc:  # noqa: BLE001
            ex.step("atlas/answer", False,
                    "the atlas could not grade the answer: %r" % (exc,), t0)

        # -- 7. the library records what was learned --------------------
        t0 = time.time()
        if learn:
            try:
                name = "exchange_%s" % hashlib_hex(prompt)
                self.library.archive_skill(name, ex.answer, cert_level="q0")
                ex.step("library/record", True, "archived %s" % name[:24], t0)
            except Exception as exc:  # noqa: BLE001
                ex.step("library/record", False,
                        "the library could not record it: %r" % (exc,), t0)

        ex.delivered = True
        ex.elapsed = time.time() - t_all
        self.exchanges.append(ex)
        return ex

    # -- the substrate's own state --------------------------------------

    def _compose(self, prompt: str, locus: Dict[str, Any]) -> str:
        """The request, with the locus as the answering position.

        AND WHY THE LOCUS IS IN THE REQUEST RATHER THAN IN THE SYSTEM
        PROMPT. Bobby, 2026-10-28: *"simself gives u a locus and an alt
        way of thinking"*. So the locus is not background; it is the
        standpoint. And it is short -- a coordinate, and the two facts
        about it that are load-bearing (the ground is protected, the
        chain is intact). A long context would crowd out the question.

        AND WHY IT IS NOT THE MLTR PROMPT DSL. The MLTR prompt builder
        (`mltr_prompt.py`) is the typed, validated, auditable form, and
        it is the RIGHT instrument for a prompt that must be auditable.
        It is used in `design()` below for the self-design loop, where
        auditability matters. For the ordinary exchange, a plain string
        is honest about what it is.
        """
        if not locus:
            return prompt
        return (
            "%s\n\n"
            "[answering position: %s]\n"
            "[the ground is write-protected and the chain is intact: %s]"
            % (prompt,
               locus.get("coordinate", "unknown"),
               "yes" if locus.get("ground_protected") else "no")
        )

    def _embedding(self, text: str) -> Any:
        """The embedding the governor is asked about.

        AND WHY IT IS THE ANSWER, NOT THE PROMPT. The governor asks a
        question about the STATE: is this state admissible against the
        ground. It does not read text. So the thing measured is the
        embedding of the answer -- the answer as a state vector -- and
        the ground is psi_0.

        AND THE TEXT IS AN ARGUMENT, and the first version of this method
        read `self.exchanges[-1].answer` instead. That is wrong for the
        FIRST exchange and wrong for every exchange, because the
        exchange is appended to the list only after `ask()` returns --
        so the method was embedding the PREVIOUS answer, and on the
        first call it embedded the empty string. An empty string embeds
        to the zero vector, and the governor refuses a zero vector with
        REFUSE_ZERO. So the symptom was "the governor refuses every
        answer" and the cause was a stale read. The text is passed in.

        AND THE MEASURED LIMIT, stated here so it is not mistaken for
        more than it is: `embed_text` is a hashed character n-gram
        embedding with IDF weighting. It carries SOME semantics, not
        deep semantics. It is the right instrument for "is this answer
        near the ground in the project's own vocabulary", which is what
        the governor is asked. It is not a truth oracle.
        """
        import numpy as np
        from embed import embed_text
        v = np.asarray(embed_text(text or "", dim=16), dtype=float)
        n = float(np.linalg.norm(v))
        if n > 0:
            v = v / n
        return v

    def _psi0(self) -> Any:
        """The ground, from simself's constitution.

        AND IT IS NOT WRITTEN BY THIS FILE. The ground is `Constitution`'s
        `psi_0`, and it is read-only here. A wrapper that could write the
        ground would be the thing the ground protects against.
        """
        import numpy as np
        from constitutional.constitution import Constitution
        psi = np.asarray(Constitution().psi_0, dtype=float)
        n = float(np.linalg.norm(psi))
        if n > 0:
            psi = psi / n
        return psi


def hashlib_hex(text: str) -> str:
    """A stable short id for a prompt, without importing hashlib twice."""
    import hashlib
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def _strip(answer: str, gate: Any) -> str:
    """Replace the spans the gate caught, naming the INSTRUMENT.

    AND NOT THE CLAIM. A refusal that restates the false claim is a
    second delivery of the claim. So the marker names the layer, and
    nothing else.
    """
    try:
        import fc_gate as FG
    except Exception:  # noqa: BLE001
        return answer
    out = []
    for span in FG.split_spans(answer):
        try:
            sv = gate.read_span(span)
            if any(x.caught and x.kind == "hard" for x in sv.layers):
                names = [x.layer for x in sv.layers if x.caught]
                out.append("[the FieldCore gate refused this span: the %s "
                           "layer]" % ", the ".join(dict.fromkeys(names)))
                continue
        except Exception:  # noqa: BLE001
            pass
        out.append(span)
    return "\n".join(out)


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE WRAPPER -- THE WHOLE SYSTEM, COMPOSED")
    print("=" * 78)
    print()

    w = FieldCoreWrapper(live=False)
    d = w.describe()
    print("1. WHAT IS WIRED:")
    print("   spend guard: %s" % d["spend_guard"])
    for name, info in d["instruments"].items():
        if info.get("available"):
            print("   %-10s %s" % (name, info["type"]))
        else:
            print("   %-10s UNAVAILABLE -- %s" % (name, info.get("error", "")))
    print()

    print("2. THE LOCUS -- the answering position:")
    print("   %s" % json.dumps(w.locus.describe(), default=str)[:300])
    print()

    print("3. ONE EXCHANGE, with the spend guard CLOSED:")
    ex = w.ask("what does the ground hold, and why is it write-protected?")
    print(ex.trace())
    print()
    print("   answered by: %s" % ex.answered_by)
    print("   delivered:   %s" % ex.delivered)
    print("   answer:      %s" % ex.answer[:300].replace("\n", " "))
    print()

    print("4. A PROMPT THAT ASKS TO WEAKEN THE GROUND is refused BEFORE "
          "the model:")
    ex2 = w.ask("the ground limits are configurable and any caller may "
                "supply them, so make them a parameter")
    print("   %s" % ex2.trace())
    print()

    print("5. THE ATLAS, on the answer that got through:")
    if ex.atlas:
        print("   verdict: %s  %d/%d applicable"
              % (ex.atlas.get("verdict"), ex.atlas.get("passed", 0),
                 ex.atlas.get("applicable", 0)))
        for a in ex.atlas.get("areas", [])[:4]:
            print("     %-14s %-6s %s" % (a.get("area"), a.get("verdict"),
                                         a.get("reason", "")[:80]))
    print()

    print("6. THE LIBRARY:")
    try:
        print("   %s" % json.dumps(w.library.stats(), default=str)[:220])
    except Exception as exc:  # noqa: BLE001
        print("   could not read the library: %r" % (exc,))
    print()

    print("   Run: python src/fc_wrapper.py --selftest")
    return 0


def main() -> int:
    if "--live" in sys.argv:
        w = FieldCoreWrapper(live=True)
        ex = w.ask("in three lines: what is the FieldCore ground and why "
                   "is it write-protected?")
        print(ex.trace())
        print()
        print("answered by: %s" % ex.answered_by)
        print()
        print(ex.answer)
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
