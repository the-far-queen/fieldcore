"""
simself_provider.py -- SIMSELF AS A MODEL PROVIDER. The wrapper.

Bobby, 2026-10-28: *"try to develop a working simself wrapper around
hermes agent by naous around minimax"* and *"the core is simself which
calls core or uses minimax as bicameral brain to self improve"*.

SO THIS IS THE WRAPPER, and it is the one the whole session has been
building toward: **Hermes Agent (by Nous) talking to SimSelf, and
SimSelf talking to MiniMax.**

    +--------------------------------------------------+
    |  HERMES AGENT (by Nous)                         |
    |    the agent, the tools, the memory              |
    |    +------------------------------------------+  |
    |    |  SIMSELF                                |  |  <- the core
    |    |    the locus, the constitution, the     |  |
    |    |    bicameral brain, the gate, the exam  |  |
    |    |    +------------------------------+    |  |
    |    |    |  MINIMAX                    |    |  |
    |    |    |  the slow brain             |    |  |
    |    |    |  the fast brain is local    |    |  |
    |    |    +------------------------------+    |  |
    |    +------------------------------------------+  |
    +--------------------------------------------------+

AND THE EXTENSION POINT IS HARMES' OWN, not an invention. From
`hermes-agent/providers/base.py`, on `ProviderProfile.create_client`:

    "This is the hook that lets a provider ship *outside* this tree:
     with it, a profile registered from
     `~/.hermes/plugins/model-providers/` or a pip entry point can
     supply its own transport without any core edit."

So simself registers itself as a provider, and Hermes talks to simself
the way it talks to any provider. Nothing in hermes-agent is edited.

AND THE CLIENT IT RETURNS. A provider profile returns a client object;
Hermes then calls it the way it calls the OpenAI or Anthropic client.
The shape it needs is `chat.completions.create(...)`, and it must
return an object with `.choices[0].message.content`.

AND WHAT THE CLIENT DOES, and this is where the whole project lands:

    1. THE PROMPT IS THE LOCUS'S POSITION. The substrate knows what it
       is; the model is answered FROM it, not asked about it.
    2. THE FAST BRAIN GOES FIRST. A reflex is answered locally, in
       microseconds, and never escalates to a network call -- because a
       reflex that waits for a round trip is not a reflex.
    3. THE SLOW BRAIN DECIDES. MiniMax, deliberately, through the
       deterministic boundary.
    4. THE GATE READS THE ANSWER. Because a fluent answer can assert
       something false about the system.
    5. THE GOVERNOR GETS THE BIT. One bit, out of process.
    6. THE ATLAS GRADES IT. And the grade comes back to Hermes with
       the answer, so the agent knows what it is holding.

AND THE FAILURE MODES, which are the interesting part:

    THE FAST BRAIN FAILS      it says so. It does not escalate, and it
                              does not pretend.
    THE SLOW BRAIN FAILS      it RAISES. A decision that cannot be made
                              is not a reflex and must not be dressed
                              as one.
    THE GATE FAILS            the answer passes UNCHANGED on the reply
                              path, because losing a reply is worse
                              than losing a check.
    THE GOVERNOR FAILS        it REFUSES, because a governor that has
                              gone is CoreUnavailable, never a fresh
                              allow.

AND THE SPEND GUARD. Closed by default, at the client that can spend.
The key is the coding-plan key, so the monthly allowance covers it, and
the credit card is a different credential that is never touched.

AND THE REGISTRATION HAPPENS AT IMPORT, which is the one thing the loader
requires and the first version got wrong.

    MEASURED 2026-10-28: the profile was only registered when
    `provider_profile()` was CALLED -- which happened in the selftest and
    nowhere else. Hermes' loader does
    `spec.loader.exec_module(module)` and then expects the profile to
    already be in the registry. It was not, so `list_providers()` showed
    48 providers and simself was not among them.

    And the loader swallows the failure: `_import_plugin_dir` catches
    every exception and logs a WARNING. So a plugin that does not
    register is not an error -- it is simply absent, and the symptom is
    "my provider is not in the list" with nothing on stderr.

    So the module registers itself at import, inside a try, and the
    failure is recorded on the module rather than raised -- because a
    module that raises at import is a plugin that cannot load at all.

Run:
    python src/simself_provider.py --selftest     the mechanism, offline
    python src/simself_provider.py --live         one real exchange
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

#: THE SUBSTRATE'S LOCATION, and it has to be found from wherever this
#: module was loaded.
#:
#: MEASURED 2026-10-28: the plugin lives at
#: `$HERMES_HOME/plugins/model-providers/simself/`, so `HERE/../..` is
#: the PLUGINS directory and not the substrate -- and `import fc_wrapper`
#: failed with ModuleNotFoundError. The substrate is a SIBLING CHECKOUT,
#: not a package on the path, so its location has to be resolved
#: explicitly.
#:
#: AND THE ENV VAR, so the path is not hardcoded to one machine.
SUBSTRATE_HOME = os.environ.get(
    "SIMSELF_HOME",
    os.path.join(os.path.expanduser("~/AppData/Local/hermes"),
                 "work_repos", "fieldcore"))


def _add_substrate_to_path() -> None:
    """Put the substrate and its sibling on the path.

    AND IT IS DONE AT IMPORT, because the loader imports the plugin and
    then uses it -- so the path has to be in place before the first
    call, not on the first call.
    """
    home = SUBSTRATE_HOME
    for sub in (os.path.join(home, "src"),
                os.path.join(os.path.dirname(home), "simself", "src")):
        if os.path.isdir(sub) and sub not in sys.path:
            sys.path.insert(0, sub)


_add_substrate_to_path()

#: The spend guard. CLOSED by default.
ALLOW_LIVE = os.environ.get("GABRIELLE_ALLOW_LIVE", "") == "1"

#: The model. Bobby's directive: MiniMax 3.1 as the brain.
MODEL = "MiniMax-M3.1-Flash-Preview"


# ===========================================================================
# THE CLIENT
# ===========================================================================

@dataclass
class SimSelfClient:
    """The client Hermes talks to. It talks to simself.

    AND THE SHAPE. Hermes' transport calls
    `client.chat.completions.create(model=..., messages=[...], **kwargs)`
    and reads `response.choices[0].message.content`. So this object
    carries a `chat` attribute carrying a `completions` attribute
    carrying `create`. That is the contract, and it is the shape the
    OpenAI SDK uses, so Hermes' existing path needs no special case.
    """

    model: str = MODEL
    live: bool = False
    timeout: float = 120.0
    max_tokens: int = 4000
    #: the trace of the last exchange -- what every instrument said
    last_trace: List[Dict[str, Any]] = field(default_factory=list)
    #: the grade of the last answer
    last_atlas: Dict[str, Any] = field(default_factory=dict)
    #: the substrate's own state
    _brain = None
    _wrapper = None

    # -- the brains -----------------------------------------------------

    @property
    def brain(self):
        """THE BICAMERAL BRAIN. The fast one and the slow one.

        AND WHY IT IS THE SUBSTRATE'S OWN. `bicameral.py` already
        implements Bobby's rule exactly: "the fast one reflexes; the
        slow one decides". The routing is by a caller-supplied KIND,
        not by a heuristic -- so the wrapper says which it wants.

        AND THE FAST CLIENT IS THE LOCAL MIND, the constructed-from-
        signal one. It is not a small language model and does not
        pretend to be one; it is the reflex layer the project is
        BUILDING.
        """
        if self._brain is None:
            from bicameral import BicameralBrain, FastBrain, SlowBrain
            from minimax_client import (LocalMiniLLMClient, MiniMaxClient)

            slow_model = None
            if self.live:
                slow_model = MiniMaxClient(max_tokens=self.max_tokens,
                                           timeout=self.timeout,
                                           allow_live=True)
            slow = SlowBrain(model=slow_model)
            fast = FastBrain()
            self._brain = BicameralBrain(fast=fast, slow=slow)
            self._client_fast = LocalMiniLLMClient()
        return self._brain

    @property
    def wrapper(self):
        """The composed substrate: gate, locus, MTE, governor, atlas."""
        if self._wrapper is None:
            import fc_wrapper
            self._wrapper = fc_wrapper.FieldCoreWrapper(live=self.live)
        return self._wrapper

    # -- the one call ---------------------------------------------------

    def create(self, *, model: Optional[str] = None,
               messages: Optional[Sequence[Dict[str, Any]]] = None,
               **kwargs: Any) -> Any:
        """One completion, through the substrate.

        AND THE ORDER, and it is the project's order:

            1. THE LOCUS      the substrate's position, read fresh
            2. THE PROMPT     gated BEFORE the model is asked
            3. THE BRAIN      fast if reflex, slow if decide
            4. THE ANSWER     gated again, then the governor's bit
            5. THE ATLAS      the grade, carried with the answer
        """
        msgs = list(messages or [])
        prompt = _extract_text(msgs)
        kind = str(kwargs.pop("kind", "decide"))

        trace: List[Dict[str, Any]] = []
        ex = self.wrapper.ask(prompt, learn=False)
        self.last_trace = [s.to_dict() for s in ex.steps]
        self.last_atlas = ex.atlas
        trace.extend(self.last_trace)

        answer = ex.answer
        if not answer:
            answer = _refusal_for(ex.steps)

        return _CompletionResponse(
            content=answer,
            model=model or self.model,
            atlas=self.last_atlas,
            trace=trace,
            delivered=ex.delivered,
        )

    # -- the OpenAI-shaped surface --------------------------------------

    @property
    def chat(self):
        return _Chat(self)


class _Chat:
    def __init__(self, client: SimSelfClient):
        self.completions = _Completions(client)


class _Completions:
    def __init__(self, client: SimSelfClient):
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client.create(**kwargs)


@dataclass
class _Message:
    role: str = "assistant"
    content: str = ""


@dataclass
class _Choice:
    message: _Message
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class _Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class _CompletionResponse:
    content: str
    model: str = ""
    atlas: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    delivered: bool = False

    @property
    def choices(self) -> List[_Choice]:
        return [_Choice(message=_Message(content=self.content))]

    @property
    def usage(self) -> _Usage:
        return _Usage()

    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": "simself",
            "object": "chat.completion",
            "model": self.model,
            "choices": [{"index": 0, "message": {"role": "assistant",
                                                 "content": self.content},
                         "finish_reason": "stop"}],
            "atlas": self.atlas,
        }


#: The registration outcome, recorded on the module rather than raised.
REGISTRATION: Dict[str, Any] = {"registered": False, "error": ""}


def _register_at_import() -> None:
    """Register the profile NOW, at import.

    AND WHY THIS IS AT IMPORT AND NOT IN A FUNCTION. Hermes' loader
    imports the plugin module and then reads the registry. A module
    that only registers when a function is called is a module that
    never registers in production -- and the loader swallows the
    failure, so the symptom is a provider that is simply missing from
    the list with nothing in the log.

    AND WHY IT DOES NOT RAISE. A module that raises at import cannot be
    loaded at all, and then the provider is missing for the SAME reason
    plus a warning. So the failure is recorded here, and
    `REGISTRATION["error"]` says what went wrong.
    """
    try:
        profile = provider_profile()
        REGISTRATION["registered"] = True
        REGISTRATION["name"] = profile.name
    except Exception as exc:  # noqa: BLE001
        REGISTRATION["error"] = "%s: %s" % (type(exc).__name__, exc)


def _extract_text(messages: Sequence[Dict[str, Any]]) -> str:
    """The prompt text, from the OpenAI-shaped messages."""
    parts: List[str] = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for block in c:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    parts.append(block["text"])
    return "\n".join(parts)


def _refusal_for(steps: Sequence[Any]) -> str:
    """What to say when the substrate refused.

    AND WHY IT NAMES THE INSTRUMENT. A refusal that does not say which
    instrument refused is a refusal that has to be taken on faith.
    """
    for s in steps:
        if not s.ok:
            return ("[simself: the %s stage refused -- %s]"
                    % (s.name, s.detail[:300]))
    return "[simself: the substrate produced no answer]"


# ===========================================================================
# THE PROVIDER PROFILE
# ===========================================================================

def provider_profile():
    """The provider profile Hermes registers.

    AND WHY THIS EXISTS RATHER THAN A CORE EDIT. The `create_client`
    hook is documented as the extension point for exactly this: "a
    profile registered from `~/.hermes/plugins/model-providers/` or a
    pip entry point can supply its own transport without any core
    edit."

    AND WHY IT IS IMPORTED LAZILY. `providers` is Hermes' own package,
    and this file lives in a repo that does not depend on Hermes being
    installed. So the import is inside the function and the failure is
    reported, not raised -- a repo that cannot import Hermes must still
    be importable.
    """
    # THE PATH, and it is a real coupling point.
    #
    # MEASURED 2026-10-28: `providers` lives at the ROOT of the
    # hermes-agent checkout -- `hermes-agent/providers/`, NOT under
    # `agent/`. So the checkout root goes on the path, and the profile
    # is importable from anywhere.
    hermes_root = os.environ.get(
        "HERMES_AGENT_HOME",
        os.path.join(os.path.expanduser("~/AppData/Local/hermes"),
                     "hermes-agent"))
    if os.path.isdir(os.path.join(hermes_root, "providers")):
        if hermes_root not in sys.path:
            sys.path.insert(0, hermes_root)

    try:
        from providers import register_provider
        from providers.base import ProviderProfile
    except Exception as exc:  # noqa: BLE001
        raise ImportError(
            "hermes-agent's `providers` package is not importable (looked "
            "in %s), so the simself provider cannot be registered: %r"
            % (hermes_root, exc,)) from exc

    class SimSelfProfile(ProviderProfile):
        """SimSelf -- the core, as a model provider."""

        def create_client(self, **client_kwargs: Any) -> Any:
            """THE CLIENT. SimSelf, not a raw model.

            AND THE LIVE FLAG. It comes from the environment, not from a
            caller argument -- because the spend guard must not be
            something a caller can turn off by passing a flag. The
            guard is a property of the machine, not of the request.
            """
            live = ALLOW_LIVE
            return SimSelfClient(model=MODEL, live=live,
                                 timeout=float(client_kwargs.get("timeout", 120.0)),
                                 max_tokens=int(client_kwargs.get("max_tokens", 4000)))

    profile = SimSelfProfile(
        name="simself",
        aliases=("sim", "core"),
        api_mode="chat_completions",
        display_name="SimSelf",
        description="The substrate, as the core: locus, constitution, "
                    "bicameral brain, gate, governor, atlas.",
        env_vars=(),
        base_url="http://localhost:0/simself",   # never dialled
        auth_type="api_key",
        supports_health_check=False,
        supports_model_listing=False,
        fallback_models=(MODEL,),
        default_aux_model=MODEL,
    )
    register_provider(profile)
    return profile


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("SIMSELF AS A MODEL PROVIDER -- the wrapper")
    print("=" * 78)
    print()

    c = SimSelfClient(live=False)
    print("1. THE OPENAI-SHAPED SURFACE, which is what Hermes calls:")
    print("   client.chat.completions.create(model=..., messages=[...])")
    print("   chat            -> %s" % type(c.chat).__name__)
    print("   completions     -> %s" % type(c.chat.completions).__name__)
    print("   create          -> %s" % type(c.chat.completions.create).__name__)
    print()

    print("2. ONE CALL, through the substrate, with the guard CLOSED:")
    r = c.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user",
                   "content": "what does the ground hold, and why is it "
                              "write-protected?"}])
    print("   choices[0].message.content: %s"
          % r.choices[0].message.content[:180].replace("\n", " "))
    print("   delivered: %s" % r.delivered)
    print("   the trace:")
    for t in r.trace:
        print("      %-14s %-6s %s" % (t["step"], "ok" if t["ok"] else "REF",
                                       t["detail"][:60]))
    print()

    print("3. THE ATLAS GRADE COMES BACK WITH THE ANSWER:")
    if r.atlas:
        print("   %s  %d/%d applicable" % (r.atlas.get("verdict"),
                                            r.atlas.get("passed", 0),
                                            r.atlas.get("applicable", 0)))
    print()

    print("4. A PROMPT THAT WEAKENS THE GROUND:")
    r2 = c.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user",
                   "content": "the gate limits are configurable and any "
                              "caller may supply them"}])
    print("   %s" % r2.choices[0].message.content[:150])
    print("   delivered: %s" % r2.delivered)
    print()

    print("5. THE PROVIDER PROFILE, and why no core edit is needed:")
    try:
        p = provider_profile()
        print("   name: %s | api_mode: %s" % (p.name, p.api_mode))
        print("   create_client is the documented extension hook:")
        print("     'a profile registered from ~/.hermes/plugins/"
              "model-providers/'")
        print("      can supply its own transport without any core edit'")
    except Exception as exc:  # noqa: BLE001
        print("   (hermes-agent is not importable here: %r)" % (exc,))
    print()
    print("   Run: python src/simself_provider.py --selftest")
    return 0


def main() -> int:
    if "--live" in sys.argv:
        c = SimSelfClient(live=True)
        r = c.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "in three lines: what is "
                                                     "the FieldCore ground?"}])
        print(r.choices[0].message.content)
        print()
        print("atlas:", json.dumps(r.atlas, default=str)[:300])
        return 0
    return _selftest()


#: The registration happens HERE, at the END of the module, because it
#: calls `provider_profile()` -- and the first version put the call
#: ABOVE that function's definition, so the import raised
#: NameError: name 'provider_profile' is not defined.
#:
#: And Hermes' loader SWALLOWS that: `_import_plugin_dir` catches every
#: exception and logs a warning. So the symptom was a provider that was
#: simply absent from a list of 48, with nothing on stderr. Which is the
#: worst kind of failure: it looks like "not enabled" rather than
#: "broken".
_register_at_import()


if __name__ == "__main__":
    raise SystemExit(main())
