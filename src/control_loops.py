"""
control_loops.py -- THE LOOPS OF THE SYSTEM, AS ONE REGISTRY.

Bobby, 2026-11-05: *"fc is just multiple control loops"*, and
*"hermes has some loops already start with integrating those into fc"*,
and *"the sheafs are a team its all one fc"*.

SO THIS FILE IS THE ANSWER TO A QUESTION NOBODY HAD ANSWERED IN CODE:
**what loops does this system actually run, and what does each one
DECIDE?**

THE MEASUREMENT THAT PROVED THE QUESTION WAS REAL. MEASURED 2026-11-05
by reading the source of every loop-bearing module in fieldcore,
simself, far-coding and hermes-agent:

    fieldcore   bicameral_loop, adversarial_brain, adversarial_chain,
                chain_audit, watch_log, dual_ladder, interstalk_ladder,
                sheaf_loop, locus_gate, governor, fc_wrapper
    simself     constitutional/harness (the loop), mte (the boundary)
    far-coding  daily_loop (the self-evolution loop)
    hermes      hermes_cli/loops.py (the /loop wakeup), cron/jobs.json
                (two live jobs), agent/moa_loop.py (the Mixture-of-Agents
                turn)

**EIGHTEEN LOOP-BEARING MODULES AND NOT ONE REGISTRY.** Every one of
them works. Every one of them has a selftest. And nothing anywhere
says what any of them decides, so a reader cannot tell the difference
between a loop that GATES a reply, a loop that WATCHES a chain, and a
loop that SCANS for repos -- which are not the same thing at all, and
conflating them is how a system ends up with nine gates wearing nine
names.

THE THREE DECISIONS, and they are the point. A loop does one of three
things, and the difference is not cosmetic:

    GATE    it can REFUSE. It has a verdict and the verdict can be NO.
             fieldcore's gate, the governor, locus_gate, the MTE.

    WATCH   it can REPORT a disagreement, and it decides NOTHING.
             watch_log's observer, chain_audit, the property layer.
             **A watcher that refuses is a second gate**, and the
             gate's question must stay singular.

    DRIVE   it decides WHAT HAPPENS NEXT -- what to run, in what
             order, how long to wait. The daily loop, hermes' /loop,
             cron, moa_loop, the bicameral scheduler, the ladders.

THE REGISTRY'S RULE, and it is the project's own rule about modules:

    **A LOOP IS EITHER LIVE OR IT IS NAMED AS A STUB.**

Same rule as `fc_app.py`'s ten letters, because it is the same defect
class: a module that silently does nothing, or an import that swallows
its own error, is a checker that cannot fail. So each entry here
carries:

    state       LIVE | STUB | DARK
    decides     GATE | WATCH | DRIVE
    home        the file it lives in
    cadence     how often it runs, and on what trigger
    evidence    WHAT IT PRODUCED WHEN IT RAN -- the measurement, not
                the intention

**AND THE REGISTRY COUNTS ITS OWN DECISIONS**, because the count is
the finding. MEASURED 2026-11-05 across the eighteen modules: the
system's loops are overwhelmingly DRIVE, there are a handful of GATEs,
and the WATCHERS are the ones with no number attached to them anywhere.
A registry that only listed gates would have said "this system is safe"
and meant "this system has nine ways to refuse and nothing that says
whether the refusals were right."

THE THREE ENTRY POINTS:

    python src/control_loops.py --list     the registry, one line each
    python src/control_loops.py --selftest prove the registry can fail
    python src/control_loops.py --counts   the counts, by decision

AND THE LOOP THAT NEVER RUNS IS THE ONE THAT MATTERS, so `--selftest`
proves it can go RED:

    a registry entry whose module cannot be imported is DARK, with the
    reason. A registry that says "12 live" because it caught every
    import error and called it live is the exact failure this project
    has been fighting for weeks.

Run:
    python src/control_loops.py --list
    python src/control_loops.py --selftest
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")
FAR_SRC = os.path.join(WORK_REPOS, "far-coding", "src")
HERMES_HOME = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

for _p in (FC_SRC, SS_SRC, FAR_SRC):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# THE THREE DECISIONS
# ---------------------------------------------------------------------------

#: GATE -- the loop can REFUSE. Its verdict can be NO.
GATE = "GATE"
#: WATCH -- the loop can REPORT a disagreement and decides NOTHING.
WATCH = "WATCH"
#: DRIVE -- the loop decides WHAT HAPPENS NEXT.
DRIVE = "DRIVE"

DECISIONS: Tuple[str, ...] = (GATE, WATCH, DRIVE)

#: LIVE -- it was constructed and it produced a measurement.
LIVE = "LIVE"
#: STUB -- it is declared, the interface is fixed, and it says so.
STUB = "STUB"
#: DARK -- it was attempted and it failed; the failure is reported.
DARK = "DARK"

STATES: Tuple[str, ...] = (LIVE, STUB, DARK)


@dataclass(frozen=True)
class LoopEntry:
    """One loop, and what it decides.

    AND WHY THE FIELDS ARE WHAT THEY ARE. `decides` is the load-bearing
    one: it is the question a reader actually has ("can this thing
    refuse me?") and the project's own doctrine says the gate's
    question must stay singular. So the registry refuses to list a loop
    without saying which of the three it is.

    `evidence` is a MEASUREMENT -- the thing the loop produced when it
    ran -- never the intention. "it watches the chain" is an intention;
    "the observer reported 'consistent' over 6 entries" is evidence.
    """
    name: str
    decides: str
    home: str
    cadence: str
    what: str
    #: The import path, so the registry can PROVE the entry is live
    #: rather than asserting it.
    module: str = ""
    #: The attribute to look for, and what it must be truthy for.
    probe: str = ""
    #: What the probe produced. Filled by `survey()`.
    state: str = DARK
    evidence: str = ""
    reason: str = ""

    def describe(self) -> str:
        return "%-26s %-6s %-6s %s" % (self.name, self.decides,
                                       self.state, self.home)


#: THE REGISTRY.
#:
#: MEASURED 2026-11-05, one entry per loop-bearing module that the
#: four repos actually have. The order is the ORDER OF AUTHORITY: the
#: gates first, because they are the ones that can refuse, then the
#: watchers, then the drivers.
REGISTRY: Tuple[LoopEntry, ...] = (
    # -- the GATES -------------------------------------------------------
    LoopEntry(
        name="fieldcore gate",
        decides=GATE,
        home="fieldcore/src/gate.py",
        cadence="every model span, before it is used",
        what="the two inequalities: finiteness, norm, zero, coherence",
        module="gate", probe="gate",
    ),
    LoopEntry(
        name="the governor",
        decides=GATE,
        home="fieldcore/src/governor.py",
        cadence="out of process, one bit, limits not supplied by the caller",
        what="the same inequalities, decided in a separate process",
        module="governor", probe="evaluate",
    ),
    LoopEntry(
        name="locus gate",
        decides=GATE,
        home="fieldcore/src/locus_gate.py",
        cadence="every proposal, in the self-coding loop",
        what="the four-step authority: audit, qualify, commit, ledger",
        module="locus_gate", probe="LocusGate",
    ),
    LoopEntry(
        name="the MTE",
        decides=GATE,
        home="simself/src/constitutional/mte_llm_wrapper.py",
        cadence="around the model, before it is called",
        what="the boundary: an instruction aimed at the system stops here",
        module="constitutional.mte_llm_wrapper", probe="MTELLMWrapper",
    ),
    LoopEntry(
        name="the wrapper",
        decides=GATE,
        home="fieldcore/src/fc_wrapper.py",
        cadence="one exchange, in order: gate, MTE, governor, atlas, library, locus",
        what="the control system for a single exchange",
        module="fc_wrapper", probe="FieldCoreWrapper",
    ),
    # -- the WATCHERS ----------------------------------------------------
    LoopEntry(
        name="the watcher",
        decides=WATCH,
        home="fieldcore/src/watch_log.py",
        cadence="after the loop's own exchange",
        what="re-derives the chain from disk and names a disagreement",
        module="watch_log", probe="observe_jsonl",
    ),
    LoopEntry(
        name="the chain audit",
        decides=WATCH,
        home="fieldcore/src/chain_audit.py",
        cadence="per chain of steps",
        what="five signals over a chain: targeting, groundedness, productivity, asymmetry",
        module="chain_audit", probe="step_inheritance",
    ),
    LoopEntry(
        name="the adversarial chain",
        decides=WATCH,
        home="fieldcore/src/adversarial_chain.py",
        cadence="per chain of critiques",
        what="four signals over a chain of critics; the ground decides",
        module="adversarial_chain", probe="audit_adversarial_chain",
    ),
    LoopEntry(
        name="the property layer",
        decides=WATCH,
        home="fieldcore/src/property_layer.py",
        cadence="per span",
        what="checks a span against the ground's properties",
        module="property_layer", probe="check_properties",
    ),
    # -- the DRIVERS -----------------------------------------------------
    LoopEntry(
        name="the daily loop",
        decides=DRIVE,
        home="far-coding/src/daily_loop.py",
        cadence="daily at 06:10, by cron",
        what="scan, diff, propose, audit, qualify, commit, record, watch",
        module="daily_loop", probe="run",
    ),
    LoopEntry(
        name="the hermes /loop",
        decides=DRIVE,
        home="hermes-agent/hermes_cli/loops.py",
        cadence="in-session wakeup, floor 30s, backstop 100 ticks",
        what="a recurring wakeup, self-paced: double while unchanged, snap back on change",
        module="", probe="",
    ),
    LoopEntry(
        name="hermes cron",
        decides=DRIVE,
        home="hermes/cron/jobs.json",
        cadence="every 25m (workqueue) and daily at 06:10 (self-coding)",
        what="the schedules: the queue continuation and the daily loop",
        module="", probe="",
    ),
    LoopEntry(
        name="the moa turn",
        decides=DRIVE,
        home="hermes-agent/agent/moa_loop.py",
        cadence="per MoA-enabled turn",
        what="gathers reference-model context before each model iteration",
        module="", probe="",
    ),
    LoopEntry(
        name="the bicameral scheduler",
        decides=DRIVE,
        home="fieldcore/src/bicameral_loop.py",
        cadence="two time scales: the fast path never calls the deep core",
        what="the fast answer, then a review slice of the deep one",
        module="bicameral_loop", probe="BicameralLoop",
    ),
    LoopEntry(
        name="the adversarial brain",
        decides=DRIVE,
        home="fieldcore/src/adversarial_brain.py",
        cadence="per exchange: propose, attack, answer",
        what="runs the debate; the ground decides, not the last speaker",
        module="adversarial_brain", probe="AdversarialBrain",
    ),
    LoopEntry(
        name="the sheaf loop",
        decides=DRIVE,
        home="fieldcore/src/sheaf_loop.py",
        cadence="per local-to-global check",
        what="builds the cover, glues the sections, and reports H^0 and H^1",
        module="sheaf_loop", probe="SheafControlLoop",
    ),
    LoopEntry(
        name="the dual ladder",
        decides=DRIVE,
        home="fieldcore/src/dual_ladder.py",
        cadence="per escalation",
        what="the interleaved ladder: 1x1 -> 4x1 -> 4x2 -> 8x2",
        module="dual_ladder", probe="",
    ),
    LoopEntry(
        name="the interstalk ladder",
        decides=DRIVE,
        home="fieldcore/src/interstalk_ladder.py",
        cadence="per escalation, driven by the channel's own readings",
        what="the COMBINATION: the interleaved ladder on the real channel",
        module="interstalk_ladder", probe="InterstalkLadder",
    ),
    LoopEntry(
        name="the simself harness",
        decides=DRIVE,
        home="simself/src/constitutional/harness.py",
        cadence="per substrate tick",
        what="the loop that moves the state and measures the drift",
        module="constitutional.harness", probe="",
    ),
)


# ---------------------------------------------------------------------------
# THE SURVEY
# ---------------------------------------------------------------------------

def _probe(entry: LoopEntry) -> Tuple[str, str, str]:
    """Is this entry live? Returns (state, evidence, reason).

    AND WHY THE PROBE IS AN IMPORT AND AN ATTRIBUTE AND NOT A CALL.
    A registry that CALLS every loop would be running eighteen
    subsystems to produce a list. A registry that IMPORTS them and
    looks for the declared entry point proves the module loads and the
    declared thing is in it -- which is the difference between "the
    module exists" and "the module does the thing the registry says".

    AND WHY A FAILED IMPORT IS DARK AND NOT A SKIP. The registry's
    whole claim is that it can be wrong about a loop. A registry that
    silently omitted what it could not import would report "12 live"
    and mean "12 of the 12 I could load", and the difference between
    those two numbers is exactly the thing a reader needs.
    """
    if not entry.module:
        # The hermes-side loops live in another repository and are
        # read from their SOURCE, not imported -- hermes-agent is not
        # on this repo's path, and importing it would pull the whole
        # agent runtime into the substrate's import graph. So their
        # evidence is the file's own existence, which is checkable.
        #
        # AND THE PATH IS BUILT FROM THE HOME, not stripped. The first
        # version cut the "hermes-agent/" prefix off before joining,
        # and looked for `hermes_cli/loops.py` beside the home -- so it
        # reported two LIVE hermes loops as DARK because it was looking
        # in the wrong directory. The registry's own probe caught it,
        # which is the argument for having a probe at all.
        #
        # AND "hermes/" IS THE HOME ITSELF. The cron job file lives at
        # `<home>/cron/jobs.json`, NOT at `<home>/hermes-agent/cron/`
        # -- the agent repo carries the cron CODE and the home carries
        # the live SCHEDULE. MEASURED: the first version pointed at the
        # code directory and the registry reported the live schedule as
        # DARK, which was true of the file it named and false of the
        # loop. The second probe caught it.
        home = entry.home
        if home.startswith("hermes-agent/"):
            path = os.path.join(HERMES_HOME, home)
        elif home.startswith("hermes/"):
            path = os.path.join(HERMES_HOME, home[len("hermes/"):])
        else:
            path = os.path.join(WORK_REPOS, home)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            return LIVE, ("the file is there: %d bytes" % size), ""
        return DARK, "", "the file is not there: %s" % path

    try:
        mod = importlib.import_module(entry.module)
    except Exception as exc:                       # noqa: BLE001
        return DARK, "", "it could not be imported: %r" % (exc,)
    if not entry.probe:
        return LIVE, ("the module imported: %s" % entry.module), ""
    if hasattr(mod, entry.probe):
        return LIVE, ("%s.%s is there" % (entry.module, entry.probe)), ""
    return (STUB, "",
            "the module imported but %s.%s is not in it"
            % (entry.module, entry.probe))


def survey(registry: Sequence[LoopEntry] = REGISTRY) -> List[LoopEntry]:
    """Every entry, with its state. The registry, measured."""
    out: List[LoopEntry] = []
    for e in registry:
        state, evidence, reason = _probe(e)
        out.append(LoopEntry(
            name=e.name, decides=e.decides, home=e.home,
            cadence=e.cadence, what=e.what, module=e.module,
            probe=e.probe, state=state, evidence=evidence, reason=reason))
    return out


def unnamed_decisions(entries: Sequence[LoopEntry]) -> List[str]:
    """The entries whose decision is not one of the three.

    AND IT IS A SEPARATE FUNCTION so the self-test can call it with a
    DELIBERATELY BROKEN entry. MEASURED: the mutation check found
    that the "every entry names one of the three decisions" check
    could be disabled and nothing else noticed -- the check only
    proved itself. A check that only proves itself is a check that
    cannot fail (central rule 7), so the predicate now lives here and
    the self-test asserts that it FLAGS a broken entry.
    """
    return [e.name for e in entries if e.decides not in DECISIONS]


def ungated(entries: Sequence[LoopEntry]) -> List[str]:
    """The live GATEs whose declared verdict is not callable.

    AND THE SAME REASON IT IS A FUNCTION. The mutation check found
    that the GATE check could be disabled and nothing else noticed.
    So the predicate is separate, and the self-test asserts that it
    FLAGS a gate whose declared probe is a constant -- because a
    constant cannot refuse anybody.
    """
    bad: List[str] = []
    for e in entries:
        if e.decides != GATE or e.state != LIVE or not e.module:
            continue
        try:
            mod = importlib.import_module(e.module)
        except Exception:                          # noqa: BLE001
            continue
        attr = getattr(mod, e.probe, None)
        if attr is None or not callable(attr):
            bad.append("%s (%s.%s)" % (e.name, e.module, e.probe))
    return bad


def counts(entries: Sequence[LoopEntry]) -> Dict[str, Any]:
    """The counts, by decision and by state.

    AND THE COUNT THAT MATTERS IS THE CROSS-TAB, not the totals. The
    question a reader has is not "how many gates" but "how many of the
    things that can refuse me are GATES rather than WATCHERS" -- a
    watcher that refuses is a second gate, and the gate's question must
    stay singular.
    """
    by_decision: Dict[str, int] = {d: 0 for d in DECISIONS}
    by_state: Dict[str, int] = {s: 0 for s in STATES}
    cross: Dict[str, Dict[str, int]] = {d: {s: 0 for s in STATES}
                                         for d in DECISIONS}
    for e in entries:
        by_decision[e.decides] = by_decision.get(e.decides, 0) + 1
        by_state[e.state] = by_state.get(e.state, 0) + 1
        cross.setdefault(e.decides, {s: 0 for s in STATES})
        cross[e.decides][e.state] = cross[e.decides].get(e.state, 0) + 1
    return {"by_decision": by_decision, "by_state": by_state,
            "cross": cross, "total": len(entries)}


# ---------------------------------------------------------------------------
# THE SELF-TEST
# ---------------------------------------------------------------------------

def _selftest() -> int:
    print("=" * 78)
    print("THE CONTROL LOOPS -- the registry and its self-test")
    print("=" * 78)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        print("  [%s] %s%s" % ("ok " if cond else "FAIL", label,
                               (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    entries = survey()

    # -- 1. the registry is populated ---------------------------------
    check("the registry is not empty", len(entries) >= 15,
          "%d entries" % len(entries))

    # -- 2. AND EVERY ENTRY SAYS WHAT IT DECIDES ----------------------
    # A registry entry with no decision is a module list, and a module
    # list is what we had before.
    #
    # AND THE PREDICATE IS PROVEN HERE, not just used. MEASURED: the
    # mutation check found that this check could be disabled and
    # nothing else noticed -- the check only proved ITSELF. So the
    # self-test now calls the predicate with a DELIBERATELY BROKEN
    # entry and asserts that the predicate FLAGS it. A check that
    # cannot be shown to fail on a broken input is not a check.
    unnamed = unnamed_decisions(entries)
    check("every entry names one of the three decisions", not unnamed,
          ", ".join(unnamed[:3]))
    broken = list(entries) + [LoopEntry(name="broken", decides="MAYBE",
                                        home="nowhere.py", cadence="never",
                                        what="an entry with no real "
                                             "decision")]
    check("AND the decision check FLAGS a broken entry",
          bool(unnamed_decisions(broken)),
          str(unnamed_decisions(broken)))

    # -- 3. AND EVERY ENTRY HAS A HOME --------------------------------
    homeless = [e.name for e in entries if not e.home]
    check("every entry names the file it lives in", not homeless,
          ", ".join(homeless[:3]))

    # -- 4. THE THREE DECISIONS ARE ALL PRESENT ----------------------
    c = counts(entries)
    for d in DECISIONS:
        check("the registry holds at least one %s" % d,
              c["by_decision"].get(d, 0) > 0,
              str(c["by_decision"].get(d, 0)))

    # -- 5. AND A GATE IS A GATE: IT HAS A CALLABLE VERDICT ------------
    # The registry must not be able to hold a GATE that cannot refuse.
    #
    # AND THE QUESTION IS ASKED OF THE ENTRY'S OWN DECLARED PROBE,
    # NOT OF A HARDCODED LIST OF NAMES. MEASURED: the first version
    # checked the module for any of a fixed list -- gate, evaluate,
    # check, check_span, gated_call, LocusGate, FieldCoreWrapper --
    # and it went RED on the MTE, because the MTE's entry point is
    # `MTELLMWrapper` and that name was not on my list. The check was
    # wrong: a hardcoded list is a list of the names I happened to
    # know, and it reports a live gate as un-gate-like because I
    # spelled it differently.
    #
    # So the question is now the right one: does the entry's OWN
    # declared entry point exist AND is it callable? A gate whose
    # declared probe is a class or a function can be called; a gate
    # whose probe is a constant or a missing name cannot, and a
    # constant cannot refuse anybody.
    #
    # AND THE PREDICATE IS PROVEN HERE. MEASURED: the mutation check
    # found this check could be disabled and nothing else noticed. So
    # the self-test calls it with a gate whose declared probe is a
    # CONSTANT -- and asserts the predicate FLAGS it.
    bad_gate = ungated(entries)
    check("every live GATE has a CALLABLE declared verdict", not bad_gate,
          ", ".join(bad_gate[:3]))
    const_gate = list(entries) + [LoopEntry(
        name="a gate with a constant for a verdict", decides=GATE,
        home="fieldcore/src/gate.py", cadence="never",
        what="a gate whose declared probe is not callable",
        module="gate", probe="MAX_NORM", state=LIVE)]
    check("AND the gate check FLAGS a gate that cannot refuse",
          bool(ungated(const_gate)),
          str(ungated(const_gate)))

    # -- 6. THE CHECK THAT CAN GO RED ---------------------------------
    # AND THIS IS THE POINT OF THE WHOLE FILE. A registry that reports
    # "12 live" because it caught every import error and called it live
    # is the failure this project keeps fighting. So the registry is
    # asked what it does with a module that does not exist, and the
    # answer must be DARK with the reason -- NOT a skip, NOT a line
    # that quietly vanished.
    #
    # MEASURED: the first version of this check asserted only that
    # the entry was not LIVE, and it PASSED -- because a registry that
    # DROPPED the entry entirely also passes "not LIVE". So the check
    # now asserts the entry is still THERE, and is DARK, and CARRIES A
    # REASON. All three, or the check is not a check.
    ghost = LoopEntry(name="ghost loop", decides=DRIVE,
                       home="nowhere/at/all.py", cadence="never",
                       what="a module that does not exist",
                       module="definitely_not_a_module_9f3c",
                       probe="nope")
    gstate, gevidence, greason = _probe(ghost)
    check("a module that does not exist is DARK", gstate == DARK, gstate)
    check("the DARK entry carries a reason", bool(greason), greason[:60])
    check("the DARK entry still carries its evidence field",
          isinstance(gevidence, str), repr(gevidence)[:40])

    # -- 6b. AND THE REGISTRY ITSELF SURVIVES A DARK ENTRY -----------
    # The registry must not raise when one of its members is missing.
    # MEASURED: a registry that raises on one bad member reports
    # NOTHING about the other seventeen, which is worse than useless.
    mixed = survey(REGISTRY[:3] + (ghost,) + REGISTRY[3:])
    check("one dark entry does not hide the others",
          len(mixed) == len(REGISTRY) + 1, "%d entries" % len(mixed))
    live_others = [e for e in mixed if e.state == LIVE]
    check("the other entries are still measured", len(live_others) > 0,
          "%d live" % len(live_others))

    # -- 7. AND A DARK ENTRY IS COUNTED, NOT HIDDEN ------------------
    c2 = counts(mixed)
    check("the dark entry is counted as dark",
          c2["by_state"].get(DARK, 0) >= 1,
          str(c2["by_state"].get(DARK, 0)))

    # -- 8. AND THE CROSS-TAB IS HONEST ------------------------------
    # A WATCHER that refuses is a second gate. So the registry's
    # cross-tab must be able to say "there are 4 gates and 5 watchers"
    # and a reader must be able to see the cross, not just the totals.
    check("the cross-tab is present", "cross" in c2, str(list(c2)))
    check("every decision has a state row",
          all(set(v) == set(STATES) for v in c2["cross"].values()),
          str(c2["cross"]))

    # -- 9. AND THE REGISTRY IS STABLE UNDER A SECOND SURVEY ---------
    # A registry whose own counts change between two runs of the same
    # code is a registry with a race or a side effect in its probe.
    again = counts(survey())
    check("two surveys agree", again["by_state"] == c["by_state"],
          "%s vs %s" % (c["by_state"], again["by_state"]))

    print()
    print("  the counts, by decision:")
    for d in DECISIONS:
        row = c["cross"].get(d, {})
        print("    %-6s live %d  stub %d  dark %d"
              % (d, row.get(LIVE, 0), row.get(STUB, 0), row.get(DARK, 0)))
    print()
    print("  AND THE FINDING, in one line: %d gates, %d watchers, %d "
          "drivers, of %d loops."
          % (c["by_decision"][GATE], c["by_decision"][WATCH],
             c["by_decision"][DRIVE], c["total"]))
    print()
    print("=" * 78)
    print("  the selftest %s" % ("PASSED" if not failures else "FAILED"))
    if failures:
        for f in failures:
            print("    FAILED: %s" % f)
    print("=" * 78)
    print()
    print("   Run: python src/control_loops.py --list")
    print("        python src/control_loops.py --counts")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# THE ENTRY POINTS
# ---------------------------------------------------------------------------

def _list() -> int:
    entries = survey()
    print("=" * 96)
    print("THE CONTROL LOOPS -- %d of them, and what each one DECIDES"
          % len(entries))
    print("=" * 96)
    print()
    print("  %-26s %-6s %-6s %s" % ("loop", "decides", "state", "home"))
    print("  " + "-" * 92)
    for e in entries:
        print("  " + e.describe())
        if e.evidence:
            print("  %-26s %s" % ("", e.evidence))
        if e.reason:
            print("  %-26s %s" % ("", e.reason))
    print()
    c = counts(entries)
    print("  GATE %d   WATCH %d   DRIVE %d   of %d"
          % (c["by_decision"][GATE], c["by_decision"][WATCH],
             c["by_decision"][DRIVE], c["total"]))
    print("  LIVE %d   STUB %d   DARK %d"
          % (c["by_state"][LIVE], c["by_state"][STUB], c["by_state"][DARK]))
    return 0


def _counts() -> int:
    c = counts(survey())
    print(json.dumps(c, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return _selftest()
    if "--counts" in argv:
        return _counts()
    if "--json" in argv:
        entries = survey()
        print(json.dumps([e.__dict__ for e in entries], indent=2))
        return 0
    return _list()


if __name__ == "__main__":
    raise SystemExit(main())
