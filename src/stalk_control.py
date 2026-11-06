"""
stalk_control.py — stalk data structure with measured coupling (per Grok master plan).

A stalk is a Hopf-fiber segment from the interface T into the working tube V:
fixed base point on S², varying signed distance from T. In runtime terms: a
record with an embedding, a list of cross-member links, and a status.

Per Grok (segment 02, applied 2026-09-16): the REINFORCE reward curve must
be reported. This file measures it.

Status values: candidate | admitted | committed | refused.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class Stalk:
    id: str
    embedding: np.ndarray
    status: str = "candidate"  # candidate | admitted | committed | refused
    support: List[str] = field(default_factory=list)  # cross-member ids


class StalkRegistry:
    """A small registry of stalks with reward-curve measurement."""

    def __init__(self):
        self.stalks: Dict[str, Stalk] = {}
        self._reward_log: List[Tuple[int, float, int, int]] = []
        # (tick, mean_reward, n_committed, n_refused)

    def add(self, stalk: Stalk) -> None:
        self.stalks[stalk.id] = stalk

    def commit(self, stalk_id: str) -> bool:
        if stalk_id not in self.stalks:
            return False
        if self.stalks[stalk_id].status == "refused":
            return False
        self.stalks[stalk_id].status = "committed"
        return True

    def refuse(self, stalk_id: str) -> bool:
        if stalk_id not in self.stalks:
            return False
        self.stalks[stalk_id].status = "refused"
        return True

    def reward_curve(self, ticks: int = 50) -> dict:
        """Measure the REINFORCE reward curve.

        For each tick we perturb each committed stalk's embedding slightly and
        measure the cosine to ψ₀. Reward = mean cosine to ψ₀ across committed
        stalks. This is a stand-in for the policy gradient signal.

        Returns a JSON-friendly summary.

        AND THE IMPORT THAT WAS HERE IS GONE, and that is the fix.
        This line used to read

            from .convergence_demo import ConcaveSurface  # reuse the small util

        and it raised `ImportError: attempted relative import with no
        known parent package` on EVERY call to this method. The reason
        is structural: fieldcore/src is a flat source root, not a
        package -- there is no `__init__.py` beside this file -- so a
        relative import has no parent package to resolve against and
        cannot work here at all.

        MEASURED 2026-11-06: the import also had no user. `ConcaveSurface`
        was never referenced below, so the line raised an exception and
        bought nothing. The psi0 proxy this method uses is the mean of
        the committed stalks' embeddings, computed below.

        The alternative was to make the import absolute
        (`from convergence_demo import ConcaveSurface`), which would
        resolve -- and would leave a dead import in place that implies
        a dependency the method does not have. Deleting it is the
        honest repair.
        """
        committed = [s for s in self.stalks.values() if s.status == "committed"]
        refused = [s for s in self.stalks.values() if s.status == "refused"]
        if not committed:
            return {"mean_reward": 0.0, "n_committed": 0, "n_refused": len(refused),
                    "curve": []}

        # ψ₀ proxy: mean of committed embeddings (a stand-in).
        psi0_proxy = np.mean([s.embedding for s in committed], axis=0)
        n0 = float(np.linalg.norm(psi0_proxy))
        if n0 > 0:
            psi0_proxy = psi0_proxy / n0

        rewards: List[float] = []
        rng = np.random.RandomState(0)
        for t in range(ticks):
            # small noise per tick
            noise = 0.01 * rng.randn(*psi0_proxy.shape)
            perturbed = psi0_proxy + noise
            cos_vals = []
            for s in committed:
                cos = float(np.dot(s.embedding, perturbed) /
                            ((np.linalg.norm(s.embedding) + 1e-9) *
                             (np.linalg.norm(perturbed) + 1e-9)))
                cos_vals.append(cos)
            mean_reward = float(np.mean(cos_vals))
            rewards.append(mean_reward)
            self._reward_log.append((t, mean_reward, len(committed), len(refused)))

        return {
            "mean_reward": float(np.mean(rewards)),
            "n_committed": len(committed),
            "n_refused": len(refused),
            "curve": rewards,
            "ticks": ticks,
        }

# concurrent touch

# concurrent touch 2
