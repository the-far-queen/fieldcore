"""
test_evidence_carry_mutations.py -- the mutants for the carrying test,
and the harness.

WHY THIS IS A SEPARATE FILE. The mutation harness runs pytest against
a file. If that file CONTAINED the mutation tests, the child pytest
would run the mutation tests, which run pytest again, on the same file,
with no depth limit. The suite does not fail -- it recurses until the
machine is saturated, printing nothing, which is why it looks like a
hang. The project hit this on 2026-10-24 and wrote it down; it was hit
again on 2026-10-25 by the same mistake. So the harness runs the
behaviour files, which hold behaviour assertions and no mutation tests.

THE SHADOWING BUG, and it is the important part of this file.

    The first version of this harness put ONLY the mutated directory on
    PYTHONPATH -- the same way test_claim_register_mutations.py does.

    AND THE MUTATION STAYED GREEN. 29 passed.

    WHY. fc_gate.py imports predicate_layer, property_layer and
    provenance_scope AT RUN TIME by name. With only the two mutated
    files on PYTHONPATH, `import predicate_layer` FAILED, the gate
    degraded to a no-op, and the test asserted against a gate that
    catches nothing at all.

    A test that passes against a degraded instrument is not a test. It
    is the same failure class as the project's own nine bugs behind
    green output, and it is the reason every mutation here asserts on
    the mutant BEING LOADED before it asserts on the suite going red.

    THE FIX. The mutant directory goes FIRST on PYTHONPATH and the
    real src directory goes SECOND. So the two mutated modules shadow
    the originals and every other module resolves normally. And the
    harness CHECKS that the mutant is the module under test, by asking
    the child which file it loaded.

EVERY SUBPROCESS HAS A TIMEOUT. A checker that can hang can wedge the
machine, and the machine is not ours to wedge.

Run:
    python -m pytest tests/test_evidence_carry_mutations.py -q
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

#: The behaviour files. They hold NO mutation tests, so the child pytest
#: has nothing to recurse into.
BEHAVIOUR = [
    pathlib.Path(__file__).resolve().parent / "test_evidence_carry.py",
    pathlib.Path(__file__).resolve().parent / "test_fc_gate.py",
]

MUTATION_TIMEOUT = 240


def _mutated_dir(tmp_path, tag, files):
    """A directory holding mutated copies of the named modules.

    `files` is a list of (name, old, new) tuples.
    """
    d = tmp_path / ("mut_" + tag)
    d.mkdir(exist_ok=True)
    for name, old, new in files:
        text = (SRC / name).read_text(encoding="utf-8")
        assert old in text, "mutation anchor missing in %s: %r" % (
            name, old)
        (d / name).write_text(text.replace(old, new, 1), encoding="utf-8")
    return d


def _run_behaviour(pythonpath_dir):
    """Run the behaviour files against whatever is first on PYTHONPATH.

    AND THE PATH. The mutant directory comes FIRST and the real src
    comes SECOND. The mutant shadows the originals; every other module
    resolves normally. Putting ONLY the mutant on the path is what made
    the first version of this harness pass a mutation that should have
    failed -- the gate degraded to a no-op and caught nothing.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath_dir) + os.pathsep + str(SRC)
    out = subprocess.run(
        [sys.executable, "-m", "pytest"]
        + [str(b) for b in BEHAVIOUR]
        + ["-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=str(ROOT), env=env,
        timeout=MUTATION_TIMEOUT)
    return out.returncode != 0, out.stdout[-1200:]


def _assert_mutant_is_loaded(pythonpath_dir, module):
    """The mutant must BE the module under test.

    Without this, "the suite went red" could have come from anything --
    including a module that failed to import at all.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath_dir) + os.pathsep + str(SRC)
    code = ("import %s as m; print(m.__file__)" % module)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, cwd=str(ROOT), env=env,
                         timeout=MUTATION_TIMEOUT)
    assert out.returncode == 0, (
        "the child could not import %s: %s" % (module, out.stderr[-400:]))
    loaded = out.stdout.strip().splitlines()[-1]
    assert str(pythonpath_dir) in loaded, (
        "the MUTANT was not the module under test: %s" % loaded)
    return loaded


# ---------------------------------------------------------------------------
# THE CONTROL
# ---------------------------------------------------------------------------

def test_the_unmutated_instrument_is_green():
    """The control for every mutation below.

    Without it, "the suite went red" could just mean "the behaviour
    files are broken".
    """
    red, tail = _run_behaviour(SRC)
    assert not red, ("the unmutated instrument is not green:\n%s" % tail)


def test_the_real_source_is_what_gets_loaded():
    """The control for the SHADOWING check below.

    With the real src on the path, the real module is what is loaded.
    """
    loaded = _assert_mutant_is_loaded(SRC, "claim_register")
    assert str(SRC) in loaded


# ---------------------------------------------------------------------------
# THE MUTANTS
# ---------------------------------------------------------------------------

def test_mutation_removing_the_carry_check_goes_red(tmp_path):
    """Remove the carrying test from the register.

    THE MUTATION IS THE MECHANISM REMOVAL, not a weakening of it. The
    evidence layer's whole job is that a span asserting a measured
    claim must carry the measurement; removing the check removes the
    layer.

    AND THE SHADOWING CHECK, because the first version of this harness
    put only the mutant on PYTHONPATH and the mutation stayed GREEN:
    the gate degraded to a no-op, caught nothing, and the test passed
    against an instrument that was not there.
    """
    d = _mutated_dir(
        tmp_path, "carry",
        [("claim_register.py",
          "            if as_measurement and not _carries_measurement(span):\n"
          "                ungrounded.append(r)",
          "            if False:\n"
          "                ungrounded.append(r)")])
    _assert_mutant_is_loaded(d, "claim_register")
    red, tail = _run_behaviour(d)
    assert red, ("removing the carry check left the suite green:\n%s"
                 % tail)


def test_mutation_unwiring_the_gate_goes_red(tmp_path):
    """Take the measurement mode out of the gate's call site.

    The register keeps the carry check, but the gate stops asking for
    measurement mode -- so the layer never runs at the real call site
    again. This is the ORIGINAL defect, in the place it lives.
    """
    d = _mutated_dir(
        tmp_path, "unwire",
        [("fc_gate.py",
          "rd = self.register.read(span, as_measurement=as_measurement)",
          "rd = self.register.read(span)")])
    _assert_mutant_is_loaded(d, "fc_gate")
    red, tail = _run_behaviour(d)
    assert red, ("unwiring the gate left the suite green:\n%s" % tail)


def test_mutation_always_measurement_mode_goes_red(tmp_path):
    """Force the gate into measurement mode for every span.

    THE COUNTERWEIGHT MUTANT. This is the defect the first wiring had:
    the gate refused the ground's own eight claims, and it looked
    healthy. So this mutation must go RED on the counterweight tests --
    a gate that refuses the ground's own text is a gate that refuses
    everything.
    """
    d = _mutated_dir(
        tmp_path, "always",
        [("fc_gate.py",
          "as_measurement = presents_as_measurement(span)",
          "as_measurement = True")])
    _assert_mutant_is_loaded(d, "fc_gate")
    red, tail = _run_behaviour(d)
    assert red, ("forcing measurement mode left the suite green:\n%s"
                 % tail)
