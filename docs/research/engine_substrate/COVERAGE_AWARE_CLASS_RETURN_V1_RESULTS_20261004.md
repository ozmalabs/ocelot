# Coverage-aware class return v1 results

## Result

The source-locked capture contains 25 frozen panels across additive,
product, ordering, opposition, and inequality. The independent v1.1 replay
reconstructs every survivor set from the frozen initial hypotheses and
recorded labels, checks the oracle labels, recomputes behavior signatures
over the policy's covered probes, and rescans all 6,560 fractional holdout
rows for each survivor. It passes with no discrepancies.

The policy expanded the probe set on 10 panels. It returned a single finite
behavior class on five panels; every returned member matched the task across
the finite holdout. The remaining 20 panels ended with an exact single term.
There were no teacher-help calls; median oracle-label use was two. A later
structural-diversity audit found that each of the five class returns contains
four IDs for one canonical Term JSON value. Thus the original result
demonstrates correct grouping of duplicate grammar outputs, not useful
equivalence-class return across distinct hypotheses. See the
[deduplication ablation](TERM_DEDUPLICATION_CLASS_RETURN_V1_RESULTS_20261004.md)
for the corrected interpretation and label-cost comparison.

## Interpretation and limits

This closes the finite coverage-policy replay gate, while the duplicate-Term
finding narrows its capability claim. The candidate pool was precomputed by
the upstream semantic-equivalence study, the five relations are authored,
and exactness is restricted to the finite holdout. After exact Term
deduplication, all five apparent class returns become exact-term outcomes
and the median label cost rises from two to three. The original policy did
not establish useful return of diverse equivalence classes. It also did not
execute a CoW graph branch, produce a graph residual, or adopt a rule.

## Reproduction artifacts

- [Protocol](COVERAGE_AWARE_CLASS_RETURN_V1_PREREG_20261003.md)
- Runner: [coverage_aware_class_return_v1.py](../../../evaluation/substrate_capability/coverage_aware_class_return_v1.py)
- [Source lock](../../../evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/coverage_aware_class_return_v1_20261003.json)
- [Locked integrity analysis](../../../evaluation/reports/coverage_aware_class_return_v1_analysis_20261004.json)
- [Independent replay analyzer](../../../evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py)
- [Independent replay analysis](../../../evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json)
