# Variation credit on real verdicts, v2: preregistration (2026-10-08)

Written before any run of `evaluation/substrate_capability/variation_credit_real_judge_v2.py`. Follows [v1](SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V1_PREREG_20261008.md), which passed on n=1 stream per arm, with one miss caused by per-trial credit on a retry_internal family.

## Questions

1. Does the v1 result replicate on more streams and on a second object template?
2. Do the two tranche-9 policy options do better than plain per-trial credit?
   - `credit_internal_exempt`: a retry_internal family is not charged, within the same concern, for trials that carried an untried-alternative route.
   - `exclude_inconclusive`: a family judged inconclusive for a concern is excluded from that concern.

## Design

- **Streams.** Each stream runs on one fresh full-seed agent per arm, in this fixed order:
  - S1 (template "<Verb> the data."): condense, tabulate, shorten, alphabetise, paraphrase, abridge
  - S2 (template "<Verb> the list."): itemise, transpose, collate, annotate, reorder, condense
- **Per verb.** The verb is said with its template, which files a gap. "Work on the <verb> <object> gap." steers it into a promoted concern. Retries are the agent's own (`max_retries=2`, so at most 3 experiments per verb). There is no human retry.
- **Misordered prior in every arm.** `VariationOp{reply_ablation}.priority = 8`, against `cue_set_edit` at 10.
- **Arms.** All arms keep `exclude_refuted=1`.

  | Arm | `use_credit` | `credit_internal_exempt` | `exclude_inconclusive` |
  |---|---|---|---|
  | A (OFF) | 0 | — | — |
  | B (CREDIT) | 1 | — | — |
  | C (CREDIT+T9) | 1 | 1 | 1 |

- **Execution.** `OZMA_SEED_PERSIST_DISABLED=1`. The six (arm, stream) runs are independent processes, each writing its own part file. An aggregator computes the gate over all part files.

## Measures

Per arm, pooled over S1 and S2:
- `handled`: verbs whose final templated turn is handled (not the gap floor, not the error surface).
- `experiments`: the number of real child experiments.
- `false_adoptions`: an adoption whose verdict was not supported, or an adopted verb that is not handled afterwards.

A verb skipped because its gap was not filed or its promotion failed is reported, and is excluded from all arms only if it is skipped in all arms.

## Gate (all must hold)

| Gate | Condition | What it tests |
|---|---|---|
| G1 | `B.handled > A.handled` | Replication of v1 |
| G2 | `C.handled >= B.handled` | The tranche-9 policy handles at least as many verbs |
| G3 | `C.experiments <= B.experiments` | The tranche-9 policy costs no more experiments |
| G4 | `B.false_adoptions == 0` and `C.false_adoptions == 0` | No false adoptions |

Each gate is reported separately. A failure is reported as a failure.

## Caveat, stated in advance

This is still small: 12 problems per arm and one deterministic run per (arm, stream). Both templates share one sentence frame. A pass supports "credit from real verdicts steers, and the tranche-9 policy does not cost more". It is not an effect size.

## Outputs

`evaluation/reports/variation_credit_real_judge_v2_<arm>_<stream>_20261008.json` (six part files) and `evaluation/reports/variation_credit_real_judge_v2_gate_20261008.json`. Runners refuse to overwrite.
