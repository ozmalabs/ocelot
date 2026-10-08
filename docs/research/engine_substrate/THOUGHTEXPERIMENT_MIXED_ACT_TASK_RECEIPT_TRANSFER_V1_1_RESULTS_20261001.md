# Mixed-act task receipt transfer v1.1 — results

**Status:** all task and receipt gates pass across eight fresh workers and 24 episodes.

This replay uses the existing ten-event `phase3_mixed_act_dialogue.v1` task, including two task Goals, production-owned selection/execution/action-result events, an unsolicited assertion, and an epistemic-limit repair. The direct, eager-receipt, and shared-snapshot-receipt arms agree on all event/Goal IDs, per-event closure progress, canonical graph facts, Goal transition paths, common-ground claims, deferred `location_unresolved` residual, and terminal fixed point. Both Goals resolve with transition indices `[1,2,3]` and `[6,7,8]`. Every receipt's adopted primary matches the producing branch before the next task step.

Each branch arm emitted 16 receipts per episode (six production-helper event-plus-closure receipts and ten ordinary settlement receipts), or **128 receipts** across eight episodes. In each arm, 48 receipts are nonempty and the receipts contain 512 total graph effects. The worker source/native lock remained stable.

## Timing

| Arm | Median route time | Range | Median branch setup | Journal readout | Receipt adoption | Rule closure |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 6.03 ms | 5.49–13.74 ms | — | — | — | 0.26 ms |
| Eager receipt | 22.15 ms | 17.23–35.43 ms | 1.96 ms | 1.30 ms | 3.33 ms | 1.17 ms |
| Shared-snapshot receipt | 20.41 ms | 14.12–26.64 ms | 0.97 ms | 1.44 ms | 3.89 ms | 1.53 ms |

Cold Python module import is separate at 85.51 ms median per worker. Route time sums fixture loading, adapter/seed setup, event construction, branch setup, closure, journal readout, adoption, and terminal probe; oracle graph serialization is excluded. Shared snapshots are about 1.09× faster than eager-copy receipt handling in this small panel, primarily through lower branch setup. Both receipt paths are substantially slower than Direct on this fixture. Eight workers provide limited timing precision.

## Edge order and boundaries

Canonical semantics match Direct at all 80 event states per receipt arm. Full graph wire order differs in **72/80** of those states for both eager and shared receipts. This is more frequent than in the common-ground fixture and confirms that receipt adoption changes observable serialization order across distinct task families. Do not call this exact graph-wire parity. This result raises the priority of an edge-order compatibility audit before broadening receipt adoption to more production routes. Source inspection supplies a likely mechanism: `graph_diff` sorts added edge triples; `apply_graph_delta` restores them in that array order; `graph_to_value` emits live edge-slab order. Direct therefore preserves the task mutation sequence while receipt adoption appends sorted additions. The capture stores per-event graph hashes, not the graph vectors themselves, so confirming the precise first-divergent operation remains a follow-up. See [`graph_diff` and `apply_graph_delta`](../../../runners/dsl/src/persist.rs) and [`graph_to_value`/slab iteration](../../../runners/dsl/src/graph.rs).

The task fixture was authored independently of the receipt mechanism, but is not a natural-task sample. The v1 capture is preserved as a failed serialization diagnostic: its worker episodes completed, but `NodeID` values in final readback prevented valid JSON records, so v1 makes no result claim. The v1.1 amendment records the JSON serialization correction and new lock/output paths.

Artifacts: [protocol](THOUGHTEXPERIMENT_MIXED_ACT_TASK_RECEIPT_TRANSFER_V1_PREREG_20261001.md), [serialization amendment](THOUGHTEXPERIMENT_MIXED_ACT_TASK_RECEIPT_TRANSFER_V1_1_AMENDMENT_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_mixed_act_task_receipt_transfer_v1_1.py), [analyzer](../../../scripts/analyze_thoughtexperiment_mixed_act_task_receipt_transfer_v1_1.py), [lock](../../../evaluation/substrate_capability/thoughtexperiment_mixed_act_task_receipt_transfer_v1_1_lock_20261001.json), [raw capture](../../../evaluation/reports/thoughtexperiment_mixed_act_task_receipt_transfer_v1_1_raw_20261001.json), and [analysis](../../../evaluation/reports/thoughtexperiment_mixed_act_task_receipt_transfer_v1_1_analysis_20261001.json). The failed v1 capture is retained at [diagnostic path](../../../evaluation/reports/thoughtexperiment_mixed_act_task_receipt_transfer_v1_failed_serialization_20261001.json).
