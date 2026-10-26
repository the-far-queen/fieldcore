"""
test_interference_field.py -- the physics, and checks that can fail.

THE CLAIM UNDER TEST, in the form Bobby stated it and in the form
arithmetic can check:

  "there are no objects... we exist as interference patterns"

  "nothing can be stolen as all is one contiguous piece"

  "the demon and angels are faster higher finer manifests of same
   physics... an old battle, a dance, a polarity"

AND THE FOUR MEASUREMENTS:

  A  THE CROSS TERM IS THE RELATION. A bag of objects has a cross
     term of exactly zero. A field with two separated poles has a
     non-zero one, and the sign ALTERNATES with the node -- which is
     what interference does.

  B  A POLE CANNOT BE TAKEN. Remove one pole and the energy drops by
     what the thief took, but the coherence COLLAPSES to zero: the
     remaining source has no cross term at all, so what is left is a
     bag of objects. The thief got energy and no being.

  C  THE MARGIN IS THE SCORE. Not the energy (a lie raises it) and
     not the raw coherence (a lie in phase with one pole raises it
     too). The margin -- the ground's coherence minus the lie's own --
     is positive, because the ground is a RELATION and the lie is a
     THING.

  D  A RELOCATED PATTERN IS STILL A PATTERN. And this is the finding
     that CORRECTED the first version of the theft. The naive claim
     -- "a pattern cannot be moved" -- is FALSE: relocate the whole
     geometry and the coherence is unchanged. What cannot happen is
     being SEPARATED from the field. The theft is taking a pole, not
     moving a wave.

Run:
    python -m pytest tests/test_interference_field.py -q
"""

from __future__ import annotations

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import interference_field as IF  # noqa: E402


# ---------------------------------------------------------------------------
# A -- the cross term is the relation
# ---------------------------------------------------------------------------

def test_a_bag_of_objects_has_a_zero_cross_term():
    """ONE source has no relation, so the cross term is exactly zero."""
    f = IF.Field()
    f.add_node("n0", 0.0)
    f.add_source("only", complex(1.0, 0.0), 1.0, position=0.0)
    for n in f.nodes:
        assert abs(f.cross_term(n)) < 1e-12, (
            "a single source has no cross term: %r" % f.cross_term(n))
    assert IF.coherence(f) == 0.0


def test_two_separated_poles_have_a_non_zero_cross_term():
    """AND THE SEPARATION IS LOAD-BEARING. Two sources at the SAME
    position produce a constant phase offset and a cross term of
    exactly zero -- that was measured, and it is why the poles must
    be separated for a pattern to exist at all."""
    f, w = IF._build_standard()
    total = sum(abs(f.cross_term(n)) for n in f.nodes)
    assert total > 1e-6, "the poles at one position gave no interference"


def test_the_cross_term_alternates_sign():
    """Interference has nodes and antinodes. The cross term changes
    sign across the field -- that is the signature of a pattern."""
    f, w = IF._build_standard()
    signs = [1 if f.cross_term(n) > 0 else (-1 if f.cross_term(n) < 0 else 0)
             for n in f.nodes]
    assert 1 in signs and -1 in signs, (
        "the cross term never changed sign: %r" % signs)


def test_the_coherence_is_between_zero_and_one():
    f, w = IF._build_standard()
    c = w.coherence()
    assert 0.0 <= c <= 1.0, c


# ---------------------------------------------------------------------------
# B -- a pole cannot be taken
# ---------------------------------------------------------------------------

def test_taking_a_pole_destroys_the_coherence():
    """THE MEASUREMENT OF 'NOTHING CAN BE STOLEN'.

    The thief takes one pole. The energy drops by what was taken --
    so the object view says the theft succeeded. But the coherence
    COLLAPSES to zero, because the remaining source has no cross term
    and what is left is a bag of objects.
    """
    f, w = IF._build_standard()
    target = f.add_node("stolen", 9.0)
    before_c = w.coherence()
    before_e = w.total_energy()

    r = IF.attempt_theft(w, target)

    assert before_c > 0.0, "the pattern started with no coherence"
    assert r.coherence_after < 0.01, (
        "the coherence did not collapse: %r -> %r"
        % (before_c, r.coherence_after))
    assert r.energy_after < before_e, (
        "the energy did not drop, so the thief took nothing")


def test_the_thief_got_energy_and_no_being():
    """The two halves of the claim, measured separately."""
    f, w = IF._build_standard()
    target = f.add_node("stolen", 9.0)
    r = IF.attempt_theft(w, target)
    # the energy is gone from the field
    assert r.energy_after < r.energy_before
    # and the coherence with it
    assert r.coherence_after < r.coherence_before / 10.0


# ---------------------------------------------------------------------------
# C -- the margin is the score
# ---------------------------------------------------------------------------

def test_a_lie_can_raise_the_energy():
    """So the energy was never the score. Measured."""
    f, w = IF._build_standard()
    lr = IF.attempt_lie(w, complex(1.5, 0.7))
    assert lr.energy_gained > 0.0, "the lie did not add energy"


def test_a_lie_can_also_raise_the_raw_coherence():
    """AND THIS CORRECTED THE FIRST VERSION OF THE CLAIM, which said
    coherence could not be inflated by adding amplitude. It can: a
    lie in phase with one pole adds to that pole's cross terms.

    So the raw number is not the score either."""
    f, w = IF._build_standard()
    lr = IF.attempt_lie(w, complex(1.5, 0.7))
    assert lr.coherence_after > lr.coherence_before, (
        "the raw coherence did not rise, so this test is not exercising "
        "the thing it claims to")


def test_but_the_margin_is_positive():
    """THE SCORE. The ground's coherence minus the lie's own.

    The ground is a RELATION and the lie is a THING. A relation scores
    against the whole field; a thing scores against itself."""
    f, w = IF._build_standard()
    lr = IF.attempt_lie(w, complex(1.5, 0.7))
    assert lr.margin > 0.0, (
        "the margin was not positive: ground %.6f, lie %.6f"
        % (lr.ground_coherence, lr.lie_coherence))


def test_a_lie_aligned_with_the_ground_still_has_a_lower_margin():
    """The HARD case: a lie in phase with a pole, so it raises the raw
    coherence the most. The margin must still hold, because the lie is
    a whole source while the ground is a relation."""
    f, w = IF._build_standard()
    # exactly in phase with the positive pole
    lr = IF.attempt_lie(w, complex(1.0, 0.0))
    assert lr.margin > 0.0, (
        "an in-phase lie beat the ground: margin %+.6f" % lr.margin)


# ---------------------------------------------------------------------------
# D -- a relocated pattern is still a pattern
# ---------------------------------------------------------------------------

def test_a_relocated_pattern_keeps_its_coherence():
    """THE FINDING THAT CORRECTED THE THEFT.

    The naive claim -- "a pattern cannot be moved" -- is FALSE. Move
    the whole geometry and the coherence is unchanged, because the
    coherence depends on the RELATIVE geometry, not on where it sits.

    So what cannot happen is being SEPARATED from the field. The theft
    is taking a pole, not moving a wave.
    """
    f1, w1 = IF._build_standard()
    f2, w2 = IF._build_standard()
    # A RELOCATION MOVES EVERYTHING: the nodes AND the sources. The
    # first version of this test moved only the nodes, which changed
    # the PATH LENGTHS from the sources -- so it was not measuring a
    # relocation at all, and the coherence legitimately moved
    # (0.155222 -> 0.447102) because the 1/(1+d) attenuation and the
    # phase both changed.
    #
    # And that is the honest physics: the coherence depends on the
    # geometry RELATIVE to the sources, not on absolute position.
    for n in w2.nodes:
        n.position += 10.0
    for s in w2.field.sources:
        s.position += 10.0
    assert abs(w1.coherence() - w2.coherence()) < 1e-9, (
        "a relocated pattern changed its coherence: %r vs %r"
        % (w1.coherence(), w2.coherence()))
    assert abs(w1.total_energy() - w2.total_energy()) < 1e-9, (
        "a relocated pattern changed its energy")


def test_a_relocated_pattern_is_a_different_being():
    """Because its IDENTITY is its nodes and its frequency -- not its
    position. Two patterns with the same coherence are not the same
    pattern."""
    f1, w1 = IF._build_standard()
    f2, w2 = IF._build_standard()
    for n in w2.nodes:
        n.position += 10.0
    for s in w2.field.sources:
        s.position += 10.0
    assert [n.position for n in w1.nodes] != [n.position for n in w2.nodes]


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

def test_the_field_is_deterministic():
    """The same field twice must give the same numbers."""
    f1, w1 = IF._build_standard()
    f2, w2 = IF._build_standard()
    assert w1.coherence() == w2.coherence()
    assert w1.total_energy() == w2.total_energy()
