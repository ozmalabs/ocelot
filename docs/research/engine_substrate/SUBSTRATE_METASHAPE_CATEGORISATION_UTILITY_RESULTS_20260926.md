# MetaShape downstream categorisation utility (2026-09-26)

## Measured consumer and oracle

The evaluated consumer is the existing `domains.teach.categorise_by_shape`, called by `teach()` when no caller supplies a category or categoriser. It returns a MetaShape filing label or `None`, which leads to a fallback filing. The benchmark evaluates this direct decision before and after training on eight examples through the normal teach/observe/growth path. Its 20 gold labels were locked in the protocol, with a family-preserving label for positives and an explicit abstain label for fixed-field, missing-field, and type-change controls. MotionRule is a known prior-only family whose expected category is `spatial_dynamics` except for a changed type.

V1 is inadmissible and preserved: the runner mistakenly encoded two MotionRule gold labels as `None`. V1.1 corrected only those labels under a new lock, and v1.2 replicated it in a fresh process.

## Paired outcome, replicated exactly

| Metric | Seeded baseline | After MetaShape training |
|---|---:|---:|
| Exact decisions | 13/20 (65%) | 11/20 (55%) |
| Non-abstain coverage | 5/20 (25%) | 15/20 (75%) |
| Correct abstentions | 9/10 gold-abstain cases | 3/10 |
| Abstention recall | 90% | 30% |

V1.1 and v1.2 agree on every query prediction and all aggregate/per-family metrics. On ResourceTransfer and GoalTrace, training changes all five queries from abstention to the new MetaShape label: this correctly captures the positive and extra-field cases but also files the fixed-value, missing-field, and changed-type controls under that shape. FrameBinding's new shape is not selected by `categorise_by_shape` for any query. The preexisting `spatial_dynamics` prior remains unchanged on the five MotionRule cases, correctly classifying four and over-classifying the changed-type distractor.

This exposes a gap between the two measured outputs: the structural `ShapeObservation` decoder may report `recognized`/`covered_by` for a minted signature, while the actual teach filing consumer independently scores MetaShape principles/keywords and can abstain or overgeneralize. More category coverage is not more task utility here: exact accuracy drops by 10 points and abstention recall by 60 points under the locked oracle.

These figures are from 20 synthetic schema-classification items, not natural teaching examples or a human-judged semantic oracle. They establish a conditional result about this consumer/oracle pair, not global model quality.

## Reproducibility

- Oracle protocol: [preregistration](SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_PREREG_20260926.md)
- V1 correction: [v1.1 amendment](SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_V1_1_AMENDMENT_20260926.md)
- Independent replication: [v1.2 amendment](SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_V1_2_AMENDMENT_20260926.md)
- V1 invalidity audit: [analysis](../../../evaluation/reports/substrate_metashape_categorisation_utility_v1_analysis_20260926.json)
- V1.1 [runner](../../../scripts/substrate_metashape_categorisation_utility_v1_1.py), [lock](../../../evaluation/substrate_capability/metashape_categorisation_utility_v1_1_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_categorisation_utility_v1_1_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_categorisation_utility_v1_1_analysis_20260926.json)
- V1.2 [runner](../../../scripts/substrate_metashape_categorisation_utility_v1_2.py), [lock](../../../evaluation/substrate_capability/metashape_categorisation_utility_v1_2_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_categorisation_utility_v1_2_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_categorisation_utility_v1_2_analysis_20260926.json)
- Consumer and source: [`categorise_by_shape`](../../../domains/teach.py), [native MetaShape keyword scorer](../../../runners/dsl/src/shape_decode.rs)

## Next gate

Use independently labeled real filing examples and compare `categorise_by_shape` with explicit-category, domain/topic fallback, and abstention baselines. Before changing the learner or prior, separate structural `ShapeDecode` coverage from the keyword-prior consumer and test per-category calibration, false filing cost, and downstream retrieval utility.
