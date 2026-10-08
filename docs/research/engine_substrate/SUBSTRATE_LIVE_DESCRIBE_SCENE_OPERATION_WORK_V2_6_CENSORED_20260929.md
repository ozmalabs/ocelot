# Live describe-scene operation-work capture v2.6 — censored

**Status:** diagnostic capture; preregistered confirmation failed. Retain all counters and worker records, but do not use them as a source-current capability estimate.

## Capture and failed gates

The six-process v2.6 run collected per-request native operation-work snapshots for all three traced workers. Work rows reconcile with per-request and process totals; every work-trace drop count is zero; untraced arms have empty work streams; all work kinds have current source definitions. Traced and untraced arms within each v2.6 replicate pass exact semantic and whole-graph parity.

The run fails `source_stable_workers_and_postrun`: two untraced workers detected file changes during capture. For replicate 1, `domains/discourse_state.py` and `seeds/communication_intent_arbitration.json` changed between worker start and finish. Replicate 2 detected a change to `seeds/episodic_working_memory_core.json`. These are outside the measurement harness's authorized output paths; the run preserved them and did not restore either version.

The preregistered comparison with v2.5 also fails for replicate 1: its traced whole-graph semantic digest and request-B boundary differ from the v2.5 worker. The v2.5 and v2.6 locks already identify distinct source snapshots for `domains/discourse_state.py` and `seeds/communication_intent_arbitration.json`, so this is not an instrumentation-only comparison. Do not infer that the work-counter read caused the difference.

## Diagnostic work rows

Across all three traced workers, the recorded counters repeat identically:

| Request | Distinct operations | Work rows | Scheduler passes | Selected-rule slots | Dirty-vector slots | External-poll slots | Fixed-point-probe slots |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 21 | 126 | 37 | 54,371 | 87,734 | 87,734 | 1,172 |
| B | 13 | 78 | 24 | 37,442 | 57,096 | 57,096 | 1,045 |

All rows have producer rule UID 0, which the native API defines as work outside an active rule context. These are independent instrumented counters, not cycles or elapsed time; the columns must not be added as if they measured one common unit. The values are useful for selecting the next probe: scheduler pass/slot work is measurable but cannot yet be mapped to a request-local frame or to individual rule candidate work.

## Next action

Keep the v2.6 raw capture and lock immutable. Re-run the operation-work study only after the source writers settle, with a new version and source lock. Before spending another long run, compare its full source closure to the v2.5 baseline and either choose a baseline from the same exact source snapshot or explicitly preregister the source changes as a new workload. Preserve exact within-pair graph parity, and add direct operation-work reconciliation and scope ownership before making tractability claims.

## Artifacts

- Protocol: [v2.6 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_OPERATION_WORK_V2_6_PREREG_20260929.md).
- Runner: [v2.6](../../../scripts/substrate_live_describe_scene_operation_work_v2_6.py); analyzer: [v2.6 analysis](../../../scripts/analyze_substrate_live_describe_scene_operation_work_v2_6.py).
- Lock: [v2.6 source lock](../../../evaluation/substrate_capability/live_describe_scene_operation_work_v2_6_lock_20260929.json); capture: [summary](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_20260929.json), [raw workers](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_workers_raw_20260929.json); [independent analysis](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_6_analysis_20260929.json).
