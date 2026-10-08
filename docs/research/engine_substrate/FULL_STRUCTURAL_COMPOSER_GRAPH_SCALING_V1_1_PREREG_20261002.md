# Full structural composer graph scaling v1.1 preregistration

This follow-up corrects the first capture's observed first-use confound. The original v1 run executed zero unrelated nodes first and showed a slow first composition; its cross-size timing comparison is retained as diagnostic only. V1.1 adds two full-composition warmups per graph-size cell and uses a deterministic shuffled cell order (seed 61002) before collecting five fresh replicates per cell.

The task remains the real seeded `mint_actor_goal_recipient` repair with the externally supplied `actor+verb` cue. Each replicate starts from a fresh `actor_context(fault=True)`, inserts 0, 1,000, or 10,000 unrelated nodes, adds the cue, and times `compose_general_structural_variant`. Graph setup remains separately timed. The expected result is `add_edge_identity_guard` at `out agent has_actor_goal attributes actor+verb`, with the active primary rule store unchanged. Source provenance includes the base v1.2 source-lock harness and native binary. This is a single-host prompted-composition measurement, not autonomous diagnosis or memory measurement.

- Runner: [measure_full_structural_composer_graph_scaling_v1_1.py](../../../evaluation/substrate_capability/measure_full_structural_composer_graph_scaling_v1_1.py)
- Lock: [full_structural_composer_graph_scaling_v1_1_lock_20261002.json](../../../evaluation/substrate_capability/full_structural_composer_graph_scaling_v1_1_lock_20261002.json)
- Results: [full_structural_composer_graph_scaling_v1_1_20261002.json](../../../evaluation/reports/full_structural_composer_graph_scaling_v1_1_20261002.json)
