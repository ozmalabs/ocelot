# Live task per-rule touch matrix v1

Date: 2026-09-26

## Measurement

This independent reanalysis uses the unchanged six-worker, source-locked `describe_scene` access-trace v2.1 capture: three traced workers and their three untraced semantic twins. It intersects each traced event's concrete node/peer IDs with the captured A and B task-owned node sets, then aggregates observed task touches by RuleUID. The analyzer rechecks worker locks, event-count conservation, zero dropped rows, disjoint task-node sets, and exact per-rule matrix replication.

All five checks pass. Each request observes all 410 loaded RuleUIDs. Request A's interval has 73 rules with at least one recorded access to A's nodes and none to B's. Request B's interval has 65 rules touching A's nodes, 71 touching B's, and 63 touching both sets across their events. Only 12 of B's 919,200 individual recorded events directly include endpoints from both task sets. In B's interval, 2,069 events touch only A, 2,999 only B, 12 both, and 914,120 neither. The corresponding A counts are 3,481 touching only A and 948,086 touching neither.

## Interpretation and limits

This gives a measured per-rule/task access matrix, finer than aggregate node-touch totals. It shows substantial observed rule overlap across task-owned vertices in B's interval, alongside very few single events spanning both sets. It does not show that the 63 overlapping rules have a semantic dependency in this execution: touches can be separate reads/writes, and the event stream is partial. In particular, no-touch rows are not proof of independence; omitted specialized scans, host effects, scheduler work, and operations outside an active RuleUID remain material gaps. This matrix is not sufficient to safely omit rules or partition closure.

## Artifacts

- [Current-source trace results](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_1_RESULTS_20260926.md)
- [Analyzer](../../../scripts/analyze_substrate_live_task_rule_touch_matrix_v1.py)
- [Independent analysis](../../../evaluation/reports/substrate_live_task_rule_touch_matrix_v1_20260926.json)
- [Source-locked capture](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_workers_raw_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_1_lock_20260926.json)

## Next measurement

Close the remaining access-coverage gaps that can affect task ownership, then use a frozen mutation/retraction workload with full-closure state as the oracle. Compare any discovered rule/scope candidate against full closure while charging discovery, rule selection, boundary exchange, notifications, and scheduler work. Require exact whole-graph, reply, and lifecycle parity before treating an observed touch matrix as executable locality.
