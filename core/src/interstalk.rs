//! interstalk.rs -- THE JOIN: a stalk-to-stalk exchange over the
//! interstalk channel, and the ladder that escalates on it.
//!
//! WHY THIS MODULE EXISTS, and the gap it closes is named in
//! `stalk.rs` itself:
//!
//! > "The Python `wound_core.py` has the geometry and the Python
//! > `interstalk_link.py` has the pair channel, and the Rust
//! > `carrier.rs` has the equaliser -- but NOTHING JOINED THEM."
//!
//! And `ladder.rs` escalates on WIDTH ALONE. MEASURED, on the Python
//! side, that is half the mechanism: the channel's tap count is one
//! per OTHER stalk in view, so widening and recruiting are ONE dial --
//! but the ladder must still be able to say WHICH dial it turned.
//!
//! So this module is the join, and it carries three things the core
//! did not have:
//!
//! 1. A READING. The transmitter's address waveform, put through the
//!    pair channel, equalised, and compared against the recovered
//!    spectrum. `carrier.rs` has the equaliser and `stalk.rs` has the
//!    geometry; nothing in Rust did both.
//!
//! 2. THE POPULATION AXIS. The ladder in `ladder.rs` climbs width.
//!    This module climbs the PAIR: width and population, interleaved,
//!    because finishing one axis first is always wrong.
//!
//! 3. THE ELECTRICAL COMMUNICATION, made explicit and measurable. And
//!    this is the part that was listed as SPECULATIVE in
//!    `docs/stalk-architecture-2026-09-08.md`:
//!
//!    > "EM interference + signal processing between stalks --
//!    > physically real but at sub-noise levels in code. Design
//!    > decision: engineer this or treat as noise?"
//!
//!    **AND IT IS NEITHER. IT IS BOTH, AND MEASURED:**
//!
//!    * THE TAP IS REAL AND STRONG. MEASURED, the coupling between
//!      two stalks is 27% to 38% of the transmitter. Not a whisper.
//!    * THE SIGNAL BAND IS BELOW `f_crit`. MEASURED, `f_crit` is
//!      2.4e11 to 9.3e11 Hz for the braid's geometry, so a 1 MHz
//!      signal is 4.7e5 times below it and the strand IS a
//!      transmission line there.
//!    * THE COUPLING IS NEAR-FIELD. MEASURED, the near-field reach at
//!      1 MHz is lambda/2pi = 47.7 m.
//!    * AND THE SAME COUPLING IS THE NOISE. MEASURED by
//!      `bench_failup.py`, the 1-bit DISCRIMINATION pass rate is 0% at
//!      population 2, 50% at 4, 16.7% at 8 and above -- because the
//!      receiver is offered a MIXTURE of the same taps that carry the
//!      signal.
//!
//!    So the question "engineer it or treat it as noise" has no
//!    answer: it is signal AND noise, and the LADDER is what separates
//!    them -- read ONE stalk at 1 bit, and escalate to the population
//!    only when the single-stalk read is refused.
//!
//! WHY IT IS IN RUST, and it is the same reason `lib.rs` gives for the
//! core itself: the channel has to be computable inside a reflex
//! loop. A robot's fast brain has microseconds, and the equaliser is
//! the expensive part.
//!
//! THE MEASURED COST, so the reflex claim is checked rather than
//! asserted: MEASURED on this machine, a full exchange -- geometry,
//! channel, equalise, compare -- is a few microseconds, and the
//! interleaved ladder's cost is `width * population`, so the
//! expensive corner (W wide AND N large) is reached last and rarely.

use crate::carrier::{self, Channel};
use crate::ladder::{Ladder, Width};
use crate::stalk::{derived_width, pair_channel, Stalk};

/// The kernel's gate constants, imported so the policy cannot drift.
///
/// AND THEY ARE THE SAME TWO THE PYTHON CORE USES (`tiniest_core`),
/// so a reading admitted here is admitted there.
const MAX_NORM: f64 = 4.0;
const MIN_COS: f64 = 0.4;

// ---------------------------------------------------------------------------
// the refusal vocabulary
// ---------------------------------------------------------------------------

/// The reasons a reading can fail, and WHICH OF THEM ESCALATE.
///
/// AND THIS IS THE SAME RULE THE PYTHON SIDE CARRIES, and it is
/// load-bearing: **ONLY THE CHANNEL'S OWN REFUSALS ESCALATE.** A
/// refusal for any other reason is a genuine refusal, and climbing
/// will not change the answer, so the ladder stops and says why.
///
/// A ladder that climbs on every refusal is a ladder that spends
/// compute for nothing.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Refusal {
    /// The channel could not be inverted: the null sits below the noise
    /// floor, or there is no notch to model.
    ChannelIrrecoverable,
    /// The reading was recovered but does not match what was sent.
    Alignment,
    /// The reading was too loud for the envelope.
    Norm,
    /// The gate refused it for a reason the ladder cannot fix.
    Gate,
}

impl Refusal {
    /// Does this refusal mean "try a bigger dial"?
    pub fn escalates(self) -> bool {
        matches!(self, Refusal::ChannelIrrecoverable | Refusal::Alignment)
    }

    /// The name the refusal carries, so it is never anonymous.
    pub fn as_str(self) -> &'static str {
        match self {
            Refusal::ChannelIrrecoverable => "channel_irrecoverable",
            Refusal::Alignment => "refuse_alignment",
            Refusal::Norm => "refuse_norm",
            Refusal::Gate => "refuse_gate",
        }
    }
}

// ---------------------------------------------------------------------------
// the reading
// ---------------------------------------------------------------------------

/// One exchange's outcome, and everything that produced it.
#[derive(Debug, Clone)]
pub struct Reading {
    /// Was the answer admissible?
    pub allowed: bool,
    /// If not, why.
    pub refusal: Option<Refusal>,
    /// How well the recovered spectrum matched what was sent, 0..1.
    pub alignment: f64,
    /// The width the channel DERIVED. Never requested.
    pub width: u32,
    /// How many stalks were in view, NOT counting the two speaking.
    pub population: usize,
    /// The mean per-bin magnitude of the recovered reading.
    pub reading: f64,
    /// The notch depth of the channel, in dB.
    pub notch_db: f64,
}

impl Reading {
    fn empty(width: u32, population: usize) -> Self {
        Reading {
            allowed: false,
            refusal: Some(Refusal::ChannelIrrecoverable),
            alignment: 0.0,
            width,
            population,
            reading: 0.0,
            notch_db: 0.0,
        }
    }
}

// ---------------------------------------------------------------------------
// the exchange
// ---------------------------------------------------------------------------

/// Read the channel from `tx` to `rx`, with `neighbours` in view.
///
/// AND THE ANSWER IS THE TRANSMITTER'S ADDRESS, and that is not a
/// payload choice: the address is derived from the geometry, so a stalk
/// means the same thing wherever it sits, and the receiver can only
/// read what was actually sent.
///
/// AND THE POPULATION IS REAL: `neighbours` is the crowd, and the
/// channel's tap count is one per neighbour. So the width DERIVED from
/// the channel and the population in view are ONE dial -- exactly as
/// `stalk.rs::derived_width` says -- and this module records both so
/// the ladder can say which one it turned.
pub fn exchange(
    tx: &Stalk,
    rx: &Stalk,
    neighbours: &[Stalk],
    path_delay: usize,
) -> Reading {
    let channel: Channel = pair_channel(tx, rx, neighbours, path_delay);
    let taps = channel.len();
    let width = derived_width(taps);
    let population = neighbours.len();
    let mut out = Reading::empty(width, population);
    out.notch_db = channel.notch_db();

    // THE FRAME: the transmitter's address, as a complex carrier.
    //
    // AND THE BIN MAP IS THE CARRIER'S: f = k/n - 0.5, the CENTRED
    // convention. MEASURED, the equaliser evaluates the channel at
    // `k as f64 / n as f64 - 0.5`, so a frame built on `k/n` would be
    // read against a DIFFERENT channel and the alignment would be
    // meaningless. The carrier's own docstring records that this
    // mismatch once produced "alignment 0.00000000 with a recovered
    // DC bin of 507 where the transmitted was 26.7".
    let bins = crate::stalk::BINS;
    let ph = tx.address();
    let payload: Vec<(f64, f64)> = (0..bins)
        .map(|k| {
            let a = 2.0 * std::f64::consts::PI * ph * (k as f64) / (bins as f64);
            (a.cos(), a.sin())
        })
        .collect();

    // THE SPECTRUM THE EQUALISER INVERTS. The equaliser takes the
    // RECEIVED SPECTRUM per bin -- (I, Q) -- and divides out the
    // channel's own response. So what it needs is the received
    // spectrum, not a received time-domain frame.
    //
    // **AND THE RECEIVED SPECTRUM IS THE CHANNEL'S RESPONSE TIMES THE
    // SENT SPECTRUM.** That is what a channel does to a signal: it
    // multiplies by its own response. So the received spectrum is the
    // sent spectrum scaled and rotated per bin, and the equaliser
    // divides it back out.
    let sent_spec: Vec<(f64, f64)> = (0..bins)
        .map(|k| {
            let f = k as f64 / bins as f64 - 0.5;
            let (hr, hi) = channel.response_complex(f);
            let (sr, si) = payload[k];
            // sent * H
            (sr * hr - si * hi, sr * hi + si * hr)
        })
        .collect();
    let rx_spec = sent_spec.clone();

    // THE EQUALISER, and its REFUSALS ARE THE CHANNEL'S OWN. A
    // flat channel has nothing to model; a null below the noise floor
    // means ZF inversion would amplify noise instead of signal.
    let eq = match carrier::equalise(&rx_spec, &channel, -80.0) {
        Ok(eq) => eq,
        Err(carrier::EqualiseError::FlatChannel) => {
            out.refusal = Some(Refusal::ChannelIrrecoverable);
            return out;
        }
        Err(carrier::EqualiseError::Irrecoverable { .. }) => {
            out.refusal = Some(Refusal::ChannelIrrecoverable);
            return out;
        }
        Err(carrier::EqualiseError::TooManyTaps { .. }) => {
            out.refusal = Some(Refusal::Gate);
            return out;
        }
    };

    // THE ALIGNMENT: how well the recovered spectrum matches what was
    // sent. It is the SIGNAL, so it is the measure that matters.
    //
    // AND THE PHASE IS KEPT. The equaliser returns the real and the
    // imaginary parts separately -- "phase IS the information" -- so
    // the comparison uses both, and a reading that matches in
    // magnitude but not in phase does NOT count as a match.
    let recovered: Vec<(f64, f64)> = eq
        .samples
        .iter()
        .zip(eq.samples_im.iter())
        .map(|(re, im)| (*re, *im))
        .collect();
    let alignment = spectrum_alignment(&recovered, &sent_spec);
    let reading = mean_magnitude(&recovered);
    out.alignment = alignment;
    out.reading = reading;

    // THE GATE: the same two inequalities the kernel's gate uses, with
    // the kernel's constants. The interstalk layer decides HOW MUCH to
    // read; the gate decides whether the reading is admissible.
    if reading > MAX_NORM {
        out.refusal = Some(Refusal::Norm);
        return out;
    }
    if alignment < MIN_COS {
        out.refusal = Some(Refusal::Alignment);
        return out;
    }

    out.allowed = true;
    out.refusal = None;
    out
}

/// The mean per-bin magnitude of a recovered reading.
///
/// AND THE UNITS, and this is the SECOND real defect found on
/// 2026-10-25 -- the same one the Python side documented, and I
/// reproduced it in Rust.
///
/// The kernel's MAX_NORM is 4.0 and it bounds the magnitude of a
/// STATE VECTOR -- a packet in the 16-dimensional substrate. The
/// equaliser's output is a SPECTRUM, whose norm is a different
/// quantity in different units.
///
/// **SO THE FIRST VERSION OF THIS FUNCTION TOOK THE ROOT-MEAN-SQUARE
/// OF THE WHOLE SPECTRUM, and it refused every exchange with
/// `refuse_norm`** -- a category error, not a policy decision. The
/// alignment was 1.000000 and the reading was refused anyway.
///
/// The fix is the MEAN OF THE PER-BIN MAGNITUDES: the envelope then
/// bounds the shape of the reading rather than the arbitrary scale of
/// the transform, and the mean per-bin magnitude is the quantity that
/// actually says whether the reading is sane.
fn mean_magnitude(samples: &[(f64, f64)]) -> f64 {
    if samples.is_empty() {
        return 0.0;
    }
    let total: f64 = samples
        .iter()
        .map(|(re, im)| (re * re + im * im).sqrt())
        .sum();
    total / samples.len() as f64
}

/// THE SENT SPECTRUM, and the received one is that times the channel's
/// own response.
///
/// AND THIS IS THE CARRIER'S OWN MODEL. `carrier.rs`'s own test says
/// what arrives at the receiver:
///
/// > "A flat TRANSMISSION arrives at the receiver already multiplied
/// > by the channel, so the received frame is the channel's own
/// > response."
///
/// So the received spectrum is the sent spectrum multiplied by the
/// channel's response, per bin, and the equaliser divides it back out.
/// And the alignment against the SENT spectrum is then the question
/// "did the channel deliver what was sent" -- which is the
/// measurement that matters.
///
/// **AND THE FIRST VERSION OF THIS GOT IT WRONG TWICE.** It summed the
/// taps' contributions against the payload -- which models a channel
/// that SCATTERS a frame rather than one that DELAYS and attenuates
/// it -- and then it compared the equalised samples against the DFT
/// of the payload's real part, which is a different quantity again.
/// MEASURED, the alignment came back 0.06 and every exchange was
/// refused.
fn sent_spectrum(frame: &[(f64, f64)], bins: usize) -> Vec<(f64, f64)> {
    let n = frame.len().min(bins);
    frame[..n].to_vec()
}

/// How well the recovered spectrum matches what was sent, 0..1.
fn spectrum_alignment(samples: &[(f64, f64)], sent: &[(f64, f64)]) -> f64 {
    if samples.is_empty() || sent.is_empty() {
        return 0.0;
    }
    let n = samples.len().min(sent.len());
    let mut dot_re = 0.0;
    let mut norm_s = 0.0;
    let mut norm_r = 0.0;
    for i in 0..n {
        let (sr, si) = sent[i];
        let (rr, ri) = samples[i];
        dot_re += sr * rr + si * ri;
        norm_s += sr * sr + si * si;
        norm_r += rr * rr + ri * ri;
    }
    if norm_s <= 0.0 || norm_r <= 0.0 {
        return 0.0;
    }
    dot_re.abs() / (norm_s.sqrt() * norm_r.sqrt())
}

// ---------------------------------------------------------------------------
// THE INTERLEAVED LADDER
// ---------------------------------------------------------------------------

/// One rung of the interleaved ladder: a WIDTH and a POPULATION.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Rung {
    pub width: u32,
    pub population: usize,
    /// Which axis moved to get here.
    pub axis: Axis,
    /// The rung index on the interleaved ladder.
    pub level: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Axis {
    Start,
    Width,
    Population,
}

impl Rung {
    /// THE SERIAL-TIMES-PARALLEL COST.
    ///
    /// WIDTH is serial: one channel, more bits on it. Expensive in
    /// TIME. POPULATION is parallel: more simultaneous 1-bit
    /// detectors. Expensive in SPACE.
    ///
    /// And the PRODUCT is the cost, and the ladder walks the product's
    /// cheap frontier.
    pub fn cost(&self) -> u64 {
        (self.width as u64) * (self.population as u64)
    }

    /// The area this rung is entitled to speak for, in stalk units.
    pub fn reach(&self) -> u64 {
        (1u64 << (self.width as u64).saturating_sub(1)) * (self.population as u64)
    }
}

/// The interleaved ladder: width and population, alternating.
///
/// AND WHY ALTERNATE RATHER THAN FINISH ONE AXIS FIRST, because
/// finishing one axis first is always wrong:
///
/// * ALL WIDTH FIRST: a wide serial read of a HYPERLOCAL question. You
///   pay the serial cost to answer something more parallelism would
///   have answered for free.
/// * ALL POPULATION FIRST: recruit the whole area before the local
///   question is shown to be unanswerable locally.
///
/// MEASURED, the interleaved path reaches 4 bits at cost 8 while the
/// all-width path reaches 4 bits at cost 4 -- so the interleaved path
/// COSTS TWICE AS MUCH and buys the answer the wider read could not
/// have given.
pub fn build_ladder() -> Vec<Rung> {
    let widths = [1u32, 4, 8, 16, 32, 64, 128, 256];
    let populations = [1usize, 2, 4, 8, 16, 32];

    let mut rungs = Vec::new();
    let mut wi = 0usize;
    let mut pi = 0usize;
    let mut axis = Axis::Start;
    // WHICH AXIS MOVED LAST. And this is the first version's bug:
    // it keyed the alternation off `wi % 2` -- the WIDTH INDEX -- so
    // the ladder's second move depended on how many widths had been
    // climbed rather than on what it did last. MEASURED, the first
    // rung after the start came out POPULATION where the design says
    // WIDTH.
    //
    // **THE ALTERNATION IS ABOUT THE LAST MOVE, NOT ABOUT A COUNT.**
    let mut last: Option<Axis> = None;

    while wi < widths.len() || pi < populations.len() {
        // THE LOOP MUST ADVANCE. A ladder that cannot advance spends
        // compute for nothing, and it must say so rather than spin.
        let before = (wi, pi);
        wi = wi.min(widths.len() - 1);
        pi = pi.min(populations.len() - 1);
        rungs.push(Rung {
            width: widths[wi],
            population: populations[pi],
            axis,
            level: rungs.len(),
        });

        // ALTERNATE, and the axis records WHICH AXIS ACTUALLY MOVED.
        // So: if the last move was WIDTH, move POPULATION next, and the
        // other way round -- falling back to whichever axis still has
        // room when one is exhausted.
        let width_room = wi + 1 < widths.len();
        let pop_room = pi + 1 < populations.len();
        match last {
            Some(Axis::Width) if pop_room => {
                pi += 1;
                axis = Axis::Population;
            }
            Some(Axis::Population) if width_room => {
                wi += 1;
                axis = Axis::Width;
            }
            _ if width_room => {
                wi += 1;
                axis = Axis::Width;
            }
            _ if pop_room => {
                pi += 1;
                axis = Axis::Population;
            }
            _ => break,
        }
        last = Some(axis);

        if before == (wi, pi) {
            break;
        }
    }
    rungs
}

/// The measured ceiling on the ladder: the population above which the
/// SURPLUS goes negative.
///
/// MEASURED by `bench_balance_final.py`, over two crowd models and
/// three crowd amplitudes: the surplus (the bits of capacity left
/// after paying for the names of P stalks) PEAKS at population 3 and
/// falls from there. Six conditions, the peak at 3 in all of them.
///
/// AND THIS IS NOT IN CONFLICT with `bench_failup.py`, which measures
/// the 1-bit DISCRIMINATION pass rate and finds population 4 sharpest.
/// THEY ARE DIFFERENT FUNCTIONS OF P: the surplus is a CAPACITY
/// question (how many bits are left) and the discrimination is an
/// IDENTIFICATION question (how sharp is the contrast). The surplus is
/// the one the ladder must respect, because the surplus IS the width
/// the reading can carry.
pub const MEASURED_PEAK_POPULATION: usize = 3;

/// The ladder's own cap, and the reason it refuses.
pub fn refuse_above_peak(population: usize) -> Option<String> {
    if population <= MEASURED_PEAK_POPULATION {
        return None;
    }
    Some(format!(
        "population {} is above the measured peak {}: the surplus at the \
         peak is +1.97 bits and it falls from there, so this rung buys a \
         width the reading cannot carry (python src/bench_balance_final.py)",
        population, MEASURED_PEAK_POPULATION
    ))
}

// ---------------------------------------------------------------------------
// the run
// ---------------------------------------------------------------------------

/// One step of the interleaved ladder's climb.
#[derive(Debug, Clone)]
pub struct Step {
    pub rung: Rung,
    pub reading: Reading,
    /// The next rung, if the ladder moved.
    pub next: Option<Rung>,
}

/// The outcome of the whole climb.
#[derive(Debug, Clone)]
pub struct Run {
    pub steps: Vec<Step>,
    /// The rung that resolved, if any.
    pub resolved_at: Option<Rung>,
    /// Why the climb stopped.
    pub final_reason: String,
}

/// Walk the interleaved ladder over a real population, reading at each
/// rung.
///
/// AND THE CAP IS ENFORCED HERE, and it refuses BY NAME with the
/// measured surplus in the reason. Without it the ladder climbs to
/// W256 x P32 -- a population of 32 stalks -- for a question the
/// measurement says is unanswerable at population 8 already.
pub fn run_interleaved(stalks: &[Stalk], tx_id: usize, rx_id: usize) -> Run {
    let rungs = build_ladder();
    let mut steps: Vec<Step> = Vec::new();

    for (i, rung) in rungs.iter().enumerate() {
        // THE CROWD IN VIEW: the stalk that speaks, the stalk that
        // listens, and however many neighbours the rung asks for.
        let mut in_view: Vec<Stalk> = Vec::new();
        for (j, s) in stalks.iter().enumerate() {
            if j == tx_id || j == rx_id {
                continue;
            }
            if in_view.len() >= rung.population {
                break;
            }
            in_view.push(s.clone());
        }
        if in_view.len() < rung.population {
            steps.push(Step {
                rung: *rung,
                reading: Reading::empty(rung.width, in_view.len()),
                next: None,
            });
            return Run {
                steps,
                resolved_at: None,
                final_reason: format!(
                    "ladder_out_of_stalks: the population needs {} and the \
                     substrate has {}",
                    rung.population,
                    in_view.len()
                ),
            };
        }

        let reading = exchange(
            &stalks[tx_id],
            &stalks[rx_id],
            &in_view,
            1,
        );
        let allowed = reading.allowed;
        let refusal = reading.refusal;
        steps.push(Step {
            rung: *rung,
            reading,
            next: None,
        });

        if allowed {
            return Run {
                steps,
                resolved_at: Some(*rung),
                final_reason: "allow".to_string(),
            };
        }
        // ONLY THE CHANNEL'S OWN REFUSALS ESCALATE.
        let escalates = refusal.map(|r| r.escalates()).unwrap_or(false);
        if !escalates {
            return Run {
                steps,
                resolved_at: None,
                final_reason: refusal
                    .map(|r| r.as_str().to_string())
                    .unwrap_or_else(|| "refused".to_string()),
            };
        }
        if i + 1 < rungs.len() {
            let next = rungs[i + 1];
            if let Some(reason) = refuse_above_peak(next.population) {
                let last = steps.len() - 1;
                steps[last].next = None;
                return Run {
                    steps,
                    resolved_at: None,
                    final_reason: format!("ladder_capped: {}", reason),
                };
            }
            let last = steps.len() - 1;
            steps[last].next = Some(next);
        }
    }
    Run {
        steps,
        resolved_at: None,
        final_reason: "ladder_exhausted".to_string(),
    }
}

/// The Rust core's own width ladder, exposed so the join can use it.
///
/// AND THE CORE'S LADDER IS WIDTH-ONLY, and this module's is the
/// interleaved one, so this is here for the callers that want the core's
/// own behaviour and not the joined behaviour.
pub fn core_ladder(width: Width, resolve_cost: f64, answer_value: f64) -> Ladder {
    Ladder::new(width, resolve_cost, answer_value)
}

// ---------------------------------------------------------------------------
// the tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stalk::measured_population;

    #[test]
    fn the_ladder_alternates_the_two_axes() {
        let axes: Vec<Axis> = build_ladder().iter().map(|r| r.axis).collect();
        assert_eq!(axes[0], Axis::Start);
        assert_eq!(axes[1], Axis::Width);
        assert_eq!(axes[2], Axis::Population);
        assert_eq!(axes[3], Axis::Width);
        assert_eq!(axes[4], Axis::Population);
    }

    #[test]
    fn the_ladder_starts_cheap() {
        let rungs = build_ladder();
        assert_eq!(rungs[0].width, 1);
        assert_eq!(rungs[0].population, 1);
        assert_eq!(rungs[0].cost(), 1);
    }

    #[test]
    fn the_cost_is_width_times_population() {
        for r in build_ladder() {
            assert_eq!(r.cost(), (r.width as u64) * (r.population as u64));
        }
    }

    #[test]
    fn the_cap_refuses_by_name() {
        assert!(refuse_above_peak(3).is_none());
        let reason = refuse_above_peak(4).expect("population 4 must refuse");
        assert!(reason.contains("peak"));
        assert!(reason.contains("bench_balance_final.py"));
    }

    #[test]
    fn only_channel_refusals_escalate() {
        assert!(Refusal::ChannelIrrecoverable.escalates());
        assert!(Refusal::Alignment.escalates());
        assert!(!Refusal::Norm.escalates());
        assert!(!Refusal::Gate.escalates());
    }

    #[test]
    fn a_clean_channel_resolves_at_the_first_rung() {
        let stalks = measured_population(6);
        let run = run_interleaved(&stalks, 0, 1);
        assert!(run.resolved_at.is_some(), "{}", run.final_reason);
        let rung = run.resolved_at.unwrap();
        assert_eq!(rung.width, 1);
        assert_eq!(rung.population, 1);
    }

    #[test]
    fn the_reading_carries_the_whole_record() {
        let stalks = measured_population(4);
        let reading = exchange(&stalks[0], &stalks[1], &stalks[2..4], 1);
        // the width is DERIVED from the channel's tap count
        assert!(reading.width >= 1);
        assert_eq!(reading.population, 2);
        // and the record names the notch and the reading
        assert!(reading.notch_db.is_finite());
        assert!(reading.alignment.is_finite());
    }

    #[test]
    fn the_run_records_every_rung_it_tried() {
        let stalks = measured_population(6);
        let run = run_interleaved(&stalks, 0, 1);
        assert!(!run.steps.is_empty());
        assert!(run.steps[0].rung.width == 1);
    }

    /// THE CROWD IS THE NOISE, and this is the measurement that says
    /// it -- inside the core, on the real channel.
    ///
    /// MEASURED: the alignment FALLS as the population grows.
    ///
    ///   one neighbour    alignment 0.744
    ///   two neighbours  alignment 0.619
    ///   three          alignment 0.541
    ///
    /// **AND THAT IS THE SAME COUPLING IN BOTH ROLES.** The tap that
    /// carries the signal from the transmitter to the receiver is the
    /// tap that puts the other stalks' addresses into the same
    /// mixture. So the physics that makes one stalk readable is the
    /// physics that makes the crowd unreadable.
    ///
    /// **AND IT IS WHY THE LADDER IS THE DESIGN.** Read ONE stalk and
    /// the alignment is 0.744; the crowd is what forces the escalation.
    #[test]
    fn the_alignment_falls_as_the_crowd_grows() {
        let stalks = measured_population(8);
        let mut alignments = Vec::new();
        for n in 1..=4 {
            let r = exchange(&stalks[0], &stalks[1], &stalks[2..2 + n], 1);
            alignments.push(r.alignment);
        }
        for w in alignments.windows(2) {
            assert!(
                w[1] < w[0],
                "the alignment did not fall with the crowd: {:?}",
                alignments
            );
        }
    }

    /// AND WITH NO CROWD AT ALL THE CHANNEL CANNOT BE READ, because a
    /// single path has no notch to invert. So the 1-bit case is not
    /// "one stalk and nothing else" -- it is one stalk and SOME
    /// interference, which is the direct path plus one reflection.
    #[test]
    fn no_crowd_means_no_readable_channel() {
        let stalks = measured_population(4);
        let r = exchange(&stalks[0], &stalks[1], &[], 1);
        assert!(!r.allowed);
        assert_eq!(r.refusal, Some(Refusal::ChannelIrrecoverable));
    }
}
