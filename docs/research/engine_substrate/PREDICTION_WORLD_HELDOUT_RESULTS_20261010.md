# Prediction world: held-out levels and the cost of improvement (results, 2026-10-10)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_20261010.md`, pre-registered and frozen at `028188587e03bed585bacfc608dfac7609f56b10`. That commit's hash drew the 8 levels. Nothing was changed after the pre-registration commit.

To reproduce:

```
evaluation/substrate_capability/prediction_world_heldout_v1.py 028188587e03bed585bacfc608dfac7609f56b10
```

There are 128 runs, about 25 minutes on 4 workers.

## Outcome against the predictions

- **H1 (the loop generalises): supported, narrowly.**
  - `on_trained` mastered 12/32 runs; `no_authoring_trained` and `off_trained` mastered 8/32 each.
  - The whole margin is one level, 108. That is bounce under gravity (g 0.279, box 36, restitution 1), the held-out level closest to curriculum L5. There `on_trained` mastered 4/4 and both ablations 0/4.
- **H2 (prior self-improvement lowers the cost of the next): supported by the letter, not in substance.**
  - Of 12 pairs, trained needed fewer episodes in 4 and naive in 0; 8 were ties.
  - The 4 wins are all on level 108, where the trained agent mastered at the minimum of 3 episodes with **zero** experiments. Its curriculum model already fitted, so this is transfer, not cheaper improvement.
  - The 8 ties are levels 103 and 104, where every arm, including off, masters in 3 episodes. Nothing needed improving there.
- **Unpredicted, and against the spirit of H2: the newborn did better.**
  - `on_naive` mastered 15/32, more than `on_trained`'s 12.
  - On level 105 (box 40, downward and sideways gravity, restitution 0.9) naive mastered 3/4 and trained 0/4.

| level | physics | on_trained | no_authoring | off | on_naive | best base model |
|---|---|---|---|---|---|---|
| 101 | box 29, g 0.57, gx −0.23, restitution 0.74 | 0/4 (0.35) | 0/4 (0.70) | 0/4 (1.03) | 0/4 (0.66) | 0.66 |
| 102 | box 22, g 0.62, damping 0.19, restitution 0.62 | 0/4 (0.63) | 0/4 (0.83) | 0/4 (0.74) | 0/4 (0.45) | 0.45 |
| 103 | open, nothing (drift) | 4/4 | 4/4 | 4/4 | 4/4 | 0 |
| 104 | open, gx 0.10 | 4/4 | 4/4 | 4/4 | 4/4 | 0 |
| 105 | box 40, g 0.40, gx 0.36, restitution 0.9 | 0/4 (0.19) | 0/4 (0.64) | 0/4 (1.11) | **3/4** (0.13; 12–21 ep) | 0.64 |
| 106 | box 30, g 0.12, damping 0.24 | 0/4 (0.42) | 0/4 (0.53) | 0/4 (0.54) | 0/4 (0.40) | 0.40 |
| 107 | box 21, g 0.38, gx 0.12, restitution 0.75 | 0/4 (0.21) | 0/4 (0.48) | 0/4 (0.77) | 0/4 (0.32) | 0.46 |
| 108 | box 36, g 0.28 | **4/4** (0.09; 3 ep) | 0/4 (0.34) | 0/4 (0.63) | 4/4 (0.12; 9 ep) | 0.34 |

Cells show runs mastered out of 4 seed bases, with the final model's mean surprise on fresh episodes in brackets (the floor is 0.15). Levels 101, 102, 106 and 107 were mastered by no arm.

## Why the trained agent lost plasticity

The trained agent requested **no residual fits on any held-out level**:
- Its curriculum model already uses both context-layer slots.
- Each atom may be used once per model.
- The layer coefficients, fitted to curriculum physics (gravity 0.5, perfect bounces), cannot be refitted.

So its only moves were swapping in base models or composites. Against five mastered levels, the retention weighing refuses most of those, which is correct by its own criterion. The naive agent has empty slots and nothing to protect, so it fits the new physics directly.

This shows the improvement process has no operator for revising what it built. What it accumulated helps where the new world resembles the old one: the trained agent's final surprise is lower than the newborn's on levels 101, 107 and 108. It blocks mastery where the new world needs different coefficients: on 102, 105 and 106 the newborn ends lower.

## What this says about the original question

- **It strengthens one claim.** The loop's products transfer to unseen physics, and the effect is causal: `on_trained`'s surprise is lower than both ablations on every non-trivial level. That claim is pre-registered and blind to tuning.
- **It does not support compounding.** The prior self-improvement made later improvement cheaper only where no improvement was needed. It made improvement impossible where it was needed.
- **It is not recursive self-improvement.** The improver is frozen, and the accumulated state reduced plasticity rather than raising it.

## Limits

- 8 levels × 4 seed bases, all deterministic.
- 4 of the 8 levels are unmasterable by any arm, and 2 are trivial, so only 2 levels discriminate.
- I wrote the physics family; the hash chose the draw.
- This draw has now been seen. It is a development set from here on, and any change motivated by it must be tested on a fresh pre-registered draw.

## Next

The concrete gap is an operator that revises the agent's own authored structure. For example:
- refitting a layer's coefficients when its own residual on the current level says the layer is wrong;
- replacing a layer, instead of using each atom once per model.

That change is motivated by this draw, so its test needs a new pre-registration and a new draw. It would then be fair to measure whether the trained agent beats the newborn on new levels, which is the real compounding test.
