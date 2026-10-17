# Prediction world: the agent selects its own judge (pre-registration v6, 2026-10-10)

This is written and committed before any v6 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v6".

## Why

In v5, the agent's rounds of policy change passed the pre-declared test, mostly by halving experiments. But in draw set B they lost about 0.7 cells of surprise in 5 pairs. The judge it used (1.6.0's: net, plus winning on more practice levels than it loses) counts levels, not magnitudes, so it could not see that tail.

I could hard-wire a tail rule. Instead, v6 tests whether the agent can choose how to judge its own policy changes from its own evidence.

## What changed (loop 1.7.0)

**The judges.** There are three, human-written:

| judge | supports a change when |
|---|---|
| `net` | its weighed net ≥ 0.002 |
| `sign` | it passes `net`, and wins on more practice levels than it loses (1.6.0's judge) |
| `tail` | it passes `sign`, and no practice level is lost by more than 0.05 |

**Judge selection.** With `meta_calibrate` on:
- Round 0's proposals are measured on practice set P1 and also on a second fresh practice set, P2. Both are drawn from seed ranges no evaluation uses.
- For each judge, the graph finds the best proposal it supports on P1, and that proposal's realised net on P2.
- It adopts the judge with the highest realised net, with ties going to the stricter judge (`pw_select_policy_judge`).
- Round 0's adoption waits for that choice. Rounds 1–2 use the chosen judge on fresh practice sets.

**Disclosure.**
- The three judges, and the idea of calibrating on a second practice set, were designed after seeing v5's set B. The v5 draws are now a development set.
- A smoke run (1 seed base, 3 practice levels, 2 rounds) selected `tail` on a three-way tie and adopted `meta_min_yield` ×2, then `meta_min_trials` ×0.5.
- Nothing has been run on held-out levels with 1.7.0.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.7.0;
- `seeds/prediction_self_improvement.json` 1.7.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v5.py`;
- `evaluation/substrate_capability/prediction_world_sequential_analysis_v6.py`.

## Procedure

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. Set A is draws 0–5 and set B is draws 6–11, with 192 pairs each.
- **Practice phase.** It runs twice per seed base, on the same P1 practice levels:
  - **calibrated:** the agent selects its judge;
  - **fixed:** `sign`, as in 1.6.0.
- **Arms.** Up to 30 episodes per run.

| arm | policy |
|---|---|
| `on_trained` | as born |
| `on_trained_meta` | from the calibrated phase |
| `on_trained_meta_fixed` | from the fixed phase |

- **Cost per run.** Final surprise + retention harm + 0.001 × experiments.
- **Tests (two per comparison).**
  - A two-sided exact sign test on per-pair cost.
  - A two-sided paired sign-flip permutation test on the mean per-pair cost difference: 200,000 flips, RNG seed 20261010.
- **Looks.** Look 1 is set A; look 2 is A and B pooled. Pocock boundary: p < 0.0294 per look.

## Hypotheses

- **H5t (its self-judged policy changes pay, without a tail).** For `on_trained_meta` vs `on_trained`, all of the following must hold:
  - the sign test favours meta with p < 0.0294;
  - the mean cost difference is < 0, with permutation p < 0.0294;
  - at most 1% of pairs are worse by more than 0.1.
- **H8 (the self-selected judge beats the fixed one).** For `on_trained_meta` vs `on_trained_meta_fixed`:
  - the mean cost difference is < 0, with permutation p < 0.0294.
- **Reported, not tested.** `on_trained_meta_fixed` vs `on_trained`, a replication of v5's H5.

My expectations:
- **H5t:** possible. It depends on whether the selected judge is `tail` and whether `tail` still lets the cheap changes through.
- **H8:** uncertain. If the agent selects `sign` on some seed bases, the arms coincide there.

## What this does and does not test

This is the first test here of the agent changing how it judges its own improvements, chosen from its own out-of-sample evidence.

The candidate judges, the choice rule, and the payoff it validates against are human-written and frozen. The agent selects among judges; it does not write one.
