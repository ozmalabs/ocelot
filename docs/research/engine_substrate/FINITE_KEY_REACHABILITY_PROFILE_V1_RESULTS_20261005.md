# Finite-key reachability profile v1 results

## Result

The source/native-locked 36-case panel passes all seven independent-analysis checks. The complete two-rule profile is admitted; the unconditional fresh-node negative control is rejected. Across paths, binary trees, and four-layer DAGs at N=8/16/32/64, every native run reaches `fixed_point` within the finite-fact progress bound. The materialized `reachable` edge relation exactly matches both an independent DFS and native `ReachableFrom` results for every source.

At N=64, path closure takes a median 40.45 ms and 63 passes to materialize 2,016 pairs; querying `ReachableFrom` once from every source takes 0.836 ms. Binary-tree closure takes 0.872 ms / six passes for 264 pairs versus 0.522 ms for all-source direct queries. Four-layer-DAG closure takes 12.18 ms / three passes for 1,536 pairs versus 1.50 ms for direct queries. Setup medians are 0.42–1.07 ms at N=64. The profile's checker bounds are conservative (8,129 for path/tree and 7,424 for the layered DAG). Peak process RSS is about 34.9 MB across these small workers; because this is a high-water mark, it is only process-level context, not per-case memory.

## Interpretation

This validates one useful explicitly authored profile inside the finite-key class: materialized reachability on finite DAGs, with an exact native query baseline. Materialization costs more than one all-source query batch on these small cases, particularly on paths where repeated relaxation propagates one edge-distance layer per pass. It may be useful when downstream work reuses many reachable pairs, but this experiment does not measure that break-even. The profile is not among the current registry roots and is not automatically enforced at all native mutation/import/restore boundaries.

This establishes a conditional, bounded operating mode that can be constructed deliberately; it does not remedy the all-root profile census, cover arbitrary Ocelot rules, prove a wall-time bound, or establish natural workload frequency. Use it as evidence for the capability of the restricted fragment and as a workload for a future enforced-profile gate.

## Reproduction

[Protocol](FINITE_KEY_REACHABILITY_PROFILE_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/finite_key_reachability_profile_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1.py), [source lock](../../../evaluation/substrate_capability/finite_key_reachability_profile_v1_lock_20261005.json), [capture](../../../evaluation/reports/finite_key_reachability_profile_v1_20261005.json), and [analysis](../../../evaluation/reports/finite_key_reachability_profile_v1_analysis_20261005.json).
