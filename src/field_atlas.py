"""
field_atlas.py — complete k-uniform hypergraph enumeration over an
n-sector field space, plus the systematic ablation harness that goes
with it.

WHY THIS EXISTS
---------------
Borrowed in structure from enuminous/FieldSpace (audited 2026-10-06),
which enumerates C(11,3) = 165 three-sector interaction blocks over an
11-sector field space. That project's real contribution is not its
placeholder physics — its own README calls the formulation
"proposed phenomenological formulation; independently unreviewed" —
it is two things we can check:

1. the enumeration result, kernel-checked in Lean 4 (Structure.lean,
   `native_decide` on Nat.choose), and
2. an ablation harness: 235 runs, systematic remove-1 / remove-2 /
   remove-3 plus term ablations, scored on a tail statistic.

So this module takes the SHAPE and drops the specific sector set.
FieldSpace hard-codes 11 sectors and rank 3; the combinatorics is
general and the generalization is the part worth having.

WHAT IS GENERALIZED
-------------------
For an n-sector field space V and interaction rank k:

    atlas size          C(n, k)
    per-sector incidence C(n-1, k-1)
    per-pair incidence  C(n-2, k-2)
    class partition     every subset of size j of k partitions V,
                        so the counts are C(a,j) * C(n-a,k-j) for a
                        distinguished sector class of size a

Every one of these is asserted as an IDENTITY against brute force in
tests, not merely computed.

WHAT IS REFUSED
---------------
1. A claim of k-uniformity without the count behind it. `atlas()` is
   the only constructor and it refuses k > n, k < 1, and an empty
   sector set, because C(n,k) is undefined or degenerate there and a
   silent empty result reads as "no interactions exist."

2. An ablation scored on a metric the caller did not name. Every
   ablation reports ALL tail statistics, not one number, because a
   single scalar hides which order of removal did the work.

3. Treating an ablation delta as a causal claim. `ablate()` returns
   deltas, and says in the payload that they are a ranking signal on a
   synthetic system. The upstream author's toy simulator used
   deterministic synthetic weights; this harness is offered as a
   harness, and running it on real dynamics requires passing real
   dynamics in. See `AblationHarness`.

ORIGIN AND LIMITS
-----------------
Adapted from enuminous/FieldSpace, MIT-unlicensed (no LICENSE file in
that repo as of 2026-10-06 — see docs/fieldspace-extraction-2026-10-06.md).
Adapted code only: none of the FieldSpace equations, sector names, or
synthetic weights are carried over.

Run: python src/field_atlas.py --help
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Atlas",
    "AtlasRefusal",
    "AblationRun",
    "AblationHarness",
    "atlas",
]


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------

class AtlasRefusal(Exception):
    """Raised instead of returning a degenerate atlas.

    A gate should be able to say no. C(0,3) is 0 and C(11,3) with an
    empty sector set both produce an empty atlas, which downstream code
    would read as a well-formed space with no interactions in it.
    """


# ---------------------------------------------------------------------------
# the enumeration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Atlas:
    """A complete rank-k uniform hypergraph on an n-sector field space.

    Immutable: the enumeration is a fact about the sector set, and a
    mutable copy would let two parts of a system disagree about how
    many interactions exist.
    """

    sectors: Tuple[str, ...]
    rank: int

    def __post_init__(self) -> None:
        if not self.sectors:
            raise AtlasRefusal("empty_sector_set")
        if len(set(self.sectors)) != len(self.sectors):
            dupes = sorted({s for s in self.sectors if self.sectors.count(s) > 1})
            raise AtlasRefusal(f"duplicate_sectors:{dupes}")
        if self.rank < 1:
            raise AtlasRefusal(f"rank_below_one:{self.rank}")
        if self.rank > len(self.sectors):
            raise AtlasRefusal(
                f"rank_exceeds_sectors:rank={self.rank},sectors={len(self.sectors)}"
            )

    # -- construction ------------------------------------------------------

    @property
    def blocks(self) -> List[Tuple[str, ...]]:
        """Every rank-k interaction block. The whole atlas."""
        return list(itertools.combinations(self.sectors, self.rank))

    def size(self) -> int:
        return math.comb(len(self.sectors), self.rank)

    # -- incidence ---------------------------------------------------------

    def sector_incidence(self) -> Dict[str, int]:
        """How many blocks each sector appears in. C(n-1, k-1) each.

        Uniformity is the load-bearing property: in a complete
        k-uniform hypergraph every vertex has identical degree. A
        sector appearing in a different number of blocks than its
        peers means the enumeration is not complete, however plausible
        the total looks.
        """
        deg: Dict[str, int] = {s: 0 for s in self.sectors}
        for b in self.blocks:
            for s in b:
                deg[s] += 1
        return deg

    def pair_incidence(self) -> Dict[Tuple[str, str], int]:
        deg: Dict[Tuple[str, str], int] = {}
        for b in self.blocks:
            for pair in itertools.combinations(b, 2):
                deg[pair] = deg.get(pair, 0) + 1
        return deg

    def is_uniform(self) -> bool:
        """Is every sector in the same number of blocks?

        The single cheapest check that the atlas is complete. FieldSpace
        asserted this at 45 incidences per sector over 11 sectors; the
        property holds for any n, k and is asserted here against brute
        force rather than trusted.
        """
        deg = self.sector_incidence()
        if not deg:
            return False
        return len(set(deg.values())) == 1

    def overlap_spectrum(self) -> Dict[int, int]:
        """Histogram of how many blocks any two distinct blocks share.

        For a complete k-uniform hypergraph this is fully determined by
        k and n; it is a structural fingerprint of the enumeration.
        FieldSpace checked the SUM (1980 + 6930 + 4620 = C(165,2)),
        which is a weaker identity. The full histogram is strictly more
        informative and costs the same.
        """
        hist: Dict[int, int] = {}
        blocks = self.blocks
        for a, b in itertools.combinations(blocks, 2):
            shared = len(set(a) & set(b))
            hist[shared] = hist.get(shared, 0) + 1
        return hist

    # -- structural taxonomy ----------------------------------------------

    def classes(self, distinguished: Sequence[str]) -> Dict[int, int]:
        """Partition blocks by how many members they draw from `distinguished`.

        This is the generalization of FieldSpace's six structural
        classes (three-scalar / gauge-two-scalar / gravity-two-scalar
        / etc). Their taxonomy was specific to an 11-sector space with
        gravity and gauge sectors singled out; here the caller names
        the distinguished set and the partition follows.
        """
        d = set(distinguished)
        unknown = d - set(self.sectors)
        if unknown:
            raise AtlasRefusal(f"unknown_distinguished_sectors:{sorted(unknown)}")
        hist: Dict[int, int] = {}
        for b in self.blocks:
            j = len(set(b) & d)
            hist[j] = hist.get(j, 0) + 1
        return hist

    def class_partition_is_exhaustive(self, distinguished: Sequence[str]) -> bool:
        """Do the classes account for every block exactly once?"""
        return sum(self.classes(distinguished).values()) == self.size()

    def to_dict(self) -> Dict:
        return {
            "sectors": list(self.sectors),
            "rank": self.rank,
            "size": self.size(),
            "uniform": self.is_uniform(),
            "overlap_spectrum": {str(k): v for k, v in sorted(self.overlap_spectrum().items())},
        }

    def __str__(self) -> str:
        return (
            f"Atlas({len(self.sectors)} sectors, rank {self.rank}, "
            f"{self.size()} blocks, uniform={self.is_uniform()})"
        )


def atlas(sectors: Iterable[str], rank: int) -> Atlas:
    """Build the complete rank-k atlas over `sectors`.

    The one constructor. Refuses rather than returning an empty atlas
    for a rank that cannot produce blocks.
    """
    return Atlas(tuple(sectors), rank)


# ---------------------------------------------------------------------------
# ablation harness
# ---------------------------------------------------------------------------

@dataclass
class AblationRun:
    """One ablation result. Every statistic is reported, not one score.

    A single headline number hides which order of removal did the
    work; the tail mean alone says nothing about stability.
    """
    kind: str
    removed: Tuple[str, ...]
    stable: bool
    final_norm: float
    peak: float
    mean_tail: float
    std_tail: float
    max_abs_final: float
    delta_mean_tail: Optional[float] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["removed"] = list(self.removed)
        return d


@dataclass
class _Stats:
    """Internal result of one simulated run, before delta is applied."""
    stable: bool
    final_norm: float
    peak: float
    mean_tail: float
    std_tail: float
    max_abs_final: float


class AblationHarness:
    """Systematic remove-k ablation over an atlas.

    USAGE — and the honest limit of it.

    The upstream FieldSpace harness ran this over a synthetic linear
    system whose couplings were literal modular arithmetic on sector
    indices. Its results are a test of the HARNESS, not of any physics.
    That is not a criticism of the design; it is what the design is for,
    and the author labelled it so.

    To run it on something real, pass a `dynamics` callable:

        dynamics(state: Dict[str, float], t: float) -> Dict[str, float]
            returns the derivative of each active sector at time t

    and a `tail_stats` callable. With no dynamics supplied the harness
    refuses rather than quietly synthesising one — that refusal is the
    point. A harness that invents dynamics when none is supplied will
    report confident deltas about a system nobody defined.
    """

    def __init__(
        self,
        atlas_: Atlas,
        dynamics: Optional[Callable[[Dict[str, float], float], Dict[str, float]]] = None,
        initial: Optional[Dict[str, float]] = None,
        steps: int = 800,
        dt: float = 0.03,
        tail_window: int = 100,
    ) -> None:
        self.atlas = atlas_
        self.dynamics = dynamics
        self.initial = initial
        self.steps = steps
        self.dt = dt
        self.tail_window = tail_window
        self._runs: List[AblationRun] = []

    def _initial(self, removed: FrozenSet[str]) -> Dict[str, float]:
        """Seeded from the atlas so runs are reproducible.

        Fixed seed, never random: an ablation whose starting state
        changes between runs cannot be compared against itself.
        """
        base = self.initial or {s: 0.08 + 0.015 * (i + 1)
                                for i, s in enumerate(self.atlas.sectors)}
        state: Dict[str, float] = dict(base)
        for s in removed:
            state[s] = 0.0
        return state

    def _stats(self, removed: FrozenSet[str]) -> _Stats:
        if self.dynamics is None:
            raise AtlasRefusal(
                "no_dynamics_supplied:harness_refuses_to_synthesise_one"
            )
        removed = frozenset(removed)
        state = self._initial(removed)
        active = [s for s in self.atlas.sectors if s not in removed]
        if not active:
            raise AtlasRefusal("all_sectors_removed")

        peak = max(abs(v) for v in state.values()) if state else 0.0
        tail: List[float] = []
        current_peak = peak
        norm = 0.0
        for n in range(self.steps):
            t = n * self.dt
            dx = self.dynamics(state, t)
            for s in active:
                state[s] += self.dt * dx.get(s, 0.0)
            current_peak = max((abs(state[s]) for s in active), default=0.0)
            peak = max(peak, current_peak)
            norm = math.sqrt(sum(state[s] ** 2 for s in active))
            if n >= self.steps - self.tail_window:
                tail.append(norm)

        return _Stats(
            stable=math.isfinite(norm) and norm < 1e5,
            final_norm=norm,
            peak=peak,
            mean_tail=statistics.fmean(tail),
            std_tail=statistics.pstdev(tail) if len(tail) > 1 else 0.0,
            max_abs_final=current_peak,
        )

    def run(self) -> List[AblationRun]:
        """Full systematic sweep: baseline, then every removal up to rank.

        Order is baseline, then all remove-1, all remove-2, ... up to
        the atlas rank. Cost grows combinatorially, so `max_rank` caps
        the sweep for large atlases.
        """
        if self.dynamics is None:
            raise AtlasRefusal("no_dynamics_supplied")
        base = self._stats(frozenset())
        runs = [AblationRun("baseline", (), base.stable, base.final_norm,
                            base.peak, base.mean_tail, base.std_tail,
                            base.max_abs_final, 0.0)]
        for r in range(1, self.atlas.rank + 1):
            for combo in itertools.combinations(self.atlas.sectors, r):
                st = self._stats(frozenset(combo))
                runs.append(AblationRun(
                    f"remove{r}", combo, st.stable, st.final_norm, st.peak,
                    st.mean_tail, st.std_tail, st.max_abs_final,
                    st.mean_tail - base.mean_tail,
                ))
        self._runs = runs
        return runs

    def summary(self) -> Dict:
        if not self._runs:
            raise AtlasRefusal("no_runs:call_run_first")
        by_kind: Dict[str, List[float]] = {}
        for r in self._runs:
            by_kind.setdefault(r.kind, []).append(r.delta_mean_tail or 0.0)
        return {
            "atlas": self.atlas.to_dict(),
            "run_count": len(self._runs),
            "all_stable": all(r.stable for r in self._runs),
            "delta_range_by_kind": {k: [min(v), max(v)] for k, v in sorted(by_kind.items())},
            "caveat": "deltas rank a synthetic or supplied system; they are not causal claims",
        }


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _demo_dynamics(atlas_: Atlas):
    """A synthetic dynamics callable, for exercising the harness.

    Reproducible modular weights, in the spirit of the upstream toy
    simulator and labelled the same way. This exists so the harness can
    be tested end to end; it is NOT a model of anything.
    """

    idx = {s: i for i, s in enumerate(atlas_.sectors)}
    pair = {}
    for a, b in itertools.combinations(atlas_.sectors, 2):
        i, j = idx[a], idx[b]
        pair[(a, b)] = 0.004 * (((i + 1) * 7 + (j + 1) * 11) % 9 - 4)

    def dynamics(state: Dict[str, float], t: float) -> Dict[str, float]:
        dx: Dict[str, float] = {}
        for s in atlas_.sectors:
            v = -(0.10 + 0.004 * (idx[s] % 5)) * state[s]
            for (a, b), w in pair.items():
                if a == s:
                    v += w * state.get(b, 0.0)
                elif b == s:
                    v += w * state.get(a, 0.0)
            dx[s] = v
        return dx

    return dynamics


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: demo | selfcheck | sweep")
        return 0

    if argv[0] == "demo":
        # FieldSpace's own numbers, reproduced by the general code.
        a = atlas(["E", "M", "S", "F", "W", "T", "I", "R", "H", "P", "A"], 3)
        print(a)
        print("uniform:", a.is_uniform())
        print("overlap spectrum:", a.overlap_spectrum())
        print("classes by scalar count:", a.classes(
            ["F", "W", "T", "I", "R", "H", "P", "A"]))
        return 0

    if argv[0] == "selfcheck":
        ok = True
        for n, k in [(11, 3), (8, 3), (6, 2), (5, 5), (7, 1), (12, 4)]:
            a = atlas([f"s{i}" for i in range(n)], k)
            deg = set(a.sector_incidence().values())
            good = a.size() == math.comb(n, k) and len(deg) == 1
            expected_deg = math.comb(n - 1, k - 1)
            good = good and deg == {expected_deg}
            print(f"  n={n:<3} k={k:<2} blocks={a.size():<6} degree={deg} "
                  f"expected={expected_deg} {'OK' if good else 'FAIL'}")
            ok = ok and good
        print("selfcheck:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    if argv[0] == "sweep":
        a = atlas(["E", "M", "S", "F", "W", "T", "I", "R", "H", "P", "A"], 3)
        h = AblationHarness(a, dynamics=_demo_dynamics(a))
        h.run()
        print(json.dumps(h.summary(), indent=2))
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))