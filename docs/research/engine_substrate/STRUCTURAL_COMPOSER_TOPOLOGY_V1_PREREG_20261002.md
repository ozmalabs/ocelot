# Structural composer matched-topology scaling v1 preregistration

This benchmark asks whether unrelated graph topology changes full prompted composer latency after node and edge counts are held fixed. It crosses four proposal families (recurrence, repeated reply, actor relation-only, actor+verb identity) with four directed layouts over 100,000 unrelated nodes and exactly 400,000 edges: cyclic regular, 100-hub, 1,000-node clustered regular, and deterministic random regular. Each layout uses four edge types with 100,000 edges per type. Three fresh-process replicates per family/layout run two warmups; the 48 measured jobs execute in deterministic shuffled order (seed 61008).

The topologies differ in degree distribution and clustering. The hub layout concentrates all 400,000 edges on 100 source nodes, while the three regular layouts have outdegree four at every node; clustered edges remain within their 1,000-node block. Every noise edge is inserted unchecked and uses types unrelated to the proposal family. Node build, edge build, RSS, and composition are recorded separately. Expected target/operator/site and primary-rule isolation are locked from prior transfer results. This experiment measures sensitivity of prompted composer selection to unrelated topology. It does not measure inference over those edges or sensitivity when the target rule queries the noise relation itself.

- Runner: [measure_structural_composer_topology_v1.py](../../../evaluation/substrate_capability/measure_structural_composer_topology_v1.py)
- Analyzer: [analyze_structural_composer_topology_v1.py](../../../evaluation/substrate_capability/analyze_structural_composer_topology_v1.py)
- Lock: [structural_composer_topology_v1_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_topology_v1_lock_20261002.json)
- Results: [structural_composer_topology_v1_20261002.json](../../../evaluation/reports/structural_composer_topology_v1_20261002.json)
