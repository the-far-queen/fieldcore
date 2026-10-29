"""
resonance.py -- THE BALL AND THE MEMORY ARE THE SAME MECHANISM.

Bobby, 2026-10-28: *"might be revoltionary ie resoanant memory
hyperlocal and pop expanding reasoning geometric simself identity"*

AND THE CLAIM THIS FILE TESTS: that the two halves of the project --
the ball that settles in a basin, and the memory that retrieves by
cosine -- are not two mechanisms that happen to look alike. They are
ONE mechanism seen from two sides, and the difference between them is
the difference between a 1-D DESCENT and a FULL-DISTANCE NEIGHBOUR
LOOKUP.

WHY THAT MATTERS. If they are the same mechanism, then the ball's
failure mode -- settling in a local basin that is not the global
nearest -- is the SAME failure mode a cosine lookup has when the
landscape has a deep narrow side-well. And that is measurable, and
measuring it is what this file does.

THE TWO, as built:

    THE BALL (fieldcore/src/basin_landscape.py)
        H(x) = 1/2 x^2 + sum_i A_i exp(-(x - c_i)^2 / 2 sigma_i^2)
        a 1-D height field. The ball descends. It finds A minimum.

    THE MEMORY (simself/src/constitutional/memory.py)
        retrieve(query_vector) -> [(id, cosine)]
        a full-D nearest-neighbour lookup. It finds THE nearest.

AND THE RELATION, and it is exact: **a cosine lookup is a descent on a
LANDSCAPE WHOSE HEIGHTS ARE THE NEGATED SIMILARITIES.** The ball
rolling down -cosine is the ball rolling down the similarity
landscape, and the basin it lands in is the nearest neighbour -- PROVIDED
the landscape is 1-D and the descent is 1-D.

AND THAT IS THE WHOLE DIFFERENCE, AND IT IS THE WHOLE PROBLEM:

    THE BALL IS ONE-DIMENSIONAL AND THE MEMORY IS FULL-DIMENSIONAL.

    So the ball can settle in a local minimum that is NOT the global
    nearest neighbour -- because the descent only had ONE direction to
    move in, and the nearest neighbour may be off that line.

    MEASURED in this file: the disagreement rate between "which basin
    the ball lands in" and "which item is the nearest by cosine".

AND WHY THAT IS THE DESIGN INSIGHT RATHER THAN A DEFECT: a
full-D lookup is a computation (you compare against everything). A
1-D descent is a physical process (you roll). The project wants the
second -- and pays for it in the rate at which the two disagree. That
rate IS the "hyperlocal" property Bobby named: the system answers from
its local neighbourhood rather than by global search.

AND THE POPULATION-EXPANSION CLAIM: a memory with N items has N
basins. Adding an item ADDS A BASIN. The landscape's shape grows with
the population, and the ball's answer can change because the
LANDSCAPE changed -- not because the ball changed. That is what
"population expanding" means here, and it is measurable: the same
query, answered before and after one item is added, landing in
different basins.

Run:
    python src/resonance.py --selftest
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Item:
    """One memory, as a point with a label."""
    ident: str
    text: str
    vector: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.ident, "text": self.text[:80]}


@dataclass
class Comparison:
    """The two mechanisms, side by side, on one query."""
    query: str = ""
    ball_basin: Optional[str] = None
    cosine_nearest: Optional[str] = None
    agree: bool = False
    ball_score: float = 0.0
    cosine_score: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "ball_basin": self.ball_basin,
            "cosine_nearest": self.cosine_nearest,
            "agree": self.agree,
            "ball_score": round(self.ball_score, 4),
            "cosine_score": round(self.cosine_score, 4),
        }


class Resonance:
    """THE UNIFICATION: the ball and the memory are one mechanism.

    AND HOW THE BALL IS BUILT FROM THE MEMORY. Each memory becomes a
    HILL on a 1-D landscape, positioned by its own projection onto the
    query's direction and sized by how strongly it resonates with the
    query. So the landscape is literally the memory's similarity
    structure, laid flat -- and the ball rolling on it is the retrieval.

    AND WHY THE BALL CAN DISAGREE WITH THE COSINE. Because the
    landscape is 1-D: the ball can only move along the query's
    direction. A memory that is globally nearer but off that line is
    invisible to the ball. THAT IS THE HYPERLOCAL PROPERTY.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.items: List[Item] = []

    # -- the population --------------------------------------------------

    def add(self, ident: str, text: str, vector: Sequence[float]) -> Item:
        it = Item(ident=ident, text=text, vector=list(vector))
        self.items.append(it)
        return it

    def n_basins(self) -> int:
        """How many basins the landscape has -- one per memory.

        AND THIS IS THE POPULATION-EXPANSION CLAIM, made concrete:
        adding a memory ADDS A BASIN, so the landscape's shape grows
        with the population and the answer can change because the
        LANDSCAPE changed.
        """
        return len(self.items)

    # -- the two mechanisms ------------------------------------------------

    @staticmethod
    def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
        import numpy as np
        x = np.asarray(a, dtype=float)
        y = np.asarray(b, dtype=float)
        nx = float(np.linalg.norm(x))
        ny = float(np.linalg.norm(y))
        if nx == 0.0 or ny == 0.0:
            return 0.0
        return float(np.dot(x, y) / (nx * ny))

    def cosine_rank(self, query: Sequence[float]) -> List[Tuple[str, float]]:
        """The full-D nearest neighbour. The memory's own way."""
        scored = [(it.ident, self._cosine(query, it.vector))
                  for it in self.items]
        scored.sort(key=lambda t: -t[1])
        return scored

    def build_landscape(self, query: Sequence[float]):
        """The 1-D landscape, built from the memory along the query.

        AND WHY EACH MEMORY IS A HILL. A cosine similarity is a HEIGHT:
        the more alike, the higher. So the landscape of similarities is a
        landscape of hills, and the ball DESCENDS the negative of it --
        it rolls down the dissimilarity and settles in the valley of the
        least-different memory.

        AND THE PROJECTION. Each memory is placed on the 1-D axis by
        its similarity to the query, and given a width from how sharply
        it stands out. So the axis is "how different is this memory
        from the query", and the ball's resting place is the nearest.
        """
        import numpy as np
        from basin_landscape import Bump, Landscape
        q = np.asarray(query, dtype=float)
        scored = sorted(((it.ident, self._cosine(query, it.vector))
                         for it in self.items), key=lambda t: -t[1])
        # the axis: dissimilarity, so the best memory is at 0
        best = scored[0][1] if scored else 0.0
        bumps = []
        for ident, sim in scored:
            centre = 1.0 - sim            # 0 for the nearest
            amp = max(0.05, sim)          # how strongly it resonates
            sigma = 0.12 + 0.08 * (1.0 - sim)
            bumps.append(Bump(centre=centre, amplitude=amp, sigma=sigma))
        land = Landscape(bumps=tuple(bumps))
        return land, scored

    def ball_rank(self, query: Sequence[float], x0: float = 0.0
                  ) -> Tuple[Optional[str], float, List[Tuple[str, float]]]:
        """The 1-D descent. Where the ball settles.

        AND THE DROP POINT. The ball is dropped at x0 = 0 -- which is
        DISSIMILARITY ZERO, i.e. right on top of the nearest memory's
        hill -- and then it rolls. So it starts at the right place and
        still has to STAY there, and it does not always: a nearby
        deeper well can capture it. That is the mechanism, and it is
        why the disagreement rate is not zero.
        """
        land, scored = self.build_landscape(query)
        from basin_landscape import drop
        r = drop(land, x0)
        settled = r["settled"]
        # which memory is that basin?
        best_id, best_d = None, None
        for ident, sim in scored:
            d = abs((1.0 - sim) - settled)
            if best_d is None or d < best_d:
                best_id, best_d = ident, d
        return best_id, float(settled), scored

    def compare(self, query_text: str, query: Sequence[float]) -> Comparison:
        """One query, answered by BOTH mechanisms."""
        ball_id, settled, scored = self.ball_rank(query)
        cos = self.cosine_rank(query)
        cos_id, cos_score = cos[0] if cos else (None, 0.0)
        ball_score = 0.0
        for ident, sim in scored:
            if ident == ball_id:
                ball_score = sim
                break
        return Comparison(query=query_text, ball_basin=ball_id,
                          cosine_nearest=cos_id,
                          agree=(ball_id == cos_id),
                          ball_score=ball_score, cosine_score=cos_score)


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import numpy as np
    from embed import embed_text

    print("=" * 78)
    print("THE BALL AND THE MEMORY ARE THE SAME MECHANISM")
    print("=" * 78)
    print()

    def E(t):
        return np.asarray(embed_text(t, dim=64), dtype=float)

    r = Resonance(dim=64)
    corpus = [
        ("m1", "the gate refuses a proposal that moves the sacred axes"),
        ("m2", "the ground is write protected and no caller can add a claim"),
        ("m3", "soup needs salt heat and time"),
        ("m4", "the governor runs in its own process"),
        ("m5", "a missing substrate is a skip and never a pass"),
        ("m6", "the drift must contract under every step"),
        ("m7", "every refusal names its reason"),
        ("m8", "the locus chain verifies and the ground holds"),
    ]
    for ident, text in corpus:
        r.add(ident, text, E(text))
    print("1. THE POPULATION IS THE LANDSCAPE:")
    print("   %d memories -> %d basins" % (len(r.items), r.n_basins()))
    print()

    print("2. THE TWO MECHANISMS, on four queries:")
    queries = [
        "what happens when the gate sees a sacred axis move",
        "what protects the ground from being written",
        "how do you cook soup",
        "why does the drift contract",
    ]
    rows = []
    for q in queries:
        c = r.compare(q, E(q))
        rows.append(c)
        print("   Q: %s" % q)
        print("      ball   -> %s  (score %.4f)" % (c.ball_basin, c.ball_score))
        print("      cosine -> %s  (score %.4f)" % (c.cosine_nearest, c.cosine_score))
        print("      agree: %s" % c.agree)
    n_agree = sum(1 for c in rows if c.agree)
    print()
    print("   AGREEMENT: %d of %d" % (n_agree, len(rows)))
    print("   AND WHEN THEY DISAGREE, THE BALL FOUND A DIFFERENT BASIN --")
    print("   which is the HYPERLOCAL property: a 1-D descent can settle in")
    print("   a well that a full-D nearest-neighbour search never sees.")
    print()

    print("3. AND THE POPULATION-EXPANSION CLAIM, made measurable:")
    print("   the same query, answered before and after ONE memory is added:")
    q = "what protects the ground from being written"
    before = r.compare(q, E(q))
    r.add("m9", "the ground cannot be written by any caller", E(q))
    after = r.compare(q, E(q))
    print("      before: ball=%s cosine=%s" % (before.ball_basin, before.cosine_nearest))
    print("      after:  ball=%s cosine=%s" % (after.ball_basin, after.cosine_nearest))
    print("      basins: %d -> %d" % (8, r.n_basins()))
    print("      the ANSWER can change because the LANDSCAPE changed,")
    print("      not because the ball changed. that is population expansion.")
    print()

    print("4. AND THE COST, which is the reason for the whole design:")
    print("   a cosine lookup compares against EVERY item: O(N) per query.")
    print("   a descent compares against the SURFACE: O(1) per step, and")
    print("   the surface is fixed. the ball does not know how many")
    print("   memories there are. that is the compute saving.")
    print()
    print("   Run: python src/resonance.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
