# Substrate edge-identity composer v1.1 — results

The three-family source-locked evaluation passes its preregistered 13/13 integrity and outcome gates. The general composer produces the expected `add_edge_identity_guard` site in all 12 worker/family cells. Recurrence and repeated-reply proposals transfer: all 16 corresponding held-out episodes pass, and source controls pass. No-overlap and tied-site controls abstain in all four workers.

The new independent `mint_actor_goal_recipient` family reproduces the predicted scope failure. Its source rule correctly creates a goal for each distinct actor/verb pair. The composer selects `out agent has_actor_goal any endpoint`; this passes all eight one-verb training episodes but returns `[1,0]` on all eight two-verb held-out episodes. The unmodified rule returns `[1,1]` on all eight held-out episodes. This is a useful boundary result: the current operator expresses relation-level existence at a bound endpoint, but cannot express actor-plus-verb identity through a freshly minted target.

Across all three families, the harness supplies rule target, residual cue, examples, and oracle. The edit-site extraction is reusable substrate code, graph Terms choose operator and site, and Python applies the mechanical rewrite. This is prompted proposal generation, not residual discovery or an autonomous correction cycle.

Median composition time is 36.1 ms (recurrence), 29.4 ms (conversation), and 24.8 ms (actor-recipient). Median proposal scoring is 12.0/58.6 ms train/held-out for recurrence, 38.6/47.8 ms for conversation, and 4.3/4.4 ms for actor-recipient. Actor timings are not directly comparable to the other families because its oracle uses compact native seed rules and local graph counts rather than the world-adapter conversation path.

## Artifacts

- [v1.1 protocol](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_IDENTITY_COMPOSER_V1_1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_substrate_edge_identity_composer_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_1_lock_20261002.json)
- [Frozen training orders](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_1_analysis_20261002.json)

Next add a structurally derived attribute-identity scope over freshly added nodes, then compare relation-only and identity-scoped guards on actor-recipient and other rules with multiple valid outputs. Keep the false-suppression case as a required regression boundary; also evaluate rules where any existing output edge is the correct idempotence key.
