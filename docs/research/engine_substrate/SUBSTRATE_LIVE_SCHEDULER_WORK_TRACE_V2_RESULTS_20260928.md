# Live scheduler-work trace v2 results

Date: 2026-09-28

## Result

The preregistered three-worker live `describe_scene` replay passes all 13 independent analyzer checks. Each worker loads the full seed corpus, runs the same static/meter/mover scene request, and returns the expected reply. Source/native fingerprints are stable before and after each worker; all workers reproduce 21 operation IDs, identical aggregate and per-operation work rows, and zero trace drops.

For the selected graph scope, every scheduler counter reconciles exactly with the work trace in each worker:

| Metric | Scoped counter and trace units |
|---|---:|
| Scheduler passes | 37 |
| External-poll rule slots | 87,179 |
| Fixed-point probe slots | 1,172 |
| Dirty-vector slots | 87,179 |
| Selected rules | 54,085 |

All 15 deferred family/action comparisons (five queue families × enqueue, drain-batch, drained-item) also match exactly, including zeros for families inactive in the selected graph scope. The process-global audit still reports 39 scheduler passes and 16 framebuffer drain batches. The selected scope reports 37 passes and zero framebuffer drain batches. These global-minus-scope differences are not attributed by this experiment; they establish that process-global totals include activity beyond the selected scope.

The v1 serialized graph digest was removed as an equality gate because it includes noncanonical node IDs and differed across fresh workers. V2 checks the stable expected response and exact operation-work replication instead; it makes no full graph-equivalence claim.

## Claim boundary and next gate

This validates graph-scope counter parity for scheduler/deferred work inside active `run_rules` operations on one selected substrate during one authored dialogue route. It does not establish that the selected graph scope covers every substrate instance or all work in the request, nor trace recall for uninstrumented hooks, natural queue prevalence, frame locality, or scaling. The process-global framebuffer batches without a selected-scope counterpart should be traced to their owning graph/operation by capturing all live substrate scopes or adding a process-wide scope registry. Next quantify tracing overhead, cover a second task route, and join operation-level work to task-variable/domain interfaces before making a locality claim.

## Reproduction

The release wheel was built from the locked source and extracted to an isolated temporary package. Reproduce with:

```sh
SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_live_scheduler_work_trace_v2.py --lock

SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_live_scheduler_work_trace_v2.py

python3 scripts/analyze_live_scheduler_work_trace_v2.py
```

Artifacts: [preregistration](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V2_PREREG_20260928.md), [runner](../../../scripts/substrate_live_scheduler_work_trace_v2.py), [independent analyzer](../../../scripts/analyze_live_scheduler_work_trace_v2.py), [source/native lock](../../../evaluation/substrate_capability/live_scheduler_work_trace_v2_lock_20260928.json), [raw capture](../../../evaluation/reports/live_scheduler_work_trace_v2_20260928.json), and [analysis](../../../evaluation/reports/live_scheduler_work_trace_v2_analysis_20260928.json). The failed v1 parity gate and its scope diagnosis remain preserved in the [v1 amendment](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V1_AMENDMENT_20260928.md).
