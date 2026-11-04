"""
tools/mutation_check_gate_margin.py -- the gate's inequality measurement,
shown able to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
So this harness MUTATES the source of the module under test, and it
PROVES THE MUTATION APPLIED before it runs the checks.

THE MUTATIONS
-------------
Each undoes one load-bearing property of the measurement:

  the alignment is computed against the SENT spectrum  -> the old defect
  the alignment formula drifts from the substrate's     -> a second formula
  the margin excludes the winner from its class-mates  -> margin is zero
  the false transmission is not measured at all        -> no counterweight
  the channel-shuffled control is dropped               -> no control
  the class split is dropped                            -> no class report

Run: python tools/mutation_check_gate_margin.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")

MODULE = os.path.join(_SRC, "measure_gate_margin.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_measure_gate_margin.py")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# THE MUTATIONS
# --------------------------------------------------------------------------

def m_alignment_is_against_a_candidate(src: str) -> str:
    """THE OLD DEFECT: the alignment measures a CANDIDATE, not the sent."""
    out = src.replace(
        "    a = alignment(rec, sent_spec)\n"
        "            true_m.append(m.margin)",
        "    a = alignment(rec, specs[other])\n"
        "            true_m.append(m.margin)")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: alignment_is_against_a_candidate")
    return out


def m_the_alignment_formula_drifts(src: str) -> str:
    """A SECOND FORMULA, drifted from the substrate's own."""
    out = src.replace(
        "    n0 = math.sqrt(den) or 1.0\n"
        "    return max(0.0, 1.0 - resid / n0)",
        "    n0 = math.sqrt(den) or 1.0\n"
        "    return max(0.0, 1.0 - resid / (2.0 * n0))")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: the_alignment_formula_drifts")
    return out


def m_the_winner_counts_as_its_own_class_mate(src: str) -> str:
    """The margin over a class-mate collapses to zero."""
    out = src.replace(
        "    same = [s for c, s in rk if labels[c] == labels[win] and c != win]",
        "    same = [s for c, s in rk if labels[c] == labels[win]]")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: the_winner_counts_as_its_own_class_mate")
    return out


def m_the_false_transmission_is_not_measured(src: str) -> str:
    """The truth counterweight is never taken, so the gate looks perfect."""
    out = src.replace(
        "        recf = recover(link, tx, rx, view, bins,\n"
        "                       address_frame(addrs[other], bins))",
        "        recf = None")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: the_false_transmission_is_not_measured")
    return out


def m_the_channel_shuffled_control_is_dropped(src: str) -> str:
    """The control is never run, so its count is always zero."""
    out = src.replace(
        "        recs = recover(link, tx, rx, view, bins, address_frame(addrs[tx], bins),\n"
        "                       shuffle_channel=CONTROL_SEED)",
        "        recs = None")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: the_channel_shuffled_control_is_dropped")
    return out


def m_the_class_split_is_dropped(src: str) -> str:
    """The margin is no longer split by address class."""
    out = src.replace(
        "    same = [s for c, s in rk if labels[c] == labels[win] and c != win]\n"
        "    diff = [s for c, s in rk if labels[c] != labels[win]]",
        "    same = [s for c, s in rk if c != win]\n"
        "    diff = []")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: the_class_split_is_dropped")
    return out


def m_a_lone_winner_reports_its_own_score(src: str) -> str:
    """A winner alone in its class reports its SCORE as a margin.

    **THIS IS THE DEGENERATE CASE, MEASURED.** The first version of
    the measurement put the winner's own score in the class-mate slot
    when the winner was alone in its class -- 128.0 at population 32.
    That is not a margin over anything.
    """
    out = src.replace(
        "        margin_same_class=(rk[0][1] - max(same)) if same else None,",
        "        margin_same_class=(rk[0][1] - max(same)) if same else rk[0][1],")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: a_lone_winner_reports_its_own_score")
    return out


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("alignment_is_against_a_candidate", m_alignment_is_against_a_candidate),
    ("the_alignment_formula_drifts", m_the_alignment_formula_drifts),
    ("the_winner_counts_as_its_own_class_mate",
     m_the_winner_counts_as_its_own_class_mate),
    ("the_false_transmission_is_not_measured",
     m_the_false_transmission_is_not_measured),
    ("the_channel_shuffled_control_is_dropped",
     m_the_channel_shuffled_control_is_dropped),
    ("the_class_split_is_dropped", m_the_class_split_is_dropped),
    ("a_lone_winner_reports_its_own_score",
     m_a_lone_winner_reports_its_own_score),
]


def _run_tests(tmp_src: str) -> Tuple[int, str]:
    """Run the test file against a mutated copy of the module.

    **THE PATH MATTERS, AND GETTING IT WRONG MAKES EVERY MUTATION
    SURVIVE.** The temp directory goes FIRST on the path (so the
    mutated copy wins), and src/ stays on the path (so the copy's
    imports resolve). And the harness PROVES the mutation is live
    before it runs the checks: the mutated module is imported and its
    marker is checked, and if the marker is absent the run is reported
    as a harness failure rather than as a surviving mutant.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [tmp_src, _SRC] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))

    probe = subprocess.run(
        [sys.executable, "-c",
         "import measure_gate_margin as m; print(m.__file__); "
         "print(getattr(m, 'MUTATION_MARKER', 'NONE'))"],
        cwd=_ROOT, env=env, capture_output=True, text=True, timeout=120)
    if probe.returncode != 0:
        raise SystemExit(
            "HARNESS FAILURE: the mutated module could not be imported "
            "in the temp environment:\n%s" % (probe.stderr or probe.stdout))
    if "NONE" in probe.stdout:
        raise SystemExit(
            "HARNESS FAILURE: the mutated module was NOT the one "
            "imported. The mutation would not have taken effect.\n%s"
            % probe.stdout)

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header", "-x"],
        cwd=_ROOT, env=env, capture_output=True, text=True, timeout=1800)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    original = _read(MODULE)
    tmp = tempfile.mkdtemp(prefix="mutgatemargin")
    shutil.copy(MODULE, os.path.join(tmp, "measure_gate_margin.py"))
    try:
        print("=" * 70)
        print("MUTATION CHECK -- measure_gate_margin.py, shown able to go RED")
        print("=" * 70)
        print()
        red = 0
        for name, mutate in MUTATIONS:
            mutated = mutate(original)
            mutated = mutated + "\nMUTATION_MARKER = %r\n" % (name,)
            path = os.path.join(tmp, "measure_gate_margin.py")
            _write(path, mutated)
            if _read(path) == original:
                print("  [FAIL] %-40s MUTATION DID NOT APPLY" % name)
                continue
            rc, out = _run_tests(tmp)
            if rc != 0:
                red += 1
                tail = [ln for ln in out.splitlines()
                        if "failed" in ln or "error" in ln]
                summary = tail[-1] if tail else out.strip().splitlines()[-1]
                print("  [RED ] %-40s %s" % (name, summary[:70]))
            else:
                print("  [GREEN] %-40s THE MUTATION SURVIVED" % name)
        print()
        print("  %d of %d mutants RED" % (red, len(MUTATIONS)))
        print("=" * 70)
        return 0 if red == len(MUTATIONS) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
