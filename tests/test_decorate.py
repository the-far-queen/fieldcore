"""
test_decorate.py — TC39 decorators pattern (wycats javascript-decorators) tests.

the pattern: declarative decorators attach metadata to objects.
load-bearing for simself's @sacred_axis / @resilient_axis / @gate / @witness.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from decorate import (  # noqa: E402
    SACRED, RESILIENT, sacred_axis, resilient_axis, gate, witness, registry,
)


def test_d1_sacred_decorator():
    @sacred_axis("test-sacred")
    class Thing: pass
    assert Thing._axis_tier == SACRED
    assert Thing._axis_name == "test-sacred"
    print("D1: ok (sacred)")


def test_d2_resilient_decorator():
    @resilient_axis("test-resilient")
    class Thing: pass
    assert Thing._axis_tier == RESILIENT
    print("D2: ok (resilient)")


def test_d3_gate_decorator_attaches_metadata():
    @gate
    def f():
        return "x"
    assert f._is_gated is True
    result = f()
    assert result == "x"
    assert f._gate_reason == "ok"
    print("D3: ok (gate)")


def test_d4_witness_decorator():
    @witness("the assertion that holds the system")
    class A: pass
    assert A._witness == "the assertion that holds the system"
    print("D4: ok (witness)")


def test_d5_registry_picks_up_decorated_classes():
    """registry() walks nested classes and finds _axis_tier metadata."""
    reg = registry()
    names = {a["name"] for a in reg}
    tiers = {a["name"]: a["tier"] for a in reg}
    # the ConstitutionalAxes has 3 decorated inner classes: Boundaries, Coherence, Routing
    assert "boundaries" in names
    assert "coherence" in names
    assert "routing" in names
    # and the tiers are right
    assert tiers["boundaries"] == SACRED
    assert tiers["coherence"] == SACRED
    assert tiers["routing"] == RESILIENT
    print(f"D5: ok (registry: {len(reg)} axes, tiers={set(tiers.values())})")


def test_d6_registry_includes_witness():
    """the witness text is preserved on the registry entries."""
    reg = registry()
    witnesses = {a["name"]: a["witness"] for a in reg}
    assert "irreducible" in witnesses["boundaries"] or "irreducible" in witnesses["boundaries"].lower()
    assert "cosine" in witnesses["coherence"].lower() or "ground" in witnesses["coherence"].lower()
    print(f"D6: ok (witnesses preserved)")


def main():
    test_d1_sacred_decorator()
    test_d2_resilient_decorator()
    test_d3_gate_decorator_attaches_metadata()
    test_d4_witness_decorator()
    test_d5_registry_picks_up_decorated_classes()
    test_d6_registry_includes_witness()
    print("\\nALL DECORATE TESTS PASS (D1..D6)")


if __name__ == "__main__":
    main()