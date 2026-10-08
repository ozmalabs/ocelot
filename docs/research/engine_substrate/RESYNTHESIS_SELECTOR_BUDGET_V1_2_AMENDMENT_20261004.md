# Resynthesis selector-budget v1.2 amendment

The v1.1 analyzer replayed selector transcripts but incorrectly classified the registered `selection_pool` as forbidden, although the protocol explicitly draws queries from `selection_order` (which contains those rows). It therefore failed its disjointness gate and is diagnostic only. V1.2 binds a corrected analyzer that requires each query to belong to the locked selection order and to be disjoint from training and sealed holdout, then replays the same immutable candidate pools. No engine, policy, or captured query data are changed.
