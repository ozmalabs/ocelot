# Strict code-write adoption surface v1.2 — results

Date: 2026-10-02

## Result

The source/native/seed/fixture-locked panel completed 12 fresh processes with no within-run source drift. All 9 independent analyzer checks pass.

| Entry path | Result |
|---|---|
| Valid signed evidence through `WorldAdapter.converse` | 3/3 adopted exactly one new typed code-write shape |
| Tampered signature with internally accepted receipt | 3/3 refused; zero code-write shapes adopted |
| Direct `teach_write_shape_from_example` call on a strict adapter, no evidence | 3/3 refused; zero code-write shapes adopted |
| Published curriculum helper on a strict adapter, no evidence | 6/6 function attempts refused across 3 runs; zero code-write shapes adopted |

The strict gate now lives at the shared `teach_write_shape_from_example` adoption boundary, so the conversational route and `code_curriculum.learn_functions_from_lesson` cannot bypass it by calling that function directly. The adapter's construction-time provider registry is used to check the exact request candidate ID and Term before shape teaching. Valid-signature full-conversation median was 175.02 ms; tampered-signature median was 176.05 ms. These three-sample timings are descriptive only.

The gate remains explicitly opt-in. Non-strict agents retain legacy teaching behavior; lower-level direct `domains.teach.teach()` calls and the separate held-predication composition path are not authenticated by this option. This panel covers one authored square-function family on one host and does not establish provider truthfulness, process key isolation, independent task-family transfer, or general self-improvement.

V1's pre-seed-load curriculum counts are preserved as diagnostic. V1.1 established the corrected baseline protocol; v1.2 is the current-source replay and primary report.

## Artifacts

- [V1.2 preregistration](SUBSTRATE_ADEQUACY_ADOPTION_SURFACE_V1_2_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_adoption_surface_v1_2.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_adoption_surface_v1_2_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_adoption_surface_v1_2_analysis_20261002.json)
- [V1.1 corrected but superseded capture](../../../evaluation/reports/substrate_adequacy_adoption_surface_v1_1_raw_20261002.json)
- [V1 diagnostic capture](../../../evaluation/reports/substrate_adequacy_adoption_surface_v1_diagnostic_raw_20261002.json)
