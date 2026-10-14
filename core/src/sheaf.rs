//! The sheaf contract. Bounded means bounded.
//!
//! Two rules, and they are the reason this file exists rather than a
//! README:
//!
//!   1. A source not named here cannot enter. Adding one is a change to
//!      this enum, which is a diff, which is reviewable. A filter in a
//!      config file is a filter somebody edits at 3am.
//!
//!   2. A language not named here cannot enter. Same reason. "Bounded"
//!      with a soft boundary is unbounded.
//!
//! Both are `#[non_exhaustive]`-free on purpose: adding a variant is a
//! breaking change and should look like one.

use std::fmt;

// NOTE: no serde. The core has ZERO dependencies on purpose -- a governor
// that pulls in a serialization stack is a governor whose supply chain is
// part of the trust boundary. The Python bridge serialises at the edge.

// ---------------------------------------------------------------------------
// sources
// ---------------------------------------------------------------------------

/// The only three. Per Bobby, 2026-10-14: *"ONLY hf and arxiv"* and
/// github.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Source {
    HuggingFace,
    Arxiv,
    Github,
}

impl Source {
    pub const ALL: [Source; 3] = [Source::HuggingFace, Source::Arxiv, Source::Github];

    pub fn as_str(&self) -> &'static str {
        match self {
            Source::HuggingFace => "hf",
            Source::Arxiv => "arxiv",
            Source::Github => "github",
        }
    }
}

impl fmt::Display for Source {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

// ---------------------------------------------------------------------------
// languages
// ---------------------------------------------------------------------------

/// The only three. Per Bobby: *"ONLY python rust and go"*, and earlier
/// *"begin rust python only maybe go"*.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Lang {
    Python,
    Rust,
    Go,
}

impl Lang {
    pub const ALL: [Lang; 3] = [Lang::Python, Lang::Rust, Lang::Go];

    pub fn as_str(&self) -> &'static str {
        match self {
            Lang::Python => "python",
            Lang::Rust => "rust",
            Lang::Go => "go",
        }
    }

    /// The file extensions this language admits. Used by the fetcher to
    /// decide what is a candidate at all, so the filter is not a second
    /// pass somebody forgets to run.
    pub fn extensions(&self) -> &'static [&'static str] {
        match self {
            Lang::Python => &["py", "pyi"],
            Lang::Rust => &["rs"],
            Lang::Go => &["go"],
        }
    }
}

impl fmt::Display for Lang {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

// ---------------------------------------------------------------------------
// what may enter
// ---------------------------------------------------------------------------

/// A candidate from the outside world, before it is admitted.
///
/// Every field is load-bearing. `source` and `lang` are enums, so an
/// unlisted source or language does not compile. `stars` exists because
/// star count is the SNR proxy for code, and it is the ordering signal
/// the hourly pull uses.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Candidate {
    pub source: Source,
    pub lang: Lang,
    pub repo_or_id: String,
    pub path: String,
    pub stars: u32,
    pub sha256: String,
    /// When the pull happened. Snippets must be recent or they are stale
    /// code, and stale code in a sheaf is a lie about the present.
    pub fetched_unix: u64,
}

/// Why something did not enter. Naming the reason is the whole point --
/// a bare refusal is unactionable.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refusal {
    UnknownSource(String),
    UnknownLanguage(String),
    NoLicense,
    Stale { age_seconds: u64, max_age_seconds: u64 },
    TooLarge { bytes: u64, max_bytes: u64 },
    AlreadyHeld { sha256: String },
    BelowStarFloor { stars: u32, floor: u32 },
}

impl fmt::Display for Refusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Refusal::UnknownSource(s) => write!(f, "source_not_admitted:{s}"),
            Refusal::UnknownLanguage(s) => write!(f, "language_not_admitted:{s}"),
            Refusal::NoLicense => write!(f, "no_license"),
            Refusal::Stale { age_seconds, max_age_seconds } => {
                write!(f, "stale:{age_seconds}s>{max_age_seconds}s")
            }
            Refusal::TooLarge { bytes, max_bytes } => write!(f, "too_large:{bytes}>{max_bytes}"),
            Refusal::AlreadyHeld { sha256 } => write!(f, "already_held:{sha256}"),
            Refusal::BelowStarFloor { stars, floor } => write!(f, "below_star_floor:{stars}<{floor}"),
        }
    }
}

/// The admission rule for the coding sheaf.
#[derive(Debug, Clone, Copy)]
pub struct Admission {
    /// SNR floor. Star count is the proxy.
    pub star_floor: u32,
    /// Snippets older than this are stale code.
    pub max_age_seconds: u64,
    /// Per-file ceiling.
    pub max_bytes: u64,
}

impl Default for Admission {
    fn default() -> Self {
        Admission { star_floor: 50, max_age_seconds: 60 * 60 * 24 * 30, max_bytes: 1 << 20 }
    }
}

/// Admit or refuse. The only place a candidate crosses the boundary.
pub fn admit(c: &Candidate, now_unix: u64, a: &Admission) -> Result<(), Refusal> {
    if !Source::ALL.contains(&c.source) {
        return Err(Refusal::UnknownSource(format!("{:?}", c.source)));
    }
    if !Lang::ALL.contains(&c.lang) {
        return Err(Refusal::UnknownLanguage(format!("{:?}", c.lang)));
    }
    if c.stars < a.star_floor {
        return Err(Refusal::BelowStarFloor { stars: c.stars, floor: a.star_floor });
    }
    let age = now_unix.saturating_sub(c.fetched_unix);
    if age > a.max_age_seconds {
        return Err(Refusal::Stale { age_seconds: age, max_age_seconds: a.max_age_seconds });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cand() -> Candidate {
        Candidate {
            source: Source::Arxiv,
            lang: Lang::Rust,
            repo_or_id: "arxiv/2401.00001".into(),
            path: "src/lib.rs".into(),
            stars: 5000,
            sha256: "abc123".into(),
            fetched_unix: 1_000_000,
        }
    }

    #[test]
    fn exactly_three_sources() {
        assert_eq!(Source::ALL.len(), 3);
        assert_eq!(Lang::ALL.len(), 3);
    }

    #[test]
    fn good_candidate_admitted() {
        let a = Admission::default();
        assert!(admit(&cand(), 1_000_000, &a).is_ok());
    }

    #[test]
    fn stale_refused_and_named() {
        let a = Admission::default();
        let now = 1_000_000 + a.max_age_seconds + 1;
        let e = admit(&cand(), now, &a).unwrap_err();
        assert!(matches!(e, Refusal::Stale { .. }));
        assert!(e.to_string().starts_with("stale:"));
    }

    #[test]
    fn below_star_floor_refused_and_named() {
        let mut a = Admission::default();
        a.star_floor = 999_999;
        let e = admit(&cand(), 1_000_000, &a).unwrap_err();
        assert!(matches!(e, Refusal::BelowStarFloor { .. }));
    }

    #[test]
    fn extension_filter_matches_the_enum() {
        // a .ts file must not be reachable as a candidate for any lang
        for l in Lang::ALL {
            assert!(!l.extensions().contains(&"ts"));
            assert!(!l.extensions().contains(&"js"));
        }
    }
}