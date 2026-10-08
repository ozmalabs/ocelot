# Bounded planner native unit audit — v1.4 results

## Result

All five preregistered exact-name Cargo test commands pass, each reporting exactly one passing test and zero failures. The passing cases cover equal-cost tie preservation, refusal on incomplete predictions, intervention-budget filtering and abstention, a worker selection grounded in a real transition rather than submitted witnesses, and worker/evaluator agreement on intervention limits.

The confirmatory v1.4 capture records the exact commands, child stdout/stderr paths and hashes, `rustc`/Cargo versions, source and Cargo manifest hashes, dirty-workspace fingerprint, plus the `RUSTFLAGS` and `LD_LIBRARY_PATH` overrides needed to link and load this PyO3 extension-module test binary. The checkout was dirty (143 tracked files at capture), so the result is tied to the explicit source hashes in the manifest, not a clean commit build. V1/v1.1 setup failures and v1.2 remain preserved. V1.3 also passes, but is exploratory because a protocol input was corrected after capture; v1.4 is the provenance-complete passing capture.

## Interpretation and limits

This is evidence for five bounded Rust mechanisms. It does not measure long-horizon search, branching beyond the authored bound, replanning after observations, held-out-world success, utility calibration, execution safety, or comparison against another planner. The Rust tests are unit fixtures and do not establish that the production runtime activates these paths for ordinary tasks.

Earlier exploratory passes: [v1.2](../../../evaluation/reports/substrate_planning_native_unit_audit_v1_2_20260928.json), [v1.3](../../../evaluation/reports/substrate_planning_native_unit_audit_v1_3_20260928.json).

## Artifacts

- Protocol: [preregistration](SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_PREREG_20260928.md)
- Amendments: [linker setup](SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_V1_1_AMENDMENT_20260928.md), [runtime library path](SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_V1_2_AMENDMENT_20260928.md), [environment capture](SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_V1_3_AMENDMENT_20260928.md), [protocol hash correction](SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_V1_4_AMENDMENT_20260928.md)
- Runner: [versioned test runner](../../../scripts/run_substrate_planning_native_unit_audit_v1_4.py)
- Manifest and outcomes: [five-case report](../../../evaluation/reports/substrate_planning_native_unit_audit_v1_4_20260928.json)
- Earlier setup evidence: [initial link failure](../../../evaluation/run_logs/substrate_planning_native_unit_audit_20260928_1.stderr.log), [v1.1 loader failure](../../../evaluation/run_logs/substrate_planning_native_unit_audit_v1_1_20260928_1.stderr.log)
