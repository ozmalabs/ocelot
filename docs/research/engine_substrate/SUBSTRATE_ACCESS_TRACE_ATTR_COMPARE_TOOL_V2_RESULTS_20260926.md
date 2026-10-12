# Access-trace attribute comparison and tool dispatch v2 results

Date: 2026-09-26

## Result

Three fresh worker processes each ran plain/traced twins for changed and unchanged `SetAttrIfDifferent` values and one matched `UseTool` dispatch. The runner checks pass in all 34 cells. An independent analyzer passes 51/51 checks, including current source/native lock, worker replication, exact final values and fixed-point semantics, disabled-trace isolation, event counts, and capture-log integrity.

Both conditional-attribute cases emit exactly one `effect_attr_compare_read` row. Only the changed case emits `effect_attr_write`; the unchanged case emits no write. The tool fixture calls the registered Python handler exactly once, and emits one `term_tool_dispatch` event with the tool name. Plain arms emit no trace rows. The new event kinds are default-off and do not change observed semantics in these fixtures.

## Interpretation and limits

This closes two specific trace-visibility gaps: one conditional old-value read and the native boundary immediately before callback dispatch. The dispatch event does not observe callback-internal graph reads/writes or external side effects. Scheduler activity, post-rule deferred queues, matcher rejected-edge identities, and operations outside an active RuleUID remain unattributed or partial. These mechanism controls do not estimate trace overhead, real-task frequency, or complete access recall.

## Artifacts

- [Preregistration](SUBSTRATE_ACCESS_TRACE_ATTR_COMPARE_AND_TOOL_DISPATCH_V2_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_access_trace_attr_compare_tool_v2.py)
- [Independent analyzer](../../../scripts/analyze_substrate_access_trace_attr_compare_tool_v2.py)
- [Run report](../../../evaluation/reports/substrate_access_trace_attr_compare_tool_v2_20260926.json)
- [Independent analysis](../../../evaluation/reports/substrate_access_trace_attr_compare_tool_v2_analysis_20260926.json)
- [Raw workers](../../../evaluation/reports/substrate_access_trace_attr_compare_tool_v2_workers_raw_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/access_trace_attr_compare_tool_v2_lock_20260926.json)
- [Source coverage inventory](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_20260926.json)

## Next measurement

Attribute operation and scheduler/queue work outside active RuleUIDs, including deferred TrackIdentity, NetCollapse, and framebuffer sample drains. Preserve originating-rule identity where available and retain an explicit unattributed bucket otherwise. Validate counters against independent queue lengths, mutation deltas, and traced/untraced state parity before using them in task partition analysis.
