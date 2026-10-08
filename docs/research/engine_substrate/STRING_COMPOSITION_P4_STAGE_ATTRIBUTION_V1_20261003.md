# Fresh string PBE: P4 stage attribution v1

Date: 2026-10-03. Retrospective analysis of the already frozen fresh-suite capture; not a new preregistered performance claim.

## Funnel

Recognition was true on all 18 tasks in every arm. Main/replay routed three casefold-count tasks to retrieved exemplars: one generalized and two were accepted on revealed data but failed all three heldout rows. The other 15 reached enumeration and exhausted the 200,000 candidate budget without a returned candidate. With retrieval disabled, all 18 entered enumeration: three returned a candidate under the default cap, two of which were accepted incorrectly and one remained a gap; 15 exhausted the cap. At 500,000 candidates, five tasks returned candidates: two generalized, two were accepted incorrectly, and one was still a gap. Thirteen exhausted the raised cap; 14 tasks remained gaps overall.

| Arm | Recognized | Retrieved | Enumerated | Search cap exhausted | Candidate returned | Exact heldout | Accepted wrong | Gaps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Main | 18/18 | 3 | 15 | 15 | 0 | 1 | 2 | 15 |
| Retrieval bypass | 18/18 | 0 | 18 | 15 | 3 | 0 | 2 | 16 |
| Retrieval bypass, 500k | 18/18 | 0 | 18 | 13 | 5 | 2 | 2 | 14 |
| Main replay | 18/18 | 3 | 15 | 15 | 0 | 1 | 2 | 15 |

## Interpretation and next gate

This puts the observed boundary after request recognition. In this benchmark the main route is split between retrieval overfitting (two accepted false programs) and capped enumeration (15 gaps). Enlarging the enumeration budget returns two additional exact programs at substantially higher work, but still leaves 14 gaps and two false accepts. The main and replay funnel is reproducible. The direct native execution audit separately shows all six hand-authored target compositions execute on the same frozen task suite.

The capture does not log the complete rejected candidate stream or candidate-level verifier decisions, so it cannot distinguish search-order/grammar omission from failure to reach a target within the cap; nor does it identify why the two false programs evade revealed-row verification. Next evaluation should record bounded candidate-level traces and separately score train fit, holdout, and independent cross-validation for each returned program. Claims remain specific to this synthetic 18-task suite; recognition here is a fixed pipeline datum, not evidence of broad language understanding.

## Artifacts

- [Base benchmark result](STRING_COMPOSITION_FRESH_PBE_V1_RESULTS_20261003.md)
- [Direct execution audit](STRING_COMPOSITION_NATIVE_EXECUTION_AUDIT_V1_RESULTS_20261003.md)
- [Attribution script](../../../evaluation/substrate_capability/attribute_string_composition_p4_stages_v1.py) and [machine-readable output](../../../evaluation/reports/string_composition_p4_stage_attribution_v1_20261003.json)
