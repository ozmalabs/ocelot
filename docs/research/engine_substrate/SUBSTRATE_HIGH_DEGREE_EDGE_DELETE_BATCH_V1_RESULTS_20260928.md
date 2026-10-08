# Stable-order batch edge deletion v1 results

**Evidence grade:** source-locked nine-worker paired native replay; all 12 runner gates and 16 independent analysis checks pass.

## Correctness and timing

The scale graph is identical in both arms. Sequential `remove_edge` and one-call `remove_edges_batch` produce the same canonical graph before and after deletion at all sizes. A mixed-edge control also matches ordered boolean outcomes for duplicate and absent requests, `edge_deleted` hook order/count, and the order of remaining all-edge and typed-neighbor iteration. Every scaled deletion reports N successes, preserves N+1 nodes, and leaves zero edges. The sequential arm reproduces the earlier deletion medians within 1–4%.

| N edges | Sequential median | Batch median | Speedup | Batch ns/edge |
|---:|---:|---:|---:|---:|
| 5,000 | 35.94 ms | 3.53 ms | 10.2× | 707 ns |
| 20,000 | 569.54 ms | 9.16 ms | 62.1× | 458 ns |
| 80,000 | 8.74 s | 42.71 ms | 204.6× | 534 ns |

The batch method collects unique live edges, removes them, and stable-filters each affected vector once. At 80k, it reduces the measured deletion time from seconds to tens of milliseconds without a permanent per-edge position table. Time is descriptive and setup/readback are outside the deletion interval.

## Design decision and limits

Stable order is observable through neighbor and type-index iteration. Swap removal would change that order unless the engine added a separate ordered representation. Batch filtering preserves order and is substantially faster for a caller that already has a deletion set. The existing single-edge API remains useful for isolated mutations; repeated single-edge deletion on one huge bucket retains the previously measured quadratic-looking curve. The graph's `delete_node` path uses batch compaction internally, and a separate public `remove_node` replay verifies the outgoing-hub integration through 80k edges ([results](SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_1_RESULTS_20260928.md)).

This is one homogeneous high-degree source/type bucket on one host. It does not measure mixed graph churn, concurrent mutation, rule-heavy dirty propagation, or an order-independent solver contract that might permit swap removal.

## Reproduction

Run `python3 scripts/substrate_high_degree_edge_delete_batch_v1.py --lock`, then the runner and `python3 scripts/analyze_substrate_high_degree_edge_delete_batch_v1.py`. See the [protocol](SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_BATCH_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_high_degree_edge_delete_batch_v1.py), [analysis](../../../evaluation/reports/substrate_high_degree_edge_delete_batch_v1_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_high_degree_edge_delete_batch_v1_20260928.json), and [source lock](../../../evaluation/substrate_capability/high_degree_edge_delete_batch_v1_lock_20260928.json). The original sequential baseline is in [the churn result](SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_CHURN_V1_RESULTS_20260928.md).
