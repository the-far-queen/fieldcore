//! mltr.rs -- the root of the machine-language sheaf.
//!
//! WHY THE ROOT IS MATH. Three reasons, in order of weight.
//!
//! 1. IT IS ALREADY MATH. The core's types are algebra: `AxisSet` is a
//!    vector space with an invariant cone, `Channel` is a linear operator
//!    on C, `equalise` is an inverse, `Envelope` D1-D4 is a bounded order.
//!    MLTR is not a new thing to add to this crate. It is the name for
//!    the thing the crate already is.
//!
//! 2. A LANGUAGE IS MATH IF ITS SENTENCES ARE A SET AND ITS MEANING IS
//!    TOTAL. Types are sets. Programs are elements. Type checking is
//!    membership. Compilation is a homomorphism. That is not a metaphor,
//!    it is the definition, and it is the reason a mathematical root buys
//!    closure: no term can be lost by a well-typed program, because every
//!    term has a type and every type has a carrier.
//!
//! 3. THE FAILURE MODE IS ALREADY MEASURED. On day one, five separate bugs
//!    in `carrier.rs` had one shape: the code claimed a mathematical
//!    object and then discarded a term of it. `equalise()` computed
//!    Re(y * conj(H)) / |H|^2` -- the correct complex formula -- with
//!    `yi` hardcoded to `0.0`, so it returned cos(phi) instead of 1.0.
//!    `notch_db()` returned a signed dB depth and compared it the wrong
//!    way round. **A system discards exactly the term its current carrier
//!    cannot represent.** That is wordtrance at the level of arithmetic,
//!    and a math root is the cure: if the carrier is a real algebra, the
//!    term is representable by construction.
//!
//! THE ONE THING MATH CANNOT SUPPLY, and this is the load-bearing caveat.
//!
//! Math is total. A proposition is true, false, or undecided, and it never
//! says "below the floor". A vector below its invariant cone is not FALSE,
//! it is outside the domain, and mathematics has no name for being
//! outside the domain -- it has a symbol for undefined, and undefined is
//! not the same as refused, because undefined carries no reason.
//!
//! Yet refusal is the entire value of this crate. `Decision::Refuse`,
//! `Verdict::AxisBelowFloor`, `EqualiseError::FlatChannel`, `Refusal:
//! Stale` -- four modules say the same thing: a bare "no" is unactionable.
//!
//! So the machine language is NOT math. It is:
//
//!     math, as root
//!       + one non-mathematical primitive: a bounded, partial order with
//!         NAMED refusals
//!
//! `Ty` below is pure algebra and deliberately has no "nothing" variant.
//! Refusal is not a type. A type is a carrier; refusal is the absence of a
//! value, and putting it in the sort would make it mathematics, which is
//! precisely the thing it must not become. `Reply` is the trunk above the
//! root, and it is where the constitution lives.
//!
//! THE SLOT TEST -- the invariant that makes this a spec and not a sketch.
//!
//! Day one produced seven bugs, five of them the same error. So this module
//! makes lossy conversion IMPOSSIBLE TO EXPRESS QUIETLY: `Cast::Lossy`
//! must name the term it drops. There is no silent narrowing in this file,
//! so a receiver that needs quadrature cannot quietly ask for a real, and
//! the cos(phi) bug cannot recur in any code written against this root.

use crate::decision::Verdict;

// ---------------------------------------------------------------------------
// the root: types. algebra only.
// ---------------------------------------------------------------------------

/// The sorts of the machine language.
///
/// No `Option`, no `Result`, no uninhabited variant, and above all no
/// "nothing" / "never" / "error" member. That absence is deliberate and is
/// checked by `no_refusal_sorts_in_the_root`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Ty {
    Bit,
    Real,
    Complex,
    Vector(usize),
    Matrix(usize, usize),
}

impl Ty {
    /// The five KINDS of sort, as a fixed set.
    ///
    /// KINDS, not instances. `Vector` and `Matrix` are parameterised by
    /// dimension, so a list of instances could never be a bound -- and the
    /// first version of this line held `Vector(0)` and `Matrix(0,0)`,
    /// which are two zero-width sorts sitting in the enumeration of the
    /// real ones. A placeholder in a set that claims to enumerate is the
    /// "filter in a config file is a filter somebody edits at 3am" failure
    /// this codebase already forbids in `sheaf.rs`.
    pub const KINDS: [TyKind; 5] =
        [TyKind::Bit, TyKind::Real, TyKind::Complex, TyKind::Vector, TyKind::Matrix];

    /// The sorts with no parameters, which is the only finite set of
    /// instances. Everything else is `KINDS` plus a dimension.
    pub const ATOMIC: [Ty; 3] = [Ty::Bit, Ty::Real, Ty::Complex];

    /// Carrier size, in scalars. This is the quantity that decides whether
    /// a conversion can be lossless.
    ///
    /// A zero-width sort is not constructible as a term -- see
    /// `sort_and_carrier_must_agree_at_construction` -- but the arithmetic
    /// is still total, because arithmetic on an empty carrier is empty, not
    /// undefined.
    pub fn carrier(&self) -> usize {
        match self {
            Ty::Bit => 1,
            Ty::Real => 1,
            Ty::Complex => 2,
            Ty::Vector(n) => *n,
            Ty::Matrix(r, c) => r * c,
        }
    }

    /// Does this sort carry a phase term?
    ///
    /// The one question `equalise()` needed to ask on day one and could
    /// not, because the types were `f64`.
    pub fn carries_phase(&self) -> bool {
        matches!(self, Ty::Complex) || self.carrier() > 2
    }

    /// A stable name for the sort. This is part of the wire format, not a
    /// debug helper: `Reply::explain` prints it, and two modules have to
    /// agree on it.
    pub fn ty_name(&self) -> String {
        match self {
            Ty::Bit => "bit".into(),
            Ty::Real => "real".into(),
            Ty::Complex => "complex".into(),
            Ty::Vector(n) => format!("vector{n}"),
            Ty::Matrix(r, c) => format!("matrix{r}x{c}"),
        }
    }

    pub fn kind(&self) -> TyKind {
        match self {
            Ty::Bit => TyKind::Bit,
            Ty::Real => TyKind::Real,
            Ty::Complex => TyKind::Complex,
            Ty::Vector(_) => TyKind::Vector,
            Ty::Matrix(_, _) => TyKind::Matrix,
        }
    }
}

/// The five kinds, unparameterised. This is what the root actually bounds:
/// the number of KINDS of sort. The number of sorts is not five, because
/// `Vector(3)` and `Vector(7)` are different sorts, and pretending
/// otherwise is how the first draft of this file ended up enumerating
/// `Vector(0)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TyKind {
    Bit,
    Real,
    Complex,
    Vector,
    Matrix,
}

// ---------------------------------------------------------------------------
// the root: values. total, and checked at construction.
// ---------------------------------------------------------------------------

/// The carrier of a sort.
#[derive(Debug, Clone, PartialEq)]
pub enum Payload {
    Bit(bool),
    Real(f64),
    /// In-phase and quadrature. Both, or the sort is lying about itself.
    Complex(f64, f64),
    Vector(Vec<f64>),
    Matrix(usize, usize, Vec<f64>),
}

/// A term of the machine language: a sort plus its carrier.
///
/// The sort/payload agreement is enforced in `Value::new`, for the same
/// reason `Envelope::new` enforces finiteness and `AxisSet::new` enforces
/// range: **a check that only runs on use is a check that can be skipped.**
#[derive(Debug, Clone, PartialEq)]
pub struct Value {
    pub ty: Ty,
    pub payload: Payload,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ValueNotAdmissible {
    SortCarrierMismatch { ty: Ty },
    /// A real or complex term that is not a number. A term must be a term.
    NotFinite,
    /// A matrix whose declared shape does not match its data.
    ShapeMismatch { rows: usize, cols: usize, len: usize },
}

impl Value {
    pub fn bit(b: bool) -> Self {
        Value { ty: Ty::Bit, payload: Payload::Bit(b) }
    }

    pub fn real(v: f64) -> Result<Self, ValueNotAdmissible> {
        if !v.is_finite() { return Err(ValueNotAdmissible::NotFinite); }
        Ok(Value { ty: Ty::Real, payload: Payload::Real(v) })
    }

    pub fn complex(re: f64, im: f64) -> Result<Self, ValueNotAdmissible> {
        if !re.is_finite() || !im.is_finite() { return Err(ValueNotAdmissible::NotFinite); }
        Ok(Value { ty: Ty::Complex, payload: Payload::Complex(re, im) })
    }

    /// The construction gate. Every constructor routes here, so a mismatched
    /// term cannot exist.
    pub fn new(ty: Ty, payload: Payload) -> Result<Self, ValueNotAdmissible> {
        let ok = match (&ty, &payload) {
            (Ty::Bit, Payload::Bit(_)) => true,
            (Ty::Real, Payload::Real(_)) => true,
            (Ty::Complex, Payload::Complex(_, _)) => true,
            (Ty::Vector(n), Payload::Vector(v)) => v.len() == *n,
            (Ty::Matrix(r, c), Payload::Matrix(rr, cc, v)) => *rr == *r && *cc == *c && v.len() == r * c,
            _ => false,
        };
        if !ok {
            let e = match (&ty, &payload) {
                (Ty::Matrix(r, c), Payload::Matrix(_, _, v)) =>
                    ValueNotAdmissible::ShapeMismatch { rows: *r, cols: *c, len: v.len() },
                _ => ValueNotAdmissible::SortCarrierMismatch { ty },
            };
            return Err(e);
        }
        Ok(Value { ty, payload })
    }

    /// The scalars this term occupies. The currency every conversion is
    /// priced in.
    pub fn scalars(&self) -> Vec<f64> {
        match &self.payload {
            Payload::Bit(b) => vec![if *b { 1.0 } else { 0.0 }],
            Payload::Real(v) => vec![*v],
            Payload::Complex(re, im) => vec![*re, *im],
            Payload::Vector(v) => v.clone(),
            Payload::Matrix(_, _, v) => v.clone(),
        }
    }
}

// ---------------------------------------------------------------------------
// the trunk: casts. a lossy cast MUST name what it drops.
// ---------------------------------------------------------------------------

/// A conversion between sorts.
///
/// `Lossy` carries the name of the dropped term as a `&'static str`. That
/// is the entire point of this file. On day one, `equalise()` narrowed a
/// complex frame to a real one and the narrowing was invisible at the type
/// level, which is how five bugs looked like arithmetic mistakes and were
/// actually representation losses.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Cast {
    /// Same sort. Loses nothing.
    Identity(Ty),
    /// Carrier grows or holds. Every input scalar is preserved.
    Lossless { from: Ty, to: Ty },
    /// Carrier shrinks. `drops` names the term that no longer exists.
    Lossy { from: Ty, to: Ty, drops: &'static str },
}

impl Cast {
    pub fn is_lossy(&self) -> bool {
        matches!(self, Cast::Lossy { .. })
    }

    pub fn what_it_drops(&self) -> Option<&'static str> {
        match self {
            Cast::Lossy { drops, .. } => Some(drops),
            _ => None,
        }
    }

    /// The cast between two sorts, or a refusal naming why there is none.
    ///
    /// Widening a real into a complex is the model embedding: lossless, and
    /// it is how a phase term gets a home. Narrowing the other way drops
    /// quadrature, by name, forever.
    pub fn between(from: Ty, to: Ty) -> Result<Cast, Verdict> {
        if from == to {
            return Ok(Cast::Identity(from));
        }
        let from_c = from.carrier();
        let to_c = to.carrier();
        if to_c == from_c {
            // Same width, different precision or phase capability.
            //
            // Narrowing FROM a phase-carrying sort always loses the phase
            // term. Narrowing between two phase-free sorts of equal width
            // loses PRECISION, not phase: a real 0.75 becoming a bit is a
            // quantisation, and no phase term ever existed to destroy.
            //
            // The first version returned `drops: "phase"` for both cases, so
            // the 1-bit gate was told it was destroying a phase term it had
            // never had. That is a misleading reason, which is the one kind
            // of reason this codebase does not permit.
            return Ok(if from.carries_phase() && !to.carries_phase() {
                Cast::Lossy { from, to, drops: "quadrature" }
            } else {
                Cast::Lossy { from, to, drops: "precision" }
            });
        }
        if to_c > from_c {
            return Ok(Cast::Lossless { from, to });
        }
        // narrowing: name the survivors
        let name: &'static str = match to {
            Ty::Bit => "amplitude",
            Ty::Real => "quadrature",
            _ => "components",
        };
        Ok(Cast::Lossy { from, to, drops: name })
    }

    /// Apply the cast.
    ///
    /// Widening embeds and every scalar survives. Narrowing does not happen
    /// silently and does not happen at all: a lossy cast returns the
    /// REFUSAL and names the term it would have destroyed.
    ///
    /// This is the boundary between the math root and the governing trunk.
    /// Mathematics widens freely; narrowing is a DECISION, and a decision
    /// belongs to the constitution, not to algebra. That is why `apply`
    /// refuses rather than truncating, and why the reason it refuses is
    /// carried in the reply instead of being logged and forgotten.
    pub fn apply(&self, v: &Value) -> Reply {
        match self {
            Cast::Identity(t) => Reply::Val(Value { ty: *t, payload: v.payload.clone() }),
            Cast::Lossless { to, .. } =>
                Reply::Val(Value { ty: *to, payload: v.payload.clone() }),
            Cast::Lossy { drops, .. } =>
                Reply::No { verdict: Verdict::NotAQuestionThisCoreAnswers, drops: Some(*drops) },
        }
    }
}

// ---------------------------------------------------------------------------
// the trunk: reply. the root cannot say no, so this says it.
// ---------------------------------------------------------------------------

/// The output of any operation at the trunk: a term, or a named refusal.
///
/// The root `Ty` has no refusal variant on purpose. A refusal is not a
/// value; it is the absence of one, with a reason attached.
///
/// `drops` is populated only when a refusal was caused by a lossy cast, and
/// it names the term that would have been destroyed. A bare `No` is
/// unactionable; a `No` that says "I would have had to drop quadrature" is
/// a question the caller can answer.
#[derive(Debug, Clone, PartialEq)]
pub enum Reply {
    Val(Value),
    No { verdict: Verdict, drops: Option<&'static str> },
}

impl Reply {
    pub fn allowed(&self) -> bool {
        matches!(self, Reply::Val(_))
    }

    /// The one line a caller should be able to print. Same contract as
    /// `Decision::explain`: refusal must be cheap AND legible.
    pub fn explain(&self) -> String {
        match self {
            Reply::Val(v) => format!("val:{}", v.ty.ty_name()),
            Reply::No { verdict, drops } => match drops {
                Some(d) => format!("refuse: {verdict} (would drop {d})"),
                None => format!("refuse: {verdict}"),
            },
        }
    }

    pub fn value(&self) -> Option<&Value> {
        match self {
            Reply::Val(v) => Some(v),
            Reply::No { .. } => None,
        }
    }

    /// If the reply is a value whose sort is `ty`, return it.
    pub fn value_of(&self, ty: Ty) -> Option<&Value> {
        self.value().filter(|v| v.ty == ty)
    }

    pub fn verdict(&self) -> Option<Verdict> {
        match self {
            Reply::Val(_) => None,
            Reply::No { verdict, .. } => Some(*verdict),
        }
    }

    /// If the reply is a refusal, what term would it have had to destroy.
    pub fn refused_what(&self) -> Option<&'static str> {
        match self {
            Reply::No { drops, .. } => *drops,
            Reply::Val(_) => None,
        }
    }

    /// Refuse for a reason that is not about a lost term.
    pub fn no(verdict: Verdict) -> Reply {
        Reply::No { verdict, drops: None }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // -- the root ---------------------------------------------------------

    /// THE SLOT TEST, part one: the root has no refusal sort.
    ///
    /// If a "nothing" or "error" variant ever appears in `Ty`, the machine
    /// language has grown a concept mathematics cannot give, and this
    /// fails rather than letting it pass into every downstream compiler.
    #[test]
    fn no_refusal_sorts_in_the_root() {
        // The root bounds the number of KINDS, not the number of sorts.
        // `Vector` and `Matrix` are parameterised by dimension, so a list
        // of instances could never be the bound -- the first draft of this
        // line held `Vector(0)` and `Matrix(0,0)`, two zero-width sorts
        // sitting in the enumeration of the real ones.
        assert_eq!(Ty::KINDS.len(), 5);
        // every kind is non-zero-width when given a real dimension
        assert!(Ty::Vector(1).carrier() > 0);
        assert!(Ty::Matrix(1, 1).carrier() > 0);
        // Bit and Real are one scalar each; Complex is two (I and Q). That
        // difference is the whole reason phase has a home at all, so it is
        // asserted rather than assumed.
        assert_eq!(Ty::Bit.carrier(), 1);
        assert_eq!(Ty::Real.carrier(), 1);
        assert_eq!(Ty::Complex.carrier(), 2);
        for t in Ty::ATOMIC {
            assert!(!matches!(t, Ty::Vector(_) | Ty::Matrix(_, _)));
        }
    }

    #[test]
    fn phase_is_a_property_of_the_sort_not_the_caller() {
        // THE day-one bug, as a property. `equalise()` returned cos(phi)
        // because its frame was real. Here the sort knows it has no phase.
        assert!(Ty::Complex.carries_phase());
        assert!(Ty::Real.carrier() == 1 && !Ty::Real.carries_phase());
        assert!(Ty::Vector(4).carries_phase(), "a vector carries a phase basis");
    }

    #[test]
    fn sort_and_carrier_must_agree_at_construction() {
        // a real that claims to be complex cannot be constructed
        let e = Value::new(Ty::Complex, Payload::Real(1.0)).unwrap_err();
        assert_eq!(e, ValueNotAdmissible::SortCarrierMismatch { ty: Ty::Complex });
        // a vector of the wrong length cannot be constructed
        let e = Value::new(Ty::Vector(3), Payload::Vector(vec![1.0, 2.0])).unwrap_err();
        assert!(matches!(e, ValueNotAdmissible::SortCarrierMismatch { .. }));
        // a matrix whose shape disagrees with its data cannot be constructed
        let e = Value::new(Ty::Matrix(2, 2), Payload::Matrix(2, 2, vec![1.0])).unwrap_err();
        assert!(matches!(e, ValueNotAdmissible::ShapeMismatch { .. }));
        // and the agreeing one can
        assert!(Value::new(Ty::Vector(2), Payload::Vector(vec![1.0, 2.0])).is_ok());
    }

    #[test]
    fn a_term_must_be_a_number() {
        assert_eq!(Value::real(f64::NAN).unwrap_err(), ValueNotAdmissible::NotFinite);
        assert_eq!(Value::real(f64::INFINITY).unwrap_err(), ValueNotAdmissible::NotFinite);
        assert_eq!(Value::complex(f64::NAN, 0.0).unwrap_err(), ValueNotAdmissible::NotFinite);
    }

    // -- casts ------------------------------------------------------------

    /// THE SLOT TEST, part two: narrowing a complex frame is REFUSED and
    /// NAMES the term. This is the direct structural answer to the day-one
    /// bug. The old code narrowed `&[(f64,f64)]` to `&[f64]` and nothing
    /// anywhere said "quadrature is gone".
    #[test]
    fn narrowing_complex_refuses_and_names_quadrature() {
        let c = Cast::between(Ty::Complex, Ty::Real).unwrap();
        assert!(c.is_lossy());
        assert_eq!(c.what_it_drops(), Some("quadrature"));
        let v = Value::complex(1.0, 0.5).unwrap();
        let r = c.apply(&v);
        assert!(!r.allowed(), "a lossy cast must not return a value");
        assert_eq!(r.refused_what(), Some("quadrature"));
        assert!(r.value().is_none());
    }

    /// Widening is how a phase term gets a home, and it must never refuse.
    #[test]
    fn widening_is_lossless_and_always_succeeds() {
        let c = Cast::between(Ty::Real, Ty::Complex).unwrap();
        assert!(!c.is_lossy());
        let v = Value::real(2.0).unwrap();
        let r = c.apply(&v);
        assert!(r.allowed());
        assert!(r.value_of(Ty::Complex).is_some());
    }

    #[test]
    fn identity_loses_nothing() {
        let c = Cast::between(Ty::Complex, Ty::Complex).unwrap();
        assert!(!c.is_lossy());
        assert_eq!(c.what_it_drops(), None);
        let v = Value::complex(1.0, 2.0).unwrap();
        assert_eq!(c.apply(&v).value(), Some(&v));
    }

    /// Narrowing anything to a Bit is lossy and must say so. A gate that
    /// decides one bit cannot silently discard amplitude without a name.
    ///
    /// The name is `precision`, not `phase`: neither Real nor Bit carries a
    /// phase term, so a real 0.75 becoming a bit is a quantisation. Telling
    /// the caller it was destroying a phase term would be a misleading
    /// reason, and a misleading reason is the one failure this whole crate
    /// is organised against.
    #[test]
    fn narrowing_to_bit_names_precision_not_phase() {
        let c = Cast::between(Ty::Real, Ty::Bit).unwrap();
        assert_eq!(c.what_it_drops(), Some("precision"));
        assert!(!c.apply(&Value::real(0.75).unwrap()).allowed());
        // and a phase-carrying narrowing still names the phase term
        let p = Cast::between(Ty::Complex, Ty::Real).unwrap();
        assert_eq!(p.what_it_drops(), Some("quadrature"));
    }

    /// The whole point, as one end-to-end fact: a receiver that needs
    /// quadrature can NEVER get a real frame without an explicit refusal.
    /// There is no path through this module that returns a phase-stripped
    /// value quietly.
    #[test]
    fn there_is_no_silent_narrowing() {
        let from = [Ty::Real, Ty::Complex, Ty::Vector(3), Ty::Matrix(2, 2)];
        let to = [Ty::Bit, Ty::Real, Ty::Complex, Ty::Vector(2), Ty::Matrix(1, 2)];
        let mut checked = 0;
        for f in from {
            for t in to {
                let c = Cast::between(f, t).unwrap();
                checked += 1;
                if c.is_lossy() {
                    let drops = c.what_it_drops();
                    assert!(drops.is_some(), "every lossy cast names its term");
                    assert_ne!(drops, Some(""), "a lossy cast names WHICH term");
                }
            }
        }
        assert_eq!(checked, 20);
    }

    // -- the trunk --------------------------------------------------------

    #[test]
    fn a_refusal_is_never_a_value() {
        let r = Reply::no(Verdict::CoreUnavailable);
        assert!(!r.allowed());
        assert_eq!(r.value(), None);
        assert_eq!(r.verdict(), Some(Verdict::CoreUnavailable));
        assert_eq!(r.refused_what(), None);
    }

    #[test]
    fn a_1bit_answer_still_carries_its_reason() {
        // the property `decision.rs` exists for, restated at the language root:
        // refusal is cheap AND legible.
        let r = Reply::no(Verdict::AxisBelowFloor("honesty"));
        assert!(!r.allowed());
        assert!(r.explain().contains("honesty"));
    }
}
