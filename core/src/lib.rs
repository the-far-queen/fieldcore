//! fieldcore-core — the 1-bit layer, in Rust.
//!
//! WHAT THIS IS. The core of the fieldcore control system. It holds the
//! constitution, evaluates a proposal against it, and returns one bit.
//!
//! WHAT THIS IS NOT. It is not a model, not an orchestrator, and not
//! aware of what it is governing. That blindness is the design, and the
//! reason is in `governor.rs` of the Python system:
//!
//! > On a 747 the flight computer and the pilot are independent systems.
//! > A veto the governed process can decline to call is not a veto.
//!
//! So the core takes an opaque proposal and an opaque ground state, and
//! never inspects either. It knows about bounds, and nothing else. That
//! is what lets one thing govern coding, robot, language and self
//! without knowing any of them.
//!
//! WHY RUST AND NOT PYTHON. Three reasons, in order of weight:
//!
//! 1. `panic = "abort"`. A governor that unwinds can be caught and
//!    continued past. A governor that aborts is a closed process.
//! 2. No garbage collector between the check and the commit. The
//!    Python core's window exists; this one does not.
//! 3. It is fast enough to sit in a reflex loop, so the fast brain and
//!    the slow brain can disagree in the right order.
//!
//! The Python layer stays. This is the part that must not be negotiable.

pub mod decision;
pub mod stalk;
pub mod envelope;
pub mod axes;
pub mod governor;
pub mod ladder;
pub mod sheaf;
pub mod carrier;
pub mod mltr;
pub mod terms;

pub use decision::{Decision, Verdict};
pub use envelope::Envelope;
pub use axes::{Axis, AxisSet, AXIS_NAMES};
pub use governor::Governor;
pub use ladder::{Escalation, Ladder, Termination, Width};
pub use sheaf::{Admission, Candidate, Lang, Refusal, Source};
pub use carrier::{Channel, Equalised, EqualiseError, Frame, Pilot, Stratum};
pub use stalk::{derived_width, measured_population, pair_channel, Stalk, Void};

pub const CORE_VERSION: &str = env!("CARGO_PKG_VERSION");

/// The authority rule, as code rather than as prose.
///
/// SimSelf proposes, M1 audits, Atlas qualifies, M0 commits or refuses.
/// Three of those four steps stand outside the thing being governed.
/// That separation is the architecture.
pub const AUTHORITY_RULE: &str = "PROPOSE -> AUDIT -> QUALIFY -> COMMIT_OR_REFUSE";

/// Fail-closed means this, and it is the property most worth testing:
/// an unavailable core must never be read as consent.
pub fn unavailable() -> Decision {
    Decision::refuse_of(Verdict::CoreUnavailable)
}