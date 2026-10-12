# Conversation task-scope cost attribution v1.7 results

Date: 2026-10-03

V1.7 repeats the v1.6 nine-worker, three-order, four-case parity panel with the already-enabled per-rule scale audit serialized into each scoped checkpoint. The independent analyzer reports zero errors and all source, worker, trace, and state-parity gates pass: 36/36 final states and 594/594 checkpoint states match monolithic closure.

The per-rule counters reconcile exactly to the aggregate scoped work. Four discourse lifecycle rules account for all 170,853 candidate visits and all 654,438 Term evaluations:

| Rule | Candidate visits | Term evaluations |
|---|---:|---:|
| `discourse_goal_resolve` | 46,467 | 171,306 |
| `discourse_goal_select` | 44,547 | 158,922 |
| `discourse_goal_execute` | 44,247 | 165,186 |
| `discourse_goal_fail` | 35,592 | 159,024 |

This identifies the measured cost center but does not distinguish seed-path from fallback work within each rule or by closure epoch. The experiment remains an authored conversation workload; ownership is annotated for measurement. It gives no natural-task prevalence or speedup result. The v1.6 all-variable seeded path still increases aggregate work against v1.5 (9.45× versus 9.13× candidate work; 12.69× versus 11.17× Term work).

V1.8 adds rule-level path selection attribution: 8,520 calls use local-pattern seeding and 26,400 fall back. The global edge-deletion guard explains most fallback: after any deletion, local order reconstruction is disabled for every later scoped call. The data now narrows the next engineering choice to a deletion-safe matching-order index or declared anchors with an independent soundness condition. It still does not partition candidate/Term work by path, so the implementation branch remains unproven as an optimization. See [v1.8 path attribution](SUBSTRATE_CONVERSATION_TASK_SCOPE_PATH_ATTRIBUTION_V1_8_RESULTS_20261003.md).

## Provenance

- Runner: [v1.7 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_7.py)
- Independent analyzer: [v1.7 analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_7.py)
- Source lock: [v1.7 lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_7_lock_20261003.json)
- Capture: [v1.7 capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_7_20261003.json)
- Analysis: [v1.7 analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_7_analysis_20261003.json)
- Matcher implementation evaluation: [v1.6 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_LOCAL_PATTERN_V1_6_RESULTS_20261003.md)
