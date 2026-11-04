//! watch.rs -- TWO DUTIES THAT ALREADY EXIST, GIVEN A HOME IN THE CORE.
//!
//! WHAT THIS IS NOT: a new detection layer. Nothing here decides
//! whether a reply is true. That job belongs to the ground, and the
//! ground is unchanged.
//!
//! WHAT THIS IS: the two instruments the project already built, given
//! a home inside the 1-bit core so they can run inside a reflex loop,
//! next to the exchange they are watching.
//!
//! THE WATCHER -- the CHAIN-AUDIT duty. It watches the CORE'S OWN
//! readings and RE-DERIVES what the reading claims. A digest proves
//! the file did not change; a RE-DERIVATION proves the claim is true.
//! So the watcher recomputes the derived width from the channel,
//! recomputes the notch from the channel, and re-runs the exchange to
//! confirm it is deterministic. Any disagreement is a finding, by
//! name.
//!
//! THE OBSERVER -- the GROUND-DECIDES duty, applied to the watcher. It
//! reads the watcher's raw log and re-derives the whole chain -- every
//! digest, every link -- from the bytes on disk. It does NOT read the
//! watcher's summary, because a summary is what the watcher says about
//! itself. And if the watcher is ABSENT, the observer says ABSENT. It
//! never infers a healthy watcher from an empty log.
//!
//! WHY BOTH, and why the observer is not the watcher with more
//! authority:
//!
//! A watcher that grades its own homework is decoration. The
//! observer's whole job is to be able to say the watcher is WRONG,
//! and the only way to earn that is for the observer's check to be
//! INDEPENDENT of the watcher's own report. So the observer recomputes
//! the digests. If somebody edits a log line and edits its digest to
//! match -- the exact thing a digest cannot catch -- the observer
//! still recomputes from the chain and finds the break in the LINK.
//! And for the case where the attacker recomputes the digests too,
//! the observer holds an ANCHOR outside the chain.
//!
//! WHY THE CORE. The reflex loop has microseconds. A watcher that
//! needs a model call is not a watcher, it is a slow critic. These
//! are arithmetic, so they belong next to the exchange.

use crate::axes::AxisSet;
use crate::decision::Decision;
use crate::interstalk::{self, Reading};
use crate::stalk::{derived_width, pair_channel, Stalk};

/// The FNV-1a 64-bit offset basis. Used for the chain's digests.
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
/// The FNV-1a 64-bit prime.
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
/// The digest a chain starts from.
pub const GENESIS_DIGEST: &str = "0000000000000000";

// ---------------------------------------------------------------------------
// the digest
// ---------------------------------------------------------------------------

/// FNV-1a over the bytes. Deterministic, stdlib-free, and stable across
/// processes -- which matters, because a digest that depends on the
/// process would make the observer's re-derivation impossible.
pub fn fnv1a(bytes: &[u8]) -> u64 {
    let mut h = FNV_OFFSET;
    for b in bytes {
        h ^= *b as u64;
        h = h.wrapping_mul(FNV_PRIME);
    }
    h
}

/// The digest of one entry: its own content plus the previous link.
pub fn entry_digest(
    seq: u64,
    kind: &str,
    subject: &str,
    verdict: &str,
    detail: &str,
    prev: &str,
) -> String {
    let mut buf = String::with_capacity(seq.to_string().len() + kind.len() + subject.len() + verdict.len() + detail.len() + prev.len() + 8);
    buf.push_str(&seq.to_string());
    buf.push('\u{1f}');
    buf.push_str(kind);
    buf.push('\u{1f}');
    buf.push_str(subject);
    buf.push('\u{1f}');
    buf.push_str(verdict);
    buf.push('\u{1f}');
    buf.push_str(detail);
    buf.push('\u{1f}');
    buf.push_str(prev);
    format!("{:016x}", fnv1a(buf.as_bytes()))
}

// ---------------------------------------------------------------------------
// the watcher's chain
// ---------------------------------------------------------------------------

/// One entry in the watcher's chain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WatchEntry {
    pub seq: u64,
    pub kind: String,
    pub subject: String,
    /// The watcher's own verdict on what it watched.
    pub verdict: String,
    /// What it actually re-derived.
    pub detail: String,
    /// The previous entry's digest. The link.
    pub prev: String,
    /// This entry's digest.
    pub digest: String,
}

impl WatchEntry {
    /// Recompute this entry's digest from its own fields.
    pub fn recomputed_digest(&self) -> String {
        entry_digest(
            self.seq,
            &self.kind,
            &self.subject,
            &self.verdict,
            &self.detail,
            &self.prev,
        )
    }
}

/// The watcher's append-only chain.
#[derive(Debug, Clone, Default)]
pub struct WatchChain {
    pub entries: Vec<WatchEntry>,
}

/// What the observer found.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObservationVerdict {
    /// Every digest recomputed and every link matched.
    Consistent,
    /// A digest did not recompute, or a link did not match.
    Broken,
    /// There is no chain to observe. ABSENCE IS NOT HEALTH.
    Absent,
}

impl ObservationVerdict {
    pub fn as_str(self) -> &'static str {
        match self {
            ObservationVerdict::Consistent => "consistent",
            ObservationVerdict::Broken => "broken",
            ObservationVerdict::Absent => "absent",
        }
    }
}

/// The observer's report.
#[derive(Debug, Clone)]
pub struct Observation {
    pub verdict: ObservationVerdict,
    /// How many entries were re-derived.
    pub checked: usize,
    /// The sequence number where the chain broke, if it broke.
    pub broke_at: Option<u64>,
    /// Why, in words, with the numbers.
    pub reason: String,
}

impl Observation {
    pub fn consistent(&self) -> bool {
        self.verdict == ObservationVerdict::Consistent
    }
}

impl WatchChain {
    pub fn new() -> Self {
        WatchChain { entries: Vec::new() }
    }

    /// Append one entry. The link is set by the chain, so a caller
    /// cannot break the chain by accident.
    pub fn push(
        &mut self,
        kind: &str,
        subject: &str,
        verdict: &str,
        detail: &str,
    ) -> WatchEntry {
        let seq = self.entries.len() as u64;
        let prev = self
            .entries
            .last()
            .map(|e| e.digest.clone())
            .unwrap_or_else(|| GENESIS_DIGEST.to_string());
        let digest = entry_digest(seq, kind, subject, verdict, detail, &prev);
        let entry = WatchEntry {
            seq,
            kind: kind.to_string(),
            subject: subject.to_string(),
            verdict: verdict.to_string(),
            detail: detail.to_string(),
            prev,
            digest,
        };
        self.entries.push(entry.clone());
        entry
    }

    /// The chain as JSON Lines, one object per entry.
    pub fn to_jsonl(&self) -> String {
        let mut out = String::new();
        for e in &self.entries {
            out.push_str(&format!(
                "{{\"seq\":{},\"kind\":\"{}\",\"subject\":\"{}\",\"verdict\":\"{}\",\"detail\":\"{}\",\"prev\":\"{}\",\"digest\":\"{}\"}}\n",
                e.seq, e.kind, e.subject, e.verdict, e.detail, e.prev, e.digest
            ));
        }
        out
    }

    /// Read a chain back from JSON Lines. A line that does not parse is
    /// kept as a BROKEN marker rather than dropped, so the observer can
    /// see it instead of the chain appearing shorter than it was.
    pub fn from_jsonl(text: &str) -> WatchChain {
        let mut chain = WatchChain::new();
        for line in text.lines() {
            if line.trim().is_empty() {
                continue;
            }
            match parse_entry(line) {
                Some(e) => chain.entries.push(e),
                None => chain.entries.push(WatchEntry {
                    seq: chain.entries.len() as u64,
                    kind: "unparsed".to_string(),
                    subject: line.chars().take(80).collect(),
                    verdict: "unparsed".to_string(),
                    detail: String::new(),
                    prev: String::new(),
                    digest: String::new(),
                }),
            }
        }
        chain
    }
}

/// Read one JSON Lines entry without pulling in a JSON dependency.
fn parse_entry(line: &str) -> Option<WatchEntry> {
    let field = |name: &str| -> Option<String> {
        let key = format!("\"{}\":", name);
        let start = line.find(&key)? + key.len();
        let rest = &line[start..];
        let rest = rest.trim_start();
        if let Some(stripped) = rest.strip_prefix('"') {
            let mut out = String::new();
            let mut chars = stripped.chars();
            while let Some(c) = chars.next() {
                match c {
                    '"' => return Some(out),
                    '\\' => match chars.next() {
                        Some('n') => out.push('\n'),
                        Some('t') => out.push('\t'),
                        Some('r') => out.push('\r'),
                        Some('"') => out.push('"'),
                        Some('\\') => out.push('\\'),
                        Some(other) => out.push(other),
                        None => return None,
                    },
                    other => out.push(other),
                }
            }
            None
        } else {
            let end = rest
                .find(|c: char| c == ',' || c == '}')
                .unwrap_or(rest.len());
            Some(rest[..end].trim().to_string())
        }
    };
    let seq = field("seq")?.parse::<u64>().ok()?;
    Some(WatchEntry {
        seq,
        kind: field("kind")?,
        subject: field("subject")?,
        verdict: field("verdict")?,
        detail: field("detail")?,
        prev: field("prev")?,
        digest: field("digest")?,
    })
}

// ---------------------------------------------------------------------------
// the watcher
// ---------------------------------------------------------------------------

/// The watcher. It watches the CORE'S OWN readings.
#[derive(Debug, Clone, Default)]
pub struct Watcher {
    pub chain: WatchChain,
}

impl Watcher {
    pub fn new() -> Self {
        Watcher { chain: WatchChain::new() }
    }

    /// Watch ONE interstalk exchange, by RE-DERIVING what it claims.
    ///
    /// Three re-derivations, and each of them can disagree with the
    /// reading:
    ///
    ///   1. THE WIDTH. The reading reports the width it derived. The
    ///      watcher recomputes `derived_width` from the channel's own
    ///      tap count. If the reading's width is not the derived one,
    ///      the width was REQUESTED, and the whole architecture says it
    ///      must never be.
    ///   2. THE NOTCH. The reading reports the channel's notch depth.
    ///      The watcher recomputes it from the channel.
    ///   3. THE DETERMINISM. The watcher runs the exchange a second
    ///      time and compares the alignment. Two runs of the same
    ///      reading must agree; if they do not, the reading is not a
    ///      reading.
    pub fn watch_exchange(
        &mut self,
        tx: &Stalk,
        rx: &Stalk,
        neighbours: &[Stalk],
        path_delay: usize,
        reading: &Reading,
    ) -> WatchEntry {
        let channel = pair_channel(tx, rx, neighbours, path_delay);
        let recomputed_width = derived_width(channel.len());
        let recomputed_notch = channel.notch_db();

        let mut problems: Vec<String> = Vec::new();
        if reading.width != recomputed_width {
            problems.push(format!(
                "width_not_derived: the reading says {} and the channel derives {}",
                reading.width, recomputed_width
            ));
        }
        if (reading.notch_db - recomputed_notch).abs() > 1e-6 {
            problems.push(format!(
                "notch_mismatch: the reading says {:.6} and the channel measures {:.6}",
                reading.notch_db, recomputed_notch
            ));
        }
        let repeat = interstalk::exchange(tx, rx, neighbours, path_delay);
        if (repeat.alignment - reading.alignment).abs() > 1e-9 {
            problems.push(format!(
                "nondeterministic: two runs of the same exchange gave {:.9} and {:.9}",
                reading.alignment, repeat.alignment
            ));
        }

        let verdict = if problems.is_empty() { "watched_ok" } else { "watched_fault" };
        let detail = if problems.is_empty() {
            format!(
                "width={} taps={} notch_db={:.4} alignment={:.6} population={} rederived",
                reading.width,
                channel.len(),
                recomputed_notch,
                reading.alignment,
                reading.population
            )
        } else {
            problems.join("; ")
        };
        self.chain.push("exchange", &subject_of(tx, rx), verdict, &detail)
    }

    /// Watch ONE governor decision. The decision's reason is recorded
    /// verbatim, so the chain carries the refusal's own words rather
    /// than a summary of them.
    pub fn watch_decision(&mut self, subject: &str, decision: &Decision) -> WatchEntry {
        let verdict = if decision.allowed() { "allowed" } else { "refused" };
        let detail = decision.explain();
        self.chain.push("decision", subject, verdict, &detail)
    }

    /// Watch the ground itself. A ground below a floor makes every
    /// judgement against it baseless, so it is watched FIRST.
    pub fn watch_ground(&mut self, ground: &AxisSet) -> WatchEntry {
        let d = ground.is_admissible();
        let verdict = if d.allowed() { "ground_ok" } else { "ground_fault" };
        let detail = d.explain();
        self.chain.push("ground", "psi_0", verdict, &detail)
    }
}

/// The subject label for an exchange.
fn subject_of(tx: &Stalk, rx: &Stalk) -> String {
    format!("stalk{}->stalk{}", tx.id, rx.id)
}

// ---------------------------------------------------------------------------
// the observer
// ---------------------------------------------------------------------------

/// The observer of the watcher.
///
/// AND IT RE-DERIVES. It does not read the watcher's verdict and trust
/// it; it recomputes every digest from the entry's own bytes and
/// checks every link. So an edit that also edits the digest -- the
/// thing a digest cannot catch -- is still caught, because the LINK
/// from the entry before it no longer matches.
pub fn observe(chain: &WatchChain) -> Observation {
    observe_against(chain, None)
}

/// The observer, WITH AN EXTERNAL ANCHOR.
///
/// AND THIS IS THE PART THAT MATTERS, and it came out of a check that
/// failed for the right reason. The chain-internal check catches an
/// edit whose digest was NOT recomputed. It does NOT catch an edit
/// whose digest WAS recomputed: recompute the tail's digest, and the
/// chain is internally consistent again, because the link into the
/// tail still points at an unchanged head.
///
/// **A DIGEST THAT CAN BE EDITED ALONGSIDE THE THING IT DEFENDS IS
/// NOT A DEFENCE.** So the observer takes a SECOND WITNESS: the head
/// digest as it was when the anchor was taken, held OUTSIDE the chain.
/// The chain can be rewritten end to end; the anchor cannot, because
/// it lives somewhere the writer of the chain does not hold.
///
/// And the anchor is cheap to keep honest: it is the head digest plus
/// the count of entries. An attacker who rewrites the chain and wants
/// the anchor to match must also find the anchor, and the anchor is
/// the thing a later reader compares against.
pub fn observe_against(chain: &WatchChain, anchor: Option<&Anchor>) -> Observation {
    if chain.entries.is_empty() {
        return Observation {
            verdict: ObservationVerdict::Absent,
            checked: 0,
            broke_at: None,
            reason: "no_watch_log: the watcher has written nothing, and an \
                     absent watcher is not a healthy one"
                .to_string(),
        };
    }

    let mut prev_digest = GENESIS_DIGEST.to_string();
    for (i, e) in chain.entries.iter().enumerate() {
        let recomputed = e.recomputed_digest();
        if recomputed != e.digest {
            return Observation {
                verdict: ObservationVerdict::Broken,
                checked: i,
                broke_at: Some(e.seq),
                reason: format!(
                    "digest_mismatch at seq {}: the entry carries {} and its own \
                     content recomputes to {}",
                    e.seq, e.digest, recomputed
                ),
            };
        }
        if e.prev != prev_digest {
            return Observation {
                verdict: ObservationVerdict::Broken,
                checked: i,
                broke_at: Some(e.seq),
                reason: format!(
                    "link_break at seq {}: the entry points at {} and the entry \
                     before it ends at {}",
                    e.seq, e.prev, prev_digest
                ),
            };
        }
        prev_digest = e.digest.clone();
    }

    // THE SECOND WITNESS. The chain is internally consistent; now the
    // question is whether it is the SAME chain it was when the anchor
    // was taken.
    if let Some(a) = anchor {
        let head = chain.entries.last().map(|e| e.digest.clone()).unwrap_or_default();
        if a.head_digest != head {
            return Observation {
                verdict: ObservationVerdict::Broken,
                checked: chain.entries.len(),
                broke_at: Some(a.count.saturating_sub(1)),
                reason: format!(
                    "anchor_mismatch: the chain now ends at {} with {} entries and the \
                     anchor was taken at {} with {} entries",
                    head,
                    chain.entries.len(),
                    a.head_digest,
                    a.count
                ),
            };
        }
        if a.count != chain.entries.len() as u64 {
            return Observation {
                verdict: ObservationVerdict::Broken,
                checked: chain.entries.len(),
                broke_at: Some(a.count.saturating_sub(1)),
                reason: format!(
                    "anchor_count_mismatch: the chain holds {} entries and the anchor \
                     was taken at {}",
                    chain.entries.len(),
                    a.count
                ),
            };
        }
    }

    Observation {
        verdict: ObservationVerdict::Consistent,
        checked: chain.entries.len(),
        broke_at: None,
        reason: format!(
            "{} entries re-derived: every digest recomputed and every link matched",
            chain.entries.len()
        ),
    }
}

/// The external anchor: what the chain looked like at a moment in time.
///
/// It lives OUTSIDE the chain, so rewriting the chain cannot rewrite
/// it. That is the whole point of it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Anchor {
    /// The head digest at the moment the anchor was taken.
    pub head_digest: String,
    /// How many entries the chain held at that moment.
    pub count: u64,
}

impl Anchor {
    /// Take an anchor of the chain as it is NOW.
    pub fn of(chain: &WatchChain) -> Anchor {
        Anchor {
            head_digest: chain
                .entries
                .last()
                .map(|e| e.digest.clone())
                .unwrap_or_else(|| GENESIS_DIGEST.to_string()),
            count: chain.entries.len() as u64,
        }
    }
}

/// Observe a raw JSON Lines log, straight from disk.
pub fn observe_jsonl(text: &str) -> Observation {
    observe(&WatchChain::from_jsonl(text))
}
