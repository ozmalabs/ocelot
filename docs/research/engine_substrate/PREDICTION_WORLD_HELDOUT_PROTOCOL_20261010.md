# Prediction world: held-out levels and the cost of improvement (pre-registration, 2026-10-10)

This is written and committed before any held-out level exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`.

## Why

The curriculum result (`PREDICTION_WORLD_RSI_RESULTS_20261010.md`) has one central weakness. Its building blocks, the context atoms and the combining operator, were chosen after I had analysed the curriculum's own residuals. This test asks two questions:
1. Does the self-improvement loop help on levels nobody tuned for?
2. Does an agent that has already improved itself improve more cheaply on something new?

## Frozen at this commit

The following are frozen:
- `seeds/prediction_world.json` 1.2.0 and `seeds/prediction_self_improvement.json` 1.2.0 (all agent rules, the judge and the policy);
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v1.py`.

After this commit, none of them change before the run. If the harness turns out to have a bug, the fix is logged in the results doc and every arm is rerun. The agent's rules are not changed at all.

## Held-out levels

There are 8 levels, `domains/prediction_world.heldout_levels(draw_seed, 8)`, with `draw_seed = int(<this commit's hash>[:8], 16)`. The draw is fixed by the hash, so nobody chooses it.

The family is broader than the curriculum. It covers:
- open space or a box of 15–40 cells;
- downward gravity 0.1–0.8;
- sideways gravity ±0.05–0.4;
- damping 0.05–0.35;
- energy-losing bounces (restitution 0.6–0.95);
- any combination of these.

Sideways gravity, restitution, and damping inside a box never appear in the curriculum. Some levels may be unmasterable by anything the agent can express. All of them are reported, and none are dropped.

## Arms and procedure

There are 4 seed bases (1000, 2024, 5000, 9000), 8 levels and 4 arms. Every level starts from the same state, so one hard level cannot block another.

| arm | before the level | at the level |
|---|---|---|
| `on_trained` | 60-episode curriculum, self-improvement and authoring on | same flags |
| `no_authoring_trained` | curriculum, authoring off | same |
| `off_trained` | curriculum, self-improvement off | same |
| `on_naive` | nothing (newborn) | self-improvement and authoring on |

At the level, each arm gets at most 30 episodes (seeds `seed_base + 100000 + level·100 + i`). It stops once its own curriculum marks the level mastered: 3 consecutive episodes at or under 0.15.

Recorded per run:
- mastered or not, and episodes to mastery;
- the experiments and residual fits the graph requested;
- the models it authored;
- the final model's surprise on 5 fresh episodes (seeds 10⁷+);
- for reference, the best single base model's surprise.

## Predictions

- **H1 (the loop generalises).** Summed over the 32 level×seed runs, `on_trained` masters more than `no_authoring_trained`, and more than `off_trained`.
  - Falsified if `on_trained` ≤ `no_authoring_trained`.
- **H2 (prior self-improvement lowers the cost of the next).** Take the runs where both `on_trained` and `on_naive` master the level, paired by level and seed base. `on_trained` should need fewer episodes in more pairs than `on_naive` does.
  - Falsified if it doesn't.
  - An effect against H2 is plausible. The trained agent must weigh any change against five mastered levels (retention), while the naive one has nothing to protect.
- **No prediction** about absolute mastery counts.

## What this does and does not test

H2 is the falling-cost measure, but only at the object level. The improver itself (the loop seed) stays frozen. A positive H2 would mean that models the agent built earlier make later learning cheaper. It would not mean the agent improved its way of improving.

The levels are blind to tuning but not to the family. I wrote the physics family, though not the draw.
