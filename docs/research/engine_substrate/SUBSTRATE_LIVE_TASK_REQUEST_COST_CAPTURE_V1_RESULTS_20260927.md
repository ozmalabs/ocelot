# Live task request-cost capture v1 results

Date: 2026-09-27 local

## Integrity and task outcome

Three fresh current-source workers completed the frozen two-request `describe_scene` schedule under an outermost conversation-lock counter interval. The corrected independent analysis passes **36/36 capture-integrity checks**. Worker-start, worker-finish, and post-run source/native fingerprints match the saved lock. Thread scheduling, serialized order, distinct goal identity, lifecycle, pause, final semantic graph, and cross-worker reply-pair reproduction pass.

The legacy exact-reply gate remains **failed** for request A: it returns the gap response about lacking a faculty for “see.” Request B returns the registered scene-description baseline. This is a work and task-failure characterization, not a passing capability result. The first execution was invalidated because `substrate/world_adapter.py` changed during the run; its raw payload was overwritten by the valid rerun, with the invalid attempt’s SHA-256 recorded in the amendment. The valid capture was re-locked and rerun after a stable fingerprint check ([capture amendment](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_AMENDMENT_20260927.md)). An analyzer lock-envelope comparison defect was corrected after capture; the raw worker data were unchanged ([analysis amendment](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_ANALYSIS_AMENDMENT_20260927.md)).

## Request-lock matcher work

| Request | Candidate tests per worker (all three repeats) | Median | Per-rule sum | Per-clause sum |
|---|---:|---:|---:|---:|
| A | 677,795 / 677,795 / 677,795 | 677,795 | 677,795 | 677,795 |
| B | 842,748 / 842,748 / 842,748 | 842,748 | 842,748 | 842,748 |

The combined pair costs 1,520,543 candidate tests per worker, exactly reproduced in three fresh processes. These are native candidate tests within the full outermost conversation-lock interval, rather than the six event closures counted in the previous capture. The interval includes closure work between producer events. It excludes Python work before lock acquisition, after lock release, boot, and B's wait to acquire the lock.

A cross-check invalidates rule-name and arity attribution. Although the per-rule and per-clause sums each equal global `cand_tested`, the per-clause table contains positions outside the mapped match arity: 41 anomalous rows for A and 28 for B per worker (123 and 84 across three workers). For example, RuleIdx 0 maps to `abandon_goal_on_no_movement` with arity 1, while its clause counters include positions 1–11. The analyzer therefore reports `rule_attribution_gate_pass=false`; the arity shares and top-rule names in the raw attribution are diagnostic only and must not be interpreted.

The source explains a likely instrumentation gap: [`scale_audit.rs`](../../../runners/dsl/src/scale_audit.rs) associates matcher counts with a thread-local `CURRENT_RULE`, while [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs) uses Rayon workers in `collect_batch_bindings_parallel`. The clause-position mismatch is direct evidence that the current per-rule attribution is not reliable for this run. The global request-boundary `cand_tested` totals remain independently collected, stable across workers, and conserve to the per-rule/per-clause aggregate counts; they are the valid matcher-work result. Attribution should be repaired by propagating rule context into parallel workers or by returning worker-local keyed counts, then remeasured before making claims about cheap cuts or dominant rules.

## Timing and interpretation

The lock interval and whole-call wall/CPU timings are retained in raw data. Both are audit-instrumented and should be treated as diagnostic. Full-call timings include lock wait; lock interval excludes that wait. Neither is uninstrumented latency nor throughput evidence. The reply failure means no cost/quality success claim follows.

This capture establishes exact request-lock totals for one full-profile conversation, but currently cannot assign them safely to rules or match arities. It does not prove frame locality or polynomial scaling. The next engine-measurement step is to repair parallel per-rule audit context, validate attribution on both serial and Rayon matcher paths, then repeat this capture and only then design a semantics-preserving optimization around confirmed hot rules. A distinct task family and graph topology remain necessary; track request-A reply quality separately. Keep request-A reply quality as a separate remediation/evaluation track.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_PREREG_20260927.md)
- [Source-change amendment](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_AMENDMENT_20260927.md)
- [Analysis amendments](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_ANALYSIS_AMENDMENT_20260927.md)
- [Driver](../../../scripts/substrate_live_task_request_cost_capture_v1.py)
- [Worker](../../../scripts/substrate_live_task_request_cost_capture_v1_worker.py)
- [Independent analyzer](../../../scripts/analyze_substrate_live_task_request_cost_capture_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/live_task_request_cost_capture_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_live_task_request_cost_capture_v1_workers_raw_20260927.json)
- [Integrity and work analysis](../../../evaluation/reports/substrate_live_task_request_cost_capture_v1_analysis_20260927.json)
- [Capture manifest](../../../evaluation/reports/substrate_live_task_request_cost_capture_v1_20260927.json)

Claim boundary: three fresh-process repeats of one authored serialized `describe_scene` fixture; exact outer lock-interval global candidate accounting; per-rule/per-clause totals conserve arithmetically, but rule attribution fails the clause-arity cross-check. Request A's exact reply gate fails. No natural-task prevalence, general frame-locality, commodity-scale, or uninstrumented performance claim follows.
