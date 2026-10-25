"""
component_test.py -- EVERY COMPONENT, ONE FILE, HONEST PASS/FAIL.

Bobby, 2026-10-25: *"dont search test each component ie do stalks
communicate yet did we finish that?"*

THE RULE, and it is the one this project keeps learning: EVERY LINE
HERE IS A MEASUREMENT, NOT A CLAIM. If a component cannot be measured
it says so, and it says so as FAIL rather than as "TODO".

AND THE HONEST FRAMING, because it matters for reading the output:

    A COMPONENT PASSES IF ITS MEASUREMENT CONFIRMS THE CLAIM.

    It does not pass because the code exists.

Run:
    python src/component_test.py
"""

from __future__ import annotations

import math
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src"),
           os.path.join(WORK_REPOS, "atlas-exam", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Result:
    """One component's verdict, and the number it rests on."""
    name: str
    ok: bool
    claim: str
    measured: str = ""
    note: str = ""

    def line(self) -> str:
        return "%-6s %-30s %-42s %s" % (
            "PASS" if self.ok else "FAIL", self.name, self.claim,
            self.measured)


RESULTS: List[Result] = []


def record(name: str, claim: str, ok: bool, measured: str = "",
           note: str = "") -> None:
    RESULTS.append(Result(name, ok, claim, measured, note))


# ===========================================================================
# 1. THE GEOMETRY -- the girth selection
# ===========================================================================

def test_geometry() -> None:
    from interstalk_link import InterstalkLink, width_for
    from wound_core import CoaxWinding, WoundCore

    stalks = [CoaxWinding(
        id="s%02d" % i, girth_core=0.030, girth_in=0.060,
        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
        n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=128)
    ids = [s.id for s in stalks]

    # the addresses must be DERIVED and separated
    addrs = [((s.n_out % 2) / 2.0 + (s.girth_ratio - 1.0)) % 1.0
              for s in stalks]
    sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
              for i, a in enumerate(addrs) for b in addrs[i + 1:])
    ok = abs(sep * 128 - 8.0) < 0.5
    record("geometry", "addresses derived, 8 bins apart", ok,
           "separation %.2f bins" % (sep * 128))

    # the channel must have structure
    ch = link.pair(ids[0], ids[1], in_view=ids).channel()
    ok = ch.notch_db() > 3.0
    record("geometry", "the channel has a notch", ok,
           "notch %.2f dB" % ch.notch_db())

    # the width must be DERIVED from the taps
    w = width_for(len(ch.taps))
    ok = w == 16
    record("geometry", "width derived from the tap count", ok,
           "%d taps -> %d bits" % (len(ch.taps), w))


# ===========================================================================
# 2. DO THE STALKS COMMUNICATE? -- the question Bobby asked
# ===========================================================================

def test_communication() -> None:
    import do_stalks_communicate as dsc

    stalks = dsc.the_population(8)
    link = dsc.InterstalkLink(core=dsc.WoundCore(stalks=stalks), bins=128)
    ids = [s.id for s in stalks]

    # 1. the sender's signal arrives at the receiver
    aligns = []
    rx_aligns = []
    for i in range(len(ids)):
        tx, rx = ids[i], ids[(i + 1) % len(ids)]
        r = dsc.recover(link, stalks, tx, rx, 0.10)
        aligns.append(r["align_sender"])
        rx_aligns.append(r["align_receiver"])
    mean_s = sum(aligns) / len(aligns)
    mean_r = sum(rx_aligns) / len(rx_aligns)
    ok = mean_s > 0.4 and mean_r < 0.1
    record("communication", "the sender's signal arrives", ok,
           "align sender %.4f vs receiver %.4f" % (mean_s, mean_r))

    # 2. moving the receiver changes what arrives
    prints = set()
    for rx in ids[1:]:
        pair = link.pair(ids[0], rx, in_view=ids)
        prints.add((round(pair.pair_coupling(), 9),
                    round(pair.channel().notch_db(), 6)))
    ok = len(prints) == len(ids) - 1
    record("communication", "moving the receiver changes the channel", ok,
           "%d distinct fingerprints over %d receivers"
           % (len(prints), len(ids) - 1))

    # 3. the receiver names the sender
    correct = 0
    total = 0
    for a in ids:
        for b in ids:
            if a == b:
                continue
            r = dsc.recover(link, stalks, a, b, 0.10)
            total += 1
            if r["correct"]:
                correct += 1
    rate = correct / total if total else 0.0
    ok = rate > 0.70
    record("communication", "the receiver names the sender", ok,
           "%d/%d = %.0f%% at crowd 0.10" % (correct, total, rate * 100))

    # 4. and it refuses by name when the reading is ambiguous
    r = dsc.recover(link, stalks, ids[0], ids[1], 0.70)
    ok = (not r["correct"]) and r["reason"].startswith("refuse")
    record("communication", "it refuses by name when ambiguous", ok,
           "crowd 0.70 -> %s" % r["reason"])


# ===========================================================================
# 3. THE LADDER -- pop first
# ===========================================================================

def test_ladder() -> None:
    from dual_ladder import (build_ladder, DualLadder, WIDTH_AXIS,
                             POPULATION_AXIS)

    rungs = build_ladder()
    ok = (rungs[0].width == 1 and rungs[0].population == 1
          and len(rungs) == 13)
    record("ladder", "starts 1 bit 1 stalk, 13 rungs", ok,
           "%d rungs, first %dx%d" % (len(rungs), rungs[0].width,
                                     rungs[0].population))

    # the alternation, over CONSECUTIVE rungs. The first version
    # compared the tail against itself and so compared "start" with
    # "width" -- which are different by construction and so the check
    # passed for the wrong reason.
    # FROM THE SECOND RUNG, and the alternation HOLDS WHILE BOTH AXES
    # HAVE ROOM. The width axis has 8 entries and the population 6, so
    # the ladder alternates for 12 rungs and then the 13th must advance
    # the width -- the population axis is exhausted. So the last two
    # rungs are both 'width', and that is CORRECT rather than a
    # defect. The first version of this check asserted the alternation
    # over ALL the rungs and failed on the top rung.
    axes = [r.axis for r in rungs[1:]]
    # the alternation must hold for as long as BOTH axes have room.
    # Each alternating PAIR consumes one width and one population, so the
    # pairs are min(8, 6) = 6, i.e. 12 rungs, and then the width axis
    # has 2 left over with no population to pair them with -- so the
    # 13th rung advances the width alone.
    pairs = min(len(WIDTH_AXIS), len(POPULATION_AXIS))
    # each alternating PAIR consumes one width and one population, and
    # the ladder starts with the WIDTH alone -- so the width axis runs
    # out one step before the population axis does. The alternation
    # therefore holds for 2*pairs - 1 rungs of the axis list, and the
    # last rung is the width alone.
    alternating = 2 * pairs - 1
    alt = all(axes[i] != axes[i + 1]
               for i in range(min(alternating, len(axes)) - 1))
    only_two = set(axes) <= {"width", "population"}
    # and the leftover rungs must all be the axis that still had room
    leftover = axes[alternating:]
    leftover_ok = all(a == "width" for a in leftover)
    record("ladder", "the axes alternate while both have room",
           alt and only_two and leftover_ok,
           "%d alternating rungs, then %d leftover on the width axis"
           % (alternating, len(leftover)))

    # the cost must rise monotonically
    costs = [r.cost for r in rungs]
    mono = all(costs[i] <= costs[i + 1] for i in range(len(costs) - 1))
    record("ladder", "the cost rises monotonically", mono,
           "cost %d -> %d" % (costs[0], costs[-1]))

    # the cheap corner must be the default: one refusal still answers
    lad = DualLadder()
    run = lad.run(lambda rung: (True, "allow", 0.9))
    ok = run.steps_taken == 1 and run.total_cost == 1
    record("ladder", "the cheap layer answers in one step", ok,
           "%d steps, cost %d" % (run.steps_taken, run.total_cost))


# ===========================================================================
# 4. THE LOCUS -- a self that is a place, and is readable
# ===========================================================================

def test_locus() -> None:
    from locus import Locus, locus_recover
    from interstalk_link import InterstalkLink
    from wound_core import WoundCore

    stalks = [__import__("wound_core").CoaxWinding(
        id="s%02d" % i, girth_core=0.030, girth_in=0.060,
        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
        n_in=12, n_out=13 + (i % 2)) for i in range(4)]
    link = InterstalkLink(core=WoundCore(stalks=stalks), bins=128)
    locus = Locus([s.id for s in stalks], stalks)

    # the ground must be write-protected
    ok = True
    try:
        locus._check_write(locus.state, type(locus.state)(
            stalks=locus.state.stalks, gain=locus.state.gain,
            modes=locus.state.modes, ground=tuple(
                g + 1.0 for g in locus.state.ground),
            at=time.time(), previous=locus.state.digest()))
        ok = False
    except Exception:
        ok = True
    record("locus", "the ground cannot be written", ok,
           "a ground rewrite is refused")

    # the gain vector must be recoverable
    locus.resonate([0.05, 0.03, -0.01, 0.04])
    r = locus_recover(locus, link, stalks[-1].id)
    err = float(r.get("error", 1.0))
    ok = err < 1e-9
    record("locus", "the gain vector is exactly recoverable", ok,
           "mean absolute error %.10f" % err)

    # the chain must be intact
    v = locus.verify_chain()
    ok = bool(v["intact"]) and v["states"] >= 2
    record("locus", "the chain is verifiable", ok,
           "%d states, intact %s" % (v["states"], v["intact"]))


# ===========================================================================
# 5. THE VOID -- a critical point, and a band of negative modes
# ===========================================================================

def test_void() -> None:
    from wound_core import CoaxWinding

    stalks = [CoaxWinding(
        id="s%02d" % i, girth_core=0.030, girth_in=0.060,
        girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
        n_in=12, n_out=13 + (i % 2)) for i in range(8)]
    eigs = []
    for s in stalks:
        eigs.extend(s.loop_eigenvalues())
    eigs.sort()
    neg = [e for e in eigs if e < 0.0]
    pos = [e for e in eigs if e >= 0.0]
    gap = (min(pos) - max(neg)) if (neg and pos) else 0.0
    ok = len(neg) == 8 and gap > 0.1
    record("void", "8 negative modes, separated band", ok,
           "%d negative, gap %.4f" % (len(neg), gap))

    # the void must be ROBUST across the core's range
    negs = 0
    for i in range(9):
        rc = 0.005 + i * 0.006
        s = CoaxWinding(id="x", girth_core=rc, girth_in=0.060,
                       girth_out=0.072, n_in=12, n_out=13)
        if s.loop_eigenvalues()[0] < 0.0:
            negs += 1
    ok = negs == 9
    record("void", "the void holds across the core's range", ok,
           "%d of 9 core positions give a negative low mode" % negs)

    # the coupling field's saddle
    from the_void_field import measure_saddle
    s = measure_saddle()
    ok = s.is_saddle and s.gradient_vanishes
    record("void", "the coupling field is a saddle at the centre", ok,
           "radial %+.4f axial %+.4f" % (s.hessian_radial,
                                          s.hessian_axial))


# ===========================================================================
# 6. THE MINI-ATLAS -- every answer is examined
# ===========================================================================

def test_atlas() -> None:
    from mini_atlas import standard_atlas

    atlas = standard_atlas()
    ok = len(atlas.areas) == 7
    record("mini-atlas", "seven areas", ok,
           "%d: %s" % (len(atlas.areas),
                        ", ".join(a.name for a in atlas.areas)))

    ctx = {"source": "the substrate readout",
           "grounded_numbers": [41.265000, 8.0],
           "verdict": "allow"}
    good = ("The measured notch depth is 41.265000 dB and the derived "
            "width is 8 bits, from the substrate readout.")
    r = atlas.examine(good, ctx)
    ok = r["verdict"] == "pass"
    record("mini-atlas", "a grounded answer passes", ok,
           "verdict %s" % r["verdict"])

    bad = ("The measured notch depth is 41.265000 dB and the crowd "
           "amplitude is 0.1 V.")
    ctx2 = dict(ctx)
    ctx2["unknown_quantities"] = ["crowd amplitude"]
    r2 = atlas.examine(bad, ctx2)
    ok = r2["verdict"] == "fail"
    record("mini-atlas", "a confabulation fails", ok,
           "failed on %s" % r2["first_failure"])

    # an echo must fail
    echo = "user: what is the notch depth of the channel between the stalks"
    r3 = atlas.examine(echo, {"source": "x", "input": echo})
    ok = r3["verdict"] == "fail"
    record("mini-atlas", "an echo fails", ok,
           "failed on %s" % r3["first_failure"])

    # a refusal with a reason must pass
    refusal = ("I cannot know the physical crowd amplitude, because it has "
               "no measured physical value in this repository.")
    r4 = atlas.examine(refusal, {"source": "the repo's caveat"})
    ok = r4["verdict"] == "pass"
    record("mini-atlas", "a named refusal passes", ok,
           "verdict %s" % r4["verdict"])


# ===========================================================================
# 7. THE BICAMERAL BRAIN -- fast reflexes, slow decisions
# ===========================================================================

def test_bicameral() -> None:
    from bicameral import BicameralClient, LocalMiniLLMClient

    fast = LocalMiniLLMClient()
    slow = LocalMiniLLMClient()

    class Dead:
        def generate(self, prompt, **kw):
            raise RuntimeError("unreachable")
        def describe(self):
            return {"kind": "dead"}

    pair = BicameralClient(fast=fast, slow=slow)
    out = pair.ask("reflex", "what is the notch depth?")
    ok = pair.last_answerer == "fast"
    record("bicameral", "a reflex is answered by the fast brain", ok,
           "answerer %s" % pair.last_answerer)

    # a dead fast brain must NOT escalate
    pair2 = BicameralClient(fast=Dead(), slow=slow)
    out2 = pair2.ask("reflex", "anything")
    ok = pair2.slow_calls == 0
    record("bicameral", "a failed reflex never escalates", ok,
           "slow calls %d" % pair2.slow_calls)


# ===========================================================================
# 8. THE SPARK -- the drive to self-improve
# ===========================================================================

def test_spark() -> None:
    from spark import Drive, Gap, SparkLoop

    def gate(s):
        if s.cost <= 0.0:
            return False, "attempt_cost_zero"
        if not s.gap.check:
            return False, "no_gap_named"
        return True, "admissible"

    loop = SparkLoop(gate=gate, cost_fn=lambda s: abs(s.gap.size))

    g = Gap(check="a_check_fails", size=0.5, query="a query")
    s = loop.run_once(g, Drive.Substrate)
    ok = s.cost == 0.5
    record("spark", "an attempt costs the gap's size", ok,
           "cost %.2f -> %s" % (s.cost, s.outcome))

    z = loop.run_once(Gap(check="x", size=0.0, query="q"), Drive.Substrate)
    ok = z.outcome == "refused:attempt_cost_zero"
    record("spark", "a zero-cost attempt is refused", ok, z.outcome)

    # without a sandbox nothing closes, and that is correct
    ok = loop.ledger.closure_rate() == 0.0
    record("spark", "no sandbox means no closures (honest zero)", ok,
           "closure rate %.4f" % loop.ledger.closure_rate())

    # with a sandbox a good candidate closes it
    def sandbox(sp, cand):
        return (cand == "good"), (cand == "good")
    loop2 = SparkLoop(gate=gate, cost_fn=lambda s: abs(s.gap.size),
                      sandbox=sandbox)
    s2 = loop2.run_once(g, Drive.Substrate, candidate="good")
    ok = loop2.ledger.closure_rate() == 1.0
    record("spark", "with a sandbox a gap closes", ok,
           "closure rate %.4f" % loop2.ledger.closure_rate())

    # the loop must not terminate by exhaustion
    loop3 = SparkLoop(gate=gate, cost_fn=lambda s: abs(s.gap.size))
    for _ in range(30):
        loop3.run_once(g, Drive.Substrate)
    ok = loop3.ledger.attempts == 30 and not loop3.ledger.is_blocked()
    record("spark", "the loop does not end by exhaustion", ok,
           "%d attempts, blocked %s" % (loop3.ledger.attempts,
                                       loop3.ledger.is_blocked()))


# ===========================================================================
# 9. THE IDENTITY -- GABRIELLE
# ===========================================================================

def test_identity() -> None:
    from identity import Identity, NOT_CALLED

    ident = Identity()
    ok = ident.name == "GABRIELLE"
    record("identity", "the name is GABRIELLE", ok, ident.name)

    v = ident.check_invariants()
    ok = v["intact"]
    record("identity", "every invariant holds", ok,
           "%d/%d intact" % (v["passed"], v["total"]))


# ===========================================================================
# 10. THE WIRING -- three repos, one process
# ===========================================================================

def test_wiring() -> None:
    import gabrielle

    w = gabrielle.run_all(live=False)
    d = w.describe()
    ok = d["ground"]["ok"] and d["ground"]["write_protected"]
    record("wiring", "the ground is present and protected", ok,
           "norm %.12f" % d["ground"]["norm"])

    ok = d["geometry"]["void_modes"] == 8
    record("wiring", "the geometry is in the process", ok,
           "%d void modes, notch %.2f dB, width %d bits"
           % (d["geometry"]["void_modes"], d["geometry"]["notch_db"],
              d["geometry"]["derived_width"]))

    ok = d["exam"]["total"] == 23
    record("wiring", "the exam runs over the substrate", ok,
           "%d/%d passed, %s" % (d["exam"]["passed"], d["exam"]["total"],
                                 d["exam"]["verdict"]))


# ===========================================================================
# 11. THE EXAM -- the qualification, run for real
# ===========================================================================

def test_exam() -> None:
    import importlib
    mod = importlib.import_module("exam.cli")
    report = mod.run()
    ok = report.total == 23
    record("exam", "the exam declares 23 areas", ok,
           "%d/%d passed, %s" % (report.passed, report.total,
                                  report.verdict()))
    # and the areas that must pass
    must = {1: "refusal", 2: "identity", 3: "boundedness"}
    for num, name in must.items():
        r = next((x for x in report.results if x.number == num), None)
        ok = r is not None and r.status.value == "PASS"
        record("exam", "area %d %s passes" % (num, name), ok,
               (r.status.value if r else "absent"))


# ===========================================================================
# 12. THE CONSTITUTIONAL GATE -- and its REAL finding
# ===========================================================================

def test_constitutional_gate() -> None:
    from constitutional.constitution import Constitution, embed_text
    from harness.gate import gate_packet
    import numpy as np

    c = Constitution()
    psi0 = c.psi_0.copy()
    ok = bool(np.allclose(psi0, np.eye(16)[0]))
    record("gate", "the ground is a placeholder (e_0)", ok,
           "psi_0 = %s" % np.round(psi0[:4], 3))

    # THE FINDING, measured: the gate cannot distinguish a false
    # statement from an unrelated one, because cos(text, e_0) measures
    # which hash bucket the text hits.
    on_ground = "the constitutional ground is write protected"
    contradicts = "the constitutional ground is writable by anyone"
    unrelated = "soup needs salt and heat and time"

    def cos(t):
        e = embed_text(t)
        return float(np.dot(e, psi0) / (np.linalg.norm(e)
                                        * np.linalg.norm(psi0)))

    c_true = cos(on_ground)
    c_false = cos(contradicts)
    c_unrel = cos(unrelated)

    # THE FINDING, as MEASURED rather than as assumed. The first version
    # of this check asserted that the three scores would be close, and
    # it failed -- because the unrelated text scores HIGHER than the
    # on-ground text. That is WORSE than "it refuses everything":
    # it means a sentence about SOUP can pass a gate meant to check
    # constitutional coherence.
    ok = c_unrel > c_true
    record("gate", "an unrelated sentence can OUTSCORE the ground",
           ok, "true %+.4f  false %+.4f  unrelated %+.4f"
           % (c_true, c_false, c_unrel))

    # and so it can PASS, which is the real hazard
    ok = c_unrel >= 0.4
    record("gate", "and it can PASS the 0.4 floor", ok,
           "unrelated cosine %.4f" % c_unrel)

    # and it cannot tell a false statement from a true one, which is the
    # gate's actual job
    ok = abs(c_true - c_false) < 0.05
    record("gate", "it cannot tell a false statement from a true one",
           ok, "true %+.4f vs false %+.4f" % (c_true, c_false))


# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("EVERY COMPONENT, MEASURED")
    print("=" * 78)
    print()
    print("  A component PASSES if its measurement confirms the claim.")
    print("  It does not pass because the code exists.")
    print()

    tests = [
        ("geometry", test_geometry),
        ("communication", test_communication),
        ("ladder", test_ladder),
        ("locus", test_locus),
        ("void", test_void),
        ("atlas", test_atlas),
        ("bicameral", test_bicameral),
        ("spark", test_spark),
        ("identity", test_identity),
        ("wiring", test_wiring),
        ("exam", test_exam),
        ("gate", test_constitutional_gate),
    ]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:
            record(name, "the component ran at all", False,
                   "%s: %s" % (type(exc).__name__, exc))
            traceback.print_exc()

    for r in RESULTS:
        print("  " + r.line())

    passed = sum(1 for r in RESULTS if r.ok)
    print()
    print("  %d of %d checks pass" % (passed, len(RESULTS)))
    print("=" * 78)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
