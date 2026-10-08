# Node-deletion where-reader cursor invalidation v1 preregistration

**Question:** when node deletion removes an edge read only by a rule's `where` condition, does incremental matching clear that rule's stable match cursor and re-evaluate the newly enabled bindings?

## Design

Use N=8/32/128 stable `Root -slot-> Slot` match edges and one `Root -block-> Blocker` edge. One rule matches each `slot` edge, with where condition `Count(Edges(Root, block)) == 0`, and sets `Slot.open=1`. The initial fixed point has zero open slots. Delete the blocker node; the graph-derived expected open count becomes N. Compare full rescan (`incremental_match` off), sound per-edge-type incremental matching, and the explicit `incremental_match_unsound` falsifier. Three fresh worker processes per size execute all arms in deterministic construction order.

## Gates

V1 preregisters source/native lock stability, 9 unique fresh processes across the panel, zero initial opens and terminal initial closure, exact where-only access declaration for `edge:block`, deletion of the blocker, terminal post-delete closure, exact independent graph-derived open counts, and byte-identical off/sound-incremental outputs. The initial replay showed that the unsound cursor falsifier is masked by `remove_node`'s generic where-rule invalidation; see the v1.1 amendment. V1.1 requires all three arms to refresh and match, and records candidate enumeration counts and wall time descriptively. It does not attribute the full-rescan work to the edge-type invalidator.

This is one Count/Edges/Equals where-reader family and one public node deletion. It does not prove cursor correctness for every Term, scheduler, or concurrent mutation path.
