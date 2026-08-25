# The planning horizon, derived from regulation

Three rungs closed on the same admission, each time in the honest-bounds section: **the compression
was stipulated.** A mask (`STRESS_COMPRESSES_APERTURE_RESULTS.md`) or a budget
(`COMPRESSION_MODELS_RESULTS.md`) was handed to a rule by a fixture, and nothing in the substrate
said why stress should produce either. `seeds/arousal_horizon.json` v1.0.0 closes that.

## The derivation

**An agent can only plan as far ahead as it can stay regulated.** So its projection budget is the
tick at which its own projected arousal would leave its own window of tolerance.

That is not a new computation. It is exactly the escape the future-manifold audit already performs,
run on the arousal dimension with the window as the allowed tube:

    window [lo, hi]         ->  target = centre, bounds = half-width
    projected arousal       ->  future_manifold_values
    earliest_decisive_tick  ->  the projection budget

**No stress coefficient, no tuned rate, no new scalar.** The window is already an allowed band
around a centre, which is the shape `future_manifold_bounds` describes — writing it that way is a
restatement, not a model. Two rules, both mutation-gated (dropping either fails tests).

## Measured

Capacity 8, arousal climbing `0..7`, window driven directly:

| window half-width | 8 | 6 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|---|---|
| **derived horizon** | 8 | 8 | 6 | 5 | 4 | 3 |

Monotone. The two wide cases sit at the ceiling because the arousal never escapes at all —
`earliest_decisive_tick` is `0` there, and `0` must read as *"the whole capacity is available"*,
never as *"no horizon"*.

## What this resolves

`COMPRESSION_MODELS_RESULTS.md` conditioned the earlier inertness claim by showing that **temporal**
compression *is* recoverable by more budget — which looked like it weakened the result. Once the
budget is derived, that recovery stops being something the agent can help itself to. Measured:
**raising the physiological capacity from 8 to 64 does not lengthen the horizon at all while the
window stays narrow**, because the window binds first. Widening the window restores it.

So the clinically familiar shape — you cannot reason someone out of dysregulation, but regulation
restores them — **falls out of the derivation instead of being stipulated by it.** The agent cannot
buy horizon; only regulation yields it. That is the same "different cures" crossover this line of
work keeps producing, arrived at from below this time rather than asserted.

## Scope — stated precisely, because it is easy to overclaim

This derives **window → horizon**, and nothing more. The other half of the chain —
stressor → arousal → dysregulation → window narrows, including the co-regulation that widens it
again — is `arousal_window_coreg`'s, predates this question, and carries its own gates. The tests
here drive the window directly and do **not** re-test it. The full chain is therefore:

| link | owner | status |
|---|---|---|
| stressor → arousal → dysregulation → window narrows | `arousal_window_coreg` | pre-existing, its own gates |
| **window narrows → horizon shortens** | **`arousal_horizon`** | **derived, this rung** |
| horizon shortens → `information_loss`, unresolved | `future_manifold` | measured earlier |

A composed end-to-end run — stressor in, shortened horizon out, with the affect seed's own episode
rules doing the narrowing rather than a `set_attr` — has **not** been done.

One build note worth keeping: the first version hung the window off the `AffectiveState` and had to
force the edge past Γ with `add_edge_unchecked`. That refusal was the signal the shape was wrong;
the seed now composes with `arousal_window_coreg`'s own topology (`Agent -has_window->
WindowOfTolerance`) instead of inventing a second one.

## Honest bounds

One arousal trajectory, one dimension, deterministic. `arousal_window_coreg`'s standing caveat — an
authored affect model, not a clinical one — is inherited in full and is **not** discharged by this
derivation being tidy. What the rung establishes is that the horizon no longer has to be supplied by
whoever is running the experiment; it does not establish that real arousal behaves this way.

Gates: `tests/test_arousal_horizon_migrated.py` 4/4, both rules mutation-tested; 75 passed across the
affect and manifold suites.
