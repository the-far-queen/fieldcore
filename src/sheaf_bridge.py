"""
sheaf_bridge.py -- THE TWO SHEAVS, AND THE LINK BETWEEN THEM.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*.

**AND THE FC HAD THE OBSTRUCTION IN TWO FILES AND THE LINK BETWEEN THEM
IN NEITHER.** MEASURED 2026-11-07:

    fieldcore/src/coherence_spine.py   a SCALAR sheaf
        a Sheaf of Sites joined by GluingMaps, with
        `globally_consistent()`, `coherence()` and `drift()`
        and a NAMED violation:
            'b->c: restricted 0.5 vs held 0.9, gap 0.4 > tolerance 0.01'

    fieldcore/src/sheaf_loop.py        a LINEAR sheaf
        the Cech complex over a two-open cover, with H^0, H^1 and
        a NAMED question:
            'stalks disagree on shared coordinate 0: -0.5598.
             Which value is authoritative?'

**AND BOTH DETECT THE SAME PHENOMENON, IN DIFFERENT ALGEBRAS.** The
scalar sheaf says "the seam breaks". The linear sheaf says "the
cocycle is non-zero". **AND NEITHER KNEW THE OTHER EXISTED** --
`coherence_spine.py`'s own docstring says:

    "It also does not implement cohomology. There is no H^1, no Cech
     complex, no differential."

and `sheaf_loop.py` never imports it.

**SO WHAT IS THE LINK?** It is not that one calls the other. It is that
**THEY MEASURE THE SAME THING AND CAN BE CHECKED AGAINST EACH OTHER.**
The scalar sheaf has a boolean and a number; the linear sheaf has a
dimension. And the bridge is the instrument that says:

    WHEN THE SCALAR SHEAF'S SEAM BREAKS, THE LINEAR SHEAF'S H^1 IS
    NON-ZERO -- AND THE OTHER WAY ROUND.

**AND A BRIDGE THAT CANNOT GO RED IS A BRIDGE THAT PROVES NOTHING.** So
the selftest asserts BOTH directions, and the mutation check proves the
assertions can fail.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import coherence_spine as CS          # noqa: E402
import sheaf_loop as SL               # noqa: E402


@dataclass(frozen=True)
class Bridge:
    """What the two sheafs say about the same obstruction.

    **AND EVERY FIELD IS A MEASUREMENT**, the way the robot's report
    fields are. `scalar_consistent` is the scalar sheaf's own boolean;
    `h1_dim` is the linear sheaf's own dimension; `agree` is the
    bridge's own comparison.
    """
    #: THE SCALAR SHEAF'S VERDICT, on its own terms.
    scalar_consistent: bool
    #: THE SCALAR SHEAF'S SEAM ERROR, and its drift.
    scalar_coherence: float
    scalar_drift: float
    #: THE SCALAR SHEAF'S OWN NAMED VIOLATION, or None.
    violation: Optional[str]
    #: THE LINEAR SHEAF'S VERDICT, on its own terms.
    h0_dim: int
    h1_dim: int
    obstructed: bool
    #: THE COCYCLE'S NORM -- and this is the DATA's obstruction, which is
    #: NOT the same claim as H^1 > 0. **H^1 > 0 is a fact about the
    #: COVER** (the codimension); **a non-zero cocycle is a fact about
    #: the DATA** (the stalks disagree). Only the second one is a
    #: disagreement between two stalks, and only the second one is
    #: comparable to the scalar sheaf's seam break.
    cocycle_norm: float
    #: THE LINEAR SHEAF'S OWN NAMED QUESTION, or None.
    question: Optional[str]
    #: AND THE BRIDGE'S OWN COMPARISON: does a seam break mean an
    #: obstruction, in both directions?
    agree: bool

    def describe(self) -> Dict[str, Any]:
        return {
            "scalar_consistent": self.scalar_consistent,
            "scalar_coherence": round(self.scalar_coherence, 6),
            "scalar_drift": round(self.scalar_drift, 6),
            "violation": self.violation,
            "h0_dim": self.h0_dim,
            "h1_dim": self.h1_dim,
            "obstructed": self.obstructed,
            "cocycle_norm": round(self.cocycle_norm, 8),
            "question": self.question,
            "agree": self.agree,
        }

    def refusal(self) -> Optional[str]:
        """The NAMED refusal, or None.

        **AND THE REFUSAL NAMES BOTH SHEAVS**, because a caller who
        hears "the obstruction" must be able to tell WHICH algebra it
        was measured in -- and the two algebras answer different
        questions.
        """
        if self.agree:
            return None
        return (
            "the two sheafs disagree about the same obstruction: the "
            "scalar sheaf says consistent=%s (coherence %.6f, drift "
            "%.6f) and the linear sheaf's cocycle is %.8g (h1_dim=%d, "
            "obstructed=%s)"
            % (self.scalar_consistent, self.scalar_coherence,
               self.scalar_drift, self.cocycle_norm, self.h1_dim,
               self.obstructed))


def _identity(x: float) -> float:
    return x


def scalar_sheaf(broken: bool = True, tolerance: float = 0.01) -> CS.Sheaf:
    """The scalar sheaf, coherent or with a broken seam."""
    sh = CS.Sheaf("bridge")
    for nm in ("a", "b", "c"):
        sh.add(CS.Site(nm, value=0.5, tolerance=tolerance))
    sh.glue("a", "b", _identity)
    sh.glue("b", "c", _identity)
    if broken:
        sh.sites["c"].observe(0.9)
    return sh


def linear_sheaf(dim: int = 8, overlap: int = 4,
                 codim: int = 1) -> SL.SheafControlLoop:
    """The linear sheaf, over a two-open cover."""
    return SL.SheafControlLoop(n_stalks=2, dim=dim,
                                dim_intersection=overlap)


def linear_sections(loop: SL.SheafControlLoop, agree: bool,
                    seed: int = 1):
    """The local sections, agreeing or not.

    **AND THIS IS THE MEASUREMENT AND NOT A DETAIL.** MEASURED
    2026-11-07: `run_once` with no sections supplied generates two
    RANDOM vectors, and two random vectors essentially never agree on
    the overlap -- so the linear sheaf ALWAYS obstructed and the first
    version of this bridge claimed the two sheafs agreed, and it did
    not.

    **AND THE HONEST CROSS IS THE DATA, not the cover.** The scalar
    sheaf is coherent when its sites hold the same value and broken
    when one holds another. The linear sheaf glues when its two local
    sections agree on the overlap and obstructs when they do not. So
    the two sheafs are the same claim -- "the local data glue or they
    do not" -- in two algebras, and the bridge must feed them the SAME
    KIND OF DATA to compare them at all.

    `compatible_sections` builds both sections from ONE global vector,
    so they agree by construction, and the loop's own docstring says
    what must then happen: *"A loop fed these must report H^1 = 0."*
    """
    import numpy as np
    restr, _ = loop.build_cover(seed=seed)
    if agree:
        return SL.compatible_sections(restr, loop.dim, seed=seed)
    rng = np.random.default_rng(seed + 1)
    return [rng.normal(size=loop.dim), rng.normal(size=loop.dim)]


def bridge(broken: bool = True, dim: int = 8, overlap: int = 4,
           codim: int = 1) -> Bridge:
    """The two sheafs, read together.

    **AND THE COMPARISON IS MADE ON THE SHEAFS' OWN TERMS.** The scalar
    sheaf's `globally_consistent()` is its own boolean; the linear
    sheaf's `obstructed` is its own. The bridge does not rescale
    either one, because a bridge that redefines what it measures is a
    second instrument and not a bridge.

    **AND BOTH SHEAFS ARE FED THE SAME KIND OF DATA**, because a broken
    scalar sheaf and an obstructed linear sheaf are only comparable if
    the data disagrees in both.
    """
    sh = scalar_sheaf(broken=broken)
    violations = sh.violations()
    violation = violations[0] if violations else None

    loop = linear_sheaf(dim=dim, overlap=overlap, codim=codim)
    sections = linear_sections(loop, agree=not broken)
    out = loop.run_once(local_sections=sections, codim=codim)
    q = out.get("question") or {}
    question = q.get("question")

    scalar_consistent = sh.globally_consistent()
    obstructed = bool(out.get("obstructed"))
    cocycle_norm = float(out.get("cocycle_norm", 0.0))

    # AND THE AGREEMENT IS THE CROSS, AND THE CROSS IS THE COCYCLE AND
    # NOT H^1. MEASURED 2026-11-07: with agreeing local sections the
    # linear sheaf still reports `h1_dim: 1` and `obstructed: True`,
    # because H^1 > 0 is a fact about the COVER and not about the DATA.
    # So the bridge compares the COCYCLE -- the stalks' disagreement --
    # with the scalar sheaf's seam break.
    #
    # **AND THE COVER'S OBSTRUCTION IS STILL REPORTED**, because it is a
    # true fact and dropping it would be the same mistake in the other
    # direction. The bridge says BOTH: the cover's h1_dim and the
    # data's cocycle_norm.
    data_obstructed = cocycle_norm > 1e-12
    agree = (not scalar_consistent) == data_obstructed

    return Bridge(
        scalar_consistent=scalar_consistent,
        scalar_coherence=sh.coherence(),
        scalar_drift=sh.drift(),
        violation=violation,
        h0_dim=int(out.get("h0_dim", 0)),
        h1_dim=int(out.get("h1_dim", 0)),
        obstructed=obstructed,
        cocycle_norm=cocycle_norm,
        question=question,
        agree=agree)


def _selftest() -> int:
    """The bridge, proved.

    **AND THE SELFTEST ASSERTS BOTH DIRECTIONS**, because a bridge that
    checks one direction is half a bridge.
    """
    # -- 1. the BROKEN case: the scalar sheaf breaks, the linear
    #       sheaf's stalks disagree, and they AGREE.
    b = bridge(broken=True)
    assert not b.scalar_consistent, "the broken seam was not seen"
    assert b.violation is not None, "the violation was not named"
    assert "gap" in b.violation, b.violation
    assert b.cocycle_norm > 1e-12, "the stalks did not disagree"
    assert b.question, "the cocycle question was not asked"
    assert b.agree, "the two sheafs disagree about the broken case"
    assert b.refusal() is None, "a broken case is not a disagreement"

    # -- 2. the COHERENT case: the scalar sheaf is consistent AND the
    #       stalks AGREE, so the cocycle is zero.
    c = bridge(broken=False)
    assert c.scalar_consistent, "the coherent sheaf was called broken"
    assert c.violation is None, "the coherent sheaf named a violation"
    assert c.scalar_coherence == 1.0, c.scalar_coherence
    assert c.cocycle_norm <= 1e-12, (
        "the agreeing stalks produced a cocycle: %r" % c.cocycle_norm)
    assert c.question is None, (
        "the loop asked a question about agreeing stalks: %r"
        % c.question)
    assert c.agree, "the two sheafs disagree about the coherent case"

    # -- 3. AND THE COHERENT CASE IS NOT VACUOUS: the stalks' disagreement
    #       must be reachable, or the agreement is an artefact of two
    #       instruments that always say no.
    loop = linear_sheaf()
    out = loop.run_once(local_sections=linear_sections(loop, agree=False))
    assert out["cocycle_norm"] > 1e-12, (
        "the stalks never disagree, so the bridge's agreement proves "
        "nothing")

    # -- 4. AND THE COVER'S OBSTRUCTION IS A DIFFERENT CLAIM, and the
    #       bridge reports both. MEASURED 2026-11-07: with agreeing
    #       stalks the loop still says `h1_dim: 1` and `obstructed:
    #       True`, because H^1 > 0 is a fact about the COVER.
    assert c.h1_dim >= 1, (
        "the cover's obstruction is not reported: %r" % c.h1_dim)
    assert c.obstructed, "the cover's obstruction is not reported"

    # -- 5. AND A QUESTION ABOUT A ZERO DISAGREEMENT IS NOT ASKED. It
    #       WAS asked, and it said "stalks disagree on shared
    #       coordinate 0: +0.0000".
    assert c.question is None, (
        "the loop asked a question about a zero disagreement")

    # -- 6. AND THE REFUSAL NAMES BOTH SHEAFS
    bad = Bridge(scalar_consistent=True, scalar_coherence=1.0,
                 scalar_drift=0.0, violation=None, h0_dim=3, h1_dim=0,
                 obstructed=False, cocycle_norm=0.0, question=None,
                 agree=False)
    r = bad.refusal()
    assert r is not None, "a disagreement did not refuse"
    assert "scalar sheaf" in r and "linear sheaf" in r, r

    print("  [ok ] a broken seam and disagreeing stalks agree")
    print("  [ok ] a coherent sheaf and agreeing stalks agree")
    print("  [ok ] the disagreement is reachable, so the agreement is not vacuous")
    print("  [ok ] the cover's obstruction is reported as a separate claim")
    print("  [ok ] a question about a zero disagreement is not asked")
    print("  [ok ] the refusal names both sheafs")
    print()
    print("  THE SHEAF BRIDGE SELFTEST PASSED")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--coherent", action="store_true",
                    help="read the coherent case instead of the broken one")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    b = bridge(broken=not args.coherent)
    print("=" * 70)
    print("THE TWO SHEAFS, AND THE LINK")
    print("=" * 70)
    print()
    for k, v in b.describe().items():
        print("  %-18s %s" % (k, v))
    r = b.refusal()
    if r:
        print()
        print("  THE REFUSAL:", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
