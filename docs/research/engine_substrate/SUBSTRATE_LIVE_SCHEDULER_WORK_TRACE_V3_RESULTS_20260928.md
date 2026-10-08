# Live scheduler-work trace v3 results

Date: 2026-09-28

## Result

The all-scope `run_rules` replay reproduces two graph scopes and 22 operation IDs in each of three fresh workers. For both scopes, traced scheduler/deferred rows match the new scoped-counter snapshot exactly. However, the preregistered process-global conservation gate fails on 16 framebuffer drain batches: all-scope tracing reports no framebuffer drain rows, and summed run-rules scoped counters report zero, while the legacy process-global audit reports 16. All other scheduler/deferred global totals reconcile.

The discrepancy led to a source review of alternate drain paths. `apply_rule_once` and `apply_rule_batch` call `apply_pending_fb_samples()` after one-shot execution, outside the `run_rules` operation interval. The trace correctly omitted these events under its original operation contract; the remaining gap was the missing one-shot operation attribution, rather than an unobserved graph scope during the fixed-point route.

## Claim boundary and follow-up

V3 confirms graph-scope parity for all observed `run_rules` work and identifies an explicit operation-boundary gap for framebuffer drains. It does not assign those 16 drains to an owner. V4 extends operation IDs and typed markers to single-rule and batch-rule application and tests all-scope global conservation ([v4 protocol](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V4_PREREG_20260928.md), [v4 results](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V4_RESULTS_20260928.md)).

Artifacts: [preregistration](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V3_PREREG_20260928.md), [runner](../../../scripts/substrate_live_scheduler_work_trace_v3.py), [analyzer](../../../scripts/analyze_live_scheduler_work_trace_v3.py), [lock](../../../evaluation/substrate_capability/live_scheduler_work_trace_v3_lock_20260928.json), [raw capture](../../../evaluation/reports/live_scheduler_work_trace_v3_20260928.json), and [analysis](../../../evaluation/reports/live_scheduler_work_trace_v3_analysis_20260928.json). The failed gate is retained in the machine analysis.
