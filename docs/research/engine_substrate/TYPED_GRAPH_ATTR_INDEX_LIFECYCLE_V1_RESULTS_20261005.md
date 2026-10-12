# TypedGraph attribute-index lifecycle v1 results

The current-source capture passes all 36 semantic gates (four parity checks in each of nine size/selectivity cells). This is a graph-level engine benchmark on one Linux host, not evidence of natural-task prevalence or full Substrate fork cost. Raw source-linked capture: [JSON](../../../evaluation/reports/typed_graph_attr_index_lifecycle_v1_20261005.json). Protocol: [preregistration](TYPED_GRAPH_ATTR_INDEX_LIFECYCLE_V1_PREREG_20261005.md).

## Measurements

All times are medians in milliseconds except graph fork, shown in microseconds. Query timing is one batch of 25 queries; break-even is index build time divided by scan-batch time saved and excludes mutation, fork, restore, and memory costs.

| Nodes | Cardinality | Build | Indexed query batch | Scan query batch | Indexed mutation | Scan mutation | Fork without index (µs) | Fork with index (µs) | Restore index | Query batches to repay build |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 8 | 0.060 | 0.023 | 0.355 | 0.014 | 0.009 | 0.2 | 0.9 | 0.075 | 0.18 |
| 1,000 | 128 | 0.056 | 0.003 | 0.371 | 0.005 | 0.003 | 0.2 | 10.7 | 0.211 | 0.15 |
| 1,000 | 1,000 | 0.115 | 0.002 | 0.384 | 0.007 | 0.004 | 0.2 | 102.1 | 0.258 | 0.30 |
| 10,000 | 8 | 0.566 | 0.197 | 3.833 | 0.039 | 0.014 | 1.0 | 2.7 | 0.456 | 0.16 |
| 10,000 | 128 | 0.381 | 0.008 | 2.215 | 0.018 | 0.007 | 0.7 | 7.8 | 0.668 | 0.17 |
| 10,000 | 1,024 | 0.710 | 0.003 | 3.054 | 0.035 | 0.015 | 1.0 | 118.8 | 0.826 | 0.23 |
| 50,000 | 8 | 2.171 | 0.685 | 17.919 | 0.106 | 0.057 | 3.6 | 7.5 | 2.987 | 0.13 |
| 50,000 | 128 | 2.634 | 0.048 | 17.493 | 0.098 | 0.036 | 3.9 | 19.2 | 2.923 | 0.15 |
| 50,000 | 1,024 | 2.315 | 0.007 | 17.335 | 0.128 | 0.057 | 4.6 | 120.5 | 2.727 | 0.13 |

## Interpretation

- Indexed query batches were faster in all nine cells; the measured batch saved 0.33–17.33 ms. On these fixed modulo distributions, the query savings alone exceed measured build/backfill cost within one 25-query batch.
- Mutation was slower with the index in all cells: 1.4–2.8× for the same update schedule. This is an index-maintenance cost, even though the absolute batch remained below 0.13 ms.
- Indexed graph fork cost rose with index cardinality. At 50,000 nodes, it measured 7.5 μs for cardinality 8, 19.2 μs for 128, and 120.5 μs for 1,024, versus 3.6–4.6 μs without the index. Small-cell fork timings vary substantially, so the ratios should be replicated before fine-grained decisions.
- Restore does not preserve the derived index. Re-declaration/backfill cost was 2.7–3.0 ms at 50,000 nodes, in addition to graph serialization/restore. Persisted configuration and index rebuild are separate lifecycle costs.

This supports selective, workload-aware index use as an engineering hypothesis. It does not establish that the substrate can discover frame scopes, that this lookup pattern is common in natural tasks, or that total thought-experiment cost falls. The next gate is a paired full-Substrate lifecycle replay on representative GenInfer tasks, reporting query frequency, mutation schedule, fork and restore costs, peak memory, and end-to-end parity.
