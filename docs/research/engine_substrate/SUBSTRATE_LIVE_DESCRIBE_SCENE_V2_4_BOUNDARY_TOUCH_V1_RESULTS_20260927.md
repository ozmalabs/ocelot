# Live describe-scene v2.4 declared-boundary touch analysis v1 (2026-09-27)

## Result

This is a derived analysis of the three complete, identical traced workers in the v2.4 live describe-scene capture. It does not rerun the workload. Five checks pass: three trace workers, no dropped events, per-worker source stability, identical repeated touch signatures, and reconciliation of category counts to selected event totals.

Each selected trace row is classified by whether its `node` or `peer` touches one of three explicitly declared node sets: request A lifecycle, request B lifecycle, or shared Scene+Percepts input. The classification is mutually exclusive, including a separate `a+b` case.

| Request | Selected events | Own lifecycle | Other lifecycle | Shared Scene+Percepts | Neither declared set | Neither share |
|---|---:|---:|---:|---:|---:|---:|
| A | 1,140,892 | 3,726 | 0 | 400 | 1,136,766 | 99.64% |
| B | 997,848 | 3,403 | A: 2,387; both: 13 | 325 | 991,720 | 99.39% |

Among events that touch none of the declared sets, the three scene-recognition rules each perform 176,960 `name` reads for request A and 240,160 for request B. `curiosity_targets_ambivalent_nodes` performs 107,440 `state` reads and 107,440 `is_ambivalent` reads for A; for B, each count is 82,160. These repeated reads explain a large share of the selected operation volume, but the capture does not identify them as necessary task dependencies or prove they are broad scans.

## Interpretation and limit

Adding the Scene+Percepts input nodes to the declared boundary does not make the selected work look localized: more than 99% of events still touch none of the named lifecycle/input nodes. This is stronger evidence that the current projection does not account for most measured work. It is **not** evidence that those events are unrelated: task descendants, shared graph hubs, or other omitted inputs may be touched without appearing in these sets. The trace is selected and aggregated; it lacks event order and does not expose a complete read/write dependency graph. The current capture therefore cannot establish a complete task cut, separator size, or causal factorization.

The immediate engine question is which high-volume rule reads are task-relevant and which execute as broad closure work. A follow-up needs an auditable runtime dependency projection that includes rule-produced descendants and shared state, plus a causal frame-scope intervention that preserves request outputs, lifecycle, and whole-graph semantics. Any work reduction must be attributed separately to task dependencies versus unrelated global scans.

## Artifacts

- Base capture: [v2.4 results](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_4_RESULTS_20260927.md)
- Analyzer: [analyze_substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1.py](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1.py)
- Analysis: [substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1_20260927.json](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1_20260927.json)
- Raw worker source: [v2.4 raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json)
