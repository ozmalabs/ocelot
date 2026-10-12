# Mixed-topology public node deletion v1 preregistration

**Question:** does public `remove_node` correctly remove all incident edges through the stable batch path when the node has incoming edges, outgoing edges, multiple edge types, a self-loop, and attributed edges, while preserving unrelated graph state?

## Protocol

Run three fresh workers against one deterministic fixture. Each graph contains a doomed node, two incoming edges, three outgoing edges, a self-loop, and one unrelated edge. The incident edges span four edge types and carry attributes. Before and after removal, capture the canonical graph and query every fixture edge through `has_edge`. Register `node_deleted` and `edge_deleted` hooks. The expected post-state is derived independently by removing the doomed node and all incident edges from the pre-state graph snapshot.

## Gates

Require a fresh native build and stable source lock in the parent and all workers; unique worker PIDs; exact equality with the independently derived post-state; correct node/edge counts; false lookup for every removed incident edge; true lookup for the unrelated edge; exactly one `node_deleted` event with the original type; and no `edge_deleted` events, matching the existing public `remove_node` hook contract. The analyzer independently recomputes each gate from raw worker rows.

This is semantic corner-case coverage, not a timing or rule-invalidation benchmark. It does not establish mutation-log parity, cursor behavior under active rules, concurrency, or prevalence in natural workloads.
