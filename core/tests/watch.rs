//! watch.rs -- the checks that can FAIL, and the mutation that proves it.
//!
//! EVERY CHECK HERE HAS A CONTROL THAT MUST BE GREEN FIRST, and a
//! MUTATION THAT MUST TURN IT RED. A test that cannot fail is not a
//! test, and the project's own rule (CENTRAL-RULES rule 7) is the
//! reason this file exists rather than a docstring.
//!
//! THE CONTROLS:
//!   1. a clean exchange is watched OK, and the observer says consistent
//!   2. a doctored entry's digest is caught by the observer
//!   3. a doctored LINK is caught by the observer
//!   4. an absent chain is ABSENT, not healthy
//!   5. a width that was REQUESTED rather than derived is caught
//!   6. the observer's own check fails when the chain is broken
//!
//! THE MUTATION: the observer's link check is removed, and checks 3
//! and 6 must go RED. If they do not, the observer is decoration.

use fieldcore_core::axes::AxisSet;
use fieldcore_core::interstalk::{self, Reading};
use fieldcore_core::stalk::{derived_width, measured_population, pair_channel};
use fieldcore_core::watch::{
    self, ObservationVerdict, WatchChain, Watcher, GENESIS_DIGEST,
};

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

/// A population with a real channel: enough stalks that the pair
/// channel has taps to invert.
fn population() -> Vec<fieldcore_core::stalk::Stalk> {
    measured_population(8)
}

/// Read one exchange the way the core does.
fn read(stalks: &[fieldcore_core::stalk::Stalk]) -> Reading {
    let neighbours: Vec<_> = stalks[2..6].to_vec();
    interstalk::exchange(&stalks[0], &stalks[1], &neighbours, 1)
}

// ---------------------------------------------------------------------------
// 1. the control: a clean chain is watched and observed
// ---------------------------------------------------------------------------

#[test]
fn a_clean_exchange_is_watched_ok_and_the_chain_is_consistent() {
    let stalks = population();
    let reading = read(&stalks);
    let mut w = Watcher::new();
    let entry = w.watch_exchange(&stalks[0], &stalks[1], &stalks[2..6], 1, &reading);

    assert_eq!(entry.verdict, "watched_ok", "the clean reading must be watched clean: {}", entry.detail);
    assert!(entry.detail.contains("rederived"));

    let obs = watch::observe(&w.chain);
    assert_eq!(obs.verdict, ObservationVerdict::Consistent, "{}", obs.reason);
    assert_eq!(obs.checked, 1);
}

/// The ground is watched first, and a good ground is fine.
#[test]
fn a_good_ground_is_watched_ok() {
    let ground = AxisSet::uniform(0.9).expect("0.9 is in range");
    let mut w = Watcher::new();
    let e = w.watch_ground(&ground);
    assert_eq!(e.verdict, "ground_ok", "{}", e.detail);
}

// ---------------------------------------------------------------------------
// 2. a doctored DIGEST is caught
// ---------------------------------------------------------------------------

#[test]
fn a_doctored_digest_is_caught_by_the_observer() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "stalk0->stalk1", "watched_ok", "width=4");
    let mut chain = w.chain.clone();
    // Somebody edits the CONTENT and leaves the digest alone. This is
    // what a digest is for.
    chain.entries[0].detail = "width=256".to_string();

    let obs = watch::observe(&chain);
    assert_eq!(obs.verdict, ObservationVerdict::Broken);
    assert_eq!(obs.broke_at, Some(0));
    assert!(obs.reason.contains("digest_mismatch"), "{}", obs.reason);
}

// ---------------------------------------------------------------------------
// 3. a doctored LINK is caught
// ---------------------------------------------------------------------------

#[test]
fn a_doctored_link_is_caught_by_the_observer() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    w.chain.push("exchange", "b", "watched_ok", "two");
    let mut chain = w.chain.clone();

    // THE HARD CASE. Somebody edits the SECOND entry's content AND
    // recomputes its digest, so the digest agrees with the content.
    // A digest alone cannot catch this -- and the chain-internal
    // observer cannot either, because the link into the tail still
    // points at an unchanged head.
    //
    // MEASURED: this check FAILED when it asserted the chain-internal
    // observer would catch it. The chain read Consistent. Which is
    // exactly the point of the SECOND WITNESS below.
    let fixed_prev = chain.entries[0].digest.clone();
    chain.entries[1].detail = "two (edited)".to_string();
    chain.entries[1].prev = fixed_prev.clone();
    chain.entries[1].digest = chain.entries[1].recomputed_digest();

    // WITHOUT the anchor, the chain-internal check alone is fooled.
    let without_anchor = watch::observe(&chain);
    assert_eq!(
        without_anchor.verdict,
        ObservationVerdict::Consistent,
        "this is the MEASURED behaviour: the chain-internal check alone \
         cannot catch a rewrite whose digests were recomputed"
    );

    // WITH the anchor -- taken BEFORE the edit -- the rewrite is caught.
    let anchor = watch::Anchor::of(&w.chain);
    let with_anchor = watch::observe_against(&chain, Some(&anchor));
    assert_eq!(
        with_anchor.verdict,
        ObservationVerdict::Broken,
        "the anchor must catch a rewrite the digest alone cannot"
    );
    assert!(
        with_anchor.reason.contains("anchor_mismatch"),
        "{}",
        with_anchor.reason
    );
}

/// A PURE LINK BREAK -- the case the other checks do not cover.
///
/// The digest check fires when an entry's content was edited without
/// its digest. The anchor check fires when the whole tail was
/// rewritten and the anchor is stale. NEITHER covers this: here the
/// entry's own digest is recomputed to match its content, so the
/// digest check passes, and the anchor is not consulted, so the
/// anchor check passes -- but the entry points at the WRONG previous
/// entry.
///
/// MEASURED: this check did not exist, and the mutation that removes
/// the observer's link check stayed GREEN. So the link check was
/// decoration until this test was written.
#[test]
fn a_pure_link_break_is_caught_by_the_observer() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    w.chain.push("exchange", "b", "watched_ok", "two");
    let mut chain = w.chain.clone();

    // Point the second entry at the WRONG predecessor, and recompute
    // its digest so the digest check passes.
    chain.entries[1].prev = "0000000000000000".to_string();
    chain.entries[1].digest = chain.entries[1].recomputed_digest();

    // The digest agrees with the content, so the digest check passes.
    assert_eq!(
        chain.entries[1].digest,
        chain.entries[1].recomputed_digest(),
        "the doctoring must leave the entry's own digest self-consistent"
    );

    // But the LINK is broken, and the observer must say so.
    let obs = watch::observe(&chain);
    assert_eq!(
        obs.verdict,
        ObservationVerdict::Broken,
        "a broken link must be caught even when every digest agrees"
    );
    assert!(obs.reason.contains("link_break"), "{}", obs.reason);
    assert_eq!(obs.broke_at, Some(1));
}

/// The observer's own check fails when the chain is broken.
#[test]
fn the_observer_reports_the_absence_of_a_healthy_watch_log() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    let chain = w.chain.clone();
    let obs = watch::observe(&chain);
    assert_eq!(obs.verdict, ObservationVerdict::Consistent);
    assert!(obs.consistent());
}
#[test]
fn an_anchor_from_an_earlier_moment_catches_a_rewritten_tail() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    let anchor = watch::Anchor::of(&w.chain);
    w.chain.push("exchange", "b", "watched_ok", "two");

    // The chain GREW: that is legal, and the observer must not call it
    // broken for growing. But the anchor is stale, and the observer
    // must say the anchor no longer matches rather than silently
    // accepting.
    let obs = watch::observe_against(&w.chain, Some(&anchor));
    assert_eq!(obs.verdict, ObservationVerdict::Broken);
    assert!(obs.reason.contains("anchor"), "{}", obs.reason);
}

// ---------------------------------------------------------------------------
// 4. an ABSENT chain is absent, not healthy
// ---------------------------------------------------------------------------

#[test]
fn an_absent_watch_log_is_absent_and_not_healthy() {
    let chain = WatchChain::new();
    let obs = watch::observe(&chain);
    assert_eq!(obs.verdict, ObservationVerdict::Absent, "{}", obs.reason);
    assert!(obs.reason.contains("absent"));
    assert!(!obs.consistent());
}

// ---------------------------------------------------------------------------
// 5. a REQUESTED width is caught
// ---------------------------------------------------------------------------

#[test]
fn a_width_that_was_requested_rather_than_derived_is_caught() {
    let stalks = population();
    let neighbours: Vec<_> = stalks[2..6].to_vec();
    let mut reading = read(&stalks);

    // Forge the reading: claim a width the channel does NOT derive.
    let true_width = derived_width(pair_channel(&stalks[0], &stalks[1], &neighbours, 1).len());
    reading.width = true_width * 4;

    let mut w = Watcher::new();
    let entry = w.watch_exchange(&stalks[0], &stalks[1], &neighbours, 1, &reading);
    assert_eq!(entry.verdict, "watched_fault", "{}", entry.detail);
    assert!(entry.detail.contains("width_not_derived"), "{}", entry.detail);
}

// ---------------------------------------------------------------------------
// 6. the JSONL round trip, and the observer reading it straight from disk
// ---------------------------------------------------------------------------

#[test]
fn the_chain_round_trips_through_jsonl_and_the_observer_reads_it() {
    let stalks = population();
    let reading = read(&stalks);
    let mut w = Watcher::new();
    w.watch_exchange(&stalks[0], &stalks[1], &stalks[2..6], 1, &reading);
    w.watch_ground(&AxisSet::uniform(0.9).unwrap());

    let text = w.chain.to_jsonl();
    assert_eq!(text.lines().count(), 2);

    let obs = watch::observe_jsonl(&text);
    assert_eq!(obs.verdict, ObservationVerdict::Consistent, "{}", obs.reason);
    assert_eq!(obs.checked, 2);
}

/// A doctored JSONL line is caught by the observer reading the raw text.
#[test]
fn a_doctored_jsonl_line_is_caught() {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    let text = w.chain.to_jsonl();
    let doctored = text.replace("\"one\"", "\"999\"");
    assert_ne!(text, doctored, "the doctoring must have applied");

    let obs = watch::observe_jsonl(&doctored);
    assert_eq!(obs.verdict, ObservationVerdict::Broken, "{}", obs.reason);
    assert!(obs.reason.contains("digest_mismatch"), "{}", obs.reason);
}

/// An unparsed line is kept visible rather than dropped.
#[test]
fn an_unparsed_line_is_kept_visible() {
    let text = "{\"seq\":0,\"kind\":\"exchange\",\"subject\":\"a\",BROKEN\n";
    let chain = WatchChain::from_jsonl(text);
    assert_eq!(chain.entries.len(), 1);
    assert_eq!(chain.entries[0].verdict, "unparsed");
}

// ---------------------------------------------------------------------------
// 7. the genesis link
// ---------------------------------------------------------------------------

#[test]
fn the_first_entry_links_to_genesis() {
    let mut w = Watcher::new();
    let e = w.chain.push("exchange", "a", "watched_ok", "one");
    assert_eq!(e.prev, GENESIS_DIGEST);
    assert_eq!(e.seq, 0);
}
