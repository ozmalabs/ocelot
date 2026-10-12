# Scheduler checkpoint transfer v3 results

## Result

The expanded `RuleSchedulerCheckpointV2` passes the source-locked cross-family transfer panel. Both the productive CAN coactivation family (N=32, Q=128) and retinal percept synthesis (12 columns) pass at both fresh and post-call entry states: all 4/4 states exactly round-trip graph, ordered rules, scheduler state, and match the live global and per-rule counters and post-closure state. The independent analyzer passes all six registered gates with no errors.

The CAN productive call performs 61,056 candidate tests and 117,504 Term evaluations; replay matches those and all other recorded counters exactly. The retinal post-closure external activation change leaves one dirty rule, one dirty node, and five cursor entries. With predicate retraction enabled, replay restores its flag and the pending graph attribute-write journal; the call's 15 candidate tests, 48 Term evaluations, per-rule counters, and resulting state match the live call exactly. The first retinal call also reaches its productive closure and is exactly reproduced.

V2 of this panel failed before output because restore rejected the valid empty `empty_match_skips` vector when empty-match proof was disabled. The validator was corrected and v3 was freshly locked and run. Both failed v2 lock and v3 successful artifacts remain available.

## Limits and next gate

This provides independent synthetic transfer evidence across two authored rule families, including the previously uncovered dirty-node path. It does not estimate how often these scheduler states occur on natural tasks, establish a scale envelope, or demonstrate new-dimension learning. The checkpoint now includes relevant opt-in closure flags, active shape target, gamma residual state, dirty telemetry, and the pending attr-write log, but evaluation-cache entries and incremental per-edge deletion-version maps are still outside its state. Next add source-derived checkpoint coverage for these remaining state components, then capture natural task families before drawing broader engine-fidelity conclusions.

## Artifacts

See [preregistration](SUBSTRATE_SCHEDULER_CHECKPOINT_TRANSFER_V3_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/scheduler_checkpoint_transfer_v3.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_scheduler_checkpoint_transfer_v3.py), [source lock](../../../evaluation/substrate_capability/scheduler_checkpoint_transfer_v3_lock_20261004.json), [raw capture](../../../evaluation/reports/scheduler_checkpoint_transfer_v3_20261004.json), and [analysis](../../../evaluation/reports/scheduler_checkpoint_transfer_v3_analysis_20261004.json). The first two-family baseline is recorded in [v1 results](SUBSTRATE_SCHEDULER_CHECKPOINT_TRANSFER_V1_RESULTS_20261004.md).
