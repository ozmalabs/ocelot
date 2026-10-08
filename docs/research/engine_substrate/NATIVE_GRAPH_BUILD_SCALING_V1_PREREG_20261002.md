# Native graph build throughput and memory v1 preregistration

This benchmark measures raw Rust substrate graph-store insertion, separate from cognitive rule execution. Each isolated worker constructs `substrate_rs.Substrate`, inserts `N` `ScaleNode` nodes through `add_node`, then inserts `N × d` edges through `add_edge_unchecked`, where each source connects to cyclically offset targets with distinct edge types. It records node and edge insertion nanoseconds, throughput, current RSS after each stage, and process high-water RSS after each stage.

The locked grid is `N ∈ {100,000, 1,000,000}`, `d ∈ {0,1,2}`, with three fresh processes per cell and deterministic shuffled order (seed 61006). Node and edge insertion are timed separately. RSS is current resident pages from `/proc/self/statm`; peak RSS uses Linux `ru_maxrss`. This is a storage-path benchmark: edge grammar checks are intentionally bypassed, matching the engine's unchecked seed/reflection insertion primitive. Results must not be presented as checked/public `Substrate.add_edge` throughput or as cognitive-task performance. RSS/peak memory includes interpreter and native binary baselines; deltas are process-level estimates.

- Runner: [measure_native_graph_build_scaling_v1.py](../../../evaluation/substrate_capability/measure_native_graph_build_scaling_v1.py)
- Analyzer: [analyze_native_graph_build_scaling_v1.py](../../../evaluation/substrate_capability/analyze_native_graph_build_scaling_v1.py)
- Lock: [native_graph_build_scaling_v1_lock_20261002.json](../../../evaluation/substrate_capability/native_graph_build_scaling_v1_lock_20261002.json)
- Results: [native_graph_build_scaling_v1_20261002.json](../../../evaluation/reports/native_graph_build_scaling_v1_20261002.json)
