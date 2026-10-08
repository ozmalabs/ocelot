# Native typed-graph storage scale v1.1 results

## Outcome

The corrected, source-locked eight-worker panel passes all runner gates; an independent analyzer passes 11/11 checks. It covers two fresh processes at each of 10k, 100k, 1M, and 10M nodes. Every process builds exactly N `StorageProbe` nodes and N−1 directed `next` edges, passes sampled node/edge reads, and matches the same source/native lock at worker start/end and parent post-run. The initial attempt completed all eight cells but failed because the runner asserted six workers; it is retained separately and excluded. See the [correction amendment](SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_CAPTURE_CORRECTION_20260928.md).

| Nodes | Edges | Median node build | Median edge build | Median total build | Median RSS increase | RSS increase per node |
|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 9,999 | 5.4 ms | 8.1 ms | 13.5 ms | 3.69 MB | 368 B |
| 100,000 | 99,999 | 49.0 ms | 94.1 ms | 143.1 ms | 27.4 MB | 274 B |
| 1,000,000 | 999,999 | 505.1 ms | 1.00 s | 1.51 s | 253.7 MB | 254 B |
| 10,000,000 | 9,999,999 | 4.77 s | 10.88 s | 15.66 s | 2.15 GB | 215 B |

For the 10M workers, process peak RSS is 2.393–2.394 GB. CPU and wall time are close on this run. The per-node RSS ratio falls with size because the denominator amortizes process/import baseline; the total RSS delta is the more useful capacity measure here. RSS includes Python, native allocator and process state, not just graph-owned bytes.

## Interpretation and limits

This is direct evidence that the current public Python-to-native mutation path can build a sparse, empty-attribute 10M-node/approximately 10M-edge graph on this host in about 15.7 CPU seconds at about 2.4 GB peak RSS. It narrows the storage/FFI scaling gap at 10⁷ nodes. It does not measure 10⁸ nodes, rule closure, inference, realistic attrs/rule sets, random-access latency, steady-state mutation, deletion/reuse, fragmentation, or another machine's commodity-CPU envelope. The chain is intentionally sparse and favorable; no complexity theorem or general tractability claim follows.

The next scale step should add representative attribute and rule density, then measure closure work and semantic parity at increasing sizes. Keep those operation costs separate from graph construction and memory.

Artifacts: [base preregistration](SUBSTRATE_GRAPH_STORAGE_SCALE_V1_PREREG_20260928.md), [10M extension](SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_AMENDMENT_20260928.md), [runner correction](SUBSTRATE_GRAPH_STORAGE_SCALE_V1_1_CAPTURE_CORRECTION_20260928.md), [runner](../../../scripts/substrate_graph_storage_scale_v1_1.py), [independent analyzer](../../../scripts/analyze_substrate_graph_storage_scale_v1_1.py), [source lock](../../../evaluation/substrate_capability/graph_storage_scale_v1_1_lock_20260928.json), [raw capture](../../../evaluation/reports/substrate_graph_storage_scale_v1_1_20260928.json), [analysis](../../../evaluation/reports/substrate_graph_storage_scale_v1_1_analysis_20260928.json), [excluded attempt-1 raw](../../../evaluation/reports/substrate_graph_storage_scale_v1_1_attempt1_20260928.json), [attempt-1 lock](../../../evaluation/substrate_capability/graph_storage_scale_v1_1_attempt1_lock_20260928.json).
