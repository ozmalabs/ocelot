# Provider-authenticated WorldAdapter route v1.1 — results

Date: 2026-10-02

## Result

The source/native/seed-locked six-worker panel passed all 7 independent checks. The valid-signature arm adopted exactly one new `code_write_construction` shape in all 3/3 fresh processes. The tampered-signature arm received an `accepted` receipt from the legacy consistency adjudicator in all 3/3 processes, but the strict live route refused it and added zero code-write shapes in all 3/3. The test therefore distinguishes provider authentication from the receipt's internal consistency check on the actual `WorldAdapter.converse` route.

Median full `converse` time was 174.99 ms for valid evidence and 179.23 ms for tampered evidence on this host. With three samples per arm, this is descriptive end-to-end timing only; it does not show an authentication overhead difference or an operating-cost improvement. The earlier v1 raw node-count result remains preserved as diagnostic because normal conversation processing adds unrelated `ShapeSignature` nodes; v1.1 counts only nodes typed `kind="code_write_construction"`.

This is one authored scalar function family with a fixture oracle and process-local test key. It demonstrates route-level authentication when the strict option is enabled, not provider truthfulness, key isolation, production default enforcement, bypass resistance for direct/alternate legacy entrypoints, broad transfer, or general self-improvement.

## Artifacts

- [V1.1 amendment](SUBSTRATE_ADEQUACY_ADAPTER_PATH_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_adapter_path_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_adapter_path_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_adequacy_adapter_path_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_adapter_path_v1_1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_adapter_path_v1_1_analysis_20261002.json)
- [V1 diagnostic capture](../../../evaluation/reports/substrate_adequacy_adapter_path_v1_diagnostic_raw_20261002.json)
