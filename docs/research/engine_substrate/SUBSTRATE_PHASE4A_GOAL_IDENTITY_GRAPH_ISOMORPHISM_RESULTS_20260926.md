# Phase 4A Goal identity graph-isomorphism scale results

The N=2 follow-up diagnostic found that full and scoped closure produced equal typed graphs up to node ID ordering. This preregistered extension repeats the structural comparison for three fresh-process pairs per N=2/4/8 cell, using the same locked Phase 4A producer workload, rule seed, and worker implementation.

All 18 worker PIDs were distinct. For every one of the nine pairs:

- Full and scoped runs completed and retained exact task-projection parity.
- The typed node descriptor multisets matched (`type` plus sorted attributes), and every node was mapped.
- The complete typed edge multisets matched after mapping nodes by descriptors.
- Raw graph digests differed, consistent with generated node IDs and insertion order changing between scheduling policies.
- One repeated `Deliberation` descriptor class per pair was ambiguous by attributes alone. Nodes in each such class were paired in ID order, then the complete edge comparison passed.

The result verifies graph isomorphism under this explicit descriptor mapping for one small, finite Phase 4A task family. It does not prove that the mapping algorithm is complete for general graph isomorphism or that arbitrary scheduling policies preserve state. The edge equality check makes the tie-breaking mapping auditable for these nine captured pairs.

Protocol: [preregistration](SUBSTRATE_PHASE4A_GOAL_IDENTITY_GRAPH_ISOMORPHISM_PREREG_20260926.md). Runner and independent analyzer: [capture](../../../scripts/substrate_phase4a_goal_identity_graph_isomorphism_v1.py), [analysis](../../../scripts/analyze_substrate_phase4a_goal_identity_graph_isomorphism_v1.py). Lock, raw graph captures and analysis: [lock](../../../evaluation/substrate_capability/phase4a_goal_identity_graph_isomorphism_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_phase4a_goal_identity_graph_isomorphism_v1_20260926.json), [analysis report](../../../evaluation/reports/substrate_phase4a_goal_identity_graph_isomorphism_v1_analysis_20260926.json).

Next: keep this descriptor/edge comparison as a regression diagnostic for additional producer and task families, then add event-driven mutations and compare scoped wakeup against full closure while measuring frame reconstruction and notification costs.
