# Unified five-family queue and mutation-work trace v1 results

**Result:** one source/native-locked positive-join workload exercises all five deferred queue families, operation-work tracing, target mutation, and trigger deletion with exact queue-counter reconciliation.

The panel has 27 fresh worker processes: `R={1,8,32}` writer/target pairs, `M={1,4,16}` join paths per writer, and three replications per cell. All **300/300 checks pass**. Audit-on and audit-off graph/report state match in every cell; closure reaches fixed point with zero budget overshoot; all R targets fire, all R trigger edges are deleted, and all R games receive four framebuffer cells. The work trace has no dropped rows and its queue units exactly match the independent scale-audit counters.

Per cell, RulePatch enqueues/drains once per writer because repeated bindings share one pending patch and duplicate enqueue is suppressed. `rule_edits`, `fb_samples`, `track_identity`, and `net_collapses` each enqueue/drain `R×M` items. Each of the five families drains in one batch. Combined queue-item work is therefore `R×(1+4M)` enqueues and the same number of drains; the trace also attributes one successful trigger deletion per writer, preventing another writer firing after mutation.

| R writers | Candidate tests, M=1 | M=4 | M=16 | Total queue items across all five families, M=1 / 4 / 16 |
|---:|---:|---:|---:|---:|
| 1 | 10 | 28 | 280 | 5 / 17 / 65 |
| 8 | 80 | 209 | 2,240 | 40 / 136 / 520 |
| 32 | 320 | 809 | 5,645 | 160 / 544 / 2,080 |

Scheduler passes remain three in every cell; selected-rule, dirty-vector, and external-poll work each equal `6R`, independent of M for this construction. Candidate tests increase with M, but the curve is not uniform across R; the data do not establish an asymptotic law. This is a bounded synthetic fixture with static local framebuffer input, not natural queue prevalence, general throughput, or a safe partition proof. It captures all five families in one full-closure trace; separate panels still provide the scoped-pending/fallback evidence.

See the [v1 preregistration](SUBSTRATE_ALL_QUEUE_MULTIPLICITY_WORK_TRACE_V1_PREREG_20261001.md), [runner](../../../scripts/substrate_all_queue_multiplicity_work_trace_v1.py), [analyzer](../../../scripts/analyze_substrate_all_queue_multiplicity_work_trace_v1.py), [source/native lock](../../../evaluation/substrate_capability/all_queue_multiplicity_work_trace_v1_lock_20261001.json), [raw capture](../../../evaluation/reports/all_queue_multiplicity_work_trace_v1_workers_20261001.json), and [analysis](../../../evaluation/reports/all_queue_multiplicity_work_trace_v1_analysis_20261001.json).
