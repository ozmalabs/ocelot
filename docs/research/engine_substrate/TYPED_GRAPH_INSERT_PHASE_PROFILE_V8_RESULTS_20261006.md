# TypedGraph insert-phase profile v8 results

Date: 2026-10-06

## Measurement

The source-locked profile ran three fresh processes per size/shard cell, with
41 branch insertions per process, and passed exact NodeID, type-order,
parent/sibling, and query-result checks in all 24 workers. It separates the
fork, indexed `TypedGraph::insert_node` call, exact post-insert `nodes_where`
lookup, and an otherwise matched insertion into a graph without the attribute
index.

| Nodes | Shards | indexed insert | no-index insert | indexed/no-index | lookup | fork |
|---:|---:|---:|---:|---:|---:|---:|
| 7,164 | 64 | 11.14 µs | 3.47 µs | 3.21× | 0.11 µs | 0.08 µs |
| 7,164 | 128 | 8.93 µs | 3.49 µs | 2.56× | 0.11 µs | 0.08 µs |
| 7,164 | 256 | 8.63 µs | 3.54 µs | 2.44× | 0.10 µs | 0.08 µs |
| 7,164 | 512 | 9.33 µs | 3.60 µs | 2.59× | 0.09 µs | 0.09 µs |
| 50,771 | 64 | 41.84 µs | 3.24 µs | 12.91× | 0.12 µs | 0.08 µs |
| 50,771 | 128 | 24.71 µs | 3.50 µs | 7.06× | 0.14 µs | 0.09 µs |
| 50,771 | 256 | 15.86 µs | 3.36 µs | 4.72× | 0.14 µs | 0.09 µs |
| 50,771 | 512 | 13.06 µs | 3.53 µs | 3.70× | 0.12 µs | 0.10 µs |

Values are medians across three per-process medians. At 7,164 nodes, indexed
insert time stays within 8.6–11.1 µs, and lookup stays within 0.09–0.11 µs.
This isolated workload does not reproduce v7's 73–116 µs insert-plus-lookup
measurements for the 128/256 shard arms. The post-insert lookup itself is far
too small to explain that difference. At 50,771 nodes, indexed insert costs
fall as shards increase, while the no-index insertion control stays near
3.2–3.5 µs. This is consistent with large value-shard copy work being a
material part of indexed insertion at scale.

## Interpretation and next experiment

The v9 exact-schedule replay also did not reproduce the small-graph anomaly:
with v7's set-attribute/eager-clone/insert ordering, its combined insert and
lookup medians were 10.97–11.57µs at 128/256 shards, and lookup itself was
about 0.12µs. The original v7 73–116µs observation therefore remains a
non-replicating outlier, not evidence of a stable shard-count penalty. Keep 64
as the production default pending counterbalanced rule-closure and live
Substrate evidence. The large-graph mechanism result remains promising but is
not an end-to-end result. See [v9 schedule-replay results](TYPED_GRAPH_COW_INSERT_SCHEDULE_PROFILE_V9_RESULTS_20261006.md).

## Reproduction artifacts

- [Protocol](TYPED_GRAPH_INSERT_PHASE_PROFILE_V8_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/typed_graph_insert_phase_profile_v8.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_typed_graph_insert_phase_profile_v8.py)
- [Source/binary lock](../../../evaluation/substrate_capability/typed_graph_insert_phase_profile_v8_lock_20261006.json)
- [Raw capture](../../../evaluation/reports/typed_graph_insert_phase_profile_v8_raw_20261006.json)
- [Analysis](../../../evaluation/reports/typed_graph_insert_phase_profile_v8_analysis_20261006.json)
