# Mixed-relation join-cost and order-selection v1 results

Date: 2026-10-01  
Status: complete; all 9 analyzer gates pass.

## Result

The source-locked panel ran 90 fresh workers over path4, star4, and cycle4 rules; N=16/32; four rotations of one sparse relation plus a balanced control; and three replicates. Relation populations were loaded into the native graph before rule import. The analyzer independently replayed the engine's rarest-edge/connected-edge ordering and simulated candidate work for the installed order and all 24 clause permutations.

All observed installed orders matched the independent policy replay. The independent prefix simulator matched the native per-clause counters in every worker, and each prefix sum reconciled to the global candidate-test total. All effect-free runs preserved the graph and reached a stable terminal probe. The installed order was a minimum-work permutation in **90/90 workers**.

| N | Relation population layout | Median candidate tests, all three patterns | Minimum among 24 orders | Reduction from balanced |
|---:|---|---:|---:|---:|
| 16 | One relation at N, other three at 4N | 1,360 | 1,360 | 75% |
| 16 | All four relations at 4N | 5,440 | 5,440 | — |
| 32 | One relation at N, other three at 4N | 2,720 | 2,720 | 75% |
| 32 | All four relations at 4N | 10,880 | 10,880 | — |

Rotating the sparse relation among the four clauses did not change total work for these graph layouts. The heuristic chose that relation first; on balanced ties it followed authored order. Doubling N doubled candidate work in both population conditions. This is a positive control for rare-edge-first on regular mixed-type joins, and it contrasts with the CAN Hebbian shape where raw cardinality selects `has_concept` first and costs 2.28–2.89× explicit sparse-first.

## Interpretation and limits

The 90/90 result does not show that the selector is generally optimal. Each relation's cyclic-offset edge set is nested inside the denser relation sets, with uniform per-node degrees and no skew; the four relation populations vary only from N to 4N. These regular conditions strongly favor starting from the sparse relation. They do not reproduce the CAN case's repeated edge types, two-hop coactivation ledger, or mismatched intermediate-binding growth. The synthetic relation names are installed with `graph_from_dict()`, which bypasses application ontology admission while still exercising the native typed graph matcher. Next test nonnested and degree-skewed relations, repeated relation types, and the production CAN pattern under the same independent 24-order work oracle.

## Reproduction and artifacts

- Protocol: [preregistration](SUBSTRATE_MIXED_RELATION_JOIN_COST_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1.py)
- Analyzer: [independent work simulation and exhaustive order comparison](../../../scripts/analyze_substrate_mixed_relation_join_cost_v1.py)
- Lock: [source/input lock](../../../evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1_lock_20261001.json)
- Raw data: [90 worker records](../../../evaluation/reports/substrate_mixed_relation_join_cost_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/substrate_mixed_relation_join_cost_v1_analysis_20261001.json)

Reproduce with `python3 evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1.py` to check the lock, execute workers, and invoke the analyzer.
