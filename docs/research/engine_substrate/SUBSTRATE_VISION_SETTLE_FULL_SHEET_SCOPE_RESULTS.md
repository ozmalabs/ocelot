# Full built-sheet root-scoped competition fidelity

**Run:** 2026-09-25. **Evidence:** four paired native workloads from `settle_lib.build_sheet`, with independent equation/provenance audit. The authored seed and engine source remain unchanged.

## Design and findings
Each paired workload built complete 3×3 or 4×4 SUnit anatomy with connectivity 8, using the same seed for global and root-scoped arms. A deterministic matched afferent field was installed and `aff_step` matched the single Retina root's step. All rules except the selected `st_settle` clone and `st_commit` were tombstoned in the benchmark substrate; native `run_rules` executed the batch rules.

Across all four pairs, the Retina root owned every built SUnit, terminal activation arrays were identical between variants, and native progress-application counts matched. The independent analyzer recomputed the update equation using the full lattice neighbor sets. All eight terminal states had max absolute residual ≤2.23×10⁻¹⁶, below the registered 10⁻¹² numerical tolerance.

Three cases consumed the full 10,000 application cap under the engine's exact progress test, despite residuals at float64 last-bit scale. The fourth stopped after 176 applications. The capped cases are classified as numerical convergence, not exact engine termination. A v1 harness error and the v1.1 cap exits remain preserved in their raw reports.

## Evidence
- [`v1 preregistration`](SUBSTRATE_VISION_SETTLE_FULL_SHEET_SCOPING_PREREG_20260925.md), [`v1.1 driver correction`](SUBSTRATE_VISION_SETTLE_FULL_SHEET_SCOPING_V1_1_AMENDMENT_20260925.md), [`v1.2 residual amendment`](SUBSTRATE_VISION_SETTLE_FULL_SHEET_SCOPING_V1_2_AMENDMENT_20260925.md)
- [`runner`](../../../scripts/substrate_vision_settle_full_sheet_scope.py), [`independent analyzer`](../../../scripts/analyze_substrate_vision_settle_full_sheet_scope_v1_2.py)
- [`v1.2 raw`](../../../evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_2_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_2_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_settle_full_sheet_scope_v1_2_lock_20260925.json)
- Preserved earlier attempts: [v1 raw](../../../evaluation/reports/substrate_vision_settle_full_sheet_scope_20260925.json), [v1.1 raw](../../../evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_1_20260925.json)

## Claim boundary and next gate
This establishes one-sheet semantic fidelity of root-scoped competition on these built workloads. It does not measure orientation selectivity, visual task outcomes, learning, full-sheet multiplicity, or performance benefit. Next compare both variants in the actual orientation-response pipeline on identical stimuli and report OSI/task quality, afferent and settled states, exact-cap status, residual, application counts, and repeated timing. Keep production seed unchanged until task outcomes are shown equivalent or a justified improvement is documented.
