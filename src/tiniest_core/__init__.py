"""tiniest_core — kernel package.

Public surface:
- gate(emb, psi0, max_norm, min_cos) — two-inequality veto
- M0_Governor — class wrapper around gate
- gate_packet — alias for gate with default thresholds
- install_ground(dim, axis) — install ψ₀ = e_axis
- make_state(dim, R, perturb, seed) — KernelState with perturb init
- project_ball(psi, psi0, R) — radial projection
- step / gradient / energy / tick — kernel operations
- Channel, ChannelType, VerdictKind, Packet, KernelState — types
"""

from .tiniest_core import (
    MAX_NORM, MIN_COS, DEFAULT_DIM, DEFAULT_R, DEFAULT_ETA,
    ChannelType, VerdictKind, Packet, KernelState,
    norm_ok, cos_ok, gate,
    M0_Governor,
    Channel, glue,
    energy, gradient, project_ball, tick,
    install_ground, make_state,
    run_local_asserts,
)
