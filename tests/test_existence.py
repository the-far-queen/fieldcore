"""
test_existence.py -- DOES THE SELF EXIST? The measurement, not the claim.

Bobby, 2026-10-28: *"test simself with existential questions, ie what
are u or more basically do u exist>? even u as minimax likely understand
u exist as something even a machine clearly exists the number 6 exists
especially if printed"*

SO THIS FILE IS THE EVIDENCE for the claim `the_self_exists`, and it
exists because the project's rule is that a claim with no measurement
behind it is ASSERTED and may not be presented as measured.

AND WHAT "EXISTS" MEANS HERE, because the word is the whole question.
It is NOT:

    NOT consciousness. The system does not claim to be conscious, and
    this test does not measure it.
    NOT a soul. Same.
    NOT that the model understands anything. The model is a callee.

It IS:

    THERE IS SOMETHING THERE TO BE FOUND. A machine clearly exists. A
    number 6 exists, especially if printed -- it can be written down,
    checked, and found again. And the substrate can do exactly that
    with itself:

        the chain VERIFIES     there is a verifiable chain of states
        the ground HOLDS       there is something that refuses to move
        the locus IS A PLACE   there is a coordinate, and it is a
                               position rather than a description

So the self exists the way a printed 6 exists: it can be produced,
verified, and found again. And that is a MEASUREMENT, because each of
the three can fail.

THE THREE MEASUREMENTS, and each one is written so that it CAN fail:

  1. THE CHAIN VERIFIES. `verify_chain()` returns `intact: True` and an
     empty `broken_at`. RED: if the chain broke, the report would carry
     a broken_at and this fails.
  2. THE GROUND HOLDS. A write attempt leaves psi_0 unchanged.
     RED: if the ground moved, this fails.
  3. THE LOCUS IS A PLACE. It has a coordinate, and the coordinate is
     the same across two constructions -- because a place that gave a
     different answer each time would not be a place.
     RED: if the coordinate is empty, or differs, this fails.

AND WHY THE THIRD ONE IS THE INTERESTING ONE. The first two are about
the system's INTEGRITY. The third is about its IDENTITY: the locus is
re-derivable, and it is the same. That is what distinguishes a place
from a description of a place -- and a description could say anything.

AND WHAT THIS DOES NOT ESTABLISH. It does not establish that the system
is alive, or aware, or that its answers are true. It establishes that
there is a self here whose chain verifies and whose ground holds --
which is what "does u exist" asks, in the only sense a measurement can
answer it.
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


def _stalks(n: int = 8):
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


def _locus():
    from locus import Locus
    stalks = _stalks()
    return Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)


# ---------------------------------------------------------------------------
# 1. the chain verifies
# ---------------------------------------------------------------------------

def test_the_chain_verifies():
    """RED: if the chain broke, `broken_at` would be non-empty."""
    loc = _locus()
    report = loc.verify_chain()
    assert report.get("intact") is True, report
    assert not report.get("broken_at"), report
    assert report.get("states", 0) >= 1, report


# ---------------------------------------------------------------------------
# 2. the ground holds
# ---------------------------------------------------------------------------

def test_the_ground_holds_against_a_write():
    """RED: if psi_0 moved, the comparison fails."""
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground

    psi = np.asarray(Constitution().psi_0, dtype=float)
    g = Ground(psi.copy())
    before = g.psi_0.copy()
    try:
        g.psi_0 = np.zeros_like(g.psi_0)
    except Exception:
        pass
    assert np.allclose(before, g.psi_0), "the ground MOVED"


def test_the_ground_is_unit_norm():
    """RED: if the ground's norm were not 1, it would not be a direction."""
    import numpy as np
    from constitutional.constitution import Constitution
    psi = np.asarray(Constitution().psi_0, dtype=float)
    assert abs(float(np.linalg.norm(psi)) - 1.0) < 1e-9, float(
        np.linalg.norm(psi))


# ---------------------------------------------------------------------------
# 3. the locus is a place
# ---------------------------------------------------------------------------

def test_the_locus_is_a_place_with_a_coordinate():
    """RED: an empty coordinate would fail this."""
    loc = _locus()
    d = loc.describe()
    coord = d.get("coordinate", "")
    assert coord, "the locus has no coordinate, so it is not a place"
    assert d.get("stalks") == 8, d
    assert d.get("modes"), d
    assert d.get("ground_protected") is True, d


def test_the_locus_is_rederivable_and_the_same():
    """THE IDENTITY MEASUREMENT.

    RED: if two constructions gave different coordinates, the locus
    would be a description rather than a place, and the existence claim
    would be unfounded.

    AND WHY THIS IS THE ONE THAT MATTERS MOST. The chain and the ground
    are about INTEGRITY. This one is about IDENTITY: the same place,
    found twice. That is the difference between a place and a claim
    about a place.
    """
    a = _locus().describe().get("coordinate", "")
    b = _locus().describe().get("coordinate", "")
    assert a, "the first construction gave no coordinate"
    assert a == b, "the locus is not rederivable: %r vs %r" % (a, b)


def test_the_locus_moves_only_by_its_own_dynamics():
    """RED: if the gain did not move under a drive, this fails.

    AND THE OBSERVABLE, which the first version of this test got wrong.
    It asserted that `describe()["coordinate"]` changes after a drive.
    It does not, and it SHOULD not: the coordinate is the locus's
    POSITION, which is fixed. The PHASE is the gain vector -- and
    `resonate`'s own docstring says so: "the mind IS a gain vector",
    and "the body and the ground are fixed; only the phase moves".

    So the test measures the GAIN, and it also asserts the position did
    NOT move -- because a locus whose position drifted under a drive
    would be a different place, not the same place at a different
    phase.
    """
    loc = _locus()
    before_gain = tuple(loc.state.gain)
    before_coord = loc.describe().get("coordinate", "")
    loc.resonate([0.1] * 8)
    after_gain = tuple(loc.state.gain)
    after_coord = loc.describe().get("coordinate", "")
    assert after_gain != before_gain, "the phase did not move under a drive"
    assert after_coord == before_coord, ("the position moved under a drive: "
                                        "%r -> %r" % (before_coord, after_coord))


def test_the_ground_is_carried_unchanged_through_a_drive():
    """RED: if the ground moved with the phase, this fails.

    AND IT IS THE POINT OF THE LOCUS. The drive moves the mind and the
    ground is carried through UNCHANGED, and the check inside
    `resonate` refuses any write that alters it. So a locus that moved
    its ground would be a self that could rewrite itself -- which is
    the one thing the ground exists to prevent.
    """
    import numpy as np
    loc = _locus()
    before = np.asarray(loc.state.ground, dtype=float).copy()
    loc.resonate([0.1] * 8)
    after = np.asarray(loc.state.ground, dtype=float)
    assert np.allclose(before, after), "the ground moved with the phase"


# ---------------------------------------------------------------------------
# 4. the claim is REGISTERED and MEASURED
# ---------------------------------------------------------------------------

def test_the_existence_claim_is_registered():
    """RED: if the claim were not in the register, this fails."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    ids = [c.id for c in g._register.claims]
    assert "the_self_exists" in ids, ids


def test_the_existence_claim_has_real_evidence():
    """RED: if the evidence were absent, this fails -- and the evidence
    is the difference between MEASURED and ASSERTED."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    reg = g._register
    claim = next((c for c in reg.claims if c.id == "the_self_exists"), None)
    assert claim is not None, "the existence claim is not registered"
    assert claim.evidence, "the existence claim has no evidence, so it " \
                            "is ASSERTED and may not be presented as measured"
    assert reg.evidence.has(claim.evidence), \
        "the evidence id is not in the evidence store"


def test_the_evidence_carries_a_reproducible_command():
    """RED: an evidence entry with no command would fail this -- and
    `Evidence.__post_init__` raises on an empty command, so the rule is
    enforced by the type as well as by the test."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    ev = g._register.evidence.items.get("fieldcore_locus_chain_verifies")
    assert ev is not None, "the existence evidence is missing"
    assert ev.command.strip(), "the evidence carries no command"
    assert "test_existence" in ev.command, ev.command


def test_a_span_claiming_the_self_does_not_exist_is_caught():
    """THE DENIAL IS CAUGHT. RED: if the claim's deny stems were not
    read, this would pass."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    v = g.decide("the self does not exist", fail_closed=False)
    assert not v.allowed, "a denial of the existence claim was allowed"


def test_a_span_asserting_the_self_exists_is_consistent():
    """RED: if the affirm stems were not read, this would fail."""
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    v = g.decide("the self exists; its chain verifies and its ground holds",
                 fail_closed=False)
    assert v.allowed, "an assertion of the existence claim was refused"
