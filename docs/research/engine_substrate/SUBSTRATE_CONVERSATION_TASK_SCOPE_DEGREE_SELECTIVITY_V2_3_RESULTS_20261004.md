# Conversation matcher degree and partial-selectivity v2.3 results

## Result

The current-source replay repeats the v2.2 workload with a new source lock and a compressed capture. Nine fresh workers complete 126 paired cases and 1,314 checkpoint comparisons. Runner gates and the independent analyzer pass, including source stability, exact monolithic/fallback/anchor state parity, trace-on/off parity, fallback-path controls, and rejection of unsafe ownership on cross-frame and orphan controls.

Across the panel, declared-anchor pruning reduces candidate pairs by 33.7% and Term evaluations by 33.8% against verified full fallback. It remains more expensive than monolithic closure: 2.67x candidate pairs and 2.77x Term evaluations. Every decoy profile retains a work reduction. The weakest is `missing_has_active_goal` at 13.6% fewer candidate pairs and 18.1% fewer Term evaluations; other profiles show about 32–33% reductions. Semantic-edge candidate accounting has zero unattributed delta.

The v2.3 totals match the v2.2 capture, establishing a current-source reproduction of this bounded matcher result. It is still a synthetic, ownership-annotated conversation fixture. The replay does not establish natural-task frame prevalence, learned ownership, partition discovery cost, a speed advantage over monolithic closure, or general tractability.

## Artifacts

- [Frozen protocol](SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_3_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_3.py) and [independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_degree_selectivity_pilot_v2_3.py)
- [Current-source lock](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_3_lock_20261004.json)
- [Compressed raw capture](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_3_20261004.json.gz)
- [Independent analysis](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_3_analysis_20261004.json)
- [Historical v2.2 result](SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_2_RESULTS_20261003.md)
