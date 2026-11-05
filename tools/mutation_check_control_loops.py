#!/usr/bin/env python3
"""
mutation_check_control_loops.py -- prove the loop registry's checks can
go RED.

Central rule 7: a test that cannot fail is not a test.

THE MUTATIONS, and each one breaks exactly one claim the registry
makes:

  M1  the DARK path is removed -- a module that does not import is
      reported LIVE instead of DARK. This breaks the whole point: the
      registry's claim is that it can be wrong about a loop.

  M2  the reason is dropped -- a DARK entry carries no reason. This is
      the silent-failure shape: an entry that says "not live" and not
      why is indistinguishable from one that was never checked.

  M3  the dark entry is DROPPED from the survey -- the survey quietly
      skips what it could not load. This is the defect the registry
      exists to prevent, and it is the one a reader would never see.

  M4  the decision is not declared -- an entry with no decision. Then
      the registry is a module list, which is what we had before.

  M5  the GATE check is disabled -- a GATE with a non-callable
      declared probe passes. So a gate that cannot refuse anybody
      reads as a gate.

Run:
    python tools/mutation_check_control_loops.py
Exit: 0 when every mutation turns the check RED, 1 otherwise.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src" / "control_loops.py"
WORK_REPOS = REPO.parent
VENV_PY = WORK_REPOS / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.is_file():
    VENV_PY = pathlib.Path(sys.executable)


def _run(path: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run([str(VENV_PY), str(path), "--selftest"],
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout + proc.stderr


def _mutate(source: str, old: str, new: str) -> str:
    if old not in source:
        raise SystemExit("MUTATION TARGET NOT FOUND: %r" % old[:70])
    return source.replace(old, new, 1)


MUTATIONS = [
    ("M1  a module that does not import is reported LIVE",
     'return DARK, "", "it could not be imported: %r" % (exc,)',
     'return LIVE, "it imported", ""'),

    ("M2  the DARK reason is dropped",
     'return DARK, "", "it could not be imported: %r" % (exc,)',
     'return DARK, "", ""'),

    ("M3  the dark entry is DROPPED from the survey",
     "        out.append(LoopEntry(\n"
     "            name=e.name, decides=e.decides, home=e.home,\n"
     "            cadence=e.cadence, what=e.what, module=e.module,\n"
     "            probe=e.probe, state=state, evidence=evidence, reason=reason))",
     "        if state == DARK:\n"
     "            continue\n"
     "        out.append(LoopEntry(\n"
     "            name=e.name, decides=e.decides, home=e.home,\n"
     "            cadence=e.cadence, what=e.what, module=e.module,\n"
     "            probe=e.probe, state=state, evidence=evidence, reason=reason))"),

    ("M4  the DECISION PREDICATE stops flagging a broken entry",
     '    return [e.name for e in entries if e.decides not in DECISIONS]',
     '    return []'),

    ("M5  the GATE predicate stops flagging a gate that cannot refuse",
     "        if attr is None or not callable(attr):\n"
     '            bad.append("%s (%s.%s)" % (e.name, e.module, e.probe))',
     "        if False:\n"
     '            bad.append("%s (%s.%s)" % (e.name, e.module, e.probe))'),
]


def _saw_zero_live(output: str) -> bool:
    """Did the mutant see zero live entries?

    AND THE MATCH IS EXACT, ON THE COUNT LINE. The first version
    searched for the substring "0 live" and it MATCHED "20 live" --
    so a mutant that worked perfectly was reported as having broken
    its own world. The marker is now the count line's own shape.

    MEASURED: the self-test prints
        "    GATE   live 4  stub 1  dark 0"
    so the broken case reads "live 0  stub" and the working case
    reads "live 4  stub". The regex requires the zero to be the whole
    number.
    """
    return bool(re.search(r"live 0\s+stub", output))


def main() -> int:
    original = SRC.read_text(encoding="utf-8")

    print("=" * 78)
    print("MUTATION CHECK -- the loop registry")
    print("=" * 78)
    print()

    rc, out = _run(SRC)
    print("  the unmutated registry: %s" % ("PASSES" if rc == 0 else "FAILS"))
    if rc != 0:
        print(out[-3000:])
        print()
        print("  THE BASELINE IS RED, so no mutation can be proven.")
        return 1

    ok = True
    # AND THE MUTANT RUNS FROM THE SOURCE'S OWN DIRECTORY, not from a
    # temp dir. MEASURED: the first version copied the mutant into a
    # temporary directory, and the mutant computes its repo paths from
    # __file__ -- so every import failed, every entry came back DARK,
    # and M3, M4 and M5 went red for the WRONG REASON ("0 live"). A
    # mutation that fails because the harness broke the code is not a
    # proof that the check can fail. So the mutant is written beside
    # the original, run, and removed.
    mutant = SRC.with_name("control_loops_mutant_tmp.py")
    try:
        for label, old, new in MUTATIONS:
            mutated = _mutate(original, old, new)
            mutant.write_text(mutated, encoding="utf-8")
            rc2, out2 = _run(mutant)
            red = rc2 != 0
            print("  [%s] %s" % ("RED " if red else "NOT RED", label))
            if not red:
                ok = False
                print("        the mutated registry still passed -- the "
                      "check cannot fail")
            else:
                fails = [ln for ln in out2.splitlines()
                         if "[FAIL]" in ln or "FAILED:" in ln]
                for ln in fails[:3]:
                    print("        %s" % ln.strip())
            # AND THE MUTANT MUST STILL SEE THE REPOS. If the harness
            # broke the module's own world, the red is not evidence.
            #
            # AND THE MARKER IS EXACT. MEASURED: the first version
            # searched the output for the substring "0 live", and it
            # MATCHED "20 live" -- so a mutant that was working
            # perfectly was reported as having broken its own world.
            # The check reads the count line itself.
            if _saw_zero_live(out2):
                print("        [WARN] the mutant saw 0 live entries -- "
                      "the harness broke its world, so this red is not "
                      "evidence")
                ok = False
    finally:
        if mutant.exists():
            mutant.unlink()

    print()
    print("=" * 78)
    print("  every mutation turned the check RED: %s" % ("YES" if ok else "NO"))
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
