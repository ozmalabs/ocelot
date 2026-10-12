# High-degree edge deletion and reinsertion v1 results

**Evidence grade:** source-locked nine-worker native probe; all 8 runner gates and 11 independent analysis checks pass.

## Result

Each fresh process builds one root, N attributed leaves, and N edges in one outgoing `(source, edge type)` bucket. It deletes the complete bucket through the public native `remove_edge` method, verifies zero edges, then reinserts the same N edges and verifies exact counts and sampled lookup parity. Three processes run at each N.

| N edges | Median setup: nodes / edges | Delete all | Delete time per edge | Reinsert all |
|---:|---:|---:|---:|---:|
| 5,000 | 3.67 / 2.08 ms | 35.15 ms | 7.03 µs | 1.83 ms |
| 20,000 | 14.95 / 9.01 ms | 550.73 ms | 27.54 µs | 8.57 ms |
| 80,000 | 62.47 / 36.24 ms | 8.70 s | 108.69 µs | 37.87 ms |

For each 4× increase in N, delete-all time grows 15.67× and 15.79×; per-edge deletion cost grows about 3.9× each step. Reinsertion grows 4.68× and 4.42×, close to linear over these points. Every delete returns true, edge count reaches zero, sampled lookups become false, and reinsertion restores all N edges and sampled lookups.

## Interpretation

This identifies deletion as a separate high-degree tractability gap after insertion was fixed. The current `delete_edge` removes an edge by retaining across the source's full outgoing vector, its typed outgoing vector, and the global vector for that edge type. On a homogeneous star bucket these vectors all grow with N, so deleting every edge scans large vectors repeatedly. The measured near-quadratic curve and increasing per-edge cost agree with this source structure. The target index speeds up locating the edge, but does not make removal from these vectors constant time.

The immediate design choices are a batch deletion operation that filters each affected vector once, or position-aware adjacency storage with swap removal. A batch API would match bulk teardown and reduce complexity without per-edge location metadata; individual deletion still needs a position index or a different container. Any change must preserve adjacency iteration, `edges_by_type` contents/order expectations, edge deletion generation/cursor invalidation, edge attributes, mutation logs, and endpoint cleanup. No runtime deletion optimization is claimed here.

## Reproduction and limits

Run `python3 scripts/substrate_high_degree_edge_delete_churn_v1.py --lock` once for the frozen lock, then run the script and `python3 scripts/analyze_substrate_high_degree_edge_delete_churn_v1.py`. Artifacts: [protocol](SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_CHURN_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_high_degree_edge_delete_churn_v1.py), [analysis](../../../evaluation/reports/substrate_high_degree_edge_delete_churn_v1_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json), and [source lock](../../../evaluation/substrate_capability/high_degree_edge_delete_churn_v1_lock_20260928.json).

This is one homogeneous high-degree source/type bucket on one host, with three sizes and three replicates per size. It does not establish an asymptotic theorem, measure mixed type degrees, bulk node deletion, rule invalidation, concurrency, or application-level churn.
