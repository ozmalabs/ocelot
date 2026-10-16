# Prediction world: many draws, robust mastery, and a search that learns from its own record (pre-registration v3, 2026-10-10)

This is written and committed before any v3 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v3".

## What changed since v2 (loop 1.4.0)

**1. Robust mastery.** A level is mastered when the one-sided 95% upper confidence bound on the mean surprise of its last 5 episodes is at or under the 0.15 floor:
- the bound is `mean + 1.645·sd/√5`;
- all 5 episodes must be under the current model;
- under the old rule, three lucky episodes in a row were enough.

A concern is filed when the mean of the last 3 episodes since the last change is above the floor, or when 10 episodes have passed without robust mastery.

**2. A search that learns from its own record (meta level).** The agent keeps a `PredictionOperatorStat` per authoring operator: base, composition, residual_fit, residual_refit, residual_refit_all, prune_component and drop_layer. Each records how many of that operator's candidates were tried, supported and adopted. Graph rules update it after every judged trial. With `meta_search` on, two things change:
- **Batched proposals.** Trials go in batches: only the untried candidates whose operator has the best yield so far, where yield = (supported+1)/(tried+2). The next batch is proposed only once this one is judged with nothing to adopt.
- **Skipping.** An operator tried at least 8 times with yield under 0.15 is skipped altogether.

The rules are human-written and frozen. What changes with experience is the record, and so the order and breadth of the agent's search. This is second-order adaptation: the improver's behaviour is shaped by its own history. It is not the agent rewriting its improvement rules.

**Development evidence, disclosed.** It comes only from the curriculum and from two already-seen levels (v2's 104 and 108, seed base 1000).
- Curriculum: meta search cut experiments by 7–20% on all four seed bases, with identical levels, adoptions and held-out surprise.
- On 104, the experiment counts were:

  | arm | experiments |
  |---|---|
  | learned record | 35 |
  | reset record | 53 |
  | flat (meta off) | 68 |

  Final surprise was the same for all three, except flat, which was 0.178 vs 0.171.
- On 108: learned 26, reset 32, flat 32.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.4.0;
- `seeds/prediction_self_improvement.json` 1.4.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v2.py`.

## Draws and procedure

- **Draws.** There are 6 fresh draws: draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. With 8 levels each, that is 48 levels, run on 4 seed bases (1000, 2024, 5000, 9000), giving 192 level×seed pairs.
- **Arms.** Each arm starts from the same state. The three trained arms are identical forks of one curriculum-trained agent per seed base.

| arm | start |
|---|---|
| `on_trained` | as trained, meta search on, its own record |
| `on_trained_reset` | as trained, record zeroed |
| `on_trained_flat` | as trained, meta search off |
| `on_naive` | newborn, meta search on |

- **Budget.** Each run gets up to 30 episodes and stops at robust mastery.
- **Primary external metric.** The final model's mean surprise on 5 fresh episodes of the level (seeds 10⁷+), which the agent never sees.
- **Cost metric.** The number of experiments the graph requested at the level.
- **Statistics.** Pairs are matched by draw, level and seed base. Tests are two-sided exact sign tests with ties dropped, at α = 0.05.

## Predictions

- **H3 (prior self-improvement leaves it better placed than a newborn).** `on_trained` has lower final surprise than `on_naive` in more pairs, with p < 0.05.
  - Falsified otherwise.
- **H4 (its own record makes later improvement cheaper, at no cost in quality).** Both of the following must hold:
  - **(a)** `on_trained` requests fewer experiments than `on_trained_reset` in more pairs, with p < 0.05;
  - **(b)** non-inferiority: the mean of (`on_trained` − `on_trained_reset`) final surprise is ≤ +0.01.

  Falsified if either fails.
- **H4b (vs no meta search).** The same two tests against `on_trained_flat`. Expected to hold, reported either way.
- **No prediction** about robust mastery counts. They are reported.

## What this does and does not test

H4 is the first test here of the improver's behaviour improving with experience. If it holds, the record of what worked in the curriculum makes the search on new physics cheaper, without making it worse.

It does not show open-ended recursive self-improvement:
- the meta rules (batching, skipping, and the yield formula) are human-written and frozen;
- the agent cannot invent a new way to search, only re-weight the operators it has.
