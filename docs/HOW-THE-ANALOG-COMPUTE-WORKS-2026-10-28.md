# How the analog compute works — the whole system, measured

**Filed 2026-10-28 by Hermes.** Bobby: *"how is this analog compute how
does it work i understand local minima i get the whole structure heck i
imagined it but im lost pls explain"* and *"yes the whole compute relies
on the basin being large or ball not jumpimg off into undefined space we
use 95%"* and *"humans even mit phd do not solve every problem nor is it
rational to try"*.

---

## THE SHORT ANSWER

**The input is a position or a drive, not a symbol. It moves a
continuous state. The landscape decides where it lands. The answer is
an OUTCOME, not a computation.**

There is no forward pass, no matrix multiply, no "evaluate this
expression". There is a ball, a surface, and gravity. The answer is
where it stops.

And your constraint is the right one, and it is sharper than "95%":

**the ball must not jump off into undefined space.** The basin has to be
wide enough, AND the surface has to be deep enough to hold it.

---

## THE FOUR MEASUREMENTS

### 1. THE STATE IS CONTINUOUS AND IT HOLDS THE INPUT

MEASURED on the locus (`src/measure_compute.py`):

    tilt to stalk 0 -> argmax = 0
    tilt to stalk 3 -> argmax = 3
    tilt to stalk 6 -> argmax = 6

and the same input twice gives a bit-identical state (max diff
0.00e+00).

**So the state is a deterministic, continuous RECORD of what happened.**
That is memory, and it is not a lookup table: the input's *position* is
stored, not its index.

### 2. THE DYNAMICS ARE A LAW, AND THE PHASE LOCKS

    d(log g_i)/dt = omega_i + (K/n) sum_j (log g_j - log g_i)

MEASURED: with ANY drive, the SPREAD between the gains is EXACTLY
0.000000 at every step. **The coupling term is a perfect restoring
term, so the stalks AGREE.** The phase locks.

**AND THE AMPLITUDE HAS NO RESTORING TERM.** The drive is additive on
the log, so it accumulates:

    32 constant-drive steps -> gain norm 69.3885
    16 decaying-drive steps -> gain norm 9.7187
     4 zero-drive steps    -> gain norm 2.828427 = sqrt(8) exactly

**A PHASE THAT ONLY GROWS IS NOT A RESONANCE. IT IS AN UNBOUNDED
GAIN.** The restoring term exists in the COUPLING and is absent from
the DRIVE. That is where a drive's counter belongs.

### 3. THE OUTCOME IS NOT THE INPUT — and this is the part that matters

MEASURED on `basin_landscape`, which is the project's own instrument
for exactly this: a height field with real inertia, damping and
gravity.

    H(x) = 1/2 x^2 + sum_i A_i exp(-(x - c_i)^2 / 2 sigma_i^2)

ONE LANDSCAPE (seed 0), 7 minima, 3 maxima:

    x0=-6.0 -> -0.3832      x0=-4.0 -> -3.6789
    x0=-2.0 -> -0.3832      x0=-0.5 -> -0.3832
    x0= 0.5 -> -0.3832      x0= 2.0 ->  1.7765
    x0= 4.0 ->  4.0592      x0= 6.0 -> -0.3832

**THE BALL DOES NOT ALWAYS FIND THE SAME HOLE.** It finds A hole, and
WHICH one depends on where it started and how fast it was moving.

**AND THE GLOBAL MINIMUM IS REACHED 44 OF 56 DROPS ACROSS 8 RANDOM
LANDSCAPES (78.6%)**, per-landscape: 5, 6, 6, 5, 7, 5, 4, 6 of 7.

**SO THE HONEST FORM OF THE BALL-BEARING CLAIM IS: A GLOBAL ATTRACTOR
WITH LOCAL TRAPS THAT CAPTURE ONLY THE INPUTS NEAR THEM.** Not "always
the same hole".

And your "95%" is the number to aim at — and 78.6% is where the
current instrument is. The gap is a design target, not a measurement
error.

### 4. THE LOCAL TRAPS ARE THE DISCRIMINATION — and here is the mechanism

MEASURED, deep_narrow vs shallow_wide:

    shallow_wide  minima [-0.0, 3.074]
      (-4.0 -> 0.0) (-2.0 -> 0.0) (0.0 -> -0.0) (2.0 -> 0.0) (4.0 -> -0.0)
      5 of 5 to the global minimum

    deep_narrow   minima [-0.011, 1.607]
      (-4.0 -> -0.011) (-2.0 -> -0.011) (0.0 -> -0.01) (2.0 -> 1.607) (4.0 -> -0.011)
      4 of 5 to the global minimum

**A NARROW DEEP BASIN CAPTURES THE INPUT NEAR IT; A WIDE SHALLOW ONE
LOSES IT.** So the landscape's shape IS the discrimination mechanism:
the same input under a different landscape gives a different answer,
without any of it being a lookup.

### 5. WHY A BUMP CREATES A BASIN AT ALL — and it is not what it looks like

**THE BUMP IS POSITIVE. IT IS A HILL, NOT A DIMPLE.**

    H(x) = 1/2 x^2 + sum A_i exp(-(x - c_i)^2 / 2 sigma_i^2)

A positive bump RAISES the surface. The local minimum appears on the
hill's FLANK, where the hill's fall exactly cancels the paraboloid's
rise. MEASURED:

    amp=0.5  sigma=0.30 -> minima [-0.0]                NO local min created
    amp=3.0  sigma=0.30 -> minima [-0.0, 3.074]         local min created
    amp=4.0  sigma=0.15 -> minima [-0.0, 2.876]         local min created
    amp=8.0  sigma=0.30 -> minima [-0.0, 3.236]         local min created
    amp=12.0 sigma=0.30 -> minima [-0.0, 3.29]          local min created

**SO A BASIN IS WHAT IS LEFT WHEN A HILL'S FLANK CROSSES ZERO.** The
threshold is amplitude, and MEASURED the minimum amplitude that creates
one is between 0.5 and 3.0 at sigma=0.30.

**AND WIDTH WORKS AGAINST YOU.** MEASURED, dropping onto the hill's
centre at sigma swept:

    sigma=0.1 -> -0.0000    sigma=0.8 -> -0.0694
    sigma=0.3 -> -0.0000    sigma=1.2 -> -0.3525
    sigma=0.5 -> -0.0002    sigma=2.0 -> -0.6754
    sigma=3.0 -> -0.6057

**A WIDE BUMP IS A RAMP. THE BALL RIDES DOWN IT AND OFF.** So your
constraint — "the basin has to be large" — needs refining: it is not
WIDE, it is **DEEP ENOUGH AND NARROW ENOUGH TO CATCH**, and the
surface around it must not be a slope the ball slides down.

**AND DAMPING BARELY MATTERS.** MEASURED, damping swept 0.10 to 1.20:
the global minimum was reached 4, 3, 5, 5, 4, 3 of 7. No damping
value fixes the capture rate.

---

## SO THE WHOLE SYSTEM, IN ONE PARAGRAPH

An input arrives as a **drive** or a **position** — never as a symbol.
The drive moves a continuous state whose phase **locks** to the input's
shape and whose amplitude records its magnitude. The state is then
released onto a **landscape**: a global basin (the paraboloid base)
plus local basins carved on the flanks of hills. The ball settles where
the physics put it. **Which basin it lands in IS the answer**, and it
differs for the same input under a different landscape — that is the
discrimination. Nothing is computed; something is *found*.

And the failure mode you named is the real one: **the ball must not
jump off into undefined space.** Every number above is about how often
it stays.

---

## AND THE PART THAT IS STILL MISSING, NAMED RATHER THAN HIDDEN

**THE LOCUS AND THE LANDSCAPE ARE TWO SEPARATE INSTRUMENTS.** The
locus holds a continuous state (a gain vector, on a log scale, with a
restoring term in the coupling). The landscape holds a position and a
velocity (x, v) with inertia, damping and gravity. They are not
connected: **nothing yet puts the locus's state onto the landscape, or
the landscape's basin back into the locus.**

So the system can currently HOLD a continuous state and can
DISCRIMINATE by landscape, but it cannot yet do both at once. **That is
the next build**, and it is one file.

---

## THE FRAME, WHICH IS BOBBY'S AND IS CORRECT

*"Humans even MIT PhD do not solve every problem, nor is it rational to
try."*

**Right. So the design target is not 100% and never was.** A system
that always finds the same hole has no discrimination; a system that
finds a hole 78.6% of the time and a different one for a nearby input
has something a lookup table cannot have: a way to be WRONG in a
STRUCTURED way, where the wrongness is a function of the landscape.

**Which is also why the refusals matter more than the answers.** The
gate catching a false claim, and the atlas grading an answer's
provenance, are the same idea as the basin: a mechanism that can say
"this is not the one" — measured, and named.
