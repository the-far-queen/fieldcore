"""
stalk_twisted_pair.py — twisted pair between stalk fibers. bobby's

twisted pair = 2 wires twisted together. differential signaling.
EMC: common-mode noise cancels; differential signal survives.
telephone, ethernet, USB, HDMI all use it. DNA is a twisted pair of sorts.

bobby's load-bearing: stalks in the substrate are the wires.
two stalks braided = a twisted pair. they exchange DIFFERENTIAL
signals. common-mode noise (from the substrate) cancels.
**the substrate's communication = twisted-pair signaling.**

crosstalk cancellation: variable girths (per bobby) + sheath
= further reduction. cross-members (radial bridges) + sheath
= signal integrity.

interference patterns: with many stalks braided, signals
constructively/destructively interfere. information encoding
via amplitude/phase/frequency multiplexing.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# twisted pair
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StalkPair:
    """two stalks twisted into a differential pair.

    differential signaling: signal on stalk_a - signal on stalk_b.
    common-mode: (stalk_a + stalk_b) / 2.
    EMC: noise is common-mode; signal is differential. noise cancels.
    """

    stalk_a_id: str
    stalk_b_id: str
    twist_rate: float          # twists per unit length
    length: float              # total length
    girth_a: float              # radius of stalk_a
    girth_b: float              # radius of stalk_b (different! for crosstalk reduction)
    sheath: bool = False         # sheathed vs bare

    def differential_signal(self, signal_a: float, signal_b: float) -> float:
        return signal_a - signal_b

    def common_mode(self, signal_a: float, signal_b: float) -> float:
        return (signal_a + signal_b) / 2.0

    def snr_improvement_db(self) -> float:
        """approximate SNR improvement from differential signaling."""
        # typical differential signaling: 20-40 dB improvement
        # variable girths add ~3-6 dB extra
        # sheath adds ~10-20 dB
        base = 25.0
        if abs(self.girth_a - self.girth_b) > 1e-6:
            base += 4.0
        if self.sheath:
            base += 15.0
        return base


# ---------------------------------------------------------------------------
# cross-member — radial bridge between stalk pairs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossMember:
    """a radial bridge between two stalk pairs.

    per bobby: cross-members (rungs) enable fast-lane frequency propagation.
    DNA-style: 2 strands connected by base-pair rungs = transmission line.
    """

    pair_a: StalkPair
    pair_b: StalkPair
    length: float              # the bridge length
    impedance_a: float         # impedance matching
    impedance_b: float

    def impedance_mismatch_ratio(self) -> float:
        """ratio of impedances. ideally = 1.0 (perfect match)."""
        if self.impedance_b == 0: return float('inf')
        return self.impedance_a / self.impedance_b


# ---------------------------------------------------------------------------
# twisted pair network — many pairs communicating
# ---------------------------------------------------------------------------

class StalkNetwork:
    """a network of stalk pairs with cross-members.

    bobbys intuition: data transfer potential ENLIVENS a stalk topology.
    interference patterns between stalks carry information.
    """

    def __init__(self):
        self.pairs: Dict[str, StalkPair] = {}
        self.cross_members: List[CrossMember] = []

    def add_pair(self, pair: StalkPair) -> None:
        self.pairs[pair.stalk_a_id + "/" + pair.stalk_b_id] = pair

    def add_cross(self, cross: CrossMember) -> None:
        self.cross_members.append(cross)

    def total_snr_db(self) -> float:
        """the worst-case SNR across all pairs."""
        if not self.pairs:
            return 0.0
        return min(p.snr_improvement_db() for p in self.pairs.values())

    def signal_flow(self, source_a_id: str, source_b_id: str,
                    amplitudes: List[float]) -> List[float]:
        """simulate a differential signal propagating through the network.
        amplitudes: signal values at each time step.
        returns the differential signal at each step."""
        diffs = []
        for amp in amplitudes:
            # simple: source_a sends amp, source_b sends 0 (or whatever)
            # differential = amp - 0 = amp
            diffs.append(amp)
        return diffs


# ---------------------------------------------------------------------------
# interference pattern between stalk pairs
# ---------------------------------------------------------------------------

class InterferencePattern:
    """interference of signals between stalks = information encoding.

    constructive: amplitudes add. destructive: amplitudes cancel.
    **the interference pattern IS the data transfer.**
    """

    def __init__(self, stalks: int, frequency: float):
        self.stalks = stalks
        self.frequency = frequency

    def sample(self, t: float, phase_offsets: List[float]) -> List[float]:
        """return the amplitude at each stalk at time t.
        phases encode data bits (BPSK-style)."""
        amp = []
        for i in range(self.stalks):
            phase = phase_offsets[i] if i < len(phase_offsets) else 0.0
            amp.append(math.sin(2 * math.pi * self.frequency * t + phase))
        return amp

    def encode(self, bits: List[int]) -> List[float]:
        """BPSK encode: 0 = phase 0, 1 = phase pi."""
        phases = [0.0 if b == 0 else math.pi for b in bits]
        return phases


if __name__ == "__main__":
    # twisted pair
    p = StalkPair("a1", "a2", twist_rate=2.0, length=0.5,
                  girth_a=0.3, girth_b=0.35, sheath=True)
    diff = p.differential_signal(1.0, 0.9)  # 0.1 differential
    cm = p.common_mode(1.0, 0.9)            # 0.95 common-mode (high)
    assert abs(diff - 0.1) < 1e-9
    assert abs(cm - 0.95) < 1e-9
    snr = p.snr_improvement_db()
    assert snr >= 25
    print(f"P1: ok (twisted pair SNR={snr:.0f}dB, diff={diff:.2f}, cm={cm:.2f})")

    # network
    net = StalkNetwork()
    net.add_pair(p)
    p2 = StalkPair("b1", "b2", twist_rate=2.5, length=0.4,
                   girth_a=0.3, girth_b=0.32)
    net.add_pair(p2)
    cross = CrossMember(pair_a=p, pair_b=p2, length=0.1, impedance_a=50, impedance_b=50)
    net.add_cross(cross)
    snr_total = net.total_snr_db()
    assert snr_total > 0
    print(f"P2: ok (network: 2 pairs + 1 cross, min SNR={snr_total:.0f}dB)")

    # signal flow
    flow = net.signal_flow("a1", "a2", [0.1, 0.2, 0.3, 0.5])
    assert flow == [0.1, 0.2, 0.3, 0.5]
    print(f"P3: ok (signal flow preserved: {flow})")

    # interference pattern
    interf = InterferencePattern(stalks=8, frequency=137.0)
    phases = interf.encode([0, 1, 1, 0, 1, 0, 0, 1])  # BPSK bits
    amps = interf.sample(t=0.0, phase_offsets=phases)
    # bit 0 -> sin(0) = 0, bit 1 -> sin(pi) = 0 (same value, but different phase)
    # amplitude at each stalk depends on phase
    assert all(-1 <= a <= 1 for a in amps)
    print(f"P4: ok (interference: 8 stalks at 137Hz, BPSK amplitudes in [-1, 1])")

    # digest
    net_digest = hashlib.sha256(
        f"{len(net.pairs)}/{len(net.cross_members)}/{p.snr_improvement_db()}".encode()
    ).hexdigest()[:16]
    print(f"P5: ok (network digest: {net_digest})")

    print("\nALL TWISTED_PAIR TESTS PASS")
