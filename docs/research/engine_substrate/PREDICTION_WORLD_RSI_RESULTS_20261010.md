# Prediction world: endemic self-improvement with an off-arm counterfactual (2026-10-10)

Plan: `OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md`. Redirect from the persona-chat work: demonstrate endemic self-improvement in any domain, not a chatbot.

## Result (1.1.0: the agent authors its own models)

Over 60 episodes, an agent that is allowed to change its own predictor climbs from level 1 to level 5 and masters levels 1–4. It does this by working out its own surprise, running its own trials, judging them against its own bar, and adopting the best trade. At level 4 every model it had was refuted, so it authored a new one: a composite of its current model and the trial that had won locally but cost too much elsewhere. It tried that model, adopted it and mastered the level.

The same agent with self-change switched off (`PredictionPolicy.self_improvement = 0`) still notices it keeps missing and files the concern. It cannot act on it, so it stays at level 2 for good.

The seed bases 1000, 2024, 5000 and 9000 gave different episodes and trial numbers but the same outcome.

| | on (1.1.0) | on (1.0.0, no authoring) | off |
|---|---|---|---|
| final level / mastered through | 5 / 4 | 4 / 3 | 2 / 1 |
| experiments / adoptions / authored models | 22 / 3 / 1 | 15 / 2 / 0 | 0 / 0 / 0 |
| final model | acceleration+reflect \| ratio | acceleration+reflect | velocity |
| concerns | L2–L4 resolved, L5 exhausted | L2–L3 resolved, L4 exhausted | L2 open |
| held-out surprise L1–L5 (cells) | 0, 0.380, 0.023, 0, 0.575 | 0, 0.366, 0, 0.280, 0.562 | 0, 0.445, 0.5, 0.652, 0.971 |

The held-out surprise is the final model's mean over 5 fresh episodes per level (seeds 10⁶+), which no live episode uses.

Trajectory (on arm, seed base 1000):
1. L2 (bounce): velocity → velocity+reflect, net 0.209.
2. L3 (fall): → acceleration+reflect, net 0.300. It beat plain acceleration (net 0.076, also supported) because plain acceleration loses the bounce on L2.
3. L4 (glide): all five base alternatives were refuted. Ratio is exact at L4 (variant 0.000 vs control 0.281), but it adds 1.28 cells on mastered levels, so the concern exhausted.
4. The agent then authored `acceleration+reflect | ratio`. Its components are its current model and its best local trial, and for each body and axis it uses whichever component predicted best last frame. That trial scored 0.277 → 0.000 at L4 with retention harm 0.043 (net 0.234). It was supported and adopted, and L4 was mastered.
5. L5 (bounce under gravity): all six alternatives were refuted, and no trial cleared the bar at the level. With no local winner there is nothing to compose, so the concern is honestly exhausted.

A run takes about 4 s per arm. Reproduce with `evaluation/substrate_capability/prediction_world_rsi_v1.py 60 <seed_base>`. The test is `tests/test_prediction_world_migrated.py`.

## What the graph decides and what is mechanical

The graph decides everything below. These are rules in `seeds/prediction_world.json` and in `seeds/prediction_self_improvement.json`, which is frozen and has its types protected by `improvement_integrity`:
- the prediction itself (`predict_body_next`, including per-body, per-axis component selection);
- mastery and level advance;
- filing a surprise concern;
- proposing one experiment per untried candidate;
- the judge;
- adoption (best `weighed_net`, with ties going to the simpler model);
- declaring a concern exhausted;
- authoring a composite (`pw_author_composite_predictor`): when to author, which components to compose, its rank and name, and reopening the concern.

Python (`domains/prediction_world.py`) handles the mechanical parts:
- simulating levels;
- writing observations onto `Body` nodes;
- measuring surprise;
- replaying the agent's own recorded episodes for a requested experiment, through fresh agents holding only the predictor seed.

The judge is weighed, not protective. A trial is supported when two conditions hold:
- it cuts surprise at the level by `min_gain` (20%);
- its gain, net of the surprise it adds on each level already mastered (summed per level, `retention_weight` 1.0), is at least 0.05.

Harm elsewhere is a cost to trade against. The authoring rule follows from that. A trial that wins at the level but loses on retention is evidence of a model that is right somewhere, and composing it with the current model keeps both.

## Limits

- The building blocks are human-designed. These are the six base models (velocity `x+dx`, acceleration `x+2dx−pdx`, ratio `x+dx²/pdx`, each with or without reflecting at walls) and the one composition operator: per body and axis, select the component with the lowest last-frame error.
  - The agent decides when to compose and what to compose, from its own refuted trials. It cannot invent new base forms or new operators.
  - The composite space is finite (2⁶ masks), and authoring never repeats a mask, so it always terminates.
- L5 is the current ceiling. No base model or composite tried cuts L5 surprise by 20%; the best is about 0.55. Bounce under gravity needs something the blocks cannot express, for example reflection that conserves the vertical velocity under acceleration.
- L2 is above the floor under the final model (0.38 held-out vs floor 0.15). Each adoption traded some L2 accuracy for a larger gain elsewhere, and the judge counted it each time (retention harm 0.20, then 0.04). L2 stays mastered by the curriculum's record only.
- The harness runs in-process (`WorldAdapter`), not in the daemon. Replays use fresh in-process agents.
- The worlds are deterministic and small: 3 bodies, 15–40 frames.

## Next

The L5 exhausted concern has no local winner, so composition has no evidence to work from. The next rung is letting the agent author a new base form from its own residuals: for example, fitting the structure of its error at L5 (wall contact under gravity) into a new term, under the same judge and the same off-arm comparison.
