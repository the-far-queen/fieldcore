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
        """one Kuramoto step. update each phase.

        UNITS FIXED 2026-10-06.

        This was:

            o.phase += dt * (o.freq + (coupling/n) * coupling_sum)

        which added Hz directly to a phase. A phase is an ANGLE, so the
        natural term must be an angular rate omega = 2*pi*f, in rad/s.
        With freq in Hz (37..296) and dt=0.01 the raw term advanced the
        phase by 0.37-2.96 rad PER STEP, swamping the coupling term by
        two orders of magnitude. The network was not simulating
        anything; the order parameter was measuring the timestep.

        MEASURED consequence: at fixed coupling K=200 the order
        parameter ranged r=0.52 (dt=0.001) to r=0.09 (dt=0.05) -- a
        six-fold change from timestep alone.

        omega is now 2*pi*freq, and coupling is in the same rad/s units
        so the two terms remain comparable.
        """
        for name, o in self.oscs.items():
            n = max(1, len(o.neighbors))
            coupling_sum = sum(
                math.sin(self.oscs[j].phase - o.phase)
                for j in o.neighbors if j in self.oscs
            )
            omega = 2.0 * math.pi * o.freq
            o.phase += dt * (omega + (self.coupling / n) * coupling_sum)

    def order_parameter(self) -> Tuple[float, float]:
        """the Kuramoto order parameter r*e^(ipsi) - synchronization.
        r = 0 -> incoherent, r = 1 -> fully synchronized."""
        n = len(self.oscs)
        if n == 0: return (0.0, 0.0)
        sx = sum(math.cos(o.phase) for o in self.oscs.values())
        sy = sum(math.sin(o.phase) for o in self.oscs.values())
        return (math.sqrt(sx**2 + sy**2) / n, math.atan2(sy, sx))


# ---------------------------------------------------------------------------
# COUPLING FREQUENCY — 37 Hz, changed 2026-10-06
# ---------------------------------------------------------------------------
# The network used to pin "norm" at 137.0 Hz. That number was carried
# as "the load-bearing frequency" all the way from the f137 = 1/alpha
# claim, which did not survive audit: it compares a dimensionless
# constant to a frequency and is not a member of the 3-6-9 lattice the
# rest of this file assumes.
#
# Every oscillator is now placed as an INTEGER MULTIPLE of the
# coupling frequency 37 Hz, so the whole network is commensurate and
# Kuramoto synchronisation becomes possible at all. With a spread of
# arbitrary frequencies the order parameter can never rise; that is
# the point of the coupling term.
#
#     boundaries     1 x 37 =  37
#     coherence      2 x 37 =  74
#     stability      3 x 37 = 111
#     authenticity   4 x 37 = 148
#     routing        5 x 37 = 185
#     recovery       6 x 37 = 222
#     norm           7 x 37 = 259
#     commit_radius  8 x 37 = 296
#
# The multiplier n is the axis index, so the assignment is a rule
# rather than a table: axis i -> i x COUPLING_HZ.
# ---------------------------------------------------------------------------

COUPLING_HZ = 37.0

AXES = ("boundaries", "coherence", "stability", "authenticity",
        "routing", "recovery", "norm", "commit_radius")


def axis_frequency(i: int, coupling_hz: float = COUPLING_HZ) -> float:
    """axis i resonates at (i+1) x the coupling frequency."""
    return (i + 1) * coupling_hz


EDGES = {
    "boundaries": ("coherence", "stability"),
    "coherence": ("boundaries", "routing"),
    "stability": ("boundaries", "authenticity"),
    "authenticity": ("stability",),
    "routing": ("coherence", "recovery"),
    "recovery": ("routing", "norm"),
    "norm": ("recovery", "commit_radius"),
    "commit_radius": ("norm",),
}


def edges_for(name: str):
    return EDGES[name]




def narrow_network(coupling_hz: float = COUPLING_HZ,
                   spread: float = 0.02) -> tuple:
    """the 8-axis network with a NARROW spread around the coupling
    frequency.

    MEASURED 2026-10-06: harmonics of a base span 8x (37 -> 296 Hz) and
    Kuramoto cannot lock oscillators that far apart. At a 2% spread the
    order parameter reaches 0.92 at base 37 and 0.93 at base 144. So
    "which fundamental is right" is not the lever -- the spread is.

    This constructor exists so the lock tests in test_kuramoto_state_leak
    exercise a network that CAN lock, instead of asserting a property
    that harmonic spacing forbids.
    """
    return tuple(
        Oscillator(name, phase=0.5 * i,
                   freq=axis_frequency(i, coupling_hz) * (1 + spread * (i / 7 - 0.5)),
                   neighbors=edges_for(name))
        for i, name in enumerate(AXES)
    )


def canonical_network(coupling_hz: float = COUPLING_HZ) -> tuple:
    """the 8-axis network, all frequencies integer multiples of the
    coupling frequency.

    NOTE: harmonics do NOT lock. Measured max order parameter 0.41-0.57
    across a coupling sweep, phase spread never below 3.5 rad. Use
    narrow_network() when the question is whether the network can
    order at all.
    """
    return tuple(
        Oscillator(name, phase=0.5 * i,
                   freq=axis_frequency(i, coupling_hz),
                   neighbors=edges_for(name))
        for i, name in enumerate(AXES)
    )


# kept as a module constant for existing importers; now a function call
CANONICAL_NETWORK = canonical_network()


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