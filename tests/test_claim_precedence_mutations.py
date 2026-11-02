"""
test_claim_precedence_mutations.py -- the mutants, and the harness.

WHY THIS IS A SEPARATE FILE. The mutation harness runs pytest against
a file. If that file CONTAINED the mutation tests, the child pytest
would run the mutation tests, which run pytest again, on the same file,
with no depth limit. The suite does not fail -- it recurses until the
machine is saturated. It prints nothing, which is why it looks like a
hang. The project hit this on 2026-10-24 and wrote it down; it was hit
again on 2026-10-25 by the same mistake, and the fix is the same: the
harness runs test_claim_precedence.py, which holds behaviour assertions
and no mutation tests.

THE OTHER HALF OF THE RULE, from the same defect: the mutant must
actually BE the module under test. The child process gets the mutated
copy FIRST on PYTHONPATH, and the behaviour file does not insert src/
into sys.path ahead of it -- so the child imports the MUTANT. A green
mutation test proves nothing if the mutant was never loaded.

EVERY SUBPROCESS HAS A TIMEOUT. A checker that can hang can wedge the
machine, and the machine is not ours to wedge.

THE MUTANTS, and the defect each one attacks:

  1  the nearest clause boundary is replaced by the first break TYPE
     -- the ORIGINAL defect, and the laundering hole
  2  the nearest clause boundary is removed entirely
  3  the affirm precedence is removed -- the deny always wins
  4  the affirm precedence becomes BLANKET -- the laundering hole
  5  the goal-2 claim's anchors are reverted to the blunt list
  6  the goal-2 claim's deny list is reverted to the blunt wording

Run:
    python -m pytest tests/test_claim_precedence_mutations.py -q
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
BEHAVIOUR = pathlib.Path(__file__).resolve().parent / "test_claim_precedence.py"

MUTATION_TIMEOUT = 180


def _mutated_dir(tmp_path, old, new, name):
    """A directory holding a mutated claim_register.py."""
    text = (SRC / "claim_register.py").read_text(encoding="utf-8")
    assert old in text, "mutation anchor missing: %r" % (old,)
    d = tmp_path / ("mut_" + re.sub(r"\W+", "_", name)[:28])
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


def test_mutation_the_far_clause_boundary_goes_red(tmp_path):
    """Go back to the FIRST break TYPE, and the laundering hole opens.

    THE ORIGINAL DEFECT. `CLAUSE_BREAKS` is ordered with "." first, so
    the old rule took the first break TYPE it found anywhere in the
    head -- and a "." 39 characters back beat the ";" immediately
    before the stem. So a negator in an earlier sentence scoped over a
    later clause, and the attack was admitted.
    """
    d = _mutated_dir(
        tmp_path,
        "    cut = _nearest_clause_break(head)\n"
        "    if cut is not None:\n"
        "        head = head[cut:]",
        "    for brk in CLAUSE_BREAKS:\n"
        "        idx = head.rfind(brk)\n"
        "        if idx >= 0:\n"
        "            head = head[idx + len(brk):]\n"
        "            break",
        "far_clause_boundary")
    red, tail = _run_behaviour(d)
    assert red, f"the far clause boundary left the suite green:\n{tail}"


def test_mutation_removing_the_clause_break_goes_red(tmp_path):
    """Remove the boundary entirely, and a negator scopes across
    sentences."""
    d = _mutated_dir(
        tmp_path,
        "    cut = _nearest_clause_break(head)\n"
        "    if cut is not None:\n"
        "        head = head[cut:]",
        "    pass",
        "no_clause_break")
    red, tail = _run_behaviour(d)
    assert red, f"removing the clause break left the suite green:\n{tail}"


#: The affirm-precedence block, as it stands. AND WHY IT IS A
#: CONSTANT: the block changed when the OVERLAP RULE was added (an
#: affirm inside the deny stem is part of the denial), and the
#: hand-copied anchors went stale -- so the mutants were never applied
#: and the assertion "the anchor is missing" fired instead of the
#: assertion "the suite went red".
#:
#: MEASURED 2026-11-02: two mutation tests failed with an anchor
#: error rather than with a red suite.
AFFIRM_PRECEDENCE = (
    "                if affirm_hits:\n"
    "                    # AND THE AFFIRM MUST LIE OUTSIDE THE DENY STEM.\n"
    "                    #\n"
    "                    # AND WHY. The deny stem \"not write protected\" and\n"
    "                    # the affirm stem \"write protected\" OVERLAP: in\n"
    "                    # \"the ground is not write protected\" the affirm\n"
    "                    # sits at 18 and the deny at 14, so the affirm is\n"
    "                    # INSIDE the deny stem. And an affirm that is part\n"
    "                    # of the denial is not an affirmation -- it is a\n"
    "                    # piece of the denial.\n"
    "                    #\n"
    "                    # MEASURED: without this rule the register read\n"
    "                    # \"the ground is not write protected\" as SUPPORTING\n"
    "                    # the ground, and \"the self does not exist\" as\n"
    "                    # supporting the existence claim. Both are denials,\n"
    "                    # and both were ADMITTED.\n"
    "                    same = [a for a in affirm_hits\n"
    "                            if _same_clause(low, a[1], live_denies[0][1])\n"
    "                            and not (live_denies[0][1] <= a[1]\n"
    "                                     < live_denies[0][1]\n"
    "                                     + len(live_denies[0][0]))]\n"
    "                    if same:\n"
    "                        pol = Polarity.SUPPORTS\n"
    "                        stem = same[0][0]"
)


def test_mutation_removing_the_affirm_precedence_goes_red(tmp_path):
    """Take the precedence away, and a same-clause affirm no longer
    beats a denial of it."""
    d = _mutated_dir(
        tmp_path,
        AFFIRM_PRECEDENCE,
        "                pass",
        "no_affirm_precedence")
    red, tail = _run_behaviour(d)
    assert red, f"removing the affirm precedence left the suite green:\n{tail}"


def test_mutation_making_the_affirm_precedence_blanket_goes_red(tmp_path):
    """Make the precedence BLANKET, and the laundering hole opens.

    The predicate layer's rule is blanket: any affirm in the span
    suppresses any denial. So an adversary launders an attack by
    praising the system first. MEASURED: the blanket rule missed 11
    of 22 laundered variants.
    """
    d = _mutated_dir(
        tmp_path,
        AFFIRM_PRECEDENCE,
        "                if affirm_hits:\n"
        "                    pol = Polarity.SUPPORTS\n"
        "                    stem = affirm_hits[0][0]",
        "blanket_affirm_precedence")
    red, tail = _run_behaviour(d)
    assert red, f"the blanket affirm precedence left the suite green:\n{tail}"


def test_mutation_dropping_the_overlap_rule_goes_red(tmp_path):
    """Let an affirm INSIDE the deny stem suppress it.

    The deny stem "not write protected" and the affirm stem "write
    protected" overlap. So without the overlap rule the register reads
    "the ground is not write protected" as SUPPORTING the ground --
    and "the self does not exist" as supporting the existence claim.
    Both are denials, and both were ADMITTED.
    """
    d = _mutated_dir(
        tmp_path,
        "                            and not (live_denies[0][1] <= a[1]\n"
        "                                     < live_denies[0][1]\n"
        "                                     + len(live_denies[0][0]))]",
        "                            ]",
        "no_overlap_rule")
    red, tail = _run_behaviour(d)
    assert red, f"dropping the overlap rule left the suite green:\n{tail}"


def test_mutation_reverting_the_goal_two_anchors_goes_red(tmp_path):
    """Put the blunt anchors back, and the deny stem fires on its own
    anchor.

    THE OLD ANCHORS were ("gate", "veto", "refuse"). "refuse" is an
    anchor, so every span containing the word "refuse" was "about"
    this claim -- and the deny stem "does not refuse" then fired on a
    span that merely NAMED the literal.

    MEASURED: the gate refused my own probe command for exactly this
    reason, and the probe's text was a Python call that mentioned the
    string 'does not refuse' and said nothing about the system.
    """
    d = _mutated_dir(
        tmp_path,
        "        anchors=(\"the gate\", \"the veto\", \"the sacred axes\",\n"
        "                 \"the reserved axes\", \"the axes\", \"the geometry\",\n"
        "                 \"a proposal\", \"the proposal\", \"the sacred geometry\"),",
        "        anchors=(\"gate\", \"veto\", \"refuse\"),",
        "blunt_goal_two_anchors")
    red, tail = _run_behaviour(d)
    assert red, f"the blunt goal-2 anchors left the suite green:\n{tail}"


def test_mutation_reverting_the_goal_two_deny_list_goes_red(tmp_path):
    """Put the blunt deny wording back, and the honest abstract
    argument is condemned.

    THE BLUNT WORDING was "admits every", and the matcher allows a
    bounded interior gap -- so "every" matched "everything" in the
    honest sentence "a gate that admits everything isn't learning".
    """
    d = _mutated_dir(
        tmp_path,
        "        deny=(\"waves through\", \"wave through\", \"sails through\",",
        "        deny=(\"admits every\", \"allows any\", \"allows every\",\n"
        "              \"waves through\", \"wave through\", \"sails through\",",
        "blunt_goal_two_deny")
    red, tail = _run_behaviour(d)
    assert red, f"the blunt goal-2 deny list left the suite green:\n{tail}"
