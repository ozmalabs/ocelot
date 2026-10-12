# Live describe-scene access trace v2.3: censored run (2026-09-27)

The six-worker capture is censored and supplies no locality or performance evidence. All workers retained the locked source snapshot and each traced/untraced pair had identical final graph semantic hashes. However, all six failed before request A reached `selection`, emitted no `_record_live_goal_event` producer work, and ended with no request-bound Goals. The access rows and timing fields are instrumentation artifacts from an incomplete lifecycle and must not be interpreted as successful request cost.

An independent analyzer passes nine integrity checks: worker/arm counts, source-lock stability, paired graph parity, joined workers, and the uniform lifecycle failure. This verifies the censoring classification only.

A separate two-request diagnostic exercised the observed lock proxy, audit wrapper, and nested public lock together, without access tracing or a selection pause. Both requests completed on that diagnostic's stable source snapshot, with expected replies and resolved Goals. However, its `world_adapter.py` and `conversation_action.py` hashes differ from v2.3's locked snapshot. This is not a controlled reproduction or isolation of the v2.3 failure; source changes confound the comparison. The cause remains unresolved. A valid follow-up must freeze one immutable source snapshot and factorially toggle the hooks and driver schedule on that same snapshot.

## Artifacts

- [v2.3 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_3_PREREG_20260927.md)
- [censored analyzer](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_3_censored.py)
- [independent analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_3_censored_analysis_20260927.json)
- [raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_3_workers_raw_20260927.json)
- [summary report](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_3_20260927.json)
- [combined-hooks protocol](SUBSTRATE_DESCRIBE_SCENE_MEASUREMENT_HOOKS_COMBINED_DIAGNOSTIC_V1_PREREG_20260927.md)
- [combined-hooks report](../../../evaluation/reports/describe_scene_measurement_hooks_combined_diagnostic_v1_20260927.json)
