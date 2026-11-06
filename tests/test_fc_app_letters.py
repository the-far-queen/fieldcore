"""
test_fc_app_letters.py -- every letter is LIVE, and the check can fail.

Central rule 7: a test that cannot fail is not a test. Every test below
names its RED version in the docstring, and the mutation at the bottom
proves each one goes red when the mechanism is removed.

THE DEFECT THIS FILE WAS WRITTEN AGAINST
-----------------------------------------
measured 2026-11-06, on `simself/src/modulator.py`:

    the whole module body was wrapped in `try: ... except ImportError:`,
    so the import SUCCEEDED while the classes were never created.

the swallowed error was:

    ImportError("cannot import name 'SpiralStage' from 'state_vector'")

and it was the first of THREE dead imports in the same block:

    from state_vector import StateVector, SpiralStage
        -> ImportError: cannot import name 'SpiralStage'
    from governor import Governor
        -> ModuleNotFoundError: No module named 'governor'
    from boundaries import Boundaries
        -> ImportError: cannot import name 'Boundaries'

`letter_m` in fc_app.py reported this as STUB with the reason "the
module imports but does not define Modulator at module level". The
survey was right and the module was wrong. The module is fixed at the
source; this file is what stops it from happening again.

WHY THE CHECKS BELOW ARE NOT JUST "letter M is LIVE"
-----------------------------------------------------
a single assertion that M is LIVE would pass again the moment somebody
re-wrapped the module body in a try/except, because the survey would
report STUB and STUB is not LIVE -- so that one IS enough. But the
generalisation matters more than the instance, and this repo has three
modules with the same shape:

    simself/src/modulator.py            (fixed here)
    simself/src/loop.py                 (still swallows: 'environment')
    simself/src/resilient_self_model.py (still swallows: 'SwedenborgianAxes')

so there is a check for the CLASS here too, in
test_no_module_in_simself_swallows_its_own_import_error. It names the
two survivors as STUBS with a reason, which is the project's own rule:
a module is either LIVE or it is NAMED AS A STUB, never silently
broken. The naming is a decision recorded in the test, so a third
module cannot join the list by accident.
"""

from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.join(REPO, "..", "simself", "src")
ATLAS_SRC = os.path.join(REPO, "..", "atlas-exam", "src")
for _p in (FC_SRC, SS_SRC, ATLAS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fc_app  # noqa: E402

SIMSELF_SRC = os.path.join(REPO, "..", "simself", "src")


# ---------------------------------------------------------------------------
# 1. letter M is LIVE, and it is live for the right reason
# ---------------------------------------------------------------------------

def test_letter_m_is_live_and_measured():
    """THE LOAD-BEARING PROPERTY: M is LIVE and it MEASURED something.

    A letter that reports LIVE with an empty measurement is the hole
    this project fights wearing a passing test's clothes. So this
    asserts the measurement is populated, not just that the state
    string says LIVE.

    RED: if `modulator` stopped defining `Modulator` at module level,
    `letter_m` returns a Stub and this fails on the state.
    """
    letter = fc_app.letter_m()
    assert letter.state == "LIVE", (letter.state, letter.reason)
    m = letter.measured
    assert m.get("has_modulator") is True, m
    # the cycle keys are the evidence that run_cycle ran and returned
    # a measurement. an empty list means the probe saw nothing.
    assert m.get("cycle_keys"), (
        "letter M is LIVE but measured nothing: %s" % m)
    assert "stage" in m, m
    assert m["stage"], m


def test_the_modulator_module_defines_its_class_at_module_level():
    """The import must SUCCEED WITH THE CLASS PRESENT.

    This is the check that would have caught the original defect
    directly, without going through the survey. `import modulator`
    returning a module that has no `Modulator` attribute is the exact
    shape of the swallowed-import bug: the import worked, the work
    did not happen.

    RED: re-wrap the module body in try/except ImportError and this
    fails.
    """
    import modulator
    assert hasattr(modulator, "Modulator"), (
        "modulator imported but does not define Modulator at module "
        "level: %r" % (dir(modulator),))
    # the class must be constructible with no arguments, because the
    # survey constructs it that way.
    instance = modulator.Modulator()
    assert instance is not None
    cycle = instance.run_cycle()
    assert isinstance(cycle, dict), cycle
    assert cycle.get("stage"), cycle


def test_the_modulator_import_is_not_wrapped_in_a_swallowing_try():
    """THE SOURCE-LEVEL CHECK: no try/except may swallow the imports.

    The defect was structural: the module body was inside the try, so
    every failure of every import became a silently missing class.
    The fix moved the imports out. This asserts that structurally, by
    reading the AST, so the shape cannot come back.

    RED: wrap the module body in try/except ImportError again and this
    fails, even though the import still succeeds.
    """
    path = os.path.join(SIMSELF_SRC, "modulator.py")
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    # every module-level `try` in this file must exist only to guard
    # the optional yaml import, and must not contain the class or
    # function definitions.
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        guarded = [n for n in node.body
                   if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
        assert not guarded, (
            "modulator.py has a module-level try/except that wraps %s. "
            "a swallowed import is a silently missing class."
            % [n.name for n in guarded])
        # the only permitted module-level try guards a single import
        assert len(node.body) == 1 and isinstance(node.body[0], ast.Import), (
            "the module-level try/except must guard exactly one import")


def test_the_modulator_uses_the_simself_governor_not_the_fieldcore_one():
    """THE NAME-COLLISION CHECK: `governor` is two different modules.

    `fieldcore/src/governor.py` exists and sits on the SAME sys.path
    the survey builds, so the old `from governor import Governor` would
    have imported the WRONG substrate's governor -- and it would have
    failed with a different error depending on which src/ came first.
    The modulator must name the simself governor explicitly.

    RED: change the import back to `from governor import Governor` and
    this fails.
    """
    path = os.path.join(SIMSELF_SRC, "modulator.py")
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    # AST, not a string search. the module's docstring QUOTES the dead
    # import, and a string search would match its own explanation of
    # the bug -- which is how a check ends up failing for the wrong
    # reason.
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)

    assert "governor" not in imported, (
        "modulator.py imports a bare 'governor', which resolves to "
        "fieldcore/src/governor.py on the survey's sys.path")
    assert "simself_core" in imported, (
        "modulator.py must name the simself governor explicitly")
    assert "boundaries" in imported and "metrics" in imported, (
        "modulator.py must import its hard dependencies explicitly: %s"
        % sorted(imported))


# ---------------------------------------------------------------------------
# 2. the survey as a whole
# ---------------------------------------------------------------------------

def test_the_whole_survey_is_ten_live_and_no_holes():
    """LIVE 10, STUB 0, DARK 0.

    RED: if any letter went back to STUB or DARK -- M going back to
    STUB being the case this file exists for -- this fails.
    """
    letters = fc_app.survey()
    states = {lt.letter: lt.state for lt in letters}
    assert len(letters) == 10, states
    for lt in letters:
        assert lt.state == "LIVE", (lt.letter, lt.state, lt.reason)
    live = sum(1 for lt in letters if lt.state == "LIVE")
    stub = sum(1 for lt in letters if lt.state == "STUB")
    dark = sum(1 for lt in letters if lt.state == "DARK")
    assert (live, stub, dark) == (10, 0, 0), (live, stub, dark)


def test_letter_m_still_reports_dark_with_a_reason_when_the_probe_raises():
    """A letter that cannot run must be DARK and say WHY.

    The M probe must not be a rubber stamp. This drives the decorator
    with a probe that raises and checks the failure is NAMED.

    RED: if the decorator swallowed the exception and reported LIVE,
    this fails.
    """
    @fc_app._letter("Z", "does not exist", "a letter the system lacks",
                    "nowhere")
    def letter_z():
        raise RuntimeError("this letter does not exist, by construction")

    z = letter_z()
    assert z.state == "DARK", z.state
    assert "RuntimeError" in z.reason, z.reason


# ---------------------------------------------------------------------------
# 2b. the second defect: the M probe reported LIVE for a modulator
#     that measured NOTHING
# ---------------------------------------------------------------------------

def _with_a_fake_modulator(source, fn):
    """run `fn` against a fake `modulator` module built from `source`.

    the fake is built in a scratch directory and put FIRST on
    sys.path, so the real simself/src/modulator.py is shadowed for the
    duration and the file on disk is never touched.
    """
    import importlib
    import shutil
    import tempfile

    scratch = tempfile.mkdtemp(prefix="fc_fake_modulator_")
    original_path = sys.path[:]
    original_module = sys.modules.get("modulator")
    try:
        with open(os.path.join(scratch, "modulator.py"), "w",
                  encoding="utf-8") as handle:
            handle.write(source)
        sys.path.insert(0, scratch)
        sys.modules.pop("modulator", None)
        importlib.invalidate_caches()
        return fn()
    finally:
        sys.path[:] = original_path
        sys.modules.pop("modulator", None)
        if original_module is not None:
            sys.modules["modulator"] = original_module
        shutil.rmtree(scratch, ignore_errors=True)


def test_a_modulator_without_a_cycle_is_not_reported_live():
    """THE SECOND DEFECT, MEASURED 2026-11-06.

    `letter_m` used to read `cycle = m.run_cycle() if hasattr(m,
    "run_cycle") else {}`. So a `Modulator` class with NO run_cycle was
    reported LIVE, with cycle_keys=[] and stage="". That is not LIVE by
    fc_app's own definition -- "it was constructed and it ran, and it
    produced a measurement" -- and it is the same defect class as the
    import swallow one level up: a probe that cannot fail.

    RED: if the `hasattr(m, "run_cycle")` fallback came back, this
    fails.
    """
    def check():
        letter = _with_a_fake_modulator(
            "class Modulator:\n"
            "    def __init__(self):\n"
            "        pass\n", fc_app.letter_m)
        assert letter.state != "LIVE", (
            "a modulator with no run_cycle was reported LIVE: %s"
            % letter.measured)
        assert letter.state == "STUB", (letter.state, letter.reason)
        assert "run_cycle" in letter.reason, letter.reason
        return letter

    check()


def test_a_modulator_that_measures_nothing_is_not_reported_live():
    """A controller that runs and returns an empty measurement is a stub.

    Same defect class, one step deeper: the class exists, the cycle
    runs, and the result is empty. Reporting that as LIVE is claiming
    a measurement that does not exist.

    RED: if the empty-cycle check came back, this fails.
    """
    def check():
        letter = _with_a_fake_modulator(
            "class Modulator:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def run_cycle(self):\n"
            "        return {}\n", fc_app.letter_m)
        assert letter.state != "LIVE", (
            "a modulator that measured nothing was reported LIVE: %s"
            % letter.measured)
        assert letter.state == "STUB", (letter.state, letter.reason)
        assert "measurement" in letter.reason, letter.reason
        return letter

    check()


def test_a_modulator_whose_cycle_returns_a_non_dict_is_not_reported_live():
    """A cycle that returns a non-dict is not a measurement.

    RED: if the isinstance check came back, this fails.
    """
    def check():
        letter = _with_a_fake_modulator(
            "class Modulator:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def run_cycle(self):\n"
            "        return None\n", fc_app.letter_m)
        assert letter.state != "LIVE", (
            "a modulator returning None was reported LIVE: %s"
            % letter.measured)
        assert letter.state == "STUB", (letter.state, letter.reason)
        return letter

    check()


# ---------------------------------------------------------------------------
# 2c. the modulator is a CONTROLLER, not a shell
# ---------------------------------------------------------------------------

def test_the_modulator_actually_advances_its_stage():
    """THE MEASUREMENT MUST MOVE, OR IT MEASURES NOTHING.

    A controller whose every number is constant is a controller that
    computes nothing. This asserts the stage TRANSITION actually
    happens, which is the branch that was unreachable while the stage
    progress could only ever be reset to 0.0.

    RED: if the progress stops advancing, or the threshold is set
    above the resting coherence so no state can cross it, this fails.
    """
    import modulator
    m = modulator.Modulator()
    stages = [m.run_cycle()["stage"] for _ in range(12)]
    assert "seeker" in stages, stages
    assert "deconstructor" in stages, (
        "the stage never advanced -- the transition branch is "
        "unreachable: %s" % stages)
    # and the transition must be the LAST thing that happened, not the
    # first: a controller that starts at the top has no path.
    assert stages.index("deconstructor") > stages.index("seeker"), stages


def test_the_modulators_coherence_is_measured_and_moves():
    """THE COHERENCE MUST NOT BE A FIXED POINT.

    MEASURED 2026-11-06: the coherence was read from the metrics
    tracker's own stage_assessment AND recorded back into it, so it was
    the mean of copies of itself -- 0.5000 on every cycle, forever. It
    is now measured from the constitution, which the act step moves.

    RED: if the coherence goes back to being the tracker's echo, this
    fails.
    """
    import modulator
    m = modulator.Modulator()
    first = m.run_cycle()
    last = first
    for _ in range(5):
        last = m.run_cycle()
    assert last["coherence"] != 0.5, (
        "the coherence is a fixed point at 0.5 -- it is being echoed, "
        "not measured")
    assert first["coherence"] > 0.0, first


def test_the_modulator_records_a_governor_refusal():
    """THE GATE MUST BE ABLE TO SAY NO, AND THE NO MUST BE RECORDED.

    A controller that can never be refused is a controller that does not
    consult a gate. This drives a sacred-axis violation through the
    M0 governor and checks the refusal comes back NAMED and that the
    change is not applied.

    RED: if the verdict is swallowed, or the axis moves anyway, this
    fails.
    """
    import modulator
    m = modulator.Modulator()
    # push a proposal onto a sacred axis, far enough to breach it
    m.AXIS_PROPOSALS["activate_recursive_stress_test"] = (
        "lexical_integrity", 0.5)
    m.agent.constitution.axes["lexical_integrity"].value = 0.05
    before = m.agent.constitution.axes["lexical_integrity"].value

    cycle = m.run_cycle()
    assert cycle["allowed"] is False, cycle
    assert cycle["violated_axes"], cycle
    assert "lexical_integrity" in cycle["violated_axes"], cycle
    after = m.agent.constitution.axes["lexical_integrity"].value
    assert after == before, (
        "the axis moved despite the refusal: %s -> %s" % (before, after))
    # and the refusal is in the event log, with its reason
    assert m.events, "the refusal was not recorded"
    assert m.events[-1]["details"]["allowed"] is False, m.events[-1]


def test_the_modulator_honours_an_armed_boundary():
    """THE BOUNDARY LAYER IS A REAL GATE, NOT A DESCRIPTION OF ONE.

    RED: if enforce_sacred_constraints stops consulting the live
    boundary set, this fails.
    """
    import modulator
    m = modulator.Modulator()
    assert m.enforce_sacred_constraints({"reason": "anything"}) is True

    m.agent.boundaries.boundaries["no_hallucination"].check_fn = \
        lambda: False
    assert m.enforce_sacred_constraints({"reason": "anything"}) is False, (
        "an armed boundary did not refuse the action")


# ---------------------------------------------------------------------------
# 3. the CLASS of defect, not just this instance
# ---------------------------------------------------------------------------

#: the modules in simself/src that are allowed to swallow their import
#: error. Each is NAMED, with the reason -- which is the project's own
#: rule: a module is either LIVE or it is NAMED AS A STUB, never
#: silently broken.
#:
#: modulator.py is NOT in this list. It was fixed.
KNOWN_STUBBED_MODULES = {
    "loop.py": "references the removed `environment` module; not on the "
               "runtime path",
    "resilient_self_model.py": "references the removed "
                               "`state_vector.SwedenborgianAxes` and "
                               "`CoreMetrics`; not on the runtime path",
}


def _modules_that_swallow_their_import_error():
    """every simself/src module whose body sits inside try/except ImportError.

    found by AST, not by importing: an importing check cannot see a
    module whose classes are missing, because the import SUCCEEDS.
    """
    found = {}
    for root, dirs, files in os.walk(SIMSELF_SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            try:
                tree = ast.parse(open(path, encoding="utf-8",
                                      errors="replace").read())
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, ast.Try):
                    continue
                catches_import = any(
                    isinstance(h.type, ast.Name) and h.type.id == "ImportError"
                    for h in node.handlers)
                if not catches_import:
                    continue
                # a try that only guards an import is fine. a try that
                # also defines classes or functions is the swallow.
                defines = [n.name for n in node.body
                           if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
                if defines:
                    found[os.path.relpath(path, SIMSELF_SRC).replace(
                        "\\", "/")] = defines
    return found


def test_no_module_in_simself_swallows_its_own_import_error():
    """THE GENERAL CHECK, and the one that would have caught the defect.

    A module whose class definitions sit inside `try: ... except
    ImportError:` has a hole that no import can see: the import
    succeeds, so every caller believes the module works, and the class
    is simply not there.

    the survivors are NAMED in KNOWN_STUBBED_MODULES, with a reason.
    a NEW module cannot join that list by accident -- adding one is a
    decision someone has to write down.

    RED: re-wrap modulator.py's body in try/except ImportError and
    this fails, because modulator.py is not in the named list.
    """
    found = _modules_that_swallow_their_import_error()
    unnamed = {name: names for name, names in found.items()
               if os.path.basename(name) not in KNOWN_STUBBED_MODULES}
    assert not unnamed, (
        "these modules swallow their import error and are not NAMED as "
        "stubs: %s" % unnamed)

    # and the named list must match reality in both directions: a stub
    # that was FIXED must be removed from the list, or the list becomes
    # a place where brokenness hides.
    real = set(found)
    listed = set(KNOWN_STUBBED_MODULES)
    assert listed <= real, (
        "these are named as stubs but no longer swallow an import "
        "error: %s" % sorted(listed - real))


def test_the_named_stubs_carry_a_reason():
    """A stub with no reason is a hole wearing a stub's name.

    RED: blank a reason and this fails.
    """
    for name, reason in KNOWN_STUBBED_MODULES.items():
        assert reason.strip(), (
            "the stub %r is named without a reason" % name)


# ---------------------------------------------------------------------------
# 4. THE MUTATION -- the proof that the checks above can fail
# ---------------------------------------------------------------------------

def test_mutation_the_modulator_import_can_be_broken_and_the_survey_catches_it():
    """MUTATION: break the modulator's import, and prove the checks go RED.

    This is the central rule 7 proof. It does not edit the file on
    disk. It builds a fake `modulator` module in a temp directory --
    the same shape as the original bug: the import SUCCEEDS and the
    class is NOT defined -- puts that directory FIRST on sys.path, and
    asserts that the survey reports M as something other than LIVE.

    THE REASON IT IS BUILT RATHER THAN EDITED: editing simself/src on
    disk from inside a test would race any other test reading the same
    file, and a test that corrupts the source tree to prove itself is
    a test that can leave the tree broken. This builds the same defect
    in a scratch directory and removes it afterwards.

    MUST BE CAUGHT BY: test_letter_m_is_live_and_measured,
    test_the_modulator_module_defines_its_class_at_module_level,
    test_the_whole_survey_is_ten_live_and_no_holes.
    """
    import shutil
    import tempfile

    scratch = tempfile.mkdtemp(prefix="fc_mutation_")
    original_path = sys.path[:]
    original_module = sys.modules.get("modulator")
    try:
        # THE DEFECT, REBUILT: the module imports, and the class is
        # never created because the import failed inside a try.
        with open(os.path.join(scratch, "modulator.py"), "w",
                  encoding="utf-8") as handle:
            handle.write(
                "try:\n"
                "    from state_vector import StateVector, SpiralStage\n"
                "    class Modulator:\n"
                "        pass\n"
                "except ImportError as _e:\n"
                "    _legacy_marker = repr(_e)\n")

        sys.path.insert(0, scratch)
        sys.modules.pop("modulator", None)
        try:
            import importlib
            importlib.invalidate_caches()
            broken = importlib.import_module("modulator")
            assert not hasattr(broken, "Modulator"), (
                "the mutation did not take effect: the fake module "
                "defines Modulator")

            # the survey must NOT call this LIVE.
            letter = fc_app.letter_m()
            assert letter.state != "LIVE", (
                "the survey reported a broken modulator as LIVE -- the "
                "check cannot fail")
            assert letter.state == "STUB", (letter.state, letter.reason)
            assert "Modulator" in letter.reason, letter.reason
        finally:
            sys.modules.pop("modulator", None)
            if original_module is not None:
                sys.modules["modulator"] = original_module
    finally:
        sys.path[:] = original_path
        shutil.rmtree(scratch, ignore_errors=True)


def test_mutation_the_real_modulator_is_reimportable_after_the_fake_one():
    """MUTATION: the fake module must not poison the real one.

    The previous test puts a broken `modulator` on sys.path. If the
    real module were left shadowed, every LATER test in this file
    would be testing the fake -- and the suite would go green for the
    wrong reason. So this checks the real module is back.

    MUST BE CAUGHT BY: the ordering of the tests above. RED: if the
    mutation test did not restore sys.path and sys.modules, this
    fails.
    """
    import modulator
    assert hasattr(modulator, "Modulator"), (
        "the real modulator module is shadowed by the mutation's fake")
    assert fc_app.letter_m().state == "LIVE", (
        "the real modulator no longer reports LIVE")
