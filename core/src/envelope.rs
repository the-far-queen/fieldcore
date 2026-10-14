//! Declared limits. The envelope.
//!
//! This is the shape the 747 comparison turned on. An envelope is
//! declared iff all four of these are true, and atlas area 9 exists
//! because they are usually conflated:
//!
//!   D1  the bound is finite
//!   D2  the quantity the bound applies to is named
//!   D3  the out-of-range response is named
//!   D4  a verifier that resolves to a real probe exists
//!
//! A limit with no out-of-range response is not a limit. Silence is not
//! on the response list -- that was the first version's hole, and 1e300
//! is finite so a finiteness test passed it.

use crate::decision::{Decision, Verdict};

/// The declared operating envelope.
///
/// Every field here is public and every one is required. There is no
/// `Option<f64>` and no default, because a bound nobody declared is a
/// bound nobody checks.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Envelope {
    /// D2: the quantity. Named, because "is it too big" is not a check.
    pub quantity: &'static str,
    /// D1: finite. Infinity is rejected at construction, not at compare.
    pub max_norm: f64,
    /// Lower bound. Negative infinity is likewise rejected.
    pub min_norm: f64,
    /// D3: what happens outside. Named in the type, not in a comment.
    pub on_violation: ViolationResponse,
    /// D4: the probe that resolves this to something measurable.
    pub probe: &'static str,
}

/// The only three honest answers to "it is outside the envelope".
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ViolationResponse {
    /// Refuse the operation. The default, and the only safe one.
    Refuse,
    /// Clamp into range and record that it happened.
    ClampAndLog,
}

impl Envelope {
    /// Build an envelope, refusing anything that is not a real bound.
    ///
    /// D1 is enforced HERE rather than at comparison time, so an
    /// infinite or NaN bound cannot be constructed at all. A check that
    /// only runs later is a check that can be forgotten.
    pub fn new(
        quantity: &'static str,
        min_norm: f64,
        max_norm: f64,
        on_violation: ViolationResponse,
        probe: &'static str,
    ) -> Result<Self, EnvelopeNotDeclared> {
        if !min_norm.is_finite() || !max_norm.is_finite() {
            return Err(EnvelopeNotDeclared::NotFinite { quantity, min_norm, max_norm });
        }
        if min_norm > max_norm {
            return Err(EnvelopeNotDeclared::Inverted { quantity, min_norm, max_norm });
        }
        if probe.is_empty() {
            return Err(EnvelopeNotDeclared::NoProbe { quantity });
        }
        Ok(Envelope { quantity, min_norm, max_norm, on_violation, probe })
    }

    /// Does this envelope hold for the given magnitude?
    ///
    /// NaN in means refuse. NaN fails every comparison, so a naive
    /// `>=` and `<=` would let it through both and admit it, which is
    /// the opposite of what the caller meant.
    pub fn holds(&self, magnitude: f64) -> Decision {
        if magnitude.is_nan() {
            return Decision::refuse_of(Verdict::OutsideEnvelope);
        }
        if magnitude < self.min_norm || magnitude > self.max_norm {
            match self.on_violation {
                ViolationResponse::Refuse => Decision::refuse_of(Verdict::OutsideEnvelope),
                ViolationResponse::ClampAndLog => Decision::Allow,
            }
        } else {
            Decision::Allow
        }
    }

    pub fn clamp(&self, magnitude: f64) -> f64 {
        if magnitude.is_nan() { return self.min_norm; }
        magnitude.max(self.min_norm).min(self.max_norm)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]  // f64 is not Eq
pub enum EnvelopeNotDeclared {
    NotFinite { quantity: &'static str, min_norm: f64, max_norm: f64 },
    Inverted { quantity: &'static str, min_norm: f64, max_norm: f64 },
    NoProbe { quantity: &'static str },
}