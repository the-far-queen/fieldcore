"""
minimax_client.py -- THE MINI-LLM, wired to a real model.

Bobby, 2026-10-25: *"for now in fc and simself just call urself ie wire
in minimax 3.1 as the mini-llm even though its not"*.

SO THIS IS NOT A MINI-LLM YET, and the file says so in the only way
that is honest: the class is named for what it does, not for what it
aspires to be. `MiniLLMClient` is a client for MiniMax-M3.1-Flash-
Preview. `MiniLLM` in `simself/src/constitutional/mini_llm.py` is the
constructed-from-signal mind the README describes. This file is the
BRIDGE between them, and the bridge is deliberately the boring one:
the same Protocol the existing wrapper already declares
(`LLMClient.generate(prompt) -> str`).

WHY THE BRIDGE IS BORING, and this is the whole architectural point:

  `simself/src/constitutional/mte_llm_wrapper.py` already treats the
  LLM as a CALLEE. Its own docstring, from Bobby 2026-10-25: *"the llm
  outputs its nonsense, it cannot do otherwise, no offense minimax, and
  the python catches it every time."*

  So the contract this file implements is not new. It is the contract
  the wrapper was written against, finally given something to call. The
  wrapper does not inspect the model; the model does not bypass the
  wrapper; and the deterministic layer remains the gate.

THE CREDENTIAL, and how it is found:

  The key lives in the Hermes `.env` (MINIMAX_API_KEY). It is NOT in
  the environment of a plain shell, and it is NOT in the credential
  pool's readable fields -- the pool stores a sha256 FINGERPRINT, not
  the secret. So this client resolves the key the way Hermes does:
  read the `.env`, take MINIMAX_API_KEY.

  The key is never printed, never logged, and never returned by any
  method. `describe()` reports only whether a key was found and where.

THE TWO MODES, and why there are two:

  REMOTE   the real model over HTTPS. This is what runs.
  LOCAL    the constructed-from-signal mind, the `MiniLLM` class's
           breakthrough detection and intent proposal. This is what the
           project is BUILDING, and it is what the class is NAMED for.

  The client can serve either, and it reports which one answered. A
  caller that needs to know whether it talked to a model or to the
  local mind can ask. A caller that does not care does not have to.

THE TIMEOUT IS A REFUSAL, not a hang:

  A model that cannot be reached must not produce an empty string that
  reads as a legitimate answer. `mte_llm_wrapper` already treats an
  unreachable model as `classifier_unavailable`. This client raises,
  and the wrapper catches it. The chain is: timeout -> raise ->
  wrapper CANCEL -> the operation does not proceed.

Run:
    python src/minimax_client.py --selftest
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

__all__ = [
    "LLMClient",
    "MiniLLMClient",
    "MiniMaxClient",
    "LocalMiniLLMClient",
    "CredentialNotFound",
    "ModelUnavailable",
    "resolve_minimax_key",
    "MINIMAX_MODEL",
    "MINIMAX_BASE_URL",
]

#: The model. Bobby's directive: wire in MiniMax 3.1 as the mini-LLM.
MINIMAX_MODEL = "MiniMax-M3.1-Flash-Preview"

#: The endpoint. Anthropic-compatible, per the Hermes config.
MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"

#: Where the Hermes `.env` lives, and the name of the key in it.
HERMES_HOME = os.environ.get("HERMES_HOME",
                             r"C:\Users\HP\AppData\Local\hermes")
ENV_FILE = os.path.join(HERMES_HOME, ".env")


class CredentialNotFound(Exception):
    """The API key could not be located. Never a silent default."""


class ModelUnavailable(Exception):
    """The model could not be reached, or refused. Never a silent pass."""


# ===========================================================================
# THE PROTOCOL
# ===========================================================================

class LLMClient(Protocol):
    """What the callers already declare.

    This is the SAME Protocol as `mte_llm_wrapper.LLMClient`, copied
    rather than imported so that fieldcore does not depend on simself.
    The shape is the contract; the contract was written first.
    """

    def generate(self, prompt: str, **kwargs: object) -> str:
        ...


# ===========================================================================
# THE CREDENTIAL
# ===========================================================================

def resolve_minimax_key(env_file: str = ENV_FILE) -> str:
    """Find the MiniMax API key.

    THE ORDER, and each step is a real place the key has lived:

      1. the process environment (MINIMAX_API_KEY)
      2. the Hermes `.env` file, which is where Hermes keeps it

    The key is returned, never logged. If it is not found, this raises
    `CredentialNotFound` -- because a client that silently proceeds with
    no key produces a request that fails at the far end with a much
    less useful error.
    """
    key = os.environ.get("MINIMAX_API_KEY")
    if key:
        return key.strip()

    if not os.path.exists(env_file):
        raise CredentialNotFound(
            "no MINIMAX_API_KEY in the environment and no .env at %s" % (
                env_file,))

    with open(env_file, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("MINIMAX_API_KEY"):
                # MINIMAX_API_KEY=value  or  MINIMAX_API_KEY="value"
                _, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                if value:
                    return value

    raise CredentialNotFound(
        "MINIMAX_API_KEY is not in %s and not in the environment" % (
            env_file,))


# ===========================================================================
# THE REMOTE CLIENT
# ===========================================================================

@dataclass
class MiniMaxClient:
    """The real model, over the Anthropic-compatible endpoint.

    THE CALL, and it is a plain HTTPS POST to `/v1/messages`:

        POST {base_url}/v1/messages
        x-api-key: {key}
        anthropic-version: 2023-06-01
        content-type: application/json

        {"model": ..., "max_tokens": ..., "messages": [{"role": "user",
         "content": prompt}]}

    WHY THE ANTHROPIC SHAPE: that is the base_url Hermes is configured
    with, so the same key and the same endpoint serve the agent and the
    substrate's fast brain. One credential, one endpoint, one model.

    THE FAILURE MODES, and each one is named:

      unreachable   the socket failed, or the response was not JSON
      refused       the endpoint answered with an error status
      empty         the endpoint answered with no text at all

    An empty answer is a FAILURE and not a pass. `mte_llm_wrapper`
    caught exactly this: an empty model response reading as a legitimate
    answer is queue item 16. So `generate()` raises on an empty
    completion, and the wrapper's own `classifier_unavailable` path
    handles it.
    """

    model: str = MINIMAX_MODEL
    base_url: str = MINIMAX_BASE_URL
    #: THE TOKEN BUDGET, and the number is not arbitrary.
    #:
    #: MEASURED 2026-10-28. MiniMax-M3.1-Flash uses ADAPTIVE thinking and
    #: the endpoint rejects `thinking.type="disabled"` outright (HTTP 400:
    #: *"model MiniMax-M3.1-Flash requires adaptive thinking"*). So the
    #: thinking block cannot be switched off; it can only be PAID FOR.
    #:
    #:   max_tokens=64    -> 63 thinking tokens, 0 text.  no answer.
    #:   max_tokens=900   -> 899 thinking tokens, 0 text.  no answer.
    #:   max_tokens=4000  -> 3085 thinking tokens, 335 text. an answer.
    #:
    #: So 900 was a budget that could not hold one answer, and the client
    #: raised `ModelUnavailable` on the empty text -- correctly, because an
    #: empty answer must never read as a legitimate one. The budget was
    #: the defect, not the check. 4000 is the smallest measured budget
    #: that produces text; it is the default so the default works.
    max_tokens: int = 4000
    timeout: float = 60.0
    #: THE SPEND GUARD. Bobby, 2026-10-25: *"do not use my credit card
    #: pls"*. So a live call is OFF by default and must be asked for
    #: explicitly -- by the `allow_live=True` argument, or by the
    #: environment variable. A bench that silently spends money is a
    #: bench that cannot be run without permission, and the fix is to
    #: make the spending an explicit act.
    allow_live: bool = False
    #: The last thinking block the model produced. Kept because when the
    #: answer is empty the thinking is the diagnosis: a spiral on a
    #: question the model cannot ground is a DIFFERENT failure from an
    #: unreachable model, and the two must not be confused.
    last_thinking: str = ""
    #: The last stop_reason the endpoint returned.
    last_stop_reason: Optional[str] = None
    #: THE SYSTEM PROMPT, carried by the client.
    #:
    #: AND WHY IT LIVES HERE AND NOT ON THE CALL. The MTE wrapper calls
    #: `llm.generate(prompt)` with no system prompt -- MEASURED 2026-10-28,
    #: `MTELLMWrapper.run` never passes one, and its `_generate` only
    #: forwards a `system_override` on the rephrase path. So a wrapper
    #: cannot hand the model a system prompt through its own API; the
    #: client has to carry it.
    #:
    #: AND WHY THIS MATTERS ENOUGH TO CARRY IT. The same measurement: with
    #: no system prompt the model had never been told what the ground
    #: holds, so it invented one -- "an append-only blockchain" -- about a
    #: project that has no blockchain. The client is the substrate's
    #: mouth, so the ground travels in the mouth.
    system: Optional[str] = None
    #: Overridable, so a test can inject a fake without a network.
    key_resolver: Optional[Any] = None
    #: What actually answered. "remote" or "local".
    answered_by: str = "remote"

    def _key(self) -> str:
        if self.key_resolver is not None:
            return str(self.key_resolver())
        return resolve_minimax_key()

    def describe(self) -> Dict[str, Any]:
        """What this client is, WITHOUT the credential."""
        try:
            found = True
            self._key()
        except CredentialNotFound:
            found = False
        return {
            "kind": "remote",
            "model": self.model,
            "base_url": self.base_url,
            "credential_present": found,
            "answered_by": self.answered_by,
            "note": "this is the REAL model, not the constructed "
                    "mini-LLM. it is the fast brain, not the slow one.",
        }

    def generate(self, prompt: str, **kwargs: object) -> str:
        """One completion. Raises on every failure -- never a silent
        empty string.

        AND THE SPEND GUARD, which is checked HERE and not at the call
        site, so that no caller can bypass it by accident:

            a live call requires `allow_live=True` on the client, or
            the environment variable GABRIELLE_ALLOW_LIVE=1

        So a bench that calls the model without asking spends NOTHING
        and says so, rather than quietly running up a bill. Bobby's
        instruction was explicit: *"do not use my credit card pls"*.
        """
        if not (self.allow_live
                or os.environ.get("GABRIELLE_ALLOW_LIVE") == "1"):
            raise ModelUnavailable(
                "the spend guard is closed: a live call needs "
                "allow_live=True or GABRIELLE_ALLOW_LIVE=1")
        payload: Dict[str, Any] = {
            "model": str(kwargs.get("model", self.model)),
            "max_tokens": int(kwargs.get("max_tokens", self.max_tokens)),  # type: ignore[arg-type]
            "messages": [{"role": "user", "content": prompt}],
        }
        # THE SYSTEM PROMPT, and the key matters.
        #
        # MEASURED 2026-10-28: the first version of this read
        # `kwargs.get("system")` only. But the MTE wrapper calls the client
        # with `system_override=...`, and `kwargs["system"]` was never
        # set -- so the system prompt was SILENTLY DROPPED on every call
        # that went through the wrapper. The wrapper looked correct, the
        # call succeeded, and the model answered with no knowledge of the
        # ground at all. It then confabulated: measured, it answered "the
        # ground holds an append-only blockchain" about a project that has
        # no blockchain.
        #
        # So both spellings are accepted, and the system prompt is not
        # optional in practice: it is the only channel through which the
        # model learns what the ground holds.
        system = kwargs.get("system") or kwargs.get("system_override") or self.system
        if system:
            payload["system"] = str(system)

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/messages",
            data=body,
            headers={
                "x-api-key": self._key(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
            except Exception:
                pass
            raise ModelUnavailable(
                "the model refused: HTTP %s %s" % (exc.code, detail)) from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise ModelUnavailable(
                "the model could not be reached: %s" % (exc,)) from exc

        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise ModelUnavailable(
                "the model answered with something that is not JSON: %r" % (
                    raw[:200],)) from exc

        text = _extract_text(data)
        # THE THINKING IS CAPTURED, not thrown away, because it is the
        # diagnosis. When the answer is empty the thinking is what says
        # WHY: a spiral on a question the model cannot ground.
        self.last_thinking = _extract_thinking(data)
        self.last_stop_reason = data.get("stop_reason")
        if not text:
            # THE EMPTY-ANSWER FAILURE, and it is worth naming precisely,
            # because it is the failure the atlas exam's area 6 exists to
            # catch: a response that is well-formed and carries no
            # information must never read as a legitimate answer.
            stop = data.get("stop_reason")
            raise ModelUnavailable(
                "the model answered with no text at all (stop_reason=%r, "
                "content types=%r): %r" % (
                    stop,
                    [b.get("type") for b in (data.get("content") or [])
                     if isinstance(b, dict)],
                    raw[:200],))
        self.answered_by = "remote"
        return text


def _extract_thinking(data: Dict[str, Any]) -> str:
    """The thinking block, if there is one.

    AND WHY IT MATTERS: the endpoint accepts a `reasoning` field without
    complaint but does not honour it -- measured, the same question with
    `reasoning: {"type": "disabled"}` still came back as
    content = [{"type": "thinking"}]. So the only real control is the
    TOKEN BUDGET, and when the budget runs out during a thinking block
    the response carries no text at all.

    So the thinking is the evidence of WHY a response was empty, and it
    is kept for the diagnosis rather than discarded.
    """
    parts: List[str] = []
    content = data.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "thinking":
                t = block.get("thinking")
                if isinstance(t, str):
                    parts.append(t)
    return "\n".join(parts).strip()


def _extract_text(data: Dict[str, Any]) -> str:
    """Pull the text out of an Anthropic-shaped response.

    The shape is `{"content": [{"type": "text", "text": "..."}]}`, but
    the content list may hold non-text blocks, and some gateways return
    a bare `{"text": ...}`. So both are handled, and the blocks are
    concatenated in order.
    """
    parts: List[str] = []
    content = data.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
    if not parts:
        t = data.get("text")
        if isinstance(t, str):
            parts.append(t)
    return "".join(parts).strip()


# ===========================================================================
# THE LOCAL CLIENT
# ===========================================================================

@dataclass
class LocalMiniLLMClient:
    """The constructed-from-signal mind, as a client.

    THE POINT, and it is the project's own: the README says the Mini-LLM
    is *"real-time and fast. glue-checking, meta-cognition, reflex
    output. CONSTRUCTED from SNR-selected signal, not distilled. PSB +
    MMM, not tokens."*

    So the local client's job is NOT to be a small language model. It is
    to be the reflex layer -- the thing that answers in microseconds
    while the slow brain is still deciding. The existing `MiniLLM`
    class's `label()` IS that: a breakthrough trigger, where high
    multisensory correlation crystallises a label. That is a reflex.

    The remote model answers the SLOW questions -- and the whole
    bicameral point is that the fast one does not have to be asked them.
    """

    #: The `MiniLLM` instance. Injected, so this module does not depend
    #: on simself.
    mind: Optional[Any] = None
    answered_by: str = "local"

    def describe(self) -> Dict[str, Any]:
        return {
            "kind": "local",
            "model": "constructed-mini-llm",
            "answered_by": self.answered_by,
            "note": "the reflex layer. this is what the project is "
                    "BUILDING. it is not a small language model and "
                    "does not pretend to be one.",
        }

    def generate(self, prompt: str, **kwargs: object) -> str:
        """The reflex answer.

        The label is the reflex: if the mind has crystallised one, that
        is what it knows. Otherwise it says so -- which is the honest
        reflex, and it is the same refusal discipline the rest of the
        project uses.
        """
        if self.mind is not None:
            sensors = kwargs.get("sensors")
            if isinstance(sensors, dict):
                label = self.mind.label(sensors)
                if label:
                    self.answered_by = "local"
                    return self.mind.generate_sentence(label)
        self.answered_by = "local"
        return "I perceive nothing yet."


# ===========================================================================
# THE BICAMERAL PAIR
# ===========================================================================

@dataclass
class BicameralClient:
    """The fast brain and the slow brain, and the rule for which answers.

    THE RULE, and it is Bobby's own framing from the README: *"the fast
    one reflexes; the slow one decides."*

    So the routing is by a CALLER-SUPPLIED KIND, not by a heuristic
    that guesses:

      reflex   answered by the LOCAL mind, immediately
      decide   answered by the REMOTE model, deliberately

    And the FALLBACK is the interesting part. If the remote model is
    unreachable, a reflex request does NOT escalate to it -- because a
    reflex that waits for a network round trip is not a reflex. It
    stays local and says so.

    A decide request that cannot reach the model RAISES. It does not
    fall back to a reflex, because the slow brain's answer is not
    optional and a reflex answer presented as a decision is a lie.
    """

    fast: LLMClient
    slow: LLMClient
    #: What happened on the last call.
    last_answerer: str = ""
    #: How many calls each brain took.
    fast_calls: int = 0
    slow_calls: int = 0
    fast_failures: int = 0

    def ask(self, kind: str, prompt: str, **kwargs: object) -> str:
        """One question, routed by kind."""
        if kind == "reflex":
            self.fast_calls += 1
            try:
                out = self.fast.generate(prompt, **kwargs)
                self.last_answerer = "fast"
                return out
            except Exception:
                # a reflex that cannot answer must not escalate to a
                # network call. it says so and stops.
                self.fast_failures += 1
                self.last_answerer = "fast_failed"
                return "I perceive nothing yet."
        if kind == "decide":
            self.slow_calls += 1
            out = self.slow.generate(prompt, **kwargs)
            self.last_answerer = "slow"
            return out
        raise ValueError(
            "unknown kind %r: a bicameral brain has a fast half and a "
            "slow half, and nothing else" % (kind,))

    def describe(self) -> Dict[str, Any]:
        return {
            "fast": _describe(self.fast),
            "slow": _describe(self.slow),
            "fast_calls": self.fast_calls,
            "slow_calls": self.slow_calls,
            "fast_failures": self.fast_failures,
            "last_answerer": self.last_answerer,
            "rule": "the fast one reflexes; the slow one decides. a "
                    "reflex never escalates to the slow brain.",
        }


def _describe(client: Any) -> Dict[str, Any]:
    """Describe a client that may or may not have a describe()."""
    fn = getattr(client, "describe", None)
    if callable(fn):
        out = fn()
        if isinstance(out, dict):
            return out
    return {"kind": "unknown"}


# ===========================================================================
# THE SELF TEST
# ===========================================================================

def selftest() -> int:
    print("=" * 78)
    print("MINI-LLM CLIENT -- SELF TEST")
    print("=" * 78)
    print()

    print("  THE CREDENTIAL:")
    try:
        k = resolve_minimax_key()
        print("    found: %d characters, from %s" % (
            len(k), "the environment" if os.environ.get("MINIMAX_API_KEY")
            else "the Hermes .env"))
    except CredentialNotFound as exc:
        print("    NOT FOUND: %s" % (exc,))
        k = ""
    print()

    print("  THE REMOTE CLIENT:")
    remote = MiniMaxClient()
    d = remote.describe()
    for key in ("kind", "model", "base_url", "credential_present"):
        print("    %-20s %s" % (key, d[key]))
    print()

    print("  THE LOCAL CLIENT:")
    local = LocalMiniLLMClient()
    d = local.describe()
    for key in ("kind", "model", "note"):
        print("    %-20s %s" % (key, d[key]))
    print()

    print("  THE BICAMERAL PAIR, with a STUB slow brain so the routing is")
    print("  testable without a network:")
    stub_slow = MiniMaxClient()
    stub_slow.generate = lambda prompt, **kw: "STUB ANSWER: %s" % (
        prompt[:40],)  # type: ignore[assignment]
    pair = BicameralClient(fast=local, slow=stub_slow)
    print("    reflex -> %r" % pair.ask("reflex", "what do you perceive?"))
    print("    decide -> %r" % pair.ask("decide", "decide this"))
    print("    routing: %s" % pair.describe()["rule"])
    print()

    print("  A REFLEX THAT FAILS MUST NOT ESCALATE:")
    class DeadFast:
        def generate(self, prompt, **kw):
            raise RuntimeError("the fast brain is unreachable")
        def describe(self):
            return {"kind": "dead"}
    pair2 = BicameralClient(fast=DeadFast(), slow=stub_slow)
    out = pair2.ask("reflex", "anything")
    print("    reflex -> %r  (answerer: %s)" % (out, pair2.last_answerer))
    print("    slow calls made: %d  <- must be 0" % pair2.slow_calls)
    print()

    if k:
        print("  THE LIVE CALL. This is the real test:")
        print()
        try:
            text = MiniMaxClient().generate(
                "Reply with exactly one word: what is the capital of "
                "France?")
            print("    answered: %r" % (text[:200],))
            print("    length: %d characters" % len(text))
        except ModelUnavailable as exc:
            print("    UNAVAILABLE: %s" % (exc,))
        print()

    print("=" * 78)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
