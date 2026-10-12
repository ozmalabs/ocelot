# TypedGraph attribute-index COW mutation v3 results

Date: 2026-10-06
Status: all graph-level semantic and isolation gates pass; fork-plus-write beats eager copy in this fixture, while delete/retype expose a remaining linear scan.

The source-locked capture covers 12 size-by-operation cells, 21 paired repetitions per cell, and four mutations: indexed attribute replacement, insertion, deletion, and retyping. All baseline lookups are exact. Every shared and eager branch preserves the expected local index result, while its parent and sibling retain the pre-mutation result. The independent analysis passes all four integrity gates.

| Nodes / distinct values | Mutation | Shared fork + write | Eager fork + write | Paired reduction |
|---:|---|---:|---:|---:|
| 7,164 | set attribute | 11.560 µs | 1.275 ms | 99.1% |
| 7,164 | insert | 8.600 µs | 1.272 ms | 99.3% |
| 7,164 | delete | 234.201 µs | 1.292 ms | 81.9% |
| 7,164 | retype | 235.220 µs | 1.299 ms | 81.9% |
| 16,384 | set attribute | 25.100 µs | 3.354 ms | 99.3% |
| 16,384 | insert | 18.220 µs | 3.418 ms | 99.5% |
| 16,384 | delete | 681.372 µs | 3.635 ms | 81.4% |
| 16,384 | retype | 603.123 µs | 3.380 ms | 81.9% |
| 50,771 | set attribute | 181.290 µs | 15.145 ms | 98.8% |
| 50,771 | insert | 112.891 µs | 15.187 ms | 99.3% |
| 50,771 | delete | 5.647 ms | 15.580 ms | 63.6% |
| 50,771 | retype | 5.851 ms | 15.270 ms | 61.9% |

The shared branch uses `clone_sharing_graph_pages`; the eager control uses `clone_eager`, which explicitly deep-copies attribute-index shards. Fork and mutation timings are measured separately, and the table reports their paired sum. The mutation timer includes the immediate local indexed-result check; parent/sibling isolation checks occur after timing. Arm order alternates. These are same-process graph-level synthetic medians on one host, not end-to-end thoughtexperiment timings.

## Interpretation

Attribute replacement and insertion retain large fork-plus-write gains at all tested sizes. Delete and retype are slower because `unindex_node` scans every indexed value bucket to find the node. Shared-branch first-write time rises from roughly 0.23 ms at 7,164 nodes to 5.64–5.84 ms at 50,771; eager mutation is 0.024–0.325 ms. The shared branch still wins on combined fork-plus-write, but the gap narrows to 61.9–63.6% at 50,771 nodes. This identifies a concrete avoidable operation: deletion/retyping already has the node's attribute map and can remove it directly from only the matching value buckets.

Next change `unindex_node` to use the node's old attributes, then repeat this source-locked panel. Keep deletion/retyping separate from point writes. After that, evaluate whole `Substrate::fork` and representative closure and measure memory; these results do not prove natural-task prevalence, frame locality, or general tractability.

## Artifacts

- [Preregistration](TYPED_GRAPH_COW_ATTR_INDEX_MUTATION_V3_PREREG_20261006.md)
- [Source-locked runner](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_mutation_v3.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_typed_graph_cow_attr_index_mutation_v3.py)
- [Source lock](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_mutation_v3_lock_20261006.json)
- [Raw capture](../../../evaluation/reports/typed_graph_cow_attr_index_mutation_v3_raw_20261006.json)
- [Analysis](../../../evaluation/reports/typed_graph_cow_attr_index_mutation_v3_analysis_20261006.json)
