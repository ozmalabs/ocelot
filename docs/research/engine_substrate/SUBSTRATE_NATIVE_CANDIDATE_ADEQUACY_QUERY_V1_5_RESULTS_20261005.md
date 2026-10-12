# Native candidate-adequacy query v1.5 results

## Result

The fresh 40-panel, three-arm capture passes all five runtime gates across 120 workers. The independent analyzer passes all 14 checks, including current source lock, native/host candidate-positive query-order and decision parity, score and prediction replay, task-identity exclusion, query/transfer disjointness, and mismatch-to-help receipts.

Three of the 10 opposition panels initially accept an incorrect candidate. Native and host candidate-positive arms find all three counterexamples and request help with four labels total. Uniform querying finds one and leaves two accepted. Additive/product controls select correctly in all 20 panels with no false help; all 10 inequality panels request help before querying. The opposition false-accept count varies across fresh cohorts and is too small for prevalence claims.

## Cost

| Native candidate-positive worker metric | v1.4 median | v1.5 median |
|---|---:|---:|
| Total CPU | 291.29 ms | 310.50 ms |
| Eligibility closure | 6.72 ms | 7.41 ms |
| Query selection closure | 12.17 ms | 15.42 ms |
| Query adjudication closure | 12.31 ms | 15.99 ms |
| Probe prediction closure | 19.66 ms | 21.50 ms |
| Peak RSS | 155.1 MiB | 156.6 MiB |

The v1.5 host candidate-positive arm uses 282.60 ms median CPU, making native about 9.9% higher for this cohort. Timings come from separate source-locked captures with fresh seeds, so small differences may include run variation; this does not establish a regression from the repeated-variable fix. The v1.5 result is the current-build reference. The matcher scale gain remains strong in its dedicated same-workload comparison, but a new scale capture should carry the latest engine fingerprint.

## Interpretation and limits

This regression panel confirms end-to-end behavior after correcting semi-naive repeated-variable seeding. Native and host query decisions continue to match. The candidate menu, task-blind priorities, and label oracle remain supplied by the harness; candidate acquisition is not tested. The result is bounded to synthetic numeric tasks.

## Evidence

See the [v1.5 protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_5_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_5.py), [source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_5_lock_20261005.json), [capture](../../../evaluation/reports/native_candidate_adequacy_query_v1_5_20261005.json), and [independent analysis](../../../evaluation/reports/native_candidate_adequacy_query_v1_5_analysis_20261005.json). The repaired repeated-variable path is evaluated in the [matcher v3 differential](SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V3_RESULTS_20261005.md); v1.4 is preserved for cross-capture comparison.

