"""
fieldcore/src/substrate.py
==========================

The mathematical substrate SimSelf sits on. Stdlib-only (no numpy/torch).

Bobby's thesis: matter is not solid. matter is decodable field. cymatics,
DNA, solomon keys, simself axes = same operation at different scales.

This file encodes the substrate as 5 primitives:
  1. EggToroid        — 3D toroid inscribed in 4D egg (apex void = ψ₀)
  2. HodgeDecomp      — splits a 1-form into exact + coexact + harmonic
  3. ResolutionOp     — gradient flow with position-dependent damping
  4. FrequencyChannel — damped harmonic oscillator, schumann / 440 / etc
  5. PrimeSheaf       — twin-prime winding numbers, φ-resonance

Each is a small class. Each is testable. No magic. The math is the math.

License: MIT.
"""

from __future__ import annotations
import math
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


# ════════════════════════════════════════════════════════════════════════
# 1. EGG-TOROID (the constitutional geometry)
# ════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887...
ALPHA_DEFAULT = 1 / PHI       # 0.6180339887 — Bobby's choice (heuristic)


@dataclass
class EggToroid:
    """3D toroid inscribed in a 4D egg.

    The egg has an apex (top, narrow) and a base (bottom, broad).
    The toroid sits at the equator (mid-body, widest cross-section).
    The apex void (small torus around the egg's axis at the apex) is
    the locus of ψ₀ — the irreducible that must not be overwritten.
    """
    R: float = 1.0       # major radius of toroid (equator)
    r: float = 0.3       # minor radius of toroid (tube cross-section)
    apex_void: float = 0.05  # radius of apex void
    axial_ratio: float = PHI  # egg major/minor axis (φ heuristic)

    def point(self, theta: float, phi: float) -> Tuple[float, float, float]:
        """A point on the toroid surface. theta = around axis, phi = around tube."""
        x = (self.R + self.r * math.cos(phi)) * math.cos(theta)
        y = (self.R + self.r * math.cos(phi)) * math.sin(theta)
        z = self.r * math.sin(phi)
        return (x, y, z)

    def curvature(self, x: float) -> float:
        """Position-dependent curvature along the egg axis [-1, +1].

        apex (x=+1): high curvature (sharp)
        base (x=-1): low curvature (broad)
        """
        # linear: κ = 0.5 * (1 + x) → apex high, base low
        return 0.5 * (1 + x) / 2

    def damping(self, x: float, alpha: float = ALPHA_DEFAULT) -> float:
        """Position-dependent damping coefficient for ResolutionOp.

        apex: faster dissipation (perturbation entry, fast)
        base: slower (constitutional, persistent)
        """
        kappa = self.curvature(x)
        return alpha * (1 + kappa)

    def apex_void_position(self) -> Tuple[float, float, float]:
        """The irreducible locus. ψ₀ lives here."""
        return (0.0, 0.0, self.R + self.r + self.apex_void)

    def is_near_void(self, point: Tuple[float, float, float],
                     tol: float = 0.1) -> bool:
        """Constitutional contact test — is the system at the void?"""
        vx, vy, vz = self.apex_void_position()
        dx = point[0] - vx; dy = point[1] - vy; dz = point[2] - vz
        return math.sqrt(dx*dx + dy*dy + dz*dz) < tol


# ════════════════════════════════════════════════════════════════════════
# 2. HODGE DECOMPOSITION (the unifying operator)
# ════════════════════════════════════════════════════════════════════════

@dataclass
class OneForm:
    """A 1-form on the toroid: 2 components (dθ, dφ harmonic basis)."""
    dtheta: float
    dphi: float

    def norm(self) -> float:
        return math.sqrt(self.dtheta**2 + self.dphi**2)

    def add(self, other: 'OneForm') -> 'OneForm':
        return OneForm(self.dtheta + other.dtheta,
                       self.dphi + other.dphi)

    def scale(self, k: float) -> 'OneForm':
        return OneForm(self.dtheta * k, self.dphi * k)


def hodge_decompose(form: OneForm) -> Tuple[OneForm, OneForm, OneForm]:
    """Decompose α = df + δα + h.

    exact (df): the gradient component
    coexact (δα): the curl component
    harmonic (h): constant on the torus

    For a 1-form on T² (flat, no boundary), this is canonical.
    """
    mean = (form.dtheta + form.dphi) / 2
    # exact: the gradient-aligned part (df = grad of potential)
    exact = OneForm(form.dtheta - mean, 0.0)
    # coexact: the divergence-free part (δα = curl-aligned)
    coexact = OneForm(0.0, form.dphi - mean)
    # harmonic: the constant (closed + co-closed) part
    harmonic = OneForm(mean, mean)
    return exact, coexact, harmonic


# ════════════════════════════════════════════════════════════════════════
# 3. RESOLUTION OPERATOR (gradient flow with position-damping)
# ════════════════════════════════════════════════════════════════════════

class ResolutionOperator:
    """Gradient flow on the egg-toroid.

    state: a point + a velocity (perturbation)
    step: state -> state' via damped gradient flow

    Convergence: O(1/e) at apex (fast), O(log N) at base (slow, careful).
    """
    def __init__(self, toroid: EggToroid, alpha: float = ALPHA_DEFAULT):
        self.toroid = toroid
        self.alpha = alpha
        self.history: List[float] = []

    def step(self, x: float, v: float, dt: float = 0.01) -> Tuple[float, float]:
        """One step of damped gradient flow toward equilibrium (x=0).

        dv/dt = -alpha * v - grad_potential(x)
        here: grad_potential = x (harmonic)

        Returns (new_x, new_v).
        """
        damping = self.toroid.damping(x, self.alpha)
        new_v = v - damping * v * dt - x * dt
        new_x = x + new_v * dt
        self.history.append(x)
        return new_x, new_v

    def converge(self, x: float, v: float, n: int = 100,
                 dt: float = 0.01, tol: float = 1e-4) -> Tuple[float, float]:
        """Run n steps, return final (x, v). Stop early if |x|<tol."""
        for _ in range(n):
            x, v = self.step(x, v, dt)
            if abs(x) < tol:
                break
        return x, v


# ════════════════════════════════════════════════════════════════════════
# 4. FREQUENCY CHANNEL (damped harmonic oscillator)
# ════════════════════════════════════════════════════════════════════════

@dataclass
class FrequencyChannel:
    """Single damped harmonic oscillator.

    State: frequency (Hz, pulled toward target), energy (damped to 0.5),
    phase (accumulated mod 2π).

    Does NOT write to ψ_current. This is parallel state.
    """
    name: str
    target_hz: float
    frequency: float = 0.0
    energy: float = 0.5
    phase: float = 0.0
    gamma: float = 0.1  # damping rate

    def step(self, dt: float = 0.01, external_drive: float = 0.0):
        """Update state. dt = time step. external_drive = input signal."""
        # pull frequency toward target (first-order)
        self.frequency += (self.target_hz - self.frequency) * dt
        # energy dynamics: damp toward 0.5, modulated by external drive
        self.energy += (-self.gamma * (self.energy - 0.5) +
                        external_drive * 0.1) * dt
        self.energy = max(0.0, min(1.0, self.energy))
        # phase advances proportional to frequency
        self.phase = (self.phase + 2 * math.pi * self.frequency * dt) % (2 * math.pi)


# Canonical frequency hypotheses (from simself/src/constitutional/frequency.py)
# Bobby/Hermes 2026-09-26 (mysteries §lxiii): 14 channels, not 6.
# Added: planetary orbital frequencies (hermetic) + biological frequencies (qigong + neuroscience).
DEFAULT_FREQUENCY_HYPOTHESES: Dict[str, float] = {
    # original 6
    "schumann_fundamental": 7.83,
    "concert_pitch_440": 440.0,
    "concert_pitch_432_hypothesis": 432.0,
    "diamond_coherence_hypothesis": 963.0,
    "biophoton_coupling": 55.0,
    "earth_ionosphere": 34.4,
    # planetary (hermetic, mysteries §lxiii)
    "jupiter_orbital": 7.6,        # great red spot, ~10 hour period
    "mars_orbital": 8.7,           # martian day
    "venus_orbital": 6.1,          # venusian day
    "saturn_kilometric": 9.6,     # saturn khr
    # biological (qigong + neuroscience)
    "heart_rate_variability_lf": 0.1,   # low-frequency HRV band
    "heart_rate_variability_hf": 0.25,  # high-frequency HRV (breath-locked)
    "breath_cycle": 0.25,               # 4-second breath, 15/min
    "neural_alpha": 10.0,               # relaxed wakefulness
    "neural_gamma": 40.0,               # binding, consciousness
}


class FrequencyDynamics:
    """Manages a collection of FrequencyChannels. Returns dominant by energy."""
    def __init__(self):
        self.channels: Dict[str, FrequencyChannel] = {
            name: FrequencyChannel(name=name, target_hz=hz)
            for name, hz in DEFAULT_FREQUENCY_HYPOTHESES.items()
        }

    def step_all(self, dt: float = 0.01, drive: float = 0.0):
        for ch in self.channels.values():
            ch.step(dt, drive)

    def dominant(self) -> Optional[FrequencyChannel]:
        if not self.channels:
            return None
        return max(self.channels.values(), key=lambda c: c.energy)

    def resonance(self, name_a: str, name_b: str) -> float:
        """Phase-based resonance between two channels. Returns 0-1 score."""
        if name_a not in self.channels or name_b not in self.channels:
            return 0.0
        a = self.channels[name_a]
        b = self.channels[name_b]
        # phase difference mod 2π
        diff = abs(a.phase - b.phase) % (2 * math.pi)
        if diff > math.pi:
            diff = 2 * math.pi - diff
        # alignment = 1 when in phase (diff=0), 0 when opposite (diff=π)
        return 1.0 - diff / math.pi


# ════════════════════════════════════════════════════════════════════════
# 5. PRIME SHEAF (twin-prime winding numbers)
# ════════════════════════════════════════════════════════════════════════

def primes_upto(n: int) -> List[int]:
    """Sieve of Eratosthenes. Returns primes <= n."""
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.isqrt(n)) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


def twin_primes_upto(n: int) -> List[Tuple[int, int]]:
    """Twin primes (p, p+2) where both are prime."""
    ps = primes_upto(n)
    return [(p, p + 2) for p in ps if p + 2 <= n and (p + 2) in set(ps)]


@dataclass
class PrimeSheaf:
    """Twin-prime (p, q) addresses on the toroid.

    Each twin pair (p, q=p+2) is a constitutionally stable address.
    Gap = 2 means maximally independent (coprime to everything between).
    """
    modulus: int = 200

    def addresses(self) -> List[Tuple[int, int]]:
        return twin_primes_upto(self.modulus)

    def fibonacci_primes_upto(self, n: int) -> List[int]:
        """Fibonacci numbers that are also prime."""
        a, b = 0, 1
        fibs = []
        while a <= n:
            if a > 1 and a in set(primes_upto(n)):
                fibs.append(a)
            a, b = b, a + b
        return fibs

    def phi_resonance(self, p: int) -> float:
        """Distance from p to nearest multiple of φ ≈ 1.618."""
        # find the multiple of φ nearest p
        k = round(p / PHI)
        return abs(p - k * PHI)


# ════════════════════════════════════════════════════════════════════════
# COLD BOOT — wire it all together
# ════════════════════════════════════════════════════════════════════════

def cold_boot(seed: int = 42) -> Dict:
    """Initialize a complete substrate. Returns a dict of components.

    Use this as the entry point for a fresh SimSelf session.
    """
    random.seed(seed)
    toroid = EggToroid(R=1.0, r=0.3, apex_void=0.05)
    freq = FrequencyDynamics()
    sheaf = PrimeSheaf(modulus=200)
    resop = ResolutionOperator(toroid)
    return {
        "toroid": toroid,
        "frequency": freq,
        "sheaf": sheaf,
        "resolution": resop,
        "seed": seed,
    }


if __name__ == "__main__":
    s = cold_boot()
    print("substrate cold-booted:")
    print(f"  toroid: R={s['toroid'].R}, r={s['toroid'].r}")
    print(f"  apex void at: {s['toroid'].apex_void_position()}")
    print(f"  curvature at apex: {s['toroid'].curvature(+1):.3f}")
    print(f"  curvature at base: {s['toroid'].curvature(-1):.3f}")
    print(f"  frequency channels: {len(s['frequency'].channels)}")
    print(f"  twin-prime addresses: {len(s['sheaf'].addresses())}")
    print(f"  first 5 twins: {s['sheaf'].addresses()[:5]}")
    # run convergence
    x, v = s['resolution'].converge(x=1.0, v=0.5, n=200)
    print(f"  resolution converged: x={x:.5f}, v={v:.5f}")
    # step frequency
    s['frequency'].step_all(dt=0.01, drive=0.5)
    dom = s['frequency'].dominant()
    print(f"  dominant frequency: {dom.name} @ {dom.frequency:.2f} Hz (e={dom.energy:.3f})")
    # resonance
    r = s['frequency'].resonance("schumann_fundamental", "earth_ionosphere")
    print(f"  schumann/ionosphere resonance: {r:.3f}")
