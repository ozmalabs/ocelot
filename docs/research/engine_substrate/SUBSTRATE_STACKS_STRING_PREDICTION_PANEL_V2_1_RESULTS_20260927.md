# Stacks string-predicate panel v2.1 current-source replication results

Date: 2026-09-27  
Status: completed; all independent analysis and runtime integrity gates pass.

## Result

The two fresh workers replayed the frozen v2 schedule on the current source snapshot. Each returned the exact oracle output on 25/25 Stacks calls, including 20/20 calls on the four held-out functions and five Unicode-prefix probes. Both arithmetic controls passed 2/2. The 25/25 coverage reproduces the targeted lowering's behavior; it is not blind transfer because the lowering was designed after inspecting the selected family. Predictions, errors, abstentions, receipt deltas, axis counts and minted-observation counts match the frozen v2 workers case by case. There were no wrong values, receipts or mints.

All runner integrity checks pass: two distinct worker PIDs, complete 27-call schedules, stable full locks before/after both workers, successful boots, and a hashed console capture in the shared run manifest. The independent analyzer passes every check, including AST-oracle reconstruction, source/case hashes, worker parity, frozen v1/v2 references and runtime-drift accounting.

## Cost and runtime envelope

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Stacks exact outputs | 25/25 | 25/25 |
| Held-out function outputs | 20/20 | 20/20 |
| Arithmetic controls | 2/2 | 2/2 |
| Median call wall time (27 calls) | 39.89 ms | 38.65 ms |
| p95 call wall time | 50.49 ms | 47.12 ms |
| Boot manifests loaded | 731/742 | 731/742 |
| Boot failures | 11 | 11 |
| Peak RSS | 1.805 GB | 1.806 GB |

Whole-module ingestion is included in each function prediction, so these are route costs, not isolated lowering costs. The cold boot dominates the resource envelope and has 11 repeatable manifest failures; neither is a useful-scale CPU throughput bound.

## Source drift and interpretation

Compared with the frozen v2 source lock, the current runtime differs in two files: `substrate/boot_profiles.py` and `substrate/boot_all.py`. The latter includes substantive seed-index and load-selection changes. All compared domains, substrate, world, seed, native Python, and Rust files other than those two match v2; the native extension hash and candidate/control frames also match. Because both runtime files changed, this replication does not isolate a boot-profile effect. It establishes that the v2 case-by-case behavior repeats under the current locked runtime despite the broader boot-system drift.

The v2.1 diagnostic correction and source-drift accounting are documented in the [amendment](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_1_AMENDMENT_20260927.md). The result remains targeted engineering evidence and does not estimate general code capability, natural prevalence, learning cost, or scaling.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_1_REPLICATION_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_stacks_string_prediction_panel_v2_1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_stacks_string_prediction_panel_v2_1.py)
- [Source lock](../../../evaluation/substrate_capability/stacks_string_prediction_panel_v2_1_lock_20260927.json)
- [Frame](../../../evaluation/reports/stacks_string_prediction_frame_v2_1_20260927.json)
- [Raw workers and run manifest](../../../evaluation/reports/stacks_string_prediction_panel_v2_1_20260927.json)
- [Independent analysis](../../../evaluation/reports/stacks_string_prediction_panel_v2_1_analysis_20260927.json)
- [Console capture](../../../evaluation/run_logs/stacks-string-prediction-panel-v2-1-20260927.stdout_stderr.log)

Final artifact SHA-256 values: frame `5a0f2b31d30835ab44e664dc61a238ee5d76b32b5370b0750e66f394edbb8927`; raw `f50cd5797b76534438357615c0fe55a3d08d984e815e9eebb589e3ac236b54ff`; analysis `79b2a4f0fdfcf1965b6bc093fde62ff4f4ad14252149df0780229f2f8671c10b`; source lock `9a5779c64013604d373f68c6f2c5d9bc4da456a6616d981993ccd2a363b75fe4`.
