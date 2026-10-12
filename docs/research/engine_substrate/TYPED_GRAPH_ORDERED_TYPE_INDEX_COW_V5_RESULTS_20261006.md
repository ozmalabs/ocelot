# Ordered typed-node COW index v5 results

Date: 2026-10-06

Status: exact type order, NodeID reuse, compaction, and branch isolation pass; large-population first-write latency does not materially improve over v4.

The typed-population index now uses a COW-paged ordered vector with tombstones and a COW-paged NodeID-to-position map. Insertion appends, removal clears the located slot, and compaction preserves the order of live IDs while remapping their positions. The locked v5 panel passes all seven analysis gates across 12 size/operation cells and 21 paired repetitions: exact baseline attribute queries, exact baseline type order, per-arm mutation/index semantics, post-mutation type order, parent/sibling isolation, the 128-node delete/compact/reuse/restore control, and v4 baseline validity.

| Nodes | Mutation | V4 shared write | V5 shared write | Cross-capture change |
|---:|---|---:|---:|---:|
| 7,164 | delete | 8.33 µs | 7.89 µs | 5.3% lower |
| 7,164 | retype | 8.58 µs | 9.42 µs | 9.8% higher |
| 16,384 | delete | 17.96 µs | 14.65 µs | 18.4% lower |
| 16,384 | retype | 17.41 µs | 14.23 µs | 18.3% lower |
| 50,771 | delete | 110.91 µs | 110.49 µs | 0.4% lower |
| 50,771 | retype | 96.59 µs | 106.33 µs | 10.1% higher |

These v4/v5 timings come from separate source captures, so small differences are descriptive rather than paired treatment effects. The v5 within-capture fork-plus-write median is 98.9–99.7% below `clone_eager` across the 12 cells. At 50,771 nodes, however, type-index replacement does not produce a material write-time reduction. It establishes order-preserving constant-time membership removal in the data structure and exact behavior under compaction/reuse; it does not yet establish a large-scale runtime gain.

## Interpretation and remaining cost

The measured ~100 µs deletion/retype write at 50,771 nodes remains after removing both all-value-bucket unindex scans and typed-vector `retain`. The current attribute value map has 64 COW shards; its first mutation in a fork can copy the selected shard, whose size grows with distinct attribute values. This is a concrete remaining cost candidate from source inspection, but the capture does not attribute elapsed time among index-shard copy, node-page copy, and other writes. Next profile those branch-local copy costs directly, then vary attribute shard count prospectively and measure memory/write amplification. Retain exact output, type-order, compaction, and NodeID-reuse controls. Also measure the effect of tombstones on repeated `nodes_of_type` reads and full Substrate closure.

The representation adds a per-node position page and tombstone slots; exact memory has not been measured. These are graph-level synthetic findings, not natural-task prevalence, whole-Substrate throughput, or a general tractability result.

After capture, the native extension was rebuilt with the ordered index; engine provenance resolves to the workspace extension with ID `b621649fb3be`.

## Artifacts

- [Preregistration](TYPED_GRAPH_ORDERED_TYPE_INDEX_COW_V5_PREREG_20261006.md)
- [Source-locked runner](../../../evaluation/substrate_capability/ordered_type_index_cow_v5.py)
- [Probe source](../../../runners/dsl/src/bin/typed_graph_cow_attr_index_mutation_v3.rs)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_ordered_type_index_cow_v5.py)
- [Source lock](../../../evaluation/substrate_capability/ordered_type_index_cow_v5_lock_20261006.json)
- [Raw capture](../../../evaluation/reports/ordered_type_index_cow_v5_raw_20261006.json)
- [Analysis](../../../evaluation/reports/ordered_type_index_cow_v5_analysis_20261006.json)
- [V4 baseline](TYPED_GRAPH_COW_ATTR_INDEX_TARGETED_UNINDEX_V4_RESULTS_20261006.md)
