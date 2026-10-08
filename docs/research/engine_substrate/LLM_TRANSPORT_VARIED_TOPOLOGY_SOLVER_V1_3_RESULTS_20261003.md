# Varied-topology transport solver v1.3 results

Date: 2026-10-03  
Status: confirmatory three-worker run; all registered and independent gates passed.

## Question and workload

This experiment tests whether anonymous graph-only minimum separators can be reused to condition exact MAP inference over varied model-derived topologies, and whether the resulting route costs less than monolithic junction-tree MAP.

The locked workload contains 320 unique factor graphs: two Qwen3 exports, four adjacent layer transitions, ten held-out inputs, and imposed fan-in 1/2/4/8. Each graph has 16 variables with pair factors produced by the same fitted transport map and top-fan-in pruning as the existing cross-model assay. Three fresh workers each completed all 320 cases. Proposals use exhaustive graph-only minimum-separator search on a stable opaque node permutation. Component structure and elimination orders are cached by anonymous topology; each row binds its own factor weights to that structure. Components of at most five nodes use direct enumeration; larger components use exact local junction-tree MAP for each assignment to the separator.

The v1.3 analyzer independently recomputes each distinct separator family, rescoring both captured states from their factor tables and reconstructing target signs from returned node states. Source, topology, width, exact-energy, exact-sign, vocabulary, mutation, worker, and coverage gates all pass. See [protocol](LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_PREREG_20261003.md), [v1.1 amendment](LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_1_AMENDMENT_20261003.md), [v1.2 amendment](LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_2_AMENDMENT_20261003.md), [v1.3 amendment](LLM_TRANSPORT_VARIED_TOPOLOGY_SOLVER_V1_3_AMENDMENT_20261003.md), [source lock](../../../evaluation/substrate_capability/llm_transport_varied_topology_solver_v1_3_lock_20261003.json), [capture](../../../evaluation/reports/llm_transport_varied_topology_solver_v1_3_20261003.json), and [independent analysis](../../../evaluation/reports/llm_transport_varied_topology_solver_v1_3_analysis_20261003.json).

## Results

Across all 960 worker-cases, conditioned MAP matches junction-tree energy and returned target signs; both states directly rescore to their captured energies. Topology reconstruction and census joins, min-fill width certificates, valid-state checks, and no-mutation checks pass. Each worker discovers 241 distinct anonymous topologies and reuses 79 proposals in the 320-case batch.

Complete-batch time, including shared seed initialization, graph construction, factor extraction, proposal and component-order preparation, per-row factor binding, and solving:

| Worker | Structural route | Monolithic junction tree | Batch speedup |
|---|---:|---:|---:|
| 0 | 21.10 s | 41.91 s | 1.99× |
| 1 | 20.79 s | 40.61 s | 1.95× |
| 2 | 20.72 s | 40.56 s | 1.96× |

The discovery and cached component-order preparation cost is 388–420 ms per worker, or 1.21–1.31 ms per case when spread over this batch. Results vary strongly with fan-in:

| Model | Fan-in 1 | Fan-in 2 | Fan-in 4 | Fan-in 8 |
|---|---:|---:|---:|---:|
| Qwen3 0.6B | 1.11× | 0.91× | 0.32× | 2.20× |
| Qwen3 1.7B | 1.06× | 0.96× | 0.32× | 2.27× |

Ratios above 1 favor the structural route. Fan-in 1 shows a small advantage, fan-in 2 is near parity or slightly slower, fan-in 4 is about three times slower, and fan-in 8 is a little over twice as fast. Thus, separator search and exact decomposition do not yield a uniform speedup: performance depends on the entire graph/component structure and the implementation path.

## What the failed revisions taught us

V1.1's partial checkpoint contains 21 exact, mutation-free cases. It exposed a disconnected graph with a zero-sized separator but a 15-node component: enumerating `3^15` component assignments made that solver formulation unsuitable. V1.2 replaced large-component enumeration with exact local junction-tree inference, but its cache incorrectly reused per-row factor weights; independent rescore rejected 237/960 cases. V1.3 caches only graph-derived structure and binds the current row's factors separately. These failures are retained as diagnostics and excluded from the confirmatory claim.

## Interpretation and limits

This is evidence that exact separator-conditioned inference can be competitive on a repeated, evaluator-generated batch, and that local exact inference must exploit component treewidth rather than component size alone. It also shows a substantial regression on fan-in 4, so the overall 1.96× batch result is conditional on this particular mixture, batch repetition, graph family, and implementation.

The graphs have 16 nodes; fan-in is imposed; the corpus is generated; there are only two model exports; and the baseline and structural route are Python implementations with different code paths. This does not estimate natural-task cheap-cut prevalence, demonstrate substrate-native inference speed, establish scaling to larger graphs, or show substrate-driven learning or self-improvement. The useful next gate is to test naturally sourced task factor graphs, compare optimized baselines, and vary graph size while tracking both separator size and residual treewidth. Then measure whether the substrate can learn when to choose each route from observed costs and correctness.
