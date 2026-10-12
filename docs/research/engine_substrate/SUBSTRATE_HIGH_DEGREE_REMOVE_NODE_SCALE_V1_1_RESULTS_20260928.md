# High-degree public remove-node scale v1.1 results

**Evidence grade:** source-locked nine-worker native replay; all 8 runner gates and 13 independent analysis checks pass. V1's workers passed the graph and sample oracles but its aggregate gate compared a JSON-decoded hook list to a tuple; that failed capture is retained, and v1.1 corrects the representation check without changing the workload or engine.

## Result

Three fresh processes at each N=5k/20k/80k build one Hub and N attributed Leaves, connect every leaf to the Hub, and call public `remove_node` once. Every run removes the Hub, preserves every Leaf and ordinal, leaves zero edges, and emits exactly one correctly typed `node_deleted` hook. Median remove-node times are 0.56 ms, 2.68 ms, and 13.36 ms (112/134/167 ns per incident edge). At 80k, this is about 651× faster than deleting each edge through the public single-edge API in the prior source-locked capture.

The core node-delete path uses `TypedGraph::delete_edges_batch` to compact incident-edge vectors once, then removes the node. It does not emit one `edge_deleted` hook per incident edge; that matches the existing `remove_node` API contract. For reference, the explicit public batch-edge API took 42.71 ms at 80k because it returns per-edge success flags and invokes the edge hook path per deleted edge. These are different APIs and work boundaries, so compare them as separate measures rather than attributing the whole difference to graph compaction.

## Limits

This verifies the public outgoing-hub node-delete path with one edge type. Incoming hubs, self-loops, mixed edge types, concurrent readers, rule-heavy dirty propagation/cursor invalidation, and mutation-log parity remain unmeasured. It does not establish a general complexity bound or natural-workload prevalence.

## Reproduction

Run `python3 scripts/substrate_high_degree_remove_node_scale_v1.py --lock`, then run the script and `python3 scripts/analyze_substrate_high_degree_remove_node_scale_v1.py`. See the [protocol](SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_PREREG_20260928.md), [v1.1 amendment](SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_1_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_high_degree_remove_node_scale_v1.py), [analysis](../../../evaluation/reports/substrate_high_degree_remove_node_scale_v1_1_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_high_degree_remove_node_scale_v1_1_20260928.json), and [source lock](../../../evaluation/substrate_capability/high_degree_remove_node_scale_v1_1_lock_20260928.json).
