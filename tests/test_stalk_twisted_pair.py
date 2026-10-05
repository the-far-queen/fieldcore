"""
test_stalk_twisted_pair.py - tests for the electronic communication substrate.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from stalk_twisted_pair import (
    StalkPair, CrossMember, StalkNetwork, InterferencePattern,
)


def test_tw1_differential_signal():
    """differential_signal = a - b. common-mode = (a + b)/2."""
    p = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.3, sheath=False)
    assert p.differential_signal(1.0, 0.5) == 0.5
    assert p.common_mode(1.0, 0.5) == 0.75
    print("T1: ok (differential + common-mode)")


def test_tw2_variable_girths_increase_snr():
    """different girths (bobby's load-bearing detail) increase SNR by ~4 dB."""
    p_same = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.3, sheath=False)
    p_diff = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.35, sheath=False)
    assert p_diff.snr_improvement_db() > p_same.snr_improvement_db()
    print(f"T2: ok (variable girths: same={p_same.snr_improvement_db():.0f}dB, diff={p_diff.snr_improvement_db():.0f}dB)")


def test_tw3_sheath_increases_snr():
    """sheathing the pair increases SNR by ~15 dB."""
    p_bare = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.3, sheath=False)
    p_sheath = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.3, sheath=True)
    assert p_sheath.snr_improvement_db() > p_bare.snr_improvement_db()
    print(f"T3: ok (sheath: bare={p_bare.snr_improvement_db():.0f}dB, sheath={p_sheath.snr_improvement_db():.0f}dB)")


def test_tw4_cross_member_impedance_match():
    """perfectly matched cross-member has mismatch ratio 1.0."""
    cm = CrossMember(
        pair_a=StalkPair("a", "b", 1, 1, 0.3, 0.3),
        pair_b=StalkPair("c", "d", 1, 1, 0.3, 0.3),
        length=0.1, impedance_a=50.0, impedance_b=50.0,
    )
    assert cm.impedance_mismatch_ratio() == 1.0
    print(f"T4: ok (perfect impedance match: 50/50 = 1.0)")


def test_tw5_cross_member_mismatch():
    """mismatched impedance causes interference (bobby's load-bearing concern)."""
    cm = CrossMember(
        pair_a=StalkPair("a", "b", 1, 1, 0.3, 0.3),
        pair_b=StalkPair("c", "d", 1, 1, 0.3, 0.3),
        length=0.1, impedance_a=75.0, impedance_b=50.0,
    )
    assert cm.impedance_mismatch_ratio() == 1.5
    print(f"T5: ok (mismatch 75/50 = 1.5 — causes interference)")


def test_tw6_network_min_snr():
    """the network's SNR is the min over all pairs."""
    p_good = StalkPair("a", "b", 2.0, 1.0, 0.3, 0.32, sheath=True)
    p_bad = StalkPair("c", "d", 2.0, 1.0, 0.3, 0.3, sheath=False)
    net = StalkNetwork()
    net.add_pair(p_good)
    net.add_pair(p_bad)
    expected_min = min(p_good.snr_improvement_db(), p_bad.snr_improvement_db())
    assert net.total_snr_db() == expected_min
    print(f"T6: ok (network min SNR = {net.total_snr_db():.0f}dB)")


def test_tw7_interference_pattern_bpsk():
    """interference pattern encodes bits via BPSK phase modulation."""
    interf = InterferencePattern(stalks=4, frequency=137.0)
    bits = [0, 1, 1, 0]
    phases = interf.encode(bits)
    assert phases[0] == 0.0  # bit 0 -> phase 0
    assert phases[1] == math.pi  # bit 1 -> phase pi
    # sample at t=0
    amps = interf.sample(t=0.0, phase_offsets=phases)
    # bit 0: sin(0+0) = 0; bit 1: sin(0+pi) = 0 (sine of pi = 0!)
    # better: sample at t = pi/(4*freq) -> quarter period
    amps_quarter = interf.sample(t=1.0 / (4 * 137.0), phase_offsets=phases)
    # bit 0: sin(pi/2) = 1; bit 1: sin(pi/2+pi) = -1
    assert abs(amps_quarter[0] - 1.0) < 1e-6  # bit 0 ~ +1
    assert abs(amps_quarter[1] - (-1.0)) < 1e-6  # bit 1 ~ -1
    print(f"T7: ok (BPSK: bit 0 = +1, bit 1 = -1)")


def test_tw8_interference_8_stalks_at_137():
    """8 stalks at f137 = the constitutional substrate."""
    interf = InterferencePattern(stalks=8, frequency=137.0)
    phases = interf.encode([0, 1, 1, 0, 1, 0, 0, 1])
    amps = interf.sample(t=1.0 / (4 * 137.0), phase_offsets=phases)
    # 8 amplitudes, all in [-1, 1]
    assert len(amps) == 8
    assert all(-1 <= a <= 1 for a in amps)
    # bit 0 at stalk 0 -> +1; bit 1 at stalk 1 -> -1
    assert abs(amps[0] - 1.0) < 1e-6
    assert abs(amps[1] - (-1.0)) < 1e-6
    print(f"T8: ok (8 stalks at f137 BPSK: amplitudes {amps})")


def main():
    test_tw1_differential_signal()
    test_tw2_variable_girths_increase_snr()
    test_tw3_sheath_increases_snr()
    test_tw4_cross_member_impedance_match()
    test_tw5_cross_member_mismatch()
    test_tw6_network_min_snr()
    test_tw7_interference_pattern_bpsk()
    test_tw8_interference_8_stalks_at_137()
    print("\\nALL TWISTED PAIR TESTS PASS (TW1..TW8)")


if __name__ == "__main__":
    main()