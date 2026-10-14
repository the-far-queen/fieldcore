//! terms.rs -- the machine-language register. 500 terms, grouped by KIND.
//!
//! THE SHAPE CAME FROM BOBBY, IN SIX CORRECTIONS. Each one moved the
//! register and none of them was decoration:
//!
//!   1. "start mltr with a math base, can that root in fact be math?"
//!      -> the ROOT is algebra, in `mltr.rs` as `Ty`. This file is not the
//!         root; it is what grows on it.
//!   2. "count, add, subtract, equals"
//!      -> VERBS. The first draft was a vocabulary of nouns (identity,
//!         field, manifold, kernel) and measuring it found 119 attested.
//!         That was the wrong shape for a machine language.
//!   3. "nouns are lists, ie lookup"
//!      -> and a noun is not a concept, it is a LIST: something a lookup
//!         takes. So the noun half is OBJECTS.
//!   4. "add prepositions about above after against among amid around"
//!      -> PREPOSITIONS. A register with no way to place a term relative
//!         to another cannot say "the core sits outside the braid".
//!   5. "comparison comparators"
//!      -> COMPARATORS: equals, less, contains, between, none.
//!   6. "verbs nouns prepositions comparators objects etc"
//!      -> and that is the grouping AXIS. Four kinds, 27 subgroups.
//!
//! WHY KIND IS THE PRIMARY AXIS AND NOT SCHOOL OF THOUGHT. The first cut
//! used 30 flat groups -- one per subject: VERB:SET, NOUN:COLLECTION,
//! CMP:MEMBERSHIP, REL:PREP_POSITION. That was a taxonomy of ORIGINS and
//! it was wrong for a register, because a lookup searching for a concept
//! had to know which school it belonged to before it could look. Now the
//! kind answers "what IS this term" and the subgroup answers "what does it
//! do inside that kind", so one concept lives in exactly one place.
//!
//! WHERE THE FREQUENCIES COME FROM. `vault/chat-transcripts/distilled/`,
//! all three parts concatenated (549 load-bearing + 292 correction + 141
//! speculative), lowercased, whole-word matched, no stoplist, no
//! handpicking. Roughly 341k characters.
//!
//! THE COMPILABLE FRACTION. 335 of 500 are attested: **67.0%**. The other
//! 165 are terms the register requires and his corpus does not contain.
//! This is paper 25's P5/T5 -- "the fraction of input that compiles to a
//! bounded form is an architectural constant" -- computed here for the
//! first time on anything real. `compilable_fraction()` recomputes it from
//! the table on every call so it cannot drift from the data.
//!
//! THE ORDER IS NOT BY IMPORTANCE. It is by the record. `to` (468) and
//! `identity` (276) are first because those are how he writes. A test
//! pins this: if the table were ranked by concept, `to` would not lead.
//!
//! `equals` scores ZERO. He writes `same` (14), `differs` (2),
//! `equivalent` (3). The word he chose to name the register is not in his
//! usage, so it is recorded as attested 0 rather than quietly renamed.

/// The four kinds of term. This is the primary axis.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Kind {
    /// Acts on a term. `add`, `count`, `gate`, `subtract`.
    Verb,
    /// Is a list a lookup takes. `stack`, `key`, `envelope`, `state`.
    Object,
    /// Places one term against another. `above`, `between`, `through`.
    Preposition,
    /// Decides. `same`, `less`, `contains`, `between`, `none`.
    Comparator,
}

/// What a term does inside its kind. Second axis.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Group {
    // -- Verbs --
    /// add, count, subtract, mean, remainder
    Arithmetic,
    /// map, project, embed, normalize, invert
    Transform,
    /// equals, less, contains, and, or, not
    Decide,
    /// loop, gate, allow, refuse, query
    Govern,
    /// read, write, push, append, store
    State,
    /// cast, widen, narrow, assign
    Type,
    /// create, build, define, enumerate
    Build,
    // -- Objects --
    /// stack, list, queue, dict, tree
    List,
    /// key, index, id, name, token, address
    Key,
    /// value, element, entry, payload, sample
    Value,
    /// state, memory, context, log, ledger, buffer
    StateObj,
    /// order, range, bound, window, tier, level
    Sort,
    /// type, schema, contract, invariant, grammar, lexicon
    Structure,
    /// class, field, module, kernel, basis, spectrum, matrix
    Mathematical,
    // -- Prepositions --
    /// above, between, through, within, across
    Position,
    /// but, because, unless, although
    Logic,
    /// more, most, less, exactly, almost
    Degree,
    /// first, next, previous, forward, last
    Order,
    /// as, per, following, given
    Reference,
    /// now, when, then, after, already, since
    Time,
    // -- Comparators --
    /// same, differs, equivalent, distinct
    Identity,
    /// less, greater, above, below, exceeds
    OrderCmp,
    /// contains, has, includes, member, subset_of
    Membership,
    /// between, inside, outside, beyond
    RangeCmp,
    /// none, null, empty, missing, absent
    Nil,
    /// pattern, exact, similar, matches, prefix
    Match,
    /// itself, same_as, identical_to
    Reflexive,
}

/// One term of the register.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Term {
    pub kind: Kind,
    pub group: Group,
    pub name: &'static str,
    /// Measured count in Bobby's corpus, or 0 for a term the register
    /// requires and he has never used. The zeros are the residue and they
    /// are data, not omissions.
    pub attested: u32,
}

/// The register. Bounded, and the bound is in the type.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Register {
    terms: &'static [Term],
}

impl Register {
    /// The whole register.
    pub fn all() -> Register {
        Register { terms: &TERMS }
    }

    pub fn terms(&self) -> &'static [Term] {
        self.terms
    }
    pub fn len(&self) -> usize {
        self.terms.len()
    }
    pub fn is_empty(&self) -> bool {
        self.terms.is_empty()
    }

    /// Look up by name. One concept, one place.
    pub fn find(&self, name: &str) -> Option<&'static Term> {
        self.terms.iter().find(|t| t.name == name)
    }

    pub fn of_kind(&self, k: Kind) -> impl Iterator<Item = &'static Term> {
        self.terms.iter().filter(move |t| t.kind == k)
    }

    pub fn of_group(&self, g: Group) -> impl Iterator<Item = &'static Term> {
        self.terms.iter().filter(move |t| t.group == g)
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
        if n <= 0.0 {
            return 0.0;
        }
        self.terms.iter().filter(|t| t.attested > 0).count() as f64 / n
    }

    /// The four he named on the first correction, measured.
    /// Falsifiable: if these do not move when the corpus grows, the
    /// ranking is measuring nothing.
    pub fn bobbys_four(&self) -> [Option<&'static Term>; 4] {
        [
            self.find("count"),
            self.find("add"),
            self.find("subtract"),
            self.find("equals"),
        ]
    }

    /// Every kind must be non-empty, or the grouping has drifted.
    pub fn kinds_present(&self) -> usize {
        [Kind::Verb, Kind::Object, Kind::Preposition, Kind::Comparator]
            .iter()
            .filter(|k| self.of_kind(**k).count() > 0)
            .count()
    }
}

/// The register as a static table, so the bound is checked by the
/// compiler. `500` is in the type: adding a term without changing the
/// bound is a compile error, which is the only kind of bound that holds.

static TERMS: [Term; 500] = [
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "to", attested: 468 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "for", attested: 413 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "in", attested: 355 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "of", attested: 319 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "if", attested: 284 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "identity", attested: 276 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "and", attested: 271 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "with", attested: 230 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "state", attested: 190 },
    // ---- Verbs/Type ----
    Term { kind: Kind::Verb, group: Group::Type, name: "from", attested: 188 },
    Term { kind: Kind::Verb, group: Group::Type, name: "as", attested: 167 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "not", attested: 158 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "return", attested: 156 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "class", attested: 134 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "on", attested: 130 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "field", attested: 118 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "or", attested: 108 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "module", attested: 96 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "test", attested: 77 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "but", attested: 74 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "by", attested: 73 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "update", attested: 69 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "check", attested: 66 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "memory", attested: 62 },
    Term { kind: Kind::Object, group: Group::StateObj, name: "context", attested: 59 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "name", attested: 58 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "loop", attested: 54 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "create", attested: 54 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "vector", attested: 53 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "first", attested: 52 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "get", attested: 50 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "real", attested: 45 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "dict", attested: 44 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "now", attested: 44 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "all", attested: 42 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "add", attested: 41 },
    // ---- Verbs/Type ----
    Term { kind: Kind::Verb, group: Group::Type, name: "into", attested: 41 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "prime", attested: 40 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "when", attested: 40 },
    // ---- Comparators/Match ----
    Term { kind: Kind::Comparator, group: Group::Match, name: "pattern", attested: 39 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "new", attested: 38 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "key", attested: 38 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "domain", attested: 38 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "has", attested: 36 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "build", attested: 36 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "between", attested: 35 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "graph", attested: 34 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "value", attested: 34 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "via", attested: 34 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "append", attested: 31 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "across", attested: 31 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "any", attested: 30 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "generate", attested: 29 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "boundary", attested: 29 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "type", attested: 29 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "like", attested: 29 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "map", attested: 28 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "apply", attested: 28 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "kernel", attested: 28 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "matrix", attested: 28 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "next", attested: 28 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "push", attested: 27 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "range", attested: 27 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "over", attested: 27 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "none", attested: 26 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "list", attested: 26 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "through", attested: 26 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "more", attested: 26 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "project", attested: 25 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "log", attested: 25 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "before", attested: 25 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "mean", attested: 24 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "stack", attested: 24 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "id", attested: 23 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "operator", attested: 23 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "cross", attested: 22 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "position", attested: 22 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "function", attested: 21 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "history", attested: 21 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "without", attested: 21 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "most", attested: 21 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "load", attested: 20 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "observation", attested: 20 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "session", attested: 20 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "set", attested: 20 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "about", attested: 20 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "sum", attested: 19 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "start", attested: 19 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "entry", attested: 19 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "invariant", attested: 19 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "find", attested: 18 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "query", attested: 18 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "scale", attested: 18 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "forward", attested: 18 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "mode", attested: 17 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "packet", attested: 17 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "under", attested: 17 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "within", attested: 17 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "then", attested: 17 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "store", attested: 16 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "sample", attested: 16 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "level", attested: 16 },
    // ---- Comparators/Match ----
    Term { kind: Kind::Comparator, group: Group::Match, name: "similar", attested: 16 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "gate", attested: 15 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "token", attested: 15 },
    // ---- Comparators/Reflexive ----
    Term { kind: Kind::Comparator, group: Group::Reflexive, name: "itself", attested: 15 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "same", attested: 14 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "pass", attested: 14 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "primary", attested: 14 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "item", attested: 14 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "per", attested: 14 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "because", attested: 14 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "average", attested: 13 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "exists", attested: 13 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "verify", attested: 13 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "skip", attested: 13 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "path", attested: 13 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "window", attested: 13 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "observe", attested: 12 },
    Term { kind: Kind::Verb, group: Group::State, name: "replace", attested: 12 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "power", attested: 11 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "scan", attested: 11 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "symbol", attested: 11 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "too", attested: 11 },
    Term { kind: Kind::Preposition, group: Group::Degree, name: "exactly", attested: 11 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "after", attested: 11 },
    Term { kind: Kind::Preposition, group: Group::Time, name: "already", attested: 11 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "previous", attested: 11 },
    // ---- Comparators/Nil ----
    Term { kind: Kind::Comparator, group: Group::Nil, name: "missing", attested: 11 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "order", attested: 10 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "count", attested: 10 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "max", attested: 10 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "call", attested: 10 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "record", attested: 10 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "category", attested: 10 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "capacity", attested: 10 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "cache", attested: 10 },
    Term { kind: Kind::Object, group: Group::StateObj, name: "ledger", attested: 10 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "array", attested: 10 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "than", attested: 10 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "write", attested: 9 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "define", attested: 9 },
    Term { kind: Kind::Verb, group: Group::Build, name: "make", attested: 9 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "sequence", attested: 9 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "complex", attested: 9 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "tuple", attested: 9 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "during", attested: 9 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "up", attested: 9 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "difference", attested: 8 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "embed", attested: 8 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "both", attested: 8 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "allow", attested: 8 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "read", attested: 8 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "normalize", attested: 8 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "setup", attested: 8 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "ring", attested: 8 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "series", attested: 8 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "schema", attested: 8 },
    Term { kind: Kind::Object, group: Group::Structure, name: "definition", attested: 8 },
    Term { kind: Kind::Object, group: Group::Structure, name: "contract", attested: 8 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "buffer", attested: 8 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "dictionary", attested: 8 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "beyond", attested: 8 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "off", attested: 8 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "out", attested: 8 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "so", attested: 8 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "trace", attested: 7 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "break", attested: 7 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "abs", attested: 7 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "snapshot", attested: 7 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "while", attested: 7 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "still", attested: 7 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "sort", attested: 6 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "root", attested: 6 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "enumerate", attested: 6 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "min", attested: 6 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "dot", attested: 6 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "remove", attested: 6 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "collection", attested: 6 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "past", attested: 6 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "whether", attested: 6 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "once", attested: 6 },
    // ---- Comparators/Match ----
    Term { kind: Kind::Comparator, group: Group::Match, name: "exact", attested: 6 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "compare", attested: 5 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "contains", attested: 5 },
    // ---- Verbs/Type ----
    Term { kind: Kind::Verb, group: Group::Type, name: "assign", attested: 5 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "recurse", attested: 5 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "select", attested: 5 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "shift", attested: 5 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "tree", attested: 5 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "label", attested: 5 },
    Term { kind: Kind::Object, group: Group::Key, name: "reference", attested: 5 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "variance", attested: 5 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "proof", attested: 5 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "against", attested: 5 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "near", attested: 5 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "backward", attested: 5 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "less", attested: 4 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "rank", attested: 4 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "product", attested: 4 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "basis", attested: 4 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "pop", attested: 4 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "split", attested: 4 },
    Term { kind: Kind::Verb, group: Group::Build, name: "init", attested: 4 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "symbolic", attested: 4 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "payload", attested: 4 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "tier", attested: 4 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "lattice", attested: 4 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "transformation", attested: 4 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "spectrum", attested: 4 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "vocabulary", attested: 4 },
    Term { kind: Kind::Object, group: Group::Structure, name: "lexicon", attested: 4 },
    Term { kind: Kind::Object, group: Group::Structure, name: "axiom", attested: 4 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "region", attested: 4 },
    Term { kind: Kind::Object, group: Group::StateObj, name: "baseline", attested: 4 },
    Term { kind: Kind::Object, group: Group::StateObj, name: "register", attested: 4 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "bound", attested: 4 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "inside", attested: 4 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "since", attested: 4 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "last", attested: 4 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "greater", attested: 3 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "extend", attested: 3 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "reduce", attested: 3 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "holds", attested: 3 },
    // ---- Verbs/Type ----
    Term { kind: Kind::Verb, group: Group::Type, name: "construct", attested: 3 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "index", attested: 3 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "nor", attested: 3 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "le", attested: 3 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "stop", attested: 3 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "pool", attested: 3 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "address", attested: 3 },
    Term { kind: Kind::Object, group: Group::Key, name: "handle", attested: 3 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "factor", attested: 3 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "grammar", attested: 3 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "prior", attested: 3 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "along", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "despite", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "onto", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "outside", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "toward", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "until", attested: 3 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "yet", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "unless", attested: 3 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "least", attested: 3 },
    // ---- Prepositions/Reference ----
    Term { kind: Kind::Preposition, group: Group::Reference, name: "following", attested: 3 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "provided", attested: 3 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "second", attested: 3 },
    // ---- Comparators/Identity ----
    Term { kind: Kind::Comparator, group: Group::Identity, name: "equivalent", attested: 3 },
    // ---- Comparators/Nil ----
    Term { kind: Kind::Comparator, group: Group::Nil, name: "nothing", attested: 3 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "resolve", attested: 3 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "commit", attested: 3 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "distinct", attested: 2 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "subtract", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "multiply", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "absolute", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "truncate", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "clamp", attested: 2 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "fold", attested: 2 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "iterate", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "exit", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "yield", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "refuse", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "match", attested: 2 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "isomorphism", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "composition", attested: 2 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "differs", attested: 2 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "exp", attested: 2 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "inc", attested: 2 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "includes", attested: 2 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "fail", attested: 2 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "insert", attested: 2 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "lookup", attested: 2 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "literal", attested: 2 },
    Term { kind: Kind::Object, group: Group::Value, name: "measurement", attested: 2 },
    Term { kind: Kind::Object, group: Group::Value, name: "scalar", attested: 2 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "limit", attested: 2 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "declaration", attested: 2 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "above", attested: 2 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "although", attested: 2 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "middle", attested: 2 },
    // ---- Comparators/Membership ----
    Term { kind: Kind::Comparator, group: Group::Membership, name: "member", attested: 2 },
    // ---- Comparators/Nil ----
    Term { kind: Kind::Comparator, group: Group::Nil, name: "null", attested: 2 },
    Term { kind: Kind::Comparator, group: Group::Nil, name: "empty", attested: 2 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "quotient", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "cube", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "floor", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "ceiling", attested: 1 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "cover", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "image", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "compose", attested: 1 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "implies", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "either", attested: 1 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "branch", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "continue", attested: 1 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "accumulate", attested: 1 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "prove", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "inspect", attested: 1 },
    // ---- Verbs/Build ----
    Term { kind: Kind::Verb, group: Group::Build, name: "join", attested: 1 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "mod", attested: 1 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "eigen", attested: 1 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "iff", attested: 1 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "neq", attested: 1 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "sign", attested: 1 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "bundle", attested: 1 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "compound", attested: 1 },
    Term { kind: Kind::Object, group: Group::Key, name: "uuid", attested: 1 },
    Term { kind: Kind::Object, group: Group::Key, name: "column", attested: 1 },
    Term { kind: Kind::Object, group: Group::Key, name: "identifier", attested: 1 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "element", attested: 1 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "ordering", attested: 1 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "integer", attested: 1 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "functor", attested: 1 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "morphism", attested: 1 },
    // ---- Objects/Structure ----
    Term { kind: Kind::Object, group: Group::Structure, name: "alphabet", attested: 1 },
    Term { kind: Kind::Object, group: Group::Structure, name: "theorem", attested: 1 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "around", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "behind", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "below", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "down", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "except", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "plus", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "throughout", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "upon", attested: 1 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "therefore", attested: 1 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "almost", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Degree, name: "nearly", attested: 1 },
    // ---- Prepositions/Reference ----
    Term { kind: Kind::Preposition, group: Group::Reference, name: "given", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "assuming", attested: 1 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "seeing", attested: 1 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "third", attested: 1 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "approximately", attested: 1 },
    // ---- Comparators/Order ----
    Term { kind: Kind::Comparator, group: Group::OrderCmp, name: "exceeds", attested: 1 },
    // ---- Comparators/Nil ----
    Term { kind: Kind::Comparator, group: Group::Nil, name: "absent", attested: 1 },
    // ---- Comparators/Match ----
    Term { kind: Kind::Comparator, group: Group::Match, name: "matches", attested: 1 },
    Term { kind: Kind::Comparator, group: Group::Match, name: "prefix", attested: 1 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "divide", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "decrement", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "increment", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "negate", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "round", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "saturate", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "remainder", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "median", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "logarithm", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "square", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "exponent", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "reciprocal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "gcd", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "lcm", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "tally", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "interpolate", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "normalise", attested: 0 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "equals", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "not_equals", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "less_or_equal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "greater_or_equal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "equal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "unequal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "gt", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "lt", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "ge", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "compare_order", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "rank_by", attested: 0 },
    // ---- Verbs/Transform ----
    Term { kind: Kind::Verb, group: Group::Transform, name: "union", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "intersect", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "subset", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "complement", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "restrict", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "preimage", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "belongs", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "disjoint", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "partition", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "equivalence", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "symmetric_difference", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "coset", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "superset", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "is_member", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "not_member", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "invert", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "transpose", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "mul", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "scalar_mul", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "inner_product", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "outer", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "determinant", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "diagonal", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "group", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "homomorphism", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "span", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "zero_map", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "identity_map", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "negation", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "division", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "distributive", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "commutative", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Transform, name: "associative", attested: 0 },
    // ---- Verbs/Decide ----
    Term { kind: Kind::Verb, group: Group::Decide, name: "xor", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "nand", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "neither", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "only_if", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Decide, name: "for_all", attested: 0 },
    // ---- Verbs/Type ----
    Term { kind: Kind::Verb, group: Group::Type, name: "cast", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "widen", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "narrow", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "coerce", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "declare", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "substitute", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "unify", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "discriminate", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "instantiate", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Type, name: "bind", attested: 0 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "halt", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "abort", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "guard", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "find_all", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "describe", attested: 0 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "delete", attested: 0 },
    Term { kind: Kind::Verb, group: Group::State, name: "emit", attested: 0 },
    Term { kind: Kind::Verb, group: Group::State, name: "seek", attested: 0 },
    Term { kind: Kind::Verb, group: Group::State, name: "swap", attested: 0 },
    Term { kind: Kind::Verb, group: Group::State, name: "dequeue", attested: 0 },
    // ---- Objects/List ----
    Term { kind: Kind::Object, group: Group::List, name: "multiset", attested: 0 },
    Term { kind: Kind::Object, group: Group::List, name: "permutation", attested: 0 },
    Term { kind: Kind::Object, group: Group::List, name: "slab", attested: 0 },
    Term { kind: Kind::Object, group: Group::List, name: "arena", attested: 0 },
    Term { kind: Kind::Object, group: Group::List, name: "deque", attested: 0 },
    Term { kind: Kind::Object, group: Group::List, name: "iterator", attested: 0 },
    // ---- Objects/Key ----
    Term { kind: Kind::Object, group: Group::Key, name: "surrogate", attested: 0 },
    Term { kind: Kind::Object, group: Group::Key, name: "ordinal", attested: 0 },
    Term { kind: Kind::Object, group: Group::Key, name: "cardinal", attested: 0 },
    Term { kind: Kind::Object, group: Group::Key, name: "pointer", attested: 0 },
    // ---- Objects/Value ----
    Term { kind: Kind::Object, group: Group::Value, name: "atom", attested: 0 },
    Term { kind: Kind::Object, group: Group::Value, name: "constant", attested: 0 },
    Term { kind: Kind::Object, group: Group::Value, name: "datum", attested: 0 },
    // ---- Objects/Sort ----
    Term { kind: Kind::Object, group: Group::Sort, name: "percentile", attested: 0 },
    Term { kind: Kind::Object, group: Group::Sort, name: "quartile", attested: 0 },
    Term { kind: Kind::Object, group: Group::Sort, name: "cutoff", attested: 0 },
    Term { kind: Kind::Object, group: Group::Sort, name: "interval", attested: 0 },
    Term { kind: Kind::Object, group: Group::Sort, name: "bucket", attested: 0 },
    Term { kind: Kind::Object, group: Group::Sort, name: "stratum", attested: 0 },
    // ---- Objects/Mathematical ----
    Term { kind: Kind::Object, group: Group::Mathematical, name: "intersection", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "rational", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "irrational", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "divisor", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "denominator", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "numerator", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "parity", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "residue", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "modulus", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "eigenvalue", attested: 0 },
    Term { kind: Kind::Object, group: Group::Mathematical, name: "eigenvector", attested: 0 },
    // ---- Objects/State ----
    Term { kind: Kind::Object, group: Group::StateObj, name: "frame", attested: 0 },
    Term { kind: Kind::Object, group: Group::StateObj, name: "journal", attested: 0 },
    // ---- Prepositions/Position ----
    Term { kind: Kind::Preposition, group: Group::Position, name: "amid", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "among", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "alongside", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "beneath", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "besides", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "underneath", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Position, name: "unlike", attested: 0 },
    // ---- Prepositions/Logic ----
    Term { kind: Kind::Preposition, group: Group::Logic, name: "hence", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "thus", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "whenever", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "whereas", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "consequently", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "furthermore", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Logic, name: "moreover", attested: 0 },
    // ---- Prepositions/Degree ----
    Term { kind: Kind::Preposition, group: Group::Degree, name: "rather", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Degree, name: "quite", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Degree, name: "sufficiently", attested: 0 },
    // ---- Prepositions/Reference ----
    Term { kind: Kind::Preposition, group: Group::Reference, name: "regarding", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "concerning", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "respecting", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Reference, name: "irrespective", attested: 0 },
    // ---- Prepositions/Time ----
    Term { kind: Kind::Preposition, group: Group::Time, name: "meanwhile", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Time, name: "henceforth", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Time, name: "thence", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Time, name: "afterwards", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Time, name: "beforehand", attested: 0 },
    // ---- Prepositions/Order ----
    Term { kind: Kind::Preposition, group: Group::Order, name: "latter", attested: 0 },
    Term { kind: Kind::Preposition, group: Group::Order, name: "centre", attested: 0 },
    // ---- Comparators/Identity ----
    Term { kind: Kind::Comparator, group: Group::Identity, name: "identical", attested: 0 },
    // ---- Comparators/Order ----
    Term { kind: Kind::Comparator, group: Group::OrderCmp, name: "below_or_equal", attested: 0 },
    // ---- Comparators/Membership ----
    Term { kind: Kind::Comparator, group: Group::Membership, name: "subset_of", attested: 0 },
    Term { kind: Kind::Comparator, group: Group::Membership, name: "superset_of", attested: 0 },
    Term { kind: Kind::Comparator, group: Group::Membership, name: "not_in", attested: 0 },
    // ---- Comparators/Range ----
    Term { kind: Kind::Comparator, group: Group::RangeCmp, name: "within_bound", attested: 0 },
    Term { kind: Kind::Comparator, group: Group::RangeCmp, name: "out_of_bound", attested: 0 },
    // ---- Comparators/Nil ----
    Term { kind: Kind::Comparator, group: Group::Nil, name: "void", attested: 0 },
    // ---- Comparators/Match ----
    Term { kind: Kind::Comparator, group: Group::Match, name: "suffix", attested: 0 },
    // ---- Comparators/Reflexive ----
    Term { kind: Kind::Comparator, group: Group::Reflexive, name: "same_as", attested: 0 },
    Term { kind: Kind::Comparator, group: Group::Reflexive, name: "identical_to", attested: 0 },
    Term { kind: Kind::Comparator, group: Group::Reflexive, name: "self_equal", attested: 0 },
    // ---- Verbs/Arithmetic ----
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "modulo", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "floored", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "ceiled", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Arithmetic, name: "reciprocal_unit", attested: 0 },
    // ---- Verbs/Govern ----
    Term { kind: Kind::Verb, group: Group::Govern, name: "dispatch", attested: 0 },
    Term { kind: Kind::Verb, group: Group::Govern, name: "emit_query", attested: 0 },
    // ---- Verbs/State ----
    Term { kind: Kind::Verb, group: Group::State, name: "write_back", attested: 0 },
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
        for k in [Kind::Verb, Kind::Object, Kind::Preposition, Kind::Comparator] {
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
    fn the_four_kinds_bobby_named_are_all_present() {
        // "verbs nouns prepositions comparators objects etc" -- the grouping
        // axis. If a kind empties out, the axis has drifted.
        assert_eq!(Register::all().kinds_present(), 4);
        for k in [Kind::Verb, Kind::Object, Kind::Preposition, Kind::Comparator] {
            assert!(Register::all().of_kind(k).count() > 0, "{:?} is empty", k);
        }
    }

    #[test]
    fn every_kind_has_several_groups_and_several_every_group_has_terms() {
        // 4 kinds, 27 subgroups. Both directions are checked: a kind with
        // one group is not grouped, and a group with no terms is a label
        // somebody invented.
        use Group::*;
        let kinds: &[(Kind, &[Group])] = &[
            (Kind::Verb, &[Arithmetic, Transform, Decide, Govern, State, Type, Build]),
            (Kind::Object, &[List, Key, Value, StateObj, Sort, Structure, Mathematical]),
            (Kind::Preposition, &[Position, Logic, Degree, Order, Reference, Time]),
            (Kind::Comparator, &[Identity, OrderCmp, Membership, RangeCmp, Nil, Match, Reflexive]),
        ];
        let r = Register::all();
        let mut group_total = 0;
        for (k, groups) in kinds {
            let mut kind_total = 0;
            for g in *groups {
                let n = r.of_group(*g).count();
                assert!(n > 0, "{:?} has no terms", g);
                // every term in a group must carry that group's kind
                for t in r.of_group(*g) {
                    assert_eq!(t.kind, *k, "{} is in {:?} but is a {:?}", t.name, g, t.kind);
                }
                kind_total += n;
                group_total += 1;
            }
            assert!(kind_total > 0);
        }
        assert_eq!(group_total, 27);
        // and the table itself contains no term outside those 27 groups
        assert_eq!(r.len(), 500);
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
    fn objects_are_the_lists_a_lookup_takes() {
        // Bobby: "nouns are lists, ie lookup". So every object must be a
        // container, a key, a value, a sort, a structure, state, or a
        // mathematical object -- never a bare concept.
        let r = Register::all();
        let objects: Vec<&str> =
            r.of_kind(Kind::Object).map(|t| t.name).collect();
        for required in ["stack", "key", "list", "dict", "state"] {
            assert!(objects.contains(&required), "object {} missing", required);
        }
        assert!(r.of_group(Group::Key).count() > 0);
        assert!(r.of_group(Group::List).count() > 0);
        assert!(r.of_group(Group::Value).count() > 0);
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
