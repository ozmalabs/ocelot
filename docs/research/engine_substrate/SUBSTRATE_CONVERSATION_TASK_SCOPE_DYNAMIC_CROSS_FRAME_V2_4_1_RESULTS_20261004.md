# Dynamic cross-frame mutation control v2.4.1 results

## Gate result

The source-locked 9-worker replay passes all runner gates over 135 paired cases and 1,386 checkpoints. The independently analyzed full matrix passes with exact monolithic/fallback/anchor state parity, lifecycle parity, trace-on/off parity, source stability, and unsafe-ownership rejection.

The added control mutates the graph after both task frames and ownership roots exist: the first continuation Event in frame 0 receives a new `for_goal` edge to the Goal in frame 1. The mutation is applied identically in monolithic, full-fallback, anchor, and trace arms. A separate capture-hash-locked analyzer checks each control individually. All nine dynamic controls inject the edge; each produces 102 anchor-proof rejections and 102 full-fallback calls after the injection checkpoint, with exact checkpoint/final and lifecycle parity. The insertion is source-locked and represented by the capture's mutation flag; the control is not a naturally sampled dependency.

Across the full panel, anchor matching reduces candidate pairs by 33.64% and Term evaluations by 33.75% versus verified fallback. It remains 2.67x and 2.77x monolithic work. The dynamic control therefore shows that this guard can refuse an ownership-invalid shortcut on the exercised path, not that partitioning is cheaper or universally complete.

V2.4's first capture is preserved as a harness-gate failure: runtime parity held and all nine edges were injected, but its checks expected the old 14-case/126-case counts and only three controls. V2.4.1 fixes those accounting predicates and independently verifies the nine per-control guard outcomes; it does not change the workload or semantic gates.

## Limits and next gate

Frames and ownership are supplied by the harness. One synthetic conversation family does not establish ownership discovery, dependency recall for arbitrary mutations, natural-task prevalence, or general tractability. Next apply the guarded matcher to independently reviewed live task graphs, include discovery and memory costs, and retain exact monolithic parity as the acceptance condition.

## Artifacts

- [V2.4.1 preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_4_1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_4_1.py) and [main analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_degree_selectivity_pilot_v2_4_1.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_4_1_lock_20261004.json)
- [Compressed capture](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_4_1_20261004.json.gz)
- [Main independent analysis](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_4_1_analysis_20261004.json)
- [Per-control analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_degree_selectivity_v2_4_1_dynamic.py), [analysis lock](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_v2_4_1_dynamic_lock_20261004.json), and [analysis](../../../evaluation/reports/conversation_task_scope_degree_selectivity_v2_4_1_dynamic_analysis_20261004.json)
- [Preserved v2.4 gate-failure capture](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_4_20261004.json.gz)
