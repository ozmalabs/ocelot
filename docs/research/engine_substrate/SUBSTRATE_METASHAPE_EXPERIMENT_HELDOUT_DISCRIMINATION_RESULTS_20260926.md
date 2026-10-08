# MetaShape experiment-summary held-out discrimination (2026-09-26)

## Result

Two fresh-process source-locked captures passed seven gates each on the same fixed pattern. Two supported experiment summaries varying in `axis_tag` and topic minted one MetaShape (`support=2`). A new supported summary with new values for those varying fields was recognized and attributed to that exact MetaShape. A refuted summary with the fixed `answer` field changed was left `residual`, was not covered by that MetaShape, and caused no additional mint. The observation/status and covered-by records match across both processes.

This supports a narrow claim: the graph-authored growth rule abstracts the two varying fields while retaining the fixed `answer` relation in this experiment-summary schema, and that abstraction transfers to one held-out supported summary while refusing one fixed-field control. Outcome labels and examples were authored by the harness. This is not evidence that the conclusions are true, a population false-positive rate, or transfer across schemas/domains.

## Reproduction

Protocol: [preregistration](SUBSTRATE_METASHAPE_EXPERIMENT_HELDOUT_DISCRIMINATION_PREREG_20260926.md); replication: [v1.1 amendment](SUBSTRATE_METASHAPE_EXPERIMENT_HELDOUT_DISCRIMINATION_V1_1_AMENDMENT_20260926.md).

| Run | Runner | Lock | Raw | Analysis |
|---|---|---|---|---|
| v1 | [runner](../../../scripts/substrate_metashape_experiment_heldout_discrimination_v1.py) | [lock](../../../evaluation/substrate_capability/metashape_experiment_heldout_discrimination_v1_lock_20260926.json) | [capture](../../../evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_20260926.json) | [gates](../../../evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_analysis_20260926.json) |
| v1.1 fresh-process replication | [runner](../../../scripts/substrate_metashape_experiment_heldout_discrimination_v1_1.py) | [lock](../../../evaluation/substrate_capability/metashape_experiment_heldout_discrimination_v1_1_lock_20260926.json) | [capture](../../../evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_1_20260926.json) | [gates](../../../evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_1_analysis_20260926.json) |

## Next capability gate

Scale the contrast across held-out positive and fixed-field negative examples, multiple schema families, and distractors that preserve the same fields but alter more than one fixed relation. Track false recognition, residuals, additional mints, graph growth, and downstream task utility. Keep automatic production adoption gated until those decision-quality measures are available.
