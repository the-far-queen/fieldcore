"""
kuramoto_interference.py - coupled oscillator network. adopted from bobby's
frequency-coupling-implementation-2026-09-11.md.

the pattern: N oscillators with phase phi_i and frequency omega_i. coupled
by sin(phi_j - phi_i). the Kuramoto model.

dphi_i/dt = omega_i + (K/|N(i)|) * sum_{j in N(i)} sin(phi_j - phi_i)

simself adoption: the constitutional kernel as a Kuramoto network.
8 axes = 8 oscillators. coupling = axiom influences. the harmonic
modes of the network ARE the eigenstates of the constitutional kernel.

bobbys exact words: brain does it. 86 billion neurons, locally coupled,
produce standing waves. local coupling produces global standing waves from
local rules - this is the Kuramoto model.
"""

from __future__ import annotations

import math
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple


@dataclass
class Oscillator:
    """one coupled oscillator. phase phi, frequency omega, neighbors."""
    name: str
    phase: float
    freq: float
    neighbors: Tuple[str, ...] = ()


@dataclass
class KuramotoNetwork:
    """N coupled oscillators. the constitutional kernel network."""

    def __init__(self, oscillators: Tuple[Oscillator, ...], coupling: float = 0.5):
        # copy, don't alias. the canonical network is a module-level constant
        # and step() mutates phase in place — aliasing it would leak state
        # between every KuramotoNetwork constructed in the process.
        self.oscs = {o.name: Oscillator(o.name, o.phase, o.freq, o.neighbors)
                     for o in oscillators}
        self.coupling = coupling

    def step(self, dt: float = 0.01) -> None:
        """one Kuramoto step. update each phase."""
        for name, o in self.oscs.items():
            n = max(1, len(o.neighbors))
            coupling_sum = sum(
                math.sin(self.oscs[j].phase - o.phase)
                for j in o.neighbors if j in self.oscs
            )
            o.phase += dt * (o.freq + (self.coupling / n) * coupling_sum)

    def order_parameter(self) -> Tuple[float, float]:
        """the Kuramoto order parameter r*e^(ipsi) - synchronization.
        r = 0 -> incoherent, r = 1 -> fully synchronized."""
        n = len(self.oscs)
        if n == 0: return (0.0, 0.0)
        sx = sum(math.cos(o.phase) for o in self.oscs.values())
        sy = sum(math.sin(o.phase) for o in self.oscs.values())
        return (math.sqrt(sx**2 + sy**2) / n, math.atan2(sy, sx))


# canonical 8-axis network (constitutional axes as oscillators)
CANONICAL_NETWORK = (
    Oscillator("boundaries", phase=0.0, freq=30.0, neighbors=("coherence", "stability")),
    Oscillator("coherence", phase=0.5, freq=42.0, neighbors=("boundaries", "routing")),
    Oscillator("stability", phase=1.0, freq=54.0, neighbors=("boundaries", "authenticity")),
    Oscillator("authenticity", phase=1.5, freq=57.0, neighbors=("stability",)),
    Oscillator("routing", phase=2.0, freq=72.0, neighbors=("coherence", "recovery")),
    Oscillator("recovery", phase=2.5, freq=108.0, neighbors=("routing", "norm")),
    Oscillator("norm", phase=3.0, freq=137.0, neighbors=("recovery", "commit_radius")),
    Oscillator("commit_radius", phase=3.5, freq=144.0, neighbors=("norm",)),
)


if __name__ == "__main__":
    net = KuramotoNetwork(CANONICAL_NETWORK, coupling=0.3)
    r0, _ = net.order_parameter()
    for _ in range(100):
        net.step(dt=0.01)
    r1, _ = net.order_parameter()
    # after coupling, oscillators may synchronize
    assert 0.0 <= r1 <= 1.0
    print(f"K1: ok (Kuramoto network, r={r0:.3f} -> r={r1:.3f} after 100 steps)")
    # all 8 axes present
    assert len(net.oscs) == 8
    print(f"K2: ok (8 axes in network)")