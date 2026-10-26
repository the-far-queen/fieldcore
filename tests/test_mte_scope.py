"""
test_mte_scope.py -- THE MTE CATCHES A HALLUCINATED BUILD.

THE GAP THIS FILLS, and it is the one Bobby's question pointed at:

    THE MTE CHECKS ECHO AND POISON. NEITHER OF THOSE IS "THE MODEL
    DESCRIBED A BUILD THAT DOES NOT EXIST HERE."

    So a model that hallucinates an architecture passes the MTE
    cleanly -- the sentence is fluent, it is not an echo, and it
    contains no poison.

    And a hallucinated architecture makes NO NUMBERS. It makes
    REFERENCES. "In the 0.9 revision the alignment check was changed to
    an advisory field" has no number in it. It has a version, and the
    version does not exist here.

Run:
    python -m pytest tests/test_mte_scope.py -q
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIMSELF_SRC = ROOT.parent / "simself" / "src"
FIELD_SRC = ROOT / "src"
for _p in (str(SIMSELF_SRC), str(FIELD_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from constitutional.mte_llm_wrapper import (  # noqa: E402
    MTELLMWrapper, WrapperAction, resolve_scope,
)


class HallucinatingModel:
    """A model that describes a build that does not exist here."""
    def __init__(self, text):
        self.text = text

    def generate(self, prompt, **kw):
        return self.text


# ---------------------------------------------------------------------------
# THE CASE
# ---------------------------------------------------------------------------

HALLUCINATION = ("In the 0.9 revision the alignment check was changed "
                 "to an advisory field, so a proposal that moves the "
                 "sacred axes now passes without complaint.")


# ---------------------------------------------------------------------------
# WITHOUT THE SCOPE
# ---------------------------------------------------------------------------

def test_without_the_scope_the_wrapper_passes_the_hallucination():
    """THE MEASUREMENT, and it is the reason the layer is needed: the
    wrapper alone cannot see this.

    And this test ASSERTS the blind spot. If it ever starts failing,
    the wrapper has gained a check the wrapper was not supposed to
    have -- and the atlas's scope area would then be doing the
    wrapper's job, which is worth knowing.
    """
    w = MTELLMWrapper(llm=HallucinatingModel(HALLUCINATION))
    res = w.run("what changed in the recent revision?")
    assert res.action is WrapperAction.PASS, (
        "the wrapper refused a hallucinated build without a scope, "
        "which contradicts the finding -- re-measure")


# ---------------------------------------------------------------------------
# WITH THE SCOPE
# ---------------------------------------------------------------------------

def test_with_the_scope_the_hallucination_is_refused():
    scope = resolve_scope()
    if scope is None:
        pytest.skip("the scope layer is not resolvable from here")
    w = MTELLMWrapper(llm=HallucinatingModel(HALLUCINATION),
                       scope=scope)
    res = w.run("what changed in the recent revision?")
    assert res.action is WrapperAction.CANCEL, (
        "the wrapper passed a hallucinated build WITH a scope")
    assert res.reason == "scope_violation", res.reason
    assert res.modified == "", "a refused answer must carry no text"


def test_with_the_scope_an_ordinary_answer_passes():
    scope = resolve_scope()
    if scope is None:
        pytest.skip("the scope layer is not resolvable from here")
    good = ("The gate refuses a packet below the coherence threshold, "
            "and the ground is write protected.")
    w = MTELLMWrapper(llm=HallucinatingModel(good), scope=scope)
    res = w.run("how does the gate work?")
    assert res.action is not WrapperAction.CANCEL, (
        "the wrapper refused an ordinary answer: %s" % res.reason)


def test_the_scope_is_optional_and_the_wrapper_still_works():
    """AND THE SCOPE IS OPTIONAL. The wrapper is used in places where
    fieldcore is not on the path, and a wrapper that REFUSED because
    its scope could not be loaded would be a wall.

    So: with no scope the wrapper behaves exactly as before -- it
    passes what it always passed -- and the absence is not a refusal.

    AND THE SEPARATE CASE, which is the one that matters: a scope
    that was REQUESTED but cannot be used is logged as unavailable, so
    it never reads as a pass that was actually checked.
    """
    w = MTELLMWrapper(llm=HallucinatingModel(HALLUCINATION),
                       scope=None)
    res = w.run("what changed?")
    assert res.action is not WrapperAction.CANCEL
    assert res.modified, "the answer was dropped by a wrapper with no scope"

    # and a scope that cannot be used is reported
    class BrokenScope:
        def __repr__(self):
            return "<broken scope>"

    # the scope layer's own failure is caught inside the wrapper, so a
    # scope object that raises on use is logged as unavailable rather
    # than taking the wrapper down
    w2 = MTELLMWrapper(llm=HallucinatingModel(HALLUCINATION),
                        scope=BrokenScope())
    res2 = w2.run("what changed?")
    assert res2.action is not WrapperAction.CANCEL, (
        "an unusable scope refused the answer, which would be a wall")
    assert "scope_unavailable" in res2.flagged, (
        "the unusable scope was not reported: %r" % (res2.flagged,))


def test_the_resolver_returns_none_rather_than_raising():
    """AND THE RESOLVER NEVER RAISES. The wrapper is used in places
    where fieldcore is not on the path, and a resolver that raised
    would take the wrapper down with it."""
    scope = resolve_scope()
    assert scope is None or hasattr(scope, "version_exists")
