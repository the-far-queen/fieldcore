//! watch_cli.rs -- the watcher and its observer, RUN. So the two duties
//! have a caller and not only a library.
//!
//! WHY A BINARY AND NOT JUST A MODULE. The project's own rule is that
//! a mechanism nobody calls is a decoration, and the atlas exam's
//! reachability audit exists because it found five unwired things in
//! one pass. So the watcher gets a command that actually reads the
//! channel, watches the reading, writes the chain, and hands it to the
//! observer -- and the observer's verdict is the exit code.
//!
//! THE THREE COMMANDS:
//!     watch     read one exchange, watch it, print the chain
//!     observe   read a chain from a file, re-derive it, print the verdict
//!     selftest  run the whole thing with a doctored chain and show
//!               that the observer catches it
//!
//! AND THE EXIT CODES, because a script must be able to gate on this:
//!     0  the observer found the chain consistent
//!     1  the observer found the chain broken
//!     2  there was no chain to observe
//!     3  the chain could not be read
//!
//! So a cron job can run `observe` on the watch log and refuse the
//! session when the watcher and the observer disagree.

use std::env;
use std::process::ExitCode;

use fieldcore_core::interstalk;
use fieldcore_core::stalk::measured_population;
use fieldcore_core::watch::{self, Anchor, ObservationVerdict, Watcher};

/// How many stalks are in view by default. The population is the
/// channel's tap count, so this is also the width the channel derives.
const DEFAULT_VIEW: usize = 4;

fn usage() -> &'static str {
    "usage:\n  \
     fieldcore-watch watch    [population]   read one exchange and watch it\n  \
     fieldcore-watch observe  <file.jsonl>   re-derive a chain from disk\n  \
     fieldcore-watch selftest                 prove the observer can fail"
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let cmd = args.first().map(|s| s.as_str()).unwrap_or("");
    match cmd {
        "watch" => cmd_watch(&args[1..]),
        "observe" => cmd_observe(&args[1..]),
        "selftest" => cmd_selftest(),
        "" | "-h" | "--help" => {
            println!("{}", usage());
            ExitCode::SUCCESS
        }
        other => {
            eprintln!("unknown command: {}\n\n{}", other, usage());
            ExitCode::from(3)
        }
    }
}

/// Read one exchange over a real channel and watch it.
fn cmd_watch(args: &[String]) -> ExitCode {
    let population: usize = args
        .first()
        .and_then(|s| s.parse().ok())
        .unwrap_or(DEFAULT_VIEW)
        .max(2);
    let view = population - 2;

    let stalks = measured_population(population);
    let neighbours: Vec<_> = stalks[2..2 + view].to_vec();
    let reading = interstalk::exchange(&stalks[0], &stalks[1], &neighbours, 1);

    let mut w = Watcher::new();
    let entry = w.watch_exchange(&stalks[0], &stalks[1], &neighbours, 1, &reading);

    println!("population={} in_view={} taps={} width={} alignment={:.6} reading={:.4}",
             population, view, view + 1, reading.width, reading.alignment, reading.reading);
    println!("watcher: {} {}", entry.verdict, entry.detail);
    println!("--- chain ---");
    print!("{}", w.chain.to_jsonl());

    let obs = watch::observe(&w.chain);
    println!("observer: {} ({})", obs.verdict.as_str(), obs.reason);
    match obs.verdict {
        ObservationVerdict::Consistent => ExitCode::SUCCESS,
        ObservationVerdict::Broken => ExitCode::from(1),
        ObservationVerdict::Absent => ExitCode::from(2),
    }
}

/// Re-derive a chain from a file on disk.
fn cmd_observe(args: &[String]) -> ExitCode {
    let path = match args.first() {
        Some(p) => p,
        None => {
            eprintln!("observe needs a file\n\n{}", usage());
            return ExitCode::from(3);
        }
    };
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("could not read {}: {}", path, e);
            return ExitCode::from(3);
        }
    };
    let chain = watch::WatchChain::from_jsonl(&text);
    let obs = watch::observe(&chain);
    println!("entries={} checked={} verdict={}", chain.entries.len(), obs.checked, obs.verdict.as_str());
    println!("{}", obs.reason);
    match obs.verdict {
        ObservationVerdict::Consistent => ExitCode::SUCCESS,
        ObservationVerdict::Broken => ExitCode::from(1),
        ObservationVerdict::Absent => ExitCode::from(2),
    }
}

/// Prove the observer can fail. A check that cannot fail is not a check.
fn cmd_selftest() -> ExitCode {
    let mut w = Watcher::new();
    w.chain.push("exchange", "a", "watched_ok", "one");
    w.chain.push("exchange", "b", "watched_ok", "two");

    let clean = watch::observe(&w.chain);
    println!("clean chain          -> {}", clean.verdict.as_str());

    // A doctored tail whose digest was recomputed: the chain-internal
    // check cannot see it, so the ANCHOR is what catches it.
    let anchor = Anchor::of(&w.chain);
    let mut doctored = w.chain.clone();
    doctored.entries[1].detail = "two (edited)".to_string();
    doctored.entries[1].prev = doctored.entries[0].digest.clone();
    doctored.entries[1].digest = doctored.entries[1].recomputed_digest();
    println!("doctored, no anchor  -> {}", watch::observe(&doctored).verdict.as_str());
    println!("doctored, with anchor-> {}", watch::observe_against(&doctored, Some(&anchor)).verdict.as_str());

    // An absent chain is ABSENT, not healthy.
    let empty = watch::WatchChain::new();
    println!("empty chain          -> {}", watch::observe(&empty).verdict.as_str());

    let ok = clean.verdict == ObservationVerdict::Consistent
        && watch::observe(&doctored).verdict == ObservationVerdict::Consistent
        && watch::observe_against(&doctored, Some(&anchor)).verdict == ObservationVerdict::Broken
        && watch::observe(&empty).verdict == ObservationVerdict::Absent;
    println!("selftest {}", if ok { "ok" } else { "FAILED" });
    if ok {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    }
}
