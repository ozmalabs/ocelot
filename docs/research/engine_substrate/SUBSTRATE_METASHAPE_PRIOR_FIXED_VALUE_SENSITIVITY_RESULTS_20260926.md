# MetaShape fixed-value/prior sensitivity sweep (2026-09-26)

## Rung-specific outcome

The locked 40-observation panel and an exact fresh-process replication agree on every family/control category. It contains eight training examples, four positive holdouts, and 28 controls over four item types. The control outcomes are:

| Outcome rung | Cases | Interpretation |
|---|---:|---|
| `recognized`, attributed to target MetaShape | 3 | Extra-field controls; consistent with open structural coverage |
| `recognized_prior`, attributed to target MetaShape | 12 | Four changed fixed values each for ResourceTransfer and GoalTrace, plus their missing-fixed-field and changed-type controls |
| `recognized_prior`, attributed to another prior | 7 | All seven MotionRule controls are absorbed by the preexisting `spatial_dynamics` prior |
| `residual` | 6 | FrameBinding fixed-value changes and selected missing/type controls |

No control caused an additional mint. The eight pairwise capture results (v1 and v1.1 by four categories) match exactly. These are fixed-panel counts, not natural error prevalence.

## Reading the result

The ladder has materially different sensitivity by rung. The structural matcher treats the minted pattern as open to extra relations in the tested cases, which is consistent with `CoversOpen`. The weaker prior attributes many same-predicate observations despite fixed-value changes, missing fixed fields, or type changes. A distinct preexisting `spatial_dynamics` prior can absorb a candidate family before it mints a new signature. Therefore a single `covered_by` field or broad `recognized*` status is not an adequate capability metric: report status rung, selected shape, residual, and exact fixed-field agreement together.

The held-out `TaughtHint` experiment pair that passed earlier remains true within its narrow schema. The 40-case extension shows why it cannot support a broad precision claim: the weak prior frequently labels controls and the matcher may ignore distinctions that a downstream task could require.

## Evidence

- Protocol: [v1 preregistration](SUBSTRATE_METASHAPE_PRIOR_FIXED_VALUE_SENSITIVITY_V1_PREREG_20260926.md)
- Independent replication: [v1.1 amendment](SUBSTRATE_METASHAPE_PRIOR_FIXED_VALUE_SENSITIVITY_V1_1_AMENDMENT_20260926.md)
- V1 [runner](../../../scripts/substrate_metashape_prior_fixed_value_sensitivity_v1.py), [lock](../../../evaluation/substrate_capability/metashape_prior_fixed_value_sensitivity_v1_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_analysis_20260926.json)
- V1.1 [runner](../../../scripts/substrate_metashape_prior_fixed_value_sensitivity_v1_1.py), [lock](../../../evaluation/substrate_capability/metashape_prior_fixed_value_sensitivity_v1_1_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_1_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_1_analysis_20260926.json)

## Next gate

Add a downstream task oracle that uses these observations to choose or validate an action. Measure outcome utility for structural recognition, prior-only attribution, and residual abstention on independently labeled examples. Keep the present engine unchanged during that measurement; capability is not established by recognition labels alone.
