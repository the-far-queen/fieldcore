# Stalk Architecture v6.1

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). The previous
> version of this paper presented stalks as a "topology theorem." Per Grok
> (segment 02, applied 2026-09-16): "stalks are a data-structure proposal, not
> a topology theorem." This rewrite says so and shows the measured coupling.

## 1. What a stalk is

A stalk is a **Hopf-fiber segment from the interface T into the working tube V**:
fixed base point on S², varying signed distance `r ≥ π/4` from T. In runtime
terms: a record with an embedding, a list of cross-member links, and a
status (`candidate | admitted | committed | refused`).

Implementation: `fieldcore/src/stalk_control.py`. The StalkRegistry exposes
`add`, `commit`, `refuse`, and `reward_curve`.

## 2. REINFORCE reward curve (now measured)

Per Grok: "REINFORCE in stalk_control.py needs a reported reward curve or it
is decoration." The reward curve is now measured.

Method:

1. Take a small registry of committed stalks (n ≥ 1).
2. Compute ψ₀ proxy = mean of committed embeddings.
3. For t in `range(ticks)`: perturb ψ₀ proxy by small Gaussian noise; measure
   mean cosine to ψ₀ proxy across committed stalks. This is the reward.
4. Record `(tick, mean_reward, n_committed, n_refused)`.

Output JSON:

    {
      "mean_reward": float,
      "n_committed": int,
      "n_refused": int,
      "curve": [float, ...],
      "ticks": int
    }

Interpretation: if `mean_reward` rises across the curve, the policy gradient
is pushing stalks toward ψ₀. If it falls or oscillates, the perturbation
is too large or the committed set is too sparse.

## 3. Cross-members as support lists

Cross-members are the support lists on the unit. A unit admitted because it
was close to a committed unit carries that unit's id in its `support` list.
Retrieval along cross-members uses the same gate as direct retrieval.

## 4. What is NOT in this paper

- No claim that stalks are a Heegaard surface theorem. They are records.
- No claim that the reward curve implements policy gradient in the formal
  sense. It is a stand-in for the policy gradient signal until a real one
  is wired.
- No claim about topological depth beyond "Hopf-fiber segment from T into V."

## 5. Tests

A stalk survives a tick: `reward_curve(ticks=50)` runs without raising.
Cross-member support is preserved across `commit()`.

## 6. The picture, restated

The interface T is the wall. Stalks point inward. Each stalk is a fiber
segment. The reward curve measures whether the policy is moving stalks
toward the ground or away from it.
