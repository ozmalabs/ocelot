# Runtime audit mode probe v2 — results and limits (2026-10-04)

## Result

The source-locked single-worker probe is stable before and after execution. Its first request (`report your organisation`) still records 8,099 candidate tests, 86,114 Term evaluations, 5,680 per-rule rows, and 2,340 metadata rows although the process mode, Python-thread override, and per-rule mode all sample `(false, false, false)` before, after reset, and after the request. The audit-off zero-counter gate correctly fails. The second request has no work or audit rows. Since the base worker resets counters at each producer event, these first-request totals represent the final nested event window, not the whole request's native work; the original v1.4 totals must not be interpreted as full-request totals.

An opt-in native setter trace captures three repeated process/per-rule enable-disable windows on the first request, all on `ThreadId(1)`. Source tracing identifies their owner: `scripts/substrate_live_self_report_task_boundary_v2_1.py:125–129` wraps each `_record_live_goal_event` call by resetting counters, enabling aggregate and per-rule audit, taking snapshots, then disabling audit. The first request emits three such goal events; the second emits none. The v1.4 outer panel reused this instrumented worker, so its nominal audit-off arm was contaminated by the worker's nested producer-event measurement. This resolves the v1.4 audit-off anomaly as harness interference; it does not indicate an engine isolation defect.

## Consequence for the measurement programme

Keep v1.4 as historical diagnostic evidence, but do not use it for audit-on/off cost comparisons. V1.5 implements the needed worker path: it preserves the same task and graph semantics, delegates producer-event observations without nested scale-audit toggles, and passes audit-off zero-counter gates. Its results and remaining Term-attribution gap are in [v1.5 results](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_5_RESULTS_20261004.md).

The separate v1.4 audit-on Term attribution gap remains: each second audit-on prompt recorded 134 Term evaluations without a current rule attribution. This probe does not locate those call sites. Trace those Term invocations independently before claiming complete per-rule workload costs.

## Artifacts

- [Probe preregistration](SUBSTRATE_RUNTIME_AUDIT_MODE_PROBE_V2_PREREG_20261004.md)
- [Probe runner](../../../evaluation/substrate_capability/live_runtime_audit_mode_probe_v2.py)
- [Source lock](../../../evaluation/substrate_capability/live_runtime_audit_mode_probe_v2_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/live_runtime_audit_mode_probe_v2_20261004.json)

The runner exits nonzero because the preregistered zero-counter gate fails, as expected from the captured first-request work. This is a failed diagnostic gate with a resolved harness cause, not a failed source-stability or worker-completion gate.
