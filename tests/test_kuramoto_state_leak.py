"""
test_kuramoto_state_leak.py — regression tests for the Kuramoto network.

Two bugs found and fixed on 2026-10-06:

1. STATE LEAK. KuramotoNetwork aliased the module-level CANONICAL_NETWORK
   tuple of mutable Oscillator dataclasses and step() mutated phase in
   place. Every network built in a process started from whatever phase
   the previous network left behind, so r0 differed run to run and no
   measurement was reproducible. Fixed by copying each Oscillator.

2. NYQUIST ALIASING. dt=0.001 against a 144 Hz axis (~905 rad/s) pushes
   the leapfrog integrator past its stability window; the apparent
   "synchronization" is numerical garbage. At dt = pi/400 the network
   frequency-locks cleanly across K in [160, 280].

The load-bearing property is frequency LOCKING: all 8 axes converge to a
single angular velocity (sd -> 0). r is NOT the right test — r is
non-monotonic in K and oscillates.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kuramoto_interference import CANONICAL_NETWORK, KuramotoNetwork

DT_STABLE = math.pi / 400.0


def _measure(K, steps=4000, dt=DT_STABLE):
    """run to steady state, then measure per-axis instantaneous omega."""
    net = KuramotoNetwork(CANONICAL_NETWORK, coupling=K)
    for _ in range(steps):
        net.step(dt=dt)
    p1 = {n: o.phase for n, o in net.oscs.items()}
    for _ in range(steps):
        net.step(dt=dt)
    p2 = {n: o.phase for n, o in net.oscs.items()}
    inst = {n: ((p2[n] - p1[n] + math.pi) % (2 * math.pi) - math.pi) / dt
            for n in p1}
    mean_w = sum(inst.values()) / len(inst)
    sd_w = math.sqrt(sum((v - mean_w) ** 2 for v in inst.values()) / len(inst))
    return mean_w, sd_w


def test_kl_1_no_state_leak():
    """two networks built from the constant start from identical state."""
    # measure r BEFORE stepping either network: stepping A must not move
    # what a fresh B starts from.
    a = KuramotoNetwork(CANONICAL_NETWORK, coupling=0.3)
    ra0, _ = a.order_parameter()
    b = KuramotoNetwork(CANONICAL_NETWORK, coupling=0.3)
    rb0, _ = b.order_parameter()
    assert abs(ra0 - rb0) < 1e-12, (
        f"fresh networks disagree: A r0={ra0:.6f}, B r0={rb0:.6f}"
    )
    # now advance A hard, and confirm a third fresh network is unaffected
    for _ in range(500):
        a.step(dt=0.001)
    c = KuramotoNetwork(CANONICAL_NETWORK, coupling=0.3)
    rc0, _ = c.order_parameter()
    assert abs(rc0 - rb0) < 1e-12, (
        f"state leaked: stepping A moved the constant. "
        f"fresh r0 {rb0:.6f} -> {rc0:.6f}"
    )


def test_kl_2_canonical_not_mutated():
    """stepping one network must not move the module-level constant."""
    before = [o.phase for o in CANONICAL_NETWORK]
    net = KuramotoNetwork(CANONICAL_NETWORK, coupling=200.0)
    for _ in range(2000):
        net.step(dt=DT_STABLE)
    after = [o.phase for o in CANONICAL_NETWORK]
    assert before == after, "CANONICAL_NETWORK was mutated in place"


def test_kl_3_locks_at_stable_dt():
    """K=200 at a stable dt: all 8 axes reach one angular velocity."""
    mean_w, sd_w = _measure(200.0)
    assert sd_w < 1.0, f"no frequency lock at K=200: sd(omega)={sd_w:.4f}"
    assert 0.0 <= sd_w <= 1.0


def test_kl_4_lock_survives_step_count():
    """the lock is not an artifact of one particular step count."""
    for steps in (2000, 4000, 8000):
        _, sd_w = _measure(200.0, steps=steps)
        assert sd_w < 1.0, f"lock lost at steps={steps}: sd={sd_w:.4f}"


def test_kl_5_lock_survives_coupling_sweep():
    """locking holds across the K window, not just at one point."""
    for K in (160.0, 200.0, 240.0, 280.0):
        _, sd_w = _measure(K, steps=3000)
        assert sd_w < 1.0, f"lock lost at K={K}: sd={sd_w:.4f}"


def test_kl_6_order_parameter_bounded():
    """r stays a valid order parameter under every coupling tested."""
    for K in (0.0, 0.3, 10.0, 200.0, 400.0):
        net = KuramotoNetwork(CANONICAL_NETWORK, coupling=K)
        for _ in range(500):
            net.step(dt=DT_STABLE)
        r, _ = net.order_parameter()
        assert 0.0 <= r <= 1.0, f"r out of range at K={K}: {r}"


if __name__ == "__main__":
    test_kl_1_no_state_leak()
    print("KL.1: ok (no state leak between networks)")
    test_kl_2_canonical_not_mutated()
    print("KL.2: ok (CANONICAL_NETWORK not mutated)")
    test_kl_3_locks_at_stable_dt()
    print("KL.3: ok (frequency lock at K=200)")
    test_kl_4_lock_survives_step_count()
    print("KL.4: ok (lock robust to step count)")
    test_kl_5_lock_survives_coupling_sweep()
    print("KL.5: ok (lock robust across K)")
    test_kl_6_order_parameter_bounded()
    print("KL.6: ok (r bounded)")
    print("\nALL KURAMOTO REGRESSION TESTS PASS (KL.1..KL.6)")
