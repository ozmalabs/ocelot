# Prediction world: a robustness view for the trend judge, and a trained-vs-newborn replication (pre-registration v10, 2026-10-10)

This is written and committed before any v10 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v10".

## Why

In v9, the trend judge adopted 9 models (of 384 runs) that blew up off-sample.
- Each carried an authored predicate that was harmless on the replayed episodes but explosive on fresh episodes of old levels. Retention harm was 45–1,134.
- All 9 had settled early, on narrow evidence. The judge never looked outside its recorded sample.

Separately, v8's reference comparison (plain trained vs newborn) passed for the first time, and needs a pre-registered replication.

## What changed (loop 1.11.0, `judge_robust = 1`)

- **Rehearsal views (mechanical).** For every level met, the candidate and control play 3 fresh episodes of the level. These come from the world, in a seed range no evaluation, practice or escalation uses: the agent revisiting a level it knows. They enter at aperture 1.
- **Look again before you leap (graph).** A favourable verdict commits only if it still holds one aperture wider. An unfavourable verdict settles at once.
- Everything else is the v9 trend judge.

**Development, disclosed.** On the three seen v9 blow-up cases (level 121, seeds 2024, 5000 and 9000), with the robust judge:
- retention harm fell to 0.00–0.01;
- final surprise was 0.157 vs 0.160, 0.221 vs 0.176, and 0.244 vs 18.8.

The curriculum still masters all 5 levels on all 4 seed bases (L5 held-out 0.062–0.139).

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.11.0;
- `seeds/prediction_self_improvement.json` 1.11.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v9.py`, and the v6/v7/v8 code it imports;
- `evaluation/substrate_capability/prediction_world_sequential_analysis_v10.py`.

## Procedure

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. Set A is draws 0–5 and set B is draws 6–11, giving 384 pairs.
- **Arms.** Each run gets up to 30 episodes.

| arm | judge | before the level |
|---|---|---|
| `on_trained_old` | threshold | curriculum |
| `on_naive_old` | threshold | newborn |
| `on_trained_plain` | trend, robust off | curriculum |
| `on_trained_robust` | trend, robust on | curriculum |
| `on_escalated_robust` | trend, robust on | curriculum + escalation |
| `on_naive_robust` | trend, robust on | newborn |

- **Metrics.**
  - final surprise;
  - `all_levels_mean` (the final model on fresh episodes of every level met, plus the held-out level);
  - retention harm;
  - a blow-up, meaning retention harm ≥ 1 or final surprise ≥ 2.
- **Tests.** A two-sided exact sign test, and a two-sided sign-flip permutation test on the mean (200,000 flips, seed 20261010). Pocock boundary: p < 0.0294 at each of two looks.

## Hypotheses

- **H15 (the robustness view removes off-sample blow-ups without giving up the gain).** For `on_trained_robust` vs `on_trained_plain`, all of the following must hold:
  - on `all_levels_mean`, the mean difference is < 0, with permutation p < 0.0294;
  - `on_trained_robust` has at most 1% blow-ups (≤ 3 of 384);
  - over pairs where neither arm blew up, the mean final-surprise difference is ≤ +0.005.
- **H3r (replication: trained beats newborn, threshold judge).** For `on_trained_old` vs `on_naive_old` on final surprise:
  - the sign test favours trained, with p < 0.0294;
  - the mean difference is < 0, with p < 0.0294.
- **H13r (an escalated agent under the robust trend judge beats a newborn under the same judge).** For `on_escalated_robust` vs `on_naive_robust`: the same two tests.
- **Reported:**
  - `on_trained_robust` vs `on_trained_old`, on final surprise and on all levels;
  - `on_trained_robust` vs `on_naive_robust`;
  - `on_escalated_robust` vs `on_trained_robust`.

My expectations:
- **H15:** likely, from development.
- **H3r:** uncertain. v8 passed, but v3–v5 disagreed.
- **H13r:** uncertain. v9's H13 was ahead but not significant.

## What this does and does not test

H15 tests whether the judge, given a view outside its own sample and a rule to confirm before committing, avoids adopting changes that only look good on what it has recorded.

The rehearsal count, its rank and the confirmation rule are human-written and frozen.
