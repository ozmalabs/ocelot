# Substrate edge-attribute identity v1 — results

The preregistered, source-locked comparison passes **14/14 analysis gates** across four workers. Relation-level recurrence and repeated-reply proposals again pass 8/8 held-out episodes each. On the actor-recipient task, the relation-only guard passes its one-verb training cases but suppresses the second valid verb in all eight held-outs (`[1,0]`). The graph composer selects an attribute-scoped `actor+verb` guard from the new-node identity sites; it passes all eight held-out episodes (`[1,1]`). The original source rule also passes all source controls. No-overlap and ambiguous-site controls abstain in all four workers.

This is the first measured repair of the v1.1 false-suppression boundary by expanding proposal structure rather than patching the task rule. The pure edit layer finds fresh `add_node` targets linked to emitted edges and derives identity sites from direct `Attr(Var(bound), key)` fields. It enumerates each single field, each pair, and the complete field set when there are more than two fields, giving O(m²) site growth. The graph carries these sites as `EditSite` nodes and a native Term selects a unique edit. The selected `Not Exists(NodesOfType(ActorGoal))` guard compares the existing goal's `actor` and `verb` against the current rule binding.

The supported feature fragment is intentionally bounded: this capture does not exercise nested expressions, computed values, constants as identity dimensions, or field counts at scale. Python still extracts sites and applies the mechanical edit; the harness still supplies target and cue (`mint recipient actor verb pair identity`), examples, and oracle. The result is prompted proposal generation with a real held-out correction, not residual discovery or autonomous self-improvement.

Median composition is 36.9 ms (recurrence), 30.1 ms (conversation), 26.2 ms (relation-only actor), and 17.0 ms (actor+verb identity). Median training/held-out proposal scoring is 12.5/60.4 ms, 39.6/49.9 ms, 4.3/4.5 ms, and 4.3/4.5 ms respectively. These are sequential local diagnostics; actor scoring uses direct seeded graph rules while conversation includes world-adapter work.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_attribute_identity_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_attribute_identity_v1_lock_20261002.json)
- [Frozen training orders](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_v1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_v1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_attribute_identity_v1_analysis_20261002.json)

Next measure site growth and composition cost as the number of identity fields and target graph size increase, add cases with computed or absent identity fields, and test whether a residual can select this scope without a task-authored cue.
