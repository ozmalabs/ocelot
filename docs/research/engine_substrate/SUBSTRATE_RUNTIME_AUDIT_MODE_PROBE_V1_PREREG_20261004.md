# Runtime audit mode probe v1 — preregistration (2026-10-04)

## Question

Why does the first request in live runtime closure panel v1.4 record scale-audit work in its audit-off arm? Specifically, do process-global mode, current-thread override, or per-rule mode remain enabled at the Python wrapper boundary or change during the ordinary live `WorldAdapter.converse` call?

## Method

Run the existing source-locked live-frame worker once in a fresh subprocess with the audit-off wrapper. At each intercepted `WorldAdapter.converse`, record `scale_audit_mode_snapshot()` before any change, after explicitly disabling global and per-rule modes and resetting counters, immediately after the ordinary conversation returns, and after taking the counter snapshot. Preserve the two requests, full worker payload, exception behavior, and native engine provenance. This is a diagnostic of gate state; it is not a cost comparison or a natural workload estimate.

## Gates

1. Native extension and all source inputs match the generated source lock before and after the run.
2. Worker exits successfully with the expected two request records and task result.
3. Every mode sample is a three-boolean tuple `(process_mode, thread_override, per_rule_mode)`.
4. The post-disable sample is `(false, false, false)` for each request.
5. Report counter totals by request and mode samples; do not claim the probe explains the v1.4 failure unless a mode sample or source-traced path demonstrates the transition.

## Scope limits

The snapshot reads thread-local state only on the Python calling thread. If native work is dispatched to Rayon, this probe does not sample worker-thread overrides. It also does not trace the call stack for Term evaluations that lack a current rule identity. A clean probe therefore does not validate audit-off isolation for every execution thread.

## Artifacts

Runner: `evaluation/substrate_capability/live_runtime_audit_mode_probe_v1.py`.
Lock: `evaluation/substrate_capability/live_runtime_audit_mode_probe_v1_lock_20261004.json`.
Capture: `evaluation/reports/live_runtime_audit_mode_probe_v1_20261004.json`.
