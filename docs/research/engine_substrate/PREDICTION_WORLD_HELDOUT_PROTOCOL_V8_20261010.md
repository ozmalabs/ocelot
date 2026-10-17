# Prediction world: authored predicates and an escalating curriculum (pre-registration v8, 2026-10-10)

This is written and committed before any v8 draw exists. The results go in `PREDICTION_WORLD_HELDOUT_RESULTS_20261010.md`, under "v8".

## Why

v7 concluded that the meta-level gains that hold are about cost, not capability. The remaining failures are hard levels the agent either cannot solve with its building blocks or declines to change for. Two directions follow:
- **A.** Let the agent author new building blocks, so hard levels become solvable.
- **B.** Let it experience hard levels before it is tested, through a curriculum that keeps escalating.

## What changed (loop 1.9.0)

**A. Predicates the agent authors.** Each model, and each expert, can hold one more layer, checked before the others. It is conditioned on a predicate `comb(F[a], F[b])  cmp  thr`:
- **Features** (9): dx, pdx, ppdx, acc, x, w−1−x, |dx|, |acc| and 1.
- **Combinations:** product, sum, difference. **Comparisons:** < or >.
- **Thresholds:** 0, and the 10/25/50/75/90% quantiles of the value on the level's frames.

That gives about 3,000 distinct predicates per search.

- **Search (mechanical).** On a residual fit, Python searches the predicates. It keeps those covering at least 16 frames and at most 60% of them. For each, it fits the linear layer, level-only and pooled. The top 3 per mode by in-sample gain become `author_atom` cells.
- **Authoring (graph).** `pw_author_predicate_layer` authors candidates from those cells, replacing any predicate layer the model held. It acts as a last resort, after named-atom fits are spent. The unchanged judge decides.
- The feature set and the grammar are human-written. Which predicate, and its coefficients, come from the agent's own residual.

**B. Escalating curriculum.** With `level_patience` > 0, `pw_move_on_from_level` moves the agent on from a level not mastered after that many episodes. The escalation phase used in v8, after the standard curriculum:
- 8 more levels from the same physics family. Seeds are `10⁸ + seed_base`, a range no evaluation uses.
- Chosen to span difficulty, and ordered easiest-first by the newborn model's surprise.
- 12 episodes of patience each: 96 episodes.

**Development evidence, disclosed.**
- **Curriculum.** With predicate authoring as a last resort, all 4 seed bases master all 5 levels.
  - On 2 bases the curriculum authors `acc + wx < 0`: accelerating towards the far wall. That lowers L5 held-out surprise from 0.14 to 0.064 and L2 from 0.115 to 0.095.
  - A version without the last-resort condition broke L5 mastery on 3 bases.
- **Seen hard levels** (v5's 164, v6's 133, v4's 101 and 171; seed bases 1000 and 2024). Predicate authoring at the held-out level changed nothing.
- **Escalation, seed base 1000.** It mastered levels 6–10 and moved on from 11 and 12. It made 8 adoptions, ending with an expert refitted at level 11.

## Frozen at this commit

The following are frozen at this commit:
- `seeds/prediction_world.json` 1.9.0;
- `seeds/prediction_self_improvement.json` 1.9.0;
- `domains/prediction_world.py`;
- `evaluation/substrate_capability/prediction_world_heldout_v7.py`, and the v6 harness it imports from;
- `evaluation/substrate_capability/prediction_world_sequential_analysis_v8.py`.

## Procedure

- **Draws.** Draw d uses `heldout_levels(int(<this commit's hash>[:8], 16) + 7919·d, 8)`. Set A is draws 0–5 and set B is draws 6–11, giving 384 pairs.
- **Arms.** Each run gets up to 30 episodes.

| arm | before the level |
|---|---|
| `on_trained` | curriculum, predicate authoring on |
| `on_trained_noatoms` | curriculum, predicate authoring off throughout |
| `on_trained_escalated` | curriculum + escalation, predicate authoring on |
| `on_naive` | newborn |

- **Metrics.** Final surprise on 5 fresh episodes; retention harm on curriculum levels 1–5; experiments; cost = final surprise + harm + 0.001 × experiments.
- **Tests.** A two-sided exact sign test, and a two-sided sign-flip permutation test on the mean (200,000 flips, seed 20261010). Pocock boundary: p < 0.0294 at each of two looks.

## Hypotheses

- **H10 (authored predicates help).** For `on_trained` vs `on_trained_noatoms`, both must hold:
  - mean final-surprise difference < 0, with permutation p < 0.0294;
  - mean retention-harm difference ≤ +0.01.
- **H11 (escalation helps).** For `on_trained_escalated` vs `on_trained`:
  - mean cost difference < 0, with permutation p < 0.0294.
- **H3e (an escalated agent beats a newborn).** For `on_trained_escalated` vs `on_naive` on final surprise:
  - the sign test favours escalated, with p < 0.0294;
  - the mean difference is < 0, with permutation p < 0.0294.
- **Reported:** `on_trained` vs `on_naive`.

My expectations:
- **H10:** uncertain, leaning yes, because of the curriculum's L5 gain on 2 bases.
- **H11:** uncertain. Escalation adds experience, but also more retention for the judge to protect.
- **H3e:** uncertain.

## What this does and does not test

H10 tests whether building blocks the agent finds for itself, in a grammar much larger than the named atoms, transfer to unseen physics. H11 and H3e test whether experiencing harder levels makes an experienced agent better on new ones.

The feature set, the predicate grammar, the escalation family, its ordering and the patience are human-written and frozen.
