# CAN mixed-degree join-order v1 results

Date: 2026-10-01  
Status: complete; all 9 analyzer gates pass.

## Result

The panel ran 36 source-locked fresh workers over N={16,32}, Q={N,4N,floor(N(N−1)/4)}, uniform cyclic-offset and source-skewed coactivation layouts, and three replicates per cell. It used the exact production CAN Hebbian match pattern, with effects and `where` predicates removed so the matcher exhaustively enumerated bindings without modifying graph state. Rules were imported after graph construction. The independent typed-graph simulator reproduced all candidate-test prefix counts and exhaustively evaluated all 24 clause orders.

The engine installed `[mt has_concept a, mt has_concept b, coact coactivation_of b, a coactivated_with coact]` in all cells. That order was never minimum-work. The best order in every cell was `[mt has_concept a, a coactivated_with coact, coact coactivation_of b, mt has_concept b]`: use one membership edge to bind `a`, follow the coactivation chain, then check membership for `b`.

| N | Q | Installed candidate tests | Best of 24 | Regret |
|---:|---:|---:|---:|---:|
| 16 | 16 | 784 | 304 | 2.58× |
| 16 | 64 | 5,392 | 1,168 | 4.62× |
| 16 | 60 | 4,832 | 1,096 | 4.41× |
| 32 | 32 | 3,104 | 1,120 | 2.77× |
| 32 | 128 | 21,536 | 4,384 | 4.91× |
| 32 | 248 | 70,496 | 8,464 | 8.33× |

The N=32,Q=248 installed prefix counts are `[32, 1,024, 7,936, 61,504]`; the minimum-work order has `[32, 248, 248, 7,936]`. Thus the first edge is already a low-cardinality `has_concept` edge; the wasted work comes from taking the *second* membership edge before joining the two coactivation edges. Across these cells, source-skewed and uniform pair layouts produce identical candidate prefix vectors. Under this pattern and full Microtheory membership, tested work depends on the aggregate relation populations and clause sequence, not the tested source-degree skew.

## Interpretation and limits

This directly diagnoses the prior CAN heuristic gap: first-edge cardinality can select a reasonable starting edge while connected-prefix ordering still creates an avoidable cross product. The exact 24-order oracle gives a concrete target for a cost model: estimate intermediate binding counts at each prefix, not just the first edge's global count. The observed regret is finite and exact for one rule pattern, small graphs, one Microtheory, and two synthetic pair layouts. The removed production `where` predicates, effect writes, other interacting rules, natural graph shapes, and statistics-collection cost remain unmeasured. This is matcher-work evidence, not a justified engine code change or broad capability result.

## Reproduction and artifacts

- Protocol: [preregistration](CAN_MIXED_DEGREE_JOIN_ORDER_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/can_mixed_degree_join_order_v1.py)
- Analyzer: [independent typed join and 24-order oracle](../../../scripts/analyze_can_mixed_degree_join_order_v1.py)
- Lock: [source/input lock](../../../evaluation/substrate_capability/can_mixed_degree_join_order_v1_lock_20261001.json)
- Raw data: [36 worker records](../../../evaluation/reports/can_mixed_degree_join_order_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/can_mixed_degree_join_order_v1_analysis_20261001.json)

Reproduce with `python3 evaluation/substrate_capability/can_mixed_degree_join_order_v1.py` to verify locked inputs, capture all cells, and run the analyzer.
