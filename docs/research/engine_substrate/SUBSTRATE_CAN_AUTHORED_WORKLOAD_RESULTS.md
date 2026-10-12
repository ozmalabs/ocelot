# Authored CAN workload replay — 2026-09-24

## Question

Does the current native rule engine execute the project’s authored discrete asynchronous CAN relaxation on its real seeded rules, and what cost is visible at the existing N=8 workload size?

## Method

[`scripts/substrate_can_authored_workload.py`](../../../scripts/substrate_can_authored_workload.py) reuses the graph constructor and workload definitions in `tests/test_can_native_reimplementation.py`. It replays 20 fixed seeds for each combination of 2-state/3-state updates and coarse/fine coupling weights: 80 runs total. Each graph has eight concepts and 56 directed symmetric coupling edges. It records progress count, wall and CPU time, final state histogram, native frustration metric, and a one-step terminal probe. The terminal probe must do zero work. This is a measured workload replay, not a test-suite invocation.

The raw draw records, summary values, platform, command, source hashes, seed-manifest hash, and native-extension hash are in [`evaluation/reports/substrate_can_authored_workload_20260924.json`](../../../evaluation/reports/substrate_can_authored_workload_20260924.json). The extension was the fresh release build used for the corrected access-model pilots (`4a6fef0d74e11ac6e0e9dacd357739bd9f597ba0d7569afd1f84dcaf514c88ba`).

## Results

| Update mode | Weight granularity | Runs | Converged / zero-work terminal / valid vocabulary | Median progress | Median wall time | Median CPU time |
|---|---:|---:|---|---:|---:|---:|
| 2-state | 1.00 | 20 | 20 / 20 / 20 | 2 | 0.300 ms | 0.303 ms |
| 2-state | 0.25 | 20 | 20 / 20 / 20 | 1 | 0.223 ms | 0.225 ms |
| 3-state | 1.00 | 20 | 20 / 20 / 20 | 3 | 0.367 ms | 0.370 ms |
| 3-state | 0.25 | 20 | 20 / 20 / 20 | 2.5 | 0.359 ms | 0.361 ms |

The medians are descriptive for this environment and this small workload. The observed convergence and terminal checks support the registered local behavior on these 80 draws. Timing includes only `run_rules`, not graph construction or seed loading.

## Interpretation and limits

This closes one task-level evidence gap between synthetic closure pilots and an authored domain workload: the native engine applies the CAN rules and settles on the tested draws. It does **not** establish an independent correctness oracle for the resulting basin, energy, or action quality; the recorded frustration is the engine’s own metric. The run has only one graph size and complete coupling, so it cannot support a scaling or frame-locality claim. The small timings also say nothing about commodity-scale graphs.

Next: add sparse and frame-structured CAN variants at several sizes; compare native final states and observables to an independently implemented reference relaxation; preserve matched graph seeds while varying width and boundary size; then include the same workload in cold-process resource and memory measurements. Keep the N=8 replay as the reproducible baseline.
