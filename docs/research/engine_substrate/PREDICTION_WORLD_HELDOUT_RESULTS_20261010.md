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


---

# v3: many draws, robust mastery, learned search (loop 1.4.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V3_20261010.md`, frozen at `c06ac6e48700c93ae69f76c7e8c7fd41e254365c`. There were 6 fresh draws × 8 levels × 4 seed bases, giving 192 pairs and 768 runs. Nothing was changed after the commit.

To reproduce:

```
evaluation/substrate_capability/prediction_world_heldout_v2.py c06ac6e48700c93ae69f76c7e8c7fd41e254365c 6
```

This takes about 30 minutes on 12 workers.

## Pre-registered outcome

| arm | robust mastery | mean final surprise | mean experiments/run | adoptions |
|---|---|---|---|---|
| `on_trained` (own record) | 128/192 | 0.162 | **11.0** | 29 |
| `on_trained_reset` (record zeroed) | 129/192 | 0.159 | 15.5 | 30 |
| `on_trained_flat` (meta search off) | 129/192 | 0.159 | 17.6 | 30 |
| `on_naive` | 122/192 | 0.187 | 12.1 | 220 |

**H4: supported (the agent's own record makes later improvement cheaper, at no cost in quality).**
- **(a)** The learned record used fewer experiments than the reset record in 79 pairs, and more in none. The other 113 pairs needed no trials at all. The sign test gives p < 10⁻²³.
  - Over the 79 pairs with trials: 2,110 experiments vs 2,970 reset (−29%) and 3,372 flat (−37%).
- **(b)** Mean final-surprise difference, learned − reset: +0.0023, within the +0.01 margin.
  - That whole difference is one pair (see below). Of the other 191 pairs, 190 are identical.
- **H4b (vs no meta search): the same picture.** 79 vs 0 on experiments; surprise difference +0.0022, with 186 of 192 pairs tied.

**H3: falsified (trained vs newborn).** The trained agent had lower final surprise in 87 pairs and the newborn in 93, with 12 ties (p = 0.71).
- The mean favours the trained agent (−0.025), because it wins by large margins on hard levels. But pair for pair it does not beat the newborn.
- Robust mastery is 128 vs 122, also not significant (17 vs 11 discordant pairs, p = 0.34).

## What produced it (post-hoc analysis)

**The cost of learned search.**
- In the curriculum, base models were supported 3 times in 35 trials. So on new levels the agent skips them (the skip rule: tried at least 8 times, yield under 0.15).
- That removes trials whose answer would have been "refuted" anyway. That is the 29–37% saving.
- In one pair (draw 4, level 139: open space, g 0.76, gx 0.30; seed 1000), it also removed the one useful path:
  - the composition operator builds from a refuted base trial;
  - with base trials skipped, it never formed `current | acceleration`;
  - the reset and flat arms did form it, and reached 0.025;
  - the learned arm stayed at 0.466.
- The skip rule treats operators as independent, and they are not. One pair in 192 is cheap on average, but it is a real failure mode, not noise.

**Why the trained agent does not beat a newborn.**
- The trained agent adopted something new in only 26 of 192 runs (29 adoptions, about 73 experiments per adoption). The newborn adopted 220 times, about 11 experiments per adoption.
- The trained agent starts closer (initial surprise 0.196 vs the newborn's 0.553), but it improves little at the level: 0.196 → 0.161. The newborn goes 0.553 → 0.187.
- Every change the trained agent considers is weighed against five mastered levels (retention). On the levels it does change, it ends lower than the newborn on average (0.486 vs 0.577). Where it does not change, the newborn, free of retention, often fits the new physics more closely in small steps.
- Draws differ: trained wins draws 2 and 5 on pair counts, the newborn wins 1 and 3, and 0 and 4 are close. Eight-level single-draw verdicts (v1, v2) were not reliable, as v2's write-up warned.

## Where the whole line stands

**Established, pre-registered and blind to tuning:**
1. **The object-level loop works on unseen physics.** Agents that may change themselves beat ablations that may not (v1, v2).
2. **The improver's behaviour improves with its own experience** (v3, H4). The record of what paid off in the curriculum makes its search on new levels a third cheaper, with no change in outcome in 191 of 192 cases.
   - This is the first evidence in this line at the meta level.
   - The meta rules are human-written and frozen; what is learned is the record that steers them.

**Not established:**
- **That earlier object-level improvement leaves the agent better placed than a newborn** (H3 falsified over 192 pairs). The retention trade, which is correct by the agent's own criterion, makes the experienced agent conservative on new physics.
- **Open-ended recursive self-improvement.** The agent re-weights operators it has. It cannot invent a new way to search, and the skip rule's independence assumption is a human design error the agent cannot see or fix.

**Next, if this line continues:**
- Let the record see dependencies between operators, e.g. count a composition's adoption as credit for the base trial it was built from. Better still, let the agent propose changes to its own meta rules under the same pre-registered, many-draw judge.
- Make retention scope-aware, so a model change can be confined to the frames it was fitted on. This is the likely route to an experienced agent that is not out-learned by a newborn.


---

# v4: experts, provenance credit, self-proposed policy (loop 1.5.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V4_20261010.md`, frozen at `37decde1b9f6f4ac0f536b88496d67211fb81a7a`. There were 6 fresh draws × 8 levels × 4 seed bases, giving 192 pairs and 960 runs, plus the practice phase. Nothing was changed after the commit.

To reproduce:

```
evaluation/substrate_capability/prediction_world_heldout_v3.py 37decde1b9f6f4ac0f536b88496d67211fb81a7a 6
```

## Pre-registered outcome

| arm | robust mastery | mean final surprise | mean retention harm | mean experiments |
|---|---|---|---|---|
| `on_trained` | 134/192 | 0.116 | 0.010 | 17.2 |
| `on_trained_noexperts` | 132/192 | 0.118 | 0.010 | 16.6 |
| `on_trained_reset` | 134/192 | 0.116 | 0.010 | 17.2 |
| `on_trained_meta` | 134/192 | 0.119 | 0.009 | 16.6 |
| `on_naive` | 138/192 | 0.146 | 0 | 10.5 |

**H3: supported on this draw set, but not because of 1.5.0.**
- Trained vs newborn: 105 vs 71 with 16 ties (p = 0.013).
- Counterfactual (not pre-registered): loop 1.4.0 on the same draws gives 106 vs 70 (p = 0.008). The difference from v3 (87 vs 93) is the draws.
- Pooled over v3 and v4 for loop 1.4.0: 193 vs 163, p = 0.12, not significant.
- Draws vary: in v4, trained wins draws 0, 1 and 5 clearly, ties 2 and 4, and loses 3.

**H6: falsified, narrowly.**
- Experts lowered final surprise in 5 pairs and raised it in none (p = 0.0625 against α = 0.05).
- Retention harm was unchanged.
- Each of the 5 is a real improvement: 0.184 → 0.118, 0.087 → 0.062, 0.168 → 0.116, 0.169 → 0.104, 0.167 → 0.105. But experts are authored only as a last resort, so they rarely act.

**H4: falsified.**
- Learned vs reset record: identical in all 192 pairs.
- 1.5.0's two fixes to the skip rule removed the saving v3 found:
  - credit through provenance gives base models `enabled` credit in every curriculum, so they are never skipped;
  - skipping became a last resort.
- 1.4.0 on the same draws keeps the saving: 76 vs 0 pairs, −4.4 experiments per run, identical outcome.
- So 1.5.0 traded v3's 29% saving for not repeating v3's one bad skip. On the v4 draws, 1.5.0's trained agent used 64% more experiments than 1.4.0's (17.2 vs 10.5). In exchange it was better in 5 pairs (the expert wins) and worse in none.

**H5: falsified.**
- The agent adopted a policy change on only 1 of 4 seed bases: base 1000, `retention_weight` ×2, practice net +0.083. The practice judge refuted every other proposal, so the other bases are ties by construction.
- On the held-out draws that change was worse in 3 pairs and better in none (p = 0.25). A heavier retention weight made the agent more conservative: on those levels final surprise rose by 0.16–0.25, while retention harm fell by about 0.08.
- Its own practice evidence (6 levels, with most of the net from one level) did not transfer.

## Where the whole line stands now

**Holds, pre-registered:**
- The self-improvement loop beats ablations that cannot change themselves (v1, v2).
- The agent's own operator record made its search a third cheaper without changing outcomes (v3, loop 1.4.0). This was replicated on the v4 draws by the 1.4.0 counterfactual: 76 vs 0 pairs.

**Does not hold, or is not established:**
- **Trained vs newborn.** Draw-dependent. v3 and v4 point opposite ways, and the pooled result is not significant.
- **Experts as scope-confined change.** Each use helps, but they are too rarely used to pass a test (5/192).
- **The agent's own policy proposals.** One round, from 6 practice levels, adopted on 1 of 4 bases, and it did not transfer.
- **v4 lost the v3 saving.** Making the skip rule safe removed it. Safety and cost trade against each other here, and both v3 and v4 measured one side of that trade.

**Recursive self-improvement.** The tests have now reached the meta level twice:
- v3: a learned record steering a fixed search. That passed.
- v4: self-chosen policy changes. That failed to transfer.

The part that passed is the shallow one. The agent improving its way of improving, in a way that holds on unseen worlds, has not been shown.

**What I would do next, if this line continues:**
- **Separate the safety question from the saving.** For example, skip an operator only when no other operator has ever built on it *in a world of the same kind*.
- **More practice and more rounds for self-proposed policy.** Several rounds, each judged on practice levels never reused. The current single round on 6 levels is too thin to learn from.
- **Stop using one sign test per hypothesis per draw set.** Use a pooled, pre-declared sequential analysis across draw sets. The draw-to-draw variance seen here is larger than most of the effects being tested.


---

# v5: per-kind record, rounds of self-proposed policy, sequential analysis (loop 1.6.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V5_20261010.md`, frozen at `26cd9cf8a8b8ed66dadb11f65241ff9e9fd9e0d8`. There were two six-draw sets (A: draws 0–5, B: draws 6–11) × 8 levels × 4 seed bases, giving 384 pairs and 1,920 runs, plus the three-round practice phase. Nothing was changed after the commit.

To reproduce:

```
prediction_world_heldout_v4.py <hash> 0 6
prediction_world_heldout_v4.py <hash> 6 12 <meta.json>
prediction_world_sequential_analysis.py <A> <B>
```

## The agent's own policy rounds (phase 1)

On every seed base the agent adopted a change in each of its 3 rounds. Each change was supported by its weighed net and by winning on more fresh practice levels than it lost.

| seed base | adopted policy changes, in order | final policy |
|---|---|---|
| 1000 | `meta_min_yield` ×2; `meta_min_trials` ×0.5; `min_gain` ×0.5 | yield 0.3, trials 4, min_gain 0.1 |
| 2024 | `meta_min_trials` ×0.5; `retention_weight` ×0.5; `retention_weight` ×2 | net: trials 4 |
| 5000 | `meta_min_trials` ×0.5; `meta_min_yield` ×2; `meta_min_yield` ×2 | yield 0.6, trials 4 |
| 9000 | `min_gain` ×0.5; `meta_min_yield` ×2; `meta_min_trials` ×0.5 | yield 0.3, trials 4, min_gain 0.1 |

The common direction is clear: skip low-yield operators sooner, and on a stricter yield bar.

## Pre-registered verdicts (Pocock, p < 0.0294 per look)

| hypothesis | look 1 (192 pairs) | look 2 (384 pairs) | verdict |
|---|---|---|---|
| H3 trained beats newborn (final surprise) | 107–77 (p = 0.032) | 194–170 (p = 0.23) | **not supported** |
| H4 per-kind record cheaper and safe | experiments 74–0; surprise identical in all 192; 0 big losses | 168–0; surprise 4–1, mean −0.0003; 0 big losses | **supported at look 1** |
| H5 its own policy rounds pay (weighed cost) | 76–0 | 168–5 | **supported at look 1** |
| H6 experts help (final surprise; harm ≤ +0.01) | 12–0; harm +0.001 | 24–0; harm +0.002 | **supported at look 1** |

**Per set:**
- H4 and H6 hold in both sets on their own: H4 74–0 and 94–0; H6 12–0 and 12–0.
- H3 splits again: A 107–77, B 87–93.

## What is behind each verdict (post-hoc analysis, not pre-registered)

**H4: real and safe.**
- The per-kind record cuts experiments by 4–6 per run, about 25–26% of the reset arm's.
- No pair is worse by more than 0.1, and final surprise is unchanged.
- The v3 trade between cheap and safe is gone at this sample size.

**H6: real, small in aggregate, large where it acts.**
- Experts act in 24 of 384 pairs and help in all of them. Typical improvements: 0.24 → 0.15, 0.23 → 0.14, and on one level (171) 0.56 → 0.16 on all 4 seed bases.
- They add a little retention harm (mean +0.002), inside the pre-declared margin.

**H5: supported by the rule, but the benefit is mostly cheaper search, and it has a tail.**
- The adopted policies cut experiments by 7–9 per run (about half).
- **Set A:** final surprise improved slightly (mean −0.0007), with no pair worse by more than 0.05.
- **Set B:** 5 pairs were much worse, on levels 164 (all 4 seed bases) and 168.
  - On those, the stricter policy did not adopt the fix the default policy found: final surprise about 0.35 → 1.0–1.1.
  - The default policy's fix itself cost 0.31–0.39 in retention harm.
  - So set B's mean weighed cost improved by only 0.0006, and its mean final surprise got worse by 0.018.
- The pre-declared test counts pairs, not magnitudes. It passes with many small savings against a few large losses. That is the same pattern as v3's single bad skip, now produced by the agent's own policy choices.

**H3: not supported.** After 384 pairs, trained vs newborn is 194–170. Prior object-level self-improvement leaves the agent more often ahead than behind, but not reliably.

## Where the line stands

**Pre-registered and replicated across draw sets:**
1. The loop beats ablations that cannot change themselves (v1, v2).
2. The agent's own record of what pays makes its search much cheaper at no loss of quality, now safely: per kind of world, with credit for what operators enable (v3 and v5 H4).
3. Scope-confined experts improve the levels where they act, at a small retention cost (v5 H6).
4. Over three rounds, on fresh practice levels, the agent's own changes to its search policy pay on the pre-declared weighed cost (v5 H5). Mostly they make the search cheaper, at the cost of occasional large misses on hard levels.

**Not established:**
- That an experienced agent beats a newborn on new physics (H3).
- That the agent's policy changes improve quality rather than cost. They don't on average.
- Open-ended recursive self-improvement. Every operator, grammar, partition and judge is human-written and frozen. What the agent changes at the meta level is a few parameters, chosen from a human-written grammar of changes.

**If this continues, the evident next step** is for the practice judge to weigh tail risk, not just mean net and level counts. For example, a policy change must not lose more than X on any practice level. That is exactly the failure v5 set B shows, and the agent's own judge did not see it. Beyond that, the remaining gap to the original goal is the agent authoring its own operators and judges rather than choosing among mine.


---

# v6: the agent selects its own judge (loop 1.7.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V6_20261010.md`, frozen at `f610f3312a38461eeeb7ea181c039740444501da`. There were two six-draw sets, giving 384 pairs × 3 arms, plus two practice phases. Nothing was changed after the commit. The analysis is `prediction_world_sequential_analysis_v6.py <A> <B>`.

## Practice phase

**The selected judge.** On all four seed bases the agent selected `tail`, but only on a tie.
- On each base, the best supported round-0 proposal was the same under all three judges. Its realised P2 net was the same for each: 0.057, 0.021, 0.032 and −0.001.
- The tie rule chose the stricter judge.

**What it adopted.** Under `tail` it adopted exactly the changes the fixed `sign` judge adopted. These are also v5's changes, since the curriculum and the practice seeds are the same:
- `meta_min_trials` ×0.5 everywhere;
- `meta_min_yield` ×2 on three bases;
- `min_gain` ×0.5 on two.

No practice level showed a single-level loss above 0.05 for any supported proposal, so the tail limit never bound.

## Pre-registered verdicts

| hypothesis | look 1 (192) | look 2 (384) | verdict |
|---|---|---|---|
| H5t self-judged policy pays, without a tail | sign 49–4 (p < 10⁻¹⁰); mean −0.0018 (p = 0.51); big losses 2 | sign 109–4; mean −0.0035 (p = 6·10⁻⁵); big losses 2 (≤ 3 allowed) | **supported at look 2** |
| H8 self-selected judge beats the fixed one | identical in all 192 | identical in all 384 | **not supported** |

**Per set (H5t):** A 49–4, mean −0.0018, 2 big losses; B 60–0, mean −0.0052, 0 big losses.

## What is behind it (post-hoc analysis)

**H5t: the improvement is the trade the policy makes.** Mean differences, meta − trained:

| component | difference |
|---|---|
| experiments | −5.1 per run, about −56% |
| retention harm | −0.0035 |
| final surprise | +0.005, slightly worse |

- At the pre-declared price of 0.001 per experiment, the net is a small, reliable gain.
- The two big losses are one level (draw 4, level 133) on two seed bases. The stricter policy declined a fix the default made, which cost the default 0.30–0.41 in retention harm. Final surprise there went 0.68–0.77 → 1.32–1.45.
- These are the v5 tail, now inside the 1% allowance.

**H8: the judge choice was real but inconsequential.**
- The agent's own calibration could not tell the judges apart: none of the proposals it would adopt had a heavy single-level loss on practice.
- On these practice draws, no judge choice could have changed anything. The tail v5 saw on held-out level 164, and v6 on level 133, does not appear on the agent's practice levels.

## Where the line stands

**Pre-registered, replicated, and now magnitude-tested:**
- The agent's own operator record makes its search much cheaper at no loss of quality (v3, v5).
- Experts help where they act (v5).
- Its own rounds of policy change pay on the declared weighed cost, by sign and by mean, with the tail inside the declared allowance (v5 sign test; v6 sign and mean).

**Not shown:**
- That choosing its own judge matters (v6 H8). The agent did choose, from its own out-of-sample evidence. But its practice never contained the kind of case the choice would decide.
- That the experienced agent beats a newborn (v3–v5).
- Open-ended recursive self-improvement. The agent now adapts its search record, its search policy, and its judge, each from its own evidence and each validated on unseen worlds. But it does so by choosing among human-written options, and its practice distribution is too narrow to expose the rare failures the held-out levels contain.

**The concrete gap this exposes:** practice levels that resemble the worlds where the agent's choices fail. For example, the agent could search its own practice family for levels where proposals disagree most. That would be the agent shaping its own curriculum for self-evaluation.


---

# v7: the agent shapes its own practice (loop 1.8.0)

The protocol is `PREDICTION_WORLD_HELDOUT_PROTOCOL_V7_20261010.md`, frozen at `1fc1b2cbcc83da15f4dbe346da2c55f0f34ec826`. There were two six-draw sets, giving 384 pairs × 3 arms, plus two calibrated practice phases. Nothing was changed after the commit. The analysis is `prediction_world_sequential_analysis_v7.py <A> <B>`.

## Practice phase

**Random practice** reproduced v6 exactly: the same judges (`tail` on ties) and the same adopted policies.

**Shaped practice changed what the agent adopted.** On 3 of 4 seed bases the policy differs from the random-practice policy:

| seed base | shaped-practice changes |
|---|---|
| 1000 | `meta_min_yield` ×2 ×2 and `meta_min_trials` ×0.5, instead of `min_gain` ×0.5 |
| 2024 | adds `meta_min_yield` ×2, and ends with `retention_weight` ×2 |
| 9000 | `retention_weight` ×0.5, instead of `min_gain` ×0.5 |
| 5000 | identical |

**The selected levels were more contested.**
- On seed 1000 round 0, the selected spreads were 0.04–0.39, where random levels often had 0.
- Proposals' P1 nets were larger in both directions, e.g. −0.36, +0.16, −0.17.

**The judge choice was still decided by ties.** All three judges' best supported proposal was the same on every base. The tail limit still never bound on what the agent would adopt.

## Pre-registered verdicts

| hypothesis | look 1 (192) | look 2 (384) | verdict |
|---|---|---|---|
| H5s shaped-practice policy pays, without a tail | sign 97–4; mean −0.0094 (p = 5·10⁻⁶); 0 big losses | sign 149–15; mean −0.0020 (p = 0.37); 7 big losses | **supported at look 1** |
| H9 shaped practice beats random practice | sign 40–11; mean +0.0004 (p = 0.65) | sign 67–17; mean +0.0001 (p = 0.85) | **not supported** |

By the pre-declared rule, H5s was decided at look 1 and stays supported. **That verdict must not be read alone.**

## Set B reverses set A (post-hoc analysis)

| comparison | set A mean cost | set B mean cost | set B big losses |
|---|---|---|---|
| shaped-practice policy − trained | −0.0094 | **+0.0054** | 7 |
| random-practice policy − trained (the v6 policy) | −0.0098 | **+0.0055** | 7 |

- In set B both policy arms lose on mean cost, with 7 pairs each worse by more than 0.1. That is the tail again, above the 1% allowance.
- Pooled over both sets, neither passes the mean test (p = 0.33–0.37).
- Over all 384 pairs, the components are the same trade as before:

| component | random − trained | shaped − trained |
|---|---|---|
| experiments per run | −7.3 | −8.4 |
| retention harm | −0.006 | −0.005 |
| final surprise | +0.011 | +0.012 |

**H9.** Shaped practice made different choices and won more pairs than random practice (67–17). But the per-pair differences are tiny and cancel in the mean: +0.0001 overall, and per seed base between −0.0021 and +0.0023.

## The policy-change result across every draw set so far

Mean weighed cost of the agent's own policy vs the born policy:

| draw set | mean cost difference |
|---|---|
| v5 A | −0.0072 |
| v5 B | −0.0006 |
| v6 A | −0.0018 |
| v6 B | −0.0052 |
| v7 A | −0.0098 |
| v7 B | **+0.0055** |

- The policy changes the agent chooses for itself usually pay a little on the declared weighing. They do it by searching about half as much and protecting mastered levels a little more, at a small cost in new-level surprise.
- In 1 of 6 draw sets the occasional hard level where they decline a needed fix outweighs that. Three mechanisms aimed at that tail have failed to remove it:
  - a level-count judge (v5);
  - self-selected judges (v6);
  - self-shaped practice (v7).
- The agent's practice evidence never shows the tail on what it would adopt, so nothing it can choose among sees it.

## Where the line stands

**Holds across draw sets:**
- The loop beats ablations.
- The per-kind operator record makes search much cheaper at no quality cost.
- Experts help where they act.

**Mixed:**
- The agent's own policy changes pay on most draw sets, but not all, and carry a tail its self-evaluation cannot see.

**Not shown:**
- That self-chosen judges or self-shaped practice improve on the defaults.
- That an experienced agent beats a newborn.
- Open-ended recursive self-improvement.

**Assessment.** The meta-level machinery now has every piece I proposed: learned record, experts, self-proposed policy, self-selected judge, self-shaped practice. The meta-level gains that hold are about cost, not capability. The remaining failure (a rare, large miss on a hard level) is invisible to every piece of evidence the agent generates for itself. More selection among human-written options is unlikely to fix that.

The two plausible directions are:
- letting the agent author new options (operators, features), so the hard levels become solvable rather than merely avoidable;
- changing the frame, so the agent experiences the hard levels it currently declines, e.g. a curriculum that keeps escalating rather than one that stops at five levels.
