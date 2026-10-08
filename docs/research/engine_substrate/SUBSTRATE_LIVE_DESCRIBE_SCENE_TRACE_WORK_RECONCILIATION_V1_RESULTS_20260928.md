# Live describe-scene trace/work reconciliation v1 results

Date: 2026-09-28

## Scope and method

This post-hoc analysis crosswalks the retained three-worker `describe_scene` whole-request capture against its native matcher, Term, scheduler, deferred-queue, and graph-effect counters. It does not rerun the task or add event instrumentation. Its input is the source-locked v1.1 capture; the analyzer hashes that file and requires exactly three audited plus three untraced workers.

## Results

All three audited workers reproduce 1,140,892 weighted trace events in 53,215 distinct rows, with zero dropped events and identical event-kind, missing-field, counter, and effect-reconciliation profiles. The trace includes 18 kinds in this fixture. Five graph-effect families match their independent native counters exactly in every worker:

| Trace event | Trace count | Native counter | Counter value |
|---|---:|---|---:|
| `effect_edge_upsert` | 190 | `rule_effect_edge_insert_attempts` | 190 |
| `effect_edge_delete` | 1 | `rule_effect_edge_deletes` | 1 |
| `effect_node_mint` | 41 | `rule_effect_node_inserts` | 41 |
| `effect_node_delete` | 52 | `rule_effect_node_delete_attempts` | 52 |
| `effect_attr_write` | 418 | `rule_effect_attr_set_attempts` | 418 |

The independent whole-request counters report 678,432 candidate tests. The analyzer independently sums 678,013 per-clause candidate tests; adding the explicit unattributed count of 419 (0.062%) exactly reconciles to the total in each worker. It also reports 3,676,862 Term evaluations, including 2,461 unattributed (0.067%); Term-unit work has zero unattributed units. Scheduler counters record 86,632 dirty-vector slots, 86,632 external-poll slots, 1,219 fixed-point probes, 52,916 selected rules, 52,961 rule enumerations, and 39 passes. There is no corresponding scheduler event family in this trace, so those totals are an independent workload account, not trace-to-event reconciliation. Deferred framebuffer queue drain batches are 16 in each audited worker; measured drain time varies 720–760 ns and is kept as timing data, not a semantic invariant.

The captured rows aggregate by RuleUID and event tuple but do not retain the active scope ID. Many event classes intentionally lack one or more node/resource/peer fields: for example, every attribute read omits `peer`, all 528 index-query events omit `node`, and query marker events are not concrete node accesses. Trace UID-zero/scope-mismatched work is not represented at all. Three untraced controls have zero trace rows, but their raw capture does not include the same scale-counter profile, so this report does not infer instrumentation overhead or audited/untraced work parity.

## Interpretation and next gate

This closes a narrow but useful accounting check: selected graph-effect trace rows reconcile exactly with five independent mutation counters, while matcher/Term unattributed totals and scheduler/deferred work are explicit. It does not provide a general trace-recall percentage, identify all no-ID or out-of-rule operations, validate each rule's access scope, or recover task-variable/domain interfaces. Next capture scheduler and queue work with stable operation IDs and scope, preserve excluded/no-ID classes, and map independently counted accesses onto candidate frames before any locality claim.

## Reproduction and artifacts

Run:

```sh
python3 scripts/analyze_live_describe_scene_trace_work_reconciliation_v1.py
```

Artifacts: [analyzer](../../../scripts/analyze_live_describe_scene_trace_work_reconciliation_v1.py), [machine-readable analysis](../../../evaluation/reports/live_describe_scene_trace_work_reconciliation_v1_20260928.json), and [source capture](../../../evaluation/reports/live_describe_scene_whole_request_audit_v1_1_workers_raw_20260927.json).
