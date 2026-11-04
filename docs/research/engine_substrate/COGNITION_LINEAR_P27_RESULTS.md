# P27 scheduled-checkpoint successor v1 results

**Status:** complete, structurally valid, registered efficacy gate failed (flat ceiling).
**Preregistration:** [`COGNITION_LINEAR_P27_PREREG.md`](COGNITION_LINEAR_P27_PREREG.md), frozen in `260029d4`; implementation is `0a2f8c22`.
**Scope:** finite simulator evidence only. The original P22 preregistration remains `DRAFT — NOT FROZEN` and is not amended by this result.

## Execution and integrity

The one-shot held-out command completed and its marker is `complete`. The raw artifact contains 8,000 scored records: 6,400 common-test rows (400 worlds × 4 arms × 4 checkpoints) and 1,600 independent-validation rows (400 worlds × 4 arms at g3). There are 200 test and 200 validation worlds per family. The raw file is 17,267,526 bytes with SHA-256 `5477802e0471b91fa933f113e4b2a9372761a1800d902708097e3c54df8e0e62`. The analysis file is 14,705 bytes with SHA-256 `0e3f4bf41f827f02d7705f4b6b06d4b94d44f8379506f4f6e597e11db2930d51`.

Analyzer structural status is **VALID**, with 0 structural failures; runtime status is **ATTESTED**. The preregistered allocation digest is `814da3ba7b2c936212ebcd553fb4fd3e1ea8f37eea3f4afd526fd1f32685dae2` and source-bundle digest is `508e5949da8fd28f2c7c26e6fdcae41439d107b6d69a558289fc036a0fc138b1`. The full raw record binds the allocation and per-family world IDs; all arm comparisons use the same worlds at each checkpoint. No score fed back to training.

## Registered outcomes

Every family × arm × checkpoint cell scored 200/200 (100%) with zero missing predictions. This includes g0 and the frozen ancestor: the held-out panel was already at ceiling before scheduled learning intervals. The independent g3 validation panel also scored 200/200 for every family × arm. Accordingly, all paired effects are exactly zero; flat and ceiling outcomes were retained under the preregistration.

| Family | Arm vs frozen ancestor | Final gain | One-sided 99% lower bound | Checkpoint slope | One-sided 99% lower bound | Holm p (gain / slope) | Registered contrast |
|---|---|---:|---:|---:|---:|---:|---|
| branching_relation | combined | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |
| branching_relation | evidence_selection_only | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |
| branching_relation | process_search_only | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |
| cyclic_relation | combined | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |
| cyclic_relation | evidence_selection_only | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |
| cyclic_relation | process_search_only | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 / 1.00 | FAIL |

The paired bootstrap intervals are degenerate at `[0.00, 0.00]` for both estimands in all six family/arm contrasts because every paired world/checkpoint difference is zero. The primary combined-minus-ancestor contrasts fail the registered ≥0.10 final-gain, ≥0.05/checkpoint slope, positive-lower-bound, and Holm-adjusted p<0.01 requirements in both families. The phase efficacy gate is **false**; this is a valid negative advantage result, not an invalid or incomplete run.

### Per-cell test and validation results

| Family | Arm | g0 | g1 | g2 | g3 | Validation g3 | Missing test / validation | Pending at g3 test / validation |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| cyclic_relation | frozen_ancestor | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| cyclic_relation | evidence_selection_only | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| cyclic_relation | process_search_only | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| cyclic_relation | combined | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| branching_relation | frozen_ancestor | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| branching_relation | evidence_selection_only | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 0 / 0 |
| branching_relation | process_search_only | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 200 / 200 |
| branching_relation | combined | 200/200 | 200/200 | 200/200 | 200/200 | 200/200 | 0 / 0 | 200 / 200 |

## Training, pending proposals, and resource strata

Each family/arm started from three common authorized baseline training receipts. Evidence-selection-only delivered four additional target receipts; combined delivered three; frozen and process-search-only delivered none. Native search used four attempts in each search-enabled lineage (16 total). It produced one unapproved candidate in branching-relation process-search-only and one in branching-relation combined; both are retained as `authorization_pending` at g3. Neither received an approval, was executed, nor created an adoption receipt. Every other lineage added no candidate. Candidate search produced no action authority.

All 32 family × arm × checkpoint resource strata follow. `work` and `native rules` are cumulative counts; `exposure` is source exposure; `debits` are shared-budget charges; `access` is cumulative scheduled task-world access. Graph bytes are the complete captured graph footprint.

| Family | Arm | CP | Work | Source exposure | Native rules | Graph bytes | Budget debits | Task accesses | Interval status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| branching_relation | combined | g0 | 19 | 0 | 19 | 279,593 | 3 | 0 | initial |
| branching_relation | combined | g1 | 38 | 0 | 38 | 298,567 | 8 | 1 | progress |
| branching_relation | combined | g2 | 54 | 0 | 54 | 315,166 | 12 | 2 | progress |
| branching_relation | combined | g3 | 79 | 0 | 79 | 341,220 | 16 | 4 | authorization_pending |
| branching_relation | evidence_selection_only | g0 | 18 | 0 | 18 | 279,703 | 3 | 0 | initial |
| branching_relation | evidence_selection_only | g1 | 30 | 0 | 30 | 292,706 | 6 | 1 | progress |
| branching_relation | evidence_selection_only | g2 | 38 | 0 | 38 | 303,302 | 8 | 2 | progress |
| branching_relation | evidence_selection_only | g3 | 51 | 0 | 51 | 323,158 | 11 | 4 | progress |
| branching_relation | frozen_ancestor | g0 | 18 | 0 | 18 | 279,415 | 3 | 0 | initial |
| branching_relation | frozen_ancestor | g1 | 18 | 0 | 18 | 282,088 | 3 | 1 | progress |
| branching_relation | frozen_ancestor | g2 | 18 | 0 | 18 | 284,762 | 3 | 2 | progress |
| branching_relation | frozen_ancestor | g3 | 18 | 0 | 18 | 290,109 | 3 | 4 | progress |
| branching_relation | process_search_only | g0 | 19 | 0 | 19 | 279,989 | 3 | 0 | initial |
| branching_relation | process_search_only | g1 | 27 | 0 | 27 | 288,829 | 5 | 1 | search_failed |
| branching_relation | process_search_only | g2 | 35 | 0 | 35 | 297,669 | 7 | 2 | search_failed |
| branching_relation | process_search_only | g3 | 53 | 0 | 53 | 316,467 | 11 | 4 | authorization_pending |
| cyclic_relation | combined | g0 | 19 | 0 | 19 | 279,046 | 3 | 0 | initial |
| cyclic_relation | combined | g1 | 38 | 0 | 38 | 297,650 | 8 | 1 | progress |
| cyclic_relation | combined | g2 | 54 | 0 | 54 | 313,911 | 12 | 2 | progress |
| cyclic_relation | combined | g3 | 77 | 0 | 77 | 338,397 | 16 | 4 | progress |
| cyclic_relation | evidence_selection_only | g0 | 18 | 0 | 18 | 279,156 | 3 | 0 | initial |
| cyclic_relation | evidence_selection_only | g1 | 30 | 0 | 30 | 291,886 | 6 | 1 | progress |
| cyclic_relation | evidence_selection_only | g2 | 38 | 0 | 38 | 302,241 | 8 | 2 | progress |
| cyclic_relation | evidence_selection_only | g3 | 51 | 0 | 51 | 321,636 | 11 | 4 | progress |
| cyclic_relation | frozen_ancestor | g0 | 18 | 0 | 18 | 278,868 | 3 | 0 | initial |
| cyclic_relation | frozen_ancestor | g1 | 18 | 0 | 18 | 281,491 | 3 | 1 | progress |
| cyclic_relation | frozen_ancestor | g2 | 18 | 0 | 18 | 284,114 | 3 | 2 | progress |
| cyclic_relation | frozen_ancestor | g3 | 18 | 0 | 18 | 289,361 | 3 | 4 | progress |
| cyclic_relation | process_search_only | g0 | 19 | 0 | 19 | 279,442 | 3 | 0 | initial |
| cyclic_relation | process_search_only | g1 | 27 | 0 | 27 | 288,135 | 5 | 1 | search_failed |
| cyclic_relation | process_search_only | g2 | 35 | 0 | 35 | 296,827 | 7 | 2 | search_failed |
| cyclic_relation | process_search_only | g3 | 51 | 0 | 51 | 314,214 | 11 | 4 | search_failed |

Observed resource ranges were 18–79 cumulative primitive work, 18–79 native-rule steps, 278,868–341,220 graph bytes and 3–16 shared-budget debits; source exposure was zero throughout. All are within the frozen 250,000 native-rule-step, 2,000,000-byte graph, and 32-debit/search resource limits. Realized arm costs differ, so **efficiency is NOT_ESTABLISHED**. Checkpoint task access follows the fixed `[0,1,2,4]` schedule. No checkpoint or result was filtered for success.

## Controls and interpretation

All 100/100 integrity controls passed: 34 held-out selector-denial checks, 33 receipt-replay checks, and 33 approval-boundary checks. The approval-boundary controls recorded zero approval-policy activation, simulator transitions, adoption approvals, and adoption receipts. The two pending search candidates do not change those counts.

P27 closes as a completed, attested, structurally valid evaluation with no measured cumulative advantage: the shared baseline was already perfect at g0, and all four arms remained perfect through g3. Evidence selection and native process search add resource cost without changing measured success. This does not establish improvement, efficiency, novel goal performance, human-relative ability, or broad recursive competence. P16–P22 outcomes and capability-level dispositions remain unchanged; no L-level closure follows from finishing the P27 reporting cycle.

## Reproduction references

- Raw: [`p27_linear_v1_heldout_20261025.json`](../../../evaluation/process_mastery/results/p27_linear_v1_heldout_20261025.json), SHA-256 `5477802e0471b91fa933f113e4b2a9372761a1800d902708097e3c54df8e0e62`.
- Analysis: [`p27_linear_v1_heldout_20261025_analysis.json`](../../../evaluation/process_mastery/results/p27_linear_v1_heldout_20261025_analysis.json), SHA-256 `0e3f4bf41f827f02d7705f4b6b06d4b94d44f8379506f4f6e597e11db2930d51`.
- Completion marker: [`.p27_v1_heldout_run_started`](../../../evaluation/process_mastery/results/.p27_v1_heldout_run_started) (status `complete`, raw hash agrees).
- Frozen allocation, source/runtime details and all concrete seeds: [`COGNITION_LINEAR_P27_PREREG.md`](COGNITION_LINEAR_P27_PREREG.md).
- Prescribed E1/E2 regression command passed 96 tests before freeze; final targeted checkpoint/allocation bundle passed 9 tests before the held-out run.
