# Structural composer topology follow-up v1.1 preregistration

The initial matched-topology panel produced two slower actor+verb identity trials in the 100-hub layout and isolated slow trials elsewhere. V1.1 is a targeted repeat to assess whether the actor-identity hub result is stable. It measures that family across all four matched layouts (cyclic, hub, clustered, random regular), retaining 100,000 nodes, 400,000 unrelated edges, four equally sized edge types, two warmups, and eight fresh-process replicates per layout. The deterministic order seed is 61009.

The expected proposal is `mint_actor_goal_recipient` with `add_edge_identity_guard` at `out agent has_actor_goal attributes actor+verb`, and the primary rule store must remain unchanged. Topology construction and RSS are captured alongside composition. This follow-up adjudicates one family/topology anomaly; it is not a new broad family claim.

- Runner: [measure_structural_composer_topology_v1_1.py](../../../evaluation/substrate_capability/measure_structural_composer_topology_v1_1.py)
- Analyzer: [analyze_structural_composer_topology_v1_1.py](../../../evaluation/substrate_capability/analyze_structural_composer_topology_v1_1.py)
- Lock: [structural_composer_topology_v1_1_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_topology_v1_1_lock_20261002.json)
- Results: [structural_composer_topology_v1_1_20261002.json](../../../evaluation/reports/structural_composer_topology_v1_1_20261002.json)
