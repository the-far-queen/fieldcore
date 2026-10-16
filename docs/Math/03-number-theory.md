# 03 — Number theory (Layer A verified, Layer C refuted-in-place)

All figures below come from `python -m pytest tests/ -q` and
`farmath.number_theory`. Re-run them; do not quote from this table without
re-running.

## Layer A — holds

### Twin primes

Sieve to 200,000: **2,160 pairs**, 2,159 above (3,5).

| claim | measured | verdict |
|---|---|---|
| every twin-prime sum above (3,5) is divisible by 12 | 0 failures in 2,159 pairs | holds |
| twin-prime products above (3,5) are ≡ 11 (mod 12) | the only residue seen is 11 | holds |

Why: `p > 3` is `6k − 1`, so the sum `2p + 2 = 12k`, and the product
`p(p+2) ≡ 11 (mod 12)`.

**These are proven theorems.** They do **not** justify the axis
cardinality in `constitution.py`. That connection was never made and is
not made here.

### Seifert genus (torus knots)

`g = (p−1)(q−1)/2`, exact for coprime p, q:

| knot | genus |
|---|---|
| T(29,31) | 420 |
| T(41,43) | 840 |

The module refuses non-coprime arguments with a `ValueError` — T(6,9) is a
link, not a knot, and the formula does not apply. That is a knot
invariant; it is unrelated to the Heegaard genus of the surrounding
3-manifold.

### The arctan identity

```
arctan(1/√φ) + arctan(√φ) = π/2
```

Measured absolute error: **0.0**. A reciprocal pair of positive arguments
sums to π/2, so this is a cheap identity — worth stating plainly rather
than dressing up. A control pair with no golden-ratio content (7 and 1/7)
also lands at π/2 with error 0.0, which is what a real identity does.

## Layer C — preserved, one refuted by its own arithmetic

### Twin-prime-sum cascade around φ — **not supported**

Bobby's claim: successive twin-prime sums form a quasi-φ cascade, ratios
oscillating around φ.

Measured to 200,000, over 2,158 consecutive ratios:

| quantity | measured |
|---|---|
| mean ratio | **1.0053** |
| φ | 1.6180 |
| mean abs log error vs φ | 0.4766 |
| min / max ratio | 1.00003 / 2.0 |

The ratios concentrate near **1**, not near φ. The reason is mundane:
consecutive twin-prime sums are close in magnitude, so the ratio sequence
tracks 1 regardless of any golden-ratio structure. The verdict is in
code as `twin_prime_sum_cascade_verdict()`.

**The claim is not deleted.** Per Bobby's standing directive, unfounded is
speculative rather than grounds for removal. It is preserved, marked, and
carries its own refutation.

### α as fractal intersection offset — **measurement, not verdict**

Bobby's claim (per `Desktop/Geometry/constant.txt`): α⁻¹ = 137.036 is the
fractal intersection offset between the prime and Fibonacci fractals near
the prime 137.

| quantity | measured |
|---|---|
| α⁻¹ (CODATA 2018) | 137.035999084 |
| nearest prime | 137 |
| nearest Fibonacci below / above | 89 / 144 |
| distance to nearest prime | 0.0263 % |
| 137 / 89 | 1.53933 |
| φ | 1.61803 |
| **137/89 vs φ** | **4.86 % low** |

**Correction, 2026-10-09.** The original document compared 137/89 = 1.5393
against "φ²/1.618 = 1.528" and called the two close. But φ²/1.618 *is* φ
= 1.6180. The comparison cancelled itself. Measured honestly, 1.5393 is
**4.86 % below** φ — the opposite direction from what the framing implied,
and much further away than "close".

Two other arithmetic facts worth keeping, since they are what the claim
would have to explain: 137 sits in the twin pair (131, 137), and 144/89 =
1.61798 — within 3e-5 of φ. That Fibonacci near-miss is closer to φ than
137/89 is, which is the fact the original framing did not use.

Whether α *is* that offset is not decidable by arithmetic here, and this
repo does not claim it.

## What would falsify what

| claim | falsifier |
|---|---|
| twin-prime cascade ≈ φ | already falsified to 200,000; extends if it fails at 10⁷ |
| α as prime/Fibonacci offset | a derivation of α⁻¹ from the offset arithmetic to better than 0.1 % — or a measured offset that misses 137 by more than the quoted error |
| the layer rule itself | a Layer C claim surviving promotion to A without a check that can go red |

## Terms used here

Defined here so this document can be read cold. The full glossary is
`GLOSSARY.md`.


- **twin primes** - two primes differing by 2, such as 11 and 13
- **Seifert genus** - the least number of handles on a surface bounding a given knot
- **manifold** - a space that locally looks like ordinary Euclidean space
