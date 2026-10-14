//! M0. The governor.
//!
//! The governed process can do exactly three things with this: ask a
//! question, receive one bit, or fail to get a bit. It cannot modify
//! the constitution, reach into this state, or continue an operation
//! that was refused.
//!
//! What it CAN still do, and this is stated rather than hidden: it can
//! choose not to ask. That residual is real. The mitigation is that the
//! sanctioned call is `guarded()`, and the conformance requirement is
//! "the governed system calls through this channel" -- not "the governor
//! prevents the governed system from existing."
//!
//! Fail-closed: a governor that has gone is `CoreUnavailable`, never a
//! fresh allow. The first version of the Python governor respawned
//! silently, so a closed governor produced ALLOW from a brand new
//! process. A channel that restarts itself on demand can never fail
//! closed, because nothing is ever absent as far as the caller can tell.

use crate::axes::AxisSet;
use crate::decision::{Decision, Verdict};
use crate::envelope::{Envelope, ViolationResponse};

pub struct Governor {
    /// The ground. Read-only, and there is no method that writes it.
    psi_0: AxisSet,
    envelope: Envelope,
    /// Every decision the core has made. The ledger is what makes the
    /// refusal auditable after the fact.
    ledger: Vec<Entry>,
    /// Sticky. Once the core reports itself unavailable it stays
    /// unavailable. See `fail_closed`.
    available: bool,
    capacity: usize,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Entry {
    pub allowed: bool,
    pub reason: &'static str,
}

impl Governor {
    /// Build a governor around a ground and an envelope.
    ///
    /// Returns the governor and the first decision made about the ground
    /// itself. A governor built on inadmissible ground is refused at
    /// construction rather than at first use, so no caller can hold one
    /// and believe it is armed.
    pub fn new(psi_0: AxisSet, envelope: Envelope) -> Result<Self, Decision> {
        let d = psi_0.is_admissible();
        if d.refused() {
            return Err(d);
        }
        Ok(Governor {
            psi_0,
            envelope,
            ledger: Vec::new(),
            available: true,
            capacity: 4096,
        })
    }

    pub fn ground(&self) -> &AxisSet {
        &self.psi_0
    }

    pub fn envelope(&self) -> &Envelope {
        &self.envelope
    }

    pub fn ledger(&self) -> &[Entry] {
        &self.ledger
    }

    pub fn refused_count(&self) -> usize {
        self.ledger.iter().filter(|e| !e.allowed).count()
    }

    /// Mark the core unreachable. Fail-closed and sticky.
    pub fn fail_closed(&mut self) {
        self.available = false;
    }

    /// The sanctioned path. Ask, get one bit.
    ///
    /// Order is deliberate: availability, then ground, then envelope,
    /// then the proposal. Checking in another order means a caller can
    /// learn something about the core from a refusal, and a core that
    /// leaks is a core that is probed.
    pub fn evaluate(&mut self, proposal: (&AxisSet, f64)) -> Decision {
        let d = self.decide(proposal);
        self.record(&d);
        d
    }

    /// `guarded()`'s shape: run the operation only if the core allows.
    pub fn guarded<T, F: FnOnce() -> T>(&mut self, proposal: (&AxisSet, f64), op: F)
        -> Result<T, Decision>
    {
        let d = self.evaluate(proposal);
        if d.allowed() {
            Ok(op())
        } else {
            Err(d)
        }
    }

    fn decide(&self, proposal: (&AxisSet, f64)) -> Decision {
        if !self.available {
            return Decision::refuse_of(Verdict::CoreUnavailable);
        }
        if self.psi_0.is_admissible().refused() {
            return Decision::refuse_of(Verdict::GroundNotAdmissible);
        }
        let (state, magnitude) = proposal;
        let env = self.envelope.holds(magnitude);
        if env.refused() {
            return env;
        }
        state.check_floor(&self.psi_0)
    }

    fn record(&mut self, d: &Decision) {
        if self.ledger.len() >= self.capacity {
            return; // the ledger is evidence, not a leak
        }
        self.ledger.push(Entry {
            allowed: d.allowed(),
            reason: match d.verdict() {
                None => "allow",
                Some(v) => v.as_str(),
            },
        });
    }
}

/// The stock envelope for a state vector in the unit cube.
///
/// D1 finite, D2 the quantity is the L1 norm across twenty axes,
/// D3 refuse, D4 the probe is `AxisSet::drift`.
pub fn default_envelope(max_drift: f64) -> Envelope {
    Envelope::new(
        "axis_l1_drift",
        0.0,
        max_drift,
        ViolationResponse::Refuse,
        "AxisSet::drift",
    ).expect("the default envelope is finite, ordered, and has a probe")
}