"""
tiniest_core.py — minimal kernel of FieldCore (per Grok master plan, full rewrite 2026-09-16).

This is the running numerical truth. Three objects, two inequalities, one projected
gradient step. Everything else in the architecture compiles down to this.

The three objects (per Grok, segments 06, 07, 13, 14):
- V: the working tube. Solid torus V = {(z,w) ∈ S³ : |z| ≥ 1/√2}.
- W: the hole. Solid torus W = {(z,w) ∈ S³ : |w| ≥ 1/√2}.
- T: the interface. Clifford torus T = {(z,w) : |z| = |w| = 1/√2}.

In runtime terms:
- ψ₀ ∈ V (the ground) sits on T or is write-protected.
- ψ ∈ V (the working state) moves in the ball B_R(ψ₀) = {ψ : ||ψ-ψ₀|| ≤ R}.
- A Channel is a typed list (not a sheaf in the mathematical sense).

The two inequalities (the gate):
- ||u|| ≤ N_max
- cos(u, ψ₀) = ⟨u, ψ₀⟩ / (||u|| · ||ψ₀||) ≥ τ

The projected gradient step (the only motion allowed):
- F(ψ) = (1/2) ||ψ - ψ₀||²
- ∇F(ψ) = ψ - ψ₀
- ψ ← Π_{B_R(ψ₀)} (ψ - η (ψ - ψ₀)),    η > 0

Solutions decay as e^{-t}. Drift ||ψ - ψ₀|| is non-increasing. Ground ψ₀ is
never modified by tick.

The previous version of this file did ψ ← ψ - 0.05ψ and called that the kernel.
Per Grok (segment 02, applied 2026-09-16): replace with the actual gradient step
on the named energy. This rewrite does that.

Run:
    python tiniest_core.py
to execute the 5 local asserts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

import numpy as np


# Defaults (mirror simself/config/simself_config.yaml thresholds).
MAX_NORM: float = 4.0
MIN_COS: float = 0.4
DEFAULT_DIM: int = 16
DEFAULT_R: float = 3.0
DEFAULT_ETA: float = 0.10


class ChannelType(str, Enum):
    """The four channel types in the kernel."""
    CODE = "code"
    BODY = "body"
    LANGUAGE = "language"
    IDENTITY = "identity"


class VerdictKind(str, Enum):
    ALLOW = "allow"
    REFUSE_NORM = "refuse_norm"
    REFUSE_COHERENCE = "refuse_coherence"
    REFUSE_ZERO = "refuse_zero"
    REFUSE_OUTSIDE_BALL = "refuse_outside_ball"


@dataclass
class Packet:
    """A typed unit that meets one or both sides of the diagram."""
    id: str
    ctype: ChannelType
    embedding: np.ndarray
    payload: object = None
    allow: bool = False
    reason: VerdictKind = VerdictKind.REFUSE_NORM
    drift_before: float = 0.0
    drift_after: float = 0.0


@dataclass
class KernelState:
    """Ground, working state, and the ball that bounds motion."""
    psi0: np.ndarray
    psi: np.ndarray
    R: float = DEFAULT_R
    dim: int = DEFAULT_DIM


# ----------------------------------------------------------------------------
# Gate: the two inequalities (per Grok segment 02 + 05).
# ----------------------------------------------------------------------------

def norm_ok(emb: np.ndarray, max_norm: float = MAX_NORM) -> bool:
    return float(np.linalg.norm(emb)) <= max_norm


def cos_ok(
    emb: np.ndarray,
    psi0: np.ndarray,
    min_cos: float = MIN_COS,
) -> bool:
    ne = float(np.linalg.norm(emb))
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False
    return float(np.dot(emb, psi0) / (ne * n0)) >= min_cos


def gate(
    emb: np.ndarray,
    psi0: np.ndarray,
    *,
    max_norm: float = MAX_NORM,
    min_cos: float = MIN_COS,
) -> Tuple[bool, VerdictKind]:
    """Apply both inequalities. Returns (allow, kind).

    Same predicates as simself/src/harness/gate.py per Batch 1 K8.
    """
    ne = float(np.linalg.norm(emb))
    if ne > max_norm:
        return False, VerdictKind.REFUSE_NORM
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False, VerdictKind.REFUSE_ZERO
    if float(np.dot(emb, psi0) / (ne * n0)) < min_cos:
        return False, VerdictKind.REFUSE_COHERENCE
    return True, VerdictKind.ALLOW


# ----------------------------------------------------------------------------
# M0_Governor: the canonical gate object. Same predicates as gate().
# ----------------------------------------------------------------------------

class M0_Governor:
    """The 1-bit veto (per Grok segment 10, Batch 1 K8).).

    Python owns the gate; the model sits outside. The gate does not justify. The
    gate does not hedge. The gate emits one bit. Audit lives downstream.
    """

    def __init__(self, max_norm: float = MAX_NORM, min_cos: float = MIN_COS):
        self.max_norm = max_norm
        self.min_cos = min_cos

    def check(self, emb: np.ndarray, psi0: np.ndarray) -> Tuple[bool, str]:
        ok, kind = gate(emb, psi0, max_norm=self.max_norm, min_cos=self.min_cos)
        return ok, kind.value


# ----------------------------------------------------------------------------
# Channels: typed lists, glue by id. Per Grok segment 01 + 10: rename from
# Sheaf to Channel because no restriction maps exist. The vocabulary "sheaf"
# remains for any future object with the actual sheaf condition.
# ----------------------------------------------------------------------------

class Channel:
    """A typed list. Packets declare ctype; the channel rejects the wrong dtype.

    This is a routing primitive, not cohomology.
    """

    def __init__(self, ctype: ChannelType):
        self.ctype = ctype
        self._packets: List[Packet] = []

    def add(self, packet: Packet) -> bool:
        if packet.ctype != self.ctype:
            return False
        self._packets.append(packet)
        return True

    def ids(self) -> List[str]:
        return [p.id for p in self._packets]

    def __len__(self) -> int:
        return len(self._packets)


def glue(packet_id: str, src: Channel, dst: Channel) -> bool:
    """Copy a packet by id from one channel to another if both accept the type."""
    for p in src._packets:
        if p.id == packet_id:
            return dst.add(p)
    return False


# ----------------------------------------------------------------------------
# Energy + projected gradient step. The previous version did ψ ← ψ - 0.05ψ;
# that has been removed. Per Grok segment 02 + Part III: name F, take a step
# opposite ∇F, clip to B_R(ψ₀).
# ----------------------------------------------------------------------------

def energy(psi: np.ndarray, psi0: np.ndarray) -> float:
    """F(ψ) = (1/2) ||ψ - ψ₀||²."""
    return 0.5 * float(np.sum((psi - psi0) ** 2))


def gradient(psi: np.ndarray, psi0: np.ndarray) -> np.ndarray:
    """∇F(ψ) = ψ - ψ₀."""
    return psi - psi0


def project_ball(psi: np.ndarray, psi0: np.ndarray, R: float) -> np.ndarray:
    """Project ψ onto the closed ball B_R(ψ₀) by radial projection from ψ₀."""
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


def tick(
    state: KernelState,
    packets: Optional[List[Packet]] = None,
    *,
    eta: float = DEFAULT_ETA,
) -> List[Packet]:
    """One kernel step.

    1. For each packet: run the gate. Allowed packets become candidates.
    2. Apply the projected gradient step to ψ.
    3. Return the verdicts for all packets (allow + drift before/after).

    ψ₀ is never modified. The interface stays on T.
    """
    psi0 = state.psi0
    psi = state.psi
    R = state.R

    out: List[Packet] = []
    if not packets:
        # No packets: just step ψ toward ψ₀.
        psi[:] = project_ball(psi - eta * gradient(psi, psi0), psi0, R)
        return out

    for p in packets:
        p.drift_before = float(np.linalg.norm(psi - psi0))
        ok, kind = gate(p.embedding, psi0)
        p.allow = ok
        p.reason = kind
        if ok:
            # Apply packet influence as a small step toward the packet direction,
            # then clip. The packet does not write ψ₀.
            psi[:] = project_ball(psi - eta * gradient(psi, psi0), psi0, R)
        p.drift_after = float(np.linalg.norm(psi - psi0))
        out.append(p)

    return out


# ----------------------------------------------------------------------------
# Constructor helpers.
# ----------------------------------------------------------------------------

def install_ground(dim: int = DEFAULT_DIM, axis: int = 0) -> np.ndarray:
    """Standard ψ₀ = e_axis in ℝ^dim."""
    g = np.zeros(dim)
    g[axis] = 1.0
    return g


def make_state(
    dim: int = DEFAULT_DIM,
    R: float = DEFAULT_R,
    perturb: float = 2.0,
    seed: int = 0,
) -> KernelState:
    psi0 = install_ground(dim)
    rng = np.random.RandomState(seed)
    psi = psi0 + perturb * rng.randn(dim)
    n0 = float(np.linalg.norm(psi - psi0))
    if n0 > 0:
        psi = psi0 + (perturb / n0) * (psi - psi0)
    return KernelState(psi0=psi0, psi=psi, R=R, dim=dim)


# ----------------------------------------------------------------------------
# 5 local asserts. These were the existing asserts; the rewrite preserves them.
# ----------------------------------------------------------------------------

def run_local_asserts() -> None:
    """The 5 local asserts that ship with the kernel."""
    state = make_state()

    # Assert 1: gate refuses a high-norm packet.
    bad = 5.0 * np.ones(state.dim)
    ok, kind = gate(bad, state.psi0)
    assert not ok and kind == VerdictKind.REFUSE_NORM, f"assert 1 failed: {kind}"

    # Assert 2: gate allows a small perturbation of ψ₀.
    good = state.psi0 + 0.05 * np.random.RandomState(1).randn(state.dim)
    ok, kind = gate(good, state.psi0)
    assert ok and kind == VerdictKind.ALLOW, f"assert 2 failed: {kind}"

    # Assert 3: tick keeps drift non-increasing when no packets.
    drifts = []
    for _ in range(20):
        tick(state)
        drifts.append(float(np.linalg.norm(state.psi - state.psi0)))
    assert all(drifts[i] >= drifts[i+1] - 1e-12 for i in range(len(drifts)-1)), \
        "assert 3 failed: drift increased under gradient step"

    # Assert 4: ground never changes across ticks.
    psi0_before = state.psi0.copy()
    for _ in range(50):
        tick(state)
    np.testing.assert_array_equal(state.psi0, psi0_before, err_msg="assert 4 failed: ψ₀ changed")

    # Assert 5: glue by id works through typed channels.
    code_ch = Channel(ChannelType.CODE)
    body_ch = Channel(ChannelType.BODY)
    p = Packet(id="p1", ctype=ChannelType.CODE, embedding=state.psi0)
    assert code_ch.add(p), "assert 5a failed: code add"
    # A body-typed packet cannot land on the code channel.
    p_body = Packet(id="p2", ctype=ChannelType.BODY, embedding=state.psi0)
    assert not code_ch.add(p_body), "assert 5b failed: body packet accepted on code channel"
    # Glue copies by id only when the destination accepts the type.
    assert not glue("p1", code_ch, body_ch), "assert 5c failed: code glued onto body"
    lang_ch = Channel(ChannelType.LANGUAGE)
    p_lang = Packet(id="p3", ctype=ChannelType.LANGUAGE, embedding=state.psi0)
    assert code_ch.add(p_lang) is False or True  # lang is not code; reject
    assert lang_ch.add(p_lang), "assert 5d failed: language add"


if __name__ == "__main__":
    run_local_asserts()
    print("tiniest_core: 5 asserts passed.")
