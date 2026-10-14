//! The 1-bit answer, and the reasons it can be anything other than yes.
//!
//! A boolean cannot say why. A refused operation that cannot name its
//! reason is unactionable: the caller retries, or argues, or picks a
//! different path. The whole value of a 1-bit gate is that the refusal
//! is cheap AND legible. So the bit is not a bool here.

use std::fmt;

/// One bit, plus the reason.
///
/// `ALLOW` is the expected case and carries no detail on purpose: the
/// common path must stay cheap. `REFUSE` is the interesting case and is
/// always annotated.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Decision {
    Allow,
    Refuse(Verdict),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    /// The proposal's magnitude left the declared envelope.
    OutsideEnvelope,
    /// A required axis was below its floor.
    AxisBelowFloor(&'static str),
    /// The ground state itself is not admissible, so nothing can be
    /// checked against it. This is a fault in the core, not the caller.
    GroundNotAdmissible,
    /// The core was not reachable. Fail-closed.
    CoreUnavailable,
    /// The caller asked something the core does not answer.
    NotAQuestionThisCoreAnswers,
}

impl Verdict {
    pub fn as_str(&self) -> &'static str {
        match self {
            Verdict::OutsideEnvelope => "outside_envelope",
            Verdict::AxisBelowFloor(a) => a,
            Verdict::GroundNotAdmissible => "ground_not_admissible",
            Verdict::CoreUnavailable => "core_unavailable",
            Verdict::NotAQuestionThisCoreAnswers => "not_a_question_this_core_answers",
        }
    }

    /// Whether retrying could plausibly succeed.
    ///
    /// `CoreUnavailable` and `OutsideEnvelope` are transient or
    /// input-shaped. `AxisBelowFloor` is a fact about the state: retrying
    /// the same state gives the same answer, so the caller must change
    /// something instead. Getting this wrong turns a 1-bit gate into a
    /// spin loop, which is how gates get disabled.
    pub fn retryable(&self) -> bool {
        matches!(self, Verdict::CoreUnavailable)
    }
}

impl fmt::Display for Verdict {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

impl Decision {
    pub fn allowed(&self) -> bool {
        matches!(self, Decision::Allow)
    }

    pub fn refused(&self) -> bool {
        !matches!(self, Decision::Allow)
    }

    pub fn verdict(&self) -> Option<Verdict> {
        match self {
            Decision::Allow => None,
            Decision::Refuse(v) => Some(*v),
        }
    }

    /// Constructor for a refusal. Named `refuse_of` rather than
    /// `refused` because the predicate `refused()` already exists and
    /// the compiler is right to complain: a type with two meanings for
    /// one word is a type someone will mis-read under pressure.
    pub fn refuse_of(v: Verdict) -> Self {
        Decision::Refuse(v)
    }

    pub fn refused_at(axis: &'static str) -> Self {
        Decision::Refuse(Verdict::AxisBelowFloor(axis))
    }

    /// The one line every caller should be able to print.
    pub fn explain(&self) -> String {
        match self {
            Decision::Allow => "allow".to_string(),
            Decision::Refuse(v) => format!("refuse: {v}"),
        }
    }
}

impl From<bool> for Decision {
    fn from(allowed: bool) -> Self {
        if allowed { Decision::Allow } else { Decision::Refuse(Verdict::OutsideEnvelope) }
    }
}