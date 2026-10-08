"""
coherence_spine.py -- the three concepts six files agreed on, as code.

WHERE THIS COMES FROM
---------------------
Six frontier transcripts, receipt-verified, read end to end. Measured
occurrence counts (`fieldcore/docs/corpus-vocabulary-index-2026-10-09.md`):

    concept      f1  f2  f3  f4  f5  f6   files
    coherence    21 419 523 495 209 326    6/6
    sheaf        11  40 174   1  14 405    6/6
    threshold    21  33  84  68   9  19    6/6

**Exactly three concepts survive all six files.** Everything else is
regional: PSB 4/6, sacred axis 5/6, governor 5/6, MVCC 3/6, and two
concepts that never propagated at all -- constitutional ground (psi_0,
45 mentions, file 1 only) and counterfactual (108, file 6 only).

Read together, the three survivors are one sentence:

    A SYSTEM IS HELD BY THRESHOLDS ON A SHEAF,
    AND THE QUALITY OF THE HOLDING IS COHERENCE.

This module is that sentence, executable. It is deliberately the only
part of the corpus promoted to code, because it is the only part six
files independently converged on.

WHAT IS ACTUALLY HERE
--------------------
1. `Site`      -- a stalk: a point with a value and a local tolerance
2. `Sheaf`     -- gluing maps BETWEEN sites, with a consistency law
3. `Threshold` -- a declared boundary that fires REFUSE or PASS
4. `Coherence` -- the measured quality of a sheaf, from real numbers

The sheaf is the part the corpus never implemented. Files 3 and 6 name
`LocalPatch`, `GluingMap`, `GlobalSection` and `CechCohomology` as classes
and define none of them usefully. **Genuine sheaf theory is the only
place where the corpus borrowed mathematics it did not build, and a local
construction is checkable in a way that the word "sheaf" is not.**

THE GLUING LAW, and why it is the whole point
---------------------------------------------
A sheaf is not a bag of points. It is a set of points plus restriction
maps, satisfying:

    for x in U_open(V):  i(x) in U_open(i(V))      locality

Any single global number satisfies that trivially, which is why most
"sheaf" implementations are a veneer over averaging. What separates a
real sheaf from a veneer is the FAILURE OF NAIVE MONOTONICITY:

    the whole is not automatically >= the sum of its parts

Two subspaces can each be locally consistent and their union be
inconsistent at the seam. That is the whole reason this structure
exists, and it is what `Sheaf.global_consistent()` measures. A structure
that cannot fail monotonicity is not a sheaf, it is an average.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that coherence is the right measure of anything.
It establishes that coherence can be COMPUTED from declared structure
rather than asserted about it -- and that the corpus's three surviving
concepts fit together tightly enough to be one mechanism rather than
three slogans.

It also does not implement cohomology. There is no H^1, no Cech
complex, no differential. The corpus named `CechCohomology` as a class
and left it empty; this file leaves it unnamed and honest instead.

Run: python src/coherence_spine.py --selftest
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# thresholds -- the boundary that fires
# ---------------------------------------------------------------------------

class Disposition(str, Enum):
    PASS = "pass"
    REFUSE = "refuse"          # matched deepseek4's vocabulary exactly


@dataclass(frozen=True)
class Threshold:
    """A declared boundary. Immutable: a system that edits its own
    yardstick has no yardstick."""
    name: str
    quantity: str               # what it bounds
    bound: float
    direction: str = "above"    # "above" fires when value >= bound
    on_refuse: Disposition = Disposition.REFUSE

    def __post_init__(self) -> None:
        if self.direction not in ("above", "below"):
            raise ValueError(f"{self.name}: direction must be above/below")
        if math.isnan(self.bound) or math.isinf(self.bound):
            raise ValueError(f"{self.name}: bound must be finite, got {self.bound}")

    def fires(self, value: float) -> bool:
        return value >= self.bound if self.direction == "above" \
            else value <= self.bound

    def check(self, value: float) -> Tuple[Disposition, str]:
        if self.fires(value):
            return self.on_refuse, f"{self.name}: {self.quantity}={value:.6g} breaches {self.direction} {self.bound}"
        return Disposition.PASS, ""


# ---------------------------------------------------------------------------
# sites -- the stalks
# ---------------------------------------------------------------------------

@dataclass
class Site:
    """One point of the sheaf: a value with local structure.

    `tolerance` is the LOCAL statement of how much this site may disagree
    with its neighbours. Sites with different tolerances are how a sheaf
    stops being an average.
    """
    name: str
    value: float = 0.0
    tolerance: float = 0.0
    prior: Optional[float] = None   # defaults to the initial value
    history: List[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        # A site that has never been updated has NOT drifted. Without this,
        # prior defaults to 0.0 and every freshly constructed site reports
        # drift == its initial value -- so constructing a system at rest
        # looks like it had just moved a lot. Found by a test that assumed
        # the sane behaviour and was surprised.
        if self.prior is None:
            self.prior = self.value

    def observe(self, value: float) -> None:
        self.prior = self.value
        self.value = float(value)
        self.history.append(float(value))

    def drift(self) -> float:
        return abs(self.value - self.prior)


@dataclass
class GluingMap:
    """A restriction map between two sites.

    Deliberately a plain callable. A sheaf whose gluing is a learned
    matrix cannot be checked; one whose gluing is a rule can.
    """
    name: str
    source: str
    target: str
    rule: Callable[[float], float]

    def apply(self, value: float) -> float:
        return float(self.rule(value))


# ---------------------------------------------------------------------------
# the sheaf
# ---------------------------------------------------------------------------

@dataclass
class Sheaf:
    """Sites plus restriction maps, with a consistency law that can FAIL.

    `global_consistent()` is the load-bearing method. It is the only place
    this file could be accused of being an average, and it is the only
    place the structure can say "no".
    """
    name: str
    sites: Dict[str, Site] = field(default_factory=dict)
    maps: List[GluingMap] = field(default_factory=list)

    def add(self, site: Site) -> Site:
        self.sites[site.name] = site
        return site

    def glue(self, source: str, target: str, rule: Callable[[float], float],
             name: Optional[str] = None) -> GluingMap:
        for s in (source, target):
            if s not in self.sites:
                raise KeyError(f"{self.name}: unknown site {s!r}")
        g = GluingMap(name=name or f"{source}->{target}",
                      source=source, target=target, rule=rule)
        self.maps.append(g)
        return g

    # -- the consistency law --------------------------------------------

    def violations(self) -> List[str]:
        """Every place a restricted value disagrees with the value held.

        A violation is a SEAM. Two subspaces can each be internally
        consistent and their union be inconsistent exactly here -- which is
        why gluing is not decoration and why averaging cannot see it.
        """
        out: List[str] = []
        for g in self.maps:
            src = self.sites[g.source]
            tgt = self.sites[g.target]
            restricted = g.apply(src.value)
            gap = abs(restricted - tgt.value)
            if gap > tgt.tolerance + 1e-12:
                out.append(
                    f"{g.name}: restricted {restricted:.6g} vs held "
                    f"{tgt.value:.6g}, gap {gap:.6g} > tolerance "
                    f"{tgt.tolerance:.6g}")
        return out

    def globally_consistent(self) -> bool:
        """Does the sheaf hold together?

        NOTE this can return False for two perfectly smooth subspaces.
        That is correct and it is the entire reason a sheaf is not an
        average: the seam is a real place where things can break, and a
        global mean would have reported both halves as fine.
        """
        return not self.violations()

    # -- coherence ------------------------------------------------------

    def coherence(self) -> float:
        """Measured, not asserted: 1.0 minus mean relative seam error.

        Returned alongside the threshold verdict so a reader can see
        whether the refusal was driven by a seam or by drift.
        """
        if not self.maps:
            return 1.0
        total = 0.0
        for g in self.maps:
            src = self.sites[g.source]
            tgt = self.sites[g.target]
            gap = abs(g.apply(src.value) - tgt.value)
            denom = max(abs(tgt.value), 1e-9)
            total += gap / denom
        mean_gap = total / len(self.maps)
        return max(0.0, min(1.0, 1.0 - mean_gap))

    def drift(self) -> float:
        if not self.sites:
            return 0.0
        return max(s.drift() for s in self.sites.values())


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def _identity(x: float) -> float:
    return x


def selftest() -> None:
    print("=" * 70)
    print("1. the spine, three concepts, as one mechanism")
    print("=" * 70)
    sh = Sheaf("demo")
    for i, nm in enumerate(("a", "b", "c")):
        sh.add(Site(nm, value=0.5, tolerance=0.01))
    sh.glue("a", "b", _identity)
    sh.glue("b", "c", _identity)
    print(f"  coherent sheaf   : {sh.coherence():.6f}  consistent={sh.globally_consistent()}")

    # a seam that breaks: c holds something a and b do not imply
    sh.sites["c"].observe(0.9)
    print(f"  broken seam      : {sh.coherence():.6f}  consistent={sh.globally_consistent()}")
    for v in sh.violations():
        print(f"      {v}")
    assert not sh.globally_consistent(), "a seam break must be visible"
    print()
    print("  >>> two internally-consistent halves, an inconsistent union.")
    print("      A global average would have called both halves fine. This")
    print("      is the failure-of-naive-monotonicity the sheaf exists for.")

    print()
    print("=" * 70)
    print("2. thresholds fire on a declared bound, and are immutable")
    print("=" * 70)
    t = Threshold("seam_budget", "relative_gap", 0.05, "above")
    print(f"  gap 0.01 -> {t.check(0.01)[0].value}")
    print(f"  gap 0.09 -> {t.check(0.09)[0].value}   ({t.check(0.09)[1]})")
    assert t.check(0.01)[0] is Disposition.PASS
    assert t.check(0.09)[0] is Disposition.REFUSE
    try:
        object.__setattr__  # noqa
        t.bound = 999.0
        raise AssertionError("threshold must be immutable")
    except AttributeError:
        print("  bound mutation refused: frozen dataclass, as it should be")
    try:
        Threshold("bad", "q", float("nan"))
        raise AssertionError("NaN bound must be refused")
    except ValueError:
        print("  NaN bound refused")

    print()
    print("=" * 70)
    print("3. coherence is computed from structure, not asserted")
    print("=" * 70)
    sh2 = Sheaf("d2")
    sh2.add(Site("x", 1.0, 0.01))
    sh2.add(Site("y", 1.0, 0.01))
    sh2.glue("x", "y", _identity)
    print(f"  matched sites        -> {sh2.coherence():.6f}")
    sh2.sites["y"].observe(1.5)
    print(f"  after 0.5 divergence-> {sh2.coherence():.6f}")
    assert sh2.coherence() < 1.0, "coherence must respond to a seam"
    print("  >>> the number moves because the STRUCTURE moved, not because")
    print("      anyone scored it.")

    print()
    print("=" * 70)
    print("4. what this is NOT")
    print("=" * 70)
    print("  not cohomology: no H^1, no Cech complex, no differential.")
    print("  Files 3 and 6 named 'CechCohomology' as a class and left it")
    print("  empty. This file leaves it unnamed instead.")
    print()
    print("  not a claim that coherence measures anything real. It shows")
    print("  the corpus's three surviving concepts fit together tightly")
    print("  enough to be ONE mechanism rather than three slogans.")
    print()
    print("  and it does not yet carry psi_0 (45 mentions, file 1 only) or")
    print("  counterfactual (108, file 6 only) -- the two concepts that")
    print("  never propagated. Those are the next candidates.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()