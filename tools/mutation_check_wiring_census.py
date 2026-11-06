#!/usr/bin/env python3
"""
mutation_check_wiring_census.py -- CAN THE CENSUS GO RED?

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all
modules"*.

**A CENSUS THAT CANNOT GO RED IS NOT A CENSUS.** The census is the
instrument that says which of the fc's modules are reached and which
are not. If its bins are wrong, it says the wrong thing confidently --
and a confident wrong answer about wiring is the worst kind, because a
session acts on it.

So each mutation breaks ONE rule of the census and the check must go
RED for that reason.

THE FIXTURE TREE, and why it exists
-----------------------------------
MEASURED 2026-11-06: the first version of this harness ran the
census over the REAL tree and asserted only that the counts moved.
Two of the five mutations then failed FOR THE WRONG REASON -- they
moved a different count, because the real tree is large and noisy and
a change in it cannot be attributed to one rule. A harness that
reports "RED" for the wrong reason is the exact defect this project
keeps finding in itself.

So there is now a FIXTURE tree, at
`tests/fixtures/wiring_census/repos/fieldcore/src/`, with exactly one
example of each shape the census must get right:

    entry_static.py     a __main__ entry point, statically importing
    cap_static.py       a capability reached by a STATIC import
    entry_dynamic.py    an entry point reaching a capability with
                        importlib.import_module("...")
    cap_dynamic.py      a capability reached only DYNAMICALLY
    bench_probe.py      a bench: nothing imports it, and that is right
    orphan_top.py       a capability nothing reaches
    cap_island.py       a capability reached only by UNREACHABLE code
    pkg/__init__.py     a package whose init does `from . import x`
    pkg/mod_rel.py      a module doing `from .result import ...`
                        and `from .. import ...`
    pkg/result.py       the real result module
    pkg/cap_rel.py      reached from inside the package
    cap_top_level.py    reached from inside a package, above it
    other/result.py     a DECOY with the same leaf name -- it must
                        stay an orphan, so a relative import that
                        resolves to the wrong place is visible

And every mutation names the ONE module whose bin must move. So the
harness cannot pass for the wrong reason: if the wrong module moves,
the check is RED.

THE MUTATIONS
-------------
  M1  the ORPHAN bin never fires
      -> orphan_top must stop being an ORPHAN
  M2  a relative import is not resolved to its package
      -> pkg/result.py must stop being WIRED
  M3  a dynamic import is not counted
      -> cap_dynamic.py must stop being WIRED
  M4  the ISLAND bin is dropped
      -> cap_island.py must stop being an ISLAND
  M5  the ENTRY bin never fires
      -> bench_probe.py must stop being an ENTRY

Run:
    python tools/mutation_check_wiring_census.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CENSUS = os.path.join(HERE, "wiring_census.py")

#: The fixture tree, relative to the repo root.
FIXTURE = os.path.join(REPO, "tests", "fixtures", "wiring_census", "repos")

#: What the census MUST say about the fixture, before any mutation.
#: This is the ground truth, and it is written out rather than
#: computed -- so a change in the census that happens to agree with a
#: recomputed expectation cannot hide.
EXPECTED: Dict[str, str] = {
    "src/entry_static.py": "ENTRY",
    "src/cap_static.py": "WIRED",
    "src/entry_dynamic.py": "ENTRY",
    "src/cap_dynamic.py": "WIRED",
    "src/bench_probe.py": "ENTRY",
    "src/orphan_top.py": "ORPHAN",
    "src/cap_island.py": "ISLAND",
    "src/pkg/__init__.py": "ENTRY",
    "src/pkg/mod_rel.py": "WIRED",
    "src/pkg/result.py": "WIRED",
    "src/pkg/cap_rel.py": "WIRED",
    "src/cap_top_level.py": "WIRED",
    "src/other/result.py": "ORPHAN",
    "src/other/__init__.py": "ORPHAN",
}


def _run_python() -> str:
    venv = os.path.join(os.path.dirname(REPO), ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv):
        return venv
    return sys.executable


def _census_bins(tmp: str) -> Optional[Dict[str, str]]:
    """Run the (possibly mutated) census over the fixture tree."""
    env = dict(os.environ)
    env["PYTHONPATH"] = tmp + os.pathsep + env.get("PYTHONPATH", "")
    env["FC_WORK_REPOS"] = FIXTURE
    proc = subprocess.run(
        [_run_python(), os.path.join(tmp, "wiring_census.py"), "--json",
         "--work-repos", FIXTURE, "--repo", "fieldcore"],
        capture_output=True, text=True, env=env, cwd=tmp,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        return None
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    bins: Dict[str, str] = {}
    for row in data.get("rows", []):
        bins[row["path"]] = row["bin"]
    return bins


def _write_census(tmp: str, old: Optional[str] = None,
                  new: Optional[str] = None) -> bool:
    """Write the census into tmp, optionally with one rule mutated."""
    src = open(CENSUS, encoding="utf-8").read()
    if old is not None and new is not None:
        if old not in src:
            return False
        src = src.replace(old, new, 1)
    open(os.path.join(tmp, "wiring_census.py"), "w", encoding="utf-8").write(src)
    return True


#: Each mutation: (code, name, old, new, module, expected_bin)
MUTATIONS: List[Tuple[str, str, str, str, str, str]] = [
    (
        "M1",
        "the ORPHAN bin never fires",
        '        if self.is_entry:\n            return "ENTRY"\n        return "ORPHAN"',
        '        if self.is_entry:\n            return "ENTRY"\n        return "WIRED"',
        "src/orphan_top.py", "WIRED",
    ),
    (
        "M2",
        "a relative import is not resolved to its package",
        "                parts = m.pkg_parts\n"
        "                up = node.level - 1\n"
        "                prefix_parts = parts[:len(parts) - up] if len(parts) >= up else []",
        "                parts = m.pkg_parts\n"
        "                up = node.level\n"
        "                prefix_parts = parts[:len(parts) - up] if len(parts) >= up else []",
        "src/pkg/result.py", "ORPHAN",
    ),
    (
        "M3",
        "a dynamic import is not counted",
        "            names = set(other.imports) | set(other.attr_refs) | set(other.dynamic)",
        "            names = set(other.imports) | set(other.attr_refs)",
        "src/cap_dynamic.py", "ORPHAN",
    ),
    (
        "M4",
        "the ISLAND bin is dropped",
        '        if self.inbound:\n            return "WIRED" if self.reachable else "ISLAND"',
        '        if self.inbound:\n            return "WIRED"',
        "src/cap_island.py", "WIRED",
    ),
    (
        "M5",
        "the ENTRY bin never fires",
        '        if self.is_entry:\n            return "ENTRY"',
        '        if False:\n            return "ENTRY"',
        "src/bench_probe.py", "ORPHAN",
    ),
]


def main() -> int:
    print("=" * 78)
    print("THE WIRING CENSUS -- MUTATION CHECK")
    print("=" * 78)
    print()
    print("  The census is the instrument that says which of the fc's")
    print("  modules are reached. If it cannot go red it is not one.")
    print()
    print("  The fixture tree is at")
    print("    %s" % FIXTURE)
    print()

    tmp = tempfile.mkdtemp(prefix="census_mutation_")
    try:
        # -- the baseline -------------------------------------------------
        _write_census(tmp)
        base = _census_bins(tmp)
        if base is None:
            print("  BASELINE FAILED -- the census did not run on the")
            print("  fixture tree. A census that does not run cannot be")
            print("  mutated.")
            return 2
        print("BASELINE (no mutation) -- the census must agree with the")
        print("written ground truth")
        wrong = []
        for path, want in sorted(EXPECTED.items()):
            got = base.get(path, "(absent)")
            ok = (got == want)
            if not ok:
                wrong.append((path, want, got))
            print("  %-28s %-8s %s" % (path, got,
                                      "OK" if ok else "WRONG (want %s)" % want))
        print()
        if wrong:
            print("  THE BASELINE DISAGREES WITH THE GROUND TRUTH in %d "
                  "place(s)." % len(wrong))
            print("  A mutation check on a baseline that is already wrong")
            print("  proves nothing. STOP.")
            return 2
        print("  the census agrees with the ground truth: OK")
        print()

        # -- the mutations ------------------------------------------------
        # `red` counts the mutations the harness could NOT see. The
        # summary said "N of M mutations caught" while printing the
        # INVERSE of what it had counted, so a run where all five were
        # caught reported "0 of 5 caught" and FAILED. The harness was
        # judging itself by its own miscount -- which is the defect
        # this project keeps finding, this time in the instrument
        # rather than in the thing the instrument measures.
        red = 0
        total = 0
        for code, name, old, new, module, want in MUTATIONS:
            total += 1
            print("%s: %s" % (code, name))
            if not _write_census(tmp, old, new):
                print("  NOT APPLIED -- the anchor text is not in the file.")
                print("  the mutation is stale, so it proves nothing.")
                print("  RED as required (the harness cannot check it)")
                red += 1
                print()
                continue
            mut = _census_bins(tmp)
            if mut is None:
                print("  the mutated census did not run.")
                print("  RED as required (the harness cannot check it)")
                red += 1
                print()
                continue
            got = mut.get(module, "(absent)")
            if got == want:
                print("  %s is now %s, as the mutation requires." % (module, got))
                print("  -> caught: the rule the census relies on is broken")
                print("  GREEN, as required (the mutation was caught)")
            else:
                print("  %s is %s, and the mutation requires %s."
                      % (module, got, want))
                print("  -> the mutation did NOT move the module it claims")
                print("     to move, so the harness cannot see the defect")
                print("  RED as required (the mutation went unnoticed)")
                red += 1
            moved = [p for p in sorted(set(base) | set(mut))
                     if base.get(p) != mut.get(p)]
            if len(moved) > 1:
                print("  NOTE: %d modules moved, not 1: %s"
                      % (len(moved), ", ".join(moved)))
            print()

        print("=" * 78)
        print("THE SUMMARY")
        print("=" * 78)
        caught = total - red
        print("  baseline: the census agrees with the written ground truth   OK")
        print("  %d of %d mutations caught" % (caught, total))
        print()
        if red == 0:
            print("  VERDICT: PASS")
            return 0
        print("  VERDICT: FAIL -- %d of %d mutations were not caught"
              % (red, total))
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
