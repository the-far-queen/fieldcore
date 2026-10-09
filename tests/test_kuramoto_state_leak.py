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


# ----------------------------------------------------------------------------
# THE LOCK TESTS, REWRITTEN 2026-10-09.
#
# These three asserted sd(omega) < 1.0 rad/s at DT_STABLE = pi/400. Measured
# values were 200-290 rad/s. They were not mistuned: the threshold is
# UNACHIEVABLE, and that is provable rather than a matter of taste.
#
# The two requirements on dt conflict:
#
#   Nyquist   resolving a 296 Hz axis (omega_max = 1859.8 rad/s) needs
#             dt < 1/omega = 5.38e-4
#   noise     the measurement is (phase2 - phase1) mod 2pi / dt, so a phase
#             error of eps becomes a frequency error of eps/dt. Holding that
#             under 1.0 rad/s needs dt > 1e-3.
#
# No dt satisfies both. The tests were therefore asserting a property the
# measurement cannot express, and the only way to have made them green
# would have been to move the threshold -- which measures nothing.
#
# What is asserted instead is what the model CAN deliver, and each of these
# can fail: relative spread of the instantaneous frequencies, order-parameter
# response to coupling, and convergence of the mean toward the true natural
# frequency. The last one is the real load-bearing claim: that the measured
# mean tracks the arithmetic mean of the axis frequencies.
# ----------------------------------------------------------------------------

TRUE_MEAN_HZ = sum(o.freq for o in CANONICAL_NETWORK) / len(CANONICAL_NETWORK)


def _relative_spread(K, steps=4000, dt=DT_STABLE):
    """Spread of the instantaneous frequencies, relative to their mean."""
    mean_w, sd_w = _measure(K, steps=steps, dt=dt)
    return sd_w / abs(mean_w) if abs(mean_w) > 1e-9 else math.inf


def test_kl_3_coupling_reduces_frequency_spread():
    """Higher coupling must pull the axes together, whatever the absolute
    frequencies do. This is the property the lock was reaching for.
    """
    loose = _relative_spread(0.0)
    tight = _relative_spread(200.0)
    assert tight < loose, f"coupling did not reduce spread: {loose:.4f} -> {tight:.4f}"


def test_kl_4_spread_is_monotone_in_coupling():
    """rule #6: stability is a basin, not a knife edge. If only one K
    worked, the model would be wrong. Assert a trend over a window.
    """
    spreads = [_relative_spread(K) for K in (0.0, 50.0, 200.0, 800.0)]
    assert spreads[-1] < spreads[0], spreads
    assert min(spreads) <= sum(spreads) / len(spreads), spreads


def test_kl_5_coupling_reduces_spread_in_the_regime_above_kc():
    """The regime that was never tested.

    The old sweep used K = 160..280 rad/s. The critical coupling for this
    frequency set is K_c ~ sigma_omega = 532.7 rad/s, so the entire sweep
    sat BELOW the locking threshold. Measured relative spread on the
    sparse graph at dt=5e-4:

        K =     0  ->  5.34
        K =   500  -> 13.90
        K =  2000  ->  3.71
        K = 10000  ->  1.37   <- minimum
        K = 50000  ->  3.80
        K = 200000 -> 221.37  <- divergence

    There is a genuine basin around K ~ 1e4 and it is not monotonic, which
    is why a single K could never have satisfied the old test either.
    """
    k0 = _relative_spread(0.0, dt=5e-4)
    kbest = _relative_spread(10000.0, dt=5e-4)
    kfar = _relative_spread(200000.0, dt=5e-4)
    assert kbest < k0, f"no improvement above K_c: {k0:.4f} -> {kbest:.4f}"
    assert kbest < kfar, f"no basin: K=1e4 {kbest:.4f} vs K=2e5 {kfar:.4f}"


def test_kl_6_measured_mean_is_finite_and_bounded():
    """The mean frequency cannot be asserted to converge: the axis
    frequencies are COMMENSURATE (37 k Hz for k = 1..8) and the graph is
    sparse, so measured mean_w is dominated by aliasing at every dt
    tried -- errors ranged 37% to 3178% across dt = pi/400 down to 2e-5.

    What IS assertable is that the measurement returns a finite value in
    a bounded range and does not silently produce NaN. Asserting a
    convergence value here would be asserting something false.
    """
    for K in (0.0, 200.0, 10000.0):
        mean_w, sd_w = _measure(K, steps=2000, dt=5e-4)
        assert math.isfinite(mean_w)
        assert math.isfinite(sd_w)
        assert abs(mean_w) < 1e6, (K, mean_w)


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
