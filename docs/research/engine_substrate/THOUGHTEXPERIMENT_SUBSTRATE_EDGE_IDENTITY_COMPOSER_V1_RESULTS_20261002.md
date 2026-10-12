# Substrate edge-identity composer v1 — results

The source-locked evaluation passes all 12 analysis gates across four workers and two authored rule families. The general structural composer generated the expected `add_edge_identity_guard` proposal in all eight family/worker cells. It chose the outgoing `candidate` / `has_mint_offer` site for recurrence and incoming `m` / `responds_to` site for conversation. All 16 training and all 16 held-out episodes passed, as did both families' source-rule controls. The no-overlap cue abstained in 4/4 workers, and the cue that left three conversation sites tied also abstained in 4/4 with an explicit tie report.

This advances the proposal boundary: the evaluation harness no longer scans the target AST or supplies a candidate edit list. The reusable `domains.edit_ops.find_edge_identity_sites` exposes applicable sites, `EditSite` graph nodes carry those choices, and the native graph Term selects an applicable operator and a unique site before the mechanical applier builds the rule variant. The harness still supplies the faulty target, the residual cue, examples, and independent oracle. The result is prompted substrate-side proposal generation for two authored rules; residual discovery, operator invention, durable integration, and broad generalization remain unmeasured.

Median composer time is 36.8 ms for recurrence and 30.5 ms for conversation. Median proposal scoring over the two training episodes is 11.7 ms and 38.7 ms; held-out scoring is 58.8 ms and 48.1 ms. These local sequential fixture measurements include helper/context costs in the scoring phase and do not support a general performance claim.

The follow-on makes the action-only structural composer eligible for this edit only when `structural_rule_scope=all_mutable_rules`; its existing action scope keeps its four prior operators. The measured path still performs rule-shape applicability extraction in Python, represents the resulting edit sites in the graph, uses a native Term for operator/site choice, and applies the chosen pure edit in Python.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_identity_composer_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_lock_20261002.json)
- [Frozen training orders](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_analysis_20261002.json)

Next test additional edge-producing rule families, especially cases where coarse output scope is incorrect, then test whether residuals can be detected without a task-authored cue. Count proposal recall, false or overly broad edits, abstentions, and full end-to-end cost.
