# Where-reader Term and fan-out scaling v1 preregistration

**Question:** do edge-type deletion invalidation and full-rescan parity extend to transitive `ReachableFrom` and `Not Exists` where readers, and how does operation work grow to larger N and reader fan-out?

## Panel

Cross N=128/512 stable `Root -slot-> Slot` match edges with R=1/16/64 identical reader rules. Compare two where families: `Count(ReachableFrom(Root, block)) == 0` over a shared outgoing block subgraph; and `Not Exists` over `InNeighbours(Slot, block)` with one blocker per slot. Each graph begins with every slot blocked. Remove the complete block-edge set with one public `remove_edges_batch` call, then settle. Compare full rescan, sound incremental matching, and the unsound cursor falsifier. Run three fresh workers per cell (36 worker processes total).

## Gates and measures

Require stable source/native locks, exact where-read declarations, zero initial openings, successful complete edge removal, fixed-point reports, N opened slots and byte-identical graph state in full-rescan/sound arms, and zero openings in the unsound arm. Independently recompute candidate pairs, rule enumerations, and native Term evaluation/unit counts. Candidate work should follow N×R; report Term work separately because `ReachableFrom` traverses graph structure. Timing is descriptive. The unsound zero-work arm is a correctness falsifier, never a performance baseline.

This is a controlled synthetic panel of two Term families and does not establish completeness for all Terms, broad production closure, or natural-task prevalence.
