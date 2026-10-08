# High-degree public remove-node scale v1 preregistration

**Question:** does the public native `remove_node` path correctly and efficiently remove a hub with many incident edges after `TypedGraph::delete_node` was changed to batch-compaction?

Run three fresh processes at 5,000/20,000/80,000 outgoing `hub_child` edges. Each graph contains one attributed Hub and N attributed Leaves. Time setup and the single public `remove_node` call separately. Afterward require the Hub gone, all N Leaves and their ordinals preserved, zero edges, exact node count, and one correct `node_deleted` hook. Source fingerprints and native build must be fresh and stable. Compare deletion medians descriptively with the same sizes from sequential-edge and public batch-edge deletion captures.

This tests the public node-removal integration for one homogeneous high-degree source. It does not measure incoming-edge hubs, self-loops, mixed edge types, rules/cursors, mutation-log parity, or concurrent graph readers.
