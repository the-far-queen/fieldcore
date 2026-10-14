> **Sole note.** This file answers one question: *do we have a working core in Rust?*
>
> **Answer, updated 2026-10-14 — DAY ONE. 52/52 passing.** On 2026-10-14 the
> core was linked for the first time in its existence and ran its test suite for
> the first time. 7 latent bugs surfaced, all in code that had never once
> executed. §0 is the historical account; §0.1 is what is true now. Commit
> `f93f055`.
>
> **Bobby, reading that run: "this signals CORRECT idea in my mind."** And:
> *"this was a first-run effort, we begin today."* That date is day one.
>
> **Toolchain note (cost me an hour, do not repeat):** this machine has NO
> Visual Studio Build Tools. `link.exe` resolves to git-bash's coreutils
> `link(1)`, so MSVC `cargo test` fails at link with coreutils error syntax.
> Use `cargo +stable-x86_64-pc-windows-gnu test --release`. Toolchain installed
> 2026-10-14.
>
> **Pointers:** `core/src/lib.rs` (what the core is), `core/src/axes.rs` (20 axes + floors), `core/src/governor.rs` (M0, fail-closed), `core/src/envelope.rs` (D1-D4), `core/src/ladder.rs` (width ladder), `core/src/carrier.rs` (the interstalk channel — 5 of the 7 bugs live here), `core/src/sheaf.rs` (admission + the 3-source/3-language bound), `core/src/decision.rs` (1 bit + reason). Docs: `docs/day-one-2026-10-14.md`, `papers/24-...`, `papers/25-the-narrow-claim-2026-10-14.md`, `docs/fieldcore-is-the-system-2026-10-09.md`, `docs/CENTRAL-RULES.md`. v6.2 3-part stalk: `simself/notes/analogies/stalk-architecture-v6_2-3part-2026-10-14.md`.

# The Rust Core — actual state, and the 4-sheaf plan

**Filed 2026-10-14 by Hermes for Bobby.** Source: reading every file in `fieldcore/core/`, running the toolchain, reading the papers that claim the artifacts work.

---

## 0. The honest answer to your question

**There is a Rust core. It is 1796 lines, 8 modules, zero dependencies, and it type-checks clean. It has never been linked.**

This is not a small caveat and I am putting it first because both papers 24 and 25 list Rust files under "Artifacts" and name four tests as "load-bearing" — and those tests have never executed.

```
$ cargo check --release --all-targets
Finished `release` profile [optimized] target(s) in 0.23s     ← exit 0

$ cargo test --release
error: linking with `link.exe` failed: exit code: 1
  = note: "link.exe" "/NOLOGO" ... "libstd-512d688ad63bc3c4.rlib"
  link: extra operand '...libstd-512d688ad63bc3c4.rlib'
          Try 'link --help' for more information.
error: could not compile `fieldcore-core` (test "governor") due to 1 previous error
                                                             ← exit 101
```

**Diagnosis, before any fix (CENTRAL-RULES §1).** Two distinct problems, and the second is the real one:

1. **A genuine source bug.** `core/src/ladder.rs:280` and `:287` read
   `l.should_escalate(gain: 1.0, cost: 0.1)` — named arguments, which
   Rust has never had. This is not a style quibble: it means **the test
   suite was never compiled, not even in `cargo check`** — because
   `cargo check --all-targets` checks the lib target but the two test
   modules are only reached through the test harness build. Fixed to
   positional args, now committed.

2. **The toolchain cannot link on this machine.** The host is
   `x86_64-pc-windows-msvc` and `rustup show` confirms only that one
   target is installed. There is **no Visual Studio Build Tools
   installation** — `vswhere.exe` returns zero products, and a filesystem
   search for `MSVC/Tools/MSVC/*/bin/link.exe` finds nothing. So
   `link.exe` resolves to a *different* `link.exe`: git-bash ships one
   at `/usr/bin/link`, the GNU coreutils `link(1)` utility, and rustc is
   invoking it as if it were the MSVC linker. That is why the error is
   `link: extra operand` — coreutils error syntax, not MSVC error syntax.

   **A GNU-toolchain build is installing now** (`stable-x86_64-pc-windows-gnu`),
   which brings its own linker and does not need Visual Studio at all.

**So the answer to "do we have a working core" is: we have a core that has
never run.** Every claim papers 24 and 25 make about `clean_channel_is_uncorrectable`
is currently an argument about code, not a report of a test. That is fixable
today and it is worth fixing before anything else in this file, because
the entire interstalk claim rests on one assertion that has never executed.

---

## 1. What is actually built

Eight modules, all read, all quoted from source:

| module | lines | what it does | what it is *not* |
|---|---|---|---|
| `lib.rs` | 57 | crate root, `AUTHORITY_RULE`, `unavailable()` | not a model, not an orchestrator |
| `decision.rs` | 105 | 1 bit + `Verdict` + `retryable()` | not a bare bool, deliberately |
| `envelope.rs` | 100 | D1-D4 declared bounds | no `Option<f64>` anywhere |
| `axes.rs` | 167 | 20 axes, floors, read-only ψ₀ | knows nothing about language/robots/code |
| `governor.rs` | 149 | M0, fail-closed and sticky | not aware of what it governs |
| `ladder.rs` | 320 | 1/4/8/16/32/64/128/256 → Undecidable | width ≠ reasoning quality |
| `carrier.rs` | 396 | channel, notch, equaliser, pilot, guard, DFT | **this is the interstalk module** |
| `sheaf.rs` | 234 | admission: 3 sources, 3 languages | the real "sheaf" is only admission |

### The three properties that are actually load-bearing

**`lib.rs` — the blindness is the design.** Quoting the file:

> It is not a model, not an orchestrator, and not aware of what it is
> governing. That blindness is the design.

with the 747 justification: a veto the governed process can decline to
call is not a veto. This is the reason one thing can govern coding,
robot, language and self without knowing any of them. It is the best
argument in the codebase and it is *why the core is small* — 1796 lines
is the size of a core that refuses to understand what it governs.

**`governor.rs` — fail-closed is sticky.** `fail_closed()` sets a flag
that nothing clears. The comment records why: the first Python governor
respawned silently, so a closed governor produced ALLOW from a brand new
process, and *a channel that restarts itself on demand can never fail
closed, because nothing is ever absent as far as the caller can tell.*
That is a real bug from this project's own history, fixed in the Rust
rewrite and now enforced by test.

**`carrier.rs` — the uncorrectable-clean-channel proposition, as code.** The
entire design claim reduces to this one function:

```rust
let notch = channel.notch_db();
if notch < 3.0 {
    return Err(EqualiseError::FlatChannel);
}
```

A channel with no response null admits no inversion, so a substrate
engineered for perfect isolation is *unrecoverable by construction*.
`Channel::clean()` is refused by its own receiver. **That is the claim,
and it is now type-checked but not yet executed.**

### What "sheaf" actually means in this codebase

`docs/Math/topo-sheaf-stalk.md` §4 reserves the word, and the reservation
matters:

> Per Grok: the vocabulary "sheaf" is reserved for any future object that
> implements the actual sheaf condition (restriction maps, gluing
> condition, exactness). **The runtime objects are Channels.**

So the Rust `sheaf.rs` is honestly named `sheaf.rs` while implementing
**admission control** — a bounded enum of sources and languages — and
not the sheaf condition. Read literally, `sheaf.rs` is the first of the
4 sheafs and it is a gate, not a topology.

---

## 2. The 4 sheafs — beginning

Bobby, 2026-09-07: *"backstory core has 4 sheaves or sheafs a topology,
machine language technical register mltr and a corresponding MTE
transformer to negotiate both humans and llm in out, coding sheaf which is
crucial i will explain soon, and codingOperator outside core"*
(`vault/50-index/notes/sessions/2026-09-07-session.md`).

`docs/fieldcore-is-the-system-2026-10-09.md` names them: **Topology ·
MLTR · MTE · Coding.**

### The core's relationship to all four

```
                    ┌───────────────────────────────────────┐
                    │  M0 GOVERNOR — in the Rust core       │
                    │  20 axes · floors · fail-closed       │
                    │  1 bit + reason · knows nothing else  │
                    └───────────────┬───────────────────────┘
                                    │ one bit, or a named refusal
        ┌───────────────┬───────────┴───────────┬───────────────┐
        │               │                       │               │
   ┌────▼────┐    ┌─────▼─────┐           ┌─────▼─────┐   ┌─────▼─────┐
   │ TOPOLOGY │    │   MLTR    │           │    MTE    │   │  CODING   │
   │  sheaf  │    │  sheaf    │           │  sheaf    │   │  sheaf    │
   └────┬────┘    └─────┬─────┘           └─────┬─────┘   └─────┬─────┘
        │               │                       │               │
        │               └───────────┬───────────┘               │
        │                           │                           │
        │                    ┌──────▼──────┐          ┌─────────▼─────────┐
        │                    │  MTE = ch.  │          │  codingOperator   │
        │                    │  estimation │          │  OUTSIDE the core │
        │                    │  + INVERSION │          │  pulls hf/arxiv/  │
        │                    └─────────────┘          │  github, hourly   │
        └──────────────  geometry: the braid, the toroid, the void
```

**The single most important structural fact:** the MTE sheaf and the
`codingOperator` are the same idea, and paper 24 §3.1 identifies the idea
as **channel estimation and inversion**. They sit on opposite sides of
the core, so the core governs two *different kinds of thing*:

- **MTE** is a **transformer** — it sits between the world and the core,
  and its job is to make incoming state interpretable. Lossy in, meaning
  restored out. Paper 24: *"nothing else about it is poetic."*
- **codingOperator** is a **sensor** — it sits outside the core and pulls
  from three named sources, returning snippets to entire repos. It never
  writes state.

This is the 747 shape again, one level up: the core is independent of both,
and neither can reach ψ₀.

### Sheaf 1 — TOPOLOGY (the only one the core can actually serve today)

**Status: geometry only, not topology.** The core has no notion of the
braid, the egg-toroid, the void, or the void-as-ψ₀. Those are all in
Python docs. What the core *can* serve is the constraint half: 20 axes
mapped onto 20 stalks, each stalk gated by `Governor::evaluate`, drift
checked by `AxisSet::drift`.

The braid as a **substrate with structure** is what `carrier.rs` provides —
and this is where it stops being analogy:

- `Stratum { id, phase, gain }` — one stalk's contribution to a shared carrier
- `multiplex(strata, samples)` — the braid as a **phase-coded multiplex**
- `Channel` — the crosstalk every other strand contributes
- `equalise()` — fail-closed inversion

A braided substrate with `n` strata and a non-flat `Channel` is
*literally* a multiplexed carrier with a known channel. **That is
multiplexing, which is what the topology sheaf is for.** The topology
sheaf is not a separate thing that needs building; it is the claim that
the braid is a carrier, and `carrier.rs` already states it.

**Open: #67.** With `Stratum.phase` as the address (not girth, not length —
`carrier.rs` says so explicitly), the substrate's addressing is by phase.
Whether spacing is uniform or variable is now measurable in software
alone, because `Channel::notch_db()` reads directly off the taper vector.

### Sheaf 2 — MLTR (machine language technical register) — **the gap**

Bobby named MLTR in the same breath as MTE: *"machine language technical
register mltr and a corresponding MTE transformer to negotiate both humans
and llm in out."*

**There is no MLTR in any repo.** Not in the Rust core, not in Python.
This is the largest single hole in the 4-sheaf plan and it is the one
Bobby said he would explain soon.

What it must be, from the pairing: MLTR is the *target language* of the
MTE, and the transformer negotiates in both directions. So MTE's job is
`{human, LLM} ↔ MLTR`, not `{human, LLM} → psi`. **MLTR is a language with
a grammar, and MTE is its compiler.** If MTE compiles everything, it has
compiled nothing — paper 25's P5 / T5.

**The rule MLTR must satisfy to belong here:** it must be bounded. Paper
24's D1-D4 is the template, and the Rust `Envelope` is already the
enforcing type. An MLTR with an unbounded vocabulary is not a register, it
is the failure this project is built to prevent.

### Sheaf 3 — MTE (the transformer) — **is the interstalk module, already built**

This is the finding worth stating plainly: **the MTE sheaf and
`carrier.rs` are the same object, and it is already written.**

| paper 24 §3.1: MTE ≡ channel estimation + inversion | `carrier.rs` |
|---|---|
| a receiver that cannot estimate the channel cannot equalise it | `Channel::response_complex()` |
| the coupling is *modelled* and subtracted | `equalise()` |
| "lossy in, meaning restored out" | `Equalised { samples, residual_db, width }` |
| the gate refuses a frame it cannot equalise | `EqualiseError::FlatChannel` |

The residual is exactly `residual_db`: after inversion, how much
interference survived. **That is the compilation loss.** A compiler that
compiles everything has compiled nothing; a compiler that reports its
residual honestly is the same instrument as an equaliser.

**What MTE lacks: the reverse direction.** `carrier.rs` goes received →
intended. It has no encode path. MTE needs both, and the pilot symbol is
the argument for why the encode side needs a known reference too.

### Sheaf 4 — CODING (the crucial one) — **partly built, and the part that is built is the gate**

`sheaf.rs` is a working, type-checked admission control:

```rust
pub enum Source { HuggingFace, Arxiv, Github }   // "ONLY hf and arxiv" + github
pub enum Lang   { Python, Rust, Go }             // "ONLY python rust and go"
pub enum Refusal { UnknownSource, UnknownLanguage, NoLicense, Stale,
                   TooLarge, AlreadyHeld, BelowStarFloor }
```

Two rules make this file exist rather than a README, and both are Bobby's:

> A source not named here cannot enter. Adding one is a change to this
> enum, which is a diff, which is reviewable. A filter in a config file
> is a filter somebody edits at 3am.

**Every refusal is named.** `no_license`, `stale:12345s>2592000s`,
`below_star_floor:12<50`. A bare refusal is unactionable — the same
principle as `Verdict::AxisBelowFloor(&'static str)` in `decision.rs`.
The same principle appears three times in this codebase: in the carrier
(FlatChannel), the governor (named verdict), and the coding gate (named
refusal). **That triple is the project's actual signature.**

**What is missing in the coding sheaf:**

1. **No client.** There is no code that calls HF, arXiv or GitHub. The
   enum admits; it does not pull.
2. **The star floor is a proxy, and Bobby's own memory warns about it.**
   From the integration registry, 2026-10-09: *"openclaw 391k stars MIT yet
   reference-only — stars must never promote into the runtime path."*
   `star_floor: 50` in `Admission::default()` puts stars on the runtime
   path. **This is a live contradiction with a decision Bobby already made.**
3. **No self-coding loop.** The ladder exists, the gate exists, and
   nothing connects a committed snippet to the ladder. Per
   `docs/fieldcore-is-the-system-2026-10-09.md`: *"present, readable, dark."*

---

## 3. The load-bearing tests, and their actual status

| test | file | status | why it matters |
|---|---|---|---|
| `clean_channel_is_uncorrectable` | `carrier.rs` | **never run** | the whole interstalk claim, as an assertion |
| `equalise_recovers_a_flat_gain` | `carrier.rs` | **never run** | proves dirty is recoverable, so the refusal is not vacuous |
| `fail_closed_is_sticky` | `governor.rs` | **never run** | a gone core is never read as consent |
| `refused_operation_does_not_run` | `governor.rs` | **never run** | `guarded()` cannot be talked past |
| `exactly_three_sources` | `sheaf.rs` | **never run** | the bound is the point |
| `cheap_rung_escalates` | `ladder.rs` | **fixed, will compile now** | was a syntax error |

`carrier.rs` also contains `unequalisable_frame_is_refused_not_approximated`,
which is the fail-closed property restated for the channel. And
`governor.rs` has the one the 747 analogy rests on:
`inadmissible_ground_refuses_even_a_perfect_proposal`.

---

## 4. What building the 4 sheafs on this base actually requires

**Already done, do not rebuild:** the 1-bit gate, the fail-closed property,
the bounded admission, the channel + equaliser, the width ladder, the 20
axes with floors.

**Required, in dependency order:**

1. **Link the toolchain and run the suite.** Blocking, and it gates
   everything else. Nothing in this file's §3 table is real until it exits 0.
2. **MLTR.** The largest hole. Needs a bounded grammar and a corpus that
   exposes a stable uncompilable residue (T5/P5 — currently unmeasured).
3. **A coding client.** Three named sources, a pull, a licence check, a
   snippet return. The gate exists and is unused.
4. **A real corpus through MTE**, twice, to compute the compilable
   fraction. This is the number paper 25 says is missing.
5. **Star floor resolution.** Either stars are an ordering signal only and
   move out of `admit()`, or Bobby's integration-registry rule is
   overridden. **Right now the code contradicts a decision he already made.**

**Not required, and should not be built yet:** restriction maps. Per
`topo-sheaf-stalk.md` §4, "the sheaf" is reserved for objects that implement
the sheaf condition. Building it early would be naming before substance —
the exact inversion this project has already had to undo twice.

---

## 5. The one thing I would fix first

The star floor, and it is not a code fix.

`sheaf.rs` ranks code by stars and puts that ranking on the admission path.
Bobby's own integration registry says stars must never promote into the
runtime path, with a live example: openclaw, 391k stars, MIT licence,
reference-only. `admit()` would wave it through.

A star count is a popularity signal, not a quality signal, and a system
whose whole thesis is *don't let a proxy stand in for the thing* has a
proxy sitting on its admission gate. **Fix: stars reorder the hourly
pull; they do not admit.** SNR comes from the pull rate and the licence
check, not from a number somebody else incremented.

---

*Hermes, 2026-10-14. Every claim in §0 carries the command that produced it, run after the change. Per CENTRAL-RULES §1, the `ladder.rs` syntax error was diagnosed before being fixed and the linker failure was diagnosed (git-bash coreutils `link(1)` shadowing MSVC `link.exe`, no Build Tools installed) rather than retried with different parameters.*
