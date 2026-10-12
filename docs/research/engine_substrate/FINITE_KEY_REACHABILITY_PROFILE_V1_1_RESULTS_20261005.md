# Finite-key reachability profile v1.1 results

## Result

The preregistered reuse replay completed all 36 path, binary-tree, and four-layer-DAG cases (N=8,16,32,64; three fresh repetitions). Every closure reached its finite progress bound, and all direct and materialized answers matched independent DFS for each source at Q=1,2,4,8 all-source batches. The analyzer passes nine checks, including source-lock stability, full matrix coverage, checker recomputation, exact outputs, and refusal of the unrestricted fresh-node control.

Timing includes common graph construction; the materialized arm additionally includes rule installation and closure. Only one cell has a median crossover within the measured range: binary tree N=64 at Q=8, where direct total is 4.198 ms and profile total is 3.224 ms (profile/direct 0.77×). In the other 11 topology/size cells, materialization remains slower at Q≤8. At N=64 binary tree, the ratio falls from 3.07× at Q=1 to 0.77× at Q=8. Path N=64 remains 7.29× slower at Q=8, reflecting the quadratic reachable relation and closure cost. Timings are small and somewhat noisy; this single crossover is a candidate for replication, not a robust performance claim.

## Interpretation and limits

The profile offers exact finite-key reachability and can amortize its closure cost for repeated broad queries on at least one tested workload shape. That is a concrete reuse signal, while most tested cells remain below break-even in this envelope. It does not establish natural-task prevalence, a general CPU speed advantage, asymptotic scaling, a registered operating mode, or runtime admission enforcement. The query order is fixed, and only one small synthetic family is measured.

## Reproduction

The preregistration is [v1.1](FINITE_KEY_REACHABILITY_PROFILE_V1_1_PREREG_20261005.md). Run `python3 evaluation/substrate_capability/finite_key_reachability_profile_v1_1.py --lock`, run it again without arguments, then run `python3 evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_1.py`. The current capture and independent analysis are [capture](../../../evaluation/reports/finite_key_reachability_profile_v1_1_20261005.json) and [analysis](../../../evaluation/reports/finite_key_reachability_profile_v1_1_analysis_20261005.json).
