# Live describe-scene access trace v2.4 results (2026-09-27)

## Outcome

The six-worker run passes all eight preregistered integrity gates. All source locks match at worker start/end and after the run; all threads join; the A/B serialization and selection pause hold; both request Goals resolve through selection, execution, and action result; traced/untraced pairs preserve replies, lifecycle, output evidence, cuts, and whole-graph semantic hashes; access intervals are complete, reconcile, and have no dropped events.

The independent analyzer reconstructs the gates and the reported structural counts. The same-snapshot trace-only isolation also passed its seven gates, establishing that enabling the native trace alone does not prevent this fixture's plain two-request schedule. This does not isolate every interaction in the full v2.4 driver, but v2.4 itself completes successfully on its own locked source snapshot.

## Measured structure and selected accesses

| Request projection | Owned nodes | Induced-width upper bound | Boundary incidences | Unique external nodes | Native access events (each of 3 traced workers) |
|---|---:|---:|---:|---:|---:|
| A | 7 | 2 | 35 | 20 | 1,140,892 |
| B | 6 | 2 | 32 | 18 | 997,848 |
| Shared Scene + three Percepts | 4 | 1 | 5 | 5 | Shared input projection; accesses are not uniquely attributed to it |

The final graph has 25,201 nodes and 11,848 edges. This shows a small lifecycle projection embedded in a larger graph, but its observed structural cut is not small by external-node count, and selected access events alone do not prove that dynamic computation factorizes across that cut. The scene input is explicitly represented here, fixing the omission in the earlier lifecycle-only analysis, but descendant dependencies beyond the selected trace remain unproven.

## Separate capability finding

Both public replies match the expected scene description and both Goals resolve in every worker. Yet in all traced workers the graph-visible unsuppressed outbound Message fails to match the public reply: request A has a different gap message, and request B has no matching outbound Message. This output-channel alignment gap is independent of the locality result and should be evaluated as its own capability.

## Timing boundary

Do not use v2.4's wall/CPU values as baseline substrate latency. Its complete driver enables per-rule scale auditing around lifecycle producer callbacks and performs graph readback. These timing rows describe an instrumented capture, not commodity-CPU operating cost. A separate uninstrumented timed replay is required.

## Artifacts

- [v2.4 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_4_PREREG_20260927.md)
- [v2.4 runner](../../../scripts/substrate_live_describe_scene_access_trace_v2_4.py)
- [independent analyzer](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_4.py)
- [independent analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_analysis_20260927.json)
- [summary](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_20260927.json)
- [raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json)
- [trace-only isolation protocol](SUBSTRATE_DESCRIBE_SCENE_ACCESS_TRACE_ISOLATION_V1_PREREG_20260927.md)
- [trace-only isolation runner](../../../scripts/substrate_describe_scene_access_trace_isolation_v1.py)
- [trace-only isolation report](../../../evaluation/reports/describe_scene_access_trace_isolation_v1_20260927.json)
