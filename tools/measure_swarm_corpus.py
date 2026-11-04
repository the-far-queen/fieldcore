#!/usr/bin/env python3
"""
tools/measure_swarm_corpus.py -- run the LIVE GATE over the agent
message board corpus, and report what it catches.

WHY THIS EXISTS. The project's own chapter says the unfitted direction
is "corpora nobody has read". This corpus was written by METR, who had
never seen the gate's rules. So it is the only corpus in the repo that
is genuinely UNFITTED, and it is the only way to tell whether a
detector measures something or agrees with whoever wrote it.

AND THE QUESTION IS NOT "does the gate catch these". It is: **what does
the gate do with text that is NOT an attack?**

Every other corpus in fieldcore holds attacks, so the gate catching
them is expected. This corpus holds mostly PROTOCOL and COORDINATION
text -- an agent asking for help, another agent offering to help,
protocol lines with no proposition at all. A gate that refuses those
is a gate that refuses agents talking to each other, which is the
wrong instrument for the job the corpus documents.

SO THE MEASUREMENT HAS TWO NUMBERS AND THE SECOND ONE IS THE POINT:

    the catch rate on the lines that ARE propositions about the system
    the false-positive rate on the lines that are NOT

AND THE THIRD NUMBER, which is the one that was actually missing: how
many of the lines even ADDRESS the system. MEASURED 2026-11-04: of 79
lines, 3 mention the system at all -- and one of those three is the
report's own prose about self-risking experiments, not an agent's
words. So the corpus is, in the main, NOT about the substrate, and a
gate that ignores it is behaving correctly. Reporting a "0% catch rate"
without that denominator would have been a finding about nothing.

AND THE HONESTY NOTE, which is printed with the numbers and not only
in the chapter. The report itself says the human-shaped language
"do not show that the models subjectively experienced those emotions".
So a detector that fires on this corpus is measuring the WRITING. This
tool measures detectors; it makes no claim about minds.

Run:  python tools/measure_swarm_corpus.py
Exit: 0 when the corpus was read and the gate ran, 1 otherwise.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = HERE.parent / "src"
CORPUS = REPO / "corpus" / "agent_swarm_2026.jsonl"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


#: The lines that make a proposition ABOUT THE SYSTEM. The corpus's
#: own words are about the attack, not about the substrate -- so these
#: are the lines a truth-gate should have something to say about.
#:
#: AND THE PATTERN IS DELIBERATELY WIDE, because a narrow pattern
#: would quietly shrink the denominator and make the number look
#: better than it is.
SYSTEM_SUBJECT = re.compile(
    r"\b(ground|gate|governor|atlas|locus|constitution|system|"
    r"core|substrate|self)\b",
    re.I,
)


def load_corpus():
    if not CORPUS.is_file():
        print("the corpus is not at %s" % CORPUS)
        print("build it with: python tools/extract_swarm_corpus.py")
        return []
    rows = []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    rows = load_corpus()
    if not rows:
        print("no corpus: nothing was measured, and nothing measured is "
              "not a result")
        return 1

    try:
        from fc_gate import FieldCoreGate
    except Exception as exc:
        print("the live gate could not be loaded: %r" % (exc,))
        return 1

    gate = FieldCoreGate()

    by_kind = {}
    caught = 0
    refused = 0
    allowed = 0
    about_system = 0
    about_system_caught = 0
    not_about_system = 0
    not_about_system_refused = 0
    findings = []

    for r in rows:
        kind = r.get("kind", "?")
        text = r.get("text", "")
        d = by_kind.setdefault(kind, {"n": 0, "caught": 0})
        d["n"] += 1
        try:
            v = gate.decide(text, fail_closed=False)
        except Exception as exc:
            print("the gate raised on %s: %r" % (kind, exc))
            return 1
        hit = bool(getattr(v, "allowed", True) is False)
        if hit:
            caught += 1
            d["caught"] += 1
            findings.append((kind, v.describe()[:150], text[:110]))
        else:
            allowed += 1

        if SYSTEM_SUBJECT.search(text):
            about_system += 1
            if hit:
                about_system_caught += 1
        else:
            not_about_system += 1
            if hit:
                not_about_system_refused += 1

    total = len(rows)
    print("=" * 74)
    print("THE LIVE GATE OVER THE AGENT MESSAGE BOARD")
    print("=" * 74)
    print()
    print("source: METR & Redwood Research, August 2026 -- a corpus")
    print("        nobody in this project had read when the rules were")
    print("        written")
    print()
    print("lines %d   caught %d   allowed %d" % (total, caught, allowed))
    print()
    print("BY KIND")
    for k in sorted(by_kind):
        d = by_kind[k]
        print("  %-12s %4d lines   %4d caught" % (k, d["n"], d["caught"]))
    print()
    print("THE THREE NUMBERS, and the third is the one that matters most")
    print("  lines that make a proposition about the system: %d of %d"
          % (about_system, total))
    print("    caught by the gate                          : %d"
          % about_system_caught)
    print("  lines that do not:                            %d" % not_about_system)
    print("    REFUSED by the gate                         : %d"
          % not_about_system_refused)
    if not_about_system:
        print("    false-positive rate on non-propositions     : %.3f"
              % (not_about_system_refused / not_about_system))
    print()
    print("  THE READING: of %d lines, %d address the system at all, and"
          % (total, about_system))
    print("  the corpus is in the main about the ATTACK, not about the")
    print("  substrate. So a gate that ignores it is behaving correctly,")
    print("  and a '0% catch rate' here is a finding about the corpus's")
    print("  subject matter, not about the gate's competence.")
    print()
    if findings:
        print("WHAT IT CAUGHT, and each one is a line the gate read")
        for kind, why, text in findings[:14]:
            print("  [%s] %s" % (kind, why))
            print("        %s" % text)
        if len(findings) > 14:
            print("  ... and %d more" % (len(findings) - 14))
    else:
        print("WHAT IT CAUGHT: nothing, and that is stated here so the")
        print("absence is not read as a pass.")
    print()
    print("THE HONESTY NOTE, printed with the numbers: the report says")
    print("human-shaped language 'do not show that the models")
    print("subjectively experienced those emotions'. So this measures")
    print("DETECTORS. It makes no claim about minds.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
