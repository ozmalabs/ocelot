# Conversation scope matcher semantic-edge attribution v2.0.2

Date: 2026-10-03  
Protocol and amendment: [v2 declared-anchor preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_DECLARED_ANCHOR_V2_PREREG_20261003.md)  
Runner: [scope-anchor pilot](../../../evaluation/substrate_capability/conversation_task_scope_anchor_pilot_v2_0.py)  
Analyzer: [independent scope-anchor analysis](../../../evaluation/substrate_capability/analyze_conversation_task_scope_anchor_pilot_v2_0.py)  
Source lock: [v2.0.2 lock](../../../evaluation/substrate_capability/conversation_task_scope_anchor_pilot_v2_0_2_lock_20261003.json)  
Capture: [v2.0.2 capture](../../../evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_2_20261003.json)  
Analysis: [v2.0.2 analysis](../../../evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_2_analysis_20261003.json)

## Result

The nine-worker, 54-case capture passes the same state, goal-lifecycle, trace, ownership-guard, source-stability, and workload-coverage gates as v2.0.1. The additional semantic-edge counter accounts for every Candidate pair in both scoped arms: 81,228 attributed pairs versus 81,228 from the aggregate scale counter, with zero unattributed difference. It records 44,862 expansion calls in each arm.

For every `(rule, source variable, edge type, target variable)` signature, the fallback and anchor arms have identical candidate-pair totals and identical expansion-call totals. Thus the previous aggregate tie is not caused by work hidden in an unattributed clause. Anchor-first reordering changes neither the number of expansions nor the size of candidate sets for these authored graph cases. The result diagnoses the limit of this workload and matcher strategy; it does not establish that clause order is irrelevant for other graph distributions.

## Correction — both comparison arms carried anchor metadata

The runner patched the seed-loader module, but `substrate.boot_core` retained its module-level `manifest_for` import. The arm labelled `fallback` therefore also used the anchor metadata. The semantic-edge counters exactly reconcile the two measured arms, but they compare anchor-enabled paths and do not establish that generic fallback has the same search tree. Withdraw the interpretation in the preceding paragraph about anchor-first ordering versus full fallback. The v2.1.1 run fixes and gates arm isolation; its per-edge counts show the actual fallback/anchor difference under controlled decoy selectivity: [results](SUBSTRATE_CONVERSATION_TASK_SCOPE_SELECTIVITY_V2_1_RESULTS_20261003.md).

## Next experiment

Preserve the v2.0.2 state/guard matrix as a semantic regression panel. Add a preregistered selectivity panel with controlled branching and decoy relations around the four lifecycle patterns, while holding true bindings and outcomes fixed. Measure each semantic edge's expansion calls and candidate pairs, Term work, exact checkpoint parity, and wall time as a secondary measure. Include both degree-balanced and skewed relation populations. This will test whether the engine can benefit from anchor-first order under a graph distribution where join order changes intermediate cardinality. If per-edge work still does not change, the next matcher design needs an index/probe that avoids expansion of irrelevant edges or reuse across scopes, not another ordering tweak.
