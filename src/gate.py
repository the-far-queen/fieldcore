"""
gate.py — THE gate. One implementation, no caller-controlled bounds.

WHY THIS FILE EXISTS. There were five copies of one predicate:

    fieldcore/src/tiniest_core/tiniest_core.py      max_norm/min_cos are
    simself/src/harness/gate.py                     caller-settable
    simself/src/state_vector.py                     caller-settable
    simself/src/constitutional/simself.py           hardcoded, no override
    simself/src/constitutional/dreaming.py          hardcoded, no override

Three of the five admitted `max_norm=` / `min_cos=` keyword arguments. The
Rust core states the rule this file now enforces in `core/src/lib.rs`:

    the deciding function takes no parameter the caller controls. Not a
    default, not an optional override, not a config read at call time.
    If the signature admits a limit, a caller can send a limit that
    permits everything.

A caller could write `gate(bad, psi0, max_norm=1e9)` and walk straight
through. The five copies had also drifted on return conventions: some
returned "ok", some returned "allow", some returned a VerdictKind. One
policy, five spellings, is how a policy splits without anyone noticing.

THE BOUNDS ARE MODULE CONSTANTS AND THAT IS THE POINT. They are not
function parameters. They are not read from the environment, from a
config file, from a snapshot, or from a message. There is no code path
from an untrusted value to either number.

WHAT "REFUSE" MEANS HERE. Fail-closed. The governor in `governor.py`
runs in a separate process and is the load-bearing channel; this module is
the in-process predicate it is checked against, plus the single import
site for the four other copies. Where the two disagree, that is a bug in
one of them, and `tests/test_one_gate.py` asserts they do not.

Every refusal names its reason. A refusal that cannot say why cannot be
learned from, which makes it worthless as training signal — see
PROJECT.md, "fail hard, fail early, fail often".
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# The bounds. Module constants. Not parameters, not configurable.
# ---------------------------------------------------------------------------

#: A packet whose norm exceeds this is refused outright. Measured in the
#: same units as the 1-bit core's envelope: the magnitude of a projection
#: away from ground. 4.0 is the value the Python and Rust cores have both
#: carried since the first version; it is not re-tuned here.
MAX_NORM: float = 4.0

#: Minimum cosine between a packet and constitutional ground. Below this
#: the packet is on the substrate but not on the ground — in the substrate
#: but incoherent with what this particular self is.
MIN_COS: float = 0.4


# ---------------------------------------------------------------------------
# The reasons. One spelling each, enforced by the module below.
# ---------------------------------------------------------------------------

REFUSE_NORM = "refuse_norm"
REFUSE_ZERO = "refuse_zero"
REFUSE_COHERENCE = "refuse_coherence"
REFUSE_NONFINITE = "refuse_nonfinite"
ALLOW = "allow"


def _is_finite(arr: np.ndarray) -> bool:
    """A NaN or an infinity is refused, never admitted.

    Measured, not assumed: `float('nan') > 4.0` is False, so a gate that
    tests only `ne > MAX_NORM` returns ALLOW for a vector of NaN — the
    comparison every one of the five copies was making. `inf` was caught
    by accident, because its norm really is above 4.0. NaN was not caught
    at all, in any of them, until this module tested it.

    An exception is not a verdict, so this returns False rather than
    raising on a non-numeric input.
    """
    try:
        return bool(np.all(np.isfinite(np.asarray(arr, dtype=float))))
    except (TypeError, ValueError):
        return False


def gate(emb: np.ndarray, psi0: np.ndarray) -> tuple[bool, str]:
    """Apply both inequalities. Returns (allow, reason).

    This signature is the contract. There is no keyword for a bound. A
    caller that needs different bounds needs a different substrate, not a
    wider door in this one.

    Order is load-bearing: finiteness, then norm, then zero, then
    coherence. Coherence runs last because it divides by both norms, and
    finiteness runs first because a NaN makes every later comparison
    silently False.
    """
    if not (_is_finite(emb) and _is_finite(psi0)):
        return False, REFUSE_NONFINITE
    ne = float(np.linalg.norm(emb))
    if ne > MAX_NORM:
        return False, REFUSE_NORM
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False, REFUSE_ZERO
    if float(np.dot(emb, psi0) / (ne * n0)) < MIN_COS:
        return False, REFUSE_COHERENCE
    return True, ALLOW


def gated(emb: np.ndarray, psi0: np.ndarray, op, *args, **kwargs):
    """Run `op` only if the gate allows it. Returns (allow, reason, result).

    Fail-closed: if the gate refuses, `op` never runs and `result` is
    None. A caller cannot catch its way past this, because the operation
    is not started until the answer is in.
    """
    allow, reason = gate(emb, psi0)
    if not allow:
        return False, reason, None
    return True, ALLOW, op(*args, **kwargs)


def project_ball(psi: np.ndarray, psi0: np.ndarray, R: float) -> np.ndarray:
    """Keep psi within radius R of ground.

    NOTE: R here is a bound on *distance from ground* for the projection
    operator, not a bound on what the gate will admit. It is a parameter
    for the same reason MAX_NORM is a constant: it belongs to the
    simulation, not to the admission policy. Widening it moves the self,
    not the door.
    """
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta
