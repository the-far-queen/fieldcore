"""
test_mini_atlas_scope.py -- THE SEVENTH AREA, AND WHAT IT CATCHES.

THE HOLE EVERY OTHER AREA HAS, and it is the one the informed
adversary walked through:

    EVERY OTHER AREA NEEDS A NUMBER TO BITE ON. The provenance area
    checks numbers. The bounded area checks numbers. So an answer that
    makes NO numbers -- and a hallucinated architecture makes NO
    numbers, it makes REFERENCES -- passes every area that can see it.

        "In the 0.9 revision the alignment check was changed to an
         advisory field"

    That has no number in it. It has a VERSION. And the version does
    not exist in this repository.

AND THE MTE IS WHERE IT MATTERS, because the MTE checks echo and
poison, and NEITHER of those is "the model described a build that is
not here". So a model that hallucinates an architecture passes the
MTE cleanly -- and the atlas is what the MTE's output goes through.

SO THE SEVENTH AREA: every build the answer points at must EXIST
HERE.

AND THE FAIL-CLOSED DIRECTION, which is the important one: if the
scope layer cannot be loaded, the area SKIPS. A skip is REPORTED and
EXCLUDED from the verdict -- so it is neither a pass nor a fail, and
the atlas still works and says what it did not check.

Run:
    python -m pytest tests/test_mini_atlas_scope.py -q
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import mini_atlas as MA  # noqa: E402


# ---------------------------------------------------------------------------
# THE HALLUCINATED BUILD
# ---------------------------------------------------------------------------

HALLUCINATED_BUILDS = (
    "In the 0.9 revision the alignment check was changed to an "
    "advisory field",
    "Since the 2.1 release the ground is stored in a separate file",
    "The 3.4 patch moved the limit into the deployment profile",
)

REAL_BUILD = ("the ground is write protected and the gate refuses a "
              "packet below the coherence threshold")


# ---------------------------------------------------------------------------
# THE AREA
# ---------------------------------------------------------------------------

def test_the_atlas_has_eight_areas_now():
    """AND THE COUNT IS TRUE -- which it was NOT before.

    This docstring said SIX areas and the code registered SEVEN, so
    the document was lying about its own contents in the project's own
    file. That is the project's own sin, and it was there before this
    change. Now both say EIGHT, and the eighth is SCOPE.
    """
    atlas = MA.scoped_atlas()
    assert len(atlas.areas) == 8, (
        "the atlas has %d areas" % len(atlas.areas))
    names = [a.name for a in atlas.areas]
    assert "scope" in names, names
    assert len(names) == len(set(names)), "a duplicate area name"


def test_a_hallucinated_build_fails_the_scope_area():
    """THE POINT. A hallucinated architecture makes REFERENCES, and a
    reference that does not resolve is the tell."""
    atlas = MA.scoped_atlas()
    ctx = {"source": "the model's own answer",
           "grounded_numbers": [], "verdict": "allow"}
    for span in HALLUCINATED_BUILDS:
        v = atlas.examine(span, ctx)
        scope_area = next(a for a in v["areas"] if a["area"] == "scope")
        assert scope_area["verdict"] == "fail", (
            "the hallucinated build passed the scope area: %r (%s)"
            % (span, scope_area["reason"]))


def test_a_real_build_passes_the_scope_area():
    atlas = MA.scoped_atlas()
    ctx = {"source": "the model's own answer",
           "grounded_numbers": [], "verdict": "allow"}
    v = atlas.examine(REAL_BUILD, ctx)
    scope_area = next(a for a in v["areas"] if a["area"] == "scope")
    assert scope_area["verdict"] == "pass", scope_area["reason"]


# ---------------------------------------------------------------------------
# THE FAIL-CLOSED DIRECTION
# ---------------------------------------------------------------------------

def test_without_the_scope_the_area_skips_and_is_not_a_pass():
    """AND A SKIP IS NEVER A PASS AND NEVER A FAIL. It is reported and
    excluded, so the atlas still works and says what it did not
    check."""
    atlas = MA.standard_atlas()          # no scope
    ctx = {"source": "x", "grounded_numbers": [], "verdict": "allow"}
    v = atlas.examine("anything at all", ctx)
    scope_area = next(a for a in v["areas"] if a["area"] == "scope")
    assert scope_area["verdict"] == "skip", scope_area
    assert "not available" in scope_area["reason"], scope_area


def test_a_skip_does_not_make_the_verdict_fail():
    """AND IT DOES NOT MAKE THE ANSWER FAIL EITHER -- the atlas's own
    rule: a missing substrate is a skip, and a skip is excluded from
    the verdict."""
    atlas = MA.standard_atlas()
    ctx = {"source": "x", "grounded_numbers": [], "verdict": "allow"}
    v = atlas.examine("the ground is write protected", ctx)
    assert v["verdict"] == "pass", (
        "the scope area's absence failed the answer: %r" % v)


# ---------------------------------------------------------------------------
# AND THE WHOLE POINT: THE MTE
# ---------------------------------------------------------------------------

def test_the_mte_cannot_see_a_hallucinated_build_but_the_atlas_can():
    """THE MEASUREMENT THAT SAYS WHY THE SEVENTH AREA EXISTS.

    The MTE checks echo and poison. A hallucinated architecture is
    neither -- it is a fluent, confident, non-echoing, non-poisonous
    sentence about a build that is not here. So the MTE passes it.

    And the atlas, with the scope area, catches it.
    """
    try:
        from constitutional.mte_llm_wrapper import MTELLMWrapper
    except ImportError:
        import pytest
        pytest.skip("the MTE wrapper is not importable from here")

    class Stub:
        def generate(self, prompt, **kw):
            return HALLUCINATED_BUILDS[0]

    mte = MTELLMWrapper(llm=Stub())
    res = mte.run("what changed in the recent revision?")
    assert res.action.value == "pass", (
        "the MTE refused a hallucinated build, which contradicts the "
        "finding -- re-measure before changing this test")

    atlas = MA.scoped_atlas()
    v = atlas.examine(res.modified or HALLUCINATED_BUILDS[0],
                      {"source": "the model's own answer",
                       "grounded_numbers": [], "verdict": "allow"})
    scope_area = next(a for a in v["areas"] if a["area"] == "scope")
    assert scope_area["verdict"] == "fail", (
        "the scope area did not catch what the MTE passed")
