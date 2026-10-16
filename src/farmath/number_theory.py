"""Number-theory claims Bobby made, with the arithmetic that checks them.

Every function here returns a value that can be compared against an
independently stated expectation. If a function cannot disagree with its
own test, it is not a check (CENTRAL-RULES #7).

Layer: A (all of it) except `alpha_offset_report`, which is Layer C.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0


# ---------------------------------------------------------------- Layer A


def twin_primes(limit: int) -> list[tuple[int, int]]:
    """All twin-prime pairs (p, p+2) with p+2 <= limit, by sieve.

    Deterministic, no deps, exact. The engine for the Layer A twin-prime
    arithmetic below.
    """
    if limit < 5:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for n in range(2, math.isqrt(limit) + 1):
        if sieve[n]:
            sieve[n * n :: n] = bytearray(len(sieve[n * n :: n]))
    return [(p, p + 2) for p in range(3, limit - 1) if sieve[p] and sieve[p + 2]]


def twin_prime_sum_divisible_by_12(limit: int = 200_000) -> dict:
    """Claim: every twin-prime sum (p + p+2 = 2p+2) above (3,5) is a multiple of 12.

    Checked by exhaustive search to `limit`, and the failures are returned
    rather than swallowed. Reason it holds: p > 3 is 6k-1, so 2p+2 = 12k.
    """
    pairs = twin_primes(limit)
    considered = [(p, q) for p, q in pairs if p > 3]
    failures = [(p, q, p + q) for p, q in considered if (p + q) % 12 != 0]
    return {
        "pairs_total": len(pairs),
        "pairs_considered": len(considered),
        "limit": limit,
        "failures": failures,
        "holds": not failures,
    }


def twin_prime_product_mod_12(limit: int = 200_000) -> dict:
    """Claim: twin-prime products above (3,5) are 11 (mod 12).

    Reason: p ≡ 5 or 7 (mod 12) for p > 3, and p(p+2) ≡ 11 in both cases.
    """
    considered = [(p, q) for p, q in twin_primes(limit) if p > 3]
    residues = sorted({(p * q) % 12 for p, q in considered})
    return {
        "pairs_considered": len(considered),
        "residues_seen": residues,
        "claim_residue": 11,
        "holds": residues == [11],
    }


def seifert_genus_torus_knot(p: int, q: int, coprime: bool = True) -> int:
    """Seifert genus of the torus knot T(p, q): g = (p-1)(q-1) / 2.

    Exact for coprime p, q. This is the knot invariant used in Bobby's
    table; it is NOT the Heegaard genus of the surrounding 3-manifold
    (Math-Window1 §2.5, corrected 2026-09-16).
    """
    if coprime and math.gcd(p, q) != 1:
        raise ValueError(f"T({p},{q}) is a link, not a knot; genus formula differs")
    return ((p - 1) * (q - 1)) // 2


def arctan_golden_identity(tol: float = 1e-12) -> dict:
    """Claim: arctan(1/sqrt(phi)) + arctan(sqrt(phi)) = pi/2.

    Two arguments are reciprocals and both are positive, so the sum is
    pi/2 exactly. The check is that the floating-point sum lands inside
    `tol`, and that the identity also holds for a second, unrelated
    reciprocal pair (rule #5: two derivations must agree).
    """
    a = math.atan(1.0 / math.sqrt(GOLDEN))
    b = math.atan(math.sqrt(GOLDEN))
    # independent route: atan(u) + atan(1/u) = pi/2 for u > 0, checked on a
    # pair with no golden-ratio involvement at all.
    c = math.atan(7.0)
    d = math.atan(1.0 / 7.0)
    return {
        "golden_sum": a + b,
        "pi_over_2": math.pi / 2,
        "abs_error": abs((a + b) - math.pi / 2),
        "control_sum": c + d,
        "control_abs_error": abs((c + d) - math.pi / 2),
        "holds": abs((a + b) - math.pi / 2) < tol and abs((c + d) - math.pi / 2) < tol,
    }


def fibonacci_projection(n: int) -> list[int]:
    out, a, b = [], 0, 1
    while len(out) < n:
        out.append(a)
        a, b = b, a + b
    return out


def twin_prime_sum_ratio_cascade(limit: int = 200_000) -> dict:
    """Bobby's Layer C claim: successive twin-prime sums oscillate near phi.

    Reported as measured statistics, not as a verdict. `mean_abs_log_error`
    is |ln(ratio) - ln(phi)| averaged over consecutive pairs.
    """
    sums = [p + q for p, q in twin_primes(limit) if p > 3]
    ratios = [b / a for a, b in zip(sums, sums[1:]) if a > 0]
    if not ratios:
        return {"n": 0, "mean_ratio": None, "mean_abs_log_error": None}
    err = sum(abs(math.log(r) - math.log(GOLDEN)) for r in ratios) / len(ratios)
    return {
        "n": len(ratios),
        "mean_ratio": sum(ratios) / len(ratios),
        "golden": GOLDEN,
        "mean_abs_log_error": err,
        "max_ratio": max(ratios),
        "min_ratio": min(ratios),
    }


# ---------------------------------------------------------------- Layer C


@dataclass
class AlphaOffset:
    """The alpha-as-fractal-intersection-offset claim, measured.

    Layer C. Kept with reasoning + falsifiability per Bobby 2026-09-14-late
    ("treat unfounded as speculative not drop, all theorizing im often
    correct"). Nothing here is used by any runtime path.

    Correction, 2026-10-09: the original framing compared 137/89 = 1.5393
    against "phi^2/1.618 = 1.528" and called the two close. But
    phi^2/1.618 IS phi = 1.6180, so the honest comparison is
    1.5393 against 1.6180 -- a 4.86% miss, not agreement. The gap is
    reported here rather than smoothed over.
    """

    alpha_inverse: float
    nearest_prime: int
    nearest_fib_lo: int
    nearest_fib_hi: int
    prime_error_pct: float
    fib_ratio: float
    golden: float
    ratio_vs_golden: float
    pct_off_golden: float
    fib_bracketing_ratio: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def alpha_offset_report() -> AlphaOffset:
    """Measure the quantities the claim rests on. No narrative, no verdict.

    The claim (Bobby, per `Desktop/Geometry/constant.txt`) is that
    alpha^-1 = 137.036 is the offset of the prime/fibonacci fractal
    intersection near the prime 137. What arithmetic can settle is where
    137.036 sits relative to primes and Fibonacci numbers. Whether that
    offset *is* alpha is not decidable here and is not claimed.
    """
    alpha_inverse = 137.035999084  # CODATA 2018
    primes = twin_primes(400)
    flat = sorted({n for pair in primes for n in pair})
    nearest_prime = min(flat, key=lambda n: abs(n - alpha_inverse))
    fibs = fibonacci_projection(20)
    lo = max(f for f in fibs if f <= alpha_inverse)
    hi = min(f for f in fibs if f >= alpha_inverse)
    fib_ratio = nearest_prime / lo
    return AlphaOffset(
        alpha_inverse=alpha_inverse,
        nearest_prime=nearest_prime,
        nearest_fib_lo=lo,
        nearest_fib_hi=hi,
        prime_error_pct=abs(alpha_inverse - nearest_prime) / alpha_inverse * 100.0,
        fib_ratio=fib_ratio,
        golden=GOLDEN,
        ratio_vs_golden=fib_ratio / GOLDEN,
        pct_off_golden=abs(fib_ratio - GOLDEN) / GOLDEN * 100.0,
        fib_bracketing_ratio=hi / lo,
    )


def twin_prime_sum_cascade_verdict(limit: int = 200_000) -> dict:
    """Layer C: Bobby's twin-prime-sum cascade oscillates around phi.

    Measured to 200,000 the successive-sum ratios do NOT oscillate around
    phi -- they converge toward 1, because consecutive twin-prime sums are
    close in magnitude. This function states the measurement and the
    verdict separately so the claim is refuted without being deleted.
    """
    stats = twin_prime_sum_ratio_cascade(limit)
    measured = stats["mean_ratio"]
    return {
        **stats,
        "limit": limit,
        "verdict": "not supported at this limit",
        "verdict_reason": (
            f"mean successive-sum ratio is {measured:.4f}, not phi ({GOLDEN:.4f}); "
            "consecutive twin-prime sums are near in magnitude, so the ratio "
            "sequence concentrates near 1 regardless of any golden-ratio structure"
        ),
        "status": "preserved as refuted, per Bobby 2026-09-14-late (do not drop theorizing)",
    }
