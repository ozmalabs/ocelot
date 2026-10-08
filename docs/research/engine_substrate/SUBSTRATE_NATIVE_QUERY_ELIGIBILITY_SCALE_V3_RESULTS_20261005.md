# Native query-eligibility scaling v3 results

## Result

The rebuilt engine uses direct `TypedGraph::has_edge` membership when both endpoints of a match clause are already bound. All 25 current-source workers completed, and the independent analyzer passed its source-lock, panel, oracle, eligibility identity, selected-node, and timing checks. Every worker produced exact eligible-set and selected-node parity.

## Before/after cost

The v1 baseline and v3 intervention use the same deterministic sizes and seeds, but were run in separate captures. Ratios are descriptive, not counterbalanced same-session estimates.

| Probe examples | v1 eligibility median | v3 eligibility median | v1/v3 reduction | v3 selector median | v3 graph-build median |
|---:|---:|---:|---:|---:|---:|
| 512 | 3.45 ms | 0.67 ms | 5.2× | 0.068 ms | 3.25 ms |
| 1,024 | 17.67 ms | 1.44 ms | 12.3× | 0.157 ms | 5.72 ms |
| 2,048 | 55.56 ms | 2.55 ms | 21.8× | 0.193 ms | 15.27 ms |
| 4,096 | 203.16 ms | 5.56 ms | 36.6× | 0.391 ms | 30.60 ms |
| 8,192 | 852.06 ms | 15.59 ms | 54.7× | 0.853 ms | 61.72 ms |

Across the tested 16× population increase, v3 eligibility grows about 23.4×, compared with 247× in v1. This substantially reduces the observed superlinear cost; it does not prove a linear asymptotic bound. At 8,192 probes, the eligibility closure falls by about 98.2%. Selection stays below one millisecond median and graph construction is now a larger measured component than eligibility at the largest size.

## Interpretation and next gate

This supports the source-grounded explanation from v2: the fully bound membership clause was repeatedly enumerating unrelated neighbors. Replacing that with exact edge lookup retained results and sharply reduced cost in this synthetic route. The production matcher change has broad reach, so this panel establishes only the specific rule workload and direct membership semantics represented here. It does not establish an end-to-end application gain, broad matcher correctness, or natural-task locality.

Next rerun the full candidate-adequacy query cohort under the rebuilt engine, with a fresh lock and independent analysis. If paired native/host decisions remain equal and native total cost improves, add broader differential coverage for fully bound match clauses before promoting the optimization as a general engine capability.

## Reproduction and evidence

The preregistration is [here](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V3_PREREG_20261005.md); source-linked artifacts are the [runner](../../../evaluation/substrate_capability/native_query_eligibility_scale_v3.py), [source lock](../../../evaluation/substrate_capability/native_query_eligibility_scale_v3_lock_20261005.json), [raw capture](../../../evaluation/reports/native_query_eligibility_scale_v3_20261005.json), and [independent analysis](../../../evaluation/reports/native_query_eligibility_scale_v3_analysis_20261005.json). The source edit is in [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs). The comparison baseline is the [v1 result](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V1_RESULTS_20261005.md).

