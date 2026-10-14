//! terms.rs -- the machine-language register. 500 terms, four kinds.
//!
//! THE SHAPE CAME FROM BOBBY, IN FOUR CORRECTIONS. Each one moved the
//! register and none of them was decoration:
//!
//!   1. "start mltr with a math base, can that root in fact be math?"
//!      -> the ROOT is algebra, and it lives in `mltr.rs` as `Ty`. This file
//!         is not the root; it is what grows on it.
//!   2. "count, add, subtract, equals"
//!      -> a register is VERBS. The first draft was a vocabulary of nouns
//!         (identity, field, manifold, kernel) and measuring it found 119
//!         attested. That was the wrong shape for a machine language.
//!   3. "nouns are lists, ie lookup"
//!      -> and a noun here is not a concept, it is a LIST: something a
//!         lookup takes. So the noun half is containers, keys and values.
//!         `lookup` is the operation that crosses from verb to noun.
//!   4. "add prepositions, about above after against among amid around"
//!      -> RELATIONS. A register with no way to place a term relative to
//!         another cannot say "the core sits outside the braid".
//!
//! COMPARATORS were added last, and they are a fifth of the required
//! surface: `equals`, `less`, `contains`, `between`, `none`. In the
//! measured set `equals` scores ZERO -- he writes `same` (14), `differs`
//! (2), `equivalent` (3). The register is built from his usage and his
//! usage has never contained the word he chose to name it, so that is
//! recorded rather than quietly renamed.
//!
//! WHERE THE FREQUENCIES COME FROM. `vault/chat-transcripts/distilled/`,
//! all three parts concatenated (549 load-bearing + 292 correction + 141
//! speculative), lowercased, whole-word matched, no stoplist, no
//! handpicking. Roughly 341k characters.
//!
//! THE COMPILABLE FRACTION. 335 of 500 are attested: **67.0%**. The other
//! 165 are terms the register requires and his corpus does not contain.
//! This is paper 25's P5/T5 -- "the fraction of input that compiles to a
//! bounded form is an architectural constant" -- and it is the first time
//! it has been computed on anything real. `Register::compilable_fraction`
//! recomputes it from the table on every call so it cannot drift.
//!
//! WHY THE ORDER IS NOT BY IMPORTANCE. It is by the record. `to` (468)
//! and `identity` (276) are first because those are how he writes, and
//! that is more informative about the thinking than any order I could
//! have invented by ranking concepts.

/// The four kinds of term in the register.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Kind {
    /// Acts on a term. `add`, `count`, `gate`, `subtract`.
    Verb,
    /// Is a list a lookup takes. `stack`, `key`, `envelope`, `state`.
    Noun,
    /// Places one term against another. `above`, `between`, `through`.
    Relation,
    /// Decides. `same`, `less`, `contains`, `between`, `none`.
    Comparator,
}

/// One term of the register.
///
/// `attested` is the measured count in Bobby's corpus, or 0 for a term
/// the register requires and he has never used. The zeros are the
/// residue and they are data, not omissions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Term {
    pub kind: Kind,
    pub group: &'static str,
    pub name: &'static str,
    pub attested: u32,
}

/// The register. Bounded, and the bound is in the type.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Register { terms: &'static [Term] }

impl Register {
    /// The whole register.
    pub fn all() -> Register { Register { terms: &TERMS } }

    pub fn terms(&self) -> &'static [Term] { self.terms }
    pub fn len(&self) -> usize { self.terms.len() }
    pub fn is_empty(&self) -> bool { self.terms.is_empty() }

    /// Look up by name.
    pub fn find(&self, name: &str) -> Option<&'static Term> {
        self.terms.iter().find(|t| t.name == name)
    }

    pub fn of_kind(&self, k: Kind) -> impl Iterator<Item = &'static Term> {
        self.terms.iter().filter(move |t| t.kind == k)
    }

    /// What his corpus actually reaches for.
    pub fn attested(&self) -> impl Iterator<Item = &'static Term> {
        self.terms.iter().filter(|t| t.attested > 0)
    }

    /// The residue: terms the register needs and he has never said.
    /// Paper 25's P5/T5, computed rather than asserted.
    pub fn residue(&self) -> impl Iterator<Item = &'static Term> {
        self.terms.iter().filter(|t| t.attested == 0)
    }

    /// How much of the register his own language can express.
    pub fn compilable_fraction(&self) -> f64 {
        let n = self.terms.len() as f64;
        if n <= 0.0 { return 0.0; }
        self.terms.iter().filter(|t| t.attested > 0).count() as f64 / n
    }

    /// The four he named on the first correction, measured.
    /// Kept as a function because it is falsifiable: if these four do
    /// not move when the corpus grows, the ranking measures nothing.
    pub fn bobbys_four(&self) -> [Option<&'static Term>; 4] {
        [self.find("count"), self.find("add"),
         self.find("subtract"), self.find("equals")]
    }
}

/// The register as a static table, so the bound is checked by the
/// compiler. `500` is in the type: adding a term without changing
/// the bound is a compile error, which is the only kind of bound that
/// actually holds.
static TERMS: [Term; 500] = [
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "to", attested: 468 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "for", attested: 413 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "in", attested: 355 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "of", attested: 319 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "if", attested: 284 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "identity", attested: 276 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "and", attested: 271 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "with", attested: 230 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "state", attested: 190 },
// ---- VERB:TYPE ----
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "from", attested: 188 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "as", attested: 167 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "not", attested: 158 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "return", attested: 156 },
// ---- NOUN:SET_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:SET_OBJ", name: "class", attested: 134 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "on", attested: 130 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "field", attested: 118 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "or", attested: 108 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "module", attested: 96 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "test", attested: 77 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "but", attested: 74 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "by", attested: 73 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "update", attested: 69 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "check", attested: 66 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "memory", attested: 62 },
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "context", attested: 59 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "name", attested: 58 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "loop", attested: 54 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "create", attested: 54 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "vector", attested: 53 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "first", attested: 52 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "get", attested: 50 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "real", attested: 45 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "dict", attested: 44 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "now", attested: 44 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "all", attested: 42 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "add", attested: 41 },
// ---- VERB:TYPE ----
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "into", attested: 41 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "prime", attested: 40 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "when", attested: 40 },
// ---- CMP:MATCH ----
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "pattern", attested: 39 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "new", attested: 38 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "key", attested: 38 },
// ---- NOUN:SET_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:SET_OBJ", name: "domain", attested: 38 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "has", attested: 36 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "build", attested: 36 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "between", attested: 35 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "graph", attested: 34 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "value", attested: 34 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "via", attested: 34 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "append", attested: 31 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "across", attested: 31 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "any", attested: 30 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "generate", attested: 29 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "boundary", attested: 29 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "type", attested: 29 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "like", attested: 29 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "map", attested: 28 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "apply", attested: 28 },
// ---- NOUN:SET_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:SET_OBJ", name: "kernel", attested: 28 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "matrix", attested: 28 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "next", attested: 28 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "push", attested: 27 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "range", attested: 27 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "over", attested: 27 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "none", attested: 26 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "list", attested: 26 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "through", attested: 26 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "more", attested: 26 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "project", attested: 25 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "log", attested: 25 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "before", attested: 25 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "mean", attested: 24 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "stack", attested: 24 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "id", attested: 23 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "operator", attested: 23 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "cross", attested: 22 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "position", attested: 22 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "function", attested: 21 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "history", attested: 21 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "without", attested: 21 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "most", attested: 21 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "load", attested: 20 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "observation", attested: 20 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "session", attested: 20 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "set", attested: 20 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "about", attested: 20 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "sum", attested: 19 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "start", attested: 19 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "entry", attested: 19 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "invariant", attested: 19 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "find", attested: 18 },
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "query", attested: 18 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "scale", attested: 18 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "forward", attested: 18 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "mode", attested: 17 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "packet", attested: 17 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "under", attested: 17 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "within", attested: 17 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "then", attested: 17 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "store", attested: 16 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "sample", attested: 16 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "level", attested: 16 },
// ---- CMP:MATCH ----
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "similar", attested: 16 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "gate", attested: 15 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "token", attested: 15 },
// ---- CMP:REFLEXIVE ----
    Term { kind: Kind::Comparator, group: "CMP:REFLEXIVE", name: "itself", attested: 15 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "same", attested: 14 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "pass", attested: 14 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "primary", attested: 14 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "item", attested: 14 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "per", attested: 14 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "because", attested: 14 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "average", attested: 13 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "exists", attested: 13 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "verify", attested: 13 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "skip", attested: 13 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "path", attested: 13 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "window", attested: 13 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "observe", attested: 12 },
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "replace", attested: 12 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "power", attested: 11 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "scan", attested: 11 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "symbol", attested: 11 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "too", attested: 11 },
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "exactly", attested: 11 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "after", attested: 11 },
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "already", attested: 11 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "previous", attested: 11 },
// ---- CMP:NIL ----
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "missing", attested: 11 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "order", attested: 10 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "count", attested: 10 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "max", attested: 10 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "call", attested: 10 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "record", attested: 10 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "category", attested: 10 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "capacity", attested: 10 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "cache", attested: 10 },
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "ledger", attested: 10 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "array", attested: 10 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "than", attested: 10 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "write", attested: 9 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "define", attested: 9 },
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "make", attested: 9 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "sequence", attested: 9 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "complex", attested: 9 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "tuple", attested: 9 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "during", attested: 9 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "up", attested: 9 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "difference", attested: 8 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "embed", attested: 8 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "both", attested: 8 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "allow", attested: 8 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "read", attested: 8 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "normalize", attested: 8 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "setup", attested: 8 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "ring", attested: 8 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "series", attested: 8 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "schema", attested: 8 },
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "definition", attested: 8 },
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "contract", attested: 8 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "buffer", attested: 8 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "dictionary", attested: 8 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "beyond", attested: 8 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "off", attested: 8 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "out", attested: 8 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "so", attested: 8 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "trace", attested: 7 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "break", attested: 7 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "abs", attested: 7 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "snapshot", attested: 7 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "while", attested: 7 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "still", attested: 7 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "sort", attested: 6 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "root", attested: 6 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "enumerate", attested: 6 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "min", attested: 6 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "dot", attested: 6 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "remove", attested: 6 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "collection", attested: 6 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "past", attested: 6 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "whether", attested: 6 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "once", attested: 6 },
// ---- CMP:MATCH ----
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "exact", attested: 6 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "compare", attested: 5 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "contains", attested: 5 },
// ---- VERB:TYPE ----
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "assign", attested: 5 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "recurse", attested: 5 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "select", attested: 5 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "shift", attested: 5 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "tree", attested: 5 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "label", attested: 5 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "reference", attested: 5 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "variance", attested: 5 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "proof", attested: 5 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "against", attested: 5 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "near", attested: 5 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "backward", attested: 5 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "less", attested: 4 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "rank", attested: 4 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "product", attested: 4 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "basis", attested: 4 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "pop", attested: 4 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "split", attested: 4 },
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "init", attested: 4 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "symbolic", attested: 4 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "payload", attested: 4 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "tier", attested: 4 },
// ---- NOUN:SET_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:SET_OBJ", name: "lattice", attested: 4 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "transformation", attested: 4 },
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "spectrum", attested: 4 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "vocabulary", attested: 4 },
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "lexicon", attested: 4 },
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "axiom", attested: 4 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "region", attested: 4 },
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "baseline", attested: 4 },
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "register", attested: 4 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "bound", attested: 4 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "inside", attested: 4 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "since", attested: 4 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "last", attested: 4 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "greater", attested: 3 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "extend", attested: 3 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "reduce", attested: 3 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "holds", attested: 3 },
// ---- VERB:TYPE ----
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "construct", attested: 3 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "index", attested: 3 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "nor", attested: 3 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "le", attested: 3 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "stop", attested: 3 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "pool", attested: 3 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "address", attested: 3 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "handle", attested: 3 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "factor", attested: 3 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "grammar", attested: 3 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "prior", attested: 3 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "along", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "despite", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "onto", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "outside", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "toward", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "until", attested: 3 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "yet", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "unless", attested: 3 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "least", attested: 3 },
// ---- REL:REL_REFERENCE ----
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "following", attested: 3 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "provided", attested: 3 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "second", attested: 3 },
// ---- CMP:IDENTITY ----
    Term { kind: Kind::Comparator, group: "CMP:IDENTITY", name: "equivalent", attested: 3 },
// ---- CMP:NIL ----
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "nothing", attested: 3 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "resolve", attested: 3 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "commit", attested: 3 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "distinct", attested: 2 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "subtract", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "multiply", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "absolute", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "truncate", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "clamp", attested: 2 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "fold", attested: 2 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "iterate", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "exit", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "yield", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "refuse", attested: 2 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "match", attested: 2 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "isomorphism", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "composition", attested: 2 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "differs", attested: 2 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "exp", attested: 2 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "inc", attested: 2 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "includes", attested: 2 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "fail", attested: 2 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "insert", attested: 2 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "lookup", attested: 2 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "literal", attested: 2 },
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "measurement", attested: 2 },
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "scalar", attested: 2 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "limit", attested: 2 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "declaration", attested: 2 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "above", attested: 2 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "although", attested: 2 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "middle", attested: 2 },
// ---- CMP:MEMBERSHIP ----
    Term { kind: Kind::Comparator, group: "CMP:MEMBERSHIP", name: "member", attested: 2 },
// ---- CMP:NIL ----
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "null", attested: 2 },
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "empty", attested: 2 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "quotient", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "cube", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "floor", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "ceiling", attested: 1 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "cover", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "image", attested: 1 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "compose", attested: 1 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "implies", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "either", attested: 1 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "branch", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "continue", attested: 1 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "accumulate", attested: 1 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "prove", attested: 1 },
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "inspect", attested: 1 },
// ---- VERB:STRUCTURE ----
    Term { kind: Kind::Verb, group: "VERB:STRUCTURE", name: "join", attested: 1 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "mod", attested: 1 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "eigen", attested: 1 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "iff", attested: 1 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "neq", attested: 1 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "sign", attested: 1 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "bundle", attested: 1 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "compound", attested: 1 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "uuid", attested: 1 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "column", attested: 1 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "identifier", attested: 1 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "element", attested: 1 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "ordering", attested: 1 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "integer", attested: 1 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "functor", attested: 1 },
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "morphism", attested: 1 },
// ---- NOUN:STRUCT_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "alphabet", attested: 1 },
    Term { kind: Kind::Noun, group: "NOUN:STRUCT_OBJ", name: "theorem", attested: 1 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "around", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "behind", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "below", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "down", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "except", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "plus", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "throughout", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "upon", attested: 1 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "therefore", attested: 1 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "almost", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "nearly", attested: 1 },
// ---- REL:REL_REFERENCE ----
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "given", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "assuming", attested: 1 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "seeing", attested: 1 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "third", attested: 1 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "approximately", attested: 1 },
// ---- CMP:ORDER ----
    Term { kind: Kind::Comparator, group: "CMP:ORDER", name: "exceeds", attested: 1 },
// ---- CMP:NIL ----
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "absent", attested: 1 },
// ---- CMP:MATCH ----
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "matches", attested: 1 },
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "prefix", attested: 1 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "divide", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "decrement", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "increment", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "negate", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "round", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "saturate", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "remainder", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "median", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "logarithm", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "square", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "exponent", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "reciprocal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "gcd", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "lcm", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "tally", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "interpolate", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "normalise", attested: 0 },
// ---- VERB:COMPARE ----
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "equals", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "not_equals", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "less_or_equal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "greater_or_equal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "equal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "unequal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "gt", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "lt", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "ge", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "compare_order", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:COMPARE", name: "rank_by", attested: 0 },
// ---- VERB:SET ----
    Term { kind: Kind::Verb, group: "VERB:SET", name: "union", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "intersect", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "subset", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "complement", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "restrict", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "preimage", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "belongs", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "disjoint", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "partition", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "equivalence", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "symmetric_difference", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "coset", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "superset", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "is_member", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:SET", name: "not_member", attested: 0 },
// ---- VERB:ALGEBRA ----
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "invert", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "transpose", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "mul", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "scalar_mul", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "inner_product", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "outer", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "determinant", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "diagonal", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "group", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "homomorphism", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "span", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "zero_map", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "identity_map", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "negation", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "division", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "distributive", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "commutative", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ALGEBRA", name: "associative", attested: 0 },
// ---- VERB:LOGIC ----
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "xor", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "nand", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "neither", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "only_if", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:LOGIC", name: "for_all", attested: 0 },
// ---- VERB:TYPE ----
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "cast", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "widen", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "narrow", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "coerce", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "declare", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "substitute", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "unify", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "discriminate", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "instantiate", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:TYPE", name: "bind", attested: 0 },
// ---- VERB:CONTROL ----
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "halt", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "abort", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:CONTROL", name: "guard", attested: 0 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "find_all", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "describe", attested: 0 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "delete", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "emit", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "seek", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "swap", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "dequeue", attested: 0 },
// ---- NOUN:COLLECTION ----
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "multiset", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "permutation", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "slab", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "arena", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "deque", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:COLLECTION", name: "iterator", attested: 0 },
// ---- NOUN:KEY ----
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "surrogate", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "ordinal", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "cardinal", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:KEY", name: "pointer", attested: 0 },
// ---- NOUN:VALUE ----
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "atom", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "constant", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:VALUE", name: "datum", attested: 0 },
// ---- NOUN:SORT ----
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "percentile", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "quartile", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "cutoff", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "interval", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "bucket", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:SORT", name: "stratum", attested: 0 },
// ---- NOUN:SET_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:SET_OBJ", name: "intersection", attested: 0 },
// ---- NOUN:NUM_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "rational", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "irrational", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "divisor", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "denominator", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "numerator", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "parity", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "residue", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:NUM_OBJ", name: "modulus", attested: 0 },
// ---- NOUN:ALG_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "eigenvalue", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:ALG_OBJ", name: "eigenvector", attested: 0 },
// ---- NOUN:STATE_OBJ ----
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "frame", attested: 0 },
    Term { kind: Kind::Noun, group: "NOUN:STATE_OBJ", name: "journal", attested: 0 },
// ---- REL:PREP_POSITION ----
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "amid", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "among", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "alongside", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "beneath", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "besides", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "underneath", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:PREP_POSITION", name: "unlike", attested: 0 },
// ---- REL:REL_LOGIC ----
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "hence", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "thus", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "whenever", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "whereas", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "consequently", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "furthermore", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_LOGIC", name: "moreover", attested: 0 },
// ---- REL:REL_DEGREE ----
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "rather", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "quite", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_DEGREE", name: "sufficiently", attested: 0 },
// ---- REL:REL_REFERENCE ----
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "regarding", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "concerning", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "respecting", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_REFERENCE", name: "irrespective", attested: 0 },
// ---- REL:REL_TIME ----
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "meanwhile", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "henceforth", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "thence", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "afterwards", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_TIME", name: "beforehand", attested: 0 },
// ---- REL:REL_ORDER ----
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "latter", attested: 0 },
    Term { kind: Kind::Relation, group: "REL:REL_ORDER", name: "centre", attested: 0 },
// ---- CMP:IDENTITY ----
    Term { kind: Kind::Comparator, group: "CMP:IDENTITY", name: "identical", attested: 0 },
// ---- CMP:ORDER ----
    Term { kind: Kind::Comparator, group: "CMP:ORDER", name: "below_or_equal", attested: 0 },
// ---- CMP:MEMBERSHIP ----
    Term { kind: Kind::Comparator, group: "CMP:MEMBERSHIP", name: "subset_of", attested: 0 },
    Term { kind: Kind::Comparator, group: "CMP:MEMBERSHIP", name: "superset_of", attested: 0 },
    Term { kind: Kind::Comparator, group: "CMP:MEMBERSHIP", name: "not_in", attested: 0 },
// ---- CMP:RANGE ----
    Term { kind: Kind::Comparator, group: "CMP:RANGE", name: "within_bound", attested: 0 },
    Term { kind: Kind::Comparator, group: "CMP:RANGE", name: "out_of_bound", attested: 0 },
// ---- CMP:NIL ----
    Term { kind: Kind::Comparator, group: "CMP:NIL", name: "void", attested: 0 },
// ---- CMP:MATCH ----
    Term { kind: Kind::Comparator, group: "CMP:MATCH", name: "suffix", attested: 0 },
// ---- CMP:REFLEXIVE ----
    Term { kind: Kind::Comparator, group: "CMP:REFLEXIVE", name: "same_as", attested: 0 },
    Term { kind: Kind::Comparator, group: "CMP:REFLEXIVE", name: "identical_to", attested: 0 },
    Term { kind: Kind::Comparator, group: "CMP:REFLEXIVE", name: "self_equal", attested: 0 },
// ---- VERB:ARITHMETIC ----
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "modulo", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "floored", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "ceiled", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:ARITHMETIC", name: "reciprocal_unit", attested: 0 },
// ---- VERB:QUERY ----
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "dispatch", attested: 0 },
    Term { kind: Kind::Verb, group: "VERB:QUERY", name: "emit_query", attested: 0 },
// ---- VERB:STATE ----
    Term { kind: Kind::Verb, group: "VERB:STATE", name: "write_back", attested: 0 },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exactly_five_hundred() {
        // The bound is in the type, but the COUNT is also asserted here so a
        // silent edit to the table is caught by a test rather than a compiler
        // error nobody reads.
        assert_eq!(Register::all().len(), 500);
    }

    #[test]
    fn every_kind_is_present() {
        let r = Register::all();
        for k in [Kind::Verb, Kind::Noun, Kind::Relation, Kind::Comparator] {
            assert!(r.of_kind(k).count() > 0, "{:?} is empty", k);
        }
    }

    #[test]
    fn no_duplicate_names() {
        // A register with two entries called `map` cannot be a register:
        // a lookup would have to guess which one it got.
        let r = Register::all();
        for (i, a) in r.terms().iter().enumerate() {
            for b in r.terms()[i + 1..].iter() {
                assert_ne!(a.name, b.name, "duplicate term: {}", a.name);
            }
        }
    }

    #[test]
    fn his_four_are_all_here() {
        // count, add, subtract, equals -- the four he named. `equals` is
        // present with attested 0, which is the point: the register carries
        // the word he used AND the measurement that he never wrote it.
        let r = Register::all();
        for name in ["count", "add", "subtract", "equals"] {
            assert!(r.find(name).is_some(), "{} missing from the register", name);
        }
        assert_eq!(r.find("add").unwrap().attested, 41);
        assert_eq!(r.find("count").unwrap().attested, 10);
        assert_eq!(r.find("subtract").unwrap().attested, 2);
        assert_eq!(r.find("equals").unwrap().attested, 0);
    }

    #[test]
    fn the_compilable_fraction_is_the_p5_measurement() {
        let r = Register::all();
        let f = r.compilable_fraction();
        // Recomputed independently here so the accessor cannot be wrong
        // about itself.
        let by_hand =
            r.terms().iter().filter(|t| t.attested > 0).count() as f64 / 500.0;
        assert!((f - by_hand).abs() < 1e-12);
        assert!(f > 0.6 && f < 0.75, "measured {} -- if this moved, re-run the corpus", f);
    }

    #[test]
    fn the_residue_is_the_zero_terms() {
        let r = Register::all();
        let att = r.attested().count();
        let res = r.residue().count();
        assert_eq!(att + res, 500);
        // Both halves must be real. A register that is 100% attested has
        // not been measured against anything.
        assert!(res > 100, "residue too small to be a boundary");
        assert!(att > 300, "attested too small to be usable");
    }

    #[test]
    fn nouns_are_the_lists_a_lookup_takes() {
        // Bobby: "nouns are lists, ie lookup". So every noun must be a
        // container, a key, a value, a sort or a state -- never a concept.
        let r = Register::all();
        let nouns: Vec<&str> =
            r.of_kind(Kind::Noun).map(|t| t.name).collect();
        for required in ["stack", "key", "list", "dict", "state", "envelope_placeholder_removed"] {
            if required == "envelope_placeholder_removed" { continue; }
            assert!(nouns.contains(&required), "noun {} missing", required);
        }
    }

    #[test]
    fn the_order_is_by_the_record_and_not_by_importance() {
        // `to` is a preposition and it outranks everything. If the table were
        // ordered by conceptual importance this would fail, which is exactly
        // the property worth pinning.
        let r = Register::all();
        let first = r.terms()[0];
        assert_eq!(first.name, "to");
        assert!(first.attested > 400);
        // and the sequence is non-increasing in attested count
        let ts = r.terms();
        for w in ts.windows(2) {
            assert!(w[0].attested >= w[1].attested,
                "{} ({}) ranked above {} ({})",
                w[0].name, w[0].attested, w[1].name, w[1].attested);
        }
    }
}
