# Native query-eligibility join-order comparison v2 results

## Result

All 50 source-locked workers completed. The independent analyzer passed all nine checks, including exact host-oracle replay, paired output parity, current source lock, and five paired seeds at each population size. The two authoring-order arms produce identical eligible sets and selected nodes.

| Probe examples | Probe-first eligibility median | Vote-first eligibility median | Vote-first / probe-first | Probe-first / vote-first selection median |
|---:|---:|---:|---:|---:|
| 512 | 3.96 ms | 4.34 ms | 1.10× | 0.089 / 0.075 ms |
| 1,024 | 12.14 ms | 15.11 ms | 1.24× | 0.115 / 0.128 ms |
| 2,048 | 57.98 ms | 55.93 ms | 0.96× | 0.225 / 0.223 ms |
| 4,096 | 219.57 ms | 208.41 ms | 0.95× | 0.381 / 0.384 ms |
| 8,192 | 865.07 ms | 900.67 ms | 1.04× | 0.879 / 1.236 ms |

There is no consistent reduction from authoring the vote join first. The rule is installed through the normal API, which applies the engine's selectivity-based match-edge reordering; the panel therefore compares authoring orders under production reordering, not an engine path that guarantees the authored order is retained. The small, mixed timing differences do not indicate a useful improvement.

## Source inspection and next step

Inspection of `rewrite::extend_each` shows that when both endpoints of a match edge are already bound, the matcher currently enumerates all outgoing neighbors of the bound source for that edge type and then filters for the bound target. In this rule, the final join checks membership in the episode's `has_probe_example` population. Even with the vote-to-example edge joined first, that fully bound membership check can enumerate the full probe adjacency once for each candidate, preserving quadratic work. Replacing that enumeration with the existing exact `TypedGraph::has_edge` check is a focused engine optimization candidate; it must preserve all match, trace, and mutation semantics and should be measured with source-locked parity and cost gates before broader use.

The result is a negative join-order optimization result and a source-grounded explanation for the remaining cost. It is still a synthetic graph-level workload and does not prove natural-task tractability. The next gate is a controlled engine implementation comparison, followed by rerunning the full v1.3 task cohort if the scale curve improves.

## Reproduction and evidence

See the [preregistered protocol](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V2_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_query_eligibility_scale_v2.py), [source lock](../../../evaluation/substrate_capability/native_query_eligibility_scale_v2_lock_20261005.json), [raw capture](../../../evaluation/reports/native_query_eligibility_scale_v2_20261005.json), and [independent analysis](../../../evaluation/reports/native_query_eligibility_scale_v2_analysis_20261005.json). The preceding [v1 scale results](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V1_RESULTS_20261005.md) establish the baseline cost curve.

