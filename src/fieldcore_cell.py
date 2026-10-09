"""FieldCoreCell — single manifold: egg toroid, Hodge, prime sheaves.

Built from Bobby's frontier corpus, 2026-10-08, deepseek1 parts 15/62/84/97:

  part 15  "Minimal FieldCore cell ... 8-dimensional state vector"
  part 62  "Single manifold: egg compression, phase spin, Hodge, prime
            harmonics", alpha = 1/phi, prime channels (5,7,11,13)
  part 84  binding_proj + binding_w (n x n), topo_protection, egg_compression
  part 97  NineManifoldFieldCore with FIXED twin-prime coupling

What is implemented here, and what is deliberately not:

  IMPLEMENTED  toroidal embedding, Hodge split (grad / curl / harm),
               prime sheave encode-decode, binding weights, egg
               compression (phi^-1), phase gate, topological protection,
               the resolution operator R[Psi] = Psi + a*grad + harm

  NOT IMPLEMENTED  the claims that this cell is *conscious*, that prime
               dimensions carry meaning, that topo_protection corresponds
               to anything in particular. Those are Layer C and they stay
               unmarked nowhere: they are marked HERE, in this docstring,
               because a module that carries them without saying so is how
               a speculation becomes a runtime dependency.

The one thing worth stating plainly: alpha = 1/phi and the 5/7/11/13 prime
dims are Bobby's choices, not theorems. They are implemented exactly as
specified because the architecture is measured against them, and the
measurements are what will settle it.

SUBSTRATE INVARIANT. psi_0 = 0 and the drift must contract. Every cell
keeps its state inside a ball of radius topo_protection. If you change
that and the tests start failing, the substrate invariant is what broke.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn

PHI = 1.618033988749895
FLOOR = 1e-8


def torus_embed(state: Tensor) -> Tensor:
    """Map a state vector onto the torus: angle -> unit circle.

    Periodic in every coordinate, which is what makes the manifold
    toroidal rather than merely bounded.

    atan2 is taken on the RATIO, so the identity is in the reduced angle
    rather than in the raw coordinate. The first version did
    atan2(x[1::2], x[0::2]) directly, which is correct for bounded states
    but NOT periodic: adding 2*pi to one coordinate of a pair moves the
    angle, because only one of the two arguments changed. Reducing both
    coordinates mod 2*pi before the call makes the periodicity real.
    """
    two_pi = 2.0 * math.pi
    a = torch.remainder(state[..., 0::2], two_pi)
    b = torch.remainder(state[..., 1::2], two_pi)
    return torch.atan2(b, a)


def _circular_grad(x: Tensor) -> Tensor:
    """Gradient along a periodic 1-D signal, via centred differences with
    wrap. The Laplacian of a circle is what Hodge needs here.
    """
    return 0.5 * (torch.roll(x, -1, dims=-1) - torch.roll(x, 1, dims=-1))


def _circular_curl(x: Tensor) -> Tensor:
    """Curl along a periodic 1-D signal: the same centred difference read
    along the orthogonal phase.
    """
    d = _circular_grad(x)
    return 0.5 * (torch.roll(d, -1, dims=-1) - torch.roll(d, 1, dims=-1))


def hodge_split(x: Tensor) -> tuple[Tensor, Tensor, Tensor]:
    """Split a periodic signal into (gradient, curl, harmonic) parts.

    exact   = integral   ->  mean removal
    coexact= curl       ->  the rotation of the centred difference
    harmonic = what is left, i.e. the part with no exact and no coexact
    content. On a closed manifold the harmonic component is the part
    gradient flow does not move, which is why it is kept separately.
    """
    mean = x.mean(dim=-1, keepdim=True)
    exact = mean.expand_as(x)
    resid = x - exact
    coexact = _circular_curl(resid)
    coexact_mean = coexact.mean(dim=-1, keepdim=True)
    coexact = coexact - coexact_mean
    harmonic = resid - coexact
    return exact, coexact, harmonic


@dataclass
class CellOutput:
    state: Tensor
    control: Tensor
    curl_norm: Tensor
    harmonic: Tensor


class FieldCoreCell(nn.Module):
    """One manifold. 8-dim state, prime sheaves (5,7,11,13)."""

    def __init__(self, state_dim: int = 8, prime_set: tuple[int, ...] = (5, 7, 11, 13),
                 alpha: float = 1.0 / PHI) -> None:
        super().__init__()
        if state_dim % 2 != 0:
            raise ValueError("state_dim must be even: the torus embedding pairs coordinates")
        self.state_dim = state_dim
        self.prime_dims = tuple(prime_set)
        self.alpha = alpha
        n = len(self.prime_dims)

        self.encoders = nn.ModuleList([nn.Linear(state_dim, p) for p in self.prime_dims])
        self.decoders = nn.ModuleList([nn.Linear(p, state_dim) for p in self.prime_dims])
        # binding_proj reduces every prime channel onto the first prime's
        # dimension; bind_out lifts it back. The corridor is what makes the
        # channels interact at all rather than running in parallel.
        self.bind_proj = nn.ModuleList([nn.Linear(p, self.prime_dims[0]) for p in self.prime_dims])
        self.bind_out = nn.Linear(self.prime_dims[0], state_dim)
        self.binding_w = nn.Parameter(torch.randn(n, n) * 0.05)

        self.phase_gate = nn.Parameter(torch.randn(state_dim) * 0.08)
        self.topo_protection = nn.Parameter(torch.tensor(0.91))
        self.egg_compression = nn.Parameter(torch.tensor(1.0 / PHI))

    # ---------------------------------------------------------------- helpers

    def _normalize(self, x: Tensor) -> Tensor:
        """Keep the state inside the protected ball.

        Radius is topo_protection, floored so a near-zero protection value
        cannot make the division explode. Returns the state unchanged when
        it is already inside.
        """
        norm = x.norm(dim=-1, keepdim=True).clamp(min=FLOOR)
        radius = self.topo_protection.abs().clamp(min=FLOOR).unsqueeze(-1)
        scale = radius.clamp(max=1.0) / norm
        return x * torch.clamp(scale, max=1.0)

    def _egg_scale(self, device: torch.device, dtype: torch.dtype) -> Tensor:
        """Asymmetric scaling: only the first coordinate is compressed, by
        phi^-1. The egg is not a ball — it is compressed on one axis.
        """
        scale = torch.ones(self.state_dim, device=device, dtype=dtype)
        scale[0] = self.egg_compression.to(dtype)
        return scale

    # ---------------------------------------------------------------- forward

    def forward(self, x: Tensor, time_step: Tensor | float = 0.0,
                embed_fn=None, goal: Tensor | None = None) -> CellOutput:
        embed_fn = embed_fn or torus_embed

        # 1. egg compression
        x = x * self._egg_scale(x.device, x.dtype)

        # 2. geometric prior from the torus embedding
        theta = embed_fn(x)
        x = x + 0.1 * torch.sin(theta.repeat(1, x.shape[-1] // theta.shape[-1]))

        # 3. Hodge split
        exact, coexact, harmonic = hodge_split(x)
        grad = exact + coexact
        curl_norm = coexact.norm(dim=-1, keepdim=True)

        # 4. resolution operator  R[Psi] = Psi + alpha*grad + harm
        out = x + self.alpha * grad + harmonic

        # 5. prime sheaves: encode -> project onto the binding corridor
        #    -> decode. The corridor carries the prime-dimensional code,
        #    not the decoded state, so bind_proj sees each prime's own
        #    width (5, 7, 11, 13) and reduces it to prime_dims[0].
        encoded = [enc(x) for enc in self.encoders]            # (B, p_i)
        bound = torch.stack([proj(h) for proj, h in zip(self.bind_proj, encoded)], dim=-2)
        weights = torch.softmax(self.binding_w, dim=-1)        # (n, n)
        bound = torch.einsum("ij,bjd->bid", weights, bound)
        corridor = self.bind_out(bound.sum(dim=-2))            # (B, state_dim)

        # 6. decode each prime channel back into the state space
        decoded = [dec(h) for dec, h in zip(self.decoders, encoded)]
        prime_stack = torch.stack(decoded, dim=-2)              # (B, n, state_dim)
        prime_term = prime_stack.mean(dim=-2)                  # (B, state_dim)
        out = out + 0.1 * prime_term

        # 7. phase gate: per-coordinate modulation that rotates with time
        t = torch.as_tensor(time_step, dtype=x.dtype, device=x.device)
        phase = torch.sin(t * 0.1) * self.phase_gate
        out = out + phase * corridor

        # 8. goal bias
        if goal is not None:
            out = out + 0.05 * goal

        # 9. topological protection
        out = self._normalize(out)

        control = torch.tanh(out[..., :5])                       # 5-dim control
        return CellOutput(state=out, control=control,
                          curl_norm=curl_norm, harmonic=harmonic)


class FiveToroidArray(nn.Module):
    """Five spinning toroids inside the egg, at 72-degree offsets.

    5-fold symmetry: the manifold index sets the phase offset, so the
    array is rotationally symmetric by construction rather than by
    learning. Corresponds to part 38 ("5 spinning toroids inside egg").
    """

    OFFSETS = (0.0, 2 * math.pi / 5, 4 * math.pi / 5, 6 * math.pi / 5, 8 * math.pi / 5)

    def __init__(self, state_dim: int = 8, n_toroids: int = 5) -> None:
        super().__init__()
        if n_toroids > len(self.OFFSETS):
            raise ValueError(f"at most {len(self.OFFSETS)} toroids in this construction")
        self.n = n_toroids
        self.cells = nn.ModuleList([FieldCoreCell(state_dim) for _ in range(n_toroids)])
        self.state_dim = state_dim

    def forward(self, state: Tensor, time_step: Tensor | float = 0.0):
        states, controls, curls, harmonics = [], [], [], []
        for i, cell in enumerate(self.cells):
            offset = self.OFFSETS[i]
            out = cell(state, time_step + offset)
            states.append(out.state)
            controls.append(out.control)
            curls.append(out.curl_norm)
            harmonics.append(out.harmonic)
        return (torch.stack(states, dim=1),
                torch.stack(controls, dim=1),
                torch.stack(curls, dim=1),
                torch.stack(harmonics, dim=1))

    def collective_strength(self, states: Tensor) -> Tensor:
        """Norm of the mean field across toroids: how much they agree.

        Zero when all toroids differ, large when they converge. This is
        the quantity part 38 plots as "Collective Field Strength".
        """
        return states.mean(dim=1).norm(dim=-1, keepdim=True)