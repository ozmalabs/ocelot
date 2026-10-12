# Conversation task-scope path attribution v1.8 results

Date: 2026-10-03

V1.8 repeats the fixed v1.6 workload after adding per-rule counters for each scoped matcher path. The nine-worker source lock passes, and independent analysis reports zero errors: 36/36 final graph matches, 594/594 checkpoint matches, and trace-on/off parity. Aggregate path counts reconcile exactly with per-rule attribution.

| Rule | Local owned-pattern path | Full fallback | Total scoped matches |
|---|---:|---:|---:|
| `discourse_goal_select` | 2,184 | 6,762 | 8,946 |
| `discourse_goal_execute` | 2,148 | 6,654 | 8,802 |
| `discourse_goal_resolve` | 2,112 | 6,546 | 8,658 |
| `discourse_goal_fail` | 2,076 | 6,438 | 8,514 |
| **Total** | **8,520** | **26,400** | **34,920** |

Thus 24.4% of scoped match attempts use the local-pattern path and 75.6% fall back. Each of the four rules has nearly the same split. The guard is graph-global: once an earlier rule deletes an edge, `edge_delete_generation` disables local ordering reconstruction for every later call. This explains the fallback volume and identifies the current optimization barrier. Path attribution itself does not explain whether local-seeded attempts reduce candidate or Term work; v1.6/v1.7 show total work increased versus the v1.5 fallback-only baseline.

The next decision is whether to derive a deletion-safe ordering key from the live per-type and adjacency indexes, or use declared rule anchors with a separate soundness condition. Any implementation must still prove stable visit ordering and show reduced candidate/Term work against same-source fallback. This remains one authored workload and does not establish general tractability or speedup.

## Provenance

- Runner: [v1.8 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_8.py)
- Independent analyzer: [v1.8 analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_8.py)
- Source lock: [v1.8 lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_8_lock_20261003.json)
- Capture: [v1.8 capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_8_20261003.json)
- Analysis: [v1.8 analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_8_analysis_20261003.json)
- Cost-center report: [v1.7 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_COST_ATTRIBUTION_V1_7_RESULTS_20261003.md)
