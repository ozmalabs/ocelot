# Live scheduler-work trace v1 amendment

Date: 2026-09-28  
Status: post-capture amendment; the original parity gate remains failed and the raw capture is unchanged.

## Observed limitation

The preregistered analyzer required graph-scope work rows to equal scale-audit totals. The three-worker capture does not satisfy that gate: the work trace reports 37 scheduler passes, 87,179 external-poll slots, 1,172 fixed-point probes, 87,179 dirty-vector slots, and 54,085 selected rules, while process-global scale-audit counters report 39, 87,187, 1,174, 87,187, and 54,093. The scale audit also reports 16 framebuffer drain batches and no matching framebuffer drain rows in the selected graph-scope work trace.

Source inspection explains why the comparison is invalid as a scope-parity test: `scale_audit` accumulators are process-global atomics/maps without a graph-scope key, while `runtime_work_trace_snapshot()` filters rows to one substrate scope. The live request path can therefore contribute counters from other substrate instances to the aggregate. The capture establishes a scope-attribution gap; it does not identify which untraced instance owns each extra operation or queue drain.

The graph hash also differs in one worker because the runner hashes serialized node IDs and edges directly; this is not a canonical graph-isomorphism digest. Replies, per-operation work rows, and aggregate work totals match across workers. The raw report is retained as captured; no failed gate is reclassified as a pass.

## Amended analysis

The v1.1 analyzer treats source stability, fresh workers, expected reply, nonempty trace, no drops, and worker-to-worker operation-work equality as integrity/reproducibility checks. It reports scale-audit deltas and queue-family discrepancies as diagnostics, not parity passes. It does not assert terminal graph equivalence from the noncanonical hash.

## Follow-up result: v2 scoped counters

V2 adds graph-scoped scheduler/deferred counters while preserving legacy global totals. On the same live route, scoped counters exactly match work-trace rows for all scheduler metrics and all five queue families in three fresh workers. The original v1 capture and failed gate remain unchanged. This closes selected-scope parity, but not whole-request attribution: process-global audit totals still include 16 framebuffer drain batches absent from the selected graph scope. See [v2 results](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V2_RESULTS_20260928.md) and its [analysis](../../../evaluation/reports/live_scheduler_work_trace_v2_analysis_20260928.json). Canonical task-state comparison remains separate if full graph parity is claimed.

V3 established that the remaining 16 framebuffer batches were outside `run_rules`; source review found one-shot `apply_rule_once`/`apply_rule_batch` drain paths. V4 adds all-scope work capture and typed operation IDs for `run_rules`, `apply_rule_once`, and `apply_rule_batch`. Across three workers, all 67 observed operations are typed; per-scope totals and summed totals exactly match process-global scheduler/deferred counters, including assignment of the 16 framebuffer batches to two scopes. This closes the named scheduler/deferred operation-accounting gap for the measured route, subject to the V4 claim boundary ([v3 results](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V3_RESULTS_20260928.md), [v4 results](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V4_RESULTS_20260928.md)).
