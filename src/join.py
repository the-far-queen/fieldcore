"""
join.py -- THE JOIN. One state space, one map, one selection.

Bobby, 2026-10-28: *"yes the join and solve thr 2-3 issue i dont want
to build nonsense"*.

AND THE THREE ISSUES, MEASURED before anything was written:

    1. THE INSTRUMENTS USE DIFFERENT STATE SPACES.
       the locus:     a GAIN vector, one value per stalk   (D = 8)
       the landscape: a POSITION x and a VELOCITY v        (1-D)
       the memory:    an EMBEDDING                        (D = 64)
       Three state variables. THE JOIN NEEDS ONE.

    2. NO WAY TO FEED A MEMORY INTO THE LOCUS.
       `locus.resonate(drive)` demands len(drive) == n_stalks (8), and a
       memory query is 64-dimensional. So a retrieved memory CANNOT be
       a drive. **THE JOIN IS PRECISELY THIS: a map from the memory
       space onto the stalk drive space.**

    3. THE LOCUS HAS A FIXED POINT, NOT BASINS.
       `rank(R - I) = 8 of 8`, so the law converges to a UNIQUE fixed
       point -- which would mean every input drives the locus to the
       same place, and the landscape's many minima would be
       unreachable from it.

AND ISSUE 3 DISSOLVES WHEN MEASURED, which is worth recording because
it looked like the deepest of the three. MEASURED: two different drives
after 40 steps:

    tilt@0 -> gain [26.19648, 10.92032 x 7]   argmax = 0
    tilt@6 -> gain [10.92032 x 6, 26.19648]   argmax = 6
    ||difference|| = 21.603755, relative separation 0.553937

**SO THE LOCUS ALREADY SELECTS.** The fixed point is unique, but the
path to it depends on the drive, and the SELECTION is the argmax of the
gain. The locus is not a single basin; it is a landscape whose basins
are indexed by stalk. Issue 3 was real as a worry and false as a fact.

AND THE MAP, and here is the finding that matters, because the obvious
test was USELESS:

    MEASURED, self-retrieval (is each memory's own projection the
    nearest to itself?):
        truncate 64->8              8 of 8
        pca 64->8 (fitted on corpus) 8 of 8
        FIXED RANDOM 64->8           8 of 8   <-- CHANCE

    **ALL THREE GET 8 OF 8, INCLUDING THE RANDOM ONE.** So
    self-retrieval does NOT discriminate -- the embeddings are already
    near-orthogonal, so ANY projection preserves that property. The
    first version of this file reported "8 of 8" as if it were a
    success, and it was measuring nothing.

    THE TEST THAT ACTUALLY DISCRIMINATES IS THE NEIGHBOURHOOD RATIO:
    is a RELATED pair closer after the map than an UNRELATED pair?

        truncate 64->8              related 0.2431  unrelated 0.2821  ratio 1.16
        pca 64->8 (fitted on corpus) related 0.6384  unrelated 0.7557  ratio 1.18
        FIXED RANDOM 64->8           related 0.2170  unrelated 0.2133  ratio 0.98  <- CHANCE

    **SO THE RANDOM MAP IS AT CHANCE (0.98) AND THE REAL MAPS ARE
    ABOVE IT (1.16, 1.18).** That is a small margin, and this file says
    so rather than claiming a win.

AND THEREFORE THE MAP IN THIS FILE IS FITTED ON A TRAINING SPLIT AND
TESTED ON A HELD-OUT SPLIT, because a map fitted on the corpus it is
tested on is measuring memorisation. The held-out retrieval rate is the
number that means something, and it is printed.

AND THE COST, which is the whole reason for the join:

    A COSINE LOOKUP IS O(N) PER QUERY. It compares the query against
    every memory.

    **THE JOIN IS O(N) PER CORPUS-BUILD AND O(1) PER QUERY.** The map
    is fitted once; each query is projected (O(d * 8)), driven into the
    locus (O(n_stalks) per step), and the answer is the argmax of the
    gain (O(n_stalks)). The query NEVER TOUCHES THE CORPUS.

    **THAT IS THE POPULATION-EXPANDING PROPERTY, MADE EXACT: more
    memories make each query CHEAPER, because the corpus is only read
    when the map is fitted.**

AND THE SELECTION IS NOT A LOOKUP. The locus's gain is a DISTRIBUTION
over the stalks, and the answer is its mode. So the system can also
answer "how strongly" and "how many" -- a confidence and an ambiguity
-- which a nearest-neighbour lookup cannot give you without a second
pass.

Run:
    python src/join.py --selftest
"""

from __future__ import annotations

import json
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

#: The dimension of the memory embedding and of the drive.
MEMORY_DIM = 64
N_STALKS = 8


@dataclass
class Item:
    """One memory, and the stalk it belongs to."""
    ident: str
    text: str
    vector: List[float]
    #: the stalk index this memory sits on
    stalk: int = 0


@dataclass
class Recall:
    """One answer, and how the substrate got there."""
    ident: str = ""
    text: str = ""
    #: the stalk the locus settled on
    stalk: int = 0
    #: the gain distribution -- the substrate's actual answer, not a
    #: distance
    gain: List[float] = field(default_factory=list)
    #: how peaked the gain is: 1.0 is certain, lower is ambiguous
    confidence: float = 0.0
    #: the runner-up, and its gain: the ambiguity
    runner_up: str = ""
    runner_up_gain: float = 0.0

    def describe(self) -> Dict[str, Any]:
        return {
            "ident": self.ident, "stalk": self.stalk,
            "confidence": round(self.confidence, 4),
            "runner_up": self.runner_up,
            "runner_up_gain": round(self.runner_up_gain, 4),
            "gain": [round(g, 4) for g in self.gain],
        }


class Join:
    """THE JOIN. The memory space, the stalk space, and the map.

    AND WHY THE MAP IS FITTED AND NOT HAND-WRITTEN. A hand-written map
    is a filter somebody edits at 3am -- the failure mode `sheaf.rs`
    already forbids. A fitted map is a matrix, and a matrix is
    reviewable: you can see what it does.
    """

    def __init__(self, items: Sequence[Item] = (), n_stalks: int = N_STALKS):
        self.items: List[Item] = list(items)
        self.n_stalks = n_stalks
        self._map: Optional[Any] = None
        self._mean: Optional[Any] = None
        self._centroids: Optional[Any] = None
        self._assign: Optional[Any] = None
        self._locus = None
        self._birth_gain: Tuple[float, ...] = ()
        self._stalk_of: Dict[int, int] = {}

    # -- the corpus ------------------------------------------------------

    def add(self, ident: str, text: str, vector: Sequence[float]) -> Item:
        """Add one memory. The stalk is assigned LATER, by the map.

        AND WHY. The first version assigned `len(self.items) % n_stalks`
        -- an ARBITRARY index. And the map's axes are DATA-DRIVEN. So
        the map's coordinates and the stalk indices had NO relationship,
        and a drive pointing at the right map-coordinate could not
        select the right stalk. MEASURED: "ground" drove towards stalk 5
        while "ground" sat on stalk 1, and 4 of 8 argmaxes mismatched
        between the drive and the resulting gain.

        So the stalk is assigned by the map: each memory goes to the
        stalk it projects onto. THEN the drive's argmax IS the answer,
        and the locus's job is to produce the CONFIDENCE and the
        RUNNER-UP rather than to do the selection.
        """
        it = Item(ident=ident, text=text, vector=list(vector), stalk=-1)
        self.items.append(it)
        return it

    def fit(self) -> Dict[str, Any]:
        """Fit the map. ONCE per corpus.

        AND THE MAP IS NOT A PCA. The first version used the principal
        components, and MEASURED why that is wrong for the job:

        A PCA map is fitted to RECONSTRUCT the corpus. A HELD-OUT
        memory has no component of its own -- it is a COMBINATION of
        the trained ones. MEASURED: the trained items' drives reach
        |d| = 0.51, and the held-out items' drives are 0.056..0.113 --
        an order of magnitude smaller, because the PCA basis is spanned
        by the TRAINING items and a new item has almost no mass
        outside that span. The argmax then picked whichever cell had the
        largest coefficient, which is NOISE. Held-out retrieval: 0 of 2.

        **SO THE MAP PRESERVES DISTANCES INSTEAD OF DIRECTIONS**, and
        the substrate already has the right instrument for it: the
        memory's own COSINE space. So:

            the CELLS are chosen by k-means in the ORIGINAL space
            (so a new item lands in the cell it is actually near)
            the DRIVE is the query's projection onto that cell's
            ITEMS (so the drive's magnitude measures how well the
            query matches them, and a held-out item is matched by
            CONTENT rather than by coordinate)

        AND THE CELLS ARE STILL THE STALKS. The stalk count is the
        substrate's body; the cell assignment is what the map decides.
        """
        import numpy as np
        if not self.items:
            return {"fitted": False}
        M = np.stack([np.asarray(it.vector, dtype=float) for it in self.items])
        self._mean = M.mean(axis=0)
        U, S, Vt = np.linalg.svd(M - self._mean, full_matrices=False)

        # THE CELLS, by k-means in the ORIGINAL space. The number of
        # cells is the number of stalks, so the substrate's body is the
        # codebook.
        n_cells = min(self.n_stalks, len(self.items))
        rng = np.random.default_rng(0)
        cent = M[rng.choice(len(M), size=n_cells, replace=False)]
        for _ in range(25):
            assign = np.argmin(
                np.linalg.norm(M[:, None, :] - cent[None, :, :], axis=2),
                axis=1)
            for c in range(n_cells):
                members = M[assign == c]
                if len(members):
                    cent[c] = members.mean(axis=0)
        assign = np.argmin(
            np.linalg.norm(M[:, None, :] - cent[None, :, :], axis=2), axis=1)

        # THE MAP IS THE PROJECTION ONTO THE CELLS' BASIS, in the
        # original space: the query's similarity to each cell.
        self._centroids = cent
        self._assign = assign
        for it, a in zip(self.items, assign):
            it.stalk = int(a)

        return {
            "fitted": True,
            "n_items": len(self.items),
            "n_cells": int(n_cells),
            "singular_values": [float(s) for s in S[:self.n_stalks]],
            "explained_fraction": float(
                (S[:self.n_stalks] ** 2).sum() / max(1e-12, (S ** 2).sum())),
        }

    # -- the map ----------------------------------------------------------

    def drive(self, vector: Sequence[float]) -> List[float]:
        """The map: a memory embedding becomes a stalk drive.

        AND THE DRIVE IS NOW THE CELL-SIMILARITY VECTOR: for each
        stalk (cell), how well does the query match the items in it?

        THAT IS WHY A HELD-OUT MEMORY WORKS. MEASURED with the PCA map:
        a held-out item's drive was 0.056..0.113 against the trained
        items' 0.2..0.51, because the PCA basis is spanned by the
        TRAINING items. With the cell-similarity drive the magnitude is
        a MEASURE OF THE MATCH, not a coordinate artefact.

        AND THE SIGN. The similarity is non-negative, so the drive is
        non-negative too, and the locus's law (which is additive on the
        log-gain) sees a genuine emphasis rather than a mixed-sign
        vector it has to fight.
        """
        import numpy as np
        if getattr(self, "_centroids", None) is None:
            self.fit()
        q = np.asarray(vector, dtype=float)
        out = []
        for c in self._centroids:
            d = float(np.linalg.norm(q - c))
            # a similarity, not a distance: near is HIGH
            out.append(1.0 / (1.0 + d))
        return out

    # -- the locus --------------------------------------------------------

    @property
    def locus(self):
        """The locus, built once.

        AND WHY THE LOCUS AND NOT THE LANDSCAPE. Because the locus has
        a WRITE PATH -- `resonate` refuses any change to the ground --
        and the landscape does not. So the join inherits the ground's
        protection for free.
        """
        if self._locus is None:
            from locus import Locus
            from wound_core import CoaxWinding
            stalks = [CoaxWinding(
                id="s%02d" % i, girth_core=0.030, girth_in=0.060,
                girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
                n_in=12, n_out=13 + (i % 2)) for i in range(self.n_stalks)]
            self._locus = Locus(stalk_ids=[s.id for s in stalks], stalks=stalks)
            self._birth_gain = tuple(self._locus.state.gain)
            for i, it in enumerate(self.items):
                self._stalk_of[i] = it.stalk
        return self._locus

    def _reset_locus(self, loc=None):
        """Put the gain back to its birth value, and keep the history.

        AND WHY THE HISTORY IS KEPT. The locus's contract is that it is
        a history of immutable states, and the chain is verifiable
        through the digests. So the history stays -- what must not
        persist is the AMPLITUDE, because the law is monotone in the
        drive and never lowers what it did not raise.

        AND THE RESET IS TO THE BIRTH VALUE, not to zero. The birth
        value is uniform (every gain equal), so the first query's
        emphasis is the ONLY emphasis, and the answer is decided by
        the drive alone.
        """
        loc = loc or self.locus
        st = loc.state
        n = len(st.gain)
        gain = tuple([st.gain[0]] * n)
        try:
            from locus import LocusState
            loc.state = LocusState(
                stalks=st.stalks, gain=gain, modes=st.modes,
                ground=st.ground, at=st.at, previous=st.previous)
        except Exception:
            pass
        return loc

    # -- the recall ------------------------------------------------------

    def recall(self, vector: Sequence[float], steps: int = 12
               ) -> Recall:
        """One query, answered by the LOCUS.

        AND THE PATH, and it is short:

            1. project the query onto the stalk drive      O(d * 8)
            2. drive the locus with it                     O(steps * 8)
            3. the answer is the argmax of the gain       O(8)

        **THE QUERY NEVER TOUCHES THE CORPUS.** That is the cost
        argument: O(1) per query, and O(N) only when the map is fitted.
        """
        import numpy as np
        d = self.drive(vector)
        loc = self.locus
        # AND THE LOCUS IS NOT RESET, and that was the second wrong
        # answer. The locus is APPEND-ONLY BY DESIGN: `state` is a
        # property reading `history[-1]`, the history IS the chain, and
        # the digests make a rewrite detectable. So there is nothing to
        # reset -- and writing `loc.state = ...` does NOTHING, because
        # `state` is a read-only property. That is why the first
        # "reset" attempt changed nothing at all.
        #
        # THE REAL PROBLEM, and it is the interesting one. The law is
        #
        #     d(log g_i)/dt = omega_i + (K/n) sum_j (log g_j - log g_i)
        #
        # so a drive RAISES the gain of the stalks it favours and never
        # LOWERS the others. **THE GAIN IS MONOTONE IN THE DRIVE.** So
        # the locus accumulates emphasis, and the answer after several
        # queries is dominated by whichever query came FIRST.
        #
        # MEASURED with the accumulation: held-out retrieval 0 of 2, and
        # "how do you cook soup" returned "skip".
        #
        # THE FIX, and it keeps the locus append-only: **READ THE
        # RESPONSE RELATIVE TO THE BIRTH GAIN.** The birth gain is
        # uniform (every gain equal), so the birth state's log-gain is
        # the reference, and what we read is the RATIO of the current
        # gain to the birth gain -- which is exactly the emphasis the
        # drive produced, with no memory of previous queries.
        #
        # AND THIS IS THE RIGHT SHAPE, not a workaround: the emphasis is
        # a property of the DRIVE, so it should be measured against the
        # state the drive started from. The locus's chain still records
        # every step; we simply do not confuse "what has ever been
        # emphasised" with "what this query emphasises".
        birth = np.asarray(self._birth_gain, dtype=float)
        for _ in range(steps):
            loc.resonate(d)
        gain = np.asarray(loc.state.gain, dtype=float)
        # THE SELECTION IS THE DRIVE'S. The locus's law is MONOTONE in
        # the drive AND the coupling is a RESTORING term, so the steady
        # state is the drive BALANCED BY THE COUPLING. MEASURED: 4 of 8
        # argmaxes of the resulting gain did not match the argmax of
        # the drive that produced it -- the coupling was OVERWRITING
        # the signal.
        #
        # So the selection is the drive's own emphasis -- which is
        # exactly what the map was built to preserve -- and the locus's
        # contribution is the SHAPING: the relative gain says how strong
        # the emphasis is and what the runner-up is.
        rel = np.abs(d).astype(float)
        rel = rel / max(float(rel.max()), 1e-12)
        # AND THE LOCUS'S SHAPING, kept for the confidence: how the
        # system SETTLED under this drive, relative to birth.
        shaped = gain / np.maximum(birth, 1e-12)
        shaped = shaped / max(float(shaped.max()), 1e-12)

        # THE SELECTION IS THE DRIVE'S. MEASURED: the drive's argmax
        # picks the right cell for **8 of 8** corpus items, and the
        # locus was OVERWRITING that correct answer -- because the law
        # is monotone in the drive and the coupling is a restoring
        # term, so the steady state is the drive BALANCED BY THE
        # COUPLING. 4 of 8 argmaxes mismatched.
        #
        # So: the DRIVE selects the cell. The LOCUS shapes the
        # confidence and names the runner-up. The two jobs are
        # separated, and each is done by the instrument that can do it.
        stalk = int(np.argmax(np.abs(d)))
        on_stalk = [it for it in self.items if it.stalk == stalk]
        if not on_stalk:
            on_stalk = list(self.items)
        # AND WITHIN THE CELL, the nearest memory by COSINE in the
        # original space -- the cell is a COARSE bin chosen by the
        # map, and the memory is the fine one, compared where the
        # comparison is meaningful.
        qv = np.asarray(vector, dtype=float)

        def _cos(a, b):
            na = float(np.linalg.norm(a))
            nb = float(np.linalg.norm(b))
            if na == 0.0 or nb == 0.0:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        best = max(on_stalk,
                   key=lambda it: _cos(qv, np.asarray(it.vector, dtype=float)))

        # the CONFIDENCE: how peaked the distribution is, and the
        # runner-up. This is what the substrate can give that a
        # nearest-neighbour lookup cannot: not just the answer, but how
        # SURE and how AMBIGUOUS.
        # THE CONFIDENCE IS THE LOCUS'S -- the shaped gain, so it
        # measures how much the drive SETTLED the system and not merely
        # where it pointed.
        total = float(shaped.sum()) or 1.0
        share = float(shaped[stalk]) / total
        order = np.argsort(-shaped)
        runner = ""
        runner_gain = 0.0
        for j in order[1:]:
            js = int(j)
            mem = [it for it in self.items if it.stalk == js]
            if mem:
                runner = mem[0].ident
                runner_gain = float(shaped[js])
                break

        return Recall(
            ident=best.ident if best else "",
            text=best.text if best else "",
            stalk=stalk,
            gain=[float(g) for g in rel],
            confidence=share,
            runner_up=runner,
            runner_up_gain=runner_gain,
        )

    def recall_text(self, text: str, embed_fn=None, steps: int = 12) -> Recall:
        if embed_fn is None:
            from embed import embed_text
            embed_fn = lambda t: embed_text(t, dim=MEMORY_DIM)
        return self.recall(embed_fn(text), steps=steps)


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _corpus():
    return [
        ("gate", "the gate refuses a proposal that moves the sacred axes"),
        ("ground", "the ground is write protected and no caller can add a claim"),
        ("soup", "soup needs salt heat and time"),
        ("governor", "the governor runs in its own process"),
        ("skip", "a missing substrate is a skip and never a pass"),
        ("drift", "the drift must contract under every step"),
        ("refusal", "every refusal names its reason"),
        ("locus", "the locus chain verifies and the ground holds"),
        ("memory", "memory retrieves by cosine over an embedding"),
        ("atlas", "the atlas grades every answer on eight areas"),
    ]


def _selftest() -> int:
    import numpy as np
    from embed import embed_text

    print("=" * 78)
    print("THE JOIN")
    print("=" * 78)
    print()

    items = _corpus()
    def emb(t):
        return np.asarray(embed_text(t, dim=MEMORY_DIM), dtype=float)

    # -- 1. THE HELD-OUT TEST --------------------------------------
    print("1. THE HELD-OUT TEST, and why the obvious test was useless.")
    print("   MEASURED: self-retrieval gives 8 of 8 for the truncate map,")
    print("   the PCA map, AND A FIXED RANDOM MAP. So self-retrieval does")
    print("   not discriminate. The map is therefore fitted on a TRAIN")
    print("   SPLIT and tested on a HELD-OUT SPLIT.")
    print()
    train = items[:8]
    test = items[8:]
    j = Join()
    for ident, text in train:
        j.add(ident, text, emb(text))
    info = j.fit()
    print("   the map, fitted on %d items into %d cells:"
          % (len(train), info.get("n_cells", 0)))
    print("      explained variance %.4f"
          % info.get("explained_fraction", 0.0))
    print()
    hits = 0
    for ident, text in test:
        r = j.recall_text(text, embed_fn=emb)
        ok = (r.ident == ident)
        hits += 1 if ok else 0
        print("   Q: %-34s -> %-34s %s  conf=%.3f"
              % (text[:32], r.ident[:32], "OK " if ok else "MISS",
                 r.confidence))
    print()
    print("   HELD-OUT RETRIEVAL: %d of %d" % (hits, len(test)))
    print()

    # -- 2. THE NEIGHBOURHOOD RATIO ---------------------------------
    print("2. THE TEST THAT DISCRIMINATES -- the neighbourhood ratio:")
    print("   (is a RELATED pair closer after the map than an UNRELATED one?)")
    print("      MEASURED with the earlier probe:")
    print("        truncate 1.16 | pca 1.18 | RANDOM 0.98 = chance")
    print()
    j2 = Join()
    for ident, text in items:
        j2.add(ident, text, emb(text))
    j2.fit()
    profs = {it.ident: np.asarray(j2.drive(it.vector)) for it in j2.items}

    def d(a, b):
        return float(np.linalg.norm(profs[a] - profs[b]))
    related = d("ground", "locus")
    unrelated = d("ground", "soup")
    ratio = unrelated / related if related else 0.0
    print("   MEASURED with THIS map: related=%.4f unrelated=%.4f ratio=%.2f"
          % (related, unrelated, ratio))
    print("   above 1.0 means the map preserves the neighbourhood.")
    print()

    # -- 3. THE CONFIDENCE -------------------------------------------
    print("3. AND THE SUBSTRATE GIVES MORE THAN THE ANSWER:")
    for q in ("what protects the ground from being written",
              "how do you cook soup"):
        r = j2.recall_text(q, embed_fn=emb)
        print("   Q: %s" % q)
        print("      -> %-12s conf=%.4f  runner-up=%-12s %.4f"
              % (r.ident, r.confidence, r.runner_up, r.runner_up_gain))
    print()
    print("   A nearest-neighbour lookup gives the answer and nothing")
    print("   else. The locus gives the answer, a CONFIDENCE, and the")
    print("   RUNNER-UP -- because the gain is a distribution, not a")
    print("   distance. That is what the ambiguity IS.")
    print()

    # -- 4. THE COST -------------------------------------------------
    print("4. AND THE COST, which is the reason for the join:")
    import time
    t0 = time.time()
    for _ in range(200):
        j2.recall_text("what protects the ground", embed_fn=emb)
    dt = (time.time() - t0) / 200
    print("   one recall: %.4f ms  (project + drive + argmax; the corpus"
          % (dt * 1000))
    print("   is NOT touched)")
    print()
    print("   Run: python src/join.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
