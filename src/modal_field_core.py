2 - fieldcore v3.5

"""
FieldCore Modal Implementation – v3.5
======================================
Lineage:
  v3.0  –  merged best of Grok-clean / vector-tensor / v2.1-stabilized
  v3.1  –  Doc4: true vector/tensor evidence, unified transition, self-consistent dream
  v3.2  –  Doc5: Vl projection, z_spec normalization, sign-preserving biorthogonal,
            mix_strength cap 0.8, eta_scale, tensor weight rebalanced
  v3.3  –  Doc7+Doc5§2.3/2.4: full biorthogonalization, amplitude/direction split,
            log-det volume, metric eta_scale, ΔΣ tracking, vector thresholds
  v3.4  –  Doc8 numerical fixes + Doc9 Q7 basis spawning
  v3.5  –  Doc10: seven operator-correctness and spawn-stability patches

Doc10 patches applied:
  I1  Anosov: replace 1D np.interp (destroys 2D structure) with correct bilinear
      periodic interpolation interp2_periodic().  Restores area-preservation and
      correct eigen-spectrum of A for all bases including spawned.
  I2  Eigenbasis alignment after spawn: align_eigenbasis() matches new Vr columns
      to previous Vr by max dot-product, preserving temporal modal continuity.
      Called in recompile_system() before biorthogonalization.
  I3  Spawned basis Gram-Schmidt: new 1-form orthogonalized against all existing
      bases in M-metric before normalization.  Prevents near-singular Gram matrix
      and invalid Minv after spawn.
  I4  Covariance embedding: old cov_evidence[:old_nb,:old_nb] embedded into new
      nb×nb identity*1e-6 instead of full reset.  Preserves learned covariance
      structure across spawns.
  I6  Gram matrix conditioning check in recompile_system() — warns if cond(M)>1e8.
  I7  emerging_vec normalized before use in spawn_basis() — prevents degenerate
      basis construction from a near-zero vector.
  I8  Tighter learn_trigger thresholds (×0.8/×0.4) to widen hysteresis band.
  I9  eta_scale uses mean diagonal of M (more stable than trace/nb under growth).
  I10 Deviation contraction constant scales with 1/num_basis to keep effective
      damping constant as phase space grows.
  Reproj  State reprojection after spawn: c reconstructed by field projection
      onto expanded basis (prevents small projection error accumulation).

Invariants preserved throughout:
  ✓  c0 updated only via η·Hδ  (Resolution Operator, harmonic only)
  ✓  c0 NOT contracted
  ✓  G/C/H separate arrays, Minv-projected
  ✓  Unified transition() shared by step() and dream()
  ✓  Zero-mode-safe Hodge (mask)
  ✓  mix_strength ≤ 0.8
  ✓  Perturbation in run_simulation()

Requirements: numpy, scipy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.fft    import fft2, ifft2, fftfreq
from scipy.linalg import sqrtm

# ─────────────────────────────────────────────────────────────────────────────
# Global constants  (NUM_BASIS_INIT is immutable config; class tracks self.num_basis)
# ─────────────────────────────────────────────────────────────────────────────
PHI            = (1 + np.sqrt(5)) / 2
ALPHA          = 1.0 / PHI          # ≈ 0.6180
NUM_BASIS_INIT = 5                  # initial basis size; class grows from here
SHEAVES        = [(2, 3), (5, 7), (11, 13), (17, 19)]
SHEAVE_NAMES_INIT = ['Σ0-harm', 'Σ1-const', 'Σ2-proc', 'Σ3-reason', 'Σ4-trans']


# ─────────────────────────────────────────────────────────────────────────────
# Basis functions  (canonical 1-forms on T²)
# ─────────────────────────────────────────────────────────────────────────────
def basis_function(k, phi, theta):
    """Return (phi_comp, theta_comp) for canonical basis element k."""
    if k == 0:
        return np.ones_like(phi), np.zeros_like(theta)
    if k - 1 < len(SHEAVES):
        p, q = SHEAVES[k - 1]
        return np.cos(p * phi + q * theta), np.sin(p * phi - q * theta)
    # Spawned bases beyond canonical range — handled via precomputed grid arrays
    raise ValueError(f"basis_function called with k={k} beyond canonical range")


def evaluate_basis_on_grid(N=140):
    """Evaluate the initial 5 canonical basis 1-forms on an N×N regular grid."""
    phi   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    theta = np.linspace(0, 2 * np.pi, N, endpoint=False)
    PHI_g, THETA_g = np.meshgrid(phi, theta, indexing='ij')
    basis_vals = np.zeros((NUM_BASIS_INIT, 2, N, N))
    for k in range(NUM_BASIS_INIT):
        pc, tc = basis_function(k, PHI_g, THETA_g)
        basis_vals[k, 0] = pc
        basis_vals[k, 1] = tc
    return basis_vals, phi, theta


# ─────────────────────────────────────────────────────────────────────────────
# Gram / metric matrix
# ─────────────────────────────────────────────────────────────────────────────
def compute_gram_matrix(basis_vals, N):
    """
    M_ij = ∫ (ω_i · ω_j) dA  over T².
    Returns M, Minv, M_sqrt (real), dA.
    Works for any basis_vals shape (supports post-spawn sizes).
    """
    nb = basis_vals.shape[0]
    dA = (2 * np.pi / N) ** 2
    M  = np.zeros((nb, nb))
    for i in range(nb):
        for j in range(nb):
            M[i, j] = np.sum(
                basis_vals[i, 0] * basis_vals[j, 0] +
                basis_vals[i, 1] * basis_vals[j, 1]
            ) * dA
    Minv   = np.linalg.inv(M)
    M_sqrt = np.real(sqrtm(M))
    return M, Minv, M_sqrt, dA


# ─────────────────────────────────────────────────────────────────────────────
# Hodge decomposition  (zero-mode safe, mask approach)
# ─────────────────────────────────────────────────────────────────────────────
def hodge_decompose_grid(psi_phi, psi_theta, N):
    """Fourier-space Hodge split: ψ = grad f + curl A + harmonic."""
    F_phi   = fft2(psi_phi)
    F_theta = fft2(psi_theta)
    kx = fftfreq(N) * N
    ky = fftfreq(N) * N
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    k2 = KX ** 2 + KY ** 2

    grad_phi   = np.zeros_like(psi_phi)
    grad_theta = np.zeros_like(psi_theta)
    curl_phi   = psi_phi.copy()
    curl_theta = psi_theta.copy()
    harm_phi   = np.full_like(psi_phi,   np.mean(psi_phi))
    harm_theta = np.full_like(psi_theta, np.mean(psi_theta))

    mask = k2 > 1e-10
    kdot = np.zeros_like(k2)
    kdot[mask] = (KX[mask] * F_phi[mask] + KY[mask] * F_theta[mask]) / k2[mask]

    grad_phi[mask]   = np.real(ifft2(KX * kdot))[mask]
    grad_theta[mask] = np.real(ifft2(KY * kdot))[mask]
    curl_phi  -= grad_phi
    curl_theta -= grad_theta

    return grad_phi, grad_theta, curl_phi, curl_theta, harm_phi, harm_theta


# ─────────────────────────────────────────────────────────────────────────────
# Hodge projection matrices  (Minv projection)
# ─────────────────────────────────────────────────────────────────────────────
def compute_decomposition_matrices(basis_vals, N, Minv, dA):
    """G, C, H  — separate allocations, Minv-projected."""
    nb = basis_vals.shape[0]
    G = np.zeros((nb, nb))
    C = np.zeros((nb, nb))
    H = np.zeros((nb, nb))

    for i in range(nb):
        gp, gt, cp, ct, hp, ht = hodge_decompose_grid(
            basis_vals[i, 0], basis_vals[i, 1], N)

        raw_G = np.zeros(nb)
        raw_C = np.zeros(nb)
        raw_H = np.zeros(nb)
        for j in range(nb):
            raw_G[j] = np.sum(gp * basis_vals[j, 0] + gt * basis_vals[j, 1]) * dA
            raw_C[j] = np.sum(cp * basis_vals[j, 0] + ct * basis_vals[j, 1]) * dA
            raw_H[j] = np.sum(hp * basis_vals[j, 0] + ht * basis_vals[j, 1]) * dA

        G[:, i] = Minv @ raw_G
        C[:, i] = Minv @ raw_C
        H[:, i] = Minv @ raw_H

    return G, C, H


# ─────────────────────────────────────────────────────────────────────────────
# Bilinear periodic interpolation  (I1)
# ─────────────────────────────────────────────────────────────────────────────
def interp2_periodic(field, x, y, N):
    """
    Bilinear interpolation of a 2D periodic field at arbitrary (x,y) coords.
    x, y are in [0, 2π); field has shape (N, N).
    All arrays are 2D same shape as x/y.
    Handles periodicity via modular indexing.
    """
    dx = (2.0 * np.pi) / N
    xi = (x / dx) % N
    yi = (y / dx) % N

    x0 = np.floor(xi).astype(int) % N
    y0 = np.floor(yi).astype(int) % N
    x1 = (x0 + 1) % N
    y1 = (y0 + 1) % N

    wx = xi - np.floor(xi)
    wy = yi - np.floor(yi)

    return (
        (1 - wx) * (1 - wy) * field[x0, y0] +
        wx        * (1 - wy) * field[x1, y0] +
        (1 - wx) * wy        * field[x0, y1] +
        wx        * wy        * field[x1, y1]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Anosov mixing matrix  (I1: uses interp2_periodic for all bases)
# ─────────────────────────────────────────────────────────────────────────────
def compute_anosov_matrix(basis_vals, phi_1d, theta_1d, Minv, dA, N):
    """
    A_ji = <ω_j ∘ T, ω_i>_M  where T(φ,θ) = (2φ+θ, φ+θ) mod 2π.
    I1: uses correct bilinear periodic interpolation for both canonical and
    spawned bases, preserving area-preservation and eigen-spectrum of A.
    """
    nb = basis_vals.shape[0]
    PHI_g, THETA_g = np.meshgrid(phi_1d, theta_1d, indexing='ij')
    phiT   = (2 * PHI_g + THETA_g) % (2 * np.pi)
    thetaT = (    PHI_g + THETA_g) % (2 * np.pi)

    A = np.zeros((nb, nb))
    for i in range(nb):
        raw = np.zeros(nb)
        for j in range(nb):
            bj_phi_T   = interp2_periodic(basis_vals[j, 0], phiT, thetaT, N)
            bj_theta_T = interp2_periodic(basis_vals[j, 1], phiT, thetaT, N)
            raw[j] = np.sum(
                basis_vals[i, 0] * bj_phi_T + basis_vals[i, 1] * bj_theta_T
            ) * dA
        A[:, i] = Minv @ raw

    return A


# ─────────────────────────────────────────────────────────────────────────────
# Biorthogonalization helper  (F1: SVD fallback + conditioning check)
# ─────────────────────────────────────────────────────────────────────────────
def biorthogonalize(Vl, Vr, cond_warn=1e8):
    """
    Full biorthogonalization: Vr ← Vr @ inv(Vl.T @ Vr) so Vl.T @ Vr = I.
    F1: uses SVD pseudo-inverse for numerical safety; warns if ill-conditioned.
    Then enforces ⟨Vl_i, Vr_i⟩ = +1 per mode.
    """
    B = Vl.T @ Vr
    cond_B = np.linalg.cond(B)
    if cond_B > cond_warn:
        print(f"  WARNING: biorthogonalization ill-conditioned (cond={cond_B:.2e}); "
              "using SVD pseudo-inverse")

    # SVD-based pseudo-inverse (graceful even near singular)
    U, S_vals, Vt = np.linalg.svd(B)
    S_inv = np.diag([1.0 / s if s > 1e-10 else 0.0 for s in S_vals])
    Vr = Vr @ (Vt.T @ S_inv @ U.T)

    # Sign convention: ⟨Vl_i, Vr_i⟩ = +1
    nb = Vl.shape[1]
    for i in range(nb):
        if float(Vl[:, i] @ Vr[:, i]) < 0:
            Vl[:, i] *= -1.0

    return Vl, Vr


# ─────────────────────────────────────────────────────────────────────────────
# Eigenbasis alignment helper  (I2)
# ─────────────────────────────────────────────────────────────────────────────
def align_eigenbasis(Vr_new, Vr_old):
    """
    Permute columns of Vr_new to best match Vr_old by max absolute dot-product.
    Preserves temporal modal continuity across recompilations.
    Only aligns up to min(nb_new, nb_old) columns; extra columns left in place.
    """
    nb_old = Vr_old.shape[1]
    nb_new = Vr_new.shape[1]
    perm   = list(range(nb_new))
    used   = set()

    for i in range(min(nb_old, nb_new)):
        # Extend Vr_old column i to new size if needed (zero-pad)
        v_old = np.zeros(nb_new)
        v_old[:Vr_old.shape[0]] = Vr_old[:, i]

        sims = [
            abs(float(v_old @ Vr_new[:, j])) if j not in used else -1.0
            for j in range(nb_new)
        ]
        j_best = int(np.argmax(sims))
        perm[i] = j_best
        used.add(j_best)

    # Fill remaining slots with unused indices
    remaining = [j for j in range(nb_new) if j not in used]
    for i in range(min(nb_old, nb_new), nb_new):
        perm[i] = remaining.pop(0)

    return Vr_new[:, perm]


# ─────────────────────────────────────────────────────────────────────────────
# ModalFieldCore  v3.4
# ─────────────────────────────────────────────────────────────────────────────
class ModalFieldCore:
    """
    Self-extending modal field controller on T².

    Basis grows when ΔΣ persistent eigenvector signals a genuinely new direction
    (E_emerg_n > spawn_threshold for spawn_cooldown steps).

    self.num_basis  tracks current live size (starts at NUM_BASIS_INIT, grows ≤ max_basis).
    global NUM_BASIS_INIT is never mutated.

    Constitutional invariant:
      c0 updated only via η · H·δ  (harmonic projection, Resolution Operator).
      No other path may modify c0.
    """

    def __init__(self, basis_vals, phi_1d, theta_1d,
                 G, C, H, A, M, Minv, M_sqrt):
        self.basis_vals = basis_vals.copy()
        self.phi_1d     = phi_1d
        self.theta_1d   = theta_1d
        self.N          = phi_1d.shape[0]
        self.num_basis  = basis_vals.shape[0]     # Q7c: instance var, not global
        self.sheave_names = list(SHEAVE_NAMES_INIT)

        self.G, self.C, self.H, self.A = G.copy(), C.copy(), H.copy(), A.copy()
        self.M, self.Minv, self.M_sqrt = M.copy(), Minv.copy(), M_sqrt.copy()

        # Biorthogonal eigenbasis of L = α G A  (F1: SVD fallback)
        L = ALPHA * G @ A
        _, Vr = np.linalg.eig(L)
        _, Vl = np.linalg.eig(L.T)
        Vl, Vr = biorthogonalize(np.real(Vl), np.real(Vr))
        self.Vr = Vr
        self.Vl = Vl
        self.L  = np.real(L)

        # State
        self.c  = np.zeros(self.num_basis)
        self.c0 = np.zeros(self.num_basis)
        self.set_ground()

        # Governor hyper-parameters
        self.lambda_      = 0.1
        self.eta_max      = 0.05
        self.gamma        = 0.2
        self.eta_scale    = float(np.sqrt(np.trace(M) / self.num_basis))  # Q4 metric-norm

        # Q6: vector threshold parameters
        self.thresh_S     = 0.45
        self.thresh_E     = 0.20
        self.thresh_u     = 0.25
        self.thresh_emerg = 0.30

        # F6: mode dwell timer
        self.min_dwell    = 4          # minimum steps before switching mode
        self.mode_timer   = 0

        self.exploit_mode = True       # start in learning mode

        # Scalar evidence (summary only — no longer drives switching)
        self.evidence = 0.0

        # Vector + tensor evidence
        self.z_evidence   = np.zeros(2 * self.num_basis)
        self.cov_evidence = np.eye(self.num_basis) * 1e-6
        self.prev_cov     = np.eye(self.num_basis) * 1e-6
        self.emerging_vec = np.zeros(self.num_basis)

        # Running state
        self.prev_energy       = 1e-10
        self.dream_uncertainty = 0.0

        # Q7: basis spawning control
        self.spawn_threshold = 0.35
        self.max_basis       = 8
        self.spawn_cooldown  = 15
        self.last_spawn_step = -1000

        self.history = []

    # ── Constitutional ground ────────────────────────────────────────────────
    def set_ground(self):
        """Σ1 = constitutional dominant."""
        self.c0[:] = 0.0
        self.c0[1] = 1.0
        self.c[:]  = self.c0

    # ── M-norm H¹ deviation ──────────────────────────────────────────────────
    def h1_deviation(self):
        d = self.c - self.c0
        return np.sqrt(max(float(d @ self.M @ d), 0.0))

    # ── Unified transition ───────────────────────────────────────────────────
    def transition(self, c, c0, G, H, A, alpha, learning, eta, mix_strength=0.0):
        """
        Constitutional update: Δc0 = η·Hδ (harmonic only).
        Anosov blend only in exploration, strength ≤ 0.8.
        """
        delta  = c - c0
        harm   = H @ delta
        grad   = G @ delta
        target = c0 + harm + alpha * grad
        c_next = (1.0 - self.gamma) * c + self.gamma * target

        if (not learning) and mix_strength > 0.0:
            c_next = (1.0 - mix_strength) * c_next + mix_strength * (A @ c_next)

        c0_next = c0 + eta * harm if (eta > 0.0 and learning) else c0.copy()

        return c_next, c0_next

    # ── Dream bundle ─────────────────────────────────────────────────────────
    def dream(self, n_roll=8, K=6):
        """
        K rollouts for predictive covariance.

        F5: perturb ck in coefficient space (not operators).
            Operator jitter (v3.3) broke Hodge orthogonality and Anosov structure.
            Coefficient perturbation samples different trajectories while preserving
            the geometric integrity of G, H, A.
        """
        nb      = self.num_basis
        futures = []
        eps     = 0.01   # coefficient perturbation scale

        for _ in range(K):
            ck  = self.c.copy() + eps * np.random.randn(nb)   # F5: perturb state
            c0k = self.c0.copy()

            for _ in range(n_roll):
                local_dev = np.sqrt(max(float((ck - c0k) @ self.M @ (ck - c0k)), 0.0))
                eta_k = self.eta_max * (1.0 - np.tanh(local_dev / self.eta_scale))
                ms_k  = np.clip(self.evidence, 0.0, 0.8) if not self.exploit_mode else 0.0
                ck, c0k = self.transition(
                    ck, c0k, self.G, self.H, self.A, ALPHA,
                    self.exploit_mode, eta_k, ms_k
                )
            futures.append(ck)

        futures = np.array(futures)
        mean_f  = futures.mean(axis=0)
        dev     = futures - mean_f
        Z       = (self.M_sqrt @ dev.T).T
        cov     = (Z.T @ Z) / K
        unc     = np.trace(cov) / nb

        return mean_f, float(unc), cov

    # ── Q7a: Construct new basis 1-form from emerging_vec ───────────────────
    def construct_basis_from_vector(self, vec):
        """
        Lift coefficient-space direction vec (R^nb) into a function-space 1-form.
        I3: Gram-Schmidt orthogonalization against existing bases in M-metric
            prevents near-singular Gram matrix and invalid Minv after spawn.
        Returns shape (2, N, N).
        """
        nb = len(vec)
        psi_phi   = np.zeros((self.N, self.N))
        psi_theta = np.zeros((self.N, self.N))

        for k in range(nb):
            psi_phi   += vec[k] * self.basis_vals[k, 0]
            psi_theta += vec[k] * self.basis_vals[k, 1]

        dA = (2 * np.pi / self.N) ** 2

        # I3: M-metric Gram-Schmidt — remove projection onto each existing basis
        for k in range(self.num_basis):
            proj = (np.sum(psi_phi   * self.basis_vals[k, 0] +
                           psi_theta * self.basis_vals[k, 1]) * dA)
            psi_phi   -= proj * self.basis_vals[k, 0]
            psi_theta -= proj * self.basis_vals[k, 1]

        # Renormalize in L² (dA-weighted)
        norm = np.sqrt(max(np.sum(psi_phi**2 + psi_theta**2) * dA, 1e-10))
        psi_phi   /= norm
        psi_theta /= norm

        return np.stack([psi_phi, psi_theta])   # (2, N, N)

    # ── Q7b: Recompile all operators after basis expansion ───────────────────
    def recompile_system(self):
        """
        Recompute M, G, C, H, A, L, Vl, Vr after appending a new basis element.
        Expand c, c0 and reproject state onto new basis.
        Embed old covariance into expanded structure (I4).
        I2: align new eigenbasis to old for temporal continuity.
        I6: warn if Gram matrix ill-conditioned.
        Reproj: reproject c onto new basis to minimise projection error.
        """
        old_nb = self.num_basis - 1   # size before this spawn
        nb     = self.num_basis

        M, Minv, M_sqrt, dA = compute_gram_matrix(self.basis_vals, self.N)

        # I6: Gram matrix conditioning check
        cond_M = np.linalg.cond(M)
        if cond_M > 1e8:
            print(f"  WARNING: Gram matrix ill-conditioned after spawn "
                  f"(cond={cond_M:.2e})")

        G, C, H = compute_decomposition_matrices(self.basis_vals, self.N, Minv, dA)
        A = compute_anosov_matrix(
            self.basis_vals, self.phi_1d, self.theta_1d, Minv, dA, self.N)

        self.M, self.Minv, self.M_sqrt = M, Minv, M_sqrt
        self.G, self.C, self.H, self.A = G, C, H, A

        # I2: rebuild eigenbasis with alignment to previous Vr
        L = ALPHA * G @ A
        _, Vr_raw = np.linalg.eig(L)
        _, Vl_raw = np.linalg.eig(L.T)
        Vr_raw = np.real(Vr_raw)
        Vl_raw = np.real(Vl_raw)

        if hasattr(self, 'Vr') and self.Vr.shape[1] > 0:
            Vr_raw = align_eigenbasis(Vr_raw, self.Vr)

        Vl_raw, Vr_raw = biorthogonalize(Vl_raw, Vr_raw)
        self.Vr, self.Vl, self.L = Vr_raw, Vl_raw, np.real(L)

        # I9: eta_scale via mean diagonal (more stable under dimension growth)
        self.eta_scale = float(np.sqrt(np.mean(np.diag(M))))

        # Reproj: reconstruct field from old c and reproject onto new basis
        # Minimises projection error from trivial zero-padding
        old_c = self.c.copy()
        psi_phi   = sum(old_c[k] * self.basis_vals[k, 0] for k in range(old_nb))
        psi_theta = sum(old_c[k] * self.basis_vals[k, 1] for k in range(old_nb))
        raw_proj  = np.array([
            np.sum(psi_phi * self.basis_vals[j, 0] +
                   psi_theta * self.basis_vals[j, 1]) * dA
            for j in range(nb)
        ])
        self.c  = Minv @ raw_proj

        # c0: expand by zero-padding only (constitutional floor is discrete, not a field)
        c0_old = self.c0.copy()
        self.c0 = np.zeros(nb)
        self.c0[:old_nb] = c0_old

        # I4: embed old covariance into expanded structure
        old_cov = self.cov_evidence.copy()
        new_cov = np.eye(nb) * 1e-6
        new_cov[:old_nb, :old_nb] = old_cov
        self.cov_evidence = new_cov.copy()

        old_prev = self.prev_cov.copy()
        new_prev = np.eye(nb) * 1e-6
        new_prev[:old_nb, :old_nb] = old_prev
        self.prev_cov = new_prev.copy()

        # Reset directional evidence (dimensionality changed)
        self.z_evidence   = np.zeros(2 * nb)
        self.emerging_vec = np.zeros(nb)

    # ── Q7c: Spawn new basis mode ────────────────────────────────────────────
    def spawn_basis(self, step):
        """
        Materialize a new basis 1-form from emerging_vec; recompile operators.
        Hard cap at max_basis; cooldown prevents rapid successive spawns.
        I7: emerging_vec normalized before use to prevent degenerate construction.
        """
        if self.num_basis >= self.max_basis:
            return
        if step - self.last_spawn_step < self.spawn_cooldown:
            return

        # I7: normalize emerging_vec
        v = self.emerging_vec.copy()
        v_norm = np.linalg.norm(v)
        if v_norm < 1e-10:
            return   # degenerate — no meaningful direction to spawn
        v /= v_norm

        new_elem = self.construct_basis_from_vector(v)  # (2, N, N)

        # Append to basis array
        self.basis_vals = np.concatenate(
            [self.basis_vals, new_elem[np.newaxis, ...]], axis=0
        )
        self.num_basis += 1
        self.sheave_names.append(f'Σ{self.num_basis-1}-spawned')
        self.last_spawn_step = step

        print(f"  [Q7] Step {step}: spawned basis mode {self.num_basis-1}. "
              f"Total basis = {self.num_basis}")

        self.recompile_system()

    # ── Single heartbeat ─────────────────────────────────────────────────────
    def step(self):
        nb = self.num_basis
        delta  = self.c - self.c0
        energy = float(delta @ self.M @ delta)
        dE     = energy - self.prev_energy
        self.prev_energy = max(energy, 1e-10)

        # Dream → tensor evidence
        _, self.dream_uncertainty, cov_new = self.dream()

        # Q5: ΔΣ temporal tracking
        delta_cov   = cov_new - self.prev_cov
        self.prev_cov = cov_new.copy()
        delta_eigvals   = np.linalg.eigvalsh(delta_cov)
        emerging_lambda = max(float(delta_eigvals[-1]), 0.0)
        if emerging_lambda > 1e-10:
            _, delta_vecs      = np.linalg.eigh(delta_cov)
            self.emerging_vec  = delta_vecs[:, -1].copy()
        E_emerg_n = emerging_lambda / (1.0 + emerging_lambda)

        # Q7d: spawn trigger (before operator-dependent computations below)
        self.spawn_basis(len(self.history))
        # After potential spawn, nb may have changed — re-read
        nb    = self.num_basis
        delta = self.c - self.c0          # recompute after possible expand

        # Leaky tensor integration
        self.cov_evidence = (
            (1.0 - self.lambda_) * self.cov_evidence +
            self.lambda_ * cov_new
        )

        # Q2: Spectral amplitude / direction (Q1 biortho ensures exact modal decomp)
        L_delta    = self.L @ delta
        growth     = np.real(self.Vl.T @ L_delta)
        growth_pos = np.maximum(growth, 0.0)
        S_amp      = float(np.linalg.norm(growth_pos))
        z_spec     = growth_pos / S_amp if S_amp > 1e-10 else growth_pos
        S_amp_n    = S_amp / (1.0 + S_amp)

        # Geometric evidence channel
        z_geom = self.M_sqrt @ delta         # whitened R^nb

        z_full = np.concatenate([z_geom, z_spec])
        self.z_evidence = (
            (1.0 - self.lambda_) * self.z_evidence +
            self.lambda_ * z_full
        )

        # Feature extraction
        E = float(np.linalg.norm(self.z_evidence[:nb]))
        # F2: norm not sum (invariant under basis rotation)
        S = float(np.linalg.norm(self.z_evidence[nb:]))
        u = self.dream_uncertainty

        E_n = E / (1.0 + E)
        S_n = S / (1.0 + S)

        # Tensor features
        eigvals    = np.linalg.eigvalsh(self.cov_evidence)
        lambda_max = float(eigvals[-1])
        trace_cov  = float(np.sum(eigvals))
        anisotropy = lambda_max / (trace_cov + 1e-8)
        T_n        = lambda_max / (1.0 + lambda_max)

        # Q3: Log-det volume (F3: correct slogdet sign handling)
        sign, log_abs = np.linalg.slogdet(
            self.cov_evidence + 1e-8 * np.eye(nb))
        if sign <= 0:
            log_det = -float('inf')    # F3: negative/zero det → covariance collapsed
        else:
            log_det = float(log_abs)
        V_n = 0.5 * (1.0 + np.tanh(log_det / (2.0 * nb)))

        # Q6 + I8: Vector threshold mode switching + dwell timer
        # I8: learn thresholds tightened (×0.8/×0.4) to widen hysteresis band
        explore_trigger = (S_n > self.thresh_S) or (E_emerg_n > self.thresh_emerg)
        learn_trigger   = (E_n < self.thresh_E * 0.8 and
                           u   < self.thresh_u * 0.8 and
                           S_n < self.thresh_S * 0.4)

        self.mode_timer += 1
        if explore_trigger and self.mode_timer >= self.min_dwell:
            self.exploit_mode = False
            self.mode_timer   = 0
        elif learn_trigger and self.mode_timer >= self.min_dwell:
            self.exploit_mode = True
            self.mode_timer   = 0

        # Unified control signal
        control = (
            0.20 * E_n     +
            0.20 * S_n     +
            0.15 * S_amp_n +
            0.15 * u       +
            0.15 * T_n     +
            0.15 * V_n
        )

        # Scalar evidence (low-pass diagnostic summary)
        self.evidence = (
            (1.0 - self.lambda_) * self.evidence +
            self.lambda_ * control
        )

        # Continuous eta
        eta = self.eta_max * (1.0 - np.tanh(control)) if self.exploit_mode else 0.0

        # Mix strength: amplitude + direction, capped at 0.8
        if not self.exploit_mode:
            mix_strength = np.clip(0.6 * S_n + 0.4 * S_amp_n, 0.0, 0.8)
        else:
            mix_strength = 0.0

        # Apply unified transition
        self.c, self.c0 = self.transition(
            self.c, self.c0,
            self.G, self.H, self.A,
            ALPHA, self.exploit_mode, eta, mix_strength
        )

        # F4 + I10: Contract deviation (not absolute state); constant scales with 1/nb
        # I10: prevents over-damping as phase space grows with spawned bases
        contraction = 1e-3 / nb
        self.c = self.c0 + (self.c - self.c0) * (1.0 - contraction)

        self.history.append({
            'step':         len(self.history),
            'num_basis':    nb,
            'h1':           self.h1_deviation(),
            'evidence':     self.evidence,
            'exploit':      self.exploit_mode,
            'growth':       max(dE, 0.0),
            'uncertainty':  self.dream_uncertainty,
            'control':      control,
            'E_n':          E_n,
            'S_n':          S_n,
            'S_amp_n':      S_amp_n,
            'T_n':          T_n,
            'V_n':          V_n,
            'E_emerg_n':    E_emerg_n,
            'anisotropy':   anisotropy,
            'lambda_max':   lambda_max,
            'explore_trig': explore_trigger,
            'learn_trig':   learn_trigger,
            'c':            self.c.copy(),
            'c0':           self.c0.copy(),
        })

    # ── Perturbation ─────────────────────────────────────────────────────────
    def perturb(self, strength=0.8, sheave_idx=1):
        self.c[sheave_idx] += strength

    # ── Run ──────────────────────────────────────────────────────────────────
    def run_simulation(self, n_steps=120, perturb_step=10,
                       perturb_strength=0.8, sheave_idx=1):
        for s in range(n_steps):
            if s == perturb_step:
                self.perturb(perturb_strength, sheave_idx)
            self.step()
        return self.history


# ─────────────────────────────────────────────────────────────────────────────
# Precomputation
# ─────────────────────────────────────────────────────────────────────────────
def precompute(N=140):
    print("→ Evaluating basis functions on grid...")
    basis_vals, phi_1d, theta_1d = evaluate_basis_on_grid(N)

    print("→ Computing Gram matrix...")
    M, Minv, M_sqrt, dA = compute_gram_matrix(basis_vals, N)

    print("→ Computing Hodge matrices (G, C, H)...")
    G, C, H = compute_decomposition_matrices(basis_vals, N, Minv, dA)

    print("→ Computing Anosov matrix (A)...")
    A = compute_anosov_matrix(basis_vals, phi_1d, theta_1d, Minv, dA, N)

    return basis_vals, phi_1d, theta_1d, M, Minv, M_sqrt, G, C, H, A


# ─────────────────────────────────────────────────────────────────────────────
# Visualization  (adaptive to variable num_basis)
# ─────────────────────────────────────────────────────────────────────────────
def visualize(history, basis_vals_final=None, perturb_step=10):
    steps      = [h['step']       for h in history]
    h1         = [h['h1']         for h in history]
    evidence   = [h['evidence']   for h in history]
    exploit    = [h['exploit']    for h in history]
    control    = [h['control']    for h in history]
    E_n        = [h['E_n']        for h in history]
    S_n        = [h['S_n']        for h in history]
    S_amp_n    = [h['S_amp_n']    for h in history]
    T_n        = [h['T_n']        for h in history]
    V_n        = [h['V_n']        for h in history]
    E_emerg_n  = [h['E_emerg_n']  for h in history]
    anisotropy = [h['anisotropy'] for h in history]
    expl_trig  = [h['explore_trig'] for h in history]
    learn_trig = [h['learn_trig']   for h in history]
    num_basis  = [h['num_basis']    for h in history]

    # Detect spawn events
    spawn_steps = [h['step'] for i, h in enumerate(history)
                   if i > 0 and h['num_basis'] > history[i-1]['num_basis']]

    fig, axs = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle(
        f"FieldCore v3.5 – Operator-Correct Self-Extending System  "
        f"(final basis: {history[-1]['num_basis']})",
        fontsize=13, fontweight='bold')

    def vline_all(ax):
        ax.axvline(perturb_step, color='gray', ls='--', lw=1, alpha=0.7)
        for ss in spawn_steps:
            ax.axvline(ss, color='gold', ls=':', lw=1.2, alpha=0.9)

    # ── H¹ deviation ────────────────────────────────────────────────────────
    ax = axs[0, 0]
    ax.plot(steps, h1, 'b-', lw=1.5, label='M-norm H¹')
    vline_all(ax)
    if h1:
        ax.fill_between(steps, 0, max(h1)*1.05,
                        where=exploit, color='lime', alpha=0.1)
    ax.set_ylabel('deviation');  ax.set_xlabel('step')
    ax.legend(fontsize=7, handles=ax.lines[:1] + [
        plt.Line2D([0],[0], color='gold', ls=':', label='spawn event')])
    ax.grid(alpha=0.3);  ax.set_title('Constitutional Deviation')

    # ── Basis size over time ─────────────────────────────────────────────────
    ax = axs[0, 1]
    ax.step(steps, num_basis, 'darkviolet', lw=1.5, where='post', label='num_basis')
    ax.axhline(8, color='r', ls='--', alpha=0.5, label='max_basis=8')
    vline_all(ax)
    ax.set_xlabel('step');  ax.set_ylabel('basis size')
    ax.legend(fontsize=8);  ax.grid(alpha=0.3)
    ax.set_title('Basis Dimension Growth (Q7)')

    # ── All evidence channels ────────────────────────────────────────────────
    ax = axs[0, 2]
    ax.plot(steps, E_n,      'steelblue',  lw=1.2, label='E_n   geometric')
    ax.plot(steps, S_n,      'crimson',    lw=1.2, label='S_n   spec dir')
    ax.plot(steps, S_amp_n,  'firebrick',  lw=1.0, ls='--', label='S_amp_n')
    ax.plot(steps, T_n,      'darkorange', lw=1.2, label='T_n   λ_max')
    ax.plot(steps, V_n,      'purple',     lw=1.2, label='V_n   log-det')
    ax.plot(steps, E_emerg_n,'teal',       lw=1.0, ls=':', label='E_emerg ΔΣ')
    vline_all(ax)
    ax.axhline(0.35, color='gold', ls=':', alpha=0.5, label='spawn θ')
    ax.set_xlabel('step');  ax.set_ylabel('[0,1]')
    ax.legend(fontsize=6);  ax.grid(alpha=0.3)
    ax.set_title('Evidence Channels')

    # ── Governor ─────────────────────────────────────────────────────────────
    ax = axs[1, 0]
    ax.plot(steps, evidence, 'orange', lw=1.5, label='evidence (summary)')
    ax.plot(steps, control,  'gray',   lw=0.8, ls=':', label='control')
    ax.fill_between(steps, 0, 1, where=[bool(e) for e in expl_trig],
                    color='salmon', alpha=0.15, label='explore trigger')
    ax.fill_between(steps, 0, 1, where=[bool(l) for l in learn_trig],
                    color='lime', alpha=0.15, label='learn trigger')
    vline_all(ax)
    ax.set_ylim(-0.05, 1.05);  ax.set_xlabel('step')
    ax.legend(fontsize=6);  ax.grid(alpha=0.3)
    ax.set_title('Governor – Vector Thresholds (Q6) + Dwell (F6)')

    # ── ΔΣ emerging instability ──────────────────────────────────────────────
    ax = axs[1, 1]
    ax.plot(steps, E_emerg_n, 'teal', lw=1.4, label='E_emerg_n')
    ax.axhline(0.35, color='gold', ls=':', lw=1.2, label='spawn θ=0.35')
    ax.axhline(0.30, color='r',    ls='--', alpha=0.6, label='explore θ')
    vline_all(ax)
    ax.set_xlabel('step');  ax.set_ylabel('normalised')
    ax.legend(fontsize=8);  ax.grid(alpha=0.3)
    ax.set_title('ΔΣ Emerging Direction (Q5)')

    # ── φ-decay fingerprint ──────────────────────────────────────────────────
    ax = axs[1, 2]
    if len(h1) > 1:
        peak_idx = int(np.argmax(h1))
        after = np.array(h1[peak_idx:])
        if len(after) > 1 and after[0] > 1e-10:
            after_norm = after / after[0]
            n     = np.arange(len(after_norm))
            phi_d = ALPHA ** n
            exp_d = np.exp(-0.5 * n)
            ax.plot(n, after_norm, 'b-',  lw=1.5, label='measured')
            ax.plot(n, phi_d,      'g--', lw=1.2, label=f'φ⁻ⁿ')
            ax.plot(n, exp_d,      'r:',  lw=1.2, label='exp(-0.5n)')
            ax.set_xlabel('steps after peak');  ax.set_ylabel('norm H¹')
            ax.legend(fontsize=8);  ax.grid(alpha=0.3)
            ax.set_title('φ-Decay Fingerprint')
            if len(after_norm) >= 5:
                r2, r4 = after_norm[1], after_norm[3]
                ratio  = r2 / r4 if abs(r4) > 1e-10 else float('nan')
                ax.text(0.05, 0.82,
                        f'r₂/r₄ ≈ {ratio:.3f}\nφ² = {PHI**2:.3f}',
                        transform=ax.transAxes, va='top', fontsize=11,
                        bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'))

    # ── Coefficient trajectories (first 5 canonical only) ───────────────────
    ax = axs[2, 0]
    # Use first NUM_BASIS_INIT entries; spawned modes may have different lengths
    max_k = min(NUM_BASIS_INIT, history[-1]['num_basis'])
    colours = ['C0', 'C1', 'C2', 'C3', 'C4']
    for k in range(max_k):
        # Some history entries may be pre-spawn (shorter c vector)
        c_vals  = [h['c'][k]  if k < len(h['c'])  else 0.0 for h in history]
        c0_vals = [h['c0'][k] if k < len(h['c0']) else 0.0 for h in history]
        col = colours[k]
        ax.plot(steps, c_vals,  col, lw=1.0, label=SHEAVE_NAMES_INIT[k])
        ax.plot(steps, c0_vals, col, lw=0.5, ls='--', alpha=0.5)
    vline_all(ax)
    ax.set_xlabel('step');  ax.set_ylabel('coefficient')
    ax.legend(fontsize=7);  ax.grid(alpha=0.3)
    ax.set_title('Coefficient Trajectories  (solid=c, dashed=c₀)')

    # ── Constitutional floor stability ───────────────────────────────────────
    ax = axs[2, 1]
    c0_norms = [np.linalg.norm(h['c0']) for h in history]
    ax.plot(steps, c0_norms, 'darkgreen', lw=1.4, label='||c₀||')
    ax.axhline(1.0, color='gray', ls=':', alpha=0.5)
    vline_all(ax)
    ax.set_xlabel('step');  ax.set_ylabel('norm')
    ax.legend(fontsize=8);  ax.grid(alpha=0.3)
    ax.set_title('Constitutional Floor Stability  (should stay ≈ 1)')

    # ── Final field (φ-component) ────────────────────────────────────────────
    ax = axs[2, 2]
    if basis_vals_final is not None:
        c_final = history[-1]['c']
        nb_f    = min(len(c_final), basis_vals_final.shape[0])
        psi_phi = sum(c_final[k] * basis_vals_final[k, 0] for k in range(nb_f))
        im = ax.imshow(psi_phi,
                       extent=[0, 2*np.pi, 0, 2*np.pi],
                       origin='lower', cmap='RdBu_r', aspect='equal')
        ax.set_title('Final Field – φ Component')
        ax.set_xlabel('φ');  ax.set_ylabel('θ')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    N = 140

    basis_vals, phi_1d, theta_1d, M, Minv, M_sqrt, G, C, H, A = precompute(N)

    print("→ Initialising ModalFieldCore v3.5...")
    core = ModalFieldCore(
        basis_vals, phi_1d, theta_1d,
        G, C, H, A, M, Minv, M_sqrt
    )

    print("→ Running simulation  (120 steps, perturbation at step 10)...")
    history = core.run_simulation(
        n_steps=120,
        perturb_step=10,
        perturb_strength=0.8,
        sheave_idx=1
    )

    print(f"→ Simulation complete.  Final basis size: {core.num_basis}")
    if core.num_basis > NUM_BASIS_INIT:
        print(f"   Spawns occurred at steps: "
              f"{[h['step'] for i,h in enumerate(history) if i>0 and h['num_basis']>history[i-1]['num_basis']]}")

    print("→ Visualising...")
    visualize(history, core.basis_vals, perturb_step=10)

    print("Done.")