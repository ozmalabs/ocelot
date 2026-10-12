# Where-reader deletion fan-out v1 preregistration

**Question:** how does deletion-triggered where-reader work grow with rule fan-out, and does type-local cursor invalidation remain sound across two edge-reading Term families?

## Panel

Cross N=32/128 stable `Root -slot-> Slot` match edges with R=1/4/16 rules and two where-reader families: `Count(Edges(Root, block)) == 0`, and `Count(InNeighbours(Slot, block)) == 0`. Every slot is initially blocked by a `block` edge. Delete all block edges with public `remove_edge`, then settle. Compare full rescan, sound incremental matching, and the unsound cursor falsifier. Run three fresh workers per cell (36 worker processes total); each worker constructs separate, identical graphs per arm.

## Gates and measures

Require a stable source/native lock, exact dependency declarations, zero initial opens, terminal closure, complete edge deletion, N opened slots in full-rescan and sound incremental arms, byte-identical graph snapshots for those arms, and zero opened slots in the unsound arm. Independently recompute candidate-pair medians and verify growth with R and N. Record reader enumerations, candidate pairs, edge deletion time, and closure time. Timing is descriptive; operation counts are the primary scaling evidence.

This panel measures a synthetic where-only family and does not establish natural-task fan-out or all-Term invalidation soundness.
