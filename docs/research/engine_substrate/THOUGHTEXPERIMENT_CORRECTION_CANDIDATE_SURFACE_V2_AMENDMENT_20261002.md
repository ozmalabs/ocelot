# Candidate surface v2 amendment — historical inventory schema comparison

The preregistered runner captured three fresh workers under the complete pre-capture source/native lock. The first analyzer passed 8/9 checks because it compared v2 inventory rows including `task_shaped_labels` against v1 rows that did not have that field. No capture or inventory integrity gate failed; the failed gate was the historical equality comparator.

The corrected independent reviewer compares only the common, preregistered fields (`target_rule`, ordered `candidate_labels`, and `candidate_count`) and separately checks v2's task-shaped-label annotations against the known candidate rule. It also recomputes current source/native hashes, worker source-lock agreement, exact worker parity, state preservation, and family-count reconciliation. The original 8/9 analysis is preserved unchanged; the corrected review artifact records the reviewer hash and passes 9/9 gates. The amended conclusion is limited to an exact current-source syntactic inventory, not candidate utility.

- [Initial analysis, retained](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_20261002.json)
- [Corrected independent review](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_review_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_raw_20261002.json)
