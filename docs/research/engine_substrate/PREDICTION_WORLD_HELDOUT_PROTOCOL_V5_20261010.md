# Prediction world: per-kind record, rounds of self-proposed policy, sequential analysis (pre-registration v5, 2026-10-10)

This is written and committed before any v5 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v5".

## What changed since v4 (loop 1.6.0)

**1. A search record per kind of world.**
- `PredictionOperatorStat` is now kept per (operator, world kind). The kind is box (w < 1000) or open; the agent reads it from the level's latest episode. The two-kind partition is human-written.
- Yield, skipping and `enabled` credit all use the current kind's record.
- Skipping is a real skip again (`skip_last_resort` = 0). The safety v4 bought with last-resort trials now comes from the per-kind record plus the `enabled` credit:
  - an operator is skipped only if, in this kind of world, it was tried at least 8 times;
  - its yield there is under 0.15;
  - and nothing was ever built on its trials there.

**2. Rounds of self-proposed policy.**
- With the curriculum mastered, the agent runs 3 rounds of proposals from the same 7-change grammar. Each round proposes from the policy the earlier rounds left.
- **Measurement (mechanical).** Each round is measured on 8 practice levels drawn fresh for that round and never reused.
- **Judging (graph).** A change is supported only if both hold:
  - its weighed net ≥ 0.002;
  - it wins on more practice levels than it loses, so one level cannot carry it (as one did in v4).
- The graph closes a round once it has judged and adopted.

**3. Analysis.** See below. This replaces one sign test per draw set.

**Development evidence, disclosed.**
- **Curriculum.** All 4 seed bases still master all 5 levels.
- **v3's draw 4** (seen; it includes level 139, where v3's skip failed), seed bases 1000 and 2024:
  - learned record 303 experiments, reset 369 (−18%);
  - final surprise identical on all 16 runs, including both runs of level 139.
- **Practice phase.** A smoke run with 1 seed base, 2 levels and 2 rounds adopted `meta_min_trials` ×0.5 in round 1.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.6.0;
- `seeds/prediction_self_improvement.json` 1.6.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v4.py`;
- `evaluation/substrate_capability/prediction_world_sequential_analysis.py`.

## Draws, looks, and the decision rule

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`.
  - Set A is draws 0–5 and set B is draws 6–11, each 192 pairs (8 levels × 4 seed bases × 6 draws).
  - The practice phase runs once, and its adopted policies are reused for set B (`..._meta_20261010.json`).
- **Arms.** As in v4: `on_trained`, `on_trained_noexperts`, `on_trained_reset`, `on_trained_meta` and `on_naive`. Each run gets up to 30 episodes.
- **Look 1** = set A. **Look 2** = A and B pooled, 384 pairs.
- **Decision rule.** Pocock boundary: a hypothesis is supported at a look when its pooled two-sided exact sign test has p < 0.0294 in the predicted direction, and its non-inferiority conditions hold. Two looks give overall α = 0.05.
  - A hypothesis supported at look 1 stays supported. One not supported by look 2 is not supported.
  - Set B is run whatever look 1 shows.
  - The per-set results are reported too, so a pooled result carried by one set shows.
- **Analysis.** `prediction_world_sequential_analysis.py <set A report> <set B report>`.

## Hypotheses

- **H3 (trained beats newborn).** `on_trained` has lower final surprise than `on_naive`.
- **H4 (the per-kind record is cheaper and safe).** All three must hold:
  - `on_trained` uses fewer experiments than `on_trained_reset`;
  - the mean final-surprise difference is ≤ +0.005;
  - at most 1% of pairs are worse by more than 0.1. A v3-style failure is allowed only that often.
- **H5 (its own rounds of policy change pay).** `on_trained_meta` has lower weighed cost than `on_trained`. Weighed cost = final surprise + retention harm + 0.001 × experiments.
- **H6 (experts help).** Both must hold:
  - `on_trained` has lower final surprise than `on_trained_noexperts`;
  - the mean retention-harm difference is ≤ +0.01.

My expectations:
- **H4:** likely.
- **H6:** possible at 384 pairs, given v4's 5 vs 0.
- **H3:** uncertain. v3 and v4 disagreed.
- **H5:** uncertain.

## What this does and does not test

H5 is still the agent choosing changes to its own search from its own measured evidence. Now it does so over several rounds, on fresh practice each time, and requires consistency across practice levels.

The grammar, the practice harness, the judge and the two-kind partition are human-written and frozen. This is not open-ended recursive self-improvement.
