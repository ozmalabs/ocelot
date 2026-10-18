# Prediction world: a judge that weighs the trend, not non-regression (pre-registration v9, 2026-10-10)

This is written and committed before any v9 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v9".

## Why

v8 showed that the experienced agent is held back by its own judge.
- The old judge vetoes any change that makes an already-mastered level worse. Every extra level it knows is another veto.
- Escalation therefore made the agent change less and predict new physics worse.

The user's correction: "never getting worse" is a category error; "trending generally upwards" is the right criterion. And the judge, being the metacognition, should weigh all the variables, choosing which dimensions are salient and how wide to look, rather than applying a fixed cut-down formula.

## What changed (loop 1.10.0, `judge_mode = "aperture"`)

**Evidence (mechanical).** For every level the agent has met, the mechanical half writes `JudgeView` nodes:
- **The change now:** the candidate's gain over its control (control − variant surprise) on the level's recent episodes, and on a longer stretch.
- **The trend:** the level's movement over the agent's own adoption history, with the candidate as the newest point. It is read as the least-squares slope over the last 3 points and over all of them.
- **Noise:** each view has its own standard error, measured from the episodes.

**Judge (graph rules).**
- **Weight.** Each view's weight is its level's learned trust (`JudgeAxis.log_weight`).
- **Combined evidence.** G = Σ weight·gain, tested against its own combined noise: Z = G / √(Σ (weight·noise)²). So:
  - magnitudes decide;
  - noise decides only whether a movement is real;
  - one large loss outweighs many small gains.
- **Aperture.** It opens rank by rank, across time and order:
  1. every level, recent;
  2. plus longer stretches;
  3. plus each level's recent trend;
  4. plus its whole trend.

  It stops once |Z| ≥ 1.645. The sign is the verdict. If it never settles, the change is refuted as unsettled.
- **Dips become concerns.** A dip it accepts (a non-target level worse beyond 1.645 of its noise) becomes the agent's own concern on that level, so the trend corrects itself. Repairs do not file further dips.
- **Learned trust.** Each adoption records a forecast per level. When the level is next measured, a forecast that held raises that level's trust, and one that failed lowers it.
- **No revisits.** Under this judge the agent does not return to a model it has moved on from.

**What is not done.**
- The judge does not boot the full ~850-seed cognition. It is built from the agent's own mechanisms, as graph rules inside the frozen loop seed:
  - residual-driven aperture (`reading_dwell`, `aperture_frame`);
  - salience;
  - learned per-axis log-weights (`frame_weights`);
  - order-N trend.

  Booting the full corpus into each of the 1,920 runs' agents costs 12–27 s per boot. Its rules would not take part in this judgement unless wired to it.
- `TimeInfer` is not used. It requires exactly regular integer streams, and surprise trajectories are noisy floats. The trend is a least-squares slope measured mechanically.

**Development, disclosed.** The first designs failed in development and were changed:
1. Per-view z-scores, combined. Many small, consistent gains outvoted a 0.28 loss on another level, and the judge adopted the loss. This led to magnitude-weighted evidence.
2. Weighting levels by how bad they currently are. Each fix for the worst level reversed an earlier fix, and the judge thrashed (seed 9000 adopted 18 changes and ended worse). This led to trust-only weights.
3. Other levels entering only at wider apertures. Trials were settled on the target level alone. This led to every level being in scope at the narrowest aperture.
4. Two more fixes:
   - a cascade of dip concerns, now bounded;
   - revisiting old models, now barred.

**Curriculum with the final design:**

| seed base | levels mastered | L5 held-out surprise | old judge's L5 |
|---|---|---|---|
| 1000 | 5 | 0.139 | 0.064 |
| 2024 | 4 | 0.137 | 0.138 |
| 5000 | 5 | 0.138 | 0.066 |
| 9000 | 5 | 0.139 | 0.139 |

On 1000 and 5000 the old judge's authored predicate model has lower L5 surprise (0.064–0.066 vs 0.138–0.139).

**Smoke test.** Seed 1000, on 4 levels of the (seen) v8 draw 0:
- The escalated agent under the new judge beat the old judge on 3 of 4 levels in final surprise, and on all 4 in competence across all levels met.
- The newborn was best on the 2 easy levels.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.10.0;
- `seeds/prediction_self_improvement.json` 1.10.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v8.py`, and the v6/v7 harness code it imports;
- `evaluation/substrate_capability/prediction_world_sequential_analysis_v9.py`.

## Procedure

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. Set A is draws 0–5 and set B is draws 6–11, giving 384 pairs.
- **Arms.** Each run gets up to 30 episodes.

| arm | judge | before the level |
|---|---|---|
| `on_trained_old` | threshold | curriculum |
| `on_trained_new` | aperture | curriculum |
| `on_escalated_old` | threshold | curriculum + escalation (8 levels, patience 12) |
| `on_escalated_new` | aperture | curriculum + escalation |
| `on_naive_new` | aperture | newborn |

- **Metrics.**
  - final surprise on 5 fresh episodes of the held-out level;
  - `all_levels_mean`: the final model's mean surprise on fresh episodes of every level the arm has met, plus the held-out level;
  - experiments.
- **Tests.** A two-sided exact sign test, and a two-sided sign-flip permutation test on the mean (200,000 flips, seed 20261010). Pocock boundary: p < 0.0294 at each of two looks.

## Hypotheses

- **H12 (the new judge keeps an experienced agent improving).** For `on_escalated_new` vs `on_escalated_old` on final surprise:
  - the mean difference is < 0, with permutation p < 0.0294.
- **H13 (an experienced agent under the new judge beats a newborn).** For `on_escalated_new` vs `on_naive_new` on final surprise:
  - the sign test favours escalated, with p < 0.0294;
  - the mean difference is < 0, with p < 0.0294.
- **H14 (competence across everything it has met is higher).** For `on_escalated_new` vs `on_escalated_old` on `all_levels_mean`:
  - the mean difference is < 0, with p < 0.0294.
- **Reported:**
  - `on_trained_new` vs `on_trained_old`, on final surprise and on all levels;
  - `on_trained_new` vs `on_naive_new`;
  - `on_escalated_old` vs `on_naive_new`.

My expectations:
- **H12 and H14:** likely, from the smoke test.
- **H13:** uncertain. The newborn wins easy levels outright.

## What this does and does not test

This tests a judge that weighs the trend across every level met, at a time and order aperture chosen by the evidence, with trust learned from its own forecasts, against the non-regression threshold judge, for an agent whose experience keeps growing.

The view families, the aperture ranks, the settling bar (1.645) and the trust update are human-written and frozen. The agent learns its trust weights, and it chooses the aperture per decision.
