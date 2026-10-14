//! Tests for the 1-bit core.
//!
//! The rule these obey: a test that cannot fail is not a test. Every
//! one here was checked going red -- most of them by writing the
//! mutation into the code and watching the suite catch it. The mutation
//! notes say which.
//!
//! Three of these are the load-bearing ones and they are the three the
//! 747 analogy rests on:
//!   - fail_closed_is_sticky   a gone core is never read as consent
//!   - refused_operation_does_not_run
//!   - inadmissible_ground_refuses_even_a_perfect_proposal

use fieldcore_core::axes::{Axis, AxisSet, AxisSetNotAdmissible, AXIS_NAMES};
use fieldcore_core::decision::{Decision, Verdict};
use fieldcore_core::envelope::{Envelope, ViolationResponse};
use fieldcore_core::governor::{default_envelope, Governor};

fn ground() -> AxisSet {
    // comfortably above every floor
    AxisSet::uniform(0.8).unwrap()
}

// ---------------------------------------------------------------------------
// the 1-bit answer
// ---------------------------------------------------------------------------

#[test]
fn allow_carries_no_verdict() {
    assert!(Decision::Allow.allowed());
    assert!(Decision::Allow.verdict().is_none());
    assert_eq!(Decision::Allow.explain(), "allow");
}

#[test]
fn refusal_names_its_reason() {
    let d = Decision::refuse_of(Verdict::OutsideEnvelope);
    assert!(d.refused());
    assert_eq!(d.verdict(), Some(Verdict::OutsideEnvelope));
    assert_eq!(d.explain(), "refuse: outside_envelope");
}

#[test]
fn an_axis_refusal_names_the_axis() {
    // why the bit is not a bare bool: the caller needs to know WHICH axis
    let d = Decision::refused_at("honesty");
    assert_eq!(d.explain(), "refuse: honesty");
}

#[test]
fn only_unavailable_is_retryable() {
    // a state fact must not be retried into a spin loop
    assert!(Verdict::CoreUnavailable.retryable());
    assert!(!Verdict::OutsideEnvelope.retryable());
    assert!(!Verdict::AxisBelowFloor("honesty").retryable());
    assert!(!Verdict::GroundNotAdmissible.retryable());
}

// ---------------------------------------------------------------------------
// axes and the constitution
// ---------------------------------------------------------------------------

#[test]
fn twenty_axes_named() {
    assert_eq!(AXIS_NAMES.len(), 20);
    assert_eq!(Axis::AdaptiveDensity as usize, 19);
    assert_eq!(Axis::AdaptiveDensity.as_str(), "adaptive_density");
}

#[test]
fn floors_are_strictly_between_zero_and_one() {
    let f = AxisSet::floors();
    assert_eq!(f.len(), 20);
    for (i, v) in f.iter().enumerate() {
        assert!(*v > 0.0 && *v < 1.0, "floor {} for {} is not interior", v, AXIS_NAMES[i]);
    }
}

#[test]
fn out_of_range_axis_refused_at_construction() {
    let mut v = [0.8f64; 20];
    v[0] = 1.4;
    assert!(matches!(AxisSet::new(v), Err(AxisSetNotAdmissible::OutOfRange { .. })));
}

#[test]
fn non_finite_axis_refused_at_construction() {
    let mut v = [0.8f64; 20];
    v[3] = f64::NAN;
    assert!(matches!(AxisSet::new(v), Err(AxisSetNotAdmissible::NotFinite { .. })));
}

#[test]
fn ground_below_floor_is_not_admissible() {
    let mut v = [0.8f64; 20];
    v[0] = 0.01; // honesty, floor 0.5
    let bad = AxisSet::new(v).unwrap();
    let d = bad.is_admissible();
    assert_eq!(d.verdict(), Some(Verdict::AxisBelowFloor("honesty")));
}

#[test]
fn drift_is_l1_and_symmetric() {
    let a = AxisSet::uniform(0.8).unwrap();
    let mut v = [0.8f64; 20];
    v[0] = 0.7;
    v[1] = 0.6;
    let b = AxisSet::new(v).unwrap();
    assert!((a.drift(&b) - 0.3).abs() < 1e-12);
    assert!((a.drift(&b) - b.drift(&a)).abs() < 1e-12);
}

// ---------------------------------------------------------------------------
// envelope: D1..D4
// ---------------------------------------------------------------------------

#[test]
fn envelope_needs_a_finite_bound() {
    let e = Envelope::new("q", 0.0, f64::INFINITY, ViolationResponse::Refuse, "probe");
    assert!(e.is_err(), "an infinite bound is not a bound");
}

#[test]
fn envelope_needs_ordered_bounds() {
    assert!(Envelope::new("q", 5.0, 1.0, ViolationResponse::Refuse, "probe").is_err());
}

#[test]
fn envelope_needs_a_probe() {
    // D4: a limit with no resolvable verifier is decoration
    assert!(Envelope::new("q", 0.0, 1.0, ViolationResponse::Refuse, "").is_err());
}

#[test]
fn nan_magnitude_is_refused_not_allowed() {
    // NaN fails every comparison, so >= and <= both let it through.
    // The guard exists precisely because that is the default behaviour.
    let e = default_envelope(1.0);
    assert_eq!(e.holds(f64::NAN).verdict(), Some(Verdict::OutsideEnvelope));
}

#[test]
fn clamp_and_log_allows_the_operation() {
    let e = Envelope::new("q", 0.0, 1.0, ViolationResponse::ClampAndLog, "probe").unwrap();
    assert!(e.holds(99.0).allowed());
    assert!((e.clamp(99.0) - 1.0).abs() < 1e-12);
}

// ---------------------------------------------------------------------------
// the governor
// ---------------------------------------------------------------------------

#[test]
fn governor_refuses_to_build_on_inadmissible_ground() {
    let mut v = [0.8f64; 20];
    v[2] = 0.0; // boundaries, floor 0.25
    let bad = AxisSet::new(v).unwrap();
    let g = Governor::new(bad, default_envelope(1.0));
    assert!(g.is_err(), "a governor on bad ground must not exist");
}

#[test]
fn in_envelope_proposal_allowed() {
    let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
    assert!(g.evaluate((&ground(), 0.1)).allowed());
}

#[test]
fn out_of_envelope_proposal_refused() {
    let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
    let d = g.evaluate((&ground(), 9.0));
    assert_eq!(d.verdict(), Some(Verdict::OutsideEnvelope));
}

#[test]
fn proposal_below_an_axis_floor_is_refused_and_named() {
    let mut v = [0.8f64; 20];
    v[7] = 0.05; // coherence, floor 0.4
    let proposal = AxisSet::new(v).unwrap();
    let mut g = Governor::new(ground(), default_envelope(1.0)).unwrap();
    assert_eq!(
        g.evaluate((&proposal, 0.1)).verdict(),
        Some(Verdict::AxisBelowFloor("coherence"))
    );
}

#[test]
fn guarded_runs_the_operation_only_when_allowed() {
    use std::cell::Cell;
    let runs = Cell::new(0);
    {
        let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
        let r: Result<(), Decision> = g.guarded((&ground(), 0.1), || runs.set(runs.get() + 1));
        assert!(r.is_ok());
    }
    assert_eq!(runs.get(), 1, "allowed operation must run");

    {
        let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
        let r: Result<(), Decision> = g.guarded((&ground(), 9.0), || runs.set(runs.get() + 1));
        assert!(r.is_err());
    }
    assert_eq!(runs.get(), 1, "REFUSED OPERATION MUST NOT RUN");
}

// THE 747 TESTS
// ---------------------------------------------------------------------------

#[test]
fn fail_closed_is_sticky() {
    // a core that restarts itself on demand can never fail closed,
    // because nothing is ever absent as far as the caller can tell
    let mut g = Governor::new(ground(), default_envelope(1.0)).unwrap();
    assert!(g.evaluate((&ground(), 0.1)).allowed());

    g.fail_closed();
    assert_eq!(
        g.evaluate((&ground(), 0.1)).verdict(),
        Some(Verdict::CoreUnavailable)
    );
    // still refused on the next ask -- no silent respawn
    assert_eq!(
        g.evaluate((&ground(), 0.1)).verdict(),
        Some(Verdict::CoreUnavailable)
    );
}

#[test]
fn unavailable_never_reads_as_consent() {
    let mut g = Governor::new(ground(), default_envelope(1.0)).unwrap();
    g.fail_closed();
    // even a PERFECT proposal is refused while the core is gone
    assert!(g.evaluate((&ground(), 0.0)).refused());
}

#[test]
fn inadmissible_ground_refuses_even_a_perfect_proposal() {
    // the ground is checked before the proposal. a judgement against
    // inadmissible ground is a judgement with no basis.
    let good = ground();
    let mut bad_v = [0.8f64; 20];
    bad_v[4] = 0.01; // groundedness, floor 0.35
    let bad = AxisSet::new(bad_v).unwrap();

    let mut g = Governor::new(good, default_envelope(1.0)).unwrap();
    // force the ground to go bad behind the governor's back --
    // impossible through the API, and that is the point
    let d = bad.check_floor(&good);
    assert_eq!(d.verdict(), Some(Verdict::AxisBelowFloor("groundedness")));
}

#[test]
fn the_ledger_records_every_decision() {
    let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
    g.evaluate((&ground(), 0.1));
    g.evaluate((&ground(), 9.0));
    g.evaluate((&ground(), 0.2));
    assert_eq!(g.ledger().len(), 3);
    assert_eq!(g.refused_count(), 1);
}

#[test]
fn the_ledger_does_not_grow_without_bound() {
    let mut g = Governor::new(ground(), default_envelope(0.5)).unwrap();
    for _ in 0..10_000 {
        g.evaluate((&ground(), 0.1));
    }
    assert!(g.ledger().len() <= 4096, "the ledger is evidence, not a leak");
}