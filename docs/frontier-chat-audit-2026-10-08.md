# Frontier-chat audit — 2026-10-08

Two AI chats (DeepSeek / Claude / Grok), relayed by Bobby, ~12,000 words of
FieldCore geometry-to-code, archived at
`vault/chat-transcripts/intake/2026-10-08/fieldcore-frontier-chat-*`.
Bobby's instruction: keep everything, dismiss nothing, he deletes his copies.

This note records what runs, what does not, and what the conversations
claimed that the code does not support. It is deliberately one-sided: it
reports failures, not the parts that worked, because the failures are the
ones that would otherwise ship.

---

## 1. The divergence (reproduced, fixed, regression-tested)

Six versions of the "FieldCore cell" across both chats used:

```python
grad = roll(x,-1) - x
curl = roll(x,-1) - 2x + roll(x,1)
harm = x - grad - curl          # <- not a harmonic form
```

Every version was described as holding a bounded state in a "constitutional
ground", with `harm` staying "nearly constant". Measured on the HP machine
in numpy:

| step | \|x\|max |
|---|---|
| 0 | 0.136 |
| 1 | 0.293 |
| 3 | 5.186 |
| 5 | 95.16 |
| 10 | 1.42e+05 |
| 30 | 1.06e+18 |
| 200 | 1.55e+444 (overflow) |

Cause: `harm = (4I − 2S − S⁻¹)x`, spectral radius **7.0** on the
alternating mode. With the operator's own weights (topo 0.82 on harm, alpha
0.618 on grad) the full update has ρ = **4.50** on that mode. ρ ≫ 1, so no
seed, step count, or coefficient choice can stabilise it.

Fix and full derivation: `src/hodge_cycle.py`. Tests: `tests/test_hodge_cycle.py`
(30 tests, including 4 mutation checks).

### The deeper error

A grad / coexact / harmonic split needs three orthogonal subspaces. On a bare
1-D cycle there are only two:

```
G^T G = 2I - S - S^T = L          (the circulant Laplacian)
eigenvalues of L: 4, 3.414, 3.414, 2, 2, 0.586, 0.586, 0
rank(L) = 7 of 8,  ker(L) = span{1}
```

`im(G^T) = im(L) = the entire zero-mean subspace`. Every zero-mean 1-form on
a cycle is exact, so there is **no separate coexact direction**. The code's
`curl` was not a coexact part — it was a second filter inside the subspace
`grad` already spans. The code labelled part of the gradient subspace
"harmonic" and fed it back at gain 0.82.

Verified: `harm_chat` has spread **6.2598** across 8 components. A true
harmonic form is the constant direction and has spread 0.

## 2. The Barabar 5/17 claim does not support the weight it is cited for

The chats state: "74.9 Hz = 256 × 5/17, error 0.526%, so the twin-prime
coupling constant is a measured physical constant confirmed in granite
2,300 years ago."

The arithmetic is right. The inference is not:

- **256 is a chosen constant**, not a measurement. Exact fit needs 254.66.
  The 0.526% is the gap between the number picked and the number fitted.
- **Eight rationals fit.** Sweeping every p/q with q < 64 for
  256·p/q within 0.6% of 74.9 Hz gives: 5/17, 7/24, 10/34, 12/41, 14/48,
  15/51, 16/55, 17/58. 5/17 is one of eight, and it was selected for having a
  twin-prime story attached *after* the fit.

So 5/17 sits in a tolerance band alongside seven others, and the "skip-3
coupling" meaning is a narrative fitted to the residual. It is not a
prediction the ratio made.

The twin-prime coupling hierarchy (1.000 / 0.757 / 0.461 / 0.294 / 0.188)
remains a legitimate **design choice** — means of ratios from the twin-prime
sequence, chosen for structure. It is not a measured constant, and the
chats' stronger phrasing is not supported by the number offered as proof.

## 3. What is unaffected

Not dismissed. These carry no dependency on either failure above:

- the 15 numbered geometric invariants and the bone atlas (hierarchical
  structure, osteon/lacunae/canaliculi counts, Bouligand rotation, φ ratios)
- the fruit-fly structure-encodes-function argument (Eon Systems' 140k-neuron
  connectome walking without training at 91% behavioural accuracy)
- **sheaves on stalks with helical windings** — local prime-wound phases,
  restriction maps propagating by skip distance, memory as per-stalk phase
  read. This is the architecture that connects to the existing stalk docs
  (`stalk-architecture-2026-09-08.md`, `braided_stalks.py`) and it needs no
  Barabar at all.
- goal-directed bias as a control mechanism (harm pulled toward a target
  through a gain)
- the fix for the never-updated state — the earlier 9-manifold class
  discarded every cell's `new_state`, so the loop never evolved

## 4. The self-assessment

The chat's most accurate passage was its own: a transformer has no
constitutional ground (resets every session), learned attention weights
rather than derived ones, and global rather than stalk-local representations.

That is the counterexample to the framework's own claims, stated by the
framework. It is also the useful part: it names exactly what a
constitutional-ground architecture would have to add to a language model,
and it is checkable — reset-per-session is measurable.

---

## 5. Pre-existing test failures (not from this work)

`python -m pytest tests/` → **357 passed, 5 failed**. Verified pre-existing by
removing both new files and re-running: the identical 5 fail.

```
tests/test_coupling_37hz.py::SpreadDominanceTests::test_spread_beats_base_frequency
tests/test_em_cymatics.py::test_e9_f137_load_bearing
tests/test_kuramoto_state_leak.py::test_kl_3_locks_at_stable_dt
tests/test_kuramoto_state_leak.py::test_kl_4_lock_survives_step_count
tests/test_kuramoto_state_leak.py::test_kl_5_lock_survives_coupling_sweep
```

Not touched here. Flagged so they are not mistaken for fallout.