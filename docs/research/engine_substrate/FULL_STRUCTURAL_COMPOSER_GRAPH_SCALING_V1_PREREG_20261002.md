# Full structural composer graph scaling v1 preregistration

This experiment measures the prompted `compose_general_structural_variant` path for the real seeded `mint_actor_goal_recipient` rule and its known `actor+verb` identity repair. Each replicate starts from a fresh `actor_context(fault=True)`. It adds 0, 1,000, or 10,000 unrelated nodes, records that setup cost separately, adds the same externally supplied capability-axis cue, and times the full composer. The expected proposal is `add_edge_identity_guard` at `out agent has_actor_goal attributes actor+verb`; the active primary rule store must remain unchanged.

The preregistered design has three unrelated-node counts and five fresh replicates per count. The lock includes the runner plus hashes returned by the existing v1.2 source-lock harness, including native binary and core source provenance. This is a single-host scaling measurement for one prompted structural proposal. It does not measure autonomous residual discovery, held-out task utility, or memory.

- Runner: [measure_full_structural_composer_graph_scaling_v1.py](../../../evaluation/substrate_capability/measure_full_structural_composer_graph_scaling_v1.py)
- Lock: [full_structural_composer_graph_scaling_v1_lock_20261002.json](../../../evaluation/substrate_capability/full_structural_composer_graph_scaling_v1_lock_20261002.json)
- Results: [full_structural_composer_graph_scaling_v1_20261002.json](../../../evaluation/reports/full_structural_composer_graph_scaling_v1_20261002.json)
