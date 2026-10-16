# Prediction world: experts, dependency-aware credit, self-proposed policy (pre-registration v4, 2026-10-10)

This is written and committed before any v4 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v4".

## What changed since v3 (loop 1.5.0)

All of the following are graph rules except where marked mechanical.

**1. Experts (scope-confined change).**
- The Predictor can hold up to 2 more full models as experts, alongside its primary.
- For each body and axis, the prediction comes from the expert with the lowest cumulative error on that body so far.
- Two operators author an expert:
  - `pw_author_expert`: the concern's best local trial becomes the expert;
  - `pw_author_specialist_expert`: a specialist becomes the expert. The specialist is the best base model trialled at this level, with both context layers fitted from scratch on this level's frames alone. The fit is mechanical.
- Experts are a last resort: they are authored only once a concern's single-model fits have been tried and refuted.

**2. Dependency-aware credit.**
- A supported composite or expert credits the operator whose trial it was built from (`enabled`).
- That credit counts towards the operator's yield, and an operator with any credit is never skipped.
- Skipping is now a last resort rather than a ban: once nothing unskipped is left, skipped operators are trialled too.

**3. Self-proposed policy changes.**
- With its curriculum mastered, the agent proposes 7 changes to its own search policy (`MetaProposal`, from a human-written grammar): `retention_weight` ×0.5 or ×2, `meta_min_yield` ×0.5 or ×2, `meta_min_trials` ×0.5 or ×2, and `min_gain` ×0.5.
- **Measurement (mechanical).** Each proposal is measured on 6 practice levels the agent draws from a seed range no evaluation uses. Each practice run is a fork; control and variant get up to 20 episodes each. The score is practice surprise plus the surprise the result adds on its curriculum levels, and experiments spent.
- **Judging (graph).** The graph scores each proposal: net = (surprise saved) + 0.001 × (experiments saved). It adopts the best one with net ≥ 0.002, if any.

**Development evidence, disclosed.** The dev set was ten already-seen held-out runs: levels 101, 102, 104, 105 and 108 from earlier draws, on seed bases 1000 and 2024.
- **Experts.** They helped on 2 of the 10 runs, and changed nothing on the other 8:
  - 108/1000: 0.285 → 0.198;
  - 105/2024: 0.201 → 0.147, mastered.
- **Design changes driven by dev observations:**
  - expert gating changed from last-frame to cumulative error;
  - the specialist's base model is now the best trialled one;
  - experts became a last resort, after a version that authored them early broke curriculum L5 mastery on 2 of 4 seed bases;
  - skipping became a last resort, prompted by v3's level 139.
- **Cost.** On dev, the last-resort skipping raised experiment counts substantially compared with 1.4.0.
- **Practice phase (smoke run).** The agent adopted a change on 3 of 4 seed bases:
  - 1000: `retention_weight` ×2;
  - 2024: `meta_min_trials` ×0.5;
  - 9000: `meta_min_yield` ×2;
  - 5000: nothing; every practice level was already solved, with zero experiments.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.5.0;
- `seeds/prediction_self_improvement.json` 1.5.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v3.py`.

## Draws and procedure

- **Draws.** There are 6 fresh draws: draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. That makes 48 levels on 4 seed bases, giving 192 pairs.
- **Arms.** The arms are listed in the harness docstring: `on_trained`, `on_trained_noexperts`, `on_trained_reset`, `on_trained_meta` and `on_naive`. The trained arms are forks of one curriculum-trained agent per seed base. `on_trained_meta` carries the policy its own proposals adopted in phase 1.
- **Budget.** Each run gets up to 30 episodes.
- **Metrics.** Two are external:
  - final surprise on 5 fresh episodes of the level;
  - retention harm: the surprise the final model adds on curriculum levels 1–5, on fresh episodes.

  The cost metric is experiments.
- **Statistics.** Tests are two-sided exact sign tests over matched pairs, ties dropped, at α = 0.05.

## Predictions

- **H3 (retry: trained vs newborn).** `on_trained` has lower final surprise than `on_naive` in more pairs, with p < 0.05.
- **H6 (experts confine change).** Both of the following must hold:
  - `on_trained` has lower final surprise than `on_trained_noexperts` in more pairs, with p < 0.05;
  - the mean retention-harm difference (`on_trained` − `on_trained_noexperts`) is ≤ +0.01.
- **H4 (retry: learned record cheaper).** Both of the following must hold:
  - `on_trained` uses fewer experiments than `on_trained_reset` in more pairs, with p < 0.05;
  - the mean final-surprise difference is ≤ +0.01.
- **H5 (the agent's own policy change pays).** `on_trained_meta` has lower weighed cost than `on_trained` in more pairs, with p < 0.05. Weighed cost = final surprise + retention harm + 0.001 × experiments, the same weighing its practice judge used.
  - Pairs on a seed base where nothing was adopted are ties by construction.

My expectations from dev:
- **H6:** likely, with a small effect, because experts change few runs.
- **H3:** uncertain.
- **H4:** at risk, since last-resort skipping removes much of the saving.
- **H5:** uncertain. The practice levels come from the same family, but there are only 6 of them.

## What this does and does not test

H5 is the closest test yet to the agent improving its own improver: it chooses a change to its own search policy from its own measured evidence, and the change is judged on fresh draws.

What the test does not cover:
- The grammar of changes, the practice harness and the judge are human-written and frozen.
- The agent cannot propose a change outside the grammar.
- The agent makes only one round of proposals.
