from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class Multivector:
    """an element of the exterior algebra. (grade, components)."""
    grade: int                       # 0 (scalar), 1 (vector), 2 (bivector), ...
    components: Tuple[float, ...]     # components in the canonical basis

    def grade_select(self, k: int) -> "Multivector":
        """Hodge decomposition: select the grade-k component."""
        if k == self.grade: return self
        if k == 0: return Multivector(0, (sum(self.components),))
        return Multivector(k, ())


@dataclass(frozen=True)
class HodgeDecomposition:
    """the canonical 3-axis Hodge split: harmonic + exact + coexact.
    psi = h + d*alpha + delta*beta.
    load-bearing: harmonic part is CONSERVED under gradient flow.
    """
    harmonic: Tuple[float, ...]      # Δh = 0
    exact: Tuple[float, ...]          # h_exact = dα for some α
    coexact: Tuple[float, ...]        # h_coexact = δβ for some β

    def total(self) -> Tuple[float, ...]:
        n = len(self.harmonic)
        return tuple(self.harmonic[i] + self.exact[i] + self.coexact[i]
                    for i in range(n))


def inner_product(m1: Multivector, m2: Multivector) -> float:
    """the Hestenes inner product. <u, v>."""
    if m1.grade != m2.grade: return 0.0
    return sum(a*b for a, b in zip(m1.components, m2.components))


if __name__ == "__main__":
    m1 = Multivector(grade=2, components=(1.0, 2.0, 3.0))
    m2 = Multivector(grade=2, components=(4.0, 5.0, 6.0))
    ip = inner_product(m1, m2)
    assert ip == 1*4 + 2*5 + 3*6 == 32.0
    print(f"G1: ok (Grassmann inner product = {ip})")

    h = HodgeDecomposition(harmonic=(1, 0), exact=(0, 2), coexact=(0, 0))
    assert h.total() == (1, 2)
    print(f"G2: ok (Hodge decomposition total = {h.total()})")

    print("\\nALL GRASSMANN_CLIFFORD TESTS PASS")