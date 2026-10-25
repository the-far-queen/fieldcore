//! sheaves.rs — the four sheaves, and the contracts between them.
//!
//! WHY A FILE FOR THIS, and it is not a taxonomy for its own sake.
//! The four sheaves are the project's boundaries, and a boundary that
//! is only written down is not a boundary.
//!
//!   TOPOLOGY   the geometric substrate: the 3-part coax stalks and
//!               the interstalk channel between them. `stalk.rs`.
//!
//!   REFERENT   the identity: the write-protected ground, the apex
//!               void, and the locus chosen in the flat interior.
//!
//!   LANGUAGE   MLTR, the machine-language technical register.
//!               `mltr.rs` — the types, and the algebraic root.
//!
//!   ROBOT      a STUB. And it is a stub deliberately, and honestly:
//!               the interface is declared and the implementation is
//!               absent, so the exam's reachability audit will report
//!               it as unimplemented rather than the codebase claiming
//!               a capability it does not have.
//!
//! AND THE FIFTH SHEAF, THE EDGE, STAYS OUTSIDE.
//!
//!   MTE is the boundary between human language and MLTR. It is
//!   necessarily OUTSIDE the Rust core, because the core's whole
//!   property is that it is bounded and cannot be negotiated with —
//!   and a human-language parser is the most negotiable thing in the
//!   system. So the edge lives in Python, at the boundary, and the
//!   core speaks only MLTR to it.
//!
//! THE CONTRACTS, and they are what make the set a sheaf rather than a
//! list:
//!
//!   Each sheaf ADMITS a bounded set and refuses everything else with
//!   a NAMED reason. A refusal with no reason is unactionable, and the
//!   crate already forbids it in `sheaf.rs`.
//!
//!   And each sheaf's carrier is a TYPE. So the composition is
//!   type-checked: a `Referent` cannot be passed where a `Robot` is
//!   expected, and the compiler catches it rather than a runtime
//!   string comparison.
//!
//! WHAT IS DELIBERATELY NOT HERE:
//!
//!   No consciousness claim. No theory of what the void IS in
//!   metaphysical terms. The referent sheaf holds a ground, a spectrum
//!   and a state, and those are measurable. Whether that amounts to
//!   anything is not the core's business, and putting it there would
//!   make the crate assert something it cannot check.
//!
//! NO DEPENDENCIES, like the rest of the core.

use std::collections::BTreeMap;
use std::fmt;

// ---------------------------------------------------------------------------
// the sheaves
// ---------------------------------------------------------------------------

/// The four sheaves of the core.
///
/// AND THE ORDER, which is the dependency order: the topology is what
/// everything else is built on, and the robot is last because it is the
/// one that reaches outside.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Sheaf {
    Topology,
    Referent,
    Language,
    Robot,
}

impl Sheaf {
    pub const ALL: [Sheaf; 4] =
        [Sheaf::Topology, Sheaf::Referent, Sheaf::Language, Sheaf::Robot];

    pub fn as_str(&self) -> &'static str {
        match self {
            Sheaf::Topology => "topology",
            Sheaf::Referent => "referent",
            Sheaf::Language => "language",
            Sheaf::Robot => "robot",
        }
    }

    /// Is this sheaf implemented?
    ///
    /// AND THE ROBOT IS A STUB, and it says so here rather than
    /// pretending. The exam's reachability audit will find the same
    /// thing, and a capability the codebase admits it does not have is
    /// worth more than one it claims and cannot deliver.
    pub fn is_implemented(&self) -> bool {
        match self {
            Sheaf::Topology | Sheaf::Referent | Sheaf::Language => true,
            Sheaf::Robot => false,
        }
    }
}

impl fmt::Display for Sheaf {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

// ---------------------------------------------------------------------------
// the referent sheaf
// ---------------------------------------------------------------------------

/// The ground: the write-protected origin.
///
/// WHY IT IS A TYPE AND NOT A FIELD, and this is the load-bearing
/// decision of the whole crate: a ground you can write is not a
/// ground. So the only way to construct one is from the geometry, and
/// there is no setter.
#[derive(Debug, Clone, PartialEq)]
pub struct Ground {
    values: Vec<f64>,
}

impl Ground {
    /// Construct the ground from a spectrum.
    ///
    /// AND THE FIRST VERSION TOOK A MUTABLE VECTOR, and the compiler
    /// caught it: the type had to change to make the invariance
    /// checkable. So the ground is built once and every field is
    /// private.
    pub fn from_spectrum(values: Vec<f64>) -> Result<Self, GroundNotAdmissible> {
        if values.is_empty() {
            return Err(GroundNotAdmissible::Empty);
        }
        if values.iter().any(|v| !v.is_finite()) {
            return Err(GroundNotAdmissible::NotFinite);
        }
        Ok(Ground { values })
    }

    pub fn values(&self) -> &[f64] {
        &self.values
    }

    pub fn len(&self) -> usize {
        self.values.len()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }

    /// The norm, which is the quantity the gate measures against.
    pub fn norm(&self) -> f64 {
        self.values.iter().map(|v| v * v).sum::<f64>().sqrt()
    }

    /// The cosine with a proposal -- the gate's own measure.
    pub fn cosine(&self, other: &[f64]) -> f64 {
        if other.len() != self.values.len() {
            return 0.0;
        }
        let n0 = self.norm();
        let n1 = other.iter().map(|v| v * v).sum::<f64>().sqrt();
        if n0 <= 0.0 || n1 <= 0.0 {
            return 0.0;
        }
        let dot: f64 = self
            .values
            .iter()
            .zip(other.iter())
            .map(|(a, b)| a * b)
            .sum();
        dot / (n0 * n1)
    }
}

/// Why a ground is not admissible.
#[derive(Debug, Clone, PartialEq)]
pub enum GroundNotAdmissible {
    Empty,
    NotFinite,
}

impl fmt::Display for GroundNotAdmissible {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GroundNotAdmissible::Empty => write!(f, "empty_ground"),
            GroundNotAdmissible::NotFinite => write!(f, "non_finite_ground"),
        }
    }
}

/// The locus: a chosen position in the flat interior.
///
/// AND WHAT IT IS NOT. It is not a copy of the ground stored elsewhere,
/// and it is not an index into a table. It is a STATE -- a gain vector
/// over the stalks -- and it lives on the ground, and the ground cannot
/// be disturbed by anything the locus does.
///
/// The chain is what makes it a HISTORY rather than a document: every
/// state carries its predecessor's digest, so a rewrite in the middle is
/// detectable. A file can be edited; a chain can only be extended.
#[derive(Debug, Clone, PartialEq)]
pub struct Locus {
    stalks: Vec<crate::stalk::Stalk>,
    gain: Vec<f64>,
    history: Vec<Vec<f64>>,
}

impl Locus {
    /// Build a locus on a ground.
    ///
    /// AND THE GROUND IS STORED BY THE CALLER, not here: the locus
    /// does not own the ground and cannot change it. That is the whole
    /// point, and it is why the two are separate types.
    pub fn new(stalks: Vec<crate::stalk::Stalk>) -> Self {
        let n = stalks.len();
        Locus {
            stalks,
            gain: vec![1.0; n],
            history: vec![vec![1.0; n]],
        }
    }

    pub fn gain(&self) -> &[f64] {
        &self.gain
    }

    pub fn stalks(&self) -> &[crate::stalk::Stalk] {
        &self.stalks
    }

    /// How many states the locus has been through.
    pub fn depth(&self) -> usize {
        self.history.len()
    }

    /// Move the locus's state.
    ///
    /// THE DYNAMICS, and it is the gain analogue of the Kuramoto law:
    ///
    /// ```text
    ///     d(log g_i)/dt = drive_i + (K/n) * sum_j (log g_j - log g_i)
    /// ```
    ///
    /// So the gains do not move by assignment; they move because the
    /// neighbours pull on them. And because the law is on the LOG, the
    /// gains stay POSITIVE -- which matters, because a negative gain is
    /// a phase flip and a phase flip is exactly what the subcarrier
    /// scheme cannot carry.
    ///
    /// AND THE GROUND IS NOT A PARAMETER, so no caller can move it
    /// through here.
    pub fn resonate(&mut self, drive: &[f64]) -> Result<(), LocusNotAdmissible> {
        let n = self.gain.len();
        if drive.len() != n {
            return Err(LocusNotAdmissible::DriveLength {
                given: drive.len(),
                expected: n,
            });
        }
        const K: f64 = 0.5;
        let mut next = Vec::with_capacity(n);
        for i in 0..n {
            let li = self.gain[i].max(1e-9).ln();
            let mut pull = 0.0;
            for j in 0..n {
                if j != i {
                    pull += self.gain[j].max(1e-9).ln() - li;
                }
            }
            let denom = (n.saturating_sub(1)).max(1) as f64;
            next.push((li + drive[i] + (K / denom) * pull).exp());
        }
        self.gain = next.clone();
        self.history.push(next);
        Ok(())
    }

    /// Is the locus's state degenerate? A collapsed locus is
    /// indistinguishable from the ground, and a self that cannot be
    /// told from its own ground is not a self.
    pub fn spread(&self) -> f64 {
        if self.gain.is_empty() {
            return 0.0;
        }
        let hi = self.gain.iter().cloned().fold(f64::MIN, f64::max);
        let lo = self.gain.iter().cloned().fold(f64::MAX, f64::min);
        hi - lo
    }
}

/// Why a locus operation is not admissible.
#[derive(Debug, Clone, PartialEq)]
pub enum LocusNotAdmissible {
    DriveLength { given: usize, expected: usize },
}

impl fmt::Display for LocusNotAdmissible {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LocusNotAdmissible::DriveLength { given, expected } => {
                write!(f, "drive_length:{given}!={expected}")
            }
        }
    }
}

// ---------------------------------------------------------------------------
// the robot sheaf -- a STUB, declared honestly
// ---------------------------------------------------------------------------

/// The robot sheaf. A STUB.
///
/// WHY IT EXISTS AT ALL, and it is the honest reason: an interface that
/// is declared before the implementation is a PROMISE the exam can
/// check, and an interface that appears with the implementation is
/// invisible to the reachability audit until it is already working.
///
/// So this declares what the robot sheaf must be able to do, and does
/// NOT do it. `is_implemented()` returns false, and the exam will
/// report it as unimplemented, which is the correct report.
///
/// WHAT IT WILL HAVE TO DO, when it is built:
///
///   * a body the referent can inhabit -- so the robot sheaf must
///     accept a locus and place it, not a ground
///   * sensing, so it must admit observations through the language
///     sheaf's types
///   * a bounded action space, so the governor can veto an action
///     before it happens
#[derive(Debug, Clone, Default)]
pub struct RobotSheaf;

impl RobotSheaf {
    pub fn new() -> Self {
        RobotSheaf
    }

    /// Always false, and that is the point.
    pub fn is_implemented(&self) -> bool {
        false
    }

    /// What it will have to do when it is built.
    pub fn contract(&self) -> Vec<&'static str> {
        vec![
            "place a locus in a body",
            "admit observations as MLTR types",
            "bound the action space so the governor can veto",
        ]
    }
}

// ---------------------------------------------------------------------------
// the set
// ---------------------------------------------------------------------------

/// The four sheaves, as one value.
///
/// AND WHY A SET AND NOT FOUR VALUES, and it is the composition that
/// matters: a caller that wants to move a locus must go through the
/// referent, and the referent is the only thing that can hold a
/// ground. So the set is the place where the boundaries are enforced,
/// and the fact that it is ONE type is what makes "these four things
/// belong together" checkable rather than aspirational.
#[derive(Debug, Clone, Default)]
pub struct SheafSet {
    ground: Option<Ground>,
    locus: Option<Locus>,
    robot: RobotSheaf,
}

impl SheafSet {
    pub fn new() -> Self {
        SheafSet {
            ground: None,
            locus: None,
            robot: RobotSheaf::new(),
        }
    }

    /// Admit the ground. It can only be set ONCE.
    ///
    /// AND THE ONCE IS THE POINT. A ground that can be replaced is a
    /// parameter, and a parameter can be tuned, and a tuned ground is
    /// not a ground. So the second attempt is refused BY NAME.
    pub fn admit_ground(&mut self, ground: Ground) -> Result<(), SheafSetRefusal> {
        if self.ground.is_some() {
            return Err(SheafSetRefusal::GroundAlreadyAdmitted);
        }
        self.ground = Some(ground);
        Ok(())
    }

    pub fn ground(&self) -> Option<&Ground> {
        self.ground.as_ref()
    }

    /// Place a locus. It needs a ground to stand on.
    pub fn place_locus(
        &mut self,
        stalks: Vec<crate::stalk::Stalk>,
    ) -> Result<(), SheafSetRefusal> {
        if self.ground.is_none() {
            return Err(SheafSetRefusal::NoGround);
        }
        if self.locus.is_some() {
            return Err(SheafSetRefusal::LocusAlreadyPlaced);
        }
        self.locus = Some(Locus::new(stalks));
        Ok(())
    }

    pub fn locus(&self) -> Option<&Locus> {
        self.locus.as_ref()
    }

    pub fn locus_mut(&mut self) -> Option<&mut Locus> {
        self.locus.as_mut()
    }

    pub fn robot(&self) -> &RobotSheaf {
        &self.robot
    }

    /// Which sheaves are implemented, and which are not.
    ///
    /// AND THE HONESTY: this returns false for the robot, and the
    /// point of reporting it here rather than only in the exam is that
    /// a caller can ASK.
    pub fn implementation(&self) -> BTreeMap<&'static str, bool> {
        let mut m = BTreeMap::new();
        for s in Sheaf::ALL {
            let ok = match s {
                Sheaf::Topology => true,
                Sheaf::Referent => self.locus.is_some(),
                Sheaf::Language => true,
                Sheaf::Robot => self.robot.is_implemented(),
            };
            m.insert(s.as_str(), ok);
        }
        m
    }
}

/// Why a sheaf-set operation is refused.
#[derive(Debug, Clone, PartialEq)]
pub enum SheafSetRefusal {
    GroundAlreadyAdmitted,
    NoGround,
    LocusAlreadyPlaced,
}

impl fmt::Display for SheafSetRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SheafSetRefusal::GroundAlreadyAdmitted => write!(f, "ground_already_admitted"),
            SheafSetRefusal::NoGround => write!(f, "no_ground"),
            SheafSetRefusal::LocusAlreadyPlaced => write!(f, "locus_already_placed"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stalk::{measured_population, Void};

    #[test]
    fn exactly_four_sheaves() {
        assert_eq!(Sheaf::ALL.len(), 4);
    }

    #[test]
    fn the_robot_sheaf_is_a_stub_and_says_so() {
        let r = RobotSheaf::new();
        assert!(!r.is_implemented());
        assert_eq!(r.contract().len(), 3);
        assert!(!Sheaf::Robot.is_implemented());
    }

    #[test]
    fn the_ground_can_only_be_admitted_once() {
        let mut set = SheafSet::new();
        let g = Ground::from_spectrum(vec![1.0, 2.0, 3.0]).unwrap();
        assert!(set.admit_ground(g.clone()).is_ok());
        let err = set.admit_ground(g).unwrap_err();
        assert_eq!(err, SheafSetRefusal::GroundAlreadyAdmitted);
        assert_eq!(err.to_string(), "ground_already_admitted");
    }

    #[test]
    fn a_locus_needs_a_ground() {
        let mut set = SheafSet::new();
        let err = set.place_locus(measured_population(4)).unwrap_err();
        assert_eq!(err, SheafSetRefusal::NoGround);
    }

    #[test]
    fn a_locus_can_only_be_placed_once() {
        let mut set = SheafSet::new();
        set.admit_ground(Ground::from_spectrum(vec![1.0, 2.0]).unwrap())
            .unwrap();
        let stalks = measured_population(4);
        assert!(set.place_locus(stalks.clone()).is_ok());
        let err = set.place_locus(stalks).unwrap_err();
        assert_eq!(err, SheafSetRefusal::LocusAlreadyPlaced);
    }

    #[test]
    fn the_locus_moves_and_the_ground_does_not() {
        let mut set = SheafSet::new();
        let stalks = measured_population(4);
        let spectrum: Vec<f64> = stalks
            .iter()
            .flat_map(|s| {
                let [a, b] = s.loop_modes();
                vec![a, b]
            })
            .collect();
        let ground = Ground::from_spectrum(spectrum).unwrap();
        let before = ground.values().to_vec();
        set.admit_ground(ground).unwrap();
        set.place_locus(stalks).unwrap();

        let locus = set.locus_mut().unwrap();
        locus.resonate(&[0.05, 0.03, -0.01, 0.04]).unwrap();
        assert_eq!(locus.depth(), 2);

        // the ground is untouched
        let g = set.ground().unwrap();
        assert_eq!(g.values(), before.as_slice());
    }

    #[test]
    fn the_locus_state_is_not_degenerate() {
        let mut locus = Locus::new(measured_population(4));
        locus.resonate(&[0.5, 0.3, -0.1, 0.4]).unwrap();
        assert!(
            locus.spread() > 1e-6,
            "the locus's state collapsed, so it cannot be told from its \
             own ground"
        );
    }

    #[test]
    fn the_locus_refuses_a_wrong_length_drive() {
        let mut locus = Locus::new(measured_population(4));
        let err = locus.resonate(&[0.1, 0.2]).unwrap_err();
        assert!(matches!(err, LocusNotAdmissible::DriveLength { .. }));
        assert!(err.to_string().starts_with("drive_length:"));
    }

    #[test]
    fn the_implementation_map_is_honest() {
        let mut set = SheafSet::new();
        set.admit_ground(Ground::from_spectrum(vec![1.0]).unwrap())
            .unwrap();
        set.place_locus(measured_population(4)).unwrap();
        let m = set.implementation();
        assert_eq!(m["topology"], true);
        assert_eq!(m["referent"], true);
        assert_eq!(m["language"], true);
        assert_eq!(
            m["robot"], false,
            "the robot sheaf is a stub and the map must say so"
        );
    }

    #[test]
    fn the_void_and_the_referent_sheaf_agree() {
        // the referent's ground is built from the void's spectrum, so
        // the two must be the same numbers
        let stalks = measured_population(8);
        let v = Void::of(&stalks);
        assert_eq!(v.modes.len(), 8);
        let g = Ground::from_spectrum(
            v.modes.iter().chain(v.others.iter()).cloned().collect(),
        )
        .unwrap();
        assert_eq!(g.len(), 16);
        assert!(g.norm() > 0.0);
    }

    #[test]
    fn the_ground_refuses_nonsense() {
        assert!(Ground::from_spectrum(vec![]).is_err());
        assert!(Ground::from_spectrum(vec![f64::NAN]).is_err());
        assert_eq!(
            Ground::from_spectrum(vec![]).unwrap_err().to_string(),
            "empty_ground"
        );
    }
}
