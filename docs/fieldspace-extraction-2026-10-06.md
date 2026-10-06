# FieldSpace extraction — 2026-10-06

**source:** https://github.com/enuminous/FieldSpace
**audited by:** Hermes, 2026-10-06
**extracted into:** `fieldcore/src/field_atlas.py`, `fieldcore/tests/test_field_atlas.py`
**clone:** `work_repos/fieldspace-candidates/FieldSpace` (HEAD 3a5b659)

---

## 1. what the repo is

An 11-sector field interaction atlas. Sectors `{E, M, S, F, W, T, I, R, H, P, A}` —
E gravity, M electromagnetic gauge, S symmetry gauge, and eight scalars. Every
three-element subset gets one interaction block: **C(11,3) = 165 blocks, 585
displayed statements, 45 incidences per sector.** Graph-theoretically, the index
structure is the complete 3-uniform hypergraph on 11 vertices.

Contents worth knowing about:

| file | what it is |
|---|---|
| `EFMW_165_field_equations.txt` | 65 KB source, 165 triplet blocks |
| `FieldSpace/Structure.lean` | Lean 4, `native_decide` on the combinatorics |
| `FieldSpace/Coupling.lean` | Lean 4, `ring`/`simp` on a 4-term residual polynomial |
| `sim/fieldspace_sim.py` | 235-run ablation harness over a synthetic system |
| `scripts/audit_fieldspace.py` | source integrity audit |
| `tests/test_fieldspace.py` | 3 tests — **one is stale, see §4** |

---

## 2. what I verified myself, not from the README

I cloned and ran it rather than reading the claims.

```
python scripts/audit_fieldspace.py
  triplet_headings: 165   populated_blocks: 165
  missing_triplets: []    empty_triplets: []
  einstein 45 | gauge_dynamics 90 | bianchi 90 | scalar 360 | total 585

python sim/fieldspace_sim.py --outdir /tmp/fs
  run_count: 235   all_stable: true
  ablation_results.csv -> 235 rows

python -m pytest tests/  ->  1 failed, 2 passed
```

**Reproducible and internally consistent, with one exception.** The audit, the sim,
and the counts all check out. The Lean formalization is genuinely kernel-checked.

The author's own honesty standard is high and is worth crediting: the README says
*"proposed phenomenological formulation; independently unreviewed"*, the sim's own
output carries *"toy structural simulation only; not physical validation"*, and
§Formal issues lists seven unresolved problems including the missing dimensional
table. This is a well-labelled speculative structure, not a claim dressed as a
result.

---

## 3. the stale test, and why CI never caught it

`test_current_source_defect_is_detected` asserts `len(headings) == 164` and that
triplet `AHP` is missing. That was true on 2026-09-29, when an audit caught the
source file uploaded truncated at its tail with the S-P-A body empty and H-P-A
omitted. The source was then restored. **The test was never updated.**

```
E  AssertionError: 165 != 164
```

The CI workflow that runs these tests triggers on:

```yaml
on:
  push:
    branches:
      - "fieldspace-zoo-lean-sim-*"
  pull_request:
    branches: main
```

**Pushes to `main` do not trigger it.** The 165-restoration landed on main, so the
stale assertion was never executed. This is the same defect class as simself's
unwired dreamer: a check that exists, passes review, and never runs.

---

## 4. what was extracted, and what was refused

### taken

**The combinatorics, generalized.** FieldSpace hard-codes 11 sectors and rank 3.
The result is general and the generalization is the valuable part:

```
atlas size           C(n, k)
sector incidence     C(n-1, k-1)   — uniform across all sectors
pair incidence       C(n-2, k-2)
class partition      C(a,j) * C(n-a,k-j) for a distinguished class of size a
```

`field_atlas.py` takes any n and k. Verified against brute force for n,k in
2..10 and reproduced FieldSpace's own numbers exactly — 165 blocks, degree 45,
overlap spectrum `{2: 1980, 1: 6930, 0: 4620}`.

**The overlap histogram, as a stronger identity.** FieldSpace proved the *sum*
`1980 + 6930 + 4620 = C(165,2)` in Lean. `overlap_spectrum()` returns the full
histogram, which is more informative for the same cost, and the tests assert the
closed forms (`C(11,2)·C(9,2) = 1980`, `C(11,3)·C(8,3)/2 = 4620`), not just the sum.

**The ablation harness shape.** Systematic remove-1 / remove-2 / remove-3 sweep
with every tail statistic reported rather than one headline number. Fieldcore's
kuramoto and cymatics modules want exactly this.

### refused

**The toy simulator's dynamics.** The couplings are literal modular arithmetic on
sector indices — `((i+1)*7+(j+1)*11)%9-4`. That is a test fixture. Its 235 stable
runs say the harness works, not that anything physical is stable. Carried over as
`src/field_atlas.py::_demo_dynamics`, explicitly labelled synthetic.

**The EFMW equations themselves.** Placeholder interactions. No dimensional table,
no units, no fitted parameters, no conservation identity derived. The README's own
§4 lists these as unresolved. Importing them into fieldcore would put an
unbacked claim into a substrate repo.

**The sector names.** `{E,M,S,F,W,T,I,R,H,P,A}` is a specific phenomenological
choice, not a mathematical fact. `field_atlas.py` keeps them only as a test
fixture reproducing the upstream numbers, and takes the sector set as a parameter.

---

## 5. load-bearing refusal

`AblationHarness` **refuses to run with no dynamics supplied:**

```
AtlasRefusal: no_dynamics_supplied:harness_refuses_to_synthesise_one
```

The upstream harness hard-coded its synthetic dynamics, which is fine for testing
the harness. Reused as a general tool that default would report confident deltas
about a system nobody defined. The refusal is the point, and it is tested.

`AtlasRefusal` also fires on rank > sectors, rank < 1, empty sector set, duplicate
sectors, unknown distinguished sectors, and all-sectors-removed — each because the
degenerate case returns something that reads downstream as a well-formed space
with no interactions in it.

---

## 6. status

```
fieldcore/tests/test_field_atlas.py   18 passed
fieldcore full suite                   103 passed, 0 regressions
```

`tests/test_sparse_substrate.py` and `tests/test_sheaf_nn_latency.py` error on
collection — **numpy is not installed in this environment**. Pre-existing, unrelated
to this extraction, not fixed here.

## 7. licence

**FieldSpace has no LICENSE file.** The README states: *"No license is inferred by
this repository documentation."* With no grant, the default is exclusive
copyright — so the code cannot be copied verbatim into our MIT-licensed repo.

What was taken is the *idea and the theorem* (complete k-uniform enumeration;
ablate systematically), reimplemented from the mathematics. None of their source
text, code, or weights was copied. That distinction is the reason this is safe to
commit and should stay explicit if anyone revisits it.

---

## 8. the pattern worth keeping

The most useful thing in this repo is not the physics. It is that a 8-day-old
speculative project got three things right that most mature repos get wrong:

1. **it labels its own epistemic status** — "proposed", "independently
   unreviewed", "not physical validation", on the artifact itself, not just the
   README;
2. **it states what is unresolved** — seven named formal issues including units;
3. **it keeps the original source frozen** so corrections are auditable.

And one thing wrong that is worth more than all three: **a test that never runs.**
The CI trigger excluded the branch the work landed on. Green-looking, worthless.

That is the thing to check in our own repos. `simself` had the unwired dreamer
this week. Worth asking whether every fieldcore test is reachable from a command
someone actually runs.