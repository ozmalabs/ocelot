# Reachability cache/materialization comparison v1.1 amendment

The v1 runner and raw capture are preserved. Its independent analyzer failed because its expected cache count included a self-query (`x == q`) that the engine's injective matcher correctly excludes, and because it compared the recorded arm-order list to the JSON object's alphabetically sorted keys. These are analysis-design errors, not execution or engine mismatches. The runner also labeled expected reader matches as N×R; the correct count is (N−1)×R for this fixture because the self-edge binding is excluded.

V1.1 preserves the preregistered workloads, arm definitions, timing intervals, and three-arm order. It corrects the expected self-binding count, validates that the recorded arm order is a permutation of the three arms independently of JSON key order, and includes a fresh source lock and capture. No outcomes from the failed v1 analysis are used to change the workload or timing protocol.

Reproduction: run `python3 evaluation/substrate_capability/reachability_cache_materialization_comparison_v1_1.py --lock`, run it without arguments, then run `python3 evaluation/substrate_capability/analyze_reachability_cache_materialization_comparison_v1_1.py`.
