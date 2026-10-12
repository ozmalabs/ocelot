# Residual CoW candidate rehydration v1 results

The four-worker source-locked follow-up passes all gates. Each worker forms the expected `flip_comparison` candidate in a shared-graph-pages branch and passes held-out evaluation before return. The branch packages the candidate rule and target in a `ThoughtexperimentCandidateResidual` node. The revision-checked graph delta returns that node to the host; reading and deserializing it reproduces the exact candidate digest and exact held-out task outcomes, with all candidate receipts and host primary-rule checks passing in 4/4 workers. The return contains 41 graph nodes per worker (the earlier 40-node derived delta plus the candidate record).

The deliberate stale-revision attempt in worker 0 is rejected and leaves the host graph unchanged from its immediately prior state. Applying the same residual against the updated revision then succeeds. This verifies the conflict check and valid retry sequence in one controlled case; it is not a concurrent-writer stress test.

Median shared-page fork time is 0.273 ms and median revision-checked graph-delta application is 2.963 ms on this host. The latter excludes scoring and JSON readback. The earlier matched deep-copy comparison remains the reference for fork cost; this follow-up adds candidate packaging/rehydration and does not imply a broad performance gain.

## Scope

This demonstrates that a validated candidate can be packaged by the experiment adapter as a graph residual, returned, rehydrated, and scored without merging branch-native rewrite-rule additions. The candidate cue and navigation action geometry remain hand-authored; this measures residual transport and use, not autonomous diagnosis. The candidate residual node is a serialization convention in the harness, not a general learned serialization protocol. Production adoption, concurrent conflict rates, general residual schemas, and large-graph costs remain open.

## Artifacts

- Protocol: [preregistration](RESIDUAL_COW_CANDIDATE_REHYDRATION_V1_PREREG_20261002.md)
- Runner: [measurement script](../../../evaluation/substrate_capability/measure_residual_cow_candidate_rehydration_v1.py)
- Analyzer: [independent gate checker](../../../evaluation/substrate_capability/analyze_residual_cow_candidate_rehydration_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/residual_cow_candidate_rehydration_v1_lock_20261002.json)
- Raw workers: [capture](../../../evaluation/reports/residual_cow_candidate_rehydration_v1_20261002.json)
- Analysis: [gate results](../../../evaluation/reports/residual_cow_candidate_rehydration_v1_analysis_20261002.json)
