# Native finite-key closure counters v1.3 results

Date: 2026-10-04

## Result

The source-locked paired replay completed 180 audit-off/audit-on fixture pairs (360 closures). The independent analyzer passed all exact terminal graph checks against both the audit-off arm and an independent monotone interpreter. The terminals are invariant across rule order for all 20 N/degree cells. All runs pass finite-key admission (M=3,E=5), fixed-point, progress-bound, budget, and pre/post source-stability checks. Audit-off counters are all zero. In audit-on arms, the three numeric rule IDs map unambiguously to the installed `mint_A`, `mint_B`, and `join_AB` rules; no candidate tests or Term work are unattributed. Per-rule candidate pairs sum to global enumerations, per-rule candidate tests and clause snapshots sum to global candidate tests, per-edge candidates sum to per-rule pairs, and global path and first/repeat partitions conserve.

At N=256,d=16, the median per-rule candidate-test counts are 8,192 for A, 139,264 for B, and 1,024 for C. B's count changes with scheduler order and enumeration history, so a simple N·d² formula is not a sufficient whole-run predictor. The counters expose this native work directly; earlier v1/v1.1/v1.2 fixed-formula assumptions were invalid and their captures are retained as unscored pilots. Paired audit-on/off median end-to-end setup/closure/export ratio is 1.104 across the 180 pairs (median paired excess 0.599 ms). By-degree median ratios range from 1.051 at d=2 to 1.168 at d=16. Some cell ratios cross 1 because of timing noise; this is a one-host descriptive overhead estimate.

## Interpretation and limits

This establishes attribution and internal conservation of the native counters on the tested matcher paths, alongside exact semantics under audit. It does not prove these counters cover every matcher operation, predict costs of other rule forms, establish general closure complexity, or show these degree profiles occur in natural workloads. The next gate is to capture runtime-derived graphs and rule definitions with the same counter conservation checks and exact replay oracle, preserving unmatched or unsupported runtime state rather than filtering it out.

## Artifacts

- [Preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_NATIVE_COUNTERS_V1_3_PREREG_20261004.md)
- [Runner](../../../scripts/verify_mint_termination_native_counters_v1_3.py)
- [Independent analyzer](../../../scripts/analyze_mint_termination_native_counters_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/mint_termination_native_counters_v1_3_lock_20261004.json)
- [Compressed paired capture](../../../evaluation/reports/mint_termination_native_counters_v1_3_20261004.json.gz), SHA-256 `4479b4c0f5082c75bd76d2c2eff3839fcebbc44514a65f0961802405f7c99f87`
- [Independent analysis](../../../evaluation/reports/mint_termination_native_counters_v1_3_analysis_20261004.json)

