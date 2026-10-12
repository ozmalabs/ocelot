# Seed provider-scope / self-report intervention v1 results

Date: 2026-09-27

## Result

**Behavioral status: incomplete runtime environment.** This contrast omitted both `data/slabs` and the script-module dependency `scripts/collapse_engine.py`; it cannot support conclusions about route behavior of the provisioned substrate. The equality of graph and loaded manifests is still a valid observation for that stripped environment; route outcomes are superseded by the [v1.2 full-environment panel](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_RESULTS_20260927.md).

Six fresh processes (three per condition) passed all 9 independent gates on the same locked source tree. Replacing the baseline seed-provider loop with only the typed-provider scope-selection hunk did **not** change the result for `report your organisation`:

| Condition | Route | Loaded manifests | Graph | Semantic digest |
|---|---|---:|---:|---|
| Baseline (`boot_all.py` 9b9c2ac0…) | none; wordplay comprehension | 731 | 24,976 nodes / 11,428 edges | `39138ecf…0136f0` |
| Provider-scope hunk only (6662935b…) | none; wordplay comprehension | 731 | 24,976 nodes / 11,428 edges | `39138ecf…0136f0` |

All 731 loaded manifest IDs were identical; both conditions also reproduced the same 11 manifest failures. The exact reply and interpretation repeat in all workers. Thus the provider-scope hunk is not sufficient to restore this route in the baseline context and has no measured effect on this boot's selected seed set.

## Interpretation boundary

This is a controlled, one-hunk intervention on one prompt and one historical full-seed snapshot. It rules out that hunk as the sole cause of route restoration in this context. It does not rule out interactions, nor identify which subsequent `boot_all.py` edits matter. The later worktree version added content-selection and scaffold-retention behavior; those remain the next separate interventions. It also does not describe the live worktree, which continued changing during this study.

## Artifacts

- [Original design](SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_PREREG_20260927.md)
- [Amendment narrowing the contrast](SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_1_AMENDMENT_20260927.md)
- [Runner](../../../scripts/probe_seed_provider_scope_self_report_intervention_v1.py)
- [Independent analyzer](../../../scripts/analyze_seed_provider_scope_self_report_intervention_v1.py)
- [Archived baseline module](../../../evaluation/substrate_capability/fixtures/boot_all_before_provider_scope_20260927.py)
- [Provider-scope-only module](../../../evaluation/substrate_capability/fixtures/boot_all_provider_scope_only_20260927.py)
- [Source lock](../../../evaluation/substrate_capability/seed_provider_scope_self_report_intervention_v1_lock_20260927.json)
- [Raw paired capture](../../../evaluation/reports/seed_provider_scope_self_report_intervention_v1_20260927.json)
- [Analysis](../../../evaluation/reports/seed_provider_scope_self_report_intervention_v1_analysis_20260927.json)
