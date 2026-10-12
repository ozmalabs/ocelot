# Numeric relation model-adequacy audit v1.1 results

## Result

The source-locked capture contains five panels each for additive conservation,
product conservation, and componentwise opposition. Independent analysis passes
all six gates: frozen pools, exact selector/challenge transcript replay, paired
entropy-phase equality, rescored candidate/holdout outputs, positive-control
exact-target retention, and source/capture binding.

Without challenge queries, all five additive and product panels stop at false
singletons. The six-label challenge phase leaves additive false singletons in
2/5 panels and empties the version space in 3/5. It empties the product version
space in all 5/5 panels. Finite challenge labels can expose model failure, but
they do not ensure an adequate outcome: two additive panels still report a
false singleton.

The opposition positive control retains an exact target through all six
challenge labels in 5/5 panels and ends with an exact singleton each time.
This control used 16 coverage-directed examples, versus four random examples
for each out-of-grammar task; median synthesis time was 4.16 ms versus
1.71–1.78 ms. It validates the audit path when a correct candidate is
available, but is not a matched sample-size performance comparison. The v1
result remains immutable and diagnostic because one of its four-example
control panels lacked an exact candidate at synthesis time.

## Limits and next experiment

Targets, labels, and challenge schedules are harness-authored over a small
numeric domain. The fractional holdout scores exactness only on 1,296 points;
the local oracle supplies challenge labels. Empty candidate sets are evidence
of grammar mismatch, not a learned repair. No result here establishes
open-ended self-improvement or natural task prevalence.

Next measure whether the system can use an explicit adequacy signal to choose
among three actions: continue querying, widen the grammar, or request external
help. Include multiple grammar-mismatch families, within-grammar controls with
matched training sizes, and a cost-sensitive outcome metric. Keep task labels
and held-out oracle inaccessible to the policy under evaluation. Compare
false-singleton rate, empty-set rate, correct resolution, oracle calls,
synthesis work, and wall/CPU time.

## Reproduction artifacts

- Protocol amendment: [v1.1 preregistration](NUMERIC_RELATION_MODEL_ADEQUACY_AUDIT_V1_1_AMENDMENT_20261003.md)
- Runner: [source-locked runner](../../../evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1.py)
- Analyzer: [independent analyzer](../../../evaluation/substrate_capability/analyze_numeric_relation_model_adequacy_audit_v1_1.py)
- Source lock: [locked panels and sources](../../../evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json)
- Capture: [raw worker records](../../../evaluation/reports/numeric_relation_model_adequacy_audit_v1_1_20261003.json)
- Analysis: [independent results](../../../evaluation/reports/numeric_relation_model_adequacy_audit_v1_1_analysis_20261003.json)
