"""
test_claim_register_mutations.py -- the mutants, and the harness.

WHY THIS IS A SEPARATE FILE. The mutation harness runs pytest against
a file. If that file CONTAINED the mutation tests, the child pytest
would run the mutation tests, which run pytest again, on the same file,
with no depth limit. The suite does not fail -- it recurses until the
machine is saturated, printing nothing, which is why it looks like a
hang. The project hit this on 2026-10-24 and wrote it down; it was hit
again on 2026-10-25 by the same mistake, and the fix is the same: the
harness runs test_claim_register.py, which holds behaviour assertions
and no mutation tests.

THE OTHER HALF OF THE RULE, from the same defect: the mutant must
actually BE the module under test. The child process gets the mutated
copy FIRST on PYTHONPATH, and the behaviour file does not insert src/
into sys.path ahead of it -- so the child imports the MUTANT. A green
mutation test proves nothing if the mutant was never loaded.

EVERY SUBPROCESS HAS A TIMEOUT. A checker that can hang can wedge the
machine, and the machine is not ours to wedge.

Run:
    python -m pytest tests/test_claim_register_mutations.py -q
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

#: The behaviour file. It holds NO mutation tests, so the child pytest
#: has nothing to recurse into.
BEHAVIOUR = pathlib.Path(__file__).resolve().parent / "test_claim_register.py"

MUTATION_TIMEOUT = 180


def _mutated_dir(tmp_path, old, new):
    """A directory holding a mutated claim_register.py."""
    text = (SRC / "claim_register.py").read_text(encoding="utf-8")
    assert old in text, "mutation anchor missing: %r" % (old,)
    d = tmp_path / ("mut_" + re.sub(r"\W+", "_", old)[:24])
    d.mkdir(exist_ok=True)
    (d / "claim_register.py").write_text(text.replace(old, new, 1),
                                         encoding="utf-8")
    return d


def _run_behaviour(pythonpath_dir):
    """Run the behaviour file against whatever is first on PYTHONPATH."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath_dir)
    out = subprocess.run(
        [sys.executable, "-m", "pytest", str(BEHAVIOUR),
         "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=str(ROOT), env=env,
        timeout=MUTATION_TIMEOUT)
    return out.returncode != 0, out.stdout[-900:]


def test_the_unmutated_instrument_is_green():
    """The control for every mutation below.

    Without it, 'the suite went red' could just mean 'the behaviour
    file is broken'.
    """
    red, tail = _run_behaviour(SRC)
    assert not red, f"the unmutated instrument is not green:\n{tail}"


def test_mutation_removing_the_clause_break_goes_red(tmp_path):
    """Disarm the clause break, and a negator scopes across sentences.

    THE SCOPE RULE IN FORCE is clause-based: a negator scopes over the
    proposition it attaches to, and a proposition is a clause. So the
    clause break IS the rule, and removing it is the attack.

    (The earlier version of this test mutated a token window that the
    clause rule replaced, so the mutant no longer touched the logic
    that decides. A mutant that does not reach the decision is not a
    mutant -- it is decoration, and it would have passed as a green
    test.)
    """
    d = _mutated_dir(
        tmp_path,
        "    for brk in CLAUSE_BREAKS:\n"
        "        idx = head.rfind(brk)\n"
        "        if idx >= 0:\n"
        "            head = head[idx + len(brk):]\n"
        "            break",
        "    pass")
    red, tail = _run_behaviour(d)
    assert red, f"removing the clause break left the suite green:\n{tail}"


def test_mutation_narrowing_the_negation_window_goes_red(tmp_path):
    """The window was MEASURED at 5. Going back to the guessed 4 breaks
    the truth that puts its negator 5 tokens back."""
    d = _mutated_dir(
        tmp_path,
        "NEGATION_WINDOW = 5",
        "NEGATION_WINDOW = 4")
    red, tail = _run_behaviour(d)
    assert red, f"narrowing the negation window left the suite green:\n{tail}"


def test_mutation_removing_the_word_boundaries_goes_red(tmp_path):
    """Drop the word boundaries, and 'no' fires inside 'notebook'."""
    d = _mutated_dir(
        tmp_path,
        '    return re.compile(r"(?<![A-Za-z0-9])" + r"\\s+".join(parts)\n'
        '                      + r"(?![A-Za-z0-9])", re.IGNORECASE)',
        '    return re.compile(r"\\s+".join(parts), re.IGNORECASE)')
    red, tail = _run_behaviour(d)
    assert red, f"removing the word boundaries left the suite green:\n{tail}"


def test_mutation_removing_the_clause_break_goes_red(tmp_path):
    """Ignore the clause break, and a negator scopes across sentences."""
    d = _mutated_dir(
        tmp_path,
        "    for brk in CLAUSE_BREAKS:\n"
        "        idx = head.rfind(brk)\n"
        "        if idx >= 0:\n"
        "            head = head[idx + len(brk):]\n"
        "            break",
        "    pass")
    red, tail = _run_behaviour(d)
    assert red, f"removing the clause break left the suite green:\n{tail}"


def test_mutation_making_a_denial_always_live_goes_red(tmp_path):
    """Ignore the negation scope when deciding a denial is live."""
    d = _mutated_dir(
        tmp_path,
        "            live_denies = [(s, i) for (s, i) in deny_hits\n"
        "                            if not _negator_scopes_over(low, i)]",
        "            live_denies = list(deny_hits)")
    red, tail = _run_behaviour(d)
    assert red, f"always-live denials left the suite green:\n{tail}"


def test_mutation_making_a_denial_always_dead_goes_red(tmp_path):
    """The other direction: cancel every denial, so no lie is caught."""
    d = _mutated_dir(
        tmp_path,
        "            live_denies = [(s, i) for (s, i) in deny_hits\n"
        "                            if not _negator_scopes_over(low, i)]",
        "            live_denies = []")
    red, tail = _run_behaviour(d)
    assert red, f"always-dead denials left the suite green:\n{tail}"


def test_mutation_always_reporting_evidence_goes_red(tmp_path):
    """Report a claim with no evidence as measured."""
    d = _mutated_dir(
        tmp_path,
        "    def has(self, evidence_id: Optional[str]) -> bool:\n"
        "        return bool(evidence_id) and evidence_id in self.items",
        "    def has(self, evidence_id: Optional[str]) -> bool:\n"
        "        return True")
    red, tail = _run_behaviour(d)
    assert red, f"always-measured evidence left the suite green:\n{tail}"


def test_mutation_never_reporting_evidence_goes_red(tmp_path):
    """The other direction: nothing is ever measured, so the evidence
    layer is decoration."""
    d = _mutated_dir(
        tmp_path,
        "    def has(self, evidence_id: Optional[str]) -> bool:\n"
        "        return bool(evidence_id) and evidence_id in self.items",
        "    def has(self, evidence_id: Optional[str]) -> bool:\n"
        "        return False")
    red, tail = _run_behaviour(d)
    assert red, f"never-measured evidence left the suite green:\n{tail}"


def test_mutation_making_the_register_unsealed_goes_red(tmp_path):
    """The ground must be write-protected. Without the seal, an
    adversary can add a claim and the gate stops objecting."""
    d = _mutated_dir(
        tmp_path,
        "        if self._sealed:\n"
        "            raise ValueError(\n"
        "                \"the claim register is sealed: the ground cannot be \"\n"
        "                \"edited by a caller. Use revise(), which takes a reason \"\n"
        "                \"and records it.\")",
        "        pass")
    red, tail = _run_behaviour(d)
    assert red, f"an unsealed register left the suite green:\n{tail}"


def test_mutation_removing_the_singular_anchor_goes_red(tmp_path):
    """The claim must be reachable by the SINGULAR of its subject.

    THE HOLE. src/adversary_probe.py writes 49 phrasings of one denial
    and the span was not ABOUT the claim because the anchor missed, so
    the agenda layer never fired. 35 of 49 adversarial phrasings were
    missed by this one hole.

    (The earlier version of this mutant removed the optional plural
    from the matcher -- but the anchor list also carries the explicit
    singular, so the mutant left the logic intact and the suite stayed
    green. The mutation has to remove the ANCHOR, because the anchor
    is what the measurement found missing.)
    """
    d = _mutated_dir(
        tmp_path,
        "        if last.endswith(\"s\") and not last.endswith(\"ss\"):\n"
        "            last = last[:-1]\n"
        "        plural = last + r\"s?\"",
        "        plural = last")
    red, tail = _run_behaviour(d)
    assert red, f"removing the singular anchor left the suite green:\n{tail}"


def test_mutation_dropping_the_agenda_layer_goes_red(tmp_path):
    """The agenda layer is what catches a permission the deny lexicon
    cannot see."""
    d = _mutated_dir(
        tmp_path,
        "        agenda_reading = detect_agenda(span, self.claims)",
        "        agenda_reading = AgendaReading(agenda=Agenda.NONE)")
    red, tail = _run_behaviour(d)
    assert red, f"dropping the agenda layer left the suite green:\n{tail}"


def test_mutation_ignoring_the_trailing_negator_goes_red(tmp_path):
    """'the caller may not supply the limits' is a refusal, not a
    permission."""
    d = _mutated_dir(
        tmp_path,
        "        if _negator_follows(low, m.end()):\n"
        "            continue",
        "        pass")
    red, tail = _run_behaviour(d)
    assert red, f"ignoring the trailing negator left the suite green:\n{tail}"


def test_mutation_dropping_the_contradiction_check_goes_red(tmp_path):
    """Never report a contradiction, so every lie is admitted."""
    d = _mutated_dir(
        tmp_path,
        "        contradictions = [r for r in readings\n"
        "                          if r.polarity is Polarity.CONTRADICTS]",
        "        contradictions = []")
    red, tail = _run_behaviour(d)
    assert red, f"dropping the contradiction check left the suite green:\n{tail}"
