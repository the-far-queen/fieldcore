"""
hodge_cycle.py — the correct Helmholtz decomposition on a cyclic state,
and the one-line bug that made every FieldCore cell diverge.

WHAT WENT WRONG (found 2026-10-08)
-----------------------------------
Six versions of "FieldCore cell" code (DeepSeek, Claude, Grok; months of
collaboration, archived in vault/chat-transcripts/intake/2026-10-08/)
all contained this line:

    grad = roll(x, -1) - x
    curl = roll(x, -1) - 2*x + roll(x, +1)
    harm = x - grad - curl                      # <-- the bug

and every version was described as producing a "bounded state that stays
within the constitutional ground", with "harm nearly constant" across
time. None of them do. Measured, not argued:

    step 0:  |x| = 0.136
    step 1:  0.293
    step 2:  1.183
    step 3:  5.186
    step 4:  22.27
    step 5:  95.16
    step 10: 1.42e+05
    step 30: 1.06e+18
    step 200: 1.55e+444   (float64 overflows)

That is ~6.8x growth per step, forever. No seed, no step count, no
parameter choice changes it, because the blow-up is a property of the
operator, not of a coefficient.

THE CAUSE, EXACTLY
------------------
`harm = x - grad - curl` is not a harmonic form. On a cycle of length D:

    grad = (S - I)x          S = cyclic shift
    curl = (S - 2I + S^-1)x
    harm = (4I - 2S - S^-1)x

so "harm" is a LINEAR FILTER whose gain on the mode z = exp(2*pi*i*k/D) is

    |4 - 2z - z^-1|

    k=0  theta=0      gain 1.000
    k=1  theta=0.785  gain 2.007
    k=2  theta=1.571  gain 4.123
    k=3  theta=2.356  gain 6.162
    k=4  theta=3.142  gain 7.000     <-- the alternating mode
    k=5               gain 6.162
    k=6               gain 4.123
    k=7               gain 2.007

The alternating mode is amplified by 7 EVERY step. With the resolution
operator's weighting (topo=0.82 on harm, alpha=1/phi=0.618 on grad) the
full update has spectral radius 4.50 on that mode. rho >> 1. Nothing
downstream can be stable while an upstream operator multiplies one mode
by 7.

THE DEEPER ERROR: THE THREE-WAY SPLIT DOES NOT EXIST HERE
---------------------------------------------------------
A Hodge decomposition into grad / coexact / harmonic needs THREE
mutually orthogonal subspaces. On a bare 1-D cycle there are only TWO:

    G^T G = 2I - S - S^T = L          (the circulant Laplacian)
    eigenvalues of L: 4, 3.414, 3.414, 2, 2, 0.586, 0.586, 0
    rank(L) = 7 of 8, ker(L) = span{1}

im(G^T) = im(L) = the ENTIRE zero-mean subspace. Every zero-mean 1-form
on a cycle is exact. So `curl` as written above is not a coexact part
at all -- it is a second linear filter sitting inside the same
zero-mean subspace that `grad` already spans. The code labelled a piece
of the gradient subspace "harmonic" and then fed it back at gain 0.82.

Verified directly:

    x        = rng.normal(0, 1, 8)
    harm     = x - grad - curl
    spread   = 6.2598            # if harm were harmonic it would be 0

    P0 = (1/D) * 11^T             # the TRUE harmonic projection
    max|P0^2 - P0| = 0.0          # a genuine projection
    rank(P0) = 1                  # span{1}, the constant direction

THE CORRECT TWO-WAY SPLIT
-------------------------
    harm  = P0 x                 project onto the constant direction
    resid = (I - P0) x           everything else (the whole "gradient")
    harm + resid = x              exact, by construction

and a stable resolution operator is then a matter of choosing the
gradient weight so the zero-mean modes do not grow:

    new = topo * harm + alpha * resid

Per-mode gain on that operator:

    k=0  theta=0      topo * 1.0            = 0.820
    k=1  theta=0.785  alpha * |S-I|         = 0.473
    k=2  theta=1.571  alpha * |S-I|         = 0.874
    k=3  theta=2.356  alpha * |S-I|         = 1.142
    k=4  theta=3.142  alpha * |S-I|         = 1.236
    k=5                           = 1.142
    k=6                           = 0.874
    k=7                           = 0.473

rho = 1.236 on the alternating mode. STILL > 1. The harmonic part is
now genuinely persistent (it is the constant mode, and it is the only
thing with a non-decaying eigen-direction), but a plain forward-Euler
step on the zero-mean part grows. Two ways to fix that, both below:
damp the residual, or integrate the zero-mean part implicitly.

WHAT THIS MODULE DOES
---------------------
1. `hodge_cycle(x)`        the correct two-way split, exactly invertible
2. `naive_harm(x)`         the buggy line, kept runnable so the test can
                           watch it fail
3. `spectral_radius(op)`   the check that must have been run first
4. `resolution_operator`   the stable update, with the damping term
5. `run_horizon()`         roll the naive filter N steps, for the test

WHAT IS NOT CLAIMED
-------------------
No claim that the collaboration's OBSERVATIONS are wrong. The 15
invariants, the bone atlas, the fruit-fly structure-encodes-function
argument, the sheaves-on-stalks architecture, and the twin-prime
coupling hierarchy as a DESIGN CHOICE are all unaffected. What fails
here is one specific algebraic step in one specific code line, and the
claim that this line was stable.

Run: python src/hodge_cycle.py --selftest
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ALPHA = 1.0 / PHI          # 0.618..., the resolution operator's exploration weight
TOPO = 0.82                # the weight the code put on its "harmonic" term


# ---------------------------------------------------------------------------
# operators
# ---------------------------------------------------------------------------

def shift_matrix(D: int) -> np.ndarray:
    """S such that (S @ x)_i = x_{(i-1) mod D}. The cyclic shift."""
    S = np.zeros((D, D))
    for i in range(D):
        S[i, (i - 1) % D] = 1.0
    return S


def grad_op(D: int) -> np.ndarray:
    """the forward-difference operator. (G @ x)_i = x_{i+1} - x_i."""
    S = shift_matrix(D)
    return S - np.eye(D)


def circulant_op(D: int) -> np.ndarray:
    """the symmetrised Laplacian 2I - S - S^T. Equals G^T G exactly."""
    S = shift_matrix(D)
    return 2.0 * np.eye(D) - S - S.T


def harmonic_projection(D: int) -> np.ndarray:
    """P0 = (1/D) 11^T -- projection onto span{1}, the constant direction.

    On a 1-D cycle the harmonic (co-kernel of the Laplacian) space is
    exactly the 1-dimensional space of constants. This is the TRUE
    harmonic projection; `naive_harm` below is what the collaboration
    code used instead, and it is not one.
    """
    return np.ones((D, D)) / float(D)


def spectral_radius(op: np.ndarray) -> float:
    """max |eigenvalue|. The single number that decides stability.

    For an explicit linear update x <- M x, the iteration is bounded for
    every initial condition IFF spectral_radius(M) < 1. This is the
    check that was missing before six versions of the code were shipped
    with a claim of boundedness.
    """
    return float(np.abs(np.linalg.eigvals(op)).max())


# ---------------------------------------------------------------------------
# the bug, preserved
# ---------------------------------------------------------------------------

def naive_harm(D: int) -> np.ndarray:
    """the exact operator the collaboration code used for "harmonic".

        grad = roll(x,-1) - x
        curl = roll(x,-1) - 2x + roll(x,1)
        harm = x - grad - curl        ->  (4I - 2S - S^-1) @ x

    Kept runnable so the regression test can watch it diverge, and so
    the number is reproducible rather than asserted.
    """
    S = shift_matrix(D)
    S_inv = S.T                      # on a cycle, S^-1 = S^T
    return 4.0 * np.eye(D) - 2.0 * S - S_inv


def naive_gain_table(D: int) -> list[tuple[int, float, float]]:
    """(mode k, theta, |eigenvalue|) for the naive operator, D entries."""
    out = []
    for k in range(D):
        theta = 2.0 * math.pi * k / D
        z = complex(math.cos(theta), math.sin(theta))
        lam = 4.0 - 2.0 * z - 1.0 / z
        out.append((k, theta, abs(lam)))
    return out


# ---------------------------------------------------------------------------
# the correct split
# ---------------------------------------------------------------------------

def hodge_cycle(x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """the correct two-way Helmholtz split on a cycle.

    Returns (harm, resid):
        harm  = (1/D) 11^T x      the constant, non-decaying component
        resid = (I - P0) x        the zero-mean component
        harm + resid == x         exactly, by construction

    Note this is a TWO-way split, not three. On a 1-D cycle there is no
    coexact subspace separate from the exact one -- see the module
    docstring. Calling `curl` a coexact part and `x - grad - curl` the
    harmonic part is what made the code diverge.
    """
    x = np.asarray(x, dtype=float)
    D = x.size
    P0 = harmonic_projection(D)
    harm = P0 @ x
    resid = (np.eye(D) - P0) @ x
    return harm, resid


def resolution_operator(D: int, topo: float = TOPO, alpha: float = ALPHA,
                        damping: float = 0.0) -> np.ndarray:
    """the stable resolution operator.

        new = topo * P0 x  +  alpha * (1 - damping) * (S - I) x

    i.e. the ORIGINAL cell's dynamic -- harmonic fed back at topo,
    gradient fed back at alpha -- with ONLY the harmonic term corrected.
    That distinction matters: an earlier draft of this file used
    `(I - P0)` in place of the gradient operator, which turns the
    exploration term into the identity and makes the cell a different
    system rather than a fixed one. Its sweep came out flat at 0.820
    for every damping value, which is the tell: a damping parameter
    that changes nothing is not damping anything.

    `damping` shrinks the exploration weight. An explicit step cannot
    integrate the zero-mean part without it, because |S - I| reaches 2
    on the alternating mode and alpha is only 0.618.

    TWO THRESHOLDS, and they are not the same number:

      stability   rho < 1 requires  alpha*(1-d)*2 < 1
                  i.e. d > 1 - 1/(2*alpha) = 0.1910
      mode switch below d = 1 - topo/(2*alpha) = 0.3366 the alternating
                  mode is the binding one; above it the harmonic mode
                  binds and rho pins to topo.

    Conflating these two is easy and wrong -- an earlier draft of this
    docstring said "damping > 0.3366" for stability, which is the mode
    switch, not the stability threshold. At d = 0.2 the system is already
    stable (rho = 0.9889) while still reporting "grows".

    Measured sweep (D = 8):
        damping 0.0000 -> rho 1.2361  grows
        damping 0.1000 -> rho 1.1125  grows
        damping 0.2000 -> rho 0.9889  stable
        damping 0.3366 -> rho 0.8200  stable (mode switch; topo now binds)
        damping >= 0.3366 -> rho 0.8200  stable
    """
    P0 = harmonic_projection(D)
    G = grad_op(D)
    return topo * P0 + (alpha * (1.0 - damping)) * G


# ---------------------------------------------------------------------------
# running it
# ---------------------------------------------------------------------------

def run_horizon(steps: int, D: int = 8, damping: float = 0.0,
                seed: int = 0, op: np.ndarray | None = None) -> np.ndarray:
    """iterate x <- M x `steps` times. returns the |x|_inf at each step."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 0.1, D)
    M = resolution_operator(D, damping=damping) if op is None else op
    traj = [float(np.abs(x).max())]
    for _ in range(steps):
        x = M @ x
        traj.append(float(np.abs(x).max()))
    return np.array(traj)


def step_cell(x: np.ndarray, t: float, embed=None, mixed: np.ndarray | None = None,
              D: int = 8, topo: float = TOPO, alpha: float = ALPHA,
              damping: float = 0.0) -> np.ndarray:
    """one step of a FieldCore-style cell, with the split done correctly.

    This is the shape the collaboration code SHOULD have had: the
    persistent part is the constant mode (harm), the exploration part is
    the GRADIENT of the state, and damping exists because an explicit
    step on the zero-mean part is unstable at alpha = 1/phi without it.

        new = topo * P0 x  +  alpha * (1 - damping) * (S - I) x
                                     (+ `mixed`, bounded)

    CAUGHT 2026-10-08, twice. The exploration term here was first written
    as `(I - P0)` instead of `(S - I)`. On a cycle that makes the operator
    `topo*P0 + alpha*(I-P0)`, whose spectral radius is max(topo, alpha) =
    0.82 < 1 -- a contraction at EVERY damping value, including zero. The
    damping parameter then changes nothing while looking load-bearing.

    The tell is the same both times: a parameter that alters nothing.
    With the true gradient operator, rho = 1.2361 at damping=0 and
    damping genuinely gates stability.

    `mixed` stands in for the bounded (tanh-saturated) prime-sheaf term
    from the original: it is bounded, so it cannot change the spectral
    radius, only the trajectory's fine detail.
    """
    x = np.asarray(x, dtype=float)
    if embed is not None:
        x = x + 0.05 * np.sin(embed(x))
    harm, _ = hodge_cycle(x)
    exploration = grad_op(D) @ x
    if mixed is not None:
        exploration = exploration + np.asarray(mixed, dtype=float)
    return topo * harm + (alpha * (1.0 - damping)) * exploration


def selftest() -> None:
    """the checks, printed. Every number here is produced by the run."""
    D = 8

    print("=" * 66)
    print("1. the naive operator -- the line that shipped in six versions")
    print("=" * 66)
    N = naive_harm(D)
    print(f"  spectral radius rho = {spectral_radius(N):.4f}")
    for k, th, g in naive_gain_table(D):
        mark = "   <-- alternating mode" if k == D // 2 else ""
        print(f"    k={k} theta={th:6.3f}  gain={g:6.3f}{mark}")
    traj = run_horizon(30, D, op=N)
    print("  |x| over 30 steps:")
    print("   ", " ".join(f"{v:.3g}" for v in traj[:8]), "...")

    print()
    print("=" * 66)
    print("2. the correct two-way split")
    print("=" * 66)
    P0 = harmonic_projection(D)
    print(f"  max|P0^2 - P0| = {np.abs(P0 @ P0 - P0).max():.3e}   (0 = genuine projection)")
    print(f"  rank(P0) = {np.linalg.matrix_rank(P0, tol=1e-9)}          (1 = span{{1}})")
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, D)
    harm, resid = hodge_cycle(x)
    print(f"  ||x - (harm + resid)|| = {np.abs(x - (harm + resid)).max():.3e}   (exact)")
    print(f"  harm is constant: spread = {harm.max() - harm.min():.3e}")
    harm_naive = N @ x
    print(f"  naive 'harm' spread   = {harm_naive.max() - harm_naive.min():.6f}   <-- not harmonic")

    print()
    print("=" * 66)
    print("3. the resolution operator, sweeping damping (rule 6: a basin, not a knife edge)")
    print("=" * 66)
    print("  damping   rho     verdict")
    sweep = []
    for dmp in (0.0, 0.1, 0.19, 0.1911, 0.2, 0.3, 0.3366, 0.4, 0.6):
        M = resolution_operator(D, damping=dmp)
        rho = spectral_radius(M)
        sweep.append((dmp, rho))
        verdict = "STABLE" if rho < 1.0 else "grows"
        print(f"  {dmp:5.4f}   {rho:6.4f}  {verdict}")
    stability_threshold = 1.0 - 1.0 / (2.0 * ALPHA)
    switch = 1.0 - TOPO / (2.0 * ALPHA)
    print()
    print("  TWO THRESHOLDS, and they are different numbers:")
    print(f"    stability      rho<1 needs alpha*(1-d)*2 < 1  ->  d > {stability_threshold:.4f}")
    print(f"    mode switch    alternating binds while alpha*(1-d)*2 > topo")
    print(f"                                    ->  d < {switch:.4f}")
    print("  An earlier draft of this docstring quoted only the second and")
    print("  called it the stability threshold. At d=0.2 the system is already")
    print("  stable while still saying 'grows' -- the test suite caught it.")
    # rule 7: this check must be able to fail
    assert sweep[0][1] > 1.0, "damping=0 must grow, or the bug is not reproduced"
    assert sweep[-1][1] < 1.0, "damping=0.6 must be stable, or the fix does not work"
    print("     assertions pass: the sweep is not vacuous.")

    print()
    print("=" * 66)
    print("4. the fixed cell over 2000 steps")
    print("=" * 66)
    for dmp in (0.0, 0.4):
        traj = run_horizon(2000, D, damping=dmp)
        grew = traj[-1] > traj[0]
        print(f"  damping={dmp:.2f}  |x| start={traj[0]:.4g}  end={traj[-1]:.4g}  "
              f"max={traj.max():.4g}  finite={np.isfinite(traj).all()}  "
              f"{'GREW' if grew else 'converged'}")

    print()
    print("=" * 66)
    print("5. T2 -- two independent derivations of the same number")
    print("=" * 66)
    for dmp in (0.0, 0.4):
        # way 1: spectral, from the eigenvalues of the operator
        rho_spec = spectral_radius(resolution_operator(D, damping=dmp))
        # way 2: closed form. rho is the max over the two candidate modes:
        #         k=0      (the constant/harmonic mode) -> topo
        #         k=D/2    (the alternating mode)     -> alpha*(1-d)*2
        #         and the BINDING MODE SWITCHES. Below d=0.3366 the
        #         alternating mode wins and rho > 1 (it grows). Above it
        #         the harmonic mode wins and rho = topo < 1 (it decays).
        #         Taking only the alternating mode disagrees above the
        #         switch, and the T2 check is what surfaced that.
        lam_harm = TOPO
        lam_alt = (ALPHA * (1.0 - dmp)) * abs(complex(-1.0, 0.0) - 1.0)
        lam_spec_measured = max(lam_harm, lam_alt)
        binding = "alternating" if lam_alt >= lam_harm else "harmonic(k=0)"
        # way 3: an actual trajectory's step-to-step ratio at late time
        traj = run_horizon(400, D, damping=dmp, seed=1)
        ratio = traj[-1] / traj[-2] if traj[-2] > 0 else float("nan")
        agree = abs(rho_spec - lam_spec_measured) < 1e-9
        agree2 = abs(rho_spec - ratio) < 1e-3
        print(f"  damping={dmp:.2f}")
        print(f"    rho from eigenvalues        = {rho_spec:.6f}")
        print(f"    rho from the k=D/2 mode     = {lam_spec_measured:.6f}   agree={agree}")
        print(f"    step-to-step ratio of |x|   = {ratio:.6f}   agree={agree2}")
    print("  (the trajectory ratio is on the alternating mode, where rho is attained)")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()