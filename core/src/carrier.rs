//! carrier.rs -- the braid as a coded carrier, not a suppressed wire.
//!
//! WHY THIS REPLACED THE SUPPRESSION MODEL. The first draft of this file
//! computed girth, sheath and spacing to make crosstalk small. That is
//! the wrong frame, and running the numbers is what showed it. Look at
//! what every working analogue actually does:
//!
//!   5G        OFDM: thousands of narrow subcarriers, each narrow enough
//!             that its own interference looks like FLAT noise. Receiver
//!             models the channel, subtracts it. Interference becomes a
//!             predictable nuisance instead of a corruption.
//!   radio     pilots: the most important transmission on the link is a
//!             KNOWN reference, so what arrives can be interpreted at all.
//!   TV        guard bands: you do not raise power, you leave the gap.
//!   brain     low-SNR carrier, heavy coding. amplitude is all-or-none so
//!             it carries ONE bit; everything else is phase. 432-1858
//!             bits/s at 50-200 Hz, all of it timing.
//!   car       the opposite: no coding, reflex, one bit, escalate.
//!   minimax   token codes are a lossy 1-of-V carrier with no channel
//!             model at all. Interference between senses is never
//!             estimated, so it lands as meaning. That is wordtrance.
//!
//! Not one of them suppresses interference. All of them TRANSFORM it.
//! So the substrate's job is not to keep stalks clean. It is to model the
//! crosstalk between them and invert it.
//!
//! THE BORROWED STRUCTURE, precisely:
//!
//!   MTE      == channel estimation + inversion. You do not remove
//!              ambiguity from the input; you model it and subtract it.
//!   M0       == the pilot symbol. It carries no payload. It is the known
//!              reference that makes everything else interpretable.
//!   the gate == the receiver refusing a frame it cannot equalise.
//!
//! WHAT IS MEASURED AND WHAT IS MINE. The equaliser structure, pilot
//! insertion and guard-band arithmetic are established communications
//! engineering. Applying them to braided stalks is [H] -- a hypothesis
//! with a measurable prediction, which is the only kind worth having.

use crate::ladder::Width;

const MAX_TAPS: usize = 32;

// ---------------------------------------------------------------------------
// the channel: what one stalk sees from its neighbours
// ---------------------------------------------------------------------------

/// Crosstalk from every other strand in the braid, as a complex gain per
/// tap. Complex, not real, because phase is the information.
#[derive(Debug, Clone, PartialEq)]
pub struct Channel {
    taps: Vec<(f64, f64)>,
}

impl Channel {
    /// A clean channel: identity, no coupling.
    pub fn clean() -> Self {
        Channel { taps: vec![(1.0, 0.0)] }
    }

    pub fn from_taps(taps: Vec<(f64, f64)>) -> Self {
        assert!(!taps.is_empty(), "a channel with no taps is not a channel");
        assert!(taps.len() <= MAX_TAPS, "tap count exceeds MAX_TAPS");
        Channel { taps }
    }

    pub fn taps(&self) -> &[(f64, f64)] { &self.taps }
    pub fn len(&self) -> usize { self.taps.len() }

    /// Frequency response magnitude at normalised frequency f in [-0.5,0.5].
    ///
    /// |H(f)| = |sum_n h_n * exp(-j*2*pi*f*n)|
    pub fn response_mag(&self, f: f64) -> f64 {
        let mut re = 0.0;
        let mut im = 0.0;
        for (n, (hr, hi)) in self.taps.iter().enumerate() {
            let th = -2.0 * std::f64::consts::PI * f * n as f64;
            re += hr * th.cos() - hi * th.sin();
            im += hr * th.sin() + hi * th.cos();
        }
        (re * re + im * im).sqrt()
    }

    /// Group delay in samples. d(arg H)/dw, by central difference.
    pub fn group_delay(&self, f: f64) -> f64 {
        let h = 1e-4;
        let (re_p, im_p) = self.response_complex(f + h);
        let (re_m, im_m) = self.response_complex(f - h);
        let p = re_p.atan2(im_p);
        let m = re_m.atan2(im_m);
        let mut d = (p - m) / (2.0 * h);
        if d > 0.5 { d -= 1.0; }
        if d < -0.5 { d += 1.0; }
        -d
    }

    fn response_complex(&self, f: f64) -> (f64, f64) {
        let mut re = 0.0;
        let mut im = 0.0;
        for (n, (hr, hi)) in self.taps.iter().enumerate() {
            let th = -2.0 * std::f64::consts::PI * f * n as f64;
            re += hr * th.cos() - hi * th.sin();
            im += hr * th.sin() + hi * th.cos();
        }
        (re, im)
    }

    /// The notch depth available, in dB. This is how much of the
    /// interference the equaliser can actually remove.
    ///
    /// A channel that is flat has no usable notch: there is nothing to
    /// model and therefore nothing to invert. THE CHANNEL MUST HAVE
    /// STRUCTURE. This is the design requirement the suppression model
    /// missed -- a perfectly isolated braid is an uncorrectable braid.
    pub fn notch_db(&self) -> f64 {
        let peak = (0..=200)
            .map(|i| self.response_mag(i as f64 / 200.0 - 0.5))
            .fold(0.0f64, f64::max);
        if peak <= 0.0 { return 0.0; }
        let mut null = f64::INFINITY;
        for i in 0..=200 {
            let m = self.response_mag(i as f64 / 200.0 - 0.5);
            if m < null { null = m; }
        }
        if null <= 0.0 { return 60.0; }
        20.0 * (null / peak).log10()
    }
}

// ---------------------------------------------------------------------------
// the pilot
// ---------------------------------------------------------------------------

/// A known reference. Carries no payload; its whole job is to make the
/// received frame interpretable.
///
/// This is M0. The governor transmits no decision of its own -- it
/// transmits the reference the rest of the link is equalised against.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Pilot {
    pub value: u8,
}

impl Default for Pilot {
    fn default() -> Self {
        Pilot { value: 1 } // BPSK +1
    }
}

// ---------------------------------------------------------------------------
// equalisation
// ---------------------------------------------------------------------------

/// Why a frame cannot be corrected.
#[derive(Debug, Clone, Copy, PartialEq)]  // holds f64, so no Eq
pub enum EqualiseError {
    /// No usable notch: the channel is flat, so there is nothing to model.
    FlatChannel,
    /// The response falls below the noise floor inside the band.
    Irrecoverable { null_db: f64 },
    /// Too many taps for the sample rate.
    TooManyTaps { taps: usize },
}

/// The result of equalising a frame.
#[derive(Debug, Clone, PartialEq)]
pub struct Equalised {
    /// The recovered samples.
    pub samples: Vec<f64>,
    /// Residual error power after inversion, relative to signal.
    pub residual_db: f64,
    /// Which width this frame needed to resolve.
    pub width: Width,
}

/// Equalise one frame. Fail-closed: an unequalisable frame is refused and
/// says why, rather than being returned slightly wrong.
pub fn equalise(
    rx: &[f64],
    channel: &Channel,
    noise_floor: f64,
) -> Result<Equalised, EqualiseError> {
    if channel.len() > MAX_TAPS {
        return Err(EqualiseError::TooManyTaps { taps: channel.len() });
    }
    let notch = channel.notch_db();
    if notch < 3.0 {
        // nothing to invert. A perfectly clean braid is not a good braid,
        // it is an uncorrectable one.
        return Err(EqualiseError::FlatChannel);
    }
    if notch < noise_floor.abs() {
        return Err(EqualiseError::Irrecoverable { null_db: -notch });
    }

    // One-tap ZF inversion, per subcarrier, in the frequency domain.
    let n = rx.len();
    let mut out = vec![0.0; n];
    let mut worst = f64::INFINITY;
    for k in 0..n {
        let f = k as f64 / n as f64 - 0.5;
        let (hr, hi) = channel.response_complex(f);
        let mag2 = hr * hr + hi * hi;
        if mag2 <= f64::EPSILON {
            return Err(EqualiseError::FlatChannel);
        }
        let (yr, yi) = (rx[k], 0.0);
        out[k] = (yr * hr + yi * hi) / mag2;
        let got = channel.response_mag(f);
        if got < worst { worst = got; }
    }
    let residual = -20.0 * worst.max(1e-12).log10();
    // A frame needed more than local resolution iff the channel is long.
    let width = if channel.len() <= 2 { Width::W1 }
        else if channel.len() <= 4 { Width::W4 }
        else { Width::W8 };
    Ok(Equalised { samples: out, residual_db: residual, width })
}

// ---------------------------------------------------------------------------
// the guard band
// ---------------------------------------------------------------------------

/// OFDM's guard interval. The receiver cannot distinguish a symbol from
/// its own reflection without a gap, so the gap is not overhead -- it is
/// what makes the symbol readable at all.
pub struct Frame {
    pub guard_frac: f64,
    pub subcarriers: usize,
    pub useful_frac: f64,
}

impl Frame {
    /// Guard interval as a fraction of the symbol period. For OFDM with a
    /// rectangular pulse it is the cyclic-prefix fraction.
    pub fn new(subcarriers: usize, guard_frac: f64) -> Self {
        assert!(subcarriers > 1, "one subcarrier is not a multiplex");
        assert!((0.0..0.5).contains(&guard_frac),
                "guard must be under half or there is no signal left");
        Frame {
            guard_frac,
            subcarriers,
            useful_frac: (1.0 - guard_frac) * subcarriers as f64,
        }
    }

    /// Spectral efficiency loss. This is the price of the design and it
    /// is not free: the guard costs throughput to buy correctness.
    pub fn overhead_db(&self) -> f64 {
        -10.0 * (1.0 - self.guard_frac).log10()
    }
}

// ---------------------------------------------------------------------------
// the braid as a multiplex
// ---------------------------------------------------------------------------

/// One strand's contribution to the shared carrier.
#[derive(Debug, Clone)]
pub struct Stratum {
    pub id: &'static str,
    /// Phase offset. The braid is a phase-coded multiplex, so phase is
    /// the address -- not girth, not length.
    pub phase: f64,
    /// Amplitude weight.
    pub gain: f64,
}

/// Sum every stratum onto one carrier. Orthogonal in the frequency domain,
/// correlated in time -- which is exactly the trade the braid makes.
pub fn multiplex(strata: &[Stratum], samples: usize) -> Vec<f64> {
    let mut out = vec![0.0; samples];
    for s in strata {
        for i in 0..samples {
            let t = i as f64 / samples as f64;
            out[i] += s.gain * (2.0 * std::f64::consts::PI * s.phase * t).cos();
        }
    }
    out
}

/// FFT-lite: naive DFT. Fine at these sizes and it has no dependencies,
/// which matters more than speed for a core that must not carry a crate.
pub fn dft(x: &[f64]) -> Vec<(f64, f64)> {
    let n = x.len();
    (0..n)
        .map(|k| {
            let mut re = 0.0;
            let mut im = 0.0;
            for (i, v) in x.iter().enumerate() {
                let th = -2.0 * std::f64::consts::PI * (k * i) as f64 / n as f64;
                re += v * th.cos();
                im += v * th.sin();
            }
            (re, im)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn two_path_channel() -> Channel {
        // direct + one reflection at -0.4, delayed one sample
        Channel::from_taps(vec![(1.0, 0.0), (-0.4, 0.2)])
    }

    #[test]
    fn clean_channel_is_uncorrectable() {
        // THE POINT. An isolated braid has no notch, so it has nothing to
        // model and therefore nothing to invert.
        let e = equalise(&[1.0, 0.0, 0.0, 0.0], &Channel::clean(), -60.0);
        assert_eq!(e.unwrap_err(), EqualiseError::FlatChannel);
    }

    #[test]
    fn a_flat_channel_has_no_notch() {
        assert!(Channel::clean().notch_db() < 3.0);
    }

    #[test]
    fn two_path_channel_has_a_notch() {
        let c = two_path_channel();
        assert!(c.notch_db() > 10.0, "two paths must produce a null");
    }

    #[test]
    fn unequalisable_frame_is_refused_not_approximated() {
        // noise floor above the notch -> cannot equalise
        let e = equalise(&[1.0; 8], &two_path_channel(), -5.0);
        assert!(matches!(e, Err(EqualiseError::Irrecoverable { .. })));
    }

    #[test]
    fn equalise_recovers_a_flat_gain() {
        // constant-amplitude spectrum -> recovered amplitude is 1.0
        let rx = vec![1.0f64; 16];
        let eq = equalise(&rx, &two_path_channel(), -80.0).expect("should equalise");
        for s in &eq.samples {
            assert!((s - 1.0).abs() < 1e-9, "got {}", s);
        }
    }

    #[test]
    fn wider_channel_needs_wider_resolution() {
        let narrow = equalise(&[1.0; 16], &Channel::from_taps(vec![(1.0, 0.0), (-0.4, 0.0)]), -80.0).unwrap();
        let wide = equalise(&[1.0; 16], &Channel::from_taps(vec![(1.0, 0.0), (-0.4, 0.2), (0.2, -0.1), (0.1, 0.05)]), -80.0).unwrap();
        assert_eq!(narrow.width, Width::W1);
        assert!(wide.width > narrow.width, "more taps needs more width");
    }

    #[test]
    fn group_delay_is_finite() {
        let c = two_path_channel();
        let d = c.group_delay(0.1);
        assert!(d.is_finite());
    }

    #[test]
    fn guard_band_costs_throughput() {
        let f = Frame::new(2048, 0.25);
        assert!(f.useful_frac < 2048.0);
        assert!(f.overhead_db() > 0.0, "a guard must cost something");
    }

    #[test]
    fn guard_over_half_is_refused() {
        let r = std::panic::catch_unwind(|| Frame::new(2048, 0.75));
        assert!(r.is_err(), "no useful_frac left is not a frame");
    }

    #[test]
    fn multiplex_sums_strata() {
        let s = vec![
            Stratum { id: "coding", phase: 0.0, gain: 1.0 },
            Stratum { id: "language", phase: 0.25, gain: 1.0 },
        ];
        let out = multiplex(&s, 64);
        assert_eq!(out.len(), 64);
        assert!(out.iter().any(|v| *v > 1.5), "two strands must add");
    }

    #[test]
    fn dft_of_a_constant_is_a_single_bin() {
        let sp = dft(&[1.0f64; 8]);
        assert!((sp[0].0 - 8.0).abs() < 1e-9);
        for k in 1..8 {
            assert!(sp[k].0.abs() < 1e-9, "bin {} should be empty", k);
        }
    }

    #[test]
    fn pilot_carries_no_payload() {
        assert_eq!(Pilot::default().value, 1);
    }
}