# Amendment: v2.4 rule-descendant ownership classification v1.1 (2026-09-27)

The first derived descendant analysis treated any native rule-minted node reachable through an edge upsert from the task root as a task descendant. Source inspection shows this can absorb durable global state: request A's `SelfConcern` and `GapRecurrence` are attached to the shared Agent through `has_self_concern` and `has_gap_recurrence`. They are request-triggered persistent side effects, not private task-frame children. V1.1 preserves those nodes as a distinct shared-state category.

The v1.1 ownership policy assigns a minted node to a request-local descendant only when it is attached by one of the observed task ownership edges `has_subgoal`, `has_intent`, or `seeks_interpretation_shadow`. Nodes attached through `has_self_concern` or `has_gap_recurrence` are persistent shared side effects. Other endpoints such as Concept references remain interfaces. This policy is source-informed and explicit, but chosen after the v1 trace inspection; it is a versioned derived analysis, not a preregistered reclassification.

Under this refined policy, both requests have five task-local rule-minted descendants (three child Goals, one Intent, and one TeacherRequest). Request A also creates a SelfConcern and GapRecurrence linked to shared Agent state; request B creates neither. Events touching the named lifecycle, shared scene/percept input, and task-local descendants total 7,306/1,140,892 for A and 6,421/997,848 for B (about 0.64% each). B additionally touches A's lifecycle in 2,400 events. These counts do not classify the remaining work and do not prove the chosen ownership edge vocabulary is complete.

The v1 analyzer and its broader connected-node counts are retained unchanged for reproducibility; interpret its seven A / five B nodes as connected minted candidates, not an ownership adjudication. V1.1 supersedes its task-descendant interpretation.

## Artifacts

- V1.1 analyzer: [analyze_substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1.py](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1.py)
- V1.1 analysis: [substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1_20260927.json](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1_20260927.json)
- Prior broad candidate analysis: [v1 analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_20260927.json)
