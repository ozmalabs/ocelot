# Edge-only deletion where-reader cursor invalidation v1 preregistration

**Question:** when `remove_edge` deletes an edge read only by a rule's `where` condition, does sound incremental matching clear the rule's cursor for a different, stable match-edge type, and does the unsound falsifier miss the newly enabled bindings?

## Design

Use N=8/32/128 stable `Root -slot-> Slot` match edges and one `Root -block-> Blocker` edge. One rule matches each `slot` edge, with where condition `Count(Edges(Root, block)) == 0`, and sets `Slot.open=1`. Initially the block edge makes the where false, so zero slots open. Delete only the block edge with public `remove_edge`; do not delete a node, so generic node-mutation cursor clearing is not invoked. Compare full rescan, sound per-edge-type incremental matching, and the explicit unsound falsifier. Run three fresh workers per size.

## Gates

Require a fresh stable source/native lock, 9 unique processes, exact where-only dependency declaration, zero initial opens, and terminal initial closure. After edge deletion require a terminal report, exact graph-derived open count N in full-rescan and sound incremental arms, byte-identical graph state between those arms, and unsound falsifier divergence with zero opened slots. Record candidate counts, reader enumerations, and wall time descriptively.

This isolates one `Count(Edges)` where-reader and one edge-only deletion. It does not establish all Term families, larger rule networks, or natural workload frequency.
