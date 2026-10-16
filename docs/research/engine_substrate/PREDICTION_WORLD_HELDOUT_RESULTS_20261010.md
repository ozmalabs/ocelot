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


---

# v2: after revision (loop 1.3.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V2_20261010.md`, frozen at `4916f117873fbacf6a454c5b5ac2b97d0fa2bbd6`, whose hash drew a fresh set of 8 levels. Nothing was changed after that commit.

To reproduce:

```
evaluation/substrate_capability/prediction_world_heldout_v1.py 4916f117873fbacf6a454c5b5ac2b97d0fa2bbd6
```

## Pre-registered outcome

| arm | mastered (of 32) | mean final surprise |
|---|---|---|
| `on_trained` | **22** | 0.169 |
| `no_authoring_trained` | 8 | 0.318 |
| `off_trained` | 4 | 0.485 |
| `on_naive` | 9 | 0.234 |

- **H1: supported.** 22 > 8 and 22 > 4.
- **H3: supported on both clauses.**
  - Mastery: 22 vs 9.
  - Final surprise: the trained agent ended lower than the newborn in 26 of 32 pairs, and the newborn lower in 6.
- **H2 (reported as before).** Of 9 pairs where both mastered, trained needed fewer episodes in 5, naive in 0, and 4 were ties.

| level | physics | on_trained | no_authoring | off | on_naive |
|---|---|---|---|---|---|
| 101 | box 25, g 0.37, damping 0.07, restitution 0.83 | 0/4 (0.56) | 0/4 (1.00) | 0/4 (1.22) | 0/4 (0.63) |
| 102 | box 24, g 0.19, restitution 0.95 | **4/4** (0.09) | 0/4 (0.29) | 0/4 (0.49) | 1/4 (0.24) |
| 103 | open, g 0.50 | 4/4 | 4/4 | 0/4 | 4/4 |
| 104 | box 34, g 0.47, damping 0.34 | 2/4 (0.19) | 0/4 (0.31) | 0/4 (0.34) | 0/4 (0.22) |
| 105 | box 15, gx 0.18 | 2/4 (0.14) | 0/4 (0.41) | 0/4 (0.61) | 0/4 (0.32) |
| 106 | box 25, g 0.12, restitution 0.80 | **4/4** (0.10) | 0/4 (0.19) | 0/4 (0.32) | 0/4 (0.19) |
| 107 | open, g 0.61, damping 0.33 | 4/4 | 4/4 | 4/4 | 4/4 |
| 108 | box 28, gx −0.37, damping 0.32 | 2/4 (0.23) | 0/4 (0.33) | 0/4 (0.35) | 0/4 (0.22) |

Cells show runs mastered out of 4, with mean final surprise in brackets (the floor is 0.15).

## What produced it (post-hoc analysis, not pre-registered)

**Mostly transfer, not new improvement.**
- Of the 22 trained masteries, 19 ended on the agent's curriculum model unchanged.
- Only 3 came from adopting a revision at the held-out level:
  - level 104, seed 2024: a pooled reversal refit, 0.256 → 0.182;
  - level 108, seeds 1000 and 5000: a pooled joint refit, 0.33 → 0.20.

**Counterfactual on the same draw with loop 1.2.0 (no revision).**

| | 1.2.0 | 1.3.0 |
|---|---|---|
| `on_trained` mastered | 19 | 22 |
| `on_naive` mastered | 9 | 9 |
| pairs where trained ends lower vs naive lower | 20 vs 12 | 26 vs 6 |

So most of v2's trained-vs-newborn gap was already there before revision. This draw simply resembles the curriculum more than v1's did.

**Revision does real work at the level, but rarely to the floor.**
- On held-out levels, the trained agent adopted a revision in 9 of 32 runs: 101 ×4, 104 ×2 and 108 ×3.
- Each cut held-out surprise by 26–45%, e.g. 101: 0.74–0.80 → 0.55–0.60.
- All 9 are pooled refits of its own layers: fitted on the new level's frames together with the mastered levels' frames, so they win the retention trade.
- Only 3 of the 9 reached mastery.

**Some masteries are luck.** Mastery means three consecutive episodes at or under 0.15. Four trained masteries came after 19–26 episodes on a model whose held-out surprise is 0.14–0.21 (levels 104 and 105). They are a lucky run of episodes, not a better model. This is a weakness of the mastery criterion, and it applies to every arm.

## Across both draws

| | v1 draw | v2 draw |
|---|---|---|
| 1.2.0 trained vs newborn | 12 vs 15 | 19 vs 9 |
| 1.3.0 trained vs newborn | 12 vs 15 (dev set) | 22 vs 9 |

- Whether the trained agent beats a newborn depends heavily on the draw. With 8 levels per draw, a single level (v1's 105, v2's 102 and 106) moves the result.
- What holds on both draws is that the trained agent's final surprise is lower than the newborn's in most pairs: 22/32 on the v1 dev set, 26/32 on v2.
- The authoring and self-change ablations lose on both draws.

## What this establishes, and what it does not

**Established, pre-registered and blind to tuning:**
- The self-improvement loop's products generalise to unseen physics. The authoring and self-change ablations are clearly worse.
- With revision, an agent that has already improved itself also revises what it built, on its own evidence, on new physics. The surprise cuts are substantial, though they seldom reach mastery.

**Not established:**
- That earlier improvement makes later improvement cheaper as a general property. The trained agent's advantage is mainly transfer, and it is draw-dependent.
- Recursive self-improvement. The improver (judge, operators, mastery criterion) is frozen throughout. Everything measured here is object-level.

**Next, if this line continues:**
- More draws, to settle the trained-vs-newborn question statistically.
- A mastery criterion robust to lucky streaks.
- Then the meta-level: let the agent change parts of its own search, and measure the cost of improvement on fresh draws.
