# Live action route work comparison v1 (2026-09-26)

## Matched execution context

The describe-scene v1.5 and self-report v1.7 captures have byte-identical 1,669-file source closure maps, native extension hashes, native build manifest hashes, Python versions, and platform strings. Each route has three fresh-process replications and six production lifecycle helper calls per two-request run. Each route's independent analyzer verifies exact helper-counter replication and per-rule/global counter conservation.

The earlier describe-scene v1.4 capture remains valid under its own lock, but `boot_all.py` changed before the self-report v1.7 capture. V1.5 repeats the scene schedule under the same current source closure as v1.7; only v1.5 is used in this comparison.

## Work comparison

| Route fixture | Requests / helper calls | Candidate pairs per run | Term evaluations per run | Median helper time by event kind |
|---|---:|---:|---:|---|
| `describe_scene` | 2 / 6 | 337,522 | 1,686,456 | selection 46.02 ms; execution 47.85 ms; result 45.68 ms |
| `self_report` | 2 / 6 | 49,888 | 528,489 | selection 13.56 ms; execution 12.84 ms; result 13.46 ms |

For these two captures, describe-scene has 6.77× the candidate-pair visits and 3.19× the Term evaluations of self-report. The per-kind times are medians across the six helper calls per route (two calls per kind in each of three workers). The helper timer includes graph event preparation and native closure over the full loaded rule set.

The independent comparison analyzer passes nine checks, including exact equality of source closure, binary/build, and environment fingerprints. It verifies the input analyses and two-request/six-call shape before computing totals.

## Interpretation and limits

The result shows that full-seed production helper work can differ substantially across two action fixtures even when source code, seed corpus, native binary, and runtime match. It also shows why a single “per turn” cost estimate is misleading: task content and the evolving graph affect the closure work.

This is an exploratory comparison, not a causal route effect. `describe_scene` uses a concrete percept scene and a threaded schedule serialized by the adapter lock; `self_report` uses an organization query and sequential turns. Their contents, intermediate graph state, and schedules differ. The captures do not show which counted rules are necessary, natural action-route frequency, task quality differences, or a general capability envelope. Do not extrapolate these ratios to workloads beyond the two fixtures.

## Artifacts

- Comparison protocol and limits: [protocol](SUBSTRATE_LIVE_ACTION_ROUTE_WORK_COMPARISON_V1_PREREG_20260926.md)
- Independent comparison analyzer: [`analyze_substrate_live_action_route_work_comparison_v1.py`](../../../scripts/analyze_substrate_live_action_route_work_comparison_v1.py)
- Comparison analysis: [nine provenance and schedule checks](../../../evaluation/reports/substrate_live_action_route_work_comparison_v1_20260926.json)
- Describe-scene current-source capture: [v1.5 results](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_5_RESULTS_20260926.md), [raw](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_5_20260926.json), [lock](../../../evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_5_lock_20260926.json)
- Self-report current-source capture: [v1.7 source lock](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_7_lock_20260926.json), [raw](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_20260926.json), [work analysis](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_analysis_20260926.json)
