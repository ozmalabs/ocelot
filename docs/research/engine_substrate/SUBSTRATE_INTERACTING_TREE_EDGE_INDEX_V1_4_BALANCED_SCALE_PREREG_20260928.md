# Interacting balanced-tree closure at 10M v1.4 preregistration

**Question:** does the same two-rule monotone propagation workload reach exact fixed point on a 10M balanced binary tree, where outgoing adjacency remains low degree and the high-degree index is not activated?

Run three fresh source-locked processes at N=10,000,000 using the existing interacting-tree worker, balanced topology, and audit off. Preserve exact graph counts, fixed-point and no-overshoot checks, all-active/no-pending/no-ready oracle, sampled parent/attribute checks, and separate node-build, edge-build, closure, validation, live RSS, and process peak measures. The semantic edge-index controls also run once before workers. Compare descriptive medians with the v1.2 three-replicate 1M balanced condition; do not compare this to the 10M star as a topology-only intervention because these are different graph structures.

This tests one fixed rule pair and one balanced-tree generator on one host. It does not measure general rule diversity, induced width, learned frames, or natural task prevalence. No audit-on 10M run is planned because the prior audit overhead and candidate volume are not required for this scale claim.
