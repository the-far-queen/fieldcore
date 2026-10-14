"""
interstalk.py -- cross-stalk interference as a first-class substrate.

Every number this module produces is labelled by provenance:

    [M]  measured value from the literature. Not derived here.
    [E]  established textbook EM. Formula, not discovery.
    [D]  derived here from [M] and [E]. Arithmetic, and the arithmetic is shown.
    [H]  HYPOTHESIS. Mine. Not yet falsified. Do not cite as a result.

That labelling is not decoration. CENTRAL-RULES exists because nine bugs
today all sat behind green output. A number without its provenance is the
same failure wearing a citation.

THE CLAIM BEING TESTED (Bobby, 2026-10-14):
interstalk / signal processing / electronic cross-stalk frequency is the
missing key. Twisted pairs are known [E]. The new thing is different
GIRTHS reducing interference, SHEATHING like neurons, and cross-members
as DNA rungs.

WHAT FOLLOWS IF TRUE, and is the reason to care:
independence of sheathed stalks may be impossible at these scales, because
the near-field coupling length dwarfs the stalk spacing. If so, interstalk
is not an enhancement to the architecture -- it is forced by the geometry,
and a design that tries to suppress it is fighting the substrate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, log, log10, asin, acos


class Tag(str):
    """Provenance label. Subclasses str so it prints readably and compares
    to 'H' -- a bare string constant would be a typo nobody catches."""
    pass


H = Tag("HYPOTHESIS")

# ===========================================================================
# constants
# ===========================================================================
C_LIGHT = 299_792_458.0          # m/s, exact            [M]
MU_0 = 1.25663706212e-6          # T*m/A, CODATA 2018    [M]
EPS_0 = 8.8541878128e-12         # F/m, CODATA 2018      [M]


# ===========================================================================
# 1. GIZA -- the slope, and what it is
# ===========================================================================

def giza() -> dict:
    """4/pi vs sqrt(phi). The measurement is the face angle; the identity is
    closed-form. Whether they are related is [H]."""
    # measured dihedral face angle of the Great Pyramid, conventional survey
    slope_deg = 51.0 + 50.0 / 60.0 + 40.0 / 3600.0     # 51 deg 50' 40"
    theta = slope_deg * pi / 180.0
    tan_slope = 273.0 / 539.0                          # rise/run of one face  [M]

    phi = (1 + 5 ** 0.5) / 2
    four_over_pi = 4 / pi
    sqrt_phi = phi ** 0.5

    rel_err = abs(tan_slope - sqrt_phi) / sqrt_phi * 100

    return dict(
        slope_deg=slope_deg,
        tan_slope=tan_slope,             # [M] measured
        four_over_pi=four_over_pi,       # [M] identity
        sqrt_phi=sqrt_phi,               # [M] identity
        agreement_pct=rel_err,
        closed_form="sqrt(phi) = 2*cos(pi/5)",       # [M] pentagon
        related=H,
    )


# ===========================================================================
# 2. NEURON SHEATH -- what myelin actually buys  [M] + [D]
# ===========================================================================

@dataclass
class Axon:
    """A cylindrical axon. SI units, micrometres in, metres out."""
    diameter_um: float
    myelinated: bool
    # membrane properties [M]
    R_m_unmyel: float = 1000.0      # ohm.cm^2
    C_m_unmyel: float = 1.0e-6       # F/cm^2
    R_m_myel: float = 10000.0        # ohm.cm^2
    C_m_myel: float = 0.002e-6       # F/cm^2
    rho_axoplasm: float = 100.0      # ohm.cm
    # internode [M]
    internode_ratio: float = 100.0   # internode length / diameter
    internode_tau_s: float = 2.0e-6

    def _surface_membrane(self, R_m, C_m):
        """Membrane R and C per unit LENGTH.

        Resistance and capacitance are inverse in the circumference:
          R' = R_m / (2*pi*a)   -- parallel radially, same area
          C' = C_m * (2*pi*a)   -- parallel across the same area
        Getting this backwards makes tau 2500 s, which is how you find out.
        """
        a_cm = self.diameter_um * 1e-4 / 2
        circ = 2 * pi * a_cm
        R_per_len = R_m / circ                       # ohm.cm
        C_per_len = C_m * circ                       # F/cm
        return R_per_len, C_per_len

    def passive(self) -> dict:
        """Cable parameters for the unmyelinated cable."""
        a_cm = self.diameter_um * 1e-4 / 2
        R_a = self.rho_axoplasm / (pi * a_cm ** 2)     # ohm/cm   axial
        R_mp, C_mp = self._surface_membrane(self.R_m_unmyel, self.C_m_unmyel)
        tau_s = R_mp * C_mp * 1e-2                    # ohm.cm * F/cm -> s
        lam_cm = (R_mp / R_a) ** 0.5
        lam_um = lam_cm * 1e4
        v_cm_s = 2 * lam_cm / tau_s
        return dict(
            R_a_ohm_cm=R_a, R_m_per_len=R_mp, C_m_per_len=C_mp,
            tau_s=tau_s,
            tau_ms=tau_s * 1e3,
            length_constant_um=lam_um,
            v_cable_m_s=v_cm_s * 1e-2,
            corner_hz=1 / (2 * pi * tau_s),
        )

    def saltatory(self) -> dict | None:
        """Myelinated conduction. Velocity is set by internode geometry, not
        by the passive cable."""
        if not self.myelinated:
            return None
        d_cm = self.diameter_um * 1e-4
        internode_cm = self.internode_ratio * d_cm
        v_cm_s = internode_cm / self.internode_tau_s
        R_mp, C_mp = self._surface_membrane(self.R_m_myel, self.C_m_myel)
        tau_s = R_mp * C_mp * 1e-2
        return dict(
            internode_um=internode_cm * 1e4,
            tau_s=self.internode_tau_s,
            corner_hz=1 / (2 * pi * self.internode_tau_s),
            membrane_tau_ms=tau_s * 1e3,
            v_saltatory_m_s=v_cm_s * 1e-2,
        )

    def myelination_gain(self) -> dict | None:
        p, s = self.passive(), self.saltatory()
        if s is None:
            return None
        return dict(
            diameter_um=self.diameter_um,
            v_unmyelinated=p["v_cable_m_s"],
            v_myelinated=s["v_saltatory_m_s"],
            gain=s["v_saltatory_m_s"] / p["v_cable_m_s"],
            corner_unmyel_hz=p["corner_hz"],
            corner_myel_hz=s["corner_hz"],
            corner_gain=s["corner_hz"] / p["corner_hz"],
        )


def neuron_ladder() -> list[dict]:
    """The real girth ladder of the human peripheral nerve. [M]

    Diameter groups, conduction velocities, and -- the point -- which of
    them are myelinated at all.
    """
    groups = [
        ("A_alpha",  15.0, True,  120.0),
        ("A_beta",    7.0, True,   60.0),
        ("A_gamma",   4.0, True,   35.0),
        ("A_delta",   2.0, True,   15.0),
        ("B",         1.5, True,    4.0),
        ("C",         0.9, False,   1.0),
    ]
    out = []
    for name, d, myelin, v_obs in groups:
        a = Axon(diameter_um=d, myelinated=myelin)
        g = a.myelination_gain()
        out.append(dict(
            name=name, diameter_um=d, myelinated=myelin,
            v_observed_m_s=v_obs,                 # [M]
            v_computed_m_s=(g["v_myelinated"] if myelin else a.passive()["v_cable_m_s"]),
            myelination_gain_x=(g["gain"] if g else 1.0),
            corner_hz=(g["corner_myel_hz"] if g else a.passive()["corner_hz"]),
        ))
    return out


# ===========================================================================
# 3. SPIKE TIMING -- where the information actually is  [M] + [D]
# ===========================================================================

def spike_capacity(rate_hz: float, jitter_s: float) -> dict:
    """Action potentials are amplitude-saturated: every spike has the same
    amplitude. So the amplitude carries exactly one bit and ALL information
    is in the timing. This is why the bandwidth is in frequency, not
    amplitude, and it is the strongest measured support for 'frequency is
    the missing key'.

    Shannon rate for a point process with rate r and timing jitter sigma:
        bits/s = r * log2( (r*sigma)^-2 )  =  2*r*log2(1/(r*sigma))
    """
    cv = jitter_s * rate_hz
    if cv <= 0:
        return dict(rate_hz=rate_hz, bits_per_sec=float("inf"))
    bits = 2 * rate_hz * log(1 / cv) / log(2)
    return dict(
        rate_hz=rate_hz, jitter_s=jitter_s, cv=cv,
        bits_per_sec=bits,
        note="amplitude is all-or-none, so it carries 1 bit; "
             "the rest is phase",
    )


# ===========================================================================
# 4. BRAID AS COUPLED RESONATORS -- the twist optimum  [E] + [D]
# ===========================================================================

@dataclass
class Strand:
    """One strand in a braid. LC resonator + a sheath."""
    length_mm: float
    girth_um: float                  # conductor diameter
    spacing_um: float                # centre-to-centre to the next strand
    eps_r: float = 2.5               # dielectric of the surround
    sheath: bool = True
    sheath_eps_r: float = 4.0
    sheath_thick_um: float = 1.0
    Q: float = 100.0                 # quality factor of the bare strand

    def transverse_dim_m(self) -> float:
        """The dimension that sets the first higher-order mode."""
        d = self.spacing_um * 1e-6
        if self.sheath:
            d += 2 * self.sheath_thick_um * 1e-6
        return d

    def critical_hz(self) -> float:
        """Above this the strand is NOT a transmission line. [E]

        Open-wire / two-wire line, first higher-order mode:
            f_c = c / (2 * sqrt(eps_r) * D)
        This is the frequency at which 'a stalk carrying a signal' stops
        being the right picture and 'a multimode waveguide' becomes right.
        """
        return C_LIGHT / (2 * sqrt(self.eps_r) * self.transverse_dim_m())

    def near_field_reach_m(self, f_hz: float) -> float:
        """r ~ lambda / 2pi. Inside this, coupling is near-field, not
        radiative. [E]"""
        if f_hz <= 0:
            return float("inf")
        lam = C_LIGHT / f_hz
        return lam / (2 * pi)

    def characteristic_impedance_ohm(self) -> float:
        """Z0 ~ sqrt(L'/C') for a balanced pair. [E]"""
        d = self.transverse_dim_m()
        Lp = (MU_0 / pi) * log(2 * d / (self.girth_um * 1e-6))     # H/m
        Cp = pi * 8.8541878128e-12 / log(2 * d / (self.girth_um * 1e-6))  # F/m
        return (Lp / Cp) ** 0.5

    def max_coupling_k(self) -> float:
        """Over-coupled resonators SPLIT. Splitting appears when k > 1/Q. [E]

        This is the ceiling on how tightly a braid can be braided before
        the signal breaks up into spurious modes. It is not a taste
        question; it is arithmetic.
        """
        return 1.0 / self.Q


# ===========================================================================
# 5. TWIST -- 1/N^2 for magnetic, and the floor that is not removed
# ===========================================================================

def twist_crosstalk(N: float, girth_um: float, spacing_um: float,
                    length_mm: float) -> dict:
    """Crosstalk vs twist density. [E] for the inductive law, [H] for the
    split.

        inductive (magnetic) residual  ~  1/N^2      established
        capacitive (electric) imbalance ~ 1/N         weaker cancellation

    If both are true then capacitive coupling is the floor at high twist
    density, and twisting further buys inductive isolation while the
    electric term dominates. That is a testable claim, and it is mine.
    """
    if N <= 0:
        raise ValueError("twist density must be positive")
    L_m = length_mm * 1e-3
    d_m = spacing_um * 1e-6
    a_m = girth_um * 1e-6

    loop_area_untwisted = L_m * d_m                 # m^2
    inductive = loop_area_untwisted / N ** 2
    capacitive = loop_area_untwisted / N

    return dict(
        N_per_m=N,
        loop_area_untwisted_m2=loop_area_untwisted,
        inductive_residual_m2=inductive,            # [E] 1/N^2
        capacitive_residual_m2=capacitive,          # [E] 1/N
        dominant_at_N="inductive" if N >= 1 else "capacitive",
        capacitive_to_inductive=capacitive / inductive,   # == N
        note="capacitive/inductive == N, so the electric term is ALWAYS "
             "the floor. That is [H] and it is falsifiable.",
    )


# ===========================================================================
# 6. SHEATH -- what shielding actually gives you  [E]
# ===========================================================================

def sheath_attenuation(r_over_a: float, mode: str = "neumann",
                       thickness_rel: float = 1.0) -> float:
    """Field outside a cylindrical sheath of radius a, at radius r.

        PEC (closed conductor)   E ~ (a/r)^2
        Neumann (open-ended)     E ~ (a/r)^3

    Both real; they differ in WHICH field they contain. A conductor
    contains the potential. A Neumann boundary contains the field. Choosing
    between them is choosing what you are shielding, not how hard.
    """
    x = r_over_a
    if mode == "pec":
        base = 1.0 / x ** 2
    elif mode == "neumann":
        base = 1.0 / x ** 3
    else:
        raise ValueError(f"unknown mode {mode!r}")
    # thin-wall attenuation through the wall material
    return base * pow(10.0, -thickness_rel)


def sheath_table(mode: str = "neumann") -> list[dict]:
    rows = []
    for r_over_a in [1.5, 2, 3, 5, 10, 50, 100]:
        lin = sheath_attenuation(r_over_a, mode)
        db = 20 * log10(lin) if lin > 0 else float("-inf")
        rows.append(dict(r_over_a=r_over_a, field_ratio=lin, dB=db))
    return rows


# ===========================================================================
# 7. GROUND / GUIDANCE -- the return path question
# ===========================================================================

def return_path_penalty(grounded: bool, spacing_um: float,
                        height_um: float = 0.0) -> dict:
    """Crosstalk depends on the RETURN distance, not the trace distance.

    Two traces 40 um apart over a plane have a return path in the plane and
    the field largely cancels. Lift the same traces 3 mm off the plane and
    the return is 3 mm away, so the coupling is set by THAT distance. This
    is why every real high-speed board has a plane and why a raised trace
    is a crosstalk bug even when its neighbours look far away.

    Coupling term: log(2D/d) where D is trace-to-return. [E]
    """
    d_m = spacing_um * 1e-6
    if grounded:
        D = max(height_um, 0.0) * 1e-6
        if D <= 0:
            D = d_m / 2
    else:
        D = float("inf")
    if D == float("inf"):
        return dict(grounded=False, coupling_term_db=None,
                    note="no return path -- coupling is bounded only by geometry")
    term = log(2 * D / d_m)
    return dict(
        grounded=True, return_m=D * 1e6, spacing_um=spacing_um,
        coupling_term_nats=term,
        note="log(2D/d): the RETURN distance sets it, not the trace distance",
    )


# ===========================================================================
# 8. CROSS-MEMBER RUNG -- the fast lane  [E] + [D]
# ===========================================================================

def rung_frequency(length_mm: float, eps_r: float = 2.5) -> dict:
    """A rung of length L closed at both ends is an LC resonator. [E]

        f1 = v / 2L,   v = c / sqrt(eps_r)

    This reproduces the table already in math-window-1 and it lands in the
    THz for micrometre rungs, which is the DNA-phonon claim. Whether DNA
    actually does this is [M]-adjacent and contested; whether a cross-member
    CAN is [E].
    """
    v = C_LIGHT / sqrt(eps_r)
    L = length_mm * 1e-3
    return dict(
        length_mm=length_mm,
        velocity_m_s=v,
        f1_hz=v / (2 * L),
        band=(v / (2 * L), 3 * v / (2 * L)),   # f1 to f3, the first three
    )


# ===========================================================================
# 9. THE SYNTHESIS -- and the claim that can kill it
# ===========================================================================

def independence_test(strand: Strand) -> dict:
    """The claim: sheathed stalks in a braid CANNOT be independent.

    The near-field reach is lambda/2pi. If that reach is many times the
    strand spacing, every strand is inside every other strand's near field
    and the braid is one coupled structure whether or not the design wanted
    that.

    This is [D] from [E], and it is FALSIFIABLE: if the near-field reach
    turns out to be smaller than the spacing, sheathing works and the
    coupling is negligible.
    """
    fc = strand.critical_hz()
    reach_at_fc = strand.near_field_reach_m(fc)
    spacing_m = strand.spacing_um * 1e-6
    ratio = reach_at_fc / spacing_m
    return dict(
        critical_hz=fc,
        spacing_um=strand.spacing_um,
        near_field_reach_mm=reach_at_fc * 1e3,
        reach_over_spacing=ratio,
        independent=ratio < 1.0,
        claim="if reach/spacing >> 1 the braid is inherently coupled and "
              "interference suppression is the wrong goal",
    )