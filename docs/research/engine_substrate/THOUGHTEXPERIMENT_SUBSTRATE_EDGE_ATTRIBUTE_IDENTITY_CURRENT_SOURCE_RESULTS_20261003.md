# Edge-attribute identity composer — current-source results

Date: 2026-10-03

## Gate result

The current-source rerun preserves the October 2 identity-guard result. Four
workers complete recurrence, repeated-reply, relation-only actor, and
actor+verb identity conditions, with two training and two held-out repetitions
per condition. The source lock includes 47 inputs and matches before/after both
stages and in independent analysis. The analyzer passes 14/14 checks.

The graph composer selects the expected relation-level guard in the recurrence
and reply controls, and both families pass all eight held-out cases each. On the
actor-recipient task, the relation-only guard passes its one-verb training
cases but suppresses the distinct second verb in all eight held-outs (`[1,0]`).
The attribute identity condition selects the generated `actor+verb` guard and
passes all eight held-outs (`[1,1]`). The unmodified rule passes its controls.
No-overlap and ambiguous-site controls abstain in all four workers, and the
primary target rules remain unchanged during composition.

## Cost and boundary

Median composition times are 37.68 ms (recurrence), 30.91 ms (reply), 26.02 ms
(relation-only actor), and 20.25 ms (actor+verb identity). Actor training and
held-out candidate scoring medians are about 4.4–4.5 ms. These are sequential
measurements from one host; the conversation path includes world-adapter work,
so family costs are not directly comparable.

This current-source result confirms a prompted repair using generated
attribute-signature sites. The harness supplies target, cue, examples, and
oracle. Site generation is limited to direct attributes on fresh nodes and
singleton/pair/full-set signatures; computed/nested fields, natural cue
formation, and broad task prevalence remain unmeasured. The paired result
shows the substrate can select a useful richer representation when given a
specific cue; it does not show that it derives the cue from an unlabelled
residual.

## Artifacts

- [Original preregistration](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_PREREG_20261002.md) and [current-source amendment](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_CURRENT_SOURCE_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_current_source_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_attribute_identity_current_source_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_lock_20261003.json)
- [Frozen orders](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_orders_20261003.json), [held-out scores](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_scores_20261003.json), [analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_current_source_v1_analysis_20261003.json)
- [Historical v1 results](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_RESULTS_20261002.md)

## Next gate

Measure site-count growth and composition cost across identity-field counts
and graph sizes, then test absent, constant, and computed identity fields as
explicit admission/refusal controls. Keep candidate pool generation and cue
formation separate so costs can be attributed. After that, test whether a
residual-grounding mechanism can form the structured actor+verb cue without
the task naming identity or the operator.
