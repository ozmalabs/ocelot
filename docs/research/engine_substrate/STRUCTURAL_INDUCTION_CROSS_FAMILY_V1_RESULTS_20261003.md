# Cross-family structural induction v1.1 results

Date: 2026-10-03

## Results

The corrected, source-locked capture and independent analyzer pass integrity checks across five panels in each of three numeric task families. The additive holdout correction yields 133 positive and 2,268 negative examples, avoiding the zero-positive grid in the initial capture.

| Target family | Exact holdouts | Median oracle labels | Median synthesis calls | Median synthesis-call wall time |
|---|---:|---:|---:|---:|
| Absolute-value equality | 5/5 | 8 | 4 | 82 ms |
| Additive equality | 5/5 | 8 | 5 | 434 ms |
| XOR of axis oppositions | 1/5 | 4 | 5 | 609 ms |

All four XOR failures ended with a synthesis timeout after the fixed expansion ladder had grown to include `Plus`; one worker reached the six-agreement stop with an exact holdout term. The two simpler relation families generalized exactly under the same policy and six-agreement stopping threshold. This is preliminary evidence that the substrate's enumerative learner can acquire several authored numeric relations under a shared expansion schedule, while also exposing a substantial search-cost/failure boundary on XOR.

The first v1 capture is retained only as a diagnostic artifact: its additive fractional holdout had no positive cases and its apparent exactness was vacuous. V1.1 changes only that task's holdout domain to include zero, so the expected-value coordinate can equal integer sums. The result remains limited to three related numeric tasks, five seeded panels per task, and a human-authored operator order, stopping policy, and oracle. It does not show autonomous primitive invention, broad transfer, natural-task capability, or general adequacy detection. Holdout scores are evaluator-only.

## Artifacts

- [Base protocol](STRUCTURAL_INDUCTION_CROSS_FAMILY_V1_PREREG_20261003.md) and [holdout correction amendment](STRUCTURAL_INDUCTION_CROSS_FAMILY_V1_1_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_structural_induction_cross_family_v1_1.py) and [analyzer](../../../evaluation/substrate_capability/analyze_structural_induction_cross_family_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/structural_induction_cross_family_v1_1_lock_20261003.json), [capture](../../../evaluation/reports/structural_induction_cross_family_v1_1_20261003.json), and [analysis](../../../evaluation/reports/structural_induction_cross_family_v1_1_analysis_20261003.json)
