# Conversation route failure diagnostics v1.3 results

The graph-resident composer seed was missing the `comprehends` edge from its
new `describe_scene` Goal to the matched request Message. The Python reference
composer contained that edge, but `reflective_faculty` routes this describe
branch through `seeds/composer_comprehension_graph.json`. The seed effect was
updated to add the missing relation.

Two fresh full-seed workers replayed the same five-prompt sequence with direct
hashes for the changed seed and dynamic scene/language dependencies. Capture
and independent checks pass. Both active native rule exports now contain the
`add_edge(g, comprehends, m)` effect. Each newly created Goal links to the
current inbound Message, reaches `resolved`, and produces three utterance
subgoals. The scene action returns `describe_scene`, and the final reply in
both workers is exactly: “I see the grey thing stays, the yellow counter, and
the blue thing moves.” The prior `report_self` fallback is eliminated in this
fixture.

The concern-authoring prompt remains unchanged: native arbitration selects
`typed_unresolved_action_dependency` repair, and `ask_back` asks what “two”
means. The current prompt provides no grounded comparison objects; adjudicate
that contract before changing repair precedence. Rule count increases by 22
during `_ensure_describe`; the older isolated-task predicate required an exact
delta of 18, so this behaviorally repaired route does not satisfy that stale
implementation-detail conjunct. The scene reply, Goal ownership, and lifecycle
checks pass independently. Update that benchmark predicate only in a new
version after revalidating the intended task contract.

This is a focused two-worker intervention check on one task order, not a
counterbalanced post-fix capability estimate. The earlier ten-worker panel
also lacked a direct dynamic-helper hash; rerun that panel with the completed
dependency closure and the corrected seed before using its pass fraction for
order comparisons or prevalence claims.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_3_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_3_lock_20261004.json)
- [Capture](../../../evaluation/reports/conversation_route_failure_diagnostics_v1_3_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_route_failure_diagnostics_v1_3.py)
- [Independent analysis](../../../evaluation/reports/conversation_route_failure_diagnostics_v1_3_analysis_20261004.json)
