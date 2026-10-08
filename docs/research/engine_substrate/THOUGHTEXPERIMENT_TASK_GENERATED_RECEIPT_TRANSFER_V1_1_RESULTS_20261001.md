# Task-generated residual transfer v1.1 — results

**Status:** all semantic and task-oracle gates pass across eight fresh workers and 24 task episodes (three arms per worker).

Each worker replayed the frozen ten-event common-ground task through ordinary direct closure, eager-copy branch plus journal/adoption, and shared-snapshot branch plus journal/adoption. The 80 branch-produced event receipts in each receipt arm match the producing branch after guarded adoption, and all event/goal identities, per-event closure progress, canonical graph states, expected two-goal paths, shared commitments, and terminal fixed points agree with the direct arm. Both receipt arms produce 48 nonempty event receipts across their 80 task events, with 128 total recorded graph effects per arm. Native/source fingerprints remained stable across all workers.

## Timing

| Arm | Median measured episode route | Range | Median branch setup | Median journal readout | Median receipt adoption | Median closure |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 5.62 ms | 4.43–16.41 ms | — | — | — | 0.33 ms |
| Eager receipt | 13.65 ms | 7.40–17.64 ms | 1.40 ms | 0.61 ms | 1.95 ms | 0.36 ms |
| Shared-snapshot receipt | 11.01 ms | 7.11–12.98 ms | 0.53 ms | 0.57 ms | 1.68 ms | 0.41 ms |

The episode route includes task fixture loading, adapter/seed setup, event construction, branch setup where applicable, closure, journal readout, adoption, and terminal probe. Python module startup is measured separately (76.84 ms median per worker); canonical-state serialization used for oracle checks is excluded from the route-stage sum. Eight workers give limited timing precision. On this task, the shared-snapshot receipt route is about 1.24× faster than eager-copy receipt/adoption, while direct execution is about 1.96× faster than the shared receipt route. This is correctness/consumer-transfer evidence, not an end-to-end speedup over ordinary task execution.

## Representation caveat and scope

Canonical node/edge facts match at every event, and the producing branch matches the adopted primary in every receipt event. Full serialized graph wire order differs from Direct in 32/80 event states for each receipt arm, due to edge-order changes during adoption. Preserve this as an observable compatibility issue; do not describe canonical parity as byte-for-byte graph parity. Source inspection identifies a likely direct mechanism: `graph_diff` sorts `edges_added` by `(src,type,tgt)`, `apply_graph_delta` restores them in receipt order, and `graph_to_value` serializes live edge-slab order. This makes receipt order canonical while Direct retains mutation order. The capture did not retain full per-event graphs, so the source mechanism explains the direction but is not a byte-level reconstruction of every differing event. See [`graph_diff` and `apply_graph_delta`](../../../runners/dsl/src/persist.rs) and [`graph_to_value`/slab iteration](../../../runners/dsl/src/graph.rs). The workload is one existing authored task fixture and was held out from the synthetic residual-family benchmark design; it is not a natural-task sample. Concurrent writers, authorization quality for arbitrary proposals, large-graph scaling, and serving-runtime integration remain unmeasured.

The initial v1 capture remains preserved at its original paths. Its semantic findings agree with v1.1, but its per-arm timing totals are diagnostic because cold imports were charged to the first episode. The [v1.1 timing amendment](THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_1_AMENDMENT_20261001.md) documents the correction.

Artifacts: [base protocol](THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_PREREG_20261001.md), [amendment](THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_1_AMENDMENT_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_task_generated_receipt_transfer_v1_1.py), [analyzer](../../../scripts/analyze_thoughtexperiment_task_generated_receipt_transfer_v1_1.py), [source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_task_generated_receipt_transfer_v1_1_lock_20261001.json), [raw capture](../../../evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_1_raw_20261001.json), and [analysis](../../../evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_1_analysis_20261001.json).
