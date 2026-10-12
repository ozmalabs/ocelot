# Live `describe_scene` per-request access trace v2 (2026-09-26)

## Result

Three replicate pairs ran in six fresh processes, with traced/untraced arm order shuffled. All eight gates passed: distinct paired workers, joined threads, stable sources/build, the original serialized A/B schedule, reply and lifecycle parity, exact per-pair task cuts and semantic graph signature, one nonempty zero-drop trace interval per request, no trace rows in untraced arms, and reconciliation of per-request totals with the combined trace.

Each traced request exercised all 410 loaded rule IDs. Request A recorded 951,567 selected native events in 53,164 aggregated rows; request B recorded 919,200 events in 36,007 rows. Neither interval dropped events. In both requests, the dominant event kind was `term_attr_read` (912,362 for A; 889,530 for B). Other recorded kinds included type and edge reads, pattern-edge bindings, and selected effect writes/mints/deletes.

The complete graph contains 25,147 nodes and 11,798 edges in each arm. Replies, event sequence, Goal projections, task-boundary signatures, and semantic graph digests match exactly within every pair. Raw graph digests differ because `SystemModel` diagnostics include execution `ts` and `runtime_s`; the semantic digest removes only those two attributes on that node type and retains all node IDs/types, remaining attributes, and typed edges.

The owned-node crosswalk shows how work crosses task projections. In A's interval, 3,481 events touched A's seven owned nodes and none touched B's six. In B's interval, 2,081 events touched A-owned nodes and 3,011 touched B-owned nodes. A's interval touches six of its seven owned nodes; B's interval touches three A-owned and five B-owned nodes. These are concrete accesses in the selected trace, not proof that every observed access is required or that unobserved paths are absent.

## Timing and overhead limits

Median complete-call wall times were 10.85 s traced versus 10.63 s untraced for A, and 0.853 s versus 0.676 s for B. Median calling-thread CPU times were 10.72 s versus 10.56 s for A, and 0.468 s versus 0.352 s for B. The per-request trace intervals themselves had medians of 10.81 s wall / 10.68 s CPU for A, and 0.447 s wall / 0.438 s CPU for B. The B call includes time outside its lock-delimited trace interval, including waiting for A to finish.

With three pairs, these are fixture-specific instrumentation comparisons, not a precise overhead factor. A's between-pair timing variation is larger than its traced/untraced median difference. B is consistently slower under tracing in these three pairs, which is consistent with measurable trace overhead. Further repetitions and lighter-weight counters are needed to isolate it. The workload also shows that the earlier small graph cut is not equivalent to small closure work: roughly 1.87 million selected events occur across the two requests, all rule IDs participate, and B accesses nodes assigned to A's task projection.

## Excluded development attempts

Initial v2 development attempts are excluded from the six-worker result. A first interval-hook version mishandled reentrant lock nesting and left the second thread blocked; a timed thread dump located the hook in the nested lock path. The hook now tracks per-thread recursion depth and snapshots only at the outermost request boundary. A later six-worker capture completed but the summarizer used call labels `request-A/B` where timing rows used `A/B`; the raw capture showed exact semantic parity, and the complete six-worker capture was rerun after fixing the key mapping. The frozen lock and linked raw file correspond to the final runner.

## What follows

This strengthens the rule-access crosswalk for one authored concurrent action and points toward a useful partition experiment, while leaving access instrumentation incomplete. The next gate is to expand trace coverage for omitted graph scans and host-side effects, then compare a boundary-preserving partition with monolithic whole-graph closure. Preserve the direct A/B edge and shared external nodes; measure discovery, dirty notification, boundary exchange, total wall/CPU time, and memory. Require whole-graph graph-signature, reply, and lifecycle parity before making a factorization claim.

## Reproduction artifacts

- [Amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_describe_scene_access_trace_v2.py)
- [Frozen input lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_lock_20260926.json)
- [Analyzed report](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_20260926.json)
- [Six raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_workers_raw_20260926.json)
