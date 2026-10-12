# Thoughtexperiment A8 proposal bridge v1 — censored result

**Result: proposal-stage source-attribution gate failed; held-out scoring was not opened.** The source-locked order stage completed four workers and produced a prompted `flip_comparison` variant in each. However, all four `ground_concern` calls report `served_by: python`, not `graph`; the unprompted calls also fell back to Python. The preregistered requirement was specifically to measure the live graph-resident A8 path. These proposals therefore cannot be credited as substrate-generated, and no utility or cost comparison is claimed from this capture.

The failure was traced to a current source mismatch. `seeds/composer_experiment_graph.json` contains three graph-authored meta-rule nodes (mint, judge, and adopt). `domains.reflective_faculty._ensure_graph_composer_seed` expects exactly one Rule in every composer seed and raises `ValueError: composer_experiment_graph: expected one graph-authored composer Rule, found 3`. `_ground_via_graph_meta` catches that error and returns `None`; `ground_concern` then uses the Python composer fallback. A direct reproduction on the same locked source confirmed the exception. The target rule remains unchanged, and the frozen order capture contains no held-out outcomes.

This exposes an integration regression that the previous navigation result did not record: its capture omitted `served_by`, so its behavioral result demonstrates a useful structural edit but does not establish that the graph authored it. The graph seed and Term still exist; the runtime adapter currently prevents them from serving this path. A follow-up may fix the adapter to load and verify every Rule in a multi-rule seed, then repeat under a new protocol, source lock, and capture. Keep this failed v1 capture immutable and do not score it post hoc.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_lock_20261002.json)
- [Frozen orders and proposals](../../../evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_orders_20261002.json)
- Held-out score capture: **not created**, because the source-attribution gate failed before scoring.
