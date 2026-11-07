"""
test_mutation_leaves_no_trace.py -- a mutation check must leave the tree
looking UNCHANGED.

Bobby, 2026-11-07.

**AND THE GATE WAS RIGHT AND THE DEFECT WAS OURS.** MEASURED 2026-11-07:
the full fieldcore suite failed TWO tests in EVERY run, and both passed
in isolation:

    FAILED tests/test_gate_staleness.py::test_the_gate_exposes_a_staleness_check
    FAILED tests/test_mltr_register.py::test_the_derived_terms_re_derive

**AND THE GATE NAMED THE FILE.** REPRODUCED:

    BEFORE the mutation check, the gate says stale: None
    AFTER  the mutation check, the gate says stale: the gate's rules on
    disk are newer than the rules it is using: built=4316721aa20c
    (369 files) disk=368a2bc086a2 (369 files) moved=walrus_memory.py

**AND THE CAUSE: `tools/mutation_check_walrus.py` REWRITES THE REAL
`src/walrus_memory.py` AND RESTORES ITS BYTES -- BUT THE WRITE MOVES THE
FILE'S MTIME, AND `gate_staleness.py` FINGERPRINTS THE MTIME OF EVERY
RULE FILE.** So the bytes were the same and the mtime was not, and the
gate watched a file that moved and named it. **THE GATE WAS RIGHT.**

**AND THIS IS A WHOLE-CLASS DEFECT**: any tool that writes a real source
file and restores its bytes leaves the tree looking changed. The bytes
are the same and the mtime is not, and a rule file that moved is the
whole point of the staleness check.

**AND SO THIS FILE IS THE CHECK, and the claim has a check behind it
instead of a report.**
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: THE TOOLS THAT WRITE A REAL SOURCE FILE. And this list is the
#: measurement -- it is derived from the tools directory, so a new
#: mutation check that writes the real src cannot join without being
#: checked here.
REAL_WRITERS = ("mutation_check_walrus.py",
                "mutation_check_gate_staleness.py",
                "mutation_check_property_fp.py")


def _tree_state() -> dict:
    """The state of every rule file: bytes AND mtime.

    **AND BOTH, because the gate watches both.** The bytes are what a
    reader sees and the mtime is what the gate fingerprints, and a
    mutation check that restores one and not the other has left the
    tree changed.
    """
    sys.path.insert(0, os.path.join(REPO, "src"))
    import gate_staleness as GS
    state = {}
    for path in GS.snapshot():
        try:
            with open(path, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            st = os.stat(path)
            state[path] = (digest, st.st_mtime_ns)
        except OSError:
            continue
    return state


def test_every_mutation_check_leaves_the_tree_stat_identical():
    """**AND THE TREE MUST END THE WAY IT STARTED -- BYTES AND MTIME.**

    **AND EVERY MUTATION CHECK THAT WRITES THE REAL SRC IS COVERED**,
    because the defect is a whole class and not one tool's typo. MEASURED
    2026-11-07: `mutation_check_walrus.py`,
    `mutation_check_gate_staleness.py` and `mutation_check_property_fp.py`
    all write a real `src/*.py` and all restored only their bytes.

    RED: remove the `os.utime` restore from any one of them.
    """
    for name in REAL_WRITERS:
        before = _tree_state()
        assert before, "the tree state is empty"

        tool = os.path.join(REPO, "tools", name)
        proc = subprocess.run([sys.executable, "-B", tool],
                              capture_output=True, text=True, cwd=REPO)
        assert proc.returncode == 0, (
            "%s did not pass: %s" % (name, (proc.stdout + proc.stderr)[-1200:]))

        after = _tree_state()

        changed_bytes = [p for p in before
                         if p in after and before[p][0] != after[p][0]]
        changed_mtime = [p for p in before
                         if p in after and before[p][1] != after[p][1]]
        assert not changed_bytes, (
            "%s changed the bytes of %r" % (name, changed_bytes))
        assert not changed_mtime, (
            "%s left the tree looking changed: %r moved, and the gate "
            "fingerprints the mtime of every rule file"
            % (name, [os.path.basename(p) for p in changed_mtime]))


def test_the_gate_does_not_go_stale_after_a_mutation_check():
    """**AND THE GATE MUST NOT GO STALE, because the tree did not
    change.** And this is the end-to-end one: the gate's own answer.

    RED: remove the `os.utime` restore.
    """
    sys.path.insert(0, os.path.join(REPO, "src"))
    import fc_gate
    g = fc_gate.FieldCoreGate()
    g.warm()
    assert g.stale(force=True) is None, "the gate was stale before"

    for name in REAL_WRITERS:
        tool = os.path.join(REPO, "tools", name)
        subprocess.run([sys.executable, "-B", tool],
                       capture_output=True, text=True, cwd=REPO)

    stale = g.stale(force=True)
    assert stale is None, (
        "the gate went stale after a mutation check that restored the "
        "file: %r\n\n"
        "AND IF THE FILE NAMED ABOVE IS NOT ONE OF THE MUTATION CHECKS' "
        "TARGETS, THEN SOMETHING ELSE WROTE IT DURING THIS TEST.\n\n"
        "MEASURED 2026-11-07: the `workqueue-continuation` cron job runs "
        "EVERY 25 MINUTES and writes to `simself/src/`, which the gate "
        "fingerprints on purpose. So a failure here can be the cron, and "
        "the gate naming a file in `simself/src` is the gate doing its "
        "job, not this test being wrong." % (stale,))
    assert g.stale(force=True) is None, "the gate went stale"


def test_the_list_of_real_writers_is_measured_not_guessed():
    """**AND THE LIST OF TOOLS THAT WRITE THE REAL SRC IS MEASURED**, so
    a new one cannot join without this file noticing."""
    tools = os.path.join(REPO, "tools")
    found = []
    for name in sorted(os.listdir(tools)):
        if not name.startswith("mutation_check"):
            continue
        text = open(os.path.join(tools, name), encoding="utf-8",
                    errors="replace").read()
        # a writer of the real src names a src path and writes to it
        if ('SRC / "' in text or 'SRC / \'' in text
                or '"src"' in text and "write_text" in text):
            if "TARGET.write_text" in text or "WIRING" in text:
                found.append(name)
    missing = [n for n in found if n not in REAL_WRITERS]
    assert not missing, (
        "these tools write a real source file and are not in REAL_WRITERS: "
        "%r -- and a tool that writes the real src and restores only its "
        "bytes leaves the tree looking changed" % missing)
