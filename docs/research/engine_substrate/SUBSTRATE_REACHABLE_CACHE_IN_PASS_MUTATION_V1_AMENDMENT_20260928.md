# ReachableFrom in-pass mutation probe v1 protocol amendment

This amendment corrects the evidential status of the v1 falsifier and preserves its source history.

The first one-off three-rule reproduction was run before the file named `...V1_PREREG...` was written. The file therefore was not a preregistration for that pilot. It also stated cache-on/off parity as the expected outcome, while the subsequent runner deliberately gated on the opposite outcome to capture the falsifier. The v1 source-locked run remains valid as a reproducible counterexample, and its raw graph, source fingerprint, build provenance, and independent checks are retained, but it must not be described as preregistered confirmation. The prereg file is retained unchanged because its exact hash is part of the captured source record.

The source-locked v1.1 protocol was written after the defect was known. It is a targeted post-fix regression confirmation, not a blind test of the original hypothesis. Its expected outcome is cache-on/off fixed-point parity. Broader internal mutation and rule-family panels remain necessary before general correctness claims.

See [v1 falsifier result](SUBSTRATE_REACHABLE_CACHE_IN_PASS_MUTATION_V1_RESULTS_20260928.md), [v1.1 regression protocol](SUBSTRATE_REACHABLE_CACHE_IN_PASS_MUTATION_V1_1_PREREG_20260928.md), and [v1.1 result](SUBSTRATE_REACHABLE_CACHE_IN_PASS_MUTATION_V1_1_RESULTS_20260928.md).
