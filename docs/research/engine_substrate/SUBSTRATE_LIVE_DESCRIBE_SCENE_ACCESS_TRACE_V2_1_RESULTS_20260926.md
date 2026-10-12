# Live `describe_scene` per-request access trace v2.1 (2026-09-26)

## Result on the current adapter source

After the v2 capture, `substrate/world_adapter.py` changed to serialize public adapter transactions through a shared reentrant lock and trim allocator-free pages after completed conversations. The v2 capture remains valid for its recorded source, but its lock no longer describes the current worktree. V2.1 repeats the experiment against the current source and verifies the frozen lock still matches at report time.

Three traced/untraced pairs ran in six fresh processes, with arm order shuffled. All eight gates pass: distinct workers, joined threads, stable start/end inputs, the serialized A/B schedule, reply and Goal lifecycle parity, exact task-boundary and semantic graph parity within pairs, two nonempty per-request traces with no drops, no trace rows in untraced arms, and reconciliation of trace totals. Each arm has 25,147 nodes and 11,798 edges. Traced and untraced replies, event sequences, Goal projections, task cuts, and normalized whole-graph signatures match in all pairs.

Each traced request reaches all 410 loaded rule IDs. Request A records 951,567 selected native events in 53,164 aggregated rows. Request B records 919,200 in 36,007 rows. No rows are dropped. `term_attr_read` dominates both requests. In A's interval, 3,481 events touch A's seven owned nodes and none touch B's six. In B's interval, 2,081 events touch A-owned nodes and 3,011 touch B-owned nodes. These concrete accesses show cross-owner interaction in this schedule, while the incomplete trace cannot establish the full dependency relation.

## Tracing cost

Across three pairs, median complete-call times were:

| Request | Traced wall | Untraced wall | Traced thread CPU | Untraced thread CPU |
|---|---:|---:|---:|---:|
| A | 10.636 s | 10.660 s | 10.559 s | 10.570 s |
| B | 0.830 s | 0.682 s | 0.433 s | 0.347 s |

The request lock intervals have median wall/CPU times of 10.605/10.527 s for A and 0.415/0.404 s for B. B's complete call includes time outside its interval, including lock wait and surrounding adapter work. The B timing difference is consistent with trace overhead of roughly 22–25% in this small panel. A's total duration is dominated by work common to both arms, and its traced median is marginally lower. Three pairs do not provide a precise or general overhead estimate.

The semantic graph signature includes every node ID/type, all attributes except execution `ts` and `runtime_s` on `SystemModel` diagnostics, and every typed edge. Raw graph hashes differ due to those timing fields; normalized signatures match. The omitted values are execution metadata, not graph structure used by this comparison.

## Interpretation

Small task-owned graph cuts coexist here with about 1.87 million selected native events across the two requests. B's interval reads nodes assigned to A's set as well as its own. This challenges an assumption that per-task closure is already local in the current full-seed runtime. It does not show that all recorded work is necessary, that an alternative scheduler can omit it, or that these counts represent natural workloads. Specialized term scans and host-side paths remain outside the trace.

## Reproduction artifacts

- [Amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_1_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_describe_scene_access_trace_v2_1.py)
- [Current-source input lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_1_lock_20260926.json)
- [Analyzed report](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_20260926.json)
- [Six raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_workers_raw_20260926.json)

The original v2 trace results are retained separately as a valid capture on their recorded earlier `WorldAdapter` source; v2.1 is the current-source result.
