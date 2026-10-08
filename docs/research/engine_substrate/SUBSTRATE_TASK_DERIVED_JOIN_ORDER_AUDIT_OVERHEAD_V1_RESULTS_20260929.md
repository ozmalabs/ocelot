# Task-derived join-order audit-overhead v1 results

## Result

The paired replay completed **30 pairs / 60 fresh processes**. Its independent
analyzer passes **934/934 checks**, including the task and common-ground
oracles, ten fixed points, exact paired graph digests and installed orders,
zero off-mode counters, and on-mode target-rule candidate work matching the
locked v1 reference.

Scale-counter instrumentation increased summed ten-checkpoint closure time in
all three contexts. Median on/off ratios were:

| Decoys | Wall ratio (on/off) | CPU ratio (on/off) | Median wall: off → on |
|---:|---:|---:|---:|
| 0 | 1.37× (range 1.15–1.53×) | 1.37× (1.16–1.54×) | 0.361 → 0.491 ms |
| 8 | 1.24× (1.15–1.37×) | 1.24× (1.15–1.37×) | 0.363 → 0.438 ms |
| 32 | 1.23× (1.07–1.53×) | 1.23× (1.08–1.53×) | 0.372 → 0.451 ms |

This makes the earlier audit-on closure times unsuitable as direct latency
estimates: in this task they were 23–37% higher by paired medians than the
counter-off arm. Counter-off still runs the same Python reset/snapshot API
calls and task harness, so the ratio estimates the marginal cost of enabling
these scale counters within this harness; it does not include all tracing
instrumentation and is not a general overhead factor. The absolute closure
times are for one small ten-event fixture.

## Limits and next gate

Ten pairs per context give a local overhead estimate with visible tails, not a
portable constant. Measure ordinary seed loading and end-to-end task execution
without test-harness rule reinstallation, then repeat on an independently
authored rule/task topology. Keep instrumentation-on work counts separate from
counter-off timing.

## Artifacts

- [Preregistration](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_AUDIT_OVERHEAD_V1_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_task_derived_join_order_audit_overhead_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_join_order_audit_overhead_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_join_order_audit_overhead_v1_lock_20260929.json)
- [60-worker raw capture](../../../evaluation/reports/task_derived_join_order_audit_overhead_v1_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/task_derived_join_order_audit_overhead_v1_analysis_20260929.json)

Claim boundary: paired scale-counter overhead for one frozen task and three
synthetic context sizes. No general audit overhead, ordinary boot cost,
production latency, throughput, or substrate-scale claim follows.
