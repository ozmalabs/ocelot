# Targeted attribute-index unindex v4 results

Date: 2026-10-06

Status: all source-lock, query, mutation, and branch-isolation gates pass; indexed deletion/retyping scans are removed for this workload.

V4 changes `unindex_node` to read the node's old attributes and remove its ID only from the matching `(type, key, value)` bitmaps. Delete, retype, and restore replacement pass the old node before-image. The same 12-cell, 21-repetition panel as v3 was rebuilt against this source. The analyzer passes all gates, including exact baseline queries and primary/sibling isolation in every shared and eager arm.

| Nodes | Mutation | V3 shared write | V4 shared write | V3→V4 reduction |
|---:|---|---:|---:|---:|
| 7,164 | delete | 233.25 µs | 8.33 µs | 96.4% |
| 7,164 | retype | 234.24 µs | 8.58 µs | 96.3% |
| 16,384 | delete | 680.03 µs | 17.96 µs | 97.4% |
| 16,384 | retype | 600.10 µs | 17.41 µs | 97.1% |
| 50,771 | delete | 5.638 ms | 110.91 µs | 98.0% |
| 50,771 | retype | 5.843 ms | 96.59 µs | 98.3% |

The v4 shared fork-plus-write medians are 98.7–99.5% below the eager `clone_eager` arm across all 12 cells. Set/insert shared write times differ from v3 by roughly -5% to +2.2%, consistent with cohort noise at these durations; this does not suggest a regression from the unindex change. Cross-version timing comparisons are descriptive, not counterbalanced.

## Remaining cost

Deletion and retyping still rise with population, from about 8 µs at 7,164 nodes to 97–111 µs at 50,771. Source inspection shows a remaining `by_type` vector `retain` on these paths, so removing a node still scans its entire type population. Attribute-index removal itself is now bounded by the node's indexed attributes. A next targeted-population-index gate should measure and address `by_type` removal while retaining typed iteration order and NodeID reuse semantics.

This remains a graph-level synthetic result. It does not establish whole-Substrate fork/closure cost, natural-task frequency, memory use, or general tractability.

The native extension was rebuilt after the change; engine provenance resolves to the workspace extension with engine ID `6e7a1c3cb880`.

## Artifacts

- [Preregistration](TYPED_GRAPH_COW_ATTR_INDEX_TARGETED_UNINDEX_V4_PREREG_20261006.md)
- [Source-locked runner](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_targeted_unindex_v4.py)
- [Probe source](../../../runners/dsl/src/bin/typed_graph_cow_attr_index_mutation_v3.rs)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_typed_graph_cow_attr_index_targeted_unindex_v4.py)
- [Source lock](../../../evaluation/substrate_capability/typed_graph_cow_attr_index_targeted_unindex_v4_lock_20261006.json)
- [Raw capture](../../../evaluation/reports/typed_graph_cow_attr_index_targeted_unindex_v4_raw_20261006.json)
- [Analysis](../../../evaluation/reports/typed_graph_cow_attr_index_targeted_unindex_v4_analysis_20261006.json)
- [V3 baseline](TYPED_GRAPH_COW_ATTR_INDEX_MUTATION_V3_RESULTS_20261006.md)
