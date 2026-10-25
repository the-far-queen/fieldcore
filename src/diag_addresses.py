"""
diag_addresses.py -- IS THE BENCH'S COLLAPSE PHYSICS OR MY OWN POPULATION?

Central rule 4: a surprising result means suspect the code first.

The bench showed the name rate collapsing as the population grows
(50% at pop 4, 17-25% above, 0% at 64). Before that is reported as a
physical limit, the population generator has to be checked: are the
stalk addresses actually DISTINCT?

`make_population` varies the geometry by `i % 7`, `i % 11`, `i % 13`,
`i % 6`, `i % 9`. Those moduli repeat, so past a certain count the
generator can produce two stalks with the SAME geometry and therefore
the SAME address -- and an address collision makes the naming task
IMPOSSIBLE, no matter how good the channel is.

That is a limit of the bench, not of the design, and the two look
identical from the output.

This measures: the number of DISTINCT addresses per population, and
how many stalks collide with the speaker's own address.

Run:
    python src/diag_addresses.py
"""
from __future__ import annotations

import os
import sys

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from bench_balance_point import make_population, address_of  # noqa: E402


def main() -> int:
    print("=" * 78)
    print("ARE THE ADDRESSES DISTINCT? (the bench's own confound)")
    print("=" * 78)
    print()
    print("  %-6s %-12s %-14s %-16s %-14s" % (
        "pop", "distinct addrs", "max collision", "worst dup count",
        "speaker's dups"))
    print("  " + "-" * 66)
    for pop in (2, 4, 8, 16, 32, 64, 128):
        stalks = make_population(pop)
        addrs = [address_of(s) for s in stalks]
        counts = {}
        for a in addrs:
            counts[a] = counts.get(a, 0) + 1
        distinct = len(counts)
        worst = max(counts.values())
        # for each speaker, how many stalks share its address
        dup_counts = [counts[a] for a in addrs]
        print("  %-6d %-12d %-14d %-16d %-14d" % (
            pop, distinct, worst, worst,
            max(dup_counts)))
    print()
    print("  a 'speaker's dups' above 1 means the speaker's address is")
    print("  shared with other stalks, so naming it correctly is not a")
    print("  matter of channel quality -- it is impossible by")
    print("  construction.")
    print()

    # the address formula, so the collision is visible
    print("=" * 78)
    print("THE ADDRESSES, FOR POP 16")
    print("=" * 78)
    print()
    stalks = make_population(16)
    for s in stalks:
        print("  %-8s n_out=%-3d girth_ratio=%.6f  address=%.6f" % (
            s.id, s.n_out, s.girth_ratio, address_of(s)))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
