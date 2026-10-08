# TypedGraph attribute-index COW profile v2 results

Date: 2026-10-06
Status: high-cardinality index fork gate passes; branch mutation and whole-Substrate costs remain open.

The attribute index now uses nested `CowShardedMap`s keyed first by `(node_type, attr_key)` and then by attribute value. A cloned graph shares shard roots. Mutations use the existing COW path so a write copies affected shard maps. The new source-locked profile uses one distinct value per node and exact query checks for every value.

| Nodes / distinct values | Shard entries | Shared clone median | Deep index clone median | Deep/shared ratio |
|---:|---:|---:|---:|---:|
| 7,164 | 7,164 | 30 ns | 0.530 ms | 17,657× |
| 16,384 | 16,384 | 30 ns | 1.089 ms | 36,306× |
| 50,771 | 50,771 | 40 ns | 5.326 ms | 133,151× |

All three rows preserve exact indexed lookups and the source lock remained stable. These extremely small shallow-clone times are within timer-resolution/noise territory; the robust interpretation is that shallow clone work is independent of indexed population at this scale, while deep-copy work grows materially with the number of distinct values. This is an isolated component profile, not a whole-graph or thoughtexperiment latency claim.

## Limits and next gate

This profile does not include branch first-write latency. The next gate must fork an indexed graph, mutate a node attribute and insert/delete/retype nodes, compare shared-COW and eager-index controls, and verify parent/sibling isolation plus exact indexed query results. It should also measure whole `Substrate::fork` and one representative closure so the profile captures mutation and fixed costs. Memory should be measured with allocator or process-level deltas at a finer resolution than `VmRSS` pages. Do not claim the earlier index branch penalty is resolved for operating workloads until that gate passes.

The source was rebuilt into the native extension after the profile. Engine provenance resolves to the workspace extension; the build reports engine ID `60cbf4cca3cb`. No test suite was run.

## Artifacts

- [Preregistration](TYPED_GRAPH_COW_ATTR_INDEX_PROFILE_V2_PREREG_20261006.md)
- [Source-locked runner](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_profile_v2.py)
- [Source lock](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_profile_v2_lock_20261006.json)
- [Capture](../../../evaluation/reports/typed_graph_cow_attr_index_profile_v2_20261006.json)
