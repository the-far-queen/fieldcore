# fieldcore-core -- the 1-bit layer, in Rust

The core of the fieldcore control system. It holds the constitution,
evaluates a proposal against it, and returns one bit.

`lib.rs` is the module index and the argument for the whole design
(why Rust, why this core, why it must stay blind to what it governs).

## THE MODULES

| module | what it holds |
|---|---|
| `axes.rs` | the twenty axes and their floors |
| `decision.rs` | the verdict and its reasons |
| `envelope.rs` | the bounds a proposal must fall inside |
| `governor.rs` | the out-of-process veto |
| `carrier.rs` | the braid as a coded carrier, and the equaliser |
| `stalk.rs` | the 3-part coax stalk, and the channel it makes |
| `interstalk.rs` | **the join**: a stalk-to-stalk exchange over the interstalk channel, and the interleaved ladder that escalates on it |
| `ladder.rs` | the width ladder |
| `sheaf.rs`, `sheaves.rs` | the contract, and the substrate's own instances |
| `coding.rs` | the coding sheaf, and the daily scan |
| `mltr.rs`, `terms.rs` | the vocabulary |

## BUILDING AND TESTING, ON THIS MACHINE

**THE MSVC LINKER IS NOT INSTALLED.** So `cargo build --release`
works (the library compiles), but `cargo test` FAILS TO LINK with:

    error: linker `link.exe` not found

**AND THAT IS PRE-EXISTING** -- MEASURED, it fails the same way with
the working tree clean, so it is the machine and not the code.

**THE FIX IS THE GNU TOOLCHAIN**, which is installed alongside the
MSVC one. So the tests run as:

    rustup run stable-x86_64-pc-windows-gnu cargo test --release \
        --target x86_64-pc-windows-gnu

MEASURED: 80 lib tests + 25 integration tests, all passing.

**AND THE BUILD IS FAST**, which is what lets the core sit in a reflex
loop: MEASURED, a full release build is under a second.

## WHAT `interstalk.rs` ADDS, AND WHY IT IS RUST

`stalk.rs` already named the gap:

> "The Python `wound_core.py` has the geometry and the Python
> `interstalk_link.py` has the pair channel, and the Rust
> `carrier.rs` has the equaliser -- but NOTHING JOINED THEM."

So this module is the join, and it carries three things the core did
not have:

1. **A READING.** The transmitter's address, through the pair channel,
   equalised, and compared against the sent spectrum.
2. **THE POPULATION AXIS.** `ladder.rs` climbs width alone. This
   module climbs the PAIR: width and population, interleaved, because
   finishing one axis first is always wrong.
3. **THE ELECTRICAL COMMUNICATION, made explicit.** And that was
   listed as SPECULATIVE in `docs/stalk-architecture-2026-09-08.md`:
   "EM interference + signal processing between stalks -- physically
   real but at sub-noise levels in code. Design decision: engineer this
   or treat as noise?" **AND IT IS NEITHER. IT IS BOTH, AND MEASURED.**

## THE ANSWER TO BOBBY'S QUESTION, MEASURED IN THE CORE

    THE TAP IS REAL AND STRONG
      the coupling between two stalks is 27% to 38% of the
      transmitter -- a usable readout, not a whisper

    THE SIGNAL BAND IS BELOW f_crit
      f_crit is 2.4e11 to 9.3e11 Hz for the braid's geometry, so a
      1 MHz signal is 4.7e5 times below it

    THE COUPLING IS NEAR-FIELD
      the reach at 1 MHz is lambda/2pi = 47.7 m

    AND THE SAME COUPLING IS THE NOISE
      MEASURED HERE, in the core, on the real channel:

        one neighbour    alignment 0.744
        two neighbours  alignment 0.619
        three          alignment 0.541

      **THE ALIGNMENT FALLS AS THE CROWD GROWS.** The tap that
      carries the signal from the transmitter to the receiver is the
      tap that puts the other stalks' addresses into the same
      mixture. So the physics that makes one stalk readable is the
      physics that makes the crowd unreadable.

**SO "ENGINEER IT OR TREAT IT AS NOISE" HAS NO ANSWER. IT IS SIGNAL AND
NOISE, AND THE LADDER IS WHAT SEPARATES THEM** -- read ONE stalk at
1 bit, and escalate to the population only when the single-stalk read
is refused.

**AND WITH NO CROWD AT ALL THE CHANNEL CANNOT BE READ**, because a
single path has no notch to invert. So the 1-bit case is not "one
stalk and nothing else" -- it is one stalk and SOME interference.

## THE MEASURED CAP, and it is not in conflict with the fail-up bench

    MEASURED_PEAK_POPULATION = 3

`bench_balance_final.py` measures the SURPLUS (capacity minus the
names of P stalks) and it peaks at 3 in all six conditions.
`bench_failup.py` measures the 1-bit DISCRIMINATION pass rate and finds
population 4 sharpest.

**THOSE ARE DIFFERENT FUNCTIONS OF P, NOT A CONTRADICTION** -- one is a
capacity question and one is an identification question. The surplus is
the one the ladder respects, because the surplus IS the width the
reading can carry.

## THE REFUSAL VOCABULARY, and which refusals escalate

Only the channel's OWN refusals escalate:

    channel_irrecoverable    the channel could not be inverted
    refuse_alignment         the reading does not match what was sent
    refuse_norm              the reading was too loud for the envelope
    refuse_gate              the gate refused it for another reason

A refusal for any other reason is a genuine refusal and climbing will
not change the answer, so the ladder stops and says why. **A ladder
that climbs on every refusal is a ladder that spends compute for
nothing.**
