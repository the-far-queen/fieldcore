"""
test_fc_app_mutations.py -- proof that the tests in test_fc_app.py can fail.

Central rule 7: a test that cannot fail is not a test. So every
mechanism the fc_app/fc_hermes tests claim to protect is removed here,
one at a time, and the corresponding test must go RED.

Each mutation below names the mechanism it removes and the test that
catches it. A mutation that stays GREEN is a WEAK mutation -- it proves
nothing -- and is reported as such.

Run:
    python -m pytest work_repos/fieldcore/tests/test_fc_app_mutations.py -v
"""

from __future__ import annotations

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
import fc_hermes  # noqa: E402
import fc_wrapper  # noqa: E402


# ---------------------------------------------------------------------------
# THE HARNESS
# ---------------------------------------------------------------------------

def _run_one(test_name):
    """Run one test from test_fc_app and report whether it fails.

    Returns True when the test went RED (the mutation was caught).
    """
    import importlib
    import test_fc_app

    importlib.reload(test_fc_app)
    fn = getattr(test_fc_app, test_name, None)
    if fn is None:
        raise AssertionError("no such test: %s" % test_name)
    try:
        fn()
    except Exception:
        return True
    return False


def _with_patch(module, name, replacement):
    """A context manager that swaps a module attribute and puts it back."""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        original = getattr(module, name)
        setattr(module, name, replacement)
        try:
            yield
        finally:
            setattr(module, name, original)
    return _cm()


# ---------------------------------------------------------------------------
# THE MUTATIONS
# ---------------------------------------------------------------------------

def test_mutation_1_the_survey_mutates_the_live_boundary_again():
    """MUTATION: `letter_s` sets the LIVE check to `lambda: False` and
    restores a FRESH `lambda: True` -- the defect that was there.

    MUST BE CAUGHT BY: test_the_survey_leaves_an_armed_boundary_armed
    and test_the_survey_does_not_mutate_the_live_check_function.

    RED version of THIS test: if the mutation were not caught, this
    fails.
    """
    def mutated_letter_s():
        import boundaries
        b = boundaries.boundaries
        before = b.check_all()
        target = b.boundaries.get("no_hallucination")
        forced = None
        if target is not None:
            target.check_fn = lambda: False
            after = b.check_all()
            forced = {
                "allowed": bool(after.get("allowed")),
                "violated": list(after.get("violated", [])),
                "critical_violated": list(after.get("critical_violated", [])),
            }
            target.check_fn = lambda: True   # <-- THE DEFECT
        return {
            "boundaries": len(b.boundaries),
            "allowed_by_default": bool(before.get("allowed")),
            "passed": list(before.get("passed", [])),
            "can_refuse": bool(forced and forced["allowed"] is False),
            "forced_failure": forced,
        }

    original = fc_app.letter_s
    # AND THE PATCH IS ON `LETTERS`, NOT ON THE MODULE ATTRIBUTE.
    #
    # MEASURED 2026-11-04: the first version of this mutation patched
    # `fc_app.letter_s` and the test stayed GREEN -- the mutation did
    # nothing. `LETTERS` holds a DIRECT REFERENCE to the function
    # object, so rebinding the module attribute does not change what
    # `survey()` calls. A mutation that does not take effect is not a
    # mutation; it is a no-op that reports a pass.
    #
    # So the list entry is replaced. This is the WEAK-MUTATION lesson
    # from the wrapper chapter: the mutation has to remove the
    # mechanism, not merely shadow a name.
    original_letters = fc_app.LETTERS
    try:
        fc_app.LETTERS = [mutated_letter_s if fn is original else fn
                          for fn in original_letters]
        caught = _run_one("test_the_survey_leaves_an_armed_boundary_armed")
        assert caught, (
            "the mutation to the live boundary was NOT caught -- the test "
            "cannot fail")
    finally:
        fc_app.LETTERS = original_letters
        fc_app.letter_s = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_2_the_bridge_drops_the_ok_bit_again():
    """MUTATION: the bridge builds the trace without the ok bit -- the
    defect that was there.

    MUST BE CAUGHT BY: test_the_bridge_trace_says_REFUSED_when_the_gate_refuses
    and test_the_bridge_trace_agrees_with_the_wrapper_trace.
    """
    original = fc_hermes.Bridge.ask

    def mutated_ask(self, prompt, learn=True):
        import time
        t0 = time.time()
        r = fc_hermes.Reply(prompt=prompt)
        ex = self._wrapper.ask(prompt, learn=learn)
        r.answer = ex.answer
        r.delivered = ex.delivered
        r.answered_by = ex.answered_by
        # THE DEFECT: no ok bit, and no steps carried.
        r.trace = [s.to_dict()["step"] + ": " + s.to_dict()["detail"]
                   for s in ex.steps]
        r.letters = self.survey()
        r.elapsed = time.time() - t0
        return r

    try:
        fc_hermes.Bridge.ask = mutated_ask
        caught = _run_one(
            "test_the_bridge_trace_says_REFUSED_when_the_gate_refuses")
        assert caught, (
            "the dropped ok bit was NOT caught -- the test cannot fail")
    finally:
        fc_hermes.Bridge.ask = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_3_the_survey_stops_reporting_a_dark_letter():
    """MUTATION: the letter decorator swallows the exception and reports
    the letter as LIVE.

    MUST BE CAUGHT BY: test_a_dark_letter_is_reported_dark_with_a_reason
    """
    def mutated_letter(letter, name, role, home):
        def deco(fn):
            def run():
                t0 = __import__("time").time()
                try:
                    measured = fn()
                except Exception:
                    # THE DEFECT: a failing letter reads as a passing one.
                    return fc_app.Letter(letter, name, role, "LIVE", {},
                                         "", home, 0.0)
                state = "LIVE"
                reason = ""
                if isinstance(measured, fc_app.Stub):
                    state = "STUB"
                    reason = measured.why
                    measured = measured.measure()
                return fc_app.Letter(letter, name, role, state, measured,
                                     reason, home,
                                     (__import__("time").time() - t0) * 1000)
            run.__name__ = "letter_%s" % letter.lower()
            return run
        return deco

    original = fc_app._letter
    try:
        fc_app._letter = mutated_letter
        caught = _run_one("test_a_dark_letter_is_reported_dark_with_a_reason")
        assert caught, (
            "a failing letter reading as LIVE was NOT caught")
    finally:
        fc_app._letter = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_4_the_stub_reads_as_live():
    """MUTATION: the decorator treats a Stub as a plain measurement, so a
    stubbed letter reads as LIVE.

    MUST BE CAUGHT BY: test_a_stub_is_reported_as_a_stub_and_not_as_live
    """
    def mutated_letter(letter, name, role, home):
        def deco(fn):
            def run():
                t0 = __import__("time").time()
                try:
                    measured = fn()
                except Exception as exc:
                    return fc_app.Letter(letter, name, role, "DARK", {},
                                         "%s: %s" % (type(exc).__name__, exc),
                                         home, 0.0)
                # THE DEFECT: no Stub check at all.
                return fc_app.Letter(letter, name, role, "LIVE", measured,
                                     "", home,
                                     (__import__("time").time() - t0) * 1000)
            run.__name__ = "letter_%s" % letter.lower()
            return run
        return deco

    original = fc_app._letter
    try:
        fc_app._letter = mutated_letter
        caught = _run_one("test_a_stub_is_reported_as_a_stub_and_not_as_live")
        assert caught, "a stub reading as LIVE was NOT caught"
    finally:
        fc_app._letter = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_5_the_reflex_reads_the_request_instead_of_the_question():
    """MUTATION: the reflex selects on the composed request, so it
    matches its own scaffolding and answers the ground's claims to an
    off-ground question.

    MUST BE CAUGHT BY:
    test_the_reflex_answers_from_the_ground_and_refuses_off_ground
    """
    from minimax_client import LocalMiniLLMClient

    original = LocalMiniLLMClient._relevant_claims

    def mutated(self, prompt):
        # THE DEFECT: select against the composed request, which carries
        # the locus and its word "ground".
        return original(self, prompt)

    original_generate = LocalMiniLLMClient.generate

    def mutated_generate(self, prompt, **kwargs):
        # THE DEFECT: the question is IGNORED. Not just the kwarg --
        # the field too. The reflex falls back to `self.question` when
        # the kwarg is absent, so popping the kwarg alone changed
        # nothing.
        #
        # MEASURED 2026-11-04: the first version of this mutation
        # popped the kwarg and the test stayed GREEN -- the mutation
        # did not take effect, because the client's `question` FIELD
        # still held the real question and the fallback used it. A
        # mutation that does not take effect is not a mutation.
        #
        # So the field is cleared as well, and the selection falls back
        # to the composed request, which carries the locus and its word
        # "ground".
        self.question = ""
        kwargs.pop("question", None)
        return original_generate(self, prompt, **kwargs)

    original_question = fc_hermes.Bridge.ask
    try:
        LocalMiniLLMClient.generate = mutated_generate
        caught = _run_one(
            "test_the_reflex_answers_from_the_ground_and_refuses_off_ground")
        assert caught, (
            "the reflex reading the request instead of the question was "
            "NOT caught")
    finally:
        LocalMiniLLMClient.generate = original_generate
        LocalMiniLLMClient._relevant_claims = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_6_the_gate_bounds_become_caller_controlled():
    """MUTATION: `gate()` grows a parameter with a default, so a caller
    can widen the limit.

    MUST BE CAUGHT BY:
    test_the_gate_bounds_are_module_constants_and_not_caller_controlled
    """
    import inspect
    import numpy as np
    import gate as fc_gate

    original = fc_gate.gate

    def mutated(emb, psi0, max_norm=100.0):
        ne = float(np.linalg.norm(emb))
        n0 = float(np.linalg.norm(psi0))
        if ne > max_norm:
            return False, "norm"
        if float(np.dot(emb, psi0) / (ne * n0)) < fc_gate.MIN_COS:
            return False, "cos"
        return True, "allow"

    try:
        fc_gate.gate = mutated
        caught = _run_one(
            "test_the_gate_bounds_are_module_constants_and_not_caller_controlled")
        assert caught, (
            "a caller-controlled gate bound was NOT caught")
    finally:
        fc_gate.gate = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_7_the_describe_nesting_comes_back():
    """MUTATION: the bridge nests the wrapper's whole report under
    "instruments" again, so `d["instruments"]["gate"]` does not exist.

    MUST BE CAUGHT BY: test_the_bridge_describes_every_instrument
    """
    original = fc_hermes.Bridge.describe

    def mutated(self):
        import fc_app
        letters = fc_app.survey()
        return {
            "live": self.live,
            "spend_guard": "open" if self.live else "closed",
            "instruments": self._wrapper.describe(),   # <-- THE DEFECT
            "letters": {
                "live": sum(1 for l in letters if l.state == "LIVE"),
                "stub": sum(1 for l in letters if l.state == "STUB"),
                "dark": sum(1 for l in letters if l.state == "DARK"),
                "states": {l.letter: l.state for l in letters},
            },
        }

    try:
        fc_hermes.Bridge.describe = mutated
        caught = _run_one("test_the_bridge_describes_every_instrument")
        assert caught, "the nesting was NOT caught"
    finally:
        fc_hermes.Bridge.describe = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


def test_mutation_8_the_survey_stops_being_idempotent():
    """MUTATION: the survey's state depends on run order -- the second
    run differs from the first.

    MUST BE CAUGHT BY: test_the_survey_is_idempotent
    """
    original = fc_app.survey
    state = {"n": 0}

    def mutated():
        state["n"] += 1
        out = original()
        if state["n"] > 1:
            # THE DEFECT: the second run reports something different.
            for lt in out:
                if lt.letter == "M":
                    lt.state = "LIVE"
        return out

    try:
        fc_app.survey = mutated
        caught = _run_one("test_the_survey_is_idempotent")
        assert caught, "a survey that changes between runs was NOT caught"
    finally:
        fc_app.survey = original
        import importlib
        import test_fc_app
        importlib.reload(test_fc_app)


# ---------------------------------------------------------------------------
# THE COUNT
# ---------------------------------------------------------------------------

def test_every_mutation_in_this_file_is_caught():
    """The file's own claim: all eight mutations are caught.

    RED: if any mutation below stopped being caught, this fails -- and
    the failure names which one.
    """
    checks = [
        (test_mutation_1_the_survey_mutates_the_live_boundary_again,),
        (test_mutation_2_the_bridge_drops_the_ok_bit_again,),
        (test_mutation_3_the_survey_stops_reporting_a_dark_letter,),
        (test_mutation_4_the_stub_reads_as_live,),
        (test_mutation_5_the_reflex_reads_the_request_instead_of_the_question,),
        (test_mutation_6_the_gate_bounds_become_caller_controlled,),
        (test_mutation_7_the_describe_nesting_comes_back,),
        (test_mutation_8_the_survey_stops_being_idempotent,),
    ]
    failed = []
    for (fn,) in checks:
        try:
            fn()
        except AssertionError as exc:
            failed.append("%s: %s" % (fn.__name__, exc))
    assert not failed, "mutations not caught:\n%s" % "\n".join(failed)
