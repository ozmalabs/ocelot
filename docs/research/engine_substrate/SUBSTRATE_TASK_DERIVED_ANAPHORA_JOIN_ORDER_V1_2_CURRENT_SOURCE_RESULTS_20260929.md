# Task-derived anaphora join-order v1.2 current-source results (2026-09-29)

## Result

The current-source replay completed all 48 planned fresh processes: every permutation of the four positive clauses, two replicates each. The source/native lock was stable before and after the run and within every worker; all child logs are present and hash-valid. The independent analyzer passes 293/293 checks, including exact task-oracle output, fixed-point termination, clause-counter conservation, candidate-counter attribution, and identical canonical whole-graph digest across all runs.

The 24 requested permutations produce only **8 distinct installed edge orders** after the rule is installed. Candidate tests are stable within each realized order and range from 8 to 16, a 2× spread. Therefore the complete requested permutation count is not the number of distinct runtime orders; the observed optimization opportunity is modest for this single four-edge task. All orders return the same task result: “it” refers to “question,” and the resulting intent concerns “question.”

| Installed edge order | Requested permutations | Candidate tests (median; range) |
|---|---:|---:|
| `about_concept → has_intent → responds_to → has_mention` | 12 | 16 (16–16) |
| `has_intent → about_concept → responds_to → has_mention` | 6 | 15 (15–15) |
| `has_intent → responds_to → about_concept → has_mention` | 2 | 12 (12–12) |
| `has_intent → responds_to → has_mention → about_concept` | 4 | 11 (11–11) |
| `has_mention → responds_to → has_intent → about_concept` | 12 | 13 (13–13) |
| `responds_to → has_intent → about_concept → has_mention` | 4 | 10 (10–10) |
| `responds_to → has_intent → has_mention → about_concept` | 2 | 9 (9–9) |
| `responds_to → has_mention → has_intent → about_concept` | 6 | 8 (8–8) |

The measured closure runs with native audit enabled to collect per-rule and per-clause work counters, so its wall-clock values are diagnostic only and are not a plain-speed comparison. No semantic or graph difference appears in the tested fixture. This supports the claim that clause order changes candidate work in a second authored family; it does not show that an automatic optimizer can discover the best order, that the 2× range matters at production scale, or that natural tasks exhibit this sensitivity.

## Reproduction and evidence

- [Preregistration](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_2_CURRENT_SOURCE_PREREG_20260929.md)
- [Current-source amendment](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_2_CURRENT_SOURCE_AMENDMENT_20260929.md)
- [Runner](../../../scripts/substrate_task_derived_anaphora_join_order_v1_2.py)
- [Analyzer](../../../scripts/analyze_substrate_task_derived_anaphora_join_order_v1_2.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_anaphora_join_order_v1_2_lock_20260929.json)
- [Raw workers](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_2_workers_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_2_analysis_20260929.json)
- [Run manifest](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_2_20260929.json)

## Interpretation

The held-out CAN timing replication measures a 3.50–4.04× instrumentation-off speedup for one two-rule sparse-first change. This anaphora replay provides a second authored family only for candidate-work sensitivity, not a second plain-speed replication because counters require audit instrumentation. Together they justify broader matched task-family panels; they do not yet justify a production rule-reordering change.
