# Generic edge-once guard on repeatable replies v1 — results

## Result

All 11 independent analysis checks pass on the real `reply_to_adjacency_pair` seed. The unmodified source rule returns one reply for each of two training inputs in all four workers and one per each of three held-out inputs (8/8 and 12/12 total replies). Removing its existing per-message negative guard and applying the generic bound-source transform yields only `Not Exists(agent.sent)`, because `agent` is bound but each emitted reply is a fresh, unbound target.

That coarse proposal returns reply counts `[1, 0]` on every two-message training sequence and `[1, 0, 0]` on every three-message held-out sequence. The composer's fixed marker guard returns `[0, 0]` on training. Both proposals fail the training oracle, and the native graph evidence selector abstains in all workers. Held-out scoring of the rejected coarse proposal is diagnostic only; it was never adopted. The rule store remains unchanged during trials and evidence stays branch-local.

This is a concrete counterexample to treating source-plus-edge-type as a universal idempotence key. In recurrence, each candidate is its own source, so the coarse key works; in conversation, one agent intentionally emits replies for many messages, so the same key suppresses valid outputs. The fixed seed already carries the correct per-input guard, which the fault injection removed. The result is one authored conversation rule, not a natural-task false-positive rate. A reusable operator needs to preserve target identity or derive a per-input key and must be tested against both unique and intentionally repeated outputs.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_EDGE_IDEMPOTENCE_REPEATABLE_BOUNDARY_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_edge_idempotence_repeatable_boundary_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_lock_20261002.json)
- [Training orders](../../../evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_orders_20261002.json)
- [Held-out diagnostics](../../../evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_scores_20261002.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_analysis_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_edge_idempotence_repeatable_boundary_v1.py)
