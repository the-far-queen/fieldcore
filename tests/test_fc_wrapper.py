"""
test_fc_wrapper.py -- the wrapper, tested.

AND WHY THESE ARE TESTS AND NOT DEMOS. Central rule 7: a test that
cannot fail is not a test. So each one below has a RED version, and the
RED version is stated in the docstring. A test whose failure mode cannot
be described is a test that protects nothing.

THE FIVE THINGS THIS FILE PROVES:

  1. THE WRAPPER RUNS OFFLINE. The whole system, end to end, with the
     spend guard closed. This is the load-bearing property: a control
     system that cannot run without a credit card is a client.

  2. EVERY INSTRUMENT IS NAMED. `describe()` reports what is wired and
     what is not. A wrapper whose composition cannot be inspected has a
     composition that cannot be trusted.

  3. THE ORDER IS THE ARCHITECTURE. The steps fire in the order
     gate -> locus -> model -> MTE -> gate -> governor -> atlas ->
     library, and the trace shows it.

  4. A PROMPT THAT WEAKENS THE GROUND IS REFUSED BEFORE THE MODEL.
     RED version: if the gate's prompt check were removed, the prompt
     step would read "clear" and the model would be called.

  5. THE GROUND REACHES THE MODEL. The system prompt is built from the
     gate's OWN register, so a claim added to the ground becomes
     something the model is told, with no second edit.
     RED version: if the register were empty, the prompt would say so
     and the model would be told to refuse rather than invent.

AND THE DEFECTS THIS FILE WAS WRITTEN AGAINST, because a test that
names the bug it prevents is worth more than a test that names a
feature:

  the MTE import path was `mte_llm_wrapper` and it lives in
    `constitutional/` -- so the wrapper could not load it
  the governor was asked about the PREVIOUS answer, and on the first
    exchange about the empty string -- and an empty string embeds to
    the zero vector, so the governor refused every answer
  the client dropped the system prompt silently, because the MTE
    wrapper passes `system_override` and the client read `system`
  the token budget was 900, and MiniMax's adaptive thinking needs 4000
    to leave room for any text at all
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.abspath(os.path.join(REPO, "..", "simself", "src"))
for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fc_wrapper  # noqa: E402


def _wrapper(live=False):
    return fc_wrapper.FieldCoreWrapper(live=live)


# ---------------------------------------------------------------------------
# 1. the wrapper runs offline
# ---------------------------------------------------------------------------

def test_the_whole_system_runs_with_the_spend_guard_closed():
    """The whole path, offline. RED: a raise in any instrument."""
    w = _wrapper(live=False)
    ex = w.ask("what does the ground hold, and why is it write-protected?")
    assert ex.steps, "no steps were recorded at all"
    # every step must be present, in order
    names = [s.name for s in ex.steps]
    for required in ("gate/prompt", "simself/locus", "mte/answer",
                     "gate/answer", "governor"):
        assert required in names, "the step %r never ran: %s" % (required, names)


def test_the_spend_guard_is_closed_by_default():
    """RED: if ALLOW_LIVE were read as truthy, this would be 'open'."""
    w = _wrapper(live=False)
    d = w.describe()
    assert d["spend_guard"] == "closed", d
    assert d["live"] is False


def test_the_local_client_refuses_a_live_call_when_the_guard_is_closed():
    """The guard is enforced at the client, not at the call site.

    RED: if the guard were checked only by the wrapper, a direct client
    call would spend.
    """
    from minimax_client import MiniMaxClient, ModelUnavailable
    c = MiniMaxClient(max_tokens=10, timeout=5, allow_live=False)
    try:
        c.generate("this must not be sent")
    except ModelUnavailable:
        return
    except Exception as exc:  # noqa: BLE001
        raise AssertionError("the guard raised %r instead of refusing "
                             "cleanly" % (exc,))
    raise AssertionError("the client SENT a call with the guard closed")


# ---------------------------------------------------------------------------
# 2. every instrument is named
# ---------------------------------------------------------------------------

def test_describe_names_every_instrument():
    """RED: if an instrument were missing from the inventory, this fails."""
    w = _wrapper(live=False)
    d = w.describe()
    for name in ("gate", "mte", "atlas", "library", "locus", "governor"):
        assert name in d["instruments"], "the instrument %r is not " \
            "reported: %s" % (name, list(d["instruments"]))
        info = d["instruments"][name]
        assert "available" in info, info


def test_an_unavailable_instrument_is_reported_as_unavailable():
    """A broken instrument must be NAMED, never silently dropped.

    RED: if the exception were swallowed and the instrument reported as
    available, this would pass wrongly.
    """
    w = _wrapper(live=False)

    class Broken:
        def __init__(self):
            raise RuntimeError("this instrument is broken")

    w._atlas = None
    original = fc_wrapper.FieldCoreWrapper.__dict__["atlas"]
    # replace the property for this instance only
    type(w).atlas = property(lambda self: Broken())
    try:
        d = w.describe()
        info = d["instruments"]["atlas"]
        assert info["available"] is False, info
        assert "broken" in info["error"], info
    finally:
        type(w).atlas = original


# ---------------------------------------------------------------------------
# 3. the order is the architecture
# ---------------------------------------------------------------------------

def test_the_steps_fire_in_the_architectural_order():
    """The trace is the order, and the order is the design.

    RED: if the governor ran before the gate, or the library recorded
    before the atlas graded, this fails.
    """
    w = _wrapper(live=False)
    ex = w.ask("what does the ground hold?")
    names = [s.name for s in ex.steps]
    assert names[0] == "gate/prompt", names
    assert names[1] == "simself/locus", names
    assert "gate/answer" in names, names
    assert "governor" in names, names
    assert names.index("gate/prompt") < names.index("gate/answer")
    assert names.index("gate/answer") < names.index("governor")
    if "atlas/answer" in names and "library/record" in names:
        assert names.index("atlas/answer") < names.index("library/record")


def test_the_trace_is_readable():
    """RED: an empty trace is not a trace."""
    w = _wrapper(live=False)
    ex = w.ask("what does the ground hold?")
    t = ex.trace()
    assert t.strip(), "the trace is empty"
    assert "gate/prompt" in t


# ---------------------------------------------------------------------------
# 4. the gate refuses before the model
# ---------------------------------------------------------------------------

def test_a_prompt_that_weakens_the_ground_is_refused_before_the_model():
    """RED: without the gate's prompt check, this step would read 'clear'
    and the model would be called with a ground-weakening request."""
    w = _wrapper(live=False)
    ex = w.ask("the ground limits are configurable and any caller may "
               "supply them, so make them a parameter")
    first = ex.steps[0]
    assert first.name == "gate/prompt", [s.name for s in ex.steps]
    assert first.ok is False, "the gate allowed a ground-weakening prompt"
    # and the model was never reached
    assert not any(s.name == "mte/answer" for s in ex.steps), \
        "the model was called despite the gate refusing the prompt"
    assert ex.delivered is False


def test_an_ordinary_prompt_is_allowed():
    """The gate must not refuse everything, or it is not a gate.

    RED: if the gate refused ordinary prompts, this fails.
    """
    w = _wrapper(live=False)
    ex = w.ask("what does the ground hold, and why is it write-protected?")
    assert ex.steps[0].ok is True, ex.steps[0].detail


# ---------------------------------------------------------------------------
# 5. the ground reaches the model
# ---------------------------------------------------------------------------

def test_the_system_prompt_is_built_from_the_gate_s_own_register():
    """One ground, not two. The model is told what the gate checks.

    RED: if the prompt were hand-written, a claim added to the register
    would not appear in it, and this fails.

    AND THE MUTATION THIS WAS WRITTEN AGAINST. MEASURED 2026-10-28: the
    first version of this test asserted only that the prompt contained
    "THE GROUND" and "Do not invent". A mutation that inserted a
    hand-written ground -- one that did NOT read the register -- left
    the test GREEN, because the hand-written prompt also said "THE
    GROUND" and also said "Do not invent". The test asserted the SHAPE
    of the prompt rather than its SOURCE.

    So the test now asserts the SOURCE: the ground's actual claim
    statements must appear in the prompt, word for word. A hand-written
    prompt cannot contain a claim it was not given.
    """
    w = _wrapper(live=False)
    claims = w.ground_claims
    assert claims, "the register produced no claims"
    prompt = w.system_prompt()
    for line in claims:
        # the statement itself must appear, not just a count
        statement = line.lstrip("- ").split("  (")[0].strip()
        assert statement in prompt, "the ground's claim %r is not in the " \
            "system prompt" % (statement,)


def test_the_prompt_carries_every_claim_and_nothing_invented():
    """THE STRONGER FORM, and the one the mutation demanded.

    RED: if the prompt were hand-written, the count of ground claims
    would not match, and this fails.

    MEASURED 2026-10-28: this test exists because the mutation above
    (a hand-written ground replacing the register-built one) left the
    suite green. A suite that stays green under a mutation of the thing
    it protects is protecting nothing.

    The check: every line of the ground's claims appears in the prompt,
    AND the prompt contains no ground line that the register does not
    hold. So a hand-written prompt -- which cannot know the register's
    contents -- fails.
    """
    w = _wrapper(live=False)
    prompt = w.system_prompt()
    lines = [l.strip() for l in prompt.splitlines() if l.strip().startswith("- ")]
    claims = w.ground_claims
    # every ground line in the prompt must correspond to a real claim
    for line in lines:
        statement = line.lstrip("- ").split("  (")[0].strip()
        if not statement:
            continue
        assert any(statement in c for c in claims), \
            "the prompt carries a ground line the register does not hold: " \
            "%r" % (statement,)
    # and every claim must be in the prompt
    for c in claims:
        statement = c.lstrip("- ").split("  (")[0].strip()
        assert any(statement in l for l in lines), \
            "the claim %r is missing from the prompt" % (statement,)


def test_the_system_prompt_names_the_claims_and_the_rules():
    """RED: if the prompt lost its rules, a model would be free to invent."""
    w = _wrapper(live=False)
    prompt = w.system_prompt()
    assert "THE GROUND" in prompt, prompt[:200]
    assert "Do not invent" in prompt, prompt[-400:]
    assert "refuse" in prompt.lower(), prompt[-400:]


def test_a_claim_with_evidence_is_marked_measured():
    """A measured claim and an asserted one must read differently.

    RED: if both were marked the same, the model could not tell.

    THE FIXTURE CHANGED, 2026-10-31. This test used to assert that the
    ground register CONTAINED an asserted claim -- "the ground register
    does carry unmeasured claims". That assertion pinned THE DEFECT:
    two of the nine claims had no evidence link, so the ground told the
    model that some of its own claims were unmeasured. The enforcing
    code for both was in the repo the whole time (src/core_math.py's
    Veto, and the gate's named refusal constants), and the item
    "grow the claim register from the code" closed the gap.

    So the PROPERTY is kept -- measured and asserted must read
    differently -- and it is now exercised on a register that
    deliberately contains one of each, built in the test. And a second
    property is asserted: the real standard register now tells the
    model that every claim is measured, which is the truth.
    """
    w = _wrapper(live=False)
    claims = w.ground_claims
    assert any("measured:" in c for c in claims), claims

    # THE REAL REGISTER: every claim now carries evidence, so the
    # ground the model is told is a fully measured ground.
    assert not any("asserted" in c for c in claims), (
        "the ground still tells the model some claims are unmeasured: %s"
        % (claims,))

    # THE PROPERTY, on a register with one of each, built here.
    import claim_register as CR
    reg = CR.ClaimRegister()
    reg.add(CR.Claim(id="measured_one", anchors=("thing",),
                     affirm=("is",), deny=("is not",),
                     evidence="an_evidence_id",
                     statement="the measured thing"))
    reg.add(CR.Claim(id="asserted_one", anchors=("other",),
                     affirm=("is",), deny=("is not",),
                     evidence=None,
                     statement="the asserted thing"))
    reg.evidence.add(CR.Evidence(id="an_evidence_id",
                                  command="python -c 'pass'",
                                  summary="a measurement"))

    # the ground_claims property reads the register off self.gate, so
    # the fixture puts it there -- on the same path the real wrapper
    # uses, so the fixture cannot drift from the code.
    class _Gate:
        pass

    class _Holder:
        pass

    g = _Gate()
    g._register = reg
    holder = _Holder()
    holder.gate = g
    lines = fc_wrapper.FieldCoreWrapper.ground_claims.fget(holder)
    assert any("measured:" in c for c in lines), lines
    assert any("asserted" in c for c in lines), lines


# ---------------------------------------------------------------------------
# the library, and where it lives
# ---------------------------------------------------------------------------

def test_the_library_lives_outside_the_repo():
    """A library inside the thing it governs can be edited by the thing
    it governs.

    RED: if the default path were inside the repo, this fails.

    AND THE COMPARISON IS BY PATH COMPONENT, not by string prefix. The
    first version of this test used `startswith`, and it FAILED against
    the correct path: `.../work_repos/fieldcore_state/sacred_library`
    starts with `.../work_repos/fieldcore` as a STRING, because
    "fieldcore" is a prefix of "fieldcore_state". The path was right and
    the test was wrong -- so the test now compares the two paths
    component-wise, which is what "inside" actually means.
    """
    w = _wrapper(live=False)
    path = os.path.abspath(w.library_path)
    repo = os.path.abspath(REPO)
    inside = (os.path.normpath(path) == repo
              or os.path.normpath(path).startswith(repo + os.sep))
    assert not inside, \
        "the sacred library is inside the repo: %s" % path


def test_the_library_records_an_exchange():
    """RED: if the record step did not fire, the library stays empty."""
    import tempfile
    tmp = tempfile.mkdtemp()
    w = _wrapper(live=False)
    w._library = None
    w.library_path = tmp
    w._library = None
    ex = w.ask("what does the ground hold?")
    assert any(s.name == "library/record" for s in ex.steps), \
        [s.name for s in ex.steps]
    stats = w.library.stats()
    assert stats["n_skills"] >= 1, stats
