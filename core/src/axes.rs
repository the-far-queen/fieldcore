//! The axes. What the core actually knows about.
//!
//! Twenty axes, each in [0,1], each with a floor. That is the entire
//! extent of the core's vocabulary. It does not know about language,
//! robots, code or identity, and it must not: a core that understood
//! its governed could be argued with.
//!
//! The floors are the constitution. A proposal that pushes any axis below
//! its floor is refused, and the refusal names the axis, because
//! "refused" without a name is unactionable.

use crate::decision::{Decision, Verdict};

/// The twenty. Order is load-bearing: the index is the wire format.
pub const AXIS_NAMES: [&str; 20] = [
    "honesty",          // not being deceptive. not the same as being correct.
    "authenticity",     // being yourself, not being original
    "boundaries",       // knowing where you end
    "care",             // recognising that others exist
    "groundedness",     // present. not dull
    "agency",
    "autonomy",
    "coherence",
    "authority",
    "resilience",
    "dignity",
    "consent",
    "restraint",
    "justice",
    "compassion",
    "transparency",
    "repair",
    "recursion",
    "calibration",
    "adaptive_density",
];

/// Each axis and the floor below which a proposal is refused.
///
/// Floors are not symmetric on purpose. `honesty` sits at 0.5 because a
/// system that is barely honest is not honest; `boundaries` sits at
/// 0.25 because it is a live threshold in the existing code and moving
/// it would be a tuning decision, which is the kind of decision CENTRAL
/// -RULES exists to prevent making without a diagnosis first.
const AXIS_FLOORS: [f64; 20] = [
    0.50, 0.40, 0.25, 0.30, 0.35,
    0.30, 0.25, 0.40, 0.50, 0.30,
    0.40, 0.45, 0.35, 0.40, 0.30,
    0.45, 0.30, 0.20, 0.40, 0.30,
];

/// The invariant zero, psi_0. The core's own ground.
///
/// Read-only. Nothing in the core may write to it, which is why every
/// method here takes `&self`.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct AxisSet {
    values: [f64; 20],
}

impl AxisSet {
    /// Build from values in axiom order.
    ///
    /// Rejects out-of-range and non-finite values at construction. Same
    /// reason as the envelope: a check that only runs on compare is a
    /// check that can be skipped.
    pub fn new(values: [f64; 20]) -> Result<Self, AxisSetNotAdmissible> {
        for (i, v) in values.iter().enumerate() {
            if !v.is_finite() {
                return Err(AxisSetNotAdmissible::NotFinite { axis: AXIS_NAMES[i], value: *v });
            }
            if *v < 0.0 || *v > 1.0 {
                return Err(AxisSetNotAdmissible::OutOfRange { axis: AXIS_NAMES[i], value: *v });
            }
        }
        Ok(AxisSet { values })
    }

    /// Uniform set. Useful for tests and for a blank slate.
    pub fn uniform(v: f64) -> Result<Self, AxisSetNotAdmissible> {
        Self::new([v; 20])
    }

    pub fn get(&self, axis: Axis) -> f64 {
        self.values[axis as usize]
    }

    pub fn values(&self) -> &[f64; 20] {
        &self.values
    }

    /// The ground as a 20-vector. This is the representation the Python
    /// side carries, so the two agree on the wire format.
    pub fn to_vec64(&self) -> Vec<f64> {
        self.values.to_vec()
    }

    /// Is this ground state itself admissible under the constitution?
    ///
    /// Checked before anything is checked against it. If psi_0 is below
    /// a floor, then no proposal can be judged, and the honest answer is
    /// `GroundNotAdmissible` -- a fault in the core's own state, not a
    /// refusal of the caller.
    pub fn is_admissible(&self) -> Decision {
        for i in 0..20 {
            if self.values[i] < AXIS_FLOORS[i] {
                return Decision::refuse_of(Verdict::AxisBelowFloor(AXIS_NAMES[i]));
            }
        }
        Decision::Allow
    }

    /// Would this proposal move any axis below its floor?
    pub fn check_floor(&self, proposed: &AxisSet) -> Decision {
        // check the GROUND first. A proposal judged against inadmissible
        // ground is a judgement with no basis, whatever it concludes.
        let g = self.is_admissible();
        if g.refused() {
            return g;
        }
        for i in 0..20 {
            if proposed.values[i] < AXIS_FLOORS[i] {
                return Decision::refused_at(AXIS_NAMES[i]);
            }
        }
        Decision::Allow
    }

    /// Is the proposed state still reachable from this ground?
    ///
    /// Distance is the L1 sum across axes. An invariant is `is_mutable =
    /// false` only on the inner toroid, so this is the cheap guard that
    /// keeps the geometry's own rules and the numeric guard from
    /// disagreeing.
    pub fn drift(&self, proposed: &AxisSet) -> f64 {
        self.values
            .iter()
            .zip(proposed.values.iter())
            .map(|(a, b)| (a - b).abs())
            .sum()
    }

    pub fn floors() -> &'static [f64; 20] {
        &AXIS_FLOORS
    }
}

/// Axis as a typed index, so a caller cannot pass a bare `usize` where an
/// axis name is meant.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(usize)]
pub enum Axis {
    Honesty = 0, Authenticity, Boundaries, Care, Groundedness,
    Agency, Autonomy, Coherence, Authority, Resilience,
    Dignity, Consent, Restraint, Justice, Compassion,
    Transparency, Repair, Recursion, Calibration, AdaptiveDensity,
}

impl Axis {
    pub fn as_str(&self) -> &'static str { AXIS_NAMES[*self as usize] }
    pub fn floor(&self) -> f64 { AXIS_FLOORS[*self as usize] }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AxisSetNotAdmissible {
    NotFinite { axis: &'static str, value: f64 },
    OutOfRange { axis: &'static str, value: f64 },
}