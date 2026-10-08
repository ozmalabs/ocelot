# Native typed-graph storage scale v1 results

## Outcome

The source-locked six-worker panel passes its runner gates and the independent analyzer passes 11/11 checks. Each worker constructs an empty-attribute chain with exactly N nodes and N−1 edges, and sampled node and edge readbacks pass. All worker start/end snapshots and the parent post-run snapshot match the lock.

| Nodes | Edges | Median node build | Median edge build | Median total build | Median RSS increase | RSS increase per node |
|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 9,999 | 5.0 ms | 8.0 ms | 13.0 ms | 3.66 MB | 366 B |
| 100,000 | 99,999 | 48.3 ms | 91.7 ms | 140.0 ms | 26.3 MB | 263 B |
| 1,000,000 | 999,999 | 473.8 ms | 958.2 ms | 1.43 s | 253.7 MB | 254 B |

Timings are medians of two fresh processes. These are direct Python-to-native mutation measurements, including PyO3 calls, symbol interning, and allocator behavior. RSS is whole-process current RSS sampled before and after construction. The decreasing per-node ratio reflects fixed interpreter/import overhead being amortized; it should not be treated as a stable per-node memory constant.

## Interpretation and limits

The measured one-million-node sparse graph is constructible in about 1.43 CPU seconds and adds about 254 MB of process RSS in this configuration. This materially narrows the scale uncertainty for storage and FFI mutation, but does not establish closure or inference cost, production attribute/rule density, sustained mutation, random-access latency, deletion/reuse, memory fragmentation, or commodity CPU performance across machines. No asymptotic law is inferred from three sizes and two replicates.

The preregistered v1.1 extension adds a 10M-node sparse chain to measure another order of magnitude directly. It retains the v1 capture and uses separate raw/log/lock artifacts.

Artifacts: [preregistration](SUBSTRATE_GRAPH_STORAGE_SCALE_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_graph_storage_scale_v1.py), [independent analyzer](../../../scripts/analyze_substrate_graph_storage_scale_v1.py), [source lock](../../../evaluation/substrate_capability/graph_storage_scale_v1_lock_20260928.json), [raw capture](../../../evaluation/reports/substrate_graph_storage_scale_v1_20260928.json), [analysis](../../../evaluation/reports/substrate_graph_storage_scale_v1_analysis_20260928.json).
