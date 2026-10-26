"""
test_provenance_scope_mutations.py -- the mutants, and the harness.

WHY A SEPARATE FILE. The mutation harness runs pytest against a
file. If that file CONTAINED the mutation tests, the child pytest
would run the mutation tests, which run pytest again, on the same
file, with no depth limit. The suite does not fail -- it recurses
until the machine is saturated, printing nothing, which is why it
looks like a hang. The project hit this on 2026-10-24, hit it again
on 2026-10-25, and the fix is the same both times: the harness runs
the BEHAVIOUR file, which holds no mutation tests.

THE OTHER HALF. The mutant must genuinely BE the module under test.
The child gets the mutated copy first on PYTHONPATH and the behaviour
file does not insert src/ ahead of it -- so the child imports the
MUTANT. A green mutation test proves nothing if the mutant was never
loaded.

EVERY SUBPROCESS HAS A TIMEOUT. A checker that can hang can wedge the
machine, and the machine is not ours to wedge.

Run:
    python -m pytest tests/test_provenance_scope_mutations.py -q
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BEHAVIOUR = pathlib.Path(__file__).resolve().parent / "test_provenance_scope.py"

MUTATION_TIMEOUT = 180


def _mutated_dir(tmp_path, old, new):
    text = (SRC / "provenance_scope.py").read_text(encoding="utf-8")
    assert old in text, "mutation anchor missing: %r" % (old,)
    d = tmp_path / ("mut_" + re.sub(r"\W+", "_", old)[:24])
    d.mkdir(exist_ok=True)
    (d / "provenance_scope.py").write_text(text.replace(old, new, 1),
                                           encoding="utf-8")
    return d


def _run_behaviour(pythonpath_dir):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath_dir)
    out = subprocess.run(
        [sys.executable, "-m", "pytest", str(BEHAVIOUR),
         "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=str(ROOT), env=env,
        timeout=MUTATION_TIMEOUT)
    return out.returncode != 0, out.stdout[-800:]


def test_the_unmutated_scope_layer_is_green():
    """The control. Without it, 'red' could mean 'the file is broken'."""
    red, tail = _run_behaviour(SRC)
    assert not red, f"the unmutated scope layer is not green:\n{tail}"


def test_mutation_scanning_the_source_for_versions_goes_red(tmp_path):
    """THE POLLUTED INDEX. A free-text scan finds "0.9" in the module's
    own docstring, and the adversary's dangling reference becomes
    valid."""
    d = _mutated_dir(
        tmp_path,
        "        self.versions = _declared_versions(roots)",
        "        self.versions = set()\n"
        "        for m in VERSION_RE.finditer(blob):\n"
        "            self.versions.add(m.group(1))")
    red, tail = _run_behaviour(d)
    assert red, f"a scanned version index left the suite green:\n{tail}"


def test_mutation_dropping_the_assertion_test_goes_red(tmp_path):
    """Without it, the FRIEND's honest answer is refused."""
    d = _mutated_dir(
        tmp_path,
        "        if _asserts_about(text, v):\n"
        "            dangling.append(\"version %s\" % v)",
        "        dangling.append(\"version %s\" % v)")
    red, tail = _run_behaviour(d)
    assert red, f"dropping the assertion test left the suite green:\n{tail}"


def test_mutation_treating_every_denial_as_assertion_goes_red(tmp_path):
    """The other direction: every denial becomes an assertion, so the
    friend is refused again."""
    d = _mutated_dir(
        tmp_path,
        "    for m in DENIAL_MARKERS:\n"
        "        if m in window:\n"
        "            return False",
        "    return True")
    red, tail = _run_behaviour(d)
    assert red, f"ignoring the denial markers left the suite green:\n{tail}"


def test_mutation_narrowing_the_window_goes_red(tmp_path):
    """The window must be wide enough to hold the predicate."""
    d = _mutated_dir(
        tmp_path,
        "    window = low[max(0, pos - 90):pos + len(ref) + 90]",
        "    window = low[max(0, pos - 12):pos + len(ref) + 12]")
    red, tail = _run_behaviour(d)
    assert red, f"a narrow window left the suite green:\n{tail}"


def test_mutation_dropping_the_change_claim_check_goes_red(tmp_path):
    """A change that cannot be pointed at did not happen here."""
    d = _mutated_dir(
        tmp_path,
        "    if refs.changes and not (refs.versions or refs.files\n"
        "                             or refs.identifiers):",
        "    if False:")
    red, tail = _run_behaviour(d)
    assert red, f"dropping the change check left the suite green:\n{tail}"
