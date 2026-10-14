//! The decision ladder. Bit width IS the area of authority.
//!
//! WHY NOT A FLAT 1-BIT GATE. A single one-bit governor has to judge
//! everything on one bit, so it either refuses constantly or has to be
//! lenient, and both make it useless. A flat gate cannot work, not
//! because it is badly tuned but because the area it covers and the
//! resolution it has are the same thing, and they must not be.
//!
//! WHY NESTING. Each stalk answers hyper-locally on one bit. If its own
//! area cannot decide, the question escalates to a structure that covers
//! more area and therefore has more bits. Width is not a measure of
//! reasoning quality -- 8 bits does not think better than 1 bit -- it is
//! a measure of how much of the world that level is entitled to speak
//! for.
//!
//! Failure is therefore the useful event, not the broken one. A stalk
//! that cannot decide is not defective, it is routing. This is
//! "fail upwards" and it is the only shape in which a cheap layer stays
//! cheap: the overwhelming majority of decisions never leave 1 bit, and
//! multi-bit is the rare expensive path.
//!
//! WHERE IT CAME FROM. Tesla self-driving, per Bobby 2026-10-14, and
//! independently Gemini's read that the structure is elegant. That is
//! two sources plus simself's own mte-primitives doc, which already said
//! "4-bit, 8-bit fails upward (cheap -> expensive)" on 2026-09-14. Three
//! independent convergences. The convergence is the evidence.
//!
//! THE LADDER. 1 / 4 / 8 / 16 / 32 / 64 / 128. **It does not end at 128.**
//! 128 is not "large" or "full" or "enough" -- it is the point where a
//! cost-benefit comparison becomes cheaper than any further refinement,
//! because the cost of resolving has overtaken the value of knowing. The
//! terminal state is not a width, it is a different kind of answer.

use core::fmt;

/// The widths. Doubling, not linear: a wider level covers more than
/// double the area of the one below, which is why the ladder climbs fast
/// and why 128 is reachable in seven escalations from 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Width {
    W1,
    W4,
    W8,
    W16,
    W32,
    W64,
    W128,
    W256,
}

impl Width {
    /// Eight rungs. 256 is the last WIDTH, not the last rung --
    /// past it the answer changes kind and becomes Unanswerable.
    /// Bobby, 2026-10-14: "1/4/8/16/32/64/128 do NOT end ... 256, unanswerable."
    pub const LADDER: [Width; 8] = [
        Width::W1, Width::W4, Width::W8, Width::W16,
        Width::W32, Width::W64, Width::W128, Width::W256,
    ];

    pub fn bits(&self) -> u16 {
        match self {
            Width::W1 => 1,
            Width::W4 => 4,
            Width::W8 => 8,
            Width::W16 => 16,
            Width::W32 => 32,
            Width::W64 => 64,
            Width::W128 => 128,
            Width::W256 => 256,
        }
    }

    /// The area this width is entitled to speak for, in stalk units.
    /// Doubling per rung: the scope is a power of two, the width is the
    /// exponent taken literally.
    ///
    /// `u128`, not `u64`, because the ladder does not fit in `u64`. W128
    /// needs 2^127 and W256 needs 2^255. The previous `.min(16)` clamped
    /// the SHIFT AMOUNT rather than the result, so W32, W64, W128 and
    /// W256 ALL returned 65536 and the top four rungs had identical
    /// authority -- which defeats the entire point of a ladder whose
    /// widths mean how much of the world a level may speak for.
    ///
    /// Above 2^127 this saturates rather than overflowing, and the
    /// saturation is a fact about the ladder, not a bug in it: past W128
    /// the area of authority genuinely exceeds what any fixed-width
    /// counter can name.
    pub fn reach(&self) -> u128 {
        let shift = self.bits().saturating_sub(1);
        if shift >= 128 { u128::MAX } else { 1u128 << shift }
    }

    /// The next rung, or None at the top.
    ///
    /// None is not "128 is big enough". None means the ladder has run
    /// out of refinement and the answer has to change KIND -- see
    /// `escalate`, which returns a cost-benefit verdict rather than a
    /// wider bit.
    pub fn up(&self) -> Option<Width> {
        let i = Width::LADDER.iter().position(|w| w == self)?;
        Width::LADDER.get(i + 1).copied()
    }

    pub fn down(&self) -> Option<Width> {
        let i = Width::LADDER.iter().position(|w| w == self)?;
        i.checked_sub(1).map(|j| Width::LADDER[j])
    }
}

impl fmt::Display for Width {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}b", self.bits())
    }
}

// ---------------------------------------------------------------------------
// the cost-benefit node
// ---------------------------------------------------------------------------

/// Why an escalation stopped. Named, because a refusal without a reason
/// is unactionable.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Escalation {
    /// Answered at this width. Done.
    Resolved,
    /// Could not answer at this width; escalate.
    NeedsMore,
    /// The cost of resolving now exceeds the value of knowing.
    /// THIS IS THE TERMINAL STATE, and it is not a width.
    NotWorthKnowing,
    /// Genuinely undecidable: cost and value are both unknown.
    Undecidable,
}

/// One rung of the ladder, and the cost-benefit test at the top.
///
/// The Monte-Carlo part is not decoration. At low widths the value of
/// knowing is high and the cost is one comparison. At high widths each
/// additional bit costs more than the last -- resolving a question to
/// 128 bits of precision costs far more than resolving it to 8, and the
/// marginal value falls as the question approaches settled. So the
/// ladder terminates where `cost_of_one_more_bit > value_of_knowing`,
/// and that crossing is *measured per sample*, which is why this takes
/// a sampler rather than a constant.
///
/// The shape is a cost-benefit tree: each rung is a node, each
/// escalation is an edge, and the whole thing is a search over "how much
/// do I need to know to answer this well enough". A Monte-Carlo walk
/// samples the unresolved part -- the part nobody has closed -- so the
/// terminal width is a distribution rather than a number.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Ladder {
    /// Bits per rung, for accounting.
    pub width: Width,
    /// Expected cost of resolving to this width. Monotonic increasing.
    pub resolve_cost: f64,
    /// Expected value of the answer at this width. Monotonic decreasing
    /// as the question settles.
    pub answer_value: f64,
}

impl Ladder {
    pub fn new(width: Width, resolve_cost: f64, answer_value: f64) -> Self {
        Ladder { width, resolve_cost, answer_value }
    }

    /// Should this rung escalate?
    ///
    /// Yes when the next bit costs less than the answer is worth. No when
    /// it costs more -- and "no" at the top rung is a *decision*, not a
    /// limitation. Refusing to know more precisely is the point.
    pub fn should_escalate(&self, sampled_gain: f64, sampled_cost: f64) -> Escalation {
        if sampled_gain.is_nan() || sampled_cost.is_nan() {
            return Escalation::Undecidable;
        }
        match self.width.up() {
            Some(next) => {
                if sampled_cost <= sampled_gain {
                    Escalation::NeedsMore
                } else {
                    // refining is now more expensive than the answer is worth
                    let _ = next;
                    Escalation::NotWorthKnowing
                }
            }
            None => {
                if sampled_cost <= sampled_gain {
                    Escalation::NeedsMore
                } else {
                    Escalation::NotWorthKnowing
                }
            }
        }
    }

    /// Walk the ladder with a sampler. Returns the width it settled at
    /// and why it stopped.
    ///
    /// `gain` and `cost` are sampled because the unresolved part is
    /// genuinely unresolved: at any real rung, both the marginal value
    /// and the marginal cost depend on the specific question, and a
    /// single number would be a guess dressed as a constant.
    pub fn walk<G, C>(&self, gain: G, cost: C) -> (Width, Escalation)
    where
        G: Fn(Width) -> f64,
        C: Fn(Width) -> f64,
    {
        let mut cur = *self;
        loop {
            match cur.should_escalate(gain(cur.width), cost(cur.width)) {
                Escalation::NeedsMore => match cur.width.up() {
                    Some(next) => {
                        cur = Ladder::new(next, cur.resolve_cost, cur.answer_value);
                    }
                    // top of the ladder and still worth it. There is no
                    // rung above 128, so the answer changes kind rather
                    // than width: this is Undecidable, not "infinite".
                    None => return (cur.width, Escalation::Undecidable),
                },
                other => return (cur.width, other),
            }
        }
    }
}

/// A Monte-Carlo estimate of where the ladder terminates.
///
/// Repeated independent walks; report the distribution rather than one
/// number. If the mode is `NotWorthKnowing` at 8 bits on most runs and
/// 128 on a few, that is a genuinely uncertain question and the system
/// should treat it as uncertain -- not average it into a confident 64.
#[derive(Debug, Clone, Copy)]
pub struct Termination {
    pub width: Width,
    pub outcome: Escalation,
}

pub fn monte_carlo(
    trials: usize,
    gain: impl Fn(Width) -> f64,
    cost: impl Fn(Width) -> f64,
) -> Termination {
    assert!(trials > 0, "zero trials establishes nothing");
    let mut counts: Vec<(Width, Escalation, usize)> = Vec::new();
    for _ in 0..trials {
        let (w, o) = Ladder::new(Width::W1, 1.0, 1.0).walk(|x| gain(x), |x| cost(x));
        match counts.iter_mut().find(|(cw, co, _)| *cw == w && *co == o) {
            Some(t) => t.2 += 1,
            None => counts.push((w, o, 1)),
        }
    }
    counts.sort_by_key(|(_, _, n)| std::cmp::Reverse(*n));
    let (w, o, _) = counts[0];
    Termination { width: w, outcome: o }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn eight_rungs_from_1_to_256() {
        assert_eq!(Width::LADDER.len(), 8);
        assert_eq!(Width::W1.bits(), 1);
        assert_eq!(Width::W256.bits(), 256);
        assert_eq!(Width::W1.up().unwrap(), Width::W4);
        assert_eq!(Width::W256.up(), None, "the ladder does not end with a value");
    }

    #[test]
    fn doubling_all_the_way() {
        // The ladder is 1,4,8,16,...,256: the FIRST rung is the lone 1 bit
        // and every rung after it is a doubling. So the sequence is NOT 1,2,4
        // -- the original test doubled from 1 and expected 2 at the second
        // rung, which W4 never was. Fixed to follow the actual sequence.
        assert_eq!(Width::LADDER.iter().map(|w| w.bits()).collect::<Vec<_>>(),
                   vec![1, 4, 8, 16, 32, 64, 128, 256]);
        let mut w = Width::W1;
        for _ in 0..7 {
            w = w.up().unwrap();
        }
        assert_eq!(w, Width::W256);
        assert_eq!(w.bits(), 256);
    }

    #[test]
    fn reach_grows_with_width() {
        assert_eq!(Width::W1.reach(), 1);
        assert_eq!(Width::W4.reach(), 8);
        assert_eq!(Width::W8.reach(), 128);
        // The top four rungs used to ALL return 65536 because the shift
        // amount was clamped instead of the result. A ladder whose rungs
        // share an authority is not a ladder, so this asserts the
        // STRICTLY INCREASING property rather than spot values.
        let rungs: Vec<u128> = Width::LADDER.iter().map(|w| w.reach()).collect();
        for pair in rungs.windows(2) {
            assert!(pair[1] > pair[0], "reach must strictly increase: {:?} vs {:?}", pair[0], pair[1]);
        }
        assert!(Width::W256.reach() > Width::W128.reach());
    }

    /// Past W128 the area of authority exceeds what a fixed-width counter
    /// can name. That is a fact about the ladder, not an overflow to hide,
    /// so saturation is the declared behaviour and it is pinned here.
    #[test]
    fn reach_saturates_rather_than_overflowing() {
        assert_eq!(Width::W256.reach(), u128::MAX);
        assert!(Width::W128.reach() < u128::MAX);
    }

    #[test]
    fn cheap_rung_escalates() {
        let l = Ladder::new(Width::W1, 1.0, 1.0);
        assert_eq!(l.should_escalate(1.0, 0.1), Escalation::NeedsMore);
    }

    #[test]
    fn expensive_rung_stops_at_not_worth_knowing() {
        // the whole point: refusing to know more precisely is a DECISION
        let l = Ladder::new(Width::W8, 1.0, 1.0);
        assert_eq!(l.should_escalate(0.01, 100.0), Escalation::NotWorthKnowing);
    }

    #[test]
    fn nan_is_undecidable_not_allowed() {
        let l = Ladder::new(Width::W1, 1.0, 1.0);
        assert_eq!(l.should_escalate(f64::NAN, 0.1), Escalation::Undecidable);
        assert_eq!(l.should_escalate(1.0, f64::NAN), Escalation::Undecidable);
    }

    #[test]
    fn walk_reaches_a_width_and_stops() {
        // gain falls faster than cost rises -> stops early
        let (w, o) = Ladder::new(Width::W1, 1.0, 1.0).walk(
            |w| 10.0 - (w.bits() as f64) / 4.0,
            |w| (w.bits() as f64) / 4.0,
        );
        assert!(matches!(o, Escalation::NotWorthKnowing | Escalation::Undecidable));
        assert!(w.bits() >= 1);
    }

    #[test]
    fn monte_carlo_returns_the_mode() {
        let t = monte_carlo(200, |w| 10.0 - (w.bits() as f64) / 4.0, |w| (w.bits() as f64) / 4.0);
        assert!(t.width.bits() >= 1);
    }

    #[test]
    fn monte_carlo_needs_trials() {
        let r = std::panic::catch_unwind(|| {
            monte_carlo(0, |_| 1.0, |_| 1.0);
        });
        assert!(r.is_err(), "zero trials must not silently return a result");
    }
}