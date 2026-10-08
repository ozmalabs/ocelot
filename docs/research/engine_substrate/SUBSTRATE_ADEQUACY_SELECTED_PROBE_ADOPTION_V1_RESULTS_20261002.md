# Challenger-selected probe adoption gate v1 — results

Date: 2026-10-02

## Result

The source/native/seed-locked panel completed 12 fresh processes without source drift. The independent analyzer passes all 12 checks, including replay of the selection record, provider signatures, and core receipts.

| Condition | Selected probe entropy | Receipt | Adoption | Held-out result |
|---|---:|---|---:|---:|
| Square vs identity; broad domain; truthful square label | 1 bit | accepted | 3/3 | 9/9 correct |
| Identity vs square; alias-only `x=0`; truthful label | 0 bits | accepted | 0/3 | Refused before adoption |
| Identity vs square; broad domain; truthful square label | 1 bit | rejected | 0/3 | Refused by receipt residual |
| Identity vs square; broad domain; trusted false identity label | 1 bit | accepted | 3/3 | 0/9 correct |

The opt-in `require_discriminating_code_example_probe` adapter policy implies authenticated evidence and recomputes the maximum-entropy selection before the shared teaching function reaches `_teach_shape`. It requires exact selector-result parity, a positive-entropy selection, a single signed request probe equal to the selected input, and request seed/acquisition/domain bindings. The strict policy survives checkpoint save/load; provider secrets are not serialized, and a restored adapter without key reinjection fails closed.

The gate blocks the measured alias-only case. It only establishes separation from the caller-supplied challenger set and admissible domain; it cannot establish those sets are complete or representative. It also does not solve trusted provider dishonesty: the false signer still causes adoption when its wrong answer agrees with the candidate on the selected input. The route remains opt-in, and provider independence and low-level direct `teach()` remain outside this policy.

## Scope

One authored square/identity task family, one host, one test key, and three fresh runs per condition. These are capability-boundary measurements, not a natural-task error rate or broad transfer result.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_SELECTED_PROBE_ADOPTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_selected_probe_adoption_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_selected_probe_adoption_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_selected_probe_adoption_v1_analysis_20261002.json)
