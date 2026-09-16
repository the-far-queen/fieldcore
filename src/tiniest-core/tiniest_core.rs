// tiniest_core.rs — minimal kernel of FieldCore (per Grok master plan, full rewrite 2026-09-16).
//
// Mirrors fieldcore/src/tiniest-core/tiniest_core.py.
//
// The three objects:
//   V: working tube.    W: hole.    T: interface.
// Runtime: ψ₀ ∈ V (ground, write-protected). ψ ∈ V (working state) moves in B_R(ψ₀).
//
// The two inequalities (the gate):
//   ||u|| ≤ N_max
//   cos(u, ψ₀) = ⟨u, ψ₀⟩ / (||u|| · ||ψ₀||) ≥ τ
//
// The projected gradient step:
//   F(ψ) = (1/2) ||ψ - ψ₀||²
//   ψ ← Π_{B_R(ψ₀)} (ψ - η (ψ - ψ₀)),    η > 0

use std::f64;

pub const MAX_NORM: f64 = 4.0;
pub const MIN_COS: f64 = 0.4;
pub const DEFAULT_DIM: usize = 16;
pub const DEFAULT_R: f64 = 3.0;
pub const DEFAULT_ETA: f64 = 0.10;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VerdictKind {
    Allow,
    RefuseNorm,
    RefuseCoherence,
    RefuseZero,
}

pub fn gate(emb: &[f64], psi0: &[f64], max_norm: f64, min_cos: f64) -> (bool, VerdictKind) {
    debug_assert_eq!(emb.len(), psi0.len());
    let ne: f64 = emb.iter().map(|x| x * x).sum::<f64>().sqrt();
    if ne > max_norm {
        return (false, VerdictKind::RefuseNorm);
    }
    let n0: f64 = psi0.iter().map(|x| x * x).sum::<f64>().sqrt();
    if ne == 0.0 || n0 == 0.0 {
        return (false, VerdictKind::RefuseZero);
    }
    let dot: f64 = emb.iter().zip(psi0.iter()).map(|(a, b)| a * b).sum();
    let cos = dot / (ne * n0);
    if cos < min_cos {
        return (false, VerdictKind::RefuseCoherence);
    }
    (true, VerdictKind::Allow)
}

pub fn gate_default(emb: &[f64], psi0: &[f64]) -> (bool, VerdictKind) {
    gate(emb, psi0, MAX_NORM, MIN_COS)
}

pub fn energy(psi: &[f64], psi0: &[f64]) -> f64 {
    debug_assert_eq!(psi.len(), psi0.len());
    let s: f64 = psi.iter().zip(psi0.iter()).map(|(a, b)| (a - b).powi(2)).sum();
    0.5 * s
}

pub fn gradient(psi: &[f64], psi0: &[f64]) -> Vec<f64> {
    debug_assert_eq!(psi.len(), psi0.len());
    psi.iter().zip(psi0.iter()).map(|(a, b)| a - b).collect()
}

/// Project ψ onto the closed ball B_R(ψ₀) by radial projection from ψ₀.
pub fn project_ball(psi: &[f64], psi0: &[f64], r: f64) -> Vec<f64> {
    debug_assert_eq!(psi.len(), psi0.len());
    let delta: Vec<f64> = psi.iter().zip(psi0.iter()).map(|(a, b)| a - b).collect();
    let d: f64 = delta.iter().map(|x| x * x).sum::<f64>().sqrt();
    if d <= r || d == 0.0 {
        return psi.to_vec();
    }
    let scale = r / d;
    psi0.iter().zip(delta.iter()).map(|(p, dl)| p + scale * dl).collect()
}

/// One kernel step. Returns (new_psi, allow, kind) for the supplied packet.
/// If packet is None, just step ψ toward ψ₀.
pub fn tick(psi: &mut Vec<f64>, psi0: &[f64], r: f64, eta: f64, packet: Option<&[f64]>) -> (bool, VerdictKind) {
    let drift_before = {
        let delta: Vec<f64> = psi.iter().zip(psi0.iter()).map(|(a, b)| a - b).collect();
        delta.iter().map(|x| x * x).sum::<f64>().sqrt()
    };

    if let Some(p) = packet {
        let (ok, kind) = gate_default(p, psi0);
        if ok {
            let new_psi = project_ball(
                &psi.iter().zip(psi0.iter()).map(|(a, b)| a - eta * (a - b)).collect::<Vec<f64>>(),
                psi0,
                r,
            );
            *psi = new_psi;
        }
        let _ = drift_before; // quiet unused warning
        return (ok, kind);
    }

    let new_psi = project_ball(
        &psi.iter().zip(psi0.iter()).map(|(a, b)| a - eta * (a - b)).collect::<Vec<f64>>(),
        psi0,
        r,
    );
    *psi = new_psi;
    (true, VerdictKind::Allow)
}

pub fn install_ground(dim: usize, axis: usize) -> Vec<f64> {
    let mut g = vec![0.0; dim];
    g[axis] = 1.0;
    g
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx_eq(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn test_gate_high_norm_refused() {
        let psi0 = install_ground(DEFAULT_DIM, 0);
        let bad = vec![5.0; DEFAULT_DIM];
        let (ok, kind) = gate_default(&bad, &psi0);
        assert!(!ok);
        assert_eq!(kind, VerdictKind::RefuseNorm);
    }

    #[test]
    fn test_gate_near_ground_allowed() {
        let psi0 = install_ground(DEFAULT_DIM, 0);
        let mut good = psi0.clone();
        for i in 0..DEFAULT_DIM {
            good[i] += 0.05 * ((i as f64 * 0.1).sin());
        }
        let (ok, kind) = gate_default(&good, &psi0);
        assert!(ok);
        assert_eq!(kind, VerdictKind::Allow);
    }

    #[test]
    fn test_tick_drift_non_increasing() {
        let psi0 = install_ground(DEFAULT_DIM, 0);
        let mut psi = psi0.clone();
        psi[1] = 2.0;
        psi[2] = 2.0;
        let r = DEFAULT_R;
        let eta = DEFAULT_ETA;
        let mut drifts = Vec::new();
        for _ in 0..20 {
            tick(&mut psi, &psi0, r, eta, None);
            let delta: Vec<f64> = psi.iter().zip(psi0.iter()).map(|(a, b)| a - b).collect();
            drifts.push(delta.iter().map(|x| x * x).sum::<f64>().sqrt());
        }
        for i in 0..drifts.len() - 1 {
            assert!(drifts[i] + 1e-9 >= drifts[i + 1], "drift increased at step {}", i);
        }
    }

    #[test]
    fn test_psi0_unchanged_across_ticks() {
        let psi0 = install_ground(DEFAULT_DIM, 0);
        let psi0_before = psi0.clone();
        let mut psi = psi0.clone();
        psi[1] = 2.0;
        for _ in 0..50 {
            tick(&mut psi, &psi0, DEFAULT_R, DEFAULT_ETA, None);
        }
        for i in 0..DEFAULT_DIM {
            assert!(approx_eq(psi0[i], psi0_before[i], 1e-12));
        }
    }
}
