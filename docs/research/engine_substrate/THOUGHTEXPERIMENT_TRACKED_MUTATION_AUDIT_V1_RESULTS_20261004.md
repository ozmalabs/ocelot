# Thoughtexperiment tracked mutation source audit v1

The source scanner finds 23 public `TypedGraph` methods taking `&mut self` in the main implementation block. It classifies 12 semantic graph writers (seven node-oriented, five edge-oriented), one revision-tracked edge-scope transition, one derived-index declaration, and nine journal/observer controls. All 12 semantic writers route through the expected graph revision and before-image logging hooks, directly or through `node_mut`, `insert_edge`, or `delete_edges_batch`. The scope transition advances the graph mutation version. The attribute index changes only derived lookup state and is not represented as semantic graph content; journal controls affect observer state rather than graph facts.

The audit passes its fixed method inventory and hook-presence checks against `graph.rs` SHA-256 `498cbc5b77093563609b7f04ddfc58d0ce415af833a991b65034c569375e43dc`. This supports the tracked-writer condition for the revision/receipt benchmark's current source. It remains a static source audit: it does not execute each method, prove correctness of all hook behavior, cover unsafe aliasing or interior mutation, or establish thread safety. The 17-case runtime journal matrix complements this list with finite execution coverage, but neither result proves universal mutation completeness.

See the [source audit runner](../../../evaluation/substrate_capability/audit_thoughtexperiment_tracked_mutations_v1.py) and [machine-readable capture](../../../evaluation/reports/thoughtexperiment_tracked_mutations_v1_20261004.json).

## Artifact provenance amendment

The v1-named JSON path was regenerated during a later current-source check and now contains the current graph.rs fingerprint, not the historical `498cbc5b...` fingerprint described above. Use the [v2 results](THOUGHTEXPERIMENT_TRACKED_MUTATION_AUDIT_V2_RESULTS_20261004.md) and [v2 capture](../../../evaluation/reports/thoughtexperiment_tracked_mutations_v2_20261004.json) as the authoritative current-source evidence. The original v1 narrative is retained as historical; its original machine capture is no longer available at the v1 path.
