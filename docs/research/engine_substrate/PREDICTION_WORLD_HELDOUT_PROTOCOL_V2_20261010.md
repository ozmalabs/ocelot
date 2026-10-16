# Prediction world: held-out levels v2, after revision (pre-registration, 2026-10-10)

This is written and committed before the v2 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v2".

## What changed since v1, and why

v1 (`PREDICTION_WORLD_HELDOUT_PROTOCOL_20261010.md`, draw `02818858`) found that the curriculum-trained agent could not revise what it had built:
- both layer slots were spent;
- each atom could be used once per model;
- coefficients could not be refitted.

On that draw the newborn mastered more runs (15/32 vs 12/32). Loop 1.3.0 adds revision operators, all graph rules, all weighed by the unchanged judge:
- **Refit:** a residual fit now also covers layers the model already holds, singly (`refit`) and jointly (`refit_all`).
- **Pooled fits:** each fit is offered on the level's frames alone and pooled with the mastered levels' frames.
- **One candidate per helpful fit:** every fit that helps becomes a candidate, so the judge weighs the alternatives against each other.
- **Prune:** the model minus one of its base components.
- **Drop:** the model minus its last layer.
- **A new layer feature:** the body's running acceleration estimate (`acc`). Without it a layer's gravity is a constant, which cannot transfer between worlds with different gravity.

These changes were developed against the v1 draw, which is now a development set. Final dev-set numbers for 1.3.0 (`evaluation/reports/prediction_world_heldout_v1_02818858_loop1.3.0_20261010.json`):

| | v1 (1.2.0) | dev (1.3.0) |
|---|---|---|
| mastery, `on_trained` vs `on_naive` | 12 vs 15 | 12 vs 15 (unchanged) |
| mean final surprise, `on_trained` | 0.236 | 0.191 (`on_naive` 0.272) |
| pairs with lower final surprise, trained vs naive | — | 22 vs 6 |

- The trained agent ends lower than the newborn on 101, 104, 106, 107 and 108, and higher on 105 and (marginally) 102.
- A diagnostic run with `retention_weight = 0` on level 105 did not master it either. So the trained agent's gap on 105 is not only the retention trade.

**Disclosure.** H3's second clause (final surprise) was written knowing the dev set satisfies it. The dev set does not satisfy the first clause (mastery). The test is whether either holds on a fresh draw. I expect the mastery clause to fail again and the surprise clause to be the one that decides H3.

## Frozen at this commit

The following are frozen at this commit, under the same rules as v1:
- `seeds/prediction_world.json` 1.3.0;
- `seeds/prediction_self_improvement.json` 1.3.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v1.py`.

## Draw and procedure

- `draw_seed = int(<this commit's hash>[:8], 16)`, 8 levels from the same family as v1.
- Same 4 arms, the same 4 seed bases (1000, 2024, 5000, 9000) and the same budget of 30 episodes as v1.

## Predictions

- **H1 (the loop generalises).** `on_trained` masters more runs than `no_authoring_trained` and more than `off_trained`.
  - Falsified if `on_trained` ≤ `no_authoring_trained`.
- **H3 (prior self-improvement now helps on balance).** Over the 32 level×seed pairs, `on_trained` either masters at least as many runs as `on_naive`, or ends with lower final surprise in more pairs than `on_naive` does.
  - Falsified if `on_naive` masters more runs *and* has lower final surprise in at least as many pairs.
  - My stated expectation, from the dev set, is that this is uncertain, leaning towards falsified on mastery.
- **H2 (from v1)** is reported as before. Among pairs where both master, count which arm needed fewer episodes, and whether the trained agent needed any experiments at all.

## What this does and does not test

H3 is the compounding test at the object level: does what the agent built and can now revise leave it better placed than a newborn on new physics? The improver itself (the loop seed) remains frozen. This is not a test of the agent improving its way of improving.
