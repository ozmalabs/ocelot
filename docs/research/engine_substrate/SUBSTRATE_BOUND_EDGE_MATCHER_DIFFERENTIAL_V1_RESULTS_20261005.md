# Fully bound edge matcher differential v1 results

## Result

The source-locked capture passes all eight runtime gates across 32 workers. The independent analyzer passes all nine checks, including source/lock integrity and regeneration of every directed relation set from its seed. All workers match the host graph oracle at both closure phases.

The generated panel varies relation density across empty, sparse, medium, and complete controls. Left/right memberships overlap, candidate relations are directed, and a second edge type supplies decoys. The oracle and native matcher agree exactly on emitted witness pairs, including exclusion of same-node assignments and discrimination of the decoy edge type. After initial closure, adding the remaining selected relation edges yields exactly the newly expected witnesses on a second closure; no extra witnesses appear.

This directly exercises the fully bound match clause and its add-only incremental update route. It does not cover deletion/retraction, all rule-effect kinds, all combinations of repeated variables and clauses, or every matcher path. The change has targeted semantic support; broad engine regression coverage remains a required gate. Timings are captured but were not a preregistered performance endpoint.

## Evidence

The [protocol](SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/bound_edge_matcher_differential_v1.py), [source lock](../../../evaluation/substrate_capability/bound_edge_matcher_differential_v1_lock_20261005.json), [raw capture](../../../evaluation/reports/bound_edge_matcher_differential_v1_20261005.json), and [independent analysis](../../../evaluation/reports/bound_edge_matcher_differential_v1_analysis_20261005.json) make the targeted differential reproducible. Pair this with the [query eligibility scale v3 result](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V3_RESULTS_20261005.md) and [full query v1.4 result](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_4_RESULTS_20261005.md).

