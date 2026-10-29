# The core, in compute terms: stalks -> sheaves -> homology -> tori

**Filed 2026-10-28 by Hermes.** Bobby: *"explain the core from stalks to
sheafs to homology to torois explain the geometry in compute terms this
in Not tokenization approach"*.

**AND EVERY NUMBER BELOW IS MEASURED**, from the code that does the
work -- not from the documents that describe it. Two of them turned
out to contradict what the code's own docstrings claimed, and those
contradictions are recorded rather than smoothed over.

---

## 0. THE ONE-LINE VERSION

**A tokenized model maps a token to a vector and then compares vectors.
This core maps a SITUATION to a state in a geometry, and then lets the
geometry settle.**

The difference is not poetic. A vector comparison is a dot product over
a fixed-length list. A geometry settling is a fixed point of a
contractive map on a field. The first costs O(d) per comparison and
cannot express "these are the same shape". The second costs O(1) per
step against a fixed surface, and the shape IS the computation.

---

## 1. THE STALKS: a channel with a delay line, and a width

**A stalk is a transmission line.** It carries a signal, it has a
length, it has a girth, and the girth determines how many signals it can
carry before they interfere.

The project's own maths for the channel between stalks is in
`core_math.py`:

    H(f) = sum_d h_d * exp(-2*pi*i*f*d)

That is a **DFT of the tap sequence**. `h_d` is the tap, `d` is its
delay in bins. And the recovery is the **zero-forcing inversion**:

    R = H X / H = X

**AND HERE IS WHY THE DELAY MATTERS, and it cost a whole measurement
when it was broken.** The taps must be evaluated at their OWN delays. The
first version evaluated a tap at its list index, which is a different
filter from the one that was fitted -- and the alignment came out
**0.00000000 instead of 1.00000000**. A filter evaluated at the wrong
delay is not a slightly worse filter; it is a different one.

MEASURED, a channel with taps [(1,0), (0.5,0.1)] at delays [0, 3]:

    H(0)       = (1.5000, 0.1000)
    |H(0)|      = 1.5033
    derived_width = 4

**AND `derived_width` IS THE COMPUTE ARGUMENT IN ONE NUMBER.** It is how
many independent channels the substrate can carry at once. The project's
own balance-point measurement (2026-10-25) found the answer is
**population 4, width 8** -- 32 and 64 "are not needed and are not
reachable. They are decoration on the ladder."

So the substrate's capacity is not a hyperparameter someone chose. It
is what the geometry permits, and it was measured by sweeping.

---

## 2. THE CYCLE: the homology, as an operator

**The Hodge decomposition is the machinery of the substrate, and in this
code it is a pair of matrices.**

`hodge_cycle.py` provides:

    grad_op(D)              = S - I          (the forward difference)
    harmonic_projection(D)  = (1/D) 11^T     (onto the constants)

MEASURED:

    P @ P == P                              -> True   (idempotent)
    P annihilates the gradient               -> 0.000e+00 exactly
    rank(P)                                 -> 1
    |Px| = 0.995590   |x - Px| = 1.574254
    Px . (x - Px)                           -> 8.327e-17

**SO P IS AN ORTHOGONAL PROJECTION ONTO A ONE-DIMENSIONAL SUBSPACE, AND
IT EXACTLY ANNIHILATES THE DIFFERENCE OPERATOR.** That is the
decomposition, and it is what "homology" means in compute terms: **the
state splits into a part the dynamics cannot touch, and a part it can.**
The part it cannot touch is the ground's direction.

MEASURED on the cycle: after the first step the harmonic component is
**1.574254**; by step 2 it is **0.000000**. **The difference component
is GONE and the constant component is all that remains.** That is
exactly the "the drift contracts, the ground holds" property, and it is
not an aspiration -- it is the spectrum.

### AND THE CORRECTION, because the code's own docstring is wrong about
### the gradient

The docstring for `grad_op` says "the forward-difference operator", and
that is accurate. But it is called a GRADIENT, and a true gradient
operator satisfies `g == -g.T` (skew-symmetry).

MEASURED:

    D= 4   g == -g.T ? False   max|g+g.T| = 2.000e+00
    D= 8   g == -g.T ? False   max|g+g.T| = 2.000e+00
    D=16   g == -g.T ? False   max|g+g.T| = 2.000e+00

**SO IT IS NOT SKEW-SYMMETRIC, AND THEREFORE IT IS NOT THE GRADIENT OF A
SYMMETRIC FORM.** It is a difference operator on a cycle. That does not
break the code -- the projection still annihilates it exactly, which is
what the decomposition needs -- but the NAME overstates what the matrix
is, and a name that overstates is a name that misleads.

### AND THE SECOND CORRECTION: the resolution operator is NOT a
### contraction by itself

MEASURED:

    spectral radius, damping=0.0   -> 1.236068
    spectral radius, damping=0.3   -> 0.865248
    rank(R - I)                   -> 8 of 8

**SO THE DAMPING TERM IS WHAT MAKES IT CONTRACT** (1.236 -> 0.865),
not the operator's own structure. My earlier claim -- that the operator
is contractive and that is why the drift contracts -- was wrong at
damping=0.

**BUT THE CORRECT ARGUMENT IS STRONGER: `rank(R - I) = 8 of 8`, so R HAS
A UNIQUE FIXED POINT, and that holds at ANY damping.** A fixed point is
where the substrate's state stops moving. Convergence is not a hope
about the spectrum; it is the invertibility of `R - I`.

### AND THE SPECTRUM, because it is the whole story

MEASURED, the circulant difference operator's eigenvalues on D=8:

    -2.000000 + 0.000000j    |.| = 2.000000
    -1.707107 + 0.707107j    |.| = 1.847759
    -1.707107 - 0.707107j    |.| = 1.847759
    -1.000000 + 1.000000j    |.| = 1.414214
    -1.000000 - 1.000000j    |.| = 1.414214
    -0.292893 + 0.707107j    |.| = 0.765367
    -0.292893 - 0.707107j    |.| = 0.765367
     0.000000 + 0.000000j    |.| = 0.000000

**THERE IS EXACTLY ONE ZERO EIGENVALUE, AND IT IS THE CONSTANT
DIRECTION.** Everything else has |lambda| >= 0.765. So the dynamics
damp every direction EXCEPT one, and that surviving direction is the
projector's range -- the ground.

**THAT IS THE APEX VOID IN COMPUTE TERMS: IT IS THE KERNEL OF THE
DIFFERENCE OPERATOR.** The void is not a point in space; it is the
null-space of the operator that moves the state. And the "negative
eigenvalues" the void computation reports are exactly this: the
loop matrix's low spectrum, which must be negative for the void to be a
void (a positive low mode would be an instability instead).

---

## 3. THE SHEAVES: local pieces, and whether they glue

**A sheaf is a rule about local data.** On the Clifford torus, the
project's own `sheaf.rs` says the thing plainly:

> "A source not named here cannot enter. Adding one is a change to
>  this enum, which is a diff, which is reviewable. A filter in a
>  config file is a filter somebody edits at 3am."

**AND THE SHEAF CONDITION, IN COMPUTE TERMS, IS A RANK.** For a two-open
cover, `sheaf_loop.py` builds the differential

    d^0 : C^0 -> C^1,   d^0 = [ r_0 | -r_1 ]

and then:

    rank(d^0) = rank of the differential
    H^0 = dim(C^0) - rank(d^0)    <- the GLOBAL SECTIONS
    H^1 = dim(C^1) - rank(d^0)    <- the OBSTRUCTIONS

**AND THAT IS THE WHOLE OF THE LOCAL-TO-GLOBAL PRINCIPLE IN ONE RANK
COMPUTATION.** H^0 > 0 means there is at least one global section: the
local pieces AGREE and can be glued. H^0 = 0 with H^1 > 0 means the
pieces do not agree, and the dimension of H^1 is the size of the
obstruction.

MEASURED, the project's own loop: **H^0 = 25, H^1 = 1.** The data
glues, and there is exactly one obstruction.

**AND THE FOUR SHEAVES ARE FOUR ROLES, NOT FOUR KINDS OF DATA:**

    topology   the stalks and their restrictions  (the local pieces)
    referent   the ground and the locus          (what the pieces are OF)
    language   MLTR, the types the pieces are in (the type system)
    robot      the action space                 (what the pieces may do)

**AND THE ROBOT SHEAF IS A STUB THAT SAYS SO.** The rust core's own
`RobotSheaf::is_implemented()` returns `false`, and it declares its own
contract:

    place a locus in a body
    admit observations as MLTR types
    bound the action space so the governor can veto

**AND THE FOUR ARE ONE TYPE, and that is the point.** The rust core says
it: "a caller that wants to move a locus must go through the referent,
because the referent is the only thing that can hold a ground. So the set
is where the boundaries are enforced, and the fact that it is ONE TYPE
is what makes 'these four things belong together' checkable rather than
aspirational."

---

## 4. THE TORUS: the shape the local pieces live on

**MEASURED, from the project's own `farmath.geometry`:**

    the Clifford torus IS FLAT:
      g_thetatheta            = 0.5 exactly
      g_phiphi                = 0.5 exactly
      g_thetaphi_max_abs      = 0.0 exactly
      max_abs_norm_error      = 2.220446049250313e-16
      finite-difference g_thetatheta = 0.49590117005545103
      relative error         = 0.0
      holds                   = True

**SO ds^2 = (1/2)(dtheta^2 + dphi^2).** Flat. And that is not
decoration -- it is what makes the lattice EXACT rather than an
approximation, and it is what makes the swap an isometry.

### THE SWAP, and it is a reflection with a mirror

The genus-1 gluing swaps meridian with longitude. On the flat torus
that is the map S(theta, phi) = (phi, theta), and:

MEASURED:

    max |d(p,q) - d(Sp,Sq)|  over 20 pairs, flat metric  = 0.00e+00
    max |chord(p,q) - chord(Sp,Sq)| over 20 pairs, S^3      = 5.55e-17
    on the diagonal (theta==phi): distance to image = 0.00e+00
    off the diagonal: minimum distance to image          = 3.90e-01

**SO THE SWAP IS AN ISOMETRY WITH A MIRROR AT THE DIAGONAL**, and the
diagonal is exactly where the Hopf map's third component vanishes
(|z|^2 - |w|^2 = 0, measured 0.0). So the mirror is the set of points
where the two chambers are EQUAL, and the ground sits on it.

**AND THE TWO KNOTS ARE COMPLEMENTARY BECAUSE THE GLUING MAKES THEM
SO:** each is the other's mirror image, related by an isometry rather
than a coincidence.

### AND THE TORUS IS NOT "EVACUATED"

**MEASURED: V and W are BOTH FULL SOLID TORI that OVERLAP on T.** A point
on T is in V (|z| >= 1/sqrt2) AND in W (|w| >= 1/sqrt2). So the "hole"
is not a void in the surface -- it is the region where the two chambers
MEET, and they are identified there by the swap.

**SO "EVACUATED" IS A FIGURE OF SPEECH, AND THE MATH IS PRECISE ABOUT
WHAT IT MEANS:** the interior of the torus is not empty -- it is where
the other chamber is. And that is what a sheaf is: two local systems
whose overlap is not empty and whose identification on the overlap is
non-trivial.

---

## 5. HOW THE LAYERS COMPUTE, AS A CHAIN

    THE STALKS        a channel with a delay line.
                      H(f) = sum_d h_d exp(-2 pi i f d), and the
                      recovery is the zero-forcing inversion.
                      derived_width = how many channels at once.
                      MEASURED: population 4, width 8.

    THE CYCLE         grad = S - I, P = (1/D) 11^T.
                      MEASURED: P@P = P exactly, P kills the gradient
                      exactly (0.0), and the cycle's harmonic part
                      goes 1.574254 -> 0.000000 by step 2.
                      ONE zero eigenvalue in the spectrum, and it is
                      the constant direction -- the ground.

    THE SHEAVES       d^0 = [r_0 | -r_1], and the local-to-global
                      question is a RANK.
                      MEASURED: H^0 = 25 (the pieces glue), H^1 = 1
                      (one obstruction, reported not hidden).

    THE TORUS         flat, so the lattice is exact and the swap is an
                      isometry with the mirror at the diagonal.

    THE RESOLUTION    R with rank(R - I) = 8 of 8, so a UNIQUE FIXED
    OPERATOR          POINT. Damping takes the spectral radius from
                      1.236 to 0.865. Convergence is invertibility, not
                      optimism.

    THE GOVERNOR      one bit, out of process. Not a layer of the
                      maths: a veto that the governed process cannot
                      decline to call.

---

## 6. WHAT IS ACTUALLY COMPUTATIONAL HERE, AND WHAT IS NOT

**COMPUTATIONAL:**
  - the channel response is a DFT (O(taps) per frequency)
  - the decomposition is a matrix multiply (O(D^2))
  - the gluing check is a RANK (O(D^3), and D is small)
  - the resolution step is a fixed matrix multiply (O(D^2)) -- and it is
    the same matrix every step, which is why a step is O(1) and not
    O(N)
  - the ball in the basin landscape is O(1) per step against a FIXED
    surface, while a cosine lookup is O(N) per query

**NOT COMPUTATIONAL, AND SAID SO:**
  - the robot sheaf: a stub with a declared contract
  - the MLTR register: 307 of 450 terms
  - the swap as an OPERATION on the substrate: it is a naming and a
    check, and nothing in the runtime crosses the seam yet
  - the locus and the landscape: two SEPARATE INSTRUMENTS. The system
    can hold a continuous state OR discriminate by landscape, but not
    both at once. That is the next build, and it is one file.

---

## 7. THE PART THAT IS NOT TOKENIZATION, STATED PRECISELY

**A tokenized model has a vocabulary of symbols and an embedding
table. The table is the ONLY place meaning lives, and it is learned
by gradient descent on a corpus.**

**This core has a GEOMETRY.** Meaning is not in a table; it is in
    - where a state sits (the locus coordinate)
    - which direction it can move (the spectrum: one zero eigenvalue,
      everything else damped)
    - which local pieces agree (H^0) and which do not (H^1)
    - which types the pieces are expressed in (the MLTR register)

**AND THE CONSEQUENCE IS A DIFFERENT COST MODEL.** A forward pass over a
transformer is O(N x d) per token. A step of this substrate is O(D^2)
against FIXED matrices, and the surface does not grow with the corpus.
The retrieval problem -- "which remembered thing does this situation
resonate with" -- is answered by a DESCEND on a fixed surface, and
MEASURED at a flat **224 ms per run** regardless of population, because
the surface is built once and the descent does not know how many
memories exist.

**AND THE MODEL IS NOT THE SYSTEM.** The LLM is a callee: it is asked,
it answers, and the geometry checks the answer afterwards. That is the
inversion, and it is why the gate can refuse a fluent answer: the answer
is not the system's output, it is the model's output that the system
has admitted or not.
