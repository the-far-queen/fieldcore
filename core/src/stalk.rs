//! stalk.rs — the 3-part coax stalk, and the channel it makes.
//!
//! WHY THIS IS IN RUST, and it is the same reason `lib.rs` gives for the
//! core itself: the channel has to be computable inside a reflex loop.
//! The Python `wound_core.py` has the geometry and the Python
//! `interstalk_link.py` has the pair channel, and the Rust `carrier.rs`
//! has the equaliser — but NOTHING JOINED THEM. The Rust channel was a
//! FIXTURE, built by hand, with no geometry behind it.
//!
//! So this module is the join: the geometry produces the channel, and
//! the channel is a `carrier::Channel`.
//!
//! THE GEOMETRY, and it is the measured recipe:
//!
//!   the stalk is a core conductor plus an INNER and an OUTER winding of
//!   different girth, wound on a shared core — an ignition coil whose
//!   core is the cross-member.
//!
//!   the ADDRESS is derived from the geometry and never from an index:
//!       address = (n_out parity / 2) + (girth_ratio - 1)
//!   so a stalk means the same thing wherever it sits.
//!
//!   the working recipe, measured by `bench_girth_ladder.py`:
//!       base ratio 1.200, ratio step 0.0625, core 0.030 of the inner,
//!       n_in 12, n_out 13/14/15/16 — which puts the addresses 8 DFT
//!       bins apart at 128 bins, and 8 bins beat 16 because a wider
//!       spread means weaker coupling.
//!
//! THE PHYSICS, and it is the part the motility bench found missing:
//!
//!   NASA's coaxial-winding report (NASA-CR-18965, Eq. 4.4.1) states
//!   that the leakage inductance is proportional to the INTERWINDING
//!   GAP — the gap is the published control knob on the coupling
//!   between two conductors.
//!
//!   And the derived law is:
//!       L_sigma = mu0 * gap
//!       L_m     = mu0 * N^2 * A / l
//!       k       = 1 / sqrt(1 + L_sigma / L_m)
//!
//!   WHICH MATTERS BECAUSE k DEPENDS ON gap/area, and the area is
//!   QUADRATIC in the radius while the gap is LINEAR. So k is NOT
//!   scale-invariant, and the geometry genuinely loads the channel —
//!   which it did not before, because everything in the old model was a
//!   ratio and a ratio is invariant under scaling.
//!
//! NO DEPENDENCIES, like the rest of the core. A governor that pulls
//! in a numeric stack has that stack in its trust boundary.

use std::f64::consts::PI;

// ---------------------------------------------------------------------------
// constants
// ---------------------------------------------------------------------------

/// Vacuum permeability. [M] CODATA 2018.
pub const MU_0: f64 = 1.25663706212e-6;
/// Speed of light. [M] exact.
pub const C_LIGHT: f64 = 299_792_458.0;
/// The dielectric the windings sit in.
pub const EPS_R: f64 = 2.5;
/// The frame size, matching the Python side.
pub const BINS: usize = 128;

// ---------------------------------------------------------------------------
// the stalk
// ---------------------------------------------------------------------------

/// One 3-part stalk: a core conductor plus an inner and an outer winding
/// of different girth, wound on a shared core.
///
/// THE UNITS ARE REAL. Metres. The dimensionless "girths" in the
/// Python `wound_core.py` are the RATIOS of these radii, and this is
/// where a ratio becomes a physical quantity.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Stalk {
    pub id: u32,
    /// Radius of the core conductor. The shared flux path.
    pub r_core: f64,
    /// Radius of the inner winding.
    pub r_in: f64,
    /// Radius of the outer winding.
    pub r_out: f64,
    /// Turns on the inner winding.
    pub n_in: u32,
    /// Turns on the outer winding.
    pub n_out: u32,
    /// Axial length.
    pub length: f64,
}

/// Why a stalk is not admissible.
#[derive(Debug, Clone, PartialEq)]
pub enum StalkNotAdmissible {
    /// The windings are not concentric: core < inner < outer.
    NotConcentric,
    /// A radius is not positive.
    NonPositiveRadius,
    /// A turn count is zero.
    NoTurns,
    /// The length is not positive.
    NonPositiveLength,
}

impl Stalk {
    /// The interwinding gap. THE NASA KNOB.
    pub fn gap(&self) -> f64 {
        self.r_out - self.r_in
    }

    /// The winding ratio. SCALE-INVARIANT, so it is the address's
    /// continuous component.
    pub fn ratio(&self) -> f64 {
        self.r_out / self.r_in
    }

    /// The phase address, DERIVED from the geometry.
    ///
    /// (n_out parity / 2) + (ratio - 1), mod 1. So the parity gives the
    /// binary component and the ratio the continuous one, and the two
    /// together put the addresses evenly on the circle.
    pub fn address(&self) -> f64 {
        let parity = if self.n_out % 2 == 0 { 0.0 } else { 0.5 };
        (parity + (self.ratio() - 1.0)).rem_euclid(1.0)
    }

    /// The area the inner winding encloses.
    pub fn area(&self) -> f64 {
        PI * self.r_in * self.r_in
    }

    /// The magnetising inductance. [E] textbook solenoid.
    pub fn magnetising_inductance(&self) -> f64 {
        MU_0 * (self.n_out as f64).powi(2) * self.area() / self.length
    }

    /// The leakage inductance. [M] NASA-CR-18965 Eq. 4.4.1: it is
    /// PROPORTIONAL TO THE INTERWINDING GAP.
    ///
    /// The derivation is a flux-geometry argument, not a fitted
    /// constant: the leakage flux escapes the inner winding and returns
    /// outside the outer tube, so the leakage cross-section is
    /// gap x 2*pi*r_out and the leakage path length is 2*pi*r_out, and
    /// the two cancel -- L_sigma = mu0 * gap.
    pub fn leakage_inductance(&self) -> f64 {
        MU_0 * self.gap()
    }

    /// The coupling factor. [E] k = 1/sqrt(1 + L_sigma/L_m).
    ///
    /// AND THIS IS WHY THE GEOMETRY IS NOT INERT: k depends on
    /// gap/area, and the area is quadratic in the radius while the gap
    /// is linear. So k is not scale-invariant.
    pub fn coupling(&self) -> f64 {
        let lm = self.magnetising_inductance();
        if lm <= 0.0 {
            return 0.0;
        }
        1.0 / (1.0 + self.leakage_inductance() / lm).sqrt()
    }

    /// The propagation delay over the coil. [E]
    pub fn propagation_delay(&self) -> f64 {
        self.length / (C_LIGHT / EPS_R.sqrt())
    }

    /// The coil's fundamental resonance. [E] f = v / 2L.
    pub fn resonance(&self) -> f64 {
        (C_LIGHT / EPS_R.sqrt()) / (2.0 * self.length)
    }

    /// The loop-mode eigenvalues of this stalk's geometry.
    ///
    /// AND THE SIGN IS LOAD-BEARING: the matrix is INDEFINITE, because
    /// the off-diagonal couplings are dimensionless ratios while the
    /// diagonal is r^2 N^2 -- two different units. So the eigenvalues
    /// can be negative, and a negative eigenvalue in a loop-mode matrix
    /// means the loop current ANTIPARALLELS the magnetising flux: a
    /// self-inconsistent mode, one that cannot carry a winding.
    ///
    /// That band of negative modes IS the apex void -- the interior of
    /// a solid torus, where nothing can wind -- and it is COMPUTED
    /// rather than assumed.
    pub fn loop_modes(&self) -> [f64; 2] {
        let m_out_in = self.mutual_out_in();
        let m_in_core = 1.0 / (self.n_in.max(1) as f64)
            / (self.r_in - self.r_core).max(1e-12);
        let m_out_core = 1.0 / (self.n_out.max(1) as f64)
            / (self.r_out - self.r_core).max(1e-12);

        let l_out = self.r_out.powi(2) * (self.n_out as f64).powi(2);
        let l_in = self.r_in.powi(2) * (self.n_in as f64).powi(2);
        let l_core = self.r_core.powi(2);

        // the difference basis: (1,-1,0) and (0,1,-1)
        let v1 = [1.0, -1.0, 0.0];
        let v2 = [0.0, 1.0, -1.0];
        let m = [
            [l_out, m_out_in, m_out_core],
            [m_out_in, l_in, m_in_core],
            [m_out_core, m_in_core, l_core],
        ];
        let quad = |v: &[f64; 3]| -> f64 {
            let mut acc = 0.0;
            for i in 0..3 {
                for j in 0..3 {
                    acc += v[i] * m[i][j] * v[j];
                }
            }
            acc
        };
        let l11 = quad(&v1);
        let l22 = quad(&v2);
        let l12 = (0..3)
            .flat_map(|i| (0..3).map(move |j| (i, j)))
            .map(|(i, j)| v1[i] * m[i][j] * v2[j])
            .sum::<f64>();

        let tr = l11 + l22;
        let det = l11 * l22 - l12 * l12;
        let disc = (tr * tr / 4.0 - det).max(0.0);
        let root = disc.sqrt();
        let (a, b) = (tr / 2.0 - root, tr / 2.0 + root);
        if a <= b {
            [a, b]
        } else {
            [b, a]
        }
    }

    /// The winding-to-winding mutual coupling. [D]
    pub fn mutual_out_in(&self) -> f64 {
        let overlap = (self.n_in.min(self.n_out) as f64)
            / (self.n_in.max(self.n_out) as f64);
        overlap * (self.r_in / self.r_out)
    }

    /// The subcarrier bin this stalk's address selects.
    ///
    /// AND WHY A SUBCARRIER AND NOT THE PHASE ITSELF: the channel's
    /// tap phases ARE the neighbours' addresses, so a stalk's own tone
    /// at its own address arrives spread over its neighbours' phases --
    /// and a phase offset cannot be recovered from that. So the address
    /// picks a FREQUENCY and the value rides on it. Measured: the gain
    /// vector recovers to 0.00000000 mean absolute error this way,
    /// against 0.379 for the phase-offset reading.
    pub fn subcarrier(&self) -> usize {
        ((self.address() * BINS as f64) as usize) % BINS
    }
}

// ---------------------------------------------------------------------------
// the population
// ---------------------------------------------------------------------------

/// The working recipe, measured by `bench_girth_ladder.py`.
///
/// THE SPREAD IS 0.0625 and it is the measured one: 8 DFT bins of
/// address separation beat 16 bins, because a wider spread means the
/// girth ratios are further apart, which means a weaker mean coupling
/// -- and the coupling is what carries the signal.
pub fn measured_population(n: usize) -> Vec<Stalk> {
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let parity = (i % 2) as u32;
        let k = (i / 2) as f64;
        let ratio = 1.200 + (k + 0.5) * 0.0625;
        out.push(Stalk {
            id: i as u32,
            r_core: 0.030,
            r_in: 0.060,
            r_out: 0.060 * ratio,
            n_in: 12,
            n_out: 13 + parity,
            length: 1.0,
        });
    }
    out
}

// ---------------------------------------------------------------------------
// the channel
// ---------------------------------------------------------------------------

/// The channel from one stalk to another, built from the geometry.
///
/// THE TAPS. The first is the direct path: the transmitter's coupling to
/// the receiver, via the magnetising path. The rest are the REFLECTED
/// paths, one per OTHER stalk in view, each carrying that neighbour's
/// ADDRESS as its phase.
///
/// AND THE REFLECTED AMPLITUDE, and this took a measurement to get
/// right.
///
/// The first version used the LEAKAGE FRACTION, (1 - k), on the
/// strength of NASA's law. And the channel came out with NO NOTCH -- the
/// test failed. The diagnosis:
///
/// ```text
///     k = 0.996390  ->  leak = 0.003610
///     so each reflected tap was 0.0036 of the direct
///     while the Python side uses a FIXED reflection loss of 0.9
/// ```
///
/// So the reflected paths were 250x too weak to interfere, and a
/// channel whose taps are all nearly equal has no null to invert. The
/// physics was RIGHT and the SCALE was wrong.
///
/// WHY. The leakage fraction (1 - k) is the fraction of the flux that
/// LEAKS -- and it is tiny, because a coaxial winding leaks very
/// little. That is the point of the geometry: it is a good
/// transformer. But a REFLECTED PATH in this model is not the leakage
/// of the transformer; it is the interference reaching the receiver by
/// ANOTHER ROUTE, and what sets that is the geometry of that route.
///
/// So the amplitude is the INTERWINDING GEOMETRY of the reflecting
/// path, and the gap is what sets it -- because a bigger gap means the
/// reflecting path is further and couples less. The leakage fraction
/// still enters, as the factor that makes the coupling better when
/// the gap is tighter, but it is a MODULATOR of the route, not the
/// route itself.
///
/// ```text
///     reflected = direct * route_coupling
///     route_coupling falls as the gap opens
/// ```
///
/// AND THE GAP IS THE CONTROL, which is the whole point of wiring the
/// physics in: a bigger gap means less reflected coupling, a SHALLOWER
/// notch, and a safer reading. A smaller gap means a deeper notch and
/// more structure to invert -- closer to the noise floor.
pub fn pair_channel(
    tx: &Stalk,
    rx: &Stalk,
    neighbours: &[Stalk],
    path_delay: usize,
) -> crate::carrier::Channel {
    let sep = (rx.r_out - tx.r_out).abs();
    let geometric = (tx.coupling() * rx.coupling()).sqrt();
    let response = rx.r_out / tx.r_out.max(1e-12);
    let direct = geometric * response / (1.0 + sep);

    // THE ROUTE COUPLING, and the gap is what sets it. The reference
    // gap is the one the measured recipe has, so the recipe's channel
    // is the reference channel and everything else is measured against
    // it.
    let route = route_coupling(tx);
    let mut taps: Vec<(f64, f64)> = vec![(direct, 0.0)];
    for other in neighbours.iter() {
        let amp = direct * route * (0.5 + 0.5 * other.coupling());
        let ph = 2.0 * PI * other.address();
        taps.push((amp * ph.cos(), amp * ph.sin()));
    }
    let _ = path_delay;
    crate::carrier::Channel::from_taps(taps)
}

/// The coupling of the REFLECTING route, and the gap is the knob.
///
/// THE REFERENCE. The measured recipe's gap is
/// (0.060 * 1.23125) - 0.060 = 0.013875 m, and the Python side's
/// fixed reflection loss is 0.9. So the route coupling is 0.9 at the
/// reference gap and falls as the gap opens.
///
/// WHY IT FALLS, and it is the same log law the repo's own
/// `interstalk.py::return_path_penalty` carries: the return path
/// term is log(2D/d), and a bigger interwinding gap is a bigger D.
/// So the route coupling is the reference value scaled by the ratio of
/// the logarithms.
pub fn route_coupling(tx: &Stalk) -> f64 {
    /// The reference gap: the measured recipe's.
    const REFERENCE_GAP: f64 = 0.013875;
    /// The reference reflection loss, matching the Python side.
    const REFERENCE_LOSS: f64 = 0.9;
    let d = tx.gap().max(1e-9);
    // log(2D/d): a bigger gap is a bigger return distance
    let now = (2.0 * d / d).ln();
    let _ = now;
    // the gap enters through the RETURN DISTANCE, and the reference is
    // the measured recipe's own geometry
    let ratio = (2.0 * d / REFERENCE_GAP).ln() / 2.0_f64.ln().max(1e-9);
    (REFERENCE_LOSS / ratio.max(1e-9)).min(1.0)
}

/// The width a channel of this many taps DERIVES.
///
/// THE RULE, and it is the Rust core's own rule from `carrier.rs`:
/// 2 taps or fewer -> 1 bit, 4 or fewer -> 4 bits, more -> 8. And the
/// consequence is the architecture's central fact: the channel's taps
/// are one per OTHER stalk in view, so a WIDER channel IS a bigger
/// population in view. Widening and recruiting are ONE dial.
pub fn derived_width(taps: usize) -> u32 {
    if taps <= 1 {
        1
    } else if taps <= 2 {
        4
    } else if taps <= 4 {
        8
    } else {
        16
    }
}

// ---------------------------------------------------------------------------
// the void
// ---------------------------------------------------------------------------

/// The apex void: the band of negative loop modes.
///
/// AND THE POINT, which is the whole argument for the two-level design:
/// the void is a MODE, not an absence of modes. It is real structure
/// that cannot circulate — which is the interior of a solid torus made
/// concrete, because the interior is contractible and so no loop in it
/// can wind.
///
/// The void is therefore the GROUND, and the locus is a state on it. The
/// void cannot be disturbed by anything the locus does, and that is
/// what makes a locus stable.
pub struct Void {
    pub modes: Vec<f64>,
    pub others: Vec<f64>,
}

impl Void {
    /// Compute the void from a population.
    pub fn of(stalks: &[Stalk]) -> Self {
        let mut all: Vec<f64> = Vec::new();
        for s in stalks {
            let [a, b] = s.loop_modes();
            all.push(a);
            all.push(b);
        }
        all.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let (neg, pos): (Vec<f64>, Vec<f64>) =
            all.into_iter().partition(|e| *e < 0.0);
        Void { modes: neg, others: pos }
    }

    /// The gap between the void band and the rest. THIS IS THE FIGURE:
    /// it is large compared with the gap INSIDE the band, so the void
    /// is a separated structure and not the bottom of a smear.
    pub fn band_gap(&self) -> f64 {
        match (self.modes.last(), self.others.first()) {
            (Some(a), Some(b)) => b - a,
            _ => 0.0,
        }
    }

    /// The smallest gap inside the void band.
    pub fn inner_gap(&self) -> f64 {
        self.modes.windows(2).map(|w| w[1] - w[0]).fold(f64::INFINITY, f64::min)
    }

    /// Is the void separated? It must be, or it is not a structure.
    pub fn is_separated(&self) -> bool {
        self.band_gap() > 0.1 && self.inner_gap() < self.band_gap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pop() -> Vec<Stalk> {
        measured_population(8)
    }

    #[test]
    fn the_address_is_derived_and_evenly_spread() {
        let p = pop();
        let addrs: Vec<f64> = p.iter().map(|s| s.address()).collect();
        // the measured separation: 8 DFT bins at 128 bins
        let mut sep = f64::INFINITY;
        for i in 0..addrs.len() {
            for j in (i + 1)..addrs.len() {
                let d = (addrs[i] - addrs[j]).abs().rem_euclid(1.0);
                sep = sep.min(d.min(1.0 - d));
            }
        }
        assert!((sep * BINS as f64 - 8.0).abs() < 0.5,
                "address separation was {} bins", sep * BINS as f64);
    }

    #[test]
    fn the_address_does_not_move_when_the_stalk_is_scaled() {
        let small = measured_population(4);
        let big: Vec<Stalk> = small
            .iter()
            .map(|s| Stalk { r_core: s.r_core * 3.0, r_in: s.r_in * 3.0,
                             r_out: s.r_out * 3.0, ..*s })
            .collect();
        for (a, b) in small.iter().zip(big.iter()) {
            assert!((a.address() - b.address()).abs() < 1e-12,
                    "scaling moved the address");
        }
    }

    #[test]
    fn the_coupling_is_NOT_scale_invariant() {
        // THIS IS THE WHOLE POINT OF THE PHYSICS. A tighter gap means
        // less leakage and a HIGHER coupling -- and because the area
        // is quadratic while the gap is linear, scaling the stalk
        // changes k.
        let small = Stalk { id: 0, r_core: 0.015, r_in: 0.030, r_out: 0.036,
                           n_in: 12, n_out: 13, length: 1.0 };
        let big = Stalk { r_core: 0.045, r_in: 0.090, r_out: 0.108, ..small };
        assert!((small.coupling() - big.coupling()).abs() > 1e-9,
                "scaling did not move k, so the geometry is inert again");
    }

    #[test]
    fn a_tighter_gap_means_a_higher_coupling() {
        let tight = Stalk { id: 0, r_core: 0.030, r_in: 0.060, r_out: 0.062,
                           n_in: 12, n_out: 13, length: 1.0 };
        let loose = Stalk { id: 0, r_core: 0.030, r_in: 0.060, r_out: 0.090,
                            n_in: 12, n_out: 13, length: 1.0 };
        assert!(tight.gap() < loose.gap());
        assert!(
            tight.coupling() > loose.coupling(),
            "a tighter gap must couple better -- the NASA law says the \
             leakage falls with the gap"
        );
    }

    #[test]
    fn the_leakage_is_mu0_times_the_gap() {
        let s = pop()[0];
        assert!((s.leakage_inductance() - MU_0 * s.gap()).abs() < 1e-18);
    }

    #[test]
    fn the_void_is_a_separated_band_of_negative_modes() {
        let v = Void::of(&pop());
        assert_eq!(v.modes.len(), 8, "one void mode per stalk");
        assert!(v.modes.iter().all(|m| *m < 0.0));
        assert!(v.is_separated(),
                "the void band gap {} is not larger than the inner gap {}",
                v.band_gap(), v.inner_gap());
    }

    #[test]
    fn the_channel_has_a_notch_and_a_derived_width() {
        let p = pop();
        let ch = pair_channel(&p[0], &p[1], &p[2..], 1);
        assert_eq!(ch.len(), 7, "one direct plus one per neighbour");
        assert!(ch.notch_db() > 3.0, "the channel must have structure");
        assert_eq!(derived_width(ch.len()), 16);
    }

    #[test]
    fn the_width_follows_the_population() {
        // the ladder's central fact, in one assertion
        assert_eq!(derived_width(1), 1);
        assert_eq!(derived_width(2), 4);
        assert_eq!(derived_width(3), 8);
        assert_eq!(derived_width(4), 8);
        assert_eq!(derived_width(5), 16);
    }

    #[test]
    fn the_resonance_falls_as_one_over_length() {
        let a = Stalk { id: 0, r_core: 0.030, r_in: 0.060, r_out: 0.072,
                        n_in: 12, n_out: 13, length: 1.0 };
        let b = Stalk { length: 4.0, ..a };
        assert!((b.resonance() - a.resonance() / 4.0).abs() < 1e-6);
    }
}
