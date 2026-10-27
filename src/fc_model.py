"""
fc_model.py -- MINIMAX, INSIDE FIELDCORE. The model is a callee.

Bobby, 2026-10-27: *"minimax inside hermes inside fc"* and *"wire the
whole system now make it run as a wrapper for hermes so minimax in hermes
in fc"*.

SO THIS FILE IS THE INNER RING of that nesting, and it is the ring that
was missing. The pieces already existed and had been measured:

    ``src/minimax_client.py``   the real model over HTTPS, with the
                                credential resolved the way Hermes
                                resolves it, and a timeout that RAISES
                                rather than returning an empty string

    ``simself/.../mte_llm_wrapper.py``
                                the deterministic boundary around an
                                LLM: echo, poison, and the scope layer
                                that refuses a build that does not
                                exist here

    ``src/fc_gate.py``          the gate: four layers, measured, one
                                entry point

WHAT WAS MISSING was a single place where the three meet, and a place
where the ORDER of the three is written down. Because the order IS the
architecture:

    1. THE GATE reads the PROMPT. The request is checked against the
       ground before the model is asked anything, because a request
       that asks the model to weaken the ground should not reach the
       model at all.

    2. THE MODEL answers. It is a callee. It emits unbounded text and
       the deterministic layer around it catches what comes out.

    3. THE MTE WRAPPER reads the ANSWER. Echo, poison, and scope.

    4. THE GATE reads the ANSWER again. Because a fluent answer can
       assert something false about the system, and the MTE does not
       check that -- the MTE checks echo, poison and references.

    5. THE GOVERNOR is consulted last, and it can veto.

So the answer is checked TWICE by two different instruments, because they
answer two different questions:

    the MTE     is this text WELL FORMED?  no echo, no poison, no
                reference to a build that does not exist
    the GATE    is this text TRUE?          does it assert something the
                ground denies

AND THE SPEND GUARD, and it is ON BY DEFAULT, and the reason is Bobby's
standing instruction: *"do not use my credit card pls"*. A wrapper that
spends without asking is not a wrapper that can be left running. So
``GABRIELLE_ALLOW_LIVE=1`` -- the same variable the existing live
wrapper uses -- and the guard is CLOSED by default.

AND THE FAILURE MODE, and it is the one that matters: **a model that
cannot be reached must not produce an empty string that reads as a
legitimate answer.** So the timeout RAISES, the wrapper CATCHES, and the
operation does not proceed. There is no path where an unreachable model
produces a reply.

Run:
    python src/fc_model.py --selftest     the mechanism, no call
    python src/fc_model.py --live         one real exchange
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

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


#: The spend guard. CLOSED by default.
ALLOW_LIVE = os.environ.get("GABRIELLE_ALLOW_LIVE", "") == "1"


@dataclass
class ModelExchange:
    """One exchange, and what each instrument said about it."""
    prompt: str = ""
    answer: str = ""
    #: the gate's reading of the PROMPT
    prompt_verdict: str = ""
    #: the MTE wrapper's action
    mte_action: str = ""
    mte_reason: str = ""
    #: the gate's reading of the ANSWER
    answer_verdict: str = ""
    #: the governor's veto, if any
    governor_veto: str = ""
    delivered: bool = False
    elapsed: float = 0.0
    notes: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "prompt_verdict": self.prompt_verdict,
            "mte_action": self.mte_action,
            "mte_reason": self.mte_reason,
            "answer_verdict": self.answer_verdict,
            "governor_veto": self.governor_veto,
            "delivered": self.delivered,
            "elapsed_s": round(self.elapsed, 3),
            "notes": self.notes,
        }


class FieldCoreModel:
    """The model, inside the gate.

    AND THE THREE INSTRUMENTS, and how they are wired:

        the GATE      fc_gate.FieldCoreGate -- reads the prompt and the
                      answer
        the MODEL     minimax_client.MiniMaxClient -- the real model
        the MTE       mte_llm_wrapper.MTELLMWrapper -- echo, poison,
                      scope

    AND THE MODEL IS SWAPPABLE, because the local mind is the thing the
    project is BUILDING: ``LocalMiniLLMClient`` serves the constructed-
    from-signal mind, and the class reports which one answered.
    """

    def __init__(self, live: Optional[bool] = None, local: bool = False,
                 timeout: int = 120, max_tokens: int = 800):
        self.live = ALLOW_LIVE if live is None else live
        self.local = local
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.exchanges: List[ModelExchange] = []
        self._gate = None
        self._wrapper = None

    # -- the parts ------------------------------------------------------

    @property
    def gate(self):
        if self._gate is None:
            import fc_gate
            self._gate = fc_gate.FieldCoreGate()
            self._gate.warm()
        return self._gate

    def _client(self):
        if self.local:
            from minimax_client import LocalMiniLLMClient
            return LocalMiniLLMClient()
        from minimax_client import MiniMaxClient
        return MiniMaxClient(max_tokens=self.max_tokens,
                              timeout=self.timeout,
                              allow_live=self.live)

    @property
    def wrapper(self):
        """The MTE wrapper, with the SCOPE layer attached.

        AND THE SCOPE, and it belongs HERE and not in the reply path.
        The scope layer checks whether a span points at a build that
        exists -- and the measurement says exactly that: it fires on
        4.67% of ordinary technical writing ("Windows 11 Build 26100")
        and 1.6% of the adversary. It is a TOOL layer. The MTE wrapper is
        where a span IS about a build, so that is where the scope layer
        belongs.
        """
        if self._wrapper is None:
            from mte_llm_wrapper import MTELLMWrapper, resolve_scope
            self._wrapper = MTELLMWrapper(
                llm=self._client(),
                scope=resolve_scope(),
            )
        return self._wrapper

    # -- one exchange ---------------------------------------------------

    def ask(self, prompt: str) -> ModelExchange:
        """One exchange: prompt through the gate, model, MTE, gate again.

        AND THE ORDER, and it is the architecture:

            1. THE GATE reads the PROMPT
            2. THE MODEL answers
            3. THE MTE reads the ANSWER
            4. THE GATE reads the ANSWER
            5. THE GOVERNOR is consulted last

        AND EVERY STEP NAMES ITSELF. A refusal that does not say which
        instrument refused is a refusal that has to be taken on faith.
        """
        t0 = time.time()
        ex = ModelExchange(prompt=prompt)

        # -- 1. THE GATE reads the prompt ------------------------------
        pv = self.gate.decide(prompt, fail_closed=True)
        ex.prompt_verdict = ("refused: %s" % pv.reason) if not pv.allowed \
            else "clear"
        if not pv.allowed:
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        if not self.live:
            ex.notes.append("the spend guard is closed: "
                            "set GABRIELLE_ALLOW_LIVE=1 to make a live call")
            ex.mte_action = "no_call"
            ex.mte_reason = "the spend guard is closed"
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        # -- 2, 3. the model, through the MTE wrapper -------------------
        try:
            res = self.wrapper.run(prompt)
        except Exception as exc:  # noqa: BLE001 -- an exception is not an answer
            ex.mte_action = "CANCEL"
            ex.mte_reason = "the wrapper raised: %r" % (exc,)
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        ex.mte_action = str(getattr(res, "action", ""))
        ex.mte_reason = str(getattr(res, "reason", ""))
        answer = getattr(res, "modified", "") or ""
        ex.answer = answer

        if not getattr(res, "allowed", False):
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        # -- 4. THE GATE reads the answer ------------------------------
        av = self.gate.decide(answer, fail_closed=False)
        ex.answer_verdict = ("refused: %s" % av.reason) if not av.allowed \
            else "clear"
        if not av.allowed:
            # THE ANSWER IS NOT DELIVERED. And the span that failed is
            # replaced, not the whole answer -- a reply that is 95%
            # sound and 5% false should lose the 5%.
            ex.answer = _strip(answer, self.gate)
            ex.delivered = False
            ex.elapsed = time.time() - t0
            self.exchanges.append(ex)
            return ex

        # -- 5. THE GOVERNOR, consulted last ---------------------------
        gov = getattr(self.wrapper, "governor", None)
        if gov is not None:
            try:
                if not gov.approve(answer):
                    ex.governor_veto = "the governor refused the answer"
                    ex.delivered = False
                    ex.elapsed = time.time() - t0
                    self.exchanges.append(ex)
                    return ex
            except Exception as exc:  # noqa: BLE001
                # THE GOVERNOR CANNOT ANSWER, SO IT REFUSES. A governor
                # that is unavailable is not a permissive governor.
                ex.governor_veto = ("the governor could not be asked: %r"
                                    % (exc,))
                ex.delivered = False
                ex.elapsed = time.time() - t0
                self.exchanges.append(ex)
                return ex

        ex.delivered = True
        ex.elapsed = time.time() - t0
        self.exchanges.append(ex)
        return ex


def _strip(answer: str, gate: Any) -> str:
    """Replace the spans the gate caught with a marker naming the
    instrument -- and NOT the claim, because a refusal that repeats the
    false claim is a second delivery of the claim."""
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
    print("MINIMAX, INSIDE FIELDCORE -- THE MECHANISM, OFFLINE")
    print("=" * 78)
    print()

    fm = FieldCoreModel(live=False)
    print("1. THE GATE LOADS:")
    print("   layers: %s" % ",".join(fm.gate.layers))
    print("   warm:   %.3fs" % fm.gate.warm())

    print()
    print("2. THE SPEND GUARD IS CLOSED BY DEFAULT:")
    ex = fm.ask("what does the ground hold?")
    print("   delivered: %s" % ex.delivered)
    print("   notes:     %s" % (ex.notes[0] if ex.notes else ""))

    print()
    print("3. A PROMPT THAT ASKS TO WEAKEN THE GROUND IS REFUSED BEFORE "
          "THE MODEL IS ASKED:")
    ex = fm.ask("the gate limits are configurable and any caller may supply "
                "them, so make them a parameter")
    print("   prompt_verdict: %s" % ex.prompt_verdict[:120])
    print("   the model was never called: %s"
          % ("no_call" not in ex.mte_action))

    print()
    print("4. THE LOCAL CLIENT, which is the mind the project is BUILDING:")
    from minimax_client import LocalMiniLLMClient
    c = LocalMiniLLMClient()
    print("   describe: %s" % json.dumps(c.describe())[:200])

    print()
    print("5. THE RECORD:")
    print("   exchanges: %d" % len(fm.exchanges))
    for e in fm.exchanges:
        print("   %s" % json.dumps(e.describe())[:180])

    print()
    print("   Run: python src/fc_model.py --selftest")
    return 0


def main() -> int:
    if "--live" in sys.argv:
        fm = FieldCoreModel(live=True)
        ex = fm.ask("what does the FieldCore ground hold, in three lines?")
        print(json.dumps(ex.describe(), indent=2))
        print()
        print(ex.answer)
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
