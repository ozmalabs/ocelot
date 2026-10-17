# Prediction world: the agent shapes its own practice (pre-registration v7, 2026-10-10)

This is written and committed before any v7 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v7".

## Why

v6's judge selection was real but had no effect. On the agent's random practice levels, no proposal it would adopt showed a heavy single-level loss, so all three judges agreed. Yet held-out levels did contain such losses (v5's level 164, v6's level 133). The practice was too narrow to test the cases that decide.

## What changed (loop 1.8.0)

**Practice shaping.** With `practice_shaping` on, each practice set of each round is first drawn as a pool of 24 levels. The pool's first 8 are exactly the random regime's practice set.
- **Screening (mechanical).** Every pool level is run with the control and every proposal of the round, for 10 episodes. The spread of their weighed costs is written on a `PracticeCandidate` per level.
- **Selection (graph).** `pw_select_practice_level` keeps the 8 levels where the agent's proposals disagree most: the ones that can tell its choices apart.
- **Use.** Judging, and in round 0 judge calibration on both P1 and P2, then happens only on those 8 levels.
- Everything else is as in 1.7.0, including calibration on.

**Disclosure.**
- Designed after v6. The v6 draws are now a development set.
- A smoke run (1 seed base, 3-level sets, a 6-level pool, 1 round) selected `tail` on a tie and adopted `meta_min_yield` ×2. Nothing has been run on held-out levels with 1.8.0.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.8.0;
- `seeds/prediction_self_improvement.json` 1.8.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v6.py`;
- `evaluation/substrate_capability/prediction_world_sequential_analysis_v7.py`.

## Procedure

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. Set A is draws 0–5 and set B is draws 6–11, giving 384 pairs.
- **Practice phase.** It runs twice per seed base, both calibrated:
  - **random:** v6's regime, on the same levels as v6;
  - **shaped.**
- **Arms.** Up to 30 episodes per run.

| arm | policy |
|---|---|
| `on_trained` | as born |
| `on_trained_meta_random` | from the random phase |
| `on_trained_meta_shaped` | from the shaped phase |

- **Cost and tests.** As in v6:
  - cost = final surprise + retention harm + 0.001 × experiments;
  - a two-sided exact sign test, and a two-sided sign-flip permutation test on the mean;
  - Pocock boundary: p < 0.0294 at each of two looks.

## Hypotheses

- **H9 (self-shaped practice beats random practice).** For `on_trained_meta_shaped` vs `on_trained_meta_random`:
  - the mean cost difference is < 0, with permutation p < 0.0294.
- **H5s (policy from shaped practice pays, without a tail).** For `on_trained_meta_shaped` vs `on_trained`, the H5t criteria:
  - the sign test favours shaped with p < 0.0294;
  - the mean cost difference is < 0, with p < 0.0294;
  - at most 1% of pairs are worse by more than 0.1.
- **Reported:** `on_trained_meta_random` vs `on_trained`, a replication of v6 H5t.

My expectation is uncertain. Shaped practice is weighted towards hard, contested levels. It may make the judge choice consequential and avoid the tail, or it may tune the policy to atypical levels and lose on typical ones.

## What this does and does not test

This tests the agent choosing what to practise on, from its own screening, so that its self-evaluation reaches the cases that decide.

The pool family, the screen, the spread statistic and k are human-written and frozen.
