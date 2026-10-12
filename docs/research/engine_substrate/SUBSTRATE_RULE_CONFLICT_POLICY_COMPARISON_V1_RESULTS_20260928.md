# Rule conflict policy comparison v1 — results

All 23 analysis gates pass in three fresh workers. The comparison separates three approaches:

| Approach | Result | What it establishes |
|---|---|---|
| Existing rule `order` metadata | Still reports `repeated_graph_state`; reversing insertion changes final value from 2 to 1 | The default global fixpoint does not use this metadata to resolve conflicts |
| Exact-conflict admission prototype | Rejects the synthetic pair before installation | A narrow same-match/same-predicate, same-attribute contradiction is mechanically detectable outside the engine |
| Conflict proposal nodes | Reaches `fixed_point` under both insertion orders and preserves proposals A=1 and B=2 | Graph-resident conflict surfacing avoids oscillating overwrite while retaining both alternatives |

The admission check lives only in the measurement runner; it is not an engine capability. It uses exact structural equality and cannot detect general pattern overlap or predicate equivalence. The proposal-node representation is substrate-native via `add_node_if_absent` and `add_edge`, but it deliberately does not select a winner. A downstream resolver, policy, or abstention rule remains necessary.

Current evidence therefore favors representing unresolved conflict explicitly over relying on rule-order metadata. Rejection may be appropriate for provably contradictory generated rules, but a general checker needs a false-positive/false-negative study over overlapping graph patterns. A priority feature would require an explicit scheduler contract; existing `order` metadata alone is not one.

Artifacts: [preregistration](SUBSTRATE_RULE_CONFLICT_POLICY_COMPARISON_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_rule_conflict_policy_comparison_v1.py), [analyzer](../../../scripts/analyze_rule_conflict_policy_comparison_v1.py), [capture](../../../evaluation/reports/rule_conflict_policy_comparison_v1_20260928.json), [lock](../../../evaluation/substrate_capability/rule_conflict_policy_comparison_v1_lock_20260928.json), [analysis](../../../evaluation/reports/rule_conflict_policy_comparison_v1_analysis_20260928.json), [conflict baseline](SUBSTRATE_OVERLAPPING_RULE_CONFLICT_PROBE_V1_RESULTS_20260928.md).
