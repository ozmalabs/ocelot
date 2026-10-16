# Prediction world: endemic self-improvement with an off-arm counterfactual (2026-10-10)

Plan: `OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md`. Redirect from the persona-chat work: demonstrate endemic self-improvement in any domain, not a chatbot.

## Result (1.2.0: the agent authors models from its own residual)

The same 60 episodes were run under three arms. The arms differ only in two `PredictionPolicy` attributes.

| arm | final level / mastered through | experiments | adoptions | models authored | held-out surprise L1–L5 (cells) |
|---|---|---|---|---|---|
| on | 5 / 5 | 39–56 | 5–6 | 3–4 | 0, 0.11–0.12, 0.03, 0, 0.14–0.15 |
| no_authoring (`authoring = 0`) | 4 / 3 | 15–20 | 2 | 0 | 0, 0.37, 0, 0.28, 0.56 |
| off (`self_improvement = 0`) | 2 / 1 | 0 | 0 | 0 | 0, 0.45, 0.5, 0.65, 0.97 |

- Ranges cover the seed bases 1000, 2024, 5000 and 9000. Every base gives the same level outcome for each arm.
- Held-out surprise is the final model's mean over 5 fresh episodes per level (seeds 10⁶+), which no live episode uses. The mastery floor is 0.15.
- The off arm still notices its surprise. Its L2 concern is filed and stays open.
- The no_authoring arm adopts from the six models it was born with and stops when they run out. Its L4 concern is exhausted.

Trajectory of the on arm (seed base 2024; the other bases are alike):
1. **L2 (bounce):** adopted velocity → velocity+reflect.
2. **L3 (fall):** adopted → acceleration+reflect.
3. **L4 (glide), composition:**
   - All base alternatives were refuted. Ratio is exact here but costs too much on L2/L3.
   - The agent authored `acceleration+reflect | ratio`: its current model plus its best local trial, using per body and axis whichever component predicted best last frame.
   - Result: 0.274 → 0.000 at L4, retention harm 0.013, net 0.260. Adopted; L4 mastered.
4. **L5 (bounce under gravity), residual fit 1:**
   - All alternatives were refuted and none even cleared the bar at the level, so there was nothing to compose.
   - The agent asked where its surprise lives. Of its residual on its own recorded L5 episodes, 125 cells fell on reversal frames (`dx·pdx < 0`, a bounce just happened) and 30 on after-reversal frames.
   - It authored its model plus a reversal layer fitted on those frames. The x-axis fit came out as `x' = x − ppdx`: after a wall bounce the next step undoes the step before the bounce.
   - Result: 0.537 → 0.216, harm 0.002. Adopted.
5. **L5, residual fit 2:**
   - The next concern exhausted again, and the residual now concentrated on after-reversal frames.
   - It authored a second layer. On bases 1000, 5000 and 9000 the fit came out exactly as `x' = x + dx` (x) and `y' = y + dy + 0.5` (y): constant velocity, plus gravity on the y axis, which the fit found from data. On 2024 it was close: `y' = y + 0.94·dy − 0.04·ppdy + 0.44`.
   - The y-axis reversal layer (step 4) is only an approximation on every base, around `y' = y − 0.4·pdy − 0.7·ppdy + 0.1`. Floor bounces under gravity are not linear in the history, and that is where the remaining L5 surprise lives.
   - Result: 0.256 → 0.173, harm 0.001. Adopted.
   - Three consecutive episodes then fell at or under the floor, and L5 was mastered.
6. **After mastery:** a remaining concern exhausted honestly. Both atoms were already used, so there was nothing more to author.

Seed bases 1000 and 9000 also authored a reversal layer at L2. Base 1000 adopted it, with net 0.055. Base 9000 refuted it, because its net of 0.042 fell short of the 0.05 bar.

Reproduce with `evaluation/substrate_capability/prediction_world_rsi_v1.py 60 <seed_base>` (about 15–25 s for the on arm). The tests are in `tests/test_prediction_world_migrated.py`.

## What the graph decides and what is mechanical

The graph decides everything below. These are rules in `seeds/prediction_world.json` and in `seeds/prediction_self_improvement.json`, which is frozen and has its types protected by `improvement_integrity`:
- the prediction itself (`predict_body_next`: context layers first, then per-body, per-axis component selection);
- mastery and level advance;
- filing a surprise concern;
- proposing one trial per untried candidate;
- the judge;
- adoption (best `weighed_net`, with ties going to the simpler model);
- declaring a concern exhausted;
- authoring a composite, including which components;
- requesting a residual fit;
- authoring a context layer: which atom, and its coefficients copied from the fit.

Python (`domains/prediction_world.py`) handles the mechanical parts:
- simulating levels and writing observations;
- measuring surprise;
- replaying the agent's own recorded episodes for a requested trial or residual fit;
- for a fit, summing the residual per context atom and solving the least-squares fit. It writes these as `ResidualCell`s, and the graph chooses among them.

The judge is weighed, not protective. A trial is supported when it cuts surprise at the level by 20% and its gain, net of the surprise it adds on each mastered level, is at least 0.05. Harm elsewhere is a cost to trade against.

## Limits

- **Human-written building blocks.** These are:
  - the six base models;
  - the composition operator;
  - two context atoms (reversal, after-reversal);
  - the linear layer form (`x + c0·dx + c1·pdx + c2·ppdx + c3`, folded into the box).

  The agent decides when to author, what to compose, which atom to condition on and what the coefficients are, all from its own episodes. It does not invent atoms or operators.
- **Finite authoring space.** There are at most two layers per model, each atom is used once per model, and no model is authored twice. So authoring always terminates.
- **Mastery at L5 is narrow.** Held-out surprise is 0.14–0.15 against a floor of 0.15. Live L5 episodes still range from 0.06 to 0.23.
- **In-sample fits.** The coefficients are fitted on the same recorded episodes the trial then replays. The held-out numbers above, on unseen seeds, are the check that they generalise, and they do (L5 0.56 → 0.14).
- **Fix to concern filing in 1.2.0.** Filing used to require that none of the last `window` episodes was under the floor, so one lucky episode could block a concern forever. It now files whenever the level is not mastered. This also reshaped the earlier-level trajectories slightly. 1.2.0 also added mastery of the last level.
- **Harness.** It runs in-process (`WorldAdapter`), not in the daemon. The worlds are small and deterministic.

## Next

Every level is now mastered, so the curriculum is the ceiling. Possible next steps:
- Harder levels. For example, collisions between bodies would need a context atom the agent does not have.
- Letting the agent author context atoms themselves, from the structure of its residual, so it does not depend on the two written for it.
