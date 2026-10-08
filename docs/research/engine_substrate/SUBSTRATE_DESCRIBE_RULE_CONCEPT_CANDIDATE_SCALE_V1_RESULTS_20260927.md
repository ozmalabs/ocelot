# Describe-rule Concept candidate scaling v1 results (2026-09-27)

## Result

All 15 source-locked workers pass: three fresh processes at each of five Concept populations, fixed-point closure, and exact preservation of the three positive classifications with no distractor classification. The independent per-worker analyzer confirms the same count formula for every rule at every size:

- `candidate_pairs = C + 3`
- `term_evaluations = 4C + 18`

Here `C` includes the three positive target Concepts; the added `3` distractors-to-matches contrast is fixed. Aggregate counts across the three rules therefore rise linearly with the membership population in this controlled workload.

| Distractors | Concepts `C` | Candidate pairs | Term evaluations | Audited closure wall median |
|---:|---:|---:|---:|---:|
| 0 | 3 | 18 | 90 | 0.111 ms |
| 64 | 67 | 210 | 858 | 0.252 ms |
| 256 | 259 | 786 | 3,162 | 0.417 ms |
| 1,024 | 1,027 | 3,090 | 12,378 | 1.406 ms |
| 4,096 | 4,099 | 12,306 | 49,242 | 4.871 ms |

Medians use three workers per size. The native scale audit is enabled around closure; wall and CPU values are instrumented timings, not baseline latency. Process peak RSS medians range from about 29.0 to 29.8 MiB, dominated by the minimal process footprint at these sizes.

## Interpretation

The live trace's dominant rule motif is not inherently quadratic in the number of Concepts in this isolated engine workload: measured candidate-pair and Term counts are exactly affine in `C` through 4,099 Concepts, while the three fixed Percepts and true target Concepts remain unchanged. This is positive evidence that the current matcher handles this specific two-edge Scene/Percept × Microtheory/Concept pattern with linear measured work under the tested configuration.

It does not explain the far larger `name` read totals in the full live trace. That route has many other rules, Microtheories, scene-related graph structures, and repeated fixed-point activity; its three recognition rules may also run against more than the single Scene in this controlled harness. The sweep uses only three of six recognition rules, synthetic distractors, and simple kind-equality `Holds` definitions. It is not a general scaling theorem, complete live-route result, natural vocabulary distribution, or evidence that task execution factorizes across a small separator.

## Artifacts

- Preregistration: [SUBSTRATE_DESCRIBE_RULE_CONCEPT_CANDIDATE_SCALE_V1_PREREG_20260927.md](SUBSTRATE_DESCRIBE_RULE_CONCEPT_CANDIDATE_SCALE_V1_PREREG_20260927.md)
- Runner: [substrate_describe_rule_concept_candidate_scale_v1.py](../../../scripts/substrate_describe_rule_concept_candidate_scale_v1.py)
- Input lock: [describe_rule_concept_candidate_scale_v1_lock_20260927.json](../../../evaluation/substrate_capability/describe_rule_concept_candidate_scale_v1_lock_20260927.json)
- Raw workers: [describe_rule_concept_candidate_scale_v1_20260927.json](../../../evaluation/reports/describe_rule_concept_candidate_scale_v1_20260927.json)
- Independent analyzer: [analyze_substrate_describe_rule_concept_candidate_scale_v1.py](../../../scripts/analyze_substrate_describe_rule_concept_candidate_scale_v1.py)
- Independent analysis: [describe_rule_concept_candidate_scale_v1_analysis_20260927.json](../../../evaluation/reports/describe_rule_concept_candidate_scale_v1_analysis_20260927.json)
