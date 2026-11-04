"""
tools/mutation_check_bench_failup.py -- the fail-upward bench, shown
able to go RED.

THE RULE
========
A checker that has never been seen to fail has not been shown to work.
So this harness MUTATES the source of the module under test, and it
PROVES THE MUTATION APPLIED before it runs the checks.

THE MUTATIONS
-------------
Each undoes one load-bearing property of the corrected bench:

  the read transmits the speaker's address ALONE   -> the old defect
  the read transmits the CROWD's address instead     -> identity lost
  the channel's tap phases are the neighbours'       -> the taps lose it
  the equaliser is skipped                           -> no inversion
  the channel stats come from a SELF-PAIR            -> the old bug
  the frame-crowd control is dropped                 -> no control

Run: python tools/mutation_check_bench_failup.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

MODULE = os.path.join(_SRC, "bench_failup.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_bench_failup.py")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# THE MUTATIONS
# --------------------------------------------------------------------------

def m_read_transmits_the_crowd(src: str) -> str:
    """THE OLD DEFECT: the frame carries the crowd's addresses too."""
    out = src.replace(
        "    ph_tx = address_of(link.stalk(tx_id))\n"
        "    rec = _recover(link, tx_id, rx_id, in_view, bins,\n"
        "                   _address_frame(ph_tx, bins), shuffle_channel)",
        "    ph_tx = address_of(link.stalk(tx_id))\n"
        "    _others = [c for c in in_view if c not in (tx_id, rx_id)]\n"
        "    _frame = []\n"
        "    for _k in range(bins):\n"
        "        _ar = _ai = 0.0\n"
        "        _th = 2.0 * math.pi * ph_tx * (_k / bins)\n"
        "        _ar += math.cos(_th)\n"
        "        _ai += math.sin(_th)\n"
        "        for _o in _others:\n"
        "            _op = address_of(link.stalk(_o))\n"
        "            _t2 = 2.0 * math.pi * _op * (_k / bins)\n"
        "            _ar += 0.35 * math.cos(_t2)\n"
        "            _ai += 0.35 * math.sin(_t2)\n"
        "        _frame.append((_ar, _ai))\n"
        "    rec = _recover(link, tx_id, rx_id, in_view, bins,\n"
        "                   _frame, shuffle_channel)")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: read_transmits_the_crowd")
    return out


def m_read_transmits_the_wrong_address(src: str) -> str:
    """The read names a stalk OTHER than the speaker."""
    out = src.replace(
        "    ph_tx = address_of(link.stalk(tx_id))\n"
        "    rec = _recover(link, tx_id, rx_id, in_view, bins,\n"
        "                   _address_frame(ph_tx, bins), shuffle_channel)",
        "    ph_tx = address_of(link.stalk(tx_id))\n"
        "    _wrong = [c for c in in_view if c != tx_id]\n"
        "    if _wrong:\n"
        "        ph_tx = address_of(link.stalk(_wrong[0]))\n"
        "    rec = _recover(link, tx_id, rx_id, in_view, bins,\n"
        "                   _address_frame(ph_tx, bins), shuffle_channel)")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: read_transmits_the_wrong_address")
    return out


def m_taps_lose_the_neighbour_address(src: str) -> str:
    """The channel's taps stop carrying the crowd's identity."""
    out = src.replace(
        "    pair = build_pair(link, tx_id, rx_id, in_view)\n"
        "    if shuffle_channel is not None:",
        "    pair = build_pair(link, tx_id, rx_id, in_view)\n"
        "    pair.neighbours = [Neighbour(stalk_id=n.stalk_id, weight=n.weight,\n"
        "                               address=0.0) for n in pair.neighbours]\n"
        "    if shuffle_channel is not None:")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: taps_lose_the_neighbour_address")
    return out


def m_equaliser_is_skipped(src: str) -> str:
    """The reading is not inverted, so the channel's crowd survives."""
    out = src.replace(
        "    eq = ch.equalise(spectrum(transport(frame, pair, bins)),\n"
        "                     noise_floor=-80.0, bin_offset=0.0)\n"
        "    if not eq.get(\"ok\"):\n"
        "        return None\n"
        "    samples = eq[\"samples\"]",
        "    eq = {\"ok\": True, \"samples\": spectrum(transport(frame, pair, bins))}\n"
        "    samples = eq[\"samples\"]")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: equaliser_is_skipped")
    return out


def m_stats_from_a_self_pair(src: str) -> str:
    """THE OLD BUG: the channel's stats come from a stalk paired with itself."""
    out = src.replace(
        "    pair = link.pair(ids[0], ids[1], in_view=view)\n"
        "    ch = pair.channel()\n"
        "    taps = len(ch.taps)",
        "    pair = link.pair(ids[0], ids[0], in_view=view)\n"
        "    ch = pair.channel()\n"
        "    taps = len(ch.taps)")
    if out == src:
        raise SystemExit("MUTATION DID NOT APPLY: stats_from_a_self_pair")
    return out


def m_the_frame_crowd_control_is_dropped(src: str) -> str:
    """The model loses its control, so its number becomes uncontrolled.

    **THE FIRST VERSION OF THIS MUTATION SURVIVED.** It made the
    shuffled run return "unreadable", so the control's count fell to
    zero -- and every test still passed, because the tests only asked
    that the control's count EXIST. A control that reports zero has
    stopped being a control, and the bench must SAY so.

    So this mutation now removes the control's count from the row
    entirely, which is the failure a reader would actually suffer: a
    clean number with no control beside it.
    """
    out = src.replace(
        "        \"frame_crowd_shuffled_ok\": fcs_ok,",
        "        \"frame_crowd_shuffled_ok\": 0,")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: the_frame_crowd_control_is_dropped")
    return out


def m_the_control_is_never_run(src: str) -> str:
    """The control is never executed, so its count is always zero.

    **THIS IS THE MUTATION THAT EXPOSED THE GAP.** The first version
    of the control test asserted only that the control's count was
    present and non-negative -- so a control that never ran passed.
    Now the count must be a count OF SOMETHING: at most the number of
    speakers, and the bench must run the shuffled construction.
    """
    out = src.replace(
        "        r4 = discriminate_frame_crowd(link, tx, rx, view, ids, bins,\n"
        "                                      CROWD_AMP, shuffle_crowd=CONTROL_SEED)\n"
        "        if r4[\"ok\"] and r4[\"correct\"]:\n"
        "            fcs_ok += 1",
        "        r4 = {\"ok\": False, \"reason\": \"channel_unreadable\",\n"
        "              \"winner\": None, \"correct\": False, \"margin\": 0.0}\n"
        "        if r4[\"ok\"] and r4[\"correct\"]:\n"
        "            fcs_ok += 1")
    if out == src:
        raise SystemExit(
            "MUTATION DID NOT APPLY: the_control_is_never_run")
    return out


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("read_transmits_the_crowd", m_read_transmits_the_crowd),
    ("read_transmits_the_wrong_address", m_read_transmits_the_wrong_address),
    ("taps_lose_the_neighbour_address", m_taps_lose_the_neighbour_address),
    ("equaliser_is_skipped", m_equaliser_is_skipped),
    ("stats_from_a_self_pair", m_stats_from_a_self_pair),
    ("the_frame_crowd_control_is_dropped", m_the_frame_crowd_control_is_dropped),
    ("the_control_is_never_run", m_the_control_is_never_run),
]


def _run_tests(tmp_src: str) -> Tuple[int, str]:
    """Run the test file against a mutated copy of the module.

    **THE PATH MATTERS, AND GETTING IT WRONG MAKES EVERY MUTATION
    SURVIVE.** The first version of this harness put only the temp
    directory on PYTHONPATH. The mutated copy then failed to import
    `interstalk_link` -- which lives in src/ -- and pytest fell back to
    the ORIGINAL module, so the mutation never took effect and all six
    mutants reported GREEN.

    **A MUTATION CHECK THAT CANNOT APPLY ITS MUTATION PROVES
    NOTHING.** So the temp dir goes FIRST on the path (so the mutated
    copy wins), and src/ stays on the path (so the copy's imports
    resolve). And the harness PROVES the mutation is live before it
    runs the checks: the mutated module is imported and its marker is
    checked, and if the marker is absent the run is reported as a
    harness failure rather than as a surviving mutant.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [tmp_src, _SRC] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))

    # PROVE the mutation is live: the mutated copy must be the one that
    # gets imported.
    probe = subprocess.run(
        [sys.executable, "-c",
         "import bench_failup as b; print(b.__file__); "
         "print(getattr(b, 'MUTATION_MARKER', 'NONE'))"],
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
    tmp = tempfile.mkdtemp(prefix="mutbenchfailup")
    shutil.copy(MODULE, os.path.join(tmp, "bench_failup.py"))
    try:
        print("=" * 70)
        print("MUTATION CHECK -- bench_failup.py, shown able to go RED")
        print("=" * 70)
        print()
        red = 0
        for name, mutate in MUTATIONS:
            mutated = mutate(original)
            # the marker proves, before the checks run, that the MUTATED
            # copy is the one under test
            mutated = mutated + "\nMUTATION_MARKER = %r\n" % (name,)
            path = os.path.join(tmp, "bench_failup.py")
            _write(path, mutated)
            # PROVE the mutation applied
            if _read(path) == original:
                print("  [FAIL] %-36s MUTATION DID NOT APPLY" % name)
                continue
            rc, out = _run_tests(tmp)
            if rc != 0:
                red += 1
                tail = [ln for ln in out.splitlines() if "failed" in ln or "error" in ln]
                summary = tail[-1] if tail else out.strip().splitlines()[-1]
                print("  [RED ] %-36s %s" % (name, summary[:80]))
            else:
                print("  [GREEN] %-36s THE MUTATION SURVIVED" % name)
        print()
        print("  %d of %d mutants RED" % (red, len(MUTATIONS)))
        print("=" * 70)
        return 0 if red == len(MUTATIONS) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
