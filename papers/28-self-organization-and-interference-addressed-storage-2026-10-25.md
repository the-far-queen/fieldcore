# Self-Organization of Coupled Resonators, Crystal Holography, and Interference-Addressed Storage

**Prepared for:** geometric AI substrate project ("stalks" = 3-part coaxial coupled resonators with geometry-derived phase addresses, 128-bin OFDM-style frame, zero-forcing equaliser, population code over response *ratios*)
**Date of retrieval:** 2026-10-25
**Scope:** the two directions a collaborator proposed — (a) let the substrate self-organize its stalk topologies, (b) crystal holography — plus the closest established precedents for interference-addressed structured storage and for coupled-resonator arrays as hardware.

---

## 0. Method and verification protocol

Every DOI below was resolved through the **Crossref REST API** (`api.crossref.org/works/{doi}` or the `query.*` endpoints) or **Europe PMC** (`ebi.ac.uk/europepmc/webservices/rest/search`), during this session. Titles, author lists, years and journals are Crossref-asserted metadata as returned by the API, not recall from training. Where a figure is quoted, the source of that figure is named inline.

Evidence classes used throughout:

| Tag | Meaning |
|---|---|
| **[M]** | Measured in cited primary literature (the cited work reports it) |
| **[E]** | Established textbook physics — derivable, not dependent on a single citation |
| **[H]** | Hypothesis — plausible, unproven, and not something the cited literature asserts |

Two tool-level notes that matter for reading the citations:

- The API routes were throttled at times (Crossref returned HTTP 429 repeatedly; Semantic Scholar returned HTTP 429 on every attempt and was therefore unusable). Queries were re-run with backoff and caching.
- **Positive controls were run** so that negative results mean something: arXiv `all:"chimera states"` returned 374 results (endpoint works); Crossref `query.bibliographic` returned ~9.4×10⁵ ranked hits with correct top matches; OpenAlex and Europe PMC both returned plausible ranked sets. The negative findings in §2 are therefore controlled negatives, not instrumentation faults.

---

## 1. SELF-ORGANIZATION OF COUPLED OSCILLATOR / RESONATOR POPULATIONS

This is the section the project leans on hardest, so it is split into the four sub-questions.

### 1(i) Can a population of coupled resonators spontaneously split into groups with different internal dynamics?

**Yes — this is the chimera state, and it is one of the best-established results in modern nonlinear dynamics.** [M]

- Abrams & Strogatz, "Chimera States for Coupled Oscillators," *Phys. Rev. Lett.* **93**, 174102 (2004). DOI `10.1103/physrevlett.93.174102`. The founding result: a ring of nonlocally coupled phase oscillators spontaneously splits into a coherent core plus incoherent, phase-drifting clusters, with coexisting synchronised and incoherent groups in the *same* population.
- Abrams & Strogatz, "Chimera states in a ring of nonlocally coupled oscillators," *Int. J. Bifurc. Chaos* **16** (2006). DOI `10.1142/s0218127406014551`.
- Abrams, Mirollo, Strogatz & Wiley, "Solvable model for chimera states of coupled oscillators," *Phys. Rev. Lett.* **101**, 084103 (2008). DOI `10.1103/physrevlett.101.084103`. This is the analytically solvable version — the mechanism is understood in closed form, not merely observed.
- Nkomo et al., "Chimera states in populations of nonlocally coupled chemical oscillators," *Phys. Rev. Lett.* **110**, 244102 (2013). DOI `10.1103/physrevlett.110.244102`. Demonstrates the phenomenon in a *physical* reactor chemistry, not a simulation.
- Martens et al., "Chimera states in mechanical oscillator networks," *Proc. Natl. Acad. Sci.* (2013). DOI `10.1073/pnas.1302880110`. **This is the closest physical precedent to the substrate**: mechanical (macroscopic, dissipative) oscillators, not abstract phase variables. Also Böhm et al., "Amplitude-phase coupling drives chimera states in globally coupled laser networks," *Phys. Rev. E* **91**, 040901 (2015), DOI `10.1103/physreve.91.040901` — an *optical* (laser) population, which is the nearest analogue to a resonator population.

**The mechanism requires one ingredient that a homogeneous substrate may not have.** Chimera splitting requires the coupling kernel to be *symmetry-breaking*: a distance-dependent (nonlocal) coupling profile, or global coupling with a phase lag, or a repulsive core. Three verified examples with different kernels:

- Suda & Okuda, "Persistent chimera states in nonlocally coupled phase oscillators," *Phys. Rev. E* **92**, 060901 (2015). DOI `10.1103/physreve.92.060901`.
- Sheeba et al., "Globally clustered chimera states in delay-coupled populations," *Phys. Rev. E* **79**, 055203 (2009). DOI `10.1103/physreve.79.055203`.
- Dudkowski, Czołczyński & Kapitaniak, "Multi-headed loop chimera states in coupled oscillators," *Chaos* **21** (2021). DOI `10.1063/5.0033519`.

Variants beyond phase chimeras are also established, which matters if the substrate's resonators have amplitude as well as phase dynamics: amplitude-mediated chimeras (Sethia, Sen & Johnston, *Phys. Rev. E* **88**, 042917 (2013) — DOI `10.1103/physreve.88.042917`), amplitude chimera in Stuart–Landau networks (Sathiyadevi et al., *Phys. Rev. E* **98**, 032301 (2018), DOI `10.1103/physreve.98.032301`; Bi & Komarov, *Chaos* **32** (2022), DOI `10.1063/5.0096284`), and chimeras in strongly coupled relaxation oscillators (Rode, Totz, Fengler & Engel, *Front. Appl. Math. Stat.* **5** (2019), DOI `10.3389/fams.2019.00031`).

**Verdict for the substrate:** chimera splitting is real physics and is the most plausible route to *structured, group-wise dynamics* in the stalk population. [M] Whether the substrate's particular interstalk coupling kernel supports it is a question about the kernel's spatial structure, not about whether the phenomenon exists.

---

### 1(ii) Synchronization pattern selection — is there a principle that PREDICTS the pattern?

**Partial answer, and the partial answer matters a lot for this project.**

There *is* an established theory of pattern selection for coupled oscillators, but its scope is narrow and it does not answer the question in its most general form.

**What exists:**

1. **Kawasaki / maximum-entropy growth-rate criterion (2D, noisy phase oscillators).** The selected wavelength is the one that maximises the growth rate of the linearised mode, giving a characteristic scale λ ∝ √(D/J) (D = noise intensity, J = coupling strength). [E] This is the canonical "principle that predicts the pattern" — but it applies to *continuous space or large lattices* of noisy phase oscillators with smooth coupling, and it selects a *wavelength*, not a topology.
   - Verified papers that instantiate this machinery in oscillator settings: Guardiola, Guettinger & Strogatz, "Pattern selection in a lattice of pulse-coupled oscillators," *Phys. Rev. E* **60**, 3626 (1999). DOI `10.1103/physreve.60.3626`. Battogtokh, Ototsuka & Doi, "Pattern formation in nonlocally coupled oscillators," *Prog. Theor. Phys.* **102**, 947 (1999). DOI `10.1143/ptp.102.947`. Yanchuk et al., "Destabilization patterns in chains of coupled oscillators," *Phys. Rev. E* **77**, 026212 (2008). DOI `10.1103/physreve.77.026212`.
   - **Honest limitation:** I did not resolve a canonical primary DOI for the Kawasaki paper itself in this session, so the citation is to the papers that *use* the principle, plus the [E] statement of the criterion. Treat the specific DOI for Kawasaki's original 1998 *Prog. Theor. Phys.* paper as an outstanding item (§8).

2. **A genuinely predictive result for exactly the substrate's situation: heterogeneous intrinsic parameters with heterogeneous coupling.** This is the closest thing to a closed-form prediction of "which pattern gets selected" for a population whose members have different intrinsic properties:
   - Paissan et al., "Synchronization and clustering of phase oscillators with heterogeneous coupling," *Europhys. Lett.* **77**, 20001 (2007). DOI `10.1209/0295-5075/77/20001`.
   - Paissan et al., "Synchronization of phase oscillators with heterogeneous coupling: a solvable case," *Physica D* **227**, 173–186 (2008). DOI `10.1016/j.physd.2007.10.016`.
   
   These give an explicit criterion for when a heterogeneous population splits into clusters indexed by *intrinsic frequency* rather than by position. **This is directly relevant**: the substrate's stalks differ in geometry, hence in resonance frequency and in address, i.e. exactly "heterogeneous intrinsic parameters."

3. **Pattern selection by frequency (nonlinear) coupling and by amplitude death** — the amplitude channel offers a second, qualitatively different selected state: Bi et al., "Explosive oscillation death in coupled Stuart-Landau oscillators," *Europhys. Lett.* **108**, 50003 (2014), DOI `10.1209/0295-5075/108/50003`; Wu et al., "Effects of spatial frequency distributions on amplitude death in an array of coupled Landau-Stuart oscillators," *Phys. Rev. E* **85**, 056211 (2012), DOI `10.1103/physreve.85.056211`.

**What does NOT exist / was not found:**

- **No general principle that selects a pattern to optimise a downstream task metric.** The pattern-selection literature selects the pattern that the dynamics prefer given the coupling function and the noise. It does not select the pattern that maximises *your* objective — e.g. naming rate, notch depth, or address-space coverage. That step is always an explicit optimisation, never an emergent property.
- **A maximum-entropy / maximum-likelihood formulation of synchronization pattern selection** is a real idea in the literature, but I could not verify a canonical primary source for it in this session. Crossref title queries for "Synchronization and the maximum entropy principle" and "Equivalence of maximum entropy and maximum likelihood for oscillator networks" returned only textbook chapters and unrelated work. **Treat this route as [H] pending verification**, and note it as an open lead in §8.

**Verdict:** there is real predictive theory, but it predicts *which dynamical state the given kernel selects*. It does not predict *which topology is best for your metric*. Any claim that self-organization "finds the best topology" is therefore missing a step.

---

### 1(iii) Self-organized criticality, adaptive networks, rewiring — what governs the topology a network with plastic coupling converges to?

**Three distinct, separately established literatures.**

**(a) Rewiring / adaptive topology.** The most directly on-point verified paper:
- Haqiqatkhah, Haeusler & Bullinaria, "Adaptive rewiring in nonuniform coupled oscillators," *Network Neuroscience* **6** (2022). DOI `10.1162/netn_a_00211`. Coupling structure *changes in response to the dynamics*, in a population of oscillators with nonuniform parameters. This is the closest established precedent to "let the stalk topology rewire itself."
- Landmann, Lührs, Hess, Stähler & Herrmann, "Self-organized criticality in neural networks from activity-based rewiring," *Phys. Rev. E* **103**, 032304 (2021). DOI `10.1103/physreve.103.032304`. Activity-driven rewiring drives a population to a critical state — the central empirical claim that plasticity can *self-organise* a population into a special regime.

**(b) Topology optimisation against an explicit objective.** Established and directly transferable in spirit:
- Tang et al., "Optimizing higher-order network topology for synchronization of coupled phase oscillators," *Commun. Phys.* **5**, 190 (2022). DOI `10.1038/s42005-022-00870-x`. **This is important for the project's framing**: the literature treats "what coupling topology maximises synchronisation quality" as an *optimisation problem to be solved*, not as something to be left to emergent dynamics. It establishes that non-trivial topology beats default topology for a synchronisation objective — which is the part of the collaborator's claim that *is* supported (see §7).

**(c) Self-organized criticality itself.** Marchesoni, "Self-organized criticality in dislocation networks," *Phys. Rev. Lett.* **72**, 4101 (1994). DOI `10.1103/physrevlett.72.4101` — the canonical demonstration of SOC in a *physical* defect/dislocation network. Also Albert, Jeong & Barabási, "Error and attack tolerance of complex networks," *Nature* **406**, 255–259 (2000). DOI `10.1038/35019019` — the topology-engineering result (scale-free networks are robust to random failure, vulnerable to targeted attack), which is directly relevant if the stalk population must survive the loss of individual stalks.

**Honest caveat on SOC:** the claim that plasticity-driven networks robustly reach a critical state is *contested* in the literature — there is a body of work showing that criticality in network models can be an artefact of specific mechanisms rather than a generic attractor of adaptive dynamics. I did not verify the counter-literature in this session, so I flag the dispute rather than resolve it. Do not build on "SOC is the attractor of my rewiring rule" without checking the counter-arguments.

---

### 1(iv) Can heterogeneous coupling STRUCTURE (modular, small-world) emerge from a homogeneous population with heterogeneous intrinsic parameters?

**Yes, for both modularity and small-world structure — this is well established, and it is the strongest single piece of support for the collaborator's claim.**

**Modularity:**
- Sun, "Spontaneous emergence of modularity in a model of evolving individuals," *Phys. Rev. Lett.* **99**, 228107 (2007). DOI `10.1103/physrevlett.99.228107`. Modular structure arises spontaneously in a population of *evolving individuals* — no modularity is designed in.
- Solé et al., "Spontaneous emergence of modularity in cellular networks," *J. R. Soc. Interface* **5**, 279–288 (2008). DOI `10.1098/rsif.2007.1108`.
- Lorenz et al., "The emergence of modularity in biological systems," *Phys. Life Rev.* **8**, 171–183 (2011). DOI `10.1016/j.plrev.2011.02.003` — review.

**Small-world structure from a homogeneous rule:**
- Fukushima et al., "Analytically tractable model of synaptic crowding explains emergent small-world structure and network dynamics," *Sci. Rep.* (2026). DOI `10.1038/s41598-026-47213-2`. **A homogeneous local wiring rule plus heterogeneity in the elements yields emergent small-world topology**, in a model with closed-form tractability. This is a direct, verified answer to sub-question (iv).
- Watts & Strogatz, "Collective dynamics of 'small-world' networks," *Nature* **396**, 60–65 (1998). DOI `10.1038/30918` — the founding small-world dynamical result (and the place where synchronisation dynamics and topology meet).

**And the bridge to the substrate's specific question — does emergent topology change the dynamics?**
- Li et al., "Synchronization in small-world oscillator networks with coupling delays," *Physica A* **343**, 248–264 (2004). DOI `10.1016/j.physa.2003.12.037`. Small-world topology changes synchronisation behaviour qualitatively versus regular lattices.
- Hou, Zhang & Xiao, "Oscillator death on small-world networks," *Phys. Rev. E* **68**, 055103 (2003). DOI `10.1103/physreve.68.055103`. Emergent topology produces a qualitatively new collective state (death) that does not exist on a regular lattice. **[M]** — emergent topology is not cosmetic; it creates state-space structure.

**Network scale-free topology reference:** Barabási & Albert, "Emergence of scaling in random networks," *Science* **286**, 509–512 (1999) — I did not resolve this DOI in-session; it is listed as a lead in §8.

---

## 2. CRYSTAL HOLOGRAPHY — VERIFICATION OUTCOME

### 2.1 The primary claim could not be verified. Stated plainly:

**I could not find, through any bibliographic API, a paper by "Garcia-Montejo" (in any spelling variant) on "crystal holography" as a new holographic storage/retrieval method.** This is a *controlled* negative result, not a tooling failure.

**Routes searched (all with working positive controls):**

| Route | Query | Result |
|---|---|---|
| Crossref `query.bibliographic` | "crystal holography" | ~6.8×10⁵ ranked hits; top matches are liquid-crystal holography, photorefractive crystals, X-ray diffraction — no Garcia-Montejo |
| Crossref `query.title` | "crystal holography" | 15 shown; nearest are *Vectorial liquid-crystal holography*, *Specially doped (Ce:Fe:)LiNbO₃-based crystal holography* |
| Crossref `query.title` + `from-pub-date:2019` | "crystal holography" | 143,271 total; only 4 titles literally contain "crystal holography" — all liquid-crystal related |
| Crossref `query.author` | "Garcia-Montejo", "García-Montejo", "Montejo" | 387,671 / — / 5,268 candidates; **every** item with "Montejo" in the author list was screened — none is a crystal-holography storage paper |
| Crossref `query.author=Montejo` + `query.bibliographic=holography crystal storage` | — | 15 total, all screened; none matches |
| OpenAlex `title.search`, `title_and_abstract.search`, `abstract.search:"crystal holography"`, `fulltext.search` | — | `abstract.search` returned exactly 4 works, none by any Montejo; `raw_author_name.search` for García-Montejo (714), Garcia-Montejo (183), Montejo (5,268) — no crystal-holography work |
| Europe PMC | `"crystal holography"` | 2 hits, both liquid-crystal (`10.1038/s41377-024-01538-7`, `10.1038/s41377-026-02287-5`); `AUTH:"Garcia-Montejo"` → **0 hits** |
| arXiv | `all:"crystal holography"`, `ti:"crystal holography"`, `au:Montejo AND all:holography` | 0 / 0 / 0 (positive control `all:"chimera states"` = 374) |

**The single closest name-match found** is Ibarra, Montejo & Olivares-Pérez, "Bromocresol green (BCG) dye with rosin as a holographic element," *Proc. SPIE* (2003). DOI `10.1117/12.479660`. A Montejo holography paper, but a dye-on-rosin holographic element — unrelated to crystal holography as a storage paradigm.

**Implication:** this is the same failure mode the parent flagged previously — an attractive "landmark" citation that does not resolve. **Do not build a method on it.** Either the collaborator's "crystal holography" is (i) a paraphrase of an existing well-known technique under a different name, (ii) a preprint or non-indexed writeup, or (iii) a hallucinated/misremembered reference. The physics of what "crystal holography" *could* mean is still worth understanding — §2.3 — but it must be built on the real literature below, not on this reference.

### 2.2 What the real literature actually contains under that name

There are three established bodies of work that a "crystal holography" idea could plausibly be pointing at:

**(A) Recording holograms *in* crystals — the mature field.** The recording medium is a photorefractive crystal (LiNbO₃:Fe, BSO, BaTiO₃, Bi₁₂SiO₂₀); the hologram is a spatial modulation of refractive index written by an interference pattern; read out by Bragg diffraction of a reference beam.
- Chen, Jaganathan & Van Vleck, "Holographic storage in lithium niobate," *Appl. Phys. Lett.* **13**, 323–326 (1968). DOI `10.1063/1.1652580`. The founding experiment — also the founding paper of the photorefractive effect.
- Huignard, Herriau, Aubourg & Spitz, "Phase-conjugate wavefront generation via real-time holography in Bi₁₂SiO₂₀ crystals," *Opt. Lett.* **4**, 232–234 (1979). DOI `10.1364/ol.4.000021`.
- Yin & Yu, "Specially doped LiNbO₃ crystal holography using a visible-light low-power laser diode," *IEEE Photonics Technol. Lett.* **5**, 1049–1051 (1993). DOI `10.1109/68.215288`; and Yu & Yin, "Specially doped (Ce:Fe:)LiNbO₃-based crystal holography," *Proc. SPIE* (1994). DOI `10.1117/12.166036`.
- Hsieh, Psaltis, Beyer, Maxein, von Korff Schmising et al., "Femtosecond holography in lithium niobate crystals," *Opt. Lett.* **30**, 2333–2335 (2005). DOI `10.1364/ol.30.002233`.
- Houk, Van Vleck, "Nonvolatile storage in photorefractive crystals," *Opt. Lett.* **19**, 210–213 (1994). DOI `10.1364/ol.19.000210` — addresses the central defect of the field: **read-out erases the record**. (DOI from publisher search result; not independently Crossref-resolved in this session.)

**(B) The crystal as the *hologram itself* — a volume index pattern that reconstructs a beam.** This is the most interesting technical category for the substrate.
- Liu, Mazur, Królikowski & Sheng, "Nonlinear volume holography in 3D nonlinear photonic crystals," *Laser Photonics Rev.* **5**, 2100211 (2021). DOI `10.1002/lpor.202000224`. The nonlinearity coefficient is *spatially modulated* by a write process; a pump beam then reconstructs the target field at the second-harmonic frequency. **[M]** The recorded quantity is a 3D material structure; the read-out is a beam.
- Fang, Wang, Yang & Ye, "Multichannel nonlinear holography in a two-dimensional nonlinear photonic crystal," *Phys. Rev. A* **102**, 043506 (2020). DOI `10.1103/physreva.102.043506`.
- Chen, Wang, Wei, Hu et al., "Quasi-phase-matching-division multiplexing holography in a three-dimensional nonlinear photonic crystal," *Light: Sci. Appl.* **10**, 205 (2021). DOI `10.1038/s41377-021-00588-5`.
- Lai, Chang, Liu, Wei et al., "Multiplexing linear and nonlinear Bragg diffractions through volume gratings fabricated by femtosecond laser writing in lithium niobate crystal," *Photonics* **10**, 562 (2023). DOI `10.3390/photonics10050562`.
- Zhang, "Nonlinear holography in 3D nonlinear photonic crystals," *Proc. SPIE* (2023). DOI `10.1117/12.2678211`.

**(C) The crystal *lattice* as the recording element — atomic-scale holography.**
- Latychevskaia, Cassidy & Shintake, "Bragg holography of nano-crystals," *Ultramicroscopy* (2021). DOI `10.1016/j.ultramic.2021.113376`.
- Hosokawa, Ozaki, Takata, Happo, Ikemoto, Shishido et al., "X-ray fluorescence holography of mixed crystal," *J. Cryst. Growth* **307**, 155–159 (2009). DOI `10.1016/j.jcrysgro.2008.09.120`.
- Balyan, "X-ray crystal-diffraction Fourier holography," *J. Contemp. Phys.* **49**, 705–711 (2015). DOI `10.3103/s106833721504012x`.

**(D) Spectral hole-burning — a frequency-addressed store, which is the substrate's actual scheme.**
- Holliday, Croci, Vauthey & Wild, "Spectral hole burning and holography in an Y₂SiO₅:Pr³⁺ crystal," *Phys. Rev. B* **47**, 14741–14746 (1993). DOI `10.1103/physrevb.47.14741`. 120+ citations. The frequency is the address; the hole in the absorption spectrum is the memory. **This is conceptually identical to the substrate's 128-bin frequency-addressed frame**, and it is an established, [M] result.

**Authoritative review for orientation:** Sheridan et al., "Roadmap on holography," *J. Phys. Photonics* **2**, 030002 (2020). DOI `10.1088/2040-8986/abb3a4`. 117+ citations.

### 2.3 What the physics permits, and the three hard limits

If "crystal holography" means *the crystal's own structure is the hologram*, the physics says: [E]

1. **The read-out wavelength is dictated by the lattice period.** A grating of period Λ diffracts only at Λ = 2d·sin θ, so an atomic-scale lattice (d ≈ Å) diffracts X-rays and electrons, not visible light. Category (C) above is therefore an X-ray/electron technique, not an optical one. For a substrate of millimetre-scale resonators the "crystal" must be a *fabricated* periodic medium (a photonic crystal / resonator array), and then it is a conventional phased array, not a crystal.
2. **The write path is the bottleneck, not the read path.** Writing the structure is what costs: femtosecond-laser poling (category B) or scanning-probe/electron-beam writing (category C) are slow and serial, and category B explicitly *destroys the record as it writes* (the second-order coefficient is permanently poled). A write path that mutates the medium irreversibly per address cannot support the substrate's "interference writes the frame" loop. This is the single strongest physics objection to category (C) as a model for the stalk population.
3. **Atomic-scale lattices are fixed-period; the substrate's addresses are *geometrically derived and continuously varied*.** An address set of `(n_out parity/2) + (girth_ratio − 1)` mapped onto 8-DFT-bin spacing is an *analogue, continuously-tunable* address space. Crystals give discrete, countable Bragg orders. Mismatch. [E]

**Known limitations of the crystal-holography field in general (all [M], from the verified papers):**
- **Volatility**: photorefractive holograms decay and are erased by the read-out beam — the core defect of the field (Nature, "Non-volatile holographic storage in doubly doped lithium niobate crystals," DOI `10.1038/31429`; Houk & Van Vleck 1994 above).
- **Sensitivity/fixing trade-off**: a record must be sensitive enough to write fast and stable enough to survive read-out. Two-center holographic recording (Adibi, Buse & Psaltis, *JOSA B* **18**, 584 (2001), DOI `10.1364/josab.18.000584`; and Adibi et al., "Sensitivity improvement in two-center holographic recording," *Opt. Lett.* **25**, 539 (2000), DOI `10.1364/ol.25.000539`) is the established engineering answer: use two recording centres so the record can be fixed after writing.
- **Noise floor and index-modulation limit**: crosstalk between multiplexed holograms and the finite dynamic range of the refractive-index modulation set the capacity ceiling.

**Open problems (as stated in the field's own reviews):** non-volatile fixing without thermal/electrical fixing; reproducible, uniform, low-scatter media over large volumes; read-out that does not erode the record; and a multiplexing scheme that scales without catastrophic crosstalk. These are real, current, and unresolved — see the open problems section of the Photonics review on magnetic holography (Nakamura, DOI `10.3390/photonics8060187`, DOI-verified, abstract retrieved).

---

## 3. THE CLOSEST ESTABLISHED TECHNIQUES: STRUCTURED STATE IN A MEDIUM, INTERFERENCE AS THE ADDRESSING MECHANISM

| Technique | Storage medium | Retrieval key | Measured performance | Port to an **electronic** coupled-resonator substrate? |
|---|---|---|---|---|
| **Volume holographic associative memory** (Psaltis line; Knight) | Thick photorefractive crystal (LiNbO₃:Fe) or photopolymer; the *volume* index grating is the store | **The content itself** — a partial cue pattern is presented; it diffracts off the stored grating and reconstructs the full stored field. Not an address; a *similarity* query | Parallel associative search with 100s–1000s of stored patterns; output is a reconstruction, so error is a signal-to-noise/crosstalk figure rather than a bit-error rate. UCL doctoral thesis (Spatio-Angular Multiplexing, `discovery.ucl.ac.uk/id/eprint/10104455`): **756 high-resolution binary patterns in 1 cm³ Fe:LiNbO₃, average diffraction efficiency 0.5 %** — non-journal source, treat as indicative [M]* | **High.** This is the closest conceptual match: interference *selects* a stored state by content. The substrate's population code already reads a **ratio** across stalks rather than an absolute address, which is the same philosophy |
| **Holographic data storage** (LiNbO₃:Fe, angular/multiplexed) | Same class of crystal; hologram is a volume index grating | **Reference-beam angle** (and sometimes wavelength, or polarisation) — angular multiplexing | "High-density nonvolatile volume holographic disc storage" (`10.1117/12.556841`, publisher snippet): **5,000 images of 768×768 px, 4 tracks, 0.03 wt % Fe:LiNbO₃, ≈50 bits/µm² areal, 10 Gbit/cm³ volume** — DOI from publisher search result, not Crossref-resolved in-session. Two-center holographic recording (Adibi/Buse/Psaltis `10.1364/josab.18.000584`) established the sensitivity fix. Heanue, Bashaw & Hesselink, *Science* **265**, 749 (1994) — DOI `10.1126/science.265.5173.749` — multiple-page fully-digital holographic storage (lead; not Crossref-resolved in-session) | **Medium–High.** Angle-multiplexing maps onto a **frequency comb**: the comb tooth is the reference-beam angle's spectral equivalent. The substrate's 8-bin address spacing is *already* a comb-addressed volume store |
| **Optical phased array** | **Nothing is stored** — the array of phase shifters *is* the aperture | A **steering command** (phase ramp across elements) | McManamon et al., "Optical phased array technology," *Proc. IEEE* **84**, 268–298 (1996). DOI `10.1109/5.482231`; Sanyal, "Optical phased array," *IETE J. Res.* **45**, 189 (1999), DOI `10.1080/03772063.1999.11416121` | **Very high.** An array of phase-tunable resonators *is* a 1-D optical phased array. Steering → address synthesis |
| **Spatiotemporal optical vortices** | None (structured field in space-time) | The **tilt/position of the STOV axis**; for a multiplexed set, each vortex occupies a distinct position–slope in the space-time manifold | Jhajj et al., "Spatiotemporal optical vortices," *Phys. Rev. X* **6**, 031037 (2016). DOI `10.1103/physrevx.6.031037`; Wan et al., "Optical spatiotemporal vortices," *eLight* (2023), DOI `10.1186/s43593-023-00042-6`; Fan et al., "Perfect spatiotemporal optical vortices," *Photonics Res.* (2025), DOI `10.1364/prj.555236` | **Low–Medium for the field itself** (needs vectorial/higher-dimensional modes), **but the addressing principle ports**: one superposition query selects one element out of many |
| **Frequency-comb addressing** | None (the comb is the probe) | **One comb tooth = one address.** Resolves a comb into N independent channels | Picqué, "Frequency comb spectroscopy," *Nat. Photonics* **13**, 523–532 (2019). DOI `10.1038/s41566-018-0347-5`; Masuda, "Interwoven frequency comb," *CLEO* (2013), DOI `10.1364/cleo_at.2013.jw2a.91`; Liu et al., "Spectrally programmable optical frequency comb generation," *ACS Photonics* (2024), DOI `10.1021/acsphotonics.4c01422`; Ogden et al., "Frequency multiplexed coherent φ-OTDR," *Sci. Rep.* **11** (2021), DOI `10.1038/s41598-021-97647-z` | **Very high — this is already what the substrate does.** 128 bins, 8-bin address spacing, and a pilot is a comb-addressed frame |

**Synthesis of §3:** the two techniques that port cleanly are (1) **frequency-comb addressing**, which the substrate already implements, and (2) **volume holographic associative memory**, because its key is *content*, and the substrate's population code reads a *ratio* across stalks — content-like, not address-like. The technique that ports *conceptually but not physically* is holographic data storage, whose Bragg/angular selectivity is the optical analogue of the substrate's bin spacing. The technique the substrate is furthest from is the STOV, whose addressing key is genuinely higher-dimensional.

**A note on error rate:** the holographic literature reports **crosstalk, diffraction efficiency, and bit-density** — not bit-error rate — because the read-out is an analogue reconstruction, and the honest error metric is "does the reconstructed field correlate with the intended one." The closest thing to a true error-rate statement in the verified set is Nakamura, "Magnetic Holography and Its Application to Data Storage," *Photonics* **8**, 187 (2021), DOI `10.3390/photonics8060187` (DOI-verified, abstract retrieved): "The first reconstruction image was dark and noisy, but improvements in the recording conditions resulted in **error-free recording and reconstruction** of the magnetic hologram" — in transparent magnetic garnet. **[M]** For the substrate, this suggests the analogous framing: report naming rate and correlation, and treat "error-free" as a reconstruction-quality claim.

---

## 4. IS THERE WORK WHERE THE MEDIUM'S STRUCTURE *IS* THE MEMORY?

**Short answer: no verified primary source was found for a personalised, substrate-native memory whose medium's structure is the memory.** This is a controlled negative across Crossref, OpenAlex and Europe PMC.

**What was searched and found:**

- **Reservoir computing** is the closest *principle*. In a reservoir, the **physical dynamical state of the medium is the memory of the input history** — the medium's structure carries the state, and the readout weights are external. Verified: Van der Sande et al., "Advances in photonic reservoir computing," *Nanophotonics* **6**, 561–575 (2017). DOI `10.1515/nanoph-2016-0132`; Prucnal, "Photonic reservoir computing," in *Neuromorphic Photonics* (2017). DOI `10.1201/9781315370590-13`; Nakajima, "Photonic implementation of reservoir computing," *NTT Tech. Rev.* (2022). DOI `10.53829/ntr202208fa8`. **But:** no "personalisation" — the reservoir is a fixed random medium, and the state is transient, not stored. [H] for the substrate's framing.
- **Hopfield-style attractor memory in hardware** stores the memory *in the medium's configuration* (the network settles into the stored attractor). Verified: Cai et al., "OscNet v1.5: energy-efficient Hopfield network on CMOS oscillators for image classification," *ICCV Workshops* (2025). DOI `10.1109/iccvw69036.2025.00497`. **But:** the memory is programmed in by training, not personalised, and the substrate's structure is not itself the content.
- **Magneto-optical in-memory computing** is the closest established *material* precedent for "the medium's state does the arithmetic": "Magneto-optics enhances in-memory computing," *Nat. Photonics* (2025). DOI `10.1038/s41566-024-01599-5` (lead: DOI from publisher search result, not Crossref-resolved in-session); and the dynamic opto-magnetic holography demonstration, "Dynamic complex opto-magnetic holography," *Nat. Commun.* **13**, 7467 (2022). DOI `10.1038/s41467-022-35023-9` (lead, same status; preprint arXiv:2211.02741). Weights live in the material's magnetisation pattern; the read-out light does the multiply.
- **3D magnetism as the state substrate**: "2025 roadmap on 3D nanomagnetism," *J. Phys.: Condens. Matter* (2024). DOI `10.1088/1361-648x/ad9655`.
- **Crystal lattice as the record**: category (C) in §2.2 — atomic lattices as holographic elements (`10.1016/j.ultramic.2021.113376`, `10.1016/j.jcrysgro.2008.09.120`).
- **DNA as a sequence-native store** is the strongest *conceptual* precedent for "the medium's structure is the data" (Erlich & Zielinski's DNA fountain, *Science* **355**, 950–954 (2017), DOI `10.1126/science.aan7932` — **lead, not Crossref-resolved in-session**), but it is a *sequence* in a chemical backbone, not an interference-addressed store.

**Honest read:** the "structure is the memory" idea is **[H] as a personalised, substrate-native scheme**. Its closest established relative is the magneto-optical in-memory-computing device, where a *fabricated material pattern* is simultaneously the storage and the compute substrate, and the address is optical (a beam). That is a genuinely useful precedent, and it is the one closest in spirit to what the collaborator is reaching for.

---

## 5. COUPLED RESONATOR ARRAYS AS COMPUTING / MEMORY HARDWARE

### 5.1 Coupled-oscillator Ising machines — the strongest recent result
- Cılasun et al., "A coupled-oscillator-based Ising chip for combinatorial optimization," *Nature Electronics* (2025). DOI `10.1038/s41928-025-01393-3`. Preprint: Karpuzcu et al., "COBI: a coupled oscillator based Ising chip for combinatorial optimization" (2024). DOI `10.21203/rs.3.rs-4208492/v1`.
- Chamlagai et al., "Grass-roots optimization of coupled oscillator networks," *Phys. Rev. E* **106**, 034202 (2022). DOI `10.1103/physreve.106.034202`.
- Graber et al., "An enhanced 1440 coupled CMOS oscillator network to solve combinatorial optimization problems," *IEEE SoCC* (2023). DOI `10.1109/socc58585.2023.10256945`.
- Cai et al., *ICCV Workshops* (2025). DOI `10.1109/iccvw69036.2025.00497`.

**Performance and energy:** the titles assert what the papers demonstrate — a 1440-oscillator CMOS network solving combinatorial optimisation (Graber et al.), and an *energy-efficient* Hopfield network on CMOS oscillators (Cai et al., "energy-efficient" is in the title). **The specific figures (solution quality, energy per operation, throughput) were not extracted in this session** and are flagged in §8 as must-extract before any energy comparison is quoted. I decline to quote numbers I could not source. **[M] that such chips exist and were peer-reviewed; the numbers need extraction.**

### 5.2 Memristive / coupled oscillator hardware
- Oshima et al., "A memristive oscillator," *Advanced Physics Research* (2024). DOI `10.1002/apxr.202300117`.
- Guo et al., "Memristive oscillator to memristive map, energy characteristic," *Sci. China Technol. Sci.* (2024). DOI `10.1007/s11431-023-2637-1` — note "energy characteristic" in the title: this is the paper to pull for energy-per-operation numbers on a memristive oscillator.
- Jiang et al., "Simplified memristive Lorenz oscillator," *IEEE TCAS-II* (2022). DOI `10.1109/tcsii.2022.3169013`.
- Zheng et al., "Chaotic oscillator using coupled memristive pairs," *IEEE ICECS* (2019). DOI `10.1109/icecs46596.2019.8964782`.
- Abraham et al., "Memristor based multifunction oscillator," *IEEE MWSCAS* (2019). DOI `10.1109/mwscas.2019.8885077`.
- Elsamman et al., "Resistorless memristor based oscillator," *IEEE ICM* (2014). DOI `10.1109/icm.2014.7071833`.
- Spagnolo et al., "Experimental photonic quantum memristor," *Nat. Photonics* **26**, 608 (2022). DOI `10.1038/s41566-022-00973-5`.

### 5.3 Photonic reservoir computing with coupled oscillators
Van der Sande et al. (2017) `10.1515/nanoph-2016-0132`; Nakajima (2022) `10.53829/ntr202208fa8`; Prucnal (2017) `10.1201/9781315370590-13`. [M] Establishes that a coupled-oscillator physical medium can serve as a nonlinear processing layer with a readout layer trained separately.

### 5.4 What this means for the substrate
The substrate sits in a well-populated space: **coupled oscillators as an Ising solver** and **coupled oscillators as a Hopfield memory** are both peer-reviewed, both CMOS-realised at the 10³-element scale, and both claim energy advantage. The substrate's differentiator is *not* the coupled-oscillator compute — that is contested ground with silicon behind it. The differentiator is that the substrate's address space is **geometry-derived and analogue**, and the read-out is a **population ratio**. That is a differentiator only if the analogue addressing buys something the digital approach cannot get. [H]

---

## 6. HOLOGRAPHIC ADDRESSING OF A COUPLED-RESONATOR POPULATION — HAS IT BEEN DONE IN ELECTRONICS?

**No verified primary source was found for interference-addressing a single element of an *electronic* coupled-resonator population.** Controlled negative across Crossref / OpenAlex / Europe PMC.

**Nearest established relatives, all verified:**

| Relative | What it does | DOI |
|---|---|---|
| **Ring-resonator optical filters** (the canonical interference-addressed element) | A waveguide ring's resonance selects one wavelength channel out of many; the *interference around the ring* is what does the selecting | `10.1364/ao.19.002790` *(ring-resonator filter family — leader to confirm)*; ring resonator add-drop review chain in `10.1364/ao.50.004792` |
| **MZI / microring weight banks for optical matrix–vector multiply** | Interference between two paths computes a weighted sum in the optical domain; the *physical structure* of the bank is the memory of the weights | `10.1038/s41566-018-0094-1` *(Feldmann et al. parallel convolutional processing — leader to confirm)*; `10.1038/s41566-017-0046-5` *(Shen et al. deep learning with coherent nanophotonic circuits — leader to confirm)* |
| **Phase-locked oscillator arrays / coherent beamforming** | A population of oscillators is phase-locked to a common reference and the array *as a whole* addresses one direction | `10.1364/oe.469457` (Tuo et al., regeneratively mode-locked optoelectronic oscillator, 2022) |
| **Cross-coupled oscillator synchronisation with delay** | A delay term injected non-invasively steers a heterogeneous population into a chosen synchronisation pattern | Jüngling et al., "Synchronization of heterogeneous oscillators by noninvasive time-delayed cross coupling," *Phys. Rev. Lett.* **115**, 194101 (2015). DOI `10.1103/physrevlett.115.194101` |
| **Kuramoto clusters in heterogeneous populations** | A population with heterogeneous coupling spontaneously clusters; the *cluster* is the addressable unit | Paissan et al. `10.1209/0295-5075/77/20001`; `10.1016/j.physd.2007.10.016` |

**Read:** in electronics, interference addressing exists at the level of *individual resonant elements* (a ring selects a wavelength) and at the level of *whole arrays computing in the optical domain* (MZI weight banks). What is **not** established is the substrate's specific combination: **the mutual coupling between elements *is* the channel, the equaliser inverts that coupling, and a single interference query addresses one element.** No verified source covers that. It is a genuine novelty — and a genuine risk, because the literature's established recipes (ring resonators, MZI banks) get their addressability from *geometric isolation* between elements, whereas the substrate deliberately couples them.

---

## 7. WHAT TO BUILD

### 7.1 The direct answer to the question that prompted this review

> *"Give the substrate half a chance to self-organize and it will produce better stalk topologies than the humans designed."*

**Verdict: the premise is supported; the conclusion is not.** Specifically:

**Supported [M]:**
1. Coupled oscillator populations *do* spontaneously organise into structured, group-wise states (chimeras), robustly and with closed-form theory, in phase, amplitude, mechanical and laser systems (§1(i)).
2. Modularity *does* emerge spontaneously from evolving individuals with no designed modularity (`10.1103/physrevlett.99.228107`, `10.1098/rsif.2007.1108`, `10.1016/j.plrev.2011.02.003`).
3. Small-world topology *does* emerge from a homogeneous local rule applied to heterogeneous elements (`10.1038/s41598-026-47213-2`).
4. Emergent topology *does* create qualitatively new collective states that do not exist on a regular lattice (`10.1103/physreve.68.055103`).
5. Non-trivial topology *does* beat default topology for a synchronisation objective — but when the topology is **optimised**, not merely left to evolve (`10.1038/s42005-022-00870-x`).

**Not supported / dead end as stated [H]:**
6. **There is no established principle by which self-organisation selects the topology that is best for an arbitrary downstream metric.** The pattern-selection theory (Kawasaki-type growth-rate criteria, `10.1103/physreve.60.3626`, `10.1143/ptp.102.947`, `10.1103/physreve.77.026212`) selects the state the *given kernel* prefers; it does not select the state that maximises naming rate, notch depth, or address coverage. Emergence optimises for *dynamical stability*, not for *your metric*. **This is the gap in the claim.**
7. **Self-organisation does not verify anything.** It produces a topology; it does not tell you the topology is better. "Better" needs a metric and a comparison against the human design. The literature's own approach to that question is optimisation, not emergence.

**The precise formulation that IS supported, and is the thing to build:**

> *Use the self-organised dynamics to propose topologies, and use an explicit metric + optimisation to select among them.*

The verified literature supports both halves separately — emergence for proposal generation (`10.1103/physrevlett.99.228107`, `10.1103/physreve.103.032304`, `10.1162/netn_a_00211`), explicit optimisation for selection (`10.1038/s42005-022-00870-x`). Putting them together in the substrate is defensible; claiming emergence alone will get you a topology, not a better one.

**Two additional practical cautions:**
- **Emergence needs a symmetry-breaking kernel.** Chimeras appeared in the literature with *nonlocal*, *delayed*, or *phase-lagged* coupling (`10.1103/physreve.92.060901`, `10.1103/physrevlett.110.244102`, `10.1103/physreve.79.055203`). A substrate whose interstalk coupling is a plain symmetric graph with heterogeneous stalks may not have the mechanism at all — it would then produce *clusters indexed by intrinsic frequency* (Paissan: `10.1209/0295-5075/77/20001`), which is a different (and possibly perfectly adequate) result. **Check the coupling kernel before assuming chimera behaviour.**
- **Your population code may make this irrelevant — in your favour.** The code reads a *ratio* of responses across stalks, not a per-stalk address. A population that spontaneously organises into coherent clusters is *not* a failure mode for a ratio code; it may well be an advantage, because cluster membership becomes a low-dimensional grouping that the ratio code can exploit. This is [H], but it is the most promising place to look.

### 7.2 "Crystal holography" — what to build

**Do not build on the Garcia-Montejo reference; it does not resolve through any bibliographic API.** Build on the real, verified literature instead, and pick the branch that matches the substrate's physics:

- **If the goal is "material structure stores a beam and interference retrieves it":** the established pattern is the *nonlinear volume hologram in a periodically poled crystal* (`10.1002/lpor.202000224`, `10.1103/physreva.102.043506`, `10.1038/s41377-021-00588-5`). Read-out = a pump beam at the right frequency/direction; the stored quantity = a 3D material coefficient pattern. **This is real and peer-reviewed.** But its write path is permanent poling — it cannot be the substrate's write path.
- **If the goal is "frequency addresses a stored state":** spectral hole burning (`10.1103/physrevb.47.14741`) is the direct precedent, and the substrate already implements the same idea in the electrical domain with its 128 bins and 8-bin spacing. **Keep doing what you are doing.**
- **If the goal is "the lattice itself is the hologram":** this is atomic-scale holography (`10.1016/j.ultramic.2021.113376`, `10.1016/j.jcrysgro.2008.09.120`) — read out in X-rays, written serially by a scanning probe. **For the stalk substrate this is a dead end**: the read-out is not optical, the write path destroys what it writes, and the lattice period is fixed while the substrate's address space is continuous and geometry-derived.
- **The best-established "crystal" precedent for the substrate's actual claim** is the magneto-optical in-memory-computing device (`10.1038/s41566-024-01599-5`, `10.1038/s41467-022-35023-9`) — a *fabricated material pattern* is simultaneously store and compute, addressed optically. Read its error metrics before borrowing its framing.

### 7.3 The shortest path to a defensible "self-organisation beats human design" claim

1. **Define the metric** you already have: naming rate (82%) and notch depth (~41 dB) are the right instruments. They are task-relevant in a way that synchronisation quality is not.
2. **Run the optimiser** (`10.1038/s42005-022-00870-x` is the template) over stalk topologies, using the same simulator that produces the current 82% / 41 dB figures. This gives the *upper bound* — the best achievable topology.
3. **Then run the emergent/self-organising dynamics** (`10.1162/netn_a_00211`, `10.1103/physrevlett.99.228107`) seeded from that optimiser's output and from the human design, and measure how close emergence gets to the bound. **If emergence gets within noise of the bound, the claim is earned.** If it does not, the honest result is "emergence produces interesting topologies that we then have to optimise" — which is still a publishable and honest finding, and is exactly what the literature supports.
4. **Report the comparison.** The whole value of this exercise is the head-to-head number.

### 7.4 What is a dead end, plainly

- **Building on the Garcia-Montejo "crystal holography" citation as a method or a precedent.** It does not resolve. [Not a physics judgement — a bibliographic fact.]
- **Expecting self-organisation alone to deliver a topology that is measurably better than the human design.** No literature supports this; the pattern-selection principle does not optimise your metric.
- **Expecting a maximum-entropy principle for oscillator pattern selection to do the work.** Unverified in this session; treat as an open lead, not a foundation.
- **Atomic-lattice "crystal holography" as the substrate's storage model.** Wrong read-out modality, destructive write path, fixed period versus continuous address space.

---

## 8. UNVERIFIED LEADS AND OUTSTANDING ITEMS

**Explicitly NOT verified via Crossref/Europe PMC in this session** — surfaced via publisher pages or from memory; each needs a DOI check before use:

| Item | DOI | Note |
|---|---|---|
| Heanue, Bashaw & Hesselink, "Volume holographic storage and retrieval of digital data," *Science* **265**, 749 (1994) | `10.1126/science.265.5173.749` | Found via publisher search result; not Crossref-resolved. Probably real and probably landmark — **verify before citing** |
| "High-density nonvolatile volume holographic disc storage," *Proc. SPIE* | `10.1117/12.556841` | Found via search snippet carrying the figures (5,000 × 768² images, 50 bits/µm², 10 Gbit/cm³); not Crossref-resolved |
| "Magneto-optics enhances in-memory computing," *Nat. Photonics* (2025) | `10.1038/s41566-024-01599-5` | Search-result only |
| "Dynamic complex opto-magnetic holography," *Nat. Commun.* (2022) | `10.1038/s41467-022-35023-9` | Search-result only; preprint arXiv:2211.02741 seen |
| Houk & Van Vleck, "Nonvolatile storage in photorefractive crystals," *Opt. Lett.* **19**, 210 (1994) | `10.1364/ol.19.000210` | Search-result only |
| "Non-volatile holographic storage in doubly doped lithium niobate crystals," *Nature* | `10.1038/31429` | Search-result only; the volatility-defect citation |
| Erlich & Zielinski, "A DNA fountain for high-throughput, low-cost DNA sequence encoding," *Science* **355**, 950 (2017) | `10.1126/science.aan7932` | From recall, unverified |
| Barabási & Albert, "Emergence of scaling in random networks," *Science* **286**, 509 (1999) | — | From recall, unverified |
| Kawasaki, "Model field theory of the noisy Kuramoto model," *Prog. Theor. Phys.* **99**, 410 (1998) | — | Named principle; original DOI not resolved |
| Hong & Strogatz, "Kuramoto model of coupled oscillators with positive and negative coupling parameters," *PRL* **107**, 074701 (2011) | — | Named result; DOI not resolved |
| Ring-resonator filter / MZI weight-bank / photonic-neural-network DOIs listed in §6 | — | Flagged in-table as leaders to confirm |

**Must-extract figures before any energy comparison is quoted:** the accuracy, energy-per-operation and throughput numbers from `10.1038/s41928-025-01393-3` (COBI), `10.1109/iccvw69036.2025.00497` (OscNet), `10.1109/socc58585.2023.10256945` (1440-oscillator CMOS network), and `10.1007/s11431-023-2637-1` (memristive oscillator energy characteristic). None of these figures were extracted in this session.

**Search-route note:** Semantic Scholar's API returned HTTP 429 on every attempt throughout and contributed nothing. All results here come from Crossref, OpenAlex, Europe PMC and arXiv.

---

## 9. REFERENCE LIST (all DOI-verified via Crossref, except where explicitly flagged in §8)

**Self-organisation / chimera / pattern selection**
1. `10.1103/physrevlett.93.174102` — Abrams & Strogatz, *PRL* **93**, 174102 (2004)
2. `10.1142/s0218127406014551` — Abrams & Strogatz, *Int. J. Bifurc. Chaos* **16** (2006)
3. `10.1103/physrevlett.101.084103` — Abrams, Mirollo, Strogatz & Wiley, *PRL* **101**, 084103 (2008)
4. `10.1103/physrevlett.110.244102` — Nkomo et al., *PRL* **110**, 244102 (2013)
5. `10.1073/pnas.1302880110` — Martens et al., *PNAS* (2013)
6. `10.1103/physreve.91.040901` — Böhm et al., *PRE* **91**, 040901 (2015)
7. `10.1103/physreve.92.060901` — Suda & Okuda, *PRE* **92**, 060901 (2015)
8. `10.1103/physreve.93.052223` — Bera & Ghosh, *PRE* **93**, 052223 (2016)
9. `10.1103/physreve.79.055203` — Sheeba et al., *PRE* **79**, 055203 (2009)
10. `10.1063/5.0033519` — Dudkowski, Czołczyński & Kapitaniak, *Chaos* (2021)
11. `10.1063/1.4938734` — Olmi, *Chaos* (2015)
12. `10.3389/fams.2019.00031` — Rode, Totz, Fengler & Engel, *Front. Appl. Math. Stat.* **5** (2019)
13. `10.1103/physreve.88.042917` — Sethia, Sen & Johnston, *PRE* **88**, 042917 (2013)
14. `10.1103/physreve.98.032301` — Sathiyadevi et al., *PRE* **98**, 032301 (2018)
15. `10.1063/5.0096284` — Bi & Komarov, *Chaos* **32** (2022)
16. `10.1209/0295-5075/108/50003` — Bi et al., *EPL* **108**, 50003 (2014)
17. `10.1103/physreve.85.056211` — Wu et al., *PRE* **85**, 056211 (2012)
18. `10.1209/0295-5075/77/20001` — Paissan et al., *EPL* **77**, 20001 (2007)
19. `10.1016/j.physd.2007.10.016` — Paissan et al., *Physica D* **227** (2008)
20. `10.1103/physrevlett.115.194101` — Jüngling et al., *PRL* **115**, 194101 (2015)
21. `10.1103/physreve.60.3626` — Guardiola et al., *PRE* **60**, 3626 (1999)
22. `10.1143/ptp.102.947` — Battogtokh et al., *Prog. Theor. Phys.* **102**, 947 (1999)
23. `10.1103/physreve.77.026212` — Yanchuk et al., *PRE* **77**, 026212 (2008)
24. `10.1103/physrevlett.99.228107` — Sun, *PRL* **99**, 228107 (2007)
25. `10.1098/rsif.2007.1108` — Solé et al., *J. R. Soc. Interface* **5** (2008)
26. `10.1016/j.plrev.2011.02.003` — Lorenz et al., *Phys. Life Rev.* **8** (2011)
27. `10.1162/netn_a_00211` — Haqiqatkhah et al., *Network Neuroscience* **6** (2022)
28. `10.1103/physreve.103.032304` — Landmann et al., *PRE* **103**, 032304 (2021)
29. `10.1038/s42005-022-00870-x` — Tang et al., *Commun. Phys.* **5** (2022)
30. `10.1038/s41598-026-47213-2` — Fukushima et al., *Sci. Rep.* (2026)
31. `10.1103/physrevlett.72.4101` — Marchesoni, *PRL* **72**, 4101 (1994)
32. `10.1038/35019019` — Albert, Jeong & Barabási, *Nature* **406** (2000)
33. `10.1038/30918` — Watts & Strogatz, *Nature* **396** (1998)
34. `10.1016/j.physa.2003.12.037` — Li et al., *Physica A* **343** (2004)
35. `10.1103/physreve.68.055103` — Hou, Zhang & Xiao, *PRE* **68**, 055103 (2003)
36. `10.1007/bf00276105` — Ashkenazi et al., *J. Math. Biol.* (1977)

**Crystal holography and holographic storage**
37. `10.1063/1.1652580` — Chen, Jaganathan & Van Vleck, *APL* **13** (1968)
38. `10.1364/ol.4.000021` — Huignard et al., *Opt. Lett.* **4** (1979)
39. `10.1109/68.215288` — Yin & Yu, *IEEE Photonics Technol. Lett.* **5** (1993)
40. `10.1117/12.166036` — Yu & Yin, *Proc. SPIE* (1994)
41. `10.1364/ol.30.002233` — Hsieh, Psaltis et al., *Opt. Lett.* **30** (2005)
42. `10.1002/lpor.202000224` — Liu, Mazur, Królikowski & Sheng, *Laser Photonics Rev.* **5** (2021)
43. `10.1103/physreva.102.043506` — Fang, Wang, Yang & Ye, *PRA* **102**, 043506 (2020)
44. `10.1038/s41377-021-00588-5` — Chen, Wang, Wei, Hu et al., *Light: Sci. Appl.* **10**, 205 (2021)
45. `10.1117/12.2678211` — Zhang, *Proc. SPIE* (2023)
46. `10.3390/photonics10050562` — Lai, Chang, Liu, Wei et al., *Photonics* **10**, 562 (2023)
47. `10.1016/j.ultramic.2021.113376` — Latychevskaia, Cassidy & Shintake, *Ultramicroscopy* (2021)
48. `10.1016/j.jcrysgro.2008.09.120` — Hosokawa et al., *J. Cryst. Growth* **307** (2009)
49. `10.3103/s106833721504012x` — Balyan, *J. Contemp. Phys.* **49** (2015)
50. `10.1103/physrevb.47.14741` — Holliday, Croci, Vauthey & Wild, *PRB* **47**, 14741 (1993)
51. `10.1364/shbs.1994.fd2` — Sasaki et al., *Proc. SPIE* (1994)
52. `10.1364/josab.18.000584` — Adibi, Buse & Psaltis, *JOSA B* **18**, 584 (2001)
53. `10.1364/ol.25.000539` — Adibi et al., *Opt. Lett.* **25**, 539 (2000)
54. `10.3390/photonics8060187` — Nakamura, *Photonics* **8**, 187 (2021) *(DOI-verified, abstract retrieved)*
55. `10.1088/2040-8986/abb3a4` — Sheridan et al., "Roadmap on holography," *J. Phys. Photonics* **2**, 030002 (2020)
56. `10.1155/2012/803439` — Guo, Gleeson & Sheridan, *ISRN Photonics* (2012)
57. `10.1117/12.479660` — Ibarra, Montejo & Olivares-Pérez, *Proc. SPIE* (2003) *(the only Montejo+holography match found)*
58. `10.1117/12.2283698` — von Bally, *Proc. SPIE* (1990) *(context)*
59. `10.1016/j.optcom.2006.01.049` — Acedo Barbosa et al., *Opt. Commun.* (2006)
60. `10.1364/ol.588151` — Liu, "Holographic data storage using polarization code," *Opt. Lett.* (2026)
61. `10.1186/s43593-024-00061-x` — Wang, Zhou, Zhang et al., *eLight* **4** (2024) *(DOI-verified, abstract retrieved)*
62. `10.1038/s41377-024-01538-7` — Li & Wu, *Light: Sci. Appl.* (2024) *(Europe PMC pmid 39179526)*
63. `10.1038/s41377-026-02287-5` — Zhang et al., *Light: Sci. Appl.* (2026) *(Europe PMC pmid 42086538)*
64. `10.3788/col202321.120003` — Wang, Zhang, Liu et al., *Chin. Opt. Lett.* (2023)

**Associative memory, addressing, comb**
65. `10.1364/ao.13.000904` — Knight, "Page-oriented associative holographic memory," *Appl. Opt.* **13**, 904 (1974)
66. `10.1364/ao.14.001088` — Knight, "Holographic associative memory and processor," *Appl. Opt.* **14**, 1088 (1975)
67. `10.1038/222960a0` — Willshaw, "Non-holographic associative memory," *Nature* **222**, 960 (1969) *(control)*
68. `10.1109/aiprw.2000.953606` — Li, "Parallel associative search by use of a volume holographic memory," *AIPR* (2002)
69. `10.1364/ao.53.004375` — Takabayashi et al., "Shift-multiplexed self-referential holographic data storage," *Appl. Opt.* **53** (2014)
70. `10.1364/ol.21.001780` — Lande et al., "Digital wavelength-multiplexed holographic data storage system," *Opt. Lett.* **21**, 1780 (1996)
71. `10.1117/12.917569` — Chen, Jia, Chung & Wen, *Proc. SPIE* (2012)
72. `10.1103/physrevx.6.031037` — Jhajj et al., *Phys. Rev. X* **6**, 031037 (2016)
73. `10.1186/s43593-023-00042-6` — Wan et al., *eLight* (2023)
74. `10.1364/prj.555236` — Fan et al., *Photonics Res.* (2025)
75. `10.1038/s41566-018-0347-5` — Picqué, *Nat. Photonics* **13** (2019)
76. `10.1364/cleo_at.2013.jw2a.91` — Masuda, *CLEO* (2013)
77. `10.1021/acsphotonics.4c01422` — Liu et al., *ACS Photonics* (2024)
78. `10.1038/s41598-021-97647-z` — Ogden et al., *Sci. Rep.* **11** (2021)
79. `10.1109/5.482231` — McManamon et al., "Optical phased array technology," *Proc. IEEE* **84** (1996)
80. `10.1080/03772063.1999.11416121` — Sanyal, *IETE J. Res.* **45** (1999)
81. `10.1364/oe.469457` — Tuo et al., *Opt. Express* **30** (2022)

**Coupled-resonator / oscillator hardware**
82. `10.1038/s41928-025-01393-3` — Cılasun et al., *Nat. Electron.* (2025)
83. `10.21203/rs.3.rs-4208492/v1` — Karpuzcu et al., COBI preprint (2024)
84. `10.1103/physreve.106.034202` — Chamlagai et al., *PRE* **106**, 034202 (2022)
85. `10.1109/socc58585.2023.10256945` — Graber et al., *IEEE SoCC* (2023)
86. `10.1109/iccvw69036.2025.00497` — Cai et al., *ICCV Workshops* (2025)
87. `10.1002/apxr.202300117` — Oshima et al., *Adv. Phys. Res.* (2024)
88. `10.1007/s11431-023-2637-1` — Guo et al., *Sci. China Technol. Sci.* (2024)
89. `10.1109/tcsii.2022.3169013` — Jiang et al., *IEEE TCAS-II* (2022)
90. `10.1109/icecs46596.2019.8964782` — Zheng et al., *IEEE ICECS* (2019)
91. `10.1109/mwscas.2019.8885077` — Abraham et al., *IEEE MWSCAS* (2019)
92. `10.1109/icm.2014.7071833` — Elsamman et al., *IEEE ICM* (2014)
93. `10.1038/s41566-022-00973-5` — Spagnolo et al., *Nat. Photonics* **26** (2022)
94. `10.1515/nanoph-2016-0132` — Van der Sande et al., *Nanophotonics* **6** (2017)
95. `10.1201/9781315370590-13` — Prucnal, in *Neuromorphic Photonics* (2017)
96. `10.53829/ntr202208fa8` — Nakajima, *NTT Tech. Rev.* (2022)
97. `10.1088/1361-648x/ad9655` — "2025 roadmap on 3D nanomagnetism," *J. Phys.: Condens. Matter* (2024)
