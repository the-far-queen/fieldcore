"""
quantum_mimic.py — classical primitives that mimic quantum behavior.

Bobby's claim (2026-09-26 thread): "DNA = decodable field-compression
artifact. matter = decodable compression. field encoding = real layer,
matter = decodable compression. same operation as: simself axes =
constitutional field, chladni figures = 2d shadows of n-dim
standing-wave geometry."

If that is right, then quantum behavior — entanglement, superposition,
interference — is what you SEE when a constitutional field is observed
through a matter-shaped lens. The primitives below are the classical
operations that produce the same observable signatures without invoking
quantum mechanics. They are useful because:

  1. They let a reviewer see, in code, what "decoherence" and
     "entanglement" mean under the FieldCore geometry without needing
     to set up a quantum computer.
  2. They let SimSelf reason about state combinations that are
     "superposed" the way a constitutional field is superposed — a
     weighted combination of basis states — and that interfere when
     observed through the same gate.
  3. They give the steel-ball kernel something to do besides gradient
     descent. Entanglement is a non-local constraint; superposition is
     a non-classical state representation; interference is a phase-
     aligned summation.

This file is stdlib-only. The mathematics is in the docstrings of
each class. The asserts are in quantum_mimic_test.py.

Run:
    python src/quantum_mimic.py                # 5 demo sections, all assert
    python -m pytest tests/test_quantum_mimic.py -v
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


PHI = (1 + math.sqrt(5)) / 2     # 1.618...  used as the resonance-anchor
TWO_PI = 2 * math.pi


# ============================================================================
# 1. PHASE — the primitive that all other primitives build on.
#
# A Phase is a complex amplitude with a magnitude and an angle. Operations
# on Phase preserve magnitude (no collapse) unless explicit observation
# collapses.
# ============================================================================

@dataclass
class Phase:
    """A complex number with magnitude and phase.

    Concrete representation: magnitude (≥ 0) + angle (radians, mod 2π).
    Operations: add (mod 2π in phase, linear in magnitude — see note),
    scale (magnitude × k), conjugate (negate phase), inner product.
    """
    magnitude: float = 1.0
    angle: float = 0.0

    def conjugate(self) -> "Phase":
        return Phase(self.magnitude, -self.angle % TWO_PI)

    def scale(self, k: float) -> "Phase":
        if k < 0:
            return Phase(abs(k) * self.magnitude, (self.angle + math.pi) % TWO_PI)
        return Phase(k * self.magnitude, self.angle)

    def add(self, other: "Phase") -> "Phase":
        """Phasor addition. Result magnitude is |a+b|; angle is arg(a+b).

        This is NOT the "superposition" used in superposition.py —
        that one is over discrete basis states with weights. This is
        the continuous-phasor addition that lives inside Interference.
        """
        a_re = self.magnitude * math.cos(self.angle)
        a_im = self.magnitude * math.sin(self.angle)
        b_re = other.magnitude * math.cos(other.angle)
        b_im = other.magnitude * math.sin(other.angle)
        re = a_re + b_re
        im = a_im + b_im
        mag = math.sqrt(re * re + im * im)
        ang = math.atan2(im, re) % TWO_PI
        return Phase(mag, ang)

    def inner(self, other: "Phase") -> float:
        """Real inner product of two phasors. Returns float in [-1, 1] after
        normalization (divided by |a|·|b|). Used as the "overlap" measure
        for entanglement-pair fidelity and interference contrast.
        """
        denom = self.magnitude * other.magnitude
        if denom == 0.0:
            return 0.0
        cos_theta = math.cos(self.angle - other.angle)
        # <a|b> / (|a||b|) = cos(theta). a and b are both real+imag so
        # the complex inner product is |a||b| cos(theta).
        return cos_theta

    def is_aligned_with(self, other: "Phase", tol: float = 1e-6) -> bool:
        """Two phasors are aligned if their angles match within tol.

        This is the binary version of inner() — used in entanglement-pair
        tests where we need to know if measurement of one collapsed the
        other to the same phase.
        """
        return abs(((self.angle - other.angle + math.pi) % TWO_PI) - math.pi) < tol


# ============================================================================
# 2. ENTANGLED PAIR — two phases locked at creation, opposite signs on
# measurement.
#
# The classical mimic: at creation, store (p_a, p_b) such that
# p_b = p_a.conjugate() (or some other anti-correlated relation). When
# one is observed (its angle is "measured" / set to a specific value),
# the other instantaneously reflects the conjugate. There is no
# signaling — the correlation only becomes visible after both are
# measured and compared. The Bell inequality is violated in the
# quantum case; in the classical mimic, the correlation is built in
# at creation time, which is exactly what makes the mimic classical and
# not quantum. The value of the mimic is the API surface.
# ============================================================================

@dataclass
class EntangledPair:
    """Two phases locked at creation. Measurement of one mirrors to the other.

    Correlation: at creation, p_b = p_a.conjugate(). On measure(p_a, value):
    p_a = Phase(1, value); p_b = Phase(1, -value). The pair is a record
    of every measurement; querying history() returns the sequence.

    This is NOT quantum entanglement. It is a deterministic classical
    pair with the same observable correlation. The "no signaling" property
    holds because measuring p_a in isolation gives no information about
    p_b's pre-measurement value — only that, after measurement, p_b is
    determined.
    """
    p_a: Phase
    p_b: Phase
    correlation: str = "conjugate"   # "conjugate" | "parallel" | "anti-parallel"
    history: List[Tuple[str, float]] = field(default_factory=list)
    # history records every measurement: ("a"|"b", measured_angle)

    @classmethod
    def create(cls, p_a: Phase, correlation: str = "conjugate") -> "EntangledPair":
        if correlation == "conjugate":
            p_b = p_a.conjugate()
        elif correlation == "parallel":
            p_b = Phase(p_a.magnitude, p_a.angle)
        elif correlation == "anti-parallel":
            p_b = Phase(p_a.magnitude, (p_a.angle + math.pi) % TWO_PI)
        else:
            raise ValueError(f"unknown correlation: {correlation}")
        return cls(p_a=p_a, p_b=p_b, correlation=correlation)

    def measure_a(self, angle: Optional[float] = None) -> Phase:
        """Observe p_a. If angle is None, sample uniformly in [0, 2π).

        After measurement, p_b is updated to the correlated value:
        - "conjugate": p_b.angle = -p_a.angle
        - "parallel":   p_b.angle = p_a.angle
        - "anti-parallel": p_b.angle = p_a.angle + π
        """
        if angle is None:
            # Use a deterministic "sampling" from the current angle so the
            # test can reason about it; in production, replace with PRNG.
            angle = (self.p_a.angle + math.pi / 7) % TWO_PI
        self.p_a = Phase(1.0, angle)
        self.p_b = self._correlated(self.p_a)
        self.history.append(("a", angle))
        return self.p_a

    def measure_b(self, angle: Optional[float] = None) -> Phase:
        if angle is None:
            angle = (self.p_b.angle + math.pi / 11) % TWO_PI
        self.p_b = Phase(1.0, angle)
        self.p_a = self._correlated(self.p_b)
        self.history.append(("b", angle))
        return self.p_b

    def _correlated(self, p: Phase) -> Phase:
        if self.correlation == "conjugate":
            return p.conjugate()
        if self.correlation == "parallel":
            return Phase(1.0, p.angle)
        if self.correlation == "anti-parallel":
            return Phase(1.0, (p.angle + math.pi) % TWO_PI)
        raise ValueError(f"unknown correlation: {self.correlation}")

    def correlation_holds(self, tol: float = 1e-6) -> bool:
        """Return True iff the current state satisfies the declared correlation."""
        if self.correlation == "conjugate":
            return abs(((self.p_a.angle + self.p_b.angle) % TWO_PI)) < tol or \
                   abs(((self.p_a.angle + self.p_b.angle) % TWO_PI) - TWO_PI) < tol
        if self.correlation == "parallel":
            return abs(((self.p_a.angle - self.p_b.angle) % TWO_PI)) < tol or \
                   abs(((self.p_a.angle - self.p_b.angle) % TWO_PI) - TWO_PI) < tol
        # anti-parallel: a = b + π mod 2π
        diff = (self.p_a.angle - self.p_b.angle) % TWO_PI
        return abs(diff - math.pi) < tol or abs(diff + math.pi - TWO_PI) < tol


# ============================================================================
# 3. SUPERPOSITION — a weighted combination of basis states.
#
# The classical mimic: a Superposition holds N basis states, each with
# a complex weight (Phase). On observe(measure), the superposition
# collapses to one basis state with probability proportional to
# |weight|². The unmeasured weights are zeroed.
#
# The "interference" comes from the fact that two superpositions with
# overlapping basis sets, summed (weighted), can produce constructive
# or destructive interference in their shared bases' weights — the
# probability of observing a shared basis can be greater or less than
# the sum of the originals.
# ============================================================================

@dataclass
class Superposition:
    """A weighted combination of N basis states. Observe() collapses.

    State: dict[basis_id, Phase]. Each basis is a discrete id (string
    or int). The Phase carries magnitude (probability amplitude) and
    angle (phase). On observe(), one basis is selected with probability
    proportional to |w|² and the superposition collapses to it.
    """
    weights: Dict[str, Phase] = field(default_factory=dict)

    def add(self, basis: str, weight: Phase) -> None:
        """Add or replace the weight of a basis."""
        self.weights[basis] = weight

    def normalize(self) -> "Superposition":
        """Scale all weights so |w|² sums to 1.0. Returns self for chaining."""
        total = sum(p.magnitude ** 2 for p in self.weights.values())
        if total == 0.0:
            return self
        k = 1.0 / math.sqrt(total)
        self.weights = {b: p.scale(k) for b, p in self.weights.items()}
        return self

    def probability_of(self, basis: str) -> float:
        """Probability of observing `basis` on the next measurement."""
        total = sum(p.magnitude ** 2 for p in self.weights.values())
        if total == 0.0:
            return 0.0
        if basis not in self.weights:
            return 0.0
        return self.weights[basis].magnitude ** 2 / total

    def observe(self, basis_to_force: Optional[str] = None) -> str:
        """Collapse the superposition to one basis.

        If basis_to_force is given, deterministically collapse to that
        basis. Otherwise pick the basis with the highest probability
        (deterministic, not stochastic — see note in observe_random()
        if you want stochastic).

        Returns the collapsed basis.
        """
        if not self.weights:
            raise ValueError("empty superposition")
        if basis_to_force is not None:
            if basis_to_force not in self.weights:
                raise ValueError(f"basis {basis_to_force!r} not in superposition")
            collapsed = basis_to_force
        else:
            # Deterministic: pick the basis with highest |w|².
            collapsed = max(self.weights,
                            key=lambda b: self.weights[b].magnitude ** 2)
        # Collapse: only the chosen basis remains, with phase = 1.0.
        self.weights = {collapsed: Phase(1.0, 0.0)}
        return collapsed

    def plus(self, other: "Superposition") -> "Superposition":
        """Add two superpositions. Where bases overlap, the phases sum
        (this is the source of interference). Where they don't, the
        bases are unioned with their original weights.

        No normalization — caller should normalize() if they want a
        proper probability distribution.
        """
        out: Dict[str, Phase] = dict(self.weights)
        for b, w in other.weights.items():
            if b in out:
                out[b] = out[b].add(w)
            else:
                out[b] = w
        return Superposition(weights=out)


# ============================================================================
# 4. INTERFERENCE — phase-aligned summation of two patterns.
#
# The classical mimic: take two arrays (or superpositions) and combine
# them with phase alignment. Where the phases align (constructive
# interference), the amplitude grows. Where they anti-align
# (destructive), the amplitude shrinks.
#
# This is the operation that makes a chladni figure look like a
# chladni figure: two orthogonal modes interfere, and the nodes
# (where the amplitudes cancel) trace the pattern.
# ============================================================================

@dataclass
class Interference:
    """Two phase-fields, with phase offset, summed pointwise.

    Use case: given two Superpositions that share a basis set, sum
    them with a phase offset. The result has the same basis set but
    the weights have been re-combined.

    Concretely: for a basis b in the intersection, the new weight is
        w_new = w_a + w_b · e^{i·offset}
    For a basis in only one superposition, the weight is preserved.
    """
    offset: float = 0.0   # phase offset in radians

    def combine(self, a: Superposition, b: Superposition) -> Superposition:
        """Combine two superpositions with self.offset. Returns new Superposition.

        Each of b's weights is rotated by self.offset, then added to the
        corresponding weight in a (if any). Rotation preserves magnitude
        and adds the offset to the angle: rotated_w = Phase(|w|, w.angle + offset).
        """
        out: Dict[str, Phase] = dict(a.weights)
        # Rotate b's weights by the offset (preserves magnitude).
        rotated = {basis: Phase(w.magnitude, (w.angle + self.offset) % TWO_PI)
                   for basis, w in b.weights.items()}
        # Add into out.
        for basis, w in rotated.items():
            if basis in out:
                out[basis] = out[basis].add(w)
            else:
                out[basis] = w
        return Superposition(weights=out)

    @staticmethod
    def fringe_spacing(wavelength: float, n_bases: int) -> List[float]:
        """Compute the expected interference fringe for a 1D basis of
        length `n_bases` and wavelength `wavelength` (in basis units).

        Returns a list of intensities (|amplitudes|²) at each basis
        point. The pattern is cos²(2π·x/λ).

        Useful for visualizing what Interference looks like in 1D.
        """
        return [(math.cos(2 * math.pi * x / wavelength) ** 2)
                for x in range(n_bases)]


# ============================================================================
# 5. WAVE-FUNCTION-LIKE — a Phase field over a discrete basis. Combines
# superposition with entanglement. Two such fields, entangled, can be
# passed to Interference.combine() to produce the visible quantum-like
# correlation patterns.
# ============================================================================

@dataclass
class WaveField:
    """A phase field over a discrete basis. Like ψ(x) for x in [0..N).

    Each basis index has a complex amplitude (Phase). The wave-function-
    like is just a Superposition with integer bases; this class adds the
    geometric operations: shift, scale, gaussian envelope, normalization.
    """
    n: int
    field: Dict[int, Phase] = field(default_factory=dict)

    @classmethod
    def gaussian(cls, n: int, center: float, sigma: float,
                 k: float = 0.0) -> "WaveField":
        """A gaussian wave packet modulated by e^{i·k·x}.

        center: peak position (real)
        sigma:  width parameter
        k:      wavenumber (rad/basis unit). k=0 gives a real envelope.
        """
        wf = cls(n=n)
        for x in range(n):
            env = math.exp(-((x - center) ** 2) / (2 * sigma ** 2))
            phase = (k * x) % TWO_PI
            wf.field[x] = Phase(env, phase)
        return wf

    @classmethod
    def plane_wave(cls, n: int, k: float) -> "WaveField":
        """A pure plane wave e^{i·k·x}."""
        wf = cls(n=n)
        for x in range(n):
            wf.field[x] = Phase(1.0, (k * x) % TWO_PI)
        return wf

    def normalize(self) -> "WaveField":
        total = sum(p.magnitude ** 2 for p in self.field.values())
        if total == 0.0:
            return self
        k = 1.0 / math.sqrt(total)
        self.field = {x: p.scale(k) for x, p in self.field.items()}
        return self

    def to_superposition(self) -> Superposition:
        sp = Superposition()
        sp.weights = {str(x): p for x, p in self.field.items()}
        return sp

    def measure_at(self, x: int) -> float:
        """Return |ψ(x)|². Used to read off the field intensity at a point."""
        if x not in self.field:
            return 0.0
        return self.field[x].magnitude ** 2


# ============================================================================
# CLI: a short demo that exercises every primitive. The asserts at the
# bottom are the "this still works" smoke test.
# ============================================================================

def _demo():
    print("=" * 70)
    print("quantum_mimic.py — classical primitives that mimic quantum behavior")
    print("=" * 70)

    print("\n[1] PHASE — phasor arithmetic")
    p1 = Phase(1.0, math.pi / 4)
    p2 = Phase(1.0, -math.pi / 4)
    p_sum = p1.add(p2)
    print(f"  p1+p2 magnitude: {p_sum.magnitude:.4f}  (expect √2={math.sqrt(2):.4f})")
    assert abs(p_sum.magnitude - math.sqrt(2)) < 1e-6, \
        "phasor add: magnitude mismatch (p1+p2 should be 2·cos(π/4)=√2)"
    p_conj = p1.conjugate()
    assert abs(p_conj.angle - (TWO_PI - math.pi / 4)) < 1e-6, \
        "conjugate: angle wrong"
    print("  ✓ phasor arithmetic and conjugate hold")

    print("\n[2] ENTANGLED PAIR — correlation preserved under measurement")
    pair = EntangledPair.create(Phase(1.0, math.pi / 3), correlation="conjugate")
    assert pair.correlation_holds(), "initial pair must satisfy conjugation"
    pair.measure_a(angle=math.pi / 2)
    assert pair.correlation_holds(), "pair must satisfy conjugation after measurement"
    print(f"  after measure_a(π/2): a.angle={pair.p_a.angle:.4f}, b.angle={pair.p_b.angle:.4f}")
    assert abs(pair.p_b.angle - (TWO_PI - math.pi / 2)) < 1e-6, \
        "b should be conjugate of measured a"
    print("  ✓ entanglement-pair correlation holds across measurements")

    print("\n[3] SUPERPOSITION — weights, normalization, observe()")
    sp = Superposition()
    sp.add("a", Phase(1.0, 0.0))
    sp.add("b", Phase(1.0, math.pi / 2))
    sp.add("c", Phase(1.0, math.pi))
    sp.normalize()
    p_a = sp.probability_of("a")
    p_b = sp.probability_of("b")
    p_c = sp.probability_of("c")
    assert abs(p_a + p_b + p_c - 1.0) < 1e-9, "probabilities must sum to 1"
    collapsed = sp.observe()
    assert sp.probability_of(collapsed) == 1.0, "after observe, collapsed basis has prob 1"
    print(f"  probabilities: a={p_a:.3f} b={p_b:.3f} c={p_c:.3f}, sum={p_a+p_b+p_c:.3f}")
    print(f"  collapsed to basis: {collapsed}")
    print("  ✓ superposition normalization and observe() work")

    print("\n[4] INTERFERENCE — phasor sums and fringe patterns")
    a = Superposition(weights={
        "0": Phase(1.0, 0.0),
        "1": Phase(1.0, 0.0),
        "2": Phase(1.0, 0.0),
    })
    b = Superposition(weights={
        "0": Phase(1.0, math.pi),     # anti-aligned with a
        "1": Phase(1.0, 0.0),         # aligned with a
        "2": Phase(1.0, math.pi),     # anti-aligned with a
    })
    interf = Interference(offset=0.0)
    combined = interf.combine(a, b)
    print(f"  combined weights: 0.mag={combined.weights['0'].magnitude:.4f} (expect 0), "
          f"1.mag={combined.weights['1'].magnitude:.4f} (expect 2.0)")
    assert combined.weights["0"].magnitude < 1e-6, "destructive interference at 0"
    assert abs(combined.weights["1"].magnitude - 2.0) < 1e-6, "constructive interference at 1"
    fringe = Interference.fringe_spacing(wavelength=4.0, n_bases=16)
    assert len(fringe) == 16
    assert max(fringe) <= 1.0 + 1e-9 and min(fringe) >= 0.0 - 1e-9
    print("  ✓ interference: destructive (0) and constructive (2) verified")
    print(f"  1D fringe pattern (λ=4, n=16): peak intensity = {max(fringe):.4f}, "
          f"node intensity = {min(fringe):.4f}")

    print("\n[5] WAVE FIELD — gaussian packet, plane wave, measure_at()")
    packet = WaveField.gaussian(n=64, center=32.0, sigma=8.0, k=math.pi / 4)
    packet.normalize()
    peak_x = max(range(64), key=lambda x: packet.measure_at(x))
    assert abs(peak_x - 32) <= 1, f"gaussian peak should be near center=32, got {peak_x}"
    print(f"  gaussian packet peak at x={peak_x} (expected 32)")
    plane = WaveField.plane_wave(n=16, k=math.pi)
    plane.normalize()
    intensity = sum(plane.measure_at(x) for x in range(16))
    assert abs(intensity - 1.0) < 1e-6, "plane wave normalized intensity must sum to 1"
    print(f"  plane wave normalized intensity sum: {intensity:.4f}")
    print("  ✓ wave-field construction and measurement hold")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE — 5 primitives, all asserts hold")
    print("=" * 70)


if __name__ == "__main__":
    _demo()