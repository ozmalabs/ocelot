# Live `describe_scene` access trace v1 (2026-09-26)

## Result

The three source-locked concurrent workers passed all eight inherited gates: distinct processes, joined threads without errors, stable inputs, B serialization while A was paused, event identity/order/lifecycle, reply parity, repeated normalized behavior, and repeated full-boundary/shared structure. Each worker captured exactly 1,870,767 selected native access events in 54,117 aggregated rows across 410 rule IDs, with zero dropped rows. The traces were identical across the three workers.

The task projections are small (A owns 7 nodes; B owns 6), but the trace is broad. Events whose concrete node or peer touched A's owned set totaled 5,562, across 228 rows and 73 rule IDs; B's owned set was touched by 3,011 events across 216 rows and 71 rule IDs. Six of A's seven owned nodes and five of B's six were named in at least one recorded event. Twelve events touched both sets, all represented by one aggregated row. The remaining 1,862,206 events touched neither owned set. Across the complete trace, 1,801,892 events were `term_attr_read` (96.3%); leading sources were the three scene-recognition rules and `curiosity_targets_ambivalent_nodes`.

This is evidence that a small operational task cut does not imply that the current global closure performs only task-local work. The trace spans both serialized requests and closure they trigger, and its accesses may include global candidate scans. It does not show that each such event is semantically necessary, nor that a partitioned scheduler could safely omit it. The operationally relevant owned-event count is about 0.46% of captured events, but that ratio is specific to this authored fixture and this partial trace.

## Interpretation and limits

This records selected native operations, not complete read/write footprints. Known gaps include specialized graph scans, some aggregate/traversal Term implementations, and host-side mutations. A missing row is not evidence of absence. The two requests share one substrate and are serialized; aggregate trace rows do not attribute each access to A versus B. Counts are not a runtime overhead measurement, and the crosswalk is not a treewidth result or a semantic proof of frame independence. Trace enablement is opt-in and process-global.

The result advances the task-boundary gate by pairing live owned vertices with concrete rule-attributed accesses. The next useful experiment is a paired traced/untraced semantic replay with trace-scope timing and fuller access coverage, followed by a candidate partition that preserves direct A/B edges and shared external state. It must compare whole-graph closure, lifecycle and replies, not only owned projections, and charge partition discovery, boundary exchange, wakeup, and scheduling.

## Reproduction and artifacts

- [Amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V1_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_describe_scene_access_trace_v1.py)
- [Input lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v1_lock_20260926.json)
- [Analyzed report](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v1_20260926.json)
- [Raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v1_workers_raw_20260926.json)

Run with `PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_live_describe_scene_access_trace_v1.py` after confirming the frozen lock remains current.
