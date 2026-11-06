"""
test_capability_wiring.py -- the wiring must hold, and it must be able to
go red.

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all
modules"*. The census measures which modules are reachable. This test
measures the other half: that every capability the census called an
orphan is now REACHED, that each one is EXERCISED, and that the report
of that exercise cannot lie.

**AND THE CHECKS CAN FAIL.** Three ways, and all three are here:

  1  the census must no longer report an orphan, and the registry must
     cover exactly the list the census measured before the wiring.
     Break the registry and the coverage check goes red.
  2  the table must be re-derived, not trusted. The checker re-runs
     every probe and compares, so a table that claims LIVE where the
     probe raises is caught.
  3  the recorded expectations are written out by hand, so a probe that
     starts returning a constant is caught by the value check and by
     the sensitivity check.

The mutation harness (`tools/mutation_check_capability_wiring.py`)
breaks the wiring at the SOURCE level and shows each break go red.

Run:
    python -m pytest tests/test_capability_wiring.py -q
    python src/capability_wiring.py --selftest
    python tools/mutation_check_capability_wiring.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
TOOLS = REPO / "tools"

for _path in (str(SRC), str(TOOLS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import capability_wiring as cw      # noqa: E402
import wiring_census as wc          # noqa: E402


#: THE ORPHAN LIST AS THE CENSUS MEASURED IT, BEFORE THE WIRING.
#:
#: AND WHY IT IS WRITTEN OUT HERE RATHER THAN COMPUTED. If the test ran
#: the census and compared the result to the registry, then a registry
#: that dropped an entry would also drop the expectation, and the test
#: would agree with itself. This list was produced by
#:
#:     python tools/wiring_census.py --orphans
#:
#: on 2026-11-06, before `src/capability_wiring.py` existed.
ORPHANS_BEFORE_WIRING = (
    "fieldcore/src/adversarial_wiring.py",
    "fieldcore/src/bitnet_ops.py",
    "fieldcore/src/constraint_projection.py",
    "fieldcore/src/degrees_of_freedom.py",
    "fieldcore/src/farmath/number_theory.py",
    "fieldcore/src/fieldcore_cell.py",
    "fieldcore/src/fisher_metric.py",
    "fieldcore/src/sheaf_nn_index.py",
    "fieldcore/src/stalk_control.py",
    "simself/src/aif_being.py",
    "simself/src/constitutional/entity.py",
    "simself/src/constitutional/master_protocols.py",
    "simself/src/constitutional/metalog.py",
    "simself/src/constitutional/twin_prime_coupling.py",
    "simself/src/efmw-corpus/__init__.py",
    "simself/src/harness/planner.py",
    "simself/src/harness/telegram_bot.py",
    "simself/src/harness/telegram_text_bot.py",
    "simself/src/harness/tools.py",
    "simself/src/m1_m0_negotiation.py",
    "simself/src/research/companion.py",
    "simself/src/research/contracts.py",
    "simself/src/research/harness_adapters.py",
    "simself/src/semantic_chunking_layer.py",
    "simself/src/system/core.py",
)


# ---------------------------------------------------------------- coverage


def test_registry_covers_exactly_the_measured_orphans():
    """Every orphan the census measured has an entry, and nothing else does.

    This is the check that goes red when an entry is skipped. It
    compares the registry against a list written out by hand from the
    census's own output, so the two cannot drift together.
    """
    registered = {capability.name for capability in cw.REGISTRY}
    assert registered == set(ORPHANS_BEFORE_WIRING), (
        "the registry and the measured orphan list disagree: %s"
        % (registered ^ set(ORPHANS_BEFORE_WIRING),))


def test_the_census_now_reports_no_orphan():
    """The census must see every capability as reached.

    This is the end-to-end claim: the wiring file's imports are what
    move the modules out of the ORPHAN bin, so the census is the
    instrument that says whether the wiring took.
    """
    modules = wc.census()
    orphans = ["%s/%s" % (m.repo, m.rel) for m in modules if m.bin == "ORPHAN"]
    assert orphans == [], "the census still reports orphans: %s" % (orphans,)
    islands = ["%s/%s" % (m.repo, m.rel) for m in modules if m.bin == "ISLAND"]
    assert islands == [], "the census reports islands: %s" % (islands,)


def test_the_census_attributes_the_edge_to_the_wiring_file():
    """Each wired capability must name capability_wiring as its importer.

    Otherwise the module is WIRED for some other reason, and this file
    is decoration: the census would be happy with a registry that
    wired nothing.
    """
    modules = wc.census()
    by_path = {"%s/%s" % (m.repo, m.rel): m for m in modules}
    for name in ORPHANS_BEFORE_WIRING:
        module = by_path[name]
        assert module.bin == "WIRED", "%s is %s, not WIRED" % (name, module.bin)
        assert any("capability_wiring" in (inbound or "") for inbound in module.inbound), (
            "%s is WIRED but not through capability_wiring: %s"
            % (name, module.inbound))


# ------------------------------------------------------------------ table


@pytest.fixture(scope="module")
def rows():
    """The table, computed once: running 25 probes twice is slow."""
    return cw.run_all(cw.REGISTRY)


def test_every_capability_is_live_or_dark_with_a_reason(rows):
    """There is no third state.

    A row that is neither LIVE with a number nor DARK with a reason is
    a capability whose fate is unknown, which is the failure mode this
    whole exercise exists to remove.
    """
    for row in rows:
        assert row.status in ("LIVE", "DARK"), row
        if row.status == "LIVE":
            assert row.value is not None, row
            assert row.reason == "", row
        else:
            assert row.reason.strip(), "%s is DARK with no reason" % row.name


def test_no_capability_is_left_unmeasured(rows):
    """Every capability must produce a number or name why it cannot.

    A DARK is allowed and a DARK is not a failure -- two capabilities
    in this tree are documented stubs and are NAMED AS STUBS with a
    reason. What is not allowed is a capability that is silently
    unmeasured.
    """
    dark = [row for row in rows if row.status == "DARK"]
    assert len(dark) <= 2, "more capabilities went dark than the two named stubs: %s" \
        % ([row.name for row in dark],)
    for row in dark:
        assert row.reason.strip(), row


def test_the_wiring_holds(rows):
    """The checker must find no problems in the real tree."""
    problems = cw.check(cw.REGISTRY, rows)
    assert problems == [], "the wiring does not hold: %s" % (problems,)


def test_the_checker_goes_red_when_the_registry_is_broken(rows):
    """Break the registry and the checker must notice.

    The break is a probe that returns a constant. That is the most
    likely way a wiring rots quietly: the module still imports, the
    table still has a number in it, and the number says nothing. The
    recorded expectation catches it, and so does the sensitivity check.
    """
    victim = cw.REGISTRY[1]

    def constant(x: int) -> float:
        return 42.0

    broken = cw.Capability(
        name=victim.name, module=victim.module, callable=victim.callable,
        measures=victim.measures, run=constant, expect=victim.expect,
        tol=victim.tol, varies=victim.varies,
    )
    broken_registry = tuple(broken if c.name == victim.name else c
                            for c in cw.REGISTRY)
    broken_rows = cw.run_all(broken_registry)
    problems = cw.check(broken_registry, broken_rows)
    assert problems, "a probe that returns a constant was not caught"
    assert any("expectation" in problem or "sensitivity" in problem
               for problem in problems), problems


def test_the_checker_goes_red_when_a_dark_reason_is_dropped(rows):
    """A DARK row without a reason is a skip that is not visible."""
    broken = []
    for row in rows:
        if row.status == "DARK":
            broken.append(cw.Result(name=row.name, module=row.module,
                                    callable=row.callable, measures=row.measures,
                                    status="DARK", value=None, reason=""))
            break
    else:
        pytest.skip("no DARK row to blank on this machine")
    problems = cw.check(cw.REGISTRY, broken)
    assert any("reason" in problem for problem in problems), problems


def test_the_checker_goes_red_when_a_live_row_covers_a_raise(rows):
    """A row that says LIVE where the probe raises is a lie."""
    broken = []
    for row in rows:
        if row.status == "DARK":
            broken.append(cw.Result(name=row.name, module=row.module,
                                    callable=row.callable, measures=row.measures,
                                    status="LIVE", value=1.0, reason=""))
            break
    else:
        pytest.skip("no DARK row to relabel on this machine")
    problems = cw.check(cw.REGISTRY, broken)
    assert any("status" in problem for problem in problems), problems


def test_the_checker_goes_red_when_an_entry_is_skipped():
    """Dropping an entry must leave the coverage check red."""
    trimmed = tuple(c for c in cw.REGISTRY if c.name != ORPHANS_BEFORE_WIRING[0])
    problems = cw.check(trimmed, cw.run_all(trimmed))
    assert any("coverage" in problem for problem in problems), problems


# ------------------------------------------------------------- the source


def test_the_module_is_a_census_entry_point():
    """The wiring file must be reachable, or its imports wire nothing.

    The census only counts an inbound reference from a module that is
    itself reachable, and the roots of that reachability are the entry
    points. A wiring file with no __main__ guard would be an orphan
    itself, and every capability it names would stay an orphan.
    """
    modules = wc.census()
    wiring = [m for m in modules if m.rel == "src/capability_wiring.py"]
    assert wiring, "the census does not see src/capability_wiring.py"
    assert wiring[0].reachable, "the wiring file is not reachable, so it wires nothing"


def test_the_imports_are_deferred_and_fail_closed():
    """A probe must not import at module load.

    `fieldcore/src/fieldcore_cell.py` imports torch at module scope and
    the project's interpreter has no torch, so an eager import in the
    wiring file would make the whole file unimportable and the wiring
    would wire nothing.

    The check is that the file imports with no heavy dependency
    present, which is what a plain `import capability_wiring` does.
    """
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); "
         "import capability_wiring as cw; "
         "print(len(cw.REGISTRY))" % str(SRC)],
        capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, "the wiring file does not import cleanly: %s" \
        % proc.stderr[-600:]
    assert proc.stdout.strip() == str(len(cw.REGISTRY)), proc.stdout


def test_the_selftest_proves_the_table_can_go_red():
    """`--selftest` must catch every deliberate fault it injects."""
    proc = subprocess.run(
        [sys.executable, str(SRC / "capability_wiring.py"), "--selftest"],
        capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, "the selftest did not pass: %s\n%s" \
        % (proc.stdout[-2000:], proc.stderr[-1000:])
    assert "MISSED" not in proc.stdout, proc.stdout
    assert "4 of 4 deliberate faults were caught" in proc.stdout, proc.stdout


def test_the_cli_prints_the_table_and_reports_dark_capabilities():
    """The CLI must print a row per capability and name the DARK ones."""
    proc = subprocess.run(
        [sys.executable, str(SRC / "capability_wiring.py")],
        capture_output=True, text=True, cwd=str(REPO))
    out = proc.stdout
    assert out.count("LIVE") + out.count("DARK") >= len(cw.REGISTRY) - 1
    for capability in cw.REGISTRY:
        assert capability.name in out, "%s is missing from the table" % capability.name
    # a DARK capability must carry its reason in the table
    for row in cw.run_all(cw.REGISTRY):
        if row.status == "DARK":
            assert row.reason[:40] in out, "the reason for %s is not printed" % row.name
