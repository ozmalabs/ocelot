# GenInfer stable-relation-identity ablation results (2026-09-26)

## Preregistered prediction: not supported

The analyzer passes eight of nine gates. The no-identity arm exactly reproduces the prior 60-observation capture, and positives recover the exact matrix without residual in both arms. Outputs are deterministic across five repeats; input/provenance checks pass. The preregistered prediction that stable IDs would make every corruption refuse fails: 15/45 stable-ID corrupted observations are accepted with alternative matrices.

| Layout | Corruption | No identity | Stable identity |
|---|---:|---|---|
| Original | +1 | accept, alternate `[0,0,0,2]` | accept, alternate `[0,0,0,2]` |
| Original | +2 | accept, generating `[1,1,0,2]` | accept, alternate `[-1,-1,0,2]` |
| Original | +3 | accept, alternate `[-2,-2,0,2]` | accept, alternate `[-2,-2,0,2]` |
| Orthogonal pairs | +1/+2/+3 | refuse all | refuse all |
| Paired square | +1 | refuse | refuse |
| Paired square | +2 | accept alternate `[-1,0,0,2]` | refuse |
| Paired square | +3 | refuse | refuse |

Aggregate corruption results: no-identity accepts 20/45, recovers the generating matrix in 5/45, and refuses 25/45. Stable identity accepts 15/45, recovers the generating matrix in 0/45, and refuses 30/45. Thus adding relation IDs reduces acceptance by five cases in this fixture but does not generally recover the generating matrix; on the original geometry it changes the +2 output from the generator to an alternative.

## Interpretation

Stable relation identity affects alignment, as expected, but does not remove the broader ambiguity. Even with pair identities fixed, the inducer can trade a different matrix against predicate-local residual transforms and select it under its ranking. The previous source analysis remains relevant for the no-ID arm, while this ablation shows it is insufficient as a complete explanation. The next analysis should compare candidate matrices under exact per-ID pairing and the implemented `(residual_dims, coefficient L1, lexicographic matrix)` order. The data do not justify changing the engine or its ranking without that accounting.

## Scope

This is one authored identity schema, one matrix, three layouts, and three perturbation magnitudes. It does not demonstrate relation IDs are normally present in learned signatures or establish general noise performance. The stable-ID arm keeps the field unchanged through the target and places it before coordinate fields so canonical sorting groups rows by identity.

## Artifacts

Protocol: [`SUBSTRATE_GENINFER_RELATION_IDENTITY_ABLATION_PREREG_20260926.md`](SUBSTRATE_GENINFER_RELATION_IDENTITY_ABLATION_PREREG_20260926.md). Runner/analyzer: [`geninfer_relation_identity_ablation_probe_v1.py`](../../../scripts/geninfer_relation_identity_ablation_probe_v1.py), [`analyze_substrate_geninfer_relation_identity_ablation_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_relation_identity_ablation_probe_v1.py). Raw data: [`substrate_geninfer_relation_identity_ablation_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json). Analysis (including the failed prediction gate): [`substrate_geninfer_relation_identity_ablation_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_analysis_20260926.json).
