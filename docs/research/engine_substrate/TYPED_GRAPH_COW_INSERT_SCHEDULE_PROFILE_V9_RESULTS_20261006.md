# TypedGraph COW insert schedule profile v9 results

Date: 2026-10-06

## Result

The v9 source-locked run passed all mutation, exact query/order, parent/sibling,
and compaction/reuse controls across 24 workers (three fresh processes for each
of two sizes and four shard counts; 21 repeats per worker). It copied the v7
mutation worker and retained its set-attribute, insert, delete, retype order
and alternating shared/eager arm order, adding nested timers for
`insert_node` and the post-insert exact lookup.

| Nodes | Shards | v7 combined insert+lookup | v9 insert operation | v9 lookup | v9 outer combined |
|---:|---:|---:|---:|---:|---:|
| 7,164 | 64 | 9.62 µs | 9.72 µs | 0.12 µs | 10.03 µs |
| 7,164 | 128 | 72.82 µs | 11.28 µs | 0.12 µs | 11.57 µs |
| 7,164 | 256 | 115.77 µs | 10.54 µs | 0.12 µs | 10.97 µs |
| 7,164 | 512 | 10.09 µs | 10.51 µs | 0.11 µs | 10.79 µs |
| 50,771 | 64 | 103.90 µs | 107.40 µs | 0.16 µs | 107.89 µs |
| 50,771 | 128 | 61.38 µs | 62.16 µs | 0.18 µs | 62.66 µs |
| 50,771 | 256 | 38.14 µs | 38.80 µs | 0.20 µs | 39.19 µs |
| 50,771 | 512 | 29.88 µs | 32.75 µs | 0.20 µs | 33.24 µs |

Entries are medians across three process medians. V9 reproduces the v7
operation order but does not reproduce its 73–116 µs small-graph combined
insert timings at 128/256 shards: the v9 outer timing is 10.97–11.57 µs, with
the lookup contributing about 0.12 µs. At 50,771 nodes v9 and v7 combined
timings are within about 3–11% across shard counts, consistent with the
registered large-graph scaling trend. Cross-capture small timing differences
are descriptive; v9's nested timers identify that lookup cost is negligible.

## Interpretation and next gate

The old small-graph result is a non-replicating anomaly, not evidence of a
stable 128/256-shard insertion penalty. The v8 isolated capture and v9
schedule-replay both show ordinary small-graph insertion times. The cause of
the original timing remains unlocated, but it should not drive configuration
selection. Keep the 64-shard default until a counterbalanced rule-closure and
representative Substrate workload comparison validates the large-graph write
gain without regressing common smaller graphs.

## Reproduction artifacts

- [Protocol](TYPED_GRAPH_COW_INSERT_SCHEDULE_PROFILE_V9_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/typed_graph_cow_insert_schedule_profile_v9.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_typed_graph_cow_insert_schedule_profile_v9.py)
- [Source/binary lock](../../../evaluation/substrate_capability/typed_graph_cow_insert_schedule_profile_v9_lock_20261006.json)
- [Raw capture](../../../evaluation/reports/typed_graph_cow_insert_schedule_profile_v9_raw_20261006.json)
- [Analysis](../../../evaluation/reports/typed_graph_cow_insert_schedule_profile_v9_analysis_20261006.json)
