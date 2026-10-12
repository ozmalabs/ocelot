# Generated Euler Active Query v1.2.1 Amendment

The exploratory in-process hypothesis-branch replay found that `QueryRankingIndex.filter` used exact numeric-key equality, while the uncached harness retained predictions within absolute tolerance `1e-9`. This could remove near-equal floating predictions from a cached branch. Version 1.2.1 aligns cached filtering with the CEGIS numeric tolerance and repeats the locked Euler evaluation. Its analyzer also directly compares the complete cached and uncached query sequences and final survivor IDs for each anchor.

The v1.2 capture remains preserved as evidence of the initially measured implementation and is not used as the final cache result. Version 1.2.1 uses the same tasks, seeds, grammar, query policy, and timing fields, with the corrected response filter.
