# Native thoughtexperiment rule-patch semantics v1 — results

**Result:** 6/6 gates pass across 36 fresh processes. The native patch method matches the Python export/scan/remove/add control for all six candidate shapes on both scoped full-copy and shared-page backends. Each worker verifies the task's expected application/inertness and unchanged primary graph/rule revision, counts, and exported rules.

| Candidate shape | Expected behavior | Paired parity |
|---|---|---|
| Replace `sd_mint_quantum` | Apply positive repair | Pass |
| Remove `sd_mint_quantum` | Apply removal; candidate is non-inert | Pass |
| Absent target | No rule touched; candidate is inert | Pass |
| Existing plus absent target | Apply existing repair; ignore missing name | Pass |
| Replace later-slot `sd_dedup_existing` | Find and replace the named later rule | Pass |
| Replace both existing rules | Apply both edits in insertion order | Pass |

The native implementation was exercised through `imagine_and_check_convergence`'s default path; the legacy route was explicitly selected as the control. Based on this bounded parity evidence, native name-based patching is now the default and `_native_rule_patch=False` preserves the comparison path. The result supports a generic efficiency improvement for these rule-patch forms, while broad malformed-rule, full rewrite-dialect, natural-task, and multi-family compatibility remain unmeasured.

See the [preregistration](THOUGHTEXPERIMENT_NATIVE_RULE_PATCH_SEMANTICS_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_native_rule_patch_semantics_v1.py), [lock](../../../evaluation/substrate_capability/thoughtexperiment_native_rule_patch_semantics_v1_lock_20261001.json), and [raw capture](../../../evaluation/reports/thoughtexperiment_native_rule_patch_semantics_v1_raw_20261001.json).
