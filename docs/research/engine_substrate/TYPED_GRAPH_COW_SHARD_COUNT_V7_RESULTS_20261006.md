# TypedGraph COW shard-count v7 results

Date: 2026-10-06

## Outcome

The amended, source-locked capture completed 36 fresh workers: three process
replicates for each of 12 size/configuration cells, with shard-count order
rotated. Every worker passed exact baseline queries, typed order, set/insert/
delete/retype semantics, eager parity, parent/sibling isolation, and the
delete/compaction/NodeID-reuse/restore control (21 repeats per worker). The
first unreplicated timing capture showed bimodal small-graph insert samples and
is treated as diagnostic only. This report uses the three-process replicated
capture.

| Nodes | Shards | set attr | insert + validation lookup | delete | retype | exact query sweep |
|---:|---:|---:|---:|---:|---:|---:|
| 7,164 | 64 | 30.2 µs | 9.6 µs | 8.0 µs | 9.3 µs | 0.537 ms |
| 7,164 | 128 | 24.4 µs | 72.8 µs | 8.2 µs | 7.6 µs | 0.386 ms |
| 7,164 | 256 | 7.9 µs | 115.8 µs | 7.8 µs | 8.0 µs | 0.389 ms |
| 7,164 | 512 | 10.6 µs | 10.1 µs | 7.7 µs | 8.2 µs | 0.398 ms |
| 16,384 | 64 | 23.4 µs | 15.5 µs | 14.5 µs | 14.6 µs | 0.914 ms |
| 16,384 | 128 | 24.9 µs | 14.9 µs | 12.4 µs | 12.6 µs | 0.958 ms |
| 16,384 | 256 | 11.5 µs | 11.8 µs | 10.4 µs | 10.5 µs | 0.950 ms |
| 16,384 | 512 | 11.0 µs | 11.3 µs | 10.3 µs | 10.4 µs | 1.008 ms |
| 50,771 | 64 | 187.9 µs | 103.9 µs | 104.4 µs | 102.9 µs | 3.177 ms |
| 50,771 | 128 | 112.5 µs | 61.4 µs | 55.6 µs | 54.2 µs | 3.196 ms |
| 50,771 | 256 | 55.7 µs | 38.1 µs | 33.0 µs | 33.0 µs | 3.406 ms |
| 50,771 | 512 | 34.2 µs | 29.9 µs | 20.8 µs | 21.7 µs | 3.150 ms |

Entries are medians of the three fresh-process medians. At 50,771 nodes, all
four branch-write medians fall with more shards: 128 shards use 53–60% of the
64-shard write time, 256 use 30–37%, and 512 use 18–29%. The exact full-query
sweep remains near 3.2–3.4 ms. Fixture RSS is effectively flat at about
27.5 MiB; high-water RSS is roughly 42.7–43.6 MiB for 64/128/512, with the 256
cell at 43.6 MiB. RSS is process-level and page-granular.

Small graphs expose a material tradeoff in the combined insert-and-validation
timing: its median is 7.6× higher at 128 shards and 12.0× higher at 256 than at
64, while the 512-shard result is near the 64 baseline. These differences
repeat across three processes. The timed region includes both
`TypedGraph::insert_node` and the harness's exact `nodes_where` validation
query, so the current data does not localize the regression to insertion or
lookup. At 16,384 nodes, write effects are modest at 128 and generally
favorable at 256/512; query sweeps are within about 10%. Split the insert
operation and validation query timers, then test insertion key/shard
distributions before selecting a production count.

## Decision and next gate

This identifies a real large-population graph write-time opportunity while
showing configuration-sensitive small-population costs. Keep the production
default at 64. First split graph insertion from its exact validation lookup
and test insertion-key/shard distributions. Then
run representative closure and full-Substrate workload comparisons with exact
end-to-end parity, memory, read cost, and graph sizes drawn from the workload
inventory. Natural task prevalence and acquisition of new structure remain
separate open questions; this synthetic mutation panel closes neither.

## Reproduction artifacts

- [Protocol and timing amendment](TYPED_GRAPH_COW_SHARD_COUNT_V7_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/typed_graph_cow_shard_count_v7.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_typed_graph_cow_shard_count_v7.py)
- [Source/binary lock](../../../evaluation/substrate_capability/typed_graph_cow_shard_count_v7_lock_20261006.json)
- [Raw replicated capture](../../../evaluation/reports/typed_graph_cow_shard_count_v7_raw_20261006.json)
- [Analysis](../../../evaluation/reports/typed_graph_cow_shard_count_v7_analysis_20261006.json)
