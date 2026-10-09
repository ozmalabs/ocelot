# Mixed-kind variation credit on real verdicts, v2: preregistration (2026-10-09)

Written before any run of `evaluation/substrate_capability/variation_credit_mixed_kind_v2.py`. Follows [v1](SUBSTRATE_VARIATION_CREDIT_MIXED_KIND_V1_PREREG_20261009.md), which failed M1/M2 because its misordered family (`reply_ablation`) abstained before dispatch, so the wrong prior cost nothing.

## What changes

- **A misordered family that dispatches.** The reported concerns now also name "hardcoded … floor", which grounds the `ruleliteral` head. A feasibility check (builder calls only, no dispatch, no verdicts) confirmed that `rule_literal_edit` then **builds** a variant for these concerns: it edits an unrelated where-literal, for example in `ha_open_persistent_compound_curiosity_selection`. `knob_edit` still builds `reform_residual_threshold`. `VariationOp{rule_literal_edit}.priority` is set to 8 in every arm, so it is picked before `knob_edit` (15). A wrong first pick on the reported kind therefore costs a real child replay.
- **Instruction kind** keeps its held order (`cue_set_edit` 10 ahead of `reply_ablation` 20; `rule_literal_edit` is not eligible). It serves as the **cross-kind interference check**.
- **Three arms**, so that credit's own contribution is isolated from the tranche-9 exclusion policy:

| Arm | `use_credit` | `exclude_refuted` | `credit_internal_exempt` | `exclude_inconclusive` |
|---|---|---|---|---|
| A | 0 | 1 | 0 | 0 |
| B | 0 | 1 | 1 | 1 |
| C | 1 | 1 | 1 | 1 |

- **Steering.** All arms include `conversation_steering` v1.2.0 (tranche 14: a steer turn promotes the best-matching concern). This fixes the v1 `alphabetise` miss, whose cause was a shadow-read `comprehension` concern stealing the promote.

Everything else is as in v1:
- the lab boot, which loads `variation_credit` explicitly (the production default is unchanged);
- shadow read on;
- retries opted in for both kinds, with at most 3 experiments per concern;
- the K1 corpus heard first;
- the same interleaved 8-concern stream (I, R, I, R, …) in the same order;
- `OZMA_SEED_PERSIST_DISABLED=1`.

## Measures (per arm, per kind)

- `handled`, `experiments`, `false_adoptions`, as in v1.
- `late_reported_first_pick_knob`: for the two reported concerns at stream positions 5 and 7, whether the first **dispatched** experiment's family is `knob_edit`.

## Gates (each reported)

| Gate | Condition | What it tests |
|---|---|---|
| G1 | `C.R.experiments < B.R.experiments` **and** `C.R.handled >= B.R.handled` | Credit saves replays on the misordered kind |
| G2 | `C.I.handled >= B.I.handled` **and** `C.I.experiments <= B.I.experiments` | Credit learned on the reported kind does not harm the instruction kind |
| G3 | 0 false adoptions in B and C | |
| G4 | `C.late_reported_first_pick_knob == 2` | Credit moves the later first pick to the working family |

Arm A is reported for context only; it is not part of any gate.

## Caveat

There is one deterministic stream per arm, with 4 concerns per kind. A pass shows the mechanism works on a mixed stream; it is not an effect size.

## Outputs

`evaluation/reports/variation_credit_mixed_kind_v2_{A,B,C}_20261009.json` and `..._gate_20261009.json`. The runner refuses to overwrite.
