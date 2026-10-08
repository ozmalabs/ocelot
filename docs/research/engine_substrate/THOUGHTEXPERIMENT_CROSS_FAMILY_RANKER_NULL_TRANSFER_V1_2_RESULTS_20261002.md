# Cross-family ranker null-transfer probe v1.2 — results

**Independent review: 20/20 gates pass.** Three fresh rank workers composed the actual graph-authored `self_correct_rank_*` Program for `classify_kind_family`. They received all eight recurrence training records, but each of the six control-kind candidates retained zero prior successes and failures. The cold and recurrence-experience orders were identical in every worker:

1. `swap_term_leaf:family->name_lc`
2. `flip_comparison`
3. `add_match_guard(control)`
4. `swap_term_leaf:family->spec`
5. `swap_term_leaf:family->word`
6. `swap_term_leaf:name_lc->family`

After the order artifact was written and source parity checked, three separate fresh scoring workers received the exact serialized candidate bundles. Only `flip_comparison` passed both held-out cases (`steering wheel`, `trigger button`). Thus default generator order selects a passing candidate first, while cold and experience rank both select a failing candidate first and need a second trial. The separate evaluator confirmed that unrelated recurrence records do not alter the ranker when target and outcome class do not match.

| Policy | First-candidate utility | Attempts to reach held-out pass | Median rank-call time |
|---|---:|---:|---:|
| Default generator order | 1.0 | 1 | — |
| Cold graph rank | 0.0 | 2 | 9.01 ms |
| Graph rank with recurrence training outcomes | 0.0 | 2 | 8.47 ms |

This is direct evidence of a cross-family transfer boundary in one controlled task: experience does not transfer through the current outcome schema without a shared class or target identity. The result does not establish ranking quality across families or a full economic comparison. Rank-call timing excludes boot, candidate execution, branch, and adoption costs. The three-worker probe is not the four-family confirmatory panel.

V1's digest-only utility join and v1.1's post-write reporting failure are preserved as failed harness attempts. V1.2 uses two separate capture stages: order capture first, then scoring of those exact serialized candidate bundles. See the [v1.1 amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_1_AMENDMENT_20261002.md) and [v1.2 amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_2_AMENDMENT_20261002.md).

## Artifacts

- [Original preregistration](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_PREREG_20261002.md)
- [V1.1 amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_1_AMENDMENT_20261002.md)
- [V1.2 amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_2_AMENDMENT_20261002.md)
- [V1.2 runner](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1_2.py)
- [V1.2 lock](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_lock_20261002.json)
- [Order capture](../../../evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_orders_20261002.json)
- [Scoring capture](../../../evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_scores_20261002.json)
- [Independent review](../../../evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_analysis_review_20261002.json)
