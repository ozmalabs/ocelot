# Connected-conversation access-trace panel v1.3 results

Date: 2026-10-03
Status: runner checks and independent analysis pass.

## Result

Three fresh workers replayed the same four task cases twice from fresh worlds: with concrete runtime access tracing disabled and enabled. Across all 12 worker/case pairs and 198 closure checkpoints per arm, the final graph and every checkpoint graph digest match exactly between trace-off and trace-on. All closures reach fixed point, all goals resolve, the static access signatures agree between arms, trace attribution resolves every event to one of four loaded discourse rules, and no trace rows are dropped.

The trace-on arm records 5,448 distinct aggregated event rows with multiplicity 6,240:

| Operation kind | Event multiplicity |
|---|---:|
| `term_attr_read` | 4,080 |
| `effect_attr_compare_read` | 480 |
| `effect_attr_write` | 480 |
| `pattern_edge` | 576 |
| `term_edge_read` | 144 |
| `effect_edge_compare_read` | 240 |
| `effect_edge_upsert` | 192 |
| `effect_edge_delete` | 48 |

Of these observed accesses, 720 have two endpoints owned by the same task frame; 5,520 have one task-owned endpoint and one shared/unowned endpoint. No observed access joins two differently owned task nodes. Each of the four loaded rules has bounded static read/write signatures with no wildcard flag. Their reads cover event index/kind/lifecycle attributes and the `for_goal`, `has_active_goal`, `has_event`, and `originated_in` relations; effects update goal lifecycle/status attributes and `transitioned_by`, `has_active_goal`, and `has_closed_goal` relations.

This is paired state-preservation evidence for tracing on the current native/source build. The 2026-09 historical capture does not match: native extension, build manifest, Rust source, and discourse materializer hashes have all changed. Therefore historical graph equality is not claimed. The paired run took 4.02 s wall time and 3.49 s aggregate parent-plus-worker CPU, with 50.3 MiB peak RSS on the recorded host. These instrumented timings are descriptive, not a speed comparison.

## Interpretation and limits

The observed task-owned accesses do not cross directly between frames, but nearly all touch shared/unowned state. The producer-derived frame interaction graph is still complete because shared boundary nodes couple every frame in the selected workloads. Static access signatures and concrete traces together are better evidence than the full-node projection, but the trace implementation is explicitly partial. These results do not prove that the captured access set is complete, that shared boundary state can be safely factored, or that partitioned closure preserves all outcomes. They do not estimate natural conversation prevalence or show a speedup.

The next engine gate should make shared boundary state explicit as an interface and compare monolithic versus partitioned closure from identical snapshots. Include different event orderings, shared addressee/common-ground interactions, and high-coupling controls; verify exact graph/goal parity, dynamic updates, delete/reuse behavior, and interface maintenance cost. Keep a host/native work audit in scope because rule-level event traces do not account for all work outside rule contexts.

## Provenance

- [Method](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_METHOD_20261003.md)
- [v1 startup failure](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_FAILURE_20261003.md)
- [v1.1 source-drift amendment](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_1_AMENDMENT_20261003.md)
- [v1.2 analyzer amendment](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_2_AMENDMENT_20261003.md)
- [v1.3 analyzer amendment](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_3_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3_lock_20261003.json)
- [Capture](../../../evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_20261003.json)
- [Original analysis output](../../../evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_analysis_20261003.json) (repaired after repeat-run serialization issue; see amendment)
- [Corrected independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_3_1.py)
- [Corrected independent analysis](../../../evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_1_analysis_20261003.json)
- [Analysis serialization amendment](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_3_1_AMENDMENT_20261003.md)

V1, v1.1, and v1.2 are retained as explicit iterations. V1 stopped before workers due to a missing import; v1.1 collected accesses but used a stale historical state as its parity control; v1.2 paired correctly but its analyzer expected 36 instead of 12 comparison rows. Only the v1.3 capture and analysis are confirmatory for trace-on/trace-off state parity.
