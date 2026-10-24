"""
test_gate_contract.py — the gate's behaviour, stated as assertions.

This file exists because of a defect in test_one_gate.py found on
2026-10-24.

WHAT WAS WRONG. The mutation tests in test_one_gate.py checked that a
permissive gate makes the suite go red. To do that they ran pytest on
**their own file** (`str(pathlib.Path(__file__))`). That file contains
the mutation tests. So the child pytest ran the mutation tests, which
ran pytest again, on the same file, with no depth limit. The suite did
not fail -- it recursed until the machine was saturated. It printed
nothing, which is why it looked like a hang rather than a failure.

The second defect was quieter. The mutation was supposed to shadow the
real gate by putting the mutated copy first on PYTHONPATH. But
test_one_gate.py does `sys.path.insert(0, str(SRC))` at import time,
and a `sys.path.insert(0, ...)` at import time lands in front of
PYTHONPATH. So the child imported the REAL gate, the mutation was
never applied, and the "the suite went red" assertion could only have
passed for some other reason. A green mutation test proves nothing if
the mutant was never loaded.

THE FIX, and why it is shaped this way. The mutation tests now run THIS
file against the mutant -- a file that contains behaviour assertions
and no mutation tests, so there is nothing to recurse into. And this
file does not insert SRC into sys.path: it imports `gate` from wherever
PYTHONPATH points, which is how the mutant is allowed to shadow it.

Two things are asserted per mutation, because one is not enough:
  - the mutant makes the suite RED
  - the unmutated gate makes the suite GREEN
Without the second, "red" could mean "this file is broken" rather than
"the mutation was caught".

Every subprocess call has a timeout. A checker that can hang is a
checker that can wedge a machine, and the machine is not ours to wedge.
"""

from __future__ import annotations

import numpy as np

# NOTE: deliberately NOT inserting src/ into sys.path here. This file is
# run against a mutated copy of gate.py via PYTHONPATH, and a local
# sys.path.insert(0, ...) would shadow the mutant and make every
# mutation test vacuous. The unmutated run passes PYTHONPATH=<repo>/src.

PSI0 = np.zeros(8)
PSI0[0] = 1.0

GOOD = PSI0.copy()                     # cos = 1.0  -> allow
ORTHOGONAL = PSI0.copy()
ORTHOGONAL[0] = 0.0
ORTHOGONAL[1] = 1.0                    # cos = 0.0  -> refuse_coherence
OVERSIZE = PSI0.copy() * 100.0         # norm = 100 -> refuse_norm
ZERO = np.zeros(8)                     # norm = 0    -> refuse_zero
NOT_FINITE = np.full(8, np.nan)        # -> refuse_nonfinite


def test_good_packet_is_allowed():
    import gate as G
    allow, reason = G.gate(GOOD, PSI0)
    assert allow, reason
    assert reason == G.ALLOW


def test_oversize_is_refused():
    """Catches a widened MAX_NORM and a permissive norm branch."""
    import gate as G
    allow, reason = G.gate(OVERSIZE, PSI0)
    assert not allow, "an oversized packet was admitted"
    assert reason == G.REFUSE_NORM, reason


def test_orthogonal_is_refused():
    """Catches a lowered MIN_COS."""
    import gate as G
    allow, reason = G.gate(ORTHOGONAL, PSI0)
    assert not allow, "a packet orthogonal to ground was admitted"
    assert reason == G.REFUSE_COHERENCE, reason


def test_zero_is_refused():
    import gate as G
    allow, reason = G.gate(ZERO, PSI0)
    assert not allow, "a zero packet was admitted"
    assert reason == G.REFUSE_ZERO, reason


def test_non_finite_is_refused():
    """NaN fails every comparison, so a naive `ne > MAX_NORM` admits it."""
    import gate as G
    allow, reason = G.gate(NOT_FINITE, PSI0)
    assert not allow, "a NaN packet was admitted"
    assert reason == G.REFUSE_NONFINITE, reason


def test_gated_does_not_run_a_refused_operation():
    import gate as G
    calls = []
    allow, reason, result = G.gated(OVERSIZE, PSI0, lambda: calls.append(1))
    assert not allow
    assert calls == [], "the operation ran despite the refusal"
    assert result is None
