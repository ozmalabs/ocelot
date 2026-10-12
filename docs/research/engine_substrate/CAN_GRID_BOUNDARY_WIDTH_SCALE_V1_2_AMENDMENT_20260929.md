# CAN grid boundary-width scale v1.2 gate amendment (2026-09-29)

The complete v1.1 capture passed extraction and both independent MAP oracles in all 54 workers, but failed its `expected_width_and_bags` gate in 18 workers. Inspection of the archived rows shows that the fixed column-major order has the expected bag size q+1 in all 54; greedy min-fill returns valid but wider decompositions for q=5 (width 6) and q=6 (width 8). The original gate incorrectly treated a heuristic upper bound as a minimum-width result.

V1.2 preserves the same graph family, dimensions, seeds, oracle, metrics, and worker count. Its gates require the fixed column order to produce bag size q+1, and require min-fill's reported width and bag size to agree with each other and be no smaller than the known grid width. Min-fill width overhead remains a measured outcome. A new source lock and full fresh replication are required; v1.1's lock and capture remain unchanged as the disclosed failed-gate attempt.

