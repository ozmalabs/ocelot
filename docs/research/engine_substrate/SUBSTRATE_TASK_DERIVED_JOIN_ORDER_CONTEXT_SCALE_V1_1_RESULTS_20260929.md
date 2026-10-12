# Task-derived join-order context-scale v1.1 cost results

## Result

The preregistered timing replication completed across the same 216 fresh
process cells as v1. The independent analyzer passes **3,895/3,895 checks**;
source/native fingerprints, task and common-ground oracles, inert decoys,
installed-order readbacks, all ten fixed points, exact graph parity within
each context, and matcher-counter conservation remain valid.

The median call-boundary timings (microseconds) were:

| Decoys | Target `discourse_goal_select` add | Three lifecycle adds | Three removals | Ten audit-enabled closure checkpoints |
|---:|---:|---:|---:|---:|
| 0 | 190 wall / 196 CPU | 522 / 538 | 11 / 9 | 494 / 492 |
| 8 | 194 / 199 | 530 / 546 | 12 / 10 | 469 / 468 |
| 32 | 192 / 198 | 530 / 546 | 11 / 9 | 460 / 458 |

The target add includes the existing native relation-cardinality reorderer.
The near-flat medians over 0–32 disconnected decoys show no measurable
installation-cost growth at this small graph size. Wall-time tails are noisy:
the zero-decoy lifecycle-add maximum reaches about 2.9 ms while its median is
0.52 ms. Use CPU and repeated-cell distributions for follow-up; do not infer a
stable latency bound from these samples.

The lifecycle add calls re-install three rules in this replay, while the
closure column sums ten audit-enabled event closures. Their similar median
magnitudes describe this fixture and capture mode only. The benchmark does not
compare audit-on/off closure time, isolate cold startup, or measure the
production seed-loading path's marginal cost. It therefore does not establish
uninstrumented speed or an amortized advantage. The previous exact candidate
work result remains the stronger order-selection evidence ([v1 results](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_RESULTS_20260929.md)).

## Next gate

Run a paired instrumentation-on/off replay to estimate closure timing effects,
then measure the unmodified seed-load path and total end-to-end task cost. Keep
installation, context construction, event ingestion, and closure as separate
timers. After that, repeat on an independently authored task and match rule
with a different topology; the current disconnected decoys are synthetic and
cannot stand in for a second task family.

## Artifacts

- [v1 preregistration](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_PREREG_20260929.md)
- [v1.1 cost-capture amendment](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_1_AMENDMENT_20260929.md)
- [Runner](../../../scripts/substrate_task_derived_join_order_context_scale_v1_1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_join_order_context_scale_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_join_order_context_scale_v1_1_lock_20260929.json)
- [216-worker raw capture](../../../evaluation/reports/task_derived_join_order_context_scale_v1_1_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/task_derived_join_order_context_scale_v1_1_analysis_20260929.json)

Claim boundary: repeated Python/native rule-install API call timings and
audit-enabled closure timing for one small task family. No uninstrumented
latency, production seed-loading, natural-task, amortized-cost, optimizer, or
general tractability claim follows.
