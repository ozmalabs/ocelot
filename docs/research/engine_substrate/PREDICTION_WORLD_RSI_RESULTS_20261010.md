# Prediction world: endemic self-improvement with an off-arm counterfactual (2026-10-10)

Plan: `OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md`. Redirect from the persona-chat work: demonstrate endemic self-improvement in any domain, not a chatbot.

## Result

Over 60 episodes, one agent that is allowed to change its own predictor works out its own surprise, runs its own trials, judges them against its own bar and climbs from level 1 to level 4. It masters levels 1–3 along the way. The same agent with self-change switched off (`PredictionPolicy.self_improvement = 0`) still notices it keeps missing and files the concern. It cannot act on it, so it stays at level 2 for good. The seed bases 1000, 5000 and 9000 gave the same outcome.

| | on | off |
|---|---|---|
| final level / mastered through | 4 / 3 | 2 / 1 |
| experiments / adoptions | 15 / 2 | 0 / 0 |
| final model | acceleration, reflect | velocity, no reflect |
| concerns | L2 resolved, L3 resolved, L4 exhausted | L2 open |
| final-model surprise L1–L5 (cells) | 0, 0.345, 0, 0.277, 0.512 | 0, 0.387, 0.5, 0.647, 0.973 |

Adoptions (on arm):
1. L2 (bounce): velocity → velocity+reflect, net 0.209.
2. L3 (fall): velocity+reflect → acceleration+reflect, net 0.300. It was chosen over acceleration without reflect (net 0.076, also supported), because the latter loses the bounce on L2.

A run takes about 1 s per arm. Reproduce with `evaluation/substrate_capability/prediction_world_rsi_v1.py 60 1000`. The test is `tests/test_prediction_world_migrated.py`.

## What the graph decides and what is mechanical

The graph decides everything below. These are rules in `seeds/prediction_world.json` and in `seeds/prediction_self_improvement.json`, which is frozen and has its types protected by `improvement_integrity`:
- the prediction itself (`predict_body_next`);
- mastery and level advance;
- filing a surprise concern (after `window` episodes since the last change, none under `surprise_floor`);
- proposing one experiment per untried candidate;
- the judge;
- adoption (best `weighed_net`, with ties going to the simpler model);
- declaring a concern exhausted.

Python (`domains/prediction_world.py`) handles the mechanical parts:
- simulating levels;
- writing observations onto `Body` nodes;
- measuring surprise;
- replaying the agent's own recorded episodes for a requested experiment, through fresh agents holding only the predictor seed.

The judge is weighed, not protective. A trial is supported when two conditions hold:
- it cuts surprise at the level by `min_gain` (20%);
- its gain, net of the surprise it adds on each level already mastered (summed per level, `retention_weight` 1.0), is at least 0.05.

Harm elsewhere is a cost to trade against, not a veto.

## Limits

- The hypothesis grammar is human-designed. It has three forms (velocity `x+dx`, acceleration `x+2dx−pdx`, ratio `x+dx²/pdx`) times reflect-at-walls, giving six `PredictorCandidate`s with an MDL rank. The agent chooses, tests and adopts within that grammar. It does not author new forms.
- The ceiling is the grammar's, and the agent reports it honestly:
  - L4 (damped glide) needs the ratio model, which scores 0.0 there. But ratio adds 0.78–1.28 cells of surprise summed over L2/L3 (its retention harm), so every trial is refuted and the concern is marked exhausted.
  - L5 (bounce under gravity) is mastered by no single candidate. The best is about 0.55.
  - Getting further needs models the grammar cannot express, such as context-conditioned or mixed models.
- The L2 regression is a weighed trade. Adopting acceleration+reflect raised L2 surprise from about 0.12 to 0.345 (fresh-episode means) and cut L3 from 0.5 to 0. The judge counted that cost (retention harm 0.20) and still found the trade worth it. L2 stays mastered by the curriculum's record, but the final model is above the floor there.
- The harness runs in-process (`WorldAdapter`), not in the daemon. Replays use fresh in-process agents.
- The worlds are deterministic and small: 3 bodies, 15–40 frames. Live episodes use unseen seeds, while trials replay the agent's own recorded episodes.

## Next

Let the agent extend its own grammar, using P5-style operator authorship. For example, it could compose a model conditioned on context (wall contact, sign of `dx·pdx`) or a mixture of models. The L4 exhausted concern is the endemic supply for that, and the same off-arm comparison applies.
