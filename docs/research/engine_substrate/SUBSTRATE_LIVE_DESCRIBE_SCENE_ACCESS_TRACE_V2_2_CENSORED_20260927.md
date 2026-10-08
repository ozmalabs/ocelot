# Live describe-scene access trace v2.2 censored runs (2026-09-27)

Neither v2.2 run provides locality or timing evidence. The first capture completed six workers in the mutable worktree, but failed source-stability and paired-semantic-parity gates. The second capture used an isolated source/runtime/seed snapshot and passed those integrity gates, but failed before the intended conversation task began.

## Mixed-worktree attempt

The source lock was valid for replicate 0 untraced. During the capture, the shared worktree's conversation sources changed: `substrate/world_adapter.py`, `domains/comprehend_text.py`, `domains/communication_evidence.py`, and `seeds/communication_intent_arbitration.json` had different hashes in later worker records. The first traced/untraced pair agreed on replies, full semantic graph, lifecycle projection, and shared Scene/Percept projection. Pairs 1 and 2 did not agree on graph/event projections despite matching replies and outcome gates. This shows the lock detects concurrent edits; it does not measure locality. The first run's raw rows were superseded by the isolated rerun and were not retained.

## Isolated snapshot attempt

All six workers ran from one immutable snapshot. The source lock was stable before and after every worker, and all three traced/untraced pairs matched whole-graph semantic hashes and task boundaries. The shared input projection reconciled to one Scene and three Percept nodes in every worker.

All six workers nevertheless timed out waiting for request A's `selection` event. Every request returned `I don't know 'describe' — what does it mean?`; no Goal producer events were recorded. An earlier three-process describe-scene lifecycle capture using the same prompt passed all five gates and returned the expected scene description, but its source lock differs on `world_adapter`, `conversation_action`, `boot_all`, and `reflective_faculty`. This is an observed source-state discrepancy; the experiment does not attribute the change to any one edit. The isolated run is a reproducible path failure for the exact prompt under its locked snapshot, not a locality result.

The independent analysis passes twelve integrity checks, confirming source stability and graph parity while explicitly confirming the selection timeout and source-state discrepancy. The runner exits nonzero when any required gate fails. Do not use either run's timing or event counts as locality evidence.

## Artifacts

- [Isolated snapshot raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_workers_raw_20260927.json)
- [Driver summary](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_censored_analysis_20260927.json)
- [Analyzer](../../../scripts/analyze_substrate_live_describe_scene_v2_2_censored.py)
- [Prior successful v1.2 capture](../../../evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_2_20260926.json)
- [Protocol](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_2_PREREG_20260927.md)
- [Isolated snapshot source lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_2_lock_20260927.json)

## Recovery gate

Inspect the differing conversation source states to identify why the same prompt no longer emits a Goal selection event. Then revalidate the route using the exact current accepted task form on an immutable snapshot. Keep the shared Scene/Percept input separate from A/B lifecycle ownership and retain exact whole-graph semantic parity. Only after the task path succeeds should selected access counts be interpreted.
