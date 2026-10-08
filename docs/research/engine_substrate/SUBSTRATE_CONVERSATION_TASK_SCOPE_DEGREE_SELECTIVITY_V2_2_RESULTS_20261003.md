# Conversation matcher degree and partial-selectivity v2.2 results

Date: 2026-10-03  
Protocol: [v2.2 preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_2_PREREG_20261003.md)  
Runner: [degree/selectivity pilot](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_2.py)  
Analyzer: [independent analysis](../../../evaluation/substrate_capability/analyze_conversation_task_scope_degree_selectivity_pilot_v2_2.py)  
Source lock: [v2.2 lock](../../../evaluation/substrate_capability/conversation_task_scope_degree_selectivity_pilot_v2_2_lock_20261003.json)  
Capture: [v2.2 capture](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_2_20261003.json)  
Analysis: [v2.2 analysis](../../../evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_2_analysis_20261003.json)

## Result

The nine-worker run covers 126 paired cases and 1,314 checkpoints. Runner and independent-analysis gates pass: source stability, exact final/checkpoint states, lifecycle and trace parity, anchor path coverage, zero anchor-path calls in every fallback checkpoint, positive full-fallback calls, and cross-frame/orphan proof rejection. Semantic-edge counters account for all Candidate work in both arms.

Across the full matrix, anchor uses 2,696,652 Candidate pairs and 10,484,802 Term evaluations; verified fallback uses 4,065,435 and 15,834,393. Reductions are 33.7% and 33.8%. The anchor arm still costs 2.67× monolithic Candidate work and 2.77× monolithic Term work, so the result demonstrates pruning relative to repeated scoped fallback, not an overall engine speedup.

Each profile summary combines nine paired runs (three frame orders × three replicates):

| Unowned decoy profile | Candidate reduction | Term reduction |
|---|---:|---:|
| 256 isolated complete Goal/Event pairs | 32.3% | 33.2% |
| 32 shared-Event complete Goals | 33.1% | 32.5% |
| 256 shared-Event complete Goals | 33.3% | 33.2% |
| 1,024 shared-Event complete Goals | 33.3% | 33.3% |
| 256 decoys missing `has_active_goal` | 13.6% | 18.1% |
| 256 decoys missing `originated_in` | 32.3% | 33.2% |
| 256 decoys missing `has_event` | 33.3% | 33.2% |
| 256 decoys missing `for_goal` | 32.3% | 33.2% |

The weakest profile is the one missing `has_active_goal`, because it removes the relation that first binds the Goal variable across irrelevant decoys. Other omitted edges still incur much of the matcher and Term work: the Goal lifecycle predicate becomes decidable as soon as the Goal is bound, so later missing relations do not prevent that earlier predicate evaluation. This is consistent with the recorded semantic-edge counts and current predicate-pushdown order. The advantage therefore depends on which relation produces the candidate Goal set, not merely on whether a decoy completes the full pattern.

## Interpretation and next gate

The controlled result supports anchor pruning across isolated and shared high-degree event structures, and across several partial pattern shapes. It does not show that these structures or frame annotations occur naturally. Next measure graph size and memory while holding decoy profile fixed, then apply independently labeled ownership to a naturally harvested task graph. Include the `missing_has_active_goal` boundary explicitly; do not claim the ~33% reduction for every pattern distribution.
