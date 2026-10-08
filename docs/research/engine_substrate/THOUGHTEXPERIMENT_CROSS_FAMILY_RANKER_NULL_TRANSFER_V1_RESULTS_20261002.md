# Cross-family ranker null-transfer probe v1 — results

**Superseded: utility join failed independent audit.** The v1 order capture completed, but the reviewer found that candidate digests differed from those in the separate control-kind capture. The label-only join would not prove that the evaluated candidate bundle was the one ranked, so the utility comparison is invalid and no v1 utility conclusion is reported. See the [v1.1 amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_1_AMENDMENT_20261002.md); the original raw capture and failed reviewer attempt remain preserved.

| Policy | First candidate | Held-out utility (unverified) | Median rank-call time |
|---|---|---:|---:|
| Default generator order | `flip_comparison` | 1.0 / 1.0 / 1.0 | — |
| Cold graph rank | `swap_term_leaf:family->name_lc` | 0.0 / 0.0 / 0.0 | 8.69 ms |
| Graph rank with recurrence training outcomes | `swap_term_leaf:family->name_lc` | 0.0 / 0.0 / 0.0 | 8.50 ms |

The order and prior-count traces are useful descriptive capture: all six control-kind candidates received zero recurrence successes and failures, and experience order matched cold order. However, the separately captured held-out scores cannot be joined to these candidate bundles by digest. Treat these order-only fields as a pilot pending the v1.1 two-stage replay.

Rank-call times are measured around `rank_candidates` only. They exclude boot, candidate generation, branch execution, and adoption; the result is not a complete cost comparison or the four-family confirmatory panel. The held-out labels are joined by the separate review script from the control-kind admission capture, not loaded by the worker before ordering.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_raw_20261002.json)
- [Independent review](../../../evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_analysis_review_20261002.json)
