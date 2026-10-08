# Finite-key reachability profile v1.2 results

## Result

All 60 locked cases completed (binary and ternary trees, N=64/128, 15 repetitions each). The checker, independent DFS relation comparison, direct and materialized answers at Q=1,2,4,8,16,32, fixed-point bound, source lock, negative control, and alternating arm-order gates all pass (nine checks).

The preregistered crossover criterion (median paired profile/direct ratio below one and at least 12/15 repetitions favoring materialization) is met in **zero** cells. The v1.1 candidate, binary tree N=64 Q=8, does not replicate: median paired ratio 1.37 and only 1/15 favorable repetitions (medians: direct 2.591 ms, profile 3.806 ms). Binary tree N=128 Q=32 is near parity (median paired ratio 0.992; 8/15 favorable), but does not meet the repetition criterion. Ternary tree N=128 Q=32 is also near parity (0.990; 8/15). At smaller batch counts the profile costs more, as expected from installation and closure overhead.

## Interpretation

The earlier single-process three-repeat crossover is best treated as timing noise or an unstable local result, not evidence that reuse has paid off. The replicated workload shows a diminishing cost gap as Q grows and suggests a plausible crossover at larger Q, but it has not yet established one robustly. The next experiment should increase Q around the N=128 near-parity cells with more repetitions and retain paired timings.

## Limits and reproduction

This is a targeted timing replication on synthetic tree families, not evidence about natural-task prevalence or general asymptotic performance. The four selected topology/size cells and fixed native query operations limit external validity.

Reproduce with the locked runner and independent analyzer named in [the preregistration](FINITE_KEY_REACHABILITY_PROFILE_V1_2_PREREG_20261005.md). Current [capture](../../../evaluation/reports/finite_key_reachability_profile_v1_2_20261005.json) and [analysis](../../../evaluation/reports/finite_key_reachability_profile_v1_2_analysis_20261005.json) pass all integrity gates.
