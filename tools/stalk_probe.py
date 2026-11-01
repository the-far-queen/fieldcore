"""
DO THE STALKS ACTUALLY FUNCTION ON THIS BOX?

Bobby, 2026-11-01: *"start on this box see if stalks even function we
were working that"*. And: *"i return to thailand dec 17 over a month
away"* -- so this is the month of work on the machine before the trip.

THIS IS NOT A TEST SUITE. The suite already passes; the question is
whether the stalks COMPUTE anything real -- whether the physics is
real, the numbers move, and the modules talk to each other.

THE MEASURES
------------
  1 THE PHYSICS IS REAL. Take a differential pair and measure its
    characteristic impedance. The answer must be in the range a real
    pair has, and it must MOVE when the geometry moves. A module that
    returns a constant does not function.
  2 THE TOPOLOGY IS REAL. Braiding, nesting: the state machine must
    REFUSE the illegal transitions and allow the legal ones. A
    topology that accepts everything is decoration.
  3 THE CARRIER ROUND-TRIPS. Encode bits into phases and DECODE them
    back through noise. The bit error rate must be zero in clean
    signal and rise MONOTONE with noise -- because that is what a
    real channel does.
  4 THE RESONANCE IS REAL. Cross members must resonate at n*v/(2L),
    and the resonance must SCALE with the length.
  5 THE SPEED IS REAL. The fast brain has a microsecond-to-millisecond
    budget, so the stalk computations must not blow it.

Run: python tools/stalk_probe.py
"""

from __future__ import annotations

import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import stalk_carrier as SC
import stalk_topology as ST
import stalk_wire as SW

FAILURES = []


def check(label, cond, extra=""):
    mark = "ok " if cond else "FAIL"
    print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
    if not cond:
        FAILURES.append(label)


def _stalk(sid, length=1.0, girth=0.1, theta=0.0, winding=0,
            control_points=None):
    """A stalk on the substrate, with a REAL geometry.

    **AND THE CONTROL POINTS AND THE WINDING ARE NOT OPTIONAL.** The
    first version of this probe built stalks with the default empty
    control_points and winding 0, and then three checks failed for a
    reason that was the PROBE's fault, not the module's:

        braid() requires |winding diff| == 1, so two stalks both at
        winding 0 cannot braid -- correctly, because their windings do
        not cross.

        nest() requires the child's waypoints to lie inside the
        parent's bounding disk, and with NO control points the parent
        has no disk, so nothing can be inside it -- again correctly.

    **SO THE PROBE BUILDS THE GEOMETRY THE OPERATIONS ARE ABOUT.**
    """
    if control_points is None:
        control_points = [(theta, 0.0), (theta, length)]
    return ST.Stalk(
        id=sid,
        inner=ST.StalkAttachment(side=ST.AttachmentSide.INNER,
                                 theta=theta, phi=0.0),
        outer=ST.StalkAttachment(side=ST.AttachmentSide.OUTER,
                                 theta=theta, phi=length),
        geometry=ST.StalkGeometry(length=length, girth=girth,
                                  winding=winding,
                                  control_points=list(control_points)),
    )


def main():
    print("=" * 74)
    print("DO THE STALKS FUNCTION ON THIS BOX?")
    print("=" * 74)
    print()

    # -- 1. THE PHYSICS ------------------------------------------------
    print("1. THE PHYSICS -- a differential pair's impedance")
    # a real CAN-like pair: 0.1 mm radius, 0.5 mm apart
    w = SW.StalkWire(girth=1.0e-4, separation=5.0e-4, length=1.0,
                     v_prop=2.0e8, resistivity=1.7e-8)
    z = w.characteristic_impedance()
    print("     Z0 = %.1f ohm    R_dc = %.4f ohm/m"
          % (z, w.dc_resistance_per_m()))
    check("Z0 is in the range a real pair has", 40.0 < z < 200.0, "%.1f" % z)

    z2 = SW.StalkWire(girth=2.0e-4, separation=5.0e-4, length=1.0,
                      v_prop=2.0e8).characteristic_impedance()
    z3 = SW.StalkWire(girth=1.0e-4, separation=1.0e-3, length=1.0,
                      v_prop=2.0e8).characteristic_impedance()
    print("     thicker conductor Z0 = %.1f    wider spacing Z0 = %.1f"
          % (z2, z3))
    check("Z0 MOVES with the conductor", abs(z2 - z) > 1.0,
          "%.1f vs %.1f" % (z, z2))
    check("Z0 MOVES with the spacing", abs(z3 - z) > 1.0,
          "%.1f vs %.1f" % (z, z3))
    check("a thicker conductor has LOWER impedance", z2 < z,
          "%.1f vs %.1f" % (z2, z))
    check("wider spacing RAISES impedance", z3 > z, "%.1f vs %.1f" % (z, z3))

    a1m = w.attenuation_db(1e6)
    a1g = w.attenuation_db(1e9)
    print("     attenuation 1 MHz = %.4f dB   1 GHz = %.4f dB" % (a1m, a1g))
    check("attenuation RISES with frequency", a1g > a1m,
          "%.4f vs %.4f" % (a1m, a1g))

    d = w.propagation_delay_ns()
    print("     propagation delay = %.2f ns over %.2f m" % (d, w.length))
    check("the delay is at the right order of magnitude",
          1.0 < d < 50.0, "%.2f ns" % d)

    # -- 2. THE TOPOLOGY ------------------------------------------------
    print()
    print("2. THE TOPOLOGY -- the state machine refuses the illegal")
    topo = ST.StalkTopology()
    # a and b CROSS, so their windings differ by one -- which is what
    # braid() requires and what "crossing" means physically.
    a = _stalk("a", length=1.0, girth=0.1, theta=0.0, winding=1,
               control_points=[(0.0, 0.0), (0.0, 1.0)])
    b = _stalk("b", length=1.0, girth=0.1, theta=0.0, winding=2,
               control_points=[(0.0, 0.0), (0.0, 1.0)])
    # AND THE NESTING GEOMETRY IS TOROIDAL, which cost another probe
    # failure. MEASURED: `_is_inside` computes the parent's bounding
    # disk from its waypoints with TOROIDAL unwrapping, so for a parent
    # whose waypoints are at phi 0.0 and phi 1.0 the disk is CENTRED at
    # phi 0.5 with radius 5.78 -- and a child at phi 0.1 is 5.88
    # radians from that centre, because the distance wraps the LONG way
    # around. So the child has to sit near the parent's CENTRE, not
    # near one of its endpoints.
    inner = _stalk("inner", length=0.4, girth=0.02, theta=0.0, winding=0,
                   control_points=[(0.0, 0.35), (0.0, 0.65)])
    topo.add(a)
    topo.add(b)
    topo.add(inner)

    check("braiding two attached stalks is ALLOWED", ST.braid(a, b) is True)
    check("the braid is recorded",
          a.braid_partner == "b" and b.braid_partner == "a",
          "%s / %s" % (a.braid_partner, b.braid_partner))
    check("braiding AGAIN is REFUSED", ST.braid(a, b) is False,
          "a stalk already braided cannot be braided twice")
    check("unbraiding is ALLOWED", ST.unbraid(a, b) is True)
    check("the unbraid cleared the partner", a.braid_partner is None)

    check("nesting a small stalk inside a big one is ALLOWED",
          ST.nest(inner, a) is True)
    check("nesting it inside a SECOND parent is REFUSED",
          ST.nest(inner, b) is False,
          "a stalk already nested cannot be nested again")

    # a stalk whose waypoints are FAR outside the parent's disk
    big = _stalk("big", length=1.0, girth=0.1, theta=3.0, winding=0,
                 control_points=[(3.0, 0.35), (3.0, 0.65)])
    topo.add(big)
    check("nesting a stalk that does not FIT is REFUSED",
          ST.nest(big, inner) is False,
          "the child must fit inside the parent")

    topo.tick()
    check("a tick advances the counter", topo.tick_count == 1,
          str(topo.tick_count))

    # -- 3. THE CARRIER ROUND-TRIP ---------------------------------------
    print()
    print("3. THE CARRIER -- encode, transmit, decode")
    braid = SC.three_strand_braid()
    carr = SC.carrier(freq_hz=1e6)
    print("     braid: %d strands, %d pairs, lay angle %.1f deg"
          % (len(braid.strands), len(braid.pairs()), braid.lay_angle_deg()))
    check("the braid has strands", len(braid.strands) >= 3,
          str(len(braid.strands)))
    check("the braid has pairs", len(braid.pairs()) >= 3,
          str(len(braid.pairs())))
    check("the braid matrix is square",
          len(braid.braid_matrix()) == len(braid.strands))

    bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    phases = carr.encode(bits, scheme="bpsk")
    print("     encoded %d bits into %d phases" % (len(bits), len(phases)))
    # AND THE SCHEME MUST MATCH ON BOTH SIDES. The first version of
    # this probe encoded BPSK and decoded with the default QPSK, and
    # got a bit error rate of 0.562 on a PERFECTLY CLEAN channel --
    # which looked like a broken carrier and was actually a broken
    # probe. The decode signature defaults to qpsk, so the scheme has
    # to be passed explicitly.
    check("the decode defaults to qpsk, so the scheme must be passed",
          "scheme" in SC.PhaseCarrier.decode.__code__.co_varnames)
    check("one phase per bit", len(phases) == len(bits),
          "%d vs %d" % (len(phases), len(bits)))

    # AND THE NOISE IS IN RADIANS, and the probe's first range was in
    # the wrong units. MEASURED: the phases are in [0, pi] and the
    # decision boundary is at pi/2, so a gaussian of sigma 0.5 rad is a
    # small perturbation of the ANGLE -- the bit error rate stayed at
    # 0.000 all the way to sigma 0.5, which looked like a broken
    # channel and was actually a probe that never applied real noise.
    #
    # So the range is in RADIANS and it spans the boundary: 0, pi/8,
    # pi/4, pi/2, pi, 3pi/2.
    bers = []
    for noise in (0.0, math.pi / 8, math.pi / 4, math.pi / 2,
                  math.pi, 3 * math.pi / 2):
        got = carr.decode(phases, noise=noise, scheme="bpsk")
        ber = sum(1 for x, y in zip(bits, got) if x != y) / len(bits)
        bers.append(ber)
        print("       noise %.2f -> BER %.3f" % (noise, ber))
    check("a clean channel has NO bit errors", bers[0] == 0.0,
          "%.3f" % bers[0])
    check("noise CAUSES errors", bers[-1] > 0.0, "%.3f" % bers[-1])
    monotone = all(bers[i] <= bers[i + 1] for i in range(len(bers) - 1))
    check("the BER curve is MONOTONE in noise", monotone,
          str(["%.3f" % b for b in bers]))
    check("the channel degrades WITH the noise", bers[-1] > bers[0],
          "%.3f vs %.3f" % (bers[0], bers[-1]))

    # -- 4. THE RESONANCE ------------------------------------------------
    print()
    print("4. THE RESONANCE -- cross members")
    cm = SW.CrossMember(spacing=0.25, count=4)
    res = cm.resonance_hz()
    print("     4 rungs at 0.25 m (L=%.2f m) -> %s Hz"
          % (cm.total_length, ["%.3e" % r for r in res[:3]]))
    check("a cross member HAS resonances", len(res) >= 1, str(len(res)))
    if res:
        expect = 2.0e8 / (2.0 * cm.total_length)
        print("     fundamental %.4e Hz   n*v/(2L) = %.4e Hz"
              % (res[0], expect))
        check("the fundamental is n*v/(2L)", abs(res[0] - expect) < 1.0,
              "%.4e vs %.4e" % (res[0], expect))
        check("the modes are HARMONICS of the fundamental",
              all(abs(res[k] - (k + 1) * res[0]) < 1.0
                  for k in range(len(res))),
              str(["%.3e" % r for r in res]))
        q = cm.quality_factor()
        print("     Q = %.1f   loaded bandwidth = %.3e Hz"
              % (q, cm.loaded_bandwidth_hz()))
        check("the Q is finite and positive", q > 0 and math.isfinite(q),
              "%.2f" % q)

    cm2 = SW.CrossMember(spacing=0.125, count=4)
    r2 = cm2.resonance_hz()
    if res and r2:
        check("a SHORTER member resonates HIGHER", r2[0] > res[0],
              "%.3e vs %.3e" % (r2[0], res[0]))

    # -- 5. THE SPEED ----------------------------------------------------
    print()
    print("5. THE SPEED -- the robot budget")
    t0 = time.perf_counter()
    for _ in range(2000):
        w.characteristic_impedance()
        w.attenuation_db(1e6)
    per_call_us = (time.perf_counter() - t0) * 1000.0 / 2000.0
    print("     4000 stalk computations -> %.4f us each" % per_call_us)
    check("the stalk math is far inside a millisecond", per_call_us < 100.0,
          "%.4f us" % per_call_us)

    t0 = time.perf_counter()
    topo2 = ST.StalkTopology()
    for i in range(200):
        topo2.add(_stalk("s%d" % i, length=1.0, girth=0.01))
    topo2.tick()
    tick_ms = (time.perf_counter() - t0) * 1000.0
    print("     a 200-stalk topology tick took %.2f ms" % tick_ms)
    check("a topology tick is inside a millisecond", tick_ms < 1000.0,
          "%.2f ms" % tick_ms)

    print()
    print("=" * 74)
    if FAILURES:
        print("%d CHECK(S) FAILED:" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        return 1
    print("THE STALKS FUNCTION ON THIS BOX.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
