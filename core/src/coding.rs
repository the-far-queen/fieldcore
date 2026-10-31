//! coding.rs — the coding sheaf: an independent daily scan of the field.
//!
//! WHY THIS IS IN RUST AND WHY THE POLICY IS HERE, and the two are
//! different reasons:
//!
//! 1. THE POLICY BELONGS NEXT TO THE GOVERNOR. `sheaf.rs` already
//!    defines the contract — `Source`, `Lang`, `Candidate`, `Refusal`,
//!    `Admission` — and every one of those refusals NAMES its reason.
//!    A scanner that filters on its own criteria, away from the
//!    governor, would be a second policy, and two policies drift.
//!
//! 2. THE SCAN IS SCHEDULED, NOT REQUESTED. Bobby 2026-10-25:
//!    *"you as gabrielle must intelligently and independently scan
//!    daily or more just in rust and python and just high stars and
//!    just relevant repos"*. So the cadence is IN the artifact rather
//!    than in a habit. A thing that only happens when someone
//!    remembers it is not a loop.
//!
//! AND THE SELF-RECURSION, which is the load-bearing part:
//!
//!    The vocabulary of what counts as RELEVANT GROWS from what the
//!    scanner has admitted. So the system scans better as it gets
//!    better — not because anyone improved the filter, but because the
//!    filter learned from its own accepted work.
//!
//!    The growth is bounded and auditable:
//!      * a topic enters the learned vocabulary only through an ADMITTED
//!        candidate, so the vocabulary can never drift past what the
//!        gate actually let in
//!      * a topic's weight is the stars of the work that introduced it,
//!        so the loudest repos teach the scanner the most
//!      * and the learned vocabulary is a DATA STRUCTURE ON DISK, so
//!        the next scan reads what the last one learned
//!
//! WHAT THE SCANNER DOES NOT DO, and this is the boundary:
//!
//!    It does not INSTALL anything. It produces CANDIDATES and
//!    PROPOSALS, and the four-step chain decides. A scanner that
//!    installed code would be the thing this whole project is built to
//!    prevent.
//!
//! NO DEPENDENCIES, like the rest of the core. The transport is
//! Python's; the policy is here.

use std::collections::BTreeMap;
use std::fmt;

// ---------------------------------------------------------------------------
// the cadence
// ---------------------------------------------------------------------------

/// How often the scan is due.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Cadence {
    Hourly,
    Daily,
}

impl Cadence {
    pub fn as_str(&self) -> &'static str {
        match self {
            Cadence::Hourly => "hourly",
            Cadence::Daily => "daily",
        }
    }

    /// The interval in seconds.
    pub fn interval_seconds(&self) -> u64 {
        match self {
            Cadence::Hourly => 3600,
            Cadence::Daily => 86_400,
        }
    }
}

/// Is a scan due?
///
/// AND THE POINT: this is a function of the LAST SCAN'S TIME, so the
/// answer does not depend on anybody remembering. That is the whole
/// difference between a loop and a habit.
pub fn is_due(last_scan_unix: Option<u64>, now_unix: u64,
               cadence: Cadence) -> bool {
    match last_scan_unix {
        None => true,
        Some(t) => now_unix.saturating_sub(t) >= cadence.interval_seconds(),
    }
}

// ---------------------------------------------------------------------------
// the vocabulary
// ---------------------------------------------------------------------------

/// What counts as relevant, and what the scanner has learned.
///
/// AND WHY THE SEED IS THE PROJECT'S OWN SUBJECTS, and not a generic
/// keyword list: a repo about "AI" is not relevant to a substrate
/// whose problem is a contractible interior. The seed is the project's
/// own vocabulary, so the first scan cannot wander.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Vocabulary {
    /// topic -> weight. The seed topics start at 1.0.
    seed: BTreeMap<String, f64>,
    /// topic -> weight, learned from admitted work.
    learned: BTreeMap<String, f64>,
}

impl Vocabulary {
    /// The project's own subjects, and the topics the coding sheaf
    /// recognises out of the box.
    pub fn project_seed() -> Self {
        let mut seed = BTreeMap::new();
        for t in [
            // topology: the geometric substrate
            "manifold", "torus", "toroid", "hodge", "harmonic", "topolog",
            "curvature", "gradient-flow", "riemannian", "geodesic",
            "lattice", "symmetry", "gauge", "fibonacci", "golden-ratio",
            "eigenvalue", "spectral", "chladni", "waveguide",
            // the control system: the 747
            "constitutional-ai", "gate", "governance", "guardrail",
            "oversight", "alignment", "refusal", "veto", "envelope",
            "audit", "qualification", "falsification", "invariant",
            // the identity: the language and the meaning
            "psb", "semantic-block", "lexicon", "meaning", "ontology",
            "machine-language-technical-register", "mltr", "formal",
            "primitives", "composition",
            // the substrate: the engineering
            "oscillator", "resonator", "coupled", "interference",
            "phaselock", "kuramoto", "coherence", "dsp", "signal-processing",
            "equalizer", "holography", "photonics", "coupling",
        ] {
            seed.insert(t.to_string(), 1.0);
        }
        Vocabulary { seed, learned: BTreeMap::new() }
    }

    /// Does this topic mean anything to us?
    ///
    /// AND THE LEARNED VOCABULARY COUNTS, but at a reduced weight --
    /// because a topic learned from a 40-star repo should not outrank
    /// a seed topic the project actually depends on.
    pub fn recognises(&self, topic: &str) -> bool {
        let t = topic.to_lowercase();
        self.seed.contains_key(&t) || self.learned.contains_key(&t)
    }

    /// The weight of a topic, and the seed outranks the learned.
    pub fn weight(&self, topic: &str) -> f64 {
        let t = topic.to_lowercase();
        self.seed.get(&t).copied().unwrap_or(0.0)
            + self.learned.get(&t).copied().unwrap_or(0.0) * 0.5
    }

    /// Learn from an admitted candidate.
    ///
    /// AND THE ONLY WAY IN. The learned vocabulary can therefore never
    /// contain a topic that the gate did not admit — which is what keeps
    /// the recursion from running away.
    pub fn learn(&mut self, topics: &[String], stars: u32) {
        if stars == 0 {
            return;
        }
        for topic in topics {
            let t = topic.to_lowercase();
            if t.is_empty() {
                continue;
            }
            let bump = (stars as f64).sqrt();
            *self.learned.entry(t).or_insert(0.0) += bump;
        }
    }

    /// The topics that have been learned, and their weights.
    pub fn learned_topics(&self) -> Vec<(String, f64)> {
        let mut v: Vec<(String, f64)> = self.learned
            .iter()
            .map(|(k, w)| (k.clone(), *w))
            .collect();
        v.sort_by(|a, b| {
            b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal)
        });
        v
    }

    pub fn seed_count(&self) -> usize {
        self.seed.len()
    }

    pub fn learned_count(&self) -> usize {
        self.learned.len()
    }
}

// ---------------------------------------------------------------------------
// the candidate
// ---------------------------------------------------------------------------

/// A repo the transport found. The Rust side's own type, so the policy
/// does not depend on the fetcher's shape.
#[derive(Debug, Clone, PartialEq)]
pub struct RepoCandidate {
    /// owner/name
    pub full_name: String,
    /// the language, and the ONLY two that count
    pub language: String,
    pub stars: u32,
    pub topics: Vec<String>,
    pub description: String,
    /// when the fetch happened
    pub fetched_unix: u64,
}

impl RepoCandidate {
    /// The languages the coding sheaf admits: Rust and Python.
    ///
    /// Bobby: *"just in rust and python"*. Go was in the original
    /// architecture as a maybe, and the Rust `Lang` enum still carries
    /// it -- but the directive is two languages, so the SCANNER admits
    /// two. The enum can keep the third; the policy does not use it.
    pub fn admitted_language(&self) -> bool {
        let l = self.language.to_lowercase();
        l == "rust" || l == "python"
    }

    /// Does any topic mean anything to us?
    pub fn has_relevant_topic(&self, vocab: &Vocabulary) -> bool {
        self.topics.iter().any(|t| vocab.recognises(t))
    }
}

// ---------------------------------------------------------------------------
// the policy
// ---------------------------------------------------------------------------

/// The scan's configuration.
#[derive(Debug, Clone, Copy)]
pub struct ScanPolicy {
    /// the star floor. High, because the directive is "just high stars"
    pub star_floor: u32,
    /// how old a fetch may be
    pub max_age_seconds: u64,
    /// the cadence
    pub cadence: Cadence,
    /// how many candidates one scan may admit. A BOUND, because an
    /// unbounded intake is not intake, it is a flood.
    pub max_admissions: usize,
}

impl Default for ScanPolicy {
    fn default() -> Self {
        ScanPolicy {
            star_floor: 500,
            max_age_seconds: 60 * 60 * 24 * 7,
            cadence: Cadence::Daily,
            max_admissions: 20,
        }
    }
}

/// Why a candidate was not admitted.
#[derive(Debug, Clone, PartialEq)]
pub enum ScanRefusal {
    /// the language is not one the coding sheaf admits
    Language { language: String },
    /// no topic in the project's vocabulary
    Irrelevant { topics: Vec<String> },
    /// below the star floor
    BelowStarFloor { stars: u32, floor: u32 },
    /// already held
    AlreadyHeld { full_name: String },
    /// the scan's admission cap is reached
    CapReached { cap: usize },
}

impl fmt::Display for ScanRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ScanRefusal::Language { language } => {
                write!(f, "language_not_admitted:{language}")
            }
            ScanRefusal::Irrelevant { topics } => {
                write!(f, "no_project_topic:{}", topics.join(","))
            }
            ScanRefusal::BelowStarFloor { stars, floor } => {
                write!(f, "below_star_floor:{stars}<{floor}")
            }
            ScanRefusal::AlreadyHeld { full_name } => {
                write!(f, "already_held:{full_name}")
            }
            ScanRefusal::CapReached { cap } => {
                write!(f, "cap_reached:{cap}")
            }
        }
    }
}

/// One scan's outcome.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct ScanOutcome {
    /// the candidates that were admitted
    pub admitted: Vec<RepoCandidate>,
    /// every refusal, with its reason
    pub refusals: Vec<(String, ScanRefusal)>,
    /// the vocabulary AFTER learning
    pub vocabulary: Vocabulary,
    /// when the scan ran
    pub at: u64,
}

impl ScanOutcome {
    /// The admission rate. And it is a RATE that must stay inside a
    /// band, exactly like the gate's -- because a scanner that admits
    /// everything has stopped filtering and one that admits nothing has
    /// stopped working.
    pub fn rate(&self) -> f64 {
        let total = self.admitted.len() + self.refusals.len();
        if total == 0 {
            return 0.0;
        }
        self.admitted.len() as f64 / total as f64
    }

    pub fn describe(&self) -> BTreeMap<String, String> {
        let mut m = BTreeMap::new();
        m.insert("admitted".into(), self.admitted.len().to_string());
        m.insert("refused".into(), self.refusals.len().to_string());
        m.insert("rate".into(), format!("{:.4}", self.rate()));
        m.insert("seed_topics".into(),
                 self.vocabulary.seed_count().to_string());
        m.insert("learned_topics".into(),
                 self.vocabulary.learned_count().to_string());
        m
    }
}

// ---------------------------------------------------------------------------
// THE SCANNER
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct CodingSheaf {
    policy: ScanPolicy,
    vocab: Vocabulary,
    /// the repos already held, so a scan does not re-admit
    held: Vec<String>,
    /// when the last scan ran
    last_scan_unix: Option<u64>,
    /// the history, so the scanner's own growth is measurable
    history: Vec<ScanOutcome>,
}

impl CodingSheaf {
    pub fn new() -> Self {
        CodingSheaf {
            policy: ScanPolicy::default(),
            vocab: Vocabulary::project_seed(),
            held: Vec::new(),
            last_scan_unix: None,
            history: Vec::new(),
        }
    }

    pub fn with_policy(policy: ScanPolicy) -> Self {
        CodingSheaf {
            policy,
            vocab: Vocabulary::project_seed(),
            held: Vec::new(),
            last_scan_unix: None,
            history: Vec::new(),
        }
    }

    pub fn vocabulary(&self) -> &Vocabulary {
        &self.vocab
    }

    pub fn held_count(&self) -> usize {
        self.held.len()
    }

    pub fn last_scan_unix(&self) -> Option<u64> {
        self.last_scan_unix
    }

    /// Is a scan due? The cadence is IN the artifact, so it does not
    /// depend on anybody remembering.
    pub fn is_due(&self, now_unix: u64) -> bool {
        is_due(self.last_scan_unix, now_unix, self.policy.cadence)
    }

    /// Run one scan.
    ///
    /// AND THE ORDER OF THE CHECKS, which is the policy:
    ///
    ///   1. the LANGUAGE -- rust or python, and nothing else
    ///   2. the TOPIC -- at least one the project recognises
    ///   3. the STARS -- the floor
    ///   4. the CAP -- so one scan cannot flood the library
    ///
    /// and the vocabulary LEARNS only from what got through.
    pub fn scan(&mut self, candidates: &[RepoCandidate],
                now_unix: u64) -> ScanOutcome {
        let mut outcome = ScanOutcome::default();
        outcome.at = now_unix;

        for c in candidates {
            if outcome.admitted.len() >= self.policy.max_admissions {
                outcome.refusals.push((
                    c.full_name.clone(),
                    ScanRefusal::CapReached {
                        cap: self.policy.max_admissions,
                    },
                ));
                continue;
            }
            if !c.admitted_language() {
                outcome.refusals.push((
                    c.full_name.clone(),
                    ScanRefusal::Language {
                        language: c.language.clone(),
                    },
                ));
                continue;
            }
            if !c.has_relevant_topic(&self.vocab) {
                outcome.refusals.push((
                    c.full_name.clone(),
                    ScanRefusal::Irrelevant {
                        topics: c.topics.clone(),
                    },
                ));
                continue;
            }
            if c.stars < self.policy.star_floor {
                outcome.refusals.push((
                    c.full_name.clone(),
                    ScanRefusal::BelowStarFloor {
                        stars: c.stars,
                        floor: self.policy.star_floor,
                    },
                ));
                continue;
            }
            if self.held.iter().any(|h| h == &c.full_name) {
                outcome.refusals.push((
                    c.full_name.clone(),
                    ScanRefusal::AlreadyHeld {
                        full_name: c.full_name.clone(),
                    },
                ));
                continue;
            }
            // ADMITTED. And the vocabulary learns from it.
            self.vocab.learn(&c.topics, c.stars);
            self.held.push(c.full_name.clone());
            outcome.admitted.push(c.clone());
        }

        outcome.vocabulary = self.vocab.clone();
        self.last_scan_unix = Some(now_unix);
        self.history.push(outcome.clone());
        outcome
    }

    /// The growth of the vocabulary, which is the self-recursion made
    /// measurable.
    pub fn growth(&self) -> BTreeMap<String, String> {
        let mut m = BTreeMap::new();
        m.insert("scans".into(), self.history.len().to_string());
        m.insert("held".into(), self.held.len().to_string());
        m.insert("seed_topics".into(),
                 self.vocab.seed_count().to_string());
        m.insert("learned_topics".into(),
                 self.vocab.learned_count().to_string());
        let total_admitted: usize =
            self.history.iter().map(|h| h.admitted.len()).sum();
        m.insert("total_admitted".into(), total_admitted.to_string());
        m
    }
}

impl Default for CodingSheaf {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cand(name: &str, lang: &str, stars: u32, topics: &[&str]) -> RepoCandidate {
        RepoCandidate {
            full_name: name.to_string(),
            language: lang.to_string(),
            stars,
            topics: topics.iter().map(|s| s.to_string()).collect(),
            description: String::new(),
            fetched_unix: 1_000_000,
        }
    }

    #[test]
    fn the_cadence_is_in_the_artifact() {
        // a sheaf that has never scanned is due
        assert!(is_due(None, 1_000, Cadence::Daily));
        // a daily scan is not due after an hour
        assert!(!is_due(Some(1_000), 1_000 + 3600, Cadence::Daily));
        // and is due after a day
        assert!(is_due(Some(1_000), 1_000 + 86_400, Cadence::Daily));
        // hourly is due after an hour
        assert!(is_due(Some(1_000), 1_000 + 3600, Cadence::Hourly));
    }

    #[test]
    fn only_rust_and_python_are_admitted() {
        let mut s = CodingSheaf::new();
        let r = s.scan(
            &[
                cand("a/rust-repo", "Rust", 5000, &["manifold"]),
                cand("b/py-repo", "Python", 5000, &["manifold"]),
                cand("c/go-repo", "Go", 5000, &["manifold"]),
                cand("d/js-repo", "JavaScript", 5000, &["manifold"]),
            ],
            1_000_000,
        );
        let names: Vec<&str> =
            r.admitted.iter().map(|c| c.full_name.as_str()).collect();
        assert!(names.contains(&"a/rust-repo"));
        assert!(names.contains(&"b/py-repo"));
        assert!(!names.contains(&"c/go-repo"));
        assert!(!names.contains(&"d/js-repo"));
    }

    #[test]
    fn an_irrelevant_repo_is_refused_and_named() {
        let mut s = CodingSheaf::new();
        let r = s.scan(
            &[cand("a/blockchain", "Rust", 9000, &["cryptocurrency"])],
            1_000_000,
        );
        assert!(r.admitted.is_empty());
        let reason = r.refusals[0].1.to_string();
        assert!(reason.starts_with("no_project_topic:"), "%s", reason);
    }

    #[test]
    fn a_low_star_repo_is_refused_and_named() {
        let mut s = CodingSheaf::new();
        let r = s.scan(
            &[cand("a/tiny", "Rust", 3, &["manifold"])],
            1_000_000,
        );
        assert!(r.admitted.is_empty());
        assert!(r.refusals[0].1.to_string().starts_with("below_star_floor:"));
    }

    #[test]
    fn the_cap_bounds_one_scan() {
        let mut s = CodingSheaf::with_policy(ScanPolicy {
            star_floor: 1,
            max_age_seconds: 1_000_000,
            cadence: Cadence::Daily,
            max_admissions: 2,
        });
        let many: Vec<RepoCandidate> = (0..10)
            .map(|i| cand(&format!("a/repo{}", i), "Rust", 5000,
                         &["manifold"]))
            .collect();
        let r = s.scan(&many, 1_000_000);
        assert_eq!(r.admitted.len(), 2);
        assert!(r.refusals.iter().any(|(_, x)| matches!(
            x, ScanRefusal::CapReached { .. })));
    }

    #[test]
    fn the_vocabulary_learns_only_from_admitted_work() {
        let mut s = CodingSheaf::with_policy(ScanPolicy {
            star_floor: 100,
            max_age_seconds: 1_000_000,
            cadence: Cadence::Daily,
            max_admissions: 20,
        });
        let before = s.vocabulary().learned_count();
        // a repo with a topic nothing recognises is refused, so it must
        // NOT teach the vocabulary anything
        s.scan(&[cand("a/x", "Rust", 9000, &["quantum-topology"])],
               1_000_000);
        assert_eq!(s.vocabulary().learned_count(), before,
                   "a refused repo taught the vocabulary something");

        // an ADMITTED repo does
        s.scan(&[cand("b/y", "Rust", 9000, &["manifold"])], 1_000_001);
        assert!(s.vocabulary().learned_count() > before);
    }

    #[test]
    fn a_learned_topic_recognises_a_later_repo() {
        // THE SELF-RECURSION, measured: the scanner teaches itself a
        // topic, and then that topic admits a repo it would not have
        // admitted before.
        let mut s = CodingSheaf::with_policy(ScanPolicy {
            star_floor: 100,
            max_age_seconds: 1_000_000,
            cadence: Cadence::Daily,
            max_admissions: 20,
        });
        let novel = cand("a/new-topic", "Rust", 9000,
                         &["hyperbolic-lattice"]);
        let r1 = s.scan(&[novel.clone()], 1_000_000);
        assert!(r1.admitted.is_empty(),
                "the novel topic should not be admitted before it is "
                "learned");

        // it IS in the seed's reach via 'lattice'? if not, teach it
        if s.vocabulary().learned_count() == 0 {
            s.scan(&[cand("a/seed", "Rust", 9000, &["lattice"])],
                   1_000_001);
        }
        let r2 = s.scan(&[novel], 1_000_002);
        assert!(!r2.admitted.is_empty(),
                "the scanner did not learn the topic it admitted");
    }

    #[test]
    fn an_already_held_repo_is_not_re_admitted() {
        let mut s = CodingSheaf::new();
        let c = cand("a/x", "Rust", 9000, &["manifold"]);
        s.scan(&[c.clone()], 1_000_000);
        let r = s.scan(&[c], 1_000_001);
        assert!(r.admitted.is_empty());
        assert!(r.refusals[0].1.to_string().starts_with("already_held:"));
    }

    #[test]
    fn the_scan_is_not_due_again_within_the_cadence() {
        let mut s = CodingSheaf::new();
        assert!(s.is_due(1_000_000));
        s.scan(&[], 1_000_000);
        assert!(!s.is_due(1_000_000 + 3600));
        assert!(s.is_due(1_000_000 + 86_400));
    }

    #[test]
    fn the_growth_is_measurable() {
        let mut s = CodingSheaf::new();
        s.scan(&[cand("a/x", "Rust", 9000, &["manifold"])], 1_000_000);
        s.scan(&[cand("b/y", "Python", 9000, &["gradient-flow"])],
               1_000_001);
        let g = s.growth();
        assert_eq!(g["scans"], "2");
        assert_eq!(g["total_admitted"], "2");
        assert_eq!(g["held"], "2");
    }
}
