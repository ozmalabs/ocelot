# `explore_unscored` as default: preregistration (2026-10-09)

Written before any run of `evaluation/substrate_capability/explore_unscored_promotion_v1.py`.

## Question

`VariationOp{cue_set_edit}.explore_unscored = 1` (opt-in since tranche 5) lets `cue_route_pick` propose the best untried pooled route when no route scores by bigram overlap. Tranche 11 showed that without it a zero-overlap verb (`sort`) is never repaired.

Should it become the default?

## Design

- **Boot.** The production default boot, with no `variation_credit` loaded (per the user's instruction to leave that default as is). `OZMA_SEED_PERSIST_DISABLED=1`.
- **Retries.** Agent-initiated only.
- **Frame.** "Please <verb> the notes.", steered with "Work on the <verb> notes gap.".
- **Streams**, each on one agent per arm, in this fixed order. Gap filing was feasibility-checked beforehand, not outcomes:
  - Z (zero bigram overlap with every route Concept): sort, tag, trim, dub, snip, sift
  - O (overlap ≥ 1, a regression set): mend, buff, flag, sum, fold, group
- **Arms.** `default` (explore_unscored absent) and `explore` (`explore_unscored=1`).

## Measures (per arm, per stream)

- handled verbs;
- real child experiments;
- false adoptions.

## Promotion rule (all must hold)

| Gate | Condition |
|---|---|
| E1 | Z: `explore.handled > default.handled` |
| E2 | O: `explore.handled >= default.handled` |
| E3 | 0 false adoptions in `explore` on both streams |
| E4 | O: `explore.experiments <= default.experiments + 2` (bounded extra cost on verbs that already score) |

If all hold, `explore_unscored=1` becomes the `cue_set_edit` default in `variation_ops`, subject to the tranche regression.

## Outputs

`evaluation/reports/explore_unscored_promotion_v1_{default,explore}_{Z,O}_20261009.json` and `..._v1_20261009.json`.
