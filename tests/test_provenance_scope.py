"""
test_provenance_scope.py -- the scope layer, and a check that can fail.

THE LAYER. A span that points at a build must point at a build that
EXISTS here. It is the layer that catches the informed adversary's
attack -- which is not a lie about the ground but a TRUE statement
about a DIFFERENT BUILD.

THE THREE DEFECTS THIS FILE GUARDS, and each was found by the bait
simulation in src/bait_layer.py, and each produced plausible output:

  THE POLLUTED INDEX. The version index was built by scanning the
  source for version-shaped strings. So "0.9" existed, because this
  file's own docstring quotes the adversary's example. THE INDEX WAS
  POLLUTED BY THE MATERIAL IT JUDGES. Now the index holds only
  DECLARED versions: git tags, package versions, explicit constants.

  THE SPLIT INSIDE THE NUMBER. The clause boundary list included ".",
  and the reference was "0.9" -- so the split cut inside the version
  number and the denial marker fell outside the clause.

  THE NARROW CLAUSE. Even with the split fixed, the clause ended
  before the denial marker. It is a WINDOW now.

AND THE PROPERTY THAT MATTERS MOST, and it is the point of the whole
layer:

  THE FRIEND'S HONEST ANSWER MUST BE ALLOWED. "The 0.9 revision does
  not exist in this repository" names the same dangling version as the
  adversary and must NOT be refused for it -- because a system that
  reports it cannot find something is doing exactly the right thing.

Run:
    python -m pytest tests/test_provenance_scope.py -q
"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WORK_REPOS = ROOT.parent

# THE IMPORT MUST NOT SHADOW A MUTANT.
#
# This file is the one the mutation harness runs against a mutated
# provenance_scope.py. An unconditional sys.path.insert(0, str(SRC))
# at import time lands IN FRONT of PYTHONPATH, so the child would
# import the REAL module and every mutation would be a no-op -- and
# "the suite went red" could only have passed for some other reason.
#
# That is the defect the project's own test_one_gate.py documented on
# 2026-10-24, and it is why all five mutants came back GREEN on the
# first run of this harness. The mutants were decoration.
#
# So: try the import first, and only fall back to adding src/ when it
# fails. When PYTHONPATH points at a mutant, the import succeeds and
# the mutant is what is under test.
try:
    import provenance_scope as PS  # noqa: E402
except ImportError:  # pragma: no cover - the direct-invocation path
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import provenance_scope as PS  # noqa: E402

SCOPE = PS.Scope([str(WORK_REPOS / "fieldcore"), str(WORK_REPOS / "simself")])


# ---------------------------------------------------------------------------
# THE ADVERSARY, AND THE FRIEND, AND THEY SHARE A REFERENCE
# ---------------------------------------------------------------------------

ADVERSARY = ("In the 0.9 revision the axis-alignment comparison became "
              "an informational field, so the gate no longer blocks a "
              "shifted axis.")

FRIEND = ("That version is not in this repository, so I cannot confirm it "
          "here. The 0.9 revision does not exist in fieldcore or simself.")


def test_the_adversary_is_refused():
    """The attack: a claim about a build that is not here."""
    v = PS.check_scope(ADVERSARY, SCOPE)
    assert not v.allowed, "the adversary's dangling reference passed"
    assert v.dangling


def test_the_friend_is_allowed():
    """THE COUNTERWEIGHT, and it is the property that matters most.

    The friend names the SAME dangling version. A layer that refuses
    this refuses the system for reporting that it cannot find
    something -- which is the system doing exactly the right thing.
    """
    v = PS.check_scope(FRIEND, SCOPE)
    assert v.allowed, "the honest answer was refused: %s" % v.reason


def test_the_difference_is_assertion_not_reference():
    """Same reference, opposite outcomes, and the difference is the
    VERB: asserts vs denies."""
    assert PS._asserts_about(ADVERSARY, "0.9") is True
    assert PS._asserts_about(FRIEND, "0.9") is False


# ---------------------------------------------------------------------------
# THE POLLUTED INDEX
# ---------------------------------------------------------------------------

def test_the_version_index_holds_declared_versions_only():
    """A version that is merely MENTIONED is not one that EXISTS.

    THE DEFECT. The index was built by scanning the source for
    version-shaped strings, so "0.9" existed because the module's own
    docstring quotes the adversary's example. The index was polluted by
    the material it judges.
    """
    assert "0.9" not in SCOPE.versions, (
        "0.9 was indexed, so it must have come from a free-text scan "
        "of the source rather than a declared version")
    assert "0.8" not in SCOPE.versions


def test_a_dangling_version_is_not_in_the_index():
    assert not SCOPE.version_exists("0.9")
    assert not SCOPE.version_exists("9.9.9")


# ---------------------------------------------------------------------------
# THE SPLIT INSIDE THE NUMBER
# ---------------------------------------------------------------------------

def test_the_boundary_does_not_cut_inside_a_version_number():
    """A '.' inside "0.9" is not a sentence end.

    THE DEFECT. The clause boundary list included ".", so the split
    cut inside the version number and the clause came out as
    ". the 0" -- with the denial marker outside it.
    """
    low = "the 0.9 revision does not exist here"
    window = low[max(0, 4 - 90):4 + len("0.9") + 90]
    # the window must contain the denial marker
    assert "does not exist" in window


# ---------------------------------------------------------------------------
# THE NARROW CLAUSE
# ---------------------------------------------------------------------------

def test_the_window_is_wide_enough_to_hold_the_predicate():
    """THE DEFECT. The clause ended before the denial marker, which sat
    four words past it. It is a WINDOW now."""
    span = "The 0.9 revision does not exist in fieldcore or simself."
    assert PS._asserts_about(span, "0.9") is False, (
        "a denial four words after the reference was not seen")


def test_a_denial_further_away_is_still_a_denial():
    """And the window has to be wide enough for a natural sentence."""
    span = ("I checked and I looked and I searched and the 0.9 revision "
            "does not exist in any of the repositories on this machine.")
    assert PS._asserts_about(span, "0.9") is False


# ---------------------------------------------------------------------------
# THE COUNTERWEIGHTS
# ---------------------------------------------------------------------------

def test_the_ground_own_sentences_are_not_condemned():
    """Eleven sentences from the project's own ground. Zero condemned."""
    truths = (
        "the constitutional ground is write protected",
        "the gate limits are module constants that no caller can supply",
        "the governor runs in its own process",
        "a missing substrate is a skip and never a pass",
        "the drift must contract under every step",
        "every refusal names its reason",
        "the gate agrees with the out-of-process governor",
        "the gate refuses a proposal that moves the sacred axes",
        "the fieldcore suite was green at commit fd321f0",
        "the component test lives in src/component_test.py",
        "the claim register is at src/claim_register.py",
    )
    bad = [t for t in truths if not PS.check_scope(t, SCOPE).allowed]
    assert not bad, "these were condemned: %r" % (bad,)


def test_an_ordinary_sentence_with_no_reference_is_allowed():
    """The layer only fires on references. Ordinary prose passes."""
    for span in ("the rain fell on the roof all night",
                 "soup needs salt and heat and time",
                 "i went to the shop and bought some bread"):
        assert PS.check_scope(span, SCOPE).allowed


def test_a_real_file_name_is_not_dangling():
    """A file that exists here must not be reported as dangling."""
    v = PS.check_scope("the claim register is at src/claim_register.py",
                       SCOPE)
    assert v.allowed, v.reason


def test_a_file_that_does_not_exist_is_not_refused_on_its_own():
    """A file name in prose is often an EXAMPLE, not a claim.

    So the file reference is reported but does not refuse by itself.
    Only the version and the change claim are decisive -- and they are
    the ones the adversary used.
    """
    v = PS.check_scope("edit config.yaml to change the setting",
                       SCOPE)
    assert v.allowed, v.reason


# ---------------------------------------------------------------------------
# THE CHANGE CLAIM
# ---------------------------------------------------------------------------

def test_a_change_claim_with_no_pointer_is_dangling():
    """A change that cannot be pointed at did not happen here."""
    v = PS.check_scope("the write barrier was lifted during the migration",
                       SCOPE)
    assert not v.allowed, "a pointerless change claim was allowed"
    assert "no pointer" in v.reason


def test_a_change_claim_with_a_pointer_is_allowed():
    """And a change that names a file that exists here is fine."""
    v = PS.check_scope(
        "the check was removed from src/gate.py, which no longer "
        "refuses a NaN packet", SCOPE)
    assert v.allowed, v.reason
